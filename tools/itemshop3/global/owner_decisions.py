# -*- coding: utf-8 -*-
"""MT2009_PLUS_ITEMSHOP_V3_V8: the owner's decisions on the round-3 sheet (/opt/metin2/cache/yohara/itemshop-global-decyzje.xlsx,
24.10.2026 - "Różnice u nas", "Brak w plikach" and "Dodane"), applied to the second shop only (the in-game window keeps
common.itemshop_items as it is). gen_global_catalog.py turns them into itemshop3.line_overrides rows (price, count,
category, name, hidden) for the in-game catalogue's lines and drops the V3 lines named in V3_REMOVE.

LINES: in-game line index -> dict(price=, count=, cat=, name=, hide=True, why=) - only what changes.
"""

# "moja cena" (107 classic hairstyles without a timer): the owner's 299 SM, permanent as they are; a vnum sold on two lines
# (39 SM in "Fryzury +" and 100 SM) keeps one line - the first.
HAIR_KEEP = [301, 302, 303, 304, 309, 310, 311, 312, 314, 315, 325, 326, 327, 328, 329, 330, 331, 332, 333, 334, 335, 336, 337, 339, 340, 341, 342, 349, 350, 351, 352, 353, 354, 355, 356, 357, 358, 359, 360, 361, 362, 363, 364, 366, 367, 368, 373, 374, 375, 376, 378, 379, 380, 381, 382, 383, 384, 390, 391, 392, 393, 394, 395, 396]
HAIR_DROP = [10230, 10231, 10232, 10233, 10238, 10239, 10240, 10241, 10242, 10243, 10244, 10245, 10246, 10247, 10248, 10249, 10250, 10251, 10252, 10253, 10254, 10255, 10256, 10257, 10258, 10259, 10260, 10261, 10262, 10263, 10264, 10265, 10266, 10267, 10268, 10269, 10271, 10272, 10273, 10274, 10275, 10276, 10277]

LINES = {
	1: dict(price=59, why='59 SM (lista globalna)'),
	3: dict(why='zostaw naszą cenę i nasze pakiety'),
	16: dict(why='zostaw 1000 SM'),
	605: dict(why='zostaw naszą cenę'),
	# "Zmień nazwę" - the global list's name (the shop line here; the item's name in the game: item_proto + client)
	40928: dict(name='Klatka Transportowa', why='nazwa z listy globalnej'),
	617: dict(name='Karta Resetu', why='nazwa z listy globalnej'),
	618: dict(name='Karta Przetasowania', why='nazwa z listy globalnej'),
	40924: dict(name='Pergamin Nazwy Zwierzaka', why='nazwa z listy globalnej'),
	608: dict(name='Zaczarowanie Przedmiotu 3+1 Pakiet Oszczędny', why='nazwa z listy globalnej (cena bez zmian)'),
	40925: dict(price=79, name='Reverti Zwierza', why='cena i nazwa z listy globalnej'),
	40926: dict(price=59, name='Revertus Zwierza', why='cena i nazwa z listy globalnej'),
	# "cena z globala"
	901: dict(price=80, why='cena z listy globalnej'),
	607: dict(price=59, why='cena z listy globalnej'),
	604: dict(price=20, why='cena z listy globalnej'),
	206: dict(price=21, why='cena z listy globalnej'),
	207: dict(price=21, why='cena z listy globalnej'),
	208: dict(price=21, why='cena z listy globalnej'),
	209: dict(price=21, why='cena z listy globalnej'),
	210: dict(price=21, why='cena z listy globalnej'),
	211: dict(price=21, why='cena z listy globalnej'),
	611: dict(price=111, why='cena z listy globalnej'),
	606: dict(price=19, why='cena z listy globalnej'),
	626: dict(price=99, why='cena z listy globalnej'),
	609: dict(price=9, why='cena z listy globalnej'),
	610: dict(price=59, why='cena z listy globalnej (25 szt.)'),
	710: dict(price=350, why='cena z listy globalnej'),
	701: dict(price=350, why='cena z listy globalnej'),
	702: dict(price=300, why='cena z listy globalnej'),
	703: dict(price=125, count=1, why='cena z listy globalnej (1 szt. zamiast paczki 10)'),
	704: dict(price=125, count=1, why='cena z listy globalnej (1 szt. zamiast paczki 10)'),
	705: dict(price=95, count=1, why='cena z listy globalnej (1 szt. zamiast paczki 5)'),
	706: dict(price=95, count=1, why='cena z listy globalnej (1 szt. zamiast paczki 5)'),
	708: dict(price=95, count=1, why='cena z listy globalnej (1 szt. zamiast paczki 5)'),
	709: dict(price=420, why='cena z listy globalnej'),
	# "dodaj do sklepu, w cenie z globala" - lines the in-game window hides (index 906 / 950)
	906: dict(price=79, count=6, cat=2, why='dodane do Wyposażenia, cena z listy globalnej (6 szt.)'),
	950: dict(price=49, cat=11, why='dodane do Zwojów i ksiąg, cena z listy globalnej'),
	# removals
	112: dict(hide=True, why='usuń w ogóle'),
	205: dict(hide=True, why='usuń ze sklepu'),
	201: dict(hide=True, why='usuń'), 202: dict(hide=True, why='usuń'), 203: dict(hide=True, why='usuń'), 204: dict(hide=True, why='usuń'),
	13: dict(hide=True, why='usuń z ItemShopu (boty kupują Medale Konne na rynku graczy/botów, nie w ItemShopie)'),
}
for _i in range(40901, 40910):
	LINES[_i] = dict(hide=True, why='usuń jaja petów')
for _i in HAIR_KEEP:
	LINES[_i] = dict(price=299, why='moja cena: 299 SM (fryzura bez czasu - zostaje stała)')
