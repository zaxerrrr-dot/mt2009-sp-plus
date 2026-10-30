# -*- coding: utf-8 -*-
# MT2009_PLUS_QUICKSLOT_IMPROVE_V1 - the expanded quick slot bar (root uitaskbar.py, quickslotstate.py,
# uiscript/expandedquickslot.py; exe ENABLE_QUICKSLOT_IMPROVE) against the PLAYERS' install (uicheck model:
# klient-test-2.37 + yohara-3.0.0 + the 3.0.3 update zips + OUT), not the exe smoke client's etc (3.0.6 aborted at game
# start: the 15 expanded_quickslot_*.sub are in no pack a player has). Checks:
#   - every picture uitaskbar.py / uiscript/expandedquickslot.py name is in a pack of the players' install (or named by
#     the base client's root, e.g. 1-4.sub), and the image of every .sub among them too;
#   - OUT's pack "quickslot2" (build_quickslot2_packs.py) holds exactly the builder's 16 files, every .sub names the
#     512 x 256 expanded_quickslot_taskbar.tga (the builder checks the rectangles), and pack/Index lists it;
#   - no other pack of OUT carries one of those names, and no pack of OUT replaces d:/ymir work/ui/taskbar.tga (the
#     players' own task bar picture stays theirs).
#   docker run --rm -v /opt/metin2:/opt/metin2 m2pack-lzo python3 <repo>/client-patches/client-2.0.30/tools/quickslot2/verify_quickslot2.py \
#     <OUT pack dir>
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(HERE, '..', 'uicheck'))
import build_quickslot2_packs as B  # noqa: E402
import check_ui_assets as U  # noqa: E402

OUT = [a for a in sys.argv[1:] if not a.startswith('--')][0]
fails = []

probs, inst, total = U.feature_problems(OUT, ['uiscript/expandedquickslot.py', 'uitaskbar.py'])
fails += probs

want = B.files()
pi = os.path.join(OUT, B.PACK + '.index')
if not os.path.exists(pi):
    fails.append('OUT has no %s pack' % B.PACK)
else:
    f, v, ents = U.m2pack.read_index(pi)
    dat = open(os.path.join(OUT, B.PACK + '.data'), 'rb').read()
    have = dict((e['name'], U.m2pack.read_entry(dat, e)) for e in ents)
    if have != want:
        fails.append('%s: content differs from the builder (%d vs %d files)' % (B.PACK, len(have), len(want)))
    for n, b in sorted(have.items()):
        if n.endswith('.sub'):
            ts = U.sub_targets(n, b)
            if not ts or ts[0] != B.TGA:
                fails.append('%s: image %s, not %s' % (n, ts and ts[0], B.TGA))
for p in sorted(x[:-6] for x in os.listdir(OUT) if x.endswith('.index')):
    if p == B.PACK:
        continue
    for e in U.m2pack.read_index(os.path.join(OUT, p + '.index'))[2]:
        if e['name'] in want:
            fails.append('%s: also in %s (OUT)' % (e['name'], p))
        if e['name'] == 'd:/ymir work/ui/taskbar.tga':
            fails.append('d:/ymir work/ui/taskbar.tga replaced by %s (OUT) - the players\' task bar picture' % p)
ix = open(os.path.join(OUT, 'Index'), 'rb').read() if os.path.exists(os.path.join(OUT, 'Index')) else b''
if B.PACK.encode() not in [l.strip() for l in ix.replace(b'\r\n', b'\n').split(b'\n')]:
    fails.append('pack/Index: no %s line' % B.PACK)
for n in want:
    w = inst.where(n)
    if not w or w[0] != B.PACK:
        fails.append('%s: the players\' install opens it from %s, not %s' % (n, w, B.PACK))

print('quickslot2: %d picture name(s) of the root checked on the players\' install, pack %s %d files, %d problem(s)'
      % (total, B.PACK, len(want), len(fails)))
for x in fails:
    print('  ' + x)
sys.exit(1 if fails else 0)
