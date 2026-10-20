# MT2009_PLUS_KOLA_V1: the F12 "Kolo Losu" window's images and data module.
#
# Cuts the wheel's graphics (the same ones the itemshop page uses,
# linux-port/docker/itemshop/app/itemshop/kola/img/, converted there from the
# source's webp) into separate client images under root/mt2009_ui/kola/ and
# writes root/koladata.py (wheel names, backgrounds, idle field icons, field and
# key positions). No texture is wider than 1024: the 16-frame spinner and pointer
# strips become 16 images each. The root pack takes every file of
# client-2.0.30/root, so nothing else is needed for the build.
#
#   python3 make_kola_ui.py [<repo root>]     (needs PIL)
import json
import os
import shutil
import sys

from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = sys.argv[1] if len(sys.argv) > 1 else os.path.normpath(os.path.join(HERE, '..', '..', '..', '..'))
SRC = os.path.join(REPO, 'linux-port', 'docker', 'itemshop', 'app', 'itemshop', 'kola')
ROOT = os.path.join(REPO, 'client-patches', 'client-2.0.30', 'root')
OUT = os.path.join(ROOT, 'mt2009_ui', 'kola')
UI = 'mt2009_ui/kola/'
ICON = 64	# icons: shown at 45x45 (scale 0.70), popped up to ~105 px

# The original's field positions (JS array u: top, left of a 45x45 field
# inside .crk-items, which sits +50,+50 in the 436x436 wheel) and key positions
# (array k: top, left of a 56x56 key inside .crk-keys at -6,-6).
U = [(-22.5, 145.5), (-9.71176, 209.79082), (26.70606, 264.29394), (81.20918, 300.71176), (145.5, 313.5),
     (209.79082, 300.71176), (264.29394, 264.29394), (300.71176, 209.79082), (313.5, 145.5), (300.71176, 81.20918),
     (264.29394, 26.70606), (209.79082, -9.71176), (145.5, -22.5), (81.20918, -9.71176), (26.70606, 26.70606),
     (-9.71176, 81.20918)]
K = [(-22.5, 195.5), (-5.90574, 278.92499), (41.35072, 349.64928), (112.07501, 396.90574), (195.5, 413.5),
     (278.92499, 396.90574), (349.64928, 349.64928), (396.90574, 278.92499), (413.5, 195.5), (396.90574, 112.07501),
     (349.64928, 41.35072), (278.92499, -5.90574), (195.5, -22.5), (112.07501, -5.90574), (41.35072, 41.35072),
     (-5.90574, 112.07501)]

# sprite.png regions (the original CSS background positions): name -> (top, width, height)
SPRITE = {
    'arrow_l': (0, 20, 25), 'arrow_r': (35, 20, 25),
    'keyring_1': (70, 56, 56), 'keyring_2': (136, 56, 56),
    'ring_1': (202, 436, 436), 'ring_2': (648, 436, 436), 'ring_3': (1094, 436, 436),
    'stg': (1540, 38, 29), 'stg_f1': (1579, 38, 29), 'stg_f2': (1618, 38, 29),
    'lvl_1': (1657, 39, 39), 'lvl_1c': (1706, 58, 58), 'lvl_2': (1774, 39, 39), 'lvl_2c': (1823, 58, 58),
    'lvl_3': (1891, 39, 39), 'lvl_3c': (1940, 58, 58),
    'btn': (2008, 125, 124), 'btn_run': (2142, 125, 125),
    'slices_1': (2412, 436, 436), 'slices_2': (2858, 436, 436), 'slices_3': (3304, 436, 436),
}
# button.png regions: name -> (top, height)
BUTTON = {'exit': (2, 30), 'exit_h': (39, 30), 'prices': (224, 32), 'prices_h': (274, 32)}


def crop(im, left, top, w, h):
    out = Image.new('RGBA', (w, h), (0, 0, 0, 0))
    out.paste(im.crop((left, top, min(im.size[0], left + w), min(im.size[1], top + h))), (0, 0))
    return out


def tile(im, w, h):
    out = Image.new('RGB', (w, h))
    for y in range(0, h, im.size[1]):
        for x in range(0, w, im.size[0]):
            out.paste(im, (x, y))
    return out


def icon(path, dst):
    im = Image.open(path).convert('RGBA')
    im = im.resize((ICON, ICON), Image.LANCZOS)
    im.save(dst, optimize=True)


def esc(text):
    """Python 2 source literal, CP1250 escapes."""
    out = ''
    for ch in text.encode('cp1250'):
        if 32 <= ch < 127 and ch not in (39, 92):
            out += chr(ch)
        else:
            out += '\\x%02x' % ch
    return "'" + out + "'"


