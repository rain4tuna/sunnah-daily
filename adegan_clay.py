"""Pilih aset clay (remotion/public_panjang/aset/daftar.json) untuk tiap babak video panjang (komposisi SunnahClay).

Tanpa Gemini: berbasis aturan dari teks narasi + kunci ilustrasi storyboard_ikon, jadi hasilnya bisa diulang.

ATURAN TOKOH (lihat aset/PROMPT_ASET_META_AI.md):
- Nabi ﷺ, nabi lain, dan malaikat tidak pernah tampil (memang tidak ada asetnya).
- Tokoh bernama (keluarga Nabi, sahabat, pembesar Quraisy, ...) hanya tampil bila namanya disebut di babak itu.
- Babak yang menyebut Nabi ﷺ / malaikat TIDAK diberi tokoh umum tanpa nama, supaya tidak ada sosok yang bisa
  disangka beliau. Tokoh bernama tetap boleh, berdiri sendiri.
- Klip Flow yang menampilkan tokoh bernama hanya dipakai bila tokoh itu disebut.
"""
import json
import os
import re
import zlib

ROOT = os.path.dirname(os.path.abspath(__file__))
DAFTAR = os.path.join(ROOT, 'remotion', 'public_panjang', 'aset', 'daftar.json')

# nama tokoh di narasi -> kode karakter (aset t01..t10, k09)
TOKOH_BERNAMA = [
    (r'abdul muth?th?alib', 't01'), (r'abu th?alib', 't02'), (r'\baminah\b', 't03'), (r'halimah', 't04'),
    (r'khadijah', 't05'), (r'abu bakr|abu bakar', 't06'), (r'\bbilal\b', 't07'), (r'\bhamzah\b', 't08'),
    (r'abu lahab', 't09'), (r'abu jahl|abu jahal', 't10'), (r'heraklius|hiraql|kaisar|raja romawi', 'k09'),
]
SEBUT_NABI = ('ﷺ', 'rasulullah', 'nabi', 'beliau', 'malaikat', 'jibril', "'alaihis", 'alaihissalam')

# klip Flow: (pola kata di narasi, kode klip, kode tokoh yang wajib disebut atau '')
KLIP = [
    (r'gajah|abrahah', 'b03_gajah_abrahah', ''), (r'burung|ababil', 'b04_burung_batu', ''),
    (r'zamzam|sumur', 'b05_abdul_muthalib_sumur', 't01'), (r'romawi|heraklius|hiraql|kaisar', 'b06_raja_romawi_surat', ''),
    (r'halimah|bani sa.?d|ibu susu', 'b07_halimah_desa', 't04'), (r'khadijah', 'b08_khadijah_rumah', 't05'),
    (r'harta|kekayaan|dagang|emas|uang|hadiah', 'b09_pasar_pedagang', ''),
    (r'abu jahl|abu jahal|abu lahab|pembesar quraisy|para pembesar', 'b10_pembesar_quraisy', 't10'),
    (r'\bbilal\b|ahad', 'b11_bilal_ahad', 't07'), (r'habasyah|habsyah|najasyi', 'b12_hijrah_habasyah', ''),
    (r'rayap', 'b14_piagam_rayap', ''), (r'boikot|piagam', 'b13_abu_thalib_boikot', 't02'),
    (r'kafilah|perjalanan dagang|\bsyam\b', 'b01_kafilah_senja', ''), (r'penduduk makkah|kaum quraisy', 'b02_kerumunan_makkah', ''),
]

