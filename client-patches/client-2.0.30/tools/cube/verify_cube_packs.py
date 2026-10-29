# -*- coding: utf-8 -*-
# MT2009_PLUS_CUBE_RENEWAL_V1 - checks the root pack of a build (OUT, else BASE) for the global crafting window:
#   * every entry of cube_files.entries() is there, byte for byte the repo's file (the module, its uiscript,
#     making_001.dds and the 21 .sub files);
#   * every .sub of d:/ymir work/ui/game/cube points at making_001.dds or gemshop_001.dds inside the image (DDS size);
#   * the images it needs from earlier steps are there (gemshop_001.dds) and the old windows stay (uicube.py for the set
#     blacksmiths, uicraft.py for its category lists);
#   * the pack's interfacemodule.py makes the new windows (import uiCubeRenewal, CubeRenewalWindow, CraftingRenewalWindow)
#     and (V2) sends the set blacksmiths there too;
#   * (V2) every piece of cube_setsmith_data.py is in the client's item_proto (dbdata pack) and is one the set
#     blacksmiths take: a weapon (not an arrow), a body armour or a helmet, level 75+, "+7" or more in its name.
#   docker run --rm -v /opt/metin2:/opt/metin2 m2pack-lzo python3 <repo>/client-patches/client-2.0.30/tools/cube/verify_cube_packs.py \
#     <OUT pack dir> [<BASE pack dir>]
import os
import struct
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, '/opt/metin2/cache/tcm/tz')
sys.path.insert(0, '/opt/metin2/cache/arezzo-work/client/az58')
sys.path.insert(0, HERE)
import m2pack  # noqa: E402
import packlib  # noqa: E402
import cube_files  # noqa: E402

args = [a for a in sys.argv[1:] if not a.startswith('--')]
OUT = args[0]
BASE = args[1] if len(args) > 1 else '/opt/metin2/cache/cY/azbase'
fails = []

d = OUT if os.path.exists(os.path.join(OUT, 'root.index')) else BASE
f, v, ents = m2pack.read_index(os.path.join(d, 'root.index'))
dat = packlib.rd(os.path.join(d, 'root.data'))
have = dict((e['name'], e) for e in ents)


def entry(name):
    return m2pack.read_entry(dat, have[name]) if name in have else None


want = cube_files.entries()
for name, (path, ctype) in sorted(want.items()):
    b = entry(name)
    if b is None:
        fails.append('%s: not in the root pack' % name)
    elif b != cube_files.read(path):
        fails.append('%s: not the repo\'s file' % name)

sizes = {}
for img in ('d:/ymir work/ui/making_001.dds', 'd:/ymir work/ui/gemshop_001.dds'):
    b = entry(img)
    if b is None or b[:4] != b'DDS ':
        fails.append('%s: missing or not a DDS' % img)
    else:
        h, w = struct.unpack('<II', b[12:20])
        sizes[img.rsplit('/', 1)[1]] = (w, h)
for name in sorted(want):
    if not name.endswith('.sub'):
        continue
    b = entry(name)
    if b is None:
        continue
    kv = {}
    for line in b.decode('ascii').replace('\r\n', '\n').split('\n'):
        p = line.split(None, 1)
        if len(p) == 2:
            kv[p[0]] = p[1].strip('"')
    img = kv.get('image')
    if img not in sizes:
        fails.append('%s: image %r not shipped' % (name, img))
        continue
    (w, h) = sizes[img]
    l, t, r, btm = [int(kv.get(k, -1)) for k in ('left', 'top', 'right', 'bottom')]
    if not (0 <= l < r <= w and 0 <= t < btm <= h):
        fails.append('%s: rect %d,%d-%d,%d outside %s %dx%d' % (name, l, t, r, btm, img, w, h))

for name in cube_files.NEEDED_ELSEWHERE:
    if name not in have:
        fails.append('%s: not in the root pack' % name)
iface = entry('interfacemodule.py') or b''
for hook in cube_files.INTERFACE_HOOKS:
    if hook.encode('ascii') not in iface:
        fails.append('interfacemodule.py: %r missing' % hook)
for hook in cube_files.INTERFACE_GONE:
    if hook.encode('ascii') in iface:
        fails.append('interfacemodule.py: %r still there' % hook)

# MT2009_PLUS_CUBE_RENEWAL_V2: the set blacksmiths' pieces against the client's item_proto
import gen_setsmith_items  # noqa: E402
ns = {}
exec(compile(cube_files.read(os.path.join(cube_files.ROOT, 'cube_setsmith_data.py')), 'cube_setsmith_data.py', 'exec'), ns)
dd = OUT if os.path.exists(os.path.join(OUT, 'dbdata.index')) else BASE
proto = gen_setsmith_items.client_proto(dd)
npieces = 0
for part, vnums in sorted(ns['PIECES'].items()):
    for vnum in vnums:
        npieces += 1
        if vnum not in proto:
            fails.append('cube_setsmith_data: %d not in the client item_proto' % vnum)
            continue
        (name, typ, sub, lvl) = proto[vnum]
        if gen_setsmith_items.part_of(typ, sub) != part or lvl < gen_setsmith_items.MIN_LEVEL \
                or gen_setsmith_items.refine_level(name) < gen_setsmith_items.MIN_REFINE:
            fails.append('cube_setsmith_data: %d (%s) is not a part-%d piece of level 75+ at +7' % (vnum, name, part))

print('cube: %d entries, %d set blacksmith pieces, %d problem(s)' % (len(want), npieces, len(fails)))
for x in fails:
    print('  ' + x)
sys.exit(1 if fails else 0)
