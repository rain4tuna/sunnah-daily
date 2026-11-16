"""TTS hemat kuota untuk video panjang: beberapa babak dibacakan dalam SATU permintaan Gemini TTS, lalu suaranya
dipotong kembali per babak di jeda hening terpanjang.

Kuota TTS Gemini dibatasi per hari dan dipakai bersama jadwal Shorts. Satu episode panjang (sekitar 50 babak)
cukup sekitar 10-13 permintaan dengan cara ini.

Pengaman: kalau jumlah jeda tidak cukup atau panjang potongan tidak sebanding dengan panjang teksnya,
kelompok itu dibacakan ulang per babak (cara lama), supaya suara tidak pernah tertukar antar babak.
"""
import array
import os
import wave

import gemini

PEMISAH = '\n\n'
INSTRUKSI_JEDA = '; beri jeda hening sekitar satu setengah detik setiap pergantian paragraf'
JEDA_MIN = 0.35        # detik hening minimal yang dianggap kandidat batas babak
BATAS_MIN = 0.75       # jeda batas babak yang dipilih minimal sepanjang ini (jeda kalimat biasa lebih pendek)
JENDELA = 0.02         # detik per jendela RMS
AMBANG_RELATIF = 0.06  # hening = RMS di bawah 6% RMS rata-rata bagian bersuara


def log(*a):
    print(*a, flush=True)


def _baca(path):
    with wave.open(path) as w:
        p = w.getparams()
        data = w.readframes(w.getnframes())
    if p.sampwidth != 2:
        raise ValueError('hanya WAV 16-bit')
    sampel = array.array('h', data)
    if p.nchannels > 1:
        sampel = sampel[::p.nchannels]
    return sampel, p.framerate


def _tulis(path, sampel, rate):
    with wave.open(path, 'wb') as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(rate)
        w.writeframes(sampel.tobytes())


def cari_jeda(sampel, rate):
    """Daftar (mulai, akhir) dalam indeks sampel untuk tiap rentang hening >= JEDA_MIN, tidak di ujung audio."""
    n = max(1, int(rate * JENDELA))
    rms = []
    for i in range(0, len(sampel) - n + 1, n):
        blok = sampel[i:i + n]
        rms.append((sum(x * x for x in blok) / n) ** 0.5)
    if not rms:
        return []
    bersuara = sorted(rms)[len(rms) // 2:]          # separuh jendela terkeras sebagai acuan suara
    acuan = sum(bersuara) / len(bersuara)
    ambang = acuan * AMBANG_RELATIF
    jeda, mulai = [], None
    for j, r in enumerate(rms + [ambang * 10]):      # penjaga supaya rentang terakhir ditutup
        if r < ambang and mulai is None:
            mulai = j
        elif r >= ambang and mulai is not None:
            if (j - mulai) * JENDELA >= JEDA_MIN and mulai > 0 and j < len(rms):
                jeda.append((mulai * n, j * n))
            mulai = None
    return jeda


ALASAN = ''   # alasan terakhir potong() menolak (untuk log)


def _tolak(alasan):
    global ALASAN
    ALASAN = alasan
    return None


def potong(sampel, rate, teks):
    """Potong audio jadi len(teks) bagian di jeda terpanjang. Kembalikan daftar potongan atau None bila meragukan."""
    k = len(teks)
    if k == 1:
        return [sampel]
    jeda = cari_jeda(sampel, rate)
    panjang = sorted(((b - a) / rate for a, b in jeda), reverse=True)
    ringkas = f"audio {len(sampel) / rate:.1f}s, {len(jeda)} jeda, terpanjang {[round(x, 2) for x in panjang[:k + 2]]}"
    if len(jeda) < k - 1:
        return _tolak(f'jeda kurang ({ringkas})')
    # tiap batas babak dicari di sekitar posisi yang diperkirakan dari panjang teks, lalu dipilih jeda terpanjang di
    # sana; jeda di dalam kalimat yang jauh dari perkiraan tidak pernah terpilih
    total_teks = sum(len(t) for t in teks)
    toleransi = max(int(1.5 * rate), int(0.07 * len(sampel)))
    titik, kumulatif, sebelumnya = [0], 0, 0
    for t in teks[:-1]:
        kumulatif += len(t)
        perkiraan = len(sampel) * kumulatif / total_teks
        calon = [(a, b) for a, b in jeda if a > sebelumnya and abs((a + b) / 2 - perkiraan) <= toleransi]
        if not calon:
            return _tolak(f'batas {len(titik)}: tidak ada jeda dekat perkiraan {perkiraan / rate:.1f}s ({ringkas})')
        calon.sort(key=lambda r: r[1] - r[0], reverse=True)
        a, b = calon[0]
        # jeda antar babak harus panjang dan jelas lebih panjang dari jeda kalimat di sekitarnya; kalau tidak,
        # mungkin TTS melewatkan jeda paragraf -> lebih aman dibacakan ulang per babak
        if (b - a) < BATAS_MIN * rate or (len(calon) > 1 and (b - a) < 1.25 * (calon[1][1] - calon[1][0])):
            kedua = (calon[1][1] - calon[1][0]) / rate if len(calon) > 1 else 0
            return _tolak(f'batas {len(titik)}: jeda {(b - a) / rate:.2f}s vs kedua {kedua:.2f}s '
                          f'di sekitar {perkiraan / rate:.1f}s ({ringkas})')
        sebelumnya = b
        titik.append((a + b) // 2)
    titik.append(len(sampel))
    bagian = [sampel[titik[i]:titik[i + 1]] for i in range(k)]
    # cek: panjang tiap potongan harus sebanding dengan panjang teksnya
    total_teks = sum(len(t) for t in teks)
    total_audio = len(sampel)
    for b, t in zip(bagian, teks):
        rasio = (len(b) / total_audio) / (len(t) / total_teks)
        if not 0.45 <= rasio <= 2.2:
            return _tolak(f'rasio panjang {rasio:.2f} ({ringkas})')
    return bagian


def bacakan_kelompok(teks, wav_keluar, tmp, nama='kelompok'):
    """teks: daftar kalimat lisan per babak; wav_keluar: path WAV tujuan per babak.
    Kembalikan jumlah permintaan TTS yang dipakai."""
    assert len(teks) == len(wav_keluar)
    if len(teks) == 1:
        gemini.bacakan(teks[0], wav_keluar[0])
        return 1
    gabung = os.path.join(tmp, f'{nama}.wav')
    gaya_asli = gemini.GAYA_SUARA
    try:
        gemini.GAYA_SUARA = gaya_asli + INSTRUKSI_JEDA
        gemini.bacakan(PEMISAH.join(teks), gabung)
    finally:
        gemini.GAYA_SUARA = gaya_asli
    sampel, rate = _baca(gabung)
    bagian = potong(sampel, rate, teks)
    if bagian is None:
        log(f'   {nama}: jeda antar babak tidak jelas, dibacakan ulang per babak ({len(teks)} permintaan): {ALASAN}')
        for t, w in zip(teks, wav_keluar):
            gemini.bacakan(t, w)
        return 1 + len(teks)
    for b, w in zip(bagian, wav_keluar):
        _tulis(w, b, rate)
    return 1
