"""Server-only HF bridge; diagnostics never include credentials or uploaded paths."""
from concurrent.futures import TimeoutError as FutureTimeout
from functools import lru_cache
import logging
from pathlib import Path
import tempfile
import httpx
from gradio_client import Client, handle_file
from . import config

logger = logging.getLogger(__name__)

class SpaceError(Exception):
    def __init__(self, code, message, status=503):
        self.code, self.message, self.status = code, message, status

@lru_cache(maxsize=1)
def client():
    return Client(config.SPACE, token=config.TOKEN, verbose=False, download_files=False,
                  analytics_enabled=False, httpx_kwargs={'timeout':30.0})

def runtime_status():
    """Return a small, non-secret diagnostic suitable for the health endpoint."""
    result = {'state':'down', 'space_id':config.SPACE,
              'token_configured':bool(config.TOKEN), 'hf_http_status':None,
              'stage':None, 'reason':'unknown'}
    try:
        headers = {'Authorization':f'Bearer {config.TOKEN}'} if config.TOKEN else {}
        response = httpx.get(f'https://huggingface.co/api/spaces/{config.SPACE}/runtime',
                             headers=headers, timeout=8)
        result['hf_http_status'] = response.status_code
        if response.status_code != 200:
            result['reason'] = {401:'access_denied', 403:'access_denied',
                                404:'space_not_found_or_private', 429:'rate_limited'}.get(
                                    response.status_code, 'hf_http_error')
            return result
        body = response.json()
        if not isinstance(body, dict):
            result['reason'] = 'invalid_runtime_response'
            return result
        stage = body.get('stage','')
        result['stage'] = stage
        if stage == 'RUNNING':
            result.update(state='running', reason='ready')
        elif stage in ('SLEEPING','BUILDING','RUNNING_BUILDING','STARTING','APP_STARTING'):
            result.update(state='waking', reason='starting')
        else:
            result['reason'] = 'space_unavailable'
    except httpx.TimeoutException:
        result['reason'] = 'network_timeout'
    except httpx.RequestError:
        result['reason'] = 'network_error'
    except (ValueError, TypeError):
        result['reason'] = 'invalid_runtime_response'
    return result

def health():
    return runtime_status()['state']

def embeddings(content):
    path = None
    try:
        with tempfile.NamedTemporaryFile(suffix='.jpg',prefix='eokay-',delete=False) as f:
            f.write(content)
            path = Path(f.name)
        job = client().submit(handle_file(str(path)), 'both', api_name='/embed')
        try:
            result = job.result(timeout=config.TIMEOUT)
        except FutureTimeout:
            job.cancel()
            raise SpaceError('timeout','Analisis terlalu lama. Coba lagi sebentar.',504) from None
        data = result['embeddings']
        return data['vit'], data['dinov3']
    except SpaceError:
        raise
    except Exception as exc:
        client.cache_clear()
        diagnostic = runtime_status()
        # Exception text can contain request URLs or credentials. Log only safe metadata.
        logger.warning('HF bridge failed: exception=%s runtime_http=%s reason=%s token_configured=%s',
                       type(exc).__name__, diagnostic['hf_http_status'], diagnostic['reason'],
                       diagnostic['token_configured'])
        if diagnostic['state'] == 'waking':
            raise SpaceError('space_waking','Layanan AI sedang bangun. Coba lagi sebentar.') from None
        if diagnostic['reason'] in ('access_denied','space_not_found_or_private'):
            raise SpaceError('space_access_denied','Akses layanan AI belum tersedia. Coba contoh sambil menunggu perbaikan.') from None
        if diagnostic['reason'] == 'rate_limited':
            raise SpaceError('space_rate_limited','Layanan AI sedang membatasi permintaan. Coba lagi sebentar.') from None
        raise SpaceError('space_down','Layanan AI belum bisa dihubungi. Coba lagi atau gunakan foto contoh.') from None
    finally:
        if path:
            path.unlink(missing_ok=True)
