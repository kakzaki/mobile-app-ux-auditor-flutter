# Duplicate-Information Check

> Informasi ganda = fakta/tugas yang sama tampil di 2+ tempat TANPA nilai
> tambah. Berbeda dengan penguatan disengaja (janji kepercayaan di momen
> keputusan) dan format ganda (teks vs PDF yang sama — itu kebutuhan).

## Membedakan: duplikat vs penguatan vs format

| Pola | Contoh | Vonis |
|---|---|---|
| Fakta sama, konteks sama | Misi mingguan full-text di Beranda DAN di sheet profil | 🔴 Duplikat — satu jadi teaser + link |
| Data sama, sumber beda | Sheet profil hardcode misi, Beranda dari database | 🔴 Duplikat + bug basi — single source of truth |
| Janji sama di momen kepercayaan | Privasi di setup, footer, support | 🟢 Penguatan — boleh bila redaksi kanonis |
| Data sama, format beda | Ringkasan teks vs PDF untuk dokter | 🟢 Kebutuhan — format ikut momen pakai |
| Fakta sama, kedalaman beda | Hero sekilas vs layar Jelajah detail | 🟢 Progressive disclosure — glancable ringkas |

## Heuristik deteksi

1. **String literal identik** ≥50 karakter di ≥2 file (lihat pola scanner
   `duplicate-copy`). Abaikan import dan data terstruktur.
2. **Angka/fakta yang bisa basi**: tanggal, versi, harga, misi mingguan,
   statistik — cari consequent hardcode di luar sumber datanya.
3. **CTA kembar**: dua tombol beraksi sama dalam satu layar atau alur
   berurutan tanpa pembeda.
4. **Onboarding mengulang setup**: karusel yang isinya diinput ulang di
   layar berikutnya kata-per-kata.
5. **Bantuan mengulang manual**: artikel in-app vs docs — boleh beda media,
   tapi fakta medis/angka harus satu sumber.

## Strategi perbaiki (pilih yang terkecil)

- **Single source of truth**: satu fungsi/data, semua layar baca dari situ.
- **Teaser + link**: tempat sekunder diringkas + deep-link ke primer.
- **Kanonisasi redaksi**: bila penguatan memang perlu, samakan kalimatnya
  agar maintenance satu pola pikir.
- **Hapus**: bila tempat sekunder tak menambah keputusan/aksi.

## Skor dalam audit

- P1: duplikat menyebabkan data basi/konflik (dua kebenaran berbeda).
- P2: duplikat menambah maintenance + membingungkan ("mana yang benar?").
- P3: penguatan berlebihan (janji sama >3x tanpa momen keputusan jelas).

## Label echo (judul diulang subteks)

Detektor (`label_echo_findings`): pasangan string berdekatan (≤6 baris)
dengan ≥2 kata konten sama dan overlap ≥50% — dengan pengecualian:

- Judul dialog berisi `?` dilewati (dialog memang menggemakan tombolnya).
- Subteks yang memuat SEMUA kata judul + info baru = elaborasi, bukan echo.
- Hasil detector adalah triase: tiap hitungan harus dikonfirmasi di layar
  (judul + subteks yang sama-sama terlihat) sebelum diubah.
