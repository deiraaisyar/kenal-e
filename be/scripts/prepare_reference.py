"""Copy the existing research artifacts into the deployable backend. No training."""
import argparse
import hashlib
from pathlib import Path
import shutil
from be.config import ROOT, BUNDLED_ARTIFACTS

FILES = ('reference.npz','manifest.json','meta.json')

def prepare(source,replace=False):
    source=Path(source)
    for name in FILES:
        if not (source/name).is_file(): raise FileNotFoundError(f'Artefak wajib tidak ada: {source/name}')
    BUNDLED_ARTIFACTS.mkdir(parents=True,exist_ok=True)
    for name in FILES:
        src,dest=source/name,BUNDLED_ARTIFACTS/name
        if dest.exists() and src.read_bytes()!=dest.read_bytes() and not replace:
            raise ValueError(f'{dest} berbeda. Gunakan --replace jika memang memperbarui referensi.')
        if src.resolve()!=dest.resolve(): shutil.copy2(src,dest)
        print(f'{name}: {dest.stat().st_size:,} bytes; sha256={hashlib.sha256(dest.read_bytes()).hexdigest()}')

if __name__=='__main__':
    p=argparse.ArgumentParser()
    p.add_argument('--source',type=Path,default=ROOT/'ai/artifacts')
    p.add_argument('--replace',action='store_true')
    args=p.parse_args()
    prepare(args.source,args.replace)
