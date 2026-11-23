---
title: Still E-Okay AI
emoji: ♻️
colorFrom: green
colorTo: blue
sdk: gradio
sdk_version: 6.30.0
python_version: "3.12"
app_file: app.py
suggested_hardware: zero-a10g
models:
  - google/vit-base-patch16-224-in21k
  - facebook/dinov3-vitb16-pretrain-lvd1689m
---

# Still E-Okay AI

Gradio Space for the e-waste encoders and category candidates. The private Space is running at
[ayaayaa/still-e-okay-ai](https://huggingface.co/spaces/ayaayaa/still-e-okay-ai).
Open it with the HF account `ayaayaa`. You don't need to run the app or install Torch locally.
The private API needs a token from a user with access to the Space.

## Contents

- `app.py`: Gradio page and the `embed`, `predict`, `health` API.
- `encoder.py`: ViT-Base for Level 1, DINOv3 with four TTA views for Level 2. No DINOv2.
- `reference.py`: nearest-reference baseline for category and sub-cluster candidates.
- `prepare_artifacts.py`: validates the Kaggle export and builds the reference package.
- `artifacts/`: 3,961 reference images, 27 macro clusters (including noise), 88 sub-clusters, metadata.
- `tests/`: tests for preprocessing, normalization, and candidate/unknown output.

## Deploy to Hugging Face

1. Create a Gradio Space named `still-e-okay-ai` under the `ayaayaa` account.
2. Pick **ZeroGPU** hardware if available. `suggested_hardware` above is only a hint;
   it does not enable a GPU or change billing.
3. Upload the **contents of this folder to the Space root**: `README.md`, `requirements.txt`,
   `app.py`, `encoder.py`, `reference.py`, and the `artifacts` folder.
   `dist/still-e-okay-space.zip` has this structure; extract it and upload the contents.
   Don't upload the ZIP in place of the app files.
4. Under Settings → Variables and secrets, add a **Secret** `HF_TOKEN` from an account
   that has DINOv3 access. Use a read token with access to that model.
   Never put the token in code or the frontend. It is only for loading weights;
   user authentication and ZeroGPU quota are separate.
5. When the build shows Running, check `health`, then try a photo on the Space page.
   If the model fails to load, check the token/access/revision in the logs. There is no DINOv2 fallback.

Free ZeroGPU has a queue and a quota. If the ZeroGPU option doesn't appear on your account,
check eligibility in the HF UI. Don't pick paid hardware automatically.

## API

```python
from gradio_client import Client, handle_file

client = Client("ayaayaa/still-e-okay-ai")  # once the Space is published
status = client.predict(api_name="/health")
embedding = client.predict(handle_file("photo.jpg"), "dinov3", api_name="/embed")
both = client.predict(handle_file("photo.jpg"), "both", api_name="/embed")
candidate = client.predict(handle_file("photo.jpg"), api_name="/predict")
```

`embed` returns a 768-dimensional vector per encoder. `dinov3` runs only DINOv3,
`vit` only ViT, `both` runs both. Models load once at startup.
The four DINOv3 views are the original, a horizontal flip, and rotations of ±10° (BICUBIC, gray fill).
The CLS token of each view is L2-normalized, averaged, then normalized again.
Input limit: 12 MB / 20 megapixels.

`predict` returns `unknown` or `needs_review`. Candidates carry the category ID/name,
sub-cluster ID, and cosine similarity. **Similarity is not a probability.** `recognized`
stays false until recognition is validated; `condition` and `price` are always null.
No price or condition label is guessed from a sub-cluster number.

## Validation limits

This is an inference layer on top of the notebook's final labels. It does not re-run
UMAP/HDBSCAN or the recursive split/merge. Level 1 candidates use the nearest
reference neighbors in ViT space; Level 2 candidates use DINOv3 inside the chosen macro cluster.
The noise group competes at Level 1. The per-macro threshold is the 5th percentile of
neighbor similarity within the macro cluster, with all of the query's duplicate group excluded;
each group contributes one median. This is a **reference heuristic**, not an OOD calibration.

Weight revisions and the deployment package version are pinned. The processor/library versions
from Kaggle are not in the export, so matching the cached embeddings has to be
shown with the same source images. Before enabling the recognized status or prices:
compare against the original embeddings, test new photos and out-of-category photos,
separate duplicate groups during evaluation, then measure false accept/reject rates.

Labels come from Kaggle script version `352645046`. The downloaded file
`facets_level2.txt` turned out to be a valid CSV and was copied as `facets_level2.csv`.
The old gallery archive with 77 sub-clusters is not used for labels.
Name metadata comes from the notebook mapping where the macro member counts match;
a matching member count alone does not prove that every semantic annotation is correct.

## Local

Use Python 3.12 in a virtual environment. On CPU, install PyTorch CPU first:

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install torch==2.8.0 torchvision==0.23.0 --index-url https://download.pytorch.org/whl/cpu
pip install -r requirements.txt
hf auth login
python app.py
```

The interactive login stores credentials locally so models load without writing the token
into source. Without CUDA/ZeroGPU the encoder runs on CPU. You don't need a separate
FastAPI server; Gradio ships its own.

```bash
python -m unittest discover -s tests -v
PYTHONPATH=. python tests/smoke_api.py
```

To rebuild the reference, pass the label file as `.csv` or `.txt`:

```bash
python prepare_artifacts.py --vit /path/embeddings_vit_macro \
  --dinov3 /path/embeddings_dinov3_tta4v --labels /path/facets_level2.csv
```

Reference binaries and CSVs are ignored by Git so they aren't pushed by accident;
still include `artifacts/reference.npz`, `manifest.json`, and `meta.json` when
deploying. `facets_level2.csv` is only for local audit; the Space doesn't need it.

## Local verification, 15 October 2026

- Nine unit tests pass.
- File upload, `/health`, `/embed`, and `/predict` pass through the Gradio client
  with a fake encoder used only in tests.
- The processor → model → CLS → TTA flow produces 768-dimensional, norm-1 vectors
  for ViT and DINOv3 with a one-layer random-weight model (compatibility test).
- `pip check` passes. The local API was shut down after testing.
- The private ZeroGPU deploy `ayaayaa/still-e-okay-ai` works. The `health` endpoint is ready;
  `embed` with pretrained ViT and DINOv3 weights returns 768 dimensions
  with norm 1 for each. `predict` returns `unknown` for a plain synthetic image.
  The server test summary is in `remote_verification.json`. This is an integration test,
  not an accuracy measurement or proof that embeddings match the Kaggle cache.
- The notebook log shows the ViT processor using PIL/slow. The deployment pins the
  PIL backend for ViT and torchvision for DINOv3; numerical agreement with the cache
  still needs to be checked with source photos and the Kaggle runtime.
