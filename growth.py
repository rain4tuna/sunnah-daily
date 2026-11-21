"""Mesin optimasi Hook, CTA, Caption & Metadata lintas-platform (YouTube Shorts, IG Reels, TikTok, FB).

Dibangun mengikuti panduan skill `/claude-youtube` (shorts-playbook, retention-scripting-guide,
monetization-guide) serta skill Instagram (`ig-reel`, `ig-caption`):
- Instagram (aturan 18 Des 2025): maks 5 hashtag spesifik (tanpa #fyp/#viral), tanpa URL di caption,
  125 karakter pertama jelas & langsung ke inti/ajakan, tepat 1 CTA tunggal, kata kunci pencarian alami.
- YouTube Shorts: judul front-loaded <= 40 karakter tampil + #Shorts, deskripsi 125 karakter pertama kaya
  kata kunci + kredit kajian & tautan timestamp + jembatan ke video panjang 8+ menit.
- TikTok: caption ringkas dengan gema hook, 1 CTA komentar/simpan, maks 5 hashtag niche, tanpa URL/watermark.
- Hook & Loop: 8 rumus hook dakwah berretensi tinggi + penyaring salam/pembuka lemah + gema loop penutup.
"""
import re

USTADZ = 'Ust. Dr. Firanda Andirja, M.A.'

# 8 rumus hook dakwah (diadaptasi dari ig-reel/hooks.json & claude-youtube/retention-scripting-guide.md)
RUMUS_HOOK = {
    'curiosity_gap': {
        'nama': 'Curiosity Gap',
        'pola': 'Kenapa / Mengapa {peristiwa_tak_terduga}?',
        'badge': 'TAHUKAH KAMU?',
        'contoh': 'Kenapa tokoh Quraisy ini mendadak gemetar?',
    },
    'nobody_tells_you': {
        'nama': 'Nobody Tells You',
        'pola': 'Banyak yang belum tahu {fakta_shahih_mengejutkan}.',
        'badge': 'JARANG DIBAHAS',
        'contoh': 'Banyak yang belum tahu rahasia doa ini.',
    },
    'wrong_vs_right': {
        'nama': 'Wrong Way, Right Way',
        'pola': 'Sering keliru saat {amalan}. Begini sunnahnya.',
        'badge': 'CEK SUNNAHNYA',
        'contoh': 'Sering keliru saat bangun tidur? Begini sunnahnya.',
    },
    'negative_command': {
        'nama': 'Negative Command',
        'pola': 'Jangan lewatkan {amalan_ringan} sebelum {waktu}.',
        'badge': 'JANGAN LEWATKAN',
        'contoh': 'Jangan tidur sebelum baca 1 dzikir ini.',
    },
    'time_collapse': {
        'nama': 'Time Collapse',
        'pola': 'Cuma {durasi_singkat}, pahalanya {keutamaan_shahih}.',
        'badge': 'AMALAN RINGAN',
        'contoh': 'Cuma 10 detik, amalan ini berat di timbangan.',
    },
    'if_this_then_watch': {
        'nama': 'If This, Then Watch',
        'pola': 'Kalau hatimu sedang {kondisi}, simak kisah ini.',
        'badge': 'SIMAK SEBENTAR',
        'contoh': 'Kalau hati sedang sempit, simak kisah ini.',
    },
    'numbered_focus': {
        'nama': 'Numbered Focus',
        'pola': '{N} adab {topik} yang langsung bisa diamalkan.',
        'badge': 'SUNNAH HARIAN',
        'contoh': '3 adab makan dari Rasulullah ﷺ.',
    },
    'contrast_reveal': {
        'nama': 'Contrast Reveal',
        'pola': 'Dianggap remeh, padahal {nilai_besar_di_dalil}.',
        'badge': 'HIKMAH SIRAH',
        'contoh': 'Tampak sederhana, tapi inilah kunci kemenangan.',
    },
}

# Pembuka lemah yang membunuh retensi 3 detik pertama (retention-scripting-guide.md & ig-reel)
PEMBUKA_LEMAH = re.compile(
    r'^\s*(halo|hai|hey|assalamu|selamat datang|di video kali ini|kali ini kita|welcome back|perkenalkan)\b',
    re.I,
)

