"""Storyboard untuk template Animasi Ikon (animasi_ikon.py).

Dari kisah/materi yang SUDAH diverifikasi, Gemini (1 panggilan, tanpa pencarian) menata:
hook -> 3-5 poin (narasi lisan + label layar + ikon) -> dalil -> faedah -> penutup.
Hasil disimpan di k['storyboard_ikon'] supaya render ulang konsisten. Gagal -> cadangan tanpa Gemini.
Dipakai seri Sirah (main.py) maupun Sunnah Harian (harian.py).
"""
import json

import animasi_ikon
import gemini

PETA_LATAR = {'gurun': 'gunung', 'kafilah': 'jejak', 'kabah': 'kabah', 'masjid': 'masjid', 'gua': 'gua',
              'kota': 'rumah', 'kebun': 'pohon_kurma', 'tenda': 'tenda', 'lentera': 'lentera', 'kitab': 'kitab',
              'laut': 'awan_hujan', 'langit': 'bulan_bintang'}

# Ilustrasi untuk template Remotion (remotion/src/Ilustrasi.tsx). Kunci HARUS sama dengan JENIS di berkas itu.
ILUSTRASI = {
    'badai': 'awan petir, kilat dan hujan (azab, ancaman, ketakutan, ujian berat)',
    'kota_malam': 'kota tua di malam hari dengan bulan sabit (Makkah/Madinah, ketenangan, malam)',
    'quran': "mushaf terbuka bercahaya (ayat, wahyu, bacaan Al-Qur'an, ilmu)",
    'kafilah': 'kafilah unta di padang pasir saat senja (perjalanan, hijrah, dagang, utusan)',
    'kabah': "Ka'bah dengan orang thawaf (Makkah, haji, umrah, Masjidil Haram)",
    'masjid': 'masjid berkubah dan menara (shalat, Madinah, adab ke masjid)',
    'gua': 'gunung batu dengan gua bercahaya (Gua Hira, Gua Tsur, menyendiri, wahyu pertama)',
    'majelis': 'beberapa orang duduk melingkar (musyawarah, pembesar kaum, perkumpulan, rapat)',
    'lentera': 'lentera menyala di malam hari (ibadah malam, dzikir, doa, renungan)',
    'fajar': 'matahari terbit di balik bukit (pagi, harapan, kemenangan, awal baru)',
    'air': 'air dituang dari kendi (wudhu, bersuci, minum, kebersihan)',
    'hidangan': 'kurma, roti dan air di atas hamparan (makan, minum, puasa, menjamu tamu)',
    'pintu': 'pintu rumah terbuka bercahaya (masuk/keluar rumah, keluarga, bertamu, tidur)',
    'sedekah': 'tangan menjatuhkan koin ke mangkuk (sedekah, harta, jual beli, tawaran dunia)',
    'hati': 'hati bercahaya dan berdenyut (iman, niat, akhlak, kasih sayang, taubat)',
}
TOKOH = ('panik', 'takut', 'berdiri', 'berdoa')
# Ikon template lama -> ilustrasi, untuk storyboard lama atau jawaban Gemini yang tidak valid.
PETA_IKON = {
    'masjid': 'masjid', 'sajadah': 'masjid', 'kabah': 'kabah', 'kitab': 'quran', 'quran': 'quran', 'pena': 'quran',
    'gulungan': 'quran', 'lentera': 'lentera', 'tasbih': 'lentera', 'bulan_bintang': 'kota_malam', 'bintang': 'kota_malam',
    'rumah': 'pintu', 'pintu': 'pintu', 'kunci': 'pintu', 'pohon_kurma': 'hidangan', 'kurma': 'hidangan', 'roti': 'hidangan',
    'piring': 'hidangan', 'gelas': 'hidangan', 'tenda': 'kafilah', 'gunung': 'kafilah', 'jejak': 'kafilah', 'gua': 'gua',
    'matahari': 'fajar', 'jam': 'fajar', 'kalender': 'fajar', 'awan_hujan': 'badai', 'tetes_air': 'air', 'sumur': 'air',
    'siwak': 'air', 'parfum': 'air', 'timbangan': 'sedekah', 'koin': 'sedekah', 'hati': 'hati', 'cahaya': 'hati',
}
# Babak yang menyebut Nabi, sahabat, atau malaikat tidak pernah diberi tokoh: sosok di layar bisa disangka mereka.
KATA_TANPA_TOKOH = ('ﷺ', 'rasulullah', 'nabi ', 'radhiyallahu', 'radhiallahu', 'malaikat', 'jibril', "'alaihis")

