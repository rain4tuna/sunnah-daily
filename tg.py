"""Kirim video MP4 + caption TikTok otomatis ke Telegram pribadi (Opsi C, 0 ribet audit developer).

Env:
  TG_BOT_TOKEN   token bot Telegram dari @BotFather
  TG_CHAT_ID     chat_id tujuan (user ID pribadi / grup / channel)
  TG_DRY_RUN     true = validasi berkas & payload tanpa memanggil API Telegram
"""
import json
import os
import time
import urllib.error
import urllib.request
import uuid

API = 'https://api.telegram.org'
MAX_VIDEO_CAPTION = 1024
MAX_MSG_TEXT = 4096


class TGError(Exception):
    pass


def _env_bool(nama, default=False):
    val = os.environ.get(nama)
    if val is None or not str(val).strip():
        return default
    return str(val).strip().lower() in ('1', 'true', 'yes', 'ya', 'on')


def _redact(teks):
    """Pastikan TG_BOT_TOKEN tidak pernah muncul di log atau pesan error."""
    out = str(teks or '')
    tok = (os.environ.get('TG_BOT_TOKEN') or '').strip()
    if tok and len(tok) >= 6:
        out = out.replace(tok, '[REDACTED]')
    return out


def konfigurasi_siap():
    """True bila TG_BOT_TOKEN dan TG_CHAT_ID keduanya terisi."""
    return bool((os.environ.get('TG_BOT_TOKEN') or '').strip() and (os.environ.get('TG_CHAT_ID') or '').strip())


def _token_chat():
    tok = (os.environ.get('TG_BOT_TOKEN') or '').strip()
    cid = (os.environ.get('TG_CHAT_ID') or '').strip()
    if not tok or not cid:
        raise TGError('Konfigurasi Telegram belum lengkap: set TG_BOT_TOKEN dan TG_CHAT_ID.')
    return tok, cid


def _request_dengan_retry(make_req, konteks, percobaan=3, timeout=300):
    galat = None
    for coba in range(percobaan):
        req = make_req()
        try:
            with urllib.request.urlopen(req, timeout=timeout) as r:
                raw = r.read().decode('utf-8', errors='replace')
                data = json.loads(raw) if raw.strip() else {}
                if not data.get('ok', True):
                    raise TGError(f'{konteks} ditolak Telegram: {_redact(data.get("description") or data)}')
                return data.get('result') if 'result' in data else data
        except urllib.error.HTTPError as e:
            badan = _redact(e.read().decode('utf-8', errors='replace')[:300])
            galat = f'HTTP {e.code}: {badan}'
            if e.code not in (429, 500, 502, 503, 504):
                raise TGError(f'{konteks} gagal: {galat}') from None
        except urllib.error.URLError as e:
            galat = _redact(e)
        except TGError:
            raise
        time.sleep(min(20, 2 * (coba + 1)))
    raise TGError(f'{konteks} gagal setelah {percobaan}x: {galat}')


def _json_post(url, body, konteks, timeout=60):
    payload = json.dumps(body).encode('utf-8')

    def make_req():
        return urllib.request.Request(
            url,
            data=payload,
            method='POST',
            headers={'Content-Type': 'application/json; charset=UTF-8'},
        )

    return _request_dengan_retry(make_req, konteks, timeout=timeout)


def _multipart_post(url, fields, file_field, filename, file_bytes, content_type='video/mp4', timeout=300):
    """Kirim request RFC 7578 multipart/form-data memakai stdlib Python saja."""
    boundary = f'----SunnahDailyTG{uuid.uuid4().hex}'
    parts = []
    for k, v in (fields or {}).items():
        parts.append(
            (
                f'--{boundary}\r\n'
                f'Content-Disposition: form-data; name="{k}"\r\n\r\n'
                f'{v}\r\n'
            ).encode('utf-8')
        )
    safe_name = os.path.basename(filename).replace('"', '').replace('\r', '').replace('\n', '') or 'video.mp4'
    parts.append(
        (
            f'--{boundary}\r\n'
            f'Content-Disposition: form-data; name="{file_field}"; filename="{safe_name}"\r\n'
            f'Content-Type: {content_type}\r\n\r\n'
        ).encode('utf-8')
    )
    parts.append(file_bytes)
    parts.append(f'\r\n--{boundary}--\r\n'.encode('utf-8'))
    body = b''.join(parts)

    def make_req():
        return urllib.request.Request(
            url,
            data=body,
            method='POST',
            headers={
                'Content-Type': f'multipart/form-data; boundary={boundary}',
                'Content-Length': str(len(body)),
            },
        )

    return _request_dengan_retry(make_req, 'sendVideo', timeout=timeout)


def kirim_video(path, caption_tt, judul='', dry_run=None):
    """Kirim MP4 ke Telegram pribadi lalu kirim caption TikTok lengkap sebagai pesan terpisah agar mudah di-copy."""
    if not path or not os.path.isfile(path):
        raise TGError(f'Berkas video tidak ditemukan: {path}')
    if not str(path).lower().endswith('.mp4'):
        raise TGError(f'Format video Telegram harus .mp4, diterima: {path}')
    ukuran = os.path.getsize(path)
    if ukuran <= 0:
        raise TGError('Ukuran file video tidak valid (0 byte).')

    is_dry = _env_bool('TG_DRY_RUN', False) if dry_run is None else bool(dry_run)
    if is_dry:
        return f'tg://dry-run/{ukuran}bytes'

    tok, cid = _token_chat()
    with open(path, 'rb') as f:
        data_video = f.read()

    judul_ringkas = ' '.join(str(judul or os.path.splitext(os.path.basename(path))[0]).split())
    header_video = f'Siap Share ke TikTok — {judul_ringkas}'[:MAX_VIDEO_CAPTION]
    res_video = _multipart_post(
        f'{API}/bot{tok}/sendVideo',
        fields={
            'chat_id': cid,
            'supports_streaming': 'true',
            'caption': header_video,
        },
        file_field='video',
        filename=os.path.basename(path),
        file_bytes=data_video,
        content_type='video/mp4',
    )
    msg_id = (res_video or {}).get('message_id', '')

    teks_caption = (caption_tt or '').strip()
    if teks_caption:
        _json_post(
            f'{API}/bot{tok}/sendMessage',
            {'chat_id': cid, 'text': teks_caption[:MAX_MSG_TEXT]},
            konteks='sendMessage',
        )
    return f'tg://sent/{cid}/{msg_id}'


def cek_bot():
    """Cek validitas TG_BOT_TOKEN lewat getMe (aman, tanpa mencetak token)."""
    tok, _ = _token_chat()

    def make_req():
        return urllib.request.Request(f'{API}/bot{tok}/getMe', method='GET')

    res = _request_dengan_retry(make_req, 'getMe', timeout=30)
    return {
        'id': (res or {}).get('id'),
        'username': (res or {}).get('username', ''),
        'first_name': (res or {}).get('first_name', ''),
    }
