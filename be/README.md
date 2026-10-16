# Kenal-E backend

FastAPI untuk validasi foto, jembatan ke Space `ayaayaa/still-e-okay-ai`, keputusan kategori, dan katalog. Tidak memasang PyTorch atau menjalankan model di laptop.

Jalankan dari root repositori:

```bash
python3 -m venv be/.venv
be/.venv/bin/pip install -r be/requirements-dev.txt
be/.venv/bin/python -m uvicorn be.app:app --host 127.0.0.1 --port 8000 --reload
```

Isi `HF_TOKEN` pada `.env` di root. File ini dibaca otomatis. Variabel opsional ada di `.env.example`. Token tidak dimasukkan ke respons atau frontend.

Dokumentasi API: http://127.0.0.1:8000/docs.

## Data dan keputusan

- Memuat `reference.npz`, `manifest.json`, dan nama kategori dari `meta.json`. Default memakai salinan deployment di `be/data/artifacts`; jika belum ada, memakai `ai/artifacts`. CSV hanya dibutuhkan saat menyiapkan metadata, bukan pada runtime deployment.
- Satu wakil per `dup_group` menghasilkan 3.598 gambar independen. Label dari CSV run 88 subklaster; folder arsip gambar lama tidak dipakai sebagai label.
- kNN ViT, k=10, cosine voting; centroid makro sebagai diagnostik; centroid DINOv3 terdekat dalam makro untuk subklaster. Kategori LEAF kecil tidak mendapat label kondisi.
- Noise dan kandidat di bawah batas neighbor awal dihentikan. Batas itu hanya heuristik referensi, belum kalibrasi foto baru.
- `data/thresholds.json` memiliki `calibrated=false`. Semua kandidat yang lolos tetap `borderline`; jangan mengubahnya menjadi `true` tanpa evaluasi independen. Tidak ada angka confidence di UI.
- Metadata risiko awal mengikuti tabel spesifikasi pengguna. Semua penanganan berlabel draf. Risiko laptop tertutup/laptop perlu ditinjau terhadap baterai yang masih terpasang.
- `data/meta.json` adalah override lokal per ID. Contoh struktur: `{"13":{"info":{"verified":false},"price":{"mode":"none"}}}`. Harga hanya tampil dengan `verified=true`, `show=true`, rentang valid, sumber, dan tanggal. Tidak ada angka harga bawaan.
- `data/drop_points.json` masih kosong. Hanya entri bersumber dengan tanggal verifikasi yang disajikan.
- `/api/explain` mengembalikan `explain_unavailable`; tombol disembunyikan sampai metode makalah dan endpoint tersedia.

## Foto referensi

Foto referensi berasal dari dataset public `ayaayaa/kenal-e-thumbnails`, direktori `images`, pada commit `9800cac5b0554d5acfeb92d730e9791aee485a17`. Seluruh 3.961 nama file telah dicocokkan dengan `data/gallery_meta.json`, tanpa nama hilang atau ganda. Backend membuat URL dari nama file yang sesuai vektor, termasuk encoding spasi dan karakter khusus. Browser mengambil gambar langsung dari HF; backend tidak mengunduh seluruh dataset.

`REFERENCE_IMAGE_BASE_URL` dapat mengganti lokasi/revisi gambar; nilai kosong menonaktifkan fallback gambar remote. Gambar saat ini masih beresolusi asli. Frontend memuat gambar referensi secara lazy. Jika nanti membuat thumbnail kecil, taruh di `data/thumbnails` dan isi `data/thumbnail_manifest.json` dengan mapping nama referensi ke nama thumbnail. Thumbnail lokal yang tersedia diprioritaskan; nama file thumbnail harus tanpa path. Alternatifnya, upload thumbnail ke HF lalu ubah base URL dengan tetap menjaga nama file.

## Unggahan dan privasi

JPG/PNG/WEBP maksimal 5 MB; body multipart dibatasi; format diperiksa lewat Pillow. Gambar dikecilkan maksimal 1024 px, dikonversi JPEG dan metadata dibuang sebelum diteruskan. File sementara backend dihapus dalam `finally`. Space Gradio yang ada memakai pembersihan cache unggahan berkala, bukan jaminan tanpa penyimpanan server. Sesi Cek Laci hanya disimpan frontend di perangkat.

## Uji

```bash
be/.venv/bin/python -m pytest be/tests -q
be/.venv/bin/python -m be.scripts.check_space
```

Pengujian API mengganti encoder dengan vektor referensi untuk menguji aturan keputusan, validasi, error, dan penahanan harga. `check_space` memeriksa kontrak `/embed(photo, selected)` serta `/health` Space aktual. Kontrak aktual mengembalikan `embeddings.vit` dan `embeddings.dinov3`.

Rujukan implementasi: [FastAPI uploads](https://fastapi.tiangolo.com/tutorial/request-files/), [Gradio client](https://www.gradio.app/docs/python-client/client).

## Deploy ke Render Free

Konfigurasi `render.yaml` tersedia di root. Ikuti [DEPLOY_RENDER.md](DEPLOY_RENDER.md) untuk pengaturan, file NPZ/JSON wajib, dan secret. Backend tetap memakai satu worker dan satu thread NumPy agar sesuai anggaran RAM 512 MB. Health check `/api/ready` tidak memanggil Space. Uji memory lokal tersedia lewat `python -m be.scripts.profile_memory`.

URL deployment yang diberikan pengguna: `https://still-e-okay.onrender.com`. Frontend production otomatis memakai URL ini, dengan opsi override `VITE_API_BASE_URL`; tambahkan origin frontend yang aktif ke `CORS_ORIGINS` di Render.
