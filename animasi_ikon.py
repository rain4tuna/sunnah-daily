"""
Renderer "Animasi Ikon" Sunnah Daily (diadaptasi dari template edukasi BDF): ikon digambar kode, gaya bergiliran
  papan  — papan tulis sage tua, coretan kapur, aksen terakota
  flat   — latar gading, ikon datar berbayang
  kertas — kertas bergaris kotak, garis margin terakota, gaya spidol
Palet & font dari gaya.py (Pastel Minimalis, tema siang/malam). TANPA makhluk bernyawa: ikon hanya benda & tempat.
Tanpa musik instrumen.

segmen (dari storyboard_ikon.segmen):
  {'jenis': 'hook',    'judul': '...', 'ikon': ['masjid'], 'ucap': '...', 'wav': path}
  {'jenis': 'poin',    'narasi': '...', 'label': 'maks 5 kata', 'ikon': ['kitab', 'lentera'], 'wav': path}
  {'jenis': 'dalil',   'dalil': {...}, 'narasi': '...', 'wav': path}
  {'jenis': 'faedah',  'judul': '...', 'faedah': '...', 'ikon': ['hati'], 'wav': path}
  {'jenis': 'penutup', 'ajakan': '...', 'seri': '...', 'kredit': '...', 'wav': path}
Setiap segmen boleh punya 'kicker' (mis. "SIRAH #03" / "SUNNAH HARIAN").
"""
import math
import os
import random
import subprocess
import tempfile

from PIL import Image, ImageChops, ImageDraw, ImageFilter

import gaya
import video
from video import SAW, bungkus, judul_pas, kelompok_kata, lebar, susun_audio, tengah, tulis

W, H, FPS = gaya.W, gaya.H, gaya.FPS
FFMPEG = os.environ.get('FFMPEG', 'ffmpeg')
HANDLE = '@sun_nahdaily'
URUTAN_GAYA = ['papan', 'flat', 'kertas']


# ------------------------------------------------------------------ palet per gaya
def palet(gaya_v, tema):
    c = gaya.warna(tema)
    if gaya_v == 'papan':
        return dict(bg=(50, 70, 57), bg2=(66, 92, 74), ink=(242, 238, 228), fill=c['terakota'] if tema == 'siang' else (232, 166, 140),
                    fill2=(84, 112, 92), teks=(242, 238, 228), sub=(196, 214, 200), aksen=(236, 196, 120),
                    air=(170, 206, 214), lw=11, kapur=True, sorot=(217, 142, 115), di_sorot=(255, 255, 255),
                    kartu=(60, 84, 68), garis=(98, 128, 106))
    base = dict(bg=c['gading'], bg2=c['gading-2'], ink=c['tinta'], fill=c['terakota'], fill2=c['gading-2'],
                teks=c['tinta'], sub=c['teks-redup'], aksen=c['sage'], air=(140, 180, 196), lw=10, kapur=False,
                sorot=c['terakota-tua'], di_sorot=c['di-terakota'], kartu=c['gading-2'], garis=c['sage-muda'])
    if gaya_v == 'kertas':
        base.update(fill=c['sage'], fill2=c['gading'], lw=9)
    return base


# ------------------------------------------------------------------ ikon (benda & tempat saja)
def _r(cx, cy, s, x0, y0, x1, y1):
    return [cx + x0 * s, cy + y0 * s, cx + x1 * s, cy + y1 * s]


def _p(cx, cy, s, pts):
    return [(cx + x * s, cy + y * s) for x, y in pts]


