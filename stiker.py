"""Stiker benda untuk template Remotion: ribuan ikon garis dari Tabler Icons (MIT), disaring hanya benda.

Aturan: stiker HANYA benda, tempat, alam, dan simbol netral. Tidak ada manusia, wajah, hewan berkepala, simbol
agama lain, minuman keras, judi, atau musik. Daftar hitam ada di bawah; pustaka disaring sekali saat dibangun.

Bangun ulang pustaka (sekali, hasilnya di-commit):
    npm pack @tabler/icons@3.50.0 && tar -xzf tabler-icons-3.50.0.tgz
    python stiker.py bangun package
"""
import hashlib
import json
import os
import re
import sys

ROOT = os.path.dirname(os.path.abspath(__file__))
PUSTAKA = os.path.join(ROOT, 'data', 'stiker', 'tabler.json')

KATEGORI_BUANG = {'Brand', 'Letters', 'Numbers', 'Text', 'Arrows', 'Mood', 'Gender', 'Zodiac', 'Development',
                  'Version control', 'Database', 'Logic', 'Math', 'Charts', 'Extensions', 'Badges', 'Symbols', 'Games',
                  'Animals', 'Gestures', 'Shapes'}
# Dari kategori yang dibuang, beberapa benda tetap berguna.
TETAP = {'paw', 'feather', 'fish-bone', 'horseshoe', 'recycle', 'sword', 'swords', 'axe', 'archery-arrow', 'treasure-chest',
         'puzzle', 'pick', 'hand-stop', 'hand-grab', 'clock', 'calendar', 'bell', 'lock', 'key', 'flag', 'star', 'heart',
         'home', 'bookmark', 'gift', 'bulb', 'trash', 'scale', 'hourglass', 'alarm', 'mail', 'eye', 'link', 'shield',
         'crown', 'diamond', 'compass', 'umbrella', 'anchor', 'paperclip', 'ruler', 'scissors', 'brush', 'palette', 'quote',
         'message', 'message-circle', 'wash', 'device-mobile', 'device-tv', 'file', 'cup'}
