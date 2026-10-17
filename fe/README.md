# Kenal-E web

Empat halaman mengikuti mockup v2: Beranda, Hasil, Cek Laci, Katalog. Detail kategori, pemilahan, lokasi setor, dan informasi aplikasi tampil dalam panel. React + TypeScript + Vite; Plus Jakarta Sans disajikan lokal; ikon Lucide dan ilustrasi SVG. Logo berasal dari aset asli pengguna.

```bash
cd fe
npm ci
npm run dev
```

Vite meneruskan `/api` ke `http://127.0.0.1:8000`. Backend harus dijalankan dari root repositori. Buka `http://localhost:5173`.

- Kamera atau galeri → resize JPEG maksimal 1024 px → API → hasil.
- Tombol contoh memakai vektor referensi tanpa meminta inferensi baru dan selalu berlabel contoh.
- Hasil tidak dikenali berhenti sebelum kategori/risiko/harga. Bisa disimpan sebagai pertanyaan untuk pengelola.
- Cek Laci di IndexedDB melalui Zustand; kategori bisa dikoreksi dan barang dihapus. Rapor menghitung seluruh kelompok, termasuk belum dikenali, dan diekspor PNG via html-to-image.
- Foto dan sesi Cek Laci tidak ditanam dalam cache service worker. Cache shell/font/katalog tersedia setelah kunjungan berhasil; analisis tetap membutuhkan jaringan. Katalog offline baru bekerja setelah diakses online dalam build PWA, bukan server dev.
- PWA memiliki manifest, ikon, dan service worker. Instalasi PWA/kamera memerlukan secure context (localhost atau HTTPS).
- Foto dataset yang belum tersedia ditandai. Panel tempat setor menampilkan peta ilustrasi area UNDIP dengan titik contoh; petunjuk arah belum aktif. Harga riset disertai cakupan, satuan, sumber dan tanggal; yang belum sebanding tetap tanpa angka.

## Cek build

```bash
npm test
npm run build
npm run preview
```

## Frontend di Vercel

Frontend aktif: `https://kenal-e.vercel.app`. Backend Render: `https://still-e-okay.onrender.com`. Di Render, isi `CORS_ORIGINS=https://kenal-e.vercel.app,http://localhost:5173,http://127.0.0.1:5173` agar domain production dan development lokal diizinkan.

Set root directory `fe`, build command `npm run build`, output `dist`. Build production otomatis memakai `https://still-e-okay.onrender.com`. Jika `VITE_API_BASE_URL` sudah diatur di Vercel, samakan nilainya dengan URL tersebut atau hapus override lama, lalu redeploy. Saat development, nilai kosong tetap memakai proxy backend lokal. Jangan memasukkan `HF_TOKEN` ke variabel `VITE_`. Isi token hanya di server backend. `vercel.json` menyediakan fallback route SPA. Konfigurasi PWA mengikuti [Vite PWA](https://vite-pwa-org.netlify.app/guide/).


Thumbnail kartu katalog merupakan 26 WebP lokal 192×192 di `src/assets/catalog`,
dengan gambar tetap per ID melalui `catalogThumbnails.ts`. Vite membundel aset
dan PWA menyimpannya untuk kunjungan berikutnya; kartu tidak meminta thumbnail
dari HF. Gambar penuh detail dan hasil retrieval tetap memakai sumber referensi.
Untuk regenerasi opsional dari dataset lokal (tidak dijalankan saat deploy):

```bash
be/.venv/bin/python fe/scripts/build_catalog_thumbnails.py --images-dir /path/to/1_Electronic
```

Pemilihan gambar mengikuti `be/data/catalog_representatives.json` yang sudah
diperiksa visual pada audit 18 Oktober 2026, bukan file pertama tiap klaster.
Generator mempertahankan seluruh objek dengan padding, tanpa crop, dan mencatat
asal file di `src/assets/catalog/sources.json`. Total 26 WebP sekitar 110 KiB.
Panel kelompok visual juga menyediakan penanganan dan harga khusus mikro;
panduan umum tetap tampil untuk kelompok yang belum dapat dinilai harganya.
