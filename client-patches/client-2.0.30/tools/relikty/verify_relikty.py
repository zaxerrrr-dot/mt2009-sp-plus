# -*- coding: utf-8 -*-
# MT2009_PLUS_RELIC_V1 - checks Bonus Reliktu's client part on the OUT of the whole Yohara chain:
#   * the 15 items of tools/relikty/relikty_items.json: an item_proto record (dbdata) equal to the server's row
#     (yitem_record over the material / quest / gift box template), an item_list line whose icon is in the repo's
#     root/icon/item (Pakiet Dusz: 27999.tga of the base client's packs), an itemdesc line;
#   * the pack "relikty" (build_relikty_packs.py): GF's bytes (relikty_files.json), every entry's crc and read-back, the
#     entry types; pack/Index lists it; every GF file is in "relikty" or (same bytes) in another listed pack; every
#     .sub's image is there;
#   * the root files: uirelikt.py, uiscript/reliktwindow.py (loads, has every child uirelikt.py asks for, every image it
#     names is in a listed pack or the players' base install), relikt_data.py (= relikty_items.json's bonuses), and the
#     hooks of game.py (hello, the two commands, the key), uitooltip.py (the relic's tooltip), keybind.py, uisystem.py.
#   docker run --rm -v /opt/metin2:/opt/metin2 m2pack-lzo python3 <repo>/client-patches/client-2.0.30/tools/relikty/verify_relikty.py \
#     <OUT pack dir> [<BASE pack dir>]
import os
import re
import sys
import zlib

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, '/opt/metin2/cache/tcm/tz')
sys.path.insert(0, '/opt/metin2/cache/arezzo-work/client/az58')
sys.path.insert(0, HERE)
import m2pack  # noqa: E402
import packlib  # noqa: E402
import build_relikty_packs as B  # noqa: E402
import patch_relikty_client as pc  # noqa: E402

args = [a for a in sys.argv[1:] if not a.startswith('--')]
OUT = args[0]
BASE = args[1] if len(args) > 1 else '/opt/metin2/cache/cY/azbase'
ROOT = os.path.normpath(os.path.join(HERE, '..', '..', 'root'))
ROOT_ICONS = os.path.join(ROOT, 'icon', 'item')
BASE_INSTALL = ('d:/ymir work/ui/public/', 'd:/ymir work/ui/pattern/')
fails = []

where = {}
for _d in (BASE, OUT):
    for _f in sorted(os.listdir(_d)):
        if _f.endswith('.index'):
            for e in m2pack.read_index(os.path.join(_d, _f))[2]:
                where[e['name']] = (_d, _f[:-6])


def entry(pack, name):
    d = OUT if os.path.exists(os.path.join(OUT, pack + '.index')) else BASE
    f, v, ents = m2pack.read_index(os.path.join(d, pack + '.index'))
    dat = packlib.rd(os.path.join(d, pack + '.data'))
    for e in ents:
        if e['name'] == name:
            return m2pack.read_entry(dat, e)
    return None


# -- the items
d = pc.items_json()
ver, recs = pc.records(entry('dbdata', 'gamedata/item_proto'))
for v, r in sorted(pc.want_records(recs).items()):
    if recs.get(v) != r:
        fails.append('item_proto %d: not the server\'s record' % v)
lst = entry('gamedata', 'gamedata/item_list.txt').decode('cp1250').replace('\r\n', '\n').split('\n')
lst = dict((l.split('\t')[0].strip(), l) for l in lst if l.strip())
desc = entry('dbdata', 'locale/pl/itemdesc.txt').decode('cp1250').replace('\r\n', '\n').split('\n')
desc = dict((l.split('\t')[0].strip(), l) for l in desc if l.strip())
for k, line in d['item_list'].items():
    if lst.get(k, '').split() != line.split():
        fails.append('item_list %s: missing or other' % k)
    icon = line.split('\t')[2]
    if not os.path.isfile(os.path.join(ROOT_ICONS, os.path.basename(icon))) and icon not in where:
        fails.append('item_list %s: icon %s neither in root/icon/item nor in a listed pack' % (k, icon))
for k, line in d['itemdesc'].items():
    if desc.get(k) != line:
        fails.append('itemdesc %s: missing or other' % k)

