"""Posting ulang video yang sudah ada di branch hasil ke IG. Env: BERKAS (nama tanpa .mp4)."""
import json
import os
import sys

import ig

b = os.environ['BERKAS']
with open(f'{b}_caption.txt') as f:
    cap = f.read()
tujuan = os.environ.get('TUJUAN', 'ig')
try:
    if tujuan in ('ig', 'semua'):
        media = ig.posting_reel_berkas(os.environ.get('IG_USER_ID', '17841438717756877'), f'{b}.mp4', cap)
        print(f'::notice::IG {ig.permalink(media) or media}')
    if tujuan in ('yt', 'semua'):
        import yt
        judul = cap.split('\n')[0].replace('🌙', '').strip()
        print(f"::notice::YouTube {yt.upload(f'{b}.mp4', judul, cap, ['sunnah', 'sirah nabawiyah', 'kisah nabi'])}")
    if tujuan == 'cek-yt':
        import yt
        print(f'::notice::Channel {yt.channel()}')
except Exception as e:
    print(f'::error::{e}'[:1500])
    sys.exit(1)
