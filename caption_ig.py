"""Penyusun caption Instagram untuk semua seri Sunnah Daily (pola skill ig-caption + ig-human).

Reel sudah membawa hook-nya sendiri, jadi caption TIDAK mengulang hook. Bentuknya:
  baris 1   judul + satu ajakan (simpan), muat dalam 125 karakter yang terlihat sebelum "... more"
  isi       paragraf pendek: poin narasi, dalil lengkap (sumber, nomor, derajat), faedah, kata kunci pencarian
  tagar     paling banyak 5 (batas Instagram sejak Des 2025), sebagai label topik
Teks juga dibersihkan dari jejak mesin: karakter tak terlihat, em dash, tanda kutip melengkung.
"""
import re
import unicodedata

TERLIHAT = 125      # karakter yang tampil sebelum dipotong "... more"
MAKS = 2200         # batas caption Instagram
MAKS_TAGAR = 5
AJAKAN = 'Simpan dulu, biar gampang dibuka lagi pas mau diamalkan.'
AJAKAN_PENDEK = 'Simpan dulu ya.'

_TIPOGRAFI = {'—': ', ', '–': '-', '‘': "'", '’': "'", '“': '"', '”': '"',
              '…': '...', '•': '-', ' ': ' ', ' ': ' ', ' ': ' '}


def bersihkan(teks):
    """Buang karakter format tak terlihat, ganti tipografi 'sempurna' dengan versi keyboard biasa."""
    t = ''.join(_TIPOGRAFI.get(c, c) for c in teks)
    # Kategori Cf = karakter format (zero-width, BOM, tag). Caption tidak memuat teks Arab, jadi aman dibuang semua.
    t = ''.join(c for c in t if unicodedata.category(c) != 'Cf')
    t = re.sub(r' ,', ',', t)
    t = re.sub(r',\s*([.,!?])', r'\1', t)
    t = re.sub(r'[ \t]{2,}', ' ', t)
    return t.strip()


def tagar(tetap, tema, maks=MAKS_TAGAR):
    """Tagar spesifik: tema video dulu, lalu tagar tetap seri, maksimal 5 dan tanpa duplikat."""
    tema_tag = [re.sub(r'\W', '', t.lower()) for t in tema]
    urut = [tetap[0]] + tema_tag[:3] + list(tetap[1:])
    return ['#' + t for t in dict.fromkeys(x for x in urut if x)][:maks]


def baris_dalil(dl):
    derajat = ''
    if dl.get('jenis') in ('hadits', 'atsar') and dl.get('derajat'):
        derajat = f" · {dl['derajat'].capitalize()}"
        if dl['derajat'] == 'lemah':
            derajat += ', bukan dalil'
    return f"📖 {dl['terjemah']}\n({dl['sumber']}{derajat})"


def susun(judul, isi, dalil, faedah, tema, tetap, kredit=None):
    """isi: daftar kalimat/paragraf narasi. kredit: baris sumber kajian (opsional). Kembalikan caption siap posting."""
    judul = judul.strip().rstrip('.!?')
    baris1 = f'{judul}. {AJAKAN}'
    if len(baris1) > TERLIHAT:
        baris1 = f'{judul}. {AJAKAN_PENDEK}'
    bagian = [baris1, '\n'.join(s.strip() for s in isi if s.strip()), baris_dalil(dalil), f'Faedahnya: {faedah.strip()}']
    if tema:
        bagian.append('Topik: ' + ', '.join(t.strip() for t in tema[:3]))
    if kredit:
        bagian.append(kredit)
    tag = ' '.join(tagar(tetap, tema))
    teks = bersihkan('\n\n'.join(bagian))
    if len(teks) + len(tag) + 2 > MAKS:   # potong narasi, bukan dalil
        lebih = len(teks) + len(tag) + 2 - MAKS
        isi_teks = bagian[1]
        bagian[1] = isi_teks[:max(0, len(isi_teks) - lebih - 3)].rsplit(' ', 1)[0] + '...'
        teks = bersihkan('\n\n'.join(bagian))
    return f'{teks}\n\n{tag}'
