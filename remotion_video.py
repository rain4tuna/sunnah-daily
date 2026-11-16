"""Template Remotion (GAYA=remotion): motion graphic + ilustrasi SVG, dirender proyek di folder remotion/.

Antarmuka sama dengan animasi_ikon.buat_video: terima daftar segmen (dari storyboard_ikon.segmen, tiap segmen
sudah punya 'wav' hasil TTS), tulis MP4 9:16 dan kembalikan durasinya.

Video dirender PER POTONGAN lalu digabung dengan audio: render panjang sekali jalan bisa macet di mesin ber-RAM
kecil, sedangkan potongan pendek bisa diulang sendiri-sendiri.

Env (opsional): REMOTION_POTONG (frame per potong), REMOTION_KONKURENSI, REMOTION_GL (mis. angle),
REMOTION_TIMEOUT (ms), FFMPEG.
"""
import json
import math
import os
import shutil
import subprocess
import tempfile
import wave

import sfx
import stiker
import video

ROOT = os.path.dirname(os.path.abspath(__file__))
RDIR = os.path.join(ROOT, 'remotion')
FPS = 30
HANDLE = '@sun_nahdaily'
NPX = 'npx.cmd' if os.name == 'nt' else 'npx'
POTONG = int(os.environ.get('REMOTION_POTONG') or (150 if os.name == 'nt' else 300))
KONKURENSI = os.environ.get('REMOTION_KONKURENSI') or ('1' if os.name == 'nt' else '2')
GL = os.environ.get('REMOTION_GL', 'angle' if os.name == 'nt' else '')
TIMEOUT = os.environ.get('REMOTION_TIMEOUT') or '60000'   # ms; font kadang lambat dimuat saat mesin sibuk
LABEL_DALIL = {'ayat': "AL-QUR'AN", 'hadits': 'HADITS', 'atsar': 'ATSAR', 'ulama': 'PERKATAAN ULAMA'}


def log(*a):
    print(*a, flush=True)


def _ffmpeg():
    """ffmpeg sistem kalau ada; kalau tidak, ffmpeg bawaan Remotion (cukup untuk gabung & audio)."""
    if shutil.which(video.FFMPEG):
        return [video.FFMPEG]
    return [NPX, 'remotion', 'ffmpeg']


def _panjang_suara(path, cadangan):
    try:
        with wave.open(path) as w:
            return w.getnframes() / w.getframerate()
    except Exception:
        return cadangan


def susun_props(segmen):
    """Ubah segmen pipeline (sudah berisi mulai/durasi dari susun_audio) jadi props komposisi SunnahDaily."""
    hasil, no = [], 0
    dipakai = set()
    benih = segmen[0].get('judul') or segmen[0].get('ucap') or ''
    for i, s in enumerate(segmen):
        mulai, durasi = s['mulai'], s['durasi']
        suara = min(durasi, _panjang_suara(s['wav'], durasi - video.JEDA))
        b = {'jenis': s['jenis'], 'mulai': round(mulai, 3), 'akhir': round(mulai + durasi, 3),
             'ucapMulai': round(mulai + 0.1, 3), 'ucapAkhir': round(mulai + suara, 3)}
        if s.get('ilustrasi'):
            b['ilustrasi'], b['tokoh'] = s['ilustrasi'], s.get('tokoh') or ''
        if s.get('bab'):
            b['bab'] = s['bab']
        if s['jenis'] in ('hook', 'bab', 'poin', 'faedah'):
            teks = ' '.join(x for x in (s.get('narasi') or '', s['ucap']) if x)
            st = stiker.props(s['ucap'] if s['jenis'] != 'poin' else teks, s.get('ilustrasi') or '', s.get('stiker_en') or (),
                              f'{benih}|{i}', n=3, sudah=dipakai)
            # stiker muncul saat bendanya disebut; yang tidak disebut langsung menyebar rata di sepanjang suara
            for j, x in enumerate(st):
                rel = x.pop('pos')
                rel = min(rel, 0.9) if rel is not None else (j + 0.4) / (len(st) + 0.4)
                x['muncul'] = round(0.1 + rel * max(0.5, suara - 0.6), 2)
            b['stiker'] = st
        if s['jenis'] in ('hook', 'bab'):
            b.update(judul=s.get('judul') or '', narasi=s.get('narasi') or s['ucap'])
            no = 0                                  # nomor poin mulai lagi di tiap bab (video panjang)
        elif s['jenis'] == 'pembuka':
            b.update(judul=s.get('judul') or '', narasi=s['ucap'], kajian=s.get('kajian') or '')
        elif s['jenis'] == 'poin':
            no += 1
            b.update(no=no, label=s.get('label') or '', narasi=s.get('narasi') or s['ucap'])
        elif s['jenis'] == 'dalil':
            dl = s['dalil']
            ucap, terjemah = s['ucap'], dl.get('terjemah') or ''
            # teks yang menyala hanya terjemahnya; kalimat pengantar ("Allah Ta'ala berfirman, ...") dilewati
            i = ucap.find(terjemah) if terjemah else -1
            if i >= 0 and ucap:
                b['ucapMulai'] = round(mulai + suara * i / len(ucap), 3)
                b['ucapAkhir'] = round(mulai + suara * (i + len(terjemah)) / len(ucap), 3)
            derajat = dl.get('derajat') or ''
            b.update(arab=dl.get('arab') or '', terjemah=terjemah, sumber=dl.get('sumber') or '',
                     label=LABEL_DALIL.get(dl.get('jenis'), 'DALIL'),
                     derajat='' if dl.get('jenis') in ('ayat', 'ulama') or derajat == 'ayat' else derajat)
        elif s['jenis'] == 'faedah':
            b.update(narasi=s.get('narasi') or s['ucap'])
        elif s['jenis'] == 'ajak':
            b.update(narasi=s['ucap'])
        elif s['jenis'] in ('kuis', 'jawab'):
            b.update(narasi=s['ucap'], tanya=s.get('tanya') or '', pilihan=s.get('pilihan') or [], jawab=s.get('jawab', -1))
        else:
            kredit = (s.get('kredit') or '').split('\n')
            b.update(ajakan=s.get('ajakan') or '', kredit=kredit[0], ustadz=kredit[1] if len(kredit) > 1 else '')
        hasil.append(b)
    total = segmen[-1]['mulai'] + segmen[-1]['durasi']
    # 'frame' dikirim eksplisit: menghitung ulang dari detik di sisi Remotion bisa selisih satu frame karena pembulatan
    return {'kicker': segmen[0].get('kicker') or 'SUNNAH DAILY', 'handle': HANDLE, 'durasi': round(total, 3),
            'frame': math.ceil(total * FPS), 'segmen': hasil}


