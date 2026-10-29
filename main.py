"""Buat satu video Sunnah Daily: pilih kisah berikutnya -> verifikasi dalil -> narasi TTS -> render.

Env:
  GEMINI_API_KEY   wajib
  EPISODE          nomor episode (kosong = episode pertama yang masih punya kisah berstatus Belum)
  KISAH            nomor urut kisah di episode (kosong = kisah Belum pertama)
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

import ekstrak
import gemini
import ig
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
    for p in glob.glob(os.path.join(ekstrak.DIR, 'ep*.json')):
        with open(p) as f:
            for k in json.load(f).get('kisah', []):
                w = k.get('waktu_posting')
                if w and dt.datetime.fromisoformat(w) > batas:
                    return True
    return False


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

    for percobaan in range(5):
        data, k = pilih(eps, os.environ.get('EPISODE') or None, os.environ.get('KISAH') or None)
        log(f"Kisah {k['id']}: {k['judul_hook']}")
        if 'layak' not in k:
            try:
                ekstrak.verifikasi(k)
            except Exception as e:
                log(f'   verifikasi gagal: {e}')
                k['layak'] = False
            if (k.get('cek') or {}).get('kisah_lemah'):
                k['layak'] = False
            ekstrak.simpan(data)
        if k.get('layak'):
            break
        log(f"   dilewati: {(k.get('cek') or {}).get('catatan', '')}")
        k['status'] = 'Dilewati'
        ekstrak.simpan(data)
        if os.environ.get('KISAH'):
            raise SystemExit('Kisah yang dipilih tidak lolos verifikasi.')
    else:
        raise SystemExit('Tidak menemukan kisah yang lolos verifikasi.')

    ep = {'judul': data['judul'], 'url': data['url']}
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

    with tempfile.TemporaryDirectory() as tmp:
        for i, s in enumerate(segmen):
            s['wav'] = os.path.join(tmp, f'suara{i}.wav')
            log(f"   TTS {i + 1}/{len(segmen)}")
            gemini.bacakan(lisan(s['ucap']), s['wav'])
        mp4 = os.path.join(out, f"{k['id']}.mp4")
        durasi = video.buat_video(segmen, tema, mp4, os.path.join(out, f"{k['id']}_cuplikan.jpg"))
    log(f'Video {durasi:.1f} detik -> {mp4}')

    cap = caption(k, ep)
    with open(os.path.join(out, f"{k['id']}_caption.txt"), 'w') as f:
        f.write(cap)
    with open(os.path.join(out, f"{k['id']}.json"), 'w') as f:
        json.dump(k, f, ensure_ascii=False, indent=1)
    if not uji:
        k['status'] = 'Dibuat'
        if os.environ.get('POSTING_IG', 'false').lower() == 'true':
            ig_id = os.environ.get('IG_USER_ID') or '17841438717756877'
            media = ig.posting_reel_berkas(ig_id, mp4, cap)
            k['ig'] = ig.permalink(media) or media
            k['status'] = 'Diposting'
            log(f"Diposting ke IG: {k['ig']}")
        if os.environ.get('POSTING_YT', 'false').lower() == 'true':
            try:
                k['yt'] = yt.upload(mp4, k['judul_hook'], cap, ['sunnah', 'sirah nabawiyah', 'kisah nabi', 'hadits']
                                    + k.get('tema', []))
                k['status'] = 'Diposting'
                log(f"Diposting ke YouTube: {k['yt']}")
            except Exception as e:
                log(f'::warning::YouTube gagal: {e}')
        if k['status'] == 'Diposting':
            k['waktu_posting'] = dt.datetime.utcnow().isoformat(timespec='seconds')
        ekstrak.simpan(data)
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
