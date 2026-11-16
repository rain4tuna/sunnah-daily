"""Video YouTube panjang 16:9: satu episode Sirah utuh (semua kisah yang lolos verifikasi) jadi satu video.

Alur: pembuka episode -> tiap kisah jadi satu "pelajaran" (bab: pengantar, poin, dalil, faedah) -> penutup.
Storyboard tiap kisah memakai storyboard_ikon (yang sudah tersimpan dipakai ulang, jadi isinya sama dengan Shorts);
dalil tetap dari data kisah yang sudah diverifikasi (sumber + nomor + derajat). Render lewat komposisi Remotion
"SunnahClay" (remotion/src/Clay.tsx, aset clay dari remotion/public_panjang/aset, dipilih adegan_clay.py) atau
"SunnahPanjang" (remotion/src/Panjang.tsx, ilustrasi SVG). Status kisah dan data episode TIDAK diubah.

Env:
  GEMINI_API_KEY      wajib (TTS; storyboard hanya kalau kisah belum punya storyboard_ikon)
  EPISODE             nomor episode Sirah (wajib)
  SUARA_PANJANG       voice Gemini TTS (default Charon); GAYA_SUARA_PANJANG = gaya bacanya
  MAKS_KISAH          batasi jumlah kisah (untuk uji cepat; kosong = semua)
  OUT_DIR             folder hasil (default hasil)
  GAYA_PANJANG        clay (default) | svg
  PRATINJAU           true = tanpa TTS: durasi ditaksir dari jumlah kata, tulis props contoh untuk Remotion Studio

Hasil di OUT_DIR: epXXX_panjang.mp4, _cuplikan.jpg (thumbnail kasar), _deskripsi.txt (deskripsi + chapter YouTube).
"""
import json
import os
import re
import sys
import tempfile

import ekstrak
import gemini
import main
import remotion_video
import adegan_clay
import storyboard_ikon

ROOT = os.path.dirname(os.path.abspath(__file__))
URUTAN = ['pertama', 'kedua', 'ketiga', 'keempat', 'kelima', 'keenam', 'ketujuh', 'kedelapan', 'kesembilan', 'kesepuluh',
          'kesebelas', 'kedua belas']
USTADZ = 'Ust. Dr. Firanda Andirja, M.A.'
GAYA_SUARA = ('narator laki-laki dewasa yang tenang, hangat dan berwibawa, seperti membawakan kajian kisah; '
              'tempo sedang cenderung pelan, jeda wajar antar kalimat, intonasi mengalir, tidak terburu-buru')


def log(*a):
    print(*a, flush=True)


def muat_episode(no):
    path = os.path.join(ekstrak.DIR, f'ep{int(no):03d}.json')
    if not os.path.exists(path):
        raise SystemExit(f'Data episode {no} belum ada ({path}); jalankan ekstraksi dulu.')
    with open(path, encoding='utf-8') as f:
        return json.load(f)


def judul_pendek(judul):
    m = re.match(r'.*?#\s*\d+\s*-\s*(.+)', judul or '')
    return m.group(1).strip() if m else (judul or '')


def nomor_ep(data):
    m = re.match(r'.*?#\s*(\d+)', data.get('judul') or '')
    return int(m.group(1)) if m else int(data.get('episode') or 0)


def susun_segmen(data, kisah):
    no_ep = nomor_ep(data)
    kicker = f'SIRAH NABAWIYAH #{no_ep:02d}'
    topik = judul_pendek(data['judul'])
    n = len(kisah)
    segmen = [{'jenis': 'pembuka', 'judul': topik, 'kajian': f'Faedah dari kajian Sirah Nabawiyah #{no_ep} · {USTADZ}',
               'ucap': (f'Bismillah. Di video ini kita akan menyimak {n} pelajaran dari kajian Sirah Nabawiyah '
                        f'bagian ke-{no_ep}, tentang {topik}, yang disampaikan oleh Ustadz Doktor Firanda Andirja.')}]
    for i, k in enumerate(kisah, 1):
        bagian = storyboard_ikon.segmen(k, kicker, main.narasi_dalil)
        bagian = [s for s in bagian if s['jenis'] != 'penutup']
        for s in bagian:
            s['bab'] = i
            if s['jenis'] == 'hook':
                s['jenis'] = 'bab'
                s['ucap'] = f"Pelajaran {URUTAN[i - 1] if i <= len(URUTAN) else f'ke-{i}'}. {s['ucap']}"
        segmen += bagian
    segmen.append({'jenis': 'penutup', 'ajakan': 'Subscribe & bagikan, semoga jadi amal jariyah',
                   'kredit': f"Faedah dari kajian {data['judul']}\n{USTADZ}",
                   'ucap': ('Semoga bermanfaat. Kajian lengkapnya bisa disimak di channel Ustadz Firanda Andirja, '
                            'tautannya ada di deskripsi. Jangan lupa subscribe Sunnah Daily, dan bagikan video ini, '
                            'semoga menjadi amal jariyah untuk kita semua.')})
    for s in segmen:
        s['kicker'] = kicker
    return segmen


def daftar_bab(segmen, kisah):
    return [{'no': s['bab'], 'judul': kisah[s['bab'] - 1]['judul_hook'], 'mulai': round(s['mulai'], 3)}
            for s in segmen if s['jenis'] == 'bab']


def jam(detik):
    d = int(detik)
    return f'{d // 3600}:{d // 60 % 60:02d}:{d % 60:02d}' if d >= 3600 else f'{d // 60}:{d % 60:02d}'


