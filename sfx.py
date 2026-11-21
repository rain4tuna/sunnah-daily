"""Efek suara (SFX) untuk video Remotion: Shorts (SunnahDaily) dan video panjang (SunnahClay/SunnahPanjang).

Sumber suara: SFX Kit by Wyzowl (CC0, https://github.com/wyzowl/sfx-kit), disalin ke folder sfx/ sebagai WAV 24 kHz
mono 16-bit (sama dengan audio narasi dari video.susun_audio). Yang dipakai hanya efek NON-MUSIK (whoosh, pop, klik,
langkah, lembar kitab, detak jam, centang, konfeti); nada, jingle, denting, dan alat musik tidak dipakai.

Isyarat (kapan suara diputar) dihitung dari props komposisi yang sama dengan yang dirender, jadi selalu pas dengan
animasinya: perpindahan adegan, stiker/tokoh/properti muncul, tombol like/subscribe ditekan, hitung mundur kuis,
jawaban benar. Suara diletakkan di (momen - titik_sinkron) seperti panduan SFX Kit, dan dikecilkan saat menimpa ucapan.

Env: SFX=0 mematikan semua efek; SFX_GAIN_DB menggeser kerasnya semua efek (default 0).
Kalau ada yang gagal, video tetap jadi dengan narasi saja (pemanggil menangkap pengecualiannya).
"""
import array
import json
import os
import wave

ROOT = os.path.dirname(os.path.abspath(__file__))
DIR = os.path.join(ROOT, 'sfx')
FPS = 30


def aktif():
    return os.environ.get('SFX', '1').strip().lower() not in ('0', 'false', 'tidak', 'off')


def _data():
    with open(os.path.join(DIR, 'data.json'), encoding='utf-8') as f:
        return json.load(f)['suara']


def _cari_segmen(segmen, t):
    for s in segmen:
        if s['mulai'] <= t < s['akhir']:
            return s
    return None


