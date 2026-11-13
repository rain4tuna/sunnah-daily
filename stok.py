"""Stok naskah tanpa API: riset & cek dalil dikerjakan di chat Gemini (gratis), hasilnya ditempel ke repo.

Workflow harian memakai kisah berstatus Belum yang sudah punya 'layak' tanpa memanggil Gemini + Google Search
lagi. Kalau stok habis, workflow otomatis kembali riset/cek lewat API seperti biasa.

  python stok.py status   lihat sisa stok
  python stok.py minta    tulis prompt ke stok/minta/*.txt (tempel tiap file ke chat Gemini baru)
  python stok.py gabung   baca jawaban JSON di stok/jawab/ lalu pasang ke data/kisah

Pilihan untuk minta: --cek N (maks kisah dicek, default 12), --riset N (maks topik Sunnah Harian, default 8),
--episode N (maks episode Sirah baru yang diekstrak dari videonya, default 0), --per N (tugas per file, default 4).
"""
import argparse
import csv
import glob
import json
import os
import shutil
import sys

import ekstrak
import gemini
import harian

ROOT = os.path.dirname(os.path.abspath(__file__))
MINTA = os.path.join(ROOT, 'stok', 'minta')
JAWAB = os.path.join(ROOT, 'stok', 'jawab')
SELESAI = os.path.join(ROOT, 'stok', 'selesai')

PEMBUKA = """Di bawah ini ada {n} tugas terpisah. Kerjakan SATU PER SATU dengan teliti; untuk tiap tugas lakukan
pencarian Google sendiri, jangan menyalin hasil tugas lain.

Setelah semua selesai, balas dengan SATU blok JSON saja (tanpa penjelasan lain) berbentuk:
{{"hasil": [{{"id": "<id tugas>", ...semua field JSON yang diminta tugas itu...}}]}}
Field "id" wajib sama persis dengan id tugasnya, dan jumlah isi "hasil" harus {n}.
"""


def semua_data():
    """[(data, simpan)] untuk tiap berkas kisah: episode Sirah berurutan, lalu Sunnah Harian."""
    daftar = []
    for p in sorted(glob.glob(os.path.join(ekstrak.DIR, 'ep*.json'))):
        with open(p, encoding='utf-8') as f:
            daftar.append((json.load(f), ekstrak.simpan))
    if os.path.exists(harian.PATH):
        daftar.append((harian.muat(), harian.simpan))
    return daftar


def perlu_cek(k):
    return k.get('status') == 'Belum' and 'layak' not in k and k.get('dalil') and k.get('adegan')


def topik_tersisa():
    sudah = {k.get('topik') for k in harian.muat()['kisah']}
    return [t for t in harian.daftar_topik() if t['Topik'] not in sudah]


def episode_baru():
    """Episode Sirah yang belum diekstrak (belum punya data/kisah/epNNN.json), berurutan."""
    with open(os.path.join(ROOT, 'data', 'episode.csv'), encoding='utf-8') as f:
        return [e for e in csv.DictReader(f) if not os.path.exists(ekstrak.path_ep(e['No']))]


def id_ep(e):
    return f"ep{int(e['No']):03d}"


def status():
    siap = {'Sirah': 0, 'Sunnah Harian': 0}
    belum = dict(siap)
    for data, _ in semua_data():
        nama = 'Sunnah Harian' if data.get('seri') == 'harian' else 'Sirah'
        for k in data['kisah']:
            if k.get('status') == 'Belum' and k.get('layak'):
                siap[nama] += 1
            elif perlu_cek(k):
                belum[nama] += 1
    per_hari = {'Sirah': 3, 'Sunnah Harian': 2}
    for nama in siap:
        print(f'{nama}: {siap[nama]} siap tayang (cukup ~{siap[nama] / per_hari[nama]:.1f} hari), '
              f'{belum[nama]} menunggu cek dalil')
    print(f'Topik Sunnah Harian yang belum diriset: {len(topik_tersisa())}')
    print(f'Episode Sirah yang belum diekstrak: {len(episode_baru())}')