PROMPT = """Kamu penata konten video dakwah "Sunnah Daily" (Reels/Shorts 9:16, 40-65 detik) bergaya animasi ikon.
Materi di bawah SUDAH diverifikasi. JANGAN menambah fakta, nama, angka, tempat, atau kutipan baru.

MATERI:
{materi}

Susun:
- "hook": {{"narasi": "1 kalimat hook lisan yang bikin penasaran", "ikon": ["1 ikon"], "ilustrasi": "", "tokoh": ""}}
- "poin": 3-5 babak berurutan, tiap babak {{"narasi": "1-2 kalimat lisan", "label": "inti di layar maks 5 kata",
  "ikon": ["1-2 ikon"], "ilustrasi": "", "tokoh": ""}}. Narasi menceritakan ulang materi dengan setia, urutan sama.
- "faedah": {{"narasi": "1 kalimat menyampaikan faedah", "ikon": ["1 ikon"], "ilustrasi": "", "tokoh": ""}}
- "penutup": {{"ajakan": "ajakan komentar MAKS 5 KATA, mis. Tulis Aamiin di komentar",
  "narasi": "ajakan itu + 'Ikuti Sunnah Daily untuk {lanjut} berikutnya.'"}}
Total narasi (tanpa dalil) 75-105 kata, supaya video 45-65 detik. Bahasa Indonesia lisan yang tenang, hangat, sederhana.
Tulis "Rasulullah ﷺ"/"Nabi ﷺ" dengan simbol ﷺ. Jangan menyebut warna, ikon, atau visual di narasi.

IKON (pilih HANYA dari daftar; hanya benda & tempat, TIDAK ADA makhluk bernyawa): {ikon}
Pilih ikon yang benar-benar menggambarkan isi babak; jangan memakai benda lain sebagai pengganti.

ILUSTRASI (pilih SATU kunci per babak, HANYA dari daftar ini; pilih yang paling menggambarkan isi babak, dan
usahakan babak yang berurutan tidak memakai ilustrasi yang sama):
{ilustrasi}

TOKOH = manusia tanpa wajah yang ditambahkan ke ilustrasi. Pilihan: panik, takut, berdiri, berdoa.
Isi "tokoh" HANYA bila babak itu menceritakan orang yang BUKAN Nabi ﷺ, BUKAN nabi lain, BUKAN sahabat atau keluarga
beliau, dan BUKAN malaikat: misalnya tokoh musyrik, kaum terdahulu, atau orang umum ("kita", "seseorang").
Kalau babak itu menyebut Nabi ﷺ, sahabat, atau malaikat, "tokoh" WAJIB "" (kosong). Kalau ragu, kosongkan.

Kembalikan JSON saja: {{"hook": {{...}}, "poin": [{{...}}], "faedah": {{...}}, "penutup": {{...}}}}"""


def _ikon(daftar, cadangan='kitab'):
    ik = [i for i in (daftar or []) if i in animasi_ikon.IKON][:2]
    return ik or [cadangan]


def ilustrasi_babak(b):
    """(ilustrasi, tokoh) yang valid untuk satu babak storyboard; storyboard lama dipetakan dari ikonnya."""
    il = b.get('ilustrasi')
    if il not in ILUSTRASI:
        il = next((PETA_IKON[i] for i in (b.get('ikon') or []) if i in PETA_IKON), 'lentera')
    tokoh = b.get('tokoh') if b.get('tokoh') in TOKOH else ''
    narasi = (b.get('narasi') or '').lower()
    if tokoh and any(kata in narasi for kata in KATA_TANPA_TOKOH):
        tokoh = ''
    return il, tokoh


def _visual(asal, b):
    """Salin pilihan ilustrasi & tokoh dari jawaban Gemini (asal) ke babak b bila valid."""
    if asal.get('ilustrasi') in ILUSTRASI:
        b['ilustrasi'] = asal['ilustrasi']
    if asal.get('tokoh') in TOKOH:
        b['tokoh'] = asal['tokoh']
    return b


