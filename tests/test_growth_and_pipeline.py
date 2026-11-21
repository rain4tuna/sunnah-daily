"""Pengujian optimasi Growth (Hook/CTA/Caption YT & IG & TikTok), props SunnahMotion, SFX, dan video panjang 8+ menit."""
import os
import re
import sys
import tempfile
import unittest
import wave

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

import growth
import remotion_video
import sfx
import storyboard_ikon
import video_panjang


def _contoh_kisah():
    return {
        'id': 'ep011-02',
        'menit': '12:30',
        'judul_hook': 'Gemetar Mendengar Petir Al-Qur\'an',
        'narasi_hook': 'Mengapa tokoh Quraisy mendadak panik saat mendengar satu ayat ini?',
        'adegan': [
            {'narasi': 'Utbah datang menawarkan harta agar dakwah dihentikan.'},
            {'narasi': 'Rasulullah ﷺ menjawab tenang dengan membacakan Surah Fushshilat.'},
        ],
        'dalil': {
            'jenis': 'ayat',
            'arab': 'فَإِنْ أَعْرَضُوا فَقُلْ أَنْذَرْتُكُمْ صَاعِقَةً',
            'terjemah': 'Jika mereka berpaling, katakanlah aku memperingatkan kamu akan bencana petir.',
            'sumber': 'QS. Fussilat: 13',
            'derajat': 'ayat',
        },
        'faedah': 'Al-Qur\'an memiliki getaran kebenaran yang menembus hati sekeras apa pun.',
        'tema': ['Al-Quran', 'Dakwah', 'Keteguhan'],
        'storyboard_ikon': {
            'hook': {'narasi': 'Mengapa tokoh Quraisy mendadak panik saat mendengar satu ayat ini?', 'ikon': ['awan_hujan'], 'ilustrasi': 'badai', 'tokoh': 'panik'},
            'poin': [
                {'narasi': 'Utbah menawarkan harta dan kekuasaan agar dakwah berhenti.', 'label': 'Tawaran Pembesar Quraisy', 'ikon': ['koin'], 'ilustrasi': 'sedekah', 'tokoh': 'menunjuk'},
                {'narasi': 'Rasulullah ﷺ membacakan Surah Fushshilat dengan tenang.', 'label': 'Bacaan Surah Fushshilat', 'ikon': ['quran'], 'ilustrasi': 'belajar_ilmu', 'tokoh': 'berdiri'},
            ],
            'faedah': {'narasi': 'Al-Qur\'an sanggup menembus hati sekeras apa pun.', 'ikon': ['hati'], 'ilustrasi': 'doa_malam', 'tokoh': 'berdoa'},
            'penutup': {'ajakan': 'Tulis Aamiin di komentar', 'narasi': 'Tulis Aamiin di komentar dan ikuti Sunnah Daily.'},
        },
    }


