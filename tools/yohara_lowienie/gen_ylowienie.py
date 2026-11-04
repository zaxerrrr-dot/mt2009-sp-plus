#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""gen_ylowienie.py [--gf DIR]

MT2009_PLUS_FISHING_GLOBAL_V1: fishing as on the global server, Yohara 3.x (the owner's decisions of 4 November 2026,
cache/yohara/decyzje-lowienie-mikstury.md "Lowienie" 1-13 and Wedka Weglowa; the research cache/yohara/lowienie-analiza.md).

The item side - everything the database and the client need; the catch itself is lowienie/fishing_drop.lua, the engine
server-patches/fishglobal, the quests quest/zloty_tunczyk.quest and quest/rybak_wedki.quest.

  * Rods 27400 ... 27590 are Wedka+1 ... Wedka+20 (decision 1; the players' rods only change their name). The global
    numbers (Owsap v6.2.6 db/item_proto.txt, the pl-wiki "Wedka"): value0 10 x level (the client's tooltip shows
    value0 / 10 as the rod's level, fishing_drop.lua reads the level from it), value1 the 1-in-x chance of a point a
    catch (5, 10, 20, 40, 60, 70 ... 210), value2 the points to the next level (10 ... 420, unchanged), value3 the
    upgrade chance (100 the first time, then 39 - decision 2), value4 the rod itself (a failed upgrade keeps it with 10%
    of its points less - fishing.cpp RealRefineRod, server-patches/fishglobal), value5 the bite chance + level / 2 %
    (decision 3: +20 = 10%). The chain runs to +20 (27490 -> 27500 ... 27580 -> 27590, 27590 the last), no refine set
    (the upgrade is free, at the Rybak's dialog, no refine window). Wedka+1 costs 5 000 at the Rybak (decision 11).
  * Wedka Weglowa 27591: a rod of level 22 (value0 220) with +12% bite chance, no points, no upgrade, LIMIT_REAL_TIME
    30 days (gone afterwards, also worn - the engine's real_time_expire_event, like Bronie dla Mlodych Bohaterow), no
    drop / trade / private shop / storage (sold to an NPC: yes, as the wiki says). Made at the Rybak (cube.lowienie.txt).
  * Its parts 27621 Wedzisko, 27622 Przelotka, 27623 Rekojesc, 27624 Wlokno Weglowe (materials, from the chest).
  * Fish of the wiki list missing here (decision 6 - only these): 27824 Wezoglow, 27825 Skaber, 27826 Krab Krolewski,
    27827 Rak Niebieski, alive / dead (+30) / grilled (+60). The grilled ones are ITEM_POTION (36) of the food group
    like Pieczony Zloty Karas 27883 (value0 the seconds, value1 4, applytype0 the point) - the potions' own rules
    (quest/m2_mikstury_limity.lua, the potion branch) treat them as the other fish.
  * The six grilled fish with the wrong effect fixed to the wiki (decision 8): 27869 600 HP, 27871 600 MP, 27872 230 MP,
    27875 230 HP (instant potions as Owsap), 27879 EXP +10% 10 minutes (decision 9: Slodka Ryba 10 min), 27882 1000 HP
    (27883's +50% is the bonus mode's, item_proto_global.sql - left alone).
  * Zloty Tunczyk 27797 (a quest item - its use is quest zloty_tunczyk: release / cut / bait, decision 12).
  * Skrzynia Nimfy Wodnej 27625 (decision 10: a NEW vnum - the global 83032 is our Zloty Pakiet Yutnori; 27625 is free
    here and in the GF 26.1.11 client). A treasure box of key value 3 - Klucz Nimfy Wodnej 50043 opens it
    (special_item_group.lowienie.txt).
  * The chest's items this world lacked: 55004 Ksiega Dzikiego Zwierza, 55005 Ksiega Dzielnego Zwierza (as 55003),
    76033 Wino Kwiatu Brzoskwini+ (800 HP at once, Owsap's row).
  * The Rybak's shop (decision 11): Wedka+1 5 000, Wysuszone Drzewo 20 000, Kula Rybaka (27610, the wiki's name) 2 000.

Writes (GENERATED - edit this file, run it again):
  linux-port/docker/mariadb/playerbot/yohara_lowienie.sql   world.item_proto (INSERT IGNORE + idempotent UPDATEs)
  tools/yohara_lowienie/yohara_lowienie.json                the client's records, item_list, itemdesc
  client-patches/client-2.0.30/root/icon/item/*.tga         the GF 26.1.11 icons of the new items

Example: python3 tools/yohara_lowienie/gen_ylowienie.py
"""
import argparse
import json
import os
import shutil
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(os.path.dirname(HERE))
sys.path.insert(0, os.path.join(REPO, 'tools', 'yohara_items'))
import gen_yitems as Y  # noqa: E402  (COLS, sqlrow, ascii_name, ST)

SQL_OUT = os.path.join(REPO, 'linux-port', 'docker', 'mariadb', 'playerbot', 'yohara_lowienie.sql')
JSON_OUT = os.path.join(HERE, 'yohara_lowienie.json')
ICON_OUT = os.path.join(REPO, 'client-patches', 'client-2.0.30', 'root', 'icon', 'item')

ROD0 = 27400
CARBON = 27591
CHEST = 27625
TUNA = 27797
ANTI_NO_TRADE = 128 | 8192 | 16384 | 65536 | 131072   # drop, give, pk drop, private shop, storage (Owsap's 27591)
ANTI_TUNA = 128 | 8192 | 16384 | 65536                # one a day per character: not passed to another
STACKABLE = 4
WEAR_WEAPON = 16
LIMIT_LEVEL, LIMIT_REAL_TIME = 1, 7
ITEM_USE, ITEM_MATERIAL, ITEM_FISH, ITEM_ROD, ITEM_QUEST, ITEM_TREASURE_BOX, ITEM_POTION = 3, 5, 12, 13, 18, 20, 36
USE_POTION, USE_POTION_NODELAY = 0, 11
FISH_ALIVE, FISH_DEAD = 0, 1
FOOD_GROUP = 4                                       # potion_system.lua GROUP_TYPE_FOOD (the grilled fish)
POINT_MALL_EXPBONUS, POINT_RESIST_ICE, POINT_RESIST_EARTH, POINT_RESIST_DARK = 116, 133, 134, 135
THIRTY_DAYS = 30 * 24 * 3600


def rod_level_values(level):
    """(value0 .. value5, refined_vnum) of Wedka+level (1-20), the global numbers."""
    v1 = (5, 10, 20, 40, 60)[level - 1] if level <= 5 else 70 + 10 * (level - 6)
    v2 = (10, 20, 40, 80, 120)[level - 1] if level <= 5 else 140 + 20 * (level - 6)
    v3 = 100 if level == 1 else 39
    vnum = ROD0 + 10 * (level - 1)
    refined = vnum + 10 if level < 20 else 0
    return (10 * level, v1, v2, v3, vnum, level // 2), refined


def base_row(vnum, pl, typ, sub, **over):
    r = dict(vnum=vnum, name=Y.ascii_name(pl), locale_name=pl, type=typ, subtype=sub, stack=200, weight=0, size=1,
             antiflag=0, flag=STACKABLE, wearflag=0, gold=0, shop_buy_price=0, refined_vnum=0, refine_set=0,
             magic_pct=0, specular=0, socket_pct=0, addon_type=0, limittype0=0, limitvalue0=0, limittype1=0,
             limitvalue1=0, applytype0=0, applyvalue0=0, applytype1=0, applyvalue1=0, applytype2=0, applyvalue2=0,
             value0=0, value1=0, value2=0, value3=0, value4=0, value5=0, status=Y.ST)
    r.update(over)
    assert len(r['locale_name'].encode('cp1250')) <= 32, pl
    return r


# the four new fish of the wiki list: (live vnum, name, dead name, grilled name, (point, value, seconds), live text,
# grilled text) - the texts of Owsap's Polish client (= the global ones)
NEW_FISH = (
    (27824, u'Wężogłów', u'Martwy Wężogłów', u'Pieczony Wężogłów', (POINT_RESIST_EARTH, 10, 600),
     u'Słodkowodna ryba drapieżna występująca w tropikach.', u'Zwiększa twoją odporność na ziemię o 10% na 10 minut.'),
    (27825, u'Skaber', u'Martwy Skaber', u'Pieczony Skaber', (POINT_RESIST_ICE, 10, 600),
     u'Ryba występująca tylko w wodach płynących.', u'Zwiększa twoją odporność na lód o 10% na 10 minut.'),
    (27826, u'Krab Królewski', u'Martwy Krab Królewski', u'Pieczony Krab Królewski', (POINT_RESIST_DARK, 10, 600),
     u'Ten gatunek kraba zwany jest ze względu na swój rozmiar krabem gigantem.',
     u'Zwiększa twoją odporność na ciemność o 10% na 10 minut.'),
    (27827, u'Rak Niebieski', u'Martwy Rak Niebieski', u'Pieczony Rak Niebieski', (POINT_MALL_EXPBONUS, 100, 1800),
     u'Ten gatunek skorupiaka prowadzi nocny tryb życia, a dnie spędza w swojej kryjówce.',
     u'Zwiększa otrzymywane doświadczenie o 100% na 30 minut.'),
)
DEAD_TEXT = u'Świetnie nadaje się do upieczenia nad ogniskiem.'

# the grilled fish whose effect was not the wiki's (decision 8). Pieczony Zloty Karas 27883 is left alone: its +50% EXP is
# the bonus mode's (item_proto_global.sql - global 50, mt2009 its own value), as before:
# vnum: (type, subtype, value0, value1, applytype0, applyvalue0, client text)
GRILLED_FIX = {
    27869: (ITEM_USE, USE_POTION, 600, 0, 0, 0, u'Przywraca 600 PŻ.'),
    27871: (ITEM_USE, USE_POTION, 0, 600, 0, 0, u'Przywraca 600 PE.'),
    27872: (ITEM_USE, USE_POTION_NODELAY, 0, 230, 0, 0, u'Natychmiast przywraca 230 PE.'),
    27875: (ITEM_USE, USE_POTION_NODELAY, 230, 0, 0, 0, u'Natychmiast przywraca 230 PŻ.'),
    27879: (ITEM_POTION, 0, 600, FOOD_GROUP, POINT_MALL_EXPBONUS, 10,
            u'Zwiększa otrzymywane doświadczenie o 10% na 10 minut.'),
    27882: (ITEM_USE, USE_POTION_NODELAY, 1000, 0, 0, 0, u'Natychmiast przywraca 1000 PŻ.'),
}
GRILLED_NAMES = {27869: u'Pieczony Pstrąg', 27871: u'Pieczony Tęczowy Pstrąg', 27872: u'Pieczony Rzeczny Pstrąg',
                 27875: u'Pieczony Tenchi', 27879: u'Pieczona Słodka Ryba', 27882: u'Pieczony Lustrzany Karp'}

# the Rybak's shop (decision 11): vnum: (name or None, price)
SHOP = {27400: (None, 5000), 27600: (None, 20000), 27610: (u'Kula Rybaka', 2000)}
KULA_TEXT = u'Ten magiczny marmur pokazuje informacje o złowionej rybie i zwiększa szansę na udany połów o 2%.'


def rods():
    out = []
    for level in range(1, 21):
        (v0, v1, v2, v3, v4, v5), refined = rod_level_values(level)
        vnum = ROD0 + 10 * (level - 1)
        out.append(dict(vnum=vnum, pl=u'Wędka+%d' % level, value=(v0, v1, v2, v3, v4, v5), refined=refined))
    return out


def new_items():
    items = []
    carbon = base_row(CARBON, u'Wędka Węglowa', ITEM_ROD, 0, stack=1, size=3, antiflag=ANTI_NO_TRADE, flag=0,
                      wearflag=WEAR_WEAPON, limittype0=LIMIT_LEVEL, limitvalue0=30, limittype1=LIMIT_REAL_TIME,
                      limitvalue1=THIRTY_DAYS, value0=220, value1=0, value2=440, value3=0, value4=0, value5=12)
    carbon.update(desc=u'Przy pomocy tej wysokiej jakości wędki z włókna węglowego złapiesz wyjątkowo grube ryby. '
                       u'Jest lepsza od zwykłej wędki (jak wędka +22). Działa 30 dni (czas płynie także poza grą), '
                       u'potem znika. Nie da się jej ulepszyć ani przekazać.',
                  icon='icon/item/27591.tga', model='d:/ymir work/item/etc/fishing_rod.gr2', icon_src=27591)
    items.append(carbon)
    for vnum, pl in ((27621, u'Wędzisko'), (27622, u'Przelotka'), (27623, u'Rękojeść'), (27624, u'Włókno Węglowe')):
        it = base_row(vnum, pl, ITEM_MATERIAL, 0, gold=300, shop_buy_price=300)
        it.update(desc=u'Materiał do budowy Wędki Węglowej (u Rybaka). Ze Skrzyni Nimfy Wodnej.',
                  icon='icon/item/%d.tga' % vnum, icon_src=vnum)
        items.append(it)
    for live, pl, dead_pl, grill_pl, (point, value, secs), live_text, grill_text in NEW_FISH:
        n = live - 27800
        a = base_row(live, pl, ITEM_FISH, FISH_ALIVE, stack=10, gold=20000, shop_buy_price=20000, value0=n)
        a.update(desc=live_text, icon='icon/item/%d.tga' % live, icon_src=live)
        d = base_row(live + 30, dead_pl, ITEM_FISH, FISH_DEAD, gold=10000, shop_buy_price=10000, value0=n)
        d.update(desc=DEAD_TEXT, icon='icon/item/%d.tga' % (live + 30), icon_src=live + 30)
        g = base_row(live + 60, grill_pl, ITEM_POTION, 0, gold=10000, shop_buy_price=10000, applytype0=point,
                     applyvalue0=value, value0=secs, value1=FOOD_GROUP)
        g.update(desc=grill_text, icon='icon/item/%d.tga' % (live + 60), icon_src=live + 60)
        items += [a, d, g]
    tuna = base_row(TUNA, u'Złoty Tuńczyk', ITEM_QUEST, 0, stack=1, antiflag=ANTI_TUNA, flag=0, gold=280,
                    shop_buy_price=280)
    tuna.update(desc=u'Bardzo rzadka zdobycz. Jego łuski błyszczą niczym płynne złoto! Kliknij prawym przyciskiem: '
                     u'wypuść go, pokrój albo użyj jako przynęty.', icon='icon/item/27797.tga', icon_src=27797)
    items.append(tuna)
    chest = base_row(CHEST, u'Skrzynia Nimfy Wodnej', ITEM_TREASURE_BOX, 0, value0=3)
    chest.update(desc=u'Skrzynia z Królestwa Duchów Wodnych. Otwórz ją za pomocą Klucza Nimfy Wodnej.',
                 icon='icon/item/27625.tga', icon_src=83032)
    items.append(chest)
    for vnum, pl, text in ((55004, u'Księga Dzikiego Zwierza', u'Księga do trenowania zwierzaka (dziki zwierzak).'),
                           (55005, u'Księga Dzielnego Zwierza', u'Księga do trenowania zwierzaka (dzielny zwierzak).')):
        it = base_row(vnum, pl, ITEM_MATERIAL, 0)
        it.update(desc=text, icon='icon/item/%d.tga' % vnum, icon_src=vnum)
        items.append(it)
    wine = base_row(76033, u'Wino Kwiatu Brzoskwini+', ITEM_USE, USE_POTION_NODELAY, antiflag=ANTI_NO_TRADE,
                    gold=1000, shop_buy_price=1000, value0=800)
    wine.update(desc=u'Mikstura, która natychmiastowo regeneruje o 800 punktów twoje PŻ.',
                icon='icon/item/71108.tga', icon_src=None)
    items.append(wine)
    return items


def q(s):
    return "_cp1250 X'%s'" % s.encode('cp1250').hex().upper()


def write_sql(items, rod_rows):
    L = ['-- MT2009_PLUS_FISHING_GLOBAL_V1: fishing as on the global server (the owner, 4 November 2026). GENERATED by',
         '-- tools/yohara_lowienie/gen_ylowienie.py - do not edit, rerun it. Every start (apply.sh), idempotent: the new',
         '-- items INSERT IGNORE (a row the operator changed is kept), the rods, the grilled fish and the Rybak\'s prices',
         '-- UPDATEd to the owner\'s values (decisions 1-3, 8, 11) on every world.',
         'SET NAMES utf8mb4;',
         '-- the new items: Wedka Weglowa, its parts, the four fish (alive / dead / grilled), Zloty Tunczyk,',
         '-- Skrzynia Nimfy Wodnej (27625), the chest\'s pet books and Wino Kwiatu Brzoskwini+',
         'INSERT IGNORE INTO world.item_proto (%s) VALUES' % ','.join('`%s`' % c for c in Y.COLS),
         ',\n'.join(Y.sqlrow(i) for i in items) + ';',
         '-- Wedka Weglowa: the numbers that make it a rod of level 22 that never gains a point nor upgrades',
         'UPDATE world.item_proto SET refined_vnum = 0, refine_set = 0, value0 = 220, value2 = 440, value5 = 12, '
         'limittype1 = %d, limitvalue1 = %d WHERE vnum = %d;' % (LIMIT_REAL_TIME, THIRTY_DAYS, CARBON),
         '-- the rods +1 ... +20 (decision 1: the players\' rods only change their name)']
    for r in rod_rows:
        v = r['value']
        L.append('UPDATE world.item_proto SET name = %s, locale_name = %s, refined_vnum = %d, refine_set = 0, '
                 'value0 = %d, value1 = %d, value2 = %d, value3 = %d, value4 = %d, value5 = %d WHERE vnum = %d;'
                 % (q(r['pl']), q(r['pl']), r['refined'], v[0], v[1], v[2], v[3], v[4], v[5], r['vnum']))
    L.append('-- the grilled fish of the wiki (decision 8; 27879 10 minutes - decision 9)')
    for vnum, (typ, sub, v0, v1, at, av, _t) in sorted(GRILLED_FIX.items()):
        L.append('UPDATE world.item_proto SET type = %d, subtype = %d, applytype0 = %d, applyvalue0 = %d, '
                 'applytype1 = 0, applyvalue1 = 0, applytype2 = 0, applyvalue2 = 0, value0 = %d, value1 = %d, '
                 'value2 = 0, value3 = 0, value4 = 0, value5 = 0 WHERE vnum = %d;' % (typ, sub, at, av, v0, v1, vnum))
    L.append('-- the Rybak\'s prices and the wiki\'s name of the marble (decision 11)')
    for vnum, (pl, price) in sorted(SHOP.items()):
        name = (', name = %s, locale_name = %s' % (q(pl), q(pl))) if pl else ''
        L.append('UPDATE world.item_proto SET gold = %d, shop_buy_price = %d%s WHERE vnum = %d;'
                 % (price, price, name, vnum))
    with open(SQL_OUT, 'w', encoding='utf-8', newline='\n') as f:
        f.write('\n'.join(L) + '\n')


def write_json(items, rod_rows):
    keys = ('vnum', 'name', 'locale_name', 'type', 'subtype', 'stack', 'weight', 'size', 'antiflag', 'flag',
            'wearflag', 'gold', 'shop_buy_price', 'refined_vnum', 'refine_set', 'magic_pct', 'specular', 'socket_pct',
            'limittype0', 'limitvalue0', 'limittype1', 'limitvalue1', 'applytype0', 'applyvalue0', 'applytype1',
            'applyvalue1', 'applytype2', 'applyvalue2', 'value0', 'value1', 'value2', 'value3', 'value4', 'value5')

    def line(i):
        return '%d\tETC\t%s' % (i['vnum'], i['icon']) + ('\t%s' % i['model'] if i.get('model') else '')
    out = {'items': [dict((k, i[k]) for k in keys) for i in items],
           'item_list': dict((str(i['vnum']), line(i)) for i in items),
           'itemdesc': dict((str(i['vnum']), '%d\t%s\t%s' % (i['vnum'], i['locale_name'], Y.client_desc(i)))
                            for i in items),
           # rods: only the name and the numbers change (the client's own record is kept otherwise)
           'rods': [dict(vnum=r['vnum'], locale_name=r['pl'], value=list(r['value']), refined_vnum=r['refined'])
                    for r in rod_rows],
           # the grilled fish fixed: type, subtype, value0, value1, applytype0, applyvalue0 and the text
           'grilled': dict((str(v), dict(type=t, subtype=s, value0=a, value1=b, applytype0=at, applyvalue0=av,
                                         desc='%d\t%s\t%s' % (v, GRILLED_NAMES[v], txt)))
                           for v, (t, s, a, b, at, av, txt) in GRILLED_FIX.items()),
           'renamed': {'27610': u'Kula Rybaka'},
           'renamed_desc': {'27610': '27610\tKula Rybaka\t%s' % KULA_TEXT},
           'shop_gold': dict((str(v), p) for v, (_n, p) in SHOP.items())}
    with open(JSON_OUT, 'w', encoding='utf-8', newline='\n') as f:
        json.dump(out, f, ensure_ascii=False, indent=0, sort_keys=True)
        f.write('\n')


def copy_icons(items, gf):
    os.makedirs(ICON_OUT, exist_ok=True)
    for i in items:
        if i.get('icon_src') is None:
            continue
        s = os.path.join(gf, 'icon', 'item', '%d.tga' % i['icon_src'])
        assert os.path.isfile(s), s
        shutil.copyfile(s, os.path.join(ICON_OUT, os.path.basename(i['icon'])))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--gf', default='/opt/metin2/cache/gf/Gameforge_26.1.11/_client')
    a = ap.parse_args()
    items = new_items()
    assert len(set(i['vnum'] for i in items)) == len(items)
    rod_rows = rods()
    write_sql(items, rod_rows)
    write_json(items, rod_rows)
    copy_icons(items, a.gf)
    print('new items %d, rods %d, grilled fixed %d, shop %d' % (len(items), len(rod_rows), len(GRILLED_FIX), len(SHOP)))


if __name__ == '__main__':
    main()