# Potongan nama/tag yang berarti makhluk bernyawa, wajah, simbol agama lain, haram, judi, musik, atau UI.
KATA_BUANG = {
    'user', 'users', 'man', 'woman', 'men', 'women', 'person', 'people', 'human', 'face', 'mood', 'emoji', 'avatar',
    'baby', 'child', 'kid', 'friends', 'old', 'nurse', 'physiotherapist', 'massage', 'fall', 'blind', 'deaf',
    'disabled', 'accessible', 'empathize', 'teacher', 'yoga', 'run', 'walk', 'swimming', 'ski', 'karate', 'stretching',
    'treadmill', 'skateboarding', 'gymnastics', 'ghost', 'skull', 'alien', 'robot', 'zombie', 'pacman', 'mickey',
    'mustache', 'mask', 'spy', 'butterfly', 'snowman', 'cat', 'dog', 'pig', 'horse', 'deer', 'dragon', 'bat', 'spider',
    'snail', 'fish', 'bug', 'bird', 'cross', 'church', 'christmas', 'christianity', 'bible', 'menorah', 'jewish', 'om',
    'torii', 'ankh', 'pentagram', 'yin', 'buddha', 'confucius', 'easter', 'halloween', 'pumpkin', 'beer', 'wine',
    'cocktail', 'champagne', 'gin', 'alcohol', 'cannabis', 'smoking', 'cigarette', 'dice', 'poker', 'casino',
    'roulette', 'card', 'joker', 'music', 'guitar', 'piano', 'drum', 'playlist', 'vinyl', 'headphones', 'trumpet',
    'violin', 'disco', 'microphone', 'bikini', 'kiss', 'lips', 'bra', 'underwear', 'condom', 'sex', 'venus', 'mars',
    'bitcoin', 'crypto', 'off', 'plus', 'minus', 'check', 'x', 'cancel', 'cog', 'edit', 'exclamation', 'question',
    'search', 'share', 'up', 'down', 'dollar', 'discount', 'code', 'pause', 'dot', 'move', 'infinity', 'spark', 'filled', 'percentage', 'euro', 'pound', 'yen', 'rupee', 'yuan', 'ufo', 'scary', 'ufo', 'grave', 'coffin',
    'tombstone', 'nfc', 'qrcode', 'wifi', 'bluetooth', 'usb', 'api', 'sql', 'html', 'css', 'json', 'ai', 'gpt',
    # potongan antarmuka aplikasi, bukan benda
    'adjustments', 'layout', 'toggle', 'menu', 'layers', 'grid', 'table', 'columns', 'align', 'border', 'crop', 'select',
    'selector', 'cursor', 'pointer', 'click', 'cut', 'copy', 'clipboard', 'resize', 'arrow', 'arrows', 'chevron',
    'chevrons', 'caret', 'corner', 'separator', 'spacing', 'dimensions', 'letter', 'typography', 'list', 'sort',
    'filter', 'terminal', 'brackets', 'braces', 'variable', 'function', 'math', 'square', 'squares', 'circles',
    'radius', 'backspace', 'cloud-upload', 'download', 'upload', 'login', 'logout', 'settings', 'toggle', 'switch',
    'badge', 'id', 'barcode', 'sitemap', 'hierarchy', 'subtask', 'sidebar', 'app', 'apps', 'dashboard', 'focus',
    'zoom', 'maximize', 'minimize', 'rotate', 'flip', 'shadow', 'vector', 'bezier', 'shape', 'polygon', 'section',
    'box-model', 'transform', 'mask', 'artboard', 'frame', 'background', 'blur', 'contrast', 'exposure', 'hdr',
    # hasil cek galeri 15 Nov 2026: sosok orang, wajah, ramalan, judi, dan ikon antarmuka/teknis
    'acrobatic', 'beach', 'body', 'cliff', 'jumping', 'bong', 'crystal', 'chess', 'currency', 'creative', 'commons',
    'circuit', 'cell', 'signal', 'antenna', 'ad', 'explicit', 'error', 'favicon', 'type', 'device', 'file', 'dots',
    'ease', 'drag', 'freeze', 'grip', 'help', 'forbid', 'deselect', 'direction', 'decagram', 'details', 'dialpad',
    'geometry', 'gradienter', 'gpu', 'gizmo', 'recognition', 'glass', 'hula', 'skating', 'jump', 'rope', 'kayak', 'lego',
    'masks', 'chatbot', 'michelin', 'play', 'pool', 'monkeybar', 'http', 'info', 'loader', 'line', 'load', 'marquee',
    'mesh', 'meter', 'keyframe', 'keyframes', 'keyboard', 'scuba', 'snowboarding', 'trekking', 'waterpolo',
    'wheelchair', 'xxx', 'trident', 'xbox', 'vs', 'vip', 'uhd', 'topology', 'duration', 'dry', 'dryclean', 'tumble',
    'gentle', 'press', 'stack', 'stroke', 'tab', 'tabs', 'template', 'tilt', 'tooltip', 'view', 'viewport', 'viewfinder',
    'vignette', 'typeface', 'swipe', 'spaces', 'status', 'screenshot', 'server', 'shareplay', 'skew', 'slashes', 'tic',
    'tilde', 'texture', 'subtitles', 'rewind', 'forward', 'player', 'playstation', 'pokeball', 'protocol', 'progress',
    'placeholder', 'picture', 'reorder', 'replace', 'restore', 'report', 'reserved', 'premium', 'paywall', 'password',
    'opacity', 'outbound', 'no', 'object', 'notification', 'noise', 'mobiledata', 'manual', 'lasso', 'live', 'lens',
    'label', 'join', 'jetski', 'inbox', 'image', 'icosahedron', 'invoice', 'hours', 'history', 'hash', 'graph', 'gauge',
    'gps', 'fidget', 'exchange', 'email', 'e', 'desk', 'dual', 'cast', 'capture', 'checkbox', 'checks', 'clear',
    'credits', 'crosshair', 'components', 'congruent', 'container', 'cube', 'cpu', 'aspect', 'augmented', 'automation',
    'blend', 'blocks', 'box', 'brightness', 'browser', 'bounce', 'binary', 'barrier', 'battery', 'aperture', 'access',
    'affiliate', 'analyze', 'angle', 'article', 'ban', 'bleach', 'blob', 'pray', 'sleigh', 'diaper', 'tax', 'eye-dotted',
    'scan', 'sensor', 'channel', 'chalkboard', 'carousel', 'zeppelin', 'xbox', 'yarn', 'ux', 'universe', 'tir', 'tor',
}


