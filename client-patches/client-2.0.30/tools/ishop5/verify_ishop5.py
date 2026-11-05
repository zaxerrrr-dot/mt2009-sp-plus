# -*- coding: utf-8 -*-
# MT2009_PLUS_ITEMSHOP_V3_V8 - checks the packs build_ishop5_packs.py wrote (on the OUT of the whole Yohara chain): the 8
# new items' item_proto records (dbdata: vnum, names, type, stack, anti flags, flags, real-time limit), their
# item_list lines (gamedata) with an icon that is in a pack or the repo's root/icon/item, their itemdesc lines (dbdata),
# and the 4 + 3 renamed items' Polish names (item_proto and itemdesc).
#   docker run --rm -v /opt/metin2:/opt/metin2 m2pack-lzo python3 <repo>/client-patches/client-2.0.30/tools/ishop5/verify_ishop5.py \
#     <OUT pack dir> [<BASE pack dir>]
import os
import struct
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, '/opt/metin2/cache/tcm/tz')
sys.path.insert(0, '/opt/metin2/cache/arezzo-work/client/az58')
sys.path.insert(0, HERE)
import m2pack  # noqa: E402
import packlib  # noqa: E402
import patch_ishop5_client as pc  # noqa: E402

args = [a for a in sys.argv[1:] if not a.startswith('--')]
OUT = args[0]
BASE = args[1] if len(args) > 1 else '/opt/metin2/cache/cY/azbase'
ROOT_ICONS = os.path.normpath(os.path.join(HERE, '..', '..', 'root', 'icon', 'item'))
fails = []
# MT2009_PLUS_GROWTH_PET_V1: the pet system's json owns these vnums (tools/pety: build_pety_packs.py runs later and rewrites
# their records and lines on purpose; pety/verify_pety.py checks them) - skipped here
import json as _json  # noqa: E402
PETY_VNUMS = set(int(i['vnum']) for i in _json.load(open(os.path.join(HERE, '..', '..', '..', '..', 'tools', 'pety', 'pety_items.json'),
                                                           encoding='utf-8'))['items'])
WHERE = set()
for _d in (BASE, OUT):
	for _f in os.listdir(_d):
		if _f.endswith('.index'):
			for e in m2pack.read_index(os.path.join(_d, _f))[2]:
				WHERE.add(e['name'])


def entry(pack, name):
	d = OUT if os.path.exists(os.path.join(OUT, pack + '.index')) else BASE
	ents = m2pack.read_index(os.path.join(d, pack + '.index'))[2]
	dat = packlib.rd(os.path.join(d, pack + '.data'))
	for e in ents:
		if e['name'] == name:
			return m2pack.read_entry(dat, e)
	return None


proto = entry('dbdata', 'gamedata/item_proto')
ver, stride, cnt, size = struct.unpack_from('<IIII', proto, 4)
raw = m2pack.mcoz_decode(proto[20:], pc.base.ITEM_KEY)
recs = dict((struct.unpack_from('<I', raw, i * stride)[0], raw[i * stride:(i + 1) * stride]) for i in range(cnt))


def pl_name(r):
	return r[41:74].split(b'\0')[0].decode('cp1250')


for vnum, name, pl, stack, anti, flag, seconds, icon, desc in pc.ITEMS:
	r = recs.get(vnum)
	if r is None:
		fails.append('item_proto %d: missing' % vnum)
		continue
	if pl_name(r) != pl or r[74] != 18 or struct.unpack_from('<III', r, 78) != (stack, anti, flag):
		fails.append('item_proto %d: other record (%s)' % (vnum, pl_name(r)))
	if seconds and struct.unpack_from('<Bi', r, 114) != (pc.LIMIT_REAL_TIME, seconds):
		fails.append('item_proto %d: no real-time limit of %d s' % (vnum, seconds))
for vnum, pl in pc.RENAMES.items():
	if vnum in PETY_VNUMS:
		continue
	if vnum not in recs or pl_name(recs[vnum]) != pl:
		fails.append('item_proto %d: name is not %s' % (vnum, pl))
lst = entry('gamedata', 'gamedata/item_list.txt').decode('cp1250').replace('\r\n', '\n').split('\n')
lst = dict((l.split('\t')[0].strip(), l) for l in lst if l.strip())
desc = entry('dbdata', 'locale/pl/itemdesc.txt').decode('cp1250').replace('\r\n', '\n').split('\n')
desc = dict((l.split('\t')[0].strip(), l) for l in desc if l.strip())
for i in pc.ITEMS:
	k = str(i[0])
	if lst.get(k) != u'%d\tETC\t%s' % (i[0], i[7]):
		fails.append('item_list %s: missing or other' % k)
	if i[7] not in WHERE and not os.path.isfile(os.path.join(ROOT_ICONS, os.path.basename(i[7]))):
		fails.append('item_list %s: icon %s in no pack' % (k, i[7]))
	if desc.get(k) != u'%d\t%s\t%s' % (i[0], i[2], i[8]):
		fails.append('itemdesc %s: missing or other' % k)
for vnum, pl in pc.RENAMES.items():
	line = desc.get(str(vnum))
	if vnum in PETY_VNUMS:
		continue
	if line is not None and line.split('\t')[1] != pl:
		fails.append('itemdesc %d: name is not %s' % (vnum, pl))
print('ishop5: %d new items, %d renamed, %d problem(s)' % (len(pc.ITEMS), len(pc.RENAMES), len(fails)))
for f in fails:
	print('  ' + f)
sys.exit(1 if fails else 0)
