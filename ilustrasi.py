"""Pustaka latar ilustrasi datar (flat) Sunnah Daily.

Aturan brand: hanya bidang warna token, tanpa gradien/bayangan, TIDAK menggambar Nabi, nabi lain, sahabat,
istri Nabi maupun malaikat (termasuk siluet). Kisah dihadirkan lewat latar dan benda.

Setiap latar = beberapa lapisan statis (digeser pelan = paralaks) + unsur bergerak (bintang berkedip,
cahaya lentera berdenyut, kafilah unta berjalan, ombak). Lapisan digambar 2x lalu diperkecil (anti-alias).
"""
import math
import random

from PIL import Image, ImageDraw

import gaya

SW, SH = gaya.W, 1300          # area ilustrasi (atas); sisanya untuk teks
EXTRA = 160                    # lebar tambahan untuk paralaks
K = 2                          # supersampling

LATAR = {
    'gurun': 'padang pasir terbuka, bukit pasir',
    'kafilah': 'kafilah unta berjalan di padang pasir (perjalanan, dagang, hijrah)',
    'kabah': "Ka'bah dan Masjidil Haram (Makkah, thawaf, haji, umrah)",
    'masjid': 'masjid berkubah dan menara (Madinah, shalat, masjid Quba/Nabawi)',
    'gua': 'gunung batu dengan mulut gua (Gua Hira, Gua Tsur, wahyu, bersembunyi)',
    'kota': 'kota tua: rumah-rumah beratap datar dan pohon kurma (Makkah/Madinah, kehidupan sehari-hari)',
    'kebun': 'kebun kurma (Madinah, Anshar, sedekah, pertanian)',
    'tenda': 'perkemahan tenda di padang pasir (pasukan, perjalanan, Badui)',
    'lentera': 'lentera menggantung yang menyala (malam, ibadah, ilmu, renungan)',
    'kitab': 'kitab terbuka bercahaya (ilmu, Al-Qur\'an, wahyu, dalil, pelajaran)',
    'laut': 'laut dan perahu layar (hijrah ke Habasyah, perjalanan laut)',
    'langit': 'langit malam penuh bintang dan bulan sabit (Isra Mi\'raj, malam, doa)',
}


def _baru(w, h):
    im = Image.new('RGBA', (w * K, h * K), (0, 0, 0, 0))
    return im, ImageDraw.Draw(im)


