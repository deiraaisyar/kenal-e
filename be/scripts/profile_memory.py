"""Linux memory smoke check. Uses reference vectors, not a new HF inference."""
import os

# Set these before importing NumPy/OpenBLAS or the application.
for key in ('OPENBLAS_NUM_THREADS','OMP_NUM_THREADS'): os.environ.setdefault(key,'1')

import json
from pathlib import Path
import resource
import subprocess
import sys
import tempfile
from fastapi.testclient import TestClient
from PIL import Image
from be.app import app,gallery
from be import space

def rss_mib():
    lines=Path('/proc/self/status').read_text().splitlines()
    return round(int(next(x.split()[1] for x in lines if x.startswith('VmRSS:')))/1024,1)

def profile(paths):
    with TestClient(app) as client:
        startup=rss_mib()
        g=gallery()
        index=next(i for i,m in enumerate(g.macro) if m==13)
        space.embeddings=lambda content:(g.vit[index],g.dino[index])
        # Fixtures are generated in the parent, outside the measured worker.
        samples=[]
        for path in paths:
            payload=Path(path).read_bytes()
            response=client.post('/api/analyze',files={'image':(Path(path).name,payload,'application/octet-stream')})
            assert response.status_code==200,response.text
            assert response.json()['macro']['id']==13
            samples.append({'format':Path(path).suffix,'rss_mib':rss_mib()})
        result={'startup_rss_mib':startup,'after_requests_rss_mib':rss_mib(),
                'peak_rss_mib':round(resource.getrusage(resource.RUSAGE_SELF).ru_maxrss/1024,1),
                'image_pixels':25_000_000,'samples':samples,'inference':'mocked with reference vectors; HF network not called',
                'limit_mib':512,'environment':'local Linux; not a Render production measurement'}
        print(json.dumps(result,indent=2))
        if result['peak_rss_mib']>=450:
            raise SystemExit('Peak above the 450 MiB target; investigate before deploying on 512 MB.')

if __name__=='__main__':
    if len(sys.argv)>1 and sys.argv[1]=='--worker':
        profile(sys.argv[2:])
    else:
        with tempfile.TemporaryDirectory(prefix='kenal-e-memory-') as directory:
            paths=[]
            for mode,extension,color in [('RGB','jpg','white'),('RGBA','png',(120,160,100,180))]:
                path=Path(directory)/('large-test.'+extension)
                with Image.new(mode,(5000,5000),color) as image: image.save(path)
                paths.append(str(path))
            subprocess.run([sys.executable,'-m','be.scripts.profile_memory','--worker',paths[0],paths[0],paths[0],paths[1]],check=True)
