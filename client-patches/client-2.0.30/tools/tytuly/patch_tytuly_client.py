# -*- coding: utf-8 -*-
# MT2009_PLUS_TITLES_V1 - Tytuly (the owner's package "Official Title System Renewal", rebuilt) in the client's data: the
# three title certificates (the package's vnums). The server's side: linux-port/docker/mariadb/playerbot/tytuly.sql
# (world.item_proto - keep the two equal), server-patches/tytuly, playerbot_titles.cpp.
#
#   57000  Czerwony Certyfikat Tytułu    ITEM_QUEST, one a slot, the package's antiflags (no drop, no give, no PK drop,
#   57001  Niebieski Certyfikat Tytułu   no stacking, no private shop = 123008); used from the inventory it gives its
#   57002  Zielony Certyfikat Tytułu     title (the server's value0 / value1 - not needed by the client)
# The icons: the package's icon/item/57000-57002.tga (build_tytuly_packs.py packs them, pack "tytuly").
# Records: copies of 30228's with every value cleared (tools/monstercard's card_record), as tools/fishpuzzle.
#   docker run --rm -v /opt/metin2:/opt/metin2 m2pack-lzo python3 \
#     <repo>/client-patches/client-2.0.30/tools/tytuly/patch_tytuly_client.py <item_proto> <item_list.txt> <itemdesc.txt> [<out dir>]
import os
import struct
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'monstercard'))
import patch_monstercard_client as base  # noqa: E402

ITEM_QUEST = 18
ANTI = 128 | 8192 | 16384 | 32768 | 65536	# = tytuly.sql 123008
USE = (u' Kliknij prawym przyciskiem myszy, aby go użyć - tytuł założysz w oknie tytułów (kliknij portret w oknie '
	u'postaci).')
# (vnum, name, Polish name, icon, description)
ITEMS = (
	(57000, u'Red title certificate', u'Czerwony Certyfikat Tytułu', u'icon/item/57000.tga',
		u'Nadaje tytuł Heroiczny na 30 dni; kolejny certyfikat przedłuża go o następne 30 dni.' + USE),
	(57001, u'Blue title certificate', u'Niebieski Certyfikat Tytułu', u'icon/item/57001.tga',
		u'Nadaje na stałe tytuł Szczęściarz.' + USE),
	(57002, u'Green title certificate', u'Zielony Certyfikat Tytułu', u'icon/item/57002.tga',
		u'Nadaje na stałe tytuł Czciciel Słońca (ze złotym banerem).' + USE),
)


def items():
	return ITEMS


def record(template, it):
	vnum, name, pl = it[:3]
	r = bytearray(base.card_record(template, vnum, name, pl, ITEM_QUEST, 0, ANTI))
	struct.pack_into('<III', r, 78, 1, ANTI, 0)	# stack, antiflags, flags (not stackable)
	return bytes(r)


def item_proto(b):
	import m2pack
	assert b[:4] == b'MIPX'
	ver, stride, cnt, size = struct.unpack_from('<IIII', b, 4)
	assert stride == base.RECORD, stride
	raw = m2pack.mcoz_decode(b[20:], base.ITEM_KEY)
	recs = dict((struct.unpack_from('<I', raw, i * base.RECORD)[0], raw[i * base.RECORD:(i + 1) * base.RECORD]) for i in range(cnt))
	changed = 0
	for it in ITEMS:
		r = record(recs[base.TEMPLATE], it)
		if recs.get(it[0]) != r:
			recs[it[0]] = r
			changed += 1
	if not changed:
		return b, 0
	out = b''.join(recs[v] for v in sorted(recs))
	blob = m2pack.mcoz_encode(out, base.ITEM_KEY)
	return b'MIPX' + struct.pack('<IIII', ver, stride, len(recs), len(blob)) + blob, changed


def list_rows():
	return [u'%d\tETC\t%s' % (i[0], i[3]) for i in ITEMS]


def desc_rows():
	return [u'%d\t%s\t%s' % (i[0], i[2], i[4]) for i in ITEMS]


def main():
	if len(sys.argv) not in (4, 5):
		raise SystemExit('usage: patch_tytuly_client.py <item_proto> <item_list.txt> <itemdesc.txt> [<out dir>]')
	proto_path, list_path, desc_path = sys.argv[1:4]
	out_dir = sys.argv[4] if len(sys.argv) == 5 else None
	results = []
	with open(proto_path, 'rb') as f:
		results.append((proto_path, item_proto(f.read())))
	with open(list_path, 'rb') as f:
		results.append((list_path, base.set_rows(f.read(), list_rows())))
	with open(desc_path, 'rb') as f:
		results.append((desc_path, base.set_rows(f.read(), desc_rows())))
	for path, (data, changed) in results:
		target = os.path.join(out_dir, os.path.basename(path)) if out_dir else path
		if out_dir or changed:
			if out_dir and not os.path.isdir(out_dir):
				os.makedirs(out_dir)
			with open(target, 'wb') as f:
				f.write(data)
		print('%s: %d change(s)%s' % (os.path.basename(path), changed, '' if target == path else ' -> ' + target))


# the pack builder's jobs (build_tytuly_packs.py): an entry's name -> fn(bytes) -> (new bytes, changes)
JOBS = {'gamedata/item_list.txt': lambda b: base.set_rows(b, list_rows()), 'gamedata/item_proto': item_proto,
	'locale/pl/itemdesc.txt': lambda b: base.set_rows(b, desc_rows())}


if __name__ == '__main__':
	main()
