# -*- coding: utf-8 -*-
# MT2009_PLUS_TITLES_V1 / V2 - Tytuly (the owner's package "Official Title System Renewal", rebuilt) in the client's data:
# the title certificates. The server's side: linux-port/docker/mariadb/playerbot/tytuly.sql (world.item_proto - keep the
# two equal), server-patches/tytuly, playerbot_titles.cpp.
#
# V2 (the owner, 4 November 2026: "Tytuly jak na wiki ... trzeba kupic certyfikaty w ItemShopie"): one certificate a
# title whose wiki source we do not have, named as pl-wiki names them ("Tytul Czciciel Slonca"), with pl-wiki's text
# ("Natychmiast odblokowuje ten tytul dla twojej postaci. Czas trwania tytulu: ..."):
#   57000 Tytul Heroiczny (30 dni)        57003 Tytul PLUS (30 dni)              57006 Tytul Gwiazda Polarna (365 dni)
#   57001 Tytul Szczesciarz (na stale)    57004 Tytul Legendarny (30 dni)        57007 Tytul Czempion Nyx (na stale)
#   57002 Tytul Czciciel Slonca (365 dni) 57005 Tytul Mistyczny (30 dni)         57008 Tytul Ostatni Ocalaly (3 godziny)
# ITEM_QUEST, one a slot, the wiki's flags (no drop, no NPC sale, no give, no PK drop, no stacking, no private shop =
# 123264; the storeroom allowed); used from the inventory it gives its title (the server's value0 / value1 - not needed
# by the client). The icons: GF's three (icon/item/57000 red, 57001 blue, 57002 green - files/icon/item, pack "tytuly");
# 57003-57008 use one of them (item_list).
# Records: copies of 30228's with every value cleared (tools/monstercard's card_record), as tools/fishpuzzle.
#   docker run --rm -v /opt/metin2:/opt/metin2 m2pack-lzo python3 \
#     <repo>/client-patches/client-2.0.30/tools/tytuly/patch_tytuly_client.py <item_proto> <item_list.txt> <itemdesc.txt> [<out dir>]
import os
import struct
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'monstercard'))
import patch_monstercard_client as base  # noqa: E402

ITEM_QUEST = 18
ANTI = 128 | 256 | 8192 | 16384 | 32768 | 65536	# = tytuly.sql 123264 (V2: + no NPC sale, pl-wiki)
RED, BLUE, GREEN = u'icon/item/57000.tga', u'icon/item/57001.tga', u'icon/item/57002.tga'
USE = (u' Kliknij prawym przyciskiem myszy, aby go użyć - tytuł założysz w oknie tytułów (kliknij portret w '
	u'oknie postaci).')
MORE = u' Kolejny certyfikat przedłuża tytuł.'


def desc(title, time, more=u''):
	return u'Natychmiast odblokowuje tytuł „%s” dla twojej postaci. Czas trwania tytułu: %s.%s%s' % (
		title, time, more, USE)


# (vnum, name, Polish name, icon, description) - the title of each: tytuly.sql value0
ITEMS = (
	(57000, u'Title: Heroic', u'Tytuł Heroiczny', RED, desc(u'Heroiczny', u'30 dni', MORE)),
	(57001, u'Title: Lucky', u'Tytuł Szczęściarz', BLUE, desc(u'Szczęściarz', u'na stałe')),
	(57002, u'Title: Sun Worshipper', u'Tytuł Czciciel Słońca', GREEN, desc(u'Czciciel Słońca', u'365 dni', MORE)),
	(57003, u'Title: PLUS', u'Tytuł PLUS', RED, desc(u'PLUS', u'30 dni', MORE)),
	(57004, u'Title: Legendary', u'Tytuł Legendarny', RED, desc(u'Legendarny', u'30 dni', MORE)),
	(57005, u'Title: Mythic', u'Tytuł Mistyczny', RED, desc(u'Mistyczny', u'30 dni', MORE)),
	(57006, u'Title: North Star', u'Tytuł Gwiazda Polarna', GREEN, desc(u'Gwiazda Polarna', u'365 dni', MORE)),
	(57007, u'Title: Nyx Champion', u'Tytuł Czempion Nyx', BLUE, desc(u'Czempion Nyx', u'na stałe')),
	(57008, u'Title: Last Survivor', u'Tytuł Ostatni Ocalały', BLUE, desc(u'Ostatni Ocalały', u'3 godziny', MORE)),
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
