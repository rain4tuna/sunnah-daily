"""Video YouTube panjang 16:9: satu episode Sirah utuh (semua kisah yang lolos verifikasi) jadi satu video.

Alur: pembuka episode -> tiap kisah jadi satu "pelajaran" (bab: pengantar, poin, dalil, faedah) -> penutup.
Storyboard tiap kisah memakai storyboard_ikon (yang sudah tersimpan dipakai ulang, jadi isinya sama dengan Shorts);
dalil tetap dari data kisah yang sudah diverifikasi (sumber + nomor + derajat). Render lewat komposisi Remotion
"SunnahClay" (remotion/src/Clay.tsx, aset clay dari remotion/public_panjang/aset, dipilih adegan_clay.py) atau
"SunnahPanjang" (remotion/src/Panjang.tsx, ilustrasi SVG). Status kisah dan data episode TIDAK diubah.

Env:
  GEMINI_API_KEY      wajib (TTS; storyboard hanya kalau kisah belum punya storyboard_ikon)
  EPISODE             nomor episode Sirah (wajib)
  SUARA_PANJANG       voice Gemini TTS (default Laomedeia untuk naskah anak, Charon untuk asli); GAYA_SUARA_PANJANG = gaya baca
  MAKS_KISAH          batasi jumlah kisah (untuk uji cepat; kosong = semua)
  OUT_DIR             folder hasil (default hasil)
  GAYA_PANJANG        clay (default) | svg
  GAYA_NASKAH         anak (default: naskah ceria + ajakan + kuis, naskah_anak.py) | asli
  PRATINJAU           true = tanpa TTS: durasi ditaksir dari jumlah kata, tulis props contoh untuk Remotion Studio

Hasil di OUT_DIR: epXXX_panjang.mp4, _cuplikan.jpg (thumbnail kasar), _deskripsi.txt (deskripsi + chapter YouTube).
"""
import hashlib
import json
import os
import re
import shutil
import sys
import tempfile

import ekstrak
import gemini
import main
import remotion_video
import adegan_clay
import naskah_anak
import storyboard_ikon
import tts_kelompok

ROOT = os.path.dirname(os.path.abspath(__file__))
URUTAN = ['pertama', 'kedua', 'ketiga', 'keempat', 'kelima', 'keenam', 'ketujuh', 'kedelapan', 'kesembilan', 'kesepuluh',
          'kesebelas', 'kedua belas']
USTADZ = 'Ust. Dr. Firanda Andirja, M.A.'
# Cache naskah anak & suara per babak (dipulihkan/disimpan workflow lewat actions/cache): render yang gagal bisa
# diulang tanpa memakai kuota TTS lagi.
CACHE = os.environ.get('CACHE_PANJANG') or ''
GAYA_SUARA = ('narator laki-laki dewasa yang tenang, hangat dan berwibawa, seperti membawakan kajian kisah; '
              'tempo sedang cenderung pelan, jeda wajar antar kalimat, intonasi mengalir, tidak terburu-buru')


# Singkat: instruksi gaya yang panjang pernah ikut terbaca oleh TTS. Tempo dibuat lincah (video ±3 menit).
GAYA_SUARA_ANAK = ('pendongeng ceria untuk anak, ekspresif, tempo cepat dan lincah, jeda antar kalimat singkat; '
                   'tenang dan hormat saat membacakan ayat')


def contoh_naskah(k):
    """Pratinjau tanpa Gemini: storyboard asli + soal kuis CONTOH (bukan untuk tayang)."""
    sb = k['storyboard_ikon']
    return {'bab': sb['hook']['narasi'], 'poin': [{'narasi': p['narasi'], 'label': p.get('label') or ''} for p in sb['poin']],
            'faedah': f"Pelajaran buat kita: {k['faedah']}",
            'kuis': {'tanya': '(Contoh tampilan) Soal kuis dari Gemini akan muncul di sini?',
                     'pilihan': ['Pilihan pertama', 'Pilihan kedua', 'Pilihan ketiga'], 'jawab': 0}}


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


def susun_segmen(data, kisah, anak=False, naskah=None, dual_cta=False):
    """anak=True: naskah ceria (naskah_anak.py) + ajakan like/subscribe di tengah + kuis sebelum penutup.
    dual_cta=True (MODE_MONET): 2 titik ajakan untuk video 8+ menit (unlock mid-roll ads YouTube).
    naskah = {id_kisah: hasil naskah_anak.tulis_ulang}; kisah yang tidak punya naskah memakai storyboard asli."""
    no_ep = nomor_ep(data)
    kicker = f'SIRAH NABAWIYAH #{no_ep:02d}'
    topik = judul_pendek(data['judul'])
    n = len(kisah)
    if anak:
        return _susun_anak(data, kisah, naskah or {}, kicker, topik, no_ep, dual_cta=dual_cta)
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


def _pancing(naskah, kisah):
    """Kalimat penggoda pembuka: pancingan kisah pertama (Gemini), atau pertanyaan pembuka babnya."""
    nk = naskah.get(kisah[0]['id']) or {}
    return nk.get('pancing') or nk.get('bab')


