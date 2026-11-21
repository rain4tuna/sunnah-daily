"""Posting otonom ke TikTok lewat TikTok Content Posting API v2 (stdlib Python, tanpa dependensi tambahan).

Env:
  TT_ACCESS_TOKEN    opsional bila memakai token langsung; bila kosong akan refresh otomatis via OAuth2
  TT_CLIENT_KEY      wajib untuk refresh token OAuth2
  TT_CLIENT_SECRET   wajib untuk refresh token OAuth2
  TT_REFRESH_TOKEN   wajib untuk refresh token OAuth2
  TT_MODE            direct (default: langsung posting) | inbox (kirim ke draft/inbox TikTok)
  TT_PRIVACY         SELF_ONLY (default aman untuk aplikasi belum diaudit) | PUBLIC_TO_EVERYONE
                     | MUTUAL_FOLLOW_FRIENDS | FOLLOWER_OF_CREATOR
  TT_DISABLE_DUET    true | false (default false)
  TT_DISABLE_STITCH  true | false (default false)
  TT_DISABLE_COMMENT true | false (default false)
  TT_DRY_RUN         true = validasi berkas, ukuran chunk, dan payload tanpa memanggil API TikTok
"""
import json
import math
import os
import time
import urllib.error
import urllib.parse
import urllib.request

BASE = 'https://open.tiktokapis.com/v2'
OAUTH_TOKEN_URL = f'{BASE}/oauth/token/'
CREATOR_INFO_URL = f'{BASE}/post/creator_info/query/'
DIRECT_INIT_URL = f'{BASE}/post/publish/video/init/'
INBOX_INIT_URL = f'{BASE}/post/publish/inbox/video/init/'
STATUS_URL = f'{BASE}/post/publish/status/fetch/'

MIN_CHUNK = 5 * 1024 * 1024       # 5 MB batas minimum chunk TikTok bila multi-chunk
MAX_CHUNK = 64 * 1024 * 1024      # 64 MB batas maksimum chunk TikTok
MAX_CAPTION = 2200
PRIVACY_VALID = {'SELF_ONLY', 'PUBLIC_TO_EVERYONE', 'MUTUAL_FOLLOW_FRIENDS', 'FOLLOWER_OF_CREATOR'}


class TTError(Exception):
    pass


def _env_bool(nama, default=False):
    val = os.environ.get(nama)
    if val is None or not str(val).strip():
        return default
    return str(val).strip().lower() in ('1', 'true', 'yes', 'ya', 'on')


def _redact(teks):
    """Pastikan tidak ada token atau secret TikTok yang tercetak di log/exception."""
    out = str(teks or '')
    for k in ('TT_ACCESS_TOKEN', 'TT_REFRESH_TOKEN', 'TT_CLIENT_SECRET'):
        val = os.environ.get(k) or ''
        if val and len(val) >= 6:
            out = out.replace(val, '[REDACTED]')
    return out


def konfigurasi_siap():
    """True bila akses token langsung atau pasangan lengkap OAuth2 refresh tersedia."""
    if (os.environ.get('TT_ACCESS_TOKEN') or '').strip():
        return True
    return all((os.environ.get(k) or '').strip() for k in ('TT_CLIENT_KEY', 'TT_CLIENT_SECRET', 'TT_REFRESH_TOKEN'))


def _json_post(url, body=None, token=None, form=False, timeout=60):
    if form:
        data = urllib.parse.urlencode(body or {}).encode('utf-8')
        headers = {'Content-Type': 'application/x-www-form-urlencoded'}
    else:
        data = json.dumps(body if body is not None else {}).encode('utf-8')
        headers = {'Content-Type': 'application/json; charset=UTF-8'}
    if token:
        headers['Authorization'] = f'Bearer {token}'
    req = urllib.request.Request(url, data=data, method='POST', headers=headers)
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            raw = r.read().decode('utf-8', errors='replace')
            return json.loads(raw) if raw.strip() else {}
    except urllib.error.HTTPError as e:
        badan = e.read().decode('utf-8', errors='replace')[:400]
        raise TTError(f'HTTP {e.code} {url.split("/")[-2]}: {_redact(badan)}') from None
    except urllib.error.URLError as e:
        raise TTError(f'Koneksi TikTok gagal: {_redact(e)}') from None


def _cek_error_api(resp, konteks):
    err = resp.get('error') if isinstance(resp, dict) else None
    if isinstance(err, dict):
        code = str(err.get('code') or '').lower()
        if code and code != 'ok':
            msg = _redact(err.get('message') or err.get('log_id') or '')
            raise TTError(f'{konteks} ditolak TikTok ({code}): {msg}')
    if isinstance(resp, dict) and resp.get('error') and isinstance(resp.get('error'), str):
        raise TTError(f'{konteks} gagal: {_redact(resp.get("error_description") or resp.get("error"))}')


