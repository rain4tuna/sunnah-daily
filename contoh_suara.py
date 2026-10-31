"""Buat contoh suara narasi beberapa voice Gemini TTS untuk dipilih. Hasil MP3 di OUT_DIR."""
import os
import subprocess

import gemini

TEKS = ("Mengapa belajar hukum agama saja terkadang membuat hati terasa kaku? "
        "Ibnul Jauzi rahimahullah menasihati, menyibukkan diri dengan fikih dan hadits saja belum cukup untuk "
        "memperbaiki hati. Mempelajari kisah kehidupan Rasulullah shallallahu 'alaihi wa sallam adalah ramuan "
        "terbaik untuk melembutkan hati yang mengeras.")


PERSONA = {
    'A_sahabat': 'Kak Faiz, laki-laki 28 tahun, pencerita yang hangat seperti kakak yang bercerita ke adiknya, '
                 'senyum terdengar di suara, tempo sedang, jeda singkat sebelum bagian penting',
    'B_logat_melayu': 'laki-laki 30-an dari Sumatra, sedikit logat Melayu yang lembut, santai dan akrab seperti '
                      'ngobrol di teras masjid selepas isya, tempo sedang',
    'C_dongeng': 'pendongeng laki-laki yang ekspresif, membangun rasa penasaran, suara agak berbisik di bagian '
                 'menegangkan lalu hangat di bagian akhir, tempo mengalir',
    'D_tenang_khusyuk': 'laki-laki muda yang tenang dan lembut, penuh perasaan seperti sedang merenung, tidak berat, '
                        'tidak kaku, tempo sedang, intonasi halus',
}


def main():
    out = os.environ.get('OUT_DIR', 'hasil')
    os.makedirs(out, exist_ok=True)
    if os.environ.get('MODE') == 'persona':
        gemini.SUARA = os.environ.get('SUARA', 'Zubenelgenubi')
        for nama, gaya in PERSONA.items():
            gemini.GAYA_SUARA = gaya
            wav = os.path.join(out, f'{nama}.wav')
            try:
                gemini.bacakan(TEKS, wav)
                subprocess.run(['ffmpeg', '-y', '-loglevel', 'error', '-i', wav, '-b:a', '128k',
                                os.path.join(out, f'persona_{nama}.mp3')], check=True)
                os.remove(wav)
            except Exception as e:
                gemini.log(f'gagal {nama}: {e}')
        return
    for v in os.environ.get('SUARA_LIST', 'Puck,Achird,Umbriel,Sadachbia,Zubenelgenubi').split(','):
        v = v.strip()
        gemini.SUARA = v
        wav = os.path.join(out, f'{v}.wav')
        try:
            gemini.bacakan(TEKS, wav)
            subprocess.run(['ffmpeg', '-y', '-loglevel', 'error', '-i', wav, '-b:a', '128k',
                            os.path.join(out, f'suara_{v}.mp3')], check=True)
            os.remove(wav)
            gemini.log(f'ok {v}')
        except Exception as e:
            gemini.log(f'gagal {v}: {e}')


if __name__ == '__main__':
    main()
