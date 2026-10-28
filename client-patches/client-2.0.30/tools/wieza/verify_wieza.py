# -*- coding: utf-8 -*-
# MT2009_PLUS_SMH_TOWER_V3 - checks Wieza Sung Mahi's client part on the OUT of the whole Yohara chain:
#   * the pack "wieza" (build_wieza_packs.py) holds exactly the builder's files (GF's bytes - wieza_files.json: size,
#     sha256 - and the affect icon's image and two .sub under our wieza_* names), every entry's crc and read-back, the
#     entry types; pack/Index lists it;
#   * every file the builder makes is in "wieza" or (same bytes) in another listed pack (BASE or OUT);
#   * the root files root/uiwiezasm.py, root/uiscript/sungmaheetowerenter.py and
#     root/uiscript/sungmaheetowerinformationboard.py are in the repo; the uiscripts load (SCREEN_WIDTH / _HEIGHT given)
#     and have every child uiwiezasm.py asks for (GetChild / get("...")); every image they name (ROOT_PATH / AFFECT_PATH
#     + "x.sub" and "d:/ymir work/..." literals) is in a listed pack or in the players' base install (the stock
#     d:/ymir work/ui/public/ and ui/pattern/ images - packs this tree does not hold); every .sub's image is there too.
#   docker run --rm -v /opt/metin2:/opt/metin2 m2pack-lzo python3 <repo>/client-patches/client-2.0.30/tools/wieza/verify_wieza.py \
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
import build_wieza_packs as B  # noqa: E402

args = [a for a in sys.argv[1:] if not a.startswith('--')]
OUT = args[0]
BASE = args[1] if len(args) > 1 else '/opt/metin2/cache/cY/azbase'
ROOT = os.path.normpath(os.path.join(HERE, '..', '..', 'root'))
MODULE = os.path.join(ROOT, 'uiwiezasm.py')
SCRIPTS = {'TowerEnterWindow': os.path.join(ROOT, 'uiscript', 'sungmaheetowerenter.py'),
           'FloorBoard': os.path.join(ROOT, 'uiscript', 'sungmaheetowerinformationboard.py')}
BASE_INSTALL = ('d:/ymir work/ui/public/', 'd:/ymir work/ui/pattern/')
fails = []

where = {}
for _d in (BASE, OUT):
    for _f in sorted(os.listdir(_d)):
        if _f.endswith('.index'):
            for e in m2pack.read_index(os.path.join(_d, _f))[2]:
                where[e['name']] = (_d, _f[:-6])

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

# the .sub files: their image (relative to d:/ymir work/ui/)
subs = 0
for n in sorted(want):
    if not n.endswith('.sub'):
        continue
    b = want[n]
    r = re.search(rb'image\s+"([^"]+)"', b)
    if not r:
        fails.append('%s: no image line' % n)
        continue
    subs += 1
    img = 'd:/ymir work/ui/' + r.group(1).decode('latin-1')
    if not present(img):
        fails.append('%s: its image %s is in no listed pack' % (n, img))


# the root files
def images_of(text):
    consts = dict(re.findall(r'^(\w+_PATH)\s*=\s*"([^"]+)"', text, re.M))
    out = set(re.findall(r'"(d:/ymir work/[^"]+\.(?:sub|tga|dds|png|jpg))"', text, re.I))
    for c, tail in re.findall(r'(\w+_PATH)\s*\+\s*"([^"]+)"', text):
        if c in consts:
            out.add(consts[c] + tail)
    return out


images = set()
for path in [MODULE] + sorted(SCRIPTS.values()):
    if not os.path.isfile(path):
        fails.append('%s: missing' % os.path.relpath(path, ROOT))
        continue
    images |= images_of(open(path, 'rb').read().decode('latin-1'))
for img in sorted(images):
    if not present(img):
        fails.append('%s: named by the root files, in no listed pack' % img)


def names(node, out):
    out.add(node.get('name'))
    for c in node.get('children', ()):
        names(c, out)
    return out


if os.path.isfile(MODULE):
    module = open(MODULE, 'rb').read().decode('latin-1')
    for cls, path in sorted(SCRIPTS.items()):
        if not os.path.isfile(path):
            continue
        g = {'SCREEN_WIDTH': 1024, 'SCREEN_HEIGHT': 768}
        try:
            exec(compile(open(path, 'rb').read().decode('latin-1'), path, 'exec'), g)
        except Exception as ex:
            fails.append('%s: does not load (%s)' % (os.path.basename(path), ex))
            continue
        have = names(g['window'], set())
        body = module.split('class %s(' % cls, 1)[1].split('\nclass ', 1)[0]
        for child in sorted(set(re.findall(r'get\("([^"]+)"\)', body))):
            if child not in have:
                fails.append('%s: no child "%s" (asked by %s)' % (os.path.basename(path), child, cls))
print('wieza: %d files in the pack, %d of %d GF files elsewhere, %d .sub checked, %d root images, %d problem(s)'
      % (len(got), len([n for n in want if n not in got]), len(want), subs, len(images), len(fails)))
for f in fails:
    print('  ' + f)
sys.exit(1 if fails else 0)
