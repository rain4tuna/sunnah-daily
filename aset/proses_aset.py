"""Rapikan aset mentah (aset/mentah, hasil Meta AI/Flow) jadi aset siap pakai Remotion (remotion/public_panjang/aset).

- karakter, hewan, properti, elemen: latar putih/abu polos dibuang (numpy+scipy, tanpa model AI),
  tepi dihaluskan, dipotong rapat, disimpan WEBP transparan.
- latar: diubah ke 1920x1080 (isi penuh, potong tengah), JPG.
- gerak: video MP4 disalin apa adanya (suara dimatikan di Remotion).

Pakai: python aset/proses_aset.py            (proses semua)
       python aset/proses_aset.py karakter   (satu kategori)
"""
import os
import shutil
import sys

import numpy as np
from PIL import Image, ImageFilter
from scipy import ndimage

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MENTAH = os.path.join(ROOT, 'aset', 'mentah')
HASIL = os.path.join(ROOT, 'remotion', 'public_panjang', 'aset')   # public dir khusus video panjang
POTONG = ('karakter', 'hewan', 'properti', 'elemen')
TINGGI_MAKS = {'karakter': 1100, 'hewan': 900, 'properti': 700, 'elemen': 600}
AMBANG = 20          # beda warna maksimal dari taksiran warna latar di titik itu


def taksir_latar(a):
    """Warna latar per piksel, diinterpolasi dari keempat tepi gambar (latar studio abu sering bergradasi)."""
    h, w, _ = a.shape
    halus = lambda t: ndimage.median_filter(t, size=(41, 1), mode='nearest')   # abaikan objek yang menyentuh tepi
    kiri, kanan, atas, bawah = halus(a[:, 0]), halus(a[:, -1]), halus(a[0]), halus(a[-1])
    y = np.arange(h, dtype=np.float32)[:, None, None]
    x = np.arange(w, dtype=np.float32)[None, :, None]
    bobot = [1 / (x + 1), 1 / (w - x), 1 / (y + 1), 1 / (h - y)]
    warna = [kiri[:, None], kanan[:, None], atas[None], bawah[None]]
    total = sum(np.broadcast_to(b, (h, w, 1)) for b in bobot)
    return sum(c * b for c, b in zip(warna, bobot)) / total


def buang_latar(im):
    """Kembalikan RGBA. Latar = piksel yang warnanya dekat dengan taksiran warna latar dan tersambung ke tepi
    gambar; baju putih/krem aman karena dibandingkan dengan latar di sekitarnya, bukan sekadar 'terang'.
    Gumpalan kecil yang terpisah dari objek utama (bintik, sisa bayangan) ikut dibuang."""
    rgb = im.convert('RGB')
    a = np.asarray(rgb).astype(np.float32)
    calon = np.abs(a - taksir_latar(a)).max(axis=2) < AMBANG
    lab, _ = ndimage.label(calon)
    sentuh_tepi = np.unique(np.concatenate([lab[0], lab[-1], lab[:, 0], lab[:, -1]]))
    latar = np.isin(lab, sentuh_tepi[sentuh_tepi > 0])
    isi = ndimage.binary_fill_holes(~latar)
    # simpan objek utama + bagian lain yang cukup besar (mis. tiap orang di gambar kerumunan)
    lab, n = ndimage.label(isi)
    if n > 1:
        luas = ndimage.sum(isi, lab, range(1, n + 1))
        isi = np.isin(lab, 1 + np.flatnonzero(luas >= 0.03 * luas.max()))
    isi = ndimage.binary_erosion(isi, iterations=1)       # buang pinggiran terang 1 px
    topeng = Image.fromarray((isi * 255).astype(np.uint8)).filter(ImageFilter.GaussianBlur(1.0))
    hasil = rgb.convert('RGBA')
    hasil.putalpha(topeng)
    return hasil


def potong_rapat(im, pad=12):
    kotak = im.getchannel('A').point(lambda v: 255 if v > 20 else 0).getbbox()
    if not kotak:
        return im
    x0, y0, x1, y1 = kotak
    return im.crop((max(0, x0 - pad), max(0, y0 - pad), min(im.width, x1 + pad), min(im.height, y1 + pad)))


def kecilkan(im, tinggi):
    if im.height > tinggi:
        im = im.resize((round(im.width * tinggi / im.height), tinggi), Image.LANCZOS)
    return im


