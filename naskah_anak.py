"""Naskah video panjang versi ceria untuk anak & remaja (dipakai video_panjang.py, GAYA_NASKAH=anak).

Gemini (1 panggilan per kisah, tanpa pencarian) menulis ulang storyboard yang SUDAH diverifikasi menjadi bahasa
yang ceria dan mudah dipahami, plus satu soal kuis. Aturan isi:
- Tidak menambah fakta, nama, angka, tempat, atau kutipan baru. Urutan dan jumlah poin sama dengan storyboard.
- Dalil TIDAK ditulis ulang: tetap narasi_dalil dari data (terjemah + sumber + derajat).
- Hormat: Nabi ﷺ selalu dengan ﷺ, tidak bercanda tentang Allah, Nabi, ayat, atau hadits.
Gagal / tidak valid -> pakai storyboard asli (naskah tetap aman, hanya kurang ceria).

Kalimat episode (pembuka, ajakan di tengah, kuis, penutup) ditulis di sini sebagai templat tetap, bukan oleh Gemini.
"""
import json

import gemini

PROMPT = """Kamu penulis naskah video YouTube "Sunnah Daily" untuk ANAK-ANAK dan REMAJA (8-16 tahun), termasuk penonton
yang belum mengenal Islam. Tulis ulang materi di bawah supaya CERIA, HANGAT, dan MUDAH DIPAHAMI.

MATERI (SUDAH DIVERIFIKASI, satu kisah):
{materi}

ATURAN KERAS:
- JANGAN menambah fakta, nama, angka, tempat, peristiwa, atau kutipan yang tidak ada di materi.
- Boleh menjelaskan singkat istilah yang ADA di materi dengan arti umumnya (mis. "Quraisy, suku besar di kota Makkah").
- Urutan sama dengan materi. Jumlah "poin" HARUS {jumlah}, poin ke-n menceritakan isi poin ke-n materi.
- Tulis "Nabi Muhammad ﷺ" / "Rasulullah ﷺ" dengan simbol ﷺ. Untuk sahabat ikuti materi (mis. radhiyallahu 'anhu).
- Tidak bercanda tentang Allah, Nabi, malaikat, Al-Qur'an, atau hadits. Tidak menakut-nakuti berlebihan.
- Bahasa Indonesia lisan yang santai tapi sopan: kalimat pendek (maks 15 kata), sapa penonton dengan "kamu" atau
  "teman-teman", boleh seruan ringan ("Wah!", "Bayangkan!", "Hebat, kan?"). Jangan menyebut visual, warna, atau ikon.

Kembalikan JSON saja:
{{
 "pancing": "1 kalimat penggoda (maks 16 kata) untuk DETIK PERTAMA video: pertanyaan/teka-teki dari isi materi yang bikin anak penasaran ingin menonton sampai habis, TANPA membocorkan jawabannya, tanpa fakta baru",
 "bab": "1 kalimat pembuka kisah berupa pertanyaan pancingan yang bikin penasaran (maks 14 kata)",
 "poin": [{{"narasi": "1-2 kalimat pendek (total maks 24 kata) menceritakan ulang poin itu; sebut perasaan/perbuatan tokohnya bila ADA di materi (mis. sedih, menangis, marah, gembira, menggali)", "label": "judul layar maks 5 kata"}}],
 "faedah": "1 kalimat (maks 18 kata) 'Pelajaran buat kita: ...' yang nyambung ke kehidupan anak/remaja sehari-hari",
 "kuis": {{"tanya": "1 pertanyaan pendek yang jawabannya ADA di materi",
           "pilihan": ["3 jawaban singkat, maks 6 kata, hanya satu yang benar"], "jawab": 0}}
}}
"jawab" = indeks (0-2) pilihan yang benar."""


def _bersih(t, maks=400):
    return ' '.join(str(t or '').split())[:maks]


def tulis_ulang(k):
    """Kembalikan naskah {'bab','poin':[{'narasi','label'}],'faedah','kuis'} atau None bila gagal/tidak valid."""
    sb = k.get('storyboard_ikon') or {}
    poin = sb.get('poin') or []
    if not poin:
        return None
    materi = json.dumps({
        'judul': k['judul_hook'], 'pembuka': sb.get('hook', {}).get('narasi'),
        'poin': [p['narasi'] for p in poin], 'faedah': k.get('faedah'),
        'dalil_terjemah': (k.get('dalil') or {}).get('terjemah'),
    }, ensure_ascii=False, indent=1)
    try:
        j = gemini.teks(PROMPT.format(materi=materi, jumlah=len(poin)), suhu=0.6)
    except Exception as e:
        gemini.log(f'   naskah anak gagal ({k["id"]}): {e}')
        return None
    p = j.get('poin') if isinstance(j, dict) else None
    if not isinstance(p, list) or len(p) != len(poin) or not all(isinstance(x, dict) and x.get('narasi') for x in p):
        gemini.log(f'   naskah anak tidak valid ({k["id"]}), pakai storyboard asli')
        return None
    hasil = {
        'bab': _bersih(j.get('bab')) or sb.get('hook', {}).get('narasi') or k['judul_hook'],
        'poin': [{'narasi': _bersih(x['narasi']), 'label': _bersih(x.get('label'), 40)} for x in p],
        'faedah': _bersih(j.get('faedah')) or f"Pelajaran buat kita: {k.get('faedah')}",
    }
    if _bersih(j.get('pancing')):
        hasil['pancing'] = _bersih(j.get('pancing'), 160)
    kuis = j.get('kuis') or {}
    pil = [_bersih(x, 60) for x in (kuis.get('pilihan') or []) if str(x).strip()]
    if kuis.get('tanya') and len(pil) == 3 and kuis.get('jawab') in (0, 1, 2):
        hasil['kuis'] = {'tanya': _bersih(kuis['tanya'], 200), 'pilihan': pil, 'jawab': kuis['jawab']}
    return hasil


# ---- kalimat episode (templat tetap) ----
HURUF = 'ABC'


def pembuka(n, topik, no_ep, pancing=None):
    """Salam + penggoda rasa penasaran di detik pertama (pola curiosity gap), lalu janji kuis. Singkat: sapaan
    "selamat datang" dan kredit panjang tidak dibacakan (kredit kajian tetap tampil di layar dan deskripsi)."""
    pancing = pancing or f'Tahukah kamu, apa yang terjadi di zaman {topik}?'
    return (f"Assalamu'alaikum, teman-teman! {pancing} Jawabannya ada di video ini, dan di akhir ada kuis seru. "
            f'Tonton sampai habis, ya!')


AJAK = ('Seru, kan? Kalau kamu suka kisahnya, tekan tombol like dan subscribe, ya, biar nggak ketinggalan kisah '
        'berikutnya. Yuk, kita lanjut!')


def kuis(k):
    q = k['kuis']
    opsi = ' '.join(f'{HURUF[i]}, {p}.' for i, p in enumerate(q['pilihan']))
    return f"Sekarang waktunya kuis! {q['tanya']} {opsi} Tulis jawabanmu di komentar, ya! Kita hitung sampai lima."


def jawab(k):
    q = k['kuis']
    return f"Jawabannya adalah {HURUF[q['jawab']]}, {q['pilihan'][q['jawab']]}! Kamu benar? Hebat!"


PENUTUP = ('Terima kasih sudah menonton sampai habis! Tulis di komentar, kisah mana yang paling kamu suka. '
           'Subscribe Sunnah Daily, dan ajak teman atau adikmu ikut menonton. Sampai jumpa di kisah berikutnya. '
           "Assalamu'alaikum!")
