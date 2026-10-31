"""Siluet makhluk bernyawa yang boleh tampil: polos, datar, TANPA mata dan tanpa wajah.

Tidak pernah dipakai untuk Nabi ﷺ, para nabi, sahabat, istri-istri Nabi, maupun malaikat
(storyboard.py menolak babak "tokoh" untuk mereka).

Babak:
  tokoh    satu tokoh umum (mis. Abdul Muthalib, Abrahah, penduduk Makkah) berdiri, dilihat dari belakang-samping
  pasukan  barisan gajah dan prajurit berjalan; aksi "berlutut" = gajah terdepan bersimpuh
  kawanan  kawanan burung terbang membawa batu kecil yang berjatuhan
"""
import math
import random

from PIL import Image, ImageDraw

W, H = 1080, 1920
TANAH = 1190            # garis tanah (di atas caption)
K = 2                   # supersampling


def rgb(h):
    h = h.lstrip('#')
    return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4))


def ease(x):
    x = max(0.0, min(1.0, x))
    return x * x * (3 - 2 * x)


# ------------------------------------------------------------------ latar panggung
def panggung(latar='gurun'):
    im = Image.new('RGB', (W, H))
    a, b = rgb('#DCE5E6'), rgb('#F5E7D6')
    d = ImageDraw.Draw(im)
    for y in range(H):
        t = min(1, y / TANAH)
        d.line([(0, y), (W, y)], fill=tuple(int(a[i] + (b[i] - a[i]) * t) for i in range(3)))
    for i, (y, c, amp) in enumerate([(930, '#EFD4B6', 40), (1040, '#F2DBC0', 30)]):
        pts = [(0, H)] + [(x, y + amp * math.sin(x / 260 + i * 1.7)) for x in range(0, W + 21, 20)] + [(W, H)]
        d.polygon(pts, fill=rgb(c))
    if latar == 'kabah':
        x, y = 180, 1060
        d.rectangle([x - 90, y - 170, x + 90, y], fill=rgb('#2E2A26'))
        d.rectangle([x - 90, y - 136, x + 90, y - 116], fill=rgb('#D98E73'))
        d.rectangle([x + 20, y - 92, x + 46, y], fill=rgb('#D98E73'))
    elif latar == 'kota':
        rnd = random.Random(4)
        x = -20
        while x < W:
            w, h = rnd.randint(110, 170), rnd.randint(130, 230)
            d.rectangle([x, 1080 - h, x + w, 1080], fill=rgb(rnd.choice(['#EADCC8', '#F0E2CF', '#E4D3BC'])))
            x += w + rnd.randint(4, 20)
    d.rectangle([0, TANAH, W, H], fill=rgb('#F4DFC6'))
    pts = [(0, H)] + [(x, TANAH - 10 + 14 * math.sin(x / 180)) for x in range(0, W + 21, 20)] + [(W, H)]
    d.polygon(pts, fill=rgb('#F4DFC6'))
    return im


# ------------------------------------------------------------------ bentuk dasar
def _lapis():
    im = Image.new('RGBA', (W * K, H * K), (0, 0, 0, 0))
    return im, ImageDraw.Draw(im)


def _el(d, cx, cy, rx, ry, c):
    d.ellipse([(cx - rx) * K, (cy - ry) * K, (cx + rx) * K, (cy + ry) * K], fill=c)


def _poly(d, pts, c):
    d.polygon([(x * K, y * K) for x, y in pts], fill=c)


def _garis(d, pts, c, w):
    d.line([(x * K, y * K) for x, y in pts], fill=c, width=int(w * K), joint='curve')
    for x, y in (pts[0], pts[-1]):
        _el(d, x, y, w / 2, w / 2, c)


def _kaki(d, x, y0, y1, w, c):
    d.rounded_rectangle([(x - w / 2) * K, y0 * K, (x + w / 2) * K, y1 * K], int(w * K / 2.4), fill=c)


