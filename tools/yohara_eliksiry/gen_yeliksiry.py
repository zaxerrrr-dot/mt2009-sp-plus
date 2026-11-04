#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""gen_yeliksiry.py [--owsap DIR] [--gf DIR]

MT2009_PLUS_YELIXIRS_V1: the elixirs of Yohara (the owner, 21 October 2026: the herbs 95733-95736, 50737, 50738 and the
empty bottles 50739 / 50740 dropped but had no use; "Jesli czegos nie wiesz - wszystko zgodnie z wiki").

The pl-wiki (cache/yohara/wiki/elik: "Zielarstwo" - Eliksiry, "Eliksir Ognistej Mocy", "Eliksir Odp. na Ogien"; the
en-wiki "Power of Flame Elixir" the same): Huahn-So (20022; Bokjung, Bakra, Jayang) makes from 10 herbs of an element and
20 empty bottles one elixir - with Pusty Eliksir Mocy the element's power, with Pusty Eliksir Odp. the resistance to the
element: +8-20% for 1-10 minutes (random), from level 120, a 90% chance. Twelve elixirs, the official vnums 50830-50841
(Owsap v6.2.6 db/item_proto.txt: ITEM_BLEND, STACKABLE | SLOW_QUERY, LEVEL 120), the names and texts of Owsap's Polish
client (= the wiki's), the icons of the GF 26.1.11 client.

MT2009_PLUS_MIKSTURY_V1 (the owner, 4 November 2026; cache/yohara/decyzje-lowienie-mikstury.md M3, M4, "Eliksiry"):
the golden ones too - 50842-50853 (Owsap's rows, the same shape), Huahn-So makes them from the same 10 herbs and 20
bottles plus 1 Zlote Ziolo (50741, Owsap's ITEM_MATERIAL row; on this server a rare find of herb gathering -
game/quest/m2_mikstury_limity.lua - and of the Yohara boss chests - tools/yohara_chestdrops), 90%, 100 000 Yang
(the wiki / Owsap's cube); always +20% for a fixed 10 minutes (M4). The normal elixirs cost 50 000 Yang now (the wiki).
The golden ones' client data (and Zlote Ziolo's icon) go to zlote_eliksiry.json - client-2.0.30/tools/zeliksiry;
yohara_eliksiry.json keeps the 12 normal ones (client-2.0.30/tools/yeliksiry).

Effects: ITEM_BLEND as the dews (Rosy) - blend.txt gives an item its value and time when it is made (blend_item.cpp:
values 8/10/12/15/20 with 10/20/40/20/10%, the times 60/120/180/300/600 s the same, apart), drinking it adds
AFFECT_BLEND on the point in socket 0 (char_item.cpp). In this engine an apply is a point and blend.txt's apply_type
is read as a number (str_to_number), so the rows carry the point numbers: the element powers POINT_ENCHANT_* 178-183
(the talismans' points, server-patches/zywioly - the damage against a monster of that element, playerbot_elements.cpp)
and the resistances POINT_RESIST_FIRE 75 / ELEC 76 / WIND 78 / ICE 133 / EARTH 134 / DARK 135.

Writes (all GENERATED - edit this file, run it again):
  linux-port/docker/mariadb/playerbot/yohara_eliksiry.sql   world.item_proto (INSERT IGNORE)
  linux-port/docker/game/cube.eliksiry.txt                  Huahn-So's 12 recipes (appended to cube.txt)
  linux-port/docker/game/blend.eliksiry.txt                 the 12 blend.txt sections (appended to blend.txt)
  tools/yohara_eliksiry/yohara_eliksiry.json                the client's records, item_list, itemdesc (50830-50841)
  tools/yohara_eliksiry/zlote_eliksiry.json                 the same for 50842-50853 and 50741 (+ the 50804 fix)
  client-patches/client-2.0.30/root/icon/item/508xx.tga     the GF icons (+ 50741.tga)

Example: python3 tools/yohara_eliksiry/gen_yeliksiry.py
"""
import argparse
import json
import os
import shutil
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(os.path.dirname(HERE))
sys.path.insert(0, os.path.join(REPO, 'tools', 'yohara_items'))
import gen_yitems as Y  # noqa: E402  (the engine's numbers, the row writer)

SQL_OUT = os.path.join(REPO, 'linux-port', 'docker', 'mariadb', 'playerbot', 'yohara_eliksiry.sql')
CUBE_OUT = os.path.join(REPO, 'linux-port', 'docker', 'game', 'cube.eliksiry.txt')
BLEND_OUT = os.path.join(REPO, 'linux-port', 'docker', 'game', 'blend.eliksiry.txt')
JSON_OUT = os.path.join(HERE, 'yohara_eliksiry.json')
GOLD_JSON_OUT = os.path.join(HERE, 'zlote_eliksiry.json')    # MT2009_PLUS_MIKSTURY_V1
ICON_OUT = os.path.join(REPO, 'client-patches', 'client-2.0.30', 'root', 'icon', 'item')

HUAHN_SO = 20022
ITEM_BLEND = 27                 # common/item_length.h (our dews 50821-50826 are type 27)
BOTTLE_POWER, BOTTLE_RESIST = 50739, 50740
HERBS, BOTTLES, PERCENT = 10, 20, 90          # the wiki: 10x herb + 20x bottle -> 1 elixir, 90%
VALUES = (8, 10, 12, 15, 20)                  # +8-20%
TIMES = (60, 120, 180, 300, 600)              # 1-10 minutes
# element: (herb, power point POINT_ENCHANT_*, resistance point POINT_RESIST_*)
ELEMENTS = (
    ('ogien', 95733, 179, 75),      # Ognisty Lisc       - Sila Ognia,     Odpornosc na ogien
    ('lod', 95734, 180, 133),       # Mrozny Korzonek    - Sila Lodu,      Odpornosc na lod
    ('blyskawica', 95735, 178, 76),  # Piorunowe Ziolo   - Sila Blyskawic, Odpornosc na blyskawice
    ('wiatr', 95736, 181, 78),      # Kwiat Pln. Wiatru  - Sila Wiatru,    Odpornosc na wiatr
    ('ziemia', 50737, 182, 134),    # Ziemne Pnacze      - Sila Ziemi,     Odpornosc na ziemie
    ('mrok', 50738, 183, 135),      # Mroczny Ciern      - Sila Mroku,     Odpornosc na mrok
)
POWER0, RESIST0 = 50830, 50836  # Owsap: 50830-50835 the powers, 50836-50841 the resistances, the order above
GOLD = 50000                    # MT2009_PLUS_MIKSTURY_V1: the wiki's 50 000 Yang an elixir
HOW = (u' Sporządza go zielarz Huahn-So (Bokjung, Bakra, Jayang) z 10 ziół i 20 pustych butelek (szansa 90%, '
       u'50 000 Yang). Wartość i czas działania są losowane przy sporządzaniu; widać je w opisie eliksiru.')
# MT2009_PLUS_MIKSTURY_V1: the golden elixirs (Owsap: 50842-50847 the powers, 50848-50853 the resistances) and their herb
G_POWER0, G_RESIST0 = 50842, 50848
GOLDEN_HERB = 50741
G_GOLD = 100000                 # the wiki / Owsap's cube
G_VALUES = (20, 20, 20, 20, 20)     # always +20%
G_TIMES = (600, 600, 600, 600, 600)  # a fixed 10 minutes (the owner, M4)
G_HOW = (u' Działa zawsze 10 minut. Sporządza go zielarz Huahn-So (Bokjung, Bakra, Jayang) z 10 ziół, 20 pustych '
         u'butelek i Złotego Zioła (szansa 90%, 100 000 Yang). Zastępuje zwykły eliksir tego samego żywiołu.')
HERB_HOW = (u' Rzadko znajdziesz je przy zbieraniu ziół, w skrzyniach bossów Yohary i w Skrzyni Nimfy Wodnej. '
            u'Zielarz Huahn-So (Bokjung, Bakra, Jayang) sporządza z niego Złote Eliksiry.')


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--owsap', default='/opt/metin2/cache/owsap')
    ap.add_argument('--gf', default='/opt/metin2/cache/gf/Gameforge_26.1.11/_client')
    a = ap.parse_args()
    rows = Y.read_tsv(os.path.join(a.owsap, 'Server/Server/db/item_proto.txt'))
    head = rows[0]
    proto = dict((int(r[0]), dict(zip(head, r))) for r in rows[1:] if r and r[0].isdigit())
    desc = {}
    for r in Y.read_tsv(os.path.join(a.owsap, 'Client/Client/pack/locale/locale/pl/itemdesc.txt')):
        if len(r) >= 2 and r[0].strip().isdigit():
            desc[int(r[0])] = (r[1].strip(), r[2].strip() if len(r) > 2 else '')

    items, recipes, blends = [], [], []
    # the powers first, then the resistances (the cube window's order)
    pairs = [(POWER0 + n, herb, BOTTLE_POWER, power) for n, (elem, herb, power, resist) in enumerate(ELEMENTS)] + \
            [(RESIST0 + n, herb, BOTTLE_RESIST, resist) for n, (elem, herb, power, resist) in enumerate(ELEMENTS)]
    for vnum, herb, bottle, point in pairs:
        o = proto[vnum]
        assert (o['Type'], o['LimitType0'], o['LimitValue0']) == ('ITEM_BLEND', 'LEVEL', '120'), (vnum, o)
        pl, text = desc[vnum]
        assert pl and len(pl.encode('cp1250')) <= 32 and u'8-20%' in text, (vnum, pl, text)
        flag = Y.flags(o['Flags'], Y.FLAGS, 'flag')
        assert flag == Y.FLAGS['ITEM_STACKABLE'] | Y.FLAGS['ITEM_SLOW_QUERY'], (vnum, flag)
        items.append(dict(
            vnum=vnum, src=vnum, status=Y.ST, name=Y.ascii_name(pl), locale_name=pl, type=ITEM_BLEND, subtype=0,
            stack=1, weight=0, size=int(o['Size']), antiflag=Y.flags(o['AntiFlags'], Y.ANTI, 'antiflag'),
            flag=flag, wearflag=0, gold=0, shop_buy_price=0, refined_vnum=0, refine_set=0, magic_pct=0,
            specular=0, socket_pct=0, addon_type=0, limittype0=Y.LIMITS['LEVEL'], limitvalue0=120, limittype1=0,
            limitvalue1=0, applytype0=0, applyvalue0=0, applytype1=0, applyvalue1=0, applytype2=0, applyvalue2=0,
            value0=0, value1=0, value2=0, value3=0, value4=0, value5=0,
            desc=text + HOW, icon='icon/item/%d.tga' % vnum, list_type='ETC', point=point,
            herb=herb, bottle=bottle))
        recipes.append((vnum, pl, herb, bottle, 0, GOLD))
        blends.append((vnum, pl, point, VALUES, TIMES))
    # MT2009_PLUS_MIKSTURY_V1: the golden ones - the normal one's row with Owsap's name / text, the herb on top
    gold_items = []
    o = proto[GOLDEN_HERB]
    assert (o['Type'], o['Flags']) == ('ITEM_MATERIAL', 'ITEM_STACKABLE'), o
    pl, text = desc[GOLDEN_HERB]
    base = dict(items[0])
    base.update(vnum=GOLDEN_HERB, src=GOLDEN_HERB, name=Y.ascii_name(pl), locale_name=pl, type=Y.TYPES['ITEM_MATERIAL'],
                subtype=0, stack=200, antiflag=0, flag=Y.FLAGS['ITEM_STACKABLE'], limittype0=0, limitvalue0=0,
                desc=text + HERB_HOW, icon='icon/item/%d.tga' % GOLDEN_HERB, point=0, herb=0, bottle=0)
    gold_items.append(base)
    for n, (vnum, herb, bottle, point) in enumerate(pairs):
        g = (G_POWER0 if vnum < RESIST0 else G_RESIST0) + (vnum - (POWER0 if vnum < RESIST0 else RESIST0))
        o = proto[g]
        assert (o['Type'], o['LimitType0'], o['LimitValue0']) == ('ITEM_BLEND', 'LEVEL', '120'), (g, o)
        pl, text = desc[g]
        assert pl and len(pl.encode('cp1250')) <= 32 and u'+20%' in text, (g, pl, text)
        it = dict(items[n])
        assert it['vnum'] == vnum
        it.update(vnum=g, src=g, name=Y.ascii_name(pl), locale_name=pl, desc=text + G_HOW,
                  icon='icon/item/%d.tga' % vnum)        # the GF client's item_list: the normal elixir's icon
        gold_items.append(it)
        recipes.append((g, pl, herb, bottle, GOLDEN_HERB, G_GOLD))
        blends.append((g, pl, point, G_VALUES, G_TIMES))
    write_sql(items, gold_items)
    write_cube(recipes)
    write_blend(blends)
    write_json(items)
    write_gold_json(gold_items)
    copy_icons([i['vnum'] for i in items] + [GOLDEN_HERB], a.gf)
    print('elixirs %d + golden %d + Zlote Ziolo, recipes %d (Huahn-So %d), blend rows %d'
          % (len(items), len(gold_items) - 1, len(recipes), HUAHN_SO, len(blends)))


def write_sql(items, gold_items):
    L = ['-- MT2009_PLUS_YELIXIRS_V1: the elixirs of Yohara (the owner, 21 October 2026). GENERATED by',
         '-- tools/yohara_eliksiry/gen_yeliksiry.py - do not edit, rerun it. Every start (apply.sh), idempotent: INSERT',
         '-- IGNORE - a row the operator changed is kept. 50830-50841 (Owsap v6.2.6: ITEM_BLEND, level 120), Huahn-So',
         '-- makes them (cube.eliksiry.txt), blend.eliksiry.txt gives each its point, value and time. The vnums were free',
         '-- in our world.item_proto (21 October 2026).',
         'SET NAMES utf8mb4;',
         'INSERT IGNORE INTO world.item_proto (%s) VALUES' % ','.join('`%s`' % c for c in Y.COLS),
         ',\n'.join(Y.sqlrow(i) for i in items) + ';',
         '-- MT2009_PLUS_MIKSTURY_V1 (the owner, 4 November 2026): Zlote Ziolo 50741 (Owsap: ITEM_MATERIAL, stackable;',
         '-- herb gathering and the Yohara boss chests) and the golden elixirs 50842-50853 (Owsap: ITEM_BLEND, level 120;',
         '-- Huahn-So, +1 Zlote Ziolo, 100 000 Yang; always +20% for 10 minutes). The vnums were free (4 November 2026).',
         'INSERT IGNORE INTO world.item_proto (%s) VALUES' % ','.join('`%s`' % c for c in Y.COLS),
         ',\n'.join(Y.sqlrow(i) for i in gold_items) + ';']
    with open(SQL_OUT, 'w', encoding='utf-8', newline='\n') as f:
        f.write('\n'.join(L) + '\n')


def write_cube(recipes):
    L = ['# MT2009_PLUS_YELIXIRS_V1: GENERATED by tools/yohara_eliksiry/gen_yeliksiry.py - do not edit. Appended to the',
         '# share\'s cube.txt by the Dockerfile (quest eliksiry_yohary opens the window). Huahn-So (20022), the pl-wiki',
         '# ("Zielarstwo" - Eliksiry): 10 herbs + 20 empty bottles -> 1 elixir, 90%, 50 000 Yang; the golden ones',
         '# (MT2009_PLUS_MIKSTURY_V1) + 1 Zlote Ziolo (50741), 100 000 Yang.', '']
    for vnum, pl, herb, bottle, extra, gold in recipes:
        L += ['# %s' % Y.ascii_name(pl), 'section', 'npc\t%d' % HUAHN_SO, 'item\t%d\t%d' % (herb, HERBS),
              'item\t%d\t%d' % (bottle, BOTTLES)] + (['item\t%d\t1' % extra] if extra else []) + \
             ['reward\t%d\t1' % vnum, 'gold\t%d' % gold, 'percent\t%d' % PERCENT, 'end', '']
    with open(CUBE_OUT, 'w', encoding='ascii', newline='\n') as f:
        f.write('\n'.join(L))


def write_blend(blends):
    L = ['# MT2009_PLUS_YELIXIRS_V1: GENERATED by tools/yohara_eliksiry/gen_yeliksiry.py - do not edit. Appended to the',
         '# share\'s blend.txt by the Dockerfile. apply_type is the point number (this engine reads it as a number).', '']
    for vnum, pl, point, values, times in blends:
        L += ['# %s' % Y.ascii_name(pl), 'section', '\titem_vnum\t%d' % vnum, '\tapply_type\t%d' % point,
              '\tapply_value\t' + '\t'.join(str(v) for v in values),
              '\tapply_duration\t' + '\t'.join(str(t) for t in times), 'end', '']
    with open(BLEND_OUT, 'w', encoding='ascii', newline='\n') as f:
        f.write('\n'.join(L))


def write_json(items):
    keys = ('vnum', 'name', 'locale_name', 'type', 'subtype', 'stack', 'weight', 'size', 'antiflag', 'flag',
            'wearflag', 'gold', 'shop_buy_price', 'refined_vnum', 'refine_set', 'magic_pct', 'specular', 'socket_pct',
            'limittype0', 'limitvalue0', 'limittype1', 'limitvalue1', 'applytype0', 'applyvalue0', 'applytype1',
            'applyvalue1', 'applytype2', 'applyvalue2', 'value0', 'value1', 'value2', 'value3', 'value4', 'value5')
    out = {'items': [dict((k, i[k]) for k in keys) for i in items],
           'item_list': dict((str(i['vnum']), '%d\t%s\t%s' % (i['vnum'], i['list_type'], i['icon'])) for i in items),
           'itemdesc': dict((str(i['vnum']), '%d\t%s\t%s' % (i['vnum'], i['locale_name'], Y.client_desc(i)))
                            for i in items),
           # the affect bar (root/uiaffectbar.py): AFFECT_BLEND's point -> the elixir whose icon and name it shows
           'affect_points': dict((str(i['point']), i['vnum']) for i in items)}
    with open(JSON_OUT, 'w', encoding='utf-8', newline='\n') as f:
        json.dump(out, f, ensure_ascii=False, indent=0, sort_keys=True)
        f.write('\n')


# MT2009_PLUS_MIKSTURY_V1: 50804 Sok z Korzenia Gango heals 50 HP (the wiki, M5) - the client's tooltip reads value0
VALUE0_FIXES = {50804: (90, 50)}


def write_gold_json(items):
    keys = ('vnum', 'name', 'locale_name', 'type', 'subtype', 'stack', 'weight', 'size', 'antiflag', 'flag',
            'wearflag', 'gold', 'shop_buy_price', 'refined_vnum', 'refine_set', 'magic_pct', 'specular', 'socket_pct',
            'limittype0', 'limitvalue0', 'limittype1', 'limitvalue1', 'applytype0', 'applyvalue0', 'applytype1',
            'applyvalue1', 'applytype2', 'applyvalue2', 'value0', 'value1', 'value2', 'value3', 'value4', 'value5')
    out = {'items': [dict((k, i[k]) for k in keys) for i in items],
           'item_list': dict((str(i['vnum']), '%d\t%s\t%s' % (i['vnum'], i['list_type'], i['icon'])) for i in items),
           'itemdesc': dict((str(i['vnum']), '%d\t%s\t%s' % (i['vnum'], i['locale_name'], Y.client_desc(i)))
                            for i in items),
           'value0': dict((str(v), new) for v, (old, new) in VALUE0_FIXES.items())}
    with open(GOLD_JSON_OUT, 'w', encoding='utf-8', newline='\n') as f:
        json.dump(out, f, ensure_ascii=False, indent=0, sort_keys=True)
        f.write('\n')


def copy_icons(vnums, gf):
    os.makedirs(ICON_OUT, exist_ok=True)
    for v in vnums:
        s = os.path.join(gf, 'icon', 'item', '%d.tga' % v)
        assert os.path.isfile(s), s
        shutil.copyfile(s, os.path.join(ICON_OUT, '%d.tga' % v))


if __name__ == '__main__':
    main()
