# -*- coding: utf-8 -*-
# MT2009_PLUS_QUICKSLOT_IMPROVE_V1 - the expanded quick slot bar (root uitaskbar.py, quickslotstate.py,
# uiscript/expandedquickslot.py; exe ENABLE_QUICKSLOT_IMPROVE) needs no pack of its own: every image of the package
# (d:/ymir work/ui/taskbar.tga and the 15 d:/ymir work/ui/game/taskbar/expanded_quickslot_*.sub) is already, byte for
# byte, in the base pack "etc" every client has (quickslot2_files.json: names, sizes, sha256). This checks that:
#   - the reference "etc" pack holds the 16 files with the manifest's bytes, every .sub cuts a rectangle inside the
#     512 x 256 taskbar.tga it names;
#   - no pack of the Yohara chain's OUT carries one of those names (a pack listed before "etc" would win with other bytes);
#   - pack/Index still lists "etc";
#   - every image root's uiscript/expandedquickslot.py and uitaskbar.py name is in the manifest or in "etc" (1-4.sub).
#   docker run --rm -v /opt/metin2:/opt/metin2 m2pack-lzo python3 <repo>/client-patches/client-2.0.30/tools/quickslot2/verify_quickslot2.py \
#     <OUT pack dir> [<pack dir with etc.index>]
# No builder: clientY.sh only gets this file in its verify loop.
import hashlib
import json
import os
import re
import struct
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, '/opt/metin2/cache/tcm/tz')
sys.path.insert(0, '/opt/metin2/cache/arezzo-work/client/az58')
import m2pack  # noqa: E402
import packlib  # noqa: E402

args = [a for a in sys.argv[1:] if not a.startswith('--')]
OUT = args[0]
REF = args[1] if len(args) > 1 else '/opt/metin2/cache/exebuild/smoke/client/pack'
ROOT = os.path.normpath(os.path.join(HERE, '..', '..', 'root'))
M = json.load(open(os.path.join(HERE, 'quickslot2_files.json')))
want = M['files']
fails = []

# the reference etc pack
etc = {}
f, v, ents = m2pack.read_index(os.path.join(REF, 'etc.index'))
dat = packlib.rd(os.path.join(REF, 'etc.data'))
names = set(e['name'] for e in ents)
for e in ents:
    if e['name'] in want or re.match(r'd:/ymir work/ui/game/taskbar/[1-4]\.sub$', e['name']):
        etc[e['name']] = m2pack.read_entry(dat, e)
for n, w in sorted(want.items()):
    b = etc.get(n)
    if b is None:
        fails.append('%s: not in etc' % n)
    elif len(b) != w['size'] or hashlib.sha256(b).hexdigest() != w['sha256']:
        fails.append('%s: etc has other bytes' % n)
tga = etc.get('d:/ymir work/ui/taskbar.tga', b'')
if len(tga) >= 18:
    tw, th = struct.unpack('<HH', tga[12:16])
    for n, b in sorted(etc.items()):
        if not n.endswith('.sub'):
            continue
        t = b.decode('latin-1')
        img = re.search(r'image\s+"([^"]+)"', t)
        box = [int(x) for x in re.findall(r'(?:left|top|right|bottom)\s+(\d+)', t)]
        if not img or len(box) != 4:
            fails.append('%s: not a subImage' % n)
        elif img.group(1).lower() == 'taskbar.tga' and not (0 <= box[0] < box[2] <= tw and 0 <= box[1] < box[3] <= th):
            fails.append('%s: %s outside %dx%d' % (n, box, tw, th))

# the chain's packs must not carry them
for p in sorted(x[:-6] for x in os.listdir(OUT) if x.endswith('.index')):
    for e in m2pack.read_index(os.path.join(OUT, p + '.index'))[2]:
        if e['name'] in want:
            fails.append('%s: also in %s (OUT)' % (e['name'], p))

ix = open(os.path.join(OUT, 'Index'), 'rb').read() if os.path.exists(os.path.join(OUT, 'Index')) else b''
if b'etc' not in [l.strip() for l in ix.replace(b'\r\n', b'\n').split(b'\n')]:
    fails.append('pack/Index: no etc line')

# root names only these images
used = set()
for rel in ('uiscript/expandedquickslot.py', 'uitaskbar.py'):
    src = open(os.path.join(ROOT, rel), 'rb').read().decode('latin-1')
    base = dict(re.findall(r'^(\w+)\s*=\s*"(d:/ymir work/ui/game/taskbar/[^"]*)"', src, re.M))
    for var, name in re.findall(r'(\w+)\s*\+\s*"([^"]+\.sub)"', src):
        if var in base:
            used.add(base[var] + name)
    for suffix in ('default', 'over', 'down'):
        for kind in ('show', 'hide'):
            if 'EXPANDED_QUICKSLOT_PATH' in src:
                used.add('d:/ymir work/ui/game/taskbar/expanded_quickslot_%s_button_%s.sub' % (kind, suffix))
for n in sorted(used):
    if n not in want and n not in etc:
        fails.append('root names %s - not in etc' % n)

print('quickslot2: %d images in etc (%s), %d named by root, %d problem(s)' % (len(etc), REF, len(used), len(fails)))
for x in fails:
    print('  ' + x)
sys.exit(1 if fails else 0)
