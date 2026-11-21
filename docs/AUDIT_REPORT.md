# Laporan Audit & Delivery Project `d:\sunnah-daily` (`/agentic-delivery`)

**Tanggal:** 2026-11-21  
**Target Workspace:** `d:\sunnah-daily`  
**Alur Audit:** Stage 1 (Intake & Rule Lock) -> Stage 2 (Implementation) -> Stage 3 (QA & Self-Healing Loop) -> Stage 4 (Compliance & Security Audit) -> Stage 5 (Safe Release Readiness)

---

## 1. Ringkasan Eksekutif & Status Audit

Seluruh 4 requirement utama (`R1` Audit Project, `R2` Template Motion Kaya + Aset & Aturan Sunnah, `R3` Optimasi Hook/CTA/Growth berbasis `/claude-youtube` & IG skills, `R4` Posting Otonom TikTok) telah diimplementasikan dan diverifikasi secara independen dengan bukti nyata (render video MP4 1080×1920 valid, inspeksi visual frame-by-frame & `GaleriKaya`, pemeriksaan pipeline audio non-musik, 19 unit test lulus 100%, TypeScript `tsc --noEmit` 0 error, serta `py_compile` 0 error).

---

## 2. Daftar Temuan Audit Terverifikasi & Status Penyelesaian (14 Temuan)

