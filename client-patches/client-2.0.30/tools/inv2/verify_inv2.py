# -*- coding: utf-8 -*-
# MT2009_PLUS_INVENTORY_V2_V1 - checks what build_inv2_packs.py wrote (on the OUT of the whole Yohara chain): the inv2_ui
# pack has the repo's 15 pictures byte for byte, the Index names it once, and every picture the v2 inventory's root
# files open (inventoryv2.py, uiinventory.py, uiscript/inventoryequipwindow.py, uiscript/inventorywindowv2.py) is in a
# pack of the PLAYERS' install (tools/uicheck: klient-test-2.37 + yohara-3.0.1 zips + OUT; the base packs count when the
# base client's own root opens the name) - the tabs' tab_button_large_half_0[1-3].sub included.
#   docker run --rm -v /opt/metin2:/opt/metin2 m2pack-lzo python3 <repo>/client-patches/client-2.0.30/tools/inv2/verify_inv2.py \
#     <OUT pack dir>
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, '/opt/metin2/cache/tcm/tz')
sys.path.insert(0, '/opt/metin2/cache/arezzo-work/client/az58')
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(HERE, '..', 'uicheck'))
import m2pack  # noqa: E402
import packlib  # noqa: E402
import build_inv2_packs as bi  # noqa: E402

args = [a for a in sys.argv[1:] if not a.startswith('--')]
OUT = args[0]
BASE = args[1] if len(args) > 1 else '/opt/metin2/cache/cY/azbase'
fails = []

want = bi.new_pack_files()
idx = os.path.join(OUT, bi.NEW_PACK + '.index')
if not os.path.exists(idx):
	fails.append('%s: not in OUT' % bi.NEW_PACK)
else:
	f, v, ents = m2pack.read_index(idx)
	dat = packlib.rd(os.path.join(OUT, bi.NEW_PACK + '.data'))
	got = dict((e['name'], m2pack.read_entry(dat, e)) for e in ents)
	if got != want:
		fails.append('%s: other files (%d, want %d)' % (bi.NEW_PACK, len(got), len(want)))
ix = packlib.rd(os.path.join(OUT, 'Index') if os.path.exists(os.path.join(OUT, 'Index')) else os.path.join(BASE, 'Index'))
if [l.strip() for l in ix.replace(b'\r\n', b'\n').split(b'\n')].count(bi.NEW_PACK.encode()) != 1:
	fails.append('Index: %s not there once' % bi.NEW_PACK)

if '--no-install' not in sys.argv:
	import check_ui_assets as U  # noqa: E402
	pys = ['inventoryv2.py', 'uiinventory.py', 'uiscript/inventoryequipwindow.py', 'uiscript/inventorywindowv2.py']
	extra = sorted(want) + ['d:/ymir work/ui/game/windows/tab_button_large_half_0%d.sub' % i for i in (1, 2, 3)] + \
		['playerbot_ui/chest_button.tga']
	probs, inst, n = U.feature_problems(OUT, pys, extra)
	fails += ['install: %s' % p for p in probs]
print('\n'.join(fails) if fails else 'inv2: OK (%d files)' % len(want))
sys.exit(1 if fails else 0)
