"""Token brand Sunnah Daily (sumber: brand guideline). Satu tempat untuk warna, font dan ukuran."""
import os

from PIL import ImageFont

W, H = 1080, 1920
FPS = 24
TEPI = 96            # tepi-aman kiri/kanan
AMAN_ATAS = 220      # tertutup UI IG/YouTube
AMAN_BAWAH = 380

TEMA = {
    'siang': {
        'gading': '#F6F1E7', 'gading-2': '#EFE8DA', 'sage-muda': '#E3ECE4', 'sage': '#7FA087',
        'sage-tua': '#5E7F68', 'tinta': '#3F5A45', 'teks-redup': '#6B6358', 'terakota': '#D98E73',
        'terakota-tua': '#A9563F', 'di-terakota': '#FFFFFF', 'persik': '#F3DFD3', 'palsu': '#2E2A24',
        'langit': '#F6F1E7',
    },
    'malam': {
        'gading': '#1F2621', 'gading-2': '#2A322C', 'sage-muda': '#2F3B33', 'sage': '#7FA087',
        'sage-tua': '#A8C4AE', 'tinta': '#EDE6DA', 'teks-redup': '#B8AE9F', 'terakota': '#E8A68C',
        'terakota-tua': '#E8A68C', 'di-terakota': '#1F2621', 'persik': '#3A2C26', 'palsu': '#EDE6DA',
        'langit': '#1F2621',
    },
}


def rgb(h):
    h = h.lstrip('#')
    return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4))


def warna(tema):
    return {k: rgb(v) for k, v in TEMA[tema].items()}


_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'fonts')
_CACHE = {}


def font(nama, ukuran):
    """nama: judul | isi | isi-tebal | isi-sedang | arab"""
    berkas = {
        'judul': 'Fraunces-SemiBold.ttf', 'isi': 'Nunito-Regular.ttf', 'isi-sedang': 'Nunito-SemiBold.ttf',
        'isi-tebal': 'Nunito-ExtraBold.ttf', 'arab': 'Amiri-Regular.ttf',
    }[nama]
    k = (berkas, ukuran)
    if k not in _CACHE:
        _CACHE[k] = ImageFont.truetype(os.path.join(_DIR, berkas), ukuran,
                                       layout_engine=ImageFont.Layout.RAQM)
    return _CACHE[k]