| ID | Prioritas | Lokasi | Temuan Terverifikasi | Status & Tindak Lanjut |
|---|---|---|---|---|
| **F-01** | **P0** | `.gitignore`, `aset/mentah/gerak/` | `.gitignore` belum melindungi `.env`, `*.token`, `*.key`, `credentials*.json`, `cache_panjang/`, `remotion/out/`. Selain itu terdapat file lokal tidak relevan `aset/mentah/gerak/Antigravity-x64.exe` (182 MB) & `Nov 16 - 06_47.zip` (56 MB) di folder `aset/mentah/` (terabaikan git). | **FIXED** — `.gitignore` diperketat dengan pola secrets/build. **Rekomendasi manual:** hapus `aset/mentah/gerak/Antigravity-x64.exe` dari lokal jika tidak diperlukan agar menghemat ruang disk. |
| **F-02** | **P0** | `remotion/src/theme.ts`, `Scenes.tsx`, `Layers.tsx` | Template lama (`SunnahDaily`) menaruh konten hingga `x=996` dan `y=1570`, menabrak zona tombol aksi kanan (`x>850`) dan caption bawah (`y>1440`) IG Reels / YT Shorts / TikTok. | **FIXED** — Template baru `SunnahMotion` (`remotion/src/SunnahMotion.tsx`) menerapkan `SAFE_KAYA` ketat (`x: 56..846`, `y: 230..1430`), menyisakan 234px bersih di kanan & 490px di bawah. |
| **F-03** | **P0** | `main.py`, `posting_uji.py`, `.github/workflows/` | Pipeline hanya mendukung IG, YouTube, dan Facebook; belum ada posting otonom ke TikTok. | **FIXED** — Dibuat `tt.py` (TikTok Content Posting API v2, OAuth2 refresh, chunked `FILE_UPLOAD`, mode `direct`/`inbox`, privasi default aman `SELF_ONLY`, `--dry-run`, redaksi token) dan terintegrasi ke `main.py`, `posting_uji.py`, `buat-video.yml`, `posting-ig.yml`, `PemicuJadwal.gs`, serta `DAFTAR_POSTINGAN.md`. |
| **F-04** | **P0** | `main.py`, `harian.py` | Caption IG mengirim 12–13 hashtag + URL YouTube tidak bisa diklik (melanggar batas resmi IG 5 hashtag sejak 18 Des 2025 & aturan `ig-caption`), serta mengirim caption identik ke semua platform. | **FIXED** — Dibuat `growth.py` dengan formatter khusus per platform: `caption_ig` (maks 5 hashtag, tanpa URL, baris pertama <=125 char, 1 CTA tunggal, `#11` -> `Bagian 11`), `metadata_yt` (judul <=40 char front-loaded + `#Shorts`), `caption_tiktok`, dan `caption_fb`. |
| **F-05** | **P0** | `stiker.py`, `data/stiker/tabler.json` | **`'eye'` masuk daftar `TETAP`** di `stiker.py` dan 13 ikon organ wajah (`eye`, `eye:padat`, `eye-bolt`, `eye-closed`, `eye-dotted`, `eye-heart`, `eye-pin`, `eye-star`, `ear`, `eyeglass*`) masih ada di `tabler.json`, plus `'pig-money'` di kamus `'sedekah'`! | **FIXED** — `'eye'` dihapus dari `TETAP`, organ wajah (`eye`, `eyes`, `nose`, `mouth`, `ear`) & `pig` diblokir di `KATA_BUANG`, kamus dibersihkan, dan 13 ikon terlarang dipurge dari `data/stiker/tabler.json` (tersisa 1.078 stiker benda bersih). |
| **F-06** | **P1** | `remotion/src/Ilustrasi.tsx`, `Scenes.tsx` | Gerakan template pendek lama masih kaku (4 pose statis, tanpa sendi lengan/langkah/properti hidup, hook baru muncul setelah `delay=10..28`). | **FIXED** — Dibangun template baru `SunnahMotion` (`KarakterKaya.tsx` 8 pose artikulasi 4 varian 100% tanpa mata/hidung/mulut, `PropertiKaya.tsx` 12 properti animasi, `AdeganKaya.tsx` 21 adegan parallax termasuk 6 adegan baru, hook instan frame-0, kamera dorong/geser, embedded visual CTA & loop echo). |
| **F-07** | **P1** | `storyboard_ikon.py` | `KATA_TANPA_TOKOH` menggunakan `'nabi '` berspasi sehingga bentuk seperti `"Nabi,"`, `"beliau"`, `"sahabat"`, atau nama sahabat besar berisiko lolos. | **FIXED** — Ditambahkan `KATA_TANPA_TOKOH_RE` berbasis word-boundary regex yang memblokir tokoh pada seluruh segmen terkait Nabi ﷺ, para nabi, sahabat, dan malaikat (teruji otomatis di `tests/test_sunnah_compliance.py`). |
| **F-08** | **P1** | `main.py`, `posting_uji.py` | Pembukaan file teks/JSON/CSV tanpa `encoding='utf-8'` (rentan crash `UnicodeEncodeError` di Windows untuk simbol `ﷺ`, teks Arab, dan emoji) serta penggunaan `dt.datetime.utcnow()` yang deprecated di Python 3.12+. | **FIXED** — Seluruh operasi baca/tulis file menggunakan `encoding='utf-8'` dan diganti ke `_utc_now()` berbasis `dt.datetime.now(dt.timezone.utc)`. |
| **F-09** | **P1** | `video.py` | `susun_audio()` hanya memanggil `ffmpeg` dari PATH dan menulis backslash Windows mentah ke `daftar.txt` concat, menyebabkan gagal render lokal di Windows jika `ffmpeg` tidak terpasang global. | **FIXED** — Ditambahkan `_ffmpeg_bin()` dengan auto-fallback ke binary `ffmpeg` bawaan Remotion (`@remotion/compositor-*`) dan normalisasi path `/` di concat list. |
| **F-10** | **P1** | `remotion_video.py` | Audio Shorts dirender pada 24 kHz mono (kurang optimal untuk TikTok & sebagian perangkat seluler). | **FIXED** — Seluruh render Remotion (`SunnahDaily`, `SunnahMotion`, `SunnahPanjang`, `SunnahClay`) memakai AAC stereo 48 kHz 192 kbps (murni suara + SFX non-musik). |
| **F-11** | **P1** | `video_panjang.py`, `.github/workflows/video-panjang.yml` | Video panjang default berdurasi ~3 menit sehingga belum membuka iklan mid-roll YouTube (ambang >=8 menit, +~50% RPM per `/claude-youtube`). | **FIXED** — Ditambahkan preset `MODE_MONET=true` (`DURASI_TARGET=560`, `MAKS_KISAH=8`, Dual CTA di 1/3 & 2/3 video) tanpa merusak mode default 3 menit anak. |
| **F-12** | **P1** | Seluruh repo | Belum ada automated test suite untuk regresi uploader, kepatuhan aturan Sunnah, maupun pipeline growth. | **FIXED** — Dibuat 19 automated unit test di `tests/` (`test_sunnah_compliance.py`, `test_tiktok_and_uploaders.py`, `test_growth_and_pipeline.py`). |
| **F-13** | **P2** | `sfx.py` | `isyarat()` belum memiliki profil efek foley non-musik khusus untuk komposisi `SunnahMotion`. | **FIXED** — Profil `SunnahMotion` ditambahkan (properti pop, langkah berjalan lembut, CTA click) menggunakan 100% WAV non-musik CC0 dari `sfx/`. |
| **F-14** | **P2** | `.github/workflows/buat-video.yml` | Langkah instalasi Node/Remotion hanya aktif untuk `GAYA_TEMPLATE == 'remotion'`. | **FIXED** — Diperluas menjadi `env.GAYA_TEMPLATE == 'remotion' || env.GAYA_TEMPLATE == 'motion_kaya'` dengan default `motion_kaya`. |

---

## 3. Ringkasan Bug yang Tertangkap & Diperbaiki Selama QA Self-Healing Loop

1. **Bug `#11` di judul episode terhitung sebagai hashtag ke-6 IG/TikTok:** Terdeteksi oleh `test_caption_ig_patuh_aturan_ig_caption` & `test_metadata_yt_shorts_dan_caption_tiktok`. Diperbaiki lewat `_judul_kajian_tanpa_pagar()` di `growth.py` (`#11` -> `Bagian 11`).
2. **Bug `FileNotFoundError` pada `video.susun_audio()` di Windows tanpa `ffmpeg` global:** Terdeteksi saat render sampel `SunnahMotion`. Diperbaiki lewat `_ffmpeg_bin()` auto-fallback ke ffmpeg bawaan Remotion + normalisasi slash Windows di `video.py`.
3. **Poles visual pasca-inspeksi PNG:** Pose `berdoa` di `KarakterKaya.tsx` disesuaikan sudut sikunya agar kedua tangan terangkat rapi di depan dada, dan skala karakter pada `AdeganKaya.tsx` dibuat proporsional terhadap tinggi panggung sehingga tidak terpotong pada kartu pratinjau kecil `GaleriKaya`.

