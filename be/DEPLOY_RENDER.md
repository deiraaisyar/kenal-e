# Deploy Kenal-E API ke Render Free

Frontend tetap di Vercel; encoder tetap di Hugging Face. Render hanya menjalankan FastAPI, pencarian vektor NumPy, dan lookup JSON. Tidak memasang PyTorch, Transformers, atau bobot model.

## File yang harus ikut Git

- `render.yaml`, `be/requirements.txt`, serta kode `be/`.
- `be/data/artifacts/reference.npz` (sekitar 21,5 MiB), `manifest.json`, `meta.json`.
- `be/data/gallery_meta.json`, `thresholds.json`, `meta.json`, `drop_points.json`.
- `be/data/thumbnails/.gitkeep` untuk direktori thumbnail yang saat ini kosong.

NPZ di `ai/artifacts` diabaikan Git. Salinan untuk deployment sengaja berada di `be/data/artifacts` agar dapat ikut commit. Salinan ini sudah disiapkan; jangan memasukkan `.env` atau `.venv`.

Untuk menyiapkan ulang dari hasil riset yang sudah ada, jalankan dari root:

```bash
be/.venv/bin/python -m be.scripts.prepare_reference
be/.venv/bin/python -m be.scripts.check_deploy
```

Gunakan `--replace` pada perintah pertama hanya jika sengaja mengganti referensi dengan run baru yang sesuai metadata. Tidak ada pelatihan atau clustering ulang.

## Buat layanan

Pakai **New → Blueprint** dan pilih repo ini untuk membaca `render.yaml`, atau buat **New → Web Service** secara manual:

| Pengaturan | Nilai |
| --- | --- |
| Name | `kenal-e-api` |
| Language | Python 3 |
| Root Directory | Kosong, gunakan root repo |
| Region | Singapore |
| Instance Type | Free |
| Build Command | `pip install -r be/requirements.txt && python -m be.scripts.check_deploy` |
| Start Command | `uvicorn be.app:app --host 0.0.0.0 --port $PORT --workers 1 --limit-concurrency 8` |
| Health Check Path | `/api/ready` |

Environment variables:

| Nama | Nilai |
| --- | --- |
| `HF_TOKEN` | Token yang sudah ada di `.env`, masukkan sebagai secret Render |
| `HF_SPACE_ID` | `ayaayaa/still-e-okay-ai` |
| `CORS_ORIGINS` | URL frontend Vercel yang benar, contoh `https://kenal-e-fe.vercel.app`; beberapa origin dipisah koma, tanpa slash penutup |
| `PYTHON_VERSION` | `3.12.12` |
| `AI_TIMEOUT_SECONDS` | `180` |
| `OPENBLAS_NUM_THREADS` | `1` |
| `OMP_NUM_THREADS` | `1` |
| `MALLOC_ARENA_MAX` | `2` |

Blueprint meminta nilai `HF_TOKEN` dan `CORS_ORIGINS` saat pembuatan. Jika dibuat manual, isi seluruh pengaturan di atas. `/api/ready` hanya mengecek kesiapan backend; `/api/health` juga mengecek status Space.

Setelah backend live, buka `/api/ready`, `/api/taxonomy`, dan `/docs`. Di proyek frontend Vercel, isi `VITE_API_BASE_URL` dengan URL HTTPS backend lalu redeploy frontend. Jangan memberi frontend token HF.

## RAM dan data sementara

Render Free menyediakan RAM 512 MB. Gunakan satu worker; setiap worker tambahan akan memuat salinan galeri. Pembacaan/decode foto dan analisis diserialkan; request lain mendapat `busy`. Uvicorn dibatasi maksimal 8 koneksi/tugas bersamaan untuk mengurangi penumpukan unggahan. NumPy/OpenBLAS dibatasi satu thread.

Untuk pengukuran lokal:

```bash
OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 MALLOC_ARENA_MAX=2 be/.venv/bin/python -m be.scripts.profile_memory
```

Uji ini mengukur proses Linux lokal dengan gambar 25 megapiksel dan vektor referensi sebagai pengganti panggilan HF. Ini bukan jaminan RAM di Render; pantau metrik setelah deployment.

Free service tidur setelah 15 menit tidak menerima trafik dan bangun sekitar satu menit pada request berikutnya. File upload/cache sementara dapat hilang saat restart, sehingga NPZ dan JSON harus berasal dari deployment/repo. Cek Laci tetap di perangkat pengguna.

Metadata tambahan bisa diisi kemudian melalui `be/data/meta.json` dan `drop_points.json`, lalu commit dan redeploy. Tidak perlu membuat embedding baru untuk memperbarui harga atau lokasi. Harga/lokasi kosong dan threshold belum terkalibrasi tetap ditandai sesuai kondisi saat ini.

Rujukan: [FastAPI di Render](https://render.com/docs/deploy-fastapi), [Free instances](https://render.com/docs/free), [Compute plans](https://render.com/docs/compute-plans).