def gajah(d, x, y, s, fase, c, c2, berlutut=0.0, arah=-1):
    """Gajah polos menghadap kiri (arah=-1). (x,y)=titik tanah di bawah badan. Tanpa mata."""
    turun = 70 * s * berlutut
    by = y - 175 * s + turun
    # kaki (belakang dulu, warna lebih gelap)
    langkah = 0 if berlutut else 1
    for i, dx in enumerate((-70, 50, -40, 80)):
        angkat = langkah * max(0, math.sin(fase + i * math.pi / 2)) * 16 * s
        depan = dx < 0
        tinggi_bawah = y - angkat
        if berlutut and depan:
            tinggi_bawah = y - 10 * s
        _kaki(d, x + arah * -dx * s, by + 30 * s, tinggi_bawah, 40 * s, c2 if i < 2 else c)
    _el(d, x, by, 128 * s, 86 * s, c)                                   # badan
    _garis(d, [(x - arah * 122 * s, by - 10 * s), (x - arah * 150 * s, by + 40 * s)], c, 8 * s)   # ekor
    hx, hy = x + arah * 118 * s, by - 32 * s + 14 * s * berlutut
    _el(d, hx, hy, 66 * s, 62 * s, c)                                   # kepala
    _el(d, hx - arah * 34 * s, hy + 4 * s, 44 * s, 58 * s, c2)         # telinga
    goyang = math.sin(fase * 0.7) * 10 * s
    belalai = [(hx + arah * 50 * s, hy + 20 * s), (hx + arah * 70 * s, hy + 70 * s),
               (hx + arah * (66 * s + goyang), hy + 120 * s), (hx + arah * (78 * s + goyang), hy + 150 * s)]
    if berlutut:
        belalai = [(p[0], min(p[1], y - 6 * s)) for p in belalai]
    _garis(d, belalai, c, 26 * s)
    _poly(d, [(hx + arah * 44 * s, hy + 34 * s), (hx + arah * 86 * s, hy + 48 * s),
              (hx + arah * 46 * s, hy + 46 * s)], rgb('#F6F1E7'))       # gading


def orang(d, x, y, s, c, sorban, ayun=0.0, tombak=False, arah=-1):
    """Sosok polos berjubah, tanpa wajah. (x,y)=kaki."""
    t = 200 * s
    _poly(d, [(x - 34 * s, y), (x + 34 * s, y), (x + 24 * s, y - t * 0.72), (x - 24 * s, y - t * 0.72)], c)
    _el(d, x, y - t * 0.72, 30 * s, 18 * s, c)                          # bahu
    _el(d, x, y - t * 0.86, 20 * s, 22 * s, c)                          # kepala
    _el(d, x, y - t * 0.93, 24 * s, 14 * s, sorban)                     # sorban / penutup kepala
    if tombak:
        tx = x + arah * 30 * s
        _garis(d, [(tx, y - 10 * s), (tx + ayun * 6 * s, y - t * 1.2)], rgb('#8E7563'), 5 * s)
        _poly(d, [(tx + ayun * 6 * s - 8 * s, y - t * 1.2), (tx + ayun * 6 * s + 8 * s, y - t * 1.2),
                  (tx + ayun * 6 * s, y - t * 1.32)], rgb('#8E7563'))


def tokoh_besar(d, x, y, s, nafas, c, c2, sorban):
    """Tokoh utama dari belakang-samping: jubah, selendang, sorban. Tanpa wajah."""
    k = 1 + 0.008 * math.sin(nafas)
    h = 560 * s * k
    _poly(d, [(x - 120 * s, y), (x + 120 * s, y), (x + 92 * s, y - h * 0.70), (x - 92 * s, y - h * 0.70)], c)
    _el(d, x, y - h * 0.70, 100 * s, 54 * s, c)                         # bahu
    _poly(d, [(x - 100 * s, y - h * 0.72), (x + 60 * s, y - h * 0.70), (x + 30 * s, y - h * 0.28),
              (x - 96 * s, y - h * 0.40)], c2)                           # selendang
    _el(d, x, y - h * 0.84, 54 * s, 60 * s, c)                          # kepala (tanpa wajah)
    _el(d, x, y - h * 0.90, 66 * s, 42 * s, sorban)                     # sorban
    _poly(d, [(x + 30 * s, y - h * 0.88), (x + 58 * s, y - h * 0.86), (x + 52 * s, y - h * 0.70),
              (x + 36 * s, y - h * 0.72)], sorban)                       # ujung sorban


def burung(d, x, y, s, kepak, c):
    """Burung terbang (siluet "V" yang mengepak), tanpa mata."""
    a = math.sin(kepak) * 22 * s
    _garis(d, [(x - 52 * s, y - 14 * s - a), (x - 24 * s, y - 10 * s - a * 0.35), (x, y)], c, 8 * s)
    _garis(d, [(x + 52 * s, y - 14 * s - a), (x + 24 * s, y - 10 * s - a * 0.35), (x, y)], c, 8 * s)
    _el(d, x, y + 2 * s, 9 * s, 7 * s, c)