def proses_potong(kat):
    asal, tujuan = os.path.join(MENTAH, kat), os.path.join(HASIL, kat)
    os.makedirs(tujuan, exist_ok=True)
    n = 0
    for nm in sorted(os.listdir(asal)):
        if not nm.lower().endswith(('.jpg', '.jpeg', '.png', '.webp')):
            continue
        im = kecilkan(potong_rapat(buang_latar(Image.open(os.path.join(asal, nm)))), TINGGI_MAKS[kat])
        im.save(os.path.join(tujuan, os.path.splitext(nm)[0] + '.webp'), 'WEBP', quality=88, method=4)
        n += 1
    return n


def proses_latar():
    asal, tujuan = os.path.join(MENTAH, 'latar'), os.path.join(HASIL, 'latar')
    os.makedirs(tujuan, exist_ok=True)
    n = 0
    for nm in sorted(os.listdir(asal)):
        if not nm.lower().endswith(('.jpg', '.jpeg', '.png', '.webp')):
            continue
        im = Image.open(os.path.join(asal, nm)).convert('RGB')
        skala = max(1920 / im.width, 1080 / im.height)
        im = im.resize((round(im.width * skala), round(im.height * skala)), Image.LANCZOS)
        x, y = (im.width - 1920) // 2, (im.height - 1080) // 2
        im.crop((x, y, x + 1920, y + 1080)).save(os.path.join(tujuan, os.path.splitext(nm)[0] + '.jpg'), quality=88)
        n += 1
    return n


def proses_gerak():
    asal, tujuan = os.path.join(MENTAH, 'gerak'), os.path.join(HASIL, 'gerak')
    os.makedirs(tujuan, exist_ok=True)
    n = 0
    for nm in sorted(os.listdir(asal)):
        if nm.lower().endswith('.mp4'):
            shutil.copy2(os.path.join(asal, nm), os.path.join(tujuan, nm))
            n += 1
    return n


# Klip video (Flow/Veo) yang lolos cek: isi adegan, tokoh yang tampil, dan cocok untuk kisah apa.
# 'tokoh' dipakai storyboard supaya klip hanya muncul di babak yang memang menceritakan tokoh itu.
GERAK = {
    'b01_kafilah_senja': ('kafilah unta bermuatan berjalan di gurun senja', '', 'perjalanan, dagang, hijrah, pembuka'),
    'b02_kerumunan_makkah': ('penduduk Makkah berjalan di jalan kota, dilihat dari belakang', '', 'masyarakat Makkah, kaum Quraisy'),
    'b03_gajah_abrahah': ('gajah berjalan lalu berlutut menolak maju', 'Abrahah (pasukan gajah)', 'tahun gajah, Ka\'bah dijaga Allah'),
    'b04_burung_batu': ('kawanan burung kecil membawa batu terbang di langit gurun', '', 'burung Ababil, tahun gajah'),
    'b05_abdul_muthalib_sumur': ('Abdul Muthalib menengok sumur di dekat Ka\'bah lalu mengangkat tongkat', 'Abdul Muthalib', 'sumur Zamzam, kakek Nabi'),
    'b06_raja_romawi_surat': ('raja Romawi membuka gulungan surat di istana', 'raja Romawi (Heraklius)', 'surat Nabi kepada raja, dialog Heraklius'),
    'b07_halimah_desa': ('Halimah membawa keranjang di desa Badui, domba merumput', 'Halimah as-Sa\'diyah', 'masa kecil di Bani Sa\'d, ibu susu'),
    'b08_khadijah_rumah': ('Khadijah duduk tenang di rumah dekat lentera', 'Khadijah', 'Khadijah menenangkan, rumah tangga Nabi'),
    'b09_pasar_pedagang': ('pemuda menuang koin emas di pasar', '', 'dagang, harta, tawaran dunia, sedekah'),
    'b10_pembesar_quraisy': ('Abu Jahal dan Abu Lahab berdebat malam hari', 'Abu Jahal, Abu Lahab', 'penentangan Quraisy, makar musyrikin'),
    'b11_bilal_ahad': ('Bilal berdiri teguh di bawah terik matahari mengacungkan jari', 'Bilal', 'siksaan kaum lemah, Ahad Ahad, keteguhan iman'),
    'b12_hijrah_habasyah': ('dua orang berjalan menuju kapal di pantai', 'kaum muslimin (umum)', 'hijrah ke Habasyah'),
    'b13_abu_thalib_boikot': ('Abu Thalib memandang piagam dengan sedih di lembah tandus', 'Abu Thalib', 'boikot Quraisy, piagam zalim'),
    'b14_piagam_rayap': ('piagam di dinding termakan rayap', '', 'piagam boikot dimakan rayap'),
    'b15_anak_bermain': ('dua anak melambai ceria di desa', '', 'pembuka, ajakan, penutup'),
    'l01_gurun_siang_gerak': ('gurun siang dengan pasir tertiup angin', '', 'latar gurun siang'),
    'l02_gurun_senja_gerak': ('gurun senja dengan pasir tertiup angin', '', 'latar gurun senja'),
}


