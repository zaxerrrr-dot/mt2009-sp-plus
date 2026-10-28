# -*- coding: utf-8 -*-
# MT2009_PLUS_COMMUNITY_V1 - checks what build_community_packs.py wrote (on the OUT of the whole Yohara chain): the
# community_ui pack has the repo's 71 files byte for byte, the Index names it once, every .sub's picture is in a pack
# (d:/ymir work/ui/<image>), and every picture root/uicommunity.py names (ROOT + "...sub", the checkbox .tga) is in a
# pack or in the repo's root folder.
#   docker run --rm -v /opt/metin2:/opt/metin2 m2pack-lzo python3 <repo>/client-patches/client-2.0.30/tools/community/verify_community.py \
#     <OUT pack dir> [<BASE pack dir>]
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, '/opt/metin2/cache/tcm/tz')
sys.path.insert(0, '/opt/metin2/cache/arezzo-work/client/az58')
sys.path.insert(0, HERE)
import m2pack  # noqa: E402
import packlib  # noqa: E402
import build_community_packs as bc  # noqa: E402

args = [a for a in sys.argv[1:] if not a.startswith('--')]
OUT = args[0]
BASE = args[1] if len(args) > 1 else '/opt/metin2/cache/cY/azbase'
ROOT = os.path.normpath(os.path.join(HERE, '..', '..', 'root'))
fails = []
WHERE = {}
for _d in (BASE, OUT):
	for _f in os.listdir(_d):
		if _f.endswith('.index'):
			for e in m2pack.read_index(os.path.join(_d, _f))[2]:
				WHERE[e['name']] = _f[:-6]

want = bc.new_pack_files()
idx = os.path.join(OUT, bc.NEW_PACK + '.index')
if not os.path.exists(idx):
	fails.append('%s: not in OUT' % bc.NEW_PACK)
else:
	f, v, ents = m2pack.read_index(idx)
	dat = packlib.rd(os.path.join(OUT, bc.NEW_PACK + '.data'))
	got = dict((e['name'], m2pack.read_entry(dat, e)) for e in ents)
	if got != want:
		fails.append('%s: other files (%d, want %d)' % (bc.NEW_PACK, len(got), len(want)))
ix = packlib.rd(os.path.join(OUT, 'Index') if os.path.exists(os.path.join(OUT, 'Index')) else os.path.join(BASE, 'Index'))
if [l.strip() for l in ix.replace(b'\r\n', b'\n').split(b'\n')].count(bc.NEW_PACK.encode()) != 1:
	fails.append('Index: %s not there once' % bc.NEW_PACK)
for name, b in sorted(want.items()):
	if name.endswith('.sub'):
		image = re.search(rb'image "([^"]+)"', b).group(1).decode('ascii').lower()
		full = 'd:/ymir work/ui/' + image
		if full not in WHERE and full not in want:
			fails.append('%s: picture %s in no pack' % (name, full))
src = open(os.path.join(ROOT, 'uicommunity.py'), 'rb').read().decode('latin-1')
for sub in sorted(set(re.findall(r'ROOT \+ "([a-z0-9_]+\.sub)"', src))):
	if 'd:/ymir work/ui/game/windows/' + sub not in want:
		fails.append('uicommunity.py: %s not in the pack' % sub)
for tga in re.findall(r'"(mt2009_ui/[^"]+\.tga)"', src):
	if tga not in WHERE and not os.path.isfile(os.path.join(ROOT, tga)):
		fails.append('uicommunity.py: %s in no pack' % tga)
for prefix in sorted(set(re.findall(r'"(community_icon_[a-z_]+|community_drop_button|community_button)"', src))):
	for suffix in ('_default.sub', '_mouse_over.sub', '_click.sub'):
		n = 'd:/ymir work/ui/game/windows/' + prefix + suffix
		if n not in want and not (suffix == '_click.sub' and prefix == 'community_icon_position'):
			fails.append('uicommunity.py: %s not in the pack' % n)
print('\n'.join(fails) if fails else 'community: OK (%d files)' % len(want))
sys.exit(1 if fails else 0)
