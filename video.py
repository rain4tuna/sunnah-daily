"""Penyusun video 9:16 Sunnah Daily sesuai brand guideline.

segmen: list dict, urut tayang:
  {'jenis': 'hook',    'latar': 'gurun', 'judul': 'Kenapa ...?', 'wav': path}
  {'jenis': 'kisah',   'latar': 'kota',  'narasi': '...', 'wav': path}
  {'jenis': 'dalil',   'dalil': {...},   'narasi': '...', 'wav': path}
  {'jenis': 'faedah',  'latar': 'kitab', 'faedah': '...', 'narasi': '...', 'wav': path}
  {'jenis': 'penutup', 'narasi': '...',  'wav': path}
"""
import os
import re
import subprocess
import tempfile
import wave

from PIL import Image, ImageDraw

import gaya
import ilustrasi

W, H, FPS = gaya.W, gaya.H, gaya.FPS
JEDA = 0.35            # detik hening antar segmen
FADE = 0.3
FFMPEG = os.environ.get('FFMPEG', 'ffmpeg')
SAW = 'ﷺ'


# ------------------------------------------------------------------ teks campuran (Latin + ﷺ)
def _potong(teks):
    return [p for p in re.split(f'({SAW})', teks) if p]


def lebar(teks, f):
    fa = gaya.font('arab', int(f.size * 1.05))
    return sum(fa.getlength(p) if p == SAW else f.getlength(p) for p in _potong(teks))


def tulis(d, x, y, teks, f, warna):
    """Tulis teks dengan glyph ﷺ dari Amiri. y = garis atas."""
    fa = gaya.font('arab', int(f.size * 1.05))
    asc = f.getmetrics()[0]
    for p in _potong(teks):
        if p == SAW:
            d.text((x, y + asc), p, font=fa, fill=warna, anchor='ls')
            x += fa.getlength(p)
        else:
            d.text((x, y + asc), p, font=f, fill=warna, anchor='ls')
            x += f.getlength(p)


def bungkus(teks, f, maks):
    baris, kini = [], ''
    for k in teks.split():
        coba = (kini + ' ' + k).strip()
        if lebar(coba, f) <= maks or not kini:
            kini = coba
        else:
            baris.append(kini)
            kini = k
    if kini:
        baris.append(kini)
    return baris


def tengah(d, y, teks, f, warna, maks=W - 2 * gaya.TEPI, spasi=1.18):
    bs = bungkus(teks, f, maks)
    for b in bs:
        tulis(d, (W - lebar(b, f)) / 2, y, b, f, warna)
        y += f.size * spasi
    return y


def judul_pas(teks, nama, besar, kecil, maks_baris, maks=W - 2 * gaya.TEPI):
    for s in range(besar, kecil - 1, -4):
        f = gaya.font(nama, s)
        if len(bungkus(teks, f, maks)) <= maks_baris:
            return f
    return gaya.font(nama, kecil)


# ------------------------------------------------------------------ logo (digambar, tanpa latar)
def logo(ukuran, tema):
    c = gaya.warna(tema)
    k = ukuran / 1080 * 2
    im = Image.new('RGBA', (int(1080 * k), int(1080 * k)), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)

    def P(pts):
        return [(x * k, y * k) for x, y in pts]
    d.polygon(P([(540, 640), (400, 555), (210, 580), (210, 850), (400, 825), (540, 905)]), fill=c['sage'])
    d.polygon(P([(540, 640), (680, 555), (870, 580), (870, 850), (680, 825), (540, 905)]), fill=c['sage-tua'])
    d.ellipse([(510 - 165) * k, (370 - 165) * k, (510 + 165) * k, (370 + 165) * k], fill=c['terakota'])
    d.ellipse([(575 - 135) * k, (320 - 135) * k, (575 + 135) * k, (320 + 135) * k], fill=(0, 0, 0, 0))
    import math
    pts = []
    for i in range(10):
        a = -math.pi / 2 + i * math.pi / 5
        rr = 58 if i % 2 == 0 else 24
        pts.append((605 + rr * math.cos(a), 345 + rr * math.sin(a)))
    d.polygon(P(pts), fill=c['terakota'])
    return im.resize((ukuran, ukuran), Image.LANCZOS)


