# Aset Video Panjang Gaya Clay: Daftar & Prompt Meta AI

Target penonton: anak-anak sampai dewasa, termasuk penonton US/UK yang belum Muslim. Gayanya **clay/stop-motion
yang ceria dan hangat**, mirip contoh karakter kakek bersorban dan anak laki-laki.

Prompt ditulis dalam **bahasa Inggris**, karena Meta AI paling patuh dengan bahasa Inggris. Penjelasannya dalam
bahasa Indonesia.

---

## 1. Cara kerja: kenapa asetnya dipecah-pecah

Supaya video "hidup" seperti animasi, gambarnya **tidak dibuat sekali jadi**, tapi dipecah jadi potongan yang
nanti digerakkan Remotion:

| Potongan | Gerakannya di video |
|---|---|
| **Latar kosong** (tanpa orang) | kamera pelan zoom/geser (efek film), parallax |
| **Elemen gerak** (awan, matahari, api, bendera, burung) | melayang, berkedip, berkibar di atas latar |
| **Karakter per pose** (berdiri, jalan A, jalan B, menunjuk, ...) | masuk dari samping, jalan (ganti pose A/B + memantul), bernapas, menoleh (dicerminkan) |
| **Properti** (kurma, kendi, koin, surat, ...) | muncul memantul, berputar, jatuh, bergoyang |

Kalau mau, **latar juga bisa dianimasikan langsung di Meta AI** (tombol *Animate*), hasilnya klip MP4 pendek
yang diputar berulang. Prompt gerakannya ada di bagian 8.

---

## 2. Aturan wajib (cek SETIAP gambar sebelum disimpan)

1. **Nabi Muhammad ﷺ, para nabi lain, dan malaikat TIDAK PERNAH dibuat**, dalam bentuk apa pun, termasuk siluet,
   punggung, tangan, bayangan, atau cahaya berbentuk orang. Adegan tentang beliau cukup pakai **latar + properti**.
2. **Manusia lain boleh digambar asal tanpa wajah**, termasuk keluarga Nabi ﷺ (Abdul Muthalib, Abu Thalib, Aminah,
   Halimah, istri-istri dan putri beliau) dan para sahabat (Abu Bakar, Bilal, Hamzah, dan lain-lain). Tokoh wanita
   selalu berpakaian longgar dan berhijab.
3. **Jangan sampai ada sosok yang bisa disangka Nabi ﷺ.** Di adegan yang menceritakan beliau, sahabat/keluarga
   boleh tampil, tapi posisinya jangan seolah sedang berhadapan atau berjalan bersama "seseorang" yang tidak
   digambar, dan tidak ada sosok laki-laki tanpa nama di tengah adegan. Kalau ragu, pakai latar + properti saja.
4. **Semua manusia DAN hewan TANPA MATA dan TANPA ALIS** (wajib). Prompt tetap minta wajah polos; kalau di
   video muncul **mulut** (bicara, senyum) itu masih boleh. Kalau muncul **mata atau alis**, walau sebentar, bagian
   itu dibuang (potong klipnya) atau generate ulang.
5. Tidak ada patung berhala, salib, atau simbol agama lain. Tidak ada tulisan atau huruf di gambar.
6. Tidak ada darah, luka, atau adegan seram. Perang cukup digambarkan dengan tenda, panji polos, pedang
   bersarung, dan debu.
7. Kalau gambar dari Meta AI ada **watermark yang kelihatan**, jangan dipotong sendiri; kabari aku dulu.
   Cek juga syarat pemakaian Meta AI untuk konten yang dimonetisasi.

---

## 3. Cara generate di Meta AI

