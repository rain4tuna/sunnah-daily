"""Buat satu video Sunnah Daily: pilih kisah berikutnya -> verifikasi dalil -> narasi TTS -> render.

Env:
  GEMINI_API_KEY   wajib
  SERI             sirah | harian (kosong: slot 11.47 & 18.47 WIB = harian, slot lain = sirah)
  GAYA             ikon (default, Animasi Ikon papan/flat/kertas) | remotion (ilustrasi bergerak, butuh Node)
                   | sirah (gaya Gua Tsur) | lama
  GAYA_IKON        papan | flat | kertas (kosong = bergiliran per video)
  EPISODE          nomor episode (kosong = episode pertama yang masih punya kisah berstatus Belum)
  KISAH            nomor urut kisah di episode / nomor topik Sunnah Harian (kosong = berikutnya)
  TEMA             siang | malam | auto (auto: malam untuk jam 18.00-04.59 WIB)
  UJI              true = hanya buat video (status kisah tidak diubah)
  OUT_DIR          folder hasil (default hasil)
"""
import csv
import datetime as dt
import json
import os
import re
import sys
import tempfile

import animasi_ikon
import ekstrak
import fb
import harian
import gemini
import ig
import motion
import remotion_video
import storyboard
import storyboard_ikon
import video
import yt

ROOT = os.path.dirname(os.path.abspath(__file__))
SAW = 'ﷺ'
UCAP = "shallallahu 'alaihi wa sallam"
HASHTAG = ['sunnahdaily', 'sirahnabawiyah', 'kisahnabi', 'kisahislami', 'hadits', 'sunnah', 'dakwah',
           'nasihatislam', 'rasulullah', 'belajarislam']


def log(*a):
    print(*a, flush=True)


def episode_list():
    with open(os.path.join(ROOT, 'data', 'episode.csv')) as f:
        return [r for r in csv.DictReader(f)]


def lisan(teks):
    """Teks untuk dibacakan: simbol ﷺ diucapkan lengkap."""
    return re.sub(rf'\s*{SAW}', ' ' + UCAP, teks).strip()


def perawi(sumber):
    m = re.search(r'HR\.?\s*([^,.;·]+?)(?:\s+no\b|\s*$|[,;·])', sumber or '')
    return m.group(1).strip() if m else 'para ulama hadits'


def narasi_dalil(dl):
    jenis = dl.get('jenis')
    if jenis == 'ayat':
        return f"Allah Ta'ala berfirman, {dl['terjemah']}"
    if jenis == 'ulama':
        nama = re.split(r'[,(]', dl.get('sumber') or 'Para ulama')[0].strip()
        return f"{nama} rahimahullah berkata, {dl['terjemah']}"
    if jenis == 'atsar':
        n = f"Dalam sebuah atsar disebutkan, {dl['terjemah']}"
    else:
        n = f"Dalam hadits riwayat {perawi(dl.get('sumber'))} disebutkan, {dl['terjemah']}"
    if dl.get('derajat') == 'lemah':
        n += ' Hadits ini lemah, disebutkan sebagai penjelasan, bukan sebagai dalil.'
    return n


def detik(menit):
    try:
        bag = [int(x) for x in str(menit).split(':')]
        return bag[0] * 3600 + bag[1] * 60 + bag[2] if len(bag) == 3 else bag[0] * 60 + bag[1]
    except Exception:
        return 0


def caption(k, ep):
    dl = k['dalil']
    derajat = f" · {dl['derajat'].capitalize()}" if dl.get('jenis') in ('hadits', 'atsar') and dl.get('derajat') else ''
    if dl.get('derajat') == 'lemah':
        derajat += ' (lemah, bukan dalil)'
    isi = ' '.join(a['narasi'] for a in k['adegan'])
    tautan = ep['url'] + (f"&t={detik(k.get('menit'))}s" if detik(k.get('menit')) else '')
    tag = HASHTAG + [re.sub(r'\W', '', t.lower()) for t in k.get('tema', [])][:3]
    return (f"{k['judul_hook']} 🌙\n\n{isi}\n\n"
            f"📖 {dl['terjemah']}\n({dl['sumber']}{derajat})\n\n"
            f"🤍 Faedah: {k['faedah']}\n\n"
            f"Faedah dari kajian {ep['judul']}, Ust. Dr. Firanda Andirja, M.A.\nKajian lengkap: {tautan}\n\n"
            + ' '.join('#' + t for t in dict.fromkeys(tag) if t))