# ------------------------------------------------------------------ waktu caption
def kelompok_kata(narasi, durasi):
    """Bagi narasi jadi kelompok 1-3 kata. Kembalikan [(mulai, selesai, [kata], [(m,s) per kata])]."""
    kata = narasi.split()
    if not kata:
        return []
    bobot = [(30 if k.startswith(SAW) else len(k)) + 2 for k in kata]
    total = sum(bobot)
    t0, pakai = 0.12, max(0.5, durasi - 0.25)
    waktu = []
    t = t0
    for b in bobot:
        dur = pakai * b / total
        waktu.append((t, t + dur))
        t += dur
    grup, kini, f = [], [], gaya.font('isi-tebal', 64)
    for i, k in enumerate(kata):
        coba = ' '.join(kata[j] for j in kini + [i])
        akhir_kalimat = kini and re.search(r'[.!?,;:]$', kata[kini[-1]])
        if kini and (len(kini) >= 3 or lebar(coba, f) > W - 2 * gaya.TEPI - 60 or akhir_kalimat):
            grup.append(kini)
            kini = []
        kini.append(i)
    if kini:
        grup.append(kini)
    return [(waktu[g[0]][0], waktu[g[-1]][1], [kata[i] for i in g], [waktu[i] for i in g]) for g in grup]


def gambar_caption(d, grup, t, c, y=1420):
    for m, s, kata, wk in grup:
        if not (m <= t < s or (grup[-1][0] == m and t >= m)):
            continue
        f = gaya.font('isi-tebal', 64)
        spasi = 18
        lebar_k = [lebar(k, f) for k in kata]
        total = sum(lebar_k) + spasi * (len(kata) - 1)
        x = (W - total) / 2
        for k, lk, (km, ks) in zip(kata, lebar_k, wk):
            aktif = km <= t < ks + 0.05
            if aktif:
                d.rounded_rectangle([x - 14, y - 6, x + lk + 14, y + 80], 44, fill=c['terakota-tua'])
            tulis(d, x, y, k, f, c['di-terakota'] if aktif else c['tinta'])
            x += lk + spasi
        break


