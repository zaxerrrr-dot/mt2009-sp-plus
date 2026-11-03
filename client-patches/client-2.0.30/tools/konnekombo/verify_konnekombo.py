# -*- coding: utf-8 -*-
# MT2009_PLUS_MOUNT_COMBO_HIT_V1 - the pack "konnekombo" (build_konnekombo_pack.py) in OUT:
#   - it holds exactly the builder's 42 mounted combos, each with every InvisibleTime 0.150000 and otherwise the
#     players' file (GF 26.1.11 = the 3.0.6 install's gf_official, konnekombo_files.json);
#   - pack/Index lists it before gf_official, pc_1, pc_2, pc2_1 and pc2_2 (the exe keeps the first pack registering a
#     name), and no other pack of OUT carries one of its names.
#   docker run --rm -v /opt/metin2:/opt/metin2 m2pack-lzo python3 <repo>/client-patches/client-2.0.30/tools/konnekombo/verify_konnekombo.py \
#     <OUT pack dir>
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import build_konnekombo_pack as B  # noqa: E402
import m2pack  # noqa: E402  (build_konnekombo_pack put its path first)

OUT = [a for a in sys.argv[1:] if not a.startswith('--')][0]
fails = []

want = B.files()
for n, b in want.items():
    vals = set(m.group(2) for m in B.INV_RE.finditer(b))
    if vals != {B.INVISIBLE}:
        fails.append('%s: InvisibleTime %s' % (n, sorted(vals)))
pi = os.path.join(OUT, B.PACK + '.index')
if not os.path.exists(pi):
    fails.append('OUT has no %s pack' % B.PACK)
else:
    f, v, ents = m2pack.read_index(pi)
    dat = open(os.path.join(OUT, B.PACK + '.data'), 'rb').read()
    have = dict((e['name'], m2pack.read_entry(dat, e)) for e in ents)
    if have != want:
        fails.append('%s: content differs from the builder (%d vs %d files)' % (B.PACK, len(have), len(want)))
for p in sorted(x[:-6] for x in os.listdir(OUT) if x.endswith('.index')):
    if p == B.PACK:
        continue
    for e in m2pack.read_index(os.path.join(OUT, p + '.index'))[2]:
        if e['name'] in want:
            fails.append('%s: also in %s (OUT)' % (e['name'], p))
ix = open(os.path.join(OUT, 'Index'), 'rb').read() if os.path.exists(os.path.join(OUT, 'Index')) else b''
lines = [l.strip() for l in ix.replace(b'\r\n', b'\n').split(b'\n')]
if B.PACK.encode() not in lines:
    fails.append('pack/Index: no %s line' % B.PACK)
else:
    at = lines.index(B.PACK.encode())
    for p in B.SHADOWED:
        if p in lines and lines.index(p) < at:
            fails.append('pack/Index: %s comes before %s - its files would win' % (p.decode(), B.PACK))

print('konnekombo: pack %s %d mounted combos, InvisibleTime %s, %d problem(s)'
      % (B.PACK, len(want), B.INVISIBLE.decode(), len(fails)))
for x in fails:
    print('  ' + x)
sys.exit(1 if fails else 0)
