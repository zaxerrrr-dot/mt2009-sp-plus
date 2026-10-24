#!/usr/bin/env python3
"""MT2009_PLUS_ITEMSHOP_V3_V6: the drop chances of a costume chest of the big servers' shop, read once from the page
the owner saved (24.10.2026, the Turkish shop, the chest "Renkli palyaço sandığı" with its "Olasılıklar" tab):

  extract_tr_chances.py [<saved page .html>]   (default: the one .html in /opt/metin2/cache/yohara/ishop-global)

writes tr_chances.json next to this file: the price, every row of the probability table (also the hidden tab's,
the page keeps it in the HTML, not in a script), and each row's Polish item - the chest's list in the
"Bilgi" tab is the same as the pl-wiki's chest pages ("Majestatyczna Skrzynia Nosiciela Światła": the 18 other
items and the set's costume, hair and package), so every Turkish name has its Polish one below.
"""
import html
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
PAGE_DIR = '/opt/metin2/cache/yohara/ishop-global'

# Turkish row -> (Polish name of the pl-wiki chest pages, kind). kind: common = one of the chest's other items,
# hair15 / body15 / hair30 / body30 = the set's hair or costume for 15 / 30 days, package = the set's package.
TR_PL = {
	'Yeşil Ejderha Fasulyesi': ('Zielona Smocza Fasola', 'common'),
	'Parlak parça sandnığı': ('Lśniąca Sk. z Odłamkiem', 'common'),
	'Güneş Özütü (Ö)': ('Eliksir Słońca (S)', 'common'),
	'Ay Özütü (Ö)': ('Eliksir Księżyca (S)', 'common'),
	'Ejderha tapınağı girişi': ('Wstęp do Świątyni Smoka', 'common'),
	'Anında paralı asker şif.': ('Ekspres. Leczenie Najem.', 'common'),
	'Paralı asker lisansı': ('Licencja Najemnika', 'common'),
	'Hızlandırıcı (%30)': ('Spirala Czasu (30%)', 'common'),
	'Süslü parça sandığı': ('Zdobna Skrz. z Odłamkiem', 'common'),
	'Büyük bağış belgesi': ('Wysoki Kupon Wpłaty', 'common'),
	'Ejderha alevi': ('Smoczy Płomień', 'common'),
	'Zihin Taşı Destesi': ('Pakiet Kamieni Duszy', 'common'),
	'Kutsama Kağıdı': ('Zwój Błogosławieństwa', 'common'),
	'Taş Sanatı Kitabı': ('Księga Obróbki Kamienia', 'common'),
	'Pembe Ejderha Fasulyesi': ('Różowa Smocza Fasola', 'common'),
	'Büyülü Metal': ('Magiczny Kamień', 'common'),	# the pl-wiki chests list "Magiczny Kamień" in its place
	'Orta bağış belgesi': ('Średni Kupon Wpłaty', 'common'),
	'Liderin Kitabı (3 s)': ('Księga Lidera', 'common'),
	'Renkli palyaço şpk.+ (e) (15 g)': ('fryzura zestawu, 15 dni', 'hair15'),
	'Renkli palyaço+ (e) (15 g)': ('kostium zestawu, 15 dni', 'body15'),
	'Renkli palyaço şpk.+ (e) (30 g)': ('fryzura zestawu, 30 dni', 'hair30'),
	'Renkli palyaço+ (e) (30 g)': ('kostium zestawu, 30 dni', 'body30'),
	'Renkli palyaço paketi': ('pakiet zestawu', 'package'),
}


def main():
	if len(sys.argv) > 1:
		page = sys.argv[1]
	else:
		page = [os.path.join(PAGE_DIR, f) for f in sorted(os.listdir(PAGE_DIR)) if f.endswith('.html')][0]
	t = open(page, encoding='utf-8').read()
	i = t.index('id="probability"')
	table = t[i:t.index('</table>', i)]
	rows = []
	for m in re.finditer(r'<tr>\s*<td>(.*?)</td>\s*<td>\s*%([0-9.,]+)\s*</td>\s*</tr>', table, re.S):
		name = html.unescape(re.sub(r'<[^>]+>', ' ', m.group(1)))
		name = re.sub(r'\s+', ' ', name).replace(' !', '').strip()
		name = re.sub(r'^1x\s+', '', name).strip()
		pct = float(m.group(2).replace(',', '.'))
		pl, kind = TR_PL[name]
		rows.append({'tr': name, 'pl': pl, 'kind': kind, 'pct': pct})
	price = re.search(r'Fiyat:.*?alt="Ejderha Parası">\s*(?:</?\w[^>]*>\s*)*(\d+)', t, re.S)
	out = {
		'source': 'the saved shop page (ishop-global, 24.10.2026), tab "Olasılıklar"',
		'chest': 'Renkli palyaço sandığı',
		'price_dragon_coins': int(price.group(1)) if price else None,
		'sum_pct': round(sum(r['pct'] for r in rows), 3),
		'rows': rows,
	}
	assert abs(out['sum_pct'] - 100) < 0.01, out['sum_pct']
	json.dump(out, open(os.path.join(HERE, 'tr_chances.json'), 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
	print('%d rows, %.1f %%, price %s' % (len(rows), out['sum_pct'], out['price_dragon_coins']))


if __name__ == '__main__':
	main()
