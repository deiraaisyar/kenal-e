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
- `data/meta.json` adalah override lokal per ID. Contoh struktur: `{"13":{"info":{"verified":false},"price":{"mode":"none"}}}`. Format lama memakai `verified=true`, `show=true`, rentang valid, sumber, dan tanggal. Format riset `ranges` divalidasi terhadap observasi pada `research_sources.json` (lihat bagian metadata riset di bawah).
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

### Label dan filter katalog

`data/catalog_facets.json` memetakan ID klaster ke `groups` (jenis barang) dan
`sizes` (ukuran visual), berdasarkan Tabel 3–4 paper semifinal BDC 2026. ID noise
26 tetap dikecualikan dari katalog. Risiko awal mengikuti metadata penanganan
(Tabel 5); ID tanpa klasifikasi risiko tetap `unknown`. Ukuran ini adalah label
kelompok referensi, bukan pengukuran dimensi foto baru.

Endpoint daftar dan detail `/api/taxonomy` menyertakan `facets`, dengan tiga array:
`groups`, `sizes`, dan `risks`. Satu barang dapat memiliki beberapa label.
Tambahan label bisa diatur per ID di `data/meta.json`, misalnya struktur:

```json
{"13":{"facets":{"groups":["internal"],"sizes":["small"],"risks":["valuable"]}}}
```

Gunakan ID jenis `office`, `household`, `computing`, `media`, `energy`, `internal`,
`mixed`; ukuran `small`, `medium`, `large`, `unidentified`; risiko `high`, `medium`,
`valuable`, `low`, `unknown`. Tambahkan label hanya bila ada dasar datanya.
`risk_level` pada panduan penanganan tetap menjadi risiko utama, terpisah dari
label penyaringan. Frontend menerapkan OR antar pilihan dalam satu dimensi dan
AND antar dimensi; pilihan “Semua” menghapus pembatas di dimensi itu.
Deploy backend sebelum frontend agar label baru langsung tersedia.


### Metadata riset makro, mikro, dan harga (17 Oktober 2026)

`data/meta.json` kini memuat 27 makro dan 88 mikro dari CSV asli, termasuk makro
26 yang disimpan untuk audit tetapi tetap ditolak sebelum panduan/harga.
Katalog menampilkan 26 makro dengan 84 mikro. Satu mikro adalah satu deret galeri;
beberapa mikro boleh mempunyai nama pengguna yang sama. ID dan urutan NPZ tidak
diubah. `reference_rows` mencakup baris CSV asli; `size` pada respons API adalah
jumlah referensi setelah deduplikasi.

Setiap makro memuat `name`, `description`, `proposal_facets`, `facets`, `info`,
`price`, dan `subs` (objek dengan kunci ID mikro lokal). Kategori fungsi/ukuran/
risiko makro mengikuti Tabel 3–5 proposal semifinal. ID yang tidak tercantum
risikonya tetap `unknown`. Mikro memiliki nama dan deskripsi draf berdasarkan
galeri perwakilan, `needs_review`, serta kategori asal proposal. Pengecualian
visual pada 5_1, 21_1, 21_2, dan 23_2 tidak otomatis menerima panduan/harga induk.
Nama atau deskripsi ini belum merupakan anotasi terverifikasi seluruh anggota.

`subs.<id>.price_policy` menentukan penerapan harga: `inherit` mengikuti induk,
`override` memakai harga mikro tersendiri, `blocked` menghentikan pewarisan.
`condition_tier` dan `condition_factors` tetap null: nomor mikro, layar gelap,
posisi tutup laptop, dan sudut foto tidak diubah menjadi kondisi fungsi/harga.
ARI level 2 pada proposal adalah 0,4142; belum ada kalibrasi faktor kondisi.

Harga memakai `mode: "ranges"` dengan `whole` (jual utuh) dan `scrap` (rongsok).
Masing-masing dapat null. Angka memiliki `unit` (`item` atau `kg`), `min`, `max`,
`basis`, `source_ids`, `observation_ids`, `accessed_on`, `requires_confirmation`,
dan `note`. Acuan harga utuh bersyarat pada fungsi dan model yang sebanding;
foto tidak membuktikan fungsi. Acuan grade PCB bukan hasil deteksi grade.
Rentang minimum–maksimum berasal dari sampel terpilih, bukan interval statistik,
rata-rata pasar, ataupun harga transaksi. Harga tunggal tetap min=max.

`data/research_sources.json` menyimpan sumber, tanggal akses/publikasi bila
tersedia, cakupan wilayah, metode, dan 53 observasi angka harga. Tiga daftar
pengepul berangka adalah Kepul, Rongsok Bandung, dan ALDI SCRAP; Prabu Recycle
hanya menjadi rujukan satuan/metode karena tidak memasang angka. Iklan pembelian,
produk baru, barang paket tidak sebanding, dan biaya jasa pengelolaan tidak
dipakai sebagai harga barang utuh. Sebagian rincian iklan OLX tidak bisa dibuka;
observasi tersebut berasal dari judul dan harga pada indeks listing, dan
keterbatasannya dicatat. Tidak ada komunikasi atau konfirmasi penjual.

Harga belum dikonfirmasi ke pengepul Semarang; belum ada janji pembayaran,
verifikasi izin pengelola, atau pemeriksaan fungsi barang. `info.verified` tetap
false. Nilai kosong bukan berarti tidak bernilai jual. Jangan mengisi harga
kategori campuran hanya untuk membuat seluruh kartu mempunyai angka.

`valid_price` memeriksa kanal, satuan, sumber, dan kecocokan batas harga dengan
observasi tersimpan. API lama/simpanan perangkat dengan format satu harga tetap
didukung. Frontend membaca nama/deskripsi mikro, memakai istilah kelompok visual,
dan menampilkan dua kanal harga beserta sumber, tanggal akses, dan dasar estimasi.
Deploy backend dan frontend bersama; tidak perlu melatih ulang encoder atau
membuat ulang reference.npz.
