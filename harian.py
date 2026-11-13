"""Seri tambahan "Sunnah Harian": amalan & adab sunnah sehari-hari, template Animasi Ikon.

Materi ditulis Gemini + Google Search dari dalil SHAHIH/HASAN (diutamakan Bukhari-Muslim), lalu dicek ulang
oleh ekstrak.verifikasi (pemeriksa dalil yang sama dengan seri Sirah). Amalan yang hanya bersandar pada riwayat
lemah/palsu TIDAK diangkat (status Dilewati).

Data: data/kisah/harian.json  {"seri": "harian", "judul": "Sunnah Harian", "url": "", "kisah": [...]}
Topik: data/harian_topik.csv (No, Topik, Kategori). Tambah topik cukup tambah baris.
"""
import csv
import json
import os

import ekstrak
import gemini

ROOT = os.path.dirname(os.path.abspath(__file__))
PATH = os.path.join(ekstrak.DIR, 'harian.json')
TOPIK = os.path.join(ROOT, 'data', 'harian_topik.csv')

PROMPT = """Kamu tim riset konten akun dakwah "Sunnah Daily" yang memegang prinsip: hanya mengamalkan dalil shahih,
hadits lemah wajib disebut lemah. Topik video pendek (40-65 detik): "{topik}" (kategori {kategori}).

Cari dengan Google Search di sumber tepercaya (sunnah.com, dorar.net, hadits.id, quran.kemenag.go.id, rumaysho,
muslim.or.id, almanhaj, islamqa). Pilih SATU dalil utama yang SHAHIH atau HASAN (utamakan Bukhari/Muslim) atau ayat.
Kalau topik ini tidak punya dalil shahih, set "layak": false.

Tulis materi:
- judul_hook: maks 6 kata, bikin penasaran
- narasi_hook: 1 kalimat pembuka lisan
- adegan: 3-4 poin berurutan (apa amalannya, cara/waktunya, keutamaannya sesuai dalil), tiap poin 1-2 kalimat lisan
- faedah: 1 kalimat ajakan mengamalkan, maks 16 kata
Aturan: Bahasa Indonesia lisan yang hangat dan sederhana; tulis "Rasulullah ﷺ"/"Nabi ﷺ" dengan simbol ﷺ;
JANGAN menambah keutamaan/angka yang tidak ada di dalil; tanpa perselisihan kelompok. Narasi 70-100 kata.

Kembalikan JSON saja:
{{"judul_hook": "", "narasi_hook": "",
 "adegan": [{{"narasi": ""}}],
 "dalil": {{"jenis": "ayat|hadits", "arab": "teks Arab berharakat, maks 30 kata", "terjemah": "",
            "sumber": "QS. Nama: ayat / HR. Perawi no. X", "derajat": "ayat|shahih|hasan"}},
 "faedah": "", "tema": ["2-4 kata kunci"], "layak": true, "alasan": ""}}"""


def muat():
    if os.path.exists(PATH):
        with open(PATH, encoding='utf-8') as f:
            return json.load(f)
    return {'seri': 'harian', 'judul': 'Sunnah Harian', 'url': '', 'kisah': []}


def simpan(data):
    os.makedirs(ekstrak.DIR, exist_ok=True)
    with open(PATH, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=1)


def daftar_topik():
    with open(TOPIK, encoding='utf-8') as f:
        return [r for r in csv.DictReader(f)]


def tulis(topik, kategori):
    teks, sumber = gemini.cari(PROMPT.format(topik=topik, kategori=kategori))
    k = gemini.ambil_json(teks)
    k['sumber_riset'] = [s['uri'] for s in sumber[:6]]
    return k


def id_topik(t):
    return f"h{int(t['No']):03d}"


def pasang(data, t, k):
    """Masukkan materi k (hasil riset topik t, dari API atau stok manual) ke data; dalilnya belum dicek."""
    k['id'] = id_topik(t)
    k['topik'] = t['Topik']
    k['status'] = 'Belum' if k.get('layak', True) and k.get('adegan') and k.get('dalil') else 'Dilewati'
    k.pop('layak', None)
    data['kisah'] = [x for x in data['kisah'] if x['id'] != k['id']] + [k]
    return k


def pilih(no=None):
    """Kembalikan (data, kisah) berikutnya. Kisah 'Belum' yang sudah ada dipakai dulu; kalau tidak ada,
    tulis materi untuk topik berikutnya yang belum pernah dibuat."""
    data = muat()
    if not no:
        for k in data['kisah']:
            if k.get('status') == 'Belum':
                return data, k
    sudah = {k.get('topik') for k in data['kisah']}
    for t in daftar_topik():
        if no and int(t['No']) != int(no):
            continue
        if not no and t['Topik'] in sudah:
            continue
        gemini.log(f"Sunnah Harian: menulis materi '{t['Topik']}'")
        try:
            k = tulis(t['Topik'], t.get('Kategori', ''))
        except Exception as e:
            gemini.log(f'   gagal menulis materi: {e}')
            continue
        pasang(data, t, k)
        simpan(data)
        if k['status'] == 'Belum':
            return data, k
    raise SystemExit('Tidak ada topik Sunnah Harian yang tersisa. Tambah baris di data/harian_topik.csv.')


def caption(k):
    dl = k['dalil']
    derajat = f" · {dl['derajat'].capitalize()}" if dl.get('jenis') == 'hadits' and dl.get('derajat') else ''
    isi = ' '.join(a['narasi'] for a in k['adegan'])
    tag = ['sunnahdaily', 'sunnahharian', 'sunnah', 'hadits', 'amalansunnah', 'adabislami', 'belajarislam',
           'nasihatislam', 'dakwah'] + [t.replace(' ', '').lower() for t in k.get('tema', [])][:3]
    return (f"{k['judul_hook']} 🌙\n\n{isi}\n\n📖 {dl['terjemah']}\n({dl['sumber']}{derajat})\n\n"
            f"🤍 {k['faedah']}\n\nSimpan & bagikan, semoga jadi amal jariyah.\n\n"
            + ' '.join('#' + t for t in dict.fromkeys(tag) if t))
