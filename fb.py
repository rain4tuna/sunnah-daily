"""Posting Reel ke Facebook Page "Sunnah Daily" (Graph API video_reels, upload langsung).
Butuh izin token: pages_show_list, pages_read_engagement, pages_manage_posts."""
import os
import time
import urllib.error
import urllib.request

import ig

NAMA_PAGE = os.environ.get('FB_PAGE_NAME', 'Sunnah Daily')


def page():
    """(page_id, page_token) dari token system user."""
    for p in ig.get('me/accounts', fields='id,name,access_token', limit=100).get('data', []):
        if p.get('name', '').strip().lower() == NAMA_PAGE.lower() or p['id'] == os.environ.get('FB_PAGE_ID'):
            return p['id'], p['access_token']
    raise ig.IGError(f'Page "{NAMA_PAGE}" tidak terlihat oleh token')


def posting_reel(path, deskripsi, percobaan=3):
    pid, tok = page()
    ukuran = os.path.getsize(path)
    with open(path, 'rb') as f:
        data = f.read()
    galat = []
    for i in range(percobaan):
        try:
            mulai = ig._req('POST', f'{pid}/video_reels', {'upload_phase': 'start'}, token=tok)
            vid = mulai['video_id']
            req = urllib.request.Request(
                mulai.get('upload_url') or f'https://rupload.facebook.com/video-upload/{ig.VERSI}/{vid}',
                data=data, method='POST',
                headers={'Authorization': f'OAuth {tok}', 'offset': '0', 'file_size': str(ukuran)})
            with urllib.request.urlopen(req, timeout=600) as r:
                r.read()
            ig._req('POST', f'{pid}/video_reels', {'upload_phase': 'finish', 'video_id': vid,
                                                   'video_state': 'PUBLISHED', 'description': deskripsi}, token=tok)
            return f'https://www.facebook.com/reel/{vid}'
        except urllib.error.HTTPError as e:
            galat.append(f'percobaan {i + 1}: HTTP {e.code} {e.read()[:200]!r}')
        except Exception as e:
            galat.append(f'percobaan {i + 1}: {e}')
        print('   FB ' + galat[-1], flush=True)
        time.sleep(20 * (i + 1))
    raise ig.IGError('FB gagal: ' + ' | '.join(galat))
