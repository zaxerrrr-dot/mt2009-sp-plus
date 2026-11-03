# -*- coding: utf-8 -*-
# MT2009_PLUS_FISH_PUZZLE_V1 - Event Rybacki - Puzzle (the owner, 3 November 2026; pl-wiki "Event Rybacki - Puzzle",
# "Pudlo wedkarskich puzzli", "Zl. Skrzynia na Ryby (D)") in the client's data. The server's side:
# linux-port/docker/mariadb/playerbot/fish_puzzle.sql (world.item_proto - keep the two equal), server-patches/fishpuzzle.
#
#   25106  Pudlo wedkarskich puzzli     ITEM_QUEST, stack 200, no drop / sale / private shop: used, it opens the puzzle
#   25107  Luks. pudlo wedk. puzzli     window (root/uifishpuzzle.py), where it is opened for a piece
#   83001  Zl. Skrzynia na Ryby (M)     ITEM_GIFTBOX, one a slot, opened 1 / 2 / 3 times - the reward of a finished
#   83002  Zl. Skrzynia na Ryby (S)     board by its attempts (25+ / 11-24 / 10 or fewer)
#   83003  Zl. Skrzynia na Ryby (D)
# The official vnums and names (GF 26.1.11 item_list, Owsap's pl item_proto); the icons GF's icon/item/25106.tga,
# 25107.tga and 25111.tga (GF's item_list gives 83001-83003 the one 25111.tga) - not in the players' install:
# build_fishpuzzle_packs.py packs them (pack "fishpuzzle", with the window's pictures).
# Records: copies of 30228's with every value cleared (tools/monstercard's card_record), as tools/spirala.
#   docker run --rm -v /opt/metin2:/opt/metin2 m2pack-lzo python3 \
#     <repo>/client-patches/client-2.0.30/tools/fishpuzzle/patch_fishpuzzle_client.py <item_proto> <item_list.txt> <itemdesc.txt> [<out dir>]
import os
import struct
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'monstercard'))
import patch_monstercard_client as base  # noqa: E402

FLAG_STACKABLE = 4
# no drop, sale, PK drop, private shop (= fish_puzzle.sql 82304); the chests: no stacking only (32768, as 50270)
ANTI_BOX = 128 | 256 | 16384 | 65536
ANTI_CHEST = 32768
BOX_DESC = (u'Zawiera losowy element puzzli do zabawy w wędkarskie puzzle (Event Rybacki - Puzzle). Kliknij prawym '
	u'przyciskiem myszy, aby otworzyć okno puzzli - tam otworzysz pudło i ułożysz element.')
DELUXE_DESC = (u'Zawiera luksusowy, duży element puzzli (3 x 2) do zabawy w wędkarskie puzzle (Event Rybacki - Puzzle). '
	u'Kliknij prawym przyciskiem myszy, aby otworzyć okno puzzli.')
CHEST_DESC = u'Nagroda za ułożenie wędkarskich puzzli w %s. Można otworzyć %s.'
# (vnum, name, Polish name, type, stack, antiflag, flags, icon, description)
ITEMS = (
	(25106, u'Fish box', u'Pudło wędkarskich puzzli', 18, 200, ANTI_BOX, FLAG_STACKABLE, u'icon/item/25106.tga', BOX_DESC),
	(25107, u'Fish box(s)', u'Luks. pudło wędk. puzzli', 18, 200, ANTI_BOX, FLAG_STACKABLE, u'icon/item/25107.tga', DELUXE_DESC),
	(83001, u'Gold fish chest (M)', u'Zł. Skrzynia na Ryby (M)', 23, 1, ANTI_CHEST, 0, u'icon/item/25111.tga',
		CHEST_DESC % (u'25 lub więcej próbach', u'jeden raz')),
	(83002, u'Gold fish chest (S)', u'Zł. Skrzynia na Ryby (Ś)', 23, 1, ANTI_CHEST, 0, u'icon/item/25111.tga',
		CHEST_DESC % (u'11-24 próbach', u'dwa razy')),
	(83003, u'Gold fish chest (D)', u'Zł. Skrzynia na Ryby (D)', 23, 1, ANTI_CHEST, 0, u'icon/item/25111.tga',
		CHEST_DESC % (u'10 lub mniej próbach', u'trzy razy')),
)


def items():
	return ITEMS


def record(template, it):
	vnum, name, pl, typ, stack, anti, flags = it[:7]
	r = bytearray(base.card_record(template, vnum, name, pl, typ, 0, anti))
	struct.pack_into('<III', r, 78, stack, anti, flags)
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
	return [u'%d\tETC\t%s' % (i[0], i[7]) for i in ITEMS]


def desc_rows():
	return [u'%d\t%s\t%s' % (i[0], i[2], i[8]) for i in ITEMS]


def main():
	if len(sys.argv) not in (4, 5):
		raise SystemExit('usage: patch_fishpuzzle_client.py <item_proto> <item_list.txt> <itemdesc.txt> [<out dir>]')
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


# the pack builder's jobs (build_fishpuzzle_packs.py): an entry's name -> fn(bytes) -> (new bytes, changes)
JOBS = {'gamedata/item_list.txt': lambda b: base.set_rows(b, list_rows()), 'gamedata/item_proto': item_proto,
	'locale/pl/itemdesc.txt': lambda b: base.set_rows(b, desc_rows())}


if __name__ == '__main__':
	main()
