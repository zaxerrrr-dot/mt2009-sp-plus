# MT2009_PLUS_ITEMSHOP_V3_V8 - the second ItemShop's round 5 (the owner's sheet, 24 October 2026) in the client's data:
# the items linux-port/docker/mariadb/playerbot/apply.sh adds to world.item_proto (keep them equal) and the global
# list's names of five of ours, the dragon beans' Polish names.
#
#   72800 / 72801  Auto Łowy (7 / 14 dni)     ITEM_QUEST, stack 200 (quest ishop_v3_przedmioty)
#   72802          Szkło Handlu               ITEM_QUEST, real time 7 days (the shop's line 7 / 15 / 30), not stackable
#   72803          Buff Premium SungMa        ITEM_QUEST, real time 1 day (the shop's line 1 / 7 / 15 / 30)
#   72804-72807    Eliksir W. SungMa (SIŁA / WIT / ODP / INT)   ITEM_QUEST, stack 200
#   renamed        55002 Klatka Transportowa, 72322 Karta Resetu, 72323 Karta Przetasowania, 55008 Pergamin Nazwy
#                  Zwierzaka, 55033 Reverti Zwierza, 55034 Revertus Zwierza; 100300 / 100400 / 100500 Zielona /
#                  Niebieska / Różowa Smocza Fasola
#
# New records are copies of 30228's with every value cleared (tools/monstercard's card_record), icons of items the icon
# pack has (nothing new to pack): the ticket 71095, Szkło Intuicji's glass 71113, the premium token, the Sung Ma
# "Jazda" scroll 55050. Idempotent: a record or line that is there is rewritten only when it differs.
# From client 2.0.52 item_proto and itemdesc.txt live in the "dbdata" pack (gamedata/item_proto, locale/pl/itemdesc.txt),
# item_list.txt in gamedata. Run on plain copies of the three files, in the m2pack-lzo image for the proto's MCOZ:
#   docker run --rm -v /opt/metin2:/opt/metin2 m2pack-lzo python3 \
#     <repo>/client-patches/client-2.0.30/tools/ishop5/patch_ishop5_client.py <item_proto> <item_list.txt> <itemdesc.txt> [<out dir>]
# Then the next client's dbdata base for the panel's database editor (as tools/collectoritem).
import os
import struct
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'monstercard'))
import patch_monstercard_client as base  # noqa: E402

LIMIT_REAL_TIME = 7
# (vnum, name, Polish name, stack, antiflag, flag, real-time seconds, icon, description)
ITEMS = (
	(72800, u'Autohunt Ticket 7d', u'Auto Łowy (7 dni)', 200, 74112, 4, 0, u'icon/item/71095.tga',
	 u'Dodaje 7 dni Auto Łowów (liczy się tylko czas w grze). Użyj, aby dodać czas.'),
	(72801, u'Autohunt Ticket 14d', u'Auto Łowy (14 dni)', 200, 74112, 4, 0, u'icon/item/71095.tga',
	 u'Dodaje 14 dni Auto Łowów (liczy się tylko czas w grze). Użyj, aby dodać czas.'),
	(72802, u'Trade Glass', u'Szkło Handlu', 1, 106880, 0, 604800, u'icon/item/71113.tga',
	 u'Dopóki masz je w ekwipunku, Dom Aukcyjny działa na każdej mapie. Użyj, aby otworzyć Dom Aukcyjny.'),
	(72803, u'Premium Buff SungMa', u'Buff Premium SungMa', 1, 106880, 0, 86400, u'icon/item/premium_token.tga',
	 u'Po użyciu daje +10 do wszystkich czterech statystyk Woli SungMa (siła, witalność, odporność, inteligencja) na czas przedmiotu.'),
	(72804, u'SungMa Will Elixir (STR)', u'Eliksir W. SungMa (SIŁA)', 200, 74112, 4, 0, u'icon/item/55050.tga',
	 u'Wzmacnia twoją Wolę SungMa (SIŁA) o +5 na 30 min.'),
	(72805, u'SungMa Will Elixir (VIT)', u'Eliksir W. SungMa (WIT)', 200, 74112, 4, 0, u'icon/item/55050.tga',
	 u'Wzmacnia twoją Wolę SungMa (WIT) o +5 na 30 min.'),
	(72806, u'SungMa Will Elixir (RES)', u'Eliksir W. SungMa (ODP)', 200, 74112, 4, 0, u'icon/item/55050.tga',
	 u'Wzmacnia twoją Wolę SungMa (ODP) o +5 na 30 min.'),
	(72807, u'SungMa Will Elixir (INT)', u'Eliksir W. SungMa (INT)', 200, 74112, 4, 0, u'icon/item/55050.tga',
	 u'Wzmacnia twoją Wolę SungMa (INT) o +5 na 30 min.'),
)
RENAMES = {
	55002: u'Klatka Transportowa', 72322: u'Karta Resetu', 72323: u'Karta Przetasowania', 55008: u'Pergamin Nazwy Zwierzaka',
	55033: u'Reverti Zwierza', 55034: u'Revertus Zwierza',
	100300: u'Zielona Smocza Fasola', 100400: u'Niebieska Smocza Fasola', 100500: u'Różowa Smocza Fasola',
}


