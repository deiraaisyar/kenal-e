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
| `CORS_ORIGINS` | `https://kenal-e.vercel.app`; tambahkan origin lokal jika perlu, dipisah koma dan tanpa slash penutup |
| `PYTHON_VERSION` | `3.12.12` |
| `AI_TIMEOUT_SECONDS` | `180` |
| `OPENBLAS_NUM_THREADS` | `1` |
| `OMP_NUM_THREADS` | `1` |
| `MALLOC_ARENA_MAX` | `2` |

Blueprint meminta nilai `HF_TOKEN` saat pembuatan; `CORS_ORIGINS` sudah berisi domain frontend dan origin lokal. Jika dibuat manual, isi seluruh pengaturan di atas. `/api/ready` hanya mengecek kesiapan backend; `/api/health` juga mengecek status Space.

Backend deployment: `https://still-e-okay.onrender.com`. Cek `/api/ready`, `/api/taxonomy`, dan `/docs`. Frontend production memakai URL ini secara default. Jika Vercel sudah memiliki `VITE_API_BASE_URL`, samakan nilainya dengan URL tersebut atau hapus override lama, kemudian redeploy frontend. Jangan memberi frontend token HF.

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

## Diagnosis koneksi AI

`/api/ready` hanya memeriksa backend dan referensi. Untuk koneksi HF, buka `/api/health`:

- `space_diagnostic.token_configured`: apakah token tersedia di proses Render (nilainya tidak ditampilkan).
- `hf_http_status` 401/403: akses HF ditolak; periksa token dan izin Space. 404 juga bisa berarti Space privat atau ID salah.
- `reason` `network_timeout`/`network_error`: koneksi jaringan ke HF gagal; ini terpisah dari masalah token.
- `stage` `RUNNING` dan `space` `running`: Space dapat diakses. Kegagalan inferensi selanjutnya dicatat dengan tipe exception di log Render tanpa isi token.

Perubahan environment membutuhkan restart/redeploy. Nama secret harus `HF_TOKEN`, nilainya hanya token, bukan `HF_TOKEN=...`, bukan awalan `Bearer`, dan tanpa tanda kutip. `HF_SPACE_ID` adalah `ayaayaa/still-e-okay-ai`; URL HF penuh juga dinormalisasi oleh backend.
