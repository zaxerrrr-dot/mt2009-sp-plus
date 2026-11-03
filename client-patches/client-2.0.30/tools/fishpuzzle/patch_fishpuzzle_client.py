# -*- coding: utf-8 -*-
# MT2009_PLUS_FISH_PUZZLE_V1 / V2 - Event Rybacki - Puzzle (the owner, 3 November 2026; pl-wiki "Event Rybacki - Puzzle",
# "Pudlo wedkarskich puzzli", "Zl. Skrzynia na Ryby (D)") in the client's data. The server's side:
# linux-port/docker/mariadb/playerbot/fish_puzzle.sql (world.item_proto - keep the two equal), server-patches/fishpuzzle.
#
#   25106  Pudlo wedkarskich puzzli     ITEM_QUEST, stack 200; V2: the package's antiflags (no drop, no give, no private
#   25107  Luks. pudlo wedk. puzzli     shop - its item_proto.txt); used, it opens the puzzle game (root/uifishpuzzle.py,
#                                       uiminigamefishevent.py), where it is opened for a piece
#   83001  Zl. Skrzynia na Ryby (M)     ITEM_GIFTBOX, one a slot, opened 1 / 2 / 3 times - the reward of a finished
#   83002  Zl. Skrzynia na Ryby (S)     board by its attempts (25+ / 11-24 / 10 or fewer)
#   83003  Zl. Skrzynia na Ryby (D)
# The official vnums and names (GF 26.1.11 item_list, Owsap's pl item_proto); the icons GF's icon/item/25106.tga,
# 25107.tga and 25111.tga (GF's item_list gives 83001-83003 the one 25111.tga) - not in the players' install:
# build_fishpuzzle_packs.py packs them (pack "fishpuzzle", with the window's pictures).
# Records: copies of 30228's with every value cleared (tools/monstercard's card_record), as tools/spirala.
# MT2009_PLUS_FISH_PUZZLE_V3 (COPIES): the chests' items the client lacked or named wrong - 72309 Podrecznik Kowala (a
# copy of 70039's record), 72310 Zwoj Egzorcyzmu (71001's twin, was "NoNAme", no item_list / itemdesc line), 72027 Dlon
# Przebicia (was "Dlon Krytyka") and 72048's description (it said +20% piercing; the item is +10% critical).
#   docker run --rm -v /opt/metin2:/opt/metin2 m2pack-lzo python3 \
#     <repo>/client-patches/client-2.0.30/tools/fishpuzzle/patch_fishpuzzle_client.py <item_proto> <item_list.txt> <itemdesc.txt> [<out dir>]
import os
import struct
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'monstercard'))
import patch_monstercard_client as base  # noqa: E402

FLAG_STACKABLE = 4
# V2: the package's ANTI_DROP | ANTI_GIVE | ANTI_MYSHOP (= fish_puzzle.sql 73856); the chests: no stacking only (32768, as 50270)
ANTI_BOX = 128 | 8192 | 65536
ANTI_CHEST = 32768
# MT2009_PLUS_FISH_PUZZLE_V3: the descriptions of the pl-wiki's item pages ("Opis"), then how to use the item
BOX_DESC = (u'Zawiera losowy element puzzli do zabawy w wędkarskie puzzle. Kliknij prawym przyciskiem myszy, aby '
	u'otworzyć okno puzzli - tam otworzysz pudło i ułożysz element.')
DELUXE_DESC = (u'Zawiera duży kawałek układanki do udziału w Evencie Rybackim (element 3 x 2). Kliknij prawym '
	u'przyciskiem myszy, aby otworzyć okno puzzli.')
CHEST_DESC = (u'W skrzyni znajduje się cenna nagroda dla ciebie. Nagroda za ułożenie wędkarskich puzzli w %s. '
	u'Można otworzyć %s.')
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


# MT2009_PLUS_FISH_PUZZLE_V3: the chests' items (special_item_group.fishpuzzle.txt) the client lacked or named wrong -
# = fish_puzzle.sql's V3 part. A copy of another record of the client's proto with the vnum and names set (the
# values, flags and prices stay the source's); the icons are the base client's.
# (vnum, source vnum, name or None = the source's, Polish name, item_list icon or None = no line, description)
COPIES = (
	(72309, 70039, u'Blacksmith Handbook', u'Podręcznik Kowala', u'icon/item/70039.tga',
		u'Księga zawiera duszę starego kowala. Jeśli jej użyjesz, zwiększy to szansę na pomyślne ulepszenie przedmiotu '
		u'o 15%. Przedmiot nie ulega zniszczeniu gdy ulepszenie zawiedzie. W przypadku niepowodzenia, jakość przedmiotu '
		u'jest redukowana o 1 poziom.'),
	(72310, 71001, u'Exorcism Scroll', u'Zwój Egzorcyzmu', u'icon/item/71001.tga', u'Uwalnia Cię od klątwy złego ducha.'),
	(72027, 72027, None, u'Dłoń Przebicia', None,
		u'Zwiększa szansę na przeszywające uderzenie o 10% przez 10 minut.'),
	(72048, 72048, None, u'Dłoń Krytyka', None, u'Zwiększa szansę na krytyczne uderzenie o 10% przez 10 minut.'),
)


def items():
	return ITEMS


def copy_record(recs, c):
	vnum, src, name, pl = c[:4]
	r = bytearray(recs[src])
	struct.pack_into('<I', r, 0, vnum)
	if name is not None:
		r[8:41] = base.fixed(name, 33)
	r[41:74] = base.fixed(pl, 33)
	return bytes(r)


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
	for c in COPIES:
		r = copy_record(recs, c)
		if recs.get(c[0]) != r:
			recs[c[0]] = r
			changed += 1
	if not changed:
		return b, 0
	out = b''.join(recs[v] for v in sorted(recs))
	blob = m2pack.mcoz_encode(out, base.ITEM_KEY)
	return b'MIPX' + struct.pack('<IIII', ver, stride, len(recs), len(blob)) + blob, changed


def list_rows():
	return [u'%d\tETC\t%s' % (i[0], i[7]) for i in ITEMS] + [u'%d\tETC\t%s' % (c[0], c[4]) for c in COPIES if c[4]]


def desc_rows():
	return [u'%d\t%s\t%s' % (i[0], i[2], i[8]) for i in ITEMS] + \
		[u'%d\t%s\t%s' % (c[0], c[3], c[5]) for c in COPIES]


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