def record(template, vnum, name, pl, stack, anti, flag, seconds):
	r = bytearray(base.card_record(template, vnum, name, pl, 18, 0, anti))
	struct.pack_into('<II', r, 78, stack, anti)
	struct.pack_into('<I', r, 86, flag)
	if seconds:
		struct.pack_into('<Bi', r, 114, LIMIT_REAL_TIME, seconds)	# limit 0: type, value
	return bytes(r)


def item_proto(b):
	import m2pack
	assert b[:4] == b'MIPX'
	ver, stride, cnt, size = struct.unpack_from('<IIII', b, 4)
	assert stride == base.RECORD, stride
	raw = m2pack.mcoz_decode(b[20:], base.ITEM_KEY)
	recs = dict((struct.unpack_from('<I', raw, i * base.RECORD)[0], raw[i * base.RECORD:(i + 1) * base.RECORD]) for i in range(cnt))
	changed = 0
	for vnum, name, pl, stack, anti, flag, seconds, _icon, _desc in ITEMS:
		r = record(recs[base.TEMPLATE], vnum, name, pl, stack, anti, flag, seconds)
		if recs.get(vnum) != r:
			recs[vnum] = r
			changed += 1
	for vnum, pl in RENAMES.items():
		if vnum not in recs:
			raise SystemExit('item_proto has no %d to rename' % vnum)
		r = bytearray(recs[vnum])
		r[41:74] = base.fixed(pl, 33)
		if bytes(r) != recs[vnum]:
			recs[vnum] = bytes(r)
			changed += 1
	if not changed:
		return b, 0
	out = b''.join(recs[v] for v in sorted(recs))
	blob = m2pack.mcoz_encode(out, base.ITEM_KEY)
	return b'MIPX' + struct.pack('<IIII', ver, stride, len(recs), len(blob)) + blob, changed


def desc_rows(b):
	"""The new items' lines and, for a renamed item, its line with the new name (its text kept)."""
	text = b.decode('cp1250')
	rows = [u'%d\t%s\t%s' % (i[0], i[2], i[8]) for i in ITEMS]
	for line in text.replace('\r\n', '\n').split('\n'):
		f = line.split('\t')
		if f and f[0].strip().isdigit() and int(f[0]) in RENAMES and len(f) >= 3:
			rows.append(u'\t'.join([f[0], RENAMES[int(f[0])]] + f[2:]))
	return rows


def main():
	if len(sys.argv) not in (4, 5):
		raise SystemExit('usage: patch_ishop5_client.py <item_proto> <item_list.txt> <itemdesc.txt> [<out dir>]')
	proto_path, list_path, desc_path = sys.argv[1:4]
	out_dir = sys.argv[4] if len(sys.argv) == 5 else None
	results = []
	with open(proto_path, 'rb') as f:
		results.append((proto_path, item_proto(f.read())))
	with open(list_path, 'rb') as f:
		results.append((list_path, base.set_rows(f.read(), [u'%d\tETC\t%s' % (i[0], i[7]) for i in ITEMS])))
	with open(desc_path, 'rb') as f:
		d = f.read()
		results.append((desc_path, base.set_rows(d, desc_rows(d))))
	for path, (data, changed) in results:
		target = os.path.join(out_dir, os.path.basename(path)) if out_dir else path
		if out_dir or changed:
			if out_dir and not os.path.isdir(out_dir):
				os.makedirs(out_dir)
			with open(target, 'wb') as f:
				f.write(data)
		print('%s: %d change(s)%s' % (os.path.basename(path), changed, '' if target == path else ' -> ' + target))


if __name__ == '__main__':
	main()