def _unta(d, x, y, s, c, fase=0.0):
    """Siluet unta polos tanpa mata, menghadap kiri."""
    _el(d, x, y - 95 * s, 62 * s, 32 * s, c)
    _el(d, x + 10 * s, y - 122 * s, 30 * s, 28 * s, c)
    _poly(d, [(x - 45 * s, y - 110 * s), (x - 65 * s, y - 175 * s), (x - 80 * s, y - 172 * s), (x - 68 * s, y - 95 * s)], c)
    _el(d, x - 85 * s, y - 175 * s, 18 * s, 11 * s, c)
    for i, lx in enumerate((-46, -28, 30, 48)):
        a = max(0, math.sin(fase + i * math.pi / 2)) * 8 * s
        _kaki(d, x + lx * s, y - 80 * s, y - a, 10 * s, c)


def _kecil(im):
    return im.resize((W, H), Image.LANCZOS)


# ------------------------------------------------------------------ gambar per babak
def gambar(seg, t, latar):
    """latar: Image panggung (RGB). Kembalikan frame RGB."""
    j = seg['jenis']
    im, d = _lapis()
    if j == 'pasukan':
        berlutut = seg.get('aksi') == 'berlutut'
        jalan = 0 if berlutut else t * 55
        gelap, gelap2 = rgb('#6B5F57'), rgb('#5A4F48')
        jauh, jauh2 = rgb('#A08E80'), rgb('#94827A')
        for i in range(4):                                   # barisan jauh
            x = 1150 + i * 300 - jalan * 0.6
            x = ((x + 300) % 1500) - 300
            gajah(d, x, 1075, 0.45, t * 4 + i, jauh, jauh2)
        for i in range(5):                                   # prajurit
            x = 640 + i * 95 - jalan * 0.9
            orang(d, x, 1225 + (i % 2) * 8, 0.85, rgb('#7A6A60'), rgb('#E9DCC6'),
                  ayun=math.sin(t * 5 + i), tombak=True)
        gx = 520 - jalan if not berlutut else 560
        bl = ease((t - 0.8) / 2.2) if berlutut else 0.0
        gajah(d, gx, 1215, 1.35, t * 4, gelap, gelap2, berlutut=bl)
        if not berlutut:
            gajah(d, gx + 430, 1195, 0.8, t * 4 + 1.3, gelap, gelap2)
        orang(d, gx + 30, 1215 - 175 * 1.35 - 80 + 70 * 1.35 * bl, 0.62, rgb('#4E4540'), rgb('#E9DCC6'))
    elif j == 'kawanan':
        rnd = random.Random(11)
        for i in range(11):
            bx0, by0 = rnd.randint(0, 900), rnd.randint(380, 900)
            sp = rnd.uniform(70, 110)
            x = ((bx0 + W + 200 - t * sp) % (W + 300)) - 100
            y = by0 + math.sin(t * 2 + i) * 12
            s = rnd.uniform(1.4, 2.1)
            burung(d, x, y, s, t * 9 + i, rgb('#4E4744'))
            for k in range(2):                               # batu jatuh
                u = (t * 1.1 + k / 3 + i * 0.37) % 1.0
                sx, sy = x + 6 * s, y + 20 + u * (TANAH - y - 20)
                _el(d, sx, sy, 7, 7, rgb('#B5654C'))
        for i in range(5):                                   # pasukan jauh di tanah
            gajah(d, 150 + i * 200, 1185, 0.38, t * 2 + i, rgb('#A08E80'), rgb('#94827A'))
    elif j == 'tokoh':
        if seg.get('dengan') == 'unta':
            for i in range(3):
                _unta(d, 800 + i * 150, 1170 - (i % 2) * 8, 1.25 - i * 0.12, rgb('#9C8B7E'), t * 3 + i)
        tokoh_besar(d, 420, 1280, 1.35, t * 1.6, rgb('#5B514C'), rgb('#6E635D'), rgb('#EFE3CF'))
    img = latar.copy()
    lap = _kecil(im)
    img.paste(lap, (0, 0), lap)
    return img
