# Kenal-E backend

FastAPI service for photo validation, the bridge to the `ayaayaa/still-e-okay-ai` Space, category decisions, and the catalog. It does not install PyTorch or run any model on the laptop.

Run from the repository root:

```bash
python3 -m venv be/.venv
be/.venv/bin/pip install -r be/requirements-dev.txt
be/.venv/bin/python -m uvicorn be.app:app --host 127.0.0.1 --port 8000 --reload
```

Set `HF_TOKEN` in the `.env` file at the root. It is read automatically. Optional variables are listed in `.env.example`. The token is never included in responses or exposed to the frontend.

API docs: http://127.0.0.1:8000/docs.

## Data and decisions

- Loads `reference.npz`, `manifest.json`, and category names from `meta.json`. By default it uses the deployment copy in `be/data/artifacts`; if that is missing, it falls back to `ai/artifacts`. The CSV is only needed when preparing metadata, not at deployment runtime.
- One representative per `dup_group` yields 3,598 independent images. Labels come from the 88-sub-cluster run CSV; the old image archive folders are not used as labels.
- ViT kNN with k=10 and cosine voting; macro centroids are used as a diagnostic; the nearest DINOv3 centroid within the macro cluster picks the sub-cluster. Small LEAF categories do not get a condition label.
- Noise and candidates below the initial neighbor threshold are stopped. That threshold is only a reference heuristic and has not been calibrated on new photos.
- `data/thresholds.json` has `calibrated=false`. Every candidate that passes is still `borderline`; do not change it to `true` without independent evaluation. The UI shows no confidence numbers.
- Initial risk metadata follows the user's specification table. All handling guidance is labeled draft. The risk for a closed laptop/laptop needs review against a battery that may still be installed.
- `data/meta.json` is a local per-ID override. Example structure: `{"13":{"info":{"verified":false},"price":{"mode":"none"}}}`. The legacy format uses `verified=true`, `show=true`, valid ranges, sources, and dates. The research `ranges` format is validated against the observations in `research_sources.json` (see the research metadata section below).
- `data/drop_points.json` is still empty. Only entries with a source and a verification date are shown.
- `/api/explain` returns `explain_unavailable`; the button stays hidden until the paper's method and the endpoint are available.

## Reference photos

Reference photos come from the public dataset `ayaayaa/kenal-e-thumbnails`, directory `images`, at commit `9800cac5b0554d5acfeb92d730e9791aee485a17`. All 3,961 file names were matched against `data/gallery_meta.json`, with no missing or duplicate names. The backend builds URLs from the file name that matches each vector, including encoding of spaces and special characters. The browser fetches images directly from HF; the backend does not download the whole dataset.

`REFERENCE_IMAGE_BASE_URL` can change the image location/revision; an empty value disables the remote image fallback. The images are currently at original resolution. The frontend loads reference images lazily. If you later create small thumbnails, put them in `data/thumbnails` and fill `data/thumbnail_manifest.json` with a mapping from reference file name to thumbnail name. Available local thumbnails take priority; thumbnail file names must not contain a path. Alternatively, upload the thumbnails to HF and change the base URL while keeping the file names.

## Uploads and privacy

JPG/PNG/WEBP up to 5 MB; the multipart body is limited; the format is checked with Pillow. Images are downscaled to at most 1024 px, converted to JPEG, and stripped of metadata before being forwarded. Backend temporary files are deleted in a `finally` block. The existing Gradio Space periodically cleans its upload cache, which is not a guarantee of no server-side storage. Cek Laci sessions are stored only on the user's device by the frontend.

## Tests

```bash
be/.venv/bin/python -m pytest be/tests -q
be/.venv/bin/python -m be.scripts.check_space
```

The API tests replace the encoder with reference vectors to test decision rules, validation, errors, and price withholding. `check_space` verifies the `/embed(photo, selected)` contract and `/health` of the live Space. The live contract returns `embeddings.vit` and `embeddings.dinov3`.

