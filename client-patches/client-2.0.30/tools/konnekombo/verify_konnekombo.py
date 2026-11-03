# -*- coding: utf-8 -*-
# MT2009_PLUS_MOUNT_COMBO_HIT_V1 - the twin packs "konnekombo" / "konnekombo2" (build_konnekombo_pack.py) in OUT:
#   - each holds exactly the builder's 42 mounted combos, each with every InvisibleTime 0.150000 and otherwise the
#     players' file (GF 26.1.11 = the 3.0.6 install's gf_official, konnekombo_files.json);
#   - pack/Index lists them next to each other before gf_official, pc_1, pc_2, pc2_1 and pc2_2 (the 1st and 2nd copy
#     of every name - the builder's header says why), and no other pack of OUT carries one of the names.
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
for pack in B.PACKS:
    pi = os.path.join(OUT, pack + '.index')
    if not os.path.exists(pi):
        fails.append('OUT has no %s pack' % pack)
        continue
    f, v, ents = m2pack.read_index(pi)
    dat = open(os.path.join(OUT, pack + '.data'), 'rb').read()
    have = dict((e['name'], m2pack.read_entry(dat, e)) for e in ents)
    if have != want:
        fails.append('%s: content differs from the builder (%d vs %d files)' % (pack, len(have), len(want)))
for p in sorted(x[:-6] for x in os.listdir(OUT) if x.endswith('.index')):
    if p in B.PACKS:
        continue
    for e in m2pack.read_index(os.path.join(OUT, p + '.index'))[2]:
        if e['name'] in want:
            fails.append('%s: also in %s (OUT)' % (e['name'], p))
ix = open(os.path.join(OUT, 'Index'), 'rb').read() if os.path.exists(os.path.join(OUT, 'Index')) else b''
problem = B.index_problem([l.strip() for l in ix.replace(b'\r\n', b'\n').split(b'\n')])
if problem:
    fails.append('pack/Index: ' + problem)

print('konnekombo: packs %s, %d mounted combos each, InvisibleTime %s, %d problem(s)'
      % ('/'.join(B.PACKS), len(want), B.INVISIBLE.decode(), len(fails)))
for x in fails:
    print('  ' + x)
sys.exit(1 if fails else 0)
