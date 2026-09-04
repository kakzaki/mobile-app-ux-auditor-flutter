# Anti-Slop Reference (Flutter-first)

> Disarikan dari: Sailop 2026 (7 dimensi), Superdesign (distributional
> convergence), Developers Digest (16 pola), uxskill/laithjunaidy,
> pythoughts designer-skill, pols.dev, unscarcity.ai.
> Istilah "slop" = output generatif tanpa arah desain: rata-rata statistik
> data training, bukan keputusan. Kode jalan, tampil generik.

## Prinsip utama: BRIEF WINS

Slop BUKAN daftar elemen terlarang — melainkan **default yang tak
dipikirkan**. Gradien ungu dan kartu rounded boleh, asal ada di brief desain
proyek dengan alasan brand. Emoji tidak boleh dipakai pada UI yang menghadap
pengguna. Aturannya:

- Pilihan yang TERTULIS di brief (palet, font, radius, suara copy) = keputusan,
  bukan slop — meski bentuknya mirip pola umum.
- Pilihan yang MUNCUL karena "kelihatan modern" tanpa alasan = slop.
- Kombinasi 4+ tells tanpa alasan brand = rework.

## Uji refleks kategori (sebelum ship UI baru)

1. **First-order:** kalau orang bisa menebak tema + palet hanya dari
   kategorinya ("fintech → navy-gold", "aplikasi AI → krem SaaS"), itu refleks
   training-data. Kerjakan ulang.
2. **Second-order:** kalau tebakannya "kategori-plus-anti-referensi"
   ("AI tool yang bukan krem → editorial-tipografi") masih ketebak, jebakan
   satu tingkat lebih dalam. Kerjakan ulang sampai tak obvious.

## Tells untuk Flutter (dengan penangkal)

| # | Tell | Contoh Dart | Penangkal |
|---|---|---|---|
| 1 | Warna primer default Material tanpa alasan brand | `Colors.blue`, `Colors.indigo`, `Colors.purple`, seed bawaan | Palet hex bernama di brief; ungu hanya bila brand-nya ungu |
| 2 | Satu sans generik untuk semua job | Roboto/Inter dari headline sampai footnote, tanpa pairing | Display + body yang disengaja; skala + weight bervariasi |
| 3 | Kartu identik massal | Grid kartu: radius, shadow, tile-ikon sama; bobot visual setara walau pentingnya beda | Variasi elevasi/radius ikut hierarki; bobot beda untuk konten beda |
| 4 | Animasi reveal seragam | `fadeIn + slideY` durasi sama di semua layar | Durasi/easing per properti; hormati `MediaQuery.disableAnimations` |
| 5 | Emoji pada UI user-facing | Emoji di judul, label, tombol, status, tooltip, atau accessibility label | Gunakan icon family yang ditetapkan; emoji legacy hanya diparse untuk kompatibilitas data |
| 6 | Semua ter-center, padding seragam | Hero center + section simetris + padding sama tiap layar | Asimetri + densitas ikut fungsi (hero vs tabel data beda) |
| 7 | Copy buzzword generik | EN: seamless, unlock, empower, delve, "Welcome to…". ID: revolusioner, tanpa batas, canggih, "Selamat datang di [NamaApp]" | Copy spesifik: sebut fitur & angka nyata, bukan uplift kosong |
| 8 | Status/warna tanpa makna | Merah untuk hal netral; hijau-merah hanya andalkan warna | Warna + teks/ikon/bentuk; merah dicadangkan untuk bahaya |
| 9 | Struktur template | Onboarding karusel → hero → 3 kartu fitur → footer, tanpa variasi | Susunan ikut alur tugas pengguna, bukan urutan template |
| 10 | State bahagia saja | Empty/loading/error/offline tak didesain | Empty menjelaskan + ajakan aksi; error menyebut jalan keluar |

## Catatan Indonesia (jangan aplikasikan tell Inggris mentah-mentah)

- **Em-dash (—) adalah tanda baca baku Indonesia**, bukan tell AI. Yang tell:
  em-dash 3–4x per paragraf + pola "not X, it's Y".
- **Emoji tidak dipakai di UI**, termasuk pada app konsumen hangat (ibu, anak,
  kuliner). Gunakan icon family atau ilustrasi yang disetujui untuk ekspresi
  visual; emoji legacy hanya boleh diparse untuk kompatibilitas data.
- **Buzzword ID** yang setara: "revolusioner", "terdepan", "solusi inovatif",
  "di era digital ini", klaim superlatif tanpa angka.

## Pre-ship gate (jalan sebelum UI baru dinyatakan selesai)

- [ ] Refleks kategori first + second order tidak obvious.
- [ ] Tiap warna/font/radius punya alasan di brief (atau ditambahkan ke brief).
- [ ] Kartu/elevasi bervariasi ikut hierarki, bukan satu cetakan.
- [ ] Animasi tidak seragam + ada fallback reduced-motion.
- [ ] Copy: nol buzzword, nol placeholder, tiap klaim ada spesifiknya.
- [ ] State lengkap: loading, empty, error, offline, disabled, sukses.
- [ ] Slop test: "apakah penonton langsung bilang 'AI yang bikin'?" Bila ya, rework.

## Disiplin emoji

Emoji tidak boleh muncul dalam teks UI yang menghadap pengguna, termasuk judul,
label, tombol, status, tooltip, empty/error state, dan accessibility label.
Gunakan icon family yang sudah ditetapkan (Material/Cupertino/Phosphor) untuk
fungsi dan affordance, serta Lottie atau ilustrasi yang disetujui untuk
dekorasi ekspresif.

Emoji lama boleh diparse untuk kompatibilitas data tersimpan, tetapi tidak boleh
dirender sebagai UI baru. Scanner dapat melaporkan `emoji_density` sebagai
sinyal triase; audit tetap harus memastikan tidak ada emoji pada UI user-facing.

## Lisensi ikon dan aset

Jangan gunakan logo atau ikon brand/platform proprietary maupun trademarked
sebagai ikon UI umum, termasuk logo Apple atau SF Symbols. Utamakan icon family
open-source dengan lisensi yang kompatibel, seperti Phosphor, Material Icons,
atau Lucide, dan verifikasi provenance serta kewajiban atribusinya sebelum
menambahkan aset.
