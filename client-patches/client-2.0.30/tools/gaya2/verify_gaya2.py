# -*- coding: utf-8 -*-
# MT2009_PLUS_GAYA_CURRENCY_V1 - checks the pack build_gaya2_pack.py wrote (on the OUT of the whole Yohara chain):
#   gaya2.index / gaya2.data hold exactly the 8 names of gaya2_files.json (size, sha256, entry type), every entry's crc
#   and read-back; pack/Index lists "gaya2" once and "fireghost" stays the first pack; no other pack (OUT or BASE) has
#   one of the names; every image the root's Gaya files name is in the pack (gayacurrency.py, uiscript/
#   inventorywindow.py, uiscript/expandedmoneytaskbar.py, uitaskbar.py) or is a base image they already used.
#   docker run --rm -v /opt/metin2:/opt/metin2 m2pack-lzo python3 <repo>/client-patches/client-2.0.30/tools/gaya2/verify_gaya2.py \
#     <OUT pack dir> [<BASE pack dir>]
import hashlib
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
import build_gaya2_pack as B  # noqa: E402

args = [a for a in sys.argv[1:] if not a.startswith('--')]
OUT = args[0]
BASE = args[1] if len(args) > 1 else '/opt/metin2/cache/cY/azbase'
ROOT = os.path.normpath(os.path.join(HERE, '..', '..', 'root'))
# base images the Gaya rows name besides the pack's (the inventory's Yang row used them before)
BASE_IMAGES = {'d:/ymir work/ui/public/parameter_slot_05.sub', 'd:/ymir work/ui/game/windows/money_icon.sub',
               'd:/ymir work/ui/game/windows/cheque_icon.sub'}
fails = []

want = B.manifest()
ip = os.path.join(OUT, B.PACK + '.index')
if not os.path.exists(ip):
    fails.append('no %s.index in %s' % (B.PACK, OUT))
else:
    f, v, ents = m2pack.read_index(ip)
    dat = packlib.rd(os.path.join(OUT, B.PACK + '.data'))
    names = [e['name'] for e in ents]
    if sorted(names) != sorted(want):
        fails.append('pack names differ: extra %s, missing %s' % (sorted(set(names) - set(want)),
                                                                   sorted(set(want) - set(names))))
    for e in ents:
        if zlib.crc32(dat[e['pos']:e['pos'] + e['size']]) & 0xffffffff != e['dcrc']:
            fails.append('%s: data crc' % e['name'])
            continue
        b = m2pack.read_entry(dat, e)
        w = want.get(e['name'])
        if w and (len(b) != w['size'] or hashlib.sha256(b).hexdigest() != w['sha256'] or e['ctype'] != w['ctype']):
            fails.append('%s: not the file of gaya2_files.json' % e['name'])

ix_path = os.path.join(OUT, 'Index') if os.path.exists(os.path.join(OUT, 'Index')) else os.path.join(BASE, 'Index')
lines = [l.strip() for l in packlib.rd(ix_path).replace(b'\r\n', b'\n').split(b'\n')]
if lines.count(B.PACK.encode()) != 1:
    fails.append('Index: "%s" listed %d times' % (B.PACK, lines.count(B.PACK.encode())))
if b'fireghost' in lines and lines.index(b'fireghost') != 2:
    fails.append('Index: fireghost is no longer the first pack')

for d in (BASE, OUT):
    for fn in os.listdir(d):
        if fn.endswith('.index') and fn[:-6] != B.PACK:
            for e in m2pack.read_index(os.path.join(d, fn))[2]:
                if e['name'] in want:
                    fails.append('%s also in %s/%s' % (e['name'], d, fn))

named = set()
for rel in ('gayacurrency.py', 'uiscript/inventorywindow.py', 'uiscript/expandedmoneytaskbar.py', 'uitaskbar.py'):
    t = open(os.path.join(ROOT, rel), 'rb').read().decode('latin-1')
    for m in re.finditer(r'"(d:/ymir work/ui/gaya2/[^"]+)"', t):
        named.add(m.group(1))
    for m in re.finditer(r'GAYA2_UI \+ "([^"]+)"', t):
        named.add('d:/ymir work/ui/gaya2/' + m.group(1))
if not named:
    fails.append('the root names no gaya2 image (gayacurrency.py GAYA2_UI)')
for n in sorted(named):
    if n not in want and n not in BASE_IMAGES:
        fails.append('root names %s - not in the pack' % n)

print('gaya2: %d files, root names %d of them' % (len(want), len(named & set(want))))
if fails:
    print('FAIL')
    for x in fails:
        print('  ' + x)
    sys.exit(1)
print('OK')
