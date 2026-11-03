# -*- coding: utf-8 -*-
# MT2009_PLUS_SPIRALA_CZASU_V1 - Spirala Czasu (10%) / (20%) / (30%) of the second ItemShop (the owner, 3 November 2026;
# pl-wiki "Spirala Czasu (10%)" ...) in the client's data. The server's side: linux-port/docker/mariadb/playerbot/apply.sh
# (world.item_proto - keep the two equal) and quest spirala_czasu.
#
#   72347 / 72348 / 72349  Spirala Czasu (10%) / (20%) / (30%)  ITEM_QUEST, stack 200, no drop / sale / trade / private
#                          shop (the storeroom allowed - pl-wiki "Magazynowanie: Tak"): cuts the remaining time of one
#                          running mission wait by 10 / 20 / 30% (quest spirala_czasu)
# The GF vnums (Owsap's item_names / item_proto); the icon GF 26.1.11's icon/item/72347.tga, which GF's item_list gives all
# three - not in the players' install: build_spirala_packs.py packs it (pack "spirala").
# Records: copies of 30228's with every value cleared (tools/monstercard's card_record), as tools/skrzynieklas.
#   docker run --rm -v /opt/metin2:/opt/metin2 m2pack-lzo python3 \
#     <repo>/client-patches/client-2.0.30/tools/spirala/patch_spirala_client.py <item_proto> <item_list.txt> <itemdesc.txt> [<out dir>]
import os
import struct
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'monstercard'))
import patch_monstercard_client as base  # noqa: E402

# no drop, sale, trade, PK drop, private shop (= the class chests' ANTI_CHEST, apply.sh antiflag 90496)
ANTI = 128 | 256 | 8192 | 16384 | 65536
FLAG_STACKABLE = 4
ICON = u'icon/item/72347.tga'
# pl-wiki's "Opis" (its typo "mocą" put right) and what the spiral does here
DESC = (u'Czekanie nie jest Waszą mocną stroną? Dzięki Spirali Czasu zaoszczędzicie drogocenny czas. Skraca o %d%% '
	u'pozostały czas oczekiwania wybranej misji: badań Biologa, stajennego i konia, 6. i 7. bonusu u Seon-Hae oraz badań '
	u'reliktów. Można używać spirala po spirali. Nie dotyczy ksiąg umiejętności.')
SPIRALS = ((72347, 10), (72348, 20), (72349, 30))


def items():
	"""(vnum, name, Polish name, antiflag, icon, description) of the 3 items"""
	return [(v, u'Time Spiral (%d%%)' % p, u'Spirala Czasu (%d%%)' % p, ANTI, ICON, DESC % p) for v, p in SPIRALS]


def record(template, vnum, name, pl, anti):
	r = bytearray(base.card_record(template, vnum, name, pl, 18, 0, anti))
	struct.pack_into('<II', r, 78, 200, anti)
	struct.pack_into('<I', r, 86, FLAG_STACKABLE)
	return bytes(r)


def item_proto(b):
	import m2pack
	assert b[:4] == b'MIPX'
	ver, stride, cnt, size = struct.unpack_from('<IIII', b, 4)
	assert stride == base.RECORD, stride
	raw = m2pack.mcoz_decode(b[20:], base.ITEM_KEY)
	recs = dict((struct.unpack_from('<I', raw, i * base.RECORD)[0], raw[i * base.RECORD:(i + 1) * base.RECORD]) for i in range(cnt))
	changed = 0
	for vnum, name, pl, anti, _icon, _desc in items():
		r = record(recs[base.TEMPLATE], vnum, name, pl, anti)
		if recs.get(vnum) != r:
			recs[vnum] = r
			changed += 1
	if not changed:
		return b, 0
	out = b''.join(recs[v] for v in sorted(recs))
	blob = m2pack.mcoz_encode(out, base.ITEM_KEY)
	return b'MIPX' + struct.pack('<IIII', ver, stride, len(recs), len(blob)) + blob, changed


def list_rows():
	return [u'%d\tETC\t%s' % (i[0], i[4]) for i in items()]


def desc_rows():
	return [u'%d\t%s\t%s' % (i[0], i[2], i[5]) for i in items()]


def main():
	if len(sys.argv) not in (4, 5):
		raise SystemExit('usage: patch_spirala_client.py <item_proto> <item_list.txt> <itemdesc.txt> [<out dir>]')
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


# the pack builder's jobs (build_spirala_packs.py): an entry's name -> fn(bytes) -> (new bytes, changes)
JOBS = {'gamedata/item_list.txt': lambda b: base.set_rows(b, list_rows()), 'gamedata/item_proto': item_proto,
	'locale/pl/itemdesc.txt': lambda b: base.set_rows(b, desc_rows())}


if __name__ == '__main__':
	main()
