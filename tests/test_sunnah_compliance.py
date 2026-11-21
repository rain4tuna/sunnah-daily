"""Pengujian kepatuhan aturan Sunnah (otomatis & non-negosiabel):
1. Semua karakter SVG/properti 100% TANPA mata, alis, hidung, dan mulut.
2. Tidak ada tokoh pada segmen yang menyebut Nabi ﷺ, para nabi, sahabat, atau malaikat.
3. Tidak ada musik pada pipeline audio maupun pustaka SFX.
4. Tidak ada stiker mata/hidung/telinga/wajah/musik/babi di stiker.py dan data/stiker/tabler.json.
"""
import json
import os
import re
import sys
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

import sfx
import stiker
import storyboard_ikon


class TestSunnahCompliance(unittest.TestCase):
    def test_karakter_kaya_tanpa_mata_hidung_mulut(self):
        path = os.path.join(ROOT, 'remotion', 'src', 'KarakterKaya.tsx')
        with open(path, encoding='utf-8') as f:
            src = f.read()
        # Hapus komentar & docstring sebelum memindai identifier JSX/SVG
        kode = re.sub(r'/\*.*?\*/', '', src, flags=re.S)
        kode = re.sub(r'//.*', '', kode)
        for terlarang in (r'\bmata\b', r'\beye\b', r'\beyes\b', r'\bhidung\b', r'\bnose\b', r'\bmulut\b', r'\bmouth\b', r'\balis\b', r'\beyebrow\b'):
            self.assertIsNone(re.search(terlarang, kode, re.I), f'Ditemukan elemen wajah terlarang ({terlarang}) di KarakterKaya.tsx')

    def test_ilustrasi_tokoh_tanpa_mata_hidung_mulut(self):
        path = os.path.join(ROOT, 'remotion', 'src', 'Ilustrasi.tsx')
        with open(path, encoding='utf-8') as f:
            src = f.read()
        kode = re.sub(r'/\*.*?\*/', '', src, flags=re.S)
        kode = re.sub(r'//.*', '', kode)
        for terlarang in (r'\beye\b', r'\beyes\b', r'\bnose\b', r'\bmouth\b', r'\beyebrow\b'):
            self.assertIsNone(re.search(terlarang, kode, re.I), f'Ditemukan elemen wajah terlarang ({terlarang}) di Ilustrasi.tsx')

    def test_kata_tanpa_tokoh_blokir_nabi_sahabat_malaikat(self):
        kasus = [
            'Rasulullah ﷺ menjawab dengan tenang.',
            'Nabi, sahabat, dan kaum muslimin bersabar.',
            'Beliau berdiri di atas bukit Shafa.',
            'Malaikat Jibril membawa wahyu pertama.',
            'Abu Bakar radhiyallahu anhu membenarkan kisah itu.',
            'Khadijah menenangkan hati dengan penuh kasih.',
        ]
        for narasi in kasus:
            _, tokoh = storyboard_ikon.ilustrasi_babak({'narasi': narasi, 'ilustrasi': 'gua', 'tokoh': 'berdiri'})
            self.assertEqual(tokoh, '', f'Tokoh harus kosong untuk narasi: {narasi}')

    def test_tokoh_diizinkan_untuk_kaum_umum(self):
        il, tokoh = storyboard_ikon.ilustrasi_babak({
            'narasi': 'Seorang pedagang di pasar mulai memikirkan kembali niatnya.',
            'ilustrasi': 'sedekah',
            'tokoh': 'berjalan',
        })
        self.assertEqual(il, 'sedekah')
        self.assertEqual(tokoh, 'berjalan')
        # Mode legacy tetap memetakan ke pose dasar
        il_leg, tk_leg = storyboard_ikon.ilustrasi_babak({
            'narasi': 'Seorang pedagang berjalan di pasar.',
            'ilustrasi': 'hijrah_perjalanan',
            'tokoh': 'berjalan',
        }, legacy=True)
        self.assertEqual(il_leg, 'kafilah')
        self.assertEqual(tk_leg, 'berdiri')

    def test_audio_sfx_nol_musik(self):
        data = sfx._data()
        self.assertGreater(len(data), 0)
        kata_musik = ('music', 'melody', 'chord', 'jingle', 'guitar', 'piano', 'drum', 'violin', 'flute', 'song', 'beat', 'synth')
        for sid, info in data.items():
            gabung = f"{sid} {info.get('deskripsi', '')}".lower()
            for km in kata_musik:
                self.assertNotIn(km, gabung, f'SFX terindikasi musik: {sid}')
        # Pastikan tidak ada track musik BGM yang direferensikan di remotion_video.py atau SunnahMotion.tsx
        for rel in ('remotion_video.py', os.path.join('remotion', 'src', 'SunnahMotion.tsx')):
            with open(os.path.join(ROOT, rel), encoding='utf-8') as f:
                isi = f.read().lower()
            for k in ('bgm', 'background_music', 'music.mp3', 'backsound'):
                self.assertNotIn(k, isi, f'Referensi musik ditemukan di {rel}: {k}')

    def test_stiker_bersih_dari_mata_hidung_musik_babi(self):
        self.assertNotIn('eye', stiker.TETAP)
        for terlarang in ('eye', 'eyes', 'nose', 'mouth', 'ear', 'pig', 'music'):
            self.assertIn(terlarang, stiker.KATA_BUANG)
        with open(stiker.PUSTAKA, encoding='utf-8') as f:
            pustaka = json.load(f)
        for nama in pustaka:
            bagian = set(nama.split(':')[0].split('-'))
            self.assertFalse(
                bagian & {'eye', 'eyes', 'eyeglass', 'nose', 'mouth', 'ear', 'pig', 'music', 'guitar', 'piano'},
                f'Stiker terlarang masih ada di tabler.json: {nama}',
            )


if __name__ == '__main__':
    unittest.main()
