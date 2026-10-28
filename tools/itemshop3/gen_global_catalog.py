#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""MT2009_PLUS_ITEMSHOP_V3_V6 - the second ItemShop's catalogue next to the big servers' one, and the costume set chests.

The owner, 24.10.2026 (round 3):
  A. the pl-wiki's "Item-Shop" list (tools/itemshop3/global/wiki/Item-Shop.txt, read 24.10.2026): add what it has at its
     price (their premium coin = 1 SM, their marks = 1 SZ); what our shop has at another price, or does not list,
     stays and goes to the sheet "Różnice u nas"; what our files lack goes to "Brak w plikach"; the same thing under
     another name of ours is used and listed ("Zastąpione"); special offers are skipped (our flash offers stay).
     Fixed prices: pets 299 SM / 30 days, pets with loot 699, mounts / weapon skins and sashes / costumes and
     hairstyles 299 - for every line added here; our existing lines are only compared with them.
  B. every costume set with a bonus by the number of parts worn (the 48 "#Z" sets of costume_sets.txt,
     tools/zestawy) gets its own chest, rolled at purchase: the set's pieces and the other items of its pl-wiki
     chest (or of the model chest), the chances of the global shop's chest the owner saved (global/tr_chances.json).

  gen_global_catalog.py [--db CONTAINER] [--client-list item_list.txt] [--xlsx OUT.xlsx]

Reads (read only) the test stack's database (world.item_proto, common.itemshop_items, the itemshop3.shop view - the
default container mt2009plustest-db, its root password from the container's environment) and the client's
item_list.txt (default /opt/metin2/cache/cY/out/pack gamedata, extracted by the caller; --client-list), then writes:
  tools/itemshop3/global/v3_extra.json    the lines and chests gen_itemshop3_sql.py turns into itemshop3_schema.sql
  tools/itemshop3/global/ids.json         the stable ids of the lines and chests (never reused; history keeps them)
  tools/itemshop3/global/images.json      the pictures the shop needs (fetch_global_images.py downloads them)
  --xlsx: the owner's sheet (needs openpyxl: /opt/metin2/cache/xlsxenv/bin/python)
"""
import argparse
import json
import os
import re
import subprocess
import sys
from collections import OrderedDict, defaultdict

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.normpath(os.path.join(HERE, '..', '..'))
G = os.path.join(HERE, 'global')
sys.path.insert(0, G)
import decisions  # noqa: E402
import owner_decisions  # noqa: E402  MT2009_PLUS_ITEMSHOP_V3_V8

MARK = 'MT2009_PLUS_ITEMSHOP_V3_V6'
WIKI = 'https://pl-wiki.metin2.gameforge.com/index.php?title='
SETS_JSON = os.path.join(REPO, 'linux-port', 'docker', 'itemshop', 'app', 'shop3', 'include', 'db', 'costume_sets.json')
SETS_TXT = os.path.join(REPO, 'linux-port', 'docker', 'game', 'costume_sets.txt')
CLIENT_SETS = os.path.join(REPO, 'client-patches', 'client-2.0.30', 'root', 'costume_set_bonus.py')
IMG_ITEM = os.path.join(REPO, 'linux-port', 'docker', 'itemshop', 'app', 'itemshop', 'img', 'item')
FIRST_LINE_ID, FIRST_CHEST_ID = 100000, 1

# The owner's fixed prices (SM, 30 days) by category of the line.
RULE_PET, RULE_PET_LOOT, RULE_LOOK = 299, 699, 299
CAT_HAIR, CAT_COSTUME, CAT_SKIN, CAT_PET, CAT_MOUNT, CAT_SETS = 5, 6, 7, 8, 9, 19
CAT_NAMES = {1: 'Polecane', 2: 'Wyposażenie', 3: 'Uszlachetnianie', 4: 'VIPy', 5: 'Fryzury', 6: 'Kostiumy',
	7: 'Nakładki na broń i szarfy', 8: 'Pety', 9: 'Mounty', 10: 'Małżeństwo', 11: 'Zwoje i księgi', 12: 'Smocze Znaki',
	13: 'Kupony SM', 15: 'Oferty Błyskawiczne', 19: 'Sety Bonusowe', 0: '(niewidoczne w oknie sklepu w grze)'}
SKIP_SECTIONS = {'Oferty specjalne': 'Oferta specjalna - pomijamy (u nas „oferty błyskawiczne”, zostają bez zmian).',
	'Pakiety Yang': 'Pakiet yang bez ceny na liście - pomijamy.'}
D30, D15, D7, D60 = 43200, 21600, 10080, 86400

# --- the chests
CHEST_PRICE_DEFAULT = 39	# the saved chest of the global shop: 39 of their coin
MODEL_CHEST = 'Majestatyczna Skrzynia Nosiciela Światła'	# the pl-wiki's chest the Turkish one matches 1:1
# The other items of a chest, the pl-wiki's name -> ours (the name our item_proto has, or a vnum). None = not in our
# files (its chance goes to the others, in proportion).
COMMON = {
	'Księga Lidera': 71012, 'Książka Lidera': 71012, 'Książka Lidera+': None,
	'Średni Kupon Wpłaty': None, 'Wysoki Kupon Wpłaty': None,
	# MT2009_PLUS_ITEMSHOP_V3_V8 (the owner: "mamy smocze fasole do ulepszania alchemii"): 100300 / 100400 / 100500
	'Magiczny Kamień': 25042, 'Różowa Smocza Fasola': 100500, 'Zielona Smocza Fasola': 100300, 'Niebieska Smocza Fasola': 100400,
	'Księga Obróbki Kamienia': 71083, 'Zwój Błogosławieństwa': 25041, 'Pakiet Kamieni Duszy': 72058,
	'Smoczy Płomień': 100701, 'smoczy Płomień': 100701, 'Smoczy Płomień (B)': 100700,
	'Zdobna Skrz. z Odłamkiem': 39068, 'Zdobna Skrzynia z Odłamkiem': 39068,
	'Lśniąca Sk. z Odłamkiem': None, 'Lśniąca Skrzynia z Odłamkiem': None,
	'Spirala Czasu (30%)': None, 'Spirala Czasu (20%)': None, 'Spirala Czasu (10%)': None,
	'Licencja Najemnika': None, 'Ekspres. Leczenie Najem.': None, 'Ekspresowe Leczenie Najemnika': None,
	'Wstęp do Świątyni Smoka': None,
	'Eliksir Księżyca (S)': 72730, 'Eliksir Słońca (S)': 72726, 'Eliksir Słońca (Ś)': 72724, 'Eliksir Księżyca (D)': 72729,
	'Kamyki': 95926, 'Biała Perła': 27992, 'Niebieska Perła': 27993, 'Krwawa Perła': 27994,
	'Wzmocnienie Przedmiotu': 71085, 'Zaczarowanie Przedmiotu': 71084, 'Kula Błogosławieństwa': 70024,
	'Błogosławieństwo Życia': 71018, 'Rada Pustelnika': 71094, 'Ognista Runa Aury (10)': 49991, 'Lodowa Runa Aury': 49990,
	'Magiczny Metal': 71026, 'Przepustka': 71095, 'Magiczna Ruda Miedzi': 70035, 'Agat': 30617, 'Dwutlenek Tytanu': 30616,
	'Lizak Magii': 71188, 'Lizak Potęgi': 71136, 'Amulet Nazara': 71202,
	'Kamień Mocy Żywiołów': None, 'Kamień Ochrony Żywiołów': None, 'Pierścień Doświadczenia': None,
	'Wino z Kwiatu Brzosk. XL': None, 'Czerw. Skrzyneczka Losu': None,
	'Skrzynka na Zwierzaka': None, 'Opt. Skrz. Ksiąg Zwierza': None, 'Zaczaruj zwierzaka': None,
}
# MT2009_PLUS_ITEMSHOP_V3_V6 (the owner's rule "what can easily be replaced by another item, replace it at once"): a
# chest item we lack -> the same kind of item we have; it keeps the lacking item's chance. Every other lacking item
# (dragon-soul beans - no refine aid here, guild deposit coupons - no deposits, mercenaries - no such system, Spirala
# Czasu, Wstęp do Świątyni Smoka - our Beran's lair needs no ticket) has its chance split over the others.
SUBST = {
	'Lśniąca Sk. z Odłamkiem': (39068, 'skrzynia z odłamkiem, niższa'),
	'Lśniąca Skrzynia z Odłamkiem': (39068, 'skrzynia z odłamkiem, niższa'),
	'Książka Lidera+': (71012, 'ta sama księga lidera bez „+”'),
	'Wino z Kwiatu Brzosk. XL': (70020, 'to samo wino, zwykła butelka'),
}
# The amulets / rings the owner took out of the ItemShop (apply.sh kola_no_amulets) are not given by a chest either.
OWNER_REMOVED = {71202, 71188, 71199, 70607, 72713, 86064}
# A set's parts a chest gives (not the ring / amulet part, see OWNER_REMOVED).
CHEST_PARTS = ('Kostium', 'Fryzura', 'Nakładka na broń', 'Zwierzak', 'Wierzchowiec', 'Szarfa')
DEFAULT_WEIGHT = 5.0	# an item of a pl-wiki chest the saved chest has no chance for


def norm(s):
	return re.sub(r'\s+', ' ', s.replace('‎', '').replace('_', ' ').strip()).lower()


# ---------------------------------------------------------------- data
def db_query(container, sql):
	env = subprocess.run(['docker', 'exec', container, 'printenv', 'MARIADB_ROOT_PASSWORD'], capture_output=True, text=True, check=True).stdout.strip()
	out = subprocess.run(['docker', 'exec', '-i', container, 'mariadb', '-uroot', '-p' + env, '--default-character-set=utf8mb4', '-N', '-B', '-e', sql],
		capture_output=True, text=True, check=True).stdout
	return [l.split('\t') for l in out.split('\n') if l]


class Data:
	def __init__(self, container, client_list):
		self.proto = {}
		for f in db_query(container, 'SELECT vnum, CONVERT(locale_name USING utf8mb4), type, subtype, limittype0, limitvalue0, limittype1, limitvalue1, value0, value1, value2, antiflag, flag FROM world.item_proto'):
			self.proto[int(f[0])] = dict(name=f[1], type=int(f[2]), sub=int(f[3]), lim=[(int(f[4]), int(f[5])), (int(f[6]), int(f[7]))],
				v0=int(f[8]), v1=int(f[9]), v2=int(f[10]), anti=int(f[11]), flag=int(f[12]))
		self.byname = defaultdict(list)
		for v, p in sorted(self.proto.items()):
			self.byname[norm(p['name'])].append(v)
		# the in-game shop's lines, with the category the second shop lists each under (0 = the in-game window hides it)
		self.lines = OrderedDict()
		for f in db_query(container, 'SELECT i.`index`, i.vnum, i.count, i.price, i.currency + 0, i.minLevel, COALESCE(s.category, 0), COALESCE(s.name, \'\') FROM common.itemshop_items i LEFT JOIN itemshop3.shop s ON s.id = i.`index` ORDER BY i.`index`'):
			self.lines[int(f[0])] = dict(id=int(f[0]), vnum=int(f[1]), count=int(f[2]), price=int(f[3]), cur=int(f[4]), level=int(f[5]), cat=int(f[6]), name=f[7])
		self.shop_vnums = defaultdict(list)
		for l in self.lines.values():
			self.shop_vnums[l['vnum']].append(l['id'])
		self.client = set()
		for line in open(client_list, encoding='cp1250', errors='replace'):
			f = line.split('\t')
			if f and f[0].strip().isdigit():
				self.client.add(int(f[0]))

	def name(self, v):
		return self.proto[v]['name'] if v in self.proto else 'vnum %d' % v

	def days(self, v):
		"""The item's own duration in days (REAL_TIME / REAL_TIME_FIRST_USE limit; 0 = none)."""
		p = self.proto.get(v)
		if not p:
			return 0
		for t, val in p['lim']:
			if t in (7, 8) and val:
				return val / 86400.0
		return 0

	def days_label(self, v):
		p = self.proto.get(v)
		if p and p['type'] == 16 and not self.days(v):
			return 'czas w przedmiocie (unikat)'
		if p and p['type'] == 3 and p['sub'] == 31:
			return '%d godz. premium (VIP)' % p['v1']
		return days_text(self.days(v))

	def timed(self, v):
		p = self.proto.get(v)
		return bool(p) and any(t in (7, 8) for t, val in p['lim'])

	def loot_pet(self, v):
		p = self.proto.get(v)
		return bool(p) and p['type'] == 37 and p['sub'] == 12 and p['v2'] == 1