def pilih(eps, no_ep=None, no_kisah=None):
    daftar = [e for e in eps if not no_ep or int(e['No']) == int(no_ep)]
    for e in daftar:
        no = int(e['No'])
        data = ekstrak.ekstrak(no, e['Judul Episode'], e['Link'])
        kandidat = data['kisah']
        if no_kisah:
            kandidat = [kandidat[int(no_kisah) - 1]]
        for k in kandidat:
            if no_kisah or k.get('status') == 'Belum':
                return data, k
    raise SystemExit('Tidak ada kisah berstatus Belum.')


def tema_otomatis():
    jam = (dt.datetime.utcnow() + dt.timedelta(hours=7)).hour
    return 'malam' if jam >= 18 or jam < 5 else 'siang'


def baru_saja_posting(menit=75):
    """True kalau ada postingan dalam `menit` terakhir (cegah dobel saat jadwal GitHub telat)."""
    import glob
    batas = dt.datetime.utcnow() - dt.timedelta(minutes=menit)
    for p in glob.glob(os.path.join(ekstrak.DIR, '*.json')):
        with open(p) as f:
            for k in json.load(f).get('kisah', []):
                w = k.get('waktu_posting')
                if w and dt.datetime.fromisoformat(w) > batas:
                    return True
    return False


def tulis_daftar():
    """DAFTAR_POSTINGAN.md: semua kisah yang sudah tayang, terbaru di atas."""
    import glob
    baris = []
    for p in glob.glob(os.path.join(ekstrak.DIR, '*.json')):
        with open(p) as f:
            for k in json.load(f).get('kisah', []):
                if k.get('status') == 'Diposting':
                    w = k.get('waktu_posting')
                    wib = (dt.datetime.fromisoformat(w) + dt.timedelta(hours=7)).strftime('%d %b %Y %H.%M') if w else '-'
                    dl = k.get('dalil', {})
                    sumber = dl.get('sumber', '') + (f" ({dl['derajat']})" if dl.get('jenis') in ('hadits', 'atsar') and dl.get('derajat') else '')
                    ig_l = f"[IG]({k['ig']})" if k.get('ig') else '-'
                    yt_l = f"[YouTube]({k['yt']})" if k.get('yt') else '-'
                    if k.get('fb'):
                        yt_l += f" · [FB]({k['fb']})"
                    baris.append((w or '', f"| {wib} | {k['id']} | {k['judul_hook']} | {sumber} | {ig_l} · {yt_l} |"))
    baris.sort(reverse=True)
    isi = ['# Daftar Postingan Sunnah Daily', '', f'Total: {len(baris)} video. Waktu dalam WIB, terbaru di atas.', '',
           '| Tayang | ID | Judul | Dalil | Link |', '|---|---|---|---|---|'] + [b for _, b in baris]
    with open(os.path.join(ROOT, 'DAFTAR_POSTINGAN.md'), 'w') as f:
        f.write('\n'.join(isi) + '\n')


def seri(judul):
    m = re.match(r'.*?#\s*(\d+)\s*-\s*(.+)', judul or '')
    return f"Sirah #{int(m.group(1)):02d} · {m.group(2).strip()}" if m else (judul or '')


def segmen_storyboard(k, data):
    segmen = []
    for b in storyboard.buat(k):
        s = dict(b)
        if b['jenis'] == 'dalil':
            s['dalil'] = k['dalil']
            s['narasi'] = narasi_dalil(k['dalil'])
        if b['jenis'] == 'penutup':
            s['seri'] = seri(data['judul'])
            s['kredit'] = f"Faedah dari kajian {data['judul']}\nUst. Dr. Firanda Andirja, M.A."
        s['teks_caption'] = s['narasi']
        s['ucap'] = s['narasi']
        segmen.append(s)
    return segmen