def _kecil(im):
    return im.resize((im.width // K, im.height // K), Image.LANCZOS)


def _poly(d, pts, c):
    d.polygon([(x * K, y * K) for x, y in pts], fill=c)


def _elips(d, cx, cy, rx, ry, c):
    d.ellipse([(cx - rx) * K, (cy - ry) * K, (cx + rx) * K, (cy + ry) * K], fill=c)


def _kotak(d, x0, y0, x1, y1, c, r=0):
    if r:
        d.rounded_rectangle([x0 * K, y0 * K, x1 * K, y1 * K], r * K, fill=c)
    else:
        d.rectangle([x0 * K, y0 * K, x1 * K, y1 * K], fill=c)


def _bukit(d, w, y, amp, per, fase, c, h=SH):
    pts = [(0, h)]
    for x in range(0, w + 21, 20):
        pts.append((x, y + amp * math.sin((x / per) * 2 * math.pi + fase)))
    pts.append((w, h))
    _poly(d, pts, c)


def _sabit(d, cx, cy, r, c, latar):
    _elips(d, cx, cy, r, r, c)
    _elips(d, cx + r * 0.42, cy - r * 0.22, r * 0.82, r * 0.82, latar)


def _bintang5(d, cx, cy, R, c):
    pts = []
    for i in range(10):
        a = -math.pi / 2 + i * math.pi / 5
        rr = R if i % 2 == 0 else R * 0.42
        pts.append((cx + rr * math.cos(a), cy + rr * math.sin(a)))
    _poly(d, pts, c)


def _unta(d, x, y, s, c):
    """Siluet unta datar sederhana, menghadap kanan. (x,y)=kaki kiri bawah, s=skala."""
    _elips(d, x + 60 * s, y - 95 * s, 62 * s, 32 * s, c)            # badan
    _elips(d, x + 50 * s, y - 122 * s, 30 * s, 28 * s, c)           # punuk
    _poly(d, [(x + 105 * s, y - 110 * s), (x + 125 * s, y - 175 * s), (x + 140 * s, y - 172 * s),
              (x + 128 * s, y - 95 * s)], c)                         # leher
    _elips(d, x + 145 * s, y - 175 * s, 18 * s, 11 * s, c)          # kepala
    for lx in (12, 30, 88, 106):
        _kotak(d, x + lx * s, y - 80 * s, x + (lx + 9) * s, y, c)     # kaki


def _rumah(d, x, y, w, h, c, jendela):
    _kotak(d, x, y - h, x + w, y, c)
    _kotak(d, x + w * 0.3, y - h * 0.62, x + w * 0.46, y - h * 0.38, jendela, 4)


def _kurma(d, x, y, t, batang, daun):
    _poly(d, [(x - 7, y), (x + 7, y), (x + 4, y - t), (x - 4, y - t)], batang)
    for a in range(0, 360, 45):
        r = math.radians(a)
        ex, ey = x + 70 * math.cos(r), y - t + 26 * math.sin(r) + (18 if 20 < a < 160 else 0)
        _poly(d, [(x, y - t - 6), (ex, ey), (x, y - t + 8)], daun)


class Adegan:
    """Lapisan statis + fungsi gerak. render(t) -> Image RGB SWxSH."""

    def __init__(self, tema, latar_warna):
        self.c = gaya.warna(tema)
        self.tema = tema
        self.dasar = Image.new('RGB', (SW + EXTRA, SH), latar_warna)
        self.lapis = []          # (RGBA, px per detik)
        self.gerak = []          # fungsi(img, t)

    def tambah(self, im, laju=0.0):
        self.lapis.append((_kecil(im), laju))

    def render(self, t):
        out = self.dasar.copy()
        for im, laju in self.lapis:
            dx = int(-min(EXTRA, laju * t))
            out.alpha_composite(im, (dx, 0)) if out.mode == 'RGBA' else out.paste(im, (dx, 0), im)
        out = out.crop((0, 0, SW, SH))
        for g in self.gerak:
            g(out, t)
        return out


def _langit_bintang(a, n=40, seed=1, y_maks=700):
    rnd = random.Random(seed)
    pos = [(rnd.randint(20, SW - 20), rnd.randint(260, y_maks), rnd.uniform(2, 5), rnd.uniform(0, 6.28))
           for _ in range(n)]
    c = a.c['terakota']
    base = a.c['langit']

    def g(img, t):
        d = ImageDraw.Draw(img)
        for x, y, r, f in pos:
            k = 0.55 + 0.45 * math.sin(t * 1.3 + f)
            col = tuple(int(base[i] + (c[i] - base[i]) * k) for i in range(3))
            d.ellipse([x - r, y - r, x + r, y + r], fill=col)
    a.gerak.append(g)


def _benda_langit(a, x=780, y=420):
    """Matahari (siang) atau bulan sabit + bintang (malam)."""
    im, d = _baru(SW + EXTRA, SH)
    if a.tema == 'siang':
        _elips(d, x, y, 95, 95, a.c['terakota'])
    else:
        _sabit(d, x, y, 90, a.c['terakota'], a.c['langit'])
        _bintang5(d, x + 70, y - 10, 26, a.c['terakota'])
    a.tambah(im, 3)
    if a.tema == 'malam':
        _langit_bintang(a)


def gurun(tema):
    a = Adegan(tema, gaya.warna(tema)['langit'])
    _benda_langit(a)
    im, d = _baru(SW + EXTRA, SH)
    _bukit(d, SW + EXTRA, 860, 50, 900, 0.5, a.c['persik'])
    a.tambah(im, 6)
    im, d = _baru(SW + EXTRA, SH)
    _bukit(d, SW + EXTRA, 1010, 60, 700, 2.0, a.c['sage-muda'])
    a.tambah(im, 14)
    return a


def kafilah(tema):
    a = gurun(tema)
    c = a.c['sage-tua']
    im, d = _baru(760, 320)
    for i in range(3):
        _unta(d, 520 - i * 230, 300 + (i % 2) * 8, 1.05 - i * 0.08, c)
    sprite = _kecil(im)

    def g(img, t):
        img.paste(sprite, (int(t * 40), 1105 - 300), sprite)
    a.gerak.append(g)
    return a


def kabah(tema):
    a = Adegan(tema, gaya.warna(tema)['langit'])
    _benda_langit(a, 830, 380)
    im, d = _baru(SW + EXTRA, SH)
    for i, x in enumerate(range(-40, SW + EXTRA, 150)):       # serambi berlengkung
        _kotak(d, x, 760, x + 120, 1010, a.c['gading-2'])
        _elips(d, x + 60, 790, 42, 42, a.c['langit'])
        _kotak(d, x + 18, 790, x + 102, 1010, a.c['langit'])
    _kotak(d, -40, 1000, SW + EXTRA, SH, a.c['sage-muda'])
    a.tambah(im, 5)
    im, d = _baru(SW + EXTRA, SH)
    hitam = gaya.rgb('#2E2A24') if tema == 'siang' else gaya.rgb('#0F1310')
    _kotak(d, 360, 690, 720, 1080, hitam, 6)
    _kotak(d, 360, 770, 720, 812, a.c['terakota'])
    _kotak(d, 420, 900, 470, 1080, a.c['terakota'], 4)
    _elips(d, 540, 1150, 360, 46, a.c['gading-2'])
    a.tambah(im, 0)
    return a


def masjid(tema):
    a = Adegan(tema, gaya.warna(tema)['langit'])
    _benda_langit(a, 250, 420)
    im, d = _baru(SW + EXTRA, SH)
    _bukit(d, SW + EXTRA, 1060, 18, 1200, 0, a.c['sage-muda'])
    a.tambah(im, 6)
    im, d = _baru(SW + EXTRA, SH)
    tua, sg, gd = a.c['sage-tua'], a.c['sage'], a.c['gading-2']
    _kotak(d, 300, 840, 820, 1080, gd)
    _elips(d, 560, 840, 170, 170, sg)
    _kotak(d, 380, 840, 740, 860, gd)
    _kotak(d, 556, 600, 564, 680, tua)
    _sabit(d, 560, 590, 18, a.c['terakota'], a.c['langit'])
    _kotak(d, 860, 560, 920, 1080, gd)
    _poly(d, [(850, 560), (930, 560), (890, 480)], sg)
    for x in (370, 470, 650, 750):
        _elips(d, x, 950, 26, 26, a.c['langit'])
        _kotak(d, x - 26, 950, x + 26, 1040, a.c['langit'])
    _kotak(d, 0, 1080, SW + EXTRA, SH, a.c['persik'])
    a.tambah(im, 0)
    return a


def gua(tema):
    a = Adegan(tema, gaya.warna(tema)['langit'])
    _benda_langit(a, 820, 360)
    im, d = _baru(SW + EXTRA, SH)
    _poly(d, [(-40, SH), (180, 640), (380, 520), (560, 470), (760, 600), (980, 720), (SW + EXTRA, 820),
              (SW + EXTRA, SH)], a.c['sage'])
    _poly(d, [(380, 520), (560, 470), (620, 560), (470, 600)], a.c['sage-tua'])
    _elips(d, 520, 830, 90, 120, gaya.rgb('#2E2A24') if tema == 'siang' else gaya.rgb('#0F1310'))
    _kotak(d, 430, 830, 610, 960, gaya.rgb('#2E2A24') if tema == 'siang' else gaya.rgb('#0F1310'))
    _bukit(d, SW + EXTRA, 1090, 25, 800, 1.2, a.c['sage-muda'])
    a.tambah(im, 4)
    return a


def kota(tema):
    a = Adegan(tema, gaya.warna(tema)['langit'])
    _benda_langit(a, 300, 400)
    im, d = _baru(SW + EXTRA, SH)
    _bukit(d, SW + EXTRA, 900, 40, 1000, 1, a.c['sage-muda'])
    a.tambah(im, 5)
    im, d = _baru(SW + EXTRA, SH)
    rnd = random.Random(3)
    x = -30
    while x < SW + EXTRA:
        w = rnd.randint(130, 200)
        h = rnd.randint(170, 290)
        _rumah(d, x, 1100, w, h, rnd.choice([a.c['gading-2'], a.c['persik']]), a.c['sage-tua'])
        x += w + rnd.randint(-10, 20)
    _kurma(d, 180, 1100, 330, a.c['sage-tua'], a.c['sage'])
    _kurma(d, 900, 1100, 380, a.c['sage-tua'], a.c['sage'])
    _kotak(d, 0, 1095, SW + EXTRA, SH, a.c['sage-muda'])
    a.tambah(im, 10)
    return a


def kebun(tema):
    a = Adegan(tema, gaya.warna(tema)['langit'])
    _benda_langit(a, 820, 380)
    im, d = _baru(SW + EXTRA, SH)
    _bukit(d, SW + EXTRA, 980, 30, 900, 0.3, a.c['sage-muda'])
    for x in range(40, SW + EXTRA, 210):
        _kurma(d, x, 1000, 260, a.c['sage'], a.c['sage-muda'] if tema == 'malam' else a.c['sage'])
    a.tambah(im, 5)
    im, d = _baru(SW + EXTRA, SH)
    for x in range(120, SW + EXTRA, 300):
        _kurma(d, x, 1150, 420, a.c['sage-tua'], a.c['sage-tua'])
        for k in range(5):
            _elips(d, x - 20 + k * 10, 1150 - 420 + 30 + (k % 2) * 8, 9, 9, a.c['terakota'])
    _kotak(d, 0, 1140, SW + EXTRA, SH, a.c['persik'])
    a.tambah(im, 12)
    return a


def tenda(tema):
    a = gurun(tema)
    im, d = _baru(SW + EXTRA, SH)
    for i, x in enumerate((140, 470, 800)):
        warna_t = [a.c['gading-2'], a.c['terakota'], a.c['sage']][i % 3]
        _poly(d, [(x - 140, 1120), (x, 900), (x + 140, 1120)], warna_t)
        _poly(d, [(x - 30, 1120), (x, 1010), (x + 30, 1120)], a.c['sage-tua'])
    a.tambah(im, 10)
    return a


def lentera(tema):
    a = Adegan(tema, gaya.warna(tema)['langit'])
    if tema == 'malam':
        _langit_bintang(a, 30, 7, 1100)
    c = a.c
    halo = c['persik'] if tema == 'siang' else gaya.rgb('#3A2C26')
    im, dd = _baru(SW, 920)
    _kotak(dd, 537, 220, 543, 560, c['sage-tua'])
    _poly(dd, [(470, 600), (610, 600), (540, 545)], c['sage-tua'])
    _kotak(dd, 470, 600, 610, 880, c['sage-tua'], 18)
    _kotak(dd, 492, 625, 588, 855, c['terakota'], 12)
    _elips(dd, 540, 770, 22, 38, c['gading'])
    _kotak(dd, 460, 880, 620, 905, c['sage-tua'], 8)
    sprite = _kecil(im)

    def g(img, t):
        k = 0.5 + 0.5 * math.sin(t * 2.0)
        r = 230 + 30 * k
        d = ImageDraw.Draw(img)
        d.ellipse([540 - r, 760 - r, 540 + r, 760 + r], fill=halo)
        img.paste(sprite, (0, 0), sprite)
    a.gerak.append(g)
    return a


def kitab(tema):
    a = Adegan(tema, gaya.warna(tema)['langit'])
    if tema == 'malam':
        _langit_bintang(a, 30, 9, 600)
    c = a.c
    im, dd = _baru(SW, 1040)
    _elips(dd, 540, 560, 70, 70, c['terakota'])
    _poly(dd, [(540, 760), (400, 680), (210, 705), (210, 975), (400, 950), (540, 1030)], c['sage'])
    _poly(dd, [(540, 760), (680, 680), (870, 705), (870, 975), (680, 950), (540, 1030)], c['sage-tua'])
    sprite = _kecil(im)

    def g(img, t):
        d = ImageDraw.Draw(img)
        k = 0.5 + 0.5 * math.sin(t * 1.5)
        r = 250 + 25 * k
        d.ellipse([540 - r, 640 - r, 540 + r, 640 + r], fill=c['persik'] if tema == 'siang' else gaya.rgb('#3A2C26'))
        img.paste(sprite, (0, 0), sprite)
    a.gerak.append(g)
    return a


def laut(tema):
    a = Adegan(tema, gaya.warna(tema)['langit'])
    _benda_langit(a, 800, 420)
    c = a.c

    im, d = _baru(320, 340)
    bx, by = 160, 270
    _poly(d, [(bx - 150, by), (bx + 150, by), (bx + 105, by + 60), (bx - 105, by + 60)], c['sage-tua'])
    _kotak(d, bx - 4, by - 260, bx + 4, by, c['sage-tua'])
    _poly(d, [(bx + 8, by - 250), (bx + 8, by - 30), (bx + 140, by - 30)], c['gading-2'])
    _poly(d, [(bx - 8, by - 220), (bx - 8, by - 30), (bx - 110, by - 30)], c['terakota'])
    perahu = _kecil(im)

    def g(img, t):
        x = int(330 + 25 * math.sin(t * 0.6)) - 160
        y = int(930 + 8 * math.sin(t * 1.4)) - 270
        img.paste(perahu, (x, y), perahu)
        d = ImageDraw.Draw(img)
        for j, (yy, col) in enumerate(((985, c['sage']), (1060, c['sage-tua']))):
            f = t * (1.2 + j * 0.5)
            pts = [(0, SH)] + [(x, yy + 14 * math.sin(x / 90 + f)) for x in range(0, SW + 11, 10)] + [(SW, SH)]
            d.polygon(pts, fill=col)
    a.gerak.append(g)
    return a


def langit(tema):
    a = Adegan('malam', gaya.warna('malam')['langit'])
    _langit_bintang(a, 70, 5, 1150)
    im, d = _baru(SW + EXTRA, SH)
    _sabit(d, 540, 560, 150, a.c['terakota'], a.c['langit'])
    _bintang5(d, 650, 540, 40, a.c['terakota'])
    a.tambah(im, 2)
    im, d = _baru(SW + EXTRA, SH)
    _bukit(d, SW + EXTRA, 1130, 30, 900, 0.8, a.c['sage-muda'])
    a.tambah(im, 6)
    return a


PEMBUAT = {'gurun': gurun, 'kafilah': kafilah, 'kabah': kabah, 'masjid': masjid, 'gua': gua, 'kota': kota,
           'kebun': kebun, 'tenda': tenda, 'lentera': lentera, 'kitab': kitab, 'laut': laut, 'langit': langit}


def buat(latar, tema):
    return PEMBUAT.get(latar, gurun)(tema)


if __name__ == '__main__':
    import sys
    tema = sys.argv[1] if len(sys.argv) > 1 else 'siang'
    lembar = Image.new('RGB', (SW * 4 // 3, SH * 3 // 3), 'white')
    for i, k in enumerate(PEMBUAT):
        im = buat(k, tema).render(2.0).resize((SW // 3, SH // 3))
        lembar.paste(im, ((i % 4) * SW // 3, (i // 4) * SH // 3))
    lembar.save(f'/tmp/latar_{tema}.png')
