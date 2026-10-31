"""Renderer gaya "Sirah #01" (contoh Gua Tsur): adegan penuh layar yang bercerita, caption pil abu-abu,
handle @sun_nahdaily di kanan atas, pergantian adegan dengan fade lembut.

Jenis babak (lihat storyboard.py):
  jendela     pemandangan dari dalam gua/ruang batu lewat lengkung: langit senja | malam | fajar
  peta        rute perjalanan antar tempat dengan garis putus-putus yang memanjang + kompas
  angka       angka penting yang menghitung naik di atas gulungan, latar dinding bata
  jejak       jejak kaki mendekat di padang pasir menuju tujuan (gua | rumah | tenda | kosong)
  pemandangan latar ilustrasi datar (ilustrasi.py) penuh layar
  dalil       kartu kutipan: teks Arab, terjemah, sumber, label derajat
  renungan    lengkung jendela fajar + judul faedah
  penutup     kartu Sunnah Daily + seri + ajakan

Tidak menggambar Nabi ﷺ, sahabat, maupun malaikat. Hewan hanya siluet polos tanpa mata.
"""
import math
import os
import random
import subprocess
import tempfile

from PIL import Image, ImageDraw, ImageFilter, ImageFont

import gaya
import ilustrasi
import makhluk
from video import susun_audio, kelompok_kata, SAW

W, H, FPS = gaya.W, gaya.H, gaya.FPS
FFMPEG = os.environ.get('FFMPEG', 'ffmpeg')
FADE = 0.35
HANDLE = '@sun_nahdaily'
_FD = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'fonts')
_FC = {}


def F(nama, s):
    berkas = {'tebal': 'Poppins-Bold.ttf', 'semi': 'Poppins-SemiBold.ttf', 'sedang': 'Poppins-Medium.ttf',
              'serif': 'Lora.ttf', 'arab': 'Amiri-Regular.ttf', 'judul': 'Fraunces-SemiBold.ttf'}[nama]
    k = (berkas, s)
    if k not in _FC:
        _FC[k] = ImageFont.truetype(os.path.join(_FD, berkas), s, layout_engine=ImageFont.Layout.RAQM)
    return _FC[k]


def rgb(h):
    return gaya.rgb(h)


# ------------------------------------------------------------------ teks (Latin + ﷺ)
def _pecah(t):
    import re
    return [p for p in re.split(f'({SAW})', t) if p]


def lebar(t, f):
    fa = F('arab', int(f.size * 1.1))
    return sum(fa.getlength(p) if p == SAW else f.getlength(p) for p in _pecah(t))


def tulis(d, x, y, t, f, warna):
    """y = garis dasar (baseline)."""
    fa = F('arab', int(f.size * 1.1))
    for p in _pecah(t):
        if p == SAW:
            d.text((x, y), p, font=fa, fill=warna, anchor='ls')
            x += fa.getlength(p)
        else:
            d.text((x, y), p, font=f, fill=warna, anchor='ls')
            x += f.getlength(p)


def bungkus(t, f, maks):
    baris, kini = [], ''
    for k in t.split():
        c = (kini + ' ' + k).strip()
        if lebar(c, f) <= maks or not kini:
            kini = c
        else:
            baris.append(kini)
            kini = k
    if kini:
        baris.append(kini)
    return baris


def tengah(d, y, t, f, warna, maks=W - 160, spasi=1.25):
    for b in bungkus(t, f, maks):
        tulis(d, (W - lebar(b, f)) / 2, y, b, f, warna)
        y += f.size * spasi
    return y


def pas(t, nama, besar, kecil, baris, maks=W - 160):
    for s in range(besar, kecil - 1, -4):
        if len(bungkus(t, F(nama, s), maks)) <= baris:
            return F(nama, s)
    return F(nama, kecil)


def ease(x):
    x = max(0.0, min(1.0, x))
    return x * x * (3 - 2 * x)


def gradasi(w, h, atas, bawah):
    a, b = rgb(atas), rgb(bawah)
    g = Image.new('RGB', (1, h))
    for y in range(h):
        t = y / max(1, h - 1)
        g.putpixel((0, y), tuple(int(a[i] + (b[i] - a[i]) * t) for i in range(3)))
    return g.resize((w, h))