1. **Gabungkan**: `[BLOK GAYA yang sesuai]` + `[deskripsi item]`. Tempel jadi satu prompt.
2. **Rasio**: karakter & hewan pilih **9:16 / potret**; properti & elemen pilih **1:1**; latar pilih **16:9**.
3. **Biar karakternya konsisten**: generate dulu **pose P01** satu karakter, pilih hasil terbaik. Untuk pose lain,
   **unggah gambar P01 itu** ke Meta AI lalu tulis:
   `Same exact character as the uploaded image (same clothes, colors, proportions, clay texture). Now: [pose].`
   + BLOK GAYA KARAKTER.
4. Latar belakang putih polos memang disengaja: nanti aku hapus otomatis jadi PNG transparan, lalu dirapikan dan
   dikecilkan ukurannya.
5. Simpan hasil ke `D:\sunnah-daily\aset\mentah\<kategori>\` dengan nama sesuai kolom **File** di tabel
   (mis. `aset/mentah/karakter/k01_p03.png`). PNG atau JPG dua-duanya oke.

---

## 4. BLOK GAYA (copy persis, jangan diubah supaya semua aset seragam)

**GAYA KARAKTER** (manusia & hewan):
```
Handmade claymation figure in a cozy stop-motion children's animation style. Soft plasticine clay with visible fingerprints, gentle tool marks and tiny cracks. Cute chibi proportions with a big round head and short body. Completely blank, smooth face: NO eyes, NO eyebrows, NO nose, NO mouth (a faceless figure). Warm cheerful earthy palette: terracotta, cream, sand beige, olive green, soft sky blue, warm grey. Soft diffused studio lighting. Full body, centered, entire figure visible including feet, isolated on a plain pure white background, no floor, no cast shadow. Single subject only. Avoid: text, letters, logo, watermark, extra characters, eyes, mouth, scary look.
```

**GAYA PROPERTI** (benda & elemen gerak):
```
Handmade claymation object for a cozy stop-motion children's animation. Soft plasticine clay with visible fingerprints and gentle tool marks, slightly rounded chunky shapes, warm cheerful earthy palette with soft highlights. Soft diffused studio lighting. Single object, centered, fully visible, isolated on a plain pure white background, no cast shadow. Avoid: text, letters, logo, watermark, people, faces, hands.
```

**GAYA LATAR** (lokasi):
```
Handmade claymation diorama set for a cozy stop-motion children's animation, wide 16:9 cinematic view. Everything sculpted from plasticine clay with visible fingerprints and tool marks, miniature model look, soft tilt-shift depth of field. Warm cheerful colors, soft diffused lighting, gentle atmosphere. Empty scene with NO people and NO animals, with open space in the lower middle for characters to stand. Avoid: text, letters, signs, logo, watermark, statues, idols, faces.
```

Contoh prompt lengkap (karakter K01 pose P03):
```
Handmade claymation figure in a cozy stop-motion children's animation style. [... seluruh GAYA KARAKTER ...] Subject: an elderly Arab man with a large cream wrapped turban, short grey clay beard, long terracotta robe with a tied belt, brown boots. Pose: walking to the right, side 3/4 view, left foot forward, arms swinging slightly.
```

---

## 5. KARAKTER UMUM

**Kode pose** (tambahkan di akhir prompt sebagai `Pose: ...`):

| Kode | Pose (teks untuk prompt) |
|---|---|
| P01 | standing, front view, arms relaxed at sides |
| P02 | standing, 3/4 view facing right |
| P03 | walking to the right, side 3/4 view, left foot forward, arms swinging slightly |
| P04 | walking to the right, side 3/4 view, right foot forward, arms swinging slightly (same character, mid-step) |
| P05 | pointing forward to the right with one arm extended |
| P06 | sitting cross-legged on the ground, hands on knees, front view |
| P07 | standing with both palms raised in front of the chest in supplication, front view |
| P08 | surprised, both hands on cheeks, leaning back slightly |
| P09 | sad, head lowered, shoulders dropped, hands clasped |
| P10 | arguing, one fist raised, body leaning forward (not violent) |
| P11 | carrying a sack on the shoulder, walking to the right |

Cukup buat yang menghadap **kanan**; yang menghadap kiri nanti aku cerminkan di kode.

| ID | Karakter (deskripsi untuk prompt `Subject:`) | Pose yang dibuat | File |
|---|---|---|---|
| K01 | an elderly Arab man with a large cream wrapped turban, short grey clay beard, long terracotta robe with a tied belt, brown boots *(contoh bro)* | P01–P09 | `karakter/k01_pXX.png` |
| K02 | a wealthy Quraysh chief, plump, dark wrapped turban, rich deep purple robe with golden trim, small gold rings, black clay beard; looks proud but cute, not scary | P01–P05, P08, P10 | `karakter/k02_pXX.png` |
| K03 | a young Arab man, simple white head cloth with a dark cord, sand-beige tunic and olive vest, sandals | P01–P06, P08 | `karakter/k03_pXX.png` |
| K04 | a friendly merchant with a striped olive-and-cream turban, mustard robe, leather pouch on belt | P01–P05, P11 | `karakter/k04_pXX.png` |
| K05 | a mother wearing a long loose sky-blue abaya and a cream hijab covering the hair and neck, modest, long sleeves | P01–P03, P06, P07, P09 | `karakter/k05_pXX.png` |
| K06 | a grandmother in a loose dark-green abaya and wide cream hijab, holding a small walking stick | P01–P03, P06, P07 | `karakter/k06_pXX.png` |
| K07 | a little boy with tousled grey clay hair, cream long shirt with buttons, cream trousers, soft shoes *(contoh bro)* | P01–P06, P08 | `karakter/k07_pXX.png` |
| K08 | a little girl in a rose-pink long dress and a small cream hijab, soft shoes | P01–P06, P08 | `karakter/k08_pXX.png` |
| K09 | a foreign king (Roman/Persian style) with a simple golden crown, red royal cloak over a white tunic, short brown beard | P01, P02, P05, P06 (seated on a throne) | `karakter/k09_pXX.png` |
| K10 | an enemy soldier with a round clay helmet, leather armor over a red tunic, holding a spear upright and a round shield (cute, not scary) | P01–P04 | `karakter/k10_pXX.png` |
| K11 | a shepherd boy with a brown head cloth, sand tunic, holding a wooden staff | P01–P04 | `karakter/k11_pXX.png` |
| K12 | an old scholar of the People of the Book, long dark-grey robe, small cap, white beard, holding a rolled scroll (no religious symbols) | P01, P02, P05, P06 | `karakter/k12_pXX.png` |
| K13 | a small crowd of 5 mixed townspeople (men, women in hijab, children) standing together, seen from behind | 1 gambar | `karakter/k13_kerumunan.png` |
| K14 | a small group of 4 enemy soldiers marching to the right with spears and plain banners, seen from the side | 1 gambar | `karakter/k14_pasukan.png` |

### Tokoh bernama (keluarga Nabi ﷺ & sahabat, tetap tanpa wajah)

Tiap tokoh punya pakaian khas supaya penonton bisa mengenalinya dari episode ke episode. Pose sama dengan tabel
di atas.

| ID | Tokoh | Deskripsi untuk prompt `Subject:` | Pose | File |
|---|---|---|---|---|
| T01 | Abdul Muthalib (kakek) | a dignified very old Arab chief with a long white clay beard, white wrapped turban, cream robe with a long dark-brown cloak, holding a wooden staff | P01–P03, P06 | `karakter/t01_pXX.png` |
| T02 | Abu Thalib (paman) | an older Arab man with a grey-and-black beard, olive-green turban, long sand-beige robe with a brown cloak | P01–P03, P06, P09 | `karakter/t02_pXX.png` |
| T03 | Aminah (ibu) | a young mother in a long loose cream abaya and a soft white hijab covering hair and neck | P01–P03, P06 | `karakter/t03_pXX.png` |
| T04 | Halimah (ibu susu) | a countrywoman in a loose earthy-brown abaya and an olive hijab, with a small woven basket | P01–P03, P06 | `karakter/t04_pXX.png` |
| T05 | Khadijah | a graceful noblewoman in a loose deep-green abaya with subtle gold trim and a long cream hijab | P01–P03, P06, P07 | `karakter/t05_pXX.png` |
| T06 | Abu Bakar | a slim gentle Arab man with a short neat beard, white turban, simple white robe with a light-grey cloak | P01–P07 | `karakter/t06_pXX.png` |
| T07 | Bilal | a tall dark-skinned man (dark brown clay) with a short black beard, simple cream head cloth, plain beige tunic | P01–P07 | `karakter/t07_pXX.png` |
| T08 | Hamzah | a strong broad-shouldered Arab man with a black beard, dark-red turban, leather vest over a sand tunic, a bow on his back | P01–P05 | `karakter/t08_pXX.png` |
| T09 | Abu Lahab (musyrik) | a plump Arab man with a red beard, orange turban, flashy red-and-gold robe; looks grumpy but cute, not scary | P01–P05, P10 | `karakter/t09_pXX.png` |
| T10 | Abu Jahal (musyrik) | an Arab man with a pointed black beard, black turban, dark purple robe with a silver belt; looks arrogant but cute, not scary | P01–P05, P10 | `karakter/t10_pXX.png` |

Catatan: T01–T08 jangan pernah ditaruh seolah sedang bersama "seseorang" yang tidak digambar (lihat aturan nomor 3).

---

## 6. HEWAN (juga tanpa mata & mulut, pakai GAYA KARAKTER)

Tambahkan kalimat ini di prompt hewan: `The animal has a smooth blank head with no eyes and no mouth.`

| ID | Hewan | Variasi | File |
|---|---|---|---|
| H01 | a cute camel with a woven saddle blanket | berdiri, jalan A, jalan B, duduk | `hewan/h01_<variasi>.png` |
| H02 | a camel loaded with trade sacks and rolled carpets | jalan A, jalan B | `hewan/h02_<variasi>.png` |
| H03 | a small white sheep | berdiri, merumput (kepala menunduk) | `hewan/h03_<variasi>.png` |
| H04 | a group of 5 sheep and goats grazing | 1 gambar | `hewan/h04_kawanan.png` |
| H05 | a horse with a simple saddle | berdiri, berlari | `hewan/h05_<variasi>.png` |
| H06 | a big grey elephant with a decorated red cloth | berdiri, berlutut | `hewan/h06_<variasi>.png` |
| H07 | a small bird carrying a tiny pebble, wings spread | sayap atas, sayap bawah | `hewan/h07_<variasi>.png` |
| H08 | a white dove | terbang sayap atas, sayap bawah, hinggap | `hewan/h08_<variasi>.png` |
| H09 | a small cute spider on a round clay spider web | 1 gambar | `hewan/h09_laba.png` |
| H10 | a brown cow | berdiri | `hewan/h10_sapi.png` |

---

## 7. PROPERTI (pakai GAYA PROPERTI)

| ID | Benda (deskripsi untuk prompt) | File |
|---|---|---|
| B01 | a clay plate full of dates | `properti/b01_kurma.png` |
| B02 | a tall clay water jug with a handle | `properti/b02_kendi.png` |
| B03 | a wooden bowl of milk | `properti/b03_susu.png` |
| B04 | two round flat breads | `properti/b04_roti.png` |
| B05 | a small pile of shiny gold coins with an open leather pouch | `properti/b05_koin.png` |
| B06 | a bulging trade sack tied with rope | `properti/b06_karung.png` |
| B07 | a rolled letter scroll with a red wax seal (no writing visible) | `properti/b07_surat.png` |
| B08 | a parchment document pinned on a wooden board, edges eaten by tiny termites (no writing visible) | `properti/b08_piagam.png` |
| B09 | an oil lamp with a small flame | `properti/b09_pelita.png` |
| B10 | a lantern with a warm glowing light | `properti/b10_lentera.png` |
| B11 | a burning torch | `properti/b11_obor.png` |
| B12 | a small campfire with stones around it | `properti/b12_api_unggun.png` |
| B13 | a curved sword in its sheath | `properti/b13_pedang.png` |
| B14 | a spear and a round shield | `properti/b14_tombak_perisai.png` |
| B15 | a wooden bow with arrows in a quiver | `properti/b15_busur.png` |
| B16 | a plain cloth banner on a pole (no symbols) | `properti/b16_panji.png` |
| B17 | a stone well with a wooden bucket and rope | `properti/b17_sumur.png` |
| B18 | a shepherd's wooden staff | `properti/b18_tongkat.png` |
| B19 | a golden crown | `properti/b19_mahkota.png` |
| B20 | a royal wooden throne with cushions | `properti/b20_singgasana.png` |
| B21 | a folded patterned carpet and a cushion | `properti/b21_permadani.png` |
| B22 | a closed holy book wrapped in green cloth on a wooden stand | `properti/b22_kitab.png` |
| B23 | a reed pen and an ink pot | `properti/b23_pena.png` |
| B24 | a balance scale | `properti/b24_timbangan.png` |
| B25 | a small wooden sailing boat | `properti/b25_perahu.png` |
| B26 | a desert tent made of striped cloth | `properti/b26_tenda.png` |
| B27 | a big flat rock under the sun (hot stone) | `properti/b27_batu.png` |
| B28 | a wooden ladder reaching upward into clouds | `properti/b28_tangga.png` |

**Elemen gerak** (dibuat terpisah supaya bisa melayang/berkedip di atas latar):

| ID | Elemen | File |
|---|---|---|
| E01–E03 | a soft fluffy clay cloud (3 different shapes) | `elemen/e01_awan.png` … `e03` |
| E04 | a round warm sun with soft glow | `elemen/e04_matahari.png` |
| E05 | a crescent moon | `elemen/e05_bulan.png` |
| E06 | a small five-point clay star (golden) | `elemen/e06_bintang.png` |
| E07 | a tall date palm tree | `elemen/e07_kurma.png` |
| E08 | a desert bush and small rocks | `elemen/e08_semak.png` |
| E09 | a puff of sand dust | `elemen/e09_debu.png` |
| E10–E12 | a flame, 3 slightly different shapes (for flicker) | `elemen/e10_api.png` … `e12` |
| E13 | a small sea wave | `elemen/e13_ombak.png` |

---

## 8. LOKASI / LATAR (pakai GAYA LATAR, rasio 16:9)

Buat semuanya **kosong tanpa orang**. Kalau mau dianimasikan di Meta AI (*Animate*), pakai prompt gerak di kolom
terakhir. Hasil MP4-nya disimpan dengan nama yang sama berakhiran `_gerak.mp4`.

| ID | Lokasi (deskripsi untuk prompt `Scene:`) | Prompt gerak (Meta AI Animate) | File |
|---|---|---|---|
| L01 | sunny desert with soft rolling sand dunes and a clear blue sky | sand blowing gently, clouds drifting slowly, static camera | `latar/l01_gurun_siang.png` |
| L02 | desert dunes at golden sunset, warm orange sky | sun slowly lowering, light shimmer, static camera | `latar/l02_gurun_senja.png` |
| L03 | desert at night under a starry sky and crescent moon | stars twinkling softly, static camera | `latar/l03_gurun_malam.png` |
| L04 | old Makkah town: cube-shaped mud-brick houses in a rocky valley between mountains, daytime | clouds drifting, cloth awnings fluttering, static camera | `latar/l04_makkah_siang.png` |
| L05 | the same old Makkah town at night with warm glowing windows | windows flickering warmly, stars twinkling | `latar/l05_makkah_malam.png` |
| L06 | the Kaaba in the distance: a simple black cube with a gold band, in an open sandy courtyard, valley and mountains behind, no people | clouds drifting slowly, static camera | `latar/l06_kabah.png` |
| L07 | a small rocky hill (Safa) at the edge of the old town, morning light | soft morning light rays, clouds drifting | `latar/l07_bukit_shafa.png` |
| L08 | a tall rocky mountain with a small cave opening near the top, glowing softly, night sky | soft glow pulsing from the cave, stars twinkling | `latar/l08_gua_gunung.png` |
| L09 | inside a small dark cave looking out to a starry sky, a spider web at the entrance | stars twinkling outside, static camera | `latar/l09_dalam_gua.png` |
| L10 | a green Bedouin village in the countryside: striped tents, grass, sheep pen (no animals), small hills | grass swaying, clouds drifting | `latar/l10_desa_badui.png` |
| L11 | a busy-looking marketplace with empty stalls, colorful cloth awnings, pottery and baskets | awnings fluttering gently | `latar/l11_pasar.png` |
| L12 | inside a simple Arab house: mud walls, a carpet, cushions, a small window with sunlight | dust motes floating in sunlight | `latar/l12_rumah_dalam.png` |
| L13 | a dry, barren rocky valley with a few withered bushes (place of the boycott) | dust blowing softly, heat haze | `latar/l13_lembah_tandus.png` |
| L14 | a calm seashore with a small wooden sailing ship at the water | waves rolling gently, ship rocking softly | `latar/l14_pantai_kapal.png` |
| L15 | an African royal palace hall with tall wooden pillars, woven mats and warm light | curtains swaying, light shimmer | `latar/l15_istana_afrika.png` |
| L16 | a Roman marble palace hall with columns and a red curtain | curtain swaying gently | `latar/l16_istana_romawi.png` |
| L17 | a green date palm garden with a stone well (Madinah) | palm leaves swaying, birds far away | `latar/l17_kebun_kurma.png` |
| L18 | a very simple early mosque: mud-brick walls, palm-trunk pillars, roof of palm leaves, open courtyard | palm leaves on the roof moving slightly | `latar/l18_masjid_awal.png` |
| L19 | a wide open desert valley with a well and sand hills (battlefield, empty, peaceful) | dust drifting, banners far away fluttering | `latar/l19_lembah_perang.png` |
| L20 | a big red-brown mountain over a plain | clouds drifting | `latar/l20_gunung_uhud.png` |
| L21 | a long dug trench in front of a town | dust drifting | `latar/l21_parit.png` |
| L22 | a stone fortress on a hill among palm trees | flags fluttering on the towers | `latar/l22_benteng.png` |
| L23 | a big shady tree on an open plain | leaves swaying | `latar/l23_pohon_besar.png` |
| L24 | green mountain town with vineyards (Taif) | vines swaying, clouds drifting | `latar/l24_kebun_anggur.png` |

---

## 9. Prioritas (biar nggak harus bikin semua sekaligus)

**Batch 1, cukup untuk Sirah #1–#12:**
- Karakter: **K01, K02, K03, K05, K07, K08, K09, K10, K13** (P01, P02, P03, P04 dulu)
- Tokoh: **T01–T10** (P01, P02, P03, P04 dulu)
- Hewan: **H01, H02, H03, H06, H07**
- Properti: **B01, B02, B05, B07, B08, B09, B10, B13, B17, B19, B21, B22, B25, B27**
- Elemen: **E01–E07, E10–E12**
- Latar: **L01, L02, L03, L04, L05, L06, L07, L08, L10, L11, L12, L13, L14, L15, L16**

Batch berikutnya (Madinah, perang, haji) dibuat menyusul sesuai episode yang mau dirender.

Setelah file masuk ke `aset/mentah/`, kabari aku: aku rapikan (hapus latar putih, potong, kompres), buat daftar
aset untuk dipilih Gemini per babak, lalu sambungkan ke template video panjang.
