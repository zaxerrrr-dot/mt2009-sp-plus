#!/usr/bin/env python3
"""MT2009_PLUS_ITEMSHOP_V3_V1 - the database of the second ItemShop (linux-port/docker/itemshop/app/shop3,
the "V3 Itemshop Premium" web package).

  gen_itemshop3_sql.py --extract <package web_db/db.sql>
      once, from the package: the Polish rows of its locale_game (bonus names) and skills (skill book
      names) into v3_pl_data.json next to this script, with the package's mojibake undone (its dump
      is cp1250 text read as cp1252 and stored as UTF-8 of that).

  gen_itemshop3_sql.py
      writes linux-port/docker/mariadb/playerbot/itemshop3_schema.sql from v3_pl_data.json, the
      package's EApplyTypes (app/shop3/include/functions/items.php) and the Arezzo costume list of
      the old shop (app/itemshop/arezzo_costumes.php, made by tools/azcostume) - run again when that
      list changes. MT2009_PLUS_ITEMSHOP_V3_V6: and from global/v3_extra.json (tools/itemshop3/gen_global_catalog.py) -
      the V3-only lines, the costume set pieces and the set chests; run it again after that one.

The package's own tables (history, settings, redeem codes, ...) are real tables in itemshop3; its
catalogue tables are VIEWS onto ours, so the second shop always sells what the old one sells, at the
same price, in the same currency:
  shop        <- common.itemshop_items, the IN-GAME shop's lines with their promotions and flash offers, in the
                 in-game window's categories (CATEGORIES below) - MT2009_PLUS_ITEMSHOP_V3_V3; until V3 it was
                 itemshop.ishop_items (pay_type 1 = cash "SM", 2 = the catalogue's currency 'mileage' =
                 Smocze Znaki "SZ", paid from account.cash_mark - MT2009_PLUS_SZ_UNIFIED_V1; an Arezzo costume
                 offer is unavailable while the Arezzo module is off, as in the old shop); with
                 world.item_proto's wear restrictions as 0/1 columns anti_female .. anti_wolfman (the
                 shop hides what the character cannot wear) and stackable (ITEM_FLAG_STACKABLE: the
                 quantity choice) - MT2009_PLUS_ITEMSHOP_V3_V2
  categories  <- CATEGORIES below (V3; was itemshop.ishop_category)
  bundle_items<- empty since V3 (the in-game catalogue has no package offers)
  item_names  <- world.item_proto locale_name (shop names for a vnum the proto lacks)
  itemdesc    <- itemshop.ishop_items desc
  item_list   <- img/item/<vnum>.png for every vnum of common.itemshop_items (the web catalogue's icon name first)
  item_proto  <- world.item_proto, numbers turned into the names the package compares with
Idempotent: CREATE ... IF NOT EXISTS, CREATE OR REPLACE VIEW, INSERT IGNORE.
"""
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.normpath(os.path.join(HERE, '..', '..'))
DATA = os.path.join(HERE, 'v3_pl_data.json')
APP = os.path.join(REPO, 'linux-port', 'docker', 'itemshop', 'app')
OUT = os.path.join(REPO, 'linux-port', 'docker', 'mariadb', 'playerbot', 'itemshop3_schema.sql')
MARK = 'MT2009_PLUS_ITEMSHOP_V3_V1'


def _bytes(s):
	# cp1252 for the characters it has, the byte itself for the C1 controls it lacks (0x81, 0x9c ...)
	out = bytearray()
	for c in s:
		try:
			out += c.encode('cp1252')
		except UnicodeEncodeError:
			if ord(c) > 255:
				raise
			out.append(ord(c))
	return bytes(out)


def unmojibake(s):
	# 'UmiejÃªtnoÂœci' -> 'Umiejętności': UTF-8 of cp1252 characters that were cp1250 bytes.
	try:
		return _bytes(_bytes(s).decode('utf-8')).decode('cp1250')
	except (UnicodeEncodeError, UnicodeDecodeError):
		return s


def sql_rows(text, table):
	"""The value tuples of every INSERT INTO `table` (...) VALUES ...; statement."""
	rows = []
	for m in re.finditer(r'INSERT INTO `%s` \(([^)]*)\) VALUES\s*' % re.escape(table), text):
		cols = [c.strip().strip('`') for c in m.group(1).split(',')]
		i = m.end()
		while True:
			assert text[i] == '(', text[i:i + 40]
			i += 1
			vals = []
			while True:
				if text[i] == "'":
					i += 1
					buf = []
					while True:
						c = text[i]
						if c == '\\':
							buf.append({'n': '\n', 'r': '\r', 't': '\t', '0': '\0'}.get(text[i + 1], text[i + 1]))
							i += 2
						elif c == "'" and text[i + 1] == "'":
							buf.append("'")
							i += 2
						elif c == "'":
							i += 1
							break
						else:
							buf.append(c)
							i += 1
					vals.append(''.join(buf))
				else:
					j = i
					while text[j] not in ',)':
						j += 1
					v = text[i:j].strip()
					vals.append(None if v == 'NULL' else int(v))
					i = j
				if text[i] == ',':
					i += 1
					while text[i] == ' ':
						i += 1
					continue
				assert text[i] == ')'
				i += 1
				break
			rows.append(dict(zip(cols, vals)))
			while text[i] in ' \r\n':
				i += 1
			if text[i] == ',':
				i += 1
				while text[i] in ' \r\n':
					i += 1
				continue
			assert text[i] == ';'
			break
	return rows


def extract(db_sql):
	text = open(db_sql, encoding='utf-8').read()
	out = {'locale_game': [], 'skills': []}
	for r in sql_rows(text, 'locale_game'):
		if r['lang'] == 'pl':
			out['locale_game'].append([r['type'], r['bonus'], unmojibake(r['name'])])
	for r in sql_rows(text, 'skills'):
		if r['lang'] == 'pl':
			out['skills'].append([r['vnum'], r['type'], unmojibake(r['name'])])
	json.dump(out, open(DATA, 'w', encoding='utf-8'), ensure_ascii=False, indent=0)
	print('extracted %d bonus names, %d skill names -> %s' % (len(out['locale_game']), len(out['skills']), DATA))


def q(s):
	return "'" + str(s).replace('\\', '\\\\').replace("'", "\\'") + "'"


