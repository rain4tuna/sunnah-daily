"""Pengujian modul TikTok (`tt.py`) serta regresi alur IG, YouTube, Facebook, dan `main.py`."""
import io
import json
import os
import sys
import tempfile
import unittest
import urllib.error
from unittest import mock

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

import fb
import ig
import main
import tg
import tt
import yt


class _FakeResponse:
    def __init__(self, body=b'{}', status=200, headers=None):
        self._body = body if isinstance(body, bytes) else json.dumps(body).encode('utf-8')
        self.status = status
        self.headers = headers or {}

    def read(self):
        return self._body

    def __enter__(self):
        return self

    def __exit__(self, *args):
        return False


class TestTikTokUploader(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.mp4 = os.path.join(self.tmp.name, 'sample.mp4')
        with open(self.mp4, 'wb') as f:
            f.write(b'\x00\x00\x00\x18ftypmp42' + b'A' * 4096)

    def tearDown(self):
        self.tmp.cleanup()

    def test_hitung_chunk_single_dan_multi(self):
        # Video 2 MB -> 1 chunk penuh
        c, n = tt.hitung_chunk(2 * 1024 * 1024)
        self.assertEqual((c, n), (2 * 1024 * 1024, 1))
        # Video 64 MB -> 1 chunk penuh
        c, n = tt.hitung_chunk(64 * 1024 * 1024)
        self.assertEqual((c, n), (64 * 1024 * 1024, 1))
        # Video 135 MB dengan batas 64 MB -> 2 chunk (chunk 2 menampung sisa 71 MB)
        c, n = tt.hitung_chunk(135 * 1024 * 1024, maks_chunk=64 * 1024 * 1024)
        self.assertEqual((c, n), (64 * 1024 * 1024, 2))
        with self.assertRaises(tt.TTError):
            tt.hitung_chunk(0)

    def test_dry_run_tanpa_kredensial(self):
        with mock.patch.dict(os.environ, {}, clear=True):
            self.assertFalse(tt.konfigurasi_siap())
            res = tt.upload(self.mp4, 'Judul test #sunnahdaily', dry_run=True)
            self.assertEqual(res, 'tiktok://dry-run/direct/SELF_ONLY/1chunks')

    def test_validasi_input_gagal(self):
        with self.assertRaises(tt.TTError):
            tt.upload(os.path.join(self.tmp.name, 'tidak_ada.mp4'), 'cap', dry_run=True)
        txt = os.path.join(self.tmp.name, 'bukan.txt')
        with open(txt, 'w', encoding='utf-8') as f:
            f.write('x')
        with self.assertRaises(tt.TTError):
            tt.upload(txt, 'cap', dry_run=True)

    def test_direct_upload_sukses_dengan_oauth_refresh_dan_fallback_privasi(self):
        calls = []

        def fake_urlopen(req, timeout=60):
            url = req.full_url if hasattr(req, 'full_url') else str(req)
            calls.append((url, getattr(req, 'method', 'GET'), dict(req.header_items()) if hasattr(req, 'header_items') else {}))
            if 'oauth/token' in url:
                return _FakeResponse({'access_token': 'tok_super_rahasia_123'})
            if 'creator_info/query' in url:
                return _FakeResponse({
                    'error': {'code': 'ok'},
                    'data': {
                        'creator_username': 'sunnahdaily_id',
                        'privacy_level_options': ['SELF_ONLY'],
                        'max_video_post_duration_sec': 600,
                    },
                })
            if 'publish/video/init' in url:
                body = json.loads(req.data.decode('utf-8'))
                # Karena aplikasi hanya diizinkan SELF_ONLY, permintaan PUBLIC_TO_EVERYONE harus fallback ke SELF_ONLY!
                self.assertEqual(body['post_info']['privacy_level'], 'SELF_ONLY')
                self.assertEqual(body['source_info']['source'], 'FILE_UPLOAD')
                return _FakeResponse({
                    'error': {'code': 'ok'},
                    'data': {'publish_id': 'v_pub_999', 'upload_url': 'https://open-upload.tiktokapis.com/upload/999'},
                })
            if 'open-upload.tiktokapis.com' in url:
                ukuran = os.path.getsize(self.mp4)
                self.assertEqual(req.get_header('Content-range'), f'bytes 0-{ukuran - 1}/{ukuran}')
                return _FakeResponse(b'', status=201)
            if 'publish/status/fetch' in url:
                return _FakeResponse({
                    'error': {'code': 'ok'},
                    'data': {'status': 'PUBLISH_COMPLETE', 'publicaly_available_post_id': ['777888999']},
                })
            raise AssertionError(f'URL tidak terduga: {url}')

        env = {
            'TT_CLIENT_KEY': 'ck_123',
            'TT_CLIENT_SECRET': 'cs_secret_9999',
            'TT_REFRESH_TOKEN': 'rt_secret_8888',
            'TT_PRIVACY': 'PUBLIC_TO_EVERYONE',
            'TT_MODE': 'direct',
        }
        with mock.patch.dict(os.environ, env, clear=True), mock.patch('urllib.request.urlopen', side_effect=fake_urlopen):
            url = tt.upload(self.mp4, 'Kisah inspiratif #sunnahdaily')
            self.assertEqual(url, 'https://www.tiktok.com/@sunnahdaily_id/video/777888999')
            self.assertEqual(len(calls), 5)

    def test_inbox_mode_dan_error_redaction(self):
        env = {'TT_ACCESS_TOKEN': 'tok_rahasia_xyz987', 'TT_MODE': 'inbox'}

        def fake_err(req, timeout=60):
            raise urllib.error.HTTPError(
                req.full_url, 401, 'Unauthorized', {},
                io.BytesIO(b'invalid token tok_rahasia_xyz987'),
            )

        with mock.patch.dict(os.environ, env, clear=True), mock.patch('urllib.request.urlopen', side_effect=fake_err):
            with self.assertRaises(tt.TTError) as ctx:
                tt.upload(self.mp4, 'Test')
            self.assertNotIn('tok_rahasia_xyz987', str(ctx.exception))
            self.assertIn('[REDACTED]', str(ctx.exception))

    def test_cek_akun_tanpa_kredensial(self):
        with mock.patch.dict(os.environ, {}, clear=True):
            with self.assertRaises(tt.TTError):
                tt.cek_akun()


class TestExistingUploadersRegression(unittest.TestCase):
    def test_modul_ig_yt_fb_siap_dan_utuh(self):
        self.assertTrue(callable(ig.posting_reel_aman))
        self.assertTrue(callable(ig.permalink))
        self.assertTrue(callable(fb.posting_reel))
        self.assertTrue(callable(yt.upload))
        self.assertTrue(callable(tt.upload))

    def test_tulis_daftar_memuat_link_tiktok_ig_yt_fb(self):
        with tempfile.TemporaryDirectory() as tmp:
            kisah_dir = os.path.join(tmp, 'data', 'kisah')
            os.makedirs(kisah_dir)
            sample = {
                'episode': 99,
                'judul': 'Sirah #99 - Uji',
                'url': 'https://youtu.be/abc',
                'kisah': [{
                    'id': 'ep099-01',
                    'judul_hook': 'Uji Semua Platform',
                    'status': 'Diposting',
                    'waktu_posting': '2026-11-21T10:00:00',
                    'dalil': {'jenis': 'hadits', 'sumber': 'HR. Bukhari no. 1', 'derajat': 'shahih'},
                    'ig': 'https://instagram.com/reel/1',
                    'yt': 'https://youtube.com/shorts/2',
                    'fb': 'https://facebook.com/reel/3',
                    'tt': 'https://www.tiktok.com/@sunnahdaily/video/4',
                }],
            }
            with open(os.path.join(kisah_dir, 'ep099.json'), 'w', encoding='utf-8') as f:
                json.dump(sample, f)
            with mock.patch.object(main, 'ROOT', tmp), mock.patch.object(main.ekstrak, 'DIR', kisah_dir):
                main.tulis_daftar()
            with open(os.path.join(tmp, 'DAFTAR_POSTINGAN.md'), encoding='utf-8') as f:
                md = f.read()
            self.assertIn('[IG](https://instagram.com/reel/1)', md)
            self.assertIn('[YouTube](https://youtube.com/shorts/2)', md)
            self.assertIn('[FB](https://facebook.com/reel/3)', md)
            self.assertIn('[TikTok](https://www.tiktok.com/@sunnahdaily/video/4)', md)


class TestTelegramDelivery(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.mp4 = os.path.join(self.tmp.name, 'sample_tg.mp4')
        with open(self.mp4, 'wb') as f:
            f.write(b'\x00\x00\x00\x18ftypmp42' + b'B' * 2048)

    def tearDown(self):
        self.tmp.cleanup()

    def test_konfigurasi_dan_dry_run(self):
        with mock.patch.dict(os.environ, {}, clear=True):
            self.assertFalse(tg.konfigurasi_siap())
            hasil = tg.kirim_video(self.mp4, 'Caption TikTok #sunnahdaily', judul='Judul Test', dry_run=True)
            self.assertEqual(hasil, f'tg://dry-run/{os.path.getsize(self.mp4)}bytes')
        with mock.patch.dict(os.environ, {'TG_BOT_TOKEN': '123456:ABCdef', 'TG_CHAT_ID': '987654'}, clear=True):
            self.assertTrue(tg.konfigurasi_siap())

    def test_validasi_input_gagal(self):
        with self.assertRaises(tg.TGError):
            tg.kirim_video(os.path.join(self.tmp.name, 'missing.mp4'), 'cap', dry_run=True)
        txt = os.path.join(self.tmp.name, 'bukan.txt')
        with open(txt, 'w', encoding='utf-8') as f:
            f.write('halo')
        with self.assertRaises(tg.TGError):
            tg.kirim_video(txt, 'cap', dry_run=True)

    def test_live_kirim_video_dan_caption_multipart(self):
        calls = []

        def fake_urlopen(req, timeout=60):
            url = req.full_url if hasattr(req, 'full_url') else str(req)
            body = req.data or b''
            calls.append((url, getattr(req, 'method', 'GET'), dict(req.header_items()), body))
            if '/sendVideo' in url:
                ctype = req.get_header('Content-type') or ''
                self.assertIn('multipart/form-data; boundary=', ctype)
                self.assertIn(b'name="chat_id"', body)
                self.assertIn(b'name="supports_streaming"', body)
                self.assertIn(b'name="video"; filename="sample_tg.mp4"', body)
                return _FakeResponse({'ok': True, 'result': {'message_id': 421}})
            if '/sendMessage' in url:
                payload = json.loads(body.decode('utf-8'))
                self.assertEqual(payload['chat_id'], '99887766')
                self.assertEqual(payload['text'], 'Caption TikTok lengkap #sunnahdaily')
                return _FakeResponse({'ok': True, 'result': {'message_id': 422}})
            if '/getMe' in url:
                return _FakeResponse({'ok': True, 'result': {'id': 111, 'username': 'sunnah_bot', 'first_name': 'Sunnah Bot'}})
            raise AssertionError(f'URL tidak terduga: {url}')

        env = {'TG_BOT_TOKEN': '999999:SECRET_TOKEN_XYZ', 'TG_CHAT_ID': '99887766'}
        with mock.patch.dict(os.environ, env, clear=True), mock.patch('urllib.request.urlopen', side_effect=fake_urlopen):
            res = tg.kirim_video(self.mp4, 'Caption TikTok lengkap #sunnahdaily', judul='Rahasia Doa')
            self.assertEqual(res, 'tg://sent/99887766/421')
            info = tg.cek_bot()
            self.assertEqual(info['username'], 'sunnah_bot')
            self.assertEqual(len(calls), 3)

    def test_token_redaction_pada_error_http(self):
        env = {'TG_BOT_TOKEN': '111222:TOKEN_SANGAT_RAHASIA', 'TG_CHAT_ID': '12345'}

        def fake_err(req, timeout=60):
            raise urllib.error.HTTPError(
                req.full_url, 401, 'Unauthorized', {},
                io.BytesIO(b'Unauthorized 111222:TOKEN_SANGAT_RAHASIA'),
            )

        with mock.patch.dict(os.environ, env, clear=True), mock.patch('urllib.request.urlopen', side_effect=fake_err):
            with self.assertRaises(tg.TGError) as ctx:
                tg.kirim_video(self.mp4, 'Test')
            self.assertNotIn('TOKEN_SANGAT_RAHASIA', str(ctx.exception))
            self.assertIn('[REDACTED]', str(ctx.exception))


if __name__ == '__main__':
    unittest.main()
