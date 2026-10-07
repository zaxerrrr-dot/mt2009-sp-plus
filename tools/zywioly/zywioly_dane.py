# -*- coding: utf-8 -*-
"""MT2009_PLUS_ELEMENTS_V1 - the talismans' numbers, shared by the server SQL generator
(gen_zywioly_talizmany.py -> linux-port/docker/mariadb/playerbot/zywioly_talizmany.sql) and the
client data tool (client-patches/client-2.0.30/tools/zywioly/patch_zywioly_client.py).
Autor: Digi Rasta (Zywioly i talizmany, nowy-system 0.28.0, his talizmany_dane.py), as he set them:

  Talisman: armour subtype 7 (ARMOR_PENDANT), the WEAR_PENDANT slot, every class; +0..+200, each
  level +1% power of its element (server points 178-183); the player's level for a band of levels:
  +0..+39 20, +40..+79 40, +80..+119 60, +120..+159 80, +160..+200 100. Refined at the Blacksmith:
  10x Kwiat Zywiolu, 1x Ornament (30031), 1x Talisman +0 of the element and the band's fee, 100%
  (about 2 000 000 000 Yang to +200 with the flowers). Kwiat Zywiolu: Mistrz's (20082) shop, 100 000.
Python 2 and 3 (the client tool runs in the m2pack-lzo image).
"""

KWIAT = 95500
ORNAMENT = 30031
MAKS = 200
REFINE_ID = 20001          # refine_proto id = REFINE_ID + 200 * element + level (0..199)
SKLEP = 9550               # shop of Mistrz (20082)
MISTRZ = 20082

# (+0 vnum, name, name without Polish letters, power point, element in the text, power name)
TALIZMANY = (
    (94000, u"Talizman Ognia", "Talizman Ognia", 179, u"ognia", u"Siła Ognia"),
    (94250, u"Talizman Błyskawicy", "Talizman Blyskawicy", 178, u"błyskawicy", u"Siła Błyskawicy"),
    (94500, u"Talizman Lodu", "Talizman Lodu", 180, u"lodu", u"Siła Lodu"),
    (94750, u"Talizman Wiatru", "Talizman Wiatru", 181, u"wiatru", u"Siła Wiatru"),
    (95000, u"Talizman Ziemi", "Talizman Ziemi", 182, u"ziemi", u"Siła Ziemi"),
    (95250, u"Talizman Mroku", "Talizman Mroku", 183, u"mroku", u"Siła Mroku"),
)

# (last level of a band, the player's level for a talisman in it)
POZIOM_GRACZA = ((39, 20), (79, 40), (119, 60), (159, 80), (200, 100))
# The Blacksmith's fee for the step from level n: (last n of the band, Yang)
OPLATA = ((38, 280000), (78, 3375000), (118, 7125000), (158, 12750000), (199, 20950000))

KWIAT_CENA = 100000        # item_proto.gold (the shop's price)
KWIAT_SKUP = 100000        # shop_buy_price
TALIZMAN_CENA = 10000
STACK = 200                # ITEM_MAX_COUNT of our engine (his 1000 does not stack past 200)

IKONA = "icon/item/{0}.tga"  # root pack: client-patches/client-2.0.30/root/icon/item/<+0 vnum>.tga

ITEM_ARMOR, ARMOR_PENDANT, ITEM_MATERIAL = 2, 7, 5
WEARABLE_PENDANT = 1 << 12
ITEM_FLAG_STACKABLE = 4
LIMIT_LEVEL = 1

KWIAT_NAZWA = u"Kwiat Żywiołu"
KWIAT_OPIS = u"Klejnot w kształcie kwiatu do ulepszenia talizmanów żywiołowych."


def poziom_gracza(n):
    return next(lv for maks, lv in POZIOM_GRACZA if n <= maks)


def oplata(n):
    return next(y for maks, y in OPLATA if n <= maks)


def talizmany():
    """[(vnum, element no, level, name, ascii name, point, description, icon)] for +0..+200 of all six"""
    wynik = []
    for nr, (pierwszy, nazwa, ascii_, punkt, zyw, sila) in enumerate(TALIZMANY):
        for n in range(MAKS + 1):
            opis = (u"Przepełniony pradawną mocą %s, talizman ten roznieci w tobie nadzwyczajną moc! "
                    u"%s +%d%%." % (zyw, sila, n))
            wynik.append((pierwszy + n, nr, n, u"%s+%d" % (nazwa, n), "%s+%d" % (ascii_, n), punkt, opis,
                          IKONA.format(pierwszy)))
    return wynik


def refine_set(nr, n):
    return REFINE_ID + 200 * nr + n if n < MAKS else 0


def vnumy():
    return set(t[0] for t in talizmany()) | set([KWIAT])