class TestGrowthAndPipeline(unittest.TestCase):
    def test_skor_hook_kuat_vs_lemah(self):
        kuat = growth.skor_hook('Gemetar Mendengar Petir Al-Qur\'an', 'Mengapa tokoh Quraisy mendadak panik mendengar satu ayat ini?')
        self.assertGreaterEqual(kuat['skor'], 75)
        self.assertEqual(kuat['grade'], 'STRONG')

        lemah = growth.skor_hook('Halo teman teman semua selamat datang di channel ini ya', 'Halo guys selamat datang di video kali ini kita akan bahas cerita')
        self.assertLess(lemah['skor'], 55)
        self.assertEqual(lemah['grade'], 'WEAK')

    def test_caption_ig_patuh_aturan_ig_caption(self):
        k = _contoh_kisah()
        ep = {'judul': 'Sirah Nabawiyah #11 - Usaha Quraisy', 'url': 'https://youtu.be/xyz123'}
        cap = growth.caption_ig(k, ep, seri='sirah')
        # 1. Baris pertama <= 125 char, tidak diawali emoji atau hashtag
        baris1 = cap.splitlines()[0]
        self.assertLessEqual(len(baris1), 125)
        self.assertFalse(baris1.startswith('#'))
        # 2. Maksimal 5 hashtag (aturan IG 18 Des 2025) & tidak ada filler tag
        tags = re.findall(r'#[A-Za-z0-9_]+', cap)
        self.assertLessEqual(len(tags), 5)
        self.assertGreaterEqual(len(tags), 3)
        for t in tags:
            self.assertNotIn(t[1:].lower(), growth.TAG_FILLER)
        # 3. Tidak ada URL di caption IG
        self.assertNotRegex(cap, r'https?://')
        # 4. Total <= 2200 karakter & kredit ustadz tetap ada
        self.assertLessEqual(len(cap), 2200)
        self.assertIn('Firanda Andirja', cap)

    def test_metadata_yt_shorts_dan_caption_tiktok(self):
        k = _contoh_kisah()
        ep = {'judul': 'Sirah Nabawiyah #11 - Usaha Quraisy', 'url': 'https://youtu.be/xyz123'}
        yt_m = growth.metadata_yt(k, ep, seri='sirah')
        self.assertIn('#Shorts', yt_m['judul'])
        judul_inti = yt_m['judul'].replace('#Shorts', '').strip()
        self.assertLessEqual(len(judul_inti), growth.YT_TITLE_VISIBLE)
        self.assertIn('https://youtu.be/xyz123&t=750s', yt_m['deskripsi'])
        self.assertLessEqual(len(yt_m['tags']), 15)

        cap_tt = growth.caption_tiktok(k, ep, seri='sirah')
        self.assertLessEqual(len(cap_tt), growth.TT_CAPTION_MAX)
        self.assertNotRegex(cap_tt, r'https?://')
        self.assertLessEqual(len(re.findall(r'#[A-Za-z0-9_]+', cap_tt)), 5)

    def test_props_sunnah_motion_dan_sfx_non_musik(self):
        k = _contoh_kisah()
        seg = storyboard_ikon.segmen(k, 'SIRAH #11', lambda dl: dl['terjemah'], seri='Sirah #11', kredit='Kajian\nUst. Firanda')
        # Pastikan tokoh di babak yang menyebut Rasulullah ﷺ otomatis dikosongkan
        poin2 = [s for s in seg if s['jenis'] == 'poin'][1]
        self.assertEqual(poin2['tokoh'], '')
        self.assertEqual(poin2['ilustrasi'], 'belajar_ilmu')
        self.assertTrue(seg[0].get('hookBadge'))

        with tempfile.TemporaryDirectory() as tmp:
            t = 0.0
            for i, s in enumerate(seg):
                wav = os.path.join(tmp, f's{i}.wav')
                with wave.open(wav, 'wb') as w:
                    w.setnchannels(1)
                    w.setsampwidth(2)
                    w.setframerate(24000)
                    w.writeframes(b'\x00\x00' * 24000 * 3)
                s['wav'] = wav
                s['mulai'] = t
                s['durasi'] = 3.35
                t += 3.35
            props_kaya = remotion_video.susun_props(seg, komposisi='SunnahMotion')
            props_lama = remotion_video.susun_props(seg, komposisi='SunnahDaily')
            # SunnahMotion menyimpan adegan baru 'belajar_ilmu'; SunnahDaily otomatis memetakan ke 'quran'
            self.assertEqual(props_kaya['segmen'][2]['ilustrasi'], 'belajar_ilmu')
            self.assertEqual(props_lama['segmen'][2]['ilustrasi'], 'quran')
            # SFX untuk SunnahMotion menghasilkan isyarat valid dan semua ID ada di sfx/data.json
            cues = sfx.isyarat(props_kaya, komposisi='SunnahMotion')
            self.assertGreater(len(cues), 5)
            valid_ids = set(sfx._data().keys())
            for _, sid, _, _ in cues:
                self.assertIn(sid, valid_ids)

    def test_video_panjang_mode_monet_dual_cta(self):
        data = {'episode': 11, 'judul': 'Sirah #11 - Uji Monet', 'url': 'https://youtu.be/abc'}
        kisah_list = []
        for idx in range(6):
            k = _contoh_kisah()
            k['id'] = f'ep011-0{idx + 1}'
            kisah_list.append(k)
        seg_monet = video_panjang.susun_segmen(data, kisah_list, anak=True, naskah={}, dual_cta=True)
        jumlah_ajak = sum(1 for s in seg_monet if s['jenis'] == 'ajak')
        self.assertEqual(jumlah_ajak, 2)


if __name__ == '__main__':
    unittest.main()
