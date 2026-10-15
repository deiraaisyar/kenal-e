"""Build the reference package from aligned Kaggle exports, without unpickling."""
import argparse
import csv
import hashlib
import json
from pathlib import Path
import shutil

import numpy as np

from reference import normalize

EXPECTED_COUNTS = {0:246, 1:308, 2:22, 3:28, 4:46, 5:51, 6:40, 7:56, 8:101,
    9:298, 10:29, 11:28, 12:59, 13:374, 14:163, 15:104, 16:73, 17:126,
    18:143, 19:249, 20:341, 21:521, 22:64, 23:179, 24:83, 25:32, 26:197}


def build(vit_folder, dino_folder, labels_path, output):
    vf = np.load(vit_folder / "filenames.npy", allow_pickle=False)
    df = np.load(dino_folder / "filenames.npy", allow_pickle=False)
    if not np.array_equal(vf, df) or len(set(vf.tolist())) != len(vf):
        raise ValueError("Nama file cache tidak sinkron atau berulang.")
    vit = normalize(np.load(vit_folder / "embeddings.npy", allow_pickle=False))
    dino = normalize(np.load(dino_folder / "embeddings.npy", allow_pickle=False))
    if vit.shape != (len(vf), 768) or dino.shape != vit.shape:
        raise ValueError("Dimensi cache salah.")
    with labels_path.open(encoding="utf-8-sig", newline="") as handle:
        rows = list(csv.DictReader(handle))
    lookup = {row["filename"]: row for row in rows}
    if len(lookup) != len(rows) or set(lookup) != set(vf.tolist()):
        raise ValueError("CSV dan cache harus berisi nama file yang sama persis.")
    rows = [lookup[str(name)] for name in vf]
    macro = np.array([int(r["level1_macro_id"]) for r in rows])
    sub = np.array([int(r["level2_sub_id"]) for r in rows])
    groups = np.array([int(r["dup_group_id"]) for r in rows])
    counts = {int(m): int((macro == m).sum()) for m in np.unique(macro)}
    n_sub = len(set(zip(macro.tolist(), sub.tolist())))
    if counts != EXPECTED_COUNTS or n_sub != 88:
        raise ValueError("Label tidak cocok dengan run target: 27 macro termasuk noise, 88 subklaster.")
    # Leave duplicate groups out when measuring reference-neighbor similarity.
    thresholds, report = {}, {}
    for m in np.unique(macro):
        idx = np.flatnonzero(macro == m)
        scores = vit[idx] @ vit[idx].T
        scores[groups[idx, None] == groups[idx][None, :]] = -np.inf
        nearest = scores.max(axis=1)
        valid_groups = []
        for group in np.unique(groups[idx]):
            values = nearest[groups[idx] == group]
            values = values[np.isfinite(values)]
            if len(values):
                valid_groups.append(float(np.median(values)))
        threshold = float(np.quantile(valid_groups, .05)) if valid_groups else None
        thresholds[str(int(m))] = threshold
        report[str(int(m))] = {"rows": len(idx), "independent_groups": len(valid_groups),
                               "within_cluster_neighbor_p05": threshold}
    manifest = {"schema_version": "1.0", "rows": len(vf), "dimensions": 768,
        "macro_count_including_noise": len(counts), "subcluster_count": n_sub, "noise_id": 26,
        "label_source": "Kaggle script version 352645046 / level2_hierarchy/facets_level2.csv",
        "labels_sha256": hashlib.sha256(labels_path.read_bytes()).hexdigest(),
        "reference_thresholds": thresholds,
        "validation": "Reference-only heuristic; no out-of-domain or new-photo validation. Never a probability.",
        "processor_parity": "Pending comparison with Kaggle runtime; original library versions/revisions unavailable.",
        "reference_report": report}
    output.mkdir(parents=True, exist_ok=True)
    np.savez_compressed(output / "reference.npz", vit=vit, dinov3=dino,
                        macro=macro, sub=sub, dup_group=groups)
    (output / "manifest.json").write_text(json.dumps(manifest, indent=2)+"\n")
    shutil.copyfile(labels_path, output / "facets_level2.csv")
    return {"rows": len(vf), "macro_count_including_noise": len(counts), "subclusters": n_sub}


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--vit", type=Path, required=True)
    parser.add_argument("--dinov3", type=Path, required=True)
    parser.add_argument("--labels", type=Path, required=True)
    parser.add_argument("--output", type=Path, default=Path(__file__).parent / "artifacts")
    args = parser.parse_args()
    print(build(args.vit, args.dinov3, args.labels, args.output))
