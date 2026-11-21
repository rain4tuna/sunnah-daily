"""Posting ulang video yang sudah ada di branch hasil ke IG, FB, YT, atau TikTok. Env: BERKAS (nama tanpa .mp4)."""
import os
import sys

import ig


def _baca(path, cadangan=''):
    if os.path.exists(path):
        with open(path, encoding='utf-8') as f:
            return f.read()
    return cadangan


def jalankan():
    tujuan = os.environ.get('TUJUAN', 'ig')
    if tujuan == 'cek-yt':
        import yt
        print(f'::notice::Channel {yt.channel()}')
        return
    if tujuan == 'cek-tt':
        import tt
        print(f'::notice::TikTok {tt.cek_akun()}')
        return
    if tujuan == 'cek-tg':
        import tg
        print(f'::notice::Telegram {tg.cek_bot()}')
        return
    b = os.environ['BERKAS']
    cap = _baca(f'{b}_caption.txt')
    cap_ig = _baca(f'{b}_caption_ig.txt', cap)
    cap_fb = _baca(f'{b}_caption_fb.txt', cap)
    cap_yt = _baca(f'{b}_caption_yt.txt', cap)
    cap_tt = _baca(f'{b}_caption_tt.txt', cap)
    if tujuan in ('ig', 'semua'):
        media = ig.posting_reel_aman(os.environ.get('IG_USER_ID', '17841438717756877'), f'{b}.mp4', cap_ig)
        print(f'::notice::IG {ig.permalink(media) or media}')
    if tujuan in ('fb', 'semua'):
        import fb
        print(f"::notice::FB {fb.posting_reel(f'{b}.mp4', cap_fb)}")
    if tujuan in ('yt', 'semua'):
        import yt
        judul = cap_yt.split('\n')[0].replace('🌙', '').strip()
        print(f"::notice::YouTube {yt.upload(f'{b}.mp4', judul, cap_yt, ['sunnah', 'sirah nabawiyah', 'kisah nabi'])}")
    if tujuan == 'tt' or (tujuan == 'semua' and (os.environ.get('TT_DRY_RUN', '').lower() == 'true' or __import__('tt').konfigurasi_siap())):
        import tt
        print(f"::notice::TikTok {tt.upload(f'{b}.mp4', cap_tt)}")
    if tujuan == 'tg' or (tujuan == 'semua' and (os.environ.get('TG_DRY_RUN', '').lower() == 'true' or __import__('tg').konfigurasi_siap())):
        import tg
        judul_tg = (cap_tt.splitlines()[0] if cap_tt else b).strip()
        print(f"::notice::Telegram {tg.kirim_video(f'{b}.mp4', cap_tt, judul=judul_tg)}")


if __name__ == '__main__':
    try:
        jalankan()
    except Exception as e:
        print(f'::error::{e}'[:1500])
        sys.exit(1)
