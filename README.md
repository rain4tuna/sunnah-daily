# Sunnah Daily

Pipeline konten dakwah untuk IG Reels (@sun_nahdaily) dan YouTube Shorts (@sunnah_dailyy).

Sumber kisah: playlist Sirah Nabawiyah Ust. Dr. Firanda Andirja, M.A. (`data/episode.csv`), diceritakan ulang
dengan narasi dan animasi sendiri. Kredit kajian selalu dicantumkan di video dan caption.

Alur satu video (`main.py`):
1. `ekstrak.py`: Gemini menonton satu episode dari link YouTube dan mengambil 8 kisah + dalil,
   disimpan di `data/kisah/epNNN.json` (episode tidak ditonton ulang).
2. Verifikasi dalil dengan Google Search: teks Arab, sumber, derajat. Hadits lemah diberi label
   HADITS LEMAH dan disebut lemah di narasi; kisah yang bersumber riwayat lemah dilewati.
3. Narasi per segmen dibacakan Gemini TTS.
4. `video.py` + `ilustrasi.py`: video 1080x1920 sesuai brand guideline (Pastel Minimalis), tanpa musik
   instrumen dan tanpa menggambar Nabi ﷺ, sahabat, maupun malaikat.

Menjalankan: tab Actions → "Buat Video Sunnah Daily" → Run workflow (uji = true hanya membuat video).

Secrets: `GEMINI_API_KEY`.

## Template Animasi Ikon (default sejak 10/11/2026)

Semua video memakai `animasi_ikon.py`: ikon benda & tempat digambar kode (tanpa makhluk bernyawa), gaya bergiliran
**papan** / **flat** / **kertas**, palet Pastel Minimalis (`gaya.py`), caption karaoke, kartu dalil + label derajat.
Babak disusun `storyboard_ikon.py` (1 panggilan Gemini, disimpan di `storyboard_ikon`). Gaya lama tetap ada:
input `GAYA=sirah` (Gua Tsur) atau `lama`.

## Seri tambahan: Sunnah Harian

`harian.py` + `data/harian_topik.csv` (40 topik amalan & adab). Materi ditulis Gemini + Google Search dari dalil
shahih/hasan, dicek ulang pemeriksa dalil; riwayat lemah tidak diangkat. Data di `data/kisah/harian.json`.
Jadwal: slot **11.47** dan **18.47 WIB** = Sunnah Harian, slot lain = Sirah (input `seri` untuk memaksa).

## Stok naskah tanpa API (`stok.py`)

Riset dan cek dalil bisa dikerjakan di chat Gemini lalu ditempel ke repo, supaya jadwal tayang tidak memanggil
Gemini + Google Search lagi (yang tersisa lewat API hanya storyboard dan TTS). Kisah berstatus `Belum` yang sudah
punya `layak` langsung dipakai. Kalau stok habis, workflow kembali riset/cek lewat API seperti biasa.

1. `python stok.py minta` → prompt ditulis ke `stok/minta/*.txt` (`cek-NN` = cek dalil, `riset-NN` = topik
   Sunnah Harian baru).
2. Tempel isi tiap file ke chat Gemini **baru**, simpan jawaban JSON-nya ke `stok/jawab/` (nama file bebas).
3. `python stok.py gabung` → hasil dipasang ke `data/kisah`, ringkasan LOLOS / DILEWATI dicetak.
4. Topik hasil riset masih perlu dicek dalilnya: ulangi langkah 1-3 sekali lagi.
5. Baca perubahannya (`git diff data/kisah`), lalu commit dan push ke `main`.

`python stok.py status` menampilkan sisa stok. Kebutuhan per hari: 3 kisah Sirah dan 2 Sunnah Harian.
Folder `stok/` tidak ikut ke repo. Episode Sirah baru bisa ikut distok: `python stok.py minta --episode 2`
menulis prompt `episode-NN` (Gemini menonton videonya di chat); kisahnya lalu dicek di putaran berikutnya.

## Template Remotion (`GAYA=remotion`)

Template utama sejak 13/11/2026 untuk seri Sirah maupun Sunnah Harian: motion graphic gelap-emas dengan ilustrasi
SVG yang bergerak (proyek di `remotion/`, jembatannya `remotion_video.py`). Template lama (Animasi Ikon) tetap ada:
pilih `gaya = ikon` saat Run workflow, atau ubah `GAYA_TEMPLATE` di `buat-video.yml` untuk jadwal otomatis.

- **Ilustrasi dipilih otomatis.** `storyboard_ikon.py` meminta Gemini memilih satu ilustrasi per babak dari daftar
  `ILUSTRASI` (15 adegan: badai, kota_malam, quran, kafilah, kabah, masjid, gua, majelis, lentera, fajar, air,
  hidangan, pintu, sedekah, hati) dan, bila cocok, satu `tokoh` (panik, takut, berdiri, berdoa). Storyboard lama
  tanpa pilihan ini dipetakan dari ikonnya (`PETA_IKON`).