def days_text(d):
	if not d:
		return 'bez limitu'
	if d >= 1:
		return '%g dni' % round(d, 2) if d != 1 else '1 dzień'
	return '%g godz.' % round(d * 24, 2)


# ---------------------------------------------------------------- the wiki list
def clean(s):
	s = re.sub(r'<br\s*/?>', '\n', s)
	s = re.sub(r"'''?", '', s)
	s = re.sub(r'\[\[(?:Grafika|Plik|File):[^\]]*\]\]', '', s)
	s = re.sub(r'\[\[([^\]|]*)\|([^\]]*)\]\]', r'\2', s)
	s = re.sub(r'\[\[([^\]]*)\]\]', r'\1', s)
	s = re.sub(r'\[https?://\S+ ([^\]]*)\]', r'\1', s)
	s = re.sub(r'<[^>]+>', '', s)
	return s.strip()


def wiki_rows():
	t = open(os.path.join(G, 'wiki', 'Item-Shop.txt'), encoding='utf-8').read()
	lines = t.split('\n')
	rows, sec, sub, i = [], '', '', 0
	while i < len(lines):
		m = re.match(r'^(={2,3})\s*(.*?)\s*\1\s*$', lines[i])
		if m:
			if len(m.group(1)) == 2:
				sec, sub = m.group(2), ''
			else:
				sub = m.group(2)
			i += 1
			continue
		if lines[i].startswith('{|'):
			tbl, i = [], i + 1
			while i < len(lines) and not lines[i].startswith('|}'):
				tbl.append(lines[i])
				i += 1
			headers, cur, trs = [], None, []
			for l in tbl:
				if l.startswith('|-'):
					if cur is not None:
						trs.append(cur)
					cur = []
				elif l.startswith('!'):
					headers += [clean(h.split('|')[-1]) for h in l[1:].split('!!')]
				elif l.startswith('|'):
					body = l[1:]
					mm = re.match(r'^\s*(?:style|class|align|width|colspan|rowspan)[^|\[{]*\|(?!\|)(.*)$', body)
					if mm:
						body = mm.group(1)
					if cur is None:
						cur = []
					cur.append(body)
				elif cur:
					cur[-1] += '\n' + l
			if cur:
				trs.append(cur)
			for r in trs:
				if r and any(c.strip() for c in r):
					rows.append((sec, sub, [h.lower() for h in headers], r))
		i += 1
	out = []
	for sec, sub, h, cells in rows:
		d = dict(zip(h, cells))
		namecell = d.get('przedmiot', cells[1] if len(cells) > 1 else '')
		link = re.findall(r'\[\[(?!Grafika|Plik|File)([^\]|]+)', namecell)
		bullets = lambda k: [clean(x) for x in re.findall(r'^\*\s*(.*)$', d.get(k, ''), re.M)] or ([clean(d.get(k, ''))] if d.get(k, '').strip() else [])
		out.append(dict(section=sec, sub=sub or sec, name=clean(namecell).split('\n')[0].strip().replace('‎', ''),
			name_full=clean(namecell).replace('\n', ' '), link=link[0].strip() if link else '',
			info=clean(d.get('informacja', '')).replace('\n', ' '), time=bullets('czas trwania'), qty=bullets('sztuk'),
			price=bullets('cena')))
	return out


