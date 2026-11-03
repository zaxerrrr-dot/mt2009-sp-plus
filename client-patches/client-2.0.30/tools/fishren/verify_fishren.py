# -*- coding: utf-8 -*-
# MT2009_PLUS_FISHING_RENEWAL_V1 - the new fishing minigame's pictures in OUT (build_fishren_pack.py): pack "fishren"
# with exactly files/ (fishing_01.dds and the 15 .sub - each .sub's image fishing_01.dds and its rectangle inside it),
# every picture root/uifishingrenewal.py and root/uiscript/fishingrenewalwindow.py name, listed in pack/Index, and no
# other pack of OUT with one of those names.
#   docker run --rm -v /opt/metin2:/opt/metin2 m2pack-lzo python3 <repo>/client-patches/client-2.0.30/tools/fishren/verify_fishren.py \
#     <OUT pack dir>
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, '/opt/metin2/cache/tcm/tz')
sys.path.insert(0, '/opt/metin2/cache/arezzo-work/client/az58')
sys.path.insert(0, HERE)
import m2pack  # noqa: E402
import build_fishren_pack as B  # noqa: E402

OUT = [a for a in sys.argv[1:] if not a.startswith('--')][0]
ROOT = os.path.normpath(os.path.join(HERE, '..', '..', 'root'))
fails = []

pi = os.path.join(OUT, B.PACK + '.index')
got = {}
if not os.path.exists(pi):
	fails.append('OUT has no %s pack' % B.PACK)
else:
	f, v, ents = m2pack.read_index(pi)
	dat = open(os.path.join(OUT, B.PACK + '.data'), 'rb').read()
	got = dict((e['name'], m2pack.read_entry(dat, e)) for e in ents)
files = B.pack_files()
if got != files:
	fails.append('%s: entries %s differ from files/ %s' % (B.PACK, sorted(got), sorted(files)))

dds = got.get('d:/ymir work/ui/fishing_01.dds', b'')
subs = [n for n in got if n.endswith('.sub')]
if dds[:4] != b'DDS ':
	fails.append('fishing_01.dds: not a DDS')
else:
	dh, dw = dds[12] | dds[13] << 8, dds[16] | dds[17] << 8
	if len(subs) != 15:
		fails.append('%d .sub, want 15' % len(subs))
	for n in subs:
		kv = dict(l.split(None, 1) for l in got[n].decode('ascii').splitlines() if len(l.split(None, 1)) == 2)
		if kv.get('image', '').strip().strip('"') != 'fishing_01.dds':
			fails.append('%s: image %r' % (n, kv.get('image')))
		elif not (0 <= int(kv['left']) < int(kv['right']) <= dw and 0 <= int(kv['top']) < int(kv['bottom']) <= dh):
			fails.append('%s: rectangle outside the %dx%d texture' % (n, dw, dh))

# every picture the window names is in the pack
want = set()
for name, prefix in (('uifishingrenewal.py', None), (os.path.join('uiscript', 'fishingrenewalwindow.py'), None)):
	text = open(os.path.join(ROOT, name), 'rb').read().decode('latin-1')
	for m in re.finditer(r"(?:ROOT|FISHING_PATH|FISH_PATH|WAVE_PATH)\s*\+\s*['\"]([^'\"]+)['\"](?:\s*%\s*i)?", text):
		want.add(m.group(0))
paths = {'ROOT': 'd:/ymir work/ui/game/fishing/', 'FISHING_PATH': 'd:/ymir work/ui/game/fishing/',
	'FISH_PATH': 'd:/ymir work/ui/game/fishing/fish/', 'WAVE_PATH': 'd:/ymir work/ui/game/fishing/wave/'}
named = set()
for w in want:
	m = re.match(r"(\w+)\s*\+\s*['\"]([^'\"]+)['\"](\s*%\s*i)?", w)
	base = paths[m.group(1)] + m.group(2)
	if base.endswith('/'):
		continue	# FISH_PATH = FISHING_PATH + 'fish/' - a folder, not a picture
	if m.group(3):
		for i in (1, 2, 3, 4):
			named.add(base % i)
	else:
		named.add(base)
for n in sorted(named):
	if n.lower() not in got:
		fails.append('the window names %s - not in the pack' % n)

for p in sorted(x[:-6] for x in os.listdir(OUT) if x.endswith('.index')):
	if p == B.PACK:
		continue
	for e in m2pack.read_index(os.path.join(OUT, p + '.index'))[2]:
		if e['name'] in files:
			fails.append('%s: also in %s (OUT)' % (e['name'], p))
ix = open(os.path.join(OUT, 'Index'), 'rb').read() if os.path.exists(os.path.join(OUT, 'Index')) else b''
if B.PACK.encode() not in [l.strip() for l in ix.replace(b'\r\n', b'\n').split(b'\n')]:
	fails.append('pack/Index: no %s line' % B.PACK)

print('fishren: %d pack files, %d named by the window, %d problem(s)' % (len(got), len(named), len(fails)))
for x in fails:
	print('  ' + x)
sys.exit(1 if fails else 0)