# kata di narasi -> latar (dicek berurutan; yang pertama cocok dipakai)
LATAR_KATA = [
    (r'shafa', 'l07_bukit_shafa'), (r'\bgua\b|hira|tsur', 'l08_gua_gunung'), (r'habasyah|najasyi|uskup', 'l15_istana_afrika'),
    (r'romawi|heraklius|hiraql|kaisar', 'l16_istana_romawi'), (r'\blaut\b|kapal|pantai|menyeberang', 'l14_pantai_kapal'),
    (r'pasar|dagang|jual beli', 'l11_pasar'), (r'boikot|lembah|kelaparan|terik|panas', 'l13_lembah_tandus'),
    (r'desa|badui|bani sa.?d|pedalaman', 'l10_desa_badui'), (r"ka'?bah|thawaf|masjidil haram|baitullah", 'l06_kabah'),
    (r'\bmalam\b', 'l05_makkah_malam'), (r'rumah|keluarga|istri', 'l12_rumah_dalam'), (r'makkah|quraisy', 'l04_makkah_siang'),
]
# kunci ilustrasi storyboard_ikon -> (latar, benda)
LATAR_ILUSTRASI = {
    'badai': ('l03_gurun_malam', []), 'kota_malam': ('l05_makkah_malam', []), 'quran': ('l12_rumah_dalam', ['b22_kitab']),
    'kafilah': ('l02_gurun_senja', []), 'kabah': ('l06_kabah', []), 'masjid': ('l04_makkah_siang', []),
    'gua': ('l08_gua_gunung', []), 'majelis': ('l05_makkah_malam', []), 'lentera': ('l12_rumah_dalam', ['b10_lentera']),
    'fajar': ('l07_bukit_shafa', []), 'air': ('l10_desa_badui', ['b02_kendi']), 'hidangan': ('l12_rumah_dalam', ['b01_kurma']),
    'pintu': ('l12_rumah_dalam', []), 'sedekah': ('l11_pasar', ['b05_koin']), 'hati': ('l07_bukit_shafa', []),
}
# kata di narasi -> benda
BENDA_KATA = [
    (r'kurma|makan', 'b01_kurma'), (r'\bair\b|minum|wudhu', 'b02_kendi'), (r'harta|emas|uang|hadiah|suap', 'b05_koin'),
    (r'surat|tulisan', 'b07_surat'), (r'piagam|perjanjian', 'b08_piagam'), (r'lampu|pelita', 'b09_pelita'),
    (r'lentera|malam', 'b10_lentera'), (r'pedang|perang|bunuh', 'b13_pedang'), (r'sumur|zamzam', 'b17_sumur'),
    (r'raja|kerajaan|kekuasaan|pemimpin', 'b19_mahkota'), (r'permadani|tikar|duduk', 'b21_permadani'),
    (r"al-?qur'?an|ayat|wahyu|surah|kitab", 'b22_kitab'), (r'kapal|perahu|menyeberang', 'b25_perahu'),
    (r'batu|terik|panas', 'b27_batu'),
]
MALAM = {'l03_gurun_malam', 'l05_makkah_malam', 'l08_gua_gunung'}
DALAM = {'l12_rumah_dalam', 'l15_istana_afrika', 'l16_istana_romawi'}
# tokoh umum tanpa nama, dipilih dari konteks (pola, kandidat); yang pertama cocok dipakai
UMUM = [
    (r'habasyah|najasyi|uskup|pendeta', []),          # istana Habasyah: belum ada aset yang cocok, cukup latar & benda
    (r'radhiyallahu|sahabat', ['k03']),
    (r'musyrik|quraisy|pembesar|kafir|utusan|menyogok|suap', ['k02', 'k01']),
    (r'muslimin|muhajirin|pemuda', ['k03']),
    (r'raja romawi|heraklius|kaisar|persia', ['k09']), (r'prajurit|pasukan|tentara', ['k10']),
    (r'anak|bayi|yatim', ['k07', 'k08']), (r'ibu|wanita|perempuan', ['k05']),
    (r'', ['k03', 'k01']),
]
# benda cadangan supaya adegan tanpa tokoh/klip tidak kosong
BENDA_CADANGAN = {'l07_bukit_shafa': 'b10_lentera', 'l12_rumah_dalam': 'b10_lentera', 'l15_istana_afrika': 'b21_permadani',
                  'l16_istana_romawi': 'b19_mahkota', 'l11_pasar': 'b05_koin', 'l13_lembah_tandus': 'b27_batu',
                  'l06_kabah': 'b17_sumur', 'l10_desa_badui': 'b02_kendi', 'l14_pantai_kapal': 'b25_perahu'}


def muat_daftar():
    with open(DAFTAR, encoding='utf-8') as f:
        return json.load(f)


def _cari(pola_daftar, teks):
    return [hasil for pola, *hasil in pola_daftar if re.search(pola, teks)]


def _tokoh(kode, d, x, dari=None):
    t = {'diam': d[f'{kode}_p01']['file'], 'x': x}
    if dari and f'{kode}_p03' in d and f'{kode}_p04' in d:
        t.update(jalan=[d[f'{kode}_p03']['file'], d[f'{kode}_p04']['file']], dari=dari)
    return t