- **Aturan gambar.** Manusia dan hewan digambar tanpa wajah (tidak ada mata dan mulut). Nabi ﷺ, sahabat, dan malaikat
  tidak digambar sama sekali: prompt melarangnya, dan `ilustrasi_babak()` membuang `tokoh` dari babak yang menyebut
  mereka (`KATA_TANPA_TOKOH`).
- **Menambah ilustrasi.** Tulis komponennya di `remotion/src/Ilustrasi.tsx`, daftarkan di `JENIS` dan `ADEGAN` di
  berkas itu, lalu tambahkan kunci dan artinya ke `ILUSTRASI` di `storyboard_ikon.py`. Komposisi `Galeri`
  (`npx remotion still src/index.ts Galeri out/galeri.png --frame=120`) menampilkan semuanya dalam satu gambar.
- **Render per potongan.** Video dirender tiap `REMOTION_POTONG` frame lalu digabung dengan audio, supaya potongan
  yang macet bisa diulang. Di Windows pakai `REMOTION_GL=angle` (default); render perangkat lunak di sana menggantung.
- **Font** ditanam di `remotion/src/fontdata.ts` (dibuat dari `fonts/`), supaya render tidak memuat apa pun lewat jaringan.

## Template Motion Kaya (`GAYA=motion_kaya` / `SunnahMotion`)

Template utama 9:16 terbaru (`remotion/src/SunnahMotion.tsx`, `AdeganKaya.tsx`, `KarakterKaya.tsx`, `PropertiKaya.tsx`):
- **Gerakan lebih kaya & natural:** karakter SVG berartikulasi (napas torso, sendi bahu-siku-tangan, ayunan kain/sorban, langkah kaki + debu, 8 pose: `berdiri`, `berjalan`, `berdoa`, `panik`, `takut`, `menunjuk`, `duduk_membaca`, `berbagi`), 12 properti animasi berlapis, dan 21 adegan parallax (15 adegan dasar + 6 adegan baru: `doa_malam`, `belajar_ilmu`, `keluarga_hangat`, `hijrah_perjalanan`, `taman_berkah`, `waktu_subuh`).
- **Kepatuhan Sunnah ketat:** seluruh karakter **100% tanpa mata, alis, hidung, dan mulut**; Nabi ﷺ, para nabi, sahabat, dan malaikat tidak pernah digambar (`KATA_TANPA_TOKOH_RE` di `storyboard_ikon.py`); **tanpa musik** (hanya suara narasi + SFX non-musik CC0 di `sfx/`, output audio stereo 48 kHz AAC).
- **Optimasi Hook, CTA & Safe Zone (`growth.py`):** hook instan sejak frame 0, safe zone ketat lintas platform (`x <= 850`, `y` di `230..1430`), CTA visual+verbal setelah faedah, loop echo di penutup, serta caption/metadata khusus per platform (IG maks 5 hashtag tanpa URL, YT Shorts judul front-loaded <= 40 karakter, TikTok & FB).
- **Lembar periksa visual:** `npx remotion still src/index.ts GaleriKaya out/galeri_kaya.png --frame=24`.

## Posting Otonom TikTok (`tt.py`), Telegram Delivery (`tg.py`) & Monetisasi

- **Kirim Otomatis ke Telegram Pribadi untuk TikTok (`tg.py` — Opsi C paling praktis):** setelah video dirender, pipeline dapat mengirim file MP4 (`sendVideo`) beserta caption TikTok lengkap (`sendMessage`) langsung ke Telegram pribadi agar tinggal 1-tap Share ke TikTok tanpa perlu lolos audit TikTok Developers. Cukup isi GitHub Secrets `TG_BOT_TOKEN` & `TG_CHAT_ID` (tes lewat workflow **Posting Ulang** `tujuan=cek-tg`).
- **TikTok Content Posting API v2 (`tt.py`):** mendukung OAuth2 refresh token (`TT_CLIENT_KEY`, `TT_CLIENT_SECRET`, `TT_REFRESH_TOKEN`) atau `TT_ACCESS_TOKEN`, chunked `FILE_UPLOAD`, mode `direct`/`inbox` (`TT_MODE`), privasi aman default `SELF_ONLY` (`TT_PRIVACY`), dan simulasi lokal (`TT_DRY_RUN=true`). Terintegrasi di `main.py`, `posting_uji.py` (`tujuan=tt|tg|cek-tt|cek-tg|semua`), `buat-video.yml`, `posting-ig.yml`, dan `DAFTAR_POSTINGAN.md`.
- **Video Panjang 8+ Menit (`video_panjang.py`):** set `MODE_MONET=true` untuk menargetkan durasi ~8.5–10 menit (membuka iklan mid-roll YouTube + Dual CTA di tengah video).
- Lihat laporan audit di `docs/AUDIT_REPORT.md` dan peta jalan pertumbuhan menuju 1 juta di `docs/GROWTH_MONETIZATION_PLAYBOOK.md`.
