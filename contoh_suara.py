"""Buat contoh suara narasi beberapa voice Gemini TTS untuk dipilih. Hasil MP3 di OUT_DIR."""
import os
import subprocess

import gemini

TEKS = ("Mengapa belajar hukum agama saja terkadang membuat hati terasa kaku? "
        "Ibnul Jauzi rahimahullah menasihati, menyibukkan diri dengan fikih dan hadits saja belum cukup untuk "
        "memperbaiki hati. Mempelajari kisah kehidupan Rasulullah shallallahu 'alaihi wa sallam adalah ramuan "
        "terbaik untuk melembutkan hati yang mengeras.")


def main():
    out = os.environ.get('OUT_DIR', 'hasil')
    os.makedirs(out, exist_ok=True)
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