def _susun_anak(data, kisah, naskah, kicker, topik, no_ep, dual_cta=False):
    n = len(kisah)
    segmen = [{'jenis': 'pembuka', 'judul': topik, 'kajian': f'Kisah dari kajian Sirah Nabawiyah #{no_ep} · {USTADZ}',
               'ucap': naskah_anak.pembuka(n, topik, no_ep, _pancing(naskah, kisah))}]
    # Dual CTA strategy (/claude-youtube retention-scripting-guide): ~1 min (bab 2) & ~4 min (bab ~2/3) saat MODE_MONET
    if dual_cta and n >= 5:
        titik_ajak = {max(1, n // 3), max(2, (2 * n) // 3)}
    else:
        titik_ajak = {(n + 1) // 2} if n >= 3 else set()
    for i, k in enumerate(kisah, 1):
        bagian = [s for s in storyboard_ikon.segmen(k, kicker, main.narasi_dalil) if s['jenis'] != 'penutup']
        nk = naskah.get(k['id'])
        poin = iter((nk or {}).get('poin') or [])
        for s in bagian:
            s['bab'] = i
            if s['jenis'] == 'hook':
                s['jenis'] = 'bab'
                pembuka_bab = nk['bab'] if nk else s['ucap']
                s['ucap'] = f"Kisah {URUTAN[i - 1] if i <= len(URUTAN) else f'ke-{i}'}! {pembuka_bab}"
            elif s['jenis'] == 'poin' and nk:
                p = next(poin, None)             # poin naskah habis -> narasi storyboard asli tetap dipakai
                if p:
                    s['narasi'] = s['ucap'] = p['narasi']
                    s['label'] = p['label'] or s.get('label')
            elif s['jenis'] == 'faedah' and nk:
                s['narasi'] = s['ucap'] = nk['faedah']
        segmen += bagian
        if i in titik_ajak:
            segmen.append({'jenis': 'ajak', 'bab': i, 'ucap': naskah_anak.AJAK})
    kuis = next((naskah[k['id']] for k in reversed(kisah) if (naskah.get(k['id']) or {}).get('kuis')), None)
    if kuis:
        segmen.append({'jenis': 'kuis', 'bab': n, 'ucap': naskah_anak.kuis(kuis), 'tahan': 5.0, **kuis['kuis']})
        segmen.append({'jenis': 'jawab', 'bab': n, 'ucap': naskah_anak.jawab(kuis), **kuis['kuis']})
    segmen.append({'jenis': 'penutup', 'ajakan': 'Like, subscribe & ajak temanmu nonton!',
                   'kredit': f"Kisah dari kajian {data['judul']}\n{USTADZ}", 'ucap': naskah_anak.PENUTUP})
    for s in segmen:
        s['kicker'] = kicker
    return segmen


def kelompok_tts(segmen):
    """Indeks babak per permintaan TTS: satu kelompok per kisah (bab..faedah, plus ajakan bila ada), pembuka sendiri,
    kuis + jawaban + penutup satu kelompok. Maksimal 8 babak per kelompok supaya teks tidak terlalu panjang."""
    kelompok, kini, kunci = [], [], None
    for i, s in enumerate(segmen):
        k = 'akhir' if s['jenis'] in ('kuis', 'jawab', 'penutup') else ('awal' if s['jenis'] == 'pembuka' else s.get('bab'))
        if kini and (k != kunci or len(kini) >= 8):
            kelompok.append(kini)
            kini = []
        kini.append(i)
        kunci = k
    if kini:
        kelompok.append(kini)
    return kelompok


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


KATA_PER_DETIK = float(os.environ.get('KATA_PER_DETIK') or 2.0)


def taksiran_detik(segmen):
    """Taksiran durasi sebelum TTS (KATA_PER_DETIK + jeda + tahan kuis; dalil minimal 6 detik).
    Run 9: taksiran 2,3 kata/detik = 156 detik, nyatanya 228 detik."""
    t = 0.0
    for s in segmen:
        d = max(3.0, len(main.lisan(s['ucap']).split()) / KATA_PER_DETIK) + 0.35
        if s['jenis'] == 'dalil':
            d = max(d, 6.0)
        t += d + (s.get('tahan') or 0)
    return t


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
    # video pendek ±3 menit: 2-3 kisah. PILIH_KISAH="1,6" memilih kisah tertentu (urutan kisah yang layak, mulai 1).
    pilih = [int(x) for x in re.findall(r'\d+', os.environ.get('PILIH_KISAH') or '')]
    if pilih:
        kisah = [kisah[i - 1] for i in pilih if 0 < i <= len(kisah)]
    mode_monet = os.environ.get('MODE_MONET', '').strip().lower() == 'true'
    # MODE_MONET=true (/claude-youtube): target 8.5-10 menit (unlock mid-roll ads +50% RPM, dual CTA)
    maks_default = '8' if mode_monet else ('3' if (os.environ.get('GAYA_NASKAH') or 'anak').lower() == 'anak' else '')
    maks = os.environ.get('MAKS_KISAH') or maks_default
    if maks:
        kisah = kisah[:int(maks)]
    if not kisah:
        raise SystemExit('Tidak ada kisah yang lolos verifikasi di episode ini.')
    log(f"Episode: {data['judul']} — {len(kisah)} kisah (monet={mode_monet}): " + ', '.join(k['id'] for k in kisah))
    nama = f"ep{nomor_ep(data):03d}_panjang"
    pratinjau = os.environ.get('PRATINJAU', '').lower() == 'true'
    anak = (os.environ.get('GAYA_NASKAH') or 'anak').lower() == 'anak'
    naskah = {}
    if anak:
        for k in kisah:
            if pratinjau and not k.get('storyboard_ikon'):
                k['storyboard_ikon'] = storyboard_ikon.rapikan({}, k, 'kisah')   # tanpa Gemini
            # v3: naskah pendek + kalimat pancingan pembuka; naskah lama di cache tidak dipakai lagi
            simpan = os.path.join(CACHE, f"naskah_v3_{k['id']}.json") if CACHE and not pratinjau else ''
            lama = None
            if simpan and os.path.exists(simpan):
                with open(simpan, encoding='utf-8') as f:
                    lama = json.load(f)
                # storyboard dibuat Gemini dan tidak tersimpan di data kisah: pakai storyboard yang sama dengan naskahnya
                if lama.get('storyboard') and not k.get('storyboard_ikon'):
                    k['storyboard_ikon'] = lama['storyboard']
            storyboard_ikon.buat(k)              # storyboard tersimpan dipakai; yang belum ada dibuat (Gemini)
            if lama and len(lama.get('poin') or []) == len(k['storyboard_ikon'].get('poin') or []):
                naskah[k['id']] = lama
                log(f"   naskah anak {k['id']} dari cache")
                continue
            if lama:
                log(f"   naskah anak {k['id']} di cache tidak cocok dengan storyboard, ditulis ulang")
            naskah[k['id']] = contoh_naskah(k) if pratinjau else naskah_anak.tulis_ulang(k)
            if simpan and naskah[k['id']]:
                os.makedirs(CACHE, exist_ok=True)
                with open(simpan, 'w', encoding='utf-8') as f:
                    json.dump({**naskah[k['id']], 'storyboard': k['storyboard_ikon']}, f, ensure_ascii=False)
        log('   naskah anak: ' + ', '.join(f"{i}={'ok' if v else 'asli'}" for i, v in naskah.items()))
        with open(os.path.join(out, f'{nama}_naskah.json'), 'w', encoding='utf-8') as f:
            json.dump(naskah, f, ensure_ascii=False, indent=1)
    segmen = susun_segmen(data, kisah, anak=anak, naskah={i: v for i, v in naskah.items() if v}, dual_cta=mode_monet)
    # jaga durasi: ±3 menit untuk mode anak standar, atau ±9 menit (540 detik, di atas ambang 8 menit mid-roll) saat MODE_MONET
    target = float(os.environ.get('DURASI_TARGET') or (560 if mode_monet else (185 if anak else 0)))
    while target and len(kisah) > 2 and taksiran_detik(segmen) > target:
        log(f'   taksiran {taksiran_detik(segmen):.0f} detik > {target:.0f}: kisah {kisah[-1]["id"]} dilepas')
        kisah = kisah[:-1]
        segmen = susun_segmen(data, kisah, anak=anak, naskah={i: v for i, v in naskah.items() if v}, dual_cta=mode_monet)
    log(f'   {len(segmen)} babak, {len(kisah)} kisah, taksiran {taksiran_detik(segmen):.0f} detik')
    gemini.SUARA = os.environ.get('SUARA_PANJANG') or ('Laomedeia' if anak else 'Charon')
    gemini.GAYA_SUARA = os.environ.get('GAYA_SUARA_PANJANG') or (GAYA_SUARA_ANAK if anak else GAYA_SUARA)

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
                s['durasi'] += s.get('tahan') or 0
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
        def kunci(i):
            teks = '|'.join((gemini.SUARA, gemini.GAYA_SUARA, main.lisan(segmen[i]['ucap'])))
            return os.path.join(CACHE, 'tts_' + hashlib.sha1(teks.encode('utf-8')).hexdigest()[:20] + '.wav')

        kelompok = kelompok_tts(segmen)
        dipakai = 0
        for j, kel in enumerate(kelompok, 1):
            if CACHE and all(os.path.exists(kunci(i)) for i in kel):
                for i in kel:
                    shutil.copyfile(kunci(i), segmen[i]['wav'])
                log(f'   TTS kelompok {j}/{len(kelompok)} ({len(kel)} babak) dari cache')
                continue
            log(f'   TTS kelompok {j}/{len(kelompok)} ({len(kel)} babak)')
            dipakai += tts_kelompok.bacakan_kelompok([main.lisan(segmen[i]['ucap']) for i in kel],
                                                     [segmen[i]['wav'] for i in kel], tmp, nama=f'k{j:02d}')
            if CACHE:
                os.makedirs(CACHE, exist_ok=True)
                for i in kel:
                    shutil.copyfile(segmen[i]['wav'], kunci(i))
        log(f'   permintaan TTS: {dipakai} (tanpa pengelompokan: {len(segmen)})')
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
