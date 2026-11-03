# -*- coding: utf-8 -*-
# MT2009_PLUS_FISH_PUZZLE_V1 / V2 - Event Rybacki - Puzzle in OUT (build_fishpuzzle_packs.py): the 5 records of
# gamedata/item_proto, their item_list.txt and itemdesc.txt lines exactly as patch_fishpuzzle_client.py makes them, pack
# "fishpuzzle" with exactly files/ (the icons every item_list line names, fishingevnet001.dds and the 11 fish_event .sub
# pictures - each .sub's image is the .dds and its rectangle inside it; V2: banner.sub on public_check.dds and the rules
# locale/pl/fish_event_desc.txt), listed in pack/Index, and no other pack of OUT
# with one of those names.
#   docker run --rm -v /opt/metin2:/opt/metin2 m2pack-lzo python3 <repo>/client-patches/client-2.0.30/tools/fishpuzzle/verify_fishpuzzle.py \
#     <OUT pack dir>
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, '/opt/metin2/cache/tcm/tz')
sys.path.insert(0, '/opt/metin2/cache/arezzo-work/client/az58')
sys.path.insert(0, HERE)
import m2pack  # noqa: E402
import patch_fishpuzzle_client as pc  # noqa: E402
import build_fishpuzzle_packs as B  # noqa: E402

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
icons = entries(B.ICON_PACK)
files = B.pack_files()
want = set(files)
if icons != files:
	fails.append('%s: entries %s differ from files/ %s' % (B.ICON_PACK, sorted(icons), sorted(files)))
for n in set(i[7] for i in pc.items()):
	b = icons.get(n, b'')
	if not (len(b) > 18 and b[2] in (2, 10) and (b[12] | b[13] << 8) == 32 and (b[14] | b[15] << 8) == 32):
		fails.append('%s: not a 32x32 true-colour TGA in the pack' % n)
dds = icons.get('d:/ymir work/ui/fishingevnet001.dds', b'')
if dds[:4] != b'DDS ':
	fails.append('fishingevnet001.dds: not a DDS')
else:
	dh, dw = dds[12] | dds[13] << 8, dds[16] | dds[17] << 8
	subs = [n for n in icons if n.startswith('d:/ymir work/ui/minigame/fish_event/')]
	if len(subs) != 11:
		fails.append('fish_event: %d .sub, want 11' % len(subs))
	for n in subs:
		kv = dict(l.split(None, 1) for l in icons[n].decode('ascii').splitlines() if len(l.split(None, 1)) == 2)
		if kv.get('image', '').strip('"') != 'fishingevnet001.dds':
			fails.append('%s: image %r' % (n, kv.get('image')))
		elif not (0 <= int(kv['left']) < int(kv['right']) <= dw and 0 <= int(kv['top']) < int(kv['bottom']) <= dh):
			fails.append('%s: rectangle outside the %dx%d texture' % (n, dw, dh))
# MT2009_PLUS_FISH_PUZZLE_V2: the banner on public_check.dds and the rules text
chk = icons.get('d:/ymir work/ui/public_check.dds', b'')
banner = icons.get('d:/ymir work/ui/minigame/banner.sub', b'')
if chk[:4] != b'DDS ' or not banner:
	fails.append('banner.sub / public_check.dds missing')
else:
	ch, cw = chk[12] | chk[13] << 8, chk[16] | chk[17] << 8
	kv = dict(l.split(None, 1) for l in banner.decode('ascii').splitlines() if len(l.split(None, 1)) == 2)
	if kv.get('image', '').strip('"') != 'public_check.dds':
		fails.append('banner.sub: image %r' % kv.get('image'))
	elif not (0 <= int(kv['left']) < int(kv['right']) <= cw and 0 <= int(kv['top']) < int(kv['bottom']) <= ch):
		fails.append('banner.sub: rectangle outside the %dx%d texture' % (cw, ch))
desc = icons.get('locale/pl/fish_event_desc.txt', b'')
if b'[ENTER]' not in desc or b'Skrzynia na Ryby (D)' not in desc:
	fails.append('locale/pl/fish_event_desc.txt: missing or not the rules')
for p in sorted(x[:-6] for x in os.listdir(OUT) if x.endswith('.index')):
    if p == B.ICON_PACK:
        continue
    for e in m2pack.read_index(os.path.join(OUT, p + '.index'))[2]:
        if e['name'] in want:
            fails.append('%s: also in %s (OUT)' % (e['name'], p))
ix = open(os.path.join(OUT, 'Index'), 'rb').read() if os.path.exists(os.path.join(OUT, 'Index')) else b''
if B.ICON_PACK.encode() not in [l.strip() for l in ix.replace(b'\r\n', b'\n').split(b'\n')]:
    fails.append('pack/Index: no %s line' % B.ICON_PACK)

print('fishpuzzle: %d items, %d pack files, %d problem(s)' % (len(pc.items()), len(icons), len(fails)))
for x in fails:
    print('  ' + x)
sys.exit(1 if fails else 0)
