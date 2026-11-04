# -*- coding: utf-8 -*-
# MT2009_PLUS_TITLES_V1 - Tytuly in OUT (build_tytuly_packs.py): the 3 certificate records of gamedata/item_proto, their
# item_list.txt and itemdesc.txt lines exactly as patch_tytuly_client.py makes them, pack "tytuly" with exactly files/
# (every sub image's picture in the pack and its rectangle inside it, every plate picture a title_<res>.sub names, every
# texture an effect names, the icons 32x32 TGA), listed in pack/Index, and no other pack of OUT with one of those names.
#   docker run --rm -v /opt/metin2:/opt/metin2 m2pack-lzo python3 <repo>/client-patches/client-2.0.30/tools/tytuly/verify_tytuly.py \
#     <OUT pack dir>
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, '/opt/metin2/cache/tcm/tz')
sys.path.insert(0, '/opt/metin2/cache/arezzo-work/client/az58')
sys.path.insert(0, HERE)
import m2pack  # noqa: E402
import patch_tytuly_client as pc  # noqa: E402
import build_tytuly_packs as B  # noqa: E402

OUT = [a for a in sys.argv[1:] if not a.startswith('--')][0]
fails = []


def entries(pack):
	pi = os.path.join(OUT, pack + '.index')
	if not os.path.exists(pi):
		fails.append('OUT has no %s pack' % pack)
		return {}
	f, v, ents = m2pack.read_index(pi)
	dat = open(os.path.join(OUT, pack + '.data'), 'rb').read()
	return dict((e['name'], m2pack.read_entry(dat, e)) for e in ents)


def dds_size(b):
	if b[:4] != b'DDS ':
		return None
	return (b[16] | b[17] << 8 | b[18] << 16, b[12] | b[13] << 8 | b[14] << 16)	# width, height


def tga_size(b):
	if len(b) < 18 or b[2] not in (2, 10):
		return None
	return (b[12] | b[13] << 8, b[14] | b[15] << 8)


have = {}
have.update(entries('gamedata'))
have.update(entries('dbdata'))
for name, job in sorted(pc.JOBS.items()):
	if name not in have:
		fails.append('%s missing' % name)
		continue
	nb, changed = job(have[name])
	if changed:
		fails.append('%s: %d record(s) / line(s) not as the patcher makes them' % (name, changed))
pack = entries(B.ICON_PACK)
files = B.pack_files()
if pack != files:
	fails.append('%s: entries differ from files/ (%d / %d)' % (B.ICON_PACK, len(pack), len(files)))
for it in pc.items():
	if tga_size(pack.get(it[3], b'')) != (32, 32):
		fails.append('%s: not a 32x32 true-colour TGA in the pack' % it[3])


def ui_path(rel):
	rel = rel.strip().strip('"').replace('\\', '/').lower()
	return rel if rel.startswith('d:/') else 'd:/ymir work/ui/' + rel


subs = 0
for name, b in sorted(pack.items()):
	if not name.endswith('.sub'):
		continue
	text = b.decode('latin-1')
	if text.startswith('title subImage'):
		kv = dict(l.split(None, 1) for l in text.splitlines() if len(l.split(None, 1)) == 2)
		img = ui_path(kv.get('image', ''))
		size = dds_size(pack.get(img, b''))
		if not size:
			fails.append('%s: picture %s not in the pack' % (name, img))
			continue
		l, t, r, bt = (int(kv[k]) for k in ('left', 'top', 'right', 'bottom'))
		if not (0 <= l < r <= size[0] and 0 <= t < bt <= size[1]):
			fails.append('%s: rectangle %d,%d-%d,%d outside the %dx%d picture' % (name, l, t, r, bt, size[0], size[1]))
		subs += 1
	elif '/titles/title_' in name:
		kv = dict(l.split(None, 1) for l in text.splitlines() if len(l.split(None, 1)) == 2)
		for key in ('left_image', 'middle_image', 'right_image'):
			p = 'd:/ymir work/' + kv.get(key, '').strip().replace('\\', '/').lower()
			if not tga_size(pack.get(p, b'')):
				fails.append('%s: %s %s not in the pack' % (name, key, p))
		if 'sprites' in kv:
			d = 'd:/ymir work/' + kv['sprites'].strip().replace('\\', '/').lower()
			for i in range(int(kv.get('sprites_count', '0'))):
				if ('%s%02d.sub' % (d, i)) not in pack:
					fails.append('%s: banner frame %s%02d.sub missing' % (name, d, i))
		subs += 1
for name, b in sorted(pack.items()):
	if name.endswith('.mse'):
		folder = name.rsplit('/', 1)[0] + '/'
		for ref in re.findall(r'"([^"]+\.(?:dds|tga|mde))"', b.decode('latin-1'), re.I):
			if (folder + ref.lower()) not in pack:
				fails.append('%s: texture %s not in the pack' % (name, ref))
for need in ('d:/ymir work/ui/titlesystem_001.dds', 'd:/ymir work/ui/game/title/char_face.dds',
		'd:/ymir work/effect/etc/title/crown01.mse'):
	if need not in pack:
		fails.append('%s missing' % need)
for p in sorted(f[:-6] for f in os.listdir(OUT) if f.endswith('.index')):
	if p == B.ICON_PACK:
		continue
	for e in m2pack.read_index(os.path.join(OUT, p + '.index'))[2]:
		if e['name'] in files:
			fails.append('%s also in %s' % (e['name'], p))
ix = open(os.path.join(OUT, 'Index'), 'rb').read() if os.path.exists(os.path.join(OUT, 'Index')) else b''
if B.ICON_PACK.encode() not in [l.strip() for l in ix.replace(b'\r\n', b'\n').split(b'\n')]:
	fails.append('Index: no %s line' % B.ICON_PACK)
if fails:
	print('TYTULY FAILED (%d):' % len(fails))
	for f in fails:
		print('  ' + f)
	sys.exit(1)
print('tytuly OK: 3 certificates, pack %s %d entries (%d .sub checked), Index' % (B.ICON_PACK, len(pack), subs))