def pilih(segmen, benih=''):
    """Kembalikan daftar adegan (satu per segmen) untuk props 'adegan' komposisi SunnahClay."""
    d = muat_daftar()
    awan = [d['e01_awan']['file']] * 2 if 'e01_awan' in d else []    # e02 awan hujan, e03 gayanya beda
    bintang = d['e06_bintang']['file'] if 'e06_bintang' in d else None
    klip_terpakai, hasil, sebelumnya = set(), [], None
    for i, s in enumerate(segmen):
        teks = ' '.join(str(s.get(k) or '') for k in ('judul', 'narasi', 'ucap', 'label')).lower()
        acak = zlib.crc32(f'{benih}|{i}'.encode())
        jenis = s['jenis']
        if jenis == 'dalil' and sebelumnya:
            hasil.append(sebelumnya)          # kartu dalil di atas latar adegan sebelumnya (dikaburkan)
            continue
        if jenis == 'pembuka':
            a = {'latar': d['l02_gurun_senja']['file'], 'suasana': 'siang'}
            if 'b01_kafilah_senja' in d:
                a['gerak'] = {'file': d['b01_kafilah_senja']['file'], 'durasi': d['b01_kafilah_senja']['durasi']}
            hasil.append(a)
            sebelumnya = a
            continue
        if jenis in ('ajak', 'kuis', 'jawab'):
            a = {'latar': d['l10_desa_badui']['file'], 'suasana': 'siang', 'awan': awan}
            if jenis == 'ajak':
                a['tokoh'] = [_tokoh(k, d, x, dari=sisi) for k, x, sisi in (('k07', 520, 'kiri'), ('k08', 1400, 'kanan'))
                              if f'{k}_p01' in d]
            else:
                a['bintang'] = bintang
            hasil.append(a)
            continue
        if jenis == 'penutup':
            a = {'latar': d['l10_desa_badui']['file'], 'suasana': 'siang'}
            if 'b15_anak_bermain' in d:
                a['gerak'] = {'file': d['b15_anak_bermain']['file'], 'durasi': d['b15_anak_bermain']['durasi']}
            hasil.append(a)
            continue

        bernama = [kode for (kode,) in _cari(TOKOH_BERNAMA, teks)]
        sebut_nabi = any(k in teks for k in SEBUT_NABI)
        # latar
        latar_kode, benda = LATAR_ILUSTRASI.get(s.get('ilustrasi') or '', ('l04_makkah_siang', []))
        cocok = _cari(LATAR_KATA, teks)
        if cocok:
            latar_kode = cocok[0][0]
        a = {'latar': d[latar_kode]['file'], 'suasana': 'malam' if latar_kode in MALAM else 'siang'}
        # klip Flow: hanya bila kata kuncinya ada, tokohnya disebut (kalau klip menampilkan tokoh), belum dipakai
        for kode, wajib in _cari(KLIP, teks):
            if kode in d and kode not in klip_terpakai and (not wajib or wajib in bernama):
                a['gerak'] = {'file': d[kode]['file'], 'durasi': d[kode]['durasi']}
                klip_terpakai.add(kode)
                break
        if 'gerak' not in a:
            # tokoh: yang disebut namanya; tokoh umum hanya bila babak tidak menyebut Nabi ﷺ
            pilihan = [k for k in bernama if f'{k}_p01' in d][:2]
            if not pilihan and not sebut_nabi and (s.get('tokoh') or jenis == 'poin'):
                kandidat = next(k for pola, k in UMUM if re.search(pola, teks))
                pilihan = [kandidat[acak % len(kandidat)]] if kandidat else []
            posisi = [1340] if len(pilihan) == 1 else [560, 1360]
            a['tokoh'] = [_tokoh(k, d, x, dari='kiri' if (acak + j) % 2 == 0 else 'kanan')
                          for j, (k, x) in enumerate(zip(pilihan, posisi))]
            # benda: dari ilustrasi + kata di narasi, maksimal 2
            benda = list(dict.fromkeys(benda + [k for (k,) in _cari(BENDA_KATA, teks)]))
            benda = [k for k in benda if k in d][:1 if a['tokoh'] else 2]
            if not benda and not a['tokoh']:
                benda = [BENDA_CADANGAN.get(latar_kode, 'b22_kitab')]
            if a['tokoh']:
                bx = 900 if len(a['tokoh']) == 1 else 960
                a['benda'] = [{'file': d[k]['file'], 'x': bx, 'tinggi': 260} for k in benda]
            else:
                a['benda'] = [{'file': d[k]['file'], 'x': 1250 + j * 380, 'tinggi': 360 - j * 60} for j, k in enumerate(benda)]
            if latar_kode not in DALAM:
                if a['suasana'] == 'siang':
                    a['awan'] = awan
                elif bintang:
                    a['bintang'] = bintang
        hasil.append(a)
        sebelumnya = a
    return hasil


if __name__ == '__main__':
    contoh = [{'jenis': 'poin', 'narasi': 'Abu Thalib bersedih melihat piagam boikot', 'ilustrasi': 'badai'},
              {'jenis': 'poin', 'narasi': 'Rasulullah ﷺ berdiri di bukit Shafa', 'ilustrasi': 'fajar', 'tokoh': 'berdiri'},
              {'jenis': 'poin', 'narasi': 'Seseorang membawa kurma ke pasar', 'ilustrasi': 'hidangan', 'tokoh': 'berdiri'}]
    print(json.dumps(pilih(contoh), ensure_ascii=False, indent=1))