def php_list(path, key):
	t = open(path, encoding='utf-8').read()
	i = t.index("'%s' => [" % key)
	seg = t[i:t.index(']', i)]
	return re.findall(r"'([A-Z0-9_]+)'", seg)


# Our item_proto numbers -> the package's names (the C++ enum order the package and our
# ProtoReader share; only what the shop pages read: type, the subtypes of the gear and
# of the "use" items, limits and the three applies).
ITEM_TYPES = ['ITEM_NONE', 'ITEM_WEAPON', 'ITEM_ARMOR', 'ITEM_USE', 'ITEM_AUTOUSE', 'ITEM_MATERIAL', 'ITEM_SPECIAL',
	'ITEM_TOOL', 'ITEM_LOTTERY', 'ITEM_ELK', 'ITEM_METIN', 'ITEM_CONTAINER', 'ITEM_FISH', 'ITEM_ROD', 'ITEM_RESOURCE',
	'ITEM_CAMPFIRE', 'ITEM_UNIQUE', 'ITEM_SKILLBOOK', 'ITEM_QUEST', 'ITEM_POLYMORPH', 'ITEM_TREASURE_BOX',
	'ITEM_TREASURE_KEY', 'ITEM_SKILLFORGET', 'ITEM_GIFTBOX', 'ITEM_PICK', 'ITEM_HAIR', 'ITEM_TOTEM', 'ITEM_BLEND',
	'ITEM_COSTUME', 'ITEM_DS', 'ITEM_SPECIAL_DS', 'ITEM_EXTRACT', 'ITEM_SECONDARY_COIN', 'ITEM_RING', 'ITEM_BELT',
	'ITEM_PET', 'ITEM_MEDIUM', 'ITEM_GACHA']
SUB_TYPES = {
	1: ['WEAPON_SWORD', 'WEAPON_DAGGER', 'WEAPON_BOW', 'WEAPON_TWO_HANDED', 'WEAPON_BELL', 'WEAPON_FAN', 'WEAPON_ARROW',
		'WEAPON_MOUNT_SPEAR', 'WEAPON_CLAW', 'WEAPON_QUIVER', 'WEAPON_BOUQUET'],
	2: ['ARMOR_BODY', 'ARMOR_HEAD', 'ARMOR_SHIELD', 'ARMOR_WRIST', 'ARMOR_FOOTS', 'ARMOR_NECK', 'ARMOR_EAR'],
	3: ['USE_POTION', 'USE_TALISMAN', 'USE_TUNING', 'USE_MOVE', 'USE_TREASURE_BOX', 'USE_MONEYBAG', 'USE_BAIT',
		'USE_ABILITY_UP', 'USE_AFFECT', 'USE_CREATE_STONE', 'USE_SPECIAL', 'USE_POTION_NODELAY', 'USE_CLEAR',
		'USE_INVISIBILITY', 'USE_DETACHMENT', 'USE_BUCKET', 'USE_POTION_CONTINUE', 'USE_CLEAN_SOCKET',
		'USE_CHANGE_ATTRIBUTE', 'USE_ADD_ATTRIBUTE', 'USE_ADD_ACCESSORY_SOCKET', 'USE_PUT_INTO_ACCESSORY_SOCKET',
		'USE_ADD_ATTRIBUTE2', 'USE_RECIPE', 'USE_CHANGE_ATTRIBUTE2', 'USE_BIND', 'USE_UNBIND', 'USE_TIME_CHARGE_PER',
		'USE_TIME_CHARGE_FIX', 'USE_PUT_INTO_BELT_SOCKET', 'USE_PUT_INTO_RING_SOCKET'],
	10: ['METIN_NORMAL', 'METIN_GOLD'],
	28: ['COSTUME_BODY', 'COSTUME_HAIR', 'COSTUME_MOUNT', 'COSTUME_ACCE', 'COSTUME_WEAPON'],
}
LIMIT_TYPES = ['LIMIT_NONE', 'LEVEL', 'STR', 'DEX', 'INT', 'CON', 'PC_BANG', 'REAL_TIME', 'REAL_TIME_FIRST_USE',
	'TIMER_BASED_ON_WEAR']


def elt(expr, names, other="''"):
	return 'COALESCE(ELT(%s + 1, %s), %s)' % (expr, ', '.join(q(n) for n in names), other)


# MT2009_PLUS_ITEMSHOP_V3_V2: ITEM_ANTIFLAG_* (common/item_length.h) the shop filters the offers by - the character
# of the signed in-game link (header.php): a man does not see women's costumes, a sura no shaman-only item.
ANTI_FLAGS = [('female', 1 << 0), ('male', 1 << 1), ('warrior', 1 << 2), ('assassin', 1 << 3), ('sura', 1 << 4),
	('shaman', 1 << 5), ('wolfman', 1 << 18)]