def _bersih(nama, data):
    tok = set(nama.split('-'))
    tag = {t.lower() for t in data.get('tags', []) for t in re.split(r'[\s\-]+', str(t))}
    if nama in TETAP:
        return not (tok & KATA_BUANG)
    if data.get('category', '') in KATEGORI_BUANG:
        return False
    if 'outline' not in data.get('styles', {}):
        return False
    if tok & KATA_BUANG:
        return False
    return not (tag & {'person', 'people', 'human', 'face', 'emoji', 'avatar', 'man', 'woman', 'child', 'kid',
                       'christian', 'music', 'gambling', 'animal', 'pet'})


def bangun(folder):
    ikon = json.load(open(os.path.join(folder, 'icons.json'), encoding='utf-8'))
    simpul = json.load(open(os.path.join(folder, 'tabler-nodes-outline.json'), encoding='utf-8'))
    padat = json.load(open(os.path.join(folder, 'tabler-nodes-filled.json'), encoding='utf-8'))

    def markup(daftar):
        return ''.join('<%s %s/>' % (tag, ' '.join(f'{k}="{v}"' for k, v in at.items() if k != 'key'))
                       for tag, at in daftar)
    hasil = {}
    for nama, data in sorted(ikon.items()):
        if nama not in simpul or not _bersih(nama, data):
            continue
        kata = ' '.join(sorted({*nama.split('-'), *(str(t).lower() for t in data.get('tags', []))}))
        hasil[nama] = {'s': markup(simpul[nama]), 'k': kata}
        # versi padat (isi penuh) = gaya stiker kedua untuk benda yang sama
        if nama in padat:
            hasil[nama + ':padat'] = {'s': markup(padat[nama]), 'k': kata, 'f': 1}
    os.makedirs(os.path.dirname(PUSTAKA), exist_ok=True)
    with open(PUSTAKA, 'w', encoding='utf-8') as f:
        json.dump(hasil, f, ensure_ascii=False, separators=(',', ':'))
    print(f'{len(hasil)} stiker -> {PUSTAKA}')


_CACHE = {}


def pustaka():
    if 'p' not in _CACHE:
        try:
            with open(PUSTAKA, encoding='utf-8') as f:
                _CACHE['p'] = json.load(f)
        except OSError:
            _CACHE['p'] = {}
    return _CACHE['p']


