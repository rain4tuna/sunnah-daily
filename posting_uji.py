"""Posting ulang video yang sudah ada di branch hasil ke IG. Env: BERKAS (nama tanpa .mp4)."""
import json
import os
import sys

import ig

b = os.environ['BERKAS']
with open(f'{b}_caption.txt') as f:
    cap = f.read()
try:
    media = ig.posting_reel_berkas(os.environ.get('IG_USER_ID', '17841438717756877'), f'{b}.mp4', cap)
except Exception as e:
    print(f'::error::{e}'[:1500])
    sys.exit(1)
link = ig.permalink(media) or media
print(f'::notice::Diposting {link}')
