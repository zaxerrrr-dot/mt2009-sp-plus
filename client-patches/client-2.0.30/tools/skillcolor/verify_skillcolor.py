# -*- coding: utf-8 -*-
# MT2009_PLUS_SKILL_COLOR_V1 - Kolor umiejetnosci (root uiskillcolor.py, skillcolorpick.py, uiscript/skillcolorwindow.py,
# uicharacter.py's "Kolory" button; exe ENABLE_MT2009_SKILL_COLOR) against the PLAYERS' install (uicheck model:
# klient-test-2.37 + yohara-3.0.0 + the 3.0.3 update zips + OUT). Checks:
#   - every picture those root files name is in a pack of the players' install (or named by the base client's root:
#     the public buttons, Parameter_Slot_03), and the image of every .sub among them too;
#   - OUT's pack "skillcolor" (build_skillcolor_packs.py) holds exactly the builder's 2 files; its color_picker.tga is
#     the 180 x 120 picture of root skillcolorpick.ColorAt pixel for pixel (the window computes a click's colour with
#     that function - a picture from another version of it would pick colours the player does not see), and
#     pack/Index lists the pack;
#   - no other pack of OUT carries one of those names, the players' install opens them from "skillcolor".
#   docker run --rm -v /opt/metin2:/opt/metin2 m2pack-lzo python3 <repo>/client-patches/client-2.0.30/tools/skillcolor/verify_skillcolor.py \
#     <OUT pack dir>
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(HERE, '..', 'uicheck'))
import build_skillcolor_packs as B  # noqa: E402
import check_ui_assets as U  # noqa: E402

OUT = [a for a in sys.argv[1:] if not a.startswith('--')][0]
fails = []

probs, inst, total = U.feature_problems(OUT, ['uiscript/skillcolorwindow.py', 'uiskillcolor.py'])
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
    pick = have.get(B.PICKER)
    if pick is None:
        fails.append('%s: no %s' % (B.PACK, B.PICKER))
    else:
        w, h, bits, top = B.tga_info(pick)
        if (w, h, bits) != (B.P.PICKER_WIDTH, B.P.PICKER_HEIGHT, 32):
            fails.append('%s: %d x %d x %d, not %d x %d x 32' % (B.PICKER, w, h, bits, B.P.PICKER_WIDTH, B.P.PICKER_HEIGHT))
        else:
            bad = 0
            for y in range(h):
                for x in range(w):
                    if B.tga_pixel(pick, x, y)[:3] != B.P.ColorAt(x, y):
                        bad += 1
            if bad:
                fails.append('%s: %d pixel(s) differ from root skillcolorpick.ColorAt' % (B.PICKER, bad))
for p in sorted(x[:-6] for x in os.listdir(OUT) if x.endswith('.index')):
    if p == B.PACK:
        continue
    for e in U.m2pack.read_index(os.path.join(OUT, p + '.index'))[2]:
        if e['name'] in want:
            fails.append('%s: also in %s (OUT)' % (e['name'], p))
ix = open(os.path.join(OUT, 'Index'), 'rb').read() if os.path.exists(os.path.join(OUT, 'Index')) else b''
if B.PACK.encode() not in [l.strip() for l in ix.replace(b'\r\n', b'\n').split(b'\n')]:
    fails.append('pack/Index: no %s line' % B.PACK)
for n in want:
    w = inst.where(n)
    if not w or w[0] != B.PACK:
        fails.append('%s: the players\' install opens it from %s, not %s' % (n, w, B.PACK))

print('skillcolor: %d picture name(s) of the root checked on the players\' install, pack %s %d files, %d problem(s)'
      % (total, B.PACK, len(want), len(fails)))
for x in fails:
    print('  ' + x)
sys.exit(1 if fails else 0)