def segmen_lama(k, data):
    segmen = [{'jenis': 'hook', 'latar': k.get('latar_hook') or k['adegan'][0]['latar'],
               'judul': k['judul_hook'], 'ucap': k.get('narasi_hook') or k['judul_hook']}]
    for a in k['adegan']:
        segmen.append({'jenis': 'kisah', 'latar': a.get('latar') or 'gurun', 'narasi': a['narasi'],
                       'ucap': a['narasi']})
    segmen.append({'jenis': 'dalil', 'dalil': k['dalil'], 'ucap': narasi_dalil(k['dalil'])})
    segmen.append({'jenis': 'faedah', 'latar': k.get('latar_faedah') or 'kitab', 'faedah': k['faedah'],
                   'ucap': f"Faedahnya, {k['faedah']}"})
    segmen.append({'jenis': 'penutup', 'kredit': f"Faedah dari kajian {data['judul']}\nUst. Dr. Firanda Andirja, M.A.",
                   'ucap': 'Semoga bermanfaat. Ikuti Sunnah Daily untuk kisah berikutnya.'})
    return segmen


def pilih_seri():
    s = (os.environ.get('SERI') or '').lower()
    if s in ('sirah', 'harian'):
        return s
    # slot 11.47 & 18.47 WIB = Sunnah Harian (berlaku untuk jadwal GitHub maupun pemicu Apps Script)
    jam = (dt.datetime.utcnow() + dt.timedelta(hours=7)).hour
    return 'harian' if jam in (11, 12, 18, 19) else 'sirah'


def gaya_ikon(k):
    g = (os.environ.get('GAYA_IKON') or '').lower()
    return g if g in animasi_ikon.URUTAN_GAYA else animasi_ikon.URUTAN_GAYA[sum(map(ord, k['id'])) % 3]


