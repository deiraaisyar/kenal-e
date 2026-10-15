"""Lightweight nearest-reference baseline; scores are not probabilities."""
import json
from pathlib import Path

import numpy as np


def normalize(x):
    x = np.asarray(x, dtype=np.float32)
    norms = np.linalg.norm(x, axis=-1, keepdims=True)
    if not np.isfinite(x).all() or np.any(norms < 1e-8):
        raise ValueError("Embedding kosong atau tidak valid.")
    return x / norms


class ReferenceIndex:
    def __init__(self, folder):
        folder = Path(folder)
        self.manifest = json.loads((folder / "manifest.json").read_text())
        self.meta = json.loads((folder / "meta.json").read_text())
        with np.load(folder / "reference.npz", allow_pickle=False) as data:
            self.vit = normalize(data["vit"])
            self.dino = normalize(data["dinov3"])
            self.macro = data["macro"].astype(int)
            self.sub = data["sub"].astype(int)
        self.noise_id = int(self.manifest["noise_id"])
        if self.vit.shape != self.dino.shape or self.vit.shape[1] != 768:
            raise ValueError("Dimensi referensi tidak cocok.")
        if len(self.macro) != len(self.vit) or len(self.sub) != len(self.vit):
            raise ValueError("Jumlah label tidak cocok dengan referensi.")

    def match_macro(self, vector):
        similarities = self.vit @ normalize(vector)
        scores = [(int(m), float(similarities[self.macro == m].max()))
                  for m in np.unique(self.macro)]
        scores.sort(key=lambda pair: (-pair[1], pair[0]))
        macro, score = scores[0]
        threshold = self.manifest["reference_thresholds"].get(str(macro))
        unknown = macro == self.noise_id or threshold is None or score < threshold
        return {"macro_id": macro, "similarity": score,
                "margin": score - scores[1][1] if len(scores) > 1 else 0.0,
                "threshold": threshold, "unknown": unknown}

    def result(self, macro_match, dino_vector=None):
        base = {"schema_version": "1.0", "recognized": False,
                "status": "unknown", "category": None, "subcategory": None,
                "condition": None, "price": None,
                "validation": "reference_only_not_validated_on_new_photos"}
        if macro_match["unknown"]:
            return {**base, "message": "Tidak dikenali dengan cukup meyakinkan. Coba foto lain."}
        macro = macro_match["macro_id"]
        meta = self.meta.get(str(macro), {})
        candidate = {"id": macro, "name": meta.get("nama", f"Klaster {macro}"),
                     "similarity": macro_match["similarity"], "margin": macro_match["margin"]}
        sub_candidate = None
        if dino_vector is not None:
            indices = np.flatnonzero(self.macro == macro)
            scores = self.dino[indices] @ normalize(dino_vector)
            best = int(np.argmax(scores))
            sid = int(self.sub[indices[best]])
            sub_candidate = {"id": sid, "global_id": f"{macro}_{sid}",
                             "similarity": float(scores[best])}
        return {**base, "status": "needs_review", "category": candidate,
                "subcategory": sub_candidate,
                "message": "Kandidat berdasarkan kemiripan visual; perlu verifikasi. Kondisi dan harga belum dinilai."}
