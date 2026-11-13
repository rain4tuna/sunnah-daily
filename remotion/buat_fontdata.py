"""Buat ulang src/fontdata.ts dari ../fonts (jalankan setelah mengganti font)."""
import base64
import os

SINI = os.path.dirname(os.path.abspath(__file__))
FONT = [('Fraunces', 'Fraunces-SemiBold.ttf', '600'), ('Poppins', 'Poppins-Medium.ttf', '500'),
        ('Poppins', 'Poppins-SemiBold.ttf', '600'), ('Amiri', 'Amiri-Regular.ttf', '400')]
baris = ['// Dibuat otomatis oleh buat_fontdata.py dari ../fonts: font ditanam supaya render tidak memuat apa pun lewat jaringan.',
         'export const FONTS: { family: string; weight: string; b64: string }[] = [']
for keluarga, berkas, tebal in FONT:
    with open(os.path.join(SINI, '..', 'fonts', berkas), 'rb') as f:
        baris.append(f'  {{ family: "{keluarga}", weight: "{tebal}", b64: "{base64.b64encode(f.read()).decode()}" }},')
baris.append('];')
with open(os.path.join(SINI, 'src', 'fontdata.ts'), 'w', encoding='utf-8', newline='\n') as f:
    f.write('\n'.join(baris) + '\n')
print('src/fontdata.ts diperbarui')
