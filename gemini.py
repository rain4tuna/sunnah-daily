"""Pemanggil Gemini: teks (opsional dengan video YouTube), Google Search (Interactions API) dan TTS."""
import base64
import json
import os
import re
import time
import urllib.error
import urllib.request
import wave

API = 'https://generativelanguage.googleapis.com/v1beta'
MODEL_TEKS = os.environ.get('MODEL_TEKS', 'gemini-3.8-flash')
MODEL_TTS = os.environ.get('MODEL_TTS', 'gemini-3.8-flash-tts')
SUARA = os.environ.get('SUARA', 'Zubenelgenubi')
GAYA_SUARA = os.environ.get('GAYA_SUARA') or (
    'laki-laki muda Indonesia yang sedang bercerita ke teman dekat: hangat, ringan, ekspresif dan mengalir '
    'natural seperti ngobrol, tempo sedang cenderung cepat, intonasi naik-turun hidup, jeda singkat saja, '
    'tidak berat, tidak kaku, tidak seperti membaca teks')


def log(*a):
    print(*a, flush=True)


def _kunci():
    return os.environ['GEMINI_API_KEY']


def _post(url, body, timeout=300):
    req = urllib.request.Request(url, data=json.dumps(body).encode(), method='POST',
                                 headers={'Content-Type': 'application/json', 'x-goog-api-key': _kunci()})
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            return json.loads(r.read())
    except urllib.error.HTTPError as e:
        raise RuntimeError(f'HTTP {e.code}: {e.read()[:500]!r}') from None


def ambil_json(teks):
    teks = re.sub(r'^```(?:json)?|```$', '', teks.strip(), flags=re.M)
    m = re.search(r'[\{\[].*[\}\]]', teks, re.S)
    if not m:
        raise ValueError('Gemini tidak mengembalikan JSON: ' + teks[:300])
    return json.loads(m.group(0))


def teks(prompt, video=None, mulai=None, akhir=None, json_mode=True, suhu=0.4, coba=3):
    """Panggil generateContent. video = URL YouTube publik (Gemini menontonnya langsung)."""
    parts = []
    if video:
        p = {'file_data': {'file_uri': video, 'mime_type': 'video/*'}}
        if mulai is not None or akhir is not None:
            p['video_metadata'] = {}
            if mulai is not None:
                p['video_metadata']['start_offset'] = f'{int(mulai)}s'
            if akhir is not None:
                p['video_metadata']['end_offset'] = f'{int(akhir)}s'
        parts.append(p)
    parts.append({'text': prompt})
    cfg = {'temperature': suhu}
    if json_mode:
        cfg['responseMimeType'] = 'application/json'
    if video:
        cfg['mediaResolution'] = 'MEDIA_RESOLUTION_LOW'
    body = {'contents': [{'role': 'user', 'parts': parts}], 'generationConfig': cfg}
    galat = None
    for i in range(coba):
        try:
            j = _post(f'{API}/models/{MODEL_TEKS}:generateContent', body, timeout=900)
            cand = (j.get('candidates') or [{}])[0]
            hasil = ''.join(p.get('text', '') for p in (cand.get('content') or {}).get('parts', [])
                            if not p.get('thought'))
            if hasil.strip():
                return ambil_json(hasil) if json_mode else hasil
            galat = 'respons kosong: ' + json.dumps(j)[:300]
        except Exception as e:
            galat = e
        log(f'   Gemini percobaan {i + 1} gagal: {galat}')
        time.sleep(10 * (i + 1))
    raise RuntimeError(f'Gemini gagal: {galat}')