def tulis_prompt(awalan, tugas, per):
    berkas = []
    for i in range(0, len(tugas), per):
        potong = tugas[i:i + per]
        isi = PEMBUKA.format(n=len(potong)) + ''.join(
            f'\n\n===== TUGAS id="{id_}" =====\n{prompt}' for id_, prompt in potong)
        p = os.path.join(MINTA, f'{awalan}-{i // per + 1:02d}.txt')
        with open(p, 'w', encoding='utf-8') as f:
            f.write(isi + '\n')
        berkas.append((p, [id_ for id_, _ in potong]))
    return berkas


def minta(maks_cek, maks_riset, maks_episode, per):
    cek = [(k['id'], ekstrak.prompt_cek(k)) for data, _ in semua_data() for k in data['kisah'] if perlu_cek(k)]
    riset = [(harian.id_topik(t), harian.PROMPT.format(topik=t['Topik'], kategori=t.get('Kategori', '')))
             for t in topik_tersisa()]
    tonton = [(id_ep(e), f"Tonton video YouTube ini sampai habis: {e['Link']}\n\n"
               + ekstrak.prompt_ekstrak(e['Judul Episode'])) for e in episode_baru()]
    shutil.rmtree(MINTA, ignore_errors=True)
    for d in (MINTA, JAWAB):
        os.makedirs(d, exist_ok=True)
    berkas = (tulis_prompt('cek', cek[:maks_cek], per) + tulis_prompt('riset', riset[:maks_riset], per)
              + tulis_prompt('episode', tonton[:maks_episode], 1))
    if not berkas:
        print('Tidak ada yang perlu dicek atau diriset.')
        return
    for p, ids in berkas:
        print(f'{os.path.relpath(p, ROOT)}: {", ".join(ids)}')
    print(f'\n1. Buka tiap file di atas, tempel isinya ke chat Gemini BARU (satu file = satu chat).\n'
          f'2. Simpan jawaban JSON-nya sebagai file di {os.path.relpath(JAWAB, ROOT)} (nama bebas, mis. cek-01.json).\n'
          f'3. Jalankan: python stok.py gabung\n'
          f'Topik yang baru diriset dan episode yang baru diekstrak masih perlu dicek dalilnya:\n'
          f'jalankan minta sekali lagi setelah gabung.')


def daftar_hasil(teks):
    j = gemini.ambil_json(teks)
    if isinstance(j, dict) and isinstance(j.get('hasil'), list):
        return j['hasil']
    return j if isinstance(j, list) else [j]


def pasang_riset(h, topik, data_harian):
    t = topik.get(h['id'])
    if not t:
        return 'id topik tidak dikenal'
    lama = next((k for k in data_harian['kisah'] if k['id'] == h['id']), None)
    if lama and (lama.get('status') != 'Belum' or 'layak' in lama):
        return f"sudah ada (status {lama.get('status')}), tidak ditimpa"
    k = {x: v for x, v in h.items() if x != 'id'}
    k['sumber_riset'] = ['manual']
    harian.pasang(data_harian, t, k)
    if k['status'] == 'Belum':
        return f"materi masuk, dalil BELUM dicek: {k.get('judul_hook', '')}"
    return f"DILEWATI (tidak ada dalil shahih): {k.get('alasan', '')}"


def pasang_episode(h, semua):
    e = next((x for x in episode_baru() if id_ep(x) == h['id']), None)
    if not e:
        return 'episode sudah ada atau id tidak dikenal, tidak ditimpa'
    kisah = [k for k in h['kisah'] if isinstance(k, dict) and k.get('adegan') and k.get('dalil')]
    if not kisah:
        raise ValueError('tidak ada kisah yang lengkap (adegan + dalil)')
    semua.append((ekstrak.bentuk(e['No'], e['Judul Episode'], e['Link'], kisah), ekstrak.simpan))
    return f'{len(kisah)} kisah masuk, dalil BELUM dicek'


