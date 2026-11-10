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
