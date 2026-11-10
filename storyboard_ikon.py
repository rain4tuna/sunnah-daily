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

PROMPT = """Kamu penata konten video dakwah "Sunnah Daily" (Reels/Shorts 9:16, 40-65 detik) bergaya animasi ikon.
Materi di bawah SUDAH diverifikasi. JANGAN menambah fakta, nama, angka, tempat, atau kutipan baru.

MATERI:
{materi}

Susun:
- "hook": {{"narasi": "1 kalimat hook lisan yang bikin penasaran", "ikon": ["1 ikon"]}}
- "poin": 3-5 babak berurutan, tiap babak {{"narasi": "1-2 kalimat lisan", "label": "inti di layar maks 5 kata",
  "ikon": ["1-2 ikon"]}}. Narasi menceritakan ulang materi dengan setia, urutan sama.
- "faedah": {{"narasi": "1 kalimat menyampaikan faedah", "ikon": ["1 ikon"]}}
- "penutup": {{"ajakan": "ajakan komentar singkat terkait materi, mis. Tulis Aamiin di komentar",
  "narasi": "ajakan itu + 'Ikuti Sunnah Daily untuk {lanjut} berikutnya.'"}}
Total narasi (tanpa dalil) 90-130 kata. Bahasa Indonesia lisan yang tenang, hangat, sederhana.
Tulis "Rasulullah ﷺ"/"Nabi ﷺ" dengan simbol ﷺ. Jangan menyebut warna, ikon, atau visual di narasi.

IKON (pilih HANYA dari daftar; hanya benda & tempat, TIDAK ADA makhluk bernyawa): {ikon}
Pilih ikon yang benar-benar menggambarkan isi babak; jangan memakai benda lain sebagai pengganti.

Kembalikan JSON saja: {{"hook": {{...}}, "poin": [{{...}}], "faedah": {{...}}, "penutup": {{...}}}}"""


def _ikon(daftar, cadangan='kitab'):
    ik = [i for i in (daftar or []) if i in animasi_ikon.IKON][:2]
    return ik or [cadangan]


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
        'hook': {'narasi': (hook.get('narasi') or cad['hook']['narasi']).strip(), 'ikon': _ikon(hook.get('ikon'), 'lentera')[:1]},
        'poin': [{'narasi': p['narasi'].strip(), 'label': (p.get('label') or '').strip()[:40], 'ikon': _ikon(p.get('ikon'))}
                 for p in poin],
        'faedah': {'narasi': (fa.get('narasi') or cad['faedah']['narasi']).strip(), 'ikon': _ikon(fa.get('ikon'), 'hati')[:1]},
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
        j = gemini.teks(PROMPT.format(materi=materi, ikon=animasi_ikon.DAFTAR_IKON, lanjut=lanjut), suhu=0.5)
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
    for s in seg:
        s['kicker'] = kicker
    return seg
