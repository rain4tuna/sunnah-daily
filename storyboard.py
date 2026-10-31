"""Storyboard gaya Sirah #01: Gemini menyusun kisah yang sudah terverifikasi menjadi babak-babak visual
(lihat motion.py). Isi dan fakta tetap dari kisah; Gemini hanya menata visual dan merapikan narasi lisan.
Hasil disimpan di kisah['storyboard'] supaya render ulang konsisten."""
import json

import gemini
import ilustrasi

LANGIT = ('senja', 'malam', 'fajar')
TUJUAN = ('gua', 'rumah', 'tenda', 'kosong')
LATAR_PANGGUNG = ('gurun', 'kabah', 'kota')
# tokoh yang TIDAK boleh digambar dalam bentuk apa pun (dicek pada field "siapa" babak tokoh)
TERLARANG = ['nabi', 'rasul', 'muhammad', 'ﷺ', 'sahabat', 'radhiyallahu', 'malaikat', 'jibril', 'mikail', 'israfil',
             'ummul mukminin', 'istri', 'abu bakar', 'abu bakr', 'umar', 'utsman', 'usman', 'ali bin', 'ali ibn',
             'khadijah', 'aisyah', 'fatimah', 'hamzah', 'bilal', 'abbas', 'zaid', 'muadz', 'salman', 'anshar',
             'muhajirin', 'ibrahim', 'ismail', 'musa', 'isa', 'nuh', 'yusuf', 'sulaiman', 'dawud', 'adam',
             'khalid', 'amr bin', 'saad', "sa'ad", 'abdullah bin', 'anas', 'abu hurairah', 'ummu', 'asma']


def boleh_digambar(siapa):
    import re
    s = ' ' + re.sub(r'[^a-zﷺ\' ]', ' ', (siapa or '').lower()) + ' '
    if not s.strip():
        return False
    return not any(f' {k} ' in s or (k == 'ﷺ' and k in s) for k in TERLARANG)

PROMPT = """Kamu sutradara motion graphic untuk akun dakwah "Sunnah Daily" (Reels/Shorts 9:16, 45-70 detik).
Ubah kisah di bawah menjadi storyboard dengan gaya visual bercerita seperti contoh "Sirah #01 Hijrah":
pemandangan dari dalam gua lewat lengkung, peta rute, angka besar yang menghitung naik, jejak kaki mendekat.

KISAH (sudah diverifikasi, JANGAN menambah fakta, nama, angka, tempat, atau kutipan baru):
{kisah}

JENIS BABAK yang tersedia:
- "jendela": pemandangan lewat lengkung batu (dari dalam gua/ruangan). Field: "langit": senja|malam|fajar.
  Cocok untuk suasana, malam, persembunyian, ketegangan, renungan.
- "peta": rute perjalanan. Field: "judul" (1-2 kata, mis. "Hijrah"), "sub" (mis. "Makkah ke Gua Tsur"),
  "tempat": 2-4 titik [{{"nama": "...", "x": 0-1, "y": 0-1}}] (x kiri-kanan, y atas-bawah, kira-kira arah
  geografis; utara di atas). Hanya jika kisah memang menyebut perpindahan antar tempat yang bernama.
- "angka": angka penting yang DISEBUT di kisah. Field: "label" (2-3 kata), "angka" (bilangan bulat),
  "satuan" (mis. "ekor unta", "tahun", "pasukan"). Jangan pakai kalau kisah tidak menyebut angka.
- "jejak": jejak kaki mendekat di padang pasir. Field: "tujuan": gua|rumah|tenda|kosong.
  Cocok untuk pengejaran, perjalanan, kedatangan.
- "tokoh": satu tokoh UMUM berdiri (siluet polos tanpa wajah/mata, dari belakang). Field: "siapa" (nama/peran,
  mis. "Abdul Muthalib", "Abrahah", "penduduk Makkah"), "latar": gurun|kabah|kota, "dengan": unta|"".
  DILARANG untuk Nabi ﷺ, nabi lain, sahabat, istri Nabi, ahlul bait yang sahabat, maupun malaikat.
- "pasukan": barisan gajah dan prajurit (siluet polos). Field: "latar": gurun|kabah, "aksi": berjalan|berlutut.
- "kawanan": kawanan burung terbang membawa batu kecil. Field: "latar": gurun|kabah.
- "pemandangan": ilustrasi datar penuh layar. Field: "latar" salah satu: {latar}
- "dalil": kartu dalil. Tanpa field lain dan tanpa narasi (diisi sistem). Wajib tepat satu, setelah kisah.
- "renungan": lengkung jendela fajar + judul. Field: "judul" maks 4 kata (inti faedah). Tepat satu, setelah dalil.
- "penutup": kartu akhir. Field: "ajakan": ajakan komentar singkat yang terkait kisah,
  mis. "Tulis Laa tahzan di komentar". Tepat satu, paling akhir.

ATURAN:
- 7-10 babak. Babak pertama = hook: jenis jendela/pemandangan/jejak dengan "judul" = "{hook}".
- Variasikan jenis; jangan dua babak berturut-turut dengan jenis dan latar yang sama.
- Setiap babak (kecuali dalil) punya "narasi": 1-2 kalimat lisan Bahasa Indonesia yang tenang dan hangat.
  Total narasi selain dalil 100-140 kata. Narasi babak pertama = kalimat hook.
- Narasi menceritakan ulang kisah dengan setia: urutan dan fakta sama, tanpa tambahan.
- Tulis "Rasulullah ﷺ"/"Nabi ﷺ" dengan simbol ﷺ. Jangan menyebut warna, kamera, atau visual di narasi.
- Narasi renungan menyampaikan faedah. Narasi penutup = ajakan komentar + "Ikuti Sunnah Daily untuk kisah berikutnya."
- Tidak ada penggambaran Nabi ﷺ, para nabi, sahabat, istri Nabi, atau malaikat dalam bentuk apa pun.
- Hewan dan tokoh umum hanya lewat babak tokoh/pasukan/kawanan, dan hanya jika memang ada di kisah.

Kembalikan JSON saja: {{"babak": [{{"jenis": "...", "narasi": "...", ...field lain}}]}}"""