def ik_masjid(d, cx, cy, s, p):
    lw, ink = p['lw'], p['ink']
    d.rectangle(_r(cx, cy, s, -0.40, 0.0, 0.40, 0.42), fill=p['fill2'], outline=ink, width=lw)
    d.pieslice(_r(cx, cy, s, -0.26, -0.30, 0.26, 0.22), 180, 360, fill=p['fill'], outline=ink, width=lw)
    d.line(_p(cx, cy, s, [(0, -0.30), (0, -0.42)]), fill=ink, width=max(3, lw // 2))
    d.chord(_r(cx, cy, s, -0.05, -0.50, 0.05, -0.40), 0, 360, fill=p['aksen'])
    for x in (-0.47, 0.41):
        d.rectangle(_r(cx, cy, s, x, -0.30, x + 0.06, 0.42), fill=p['fill2'], outline=ink, width=max(3, lw - 3))
        d.polygon(_p(cx, cy, s, [(x - 0.01, -0.30), (x + 0.03, -0.42), (x + 0.07, -0.30)]), fill=p['fill'], outline=ink)
    d.pieslice(_r(cx, cy, s, -0.09, 0.16, 0.09, 0.50), 180, 360, fill=p['ink'])
    d.rectangle(_r(cx, cy, s, -0.09, 0.33, 0.09, 0.42), fill=p['ink'])


def ik_kabah(d, cx, cy, s, p):
    lw, ink = p['lw'], p['ink']
    d.polygon(_p(cx, cy, s, [(-0.40, -0.16), (0.10, -0.30), (0.42, -0.14), (-0.08, 0.0)]), fill=(70, 66, 60), outline=ink, width=lw)
    d.polygon(_p(cx, cy, s, [(-0.40, -0.16), (-0.08, 0.0), (-0.08, 0.44), (-0.40, 0.28)]), fill=(46, 42, 38), outline=ink, width=lw)
    d.polygon(_p(cx, cy, s, [(-0.08, 0.0), (0.42, -0.14), (0.42, 0.30), (-0.08, 0.44)]), fill=(58, 54, 48), outline=ink, width=lw)
    d.polygon(_p(cx, cy, s, [(-0.40, -0.06), (-0.08, 0.10), (0.42, -0.04), (0.42, 0.04), (-0.08, 0.18), (-0.40, 0.02)]),
              fill=p['aksen'])


def ik_kitab(d, cx, cy, s, p):
    lw, ink = p['lw'], p['ink']
    d.polygon(_p(cx, cy, s, [(0, -0.26), (-0.44, -0.36), (-0.44, 0.30), (0, 0.40)]), fill=p['fill2'], outline=ink, width=lw)
    d.polygon(_p(cx, cy, s, [(0, -0.26), (0.44, -0.36), (0.44, 0.30), (0, 0.40)]), fill=p['fill2'], outline=ink, width=lw)
    for i in range(3):
        y = -0.16 + i * 0.14
        d.line(_p(cx, cy, s, [(-0.34, y - 0.03), (-0.10, y + 0.02)]), fill=ink, width=max(3, lw // 2))
        d.line(_p(cx, cy, s, [(0.10, y + 0.02), (0.34, y - 0.03)]), fill=p['fill'], width=max(3, lw // 2))


def ik_quran(d, cx, cy, s, p):
    """Mushaf di atas rehal."""
    lw, ink = p['lw'], p['ink']
    d.line(_p(cx, cy, s, [(-0.36, 0.42), (0.36, 0.06)]), fill=ink, width=lw)
    d.line(_p(cx, cy, s, [(0.36, 0.42), (-0.36, 0.06)]), fill=ink, width=lw)
    d.polygon(_p(cx, cy, s, [(0, -0.06), (-0.42, -0.30), (-0.42, 0.10), (0, 0.24)]), fill=p['aksen'], outline=ink, width=lw)
    d.polygon(_p(cx, cy, s, [(0, -0.06), (0.42, -0.30), (0.42, 0.10), (0, 0.24)]), fill=p['aksen'], outline=ink, width=lw)
    d.polygon(_p(cx, cy, s, [(-0.30, -0.18), (-0.12, -0.10), (-0.12, 0.08), (-0.30, 0.0)]), fill=p['fill2'])
    d.polygon(_p(cx, cy, s, [(0.30, -0.18), (0.12, -0.10), (0.12, 0.08), (0.30, 0.0)]), fill=p['fill2'])


def ik_lentera(d, cx, cy, s, p):
    lw, ink = p['lw'], p['ink']
    d.arc(_r(cx, cy, s, -0.10, -0.50, 0.10, -0.32), 180, 360, fill=ink, width=max(4, lw // 2))
    d.polygon(_p(cx, cy, s, [(-0.16, -0.36), (0.16, -0.36), (0.22, -0.28), (-0.22, -0.28)]), fill=p['fill'], outline=ink, width=lw)
    d.polygon(_p(cx, cy, s, [(-0.20, -0.28), (0.20, -0.28), (0.26, 0.26), (-0.26, 0.26)]), fill=p['fill2'], outline=ink, width=lw)
    d.ellipse(_r(cx, cy, s, -0.08, -0.08, 0.08, 0.16), fill=(246, 196, 104))
    d.ellipse(_r(cx, cy, s, -0.04, -0.02, 0.04, 0.12), fill=(255, 236, 180))
    d.rectangle(_r(cx, cy, s, -0.28, 0.26, 0.28, 0.36), fill=p['fill'], outline=ink, width=lw)


def ik_bulan_bintang(d, cx, cy, s, p):
    d.ellipse(_r(cx, cy, s, -0.40, -0.40, 0.30, 0.30), fill=(246, 214, 140), outline=p['ink'], width=p['lw'])
    d.ellipse(_r(cx, cy, s, -0.18, -0.48, 0.44, 0.14), fill=p['bg'])
    pts = []
    for i in range(10):
        a = -math.pi / 2 + i * math.pi / 5
        rr = 0.14 if i % 2 == 0 else 0.06
        pts.append((0.26 + rr * math.cos(a), 0.10 + rr * math.sin(a)))
    d.polygon(_p(cx, cy, s, pts), fill=(246, 214, 140), outline=p['ink'])


def ik_pohon_kurma(d, cx, cy, s, p):
    lw, ink = p['lw'], p['ink']
    d.polygon(_p(cx, cy, s, [(-0.05, -0.20), (0.05, -0.20), (0.09, 0.46), (-0.09, 0.46)]), fill=(168, 128, 92), outline=ink, width=lw)
    for a in (-160, -125, -90, -55, -20):
        r = math.radians(a)
        x1, y1 = math.cos(r) * 0.44, -0.22 + math.sin(r) * 0.30 + 0.16
        d.line(_p(cx, cy, s, [(0, -0.22), ((x1) * 0.6, -0.36), (x1, y1)]), fill=p['aksen'], width=int(lw * 1.6), joint='curve')
    for x in (-0.08, 0.0, 0.08):
        d.ellipse(_r(cx, cy, s, x - 0.04, -0.16, x + 0.04, -0.06), fill=p['fill'])


def ik_kurma(d, cx, cy, s, p):
    lw, ink = p['lw'], p['ink']
    d.chord(_r(cx, cy, s, -0.46, -0.06, 0.46, 0.40), 0, 180, fill=p['fill2'], outline=ink, width=lw)
    d.line(_p(cx, cy, s, [(-0.46, 0.17), (0.46, 0.17)]), fill=ink, width=lw)
    for x, y, a in ((-0.20, 0.02, -20), (0.04, -0.02, 10), (0.24, 0.04, 30)):
        d.ellipse(_r(cx, cy, s, x - 0.12, y - 0.07, x + 0.12, y + 0.10), fill=(140, 82, 58), outline=ink, width=max(3, lw // 2))
        d.arc(_r(cx, cy, s, x - 0.08, y - 0.04, x + 0.06, y + 0.06), 200, 300, fill=(200, 140, 110), width=4)


def ik_tenda(d, cx, cy, s, p):
    lw, ink = p['lw'], p['ink']
    d.polygon(_p(cx, cy, s, [(-0.46, 0.36), (0, -0.36), (0.46, 0.36)]), fill=p['fill2'], outline=ink, width=lw)
    d.polygon(_p(cx, cy, s, [(-0.12, 0.36), (0, 0.02), (0.12, 0.36)]), fill=p['fill'], outline=ink, width=lw)
    d.line(_p(cx, cy, s, [(-0.56, 0.36), (0.56, 0.36)]), fill=ink, width=lw)
    d.line(_p(cx, cy, s, [(0, -0.36), (0, -0.46)]), fill=ink, width=max(3, lw // 2))


def ik_gua(d, cx, cy, s, p):
    lw, ink = p['lw'], p['ink']
    d.polygon(_p(cx, cy, s, [(-0.50, 0.40), (-0.36, -0.10), (-0.10, -0.34), (0.20, -0.30), (0.42, -0.04), (0.50, 0.40)]),
              fill=(176, 150, 120), outline=ink, width=lw)
    d.pieslice(_r(cx, cy, s, -0.20, -0.04, 0.20, 0.64), 180, 360, fill=(46, 42, 38))
    d.rectangle(_r(cx, cy, s, -0.20, 0.16, 0.20, 0.40), fill=(46, 42, 38))
    d.line(_p(cx, cy, s, [(-0.58, 0.40), (0.58, 0.40)]), fill=ink, width=lw)


def ik_gunung(d, cx, cy, s, p):
    lw, ink = p['lw'], p['ink']
    d.polygon(_p(cx, cy, s, [(-0.50, 0.38), (-0.12, -0.30), (0.14, 0.10), (0.26, -0.08), (0.50, 0.38)]),
              fill=p['aksen'], outline=ink, width=lw)
    d.polygon(_p(cx, cy, s, [(-0.12, -0.30), (-0.22, -0.12), (-0.02, -0.12)]), fill=p['fill2'])


def ik_matahari(d, cx, cy, s, p):
    for i in range(12):
        a = math.radians(i * 30)
        d.line([(cx + math.cos(a) * s * 0.28, cy + math.sin(a) * s * 0.28),
                (cx + math.cos(a) * s * 0.45, cy + math.sin(a) * s * 0.45)], fill=(240, 186, 96), width=p['lw'])
    d.ellipse(_r(cx, cy, s, -0.22, -0.22, 0.22, 0.22), fill=(240, 186, 96), outline=p['ink'], width=p['lw'])


def ik_awan_hujan(d, cx, cy, s, p):
    lw, ink = p['lw'], p['ink']
    for x0, y0, x1, y1 in ((-0.42, -0.16, -0.06, 0.14), (-0.20, -0.34, 0.22, 0.06), (0.04, -0.20, 0.42, 0.14)):
        d.ellipse(_r(cx, cy, s, x0, y0, x1, y1), fill=p['fill2'], outline=ink, width=lw)
    d.rectangle(_r(cx, cy, s, -0.30, -0.04, 0.30, 0.13), fill=p['fill2'])
    d.line(_p(cx, cy, s, [(-0.30, 0.14), (0.30, 0.14)]), fill=ink, width=lw)
    for x in (-0.22, 0.0, 0.22):
        d.line(_p(cx, cy, s, [(x, 0.24), (x - 0.05, 0.40)]), fill=p['air'], width=lw)


def ik_tetes_air(d, cx, cy, s, p):
    lw, ink = p['lw'], p['ink']
    d.polygon(_p(cx, cy, s, [(0, -0.44), (0.24, 0.02), (-0.24, 0.02)]), fill=p['air'])
    d.ellipse(_r(cx, cy, s, -0.26, -0.14, 0.26, 0.38), fill=p['air'], outline=ink, width=lw)
    d.line(_p(cx, cy, s, [(0, -0.44), (-0.24, 0.02)]), fill=ink, width=lw)
    d.line(_p(cx, cy, s, [(0, -0.44), (0.24, 0.02)]), fill=ink, width=lw)
    d.arc(_r(cx, cy, s, -0.16, -0.02, 0.12, 0.28), 120, 200, fill=(255, 255, 255), width=6)


def ik_gelas(d, cx, cy, s, p):
    lw, ink = p['lw'], p['ink']
    d.polygon(_p(cx, cy, s, [(-0.26, -0.36), (0.26, -0.36), (0.18, 0.40), (-0.18, 0.40)]), fill=p['fill2'], outline=ink, width=lw)
    d.polygon(_p(cx, cy, s, [(-0.235, -0.12), (0.235, -0.12), (0.18, 0.38), (-0.18, 0.38)]), fill=p['air'])
    d.polygon(_p(cx, cy, s, [(-0.26, -0.36), (0.26, -0.36), (0.18, 0.40), (-0.18, 0.40)]), outline=ink, width=lw)


def ik_jam(d, cx, cy, s, p):
    lw, ink = p['lw'], p['ink']
    d.ellipse(_r(cx, cy, s, -0.40, -0.40, 0.40, 0.40), fill=p['fill2'], outline=ink, width=lw)
    for i in range(12):
        a = math.radians(i * 30)
        d.line([(cx + math.cos(a) * s * 0.30, cy + math.sin(a) * s * 0.30),
                (cx + math.cos(a) * s * 0.35, cy + math.sin(a) * s * 0.35)], fill=ink, width=max(3, lw // 2))
    d.line(_p(cx, cy, s, [(0, 0), (0, -0.24)]), fill=ink, width=lw)
    d.line(_p(cx, cy, s, [(0, 0), (0.17, 0.08)]), fill=p['fill'], width=lw)


def ik_kalender(d, cx, cy, s, p):
    lw, ink = p['lw'], p['ink']
    d.rounded_rectangle(_r(cx, cy, s, -0.40, -0.32, 0.40, 0.42), radius=int(s * 0.05), fill=p['fill2'], outline=ink, width=lw)
    d.rectangle(_r(cx, cy, s, -0.40, -0.32, 0.40, -0.12), fill=p['fill'], outline=ink, width=lw)
    for x in (-0.22, 0.22):
        d.line(_p(cx, cy, s, [(x, -0.42), (x, -0.24)]), fill=ink, width=lw)
    for r in range(3):
        for c in range(4):
            x, y = -0.28 + c * 0.19, -0.02 + r * 0.14
            d.rectangle(_r(cx, cy, s, x - 0.04, y - 0.035, x + 0.04, y + 0.035), fill=p['fill'] if (r, c) == (1, 2) else ink)


def ik_tasbih(d, cx, cy, s, p):
    n = 18
    for i in range(n):
        a = math.radians(i * 360 / n - 90)
        x, y = math.cos(a) * 0.34, math.sin(a) * 0.34 - 0.06
        d.ellipse(_r(cx, cy, s, x - 0.055, y - 0.055, x + 0.055, y + 0.055), fill=p['fill'], outline=p['ink'], width=3)
    d.line(_p(cx, cy, s, [(0, 0.28), (0, 0.44)]), fill=p['ink'], width=p['lw'] // 2 + 2)
    d.polygon(_p(cx, cy, s, [(-0.06, 0.40), (0.06, 0.40), (0.0, 0.52)]), fill=p['aksen'], outline=p['ink'])


def ik_sajadah(d, cx, cy, s, p):
    lw, ink = p['lw'], p['ink']
    d.polygon(_p(cx, cy, s, [(-0.30, -0.42), (0.30, -0.42), (0.40, 0.42), (-0.40, 0.42)]), fill=p['fill'], outline=ink, width=lw)
    d.polygon(_p(cx, cy, s, [(-0.20, -0.30), (0.20, -0.30), (0.27, 0.30), (-0.27, 0.30)]), outline=p['fill2'], width=6)
    d.pieslice(_r(cx, cy, s, -0.12, -0.26, 0.12, 0.0), 180, 360, fill=p['aksen'])
    d.rectangle(_r(cx, cy, s, -0.12, -0.13, 0.12, 0.04), fill=p['aksen'])


def ik_pena(d, cx, cy, s, p):
    lw, ink = p['lw'], p['ink']
    d.polygon(_p(cx, cy, s, [(0.36, -0.44), (0.44, -0.36), (-0.24, 0.32), (-0.32, 0.24)]), fill=p['fill'], outline=ink, width=lw)
    d.polygon(_p(cx, cy, s, [(-0.24, 0.32), (-0.32, 0.24), (-0.44, 0.44)]), fill=p['fill2'], outline=ink, width=lw)
    d.line(_p(cx, cy, s, [(-0.10, 0.44), (0.40, 0.44)]), fill=p['aksen'], width=lw)


def ik_gulungan(d, cx, cy, s, p):
    lw, ink = p['lw'], p['ink']
    d.rectangle(_r(cx, cy, s, -0.30, -0.30, 0.30, 0.30), fill=p['fill2'], outline=ink, width=lw)
    for y in (-0.30, 0.30):
        d.rounded_rectangle(_r(cx, cy, s, -0.40, y - 0.07, 0.40, y + 0.07), radius=int(s * 0.07), fill=p['aksen'], outline=ink, width=lw)
    for y in (-0.12, 0.0, 0.12):
        d.line(_p(cx, cy, s, [(-0.20, y), (0.20, y)]), fill=ink, width=max(3, lw // 2))


def ik_timbangan(d, cx, cy, s, p):
    lw, ink = p['lw'], p['ink']
    d.line(_p(cx, cy, s, [(0, -0.40), (0, 0.36)]), fill=ink, width=lw)
    d.line(_p(cx, cy, s, [(-0.40, -0.26), (0.40, -0.26)]), fill=ink, width=lw)
    d.rectangle(_r(cx, cy, s, -0.18, 0.36, 0.18, 0.44), fill=p['fill'], outline=ink, width=lw)
    for x in (-0.40, 0.40):
        d.line(_p(cx, cy, s, [(x, -0.26), (x - 0.14, 0.06)]), fill=ink, width=4)
        d.line(_p(cx, cy, s, [(x, -0.26), (x + 0.14, 0.06)]), fill=ink, width=4)
        d.chord(_r(cx, cy, s, x - 0.16, -0.06, x + 0.16, 0.18), 0, 180, fill=p['aksen'], outline=ink, width=lw)


def ik_hati(d, cx, cy, s, p):
    lw, ink = p['lw'], p['ink']
    d.ellipse(_r(cx, cy, s, -0.40, -0.32, 0.02, 0.10), fill=p['fill'])
    d.ellipse(_r(cx, cy, s, -0.02, -0.32, 0.40, 0.10), fill=p['fill'])
    d.polygon(_p(cx, cy, s, [(-0.385, -0.03), (0.385, -0.03), (0, 0.42)]), fill=p['fill'])
    d.arc(_r(cx, cy, s, -0.40, -0.32, 0.02, 0.10), 140, 360, fill=ink, width=lw)
    d.arc(_r(cx, cy, s, -0.02, -0.32, 0.40, 0.10), 180, 40, fill=ink, width=lw)
    d.line(_p(cx, cy, s, [(-0.385, -0.03), (0, 0.42), (0.385, -0.03)]), fill=ink, width=lw, joint='curve')
    d.arc(_r(cx, cy, s, -0.30, -0.24, -0.08, -0.02), 190, 260, fill=(255, 255, 255), width=6)


def ik_rumah(d, cx, cy, s, p):
    lw, ink = p['lw'], p['ink']
    d.polygon(_p(cx, cy, s, [(-0.46, -0.02), (0, -0.42), (0.46, -0.02)]), fill=p['fill'], outline=ink, width=lw)
    d.rectangle(_r(cx, cy, s, -0.36, -0.02, 0.36, 0.42), fill=p['fill2'], outline=ink, width=lw)
    d.rectangle(_r(cx, cy, s, -0.10, 0.14, 0.10, 0.42), fill=p['aksen'], outline=ink, width=lw)
    d.rectangle(_r(cx, cy, s, 0.16, 0.06, 0.30, 0.20), fill=(246, 214, 140), outline=ink, width=max(3, lw // 2))


def ik_pintu(d, cx, cy, s, p):
    lw, ink = p['lw'], p['ink']
    d.pieslice(_r(cx, cy, s, -0.30, -0.46, 0.30, 0.14), 180, 360, fill=p['aksen'], outline=ink, width=lw)
    d.rectangle(_r(cx, cy, s, -0.30, -0.16, 0.30, 0.44), fill=p['aksen'], outline=ink, width=lw)
    d.line(_p(cx, cy, s, [(0, -0.40), (0, 0.44)]), fill=ink, width=max(3, lw // 2))
    for x in (-0.06, 0.06):
        d.ellipse(_r(cx, cy, s, x - 0.03, 0.08, x + 0.03, 0.14), fill=p['fill'])


def ik_jejak(d, cx, cy, s, p):
    for i, (x, y) in enumerate(((-0.20, 0.34), (0.10, 0.10), (-0.14, -0.14), (0.16, -0.38))):
        d.ellipse(_r(cx, cy, s, x - 0.08, y - 0.12, x + 0.08, y + 0.08), fill=p['ink'])
        d.ellipse(_r(cx, cy, s, x - 0.06, y + 0.10, x + 0.06, y + 0.18), fill=p['ink'])


def ik_sumur(d, cx, cy, s, p):
    lw, ink = p['lw'], p['ink']
    d.rectangle(_r(cx, cy, s, -0.36, 0.0, 0.36, 0.40), fill=(176, 150, 120), outline=ink, width=lw)
    for y in (0.13, 0.26):
        d.line(_p(cx, cy, s, [(-0.36, y), (0.36, y)]), fill=ink, width=3)
    d.ellipse(_r(cx, cy, s, -0.36, -0.08, 0.36, 0.08), fill=p['air'], outline=ink, width=lw)
    for x in (-0.30, 0.30):
        d.line(_p(cx, cy, s, [(x, 0.0), (x, -0.42)]), fill=ink, width=lw)
    d.line(_p(cx, cy, s, [(-0.36, -0.42), (0.36, -0.42)]), fill=ink, width=lw)
    d.line(_p(cx, cy, s, [(0, -0.42), (0, -0.16)]), fill=ink, width=4)
    d.rectangle(_r(cx, cy, s, -0.07, -0.18, 0.07, -0.04), fill=p['fill'], outline=ink, width=3)


def ik_roti(d, cx, cy, s, p):
    lw, ink = p['lw'], p['ink']
    d.ellipse(_r(cx, cy, s, -0.44, -0.20, 0.44, 0.30), fill=(214, 170, 112), outline=ink, width=lw)
    for x in (-0.20, 0.0, 0.20):
        d.arc(_r(cx, cy, s, x - 0.08, -0.10, x + 0.08, 0.10), 200, 340, fill=(250, 226, 180), width=6)


def ik_koin(d, cx, cy, s, p):
    lw, ink = p['lw'], p['ink']
    for dx, dy in ((-0.14, 0.12), (0.12, -0.08)):
        d.ellipse(_r(cx, cy, s, dx - 0.26, dy - 0.26, dx + 0.26, dy + 0.26), fill=(236, 196, 120), outline=ink, width=lw)
        d.ellipse(_r(cx, cy, s, dx - 0.16, dy - 0.16, dx + 0.16, dy + 0.16), outline=(200, 150, 70), width=6)


def ik_kunci(d, cx, cy, s, p):
    lw, ink = p['lw'], p['ink']
    d.ellipse(_r(cx, cy, s, -0.44, -0.20, -0.04, 0.20), fill=p['aksen'], outline=ink, width=lw)
    d.ellipse(_r(cx, cy, s, -0.30, -0.06, -0.18, 0.06), fill=p['bg'])
    d.rectangle(_r(cx, cy, s, -0.06, -0.05, 0.44, 0.05), fill=p['aksen'], outline=ink, width=lw)
    for x in (0.24, 0.36):
        d.rectangle(_r(cx, cy, s, x, 0.05, x + 0.06, 0.18), fill=p['aksen'], outline=ink, width=4)


def ik_bintang(d, cx, cy, s, p):
    for x, y, r in ((0, 0, 0.30), (0.30, -0.28, 0.12), (-0.30, 0.26, 0.10)):
        pts = []
        for i in range(8):
            a = -math.pi / 2 + i * math.pi / 4
            rr = r if i % 2 == 0 else r * 0.32
            pts.append((x + rr * math.cos(a), y + rr * math.sin(a)))
        d.polygon(_p(cx, cy, s, pts), fill=(246, 214, 140), outline=p['ink'])


def ik_siwak(d, cx, cy, s, p):
    lw, ink = p['lw'], p['ink']
    d.polygon(_p(cx, cy, s, [(0.34, -0.42), (0.42, -0.34), (-0.30, 0.38), (-0.38, 0.30)]), fill=(180, 140, 100), outline=ink, width=lw)
    for i in range(5):
        d.line(_p(cx, cy, s, [(0.38, -0.38), (0.44 + i * 0.012, -0.50 + i * 0.03)]), fill=(240, 226, 200), width=4)


def ik_parfum(d, cx, cy, s, p):
    lw, ink = p['lw'], p['ink']
    d.rectangle(_r(cx, cy, s, -0.06, -0.44, 0.06, -0.30), fill=p['aksen'], outline=ink, width=lw)
    d.ellipse(_r(cx, cy, s, -0.30, -0.30, 0.30, 0.40), fill=p['fill2'], outline=ink, width=lw)
    d.ellipse(_r(cx, cy, s, -0.20, -0.04, 0.20, 0.30), fill=p['fill'])
    for x, y in ((0.30, -0.40), (0.40, -0.30), (0.36, -0.48)):
        d.ellipse(_r(cx, cy, s, x - 0.025, y - 0.025, x + 0.025, y + 0.025), fill=p['aksen'])


def ik_piring(d, cx, cy, s, p):
    lw, ink = p['lw'], p['ink']
    d.ellipse(_r(cx, cy, s, -0.40, -0.26, 0.40, 0.30), fill=p['fill2'], outline=ink, width=lw)
    d.ellipse(_r(cx, cy, s, -0.24, -0.14, 0.24, 0.18), outline=p['aksen'], width=6)
    d.line(_p(cx, cy, s, [(-0.52, -0.30), (-0.52, 0.34)]), fill=ink, width=lw)
    d.line(_p(cx, cy, s, [(0.52, -0.30), (0.52, 0.34)]), fill=ink, width=lw)
    d.ellipse(_r(cx, cy, s, 0.47, -0.34, 0.57, -0.16), fill=ink)


def ik_cahaya(d, cx, cy, s, p):
    d.ellipse(_r(cx, cy, s, -0.16, -0.16, 0.16, 0.16), fill=(250, 226, 160))
    for i in range(8):
        a = math.radians(i * 45)
        d.line([(cx + math.cos(a) * s * 0.24, cy + math.sin(a) * s * 0.24),
                (cx + math.cos(a) * s * (0.44 if i % 2 == 0 else 0.34), cy + math.sin(a) * s * (0.44 if i % 2 == 0 else 0.34))],
               fill=(246, 196, 104), width=p['lw'])


IKON = {
    'masjid': ik_masjid, 'kabah': ik_kabah, 'kitab': ik_kitab, 'quran': ik_quran, 'lentera': ik_lentera,
    'bulan_bintang': ik_bulan_bintang, 'pohon_kurma': ik_pohon_kurma, 'kurma': ik_kurma, 'tenda': ik_tenda,
    'gua': ik_gua, 'gunung': ik_gunung, 'matahari': ik_matahari, 'awan_hujan': ik_awan_hujan,
    'tetes_air': ik_tetes_air, 'gelas': ik_gelas, 'jam': ik_jam, 'kalender': ik_kalender, 'tasbih': ik_tasbih,
    'sajadah': ik_sajadah, 'pena': ik_pena, 'gulungan': ik_gulungan, 'timbangan': ik_timbangan, 'hati': ik_hati,
    'rumah': ik_rumah, 'pintu': ik_pintu, 'jejak': ik_jejak, 'sumur': ik_sumur, 'roti': ik_roti, 'koin': ik_koin,
    'kunci': ik_kunci, 'bintang': ik_bintang, 'siwak': ik_siwak, 'parfum': ik_parfum, 'piring': ik_piring,
    'cahaya': ik_cahaya,
}
DAFTAR_IKON = ', '.join(IKON)


# ------------------------------------------------------------------ latar & efek
_BUTIR = None


def kapur(layer):
    global _BUTIR
    if _BUTIR is None:
        random.seed(5)
        n = Image.effect_noise((W, H), 70).filter(ImageFilter.GaussianBlur(0.6))
        _BUTIR = n.point(lambda v: 255 if v > 120 else int(v * 1.6))
    a = layer.split()[3]
    layer.putalpha(ImageChops.multiply(a, _BUTIR.crop((0, 0, layer.width, layer.height))))
    return layer.filter(ImageFilter.GaussianBlur(0.6))


def latar(gv, p):
    if gv == 'papan':
        bg = Image.new('RGB', (W, H), p['bg'])
        noda = Image.new('L', (W, H), 0)
        nd = ImageDraw.Draw(noda)
        random.seed(7)
        for _ in range(14):
            x, y, r = random.randint(0, W), random.randint(0, H), random.randint(160, 420)
            nd.ellipse([x - r, y - r, x + r, y + r], fill=random.randint(40, 90))
        bg = Image.composite(Image.new('RGB', (W, H), p['bg2']), bg, noda.filter(ImageFilter.GaussianBlur(110)))
        t = Image.effect_noise((W, H), 12).convert('RGB')
        bg = ImageChops.add(bg, ImageChops.subtract(t, Image.new('RGB', (W, H), (128, 128, 128))), 1, 0)
        ImageDraw.Draw(bg).rectangle([18, 18, W - 19, H - 19], outline=p['garis'], width=6)
        return bg.convert('RGBA')
    bg = Image.new('RGBA', (W, H), p['bg'] + (255,))
    d = ImageDraw.Draw(bg)
    if gv == 'flat':
        for x, y, r in ((960, 330, 250), (90, 1560, 290), (980, 1720, 150), (120, 470, 90)):
            d.ellipse([x - r, y - r, x + r, y + r], fill=p['bg2'] + (255,))
        return bg
    for x in range(0, W, 54):
        d.line([(x, 0), (x, H)], fill=p['garis'] + (255,), width=2)
    for y in range(0, H, 54):
        d.line([(0, y), (W, y)], fill=p['garis'] + (255,), width=2)
    d.line([(56, 0), (56, H)], fill=p['sorot'] + (255,), width=4)
    return bg


def _ease_back(t):
    t = min(max(t, 0.0), 1.0)
    return 1 + 2.70158 * (t - 1) ** 3 + 1.70158 * (t - 1) ** 2


def _ease(t):
    t = min(max(t, 0.0), 1.0)
    return 1 - (1 - t) ** 3


def _alpha(lay, a):
    if a >= 0.999:
        return lay
    l = lay.copy()
    l.putalpha(l.split()[3].point(lambda v: int(v * a)))
    return l


def _wipe(lay, pr):
    if pr >= 0.999:
        return lay
    m = Image.new('L', lay.size, 0)
    ImageDraw.Draw(m).rectangle([0, 0, int(lay.width * pr), lay.height], fill=255)
    l = lay.copy()
    l.putalpha(ImageChops.multiply(l.split()[3], m))
    return l


# ------------------------------------------------------------------ lapisan
def lapisan_ikon(nama, gv, p, size=520, tinggi=720):
    lay = Image.new('RGBA', (W, tinggi), (0, 0, 0, 0))
    d = ImageDraw.Draw(lay)
    nama = [n for n in (nama or []) if n in IKON][:2] or ['kitab']
    if gv == 'flat':
        b = Image.new('RGBA', lay.size, (0, 0, 0, 0))
        ImageDraw.Draw(b).ellipse([W / 2 - 300, tinggi - 110, W / 2 + 300, tinggi - 40], fill=(63, 90, 69, 50))
        lay.alpha_composite(b.filter(ImageFilter.GaussianBlur(18)))
    if len(nama) == 1:
        IKON[nama[0]](d, W / 2, tinggi / 2 - 20, size, p)
    else:
        s2 = int(size * 0.72)
        IKON[nama[0]](d, W / 2 - 220, tinggi / 2, s2, p)
        IKON[nama[1]](d, W / 2 + 220, tinggi / 2, s2, p)
    return kapur(lay) if p['kapur'] else lay


def lapisan_atas(kicker, judul, gv, p, besar):
    """Kicker pil + judul (besar = pembuka, kecil = pengingat di babak lain)."""
    lay = Image.new('RGBA', (W, 620), (0, 0, 0, 0))
    d = ImageDraw.Draw(lay)
    fk = gaya.font('isi-tebal', 32)
    kw = fk.getlength(kicker) + 56
    d.rounded_rectangle([(W - kw) / 2, 20, (W + kw) / 2, 80], radius=30, fill=p['sorot'])
    d.text((W / 2, 50), kicker, font=fk, fill=p['di_sorot'], anchor='mm')
    if judul:
        if besar:
            f = judul_pas(judul, 'judul', 112, 72, 3)
            y = tengah(d, 120, judul, f, p['teks'], spasi=1.12)
            d.line([(W / 2 - 110, y + 24), (W / 2 + 110, y + 24)], fill=p['aksen'], width=8)
        else:
            f = judul_pas(judul, 'judul', 52, 38, 2)
            tengah(d, 110, judul, f, p['sub'], spasi=1.15)
    return kapur(lay) if p['kapur'] and besar else lay


def lapisan_label(teks, p):
    lay = Image.new('RGBA', (W, 120), (0, 0, 0, 0))
    if not teks:
        return lay
    d = ImageDraw.Draw(lay)
    f = judul_pas(teks.upper(), 'isi-tebal', 46, 34, 1, maks=W - 260)
    tw = lebar(teks.upper(), f)
    d.rounded_rectangle([(W - tw) / 2 - 34, 14, (W + tw) / 2 + 34, 104], radius=45, fill=p['kartu'] + (255,),
                        outline=p['aksen'], width=4)
    tulis(d, (W - tw) / 2, 34, teks.upper(), f, p['teks'])
    return lay


def caption(d, grup, t, p, y=1430):
    """Caption karaoke: 1-3 kata, kata aktif disorot (gaya video Sunnah Daily)."""
    for m, s, kata, wk in grup:
        if not (m <= t < s or (grup[-1][0] == m and t >= m)):
            continue
        f = gaya.font('isi-tebal', 64)
        sp = 18
        lk = [lebar(k, f) for k in kata]
        x = (W - sum(lk) - sp * (len(kata) - 1)) / 2
        for k, l, (km, ks) in zip(kata, lk, wk):
            if km <= t < ks + 0.05:
                d.rounded_rectangle([x - 14, y - 6, x + l + 14, y + 80], 44, fill=p['sorot'])
                tulis(d, x, y, k, f, p['di_sorot'])
            else:
                tulis(d, x, y, k, f, p['teks'])
            x += l + sp
        break


def lapisan_dalil(dl, p, tema):
    """Kartu dalil: label derajat, teks Arab (RTL), terjemah, sumber. Hadits lemah diberi peringatan."""
    c = gaya.warna(tema)
    lay = Image.new('RGBA', (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(lay)
    x0, x1 = 72, W - 72
    isi_w = x1 - x0 - 96
    judul_kartu = {'ulama': 'Nasihat Ulama', 'atsar': 'Atsar', 'ayat': "Firman Allah Ta'ala"}.get(dl.get('jenis'), 'Dalilnya')
    derajat = (dl.get('derajat') or '').lower()
    label = None
    if dl.get('jenis') in ('hadits', 'atsar') and derajat:
        label = {'shahih': ('✓  SHAHIH', c['sage-muda'], c['tinta']), 'hasan': ('✓  HASAN', c['gading-2'], c['tinta']),
                 'lemah': ('!  HADITS LEMAH' if dl.get('jenis') == 'hadits' else '!  LEMAH', c['terakota-tua'], c['di-terakota']),
                 'palsu': ('×  PALSU', c['palsu'], c['gading'])}.get(derajat, ('✓  SHAHIH', c['sage-muda'], c['tinta']))
    arab = (dl.get('arab') or '').strip().replace(',', '،').replace(';', '؛').replace('?', '؟').rstrip('.').replace('.', '')
    terj, sumber = (dl.get('terjemah') or '').strip(), (dl.get('sumber') or '').strip()
    bagian = []
    if arab:
        for s in range(64, 40, -4):
            fa = gaya.font('arab', s)
            ba = video.Bingkai._bungkus_arab(arab, fa, isi_w)
            if len(ba) <= 5:
                break
        bagian.append(('arab', fa, ba))
    for s in range(40, 30, -2):
        ft = gaya.font('isi', s)
        bt = bungkus(f'"{terj}"', ft, isi_w)
        if len(bt) <= 8:
            break
    bagian.append(('terj', ft, bt))
    fs = gaya.font('isi-sedang', 30)
    bagian.append(('sumber', fs, bungkus(sumber, fs, isi_w)))
    tinggi = 96 + sum(len(bs) * f.size * (1.75 if j == 'arab' else 1.4) + 32 for j, f, bs in bagian)
    ky = int(max(460, (gaya.AMAN_ATAS + 160 + H - gaya.AMAN_BAWAH - tinggi) / 2))
    tulis(d, x0 + 8, ky - 120, judul_kartu, gaya.font('judul', 64), p['teks'])
    if label:
        fl = gaya.font('isi-tebal', 30)
        lw = fl.getlength(label[0]) + 44
        d.rounded_rectangle([x1 - lw, ky - 108, x1, ky - 48], 14, fill=label[1])
        d.text((x1 - lw + 22, ky - 78), label[0], font=fl, fill=label[2], anchor='lm')
    kartu = (255, 252, 246) if p['kapur'] is False and tema == 'siang' else p['kartu']
    d.rounded_rectangle([x0, ky, x1, ky + tinggi], 28, fill=kartu + (245,), outline=p['aksen'], width=4)
    warna_isi = p['teks'] if p['kapur'] or tema == 'malam' else c['tinta']
    y = ky + 48
    for j, f, bs in bagian:
        for b in bs:
            if j == 'arab':
                d.text((x1 - 48, y + f.size * 1.1), b, font=f, fill=warna_isi, anchor='rs', direction='rtl', language='ar')
                y += f.size * 1.75
            else:
                tulis(d, x0 + 48, y, b, f, warna_isi if j == 'terj' else p['sub'])
                y += f.size * 1.4
        y += 32
    if derajat == 'lemah':
        tengah(d, ky + tinggi + 40, ('Hadits' if dl.get('jenis') == 'hadits' else 'Riwayat') +
               ' ini lemah. Disebutkan sebagai penjelasan, bukan dalil.', gaya.font('isi-sedang', 30), p['sorot'])
    return lay


def lapisan_faedah(seg, gv, p):
    lay = Image.new('RGBA', (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(lay)
    f = gaya.font('judul', 72)
    tulis(d, (W - lebar('Faedah', f)) / 2, 300, 'Faedah', f, p['aksen'])
    lay.alpha_composite(lapisan_ikon(seg.get('ikon') or ['hati'], gv, p, 420, 560), (0, 420))
    teks = seg.get('faedah') or seg.get('judul') or ''
    ff = judul_pas(teks, 'isi-tebal', 58, 40, 4)
    tengah(d, 1040, teks, ff, p['teks'], spasi=1.28)
    return lay


def lapisan_penutup(seg, p, tema):
    lay = Image.new('RGBA', (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(lay)
    lg = video.logo(360, tema)
    if p['kapur']:
        d.ellipse([(W - 420) / 2, 300, (W + 420) / 2, 720], fill=gaya.warna('siang')['gading'] + (255,))
        lg = video.logo(360, 'siang')
    lay.alpha_composite(lg, ((W - 360) // 2, 330))
    fj = gaya.font('judul', 104)
    tulis(d, (W - lebar('Sunnah Daily', fj)) / 2, 770, 'Sunnah Daily', fj, p['teks'])
    y = 930
    if seg.get('seri'):
        fs = gaya.font('isi-sedang', 36)
        y = tengah(d, y, seg['seri'], fs, p['sub'], spasi=1.3) + 10
    ajak = seg.get('ajakan') or 'Ikuti untuk sunnah berikutnya'
    fa = judul_pas(ajak, 'isi-tebal', 42, 32, 2, maks=W - 260)
    baris = bungkus(ajak, fa, W - 260)[:2]
    lw = max(lebar(b, fa) for b in baris) + 90
    tinggi = 44 + len(baris) * fa.size * 1.25
    d.rounded_rectangle([(W - lw) / 2, y + 20, (W + lw) / 2, y + 20 + tinggi], 46, fill=p['sorot'])
    yy = y + 42
    for b in baris:
        tulis(d, (W - lebar(b, fa)) / 2, yy, b, fa, p['di_sorot'])
        yy += fa.size * 1.25
    y += tinggi - 92
    y += 170
    fk = gaya.font('isi-sedang', 30)
    for b in (seg.get('kredit') or '').split('\n'):
        if b.strip():
            y = tengah(d, y, b, fk, p['sub'], spasi=1.4)
    return lay


def lapisan_handle(p):
    lay = Image.new('RGBA', (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(lay)
    fh = gaya.font('isi-tebal', 30)
    d.text((W - 60, 150), HANDLE, font=fh, fill=p['sub'], anchor='ra')
    return lay


# ------------------------------------------------------------------ susun video
def buat_video(segmen, tema, out_mp4, contoh_jpg=None, gaya_v=None):
    gv = gaya_v if gaya_v in URUTAN_GAYA else os.environ.get('GAYA_IKON', '') or 'flat'
    if gv not in URUTAN_GAYA:
        gv = 'flat'
    p = palet(gv, tema)
    bg = latar(gv, p)
    handle = lapisan_handle(p)
    with tempfile.TemporaryDirectory() as tmp:
        wav = os.path.join(tmp, 'suara.wav')
        total = susun_audio(segmen, wav, tmp)
        judul = next((s.get('judul') for s in segmen if s['jenis'] == 'hook'), '')
        poin = [s for s in segmen if s['jenis'] == 'poin']
        pra = []
        for s in segmen:
            kicker = s.get('kicker') or 'SUNNAH DAILY'
            j = s['jenis']
            if j == 'hook':
                pra.append(dict(atas=lapisan_atas(kicker, s.get('judul'), gv, p, True),
                                ikon=lapisan_ikon(s.get('ikon'), gv, p, 560)))
            elif j == 'poin':
                k = poin.index(s)
                pra.append(dict(atas=lapisan_atas(f'{kicker} · {k + 1}/{len(poin)}', judul, gv, p, False),
                                ikon=lapisan_ikon(s.get('ikon'), gv, p, 500), label=lapisan_label(s.get('label'), p),
                                grup=kelompok_kata(s.get('narasi', ''), s['durasi'])))
            elif j == 'dalil':
                pra.append(dict(lay=lapisan_dalil(s['dalil'], p, tema)))
            elif j == 'faedah':
                pra.append(dict(lay=lapisan_faedah(s, gv, p)))
            else:
                pra.append(dict(lay=lapisan_penutup(s, p, tema)))
        proc = subprocess.Popen([
            FFMPEG, '-y', '-loglevel', 'error', '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-s', f'{W}x{H}',
            '-r', str(FPS), '-i', '-', '-i', wav, '-c:v', 'libx264', '-preset', 'veryfast', '-crf', '21',
            '-pix_fmt', 'yuv420p', '-c:a', 'aac', '-b:a', '160k', '-shortest', '-movflags', '+faststart',
            out_mp4], stdin=subprocess.PIPE)
        idx, contoh = 0, []
        for fr in range(int(total * FPS)):
            t = fr / FPS
            while idx + 1 < len(segmen) and t >= segmen[idx + 1]['mulai']:
                idx += 1
            s, b = segmen[idx], pra[idx]
            lt = t - s['mulai']
            pin = _ease(lt / 0.35)
            img = bg.copy()
            d = ImageDraw.Draw(img)
            if s['jenis'] == 'hook':
                img.alpha_composite(_alpha(b['atas'], pin), (0, gaya.AMAN_ATAS + 10 - int(30 * (1 - pin))))
                ik = _wipe(b['ikon'], lt / 0.8) if p['kapur'] else b['ikon']
                sk = 1 if p['kapur'] else 0.55 + 0.45 * _ease_back(lt / 0.55)
                if abs(sk - 1) > 0.01:
                    ik = ik.resize((int(W * sk), int(ik.height * sk)), Image.BILINEAR)
                img.alpha_composite(ik, ((W - ik.width) // 2, 820 + (720 - ik.height) // 2 + int(12 * math.sin(t * 2.3))))
            elif s['jenis'] == 'poin':
                img.alpha_composite(b['atas'], (0, gaya.AMAN_ATAS + 10))
                if p['kapur']:
                    ik = _wipe(b['ikon'], lt / 0.7)
                else:
                    sk = 0.6 + 0.4 * _ease_back(lt / 0.5)
                    ik = b['ikon'] if abs(sk - 1) < 0.01 else b['ikon'].resize((int(W * sk), int(720 * sk)), Image.BILINEAR)
                img.alpha_composite(_alpha(ik, min(1, lt / 0.2)),
                                    ((W - ik.width) // 2, 430 + (720 - ik.height) // 2 + int(10 * math.sin(t * 2.2))))
                pl = _ease((lt - 0.2) / 0.35)
                if pl > 0:
                    img.alpha_composite(_alpha(b['label'], pl), (0, 1170 + int(20 * (1 - pl))))
                d = ImageDraw.Draw(img)
                caption(d, b['grup'], lt, p)
                k, m = poin.index(s), len(poin)
                for j in range(m):
                    x = W / 2 + (j - (m - 1) / 2) * 40
                    r = 12 if j == k else 8
                    d.ellipse([x - r, 1580 - r, x + r, 1580 + r], fill=p['sorot'] if j == k else p['sub'])
            else:
                img.alpha_composite(_alpha(b['lay'], pin), (0, int(-40 * (1 - pin))))
            if s['jenis'] != 'penutup':
                img.alpha_composite(handle)
            d = ImageDraw.Draw(img)
            d.rectangle([0, 0, int(W * t / total), 10], fill=p['sorot'])
            rgb = img.convert('RGB')
            if contoh_jpg and abs(lt - min(1.5, s['durasi'] / 2)) < 0.5 / FPS:
                contoh.append(rgb.resize((W // 3, H // 3)))
            proc.stdin.write(rgb.tobytes())
        proc.stdin.close()
        if proc.wait() != 0:
            raise RuntimeError('ffmpeg gagal')
        if contoh_jpg and contoh:
            lembar = Image.new('RGB', (W // 3 * len(contoh), H // 3), 'white')
            for i, im in enumerate(contoh):
                lembar.paste(im, (i * W // 3, 0))
            lembar.save(contoh_jpg, quality=85)
        return total
