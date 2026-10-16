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
- Foto dataset dan titik setor tidak direkayasa; tampil state belum tersedia saat data belum ada. Harga tetap kosong sampai sumber diverifikasi.

## Cek build

```bash
npm test
npm run build
npm run preview
```

## Frontend di Vercel

Set root directory `fe`, build command `npm run build`, output `dist`. Atur `VITE_API_BASE_URL=https://backend-mu` sebelum build. Jangan memasukkan `HF_TOKEN` ke variabel `VITE_`. Isi token hanya di server backend. `vercel.json` menyediakan fallback route SPA. Konfigurasi PWA mengikuti [Vite PWA](https://vite-pwa-org.netlify.app/guide/).