# MT2009_PLUS_ITEMSHOP_V3_V3: the in-game window's categories, in its order (root/uiitemshop.py
# ITEMSHOP_CATEGORIES_SORT): (our id, name, kind, icon of images/gf/cat_<icon>.png, index ranges, parent).
# kind: items (by index), featured (running promotions + the premium and flash offer cards), marks (every line in
# Smocze Znaki), auctions (the flash offers), voucher / premium / topup (pages and the top-up link, no items).
# MT2009_PLUS_ITEMSHOP_V3_V4: the owner's round 2 - "Wyglad postaci" (kind group: its own list is every line of its
# subcategories) over Fryzury, Kostiumy, "Nakladki na bron i szarfy" (the sashes' skins 30800.. were there already),
# Pety and Mounty; parent = the group's id (0 = a top category). The index ranges stay the in-game window's, so
# every line of the in-game shop is still listed exactly once.
CATEGORIES = [
	(1, 'Polecane', 'featured', 'star', [], 0),
	(2, 'Wyposażenie', 'items', 'shield-alt', [(1, 99)], 0),
	(3, 'Uszlachetnianie', 'items', 'refine', [(451, 459)], 0),
	(4, 'VIPy', 'items', 'gem', [(101, 113)], 0),
	(18, 'Wygląd postaci', 'group', 'look', [], 0),
	(5, 'Fryzury', 'items', 'cut', [(301, 450), (10000, 19999)], 18),
	(6, 'Kostiumy', 'items', 'tshirt', [(20000, 29999)], 18),
	(7, 'Nakładki na broń i szarfy', 'items', 'khanda', [(30000, 39999)], 18),
	(8, 'Pety', 'items', 'paw', [(40000, 49999)], 18),
	(9, 'Mounty', 'items', 'horse', [(50000, 59999)], 18),
	(19, 'Sety Bonusowe', 'sets', 'gem', [], 18),
	(10, 'Małżeństwo', 'items', 'heart', [(201, 299)], 0),
	(11, 'Zwoje i księgi', 'items', 'magic', [(601, 699)], 0),
	(12, 'Smocze Znaki', 'marks', 'marks', [], 0),
	(13, 'Kupony SM', 'items', 'service', [(901, 905)], 0),
	(14, 'Wykorzystaj voucher', 'voucher', 'ticket', [], 0),
	(15, 'Oferty Błyskawiczne', 'auctions', 'bolt', [], 0),
	(16, 'Konto Premium', 'premium', 'crown', [], 0),
	(17, 'Doładuj SM!', 'topup', 'coins', [], 0),
]
CAT_MARKS = 12
CAT_AUCTIONS = 15
# MT2009_PLUS_ITEMSHOP_V3_V6: the owner's round 3 - "Sety Bonusowe" under "Wygląd postaci" (kind sets: every line that is a
# piece of a costume set with a bonus by the parts worn - itemshop3.set_items - and the sets' chests, which are V3 lines
# of category 19); the V3-only lines (itemshop3.v3_lines, tools/itemshop3/gen_global_catalog.py -> global/v3_extra.json):
# what the big servers' list has and ours did not, the set pieces not sold yet, and the chests rolled at purchase.
V3_EXTRA = os.path.join(HERE, 'global', 'v3_extra.json')

# root/uiitemshop.py ITEMSHOP_CUSTOM_ITEM_DATA: the in-game window adds this to the name of the line at that index.
NAME_SUFFIX = {1: '(30 godzin)', 5: '(7 dni)', 101: '(1 dzień)', 102: '(3 dni)', 103: '(1 dzień)', 104: '(3 dni)',
	105: '(1 dzień)', 106: '(3 dni)', 107: '(1 dzień)', 108: '(3 dni)', 109: '(1 dzień)', 110: '(3 dni)',
	111: '(30 dni)', 112: '(30 dni)', 608: '(3+1)', 610: '(Paczka 25)'}

ITEM_FLAG_STACKABLE = 1 << 2		# common/item_length.h
ITEM_ANTIFLAG_STACK = 1 << 15
USE_VIP = 31				# ITEM_USE subtype of the VIP effects (CItemShopManager::BuyItem: not an item, a premium time)
PREMIUM_TOKEN_VNUM = 72199		# ... except Przepustka Triumfu, which is an item


