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
      list changes.

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
	cols = [
		'i.`index` AS id',
		# the category the line is listed under: a flash offer only under the flash offers, a line in an index range
		# under it, else Smocze Znaki for a line in marks; 0 = the in-game window does not show it either
		'CASE WHEN %s THEN %d ELSE COALESCE(NULLIF(%s, 0), IF(i.currency + 0 = 2, %d, 0)) END AS category' % (auction, CAT_AUCTIONS, in_range, CAT_MARKS),
		"'2026-01-01 00:00:00' AS date", '1 AS type',
		'(SELECT d.`desc` FROM itemshop.ishop_items d WHERE d.vnum = i.vnum AND d.`desc` IS NOT NULL AND d.`desc` <> \'\' ORDER BY d.id LIMIT 1) AS description',
		'i.currency + 0 AS pay_type',
		'IF(%s, pm.price, i.price) AS coins' % promo,
		'i.price AS base_price', 'IF(%s, 1, 0) AS promo' % promo, 'IF(%s, pm.end_time, NULL) AS promo_end' % promo,
		'i.count AS count', 'i.vnum AS vnum',
		# the engine never hands the line's sockets over (GiveItem: vnum and count only)
		'0 AS socket0', '0 AS socket1', '0 AS socket2', '0 AS socket3', '0 AS socket4', '0 AS socket5',
	]
	cols += ['0 AS attrtype%d, 0 AS attrvalue%d' % (n, n) for n in range(7)]
	cols += [
		'IF(%s, 0, IF(%s, IF(NOW() >= ta.start_time AND NOW() < ta.end_time AND (ta.max_amount = 0 OR COALESCE(tc.buy_count, 0) < ta.max_amount), 1, 0), 1)) AS available' % (arezzo, auction),
		'NULL AS last_bought', 'IF(%s, ta.end_time, NULL) AS expire' % auction, '0 AS discount', 'NULL AS discount_expire',
		"0 AS polymorph", "'FIX' AS book_type", '0 AS book', '0 AS time', '0 AS limit_all', '0 AS limit_account',
		'NULL AS bonuses', '0 AS bonuses_count', '0 AS friend', '0 AS wheel_level', '0 AS jackpot',
	]
	cols += ['IF(COALESCE(pr.antiflag, 0) & %d, 1, 0) AS anti_%s' % (bit, name) for name, bit in ANTI_FLAGS]
	cols += [
		# the in-game window's quantity choice: stackable and not ANTIFLAG_STACK (1, and 5 / 10 within the stack size)
		'IF(COALESCE(pr.flag, 0) & %d AND NOT COALESCE(pr.antiflag, 0) & %d, 1, 0) AS stackable' % (ITEM_FLAG_STACKABLE, ITEM_ANTIFLAG_STACK),
		'GREATEST(COALESCE(pr.stack, 1), 1) AS max_stack',
		'CONCAT(COALESCE(CONVERT(pr.locale_name USING utf8mb4), CONCAT(\'Vnum: \', i.vnum)), %s) AS name' % suffix,
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
	]
	return ('CREATE OR REPLACE SQL SECURITY DEFINER VIEW itemshop3.shop AS SELECT %s'
		' FROM common.itemshop_items i'
		' LEFT JOIN common.itemshop_promotions pm ON pm.item_index = i.`index`'
		' LEFT JOIN common.itemshop_time_auctions ta ON ta.item_index = i.`index`'
		' LEFT JOIN player.itemshop_time_auction tc ON tc.item_index = i.`index`'
		' LEFT JOIN world.item_proto pr ON pr.vnum = i.vnum;' % ', '.join(cols))


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
	w(shop_view(az_vnums))
	w('-- No package offers in the in-game catalogue (the view keeps its columns for the shop\'s code).')
	w('CREATE OR REPLACE SQL SECURITY DEFINER VIEW itemshop3.bundle_items AS SELECT b.id AS id, b.item_id AS item_id, b.vnum AS vnum, b.count AS count, b.socket0 AS socket0, b.socket1 AS socket1, b.socket2 AS socket2 FROM itemshop.ishop_bundle_items b WHERE 1 = 0;')
	w('CREATE OR REPLACE SQL SECURITY DEFINER VIEW itemshop3.item_names AS SELECT p.vnum AS id, p.vnum AS vnum, \'pl\' AS lang, p.locale_name AS name FROM world.item_proto p;')
	w('CREATE OR REPLACE SQL SECURITY DEFINER VIEW itemshop3.itemdesc AS SELECT i.id AS id, i.vnum AS vnum, \'pl\' AS lang, i.`desc` AS description FROM itemshop.ishop_items i WHERE i.`desc` IS NOT NULL AND i.`desc` <> \'\';')
	w('-- The picture of a vnum: img/item/<vnum>.png (tools/itemshop3/gen_shop_icons.py makes the missing ones from the')
	w('-- client\'s icons); the web catalogue\'s own icon name where it has one for the vnum.')
	w('CREATE OR REPLACE SQL SECURITY DEFINER VIEW itemshop3.item_list AS SELECT g.vnum AS id, g.vnum AS vnum, CONCAT(\'item/\', COALESCE((SELECT MIN(i.vnum_icon) FROM itemshop.ishop_items i WHERE i.vnum = g.vnum), g.vnum), \'.png\') AS src FROM (SELECT DISTINCT vnum FROM common.itemshop_items) g;')
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
	print('wrote %s (%d bonus names, %d skills, %d Arezzo vnums)' % (OUT, len(data['locale_game']), len(data['skills']), az_vnums.count(',') + 1))


if __name__ == '__main__':
	if len(sys.argv) == 3 and sys.argv[1] == '--extract':
		extract(sys.argv[2])
	elif len(sys.argv) == 1:
		build()
	else:
		sys.exit(__doc__)