def cadangan(k, lanjut='kisah'):
    return {
        'hook': {'narasi': k.get('narasi_hook') or k['judul_hook'],
                 'ikon': [PETA_LATAR.get(k.get('latar_hook'), 'lentera')]},
        'poin': [{'narasi': a['narasi'], 'label': '', 'ikon': [PETA_LATAR.get(a.get('latar'), 'kitab')]}
                 for a in k['adegan']],
        'faedah': {'narasi': f"Faedahnya, {k['faedah']}", 'ikon': ['hati']},
        'penutup': {'ajakan': 'Tulis Aamiin di komentar',
                    'narasi': f'Tulis aamiin di komentar, dan ikuti Sunnah Daily untuk {lanjut} berikutnya.'},
    }


def rapikan(j, k, lanjut):
    cad = cadangan(k, lanjut)
    hook = j.get('hook') or {}
    poin = [p for p in (j.get('poin') or []) if (p.get('narasi') or '').strip()][:5]
    if len(poin) < 2:
        poin = cad['poin']
    fa = j.get('faedah') or {}
    pen = j.get('penutup') or {}
    return {
        'hook': _visual(hook, {'narasi': (hook.get('narasi') or cad['hook']['narasi']).strip(),
                               'ikon': _ikon(hook.get('ikon'), 'lentera')[:1]}),
        'poin': [_visual(p, {'narasi': p['narasi'].strip(), 'label': (p.get('label') or '').strip()[:40],
                             'ikon': _ikon(p.get('ikon'))}) for p in poin],
        'faedah': _visual(fa, {'narasi': (fa.get('narasi') or cad['faedah']['narasi']).strip(),
                               'ikon': _ikon(fa.get('ikon'), 'hati')[:1]}),
        'penutup': {'ajakan': (pen.get('ajakan') or cad['penutup']['ajakan']).strip()[:60],
                    'narasi': (pen.get('narasi') or cad['penutup']['narasi']).strip()},
    }


def buat(k, lanjut='kisah'):
    """lanjut: kata di kalimat penutup ('kisah' untuk Sirah, 'sunnah' untuk Sunnah Harian)."""
    if k.get('storyboard_ikon'):
        return k['storyboard_ikon']
    materi = json.dumps({
        'judul': k['judul_hook'], 'pembuka': k.get('narasi_hook'), 'isi': [a['narasi'] for a in k['adegan']],
        'dalil': {x: k['dalil'].get(x) for x in ('jenis', 'terjemah', 'sumber', 'derajat')}, 'faedah': k['faedah'],
    }, ensure_ascii=False, indent=1)
    try:
        daftar = '\n'.join(f'- {kunci}: {arti}' for kunci, arti in ILUSTRASI.items())
        j = gemini.teks(PROMPT.format(materi=materi, ikon=animasi_ikon.DAFTAR_IKON, lanjut=lanjut, ilustrasi=daftar),
                        suhu=0.5)
        sb = rapikan(j or {}, k, lanjut)
    except Exception as e:
        gemini.log(f'   storyboard ikon gagal, pakai cadangan: {e}')
        sb = rapikan({}, k, lanjut)
    k['storyboard_ikon'] = sb
    return sb


def segmen(k, kicker, narasi_dalil, seri='', kredit='', lanjut='kisah'):
    """Ubah storyboard jadi daftar segmen untuk animasi_ikon.buat_video."""
    sb = buat(k, lanjut)
    seg = [{'jenis': 'hook', 'judul': k['judul_hook'], 'ikon': sb['hook']['ikon'], 'ucap': sb['hook']['narasi']}]
    for p in sb['poin']:
        seg.append({'jenis': 'poin', 'narasi': p['narasi'], 'label': p['label'], 'ikon': p['ikon'], 'ucap': p['narasi']})
    seg.append({'jenis': 'dalil', 'dalil': k['dalil'], 'ucap': narasi_dalil(k['dalil'])})
    seg.append({'jenis': 'faedah', 'faedah': k['faedah'], 'ikon': sb['faedah']['ikon'], 'ucap': sb['faedah']['narasi']})
    seg.append({'jenis': 'penutup', 'ajakan': sb['penutup']['ajakan'], 'seri': seri, 'kredit': kredit,
                'ucap': sb['penutup']['narasi']})
    for s, b in zip(seg, [sb['hook'], *sb['poin'], None, sb['faedah'], None]):
        s['kicker'] = kicker
        if b:
            s['ilustrasi'], s['tokoh'] = ilustrasi_babak(b)
    return seg