def shop_view(az_vnums):
	ranges = []
	for cid, name, kind, icon, rr, parent in CATEGORIES:
		for lo, hi in rr:
			ranges.append('WHEN i.`index` BETWEEN %d AND %d THEN %d' % (lo, hi, cid))
	in_range = 'CASE %s ELSE 0 END' % ' '.join(ranges)
	auction = '(ta.item_index IS NOT NULL AND UNIX_TIMESTAMP(ta.start_time) > 0 AND UNIX_TIMESTAMP(ta.end_time) > 0)'
	promo = '(pm.item_index IS NOT NULL AND NOW() >= pm.start_time AND NOW() < pm.end_time)'
	suffix = 'CASE i.`index` %s ELSE \'\' END' % ' '.join('WHEN %d THEN %s' % (k, q(' ' + v)) for k, v in sorted(NAME_SUFFIX.items()))
	arezzo = ('(i.vnum IN (%s) AND COALESCE((SELECT qf.lValue FROM player.quest qf WHERE qf.dwPID = 0 AND qf.szName = \'mt2009_arezzo_closed\' LIMIT 1), 1) > 0)' % az_vnums)
	# MT2009_PLUS_ITEMSHOP_V3_V6: the owner's fixed prices in this shop (itemshop3.line_overrides: price, 30 days, the 30-day
	# variant of an item without a timer) - the in-game catalogue keeps its own
	GV = 'COALESCE(o.vnum, i.vnum)'
	webdesc = lambda v: '(SELECT d.`desc` FROM itemshop.ishop_items d WHERE d.vnum = %s AND d.`desc` IS NOT NULL AND d.`desc` <> \'\' ORDER BY d.id LIMIT 1)' % v
	# MT2009_PLUS_ITEMSHOP_V3_V6: a piece of a costume set with a bonus (itemshop3.set_items) is also listed in "Sety
	# Bonusowe", in the order of its set
	setcols = lambda v: ['IF(EXISTS(SELECT 1 FROM itemshop3.set_items si WHERE si.vnum = %s), 1, 0) AS in_sets' % v,
		'COALESCE((SELECT MIN(si.sort) FROM itemshop3.set_items si WHERE si.vnum = %s), 0) AS set_sort' % v,
		'COALESCE((SELECT MIN(si.set_id) FROM itemshop3.set_items si WHERE si.vnum = %s), 0) AS set_id' % v]
	common_tail = lambda: ['0 AS socket0', '0 AS socket1', '0 AS socket2', '0 AS socket3', '0 AS socket4', '0 AS socket5'] + ['0 AS attrtype%d, 0 AS attrvalue%d' % (n, n) for n in range(7)]
	cols = [
		'i.`index` AS id',
		# the category the line is listed under: a flash offer only under the flash offers, a line in an index range
		# under it, else Smocze Znaki for a line in marks; 0 = the in-game window does not show it either
		'CASE WHEN %s THEN %d ELSE COALESCE(NULLIF(%s, 0), IF(i.currency + 0 = 2, %d, 0)) END AS category' % (auction, CAT_AUCTIONS, in_range, CAT_MARKS),
		"'2026-01-01 00:00:00' AS date", '1 AS type',
		'%s AS description' % webdesc(GV),
		'i.currency + 0 AS pay_type',
		'IF(%s, pm.price, COALESCE(o.price, i.price)) AS coins' % promo,
		'COALESCE(o.price, i.price) AS base_price', 'IF(%s, 1, 0) AS promo' % promo, 'IF(%s, pm.end_time, NULL) AS promo_end' % promo,
		'i.count AS count', '%s AS vnum' % GV,
		# the engine never hands the line's sockets over (GiveItem: vnum and count only)
	] + common_tail()
	cols += [
		'IF(%s, 0, IF(%s, IF(NOW() >= ta.start_time AND NOW() < ta.end_time AND (ta.max_amount = 0 OR COALESCE(tc.buy_count, 0) < ta.max_amount), 1, 0), 1)) AS available' % (arezzo, auction),
		'NULL AS last_bought', 'IF(%s, ta.end_time, NULL) AS expire' % auction, '0 AS discount', 'NULL AS discount_expire',
		"0 AS polymorph", "'FIX' AS book_type", '0 AS book', 'COALESCE(o.minutes, 0) AS time', '0 AS limit_all', '0 AS limit_account',
		'NULL AS bonuses', '0 AS bonuses_count', '0 AS friend', '0 AS wheel_level', '0 AS jackpot',
	]
	cols += ['IF(COALESCE(pr.antiflag, 0) & %d, 1, 0) AS anti_%s' % (bit, name) for name, bit in ANTI_FLAGS]
	cols += [
		# the in-game window's quantity choice: stackable and not ANTIFLAG_STACK (1, and 5 / 10 within the stack size)
		'IF(COALESCE(pr.flag, 0) & %d AND NOT COALESCE(pr.antiflag, 0) & %d, 1, 0) AS stackable' % (ITEM_FLAG_STACKABLE, ITEM_ANTIFLAG_STACK),
		'GREATEST(COALESCE(pr.stack, 1), 1) AS max_stack',
		'CONCAT(COALESCE(CONVERT(pr.locale_name USING utf8mb4), CONCAT(\'Vnum: \', %s)), %s) AS name' % (GV, suffix),
		'i.minLevel AS min_level',
		'IF(pr.type = 3 AND pr.subtype = %d AND i.vnum <> %d, 1, 0) AS vip' % (USE_VIP, PREMIUM_TOKEN_VNUM),
		'COALESCE(pr.value0, 0) AS vip_type', 'COALESCE(pr.value1, 0) AS vip_hours', 'COALESCE(pr.value0, 0) AS value0',
		'IF(%s, 1, 0) AS auction' % auction,
		'IF(%s, ta.start_time, NULL) AS auction_start' % auction,
		'IF(%s, ta.max_amount, 0) AS auction_max' % auction,
		'IF(%s, ta.account_limit, 0) AS auction_account_limit' % auction,
		'IF(%s, COALESCE(tc.buy_count, 0), 0) AS auction_bought' % auction,
		# CItemShopManager::CanSendTimeAuction: shown from a day before its start until an hour after its end
		'IF(%s AND NOW() > ta.start_time - INTERVAL 1 DAY AND NOW() < ta.end_time + INTERVAL 1 HOUR, 1, 0) AS auction_visible' % auction,
		'IF(%s, 1, 0) AS arezzo_locked' % arezzo,
		# MT2009_PLUS_ITEMSHOP_V3_V6: where the line comes from, its chest (0 = none), its own picture
		"'game' AS source", '0 AS chest', "'' AS image",
	] + setcols(GV)
	game = ('SELECT %s FROM common.itemshop_items i'
		' LEFT JOIN common.itemshop_promotions pm ON pm.item_index = i.`index`'
		' LEFT JOIN common.itemshop_time_auctions ta ON ta.item_index = i.`index`'
		' LEFT JOIN player.itemshop_time_auction tc ON tc.item_index = i.`index`'
		' LEFT JOIN itemshop3.line_overrides o ON o.idx = i.`index`'
		' LEFT JOIN world.item_proto pr ON pr.vnum = %s'
		# MT2009_PLUS_ITEMSHOP_V3_V7: a set piece any chest gives is sold only through the chests
		' WHERE NOT EXISTS (SELECT 1 FROM itemshop3.chest_only co WHERE co.vnum = %s)' % (', '.join(cols), GV, GV))
	# MT2009_PLUS_ITEMSHOP_V3_V6: the second shop's own lines (itemshop3.v3_lines): the same columns; a line's minutes are
	# its duration (header.php keeps time > 0; Player::CreateItem writes the expiry into socket0, the db core keeps a
	# non-zero socket0 of an award - ClientManager RESULT_SAFEBOX_LOAD), a VIP line's minutes its premium time; a chest
	# (chest > 0) is no item - pages/java/buy.php rolls it (itemshop3.chests / chest_drops / chest_items).
	v3 = [
		'e.id AS id', 'e.category AS category', "'2026-10-24 00:00:00' AS date", '1 AS type',
		"COALESCE(NULLIF(e.description, ''), %s) AS description" % webdesc('e.vnum'),
		'e.pay_type AS pay_type', 'e.price AS coins', 'e.price AS base_price', '0 AS promo', 'NULL AS promo_end',
		'e.count AS count', 'e.vnum AS vnum',
	] + common_tail() + [
		'1 AS available', 'NULL AS last_bought', 'NULL AS expire', '0 AS discount', 'NULL AS discount_expire',
		"0 AS polymorph", "'FIX' AS book_type", '0 AS book', 'e.minutes AS time', '0 AS limit_all', '0 AS limit_account',
		'NULL AS bonuses', '0 AS bonuses_count', '0 AS friend', '0 AS wheel_level', '0 AS jackpot',
	]
	v3 += ['IF(COALESCE(pr.antiflag, 0) & %d, 1, 0) AS anti_%s' % (bit, name) for name, bit in ANTI_FLAGS]
	v3 += [
		# a chest: 1, 3, 5 or 10 at once - each one rolled on its own
		'IF(e.chest > 0, 1, IF(COALESCE(pr.flag, 0) & %d AND NOT COALESCE(pr.antiflag, 0) & %d, 1, 0)) AS stackable' % (ITEM_FLAG_STACKABLE, ITEM_ANTIFLAG_STACK),
		'IF(e.chest > 0, 10, GREATEST(COALESCE(pr.stack, 1), 1)) AS max_stack',
		"IF(e.chest > 0, e.name, CONCAT(COALESCE(CONVERT(pr.locale_name USING utf8mb4), CONCAT('Vnum: ', e.vnum)), IF(e.suffix <> '', CONCAT(' ', e.suffix), ''))) AS name",
		'e.min_level AS min_level',
		'IF(pr.type = 3 AND pr.subtype = %d AND e.vnum <> %d, 1, 0) AS vip' % (USE_VIP, PREMIUM_TOKEN_VNUM),
		'COALESCE(pr.value0, 0) AS vip_type', 'IF(e.minutes > 0, e.minutes DIV 60, COALESCE(pr.value1, 0)) AS vip_hours', 'COALESCE(pr.value0, 0) AS value0',
		'0 AS auction', 'NULL AS auction_start', '0 AS auction_max', '0 AS auction_account_limit', '0 AS auction_bought',
		'0 AS auction_visible', '0 AS arezzo_locked',
		"'v3' AS source", 'e.chest AS chest', 'e.image AS image',
		'IF(e.chest > 0 OR EXISTS(SELECT 1 FROM itemshop3.set_items si WHERE si.vnum = e.vnum), 1, 0) AS in_sets',
		'IF(e.chest > 0, e.set_id * 1000, COALESCE((SELECT MIN(si.sort) FROM itemshop3.set_items si WHERE si.vnum = e.vnum), 0)) AS set_sort',
		'IF(e.chest > 0, e.set_id, COALESCE((SELECT MIN(si.set_id) FROM itemshop3.set_items si WHERE si.vnum = e.vnum), 0)) AS set_id',
	]
	extra = ('SELECT %s FROM itemshop3.v3_lines e LEFT JOIN world.item_proto pr ON pr.vnum = e.vnum'
		' WHERE e.chest > 0 OR NOT EXISTS (SELECT 1 FROM itemshop3.chest_only co WHERE co.vnum = e.vnum)' % ', '.join(v3))
	return 'CREATE OR REPLACE SQL SECURITY DEFINER VIEW itemshop3.shop AS %s UNION ALL %s;' % (game, extra)