def isyarat(props, komposisi='SunnahDaily'):
    """Daftar (detik_momen, id_suara, db, maks_detik) dari props yang dikirim ke Remotion."""
    segmen = props.get('segmen') or []
    adegan = props.get('adegan') or []
    clay = komposisi == 'SunnahClay'
    kaya = komposisi == 'SunnahMotion'
    panjang = komposisi not in ('SunnahDaily', 'SunnahMotion')
    hasil = []

    def tambah(t, sid, db=0.0, maks=None):
        hasil.append((t, sid, db, maks))

    for i, s in enumerate(segmen):
        m, jenis = s['mulai'], s['jenis']
        # --- perpindahan adegan
        if i == 0:
            tambah(m + 0.15, 'pop-medium-in', -2)
        elif jenis == 'dalil':
            tambah(m + 0.05, 'props-page-turn', 0)
        elif jenis in ('bab', 'pembuka', 'kuis'):
            tambah(m, 'whoosh-medium-medium', -2)
        else:
            tambah(m, 'whoosh-medium-soft' if panjang else 'whoosh-fast-soft', 0)
        # --- stiker (Shorts & gaya SVG; gaya clay tidak menampilkan stiker): muncul memantul
        for x in ([] if clay else s.get('stiker') or []):
            if x.get('muncul') is not None:
                tambah(m + float(x['muncul']) + 0.05, 'pop-small-in', -3)
        # --- template SunnahMotion: efek foley non-musik tambahan untuk properti, langkah, dan CTA visual
        if kaya:
            if jenis in ('hook', 'poin', 'faedah'):
                tambah(m + 0.22, 'pop-medium-bubble', -6)
            if s.get('tokoh') == 'berjalan':
                for f in range(6, 48, 10):
                    tambah(m + f / FPS, 'impact-light-soft', -10)
            if jenis == 'faedah':
                tambah(m + 28 / FPS, 'pop-small-in', -4)
            if jenis == 'penutup':
                tambah(m + 14 / FPS, 'click-mouse-firm', -4)
        # --- tokoh & properti clay
        a = adegan[i] if clay and i < len(adegan) and isinstance(adegan[i], dict) else {}
        if jenis not in ('dalil',):
            for ke, tk in enumerate(a.get('tokoh') or []):
                awal = (6 + ke * 10) / FPS
                if tk.get('dari') and tk.get('jalan'):
                    # langkah kecil tiap kali kaki menapak (pantulan menyentuh tanah tiap 7 frame selama 54 frame)
                    for f in range(0, 54, 7):
                        tambah(m + awal + f / FPS, 'impact-light-soft', -9 - (ke * 3) - (2 if (f // 7) % 2 else 0))
                else:
                    tambah(m + awal + 0.1, 'pop-medium-in', -7)
            for ke, b in enumerate(a.get('benda') or []):
                muncul = b.get('muncul')
                muncul = float(muncul) if muncul is not None else 0.8 + ke * 0.5
                tambah(m + muncul + 0.08, 'pop-medium-bubble', -4)
        # --- ajakan like & subscribe: tombol muncul (frame 8, 16) lalu ditekan (frame 40, 64)
        if jenis == 'ajak':
            for f in (8, 16):
                tambah(m + f / FPS + 0.08, 'pop-medium-in', -3)
            for f in (40, 64):
                tambah(m + f / FPS, 'click-mouse-firm', 0)
        # --- kuis: pilihan masuk bergiliran, lalu detak jam selama hitung mundur 5 detik terakhir
        if jenis == 'kuis':
            for k in range(len(s.get('pilihan') or [])):
                tambah(m + (14 + k * 8) / FPS + 0.1, 'pop-small-in', -3)
            akhir = s['akhir']
            if akhir - s.get('ucapAkhir', akhir) >= 4.5:
                tambah(akhir - 5.0, 'time-clock', 0, 3.0)
                tambah(akhir - 2.0, 'time-clock', 0, 2.0)
        # --- jawaban benar: centang lalu konfeti
        if jenis == 'jawab':
            tambah(m + 0.12, 'writing-marker-tick', 0)
            tambah(m + 0.2, 'celebration-confetti', -2)
    return sorted(hasil)


def _muat(sid, cache):
    if sid not in cache:
        with wave.open(os.path.join(DIR, f'{sid}.wav')) as w:
            cache[sid] = (array.array('h', w.readframes(w.getnframes())), w.getframerate())
    return cache[sid]


def campur(wav, props, komposisi='SunnahDaily'):
    """Campurkan SFX ke WAV narasi (ditimpa di tempat). Kembalikan jumlah efek yang dipasang."""
    if not aktif():
        return 0
    data = _data()
    with wave.open(wav) as w:
        p = w.getparams()
        suara = array.array('h', w.readframes(w.getnframes()))
    if p.sampwidth != 2 or p.nchannels != 1:
        raise ValueError('narasi harus WAV mono 16-bit')
    rate, n = p.framerate, len(suara)
    geser_db = float(os.environ.get('SFX_GAIN_DB') or 0)
    segmen = props.get('segmen') or []
    cache, dipasang = {}, 0
    for t, sid, db, maks in isyarat(props, komposisi):
        info = data.get(sid)
        if not info:
            continue
        sampel, r = _muat(sid, cache)
        if r != rate:
            raise ValueError(f'rate SFX {r} != narasi {rate}')
        # dikecilkan bila jatuh di tengah ucapan supaya suara narator tetap jelas
        s = _cari_segmen(segmen, t)
        if s and s.get('ucapMulai', 0) - 0.1 <= t <= s.get('ucapAkhir', 0):
            db += info.get('bawah_suara_db', 0)
        gain = 10 ** ((db + geser_db) / 20)
        mulai = int(round((t - info['sync']) * rate))
        potong = -mulai if mulai < 0 else 0
        akhir_src = len(sampel) if maks is None else min(len(sampel), int(maks * rate))
        pudar = int(0.03 * rate) if maks is not None and akhir_src < len(sampel) else 0
        for j in range(potong, akhir_src):
            k = mulai + j
            if k >= n:
                break
            g = gain if not pudar or j < akhir_src - pudar else gain * (akhir_src - j) / pudar
            v = suara[k] + int(sampel[j] * g)
            suara[k] = 32767 if v > 32767 else (-32768 if v < -32768 else v)
        dipasang += 1
    with wave.open(wav, 'wb') as w:
        w.setparams(p)
        w.writeframes(suara.tobytes())
    return dipasang