def main():
    cfg = json.load(open(os.path.join(SRC, 'kola.json'), encoding='utf-8'))
    img = os.path.join(SRC, 'img')
    shutil.rmtree(OUT, ignore_errors=True)
    for d in ('', 'i', 'f'):
        os.makedirs(os.path.join(OUT, d), exist_ok=True)

    sprite = Image.open(os.path.join(img, 'sprite.png')).convert('RGBA')
    for name, (top, w, h) in SPRITE.items():
        crop(sprite, 0, top, w, h).save(os.path.join(OUT, name + '.png'), optimize=True)
    # the keys as one image each: the tier's frame and the key icon in the middle (.crk-key:before)
    key = Image.open(os.path.join(img, 'key.png')).convert('RGBA').resize((34, 34), Image.LANCZOS)
    for t in (1, 2):
        ring = crop(sprite, 0, SPRITE['keyring_%d' % t][0], 56, 56)
        ring.alpha_composite(key, (11, 11))
        ring.save(os.path.join(OUT, 'key_%d.png' % t), optimize=True)
        os.remove(os.path.join(OUT, 'keyring_%d.png' % t))
    for strip in ('spinner', 'pointer'):
        im = Image.open(os.path.join(img, strip + '.png')).convert('RGBA')
        for i in range(16):
            crop(im, i * 436, 0, 436, 436).save(os.path.join(OUT, '%s_%02d.png' % (strip, i)), optimize=True)
    button = Image.open(os.path.join(img, 'button.png')).convert('RGBA')
    for name, (top, h) in BUTTON.items():
        crop(button, 0, top, 144, h).save(os.path.join(OUT, name + '.png'), optimize=True)
    for name in ('coin', 'lock'):
        Image.open(os.path.join(img, name + '.png')).convert('RGBA').save(os.path.join(OUT, name + '.png'), optimize=True)
    ladder = Image.open(os.path.join(img, 'ladder.jpg')).convert('RGB')
    tile(ladder, 100, 420).save(os.path.join(OUT, 'ladder.jpg'), quality=90)
    tile(ladder, 176, 300).save(os.path.join(OUT, 'panel.jpg'), quality=90)

    wheels = []
    for wid in cfg['rotation']['order']:
        w = cfg['wheels'][str(wid)]
        shutil.copyfile(os.path.join(img, w['bg']), os.path.join(OUT, 'bg_%d.jpg' % wid))
        fields = {}
        for t, names in w['fields'].items():
            paths = []
            for n in names:
                short = n[2:14] + '.png'	# i_<hash>.png -> f/<12 hex>.png
                dst = os.path.join(OUT, 'f', short)
                if not os.path.exists(dst):
                    icon(os.path.join(img, n), dst)
                paths.append(UI + 'f/' + short)
            fields[int(t)] = paths
        wheels.append((wid, w['name'], fields))
    icons = 0
    for sid, it in cfg['src_items'].items():
        if sid.isdigit() and it.get('img'):
            icon(os.path.join(img, it['img']), os.path.join(OUT, 'i', sid + '.png'))
            icons += 1

    lines = [
        '# MT2009_PLUS_KOLA_V1: generated by client-2.0.30/tools/kola/make_kola_ui.py - do not edit by hand.',
        '# The wheels of the "Kolo Losu" (uiwheel.py): names, backgrounds, the idle field icons per tier,',
        '# and the positions of the 16 fields (45x45) and the four keys (56x56) in the 436x436 wheel.',
        '',
        "UI = '%s'" % UI,
        'WHEELS = {',
    ]
    for wid, name, fields in wheels:
        lines.append('\t%d: {' % wid)
        lines.append("\t\t'name': %s," % esc(name))
        lines.append("\t\t'bg': '%sbg_%d.jpg'," % (UI, wid))
        lines.append("\t\t'fields': {")
        for t in sorted(fields):
            lines.append('\t\t\t%d: (%s),' % (t, ', '.join("'%s'" % p for p in fields[t])))
        lines.append('\t\t},')
        lines.append('\t},')
    lines.append('}')
    lines.append('')
    lines.append('# (x, y) of field 1..16 (index 0..15), clockwise from the top')
    lines.append('FIELD_POS = (%s)' % ', '.join('(%.1f, %.1f)' % (l + 50, t + 50) for (t, l) in U))
    lines.append('# (x, y) of the key image (56x56) on field 1..16')
    lines.append('KEY_POS = (%s)' % ', '.join('(%.1f, %.1f)' % (l - 6, t - 6) for (t, l) in K))
    lines.append('KEY_FIELDS = (3, 7, 11, 15)')
    lines.append('SPECIAL_FIELDS = {1: (1,), 2: (1, 9), 3: (1, 7, 11)}')
    lines.append('')
    open(os.path.join(ROOT, 'koladata.py'), 'w', newline='\n').write('\n'.join(lines))

    total = 0
    count = 0
    for dp, dn, fn in os.walk(OUT):
        for f in fn:
            total += os.path.getsize(os.path.join(dp, f))
            count += 1
    print('kola: %d files, %.2f MB, %d prize icons' % (count, total / 1048576.0, icons))


if __name__ == '__main__':
    main()
