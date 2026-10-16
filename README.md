# Kenal-E

Demo pemilahan awal e-waste untuk warga: foto satu barang, periksa kandidat kategori, simpan ke Cek Laci, dan unduh rapor pemilahan. Frontend mengikuti desain versi kedua pada `assets/ui-ux/e-okay-mvp-v2.png`.

## Jalankan

Dari root repositori, setelah dependensi terpasang:

```bash
./dev.sh
```

Frontend: http://localhost:5173. Backend dan Swagger: http://localhost:8000/docs. `Ctrl+C` menghentikan keduanya. HF Space mengerjakan encoder; laptop tidak memerlukan PyTorch untuk `fe` dan `be`.

Instalasi awal pada komputer baru:

```bash
python3 -m venv be/.venv
be/.venv/bin/pip install -r be/requirements-dev.txt
npm --prefix fe ci
```

Isi `HF_TOKEN` pada `.env` di root. Contoh pengaturan tersedia di `.env.example`; jangan menimpa token yang sudah diisi.

Dokumentasi rinci: [frontend](fe/README.md), [backend](be/README.md), [AI Space](ai/README.md).

## Status demo

Empat halaman dan panel detail sudah terimplementasi. Kandidat hasil diberi status perlu diperiksa karena threshold belum dikalibrasi di foto baru. Metadata risiko masih draf. Harga, titik setor terverifikasi, foto referensi berizin, dan peta perhatian belum tersedia; UI menyediakan state yang sesuai. Data di Cek Laci disimpan di perangkat pengguna. Tidak ada akun atau backend database.