def cari(prompt, coba=3):
    """Gemini + Google Search lewat Interactions API. Kembalikan (teks, sumber[{judul, uri}])."""
    galat = None
    for i in range(coba):
        try:
            j = _post(f'{API}/interactions', {'model': MODEL_TEKS, 'input': prompt,
                                              'tools': [{'type': 'google_search'}]}, timeout=400)
            keluaran, sumber, kueri = [], [], []

            def jelajah(o):
                if isinstance(o, dict):
                    tipe = o.get('type')
                    if tipe == 'google_search_call':
                        kueri.extend(((o.get('arguments') or {}).get('queries')) or [])
                    if tipe == 'url_citation' and o.get('url'):
                        sumber.append({'judul': o.get('title') or o['url'], 'uri': o['url']})
                    if tipe == 'thought':
                        return
                    if tipe == 'text' and isinstance(o.get('text'), str):
                        keluaran.append(o['text'])
                    for v in o.values():
                        jelajah(v)
                elif isinstance(o, list):
                    for v in o:
                        jelajah(v)

            langkah = j.get('steps')
            if isinstance(langkah, list):
                for st in langkah:
                    if isinstance(st, dict) and st.get('type') in ('model_output', 'google_search_call'):
                        jelajah(st)
            else:
                jelajah(j.get('outputs') or j.get('output') or j)
            hasil = '\n'.join(keluaran)
            log(f'   Google Search: {len(kueri)} kueri, {len(sumber)} sitasi')
            if hasil.strip() and (sumber or kueri):
                return hasil, sumber
            galat = f'tanpa pencarian (kueri={len(kueri)})'
        except Exception as e:
            galat = e
        time.sleep(8 * (i + 1))
    raise RuntimeError(f'Google Search gagal: {galat}')


def _cari_audio(obj):
    if isinstance(obj, dict):
        mime = str(obj.get('mime_type') or obj.get('mimeType') or '')
        data = obj.get('data')
        if data and isinstance(data, str) and ('audio' in mime or len(data) > 5000):
            return mime, data
        for v in obj.values():
            r = _cari_audio(v)
            if r:
                return r
    elif isinstance(obj, list):
        for v in obj:
            r = _cari_audio(v)
            if r:
                return r
    return None


def _simpan_wav(mime, b64, path):
    raw = base64.b64decode(b64)
    if raw[:4] == b'RIFF':
        with open(path, 'wb') as f:
            f.write(raw)
        return
    rate = 24000
    m = re.search(r'rate=(\d+)', mime)
    if m:
        rate = int(m.group(1))
    with wave.open(path, 'wb') as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(rate)
        w.writeframes(raw)


def bacakan(kalimat, path, coba=3):
    """TTS satu potong narasi ke WAV."""
    galat = []
    for i in range(coba):
        try:
            j = _post(f'{API}/interactions', {
                'model': MODEL_TTS,
                'input': [{'type': 'user_input', 'content': [{
                    'type': 'text', 'text': kalimat,
                    'annotations': [{'type': 'speech_metadata', 'style': GAYA_SUARA}]}]}],
                'response_format': {'type': 'audio'},
                'generation_config': {'speech_config': [{'voice': SUARA}]},
            }, timeout=180)
            r = _cari_audio(j)
            if r:
                return _simpan_wav(r[0], r[1], path)
            galat.append('interactions: tanpa audio')
        except Exception as e:
            galat.append(f'interactions: {e}')
        try:
            j = _post(f'{API}/models/{MODEL_TTS}:generateContent', {
                'contents': [{'parts': [{'text': f'Bacakan dengan gaya {GAYA_SUARA}: {kalimat}'}]}],
                'generationConfig': {'responseModalities': ['AUDIO'], 'speechConfig': {
                    'voiceConfig': {'prebuiltVoiceConfig': {'voiceName': SUARA}}}},
            }, timeout=180)
            r = _cari_audio(j)
            if r:
                return _simpan_wav(r[0], r[1], path)
            galat.append('generateContent: tanpa audio')
        except Exception as e:
            galat.append(f'generateContent: {e}')
        time.sleep(6 * (i + 1))
    raise RuntimeError('TTS gagal | ' + ' | '.join(galat[-4:]))