def gelap(img, x0, y0, x1, y1):
    """True kalau area terang-gelapnya gelap (untuk memilih warna handle)."""
    px = img.crop((x0, y0, x1, y1)).resize((1, 1)).getpixel((0, 0))
    return sum(px[:3]) / 3 < 140


# ------------------------------------------------------------------ elemen bersama
def batu(seed=7):
    """Dinding batu gelap dengan bongkahan lembut (dalam gua)."""
    rnd = random.Random(seed)
    im = Image.new('RGB', (W // 2, H // 2), rgb('#4E4744'))
    d = ImageDraw.Draw(im)
    for _ in range(140):
        x, y = rnd.randint(-40, W // 2 + 40), rnd.randint(-40, H // 2 + 40)
        rx, ry = rnd.randint(40, 95), rnd.randint(28, 70)
        c = rnd.choice(['#5E5653', '#665E5A', '#574F4C', '#6E6560', '#463F3C'])
        d.ellipse([x - rx, y - ry, x + rx, y + ry], fill=rgb(c))
    return im.filter(ImageFilter.GaussianBlur(9)).resize((W, H), Image.BICUBIC)


def topeng_lengkung(x0, y0, x1, y1, blur=22):
    m = Image.new('L', (W, H), 0)
    d = ImageDraw.Draw(m)
    r = (x1 - x0) / 2
    d.ellipse([x0, y0, x1, y0 + 2 * r], fill=255)
    d.rectangle([x0, y0 + r, x1, y1], fill=255)
    return m.filter(ImageFilter.GaussianBlur(blur))


LENGKUNG = (165, 500, 915, 1690)


def langit_jendela(jenis, t, seed=3):
    """Isi lengkung: senja | malam | fajar. Bergerak pelan terhadap t."""
    x0, y0, x1, y1 = LENGKUNG
    w, h = x1 - x0, y1 - y0
    if jenis == 'malam':
        im = gradasi(w, h, '#2F3753', '#4A4C63')
        d = ImageDraw.Draw(im)
        rnd = random.Random(seed)
        for i in range(90):
            x, y = rnd.randint(10, w - 10), rnd.randint(30, int(h * 0.62))
            a = 0.5 + 0.5 * math.sin(t * 1.6 + i * 1.7)
            r = rnd.choice([1.5, 2, 2.5, 3])
            c = tuple(int(150 + 105 * a) for _ in range(3))
            d.ellipse([x - r, y - r, x + r, y + r], fill=c)
        nyala = Image.new('L', (w, h), 0)
        dn = ImageDraw.Draw(nyala)
        k = 1 + 0.04 * math.sin(t * 3.1)
        dn.ellipse([w * 0.08 / k, h * 0.68, w - w * 0.08 / k, h * 1.05], fill=200)
        nyala = nyala.filter(ImageFilter.GaussianBlur(70))
        im.paste(Image.new('RGB', (w, h), rgb('#D98A4E')), (0, 0), nyala)
        return im
    if jenis == 'fajar':
        im = gradasi(w, h, '#CBD6DE', '#F3DCC6')
        d = ImageDraw.Draw(im)
        naik = ease(t / 6) * 70
        cx, cy, r = w / 2, h * 0.70 - naik, 105
        d.ellipse([cx - r, cy - r, cx + r, cy + r], fill=rgb('#FBE2A6'))
        d.polygon([(0, h * 0.70)] + [(x, h * 0.70 - 40 * math.sin(math.pi * x / w)) for x in range(0, w + 1, 20)]
                  + [(w, h)], fill=rgb('#A8BFA6'))
        d.rectangle([0, h * 0.76, w, h], fill=rgb('#A8BFA6'))
        return im
    # senja
    im = gradasi(w, h, '#F2C6A9', '#EBB297')
    d = ImageDraw.Draw(im)
    cx, cy, r = w / 2, h * 0.30 + t * 4, 92
    d.ellipse([cx - r, cy - r, cx + r, cy + r], fill=rgb('#FBE6C4'))
    for i, (yy, c) in enumerate([(0.50, '#DFA48D'), (0.58, '#D49A85'), (0.68, '#C99280')]):
        geser = t * (6 + i * 4)
        pts = [(0, h)] + [(x, h * yy + 26 * math.sin((x + geser) / 160 + i)) for x in range(0, w + 1, 20)] + [(w, h)]
        d.polygon(pts, fill=rgb(c))
    return im


# ------------------------------------------------------------------ babak
class Babak:
    def __init__(self, seg, tema, ctx):
        self.s, self.tema, self.ctx = seg, tema, ctx
        self.c = gaya.warna(tema)
        self.grup = kelompok_kata(seg.get('teks_caption', ''), seg['durasi'])
        j = seg['jenis']
        self.latar = None
        if j in ('jendela', 'renungan'):
            self.latar = ctx['batu']
            self.topeng = ctx['topeng']
        elif j == 'pemandangan':
            self.adegan = ilustrasi.buat(seg.get('latar') or 'gurun', tema)
        elif j == 'angka':
            self.latar = self._bata()
        elif j == 'peta':
            self.latar = self._kertas_peta()
        elif j == 'jejak':
            self.latar = self._gurun_jejak()
        elif j in ('tokoh', 'pasukan', 'kawanan'):
            self.latar = makhluk.panggung(seg.get('latar') or 'gurun')
        elif j == 'dalil':
            self.latar = self._dalil()
        elif j == 'penutup':
            self.latar = self._penutup()

    # ---------- latar statis
    def _bata(self):
        im = Image.new('RGB', (W, H), rgb('#CDBDAC'))
        d = ImageDraw.Draw(im)
        bh, bw = 92, 230
        for r, y in enumerate(range(-20, H, bh)):
            off = (r % 2) * bw // 2
            for x in range(-bw, W + bw, bw):
                d.rounded_rectangle([x + off + 6, y + 6, x + off + bw - 6, y + bh - 6], 10, fill=rgb('#D6C7B7'))
        return im

    def _kertas_peta(self):
        im = Image.new('RGB', (W, H), rgb('#F4ECDD'))
        d = ImageDraw.Draw(im)
        for i in range(9):
            y0 = 360 + i * 150
            pts = [(x, y0 + 40 * math.sin(x / 420 + i * 0.8)) for x in range(-20, W + 21, 20)]
            d.line(pts, fill=rgb('#E6DCCB'), width=3)
        return im

    def _gurun_jejak(self):
        im = gradasi(W, H, '#D4E0E6', '#EEE6DD')
        d = ImageDraw.Draw(im)
        lap = [(780, '#E9C7A3', 46), (860, '#EDCFAE', 38), (1000, '#F1D8BA', 30), (1180, '#F4DFC6', 22)]
        for i, (y, c, a) in enumerate(lap):
            pts = [(0, H)] + [(x, y + a * math.sin(x / 230 + i * 1.3)) for x in range(0, W + 21, 20)] + [(W, H)]
            d.polygon(pts, fill=rgb(c))
        tj = self.s.get('tujuan') or 'gua'
        x, y = 830, 790
        if tj == 'gua':
            d.ellipse([x - 42, y - 62, x + 42, y + 22], fill=rgb('#5B514C'))
            d.rectangle([x - 42, y - 20, x + 42, y + 24], fill=rgb('#5B514C'))
        elif tj == 'rumah':
            d.rectangle([x - 70, y - 70, x + 70, y + 20], fill=rgb('#E2D2BE'))
            d.rectangle([x - 18, y - 30, x + 18, y + 20], fill=rgb('#8E7563'))
        elif tj == 'tenda':
            d.polygon([(x - 80, y + 20), (x, y - 80), (x + 80, y + 20)], fill=rgb('#7FA087'))
            d.polygon([(x - 16, y + 20), (x, y - 20), (x + 16, y + 20)], fill=rgb('#5E7F68'))
        return im

    def _dalil(self):
        dl = self.s['dalil']
        malam = self.tema == 'malam'
        bg, tinta, redup, aksen = (('#1F2621', '#EDE6DA', '#B8AE9F', '#A8C4AE') if malam else
                                   ('#F4ECDD', '#3E3A35', '#6B6358', '#7E9A84'))
        im = Image.new('RGB', (W, H), rgb(bg))
        d = ImageDraw.Draw(im)
        arab = (dl.get('arab') or '').strip().replace(',', '،').rstrip('.').replace('.', '')
        terj = (dl.get('terjemah') or '').strip()
        sumber = (dl.get('sumber') or '').strip()
        derajat = (dl.get('derajat') or '').lower()
        maks = W - 180
        blok = []
        if arab:
            for s in range(72, 40, -4):
                fa = F('arab', s)
                ba = self._bungkus_arab(arab, fa, maks)
                if len(ba) <= 4:
                    break
            blok.append(('arab', fa, ba, s * 1.7))
        for s in range(54, 32, -2):
            ft = F('serif', s)
            bt = bungkus(f'“{terj}”', ft, maks)
            if len(bt) * s * 1.32 <= (720 if arab else 900):
                break
        blok.append(('terj', ft, bt, ft.size * 1.32))
        fs = F('semi', 30)
        blok.append(('sumber', fs, bungkus(sumber, fs, maks), 42))
        tinggi = sum(len(b) * h for _, _, b, h in blok) + 40 * (len(blok) - 1)
        y = max(330, int((360 + 1240 - tinggi) / 2))
        d.line([(W / 2 - 60, y - 70), (W / 2 + 60, y - 70)], fill=rgb(aksen), width=3)
        for jenis, f, bs, hh in blok:
            for b in bs:
                if jenis == 'arab':
                    d.text((W / 2, y + hh * 0.72), b, font=f, fill=rgb(tinta), anchor='ms', direction='rtl',
                           language='ar')
                elif jenis == 'terj':
                    tulis(d, (W - lebar(b, f)) / 2, y + hh * 0.78, b, f, rgb(tinta))
                else:
                    d.text((W / 2, y + hh * 0.75), b, font=f, fill=rgb(aksen), anchor='ms')
                y += hh
            y += 40
        if dl.get('jenis') in ('hadits', 'atsar') and derajat in ('shahih', 'hasan', 'lemah', 'palsu'):
            teks, ikon, latar, fg = {
                'shahih': ('SHAHIH', '✓', '#E3ECE4', '#3F5A45'), 'hasan': ('HASAN', '✓', '#EFE8DA', '#3F5A45'),
                'lemah': ('HADITS LEMAH' if dl.get('jenis') == 'hadits' else 'LEMAH', '!', '#A9563F', '#FFFFFF'),
                'palsu': ('HADITS PALSU' if dl.get('jenis') == 'hadits' else 'PALSU', '×', '#2E2A24', '#F6F1E7'),
            }[derajat]
            fl = F('tebal', 28)
            lw = fl.getlength(teks) + 48 + 34
            xl = (W - lw) / 2
            d.rounded_rectangle([xl, y, xl + lw, y + 58], 12, fill=rgb(latar))
            ix, iy = xl + 34, y + 29
            if ikon == '✓':
                d.line([(ix - 10, iy), (ix - 3, iy + 8), (ix + 11, iy - 9)], fill=rgb(fg), width=5, joint='curve')
            else:
                d.text((ix, iy), ikon, font=fl, fill=rgb(fg), anchor='mm')
            d.text((xl + 58, iy), teks, font=fl, fill=rgb(fg), anchor='lm')
            if derajat == 'lemah':
                tengah(d, y + 120, 'Disebutkan sebagai penjelasan, bukan dalil.', F('sedang', 30), rgb('#A9563F'))
        return im

    @staticmethod
    def _bungkus_arab(t, f, maks):
        baris, kini = [], ''
        for k in t.split():
            c = (kini + ' ' + k).strip()
            if f.getlength(c, direction='rtl', language='ar') <= maks or not kini:
                kini = c
            else:
                baris.append(kini)
                kini = k
        if kini:
            baris.append(kini)
        return baris

    def _penutup(self):
        malam = self.tema == 'malam'
        im = gradasi(W, H, '#1F2621' if malam else '#E3ECE4', '#2A322C' if malam else '#F4ECDD')
        d = ImageDraw.Draw(im)
        tinta = rgb('#EDE6DA' if malam else '#3E3A35')
        redup = rgb('#B8AE9F' if malam else '#7A7268')
        cx, cy, r = W / 2, 560, 82
        d.ellipse([cx - r, cy - r, cx + r, cy + r], fill=rgb('#D98E73'))
        d.ellipse([cx - r + 38, cy - r - 18, cx + r + 38, cy + r - 18], fill=im.getpixel((int(cx + r + 60), int(cy))))
        y = 790
        tulis(d, (W - lebar('Sunnah Daily', F('tebal', 92))) / 2, y, 'Sunnah Daily', F('tebal', 92), tinta)
        y = tengah(d, y + 70, self.s.get('seri') or '', F('semi', 38), redup, spasi=1.3)
        tengah(d, y + 10, 'Ikuti seri berikutnya', F('sedang', 32), redup)
        fk = F('sedang', 26)
        yy = 1560
        for b in (self.s.get('kredit') or '').split('\n'):
            yy = tengah(d, yy, b, fk, redup, spasi=1.35)
        return im

    # ---------- per frame
    def render(self, t):
        s, j = self.s, self.s['jenis']
        if j in ('jendela', 'renungan'):
            img = self.latar.copy()
            x0, y0, x1, y1 = LENGKUNG
            lg = langit_jendela('fajar' if j == 'renungan' else s.get('langit', 'senja'), t)
            isi = Image.new('RGB', (W, H))
            isi.paste(lg, (x0, y0))
            img.paste(isi, (0, 0), self.topeng)
        elif j == 'pemandangan':
            sc = self.adegan.render(t + s.get('t_awal', 0)).convert('RGB')
            k = 1.2 + 0.01 * t                                    # dekat & sangat pelan maju
            sc = sc.resize((int(sc.width * k), int(sc.height * k)), Image.BILINEAR)
            img = Image.new('RGB', (W, H), sc.getpixel((sc.width // 2, 4)))
            x = (W - sc.width) // 2
            bawah = 150 if s.get('judul') else 330                  # hook: turunkan agar judul tidak menabrak matahari
            img.paste(sc, (x, H - sc.height - bawah))
            ImageDraw.Draw(img).rectangle([0, H - bawah - 2, W, H], fill=sc.getpixel((sc.width // 2, sc.height - 2)))
        elif j in ('tokoh', 'pasukan', 'kawanan'):
            img = makhluk.gambar(s, t, self.latar)
        else:
            img = self.latar.copy()
        d = ImageDraw.Draw(img)
        if j == 'peta':
            self._gambar_peta(d, t)
        elif j == 'angka':
            self._gambar_angka(img, d, t)
        elif j == 'jejak':
            self._gambar_jejak(d, t)
        judul = s.get('judul')
        if judul and j in ('jendela', 'renungan', 'pemandangan', 'jejak', 'tokoh', 'pasukan', 'kawanan'):
            f = pas(judul, 'tebal', 80, 56, 2)
            gelap_atas = gelap(img, 100, 330, W - 100, 450)
            warna = (255, 255, 255) if gelap_atas else rgb('#3E3A35')
            tengah(d, 380, judul, f, warna, spasi=1.15)
        # handle
        fh = F('semi', 30)
        hw = fh.getlength(HANDLE)
        d.text((W - 60 - hw, 150), HANDLE, font=fh,
               fill=(240, 236, 230) if gelap(img, W - 400, 120, W - 40, 170) else rgb('#3E3A35'), anchor='ls')
        return img

    def _caption(self, img, t):
        for m, sel, kata, _ in self.grup:
            if not (m <= t < sel or (self.grup[-1][0] == m and t >= m)):
                continue
            f = F('semi', 58)
            teks = ' '.join(kata)
            bs = bungkus(teks, f, W - 260)
            tb = max(lebar(b, f) for b in bs)
            hb = 76
            pad_x, pad_y = 34, 20
            x0 = (W - tb) / 2 - pad_x
            y0 = 1300
            y1 = y0 + hb * len(bs) + 2 * pad_y - 8
            lapis = Image.new('RGBA', (W, H), (0, 0, 0, 0))
            ImageDraw.Draw(lapis).rounded_rectangle([x0, y0, W - x0, y1], 26, fill=(88, 84, 80, 225))
            base = img.convert('RGBA')
            base.alpha_composite(lapis)
            img.paste(base.convert('RGB'))
            d = ImageDraw.Draw(img)
            y = y0 + pad_y + 56
            for b in bs:
                tulis(d, (W - lebar(b, f)) / 2, y, b, f, (255, 255, 255))
                y += hb
            break

    def _gambar_peta(self, d, t):
        s = self.s
        f1, f2 = pas(s.get('judul') or 'Perjalanan', 'tebal', 96, 60, 1, maks=640), F('semi', 40)
        tulis(d, 90, 420, s.get('judul') or 'Perjalanan', f1, rgb('#3E3A35'))
        if s.get('sub'):
            tulis(d, 92, 478, s['sub'], f2, rgb('#7E9A84'))
        cx, cy = 880, 470
        d.text((cx, 380), 'U', font=F('tebal', 34), fill=rgb('#3E3A35'), anchor='ms')
        d.ellipse([cx - 58, cy - 58, cx + 58, cy + 58], outline=rgb('#7E9A84'), width=4)
        d.polygon([(cx, cy - 46), (cx - 12, cy + 12), (cx + 12, cy + 12)], fill=rgb('#3E3A35'))
        tempat = s['tempat']
        X0, Y0, X1, Y1 = 160, 640, 920, 1180
        pts = [(X0 + p['x'] * (X1 - X0), Y0 + p['y'] * (Y1 - Y0)) for p in tempat]
        # titik antara agar rute sedikit berkelok
        rute = [pts[0]]
        for a, b in zip(pts, pts[1:]):
            mx, my = (a[0] + b[0]) / 2 + (b[1] - a[1]) * 0.12, (a[1] + b[1]) / 2 - (b[0] - a[0]) * 0.12
            for i in range(1, 21):
                u = i / 20
                rute.append(((1 - u) ** 2 * a[0] + 2 * (1 - u) * u * mx + u * u * b[0],
                             (1 - u) ** 2 * a[1] + 2 * (1 - u) * u * my + u * u * b[1]))
        panjang = [0.0]
        for a, b in zip(rute, rute[1:]):
            panjang.append(panjang[-1] + math.dist(a, b))
        jalan = ease(t / max(1.5, self.s['durasi'] * 0.8)) * panjang[-1]
        langkah = 22
        dd = 0.0
        while dd < jalan:
            i = next((k for k in range(1, len(panjang)) if panjang[k] >= dd), len(panjang) - 1)
            a, b = rute[i - 1], rute[i]
            u = (dd - panjang[i - 1]) / max(1e-6, panjang[i] - panjang[i - 1])
            x, y = a[0] + (b[0] - a[0]) * u, a[1] + (b[1] - a[1]) * u
            d.ellipse([x - 5, y - 5, x + 5, y + 5], fill=rgb('#C9775C'))
            dd += langkah
        fl = F('semi', 50)
        for k, (p, (x, y)) in enumerate(zip(tempat, pts)):
            sampai = k == 0 or jalan >= panjang[min(len(panjang) - 1, k * 20)] - 2
            if not sampai:
                continue
            akhir = k == len(tempat) - 1 and k > 0
            r = 18
            d.ellipse([x - r, y - r, x + r, y + r], fill=rgb('#D07A5F' if akhir else '#3E3A35'))
            nama = p['nama']
            lw = lebar(nama, fl)
            if x + 44 + lw < W - 60:
                tulis(d, x + 40, y + 17, nama, fl, rgb('#3E3A35'))
            else:
                tulis(d, x - 40 - lw, y + 17, nama, fl, rgb('#3E3A35'))

    def _gambar_angka(self, img, d, t):
        s = self.s
        x0, y0, x1, y1 = 120, 500, 960, 1180
        d.rounded_rectangle([x0 - 40, y0 - 20, x0 + 40, y1 + 20], 40, fill=rgb('#E6D2B0'))
        d.rounded_rectangle([x1 - 40, y0 - 20, x1 + 40, y1 + 20], 40, fill=rgb('#E6D2B0'))
        d.rectangle([x0 + 20, y0, x1 - 20, y1], fill=rgb('#F7EBD7'))
        d.line([(x0 + 20, y0), (x1 - 20, y0)], fill=rgb('#E2CDAA'), width=5)
        d.line([(x0 + 20, y1), (x1 - 20, y1)], fill=rgb('#E2CDAA'), width=5)
        lbl = (s.get('label') or '').upper()
        fl = pas(lbl, 'semi', 42, 30, 2, maks=x1 - x0 - 120)
        tengah(d, 640, lbl, fl, rgb('#C07A5F'), maks=x1 - x0 - 120, spasi=1.2)
        n = int(s['angka'])
        kini = int(round(n * ease(t / max(1.0, s['durasi'] * 0.55))))
        teks = f'{kini:,}'.replace(',', '.')
        fa = pas(f'{n:,}'.replace(',', '.'), 'tebal', 220, 120, 1, maks=x1 - x0 - 120)
        d.text((W / 2, 930), teks, font=fa, fill=rgb('#BE6B53'), anchor='ms')
        tengah(d, 1060, s.get('satuan') or '', pas(s.get('satuan') or '', 'semi', 64, 40, 1, maks=x1 - x0 - 120),
               rgb('#8C6E5C'), maks=x1 - x0 - 120)

    def _gambar_jejak(self, d, t):
        n = 18
        muncul = min(n, int(t * 3.2) + 1)
        for i in range(muncul):
            u = i / (n - 1)
            x = 260 + u * 520 + (24 if i % 2 else -24) * (1 - u * 0.6)
            y = 1650 - u * 760
            s = 1.0 - u * 0.62
            ang = -math.atan2(760, 520)
            self._telapak(d, x, y, 26 * s, 14 * s, ang)

    @staticmethod
    def _telapak(d, x, y, a, b, ang):
        pts = []
        for k in range(24):
            q = 2 * math.pi * k / 24
            px, py = a * math.cos(q), b * math.sin(q)
            pts.append((x + px * math.cos(ang) - py * math.sin(ang), y + px * math.sin(ang) + py * math.cos(ang)))
        d.polygon(pts, fill=rgb('#C9926B'))
        hx, hy = x - (a * 1.25) * math.cos(ang), y - (a * 1.25) * math.sin(ang)
        r = b * 0.85
        d.ellipse([hx - r, hy - r, hx + r, hy + r], fill=rgb('#C9926B'))


# ------------------------------------------------------------------ susun video
def buat_video(segmen, tema, out_mp4, contoh_jpg=None):
    ctx = {'batu': batu(), 'topeng': topeng_lengkung(*LENGKUNG)}
    with tempfile.TemporaryDirectory() as tmp:
        wav = os.path.join(tmp, 'suara.wav')
        total = susun_audio(segmen, wav, tmp)
        t_latar = 0.0
        babak = []
        for s in segmen:
            s['t_awal'] = t_latar
            t_latar += s['durasi']
            babak.append(Babak(s, tema, ctx))
        n = int(total * FPS)
        proc = subprocess.Popen([
            FFMPEG, '-y', '-loglevel', 'error', '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-s', f'{W}x{H}',
            '-r', str(FPS), '-i', '-', '-i', wav, '-c:v', 'libx264', '-preset', 'veryfast', '-crf', '21',
            '-pix_fmt', 'yuv420p', '-c:a', 'aac', '-b:a', '160k', '-shortest', '-movflags', '+faststart',
            out_mp4], stdin=subprocess.PIPE)
        idx, contoh, sebelum = 0, [], None
        for fr in range(n):
            t = fr / FPS
            while idx + 1 < len(segmen) and t >= segmen[idx + 1]['mulai']:
                sebelum = babak[idx].render(segmen[idx]['durasi'] - 1 / FPS)
                idx += 1
            lt = t - segmen[idx]['mulai']
            img = babak[idx].render(lt)
            if idx > 0 and lt < FADE and sebelum is not None:
                img = Image.blend(sebelum, img, ease(lt / FADE))
            babak[idx]._caption(img, lt)
            if contoh_jpg and abs(t - (segmen[idx]['mulai'] + min(1.5, segmen[idx]['durasi'] / 2))) < 0.5 / FPS:
                contoh.append(img.resize((W // 3, H // 3)))
            proc.stdin.write(img.tobytes())
        proc.stdin.close()
        if proc.wait() != 0:
            raise RuntimeError('ffmpeg gagal')
        if contoh_jpg and contoh:
            lembar = Image.new('RGB', (W // 3 * len(contoh), H // 3), 'white')
            for i, im in enumerate(contoh):
                lembar.paste(im, (i * W // 3, 0))
            lembar.save(contoh_jpg, quality=85)
        return total