# Kata Indonesia (awal kata) -> nama ikon Tabler. Urutan di daftar = prioritas; variasi dipilih dari daftar.
KAMUS = {
    'air': ['droplet', 'droplets', 'bottle', 'ripple'], 'wudhu': ['droplet', 'droplets', 'hand-sanitizer', 'bath'],
    'mandi': ['bath', 'droplets', 'bucket'], 'minum': ['cup', 'bottle', 'mug', 'milk'], 'susu': ['milk', 'baby-bottle'],
    'madu': ['jar', 'bottle', 'cup'], 'makan': ['tools-kitchen-2', 'bowl', 'bowl-spoon', 'bread', 'salad'],
    'roti': ['bread', 'baguette', 'wheat'], 'kurma': ['plant', 'seedling', 'nut', 'bowl'], 'buah': ['apple', 'grape', 'lemon', 'melon', 'cherry'],
    'anggur': ['grape'], 'garam': ['salt'], 'daging': ['meat', 'bone', 'grill'], 'telur': ['egg', 'eggs'],
    'sayur': ['salad', 'carrot', 'leaf'], 'gandum': ['wheat', 'bread'], 'masak': ['cooker', 'tools-kitchen-2', 'soup'],
    'piring': ['bowl', 'tools-kitchen-2'],  'kenyang': ['bowl-spoon', 'soup', 'bread'],
    'lapar': ['bowl', 'bread'], 'haus': ['droplet', 'bottle'], 'puasa': ['moon', 'moon-stars', 'clock', 'sunset'],
    'sahur': ['moon-stars', 'cup', 'clock'], 'buka': ['sunset', 'cup', 'bread'], 'tidur': ['bed', 'bed-flat', 'moon', 'zzz', 'pillow'],
    'bangun': ['sunrise', 'alarm', 'sun'], 'kasur': ['bed', 'bed-flat'], 'bantal': ['bed', 'pillow'], 'mimpi': ['moon-stars', 'cloud', 'zzz'],
    'malam': ['moon', 'moon-stars', 'stars', 'lamp'], 'bulan': ['moon', 'moon-2', 'moon-stars'], 'bintang': ['star', 'stars', 'sparkles'],
    'pagi': ['sunrise', 'sun', 'coffee'], 'subuh': ['sunrise', 'moon-stars', 'alarm'], 'siang': ['sun', 'sun-high'],
    'sore': ['sunset', 'sunset-2'], 'senja': ['sunset', 'sunset-2'], 'matahari': ['sun', 'sun-high', 'sunrise'],
    'hujan': ['cloud-rain', 'umbrella', 'droplets'], 'awan': ['cloud', 'cloud-fog'], 'petir': ['cloud-storm', 'cloud-bolt', 'storm'],
    'badai': ['storm', 'tornado', 'cloud-storm', 'wind'], 'angin': ['wind', 'whirl'], 'panas': ['temperature', 'flame', 'sun-high'],
    'dingin': ['snowflake', 'temperature'], 'api': ['flame', 'campfire', 'fire-extinguisher'], 'neraka': ['flame', 'campfire'],
    'surga': ['trees', 'plant-2', 'droplets', 'building-arch', 'stars'], 'pintu': ['door', 'door-enter', 'door-exit', 'key'],
    'rumah': ['home', 'home-2', 'building-cottage', 'door'], 'keluar': ['door-exit', 'road', 'map'], 'masuk': ['door-enter', 'door', 'home'],
    'kunci': ['key', 'lock'], 'masjid': ['building-mosque', 'moon-stars', 'clock'], 'shalat': ['building-mosque', 'clock', 'compass'],
    'sholat': ['building-mosque', 'clock', 'compass'], 'kiblat': ['compass', 'building-mosque'], 'adzan': ['speakerphone', 'building-mosque', 'clock'],
    'azan': ['speakerphone', 'building-mosque', 'clock'], 'jumat': ['building-mosque', 'calendar'], 'haji': ['building-mosque', 'map-pin', 'plane'],
    'umrah': ['building-mosque', 'plane', 'map'], 'quran': ['book', 'book-2', 'books', 'bookmark'], 'mushaf': ['book', 'book-2', 'bookmark'],
    'ayat': ['book', 'quote', 'bookmark'], 'kitab': ['book', 'books', 'notebook'], 'buku': ['book', 'books', 'notebook'],
    'ilmu': ['books', 'bulb', 'school', 'pencil'], 'belajar': ['school', 'books', 'pencil', 'notebook'], 'menulis': ['pencil', 'writing', 'feather', 'notebook'],
    'pena': ['pencil', 'feather', 'writing'], 'surat': ['mail', 'mail-opened', 'script'], 'tulis': ['pencil', 'writing', 'notebook'],
    'baca': ['book', 'eyeglass', 'book-2'], 'doa': ['hand-stop', 'moon-stars', 'sparkles', 'heart'], 'dzikir': ['heart', 'sparkles', 'moon-stars'],
    'zikir': ['heart', 'sparkles', 'moon-stars'], 'syukur': ['heart', 'sparkles', 'gift'], 'sabar': ['hourglass', 'clock', 'shield'],
    'waktu': ['clock', 'hourglass', 'calendar', 'alarm'], 'jam': ['clock', 'alarm', 'clock-hour-4'], 'hari': ['calendar', 'sun', 'clock'],
    'tahun': ['calendar', 'calendar-event'], 'tanggal': ['calendar', 'calendar-event'], 'hati': ['heart', 'heartbeat', 'heart-handshake'],
    'cinta': ['heart', 'heart-handshake', 'hearts'], 'sayang': ['heart', 'heart-handshake', 'hearts'], 'iman': ['heart', 'shield', 'sparkles'],
    'niat': ['heart', 'bulb', 'target'], 'ikhlas': ['heart', 'feather', 'sparkles'], 'taubat': ['heart', 'droplet', 'refresh'],
    'dosa': ['cloud-storm', 'scale', 'trash'], 'pahala': ['star', 'gift', 'scale', 'trophy'], 'amal': ['scale', 'gift', 'heart'],
    'timbangan': ['scale'], 'adil': ['scale', 'gavel'], 'hukum': ['gavel', 'scale', 'book'], 'harta': ['coins', 'cash', 'diamond', 'treasure-chest', 'wallet'],
    'uang': ['coins', 'cash', 'wallet', 'coin'], 'emas': ['coins', 'diamond', 'crown'], 'sedekah': ['coins', 'gift', 'heart-handshake', 'pig-money'],
    'zakat': ['coins', 'scale', 'wallet'], 'infak': ['coins', 'gift', 'heart-handshake'], 'hadiah': ['gift', 'heart'],
    'jual': ['building-store', 'basket', 'scale', 'receipt'], 'beli': ['basket', 'shopping-cart', 'building-store'], 'dagang': ['building-store', 'scale', 'coins', 'package'],
    'pasar': ['building-store', 'basket', 'scale'], 'hutang': ['receipt', 'notebook', 'wallet'], 'utang': ['receipt', 'notebook', 'wallet'],
    'kaya': ['diamond', 'crown', 'coins'], 'miskin': ['bowl', 'wallet'], 'raja': ['crown', 'building-castle'], 'istana': ['building-castle', 'crown'],
    'kota': ['building', 'buildings', 'building-castle'], 'desa': ['building-cottage', 'trees', 'tent'], 'jalan': ['road', 'route', 'map', 'footprint'],
    'perjalanan': ['map', 'route', 'compass', 'road', 'tent'], 'safar': ['map', 'route', 'compass', 'luggage'], 'hijrah': ['route', 'map', 'compass', 'moon-stars'],
    'kendaraan': ['car', 'bike', 'tractor'], 'perahu': ['sailboat', 'ship', 'anchor'], 'kapal': ['ship', 'sailboat', 'anchor'],
    'laut': ['sailboat', 'ripple', 'anchor', 'droplets'], 'sungai': ['ripple', 'droplets'], 'gunung': ['mountain', 'tent'],
    'gua': ['mountain', 'flashlight', 'lamp'], 'gurun': ['cactus', 'sun-high', 'tent'], 'padang': ['cactus', 'sun-high', 'mountain'],
    'pohon': ['tree', 'trees', 'plant-2'], 'daun': ['leaf', 'leaf-2', 'plant'], 'bunga': ['flower', 'plant'], 'tanam': ['seedling', 'plant', 'shovel'],
    'kebun': ['trees', 'plant-2', 'seedling', 'shovel'], 'batu': ['mountain', 'diamond'], 'tanah': ['shovel', 'seedling', 'mountain'],
    'tenda': ['tent', 'campfire'], 'perang': ['sword', 'swords', 'shield', 'flag'], 'pedang': ['sword', 'swords'], 'panah': ['archery-arrow', 'target'],
    'perisai': ['shield'], 'pasukan': ['flag', 'shield', 'swords', 'tent'], 'menang': ['trophy', 'flag', 'award'], 'bendera': ['flag', 'flag-2'],
    'unta': ['tent', 'cactus', 'route', 'compass'], 'kuda': ['horseshoe', 'route'], 'jejak': ['paw', 'shoe', 'route'], 'kaki': ['shoe'],
    'sandal': ['shoe'], 'sepatu': ['shoe'], 'pakaian': ['shirt', 'hanger', 'jacket'], 'baju': ['shirt', 'hanger'], 'kain': ['shirt', 'hanger'],
    'sisir': ['brush'], 'siwak': ['dental', 'brush', 'sparkles'], 'gigi': ['dental', 'brush'], 'parfum': ['perfume', 'sparkles', 'spray'],
    'wangi': ['perfume', 'sparkles', 'flower'], 'minyak': ['droplet', 'bottle'], 'bersih': ['sparkles', 'bath', 'wash'], 'kotor': ['trash', 'wash'],
    'sabun': ['wash', 'droplets', 'bath'], 'sakit': ['pill', 'thermometer', 'first-aid-kit', 'bandage'], 'obat': ['pill', 'pills', 'medicine-syrup', 'first-aid-kit'],
    'sehat': ['heartbeat', 'activity', 'apple'], 'mata': ['eye', 'eyeglass'], 'lihat': ['eye', 'eyeglass'], 'telinga': ['ear'], 'dengar': ['ear', 'speakerphone'],
    'tangan': ['hand-stop', 'hand-grab'], 'kanan': ['hand-stop', 'arrow-right'], 'kiri': ['hand-stop'], 'bersin': ['wind', 'droplets'],
    'ucap': ['message', 'message-circle', 'quote'], 'kata': ['message', 'quote', 'message-circle'], 'salam': ['message-circle', 'heart-handshake', 'door'],
    'tamu': ['door', 'cup', 'heart-handshake'], 'tetangga': ['home', 'building-cottage', 'heart-handshake'], 'keluarga': ['home', 'heart', 'hearts'],
    'orang tua': ['home', 'heart'], 'ibu': ['heart', 'home'], 'nikah': ['heart', 'diamond', 'gift'], 'saudara': ['heart-handshake', 'hearts'],
    'teman': ['heart-handshake', 'message-circle'], 'janji': ['heart-handshake', 'notebook'], 'bohong': ['message-circle', 'alert-triangle'],
    'jujur': ['shield', 'heart', 'scale'], 'marah': ['flame', 'alert-triangle'], 'senyum': ['sparkles', 'heart', 'sun'], 'malu': ['shield', 'heart'],
    'setan': ['alert-triangle', 'flame', 'shield'], 'lampu': ['bulb', 'lamp'], 'lentera': ['lamp', 'flame', 'bulb'], 'cahaya': ['bulb', 'sparkles', 'sun', 'flare'],
    'gelap': ['moon', 'cloud-fog'], 'mati': ['hourglass', 'cloud', 'plant'], 'wafat': ['hourglass', 'moon', 'cloud'], 'kubur': ['hourglass', 'moon'],
    'kiamat': ['hourglass', 'storm', 'meteor'], 'ular': ['alert-triangle', 'first-aid-kit'], 'racun': ['bottle', 'alert-triangle', 'biohazard'],
    'sumur': ['bucket', 'droplets'], 'ember': ['bucket'], 'tali': ['link'], 'rantai': ['link'], 'penjara': ['lock', 'building-fortress'],
    'benteng': ['building-fortress', 'shield'], 'tembok': ['wall', 'building-fortress'], 'pasir': ['hourglass', 'cactus', 'sun-high'],
    'debu': ['wind', 'cloud-fog'], 'kotak': ['package', 'box'], 'telepon': ['phone', 'device-mobile'], 'hp': ['device-mobile', 'phone'],
    'layar': ['device-mobile'], 'kerja': ['briefcase', 'tools', 'hammer'], 'tukang': ['hammer', 'tools', 'tool'], 'kayu': ['axe', 'trees'],
    'besi': ['hammer', 'tool'], 'pintar': ['bulb', 'books'], 'rahasia': ['lock', 'key'], 'janji allah': ['star', 'shield'],
    'cepat': ['clock', 'bolt'], 'lambat': ['hourglass'], 'pertama': ['trophy', 'flag'], 'tujuh': ['calendar'], 'delapan': ['door'],
    'seribu': ['stars', 'sparkles'], 'mudah': ['sparkles', 'thumb-up'], 'kunci surga': ['key', 'door'],
}
# Cadangan per ilustrasi kalau narasi tidak menyebut benda yang dikenal.
PER_ILUSTRASI = {
    'badai': ['cloud-storm', 'storm', 'wind', 'tornado'], 'kota_malam': ['moon-stars', 'building-cottage', 'lamp', 'stars'],
    'quran': ['book', 'bookmark', 'sparkles', 'book-2'], 'kafilah': ['tent', 'route', 'cactus', 'compass'],
    'kabah': ['building-mosque', 'compass', 'moon-stars', 'map-pin'], 'masjid': ['building-mosque', 'clock', 'moon-stars', 'compass'],
    'gua': ['mountain', 'lamp', 'moon-stars', 'flame'], 'majelis': ['message-circle', 'book', 'tent', 'heart-handshake'],
    'lentera': ['lamp', 'moon-stars', 'flame', 'sparkles'], 'fajar': ['sunrise', 'sun', 'alarm', 'clock'],
    'air': ['droplet', 'droplets', 'bottle', 'ripple'], 'hidangan': ['bowl', 'bread', 'cup', 'wheat'],
    'pintu': ['door', 'key', 'home', 'door-enter'], 'sedekah': ['coins', 'gift', 'heart-handshake', 'wallet'],
    'hati': ['heart', 'heartbeat', 'sparkles', 'hearts'],
}