def terbilang(n):
    a = ['', 'satu', 'dua', 'tiga', 'empat', 'lima', 'enam', 'tujuh', 'delapan', 'sembilan', 'sepuluh', 'sebelas']
    if n < 12:
        return a[n]
    if n < 20:
        return a[n - 10] + ' belas'
    if n < 100:
        return (a[n // 10] + ' puluh ' + a[n % 10]).strip()
    if n < 200:
        return ('seratus ' + terbilang(n - 100)).strip()
    if n < 1000:
        return (a[n // 100] + ' ratus ' + terbilang(n % 100)).strip()
    if n < 2000:
        return ('seribu ' + terbilang(n - 1000)).strip()
    if n < 1000000:
        return (terbilang(n // 1000) + ' ribu ' + terbilang(n % 1000)).strip()
    return str(n)


def _ringkas(k):
    return json.dumps({
        'judul_hook': k['judul_hook'], 'narasi_hook': k.get('narasi_hook'),
        'kisah': [a['narasi'] for a in k['adegan']],
        'dalil': {x: k['dalil'].get(x) for x in ('jenis', 'terjemah', 'sumber', 'derajat')},
        'faedah': k['faedah'],
    }, ensure_ascii=False, indent=1)


def _latar_ke_babak(latar, narasi, judul=None):
    if latar == 'gua':
        b = {'jenis': 'jendela', 'langit': 'senja'}
    elif latar == 'langit':
        b = {'jenis': 'jendela', 'langit': 'malam'}
    else:
        b = {'jenis': 'pemandangan', 'latar': latar if latar in ilustrasi.LATAR else 'gurun'}
    b['narasi'] = narasi
    if judul:
        b['judul'] = judul
    return b


def cadangan(k):
    """Storyboard tanpa Gemini, dari adegan kisah."""
    bb = [_latar_ke_babak(k.get('latar_hook') or 'gua', k.get('narasi_hook') or k['judul_hook'], k['judul_hook'])]
    for a in k['adegan']:
        bb.append(_latar_ke_babak(a.get('latar') or 'gurun', a['narasi']))
    bb.append({'jenis': 'dalil'})
    bb.append({'jenis': 'renungan', 'judul': '', 'narasi': f"Faedahnya, {k['faedah']}"})
    bb.append({'jenis': 'penutup', 'ajakan': 'Tulis Aamiin di komentar',
               'narasi': 'Tulis aamiin di komentar, dan ikuti Sunnah Daily untuk kisah berikutnya.'})
    return bb


def rapikan(bb, k):
    """Validasi field; babak tak valid diganti pemandangan. Pastikan dalil, renungan, penutup ada sekali."""
    hasil = []
    for b in bb:
        j = b.get('jenis')
        narasi = (b.get('narasi') or '').strip()
        if j in ('dalil', 'renungan', 'penutup'):
            continue
        if not narasi:
            continue
        if j == 'jendela':
            b['langit'] = b.get('langit') if b.get('langit') in LANGIT else 'senja'
        elif j == 'peta':
            t = [p for p in (b.get('tempat') or []) if p.get('nama') and isinstance(p.get('x'), (int, float))
                 and isinstance(p.get('y'), (int, float))]
            if len(t) < 2:
                b = _latar_ke_babak('kafilah', narasi)
            else:
                for p in t:
                    p['x'], p['y'] = min(1, max(0, float(p['x']))), min(1, max(0, float(p['y'])))
                b['tempat'] = t[:4]
        elif j == 'angka':
            try:
                b['angka'] = int(str(b.get('angka')).replace('.', '').replace(',', ''))
                sumber = ' '.join([k.get('narasi_hook') or ''] + [a['narasi'] for a in k['adegan']]).lower()
                ada = str(b['angka']) in sumber.replace('.', '') or terbilang(b['angka']) in sumber
                assert b['angka'] > 0 and ada
            except Exception:
                b = _latar_ke_babak('gurun', narasi)
        elif j == 'jejak':
            b['tujuan'] = b.get('tujuan') if b.get('tujuan') in TUJUAN else 'kosong'
        elif j == 'pemandangan':
            b['latar'] = b.get('latar') if b.get('latar') in ilustrasi.LATAR else 'gurun'
        elif j == 'tokoh':
            if not boleh_digambar(b.get('siapa')):
                b = _latar_ke_babak('kabah' if b.get('latar') == 'kabah' else 'gurun', narasi)
            else:
                b['latar'] = b.get('latar') if b.get('latar') in LATAR_PANGGUNG else 'gurun'
                b['dengan'] = 'unta' if b.get('dengan') == 'unta' else ''
        elif j in ('pasukan', 'kawanan'):
            b['latar'] = b.get('latar') if b.get('latar') in ('gurun', 'kabah') else 'gurun'
            if j == 'pasukan':
                b['aksi'] = 'berlutut' if b.get('aksi') == 'berlutut' else 'berjalan'
        else:
            b = _latar_ke_babak('gurun', narasi)
        b['narasi'] = narasi
        hasil.append(b)
    if len(hasil) < 3:
        raise ValueError('storyboard terlalu pendek')
    hasil[0]['judul'] = k['judul_hook']
    if hasil[0]['jenis'] not in ('jendela', 'pemandangan', 'jejak', 'pasukan', 'kawanan'):
        hasil.insert(0, _latar_ke_babak(k.get('latar_hook') or 'gua', k.get('narasi_hook') or k['judul_hook'],
                                        k['judul_hook']))
    ren = next((b for b in bb if b.get('jenis') == 'renungan' and (b.get('narasi') or '').strip()), None)
    pen = next((b for b in bb if b.get('jenis') == 'penutup' and (b.get('narasi') or '').strip()), None)
    hasil.append({'jenis': 'dalil'})
    hasil.append({'jenis': 'renungan', 'judul': ((ren or {}).get('judul') or '')[:40],
                  'narasi': (ren or {}).get('narasi') or f"Faedahnya, {k['faedah']}"})
    hasil.append({'jenis': 'penutup', 'ajakan': (pen or {}).get('ajakan') or '',
                  'narasi': (pen or {}).get('narasi') or 'Ikuti Sunnah Daily untuk kisah berikutnya.'})
    return hasil


def buat(k):
    if k.get('storyboard'):
        return k['storyboard']
    latar = ', '.join(ilustrasi.LATAR)
    try:
        j = gemini.teks(PROMPT.format(kisah=_ringkas(k), latar=latar, hook=k['judul_hook']), suhu=0.5)
        bb = rapikan((j or {}).get('babak') or [], k)
    except Exception as e:
        gemini.log(f'   storyboard gagal, pakai cadangan: {e}')
        bb = rapikan(cadangan(k), k)
    k['storyboard'] = bb
    return bb
