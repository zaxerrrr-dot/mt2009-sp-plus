# -*- coding: utf-8 -*-
# MT2009_PLUS_CLASS_CHESTS_V1 - the eight class chests of the second ItemShop (the owner's list of 3 November 2026; pl-wiki
# "Skrzynia Sura Broni (D)" and the seven others, "Encyklopedia Urana (D)" ...) in the client's data. The server's side:
# linux-port/docker/mariadb/playerbot/apply.sh (world.item_proto - keep the two equal) and quest skrzynie_klas.
#
#   39048 ... 39062 (even)  Skrzynia <class path> (D)  ITEM_QUEST, stack 200: 10x Mikstura Mądrości (3h) 71155,
#                            20x Zwój Egzorcyzmu 71001, 10x Rada Pustelnika 71094, 5x Pierścień Teleportacji 70058 and the
#                            path's Encyklopedia (D)
#   71204 ... 71218 (even)  Encyklopedia <planet> (D)   ITEM_QUEST, stack 200: 25 random skill instructions (50400 +
#                            skill) of the path
# The GF vnums (= Owsap's item_names, GF 26.1.11's icons); the (M) versions (odd vnums) are not made. The chests' icon
# is GF's 39045 (the big class chest, Owsap's item_list for every (D) chest), the encyclopedias' their own - none of
# them is in the players' install: build_skrzynieklas_packs.py packs them (pack "skrzynieklas").
# Records: copies of 30228's with every value cleared (tools/monstercard's card_record), as tools/ishop5.
#   docker run --rm -v /opt/metin2:/opt/metin2 m2pack-lzo python3 \
#     <repo>/client-patches/client-2.0.30/tools/skrzynieklas/patch_skrzynieklas_client.py <item_proto> <item_list.txt> <itemdesc.txt> [<out dir>]
import os
import struct
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'monstercard'))
import patch_monstercard_client as base  # noqa: E402

# the chest / encyclopedia antiflags: no drop, sale, trade, private shop (the chest may go to the storeroom, the
# encyclopedia not - pl-wiki "Magazynowanie")
ANTI_CHEST = 128 | 256 | 8192 | 16384 | 65536
ANTI_BOOK = ANTI_CHEST | 131072
FLAG_STACKABLE = 4

CONTENT = u'10x Mikstura Mądrości (3h), 20x Zwój Egzorcyzmu, 10x Rada Pustelnika, 5x Pierścień Teleportacji i %s.'
# (chest vnum, chest name, chest Polish name, encyclopedia vnum, its name, its Polish name, the path (dla ...), skills)
PATHS = (
	(39048, u'Body Warrior Chest (L)', u'Skrz. Woj. M. Ciała (D)', 71204, u'Saturn Encyclopedia (L)', u'Encyklopedia Saturna (D)',
	 u'Wojowników Mocy Ciała', (1, 2, 3, 4, 5)),
	(39050, u'Mental Warrior Chest (L)', u'Skrz. Woj.M. Ducho. (D)', 71206, u'Earth Encyclopedia (L)', u'Encyklopedia Ziemi (D)',
	 u'Wojowników Mocy Duchowej', (16, 17, 18, 19, 20)),
	(39052, u'Blade Ninja Chest (L)', u'Skrz. Ninja M.Ostrza (D)', 71208, u'Mars Encyclopedia (L)', u'Encyklopedia Marsa (D)',
	 u'Ninja Mocy Ostrza', (31, 32, 33, 34, 35)),
	(39054, u'Archery Ninja Chest (L)', u'Skrz. Ninja M. Łuku (D)', 71210, u'Jupiter Encyclopedia (L)', u'Encyklop. Jupitera (D)',
	 u'Ninja Mocy Łuku', (46, 47, 48, 49, 50, 51)),
	(39056, u'Weaponry Sura Chest (L)', u'Skrzynia Sura Broni (D)', 71212, u'Uranus Encyclopedia (L)', u'Encyklopedia Urana (D)',
	 u'Sury Broni', (61, 62, 63, 64, 65, 66)),
	(39058, u'Magic Sura Chest (L)', u'Skrzynia Sura Magii (D)', 71214, u'Neptune Encyclopedia (L)', u'Encyklopedia Neptuna (D)',
	 u'Sury Magii', (76, 77, 78, 79, 80, 81)),
	(39060, u'Dragon Shaman Chest (L)', u'Skrz. Szam. M. Smoka (D)', 71216, u'Mercury Encyclopedia (L)', u'Encyklop. Merkurego (D)',
	 u'Szamanów Mocy Smoka', (91, 92, 93, 94, 95, 96)),
	(39062, u'Healing Shaman Chest (L)', u'Skrz. Szam. M. Lecz. (D)', 71218, u'Venus Encyclopedia (L)', u'Encyklopedia Wenus (D)',
	 u'Szamanów Mocy Leczenia', (106, 107, 108, 109, 110, 111)),
)
CHEST_ICON = u'icon/item/39045.tga'


def items():
	"""(vnum, name, Polish name, antiflag, icon, description) of the 16 items"""
	out = []
	for cv, cn, cpl, ev, en, epl, who, _skills in PATHS:
		out.append((cv, cn, cpl, ANTI_CHEST, CHEST_ICON,
			u'W tej wspaniałej skrzyni znajdziesz wiele praktycznych przedmiotów dla swojej postaci: ' + CONTENT % epl))
		out.append((ev, en, epl, ANTI_BOOK, u'icon/item/%d.tga' % ev,
			u'Pakiet zawierający 25 losowo wybranych ksiąg z instrukcjami umiejętności dla %s.' % who))
	return out


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
		raise SystemExit('usage: patch_skrzynieklas_client.py <item_proto> <item_list.txt> <itemdesc.txt> [<out dir>]')
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


# the pack builder's jobs (build_skrzynieklas_packs.py): an entry's name -> fn(bytes) -> (new bytes, changes)
JOBS = {'gamedata/item_list.txt': lambda b: base.set_rows(b, list_rows()), 'gamedata/item_proto': item_proto,
	'locale/pl/itemdesc.txt': lambda b: base.set_rows(b, desc_rows())}


if __name__ == '__main__':
	main()