def main():
    out = os.environ.get('OUT_DIR', 'hasil')
    if os.environ.get('JADWAL') == 'schedule' and baru_saja_posting():
        log('Sudah ada postingan dalam 75 menit terakhir, slot ini dilewati.')
        return
    os.makedirs(out, exist_ok=True)
    uji = os.environ.get('UJI', 'true').lower() == 'true'
    tema = os.environ.get('TEMA', 'auto') or 'auto'
    tema = tema_otomatis() if tema == 'auto' else tema
    eps = episode_list()
    seri_v = pilih_seri()
    simpan = harian.simpan if seri_v == 'harian' else ekstrak.simpan
    log(f'Seri: {seri_v}')

    for percobaan in range(5):
        if seri_v == 'harian':
            data, k = harian.pilih(os.environ.get('KISAH') or None)
        else:
            data, k = pilih(eps, os.environ.get('EPISODE') or None, os.environ.get('KISAH') or None)
        log(f"Kisah {k['id']}: {k['judul_hook']}")
        if 'layak' not in k:
            try:
                ekstrak.verifikasi(k)
            except Exception as e:
                log(f'   verifikasi gagal: {e}')
                k['layak'] = False
            ekstrak.aturan_layak(k, harian=seri_v == 'harian')
            simpan(data)
        if k.get('layak'):
            break
        log(f"   dilewati: {(k.get('cek') or {}).get('catatan', '')}")
        k['status'] = 'Dilewati'
        simpan(data)
        if os.environ.get('KISAH'):
            raise SystemExit('Kisah yang dipilih tidak lolos verifikasi.')
    else:
        raise SystemExit('Tidak menemukan kisah yang lolos verifikasi.')

    ep = {'judul': data['judul'], 'url': data['url']}
    gaya_v = os.environ.get('GAYA', 'ikon') or 'ikon'
    if gaya_v in ('ikon', 'remotion'):
        gv = gaya_ikon(k)
        if seri_v == 'harian':
            segmen = storyboard_ikon.segmen(k, 'SUNNAH HARIAN', narasi_dalil, seri='Sunnah Harian', lanjut='sunnah')
        else:
            m = re.match(r'.*?#\s*(\d+)', data['judul'] or '')
            kicker = f'SIRAH #{int(m.group(1)):02d}' if m else 'SIRAH NABAWIYAH'
            segmen = storyboard_ikon.segmen(k, kicker, narasi_dalil, seri=seri(data['judul']),
                                            kredit=f"Faedah dari kajian {data['judul']}\nUst. Dr. Firanda Andirja, M.A.")
        simpan(data)
        if gaya_v == 'remotion':
            log('   template: remotion — ' + ', '.join(f"{s.get('ilustrasi')}{'+' + s['tokoh'] if s.get('tokoh') else ''}"
                                                       for s in segmen if s.get('ilustrasi')))
            pembuat = remotion_video.buat_video
        else:
            log(f'   template: animasi ikon ({gv})')

            def pembuat(sg, tm, mp4, jpg):
                return animasi_ikon.buat_video(sg, tm, mp4, jpg, gaya_v=gv)
    elif gaya_v == 'lama':
        segmen = segmen_lama(k, data)
        pembuat = video.buat_video
    else:
        segmen = segmen_storyboard(k, data)
        simpan(data)                 # storyboard tersimpan: render ulang/posting memakai yang sama
        pembuat = motion.buat_video
    log('   babak: ' + ', '.join(s['jenis'] for s in segmen))

    with tempfile.TemporaryDirectory() as tmp:
        for i, s in enumerate(segmen):
            s['wav'] = os.path.join(tmp, f'suara{i}.wav')
            log(f"   TTS {i + 1}/{len(segmen)}")
            gemini.bacakan(lisan(s['ucap']), s['wav'])
        mp4 = os.path.join(out, f"{k['id']}.mp4")
        durasi = pembuat(segmen, tema, mp4, os.path.join(out, f"{k['id']}_cuplikan.jpg"))
    log(f'Video {durasi:.1f} detik -> {mp4}')

    cap = harian.caption(k) if seri_v == 'harian' else caption(k, ep)
    with open(os.path.join(out, f"{k['id']}_caption.txt"), 'w') as f:
        f.write(cap)
    with open(os.path.join(out, f"{k['id']}.json"), 'w') as f:
        json.dump(k, f, ensure_ascii=False, indent=1)
    if not uji:
        k['status'] = 'Dibuat'
        gagal = []
        if os.environ.get('POSTING_IG', 'false').lower() == 'true':
            ig_id = os.environ.get('IG_USER_ID') or '17841438717756877'
            try:
                media = ig.posting_reel_aman(ig_id, mp4, cap)
                k['ig'] = ig.permalink(media) or media
                k['status'] = 'Diposting'
                log(f"Diposting ke IG: {k['ig']}")
            except Exception as e:
                gagal.append(f'IG: {e}')
                log(f'::warning::IG gagal: {e}'[:900])
        if os.environ.get('POSTING_FB', 'false').lower() == 'true':
            try:
                k['fb'] = fb.posting_reel(mp4, cap)
                k['status'] = 'Diposting'
                log(f"Diposting ke Facebook: {k['fb']}")
            except Exception as e:
                gagal.append(f'FB: {e}')
                log(f'::warning::Facebook gagal: {e}'[:900])
        if os.environ.get('POSTING_YT', 'false').lower() == 'true':
            try:
                k['yt'] = yt.upload(mp4, k['judul_hook'], cap, (['sunnah', 'amalan sunnah', 'hadits'] if seri_v == 'harian'
                                    else ['sunnah', 'sirah nabawiyah', 'kisah nabi', 'hadits']) + k.get('tema', []))
                k['status'] = 'Diposting'
                log(f"Diposting ke YouTube: {k['yt']}")
            except Exception as e:
                gagal.append(f'YouTube: {e}')
                log(f'::warning::YouTube gagal: {e}'[:900])
        if k['status'] == 'Diposting':
            k['waktu_posting'] = dt.datetime.utcnow().isoformat(timespec='seconds')
        simpan(data)
        tulis_daftar()
        if gagal and k['status'] != 'Diposting':
            raise RuntimeError('Semua posting gagal: ' + ' | '.join(gagal))
    log('\n' + cap)


if __name__ == '__main__':
    try:
        main()
    except SystemExit:
        raise
    except Exception as e:
        import traceback
        traceback.print_exc()
        print(f'::error::{type(e).__name__}: {str(e)[:900]}')
        sys.exit(1)
