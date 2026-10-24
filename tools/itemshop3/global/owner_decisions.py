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
