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