def _kata_narasi(teks):
    """Daftar (posisi, nama ikon...) dari kata di narasi yang dikenal kamus, urut posisi."""
    t = ' ' + (teks or '').lower() + ' '
    temu = []
    for kunci, ikon in KAMUS.items():
        m = re.search(r"[\s\(\"'-]" + re.escape(kunci), t)
        if m:
            temu.append((m.start(), len(kunci), ikon))
    temu.sort(key=lambda x: (x[0], -x[1]))
    return temu


def cari_inggris(kata, p=None):
    """Cocokkan kata benda bahasa Inggris (dari Gemini) ke nama ikon; nama persis > potongan nama > tag."""
    p = p or pustaka()
    k = kata.lower().strip().replace(' ', '-')
    if k in p:
        return k
    terbaik, skor = None, 0
    bagian = set(k.split('-'))
    for nama, d in p.items():
        if ':' in nama:
            continue
        tok = set(nama.split('-'))
        s = 3 * len(bagian & tok) - 0.3 * len(tok - bagian)
        if s <= 0 and k in d['k'].split():
            s = 1 - 0.1 * len(tok)
        if s > skor:
            terbaik, skor = nama, s
    return terbaik


def pilih(teks, ilustrasi='', inggris=(), benih='', n=3, sudah=()):
    """Pilih hingga n stiker untuk satu babak. Kembali [(nama, posisi_relatif_0_1 atau None)].
    Variasi: dari daftar kamus diambil satu ikon dengan benih (judul+babak), jadi video beda dapat ikon beda."""
    p = pustaka()
    if not p:
        return []
    h = int(hashlib.md5(benih.encode('utf-8')).hexdigest(), 16)
    hasil, dipakai = [], set(sudah)

    def tambah(nama, pos):
        if nama and nama in p and nama not in dipakai and len(hasil) < n:
            dipakai.add(nama)
            if nama + ':padat' in p and (h >> (len(hasil) + 3)) % 3 == 0:
                nama += ':padat'
            hasil.append((nama, pos))

    panjang = max(1, len(teks or ''))
    for i, (pos, _, daftar) in enumerate(_kata_narasi(teks)):
        ada = [x for x in daftar if x in p and x not in dipakai]
        if ada:
            tambah(ada[(h + i) % len(ada)], pos / panjang)
    for kata in inggris or ():
        tambah(cari_inggris(kata, p), None)
    cad = [x for x in PER_ILUSTRASI.get(ilustrasi, []) if x in p]
    for i in range(len(cad)):
        if len(hasil) >= n:
            break
        tambah(cad[(h + i) % len(cad)], None)
    return hasil


def props(teks, ilustrasi='', inggris=(), benih='', n=3, sudah=None):
    """Stiker siap kirim ke Remotion: [{'svg', 'padat', 'pos'}]. sudah = set nama yang dipakai babak lain."""
    sudah = sudah if sudah is not None else set()
    hasil = []
    for nama, pos in pilih(teks, ilustrasi, inggris, benih, n, {x.split(':')[0] for x in sudah}):
        sudah.add(nama.split(':')[0])
        d = pustaka()[nama]
        hasil.append({'nama': nama, 'svg': d['s'], 'padat': bool(d.get('f')), 'pos': pos})
    return hasil


if __name__ == '__main__':
    if len(sys.argv) >= 3 and sys.argv[1] == 'bangun':
        bangun(sys.argv[2])
    elif len(sys.argv) >= 2 and sys.argv[1] == 'uji':
        print(pilih(' '.join(sys.argv[2:]), benih='uji'))
    else:
        print(__doc__)
