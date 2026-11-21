# Sunnah Daily — Playbook Pertumbuhan & Monetisasi Menuju 1 Juta (YouTube, Instagram, TikTok)

Disusun langsung dari data dan aturan skill **`/claude-youtube`** (`shorts-playbook.md`, `retention-scripting-guide.md`, `monetization-guide.md`) dan skill **Instagram** (`ig-reel`, `ig-caption`), disesuaikan dengan prinsip dakwah **Sunnah Daily** (dalil shahih terverifikasi, tanpa musik, karakter tanpa mata/hidung/wajah, tanpa penggambaran Nabi ﷺ/sahabat/malaikat).

---

## 1. Keunggulan Struktural Sunnah Daily untuk Monetisasi

1. **100% Tanpa Musik = 100% Porsi Pool Shorts & Nol Risiko Content ID**
   - Berdasarkan `shorts-playbook.md`, memakai 1 lagu berlisensi memangkas porsi revenue pool YouTube Shorts kreator menjadi **50%** (2 lagu = **33%**), dan musik Content ID memblokir Shorts 1–3 menit secara global.
   - Karena Sunnah Daily murni narasi + efek suara non-musik CC0 (`sfx/`), kreator mempertahankan **100% alokasi pool** dan aman dari klaim hak cipta di YouTube, Instagram, Facebook, maupun TikTok.
2. **Keamanan terhadap Kebijakan YouTube "Inauthentic Content" (Juli 2025)**
   - Kebijakan YouTube Juli 2025 menargetkan konten templated/mass-produced berulang.
   - Solusi yang sudah ditanamkan di codebase:
     - **Template `SunnahMotion` (`GAYA=motion_kaya`)**: 21 adegan parallax berlapis, 8 pose karakter artikulasi tanpa wajah, 12 properti animasi, dan variasi stiker benda per narasi.
     - **Video panjang 16:9 `SunnahClay`**: diorama clay/stop-motion unik + kuis interaktif + verifikasi dalil terstruktur.

---

## 2. Arsitektur Hook, Retensi & CTA di Template `SunnahMotion`

| Elemen | Benchmark Skill (`/claude-youtube` & `ig-reel`) | Implementasi di Codebase |
|---|---|---|
| **Hook Frame-1 (0–2 detik)** | Viewed vs Swiped Away wajib **>= 75%** (<60% = hook rusak); kartu hook wajib tampil di **frame 1** tanpa intro salam. | `SunnahMotion.tsx` (`HookKaya`) menampilkan badge hook, judul <= 6 kata, dan panggung bergerak langsung pada **frame 0**. `growth.skor_hook()` menghukum pembuka lemah (`halo`, `selamat datang`, `di video ini`). |
| **Safe Zone 9:16 Lintas Platform** | `ig-reel`: `y` di `[230, 1440]`, kanan **230px bersih** (`x <= 850`) agar tidak tertutup tombol aksi IG/YT/TikTok. | `SAFE_KAYA` di `SunnahMotion.tsx` mengunci area konten di `x: 56..846` dan `y: 230..1430`. |
| **Visual Beat Cadence (2–3 detik)** | `shorts-playbook.md` & `retention-scripting-guide.md`: perubahan visual minimal setiap **2–3 detik** -> completion **70%+** memicu fase *Exploit*. | Kamera push-in/pan organik (`AdeganKaya.tsx`), karakter artikulasi bernapas & bergerak, properti pop-in, progress bar babak di header, karaoke kata aktif. |
| **Embedded Visual + Verbal CTA** | `retention-scripting-guide.md`: hanya **16%** penonton mencapai 10% akhir; CTA visual+verbal memberi **+380% konversi** (1 sub per 33 views vs 1 per 83 views). | `FaedahKaya` menampilkan pill CTA visual segera setelah faedah tersampaikan + `PenutupKaya` memakai **1 CTA tunggal** (`growth.cta_tunggal()`). |
| **Seamless Loop Ending** | `ig-reel` & `shorts-playbook.md`: Avg % Viewed **>100%** (replay/loop) adalah sinyal prioritas #2 setelah completion. | `PenutupKaya` menampilkan gema frasa hook (`loopEcho`) sehingga pemutaran ulang mulus kembali ke detik 0. |

---

## 3. Optimasi Distribusi Lintas-Platform (`growth.py` & `tt.py`)

