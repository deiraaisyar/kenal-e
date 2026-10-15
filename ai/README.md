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

Gradio Space untuk encoder dan kandidat kategori e-waste. Space privat sudah berjalan di
[ayaayaa/still-e-okay-ai](https://huggingface.co/spaces/ayaayaa/still-e-okay-ai).
Buka dengan akun HF `ayaayaa`. Laptop tidak perlu menjalankan app atau memasang Torch.
API privat membutuhkan token pengguna yang memiliki akses Space.

## Isi

- `app.py`: halaman Gradio dan API `embed`, `predict`, `health`.
- `encoder.py`: ViT-Base Level 1, DINOv3 Level 2 dengan empat view TTA; tanpa DINOv2.
- `reference.py`: baseline nearest-reference untuk kandidat kategori dan subklaster.
- `prepare_artifacts.py`: validasi ekspor Kaggle dan pembuatan paket referensi.
- `artifacts/`: referensi 3.961 citra, 27 macro termasuk noise, 88 subklaster, metadata.
- `tests/`: pengujian preprocessing, normalisasi, dan keluaran kandidat/tidak dikenal.

## Deploy ke Hugging Face

1. Buat Space Gradio bernama `still-e-okay-ai` di akun `ayaayaa`.
2. Pilih hardware **ZeroGPU** jika tersedia. `suggested_hardware` di atas hanya saran;
   tidak otomatis mengaktifkan GPU atau mengubah billing.
3. Upload **isi folder ini ke root Space**: `README.md`, `requirements.txt`,
   `app.py`, `encoder.py`, `reference.py`, dan folder `artifacts`.
   Paket `dist/still-e-okay-space.zip` berisi struktur ini; ekstrak lalu upload isinya.
   Jangan upload ZIP sebagai pengganti file aplikasi.
4. Di Settings → Variables and secrets, tambahkan **Secret** `HF_TOKEN` milik akun
   yang sudah memperoleh akses DINOv3. Gunakan token read dengan akses model tersebut.
   Jangan menaruh token dalam kode atau frontend. Token ini untuk memuat bobot;
   autentikasi pengguna/kuota ZeroGPU adalah hal terpisah.
5. Setelah build berstatus Running, cek `health`, lalu coba foto di halaman Space.
   Jika model gagal dimuat, periksa token/akses/revisi di log; tidak ada fallback DINOv2.

Free ZeroGPU memiliki antrean dan kuota. Bila pilihan ZeroGPU tidak muncul pada akun,
cek kelayakan melalui UI HF; jangan memilih hardware berbayar secara otomatis.

## API

```python
from gradio_client import Client, handle_file

client = Client("ayaayaa/still-e-okay-ai")  # setelah Space berhasil dipublikasikan
status = client.predict(api_name="/health")
embedding = client.predict(handle_file("foto.jpg"), "dinov3", api_name="/embed")
both = client.predict(handle_file("foto.jpg"), "both", api_name="/embed")
candidate = client.predict(handle_file("foto.jpg"), api_name="/predict")
```

`embed` menghasilkan vektor 768 dimensi per encoder. Pilihan `dinov3` hanya
menjalankan DINOv3; `vit` hanya ViT; `both` keduanya. Model dimuat sekali saat startup.
Empat view DINOv3 adalah asli, flip horizontal, rotasi ±10° (BICUBIC, gray fill).
Token CLS tiap view dinormalisasi L2, dirata-ratakan, lalu dinormalisasi lagi.
Input maksimal 12 MB / 20 megapiksel.

`predict` mengembalikan `unknown` atau `needs_review`. Kandidat berisi ID/nama kategori,
ID subklaster, dan cosine similarity. **Similarity bukan probabilitas.** `recognized`
tetap false sampai pengenalan divalidasi; `condition` dan `price` selalu null.
Tidak ada angka harga atau label kondisi yang ditebak dari nomor subklaster.

## Batas validasi

Ini lapisan inferensi tambahan atas label final notebook, bukan eksekusi ulang
UMAP/HDBSCAN beserta recursive split/merge. Kandidat Level 1 memakai tetangga
referensi terdekat di ruang ViT; kandidat Level 2 memakai DINOv3 dalam macro terpilih.
Kelompok noise ikut bersaing di Level 1. Ambang per macro berasal dari persentil 5
similarity tetangga dalam macro dengan seluruh grup duplikat query dikeluarkan;
setiap grup menyumbang satu median. Ini **heuristik referensi**, bukan kalibrasi OOD.

Revisi bobot dan versi paket deployment dikunci. Versi processor/library dari
Kaggle tidak tersedia dalam ekspor, sehingga kesamaan embedding dengan cache perlu
dibuktikan menggunakan gambar sumber yang sama. Sebelum status dikenali/harga
diaktifkan: bandingkan embedding asli, uji foto baru dan foto di luar kategori,
pisahkan grup duplikat saat evaluasi, lalu ukur tingkat salah terima/tolak.

Label bersumber dari output Kaggle script version `352645046`. File unduhan
`facets_level2.txt` ternyata CSV valid dan disalin sebagai `facets_level2.csv`.
Arsip galeri lama dengan 77 subklaster tidak digunakan untuk label.
Metadata nama berasal dari mapping notebook dengan jumlah anggota macro yang cocok;
pengecekan jumlah anggota saja tidak membuktikan kebenaran seluruh anotasi semantik.

## Lokal

Gunakan Python 3.12 dalam virtual environment. Untuk CPU, install PyTorch CPU dahulu:

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install torch==2.8.0 torchvision==0.23.0 --index-url https://download.pytorch.org/whl/cpu
pip install -r requirements.txt
hf auth login
python app.py
```

Login interaktif menyimpan kredensial lokal untuk pemuatan model tanpa menulis token
ke source. Tanpa CUDA/ZeroGPU, encoder memakai CPU. FastAPI tidak perlu dikembangkan
terpisah; Gradio membawa dependensi servernya sendiri.

```bash
python -m unittest discover -s tests -v
PYTHONPATH=. python tests/smoke_api.py
```

Pembuatan ulang referensi menerima file label berekstensi `.csv` maupun `.txt`:

```bash
python prepare_artifacts.py --vit /path/embeddings_vit_macro \
  --dinov3 /path/embeddings_dinov3_tta4v --labels /path/facets_level2.csv
```

File biner referensi dan CSV diabaikan oleh Git agar tidak ter-push tanpa sengaja;
tetap sertakan `artifacts/reference.npz`, `manifest.json`, dan `meta.json` saat
deploy. `facets_level2.csv` hanya untuk audit lokal, tidak dibutuhkan oleh Space.

## Verifikasi lokal 15 Oktober 2026

- Sembilan unit test lulus.
- Upload file, `/health`, `/embed`, dan `/predict` lulus melalui Gradio client
  dengan encoder tiruan yang hanya digunakan di test.
- Alur processor → model → CLS → TTA menghasilkan vektor 768 dimensi bernorma 1
  untuk ViT dan DINOv3 dengan model satu layer berbobot acak (uji kompatibilitas).
- `pip check` lulus. API lokal ditutup setelah pengujian.
- Deploy ke ZeroGPU privat `ayaayaa/still-e-okay-ai` berhasil. Endpoint `health` siap;
  `embed` dengan bobot pretrained ViT dan DINOv3 menghasilkan masing-masing 768 dimensi
  dengan norma 1. `predict` merespons `unknown` untuk gambar sintetis polos.
  Ringkasan pengujian server ada di `remote_verification.json`. Ini uji integrasi,
  bukan pengukuran akurasi atau bukti kesamaan embedding dengan cache Kaggle.
- Log notebook menunjukkan processor ViT memakai PIL/slow. Deployment mengunci
  backend PIL untuk ViT dan torchvision untuk DINOv3; kesamaan numerik dengan cache
  tetap perlu diperiksa memakai foto sumber dan runtime Kaggle.
