"""Cek token IG: siapa pemiliknya, izin apa saja, Page & akun IG mana yang terlihat."""
import os
import sys

import ig


def coba(label, fn):
    try:
        r = fn()
        print(f'{label}: {r}')
        return r
    except Exception as e:
        print(f'{label}: GAGAL {e}')
        return None


coba('me', lambda: ig.get('me', fields='id,name'))
coba('izin', lambda: [p['permission'] + '=' + p['status'] for p in ig.get('me/permissions').get('data', [])])
hal = coba('pages', lambda: ig.get('me/accounts', fields='id,name,instagram_business_account{id,username}',
                                   limit=100).get('data', []))
for pg in hal or []:
    iga = pg.get('instagram_business_account')
    if iga:
        print(f"IG_USER_ID {iga.get('username')} = {iga['id']}")
    else:
        coba(f"page {pg['name']} ig", lambda: ig.get(pg['id'], fields='instagram_business_account,connected_instagram_account'))