### A. YouTube (Shorts + Long-Form Flywheel -> 1 Juta Subscriber & AdSense)
- **Mengapa menggabungkan Shorts + Long-Form?**
  - `shorts-playbook.md`: channel yang menjalankan keduanya tumbuh **40–60% lebih cepat** (overlap audiens hanya ~10%, sehingga saling memperluas jangkauan tanpa kanibalisasi).
  - `monetization-guide.md`: RPM Shorts tipikal $0.01–$0.07 per 1K views, sedangkan Long-Form Edukasi mencapai **$8–$15 RPM** (dan audiens US/UK 5–8x lebih bernilai).
- **Bridge Long-Form 8+ Menit (`video_panjang.py` `MODE_MONET=true`):**
  - Melewati ambang **8 menit** membuka **iklan mid-roll** (~**+50% pendapatan iklan**) dengan **Dual CTA** pada ~1/3 dan ~2/3 durasi video (menjangkau 60% dan 35% penonton aktif).
- **SEO & Metadata (`growth.metadata_yt`):**
  - Judul Shorts front-loaded <= 40 karakter tampil + `#Shorts`.
  - 125 karakter pertama deskripsi berisi hook + kata kunci alami + kredit kajian Ust. Dr. Firanda Andirja + tautan timestamp + jembatan ke episode panjang.

### B. Instagram Reels -> 1 Juta Follower
- **Caption Job A (`growth.caption_ig`)**:
  - Video sudah membawa hook -> 125 karakter pertama caption langsung menyampaikan **1 ajakan tunggal + konteks** tanpa emoji pembuka atau salam.
  - **Maksimal 5 hashtag spesifik** (patuh aturan resmi Instagram 18 Desember 2025), 0 filler tag (`#fyp`, `#viral`, `#reels`).
  - **Tanpa URL di caption** (link tidak dapat diklik di IG; arahkan ke bio/YouTube).
  - Kata kunci pencarian alami (`sirah nabawiyah`, `amalan sunnah harian`, `hadits shahih`) tertanam dalam kalimat biasa.

### C. TikTok Otonom (`tt.py`) -> 1 Juta Follower
- **Upload Tanpa Watermark:** File MP4 1080x1920 48kHz stereo AAC murni dari Remotion langsung diunggah lewat **TikTok Content Posting API v2** (`FILE_UPLOAD` chunked) — tanpa watermark platform lain sehingga tidak ditekan algoritma.
- **Mode Aman Default:** `TT_PRIVACY=SELF_ONLY` (aman selama aplikasi TikTok belum lulus audit publik), dapat dinaikkan ke `PUBLIC_TO_EVERYONE` lewat GitHub Repo Variable `TT_PRIVACY` setelah aplikasi lulus audit TikTok Developers.
- **Setup Kredensial TikTok di GitHub Secrets / Variables:**
  - Secrets: `TT_CLIENT_KEY`, `TT_CLIENT_SECRET`, `TT_REFRESH_TOKEN` (atau `TT_ACCESS_TOKEN`).
  - Variables: `TT_MODE=direct` (atau `inbox` untuk draft), `TT_PRIVACY=SELF_ONLY` -> `PUBLIC_TO_EVERYONE`.

---

## 4. Peta Jalan Bertahap Menuju 1 Juta & Monetisasi

| Fase | Target | Fokus Eksekusi |
|---|---|---|
| **Fase 1 (Hari 1–30): Validasi Hook & Konsistensi** | YPP Expanded (500 subs + 3K jam / 3M Shorts), 10K IG & TikTok | 5 video pendek/hari (`05.17, 11.47, 15.37, 18.47, 21.13 WIB`) via `motion_kaya` + 1 video panjang/minggu (`MODE_MONET=true`). Pantau metrik **Viewed vs Swiped Away** (jika <60%, ganti rumus hook). |
| **Fase 2 (Bulan 2–4): Monetisasi Penuh YPP** | YPP Full (1K subs + 4K jam / 10M Shorts), 100K lintas platform | Aktifkan AdSense + Super Thanks (aktif di Shorts & Long-Form) + 2–3 tier Channel Membership (tanpa paywall konten utama). Uji seri khusus Ramadan/Haji/Sirah berurutan (playlist binge). |
| **Fase 3 (Bulan 5–12+): Skala 1 Juta & Diversifikasi** | 1M YT / 1M IG / 1M TikTok | Gandakan topik outlier (yang retensinya >15% di atas rata-rata channel -> **2.3x dorongan algoritma**), tambahkan seri versi bahasa Inggris (target RPM edukasi US/UK 5–8x lebih tinggi) & produk digital halal (buku saku Sirah/kartu hafalan anak). |
