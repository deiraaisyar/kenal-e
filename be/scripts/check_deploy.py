"""Fail the build early if required reference files are absent or misaligned."""
from be.config import ARTIFACTS, DATA
from be.inference import Gallery

def check():
    for folder,names in [(ARTIFACTS,('reference.npz','manifest.json','meta.json')),
                         (DATA,('gallery_meta.json','thresholds.json','meta.json','drop_points.json'))]:
        for name in names:
            if not (folder/name).is_file():
                raise FileNotFoundError(f'File deployment belum tersedia: {folder/name}')
    gallery=Gallery()
    assert len(gallery.vit)==3598, 'Jumlah referensi tidak sesuai run target.'
    assert len(gallery.catalog)==26, 'Jumlah kategori tidak sesuai run target.'
    assert gallery.vit.shape==gallery.dino.shape==(3598,768)
    print('Reference ready: 3598 unique images, 26 categories, ViT + DINOv3 vectors. No local model weights required.')

if __name__=='__main__': check()