# ------------------------------------------------------------------ bingkai per jenis
class Bingkai:
    def __init__(self, seg, tema):
        self.seg, self.tema = seg, tema
        self.c = gaya.warna(tema)
        self.adegan = ilustrasi.buat(seg.get('latar', 'gurun'), tema) if seg.get('latar') else None
        self.logo_kecil = logo(104, tema)
        self.grup = kelompok_kata(seg.get('narasi', ''), seg['durasi'])
        self.statis = None
        if seg['jenis'] == 'dalil':
            self.statis = self._dalil()
        elif seg['jenis'] == 'penutup':
            self.statis = self._penutup()

    def _panel(self, img):
        d = ImageDraw.Draw(img)
        d.rectangle([0, ilustrasi.SH, W, H], fill=self.c['gading'])
        return d

    def render(self, t):
        c, s = self.c, self.seg
        if self.statis is not None:
            img = self.statis.copy()
        else:
            img = Image.new('RGB', (W, H), c['gading'])
            img.paste(self.adegan.render(t + s.get('t_awal', 0)), (0, 0))
            d = self._panel(img)
            img.paste(self.logo_kecil, (W - gaya.TEPI - 104, gaya.AMAN_ATAS + 10), self.logo_kecil)
            if s['jenis'] == 'hook':
                f = judul_pas(s['judul'], 'judul', 104, 72, 2)
                tengah(d, 1360, s['judul'], f, c['tinta'], spasi=1.08)
            elif s['jenis'] == 'kisah':
                gambar_caption(d, self.grup, t, c)
            elif s['jenis'] == 'faedah':
                f = gaya.font('judul', 64)
                tulis(d, (W - lebar('Faedah', f)) / 2, 1335, 'Faedah', f, c['sage-tua'])
                ff = judul_pas(s['faedah'], 'isi-sedang', 48, 36, 3)
                tengah(d, 1430, s['faedah'], ff, c['tinta'], spasi=1.3)
        if t < FADE:                                     # muncul pelan dari latar
            a = t / FADE
            img = Image.blend(Image.new('RGB', (W, H), c['gading']), img, a)
        return img

    def _dalil(self):
        c, dl = self.c, self.seg['dalil']
        img = Image.new('RGB', (W, H), c['gading'])
        d = ImageDraw.Draw(img)
        x0, x1 = 72, W - 72
        fj = gaya.font('judul', 64)
        # label derajat (hadits saja)
        derajat = (dl.get('derajat') or '').lower()
        judul_kartu = {'ulama': 'Nasihat Ulama', 'atsar': 'Atsar'}.get(dl.get('jenis'), 'Dalilnya')
        if dl.get('jenis') in ('hadits', 'atsar') and derajat:
            teks_lbl, ikon, bg, fg = {
                'shahih': ('SHAHIH', '✓', c['sage-muda'], c['tinta']),
                'hasan': ('HASAN', '✓', c['gading-2'], c['tinta']),
                'lemah': ('HADITS LEMAH' if dl.get('jenis') == 'hadits' else 'LEMAH', '!', c['terakota-tua'], c['di-terakota']),
                'palsu': ('HADITS PALSU' if dl.get('jenis') == 'hadits' else 'PALSU', '×', c['palsu'], c['gading']),
            }.get(derajat, ('SHAHIH', '✓', c['sage-muda'], c['tinta']))
            fl = gaya.font('isi-tebal', 30)
            isi = f'{ikon}  {teks_lbl}'
            lw = fl.getlength(isi) + 44
            label = (lw, isi, fl, bg, fg, derajat)
        else:
            label = None
        isi_w = x1 - x0 - 2 * 48
        arab = (dl.get('arab') or '').strip().replace(',', '،').replace(';', '؛').replace('?', '؟').rstrip('.').replace('.', '')
        terj = (dl.get('terjemah') or '').strip()
        sumber = (dl.get('sumber') or '').strip()
        bagian = []
        if arab:
            for s in range(64, 40, -4):
                fa = gaya.font('arab', s)
                ba = self._bungkus_arab(arab, fa, isi_w)
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
        tinggi = 48 * 2
        for jenis, f, bs in bagian:
            tinggi += len(bs) * f.size * (1.75 if jenis == 'arab' else 1.4) + 32
        kartu_y0 = int(max(400, (gaya.AMAN_ATAS + 120 + H - gaya.AMAN_BAWAH - tinggi) / 2))
        tulis(d, x0 + 8, kartu_y0 - 120, judul_kartu, fj, c['tinta'])
        if label:
            lw, isi, fl, bg, fg, derajat = label
            d.rounded_rectangle([x1 - lw, kartu_y0 - 108, x1, kartu_y0 - 48], 14, fill=bg,
                                outline=c['sage-tua'] if derajat == 'hasan' else None, width=3)
            d.text((x1 - lw + 22, kartu_y0 - 78), isi, font=fl, fill=fg, anchor='lm')
        d.rounded_rectangle([x0, kartu_y0, x1, kartu_y0 + tinggi], 28, fill=c['gading-2'])
        y = kartu_y0 + 48
        for jenis, f, bs in bagian:
            for b in bs:
                if jenis == 'arab':
                    d.text((x1 - 48, y + f.size * 1.1), b, font=f, fill=c['tinta'], anchor='rs',
                           direction='rtl', language='ar')
                    y += f.size * 1.75
                else:
                    tulis(d, x0 + 48, y, b, f, c['teks-redup'] if jenis == 'terj' else c['teks-redup'])
                    y += f.size * 1.4
            y += 32
        if derajat == 'lemah':
            fn = gaya.font('isi-sedang', 30)
            tengah(d, kartu_y0 + tinggi + 40, ('Hadits' if dl.get('jenis') == 'hadits' else 'Riwayat') + ' ini lemah. Disebutkan sebagai penjelasan, bukan dalil.',
                   fn, c['terakota-tua'] if self.tema == 'siang' else c['terakota'])
        return img

    @staticmethod
    def _bungkus_arab(teks, f, maks):
        baris, kini = [], ''
        for k in teks.split():
            coba = (kini + ' ' + k).strip()
            if f.getlength(coba, direction='rtl', language='ar') <= maks or not kini:
                kini = coba
            else:
                baris.append(kini)
                kini = k
        if kini:
            baris.append(kini)
        return baris

    def _penutup(self):
        c = self.c
        img = Image.new('RGB', (W, H), c['gading'])
        d = ImageDraw.Draw(img)
        lg = logo(380, self.tema)
        img.paste(lg, ((W - 380) // 2, 330), lg)
        fj = gaya.font('judul', 110)
        tulis(d, (W - lebar('Sunnah Daily', fj)) / 2, 760, 'Sunnah Daily', fj, c['tinta'])
        ajak = 'Ikuti untuk sunnah berikutnya'
        fa = gaya.font('isi-tebal', 40)
        lw = fa.getlength(ajak) + 80
        d.rounded_rectangle([(W - lw) / 2, 940, (W + lw) / 2, 1030], 45, fill=c['terakota-tua'])
        d.text((W / 2, 985), ajak, font=fa, fill=c['di-terakota'], anchor='mm')
        fk = gaya.font('isi-sedang', 30)
        y = 1110
        for b in (self.seg.get('kredit') or '').split('\n'):
            y = tengah(d, y, b, fk, c['teks-redup'], spasi=1.4)
        return img


# ------------------------------------------------------------------ audio
def _durasi(path):
    with wave.open(path) as w:
        return w.getnframes() / w.getframerate()


def susun_audio(segmen, out_wav, tmp):
    """Normalkan tiap wav (24 kHz mono), sambung dengan jeda. Isi seg['durasi'] dan seg['mulai']."""
    potong = []
    t = 0.0
    for i, s in enumerate(segmen):
        norm = os.path.join(tmp, f'n{i}.wav')
        subprocess.run([FFMPEG, '-y', '-loglevel', 'error', '-i', s['wav'], '-ac', '1', '-ar', '24000',
                        '-af', f'apad=pad_dur={JEDA}', norm], check=True)
        s['durasi'] = _durasi(norm)
        if s['jenis'] == 'dalil':
            s['durasi'] = max(s['durasi'], 6.0)
        s['mulai'] = t
        t += s['durasi']
        potong.append(norm)
    lst = os.path.join(tmp, 'daftar.txt')
    with open(lst, 'w') as f:
        for i, p in enumerate(potong):
            f.write(f"file '{p}'\n")
    gabung = os.path.join(tmp, 'gabung.wav')
    subprocess.run([FFMPEG, '-y', '-loglevel', 'error', '-f', 'concat', '-safe', '0', '-i', lst, gabung],
                   check=True)
    # pastikan panjang audio = total durasi (dalil bisa diperpanjang)
    subprocess.run([FFMPEG, '-y', '-loglevel', 'error', '-i', gabung, '-af', f'apad=whole_dur={t:.3f}',
                    '-t', f'{t:.3f}', out_wav], check=True)
    return t


def buat_video(segmen, tema, out_mp4, contoh_jpg=None):
    with tempfile.TemporaryDirectory() as tmp:
        wav = os.path.join(tmp, 'suara.wav')
        total = susun_audio(segmen, wav, tmp)
        t_latar = 0.0
        bingkai = []
        for s in segmen:
            s['t_awal'] = t_latar
            t_latar += s['durasi']
            bingkai.append(Bingkai(s, tema))
        n = int(total * FPS)
        proc = subprocess.Popen([
            FFMPEG, '-y', '-loglevel', 'error', '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-s', f'{W}x{H}',
            '-r', str(FPS), '-i', '-', '-i', wav, '-c:v', 'libx264', '-preset', 'veryfast', '-crf', '21',
            '-pix_fmt', 'yuv420p', '-c:a', 'aac', '-b:a', '160k', '-shortest', '-movflags', '+faststart',
            out_mp4], stdin=subprocess.PIPE)
        idx = 0
        contoh = []
        for fr in range(n):
            t = fr / FPS
            while idx + 1 < len(segmen) and t >= segmen[idx + 1]['mulai']:
                idx += 1
            img = bingkai[idx].render(t - segmen[idx]['mulai'])
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
