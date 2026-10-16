from contextlib import asynccontextmanager
from functools import lru_cache
from io import BytesIO
import asyncio
import json
import warnings

from fastapi import FastAPI, UploadFile, File, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from starlette.concurrency import run_in_threadpool
from PIL import Image, ImageOps, UnidentifiedImageError

from .config import DATA, ORIGINS
from .inference import Gallery
from . import space

MAX_FILE = 5 * 1024 * 1024
MAX_BODY = MAX_FILE + 64 * 1024
Image.MAX_IMAGE_PIXELS = 25_000_000

@lru_cache(maxsize=1)
def gallery(): return Gallery()

@asynccontextmanager
async def lifespan(app):
    await run_in_threadpool(gallery)
    app.state.inference_lock = asyncio.Lock()
    yield

app = FastAPI(title='Kenal-E API',version='0.1.0',lifespan=lifespan)
app.add_middleware(CORSMiddleware,allow_origins=ORIGINS,allow_methods=['GET','POST'],allow_headers=['Content-Type'])

def error(code,message,status=400,headers=None):
    return JSONResponse({'error':{'code':code,'message':message}},status_code=status,headers=headers)

class BodyTooLarge(Exception): pass

class UploadLimit:
    def __init__(self, app): self.app = app
    async def __call__(self,scope,receive,send):
        if scope['type'] != 'http': return await self.app(scope,receive,send)
        length = dict(scope.get('headers',[])).get(b'content-length',b'0')
        try: oversized = int(length) > MAX_BODY
        except ValueError: oversized = True
        if oversized: return await error('too_large','Foto maksimal 5 MB.',413)(scope,receive,send)
        total = 0
        async def limited_receive():
            nonlocal total
            message = await receive()
            total += len(message.get('body',b''))
            if total > MAX_BODY: raise BodyTooLarge()
            return message
        await self.app(scope,limited_receive,send)

app.add_middleware(UploadLimit)

@app.exception_handler(BodyTooLarge)
async def oversized(request,exc): return error('too_large','Foto maksimal 5 MB.',413)

@app.exception_handler(RequestValidationError)
async def validation(request,exc): return error('invalid_image','Unggah foto melalui field image.',422)

def sanitized_photo(content):
    try:
        with warnings.catch_warnings():
            warnings.simplefilter('error',Image.DecompressionBombWarning)
            with Image.open(BytesIO(content)) as source:
                if source.format not in ('JPEG','PNG','WEBP'): raise ValueError()
                # JPEG can decode at a reduced resolution. Other formats still
                # shrink before EXIF copies and RGB conversion allocate buffers.
                source.draft('RGB',(1024,1024))
                source.thumbnail((1024,1024),Image.Resampling.LANCZOS,reducing_gap=3.0)
                with ImageOps.exif_transpose(source) as oriented:
                    with oriented.convert('RGB') as image:
                        out = BytesIO()
                        image.save(out,'JPEG',quality=85)
                        return out.getvalue()
    except (UnidentifiedImageError,OSError,ValueError,Image.DecompressionBombError,Image.DecompressionBombWarning):
        raise ValueError('Gunakan foto JPG, PNG, atau WEBP yang dapat dibuka.') from None

@app.post('/api/analyze')
async def analyze(image: UploadFile = File(...)):
    if app.state.inference_lock.locked():
        await image.close()
        return error('busy','Ada foto lain yang sedang diproses. Coba lagi sebentar.',429,{'Retry-After':'10'})
    async with app.state.inference_lock:
        try: content = await image.read(MAX_FILE+1)
        finally: await image.close()
        if len(content) > MAX_FILE: return error('too_large','Foto maksimal 5 MB.',413)
        try: photo = await run_in_threadpool(sanitized_photo,content)
        except ValueError as exc: return error('invalid_image',str(exc))
        del content
        try:
            vit,dino = await run_in_threadpool(space.embeddings,photo)
            return await run_in_threadpool(gallery().analyze,vit,dino)
        except space.SpaceError as exc: return error(exc.code,exc.message,exc.status,{'Retry-After':'20'} if exc.status==503 else None)
        except (ValueError,KeyError,TypeError): return error('invalid_response','Respons layanan AI belum sesuai. Coba lagi sebentar.',502)

@app.get('/api/taxonomy')
def taxonomy():
    return [{k:v for k,v in entry.items() if k not in ('info','price','subs')} for entry in gallery().catalog.values()]

@app.get('/api/taxonomy/{macro_id}')
def category(macro_id:int):
    entry = gallery().catalog.get(macro_id)
    return entry if entry else error('not_found','Kategori tidak ditemukan.',404)

@app.get('/api/demo')
def demo(): return gallery().demo()

@app.get('/api/drop-points')
def drop_points(city:str=''):
    points = json.loads((DATA/'drop_points.json').read_text())
    return [p for p in points if p.get('verified_on') and p.get('source') and (not city or p['city'].casefold()==city.strip().casefold())]

@app.get('/api/health')
async def health():
    diagnostic = await run_in_threadpool(space.runtime_status)
    return {'backend':'ok','space':diagnostic['state'],
            'space_diagnostic':{key:value for key,value in diagnostic.items() if key != 'state'},
            'recognition_validated':False,'feature_explain':False}

@app.get('/api/ready')
def ready():
    # Render health probes must not wait for or repeatedly call Hugging Face.
    return {'backend':'ok','reference_ready':True}

@app.post('/api/explain')
def explain(): return error('explain_unavailable','Peta perhatian belum tersedia.',501)

app.mount('/api/thumbnails',StaticFiles(directory=DATA/'thumbnails',check_dir=False),name='thumbnails')