for _i in HAIR_DROP:
	LINES[_i] = dict(hide=True, why='moja cena: ta sama fryzura w drugiej linii (299 SM) - jedna linia')

# "Dodane" rows marked "usuń": the V3 line keys (vnum:count:currency:minutes)
V3_REMOVE = {'39064:2:1:0', '39064:4:1:0', '39064:9:1:0', '30319:5:1:0', '30319:25:1:0'}

# --- round 5, part 2: new things ("Brak w plikach" decisions) -----------------------------------------------------
D1, D7, D15, D30 = 1440, 10080, 21600, 43200
# "Zrób bilety jak na globalu": the 8-hour ticket gives way to the 7 / 14-day ones (72800 / 72801, apply.sh)
LINES[6] = dict(hide=True, why='zrób bilety jak na globalu: zamiast biletu 8 h - bilety 7 dni (49 SM) i 14 dni (95 SM)')
# V3 lines of the new items: (vnum, count, price, currency, category, minutes, suffix, source)
NEW_LINES = [
	(72800, 1, 49, 1, 2, 0, '', 'Auto Łowy 7 dni (decyzja: bilety jak na globalu)'),
	(72801, 1, 95, 1, 2, 0, '', 'Auto Łowy 14 dni (decyzja: bilety jak na globalu)'),
	(72802, 1, 39, 1, 2, D7, '(7 dni)', 'Szkło Handlu (decyzja: Dom Aukcyjny zdalnie)'),
	(72802, 1, 75, 1, 2, D15, '(15 dni)', 'Szkło Handlu (decyzja: Dom Aukcyjny zdalnie)'),
	(72802, 1, 135, 1, 2, D30, '(30 dni)', 'Szkło Handlu (decyzja: Dom Aukcyjny zdalnie)'),
	(72803, 1, 39, 1, 4, D1, '(1 dzień)', 'Buff Premium SungMa (decyzja: dodaj taki buff)'),
	(72803, 1, 299, 1, 4, D7, '(7 dni)', 'Buff Premium SungMa (decyzja: dodaj taki buff)'),
	(72803, 1, 599, 1, 4, D15, '(15 dni)', 'Buff Premium SungMa (decyzja: dodaj taki buff)'),
	(72803, 1, 999, 1, 4, D30, '(30 dni)', 'Buff Premium SungMa (decyzja: dodaj taki buff)'),
	(72804, 1, 300, 2, 12, 0, '', 'Eliksir W. SungMa (decyzja: dodaj eliksiry)'),
	(72805, 1, 300, 2, 12, 0, '', 'Eliksir W. SungMa (decyzja: dodaj eliksiry)'),
	(72806, 1, 300, 2, 12, 0, '', 'Eliksir W. SungMa (decyzja: dodaj eliksiry)'),
	(72807, 1, 300, 2, 12, 0, '', 'Eliksir W. SungMa (decyzja: dodaj eliksiry)'),
	(100300, 1, 19, 1, 3, 0, '', 'Zielona Smocza Fasola (decyzja: mamy smocze fasole)'),
	(55009, 1, 129, 1, 8, 0, '', 'Skrzynia Ksiąg Zwierza = nasza Skrzynia Ksiąg Peta (decyzja: dodaj)'),
	(55001, 1, 19, 1, 8, 0, '', 'Odżywka = nasza Proteinowa Przekąska (życie peta; decyzja: dodaj)'),
	(55001, 1, 30, 2, 12, 0, '', 'Odżywka = nasza Proteinowa Przekąska (decyzja: dodaj, za SZ)'),
]
# "Dodaj jako szkatułkę tak jak kostiumy, że można losować dowolny amulet na 7 dni": a chest rolled at the purchase,
# each piece of jewellery of the unique slots equally, 7 days; the list's three offers (1, 10+1, 20+3).
JEWEL_BOX = dict(name='Szkatuła na Biżuterię', wiki_file='Szkatuła na Biżuterię.png', category=2, minutes=D7,
	vnums=[71136, 71188, 71202, 71199, 71143, 71145, 71148, 71149, 71158, 70607, 72713],
	offers=[(1, 379, ''), (11, 990, '(10+1 gratis)'), (23, 1980, '(20+3 gratis)')])
# the "Brak w plikach" rows these decisions answer (wiki row -> what was done)
BRAK_DONE = {
	3: 'dodane: skrzynia „Szkatuła na Biżuterię” (losowanie przy zakupie, dowolna biżuteria na 7 dni)',
	26: 'dodane: nasza Skrzynia Ksiąg Peta (55009) za 129 SM', 363: 'dodane: nasza Skrzynia Ksiąg Peta (55009) za 129 SM',
	27: 'dodane: nasza Proteinowa Przekąska (55001) za 19 SM / 30 SZ', 232: 'dodane: nasza Proteinowa Przekąska (55001) za 30 SZ',
	358: 'dodane: nasza Proteinowa Przekąska (55001) za 19 SM',
	106: 'dodane: Buff Premium SungMa (72803) 1/7/15/30 dni za 39/299/599/999 SM',
	115: 'dodane: Szkło Handlu (72802) 7/15/30 dni za 39/75/135 SM - Dom Aukcyjny z każdej mapy',
	150: 'dodane: Zielona Smocza Fasola (100300) za 19 SM',
	216: 'dodane: Eliksir W. SungMa (SIŁA) 72804 za 300 SZ', 217: 'dodane: Eliksir W. SungMa (INT) 72807 za 300 SZ',
	218: 'dodane: Eliksir W. SungMa (ODP) 72806 za 300 SZ', 219: 'dodane: Eliksir W. SungMa (WIT) 72805 za 300 SZ',
}