def pasang_cek(h, k, harian_kah):
    if not perlu_cek(k):
        return f"sudah dicek / status {k.get('status')}, tidak ditimpa"
    ekstrak.terapkan_cek(k, h, ['manual'])
    ekstrak.aturan_layak(k, harian=harian_kah)
    dl = k['dalil']
    ringkas = f"{dl.get('sumber', '')} [{dl.get('derajat') or dl.get('jenis', '')}]"
    if k['layak']:
        return f'LOLOS  {ringkas}'
    k['status'] = 'Dilewati'
    return f"DILEWATI  {ringkas}  {k['cek'].get('catatan', '')}"


def gabung():
    os.makedirs(SELESAI, exist_ok=True)
    berkas = sorted(p for p in glob.glob(os.path.join(JAWAB, '*')) if os.path.isfile(p))
    if not berkas:
        print(f'Tidak ada file jawaban di {os.path.relpath(JAWAB, ROOT)}.')
        return
    semua = semua_data()
    if not any(d.get('seri') == 'harian' for d, _ in semua):
        semua.append((harian.muat(), harian.simpan))
    data_harian = next(d for d, _ in semua if d.get('seri') == 'harian')
    topik = {harian.id_topik(t): t for t in harian.daftar_topik()}
    for p in berkas:
        nama = os.path.basename(p)
        try:
            with open(p, encoding='utf-8-sig') as f:
                hasil = daftar_hasil(f.read())
        except Exception as e:
            print(f'{nama}: TIDAK TERBACA ({e}). Pastikan isinya JSON jawaban Gemini; file dibiarkan di tempat.')
            continue
        print(f'{nama}:')
        gagal = False
        for h in hasil:
            id_ = str(h.get('id', '')).strip() if isinstance(h, dict) else ''
            try:
                if not id_:
                    raise ValueError('tanpa id')
                h['id'] = id_
                if isinstance(h.get('kisah'), list):
                    pesan = pasang_episode(h, semua)
                elif 'adegan' in h:
                    pesan = pasang_riset(h, topik, data_harian)
                else:
                    cocok = [(d, k) for d, _ in semua for k in d['kisah'] if k.get('id') == id_]
                    if not cocok:
                        raise ValueError('id tidak ditemukan di data/kisah')
                    d, k = cocok[0]
                    pesan = pasang_cek(h, k, d.get('seri') == 'harian')
            except Exception as e:
                gagal = True
                pesan = f'GAGAL: {e}'
            print(f'   {id_ or "?"}: {pesan}')
        for d, simpan in semua:
            simpan(d)
        if gagal:
            print('   Ada tugas yang gagal; file dibiarkan di tempat. Perbaiki lalu jalankan gabung lagi.')
        else:
            shutil.move(p, os.path.join(SELESAI, nama))
    print()
    status()
    print('\nPeriksa perubahan di data/kisah, lalu commit dan push supaya dipakai jadwal tayang.')


if __name__ == '__main__':
    for s in (sys.stdout, sys.stderr):
        s.reconfigure(encoding='utf-8', errors='replace')
    ap = argparse.ArgumentParser(description='Stok naskah Sunnah Daily tanpa API.')
    ap.add_argument('perintah', choices=['status', 'minta', 'gabung'])
    ap.add_argument('--cek', type=int, default=12)
    ap.add_argument('--riset', type=int, default=8)
    ap.add_argument('--episode', type=int, default=0)
    ap.add_argument('--per', type=int, default=4)
    a = ap.parse_args()
    if a.perintah == 'status':
        status()
    elif a.perintah == 'minta':
        minta(a.cek, a.riset, a.episode, max(1, a.per))
    else:
        gabung()