def wiki_url(title):
	return WIKI + title.replace(' ', '_')


def price_text(row):
	parts = []
	for i, p in enumerate(row['price']):
		q = row['qty'][i] if i < len(row['qty']) else ''
		t = row['time'][i] if i < len(row['time']) and row['time'][i] not in ('-', '') else ''
		parts.append(' '.join(x for x in (q, t, p) if x))
	return '; '.join(parts)


# ---------------------------------------------------------------- the build
class Build:
	def __init__(self, data):
		self.d = data
		self.ids = json.load(open(os.path.join(G, 'ids.json'), encoding='utf-8')) if os.path.exists(os.path.join(G, 'ids.json')) else {'lines': {}, 'chests': {}}
		self.lines = OrderedDict()	# key -> line
		self.diff, self.missing, self.replaced, self.added_src = [], [], [], {}
		self.compared = set()		# our line ids the list mentions
		self.chest_subs = OrderedDict()	# (wiki item, our vnum) -> a chest item replaced
		self.fixed = OrderedDict()	# our line index -> the owner's fixed price / 30 days in this shop
		self.untimed = []		# look lines that cannot be made 30 days
		self.r5_done = []		# MT2009_PLUS_ITEMSHOP_V3_V8: "Brak w plikach" rows the owner's round 5 answered

	def line_id(self, key):
		if key not in self.ids['lines']:
			used = list(self.ids['lines'].values())
			self.ids['lines'][key] = max(used) + 1 if used else FIRST_LINE_ID
		return self.ids['lines'][key]

	def chest_id(self, key):
		if key not in self.ids['chests']:
			used = list(self.ids['chests'].values())
			self.ids['chests'][key] = max(used) + 1 if used else FIRST_CHEST_ID
		return self.ids['chests'][key]

	def add_line(self, vnum, count, price, cur, cat, minutes=0, suffix='', source='', note='', set_ids=(), chest=0, name='', image='', desc='', key=None):
		key = key or ('chest:%d' % chest if chest else '%d:%d:%d:%d' % (vnum, count, cur, minutes))
		if key in self.lines:
			l = self.lines[key]
			if source and source not in l['source']:
				l['source'] += ' | ' + source
			if note and note not in l['note']:
				l['note'] = (l['note'] + ' ' + note).strip()
			for s in set_ids:
				if s not in l['sets']:
					l['sets'].append(s)
			return l
		l = dict(id=self.line_id(key), vnum=vnum, count=count, price=price, cur=cur, cat=cat, minutes=minutes, suffix=suffix,
			source=source, note=note, sets=list(set_ids), chest=chest, name=name, image=image, desc=desc)
		self.lines[key] = l
		return l

	# A: the wiki list
	def catalogue(self):
		rows = wiki_rows()
		self.rows = rows
		seen = set()
		for k, r in enumerate(rows):
			if r['section'] == 'Item-Shop':
				continue
			src = '%s / %s: %s' % (r['section'], r['sub'], r['name'])
			if r['sub'] in SKIP_SECTIONS:
				continue
			if r['sub'] == 'Fryzury bez i z atrybutami':
				self.hair_row(r)
				continue
			dec = decisions.ROWS.get((k, r['name']))
			if dec is None:
				raise SystemExit('decisions.py has no row %d %r (the wiki snapshot changed?)' % (k, r['name']))
			seen.add(k)
			if dec['st'] == 'add':
				for ln in dec['lines']:
					self.check_vnum(ln['vnum'], r)
					self.add_line(ln['vnum'], ln['count'], ln['price'], ln['cur'], ln['cat'], ln['minutes'], ln['suffix'], src, dec['note'])
				if dec.get('sub'):
					self.replace_row(r, dec, 'dodane do sklepu')
			elif dec['st'] == 'have':
				for idx in dec['ours']:
					self.compare(idx, r, dec)
				if dec.get('sub'):
					self.replace_row(r, dec, 'już w naszym sklepie (porównane w „Różnice u nas”)')
			elif dec['st'] == 'miss' and k in owner_decisions.BRAK_DONE:
				self.r5_done.append(dict(wiki=r['name'], sub=r['sub'], price=price_text(r), done=owner_decisions.BRAK_DONE[k]))
			elif dec['st'] == 'miss':
				self.missing.append(dict(wiki=r['name'], link=r['link'] or r['name'], sub=r['sub'], info=r['info'], price=price_text(r), note=dec['note']))
		extra = [k for (k, n) in decisions.ROWS if k not in seen]
		if extra:
			raise SystemExit('decisions.py rows the wiki does not have: %s' % extra)

	def replace_row(self, r, dec, how):
		for x in self.replaced:
			if x['ours'][0] == dec['sub'][0]:
				if price_text(r) not in x['price']:
					x['price'] += ' | ' + price_text(r)
				return
		self.replaced.append(dict(wiki=r['name'], link=r['link'] or r['name'], info=r['info'], ours=dec['sub'], how=how, note=dec['note'], price=price_text(r)))

	def check_vnum(self, v, r):
		if v not in self.d.proto:
			raise SystemExit('row %r: vnum %d not in item_proto' % (r['name'], v))
		if v not in self.d.client:
			raise SystemExit('row %r: vnum %d not in the client item_list' % (r['name'], v))

	def global_price(self, r, count):
		"""The list's price of this count (SM/SZ), None when it lists no such quantity."""
		qtys = [int(re.sub(r'\D', '', q.split('+')[0]) or 1) for q in r['qty']] or [1]
		for i, p in enumerate(r['price']):
			m = re.match(r'\s*(\d+)\s*(SM|SZ)', p)
			if not m:
				continue
			q = qtys[i] if i < len(qtys) else qtys[-1]
			if q == count:
				return int(m.group(1)), m.group(2)
		m = re.match(r'\s*(\d+)\s*(SM|SZ)', r['price'][-1]) if r['price'] else None
		return (int(m.group(1)) * count, m.group(2) + ' (cena 1 szt. × %d)' % count) if m and qtys[-1] == 1 else (None, '')

	def rule_price(self, line):
		cat, v = line['cat'], line['vnum']
		if cat == CAT_PET and self.d.proto.get(v, {}).get('type') == 37 and self.d.proto[v]['sub'] == 12:
			return RULE_PET_LOOT if self.d.loot_pet(v) else RULE_PET
		if cat in (CAT_HAIR, CAT_COSTUME, CAT_SKIN, CAT_MOUNT):
			return RULE_LOOK
		return None

	def round5(self):
		"""MT2009_PLUS_ITEMSHOP_V3_V8: the owner's new things - the V3 lines of the items apply.sh / the client add, and the
		jewellery box (a chest like the set chests, rolled at the purchase; its offers of 10+1 / 20+3 are chest lines with
		that many rolls)."""
		for vnum, count, price, cur, cat, minutes, suffix, source in owner_decisions.NEW_LINES:
			if vnum not in self.d.proto:
				raise SystemExit('round 5: vnum %d not in item_proto (apply.sh ishop_v3_items not run on this DB?)' % vnum)
			self.add_line(vnum, count, price, cur, cat, minutes, suffix, source, 'Runda 5 - decyzja właściciela.')
		j = owner_decisions.JEWEL_BOX
		cid = self.chest_id('jewel_box')
		image = 'images/chests/%d.png' % cid
		total = sum(e[2] for e in j['entries'])
		drops = []
		for vnum, minutes, pct, label in j['entries']:
			if vnum not in self.d.proto:
				raise SystemExit('jewel box: vnum %d not in item_proto' % vnum)
			drops.append(dict(label=label, kind='common', weight=pct * 100.0 / total, ppm=int(round(pct * 1000000.0 / total)),
				items=[dict(alts=[vnum], count=1, minutes=minutes, label=label)]))
		drops[0]['ppm'] += 1000000 - sum(x['ppm'] for x in drops)
		desc = ('Szkatuła otworzy się zaraz po zakupie i da jeden losowy przedmiot: miksturę, lizak, amulet, medal lub '
			'pierścień (szanse - zakładka „Szanse”). Przedmiot trafi od razu do magazynu ItemShopu.')
		first = None
		for count, price, suffix in j['offers']:
			l = self.add_line(0, count, price, 1, j['category'], 0, suffix, 'Szkatuła na Biżuterię (decyzja właściciela)', '', [],
				chest=cid, name=j['name'] + (' ' + suffix if suffix else ''), image=image, desc=desc,
				key=('chest:%d' % cid) if count == 1 else ('chest:%d:x%d' % (cid, count)))
			first = first or l
		self.chests.append(dict(id=cid, line=first['id'], set_id=0, set_name='', name=j['name'], price=j['offers'][0][1], image=image,
			image_src=j['wiki_file'], wiki='Szkatuła na Biżuterię', model=False, drops=drops, gone=[],
			durations=dict(body=[7], hair=[7], package=7)))
		self.jewel_lines = [l for l in self.lines.values() if l['image'] == image]

	def overrides(self):
		"""MT2009_PLUS_ITEMSHOP_V3_V8: one row a line of the in-game catalogue: the owner's fixed price / 30 days and his
		decisions on the sheet (owner_decisions.LINES: price, count, category, name, hidden)."""
		out = OrderedDict()
		for f in self.fixed.values():
			out[f['idx']] = dict(idx=f['idx'], vnum=f['vnum'], price=f['price'], minutes=f['minutes'])
		for idx, d in owner_decisions.LINES.items():
			if idx not in self.d.lines:
				# MT2009_PLUS_ITEMSHOP_V3_V9: a line apply.sh took out of the in-game catalogue (Szkło Intuicji, Medal Konny)
				print('owner_decisions: line %d is not in the in-game catalogue any more - skipped' % idx)
				continue
			o = out.setdefault(idx, dict(idx=idx))
			for k, col in (('price', 'price'), ('count', 'count'), ('cat', 'category'), ('name', 'name')):
				if k in d:
					o[col] = d[k]
			if d.get('hide'):
				o['hidden'] = 1
		return [o for o in out.values() if len(o) > 1]

	def chest_only(self):
		"""MT2009_PLUS_ITEMSHOP_V3_V7 (the owner: "anything that drops from any set chest is sold only through the chests"):
		every costume / hair / skin / sash / pet / mount a chest can give, and every variant of it (the same name, type and
		subtype - another sex, class or duration), comes off every list of this shop and cannot be bought on its own. The
		chests' general items (blessing scrolls, books, shard chests ...) stay."""
		pieces = set()
		for c in self.chests:
			for x in c['drops']:
				if x['kind'] == 'common':
					continue
				for it in x['items']:
					pieces |= set(it['alts'])
		only = set(pieces)
		for v in pieces:
			p = self.d.proto[v]
			only |= {w for w in self.d.byname.get(norm(p['name']), []) if self.d.proto[w]['type'] == p['type'] and self.d.proto[w]['sub'] == p['sub']}
		self.only_vnums = only
		self.only_lines = OrderedDict((idx, l) for idx, l in self.d.lines.items() if l['vnum'] in only)
		print('chest-only vnums %d (pieces %d), our lines taken off %d' % (len(only), len(pieces), len(self.only_lines)))

	def chests_of(self, v):
		name = norm(self.d.name(v))
		out = []
		for c in self.chests:
			for x in c['drops']:
				if x['kind'] != 'common' and any(norm(self.d.name(a)) == name for it in x['items'] for a in it['alts']):
					out.append(c['name'])
					break
		return out

	def untimed_note(self, idx):
		for u in self.untimed:
			if u['idx'] == idx:
				return 'Zasady 299/699 SM / 30 dni nie da się zastosować: ' + u['why'] + ' - do decyzji.'
		return ''

	def fixed_prices(self):
		"""MT2009_PLUS_ITEMSHOP_V3_V6 (the owner, after round 3: "wszystkie pety bez łupu 299 sm na 30 dni ... wszystkie
		kostiumy i fryzury 299 sm na 30 dni"): every look line of ours (pets 299 / with loot 699, mounts, skins and sashes,
		costumes, hairstyles 299 SM) becomes a 30-day line in this shop (itemshop3.line_overrides; the in-game catalogue
		stays). A timed item (real time / from the first use) gets the line's own 30 days; an item without a timer its
		30-day variant (the same name and antiflags) when there is one not sold yet; else it is left for the owner."""
		sold = set(self.d.shop_vnums)
		for idx, l in self.d.lines.items():
			if l['cat'] not in (CAT_HAIR, CAT_COSTUME, CAT_SKIN, CAT_PET, CAT_MOUNT) or idx in self.only_lines:
				continue
			p = self.d.proto.get(l['vnum'])
			if not p or (p['type'] == 37 and p['sub'] != 12):
				continue	# the new pet system's eggs and supplies are no pets
			rule = self.rule_price(l)
			if rule is None:
				continue
			vnum, why = l['vnum'], ''
			if not self.d.timed(vnum):
				var = [v for v in self.d.byname.get(norm(p['name']), []) if v != vnum and self.d.proto[v]['anti'] == p['anti'] and self.d.proto[v]['type'] == p['type']
					and abs(self.d.days(v) - 30) < 0.01]
				free = [v for v in var if v not in sold]
				if not free:
					self.untimed.append(dict(idx=idx, l=l, why=('wariant 30 dni (%s) jest już osobną linią sklepu' % ', '.join(map(str, var))) if var else 'przedmiot bez czasu i bez wariantu 30 dni'))
					continue
				vnum, why = free[0], 'wariant 30 dni %d zamiast %d (bez czasu)' % (free[0], l['vnum'])
			if l['price'] == rule and vnum == l['vnum'] and abs(self.d.days(vnum) - 30) < 0.01:
				continue	# already the rule
			self.fixed[idx] = dict(idx=idx, vnum=vnum, price=rule, minutes=D30, old_vnum=l['vnum'], old_price=l['price'], old_days=self.d.days_label(l['vnum']),
				name=l['name'] or self.d.name(l['vnum']), cat=CAT_NAMES.get(l['cat'], l['cat']), why=why)

	def compare(self, idx, r, dec):
		l = self.d.lines.get(idx)
		if not l:
			raise SystemExit('row %r: our in-game shop has no line %d' % (r['name'], idx))
		if idx in self.fixed or idx in self.only_lines or idx in owner_decisions.LINES:
			self.compared.add(idx)
			return	# the owner's fixed price now / only in the chests (sheet "Zmienione ceny (stałe)")
		if idx in self.compared:
			# a second row of the list for the same line of ours (e.g. "Hity" and its own section): one row, both prices
			for d in self.diff:
				if d['id'] == idx and r['name'] not in d['wiki'] and price_text(r) not in d['gprice']:
					d['gprice'] += ' | ' + price_text(r)
			return
		self.compared.add(idx)
		gp, gcur = self.global_price(r, l['count'])
		cur = 'SM' if l['cur'] == 1 else 'SZ'
		rule = self.rule_price(l)
		same = rule is None and gp is not None and gp == l['price'] and gcur.startswith(cur)
		if rule is not None:
			same = l['price'] == rule and abs(self.d.days(l['vnum']) - 30) < 0.01
		if same:
			return
		self.diff.append(dict(id=l['id'], vnum=l['vnum'], name=l['name'] or self.d.name(l['vnum']), cat=CAT_NAMES.get(l['cat'], l['cat']), count=l['count'],
			price='%d %s' % (l['price'], cur), days=self.d.days_label(l['vnum']),
			wiki=r['name'], link=r['link'] or r['name'], gprice=price_text(r), rule=('%d SM / 30 dni (zasada właściciela)' % rule) if rule else '',
			note=((dec['note'] if dec else '') + ' ' + self.untimed_note(idx)).strip()))

	def hair_row(self, r):
		"""A classic hairstyle (19 SM / 29 SM with attributes): ours by name; the owner's rule 299 SM / 30 days."""
		name = re.sub(r'\s*\((K)\)\s*$', '', re.sub(r'\s*(Wojownik|Wojowniczka|Sura Kobieta|Sura|Ninja Kobieta|Ninja|Szamanka|Szaman|Likan)\s*$', '', r['name_full']).strip())
		name = re.sub(r'(Szamanka|Szaman)$', '', name).strip()
		name = re.sub(r'\s*\(K\)', '', name).strip()
		vnums = self.d.byname.get(norm(name), [])
		ours = [i for v in vnums for i in self.d.shop_vnums.get(v, []) if v in self.d.proto and self.d.proto[v]['type'] == 28]
		if 'Likan' in r['name_full']:
			return
		if not ours:
			self.missing.append(dict(wiki=r['name_full'], link=r['link'] or r['name'], sub=r['sub'], info=r['info'], price=price_text(r), note='Brak takiej fryzury w naszym sklepie / plikach.'))
			return
		for idx in ours:
			if idx in self.compared:
				continue
			self.compare(idx, dict(r, name=r['name_full']), dict(note='Fryzura klasyczna: lista 19 SM (bez atrybutów) / 29 SM (z atrybutami); zasada 299 SM / 30 dni.'))

	def not_listed(self):
		"""Our visible lines the list does not mention: listed for the owner (with the fixed price where one applies)."""
		for idx, l in self.d.lines.items():
			if idx in self.compared or l['cat'] in (0, ) or idx in self.fixed or idx in self.only_lines or idx in owner_decisions.LINES:
				continue
			rule = self.rule_price(l)
			if rule is not None and l['price'] == rule and abs(self.d.days(l['vnum']) - 30) < 0.01:
				continue
			self.diff.append(dict(id=idx, vnum=l['vnum'], name=l['name'] or self.d.name(l['vnum']), cat=CAT_NAMES.get(l['cat'], l['cat']), count=l['count'],
				price='%d %s' % (l['price'], 'SM' if l['cur'] == 1 else 'SZ'), days=self.d.days_label(l['vnum']),
				wiki='— (brak na liście)', link='', gprice='', rule=('%d SM / 30 dni (zasada właściciela)' % rule) if rule else '', note=self.untimed_note(idx)))

	# B: the sets and their chests
	def sets(self):
		data = json.load(open(SETS_JSON, encoding='utf-8'))
		self.setlist = [s for s in data['sets'] if s['id'] < 100]	# the "#Z" sets (ids from 100 are the old two-part ones)
		srv = open(SETS_TXT, encoding='utf-8').read()
		cli = open(CLIENT_SETS, encoding='latin-1').read()
		tr = json.load(open(os.path.join(G, 'tr_chances.json'), encoding='utf-8'))
		self.tr = tr
		trw = {norm(r['pl']): r['pct'] for r in tr['rows'] if r['kind'] == 'common'}
		self.trw = trw
		self.costume_w = {r['kind']: r['pct'] for r in tr['rows'] if r['kind'] != 'common'}
		chests = self.wiki_chests()
		self.chests, self.set_rows = [], []
		for s in self.setlist:
			parts = {p['label']: p['vnums'] for p in s['parts']}
			check = []
			ok = True
			for p in s['parts']:
				for v in p['vnums']:
					if v not in self.d.proto:
						check.append('%d brak w item_proto serwera' % v)
						ok = False
					elif v not in self.d.client:
						check.append('%d brak w item_list klienta' % v)
						ok = False
			if not re.search(r'^#Z\tS\t%d\t' % s['id'], srv, re.M):
				check.append('brak linii #Z w costume_sets.txt')
				ok = False
			if not re.search(r'^\t%d: \(' % s['id'], cli, re.M):
				check.append('brak w costume_set_bonus.py klienta')
				ok = False
			bonus = dict(ok=ok, check='; '.join(check) if check else 'tak: części w item_proto serwera i w kliencie, linie #Z serwera (server-patches/zestawy), opis w kliencie (costume_set_bonus.py)')
			# MT2009_PLUS_ITEMSHOP_V3_V7 (the owner, after round 3): the set pieces are not sold on their own any more - only
			# the set chests give them (chest_only below); round 3's 37 piece lines are gone.
			has_look = any(parts.get(x) for x in ('Kostium', 'Fryzura'))
			if not has_look:
				self.set_rows.append(dict(set=s, chest=None, bonus=bonus, why='Zestaw bez kostiumu i fryzury (tylko pet / wierzchowiec / amulet) - bez skrzyni; jego części są w „Sety Bonusowe”.'))
				continue
			if not ok:
				self.set_rows.append(dict(set=s, chest=None, bonus=bonus, why='Brak części lub bonusu w naszych plikach - nie sprzedaję.'))
				continue
			self.set_rows.append(dict(set=s, chest=self.chest(s, parts, chests), bonus=bonus, why=''))

	def wiki_chests(self):
		out = {}
		d = os.path.join(G, 'wiki', 'chests')
		for fn in sorted(os.listdir(d)):
			t = open(os.path.join(d, fn), encoding='utf-8').read()
			m = re.search(r'\|Zawartość\s*=(.*?)\n\|[A-ZŁ][^=\n]*=', t, re.S)
			if not m:
				continue
			title = fn[:-4]
			img = re.search(r'\|image\s*=\s*([^\n|]+)', t)
			price = re.search(r'za\s*(\d+)\s*\[\[Smocze Monety', t)
			out[title] = dict(title=title, body=m.group(1), image=img.group(1).strip() if img else title + '.png',
				price=int(price.group(1)) if price else None, setlink='Bonus Zestawu' in t,
				desc=re.sub(r'\s+', ' ', clean(re.search(r'\|Opis\s*=(.*?)\n\|', t, re.S).group(1))) if re.search(r'\|Opis\s*=(.*?)\n\|', t, re.S) else '')
			out[title]['items'] = self.chest_items(out[title]['body'])
		return out

	@staticmethod
	def chest_items(body):
		"""[(name, count, (days...), is_sub_bullet)] of a pl-wiki chest's "Zawartość"."""
		items = []
		for line in body.split('\n'):
			sub = line.startswith('**')
			for m in re.finditer(r'\{\{ti2?\|([^}]*)\}\}\s*([^{\n]*)', line):
				parts = [p for p in m.group(1).split('|') if '=' not in p]
				name = parts[0].strip() if parts else ''
				rest = m.group(2)
				cnt = re.search(r'x\s*(\d+)', rest)
				days = [int(x) for x in re.findall(r'(\d+)', re.sub(r'x\s*\d+', '', rest))] if re.search(r'\d+\s*(d|dni)\b|\(\d+(/\d+)*d', rest) else []
				items.append((name, int(cnt.group(1)) if cnt else 1, tuple(days), sub))
		return items

	def chest(self, s, parts, chests):
		names = {}
		for label in ('Kostium', 'Fryzura'):
			for v in parts.get(label, []):
				names[norm(self.d.name(v))] = label
		# the pl-wiki chest of this set: the most of its costume / hair names, the fewest of other sets', a set bonus link
		other = set()
		for o in self.setlist:
			if o['id'] != s['id']:
				for p in o['parts']:
					if p['label'] in ('Kostium', 'Fryzura'):
						other |= {norm(self.d.name(v)) for v in p['vnums']}
		best = None
		for c in chests.values():
			mine = sum(1 for n, *_ in c['items'] if norm(n) in names)
			oth = sum(1 for n, *_ in c['items'] if norm(n) in other and norm(n) not in names)
			if mine < 4 or mine - oth < 4:
				continue
			key = (mine - oth, c['setlink'], c['price'] or CHEST_PRICE_DEFAULT)
			if best is None or key > best[0]:
				best = (key, c)
		src = best[1] if best else chests[MODEL_CHEST]
		from_wiki = best is not None
		# durations: the set's costume / hair lines of that chest (short = 2.5 %, long = 1.5 %), the package's (1 %)
		dur = {'Kostium': [], 'Fryzura': []}
		pack = []
		for n, cnt, days, sub in src['items']:
			lab = names.get(norm(n)) if from_wiki else None
			if not from_wiki:
				# the model chest: its own set's names (Nosiciel Światła) are the costume / hair rows
				lab = 'Kostium' if 'Nosiciel' in n else ('Fryzura' if 'Diadem' in n else None)
			if lab and days:
				(pack if sub else dur[lab]).extend(days)
		if not pack:
			# "*Biały Pakiet Azraela (k lub m, 30 dni) wraz z" - the package's own line, without an item template
			for line in src['body'].split('\n'):
				if re.search(r'pakiet', line, re.I) and '{{' not in line:
					pack += [int(x) for x in re.findall(r'(\d+)\s*(?:dni|d)\b', line)]
		if not pack:
			pack = [60] if not from_wiki else [max(dur['Kostium'] + dur['Fryzura'] + [30])]
		pd = max(pack)
		d_body = sorted(set(dur['Kostium'])) or [15, 30]
		d_hair = sorted(set(dur['Fryzura'])) or d_body
		drops = []
		cw = self.costume_w
		look = [(lab, parts[lab]) for lab in ('Kostium', 'Fryzura') if parts.get(lab)]
		pkg_items = []
		for label in CHEST_PARTS:
			vs = [v for v in parts.get(label, []) if v not in OWNER_REMOVED]
			if vs:
				pkg_items.append(dict(alts=vs, count=1, minutes=pd * 1440 if any(self.d.timed(v) for v in vs) else 0, label=label))
		drops.append(dict(label='Pakiet zestawu (%d dni): %s' % (pd, ', '.join(i['label'].lower() for i in pkg_items)), kind='package', weight=cw['package'], items=pkg_items))
		for kind, lab, short in (('hair15', 'Fryzura', True), ('body15', 'Kostium', True), ('hair30', 'Fryzura', False), ('body30', 'Kostium', False)):
			use = lab if parts.get(lab) else ('Kostium' if lab == 'Fryzura' else 'Fryzura')
			ds = d_hair if use == 'Fryzura' else d_body
			days = ds[0] if short else ds[-1]
			drops.append(dict(label='%s zestawu (%d dni)' % (use, days), kind=kind, weight=cw[kind],
				items=[dict(alts=list(parts[use]), count=1, minutes=days * 1440 if any(self.d.timed(v) for v in parts[use]) else 0, label=use)]))
		# the other items: the chest's (not costumes, pets or mounts of any set - those are the set's own above)
		common, gone = [], []
		for n, cnt, days, sub in src['items']:
			if sub or norm(n) in names:
				continue
			subst = SUBST.get(n)
			v = subst[0] if subst else COMMON.get(n, 'look')
			if v == 'look':
				vs = self.d.byname.get(norm(n), [])
				p = self.d.proto.get(vs[0]) if vs else None
				if p and (p['type'] in (28, 37) or 'pieczęć' in n or 'Pakiet' in n and 'Kamieni' not in n):
					continue	# another set's costume / a pet / a package of the pl-wiki chest
				if not vs:
					if re.search(r'pieczęć|\+ ?\(|\+$|Pudełko|Klatka|Skrzynka', n):
						continue
					gone.append(n)
					continue
				v = vs[0]
			if v is None:
				gone.append(n)
				continue
			if v in OWNER_REMOVED:
				gone.append(n + ' (usunięte ze sklepu przez właściciela)')
				continue
			if not subst and any(c['items'][0]['alts'][0] == v and not c.get('subst') for c in common):
				continue
			w = self.trw.get(norm(n))
			if w is None and subst and n.startswith('Lśniąca'):
				w = self.trw.get(norm('Lśniąca Sk. z Odłamkiem'))
			if w is None and n.startswith('Spirala Czasu'):
				w = self.trw.get(norm('Spirala Czasu (30%)'))
			if w is None and norm(n) == norm('Zdobna Skrzynia z Odłamkiem'):
				w = self.trw.get(norm('Zdobna Skrz. z Odłamkiem'))
			if w is None and norm(n) == norm('Książka Lidera'):
				w = self.trw.get(norm('Księga Lidera'))
			common.append(dict(label=(('%dx %s' % (cnt, self.d.name(v))) if cnt > 1 else self.d.name(v)) + ((' (zamiast: %s)' % n) if subst else ''), subst=bool(subst), kind='common', weight=w if w is not None else DEFAULT_WEIGHT,
				weight_src='skrzynia z zapisanej strony' if w is not None else 'brak na zapisanej stronie - przyjęte %g' % DEFAULT_WEIGHT,
				wiki=n, items=[dict(alts=[v], count=cnt, minutes=0, label=n)]))
			if subst:
				self.chest_subs.setdefault((n, v), dict(wiki=n, vnum=v, why=subst[1], chests=[], pct=w if w is not None else DEFAULT_WEIGHT))['chests'].append(s['name'])
		share = 100.0 - sum(x['weight'] for x in drops)
		tot = sum(x['weight'] for x in common)
		for x in common:
			x['weight'] = x['weight'] * share / tot
		drops += common
		# parts per million, summing to exactly 1 000 000
		for x in drops:
			x['ppm'] = int(round(x['weight'] * 10000))
		diff = 1000000 - sum(x['ppm'] for x in drops)
		max(common, key=lambda x: x['ppm'])['ppm'] += diff
		title = src['title'] if from_wiki else 'Skrzynia zestawu %s' % s['name']
		cid = self.chest_id('set:%d' % s['id'])
		price = (src['price'] or CHEST_PRICE_DEFAULT) if from_wiki else CHEST_PRICE_DEFAULT
		# a chest of the model: one picture for all of them (the saved shop chest's)
		image = 'images/chests/%d.png' % cid if from_wiki else 'images/chests/model.png'
		desc = ('Ta magiczna skrzynia otworzy się zaraz po zakupie i da jeden losowy przedmiot - może cały pakiet zestawu '
			'„%s”? Przedmiot trafi od razu do magazynu ItemShopu. Kostium, fryzura i nakładka pasują do postaci, dla '
			'której kupujesz. Szanse - zakładka „Szanse”.' % s['name'])
		line = self.add_line(0, 1, price, 1, CAT_SETS, 0, '', 'Skrzynia zestawu: %s' % s['name'], '', [s['id']], chest=cid, name=title, image=image, desc=desc)
		ch = dict(id=cid, line=line['id'], set_id=s['id'], set_name=s['name'], name=title, price=price, image=image,
			image_src=src['image'], wiki=src['title'] if from_wiki else '', model=not from_wiki, drops=drops, gone=gone,
			durations=dict(body=d_body, hair=d_hair, package=pd))
		self.chests.append(ch)
		return ch

	def out(self):
		lines = [l for l in self.lines.values() if (l['chest'] or l['vnum'] not in self.only_vnums)
			and '%d:%d:%d:%d' % (l['vnum'], l['count'], l['cur'], l['minutes']) not in owner_decisions.V3_REMOVE]
		# set order for "Sety Bonusowe": the set's chest first, then its pieces (ours and the new ones)
		set_items = []
		for s in self.setlist:
			order = 0
			for p in s['parts']:
				if p['label'] not in CHEST_PARTS:
					continue
				for v in p['vnums']:
					if v in OWNER_REMOVED:
						continue
					order += 1
					set_items.append(dict(vnum=v, set_id=s['id'], sort=s['id'] * 1000 + order))
		res = dict(generated_by='tools/itemshop3/gen_global_catalog.py (%s)' % MARK, lines=lines, chests=[
			dict(id=c['id'], line=c['line'], set_id=c['set_id'], name=c['name'], price=c['price'], image=c['image'],
				drops=[dict(no=i + 1, ppm=x['ppm'], label=x['label'], kind=x['kind'],
					items=[dict(no=j + 1, alts=it['alts'], count=it['count'], minutes=it['minutes']) for j, it in enumerate(x['items'])])
					for i, x in enumerate(c['drops'])]) for c in self.chests], set_items=set_items,
			overrides=self.overrides(),
			chest_only=sorted(self.only_vnums))
		json.dump(res, open(os.path.join(G, 'v3_extra.json'), 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
		json.dump(self.ids, open(os.path.join(G, 'ids.json'), 'w', encoding='utf-8'), ensure_ascii=False, indent=1, sort_keys=True)
		imgs = dict(chests=[dict(id=c['id'], wiki_file=c['image_src'], model=c['model']) for c in self.chests],
			items=sorted({v for l in lines if l['vnum'] for v in [l['vnum']] if not os.path.exists(os.path.join(IMG_ITEM, '%d.png' % v))}
				| {v for c in self.chests for x in c['drops'] for it in x['items'] for v in it['alts'] if not os.path.exists(os.path.join(IMG_ITEM, '%d.png' % v))}))
		imgs['item_names'] = {str(v): self.d.name(v) for v in imgs['items']}
		json.dump(imgs, open(os.path.join(G, 'images.json'), 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
		print('fixed prices %d (not possible %d), ' % (len(self.fixed), len(self.untimed)), end='')
		print('lines %d (chests %d), diffs %d, missing %d, replaced %d, item pictures missing %d' % (len(lines), len(self.chests), len(self.diff), len(self.missing), len(self.replaced), len(imgs['items'])))

	# ---------------------------------------------------------------- the sheet
	def xlsx(self, path):
		from openpyxl import Workbook
		from openpyxl.styles import Alignment, Font, PatternFill
		from openpyxl.utils import get_column_letter
		wb = Workbook()
		hdr_fill = PatternFill('solid', fgColor='7A1F1F')
		hdr_font = Font(bold=True, color='FFFFFF')
		dec_fill = PatternFill('solid', fgColor='FFF2CC')

		def sheet(title, headers, rows, widths, decision_col=None, links=()):
			ws = wb.create_sheet(title)
			ws.append(headers)
			for c in range(1, len(headers) + 1):
				cell = ws.cell(row=1, column=c)
				cell.fill, cell.font = hdr_fill, hdr_font
				cell.alignment = Alignment(wrap_text=True, vertical='center')
			for r in rows:
				ws.append([x[0] if isinstance(x, tuple) else x for x in r])
				rr = ws.max_row
				for c, x in enumerate(r, 1):
					if isinstance(x, tuple) and x[1]:
						ws.cell(row=rr, column=c).hyperlink = x[1]
						ws.cell(row=rr, column=c).font = Font(color='0563C1', underline='single')
					ws.cell(row=rr, column=c).alignment = Alignment(wrap_text=True, vertical='top')
				if decision_col:
					ws.cell(row=rr, column=decision_col).fill = dec_fill
			for i, w in enumerate(widths, 1):
				ws.column_dimensions[get_column_letter(i)].width = w
			ws.freeze_panes = 'A2'
			ws.auto_filter.ref = ws.dimensions
			return ws

		def wl(title):
			return ('wiki: ' + title, wiki_url(title)) if title else ''

		wb.remove(wb.active)
		sheet('Różnice u nas', ['Nr linii (u nas)', 'Vnum', 'Nasz przedmiot', 'Kategoria', 'Sztuk', 'Nasza cena', 'Czas u nas',
			'Odpowiednik na liście globalnej', 'Cena na liście globalnej', 'Cena wg zasady właściciela', 'Uwagi', 'Decyzja / Cena SM'],
			[[d['id'], d['vnum'], d['name'], d['cat'], d['count'], d['price'], d['days'], (d['wiki'], wiki_url(d['link']) if d['link'] else ''),
				d['gprice'], d['rule'], d['note'], ''] for d in self.diff],
			[10, 9, 30, 18, 7, 11, 12, 30, 30, 22, 50, 18], decision_col=12)
		sheet('Brak w plikach', ['Przedmiot (lista globalna)', 'Dział listy', 'Co robi', 'Cena na liście globalnej', 'Dlaczego nie dodany', 'Strona wiki', 'Decyzja (dodać? cena SM)'],
			[[m['wiki'], m['sub'], m['info'], m['price'], m['note'], wl(m['link']), ''] for m in self.missing],
			[30, 22, 60, 26, 50, 30, 20], decision_col=7)
		sheet('Zastąpione', ['Przedmiot (lista globalna / skrzynia)', 'Cena na liście globalnej', 'Nasz odpowiednik (vnum)', 'Nasz odpowiednik (nazwa)', 'Co zrobione', 'Skrzynia', 'Uwagi', 'Strona wiki'],
			[[r['wiki'], r['price'], r['ours'][0], r['ours'][1], r['how'], '', r['note'], wl(r['link'])] for r in self.replaced]
			+ [[s['wiki'], '', s['vnum'], self.d.name(s['vnum']), 'w skrzyni zamiast brakującego przedmiotu, z jego szansą (%g%% z zapisanej skrzyni, przed przeliczeniem)' % s['pct'],
				'%d skrzyń: %s' % (len(s['chests']), ', '.join(s['chests'])), s['why'], wl(s['wiki'])] for s in self.chest_subs.values()],
			[30, 22, 12, 28, 34, 50, 40, 30])
		rows = []
		for idx, d in owner_decisions.LINES.items():
			if idx not in self.d.lines:
				continue
			l = self.d.lines[idx]
			ch = []
			if 'price' in d:
				ch.append('cena %d -> %d %s' % (l['price'], d['price'], 'SM' if l['cur'] == 1 else 'SZ'))
			if 'count' in d:
				ch.append('sztuk %d -> %d' % (l['count'], d['count']))
			if 'cat' in d:
				ch.append('kategoria -> %s' % CAT_NAMES.get(d['cat'], d['cat']))
			if 'name' in d:
				ch.append('nazwa -> %s' % d['name'])
			if d.get('hide'):
				ch.append('usunięte ze sklepu V3')
			rows.append([idx, l['vnum'], l['name'] or self.d.name(l['vnum']), CAT_NAMES.get(l['cat'], l['cat']), '%d %s' % (l['price'], 'SM' if l['cur'] == 1 else 'SZ'),
				d.get('why', ''), '; '.join(ch) or 'bez zmian'])
		for r in self.r5_done:
			rows.append(['—', '', r['wiki'], r['sub'], r['price'], 'Brak w plikach: dodaj', r['done']])
		sheet('Decyzje (runda 5)', ['Nr linii (u nas)', 'Vnum', 'Przedmiot', 'Kategoria', 'Cena była', 'Decyzja właściciela', 'Co zrobione w sklepie V3'],
			rows, [10, 9, 30, 22, 11, 40, 50])
		sheet('Tylko w skrzyniach', ['Nr linii (u nas)', 'Vnum', 'Przedmiot', 'Kategoria', 'Cena (była)', 'Czas', 'Skrzynie, które go dają'],
			[[idx, l['vnum'], l['name'] or self.d.name(l['vnum']), CAT_NAMES.get(l['cat'], l['cat']), '%d SM' % l['price'], self.d.days_label(l['vnum']),
				', '.join(self.chests_of(l['vnum']))] for idx, l in self.only_lines.items()],
			[10, 9, 30, 22, 11, 16, 60])
		sheet('Zmienione ceny (stałe)', ['Nr linii (u nas)', 'Vnum', 'Przedmiot', 'Kategoria', 'Stara cena', 'Stary czas', 'Nowa cena', 'Nowy czas', 'Uwagi'],
			[[f['idx'], f['vnum'] if f['vnum'] == f['old_vnum'] else '%d (było %d)' % (f['vnum'], f['old_vnum']), f['name'], f['cat'], '%d SM' % f['old_price'], f['old_days'],
				'%d SM' % f['price'], '30 dni', f['why'] or 'tylko w sklepie V3 (Shift+F12); sklep w grze bez zmian'] for f in self.fixed.values()],
			[10, 16, 30, 22, 11, 22, 11, 10, 50])
		rows = []
		for l in self.lines.values():
			if l['chest']:
				rows.append([l['id'], '-', l['name'], CAT_NAMES[l['cat']], l['count'], '%d SM' % l['price'], 'skrzynia (losowanie przy zakupie)', l['source'],
					'Skrzynia zestawu - zawartość i szanse w arkuszu „Skrzynie setów”.' if l['cat'] == CAT_SETS else
					'Skrzynia - zawartość i szanse w oknie przedmiotu (zakładka „Szanse”); %d losowań za tę cenę.' % l['count']])
				continue
			nm = self.d.name(l['vnum']) + (' ' + l['suffix'] if l['suffix'] else '')
			t = days_text(l['minutes'] / 1440.0) + ' (czas linii)' if l['minutes'] else days_text(self.d.days(l['vnum']))
			rows.append([l['id'], l['vnum'], nm, CAT_NAMES.get(l['cat'], l['cat']), l['count'], '%d %s' % (l['price'], 'SM' if l['cur'] == 1 else 'SZ'), t, l['source'], l['note']])
		sheet('Dodane', ['Nr linii (V3)', 'Vnum', 'Przedmiot', 'Kategoria', 'Sztuk', 'Cena', 'Czas', 'Źródło (lista globalna / zestaw)', 'Uwagi'],
			rows, [11, 9, 34, 22, 7, 10, 22, 50, 60])
		rows = []
		for sr in self.set_rows:
			s, c, b = sr['set'], sr['chest'], sr['bonus']
			if not c:
				rows.append([s['id'], s['name'], '—', '', '', '', '', sr['why'], 'tak' if b['ok'] else 'NIE', b['check']])
				continue
			src = ('wiki: ' + c['wiki'], wiki_url(c['wiki'])) if c['wiki'] else 'model: wiki „%s” + zapisana skrzynia sklepu globalnego' % MODEL_CHEST
			first = True
			for x in c['drops']:
				items = ' / '.join('%s (%s)' % ('; '.join('%s %d' % (self.d.name(v), v) for v in it['alts']), days_text(it['minutes'] / 1440.0) if it['minutes'] else 'czas przedmiotu') for it in x['items'])
				rows.append([s['id'] if first else '', s['name'] if first else '', c['name'] if first else '', ('%d SM' % c['price']) if first else '', src if first else '',
					x['label'], '%.2f %%' % (x['ppm'] / 10000.0), items + ('' if x['kind'] != 'common' else ' — szansa: ' + x.get('weight_src', '')),
					('tak' if b['ok'] else 'NIE') if first else '', b['check'] if first else ''])
				first = False
			if c['gone']:
				rows.append(['', '', '', '', '', 'Bez zamiennika (szansa rozdzielona na resztę)', '', ', '.join(c['gone']), '', ''])
		sheet('Skrzynie setów', ['Id zestawu', 'Zestaw', 'Skrzynia', 'Cena', 'Źródło zawartości', 'Wygrana', 'Szansa', 'Przedmioty (vnum, czas)', 'Bonus działa u nas', 'Sprawdzenie'],
			rows, [9, 26, 32, 8, 36, 40, 9, 80, 12, 50])
		info = wb.create_sheet('Założenia', 0)
		for line in [
			'Porównanie sklepu ItemShop V3 z listą sklepu serwerów globalnych (pl-wiki „Item-Shop”, odczyt 24.10.2026) - runda 3.',
			'Waluta: ich moneta premium = 1 SM, ich znaki = 1 SZ (lista podaje ceny w SM i SZ, więc 1:1).',
			'Zasady właściciela (zastępują ceny z listy): pety bez łupu 299 SM, pety z łupem 699 SM, wierzchowce 299 SM, nakładki / szarfy 299 SM, kostiumy i fryzury 299 SM - zawsze 30 dni. Dotyczą wszystkich linii sklepu V3, także dotychczasowych (arkusz „Zmienione ceny (stałe)”); sklep w grze bez zmian. Części zestawów, które daje którakolwiek skrzynia (z wariantami płci, klasy i czasu), są tylko w skrzyniach - zdjęte ze wszystkich list V3 (arkusz „Tylko w skrzyniach”). Linie bez czasu, których nie da się zrobić 30-dniowymi, są w „Różnice u nas” z uwagą „do decyzji”.',
			'Czas: sklep w grze nie ustawia czasu na linii (serwer bierze go z item_proto). W sklepie V3 linia może mieć własny czas (kolumna minutes) - dla przedmiotów z limitem czasu rzeczywistego (kostiumy, fryzury, nakładki, pety, wierzchowce) serwer bierze go z gniazda (socket0) z item_award. Przedmiotów unikatowych (pierścienie, Powiększony Skład) tak zmienić się nie da.',
			'VIP (Rękawica, Trzecia Ręka, Pierścień Doświadczenia, Szczęśliwa Moneta, Rybie Wnętrzności) - jak w sklepie w grze: czas premium na koncie; dodane warianty 30/15/7 dni.',
			'Nic z naszego sklepu nie zostało zmienione ani usunięte - różnice są w arkuszu „Różnice u nas” (kolumna „Decyzja / Cena SM” do uzupełnienia).',
			'Nowe linie są tylko w sklepie V3 (Shift+F12) - sklep w grze (okno „Sklep z przedmiotami”) ich nie pokazuje.',
			'Pominięte: „Oferty specjalne” (lizaki, pierścienie, kupony z rabatem - u nas „oferty błyskawiczne”), pakiet yang, transfer serwerów, Sklep Tygrysi, przedmioty Likana.',
			'Szanse skrzyń: zapisana strona sklepu globalnego (skrzynia „Renkli palyaço sandığı”, zakładka „Olasılıklar”): pakiet zestawu 1%, fryzura 15 dni 2,5%, kostium 15 dni 2,5%, fryzura 30 dni 1,5%, kostium 30 dni 1,5%, pozostałe 18 przedmiotów razem 91% (Ekspresowe Leczenie Najemnika 10%, Zwój Błogosławieństwa / Księga Obróbki Kamienia / Różowa Smocza Fasola po 7%, ...). Strony wiki skrzyń nie podają szans - użyte szanse z zapisanej strony.',
			'Przedmioty skrzyni, których nie mamy: łatwe zamienniki z ich szansą (Lśniąca Skrzynia z Odłamkiem -> Zdobna Skrzynia z Odłamkiem, Książka Lidera+ -> Książka Lidera, Wino XL -> Wino z Kwiatu Brzoskwini; arkusz „Zastąpione”). Bez sensownego odpowiednika (fasole smoczych kamieni - u nas brak pomocy do ulepszania, kupony wpłaty - brak wpłat do gildii, najemnicy - brak systemu, Spirala Czasu, Wstęp do Świątyni Smoka - nasza Świątynia nie wymaga biletu) - szansa rozdzielona proporcjonalnie na resztę „pozostałych”; szanse kostiumów / pakietu bez zmian.',
		]:
			info.append([line])
			info.cell(row=info.max_row, column=1).alignment = Alignment(wrap_text=True, vertical='top')
		info.column_dimensions['A'].width = 140
		wb.save(path)
		print('wrote', path)


def main():
	ap = argparse.ArgumentParser()
	ap.add_argument('--db', default='mt2009plustest-db')
	ap.add_argument('--client-list', required=True)
	ap.add_argument('--xlsx')
	a = ap.parse_args()
	b = Build(Data(a.db, a.client_list))
	b.sets()
	b.round5()
	b.chest_only()
	b.fixed_prices()
	b.catalogue()
	b.not_listed()
	b.out()
	if a.xlsx:
		b.xlsx(a.xlsx)


if __name__ == '__main__':
	main()