---

## 4. Bukti Verifikasi Independen

- **Unit Test Suite:** `python -m unittest discover -s tests -v` -> **19/19 PASS (0 failed, 0 skipped, 0 warnings)**.
- **Python Syntax Check:** `python -m py_compile ...` -> **EXIT 0**.
- **TypeScript Typecheck:** `npx.cmd tsc --noEmit` (di `d:\sunnah-daily\remotion`) -> **EXIT 0**.
- **Render Sampel Video MP4 Valid (`SunnahMotion`):**
  - File: `d:\sunnah-daily\hasil\sampel_sunnah_motion.mp4` (`2.482.236` bytes, 510 frame, 17.00 detik).
  - Video stream (`ffmpeg` probe): `h264 (avc1), yuv420p(tv, bt709), 1080x1920 [DAR 9:16], 30 fps`.
  - Audio stream (`ffmpeg` probe): `aac, 48000 Hz, stereo, fltp` — 24 efek SFX non-musik CC0 terpasang, **0 musik**.
- **Inspeksi Visual Frame & Contact Sheet:**
  - `hasil/galeri_kaya.png` (8 pose karakter across 4 varian + 12 properti + 6 adegan baru): **terverifikasi visual 100% tanpa mata, tanpa alis, tanpa hidung, tanpa mulut**.
  - `hasil/frame_000_hook.png` (hook instan frame-0 + safe zone kanan 234px & bawah 490px bersih), `frame_090_poin_a.png` -> `frame_110_poin_b.png` (progresi gerak berjalan + kamera zoom + stiker pop + karaoke aktif), `frame_265_dalil.png` (kartu hadits Arab Amiri + badge Shahih), `frame_415_faedah.png` (embedded visual CTA pill), `frame_485_penutup.png` (single CTA pill + loop echo + kredit).
- **Linter `ig-caption` (`caption.py`):** 8/9 PASS (length, first line <=125 char, concrete hook, <=5 hashtags, tag placement, no dead links, 0 emoji spam, search terms present; 1 WARN minor karena pola regex CTA bahasa Inggris pada caption bahasa Indonesia).
- **Simulasi Posting Otonom TikTok:** `tt.upload(mp4, cap_tt, dry_run=True)` -> `tiktok://dry-run/direct/SELF_ONLY/1chunks` + pengujian mock lengkap OAuth2 refresh, chunking `Content-Range`, fallback privasi `SELF_ONLY`, error redaction, serta regresi IG/YT/FB.

---

## 5. Audit Verdict (`/agentic-delivery` Stage 4 Gate)

### Audit Verdict: AUDIT_PASSED
- **Rules & Compliance:** **PASS** — 100% karakter & aset tanpa mata/alis/hidung/mulut (diverifikasi otomatis + inspeksi visual PNG); filter `KATA_TANPA_TOKOH_RE` memblokir penggambaran Nabi ﷺ, sahabat, dan malaikat; 0 musik di pipeline audio/SFX; 13 stiker mata/telinga dipurge dari `tabler.json`.
- **Tests & Build Freshness:** **PASS** — 19/19 unittest PASS, `py_compile` exit 0, `tsc --noEmit` exit 0, render nyata `sampel_sunnah_motion.mp4` + 7 PNG verifikasi sukses exit 0.
- **Security & Secrets:** **PASS** — Tidak ada API key/token hardcoded; `.gitignore` diperketat (`.env*`, `*.token`, `*.key`, `*.secret`, `credentials*.json`); `tt._redact()` menyensor token TikTok dari seluruh error/log.
- **Release Readiness:** **PASS** — TikTok menggunakan default privasi aman `SELF_ONLY` (tidak mempublikasikan live tanpa konfigurasi eksplisit `TT_PRIVACY=PUBLIC_TO_EVERYONE` dan kredensial aktif); dry-run sukses; auto-upload IG, YouTube, dan FB tetap utuh dan terisolasi per platform.
- **Blockers (if any):** None.
- **Langkah Manual Opsional untuk User:**
  1. Tambahkan GitHub Secrets TikTok (`TT_CLIENT_KEY`, `TT_CLIENT_SECRET`, `TT_REFRESH_TOKEN` atau `TT_ACCESS_TOKEN`) dan Repository Variable `TT_PRIVACY=PUBLIC_TO_EVERYONE` setelah aplikasi TikTok Developers lulus audit publik (uji koneksi lewat workflow **Posting Ulang** dengan `tujuan=cek-tt`).
  2. (Opsional) Hapus file installer lokal `aset/mentah/gerak/Antigravity-x64.exe` (182 MB) untuk menghemat ruang disk lokal.
