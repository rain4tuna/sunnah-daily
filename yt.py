"""Upload YouTube Shorts lewat YouTube Data API v3 (OAuth refresh token).
Env: YT_CLIENT_ID, YT_CLIENT_SECRET, YT_REFRESH_TOKEN."""
import json
import os
import urllib.error
import urllib.parse
import urllib.request


class YTError(Exception):
    pass


def _token():
    data = urllib.parse.urlencode({
        'client_id': os.environ['YT_CLIENT_ID'], 'client_secret': os.environ['YT_CLIENT_SECRET'],
        'refresh_token': os.environ['YT_REFRESH_TOKEN'], 'grant_type': 'refresh_token'}).encode()
    try:
        with urllib.request.urlopen('https://oauth2.googleapis.com/token', data=data, timeout=60) as r:
            return json.loads(r.read())['access_token']
    except urllib.error.HTTPError as e:
        raise YTError(f'token gagal HTTP {e.code}: {e.read()[:300]!r}') from None


def channel():
    req = urllib.request.Request('https://www.googleapis.com/youtube/v3/channels?part=snippet&mine=true',
                                 headers={'Authorization': f'Bearer {_token()}'})
    with urllib.request.urlopen(req, timeout=60) as r:
        return [(c['id'], c['snippet']['title'], c['snippet'].get('customUrl')) for c in json.loads(r.read()).get('items', [])]


def upload(path, judul, deskripsi, tag=(), kategori='27', privasi='public'):
    """Upload video; kembalikan URL Shorts."""
    tok = _token()
    judul = judul.strip()
    if '#shorts' not in judul.lower():
        judul = (judul[:90] + ' #Shorts')
    meta = {
        'snippet': {'title': judul[:100], 'description': deskripsi[:4900], 'tags': list(tag)[:15],
                    'categoryId': kategori, 'defaultLanguage': 'id', 'defaultAudioLanguage': 'id'},
        'status': {'privacyStatus': privasi, 'selfDeclaredMadeForKids': False, 'embeddable': True},
    }
    ukuran = os.path.getsize(path)
    req = urllib.request.Request(
        'https://www.googleapis.com/upload/youtube/v3/videos?uploadType=resumable&part=snippet,status',
        data=json.dumps(meta).encode(), method='POST',
        headers={'Authorization': f'Bearer {tok}', 'Content-Type': 'application/json; charset=UTF-8',
                 'X-Upload-Content-Type': 'video/mp4', 'X-Upload-Content-Length': str(ukuran)})
    try:
        with urllib.request.urlopen(req, timeout=120) as r:
            lokasi = r.headers['Location']
        with open(path, 'rb') as f:
            req = urllib.request.Request(lokasi, data=f.read(), method='PUT',
                                         headers={'Authorization': f'Bearer {tok}', 'Content-Type': 'video/mp4'})
        with urllib.request.urlopen(req, timeout=900) as r:
            vid = json.loads(r.read())['id']
    except urllib.error.HTTPError as e:
        raise YTError(f'upload gagal HTTP {e.code}: {e.read()[:400]!r}') from None
    return f'https://youtube.com/shorts/{vid}'