# Tag filler yang dilarang ig-caption (tidak membantu jangkauan)
TAG_FILLER = {
    'viral', 'fyp', 'explore', 'explorepage', 'foryou', 'foryoupage', 'trending',
    'instagood', 'love', 'follow', 'like4like', 'reels', 'reelsinstagram', 'viralreels',
    'instadaily', 'tiktokviral', 'fypシ', 'masukberanda',
}

# Batas resmi platform
IG_HASHTAG_MAX = 5
IG_VISIBLE_CUT = 125
IG_CAPTION_MAX = 2200
TT_CAPTION_MAX = 2200
YT_TITLE_VISIBLE = 40
YT_TITLE_MAX = 100
YT_DESC_MAX = 4900


def _bersih_tag(t):
    return re.sub(r'[^a-z0-9_]', '', str(t or '').lower())


def _detik(menit):
    try:
        bag = [int(x) for x in str(menit).split(':')]
        return bag[0] * 3600 + bag[1] * 60 + bag[2] if len(bag) == 3 else bag[0] * 60 + bag[1]
    except Exception:
        return 0


def pilih_hashtag(k, seri='sirah', maks=5):
    """Pilih maks `maks` (default 5) hashtag niche spesifik; buang filler tag."""
    dasar = ['sunnahdaily', 'sunnahharian', 'amalansunnah'] if seri == 'harian' else [
        'sunnahdaily', 'sirahnabawiyah', 'kisahnabi'
    ]
    tambahan = [_bersih_tag(t) for t in (k.get('tema') or [])]
    dalil_jenis = (k.get('dalil') or {}).get('jenis')
    tambahan.append('alquran' if dalil_jenis == 'ayat' else 'haditsshahih')
    hasil = []
    for tag in dasar + tambahan:
        if tag and tag not in TAG_FILLER and tag not in hasil:
            hasil.append(tag)
        if len(hasil) >= maks:
            break
    return hasil


def skor_hook(judul_layar, narasi_hook):
    """Nilai kekuatan hook 0-100 berdasarkan aturan ig-reel & claude-youtube."""
    judul = ' '.join((judul_layar or '').split())
    narasi = ' '.join((narasi_hook or '').split())
    kata_judul = judul.split()
    kata_narasi = narasi.split()
    skor = 60
    masalah = []

    if not judul:
        skor -= 30
        masalah.append('judul_hook kosong')
    elif len(kata_judul) <= 6:
        skor += 12
    else:
        skor -= 10
        masalah.append(f'judul layar terlalu panjang ({len(kata_judul)} kata > 6 kata)')

    if PEMBUKA_LEMAH.search(narasi) or PEMBUKA_LEMAH.search(judul):
        skor -= 30
        masalah.append('pembuka lemah/salam di detik pertama (potong intro)')
    else:
        skor += 8

    if '?' in narasi or '?' in judul or re.search(
        r'\b(kenapa|mengapa|rahasia|jangan|ternyata|berapa|bagaimana|padahal|sebelum)\b',
        f'{judul} {narasi}',
        re.I,
    ):
        skor += 12
    else:
        masalah.append('kurang elemen curiosity gap / kontras')

    if re.search(r'\b\d+\b', f'{judul} {narasi}'):
        skor += 6

    if 6 <= len(kata_narasi) <= 20:
        skor += 6
    elif len(kata_narasi) > 26:
        skor -= 8
        masalah.append('narasi hook melebihi 3 detik pertama (>26 kata)')

    skor = max(0, min(100, skor))
    grade = 'STRONG' if skor >= 75 else ('OK' if skor >= 55 else 'WEAK')
    return {'skor': skor, 'grade': grade, 'masalah': masalah}


def pilih_hook_badge(k, seri='sirah'):
    """Badge singkat (<= 3 kata) yang muncul di frame 0 pada template SunnahMotion."""
    teks = f"{k.get('judul_hook', '')} {k.get('narasi_hook', '')}".lower()
    if any(w in teks for w in ('jangan', 'hindari', 'keliru', 'salah')):
        return 'CEK SUNNAHNYA'
    if any(w in teks for w in ('kenapa', 'mengapa', 'rahasia', 'ternyata')):
        return 'TAHUKAH KAMU?'
    if seri == 'harian':
        return 'AMALAN SUNNAH'
    return 'HIKMAH SIRAH'