def _durasi(path):
    ffprobe = shutil.which('ffprobe') or os.path.join(ROOT, 'remotion', 'node_modules', '@remotion',
                                                     'compositor-win32-x64-msvc', 'ffprobe.exe')
    import subprocess
    try:
        r = subprocess.run([ffprobe, '-v', 'error', '-show_entries', 'format=duration', '-of', 'csv=p=0', path],
                           capture_output=True, text=True, timeout=60)
        return round(float(r.stdout.strip()), 2)
    except Exception:
        return None


def buat_daftar():
    """remotion/public_panjang/aset/daftar.json: semua aset siap pakai + deskripsinya (dari PROMPT_ASET_META_AI.md)."""
    import json
    import re
    md = open(os.path.join(ROOT, 'aset', 'PROMPT_ASET_META_AI.md'), encoding='utf-8').read()
    desk = {}
    for awal, akhir, isi in re.findall(r'^\| ([KHBEL]\d\d)(?:–([A-Z]\d\d))? \| (.+?) \|', md, re.M):
        for i in range(int(awal[1:]), int((akhir or awal)[1:]) + 1):      # baris rentang, mis. E01–E03
            desk[f'{awal[0].lower()}{i:02d}'] = re.sub(r'\s*\*\(.*?\)\*|,?\s*\(?\d+ (slightly )?different shapes.*', '', isi).strip()
    nama_tokoh = {}
    for kode, nama, isi in re.findall(r'^\| (T\d\d) \| (.+?) \| (.+?) \|', md, re.M):
        nama_tokoh[kode.lower()] = nama
        desk[kode.lower()] = isi.strip()
    daftar = {}
    for kat in (*POTONG, 'latar'):
        folder = os.path.join(HASIL, kat)
        for nm in sorted(os.listdir(folder)) if os.path.isdir(folder) else []:
            kode = os.path.splitext(nm)[0]
            induk = kode[:3]
            item = {'kategori': kat, 'file': f'aset/{kat}/{nm}', 'deskripsi': desk.get(induk, '')}
            if kat == 'karakter' and '_p' in kode:
                item['pose'] = kode.split('_')[1]
            if induk in nama_tokoh:
                item['tokoh'] = nama_tokoh[induk]
            with Image.open(os.path.join(folder, nm)) as im:
                item['lebar'], item['tinggi'] = im.size
            daftar[kode] = item
    folder = os.path.join(HASIL, 'gerak')
    for nm in sorted(os.listdir(folder)) if os.path.isdir(folder) else []:
        kode = os.path.splitext(nm)[0]
        isi, tokoh, cocok = GERAK.get(kode, ('', '', ''))
        daftar[kode] = {'kategori': 'gerak', 'file': f'aset/gerak/{nm}', 'deskripsi': isi, 'tokoh': tokoh,
                        'cocok': cocok, 'durasi': _durasi(os.path.join(folder, nm))}
    with open(os.path.join(HASIL, 'daftar.json'), 'w', encoding='utf-8') as f:
        json.dump(daftar, f, ensure_ascii=False, indent=1)
    return len(daftar)


if __name__ == '__main__':
    pilih = sys.argv[1:] or [*POTONG, 'latar', 'gerak']
    for kat in pilih:
        if kat == 'daftar':
            continue
        n = proses_latar() if kat == 'latar' else proses_gerak() if kat == 'gerak' else proses_potong(kat)
        print(f'{kat}: {n} berkas')
    print(f'daftar.json: {buat_daftar()} aset')
