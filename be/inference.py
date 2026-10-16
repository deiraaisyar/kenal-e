import json
from pathlib import Path
from urllib.parse import quote
import numpy as np
from .config import ARTIFACTS, DATA, REFERENCE_IMAGE_BASE_URL
from .catalog import load_catalog

def normalized(values):
    values = np.asarray(values, dtype=np.float32)
    norm = np.linalg.norm(values, axis=-1, keepdims=True)
    if not np.isfinite(values).all() or np.any(norm < 1e-8):
        raise ValueError('Embedding tidak valid.')
    return values / norm

class Gallery:
    def __init__(self, artifacts=ARTIFACTS):
        artifacts = Path(artifacts)
        self.manifest = json.loads((artifacts/'manifest.json').read_text())
        self.thresholds = json.loads((DATA/'thresholds.json').read_text())
        self.catalog = load_catalog()
        with np.load(artifacts/'reference.npz', allow_pickle=False) as z:
            _, indices = np.unique(z['dup_group'], return_index=True)
            indices.sort()
            self.vit = normalized(z['vit'][indices])
            self.dino = normalized(z['dinov3'][indices])
            self.macro = z['macro'][indices].astype(int)
            self.sub = z['sub'][indices].astype(int)
        rows = json.loads((DATA/'gallery_meta.json').read_text())
        if len(rows) != self.manifest['rows']:
            raise ValueError('Metadata nama file tidak sesuai dengan referensi.')
        for j,i in enumerate(indices):
            if rows[int(i)]['macro'] != int(self.macro[j]) or rows[int(i)]['sub'] != int(self.sub[j]):
                raise ValueError('Urutan metadata galeri tidak sesuai dengan referensi.')
        self.filenames = [rows[int(i)]['filename'] for i in indices]
        self.centroids = {int(mid):normalized(self.vit[self.macro == mid].mean(axis=0)) for mid in np.unique(self.macro)}
        self.subcentroids = {}
        for mid, entry in self.catalog.items():
            subsets = []
            for sid in np.unique(self.sub[self.macro == mid]):
                mask = (self.macro == mid) & (self.sub == sid)
                self.subcentroids[mid,int(sid)] = normalized(self.dino[mask].mean(axis=0))
                subsets.append({'id':int(sid),'size':int(mask.sum()),'rep_urls':[]})
            entry['subs'] = subsets
            entry['n_sub'] = len(subsets)
        # Local thumbnails can override the public HF reference-image URLs.
        self.thumbs = json.loads((DATA/'thumbnail_manifest.json').read_text()) if (DATA/'thumbnail_manifest.json').exists() else {}
        for mid, entry in self.catalog.items():
            idx = np.flatnonzero(self.macro == mid)
            urls = [self.thumbnail(i) for i in idx if self.thumbnail(i)]
            entry['thumb_url'] = urls[0] if urls else None
            for sub in entry['subs']:
                sub['rep_urls'] = [self.thumbnail(i) for i in idx if self.sub[i] == sub['id'] and self.thumbnail(i)][:3]

    def thumbnail(self, index):
        name = self.thumbs.get(self.filenames[index])
        if name and Path(name).name == name and (DATA/'thumbnails'/name).is_file():
            return '/api/thumbnails/' + quote(name, safe='')
        if REFERENCE_IMAGE_BASE_URL:
            return REFERENCE_IMAGE_BASE_URL + '/' + quote(self.filenames[index], safe='')
        return None

    def analyze(self, vit, dino):
        v, d = normalized(vit), normalized(dino)
        if v.shape != (768,) or d.shape != (768,): raise ValueError('Dimensi embedding tidak sesuai.')
        scores = self.vit @ v
        top = np.argsort(-scores, kind='stable')[:10]
        labels, votes = np.unique(self.macro[top], return_counts=True)
        candidates = sorted(zip(labels, votes), key=lambda pair:(-pair[1], -float(scores[top][self.macro[top] == pair[0]].max()), int(pair[0])))
        mid, count = (int(x) for x in candidates[0])
        score = float(scores[self.macro == mid].max())
        floor = self.manifest['reference_thresholds'].get(str(mid))
        base = {'taxonomy_version':'progress-21','disclaimer':'Hasil berdasarkan kemiripan visual, bukan diagnosis.', 'thresholds_calibrated':bool(self.thresholds['calibrated'])}
        if mid == 26 or floor is None or score < floor:
            return {**base,'status':'out_of_reference','macro':None,'sub':None,'info':None,'price':None,'similar':[]}
        share = count/len(top)
        centroid_sim = float(self.centroids[mid] @ v)
        status = 'borderline'
        if self.thresholds['calibrated'] and share >= self.thresholds['in_reference_vote_share'] and centroid_sim >= self.thresholds['in_reference_centroid_sim']:
            status = 'in_reference'
        entry = self.catalog[mid]
        sub = None
        if entry['size'] >= 30 and entry['n_sub'] > 1:
            sid, sim = max(((sid,float(centroid @ d)) for (m,sid),centroid in self.subcentroids.items() if m == mid), key=lambda x:x[1])
            sub = {'id':sid,'label':f'Kelompok kondisi {sid}','name':None,'sim':sim}
        indices = np.flatnonzero(self.macro == mid)
        sims = self.dino[indices] @ d
        similar = [{'url':self.thumbnail(int(indices[i])),'macro':mid,'sub':int(self.sub[indices[i]]),'sim':float(sims[i])} for i in np.argsort(-sims,kind='stable')[:5]]
        return {**base,'status':status,'macro':{'id':mid,'name':entry['name'],'vote_share':share,'centroid_sim':centroid_sim},'sub':sub,'info':entry['info'],'price':entry['price'],'similar':similar}

    def demo(self):
        index = int(np.flatnonzero(self.macro == 13)[0])
        return {**self.analyze(self.vit[index],self.dino[index]),'demo':True,'demo_note':'Contoh dari vektor referensi; bukan analisis foto baru.'}