def v3_extra_sql(w):
	"""MT2009_PLUS_ITEMSHOP_V3_V6: the second shop's own lines, the costume set pieces and the set chests (generated
	tables: written again at every start from global/v3_extra.json; the rolls and the purchase tokens are kept)."""
	x = json.load(open(V3_EXTRA, encoding='utf-8'))
	w('')
	w('-- MT2009_PLUS_ITEMSHOP_V3_V6: the V3-only lines (tools/itemshop3/gen_global_catalog.py -> global/v3_extra.json): what')
	w('-- the big servers\' list has and the in-game shop does not, the set pieces not sold yet, the set chests. Only this')
	w('-- shop lists them (the in-game window reads common.itemshop_items). Ids from 100000, never reused (global/ids.json).')
	w('CREATE TABLE IF NOT EXISTS itemshop3.v3_lines (id INT NOT NULL PRIMARY KEY, vnum INT NOT NULL DEFAULT 0, count INT NOT NULL DEFAULT 1, price INT NOT NULL, pay_type TINYINT NOT NULL DEFAULT 1, category INT NOT NULL, minutes INT NOT NULL DEFAULT 0, suffix VARCHAR(32) NOT NULL DEFAULT \'\', name VARCHAR(96) NOT NULL DEFAULT \'\', image VARCHAR(96) NOT NULL DEFAULT \'\', description TEXT NULL, chest INT NOT NULL DEFAULT 0, set_id INT NOT NULL DEFAULT 0, min_level INT NOT NULL DEFAULT 0, source VARCHAR(255) NOT NULL DEFAULT \'\', KEY vnum (vnum)) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;')
	w('CREATE TABLE IF NOT EXISTS itemshop3.set_items (vnum INT NOT NULL, set_id INT NOT NULL, sort INT NOT NULL, PRIMARY KEY (vnum, set_id)) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;')
	w('CREATE TABLE IF NOT EXISTS itemshop3.chests (id INT NOT NULL PRIMARY KEY, line INT NOT NULL, set_id INT NOT NULL, name VARCHAR(96) NOT NULL, price INT NOT NULL, image VARCHAR(96) NOT NULL, UNIQUE KEY line (line)) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;')
	w('-- a chest\'s possible results: chance in parts per million (they sum to 1 000 000); a result gives every item_no once,')
	w('-- one of its alternatives (alt_no) - the one the buying character can wear (sex / class), at random among those')
	w('CREATE TABLE IF NOT EXISTS itemshop3.chest_drops (chest_id INT NOT NULL, drop_no INT NOT NULL, ppm INT NOT NULL, label VARCHAR(160) NOT NULL, kind VARCHAR(16) NOT NULL, PRIMARY KEY (chest_id, drop_no)) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;')
	w('CREATE TABLE IF NOT EXISTS itemshop3.chest_items (chest_id INT NOT NULL, drop_no INT NOT NULL, item_no INT NOT NULL, alt_no INT NOT NULL, vnum INT NOT NULL, count INT NOT NULL DEFAULT 1, minutes INT NOT NULL DEFAULT 0, PRIMARY KEY (chest_id, drop_no, item_no, alt_no)) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;')
	w('-- every roll of a chest bought (audit): the purchase token, the roll of the quantity, the result and its chance, the')
	w('-- random number drawn (1..1 000 000), the items and their player.item_award ids')
	w('CREATE TABLE IF NOT EXISTS itemshop3.chest_rolls (id INT NOT NULL AUTO_INCREMENT PRIMARY KEY, token CHAR(32) NOT NULL, account INT NOT NULL, pid INT NOT NULL DEFAULT 0, line INT NOT NULL, chest_id INT NOT NULL, roll_no INT NOT NULL, drop_no INT NOT NULL, ppm INT NOT NULL, rnd INT NOT NULL, label VARCHAR(160) NOT NULL, vnums VARCHAR(255) NOT NULL, award_ids VARCHAR(255) NOT NULL, price INT NOT NULL, pay_type TINYINT NOT NULL, date DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP, KEY account (account), KEY token (token), KEY chest (chest_id, date)) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;')
	w('-- one row a purchase (the token the item window hands out): a second request with the same token (a double click,')
	w('-- a reload) is not paid again - it shows the first one\'s result')
	w('CREATE TABLE IF NOT EXISTS itemshop3.purchase_tokens (token CHAR(32) NOT NULL PRIMARY KEY, account INT NOT NULL, line INT NOT NULL, qty INT NOT NULL, date DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP, result MEDIUMTEXT NULL, KEY account (account)) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;')
	w('-- MT2009_PLUS_ITEMSHOP_V3_V6: the owner\'s fixed prices for the look lines of the in-game catalogue in THIS shop (pets 299 /')
	w('-- with loot 699, mounts, skins and sashes, costumes, hairstyles 299 SM, 30 days): the line\'s price, minutes, and the')
	w('-- 30-day variant of an item without a timer; the in-game window keeps common.itemshop_items as it is')
	w('CREATE TABLE IF NOT EXISTS itemshop3.line_overrides (idx INT NOT NULL PRIMARY KEY, vnum INT NOT NULL, price INT NOT NULL, minutes INT NOT NULL DEFAULT 0) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;')
	w('-- MT2009_PLUS_ITEMSHOP_V3_V7: the set pieces (and their sex / class / duration variants) only the chests give - the')
	w('-- shop view leaves their lines out (the owner: set pieces only from the chests)')
	w('CREATE TABLE IF NOT EXISTS itemshop3.chest_only (vnum INT NOT NULL PRIMARY KEY) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;')
	w('-- MT2009_PLUS_ITEMSHOP_V3_V7: the shop view reads a line\'s description from the web catalogue by vnum - without this')
	w('-- index each of the ~1500 lines scanned the whole table (a category page took 3-5 s)')
	w('ALTER TABLE itemshop.ishop_items ADD INDEX IF NOT EXISTS mt2009_vnum (vnum);')
	w('START TRANSACTION;')
	w('DELETE FROM itemshop3.chest_only;')
	rows = ['(%d)' % v for v in x.get('chest_only', [])]
	for i in range(0, len(rows), 500):
		w('INSERT INTO itemshop3.chest_only (vnum) VALUES %s;' % ', '.join(rows[i:i + 500]))
	w('DELETE FROM itemshop3.line_overrides;')
	rows = ['(%d, %d, %d, %d)' % (o['idx'], o['vnum'], o['price'], o['minutes']) for o in x.get('overrides', [])]
	for i in range(0, len(rows), 300):
		w('INSERT INTO itemshop3.line_overrides (idx, vnum, price, minutes) VALUES %s;' % ', '.join(rows[i:i + 300]))
	w('DELETE FROM itemshop3.v3_lines;')
	w('DELETE FROM itemshop3.set_items;')
	w('DELETE FROM itemshop3.chests;')
	w('DELETE FROM itemshop3.chest_drops;')
	w('DELETE FROM itemshop3.chest_items;')
	chest_set = {c['line']: c['set_id'] for c in x['chests']}
	rows = ['(%d, %d, %d, %d, %d, %d, %d, %s, %s, %s, %s, %d, %d, 0, %s)' % (l['id'], l['vnum'], l['count'], l['price'], l['cur'], l['cat'], l['minutes'],
		q(l['suffix']), q(l['name']), q(l['image']), q(l['desc']), l['chest'], chest_set.get(l['id'], 0), q(l['source'][:255])) for l in x['lines']]
	for i in range(0, len(rows), 100):
		w('INSERT INTO itemshop3.v3_lines (id, vnum, count, price, pay_type, category, minutes, suffix, name, image, description, chest, set_id, min_level, source) VALUES %s;' % ', '.join(rows[i:i + 100]))
	rows = ['(%d, %d, %d)' % (s['vnum'], s['set_id'], s['sort']) for s in x['set_items']]
	for i in range(0, len(rows), 300):
		w('INSERT IGNORE INTO itemshop3.set_items (vnum, set_id, sort) VALUES %s;' % ', '.join(rows[i:i + 300]))
	drops, items = [], []
	w('INSERT INTO itemshop3.chests (id, line, set_id, name, price, image) VALUES %s;' % ', '.join(
		'(%d, %d, %d, %s, %d, %s)' % (c['id'], c['line'], c['set_id'], q(c['name']), c['price'], q(c['image'])) for c in x['chests']))
	for c in x['chests']:
		assert sum(d['ppm'] for d in c['drops']) == 1000000, c['name']
		for d in c['drops']:
			drops.append('(%d, %d, %d, %s, %s)' % (c['id'], d['no'], d['ppm'], q(d['label'][:160]), q(d['kind'])))
			for it in d['items']:
				for a, v in enumerate(it['alts'], 1):
					items.append('(%d, %d, %d, %d, %d, %d, %d)' % (c['id'], d['no'], it['no'], a, v, it['count'], it['minutes']))
	for i in range(0, len(drops), 200):
		w('INSERT INTO itemshop3.chest_drops (chest_id, drop_no, ppm, label, kind) VALUES %s;' % ', '.join(drops[i:i + 200]))
	for i in range(0, len(items), 300):
		w('INSERT INTO itemshop3.chest_items (chest_id, drop_no, item_no, alt_no, vnum, count, minutes) VALUES %s;' % ', '.join(items[i:i + 300]))
	w('COMMIT;')
	w('-- a chest\'s items with what the shop needs to pick the one that fits the character (the wear filter\'s antiflags)')
	w('CREATE OR REPLACE SQL SECURITY DEFINER VIEW itemshop3.chest_items_view AS SELECT c.chest_id, c.drop_no, c.item_no, c.alt_no, c.vnum, c.count, c.minutes, %s, COALESCE(CONVERT(p.locale_name USING utf8mb4), CONCAT(\'Vnum: \', c.vnum)) AS name FROM itemshop3.chest_items c LEFT JOIN world.item_proto p ON p.vnum = c.vnum;'
		% ', '.join('IF(COALESCE(p.antiflag, 0) & %d, 1, 0) AS anti_%s' % (bit, name) for name, bit in ANTI_FLAGS))
	return len(x['lines']), len(x['chests'])