def refresh_token():
    """Tukar TT_REFRESH_TOKEN menjadi access_token baru lewat OAuth2 v2."""
    kunci = (os.environ.get('TT_CLIENT_KEY') or '').strip()
    rahasia = (os.environ.get('TT_CLIENT_SECRET') or '').strip()
    ref = (os.environ.get('TT_REFRESH_TOKEN') or '').strip()
    if not (kunci and rahasia and ref):
        raise TTError('Kredensial TikTok belum lengkap: set TT_ACCESS_TOKEN atau TT_CLIENT_KEY + TT_CLIENT_SECRET + TT_REFRESH_TOKEN.')
    resp = _json_post(OAUTH_TOKEN_URL, {
        'client_key': kunci,
        'client_secret': rahasia,
        'grant_type': 'refresh_token',
        'refresh_token': ref,
    }, form=True)
    _cek_error_api(resp, 'oauth_refresh')
    tok = resp.get('access_token') or (resp.get('data') or {}).get('access_token')
    if not tok:
        raise TTError('oauth_refresh tidak mengembalikan access_token.')
    return tok


def get_token():
    tok = (os.environ.get('TT_ACCESS_TOKEN') or '').strip()
    return tok if tok else refresh_token()


def creator_info(token):
    """Ambil info kreator TikTok (opsi privasi, batas durasi video, status izin posting)."""
    resp = _json_post(CREATOR_INFO_URL, {}, token=token)
    _cek_error_api(resp, 'creator_info')
    return resp.get('data') or {}


def hitung_chunk(ukuran, maks_chunk=None):
    """Hitung (chunk_size, total_chunk_count) sesuai aturan TikTok Content Posting API v2.
    - Video <= 64 MB diunggah dalam 1 chunk utuh (paling cepat & andal untuk Shorts/Reels 9:16).
    - Video > 64 MB dibagi ke chunk [5 MB..64 MB]; sisa byte akhir (< chunk_size) digabung ke chunk terakhir
      (aturan resmi TikTok: total_chunk_count = floor(video_size / chunk_size), chunk akhir bisa > chunk_size hingga 128 MB).
    """
    if ukuran <= 0:
        raise TTError('Ukuran file video tidak valid (0 byte).')
    batas = int(maks_chunk or os.environ.get('TT_CHUNK_SIZE') or MAX_CHUNK)
    batas = max(MIN_CHUNK, min(MAX_CHUNK, batas))
    if ukuran <= batas:
        return ukuran, 1
    total = ukuran // batas
    if total < 1:
        return ukuran, 1
    return batas, total


def _upload_chunks(upload_url, path, ukuran, chunk_size, total_chunks, percobaan=3):
    """Unggah seluruh chunk ke upload_url memakai Content-Range tepat sesuai spesifikasi TikTok."""
    with open(path, 'rb') as f:
        for i in range(total_chunks):
            mulai = i * chunk_size
            # Chunk terakhir mengambil seluruh sisa byte agar tidak ada potongan < 5 MB di akhir
            akhir = ukuran - 1 if i == total_chunks - 1 else (mulai + chunk_size - 1)
            panjang = akhir - mulai + 1
            f.seek(mulai)
            potongan = f.read(panjang)
            if len(potongan) != panjang:
                raise TTError(f'Gagal membaca chunk {i + 1}/{total_chunks} dari {path}')
            headers = {
                'Content-Type': 'video/mp4',
                'Content-Length': str(panjang),
                'Content-Range': f'bytes {mulai}-{akhir}/{ukuran}',
            }
            galat = None
            for coba in range(percobaan):
                req = urllib.request.Request(upload_url, data=potongan, method='PUT', headers=headers)
                try:
                    with urllib.request.urlopen(req, timeout=300) as r:
                        if r.status in (200, 201, 206):
                            galat = None
                            break
                        galat = f'HTTP {r.status}'
                except urllib.error.HTTPError as e:
                    galat = f'HTTP {e.code} {_redact(e.read().decode("utf-8", errors="replace")[:200])}'
                    if e.code not in (429, 500, 502, 503, 504):
                        raise TTError(f'Upload chunk {i + 1}/{total_chunks} gagal: {galat}') from None
                except urllib.error.URLError as e:
                    galat = _redact(e)
                time.sleep(min(30, 3 * (coba + 1)))
            if galat is not None:
                raise TTError(f'Upload chunk {i + 1}/{total_chunks} gagal setelah {percobaan}x: {galat}')


def tunggu_publish(token, publish_id, maks_detik=240, jeda=5):
    """Polling status publish sampai selesai atau gagal."""
    t0 = time.time()
    terakhir = {}
    while time.time() - t0 < maks_detik:
        resp = _json_post(STATUS_URL, {'publish_id': publish_id}, token=token)
        _cek_error_api(resp, 'publish_status')
        data = resp.get('data') or {}
        terakhir = data
        st = str(data.get('status') or '').upper()
        if st in ('PUBLISH_COMPLETE', 'SEND_TO_USER_INBOX'):
            return data
        if st == 'FAILED':
            alasan = _redact(data.get('fail_reason') or 'unknown')
            raise TTError(f'Publish TikTok gagal ({publish_id}): {alasan}')
        time.sleep(jeda)
    raise TTError(f'Timeout menunggu status publish TikTok ({publish_id}): {terakhir}')


