# Deploy the Kenal-E API to Render Free

The frontend stays on Vercel; the encoder stays on Hugging Face. Render only runs FastAPI, NumPy vector search, and JSON lookups. It does not install PyTorch, Transformers, or model weights.

## Files that must be in Git

- `render.yaml`, `be/requirements.txt`, and the `be/` code.
- `be/data/artifacts/reference.npz` (about 21.5 MiB), `manifest.json`, `meta.json`.
- `be/data/gallery_meta.json`, `thresholds.json`, `meta.json`, `drop_points.json`.
- `be/data/thumbnails/.gitkeep` for the thumbnail directory, which is currently empty.

The NPZ in `ai/artifacts` is ignored by Git. The deployment copy intentionally lives in `be/data/artifacts` so it can be committed. This copy is already prepared; do not commit `.env` or `.venv`.

To prepare it again from the existing research output, run from the root:

```bash
be/.venv/bin/python -m be.scripts.prepare_reference
be/.venv/bin/python -m be.scripts.check_deploy
```

Use `--replace` on the first command only if you deliberately replace the reference with a new run that matches the metadata. No training or re-clustering is involved.

## Create the service

Use **New → Blueprint** and choose this repo to read `render.yaml`, or create a **New → Web Service** manually:

| Setting | Value |
| --- | --- |
| Name | `kenal-e-api` |
| Language | Python 3 |
| Root Directory | Empty, use the repo root |
| Region | Singapore |
| Instance Type | Free |
| Build Command | `pip install -r be/requirements.txt && python -m be.scripts.check_deploy` |
| Start Command | `uvicorn be.app:app --host 0.0.0.0 --port $PORT --workers 1 --limit-concurrency 8` |
| Health Check Path | `/api/ready` |

Environment variables:

| Name | Value |
| --- | --- |
| `HF_TOKEN` | The token already in `.env`, entered as a Render secret |
| `HF_SPACE_ID` | `ayaayaa/still-e-okay-ai` |
| `CORS_ORIGINS` | `https://kenal-e.vercel.app`; add local origins if needed, comma-separated and without a trailing slash |
| `PYTHON_VERSION` | `3.12.12` |
| `AI_TIMEOUT_SECONDS` | `180` |
| `OPENBLAS_NUM_THREADS` | `1` |
| `OMP_NUM_THREADS` | `1` |
| `MALLOC_ARENA_MAX` | `2` |

The Blueprint asks for the `HF_TOKEN` value at creation; `CORS_ORIGINS` already contains the frontend domain and local origins. If you create the service manually, fill in all the settings above. `/api/ready` only checks backend readiness; `/api/health` also checks the Space status.

Backend deployment: `https://still-e-okay.onrender.com`. Check `/api/ready`, `/api/taxonomy`, and `/docs`. The production frontend uses this URL by default. If Vercel already has `VITE_API_BASE_URL`, set it to this URL or remove the old override, then redeploy the frontend. Never give the frontend the HF token.

## RAM and temporary data

Render Free provides 512 MB of RAM. Use a single worker; each extra worker loads another copy of the gallery. Photo reading/decoding and analysis are serialized; other requests get `busy`. Uvicorn is capped at 8 concurrent connections/tasks to reduce upload pile-up. NumPy/OpenBLAS is limited to one thread.

For local measurement:

```bash
OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 MALLOC_ARENA_MAX=2 be/.venv/bin/python -m be.scripts.profile_memory
```

This test measures a local Linux process with a 25-megapixel image and reference vectors standing in for the HF call. It is not a guarantee of RAM on Render; monitor the metrics after deployment.

A free service sleeps after 15 minutes without traffic and wakes in about a minute on the next request. Temporary upload/cache files can be lost on restart, so the NPZ and JSON must come from the deployment/repo. Cek Laci stays on the user's device.

Additional metadata can be filled in later through `be/data/meta.json` and `drop_points.json`, then committed and redeployed. No new embeddings are needed to update prices or locations. Empty prices/locations and uncalibrated thresholds stay marked as they are today.

References: [FastAPI on Render](https://render.com/docs/deploy-fastapi), [Free instances](https://render.com/docs/free), [Compute plans](https://render.com/docs/compute-plans).

## Diagnosing the AI connection

`/api/ready` only checks the backend and the reference. For the HF connection, open `/api/health`:

- `space_diagnostic.token_configured`: whether the token is available in the Render process (its value is not shown).
- `hf_http_status` 401/403: HF access was denied; check the token and Space permissions. 404 can also mean the Space is private or the ID is wrong.
- `reason` `network_timeout`/`network_error`: the network connection to HF failed; this is separate from a token problem.
- `stage` `RUNNING` and `space` `running`: the Space is reachable. Later inference failures are logged with the exception type in the Render log, without the token contents.

Environment changes need a restart/redeploy. The secret name must be `HF_TOKEN`, and its value must be only the token: not `HF_TOKEN=...`, no `Bearer` prefix, and no quotes. `HF_SPACE_ID` is `ayaayaa/still-e-okay-ai`; a full HF URL is also normalized by the backend.

## Reference images from the HF Dataset

The public dataset `ayaayaa/kenal-e-thumbnails` is already linked to the 3,961 reference file names. The default `REFERENCE_IMAGE_BASE_URL`:

```text
https://huggingface.co/datasets/ayaayaa/kenal-e-thumbnails/resolve/9800cac5b0554d5acfeb92d730e9791aee485a17/images
```

Redeploy the backend to enable image URLs in the catalog, group details, and the five nearest references. There is no need to upload a new NPZ or put a token in the frontend for public images. The frontend code lazy-loads reference images. The uploaded images are currently originals, so thumbnail versions can still be created later.
