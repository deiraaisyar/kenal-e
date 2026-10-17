from io import BytesIO
import numpy as np
import pytest
from fastapi.testclient import TestClient
from PIL import Image
from be.app import app, gallery
from be import space
from be.catalog import valid_price

@pytest.fixture(scope='module')
def client():
    with TestClient(app) as c: yield c

def photo():
    f=BytesIO();Image.new('RGB',(50,50),'white').save(f,'JPEG');return f.getvalue()

def test_catalog_is_unique_and_excludes_noise(client):
    rows=client.get('/api/taxonomy').json()
    assert len(rows)==26
    assert {r['id'] for r in rows}==set(range(26))
    assert len(gallery().vit)==3598
    assert next(r for r in rows if r['id']==13)['size']==356
    assert client.get('/api/taxonomy/26').status_code==404

def test_unknown_has_no_category_advice_or_price(client,monkeypatch):
    g=gallery();index=int(np.flatnonzero(g.macro==26)[0])
    monkeypatch.setattr(space,'embeddings',lambda data:(g.vit[index],g.dino[index]))
    r=client.post('/api/analyze',files={'image':('photo.jpg',photo(),'image/jpeg')})
    body=r.json();assert r.status_code==200
    assert body['status']=='out_of_reference'
    for key in ('macro','sub','info','price'): assert body[key] is None
    assert body['similar']==[]

def test_real_encoder_contract_is_adapted_without_claiming_validation(client,monkeypatch):
    g=gallery();index=int(np.flatnonzero(g.macro==13)[0])
    monkeypatch.setattr(space,'embeddings',lambda data:(g.vit[index].tolist(),g.dino[index].tolist()))
    body=client.post('/api/analyze',files={'image':('photo.png',photo(),'image/png')}).json()
    assert body['status']=='borderline'
    assert body['macro']['id']==13
    assert body['info']['verified'] is False
    assert body['price']['mode']=='ranges'
    assert body['price']['whole'] is None
    assert body['price']['scrap']['estimate_only'] is True
    assert body['sub']['name']=='Papan sirkuit dengan komponen terpasang'
    assert len(body['similar'])==5
    assert body['thresholds_calibrated'] is False

def test_invalid_images_are_rejected_before_calling_space(client,monkeypatch):
    def fail(*args): pytest.fail('invalid upload must not reach AI')
    monkeypatch.setattr(space,'embeddings',fail)
    r=client.post('/api/analyze',files={'image':('bad.jpg',b'not a photo','image/jpeg')})
    assert r.status_code==400 and r.json()['error']['code']=='invalid_image'
    r=client.post('/api/analyze',files={'image':('big.jpg',b'x'*(5*1024*1024+1),'image/jpeg')})
    assert r.status_code==413
    assert client.post('/api/analyze').status_code==422

def test_space_failure_is_structured_and_has_no_internal_error(client,monkeypatch):
    def unavailable(data):raise space.SpaceError('space_waking','Server AI sedang bangun.')
    monkeypatch.setattr(space,'embeddings',unavailable)
    r=client.post('/api/analyze',files={'image':('x.jpg',photo(),'image/jpeg')})
    assert r.status_code==503 and r.headers['retry-after']=='20'
    assert r.json()=={'error':{'code':'space_waking','message':'Server AI sedang bangun.'}}

def test_embedding_vectors_are_checked(client,monkeypatch):
    monkeypatch.setattr(space,'embeddings',lambda data:([float('nan')]*768,[0]*768))
    r=client.post('/api/analyze',files={'image':('x.jpg',photo(),'image/jpeg')})
    assert r.status_code==502

def test_drop_points_and_explain_fallback(client):
    assert client.get('/api/drop-points?city=Yogyakarta').json()==[]
    assert client.post('/api/explain').json()['error']['code']=='explain_unavailable'

def test_unverified_or_unsourced_prices_are_never_shown():
    info={'assessable':True}
    price={'mode':'per_kg','min':100,'max':200,'show':True,'verified':False,'source':'owner','source_date':'2026-10-16'}
    assert valid_price(price,info)=={'mode':'none'}
    price['verified']=True
    assert valid_price(price,info)['weight_input'] is True
    assert valid_price({**price,'source':''},info)=={'mode':'none'}
    assert valid_price({**price,'min':300},info)=={'mode':'none'}
    assert valid_price(price,{'assessable':False})=={'mode':'none'}

def test_demo_is_explicitly_labeled(client):
    body=client.get('/api/demo').json()
    assert body['demo'] is True and body['macro']['id']==13

def test_render_health_probe_never_calls_huggingface(client,monkeypatch):
    def fail(): pytest.fail('readiness probe must not call an external service')
    monkeypatch.setattr(space,'health',fail)
    assert client.get('/api/ready').json()=={'backend':'ok','reference_ready':True}

def test_busy_upload_is_rejected_before_image_decode(client,monkeypatch):
    import importlib
    module=importlib.import_module('be.app')
    def fail(*args): pytest.fail('a busy backend must not decode another image')
    monkeypatch.setattr(module,'sanitized_photo',fail)
    class BusyLock:
        def locked(self): return True
    original=app.state.inference_lock
    app.state.inference_lock=BusyLock()
    try:
        r=client.post('/api/analyze',files={'image':('x.jpg',photo(),'image/jpeg')})
        assert r.status_code==429 and r.json()['error']['code']=='busy'
    finally: app.state.inference_lock=original

def test_photo_resize_preserves_orientation_and_removes_exif():
    from be.app import sanitized_photo
    source=BytesIO()
    image=Image.new('RGB',(2000,1000),'red')
    exif=Image.Exif();exif[274]=6;exif[305]='private-metadata'
    image.save(source,'JPEG',exif=exif);image.close()
    result=sanitized_photo(source.getvalue())
    with Image.open(BytesIO(result)) as photo:
        assert photo.size==(512,1024)
        assert photo.mode=='RGB'
        assert not photo.getexif()
