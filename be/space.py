"""Server-only Hugging Face bridge. Uploaded temporary files are always removed."""
from concurrent.futures import TimeoutError as FutureTimeout
from functools import lru_cache
from pathlib import Path
import tempfile
import httpx
from gradio_client import Client, handle_file
from . import config

class SpaceError(Exception):
    def __init__(self, code, message, status=503):
        self.code, self.message, self.status = code, message, status

@lru_cache(maxsize=1)
def client():
    return Client(config.SPACE, token=config.TOKEN, verbose=False, download_files=False,
                  analytics_enabled=False, httpx_kwargs={'timeout':30.0})

def embeddings(content):
    path = None
    try:
        with tempfile.NamedTemporaryFile(suffix='.jpg',prefix='eokay-',delete=False) as f:
            f.write(content)
            path = Path(f.name)
        # Live /embed takes (photo, selected), as defined by ai/app.py and view_api().
        job = client().submit(handle_file(str(path)), 'both', api_name='/embed')
        try:
            result = job.result(timeout=config.TIMEOUT)
        except FutureTimeout:
            job.cancel()
            raise SpaceError('timeout','Analisis terlalu lama. Coba lagi sebentar.',504) from None
        data = result['embeddings']
        return data['vit'], data['dinov3']
    except SpaceError: raise
    except Exception:
        client.cache_clear()
        if health() == 'waking':
            raise SpaceError('space_waking','Layanan AI sedang bangun. Coba lagi sebentar.') from None
        raise SpaceError('space_down','Layanan AI belum bisa dihubungi. Coba lagi atau gunakan foto contoh.') from None
    finally:
        if path: path.unlink(missing_ok=True)

def health():
    try:
        headers = {'Authorization':f'Bearer {config.TOKEN}'} if config.TOKEN else {}
        r = httpx.get(f'https://huggingface.co/api/spaces/{config.SPACE}/runtime',headers=headers,timeout=8)
        if r.status_code != 200: return 'down'
        stage = r.json().get('stage','')
        if stage == 'RUNNING': return 'running'
        if stage in ('SLEEPING','BUILDING','RUNNING_BUILDING','STARTING','APP_STARTING'): return 'waking'
    except httpx.HTTPError: pass
    return 'down'
