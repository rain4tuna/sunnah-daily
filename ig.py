"""Instagram Graph API (lewat token system user / halaman Facebook)."""
import json
import os
import time
import urllib.error
import urllib.parse
import urllib.request

VERSI = os.environ.get('GRAPH_VERSION', 'v26.0')
BASE = f'https://graph.facebook.com/{VERSI}'


class IGError(Exception):
    pass


def _req(method, path, params=None, token=None):
    params = dict(params or {})
    params['access_token'] = token or os.environ['IG_TOKEN']
    data = urllib.parse.urlencode(params)
    url = f'{BASE}/{path.lstrip("/")}'
    if method == 'GET':
        req = urllib.request.Request(url + '?' + data)
    else:
        req = urllib.request.Request(url, data=data.encode(), method=method)
    try:
        with urllib.request.urlopen(req, timeout=60) as r:
            return json.loads(r.read())
    except urllib.error.HTTPError as e:
        try:
            err = json.loads(e.read()).get('error', {})
            pesan = f"{err.get('type','')} {err.get('code','')}/{err.get('error_subcode','')}: {err.get('message','')}"
        except Exception:
            pesan = str(e)
        raise IGError(f'HTTP {e.code} {path.split("?")[0]} -> {pesan}') from None


def get(path, **p):
    return _req('GET', path, p)


def post(path, **p):
    return _req('POST', path, p)


def cari_ig_user_id(username=None):
    """Cari ID akun IG bisnis dari halaman yang bisa diakses token."""
    hasil = get('me/accounts', fields='name,instagram_business_account{id,username}', limit=100)
    akun = []
    for pg in hasil.get('data', []):
        iga = pg.get('instagram_business_account')
        if iga:
            akun.append((iga['id'], iga.get('username', ''), pg.get('name', '')))
    if username:
        akun = [a for a in akun if a[1].lower() == username.lower().lstrip('@')] or akun
    return akun


def tunggu_container(cid, maks_detik=300):
    t0 = time.time()
    while time.time() - t0 < maks_detik:
        st = get(cid, fields='status_code,status')
        kode = st.get('status_code')
        if kode == 'FINISHED':
            return
        if kode in ('ERROR', 'EXPIRED'):
            raise IGError(f'container {cid} {kode}: {st.get("status")}')
        time.sleep(8)
    raise IGError(f'container {cid} belum selesai setelah {maks_detik} detik')


def posting_reel_berkas(ig_id, path, caption, share_to_feed=True):
    """Unggah Reel langsung dari berkas lokal (resumable upload), tanpa hosting luar."""
    c = post(f'{ig_id}/media', media_type='REELS', upload_type='resumable', caption=caption,
             share_to_feed='true' if share_to_feed else 'false')
    ukuran = os.path.getsize(path)
    with open(path, 'rb') as f:
        data = f.read()
    req = urllib.request.Request(
        f'https://rupload.facebook.com/ig-api-upload/{VERSI}/{c["id"]}', data=data, method='POST',
        headers={'Authorization': f'OAuth {os.environ["IG_TOKEN"]}', 'offset': '0', 'file_size': str(ukuran),
                 'Content-Type': 'application/octet-stream'})
    try:
        with urllib.request.urlopen(req, timeout=600) as r:
            hasil = json.loads(r.read())
    except urllib.error.HTTPError as e:
        raise IGError(f'upload gagal HTTP {e.code}: {e.read()[:300]!r}') from None
    if not hasil.get('success', True):
        raise IGError(f'upload gagal: {hasil}')
    tunggu_container(c['id'], 600)
    return post(f'{ig_id}/media_publish', creation_id=c['id'])['id']


def posting_reel(ig_id, video_url, caption, share_to_feed=True):
    c = post(f'{ig_id}/media', media_type='REELS', video_url=video_url, caption=caption,
             share_to_feed='true' if share_to_feed else 'false')
    tunggu_container(c['id'])
    return post(f'{ig_id}/media_publish', creation_id=c['id'])['id']


def posting_carousel(ig_id, image_urls, caption):
    anak = []
    for u in image_urls[:10]:
        anak.append(post(f'{ig_id}/media', image_url=u, is_carousel_item='true')['id'])
    for a in anak:
        tunggu_container(a, 120)
    c = post(f'{ig_id}/media', media_type='CAROUSEL', children=','.join(anak), caption=caption)
    tunggu_container(c['id'], 120)
    return post(f'{ig_id}/media_publish', creation_id=c['id'])['id']


def permalink(media_id):
    try:
        return get(media_id, fields='permalink').get('permalink', '')
    except IGError:
        return ''