# -- the pack
want = B.gf_files()
got = {}
if os.path.exists(os.path.join(OUT, B.PACK + '.index')):
    f, v, ents = m2pack.read_index(os.path.join(OUT, B.PACK + '.index'))
    dat = packlib.rd(os.path.join(OUT, B.PACK + '.data'))
    for e in ents:
        if zlib.crc32(dat[e['pos']:e['pos'] + e['size']]) & 0xffffffff != e['dcrc']:
            fails.append('%s: data crc' % e['name'])
            continue
        b = m2pack.read_entry(dat, e)
        got[e['name']] = b
        w = want.get(e['name'])
        if w is None:
            fails.append('%s: not one of the builder\'s files' % e['name'])
        elif b != w:
            fails.append('%s: not the builder\'s bytes' % e['name'])
        if e['ctype'] != B.ctype(e['name']):
            fails.append('%s: entry type %d' % (e['name'], e['ctype']))
    ix = open(os.path.join(OUT, 'Index'), 'rb').read() if os.path.exists(os.path.join(OUT, 'Index')) else b''
    if B.PACK.encode() not in [l.strip() for l in ix.replace(b'\r\n', b'\n').split(b'\n')]:
        fails.append('pack/Index: no line %s' % B.PACK)


def present(name):
    name = name.replace('\\', '/')
    low = name.lower()
    if name in got or name in where or low in got or low in where:
        return True
    return low.startswith(BASE_INSTALL)


for n in sorted(want):
    if not present(n):
        fails.append('%s: in no listed pack' % n)
subs = 0
for n in sorted(want):
    if not n.endswith('.sub'):
        continue
    r = re.search(rb'image\s+"([^"]+)"', want[n])
    if not r:
        fails.append('%s: no image line' % n)
        continue
    subs += 1
    if not present('d:/ymir work/ui/' + r.group(1).decode('latin-1')):
        fails.append('%s: its image is in no listed pack' % n)

# -- the root files
MODULE = os.path.join(ROOT, 'uirelikt.py')
SCRIPT = os.path.join(ROOT, 'uiscript', 'reliktwindow.py')
DATA = os.path.join(ROOT, 'relikt_data.py')
images = set()
for path in (MODULE, SCRIPT, DATA):
    if not os.path.isfile(path):
        fails.append('%s: missing' % os.path.relpath(path, ROOT))
if os.path.isfile(SCRIPT):
    text = open(SCRIPT, 'rb').read().decode('latin-1')
    consts = dict(re.findall(r'^(\w+)\s*=\s*"(d:/ymir work/[^"]+)"', text, re.M))
    images |= set(re.findall(r'"(d:/ymir work/[^"]+\.(?:sub|tga|dds))"', text, re.I))
    for c, tail in re.findall(r'(\w+)\s*\+\s*"([^"]+\.(?:sub|tga|dds))"', text):
        if c in consts:
            images.add(consts[c] + tail)
    g = {'SCREEN_WIDTH': 1024, 'SCREEN_HEIGHT': 768}
    try:
        exec(compile(text, SCRIPT, 'exec'), g)
    except Exception as ex:
        fails.append('reliktwindow.py: does not load (%s)' % ex)
        g = None
    if g and os.path.isfile(MODULE):
        have = set()

        def names(node):
            have.add(node.get('name'))
            for c in node.get('children', ()):
                names(c)
        names(g['window'])
        module = open(MODULE, 'rb').read().decode('latin-1')
        for child in sorted(set(re.findall(r'GetChild\("([^"]+)"\)', module))):
            if child not in have:
                fails.append('reliktwindow.py: no child "%s" (asked by uirelikt.py)' % child)
for img in sorted(images):
    if not present(img):
        fails.append('%s: named by reliktwindow.py, in no listed pack' % img)
if os.path.isfile(DATA):
    ns = {}
    exec(compile(open(DATA, 'rb').read().decode('latin-1'), DATA, 'exec'), ns)
    for b in d['bonuses']:
        row = ns.get('BONUS', {}).get(b['id'])
        if not row or list(row[4]) != b['values'] or row[3] != b['cooldown']:
            fails.append('relikt_data.py: bonus %d differs from relikty_items.json' % b['id'])
HOOKS = {'game.py': ('__import__("uirelikt").Start()', 'serverCommandList["relikt_state"]', 'serverCommandList["relikt_open"]',
                     '"relic"', '__import__("uirelikt").DestroyWindow()'),
         'uitooltip.py': ('__import__("uirelikt").RelicTooltip(',),
         'keybind.py': ("('relic', ",),
         'uisystem.py': ('__import__("uirelikt").OpenWindow()',),
         os.path.join('uiscript', 'systemdialog.py'): ('"relic_button"',)}
for fn, needles in sorted(HOOKS.items()):
    text = open(os.path.join(ROOT, fn), 'rb').read().decode('latin-1')
    for n in needles:
        if n not in text:
            fails.append('%s: no %s' % (fn, n))
print('relikty: %d items, %d files in the pack (%d of %d GF files elsewhere), %d .sub checked, %d window images, %d problem(s)'
      % (len(d['items']), len(got), len([n for n in want if n not in got]), len(want), subs, len(images), len(fails)))
for f in fails:
    print('  ' + f)
sys.exit(1 if fails else 0)