Implementation references: [FastAPI uploads](https://fastapi.tiangolo.com/tutorial/request-files/), [Gradio client](https://www.gradio.app/docs/python-client/client).

## Deploy to Render Free

The `render.yaml` configuration is at the root. Follow [DEPLOY_RENDER.md](DEPLOY_RENDER.md) for settings, the required NPZ/JSON files, and secrets. The backend keeps a single worker and a single NumPy thread to fit the 512 MB RAM budget. The `/api/ready` health check does not call the Space. A local memory test is available via `python -m be.scripts.profile_memory`.

Deployment URL provided by the user: `https://still-e-okay.onrender.com`. The production frontend uses this URL automatically, with `VITE_API_BASE_URL` as an override; add the active frontend origin to `CORS_ORIGINS` on Render.

### Catalog labels and filters

`data/catalog_facets.json` maps cluster IDs to `groups` (item type) and
`sizes` (visual size), based on Tables 3–4 of the project report (report/report.pdf). Noise ID
26 stays excluded from the catalog. Initial risk follows the handling metadata
(Table 5); IDs without a risk classification stay `unknown`. Sizes are labels
for reference groups, not dimension measurements of a new photo.

The `/api/taxonomy` list and detail endpoints include `facets`, with three arrays:
`groups`, `sizes`, and `risks`. One item can have several labels.
Extra labels can be set per ID in `data/meta.json`, for example:

```json
{"13":{"facets":{"groups":["internal"],"sizes":["small"],"risks":["valuable"]}}}
```

Use these type IDs: `office`, `household`, `computing`, `media`, `energy`, `internal`,
`mixed`; sizes `small`, `medium`, `large`, `unidentified`; risks `high`, `medium`,
`valuable`, `low`, `unknown`. Add labels only when there is data to back them.
`risk_level` in the handling guidance remains the primary risk, separate from
the filter labels. The frontend applies OR across selections within one dimension
and AND across dimensions; choosing "All" removes the restriction for that dimension.
Deploy the backend before the frontend so new labels are available immediately.


### Macro, micro, and price research metadata (audit of 18 October 2026)

`data/meta.json` now holds 27 macro and 88 micro clusters from the original CSV, including macro
26, which is kept for audit but still rejected before guidance/prices.
The catalog shows 26 macro clusters with 84 micro clusters. One micro cluster is one gallery row;
several micro clusters may share the same user-facing name. NPZ IDs and order
are unchanged. `reference_rows` covers the original CSV rows; `size` in the API response is
the number of references after deduplication.

Each macro cluster holds `name`, `description`, `proposal_facets`, `facets`, `info`,
`price`, and `subs` (an object keyed by local micro ID). The macro function/size/
risk categories follow Tables 3–5 of the semifinal report. IDs whose risk is not listed
stay `unknown`. Micro clusters have a name and description based on the sample audit, `needs_review`,
and the report category they came from. Guidance for every micro cluster is filled in. Visual
exceptions use their own category and price policy: for example 9_1 and 23_2
are laptops, while 21_4 and 24_1 are mixed, so the parent price is blocked.
These names or descriptions are not yet verified annotations of all members.

`subs.<id>.price_policy` controls how prices apply: `inherit` follows the parent,
`override` uses the micro cluster's own price, `blocked` stops inheritance.
`condition_tier` and `condition_factors` stay null: micro numbers, dark screens,
laptop lid position, and photo angle are not turned into function/price condition.
The Level 2 ARI in the report is 0.4142; condition factors have not been calibrated.

Prices use `mode: "ranges"` with `whole` (sold as a whole) and `scrap`.
Each can be null. Figures have `unit` (`item` or `kg`), `min`, `max`,
`basis`, `source_ids`, `observation_ids`, `accessed_on`, `requires_confirmation`,
`scope`, and `note`. The grade scope is shown right next to the price. Whole-item references are conditional on
comparable function and model; a photo does not prove function. PCB grade references are not
the result of grade detection. Min–max ranges come from selected samples, not a statistical interval,
a market average, or a transaction price. A single price keeps min=max.

`data/research_sources.json` stores sources, access/publication dates where
available, geographic scope, method, and 57 price observations. The three
collectors with listed prices are Kepul, Rongsok Bandung, and ALDI SCRAP; Prabu Recycle
is only a reference for units/method because it lists no figures. Purchase ads,
new products, non-comparable bundled items, and management service fees are not
used as whole-item prices. Some OLX ad details could not be opened; those
observations come from the title and price on the listing index, and the
limitation is recorded. There was no communication with or confirmation from sellers.

Prices have not been confirmed with Semarang collectors; there is no payment promise,
no verification of operator permits, and no check of item function. `info.verified` stays
false. An empty value does not mean the item has no resale value. Do not fill in prices
for mixed categories just to give every card a number.

`valid_price` checks the channel, unit, source, and whether the price bounds match the
stored observations. The legacy API/device-stored single-price format is still
supported. The frontend reads micro names/descriptions, uses the term visual group,
and shows both price channels with their source, access date, and estimate basis.
Deploy the backend and frontend together; there is no need to retrain the encoder or
regenerate reference.npz.

### Visual audit trail and evaluator

`data/cluster_audit_samples_2026-10-18.json` stores 423 files from 88 micro clusters
across 27 macro clusters. For each micro cluster it takes min(5, file count), with seed 20261018.
Sampling prioritizes distinct duplicate groups, then picks members at
random; if there are fewer than five unique groups, the slots are filled from other files. This is not
a simple random sample of all files and not a visual audit of all 3,961 images.

`data/cluster_audit_2026-10-18.json` holds per-photo observations, label changes,
report matching, and the reasons for thumbnail selection. `proposal_facets` keeps
the original Tables 3–5, while micro exceptions follow visual evidence. The difference
between the macro 23 title in Table 2 and the actual file is recorded rather than changing the ID.
`data/cluster_audit_evaluator_2026-10-18.json` is the independent evaluator's report,
which checked the 423 samples, 26 thumbnails, sources, and price inheritance. The final result is
a pass with no open findings; this does not verify item function/chemistry or transaction
prices. `info.verified` stays false.

To reproduce the samples and contact sheets from the repository root:

```bash
be/.venv/bin/python -m be.scripts.sample_cluster_audit --images-dir /path/to/1_Electronic --output-dir /tmp/kenal-audit --seed 20261018
```

`data/catalog_representatives.json` assigns one visually checked image
to each catalog macro cluster. The backend uses that full image for the detail view; the frontend
uses the local WebP produced by the generator. The visual groups in the detail view show
audit samples along with the effective guidance/price of each micro cluster.