def _remotion(args, batas=900):
    r = subprocess.run([NPX, 'remotion', *args], cwd=RDIR, capture_output=True, text=True, encoding='utf-8',
                       errors='replace', timeout=batas)
    return r.returncode, (r.stdout or '') + (r.stderr or '')


def buat_video(segmen, tema, out_mp4, contoh_jpg=None, komposisi='SunnahDaily', props_tambahan=None, potong=None,
               skala_cuplikan=0.34, frame_cuplikan=1.5, public_dir=None):
    """komposisi/props_tambahan/potong dipakai video panjang 16:9 (video_panjang.py); default = Shorts."""
    if not os.path.isdir(os.path.join(RDIR, 'node_modules')):
        raise RuntimeError('Remotion belum terpasang: jalankan "npm ci" di folder remotion/.')
    out_mp4 = os.path.abspath(out_mp4)
    with tempfile.TemporaryDirectory() as tmp:
        wav = os.path.join(tmp, 'suara.wav')
        total = video.susun_audio(segmen, wav, tmp)
        isi = {**susun_props(segmen), **(props_tambahan(segmen) if props_tambahan else {})}
        try:
            n_sfx = sfx.campur(wav, isi, komposisi)
            if n_sfx:
                log(f'   SFX: {n_sfx} efek dipasang')
        except Exception as e:                  # efek suara hanya hiasan: gagal -> narasi saja
            log(f'   SFX dilewati: {e}')
        props = os.path.join(tmp, 'props.json')
        with open(props, 'w', encoding='utf-8') as f:
            json.dump(isi, f, ensure_ascii=False)
        umum = ['src/index.ts', komposisi, f'--props={props}', '--log=error', f'--timeout={TIMEOUT}',
                f'--concurrency={KONKURENSI}'] + ([f'--gl={GL}'] if GL else []) +                ([f'--public-dir={public_dir}'] if public_dir else [])
        n = math.ceil(total * FPS)
        daftar = os.path.join(tmp, 'daftar.txt')
        with open(daftar, 'w', encoding='utf-8') as lst:
            langkah = potong or POTONG
            for i, a in enumerate(range(0, n, langkah)):
                b = min(a + langkah, n) - 1
                pot = os.path.join(tmp, f'p{i:03d}.mp4')
                for coba in range(3):
                    try:
                        kode, keluaran = _remotion(['render', *umum, pot, f'--frames={a}-{b}', '--muted', '--codec=h264',
                                                    '--crf=21'])
                    except subprocess.TimeoutExpired:
                        kode, keluaran = 1, 'melewati batas waktu'
                    if kode == 0 and os.path.exists(pot) and os.path.getsize(pot) > 0:
                        break
                    log(f'   Remotion potong {i} ({a}-{b}) percobaan {coba + 1} gagal: {keluaran.strip()[-300:]}')
                else:
                    raise RuntimeError(f'Remotion gagal merender frame {a}-{b}')
                log(f'   Remotion {b + 1}/{n} frame')
                lst.write(f"file '{pot.replace(os.sep, '/')}'\n")
        # Encode ulang ke yuv420p rentang standar (tv), format paling aman untuk IG/FB/YouTube; berkas juga jadi
        # sekitar separuhnya.
        subprocess.run([*_ffmpeg(), '-y', '-loglevel', 'error', '-f', 'concat', '-safe', '0', '-i', daftar, '-i', wav,
                        '-map', '0:v', '-map', '1:a',
                        '-vf', 'scale=out_range=tv:out_color_matrix=bt709,format=yuv420p',
                        '-c:v', 'libx264', '-preset', 'veryfast', '-crf', '23', '-profile:v', 'high',
                        '-color_range', 'tv', '-colorspace', 'bt709', '-color_primaries', 'bt709', '-color_trc', 'bt709',
                        '-c:a', 'aac', '-b:a', '160k', '-shortest', '-movflags', '+faststart', out_mp4],
                       check=True, cwd=RDIR)
        if contoh_jpg:
            try:
                _remotion(['still', *umum, os.path.abspath(contoh_jpg), f'--frame={min(n - 1, int(frame_cuplikan * FPS))}',
                           '--image-format=jpeg', f'--scale={skala_cuplikan}'], batas=180)
            except Exception as e:
                log(f'   cuplikan dilewati: {e}')
    return total
