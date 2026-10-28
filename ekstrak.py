"""Ambil kisah + dalil dari satu episode kajian (Gemini menonton video YouTube), lalu verifikasi dalil
dengan Google Search. Hasil disimpan di data/kisah/epNNN.json supaya episode tidak ditonton ulang."""
import json
import os

import gemini
import ilustrasi

DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'data', 'kisah')

PROMPT_EKSTRAK = """Kamu tim riset konten untuk akun dakwah "Sunnah Daily" (IG Reels & YouTube Shorts).
Video ini kajian "{judul}" oleh Ust. Dr. Firanda Andirja, M.A. Tonton dan dengarkan SELURUH video.

Pilih {n} kisah atau faedah yang paling menyentuh, bisa berdiri sendiri, dan cocok untuk video 45-70 detik.
Urutkan sesuai urutan di video.

ATURAN KERAS:
- Ambil HANYA yang benar-benar disampaikan ustadz di video. Jangan menambah peristiwa, nama, angka atau kutipan.
- Bahasa Indonesia lisan yang santun, hangat, sederhana. Sebut "Rasulullah ﷺ" / "Nabi ﷺ" (tulis simbol ﷺ),
  sahabat dengan "radhiyallahu 'anhu" pada sebutan pertama.
- Jangan memasukkan perselisihan/kritik terhadap kelompok atau tokoh tertentu.
- Dalil: ayat atau hadits yang dibacakan/disebut ustadz untuk kisah itu. Kalau ustadz tidak menyebut dalil,
  pilih ayat/hadits SHAHIH yang paling relevan dan tandai "dari_video": false.
  Tulis teks Arab berharakat hanya jika kamu yakin; kalau ragu kosongkan "arab" (akan dicek ulang).
- Catat derajat hadits kalau ustadz menyebutkannya.
- Narasi seluruh adegan 70-110 kata. Hook berupa pertanyaan/pernyataan yang bikin penasaran, maks 6 kata.
- Latar adegan WAJIB salah satu kunci ini: {latar}
  Tidak ada penggambaran Nabi ﷺ, sahabat, atau malaikat; latar hanya tempat dan benda.

Kembalikan JSON saja:
{{"kisah": [{{
  "menit": "mm:ss di video",
  "judul_hook": "maks 6 kata",
  "narasi_hook": "kalimat pembuka lisan = hook, 1 kalimat",
  "latar_hook": "kunci latar",
  "adegan": [{{"narasi": "1-2 kalimat dibacakan", "latar": "kunci latar"}}],
  "dalil": {{"jenis": "ayat|hadits", "arab": "", "terjemah": "", "sumber": "QS. Nama: ayat / HR. Perawi no. X",
            "derajat_kata_ustadz": "", "dari_video": true}},
  "faedah": "1 kalimat pelajaran praktis untuk kehidupan sekarang, maks 16 kata",
  "latar_faedah": "kunci latar",
  "tema": ["2-4 kata kunci topik"]
}}]}}"""

PROMPT_CEK = """Kamu pemeriksa dalil untuk akun dakwah yang memegang prinsip: hadits lemah WAJIB disebut lemah.
Periksa dengan Google Search di sumber tepercaya (sunnah.com, dorar.net, hadits.id, quran.kemenag.go.id,
tafsirweb, islamqa, almanhaj, rumaysho, muslim.or.id).

Kisah: {narasi}
Dalil: {dalil}

Tugas:
1. Pastikan teks Arab benar, lengkap berharakat, dan sesuai sumber. Kalau dalil panjang, potong ke bagian yang
   relevan dengan "..." (maks 30 kata Arab).
2. Pastikan sumber benar (nama surah & nomor ayat / perawi & nomor hadits).
3. Tentukan derajat hadits menurut ulama hadits (Bukhari/Muslim = shahih; selain itu sebut penilainya, mis.
   Syaikh Al-Albani). Ayat: derajat "ayat".
4. Periksa narasi kisah: apakah ada bagian yang hanya berasal dari riwayat lemah/palsu atau keliru? Kalau ada,
   perbaiki kalimatnya agar sesuai riwayat yang shahih, atau tandai.
5. Terjemah Bahasa Indonesia yang ringkas dan tepat.

Kembalikan JSON saja:
{{"dalil": {{"jenis": "ayat|hadits", "arab": "", "terjemah": "", "sumber": "",
            "derajat": "ayat|shahih|hasan|lemah|palsu", "penilai": "", "rujukan": "URL"}},
 "kisah_lemah": false,
 "catatan_kisah": "kosong jika aman; jelaskan jika ada bagian yang lemah/keliru",
 "narasi_perbaikan": ["isi HANYA jika ada adegan yang harus diubah: narasi adegan lengkap pengganti, urut"],
 "layak": true}}"""


def path_ep(no):
    return os.path.join(DIR, f'ep{int(no):03d}.json')


def ekstrak(no, judul, url, n=8):
    p = path_ep(no)
    if os.path.exists(p):
        with open(p) as f:
            return json.load(f)
    latar = ', '.join(f'{k} ({v})' for k, v in ilustrasi.LATAR.items())
    gemini.log(f'Menonton episode {no}: {judul}')
    hasil = gemini.teks(PROMPT_EKSTRAK.format(judul=judul, n=n, latar=latar), video=url, suhu=0.3)
    kisah = hasil.get('kisah') if isinstance(hasil, dict) else hasil
    data = {'episode': int(no), 'judul': judul, 'url': url, 'kisah': kisah or []}
    for i, k in enumerate(data['kisah']):
        k['id'] = f'ep{int(no):03d}-{i + 1:02d}'
        k['status'] = 'Belum'
    simpan(data)
    return data


def simpan(data):
    os.makedirs(DIR, exist_ok=True)
    with open(path_ep(data['episode']), 'w') as f:
        json.dump(data, f, ensure_ascii=False, indent=1)


def verifikasi(k):
    """Cek dalil & kisah. Mengubah k di tempat, kembalikan True kalau layak tayang."""
    narasi = ' '.join([k.get('narasi_hook', '')] + [a['narasi'] for a in k.get('adegan', [])])
    teks, sumber = gemini.cari(PROMPT_CEK.format(narasi=narasi, dalil=json.dumps(k['dalil'], ensure_ascii=False)))
    hasil = gemini.ambil_json(teks)
    dl = hasil.get('dalil') or {}
    if not dl.get('terjemah') or not dl.get('sumber'):
        raise ValueError('verifikasi tanpa dalil yang lengkap')
    dl['derajat'] = (dl.get('derajat') or '').lower().replace('dhaif', 'lemah').replace("dha'if", 'lemah')
    k['dalil'] = dl
    k['cek'] = {'kisah_lemah': hasil.get('kisah_lemah'), 'catatan': hasil.get('catatan_kisah', ''),
                'sumber_cek': [s['uri'] for s in sumber[:6]]}
    pengganti = hasil.get('narasi_perbaikan') or []
    if pengganti and len(pengganti) == len(k['adegan']):
        for a, n in zip(k['adegan'], pengganti):
            if n and n.strip():
                a['narasi'] = n.strip()
    layak = bool(hasil.get('layak', True)) and dl['derajat'] != 'palsu'
    k['layak'] = layak
    return layak