def cta_tunggal(k, seri='sirah'):
    """Satu ajakan tunggal yang jelas (single ask, sesuai ig-caption & ig-reel)."""
    sb = k.get('storyboard_ikon') or {}
    ajakan = ((sb.get('penutup') or {}).get('ajakan') or '').strip()
    if ajakan and len(ajakan.split()) <= 7 and ' & ' not in ajakan and ' dan ' not in ajakan.lower():
        return ajakan
    return 'Simpan untuk diamalkan hari ini' if seri == 'harian' else 'Tulis Aamiin di komentar'


def loop_echo(k):
    """Gema kata dari judul hook untuk menjembatani replay loop yang mulus."""
    judul = ' '.join((k.get('judul_hook') or '').split())
    kata = judul.split()
    if not kata:
        return ''
    return ' '.join(kata[:5]) + '...'


def _info_dalil(k):
    dl = k.get('dalil') or {}
    derajat = ''
    if dl.get('jenis') in ('hadits', 'atsar') and dl.get('derajat'):
        derajat = f" · {dl['derajat'].capitalize()}"
    if dl.get('derajat') == 'lemah':
        derajat += ' (lemah, bukan dalil)'
    return dl.get('terjemah') or '', dl.get('sumber') or '', derajat


def _kata_kunci_alami(k, seri='sirah'):
    tema = [str(t).strip() for t in (k.get('tema') or []) if str(t).strip()][:3]
    dasar = ['amalan sunnah harian', 'hadits shahih'] if seri == 'harian' else ['sirah nabawiyah', 'kisah Rasulullah ﷺ']
    return ', '.join(dict.fromkeys(dasar + tema))


def _judul_kajian_tanpa_pagar(judul):
    """Ubah '#11' pada judul kajian menjadi 'Bagian 11' agar tidak terhitung sebagai hashtag IG/TikTok."""
    return re.sub(r'#\s*(\d+)', r'Bagian \1', str(judul or '')).strip()


def caption_ig(k, ep=None, seri='sirah'):
    """Caption Instagram Reels patuh ig-caption (Job A):
    - Baris 1 <= 125 karakter tanpa emoji pembuka / hashtag / salam, berisi ajakan jelas + konteks.
    - Tanpa URL/link di badan caption (link tidak bisa diklik di IG).
    - Kata kunci pencarian alami dalam paragraf ringkas.
    - Tepat 1 CTA tunggal dan maks 5 hashtag spesifik (aturan IG 18 Des 2025).
    """
    ask = cta_tunggal(k, seri)
    judul = (k.get('judul_hook') or '').strip()
    baris1 = f"{ask}. {judul}"
    if len(baris1) > IG_VISIBLE_CUT - 5:
        baris1 = baris1[:IG_VISIBLE_CUT - 8].rstrip(' .,;:') + '...'

    terjemah, sumber, derajat = _info_dalil(k)
    faedah = (k.get('faedah') or '').strip()
    kunci = _kata_kunci_alami(k, seri)
    ep_bersih = _judul_kajian_tanpa_pagar(ep.get('judul')) if ep else ''

    bagian = [
        baris1,
        f"Inti faedah: {faedah}" if faedah else '',
        f"Dalil: \"{terjemah}\" ({sumber}{derajat})" if terjemah else '',
        (f"Disarikan dari kajian {ep_bersih} bersama {USTADZ}. Topik: {kunci}."
         if seri != 'harian' and ep_bersih
         else f"Ringkasan {kunci} yang mudah diamalkan setiap hari."),
        ' '.join('#' + t for t in pilih_hashtag(k, seri, maks=IG_HASHTAG_MAX)),
    ]
    teks = '\n\n'.join(b for b in bagian if b)
    return teks[:IG_CAPTION_MAX]