def build():
	data = json.load(open(DATA, encoding='utf-8'))
	applies = php_list(os.path.join(APP, 'shop3', 'include', 'functions', 'items.php'), 'EApplyTypes')
	assert applies[0] == 'APPLY_NONE' and applies[-1] == 'MAX_APPLY_NUM', applies[-3:]
	applies = applies[:-1]
	# Index 97 is APPLY_ACCEDRAIN_RATE in both lists but POINT_MAGIC_ATT_GRADE_BONUS in our engine
	# (db/src/ProtoReader.cpp); the drain rate itself is 177 there. Neither shows a name here.
	applies[97] = 'APPLY_NONE'
	az = open(os.path.join(APP, 'itemshop', 'arezzo_costumes.php'), encoding='utf-8').read()
	az_vnums = re.search(r"define\('MT2009_AREZZO_COSTUME_VNUMS', '([0-9,]+)'\)", az).group(1)

	sub = 'CASE p.type ' + ' '.join('WHEN %d THEN %s' % (t, elt('p.subtype', n)) for t, n in sorted(SUB_TYPES.items())) + " ELSE '' END"
	L = []
	w = L.append
	w('-- %s: generated by tools/itemshop3/gen_itemshop3_sql.py - do not edit by hand.' % MARK)
	w('-- The second ItemShop (app/shop3, "V3 Itemshop Premium"): its own tables, and views onto our catalogue')
	w('-- (itemshop.ishop_items / ishop_category / ishop_bundle_items) and world.item_proto. Run as root by')
	w('-- playerbot-migrate (apply.sh) after itemshop_schema.sql, at every start; idempotent.')
	w('CREATE DATABASE IF NOT EXISTS itemshop3 CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci;')
	w("GRANT ALL PRIVILEGES ON itemshop3.* TO 'metin2'@'%';")
	w('FLUSH PRIVILEGES;')
	w('')
	w('-- The package\'s own tables (web_db/db.sql), utf8mb4, keys inline.')
	LANG = "ENUM('ar','cs','da','de','el','en','es','fr','hu','it','nl','pl','pt','ro','ru','tr') NOT NULL"
	tables = [
		('history', 'id INT NOT NULL AUTO_INCREMENT PRIMARY KEY, account INT NOT NULL, date DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP, item INT NOT NULL, taken INT(1) NOT NULL DEFAULT 1, pay_type INT(1) NOT NULL, coins INT NOT NULL, type INT(1) NOT NULL DEFAULT 1, from_account INT NOT NULL DEFAULT 0, to_player INT NOT NULL DEFAULT 0, KEY account (account), KEY item (item)'),
		('settings', 'id INT NOT NULL AUTO_INCREMENT PRIMARY KEY, name VARCHAR(24) NOT NULL, value VARCHAR(64) NOT NULL, date DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP, UNIQUE KEY name (name)'),
		('locale_game', 'id INT NOT NULL AUTO_INCREMENT PRIMARY KEY, type VARCHAR(64) NOT NULL, bonus INT NOT NULL, lang %s, name TEXT NOT NULL, UNIQUE KEY type_lang (type, lang), KEY bonus (bonus)' % LANG),
		('skills', 'id INT NOT NULL AUTO_INCREMENT PRIMARY KEY, vnum INT NOT NULL, lang %s, type VARCHAR(16) NOT NULL, name VARCHAR(64) NOT NULL, UNIQUE KEY vnum_lang (vnum, lang)' % LANG),
		('mob_names', 'id INT NOT NULL AUTO_INCREMENT PRIMARY KEY, vnum INT NOT NULL, lang %s, name VARCHAR(64) NOT NULL, KEY vnum (vnum)' % LANG),
		('price_list', 'id INT NOT NULL AUTO_INCREMENT PRIMARY KEY, type INT NOT NULL DEFAULT 0, amount INT NOT NULL, value INT NOT NULL, date DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP'),
		('redeem_codes', 'id INT NOT NULL AUTO_INCREMENT PRIMARY KEY, code VARCHAR(16) NOT NULL, type INT(1) NOT NULL DEFAULT 1, item INT NOT NULL DEFAULT 0, UNIQUE KEY code (code)'),
		('slider', 'id INT NOT NULL AUTO_INCREMENT PRIMARY KEY, img TEXT NOT NULL, title TEXT NOT NULL, text TEXT NOT NULL, link TEXT NOT NULL'),
		('transactions', 'id INT NOT NULL AUTO_INCREMENT PRIMARY KEY, account INT NOT NULL, type INT NOT NULL DEFAULT 0, amount INT NOT NULL, value INT NOT NULL, code VARCHAR(64) NOT NULL, email VARCHAR(64) NOT NULL, date DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP'),
		('transactions_admins', 'id INT NOT NULL AUTO_INCREMENT PRIMARY KEY, account INT NOT NULL, to_account INT NOT NULL, type INT NOT NULL, value INT NOT NULL, date DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP'),
		('wheel_players', 'id INT NOT NULL AUTO_INCREMENT PRIMARY KEY, account INT NOT NULL, level INT NOT NULL DEFAULT 1, stage INT NOT NULL DEFAULT 0, last_spin DATETIME DEFAULT NULL, date DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP, UNIQUE KEY account (account)'),
	]
	for name, cols in tables:
		w('CREATE TABLE IF NOT EXISTS itemshop3.%s (%s) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;' % (name, cols))
	w('')
	w('-- Settings the package reads (header.php). Payments, the happy hour and the package\'s own wheel off')
	w('-- (our Kolo Losu is F12). jcoins_back is not read any more: a Smocze Monety purchase gives 100 % back as')
	w('-- Smocze Znaki (the owner, 24.10.2026 - MT2009_PLUS_ITEMSHOP_V3_V2, include/functions/header.php).')
	settings = [('add_type', 'item_award'), ('pagination', '15'), ('paypal', ''), ('wolfman_character', '0'),
		('discount', '0'), ('jcoins_back', '100'), ('epayouts_ip', ''), ('epayouts_uid', '0'), ('epayouts_mid', '0'),
		('wheel_status', '0'), ('wheel_levels', '3'), ('wheel_lv1', '10'), ('wheel_lv2', '20'), ('wheel_lv3', '30'),
		('wheel_lv2_time', '30'), ('wheel_lv3_time', '30'), ('wheel_web', '0')]
	w('INSERT IGNORE INTO itemshop3.settings (name, value) VALUES %s;' % ', '.join('(%s, %s)' % (q(n), q(v)) for n, v in settings))
	w("INSERT IGNORE INTO itemshop3.slider (id, img, title, text, link) VALUES (1, 'images/this/slide_1.jpg', '', 'Nowości prosto z paszczy smoka.', 'items/'), (2, 'images/this/slide_2.jpg', '', '', 'items/');")
	w('')
	w('-- Bonus and skill names, Polish, from the package (v3_pl_data.json).')
	rows = ['(%s, %d, \'pl\', %s)' % (q(t), b, q(n)) for t, b, n in data['locale_game']]
	for i in range(0, len(rows), 200):
		w('INSERT IGNORE INTO itemshop3.locale_game (type, bonus, lang, name) VALUES %s;' % ', '.join(rows[i:i + 200]))
	rows = ['(%d, \'pl\', %s, %s)' % (v, q(t), q(n)) for v, t, n in data['skills']]
	w('INSERT IGNORE INTO itemshop3.skills (vnum, lang, type, name) VALUES %s;' % ', '.join(rows))
	w('')
	w('-- MT2009_PLUS_ITEMSHOP_V3_V3: the catalogue is the IN-GAME shop\'s (the owner, 24.10.2026: "the new shop must have')
	w('-- exactly the same things as the old in-game shop") - common.itemshop_items with its promotions and flash offers,')
	w('-- in the in-game window\'s categories (root/uiitemshop.py ITEMSHOP_CATEGORIES: index ranges, every line in Smocze')
	w('-- Znaki also under "Smocze Znaki", a running promotion under "Polecane", a flash offer only under "Oferty')
	w('-- Blyskawiczne"; a line outside all of them is not shown). The web catalogue (itemshop.ishop_items) gives only')
	w('-- the descriptions and pictures of the same vnums.')
	w('CREATE OR REPLACE SQL SECURITY DEFINER VIEW itemshop3.categories AS %s;' % ' UNION ALL '.join(
		'SELECT %d AS id, %s AS pl, %s AS en, %s AS ro, %s AS icon, 1 AS active, %s AS kind, %d AS sort, %d AS parent' % (cid, q(name), q(name), q(name), q(icon), q(kind), n, parent)
		for n, (cid, name, kind, icon, ranges, parent) in enumerate(CATEGORIES)))
	w('-- The flash offers\' counters (the game\'s base dump has the table; a world without it gets an empty one).')
	w('CREATE TABLE IF NOT EXISTS player.itemshop_time_auction (item_index INT(10) NOT NULL, buy_count INT(10) NOT NULL DEFAULT 0, PRIMARY KEY (item_index)) ENGINE=InnoDB DEFAULT CHARSET=latin1;')
	n_lines, n_chests = v3_extra_sql(w)
	w(shop_view(az_vnums))
	w('-- No package offers in the in-game catalogue (the view keeps its columns for the shop\'s code).')
	w('CREATE OR REPLACE SQL SECURITY DEFINER VIEW itemshop3.bundle_items AS SELECT b.id AS id, b.item_id AS item_id, b.vnum AS vnum, b.count AS count, b.socket0 AS socket0, b.socket1 AS socket1, b.socket2 AS socket2 FROM itemshop.ishop_bundle_items b WHERE 1 = 0;')
	w('CREATE OR REPLACE SQL SECURITY DEFINER VIEW itemshop3.item_names AS SELECT p.vnum AS id, p.vnum AS vnum, \'pl\' AS lang, p.locale_name AS name FROM world.item_proto p;')
	w('CREATE OR REPLACE SQL SECURITY DEFINER VIEW itemshop3.itemdesc AS SELECT i.id AS id, i.vnum AS vnum, \'pl\' AS lang, i.`desc` AS description FROM itemshop.ishop_items i WHERE i.`desc` IS NOT NULL AND i.`desc` <> \'\';')
	w('-- The picture of a vnum: img/item/<vnum>.png (tools/itemshop3/gen_shop_icons.py makes the missing ones from the')
	w('-- client\'s icons); the web catalogue\'s own icon name where it has one for the vnum.')
	w('CREATE OR REPLACE SQL SECURITY DEFINER VIEW itemshop3.item_list AS SELECT g.vnum AS id, g.vnum AS vnum, CONCAT(\'item/\', COALESCE((SELECT MIN(i.vnum_icon) FROM itemshop.ishop_items i WHERE i.vnum = g.vnum), g.vnum), \'.png\') AS src FROM (SELECT vnum FROM common.itemshop_items UNION SELECT vnum FROM itemshop3.v3_lines WHERE vnum > 0 UNION SELECT vnum FROM itemshop3.chest_items) g;')
	w('-- What the shop wrote: the quantity of a purchase (the flash offers\' account limit counts pieces).')
	w('ALTER TABLE itemshop3.history ADD COLUMN IF NOT EXISTS quantity INT NOT NULL DEFAULT 1;')
	w('-- The voucher tab\'s tries (5 a minute an account, as the game counts them per character).')
	w('CREATE TABLE IF NOT EXISTS itemshop3.voucher_tries (id INT NOT NULL AUTO_INCREMENT PRIMARY KEY, account INT NOT NULL, date DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP, KEY account_date (account, date)) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;')
	cols = ['p.vnum AS id', '%s AS item_type' % elt('p.type', ITEM_TYPES, "'ITEM_NONE'"), '%s AS sub_type' % sub, 'p.size AS size',
		"'' AS flag", 'p.magic_pct AS magic_pct']
	for n in range(2):
		cols += ['%s AS limit_type%d' % (elt('p.limittype%d' % n, LIMIT_TYPES, "'LIMIT_NONE'"), n), 'p.limitvalue%d AS limit_value%d' % (n, n)]
	for n in range(3):
		cols += ['%s AS addon_type%d' % (elt('p.applytype%d' % n, applies, "'APPLY_NONE'"), n), 'p.applyvalue%d AS addon_value%d' % (n, n)]
	cols += ['p.value%d AS value%d' % (n, n) for n in range(6)]
	cols += ['p.socket_pct AS gain_socket', 'p.addon_type AS attu_addon']
	w('CREATE OR REPLACE SQL SECURITY DEFINER VIEW itemshop3.item_proto AS SELECT %s FROM world.item_proto p;' % ', '.join(cols))
	open(OUT, 'w', encoding='utf-8', newline='\n').write('\n'.join(L) + '\n')
	print('wrote %s (%d bonus names, %d skills, %d Arezzo vnums, %d V3 lines, %d set chests)' % (OUT, len(data['locale_game']), len(data['skills']), az_vnums.count(',') + 1, n_lines, n_chests))


if __name__ == '__main__':
	if len(sys.argv) == 3 and sys.argv[1] == '--extract':
		extract(sys.argv[2])
	elif len(sys.argv) == 1:
		build()
	else:
		sys.exit(__doc__)
