"""Cek token IG: akun IG mana saja yang bisa dipakai. Opsional POSTING=path video untuk uji posting."""
import os
import sys

import ig

akun = ig.cari_ig_user_id('sun_nahdaily')
for a in akun:
    print('IG:', a)
if not akun:
    sys.exit('Token tidak melihat akun IG mana pun. Cek Assign assets di system user.')
cocok = [a for a in akun if a[1].lower() == 'sun_nahdaily']
print('IG_USER_ID sun_nahdaily =', cocok[0][0] if cocok else 'TIDAK DITEMUKAN')