def _pilih_privasi(diminta, opsi_kreator):
    priv = (diminta or os.environ.get('TT_PRIVACY') or 'SELF_ONLY').strip().upper()
    if priv not in PRIVACY_VALID:
        priv = 'SELF_ONLY'
    if opsi_kreator and priv not in opsi_kreator:
        return 'SELF_ONLY' if 'SELF_ONLY' in opsi_kreator else opsi_kreator[0]
    return priv


def upload(path, caption, mode=None, privacy=None, dry_run=None, percobaan=3):
    """Unggah MP4 9:16 ke TikTok (Direct Post atau Inbox Draft) dan kembalikan tautan/ID hasil."""
    if not path or not os.path.isfile(path):
        raise TTError(f'Berkas video tidak ditemukan: {path}')
    if not str(path).lower().endswith('.mp4'):
        raise TTError(f'Format video TikTok harus .mp4, diterima: {path}')
    ukuran = os.path.getsize(path)
    chunk_size, total_chunks = hitung_chunk(ukuran)
    judul = ' '.join((caption or '').strip().splitlines())[:MAX_CAPTION]
    # Pertahankan baris baru bila pendek, tetap hormati batas 2200 karakter TikTok
    cap_bersih = (caption or '').strip()[:MAX_CAPTION] or judul
    mode_v = (mode or os.environ.get('TT_MODE') or 'direct').strip().lower()
    if mode_v not in ('direct', 'inbox'):
        raise TTError(f'TT_MODE tidak dikenal: {mode_v} (pilih direct atau inbox)')
    is_dry = _env_bool('TT_DRY_RUN', False) if dry_run is None else bool(dry_run)

    source_info = {
        'source': 'FILE_UPLOAD',
        'video_size': ukuran,
        'chunk_size': chunk_size,
        'total_chunk_count': total_chunks,
    }
    priv_awal = _pilih_privasi(privacy, None)
    payload_preview = {
        'mode': mode_v,
        'source_info': source_info,
        'post_info': {
            'title': cap_bersih,
            'privacy_level': priv_awal,
            'disable_duet': _env_bool('TT_DISABLE_DUET', False),
            'disable_comment': _env_bool('TT_DISABLE_COMMENT', False),
            'disable_stitch': _env_bool('TT_DISABLE_STITCH', False),
        } if mode_v == 'direct' else None,
    }
    if is_dry:
        return f'tiktok://dry-run/{mode_v}/{priv_awal}/{total_chunks}chunks'

    tok = get_token()
    info = creator_info(tok)
    if mode_v == 'direct':
        priv_final = _pilih_privasi(privacy, info.get('privacy_level_options') or [])
        body = {
            'post_info': {
                'title': cap_bersih,
                'privacy_level': priv_final,
                'disable_duet': _env_bool('TT_DISABLE_DUET', False),
                'disable_comment': _env_bool('TT_DISABLE_COMMENT', False),
                'disable_stitch': _env_bool('TT_DISABLE_STITCH', False),
            },
            'source_info': source_info,
        }
        init_url = DIRECT_INIT_URL
    else:
        body = {'source_info': source_info}
        init_url = INBOX_INIT_URL

    init_resp = _json_post(init_url, body, token=tok)
    _cek_error_api(init_resp, 'publish_init')
    data = init_resp.get('data') or {}
    publish_id = data.get('publish_id')
    upload_url = data.get('upload_url')
    if not publish_id or not upload_url:
        raise TTError('publish_init tidak mengembalikan publish_id/upload_url.')

    _upload_chunks(upload_url, path, ukuran, chunk_size, total_chunks, percobaan=percobaan)
    hasil = tunggu_publish(tok, publish_id)
    post_ids = hasil.get('publicaly_available_post_id') or hasil.get('publicly_available_post_id') or []
    username = (info.get('creator_username') or '').strip().lstrip('@')
    if post_ids and username:
        return f'https://www.tiktok.com/@{username}/video/{post_ids[0]}'
    if post_ids:
        return f'https://www.tiktok.com/video/{post_ids[0]}'
    return f'tiktok://{mode_v}/{publish_id}'


def cek_akun():
    """Cek koneksi kredensial TikTok dan kembalikan info kreator (aman, tanpa mencetak token)."""
    if not konfigurasi_siap():
        raise TTError('Kredensial TikTok belum diset di environment.')
    tok = get_token()
    info = creator_info(tok)
    return {
        'username': info.get('creator_username', ''),
        'nickname': info.get('creator_nickname', ''),
        'privacy_options': info.get('privacy_level_options', []),
        'max_duration_sec': info.get('max_video_post_duration_sec', 0),
    }