def metadata_yt(k, ep=None, seri='sirah'):
    """Paket metadata YouTube Shorts patuh claude-youtube (shorts-playbook & seo-playbook):
    - Judul: front-loaded keywords <= 40 karakter tampil + #Shorts (total <= 100).
    - Deskripsi: 125 karakter pertama sarat kata kunci + dalil + kredit kajian + tautan timestamp + bridge long-form.
    - Tags: maks 15 tag SEO relevan.
    """
    judul_inti = (k.get('judul_hook') or 'Hikmah Sunnah Daily').strip()
    # Pastikan inti judul tidak terpotong buruk di feed mobile (~40 char visible)
    if len(judul_inti) > YT_TITLE_VISIBLE:
        potong = judul_inti[:YT_TITLE_VISIBLE].rsplit(' ', 1)[0]
        judul_inti = potong if len(potong) >= 18 else judul_inti[:YT_TITLE_VISIBLE].rstrip()
    judul = f"{judul_inti} #Shorts" if '#shorts' not in judul_inti.lower() else judul_inti
    judul = judul[:YT_TITLE_MAX]

    terjemah, sumber, derajat = _info_dalil(k)
    faedah = (k.get('faedah') or '').strip()
    ask = cta_tunggal(k, seri)
    kunci = _kata_kunci_alami(k, seri)
    isi = ' '.join(a.get('narasi', '') for a in (k.get('adegan') or [])).strip()

    kredit_baris = ''
    if seri != 'harian' and ep and ep.get('url'):
        t_detik = _detik(k.get('menit'))
        tautan = ep['url'] + (f"&t={t_detik}s" if t_detik else '')
        kredit_baris = (
            f"Faedah dari kajian {ep['judul']}, {USTADZ}.\n"
            f"Kajian lengkap: {tautan}\n"
            f"Tonton juga versi episode penuh Sirah Nabawiyah di channel Sunnah Daily."
        )
    else:
        kredit_baris = "Ikuti seri Sunnah Harian & Sirah Nabawiyah lengkap di channel Sunnah Daily."

    tags_h = pilih_hashtag(k, seri, maks=4)
    bagian = [
        f"{k.get('judul_hook', '')} — {faedah} ({kunci})",
        isi,
        f"Dalil: {terjemah}\n({sumber}{derajat})" if terjemah else '',
        f"{ask}.",
        kredit_baris,
        ' '.join('#' + t for t in tags_h) + ' #Shorts',
    ]
    deskripsi = '\n\n'.join(b for b in bagian if b)[:YT_DESC_MAX]

    seo_tags = (
        ['sunnah harian', 'amalan sunnah', 'hadits shahih', 'adab islami', 'sunnah daily']
        if seri == 'harian'
        else ['sirah nabawiyah', 'kisah nabi muhammad', 'hadits shahih', 'sunnah daily', 'kajian islam']
    )
    for t in (k.get('tema') or []):
        if t and t not in seo_tags:
            seo_tags.append(str(t).strip())
    return {'judul': judul, 'deskripsi': deskripsi, 'tags': seo_tags[:15]}


def caption_tiktok(k, ep=None, seri='sirah'):
    """Caption TikTok otonom: hook echo, 1 CTA tunggal, dalil singkat, kredit kajian, maks 5 hashtag, tanpa URL."""
    judul = (k.get('judul_hook') or '').strip()
    faedah = (k.get('faedah') or '').strip()
    _, sumber, derajat = _info_dalil(k)
    ask = cta_tunggal(k, seri)
    ep_bersih = _judul_kajian_tanpa_pagar(ep.get('judul')) if ep else ''
    kredit = (
        f"Kajian {ep_bersih} — {USTADZ}."
        if seri != 'harian' and ep_bersih
        else 'Seri Sunnah Harian · Dalil terverifikasi.'
    )
    bagian = [
        f"{judul}. {ask}!",
        faedah,
        f"Dalil: {sumber}{derajat}" if sumber else '',
        kredit,
        ' '.join('#' + t for t in pilih_hashtag(k, seri, maks=5)),
    ]
    return '\n\n'.join(b for b in bagian if b)[:TT_CAPTION_MAX]


def caption_fb(k, ep=None, seri='sirah'):
    """Caption Facebook Reels: ringkas, dalil + derajat, kredit kajian, 1 CTA, maks 5 hashtag."""
    terjemah, sumber, derajat = _info_dalil(k)
    faedah = (k.get('faedah') or '').strip()
    ask = cta_tunggal(k, seri)
    ep_bersih = _judul_kajian_tanpa_pagar(ep.get('judul')) if ep else ''
    kredit = (
        f"Faedah dari kajian {ep_bersih}, {USTADZ}."
        if seri != 'harian' and ep_bersih
        else 'Sunnah Harian — amalan praktis sesuai dalil shahih.'
    )
    bagian = [
        f"{(k.get('judul_hook') or '').strip()} — {ask}.",
        f"Faedah: {faedah}" if faedah else '',
        f"Dalil: {terjemah}\n({sumber}{derajat})" if terjemah else '',
        kredit,
        ' '.join('#' + t for t in pilih_hashtag(k, seri, maks=5)),
    ]
    return '\n\n'.join(b for b in bagian if b)[:IG_CAPTION_MAX]