def deskripsi(data, kisah, segmen):
    bab = daftar_bab(segmen, kisah)
    penutup = next(s for s in segmen if s['jenis'] == 'penutup')
    chapter = ['0:00 Pembuka'] + [f"{jam(b['mulai'])} {b['no']}. {b['judul']}" for b in bab] + [f"{jam(penutup['mulai'])} Penutup"]
    dalil = []
    for i, k in enumerate(kisah, 1):
        dl = k['dalil']
        derajat = f" · {dl['derajat'].capitalize()}" if dl.get('jenis') in ('hadits', 'atsar') and dl.get('derajat') else ''
        if dl.get('derajat') == 'lemah':
            derajat += ' (lemah, bukan dalil)'
        dalil.append(f"{i}. {dl['sumber']}{derajat}")
    return (f"{data['judul']} | {len(kisah)} pelajaran dalam satu video\n\n"
            f"Ringkasan faedah dari kajian {data['judul']} oleh {USTADZ}\n"
            f"Kajian lengkap: {data['url']}\n\n"
            'Daftar isi:\n' + '\n'.join(chapter) + '\n\n'
            'Dalil yang disebutkan:\n' + '\n'.join(dalil) + '\n\n'
            '#sirahnabawiyah #kisahnabi #sunnahdaily #kajianislam #firandaandirja')


def taksir_durasi(segmen, tmp):
    """Pratinjau tanpa TTS: wav hening sepanjang taksiran (2,3 kata/detik)."""
    import wave
    for i, s in enumerate(segmen):
        dur = max(3.0, len(main.lisan(s['ucap']).split()) / 2.3)
        s['wav'] = os.path.join(tmp, f'h{i}.wav')
        with wave.open(s['wav'], 'wb') as w:
            w.setnchannels(1)
            w.setsampwidth(2)
            w.setframerate(24000)
            w.writeframes(b'\0\0' * int(dur * 24000))


def jalankan():
    out = os.environ.get('OUT_DIR', 'hasil')
    os.makedirs(out, exist_ok=True)
    no = os.environ.get('EPISODE') or ''
    if not no.strip():
        raise SystemExit('EPISODE wajib diisi.')
    data = muat_episode(no)
    kisah = [k for k in data['kisah'] if k.get('layak')]
    maks = os.environ.get('MAKS_KISAH')
    if maks:
        kisah = kisah[:int(maks)]
    if not kisah:
        raise SystemExit('Tidak ada kisah yang lolos verifikasi di episode ini.')
    log(f"Episode: {data['judul']} — {len(kisah)} kisah: " + ', '.join(k['id'] for k in kisah))
    segmen = susun_segmen(data, kisah)
    log(f'   {len(segmen)} babak')
    gemini.SUARA = os.environ.get('SUARA_PANJANG') or 'Charon'
    gemini.GAYA_SUARA = os.environ.get('GAYA_SUARA_PANJANG') or GAYA_SUARA
    nama = f"ep{nomor_ep(data):03d}_panjang"
    pratinjau = os.environ.get('PRATINJAU', '').lower() == 'true'

    clay = (os.environ.get('GAYA_PANJANG') or 'clay').lower() == 'clay'
    komposisi = 'SunnahClay' if clay else 'SunnahPanjang'

    def tambahan(sg):
        t = {'judul': judul_pendek(data['judul']), 'bab': daftar_bab(sg, kisah)}
        if clay:
            t['adegan'] = adegan_clay.pilih(sg, benih=nama)
        return t

    with tempfile.TemporaryDirectory() as tmp:
        if pratinjau:
            taksir_durasi(segmen, tmp)
            t = 0.0
            for s in segmen:                     # sama dengan video.susun_audio, tanpa ffmpeg
                s['mulai'] = t
                s['durasi'] = remotion_video._panjang_suara(s['wav'], 3) + remotion_video.video.JEDA
                if s['jenis'] == 'dalil':
                    s['durasi'] = max(s['durasi'], 6.0)
                t += s['durasi']
            props = {**remotion_video.susun_props(segmen), **tambahan(segmen)}
            tujuan = os.path.join(remotion_video.RDIR, 'src', 'contoh_clay.json' if clay else 'contoh_panjang.json')
            with open(tujuan, 'w', encoding='utf-8') as f:
                json.dump(props, f, ensure_ascii=False, indent=1)
            log(f"Pratinjau {props['durasi']:.0f} detik (taksiran) -> {tujuan}")
            return
        log(f'   suara: {gemini.SUARA}')
        for i, s in enumerate(segmen):
            s['wav'] = os.path.join(tmp, f'suara{i:03d}.wav')
            log(f'   TTS {i + 1}/{len(segmen)}')
            gemini.bacakan(main.lisan(s['ucap']), s['wav'])
        mp4 = os.path.join(out, f'{nama}.mp4')
        durasi = remotion_video.buat_video(
            segmen, 'malam', mp4, os.path.join(out, f'{nama}_cuplikan.jpg'), komposisi=komposisi,
            props_tambahan=tambahan, potong=int(os.environ.get('REMOTION_POTONG_PANJANG') or 600),
            skala_cuplikan=0.5, frame_cuplikan=4, public_dir='public_panjang' if clay else None)
    log(f'Video {durasi / 60:.1f} menit -> {mp4}')
    teks = deskripsi(data, kisah, segmen)
    with open(os.path.join(out, f'{nama}_deskripsi.txt'), 'w', encoding='utf-8') as f:
        f.write(teks)
    log('\n' + teks)


if __name__ == '__main__':
    try:
        jalankan()
    except SystemExit:
        raise
    except Exception as e:
        import traceback
        traceback.print_exc()
        print(f'::error::{type(e).__name__}: {str(e)[:900]}')
        sys.exit(1)
