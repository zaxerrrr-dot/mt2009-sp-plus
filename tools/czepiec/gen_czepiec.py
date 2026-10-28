#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""gen_czepiec.py [--gf DIR]

MT2009_PLUS_SERPENT_HOOD_V1: Wężowy Czepiec, the level-120 helmet of Krypta Balathora (the owner, 29 October 2026:
"dodaj go do gry"), as the pl-wiki gives it ("Wężowy Czepiec", "Strażnik Smoków Jaharr", "Oko / Róg / Ścięgno /
Skrzydło / Łuska Balathora", "Zroszony Młot", "System Gaya", "Mroźna Skrz. Balathora(+)"). Owsap v6.2.6 has none of
these items; the vnums are the GF 26.1.11 client's (shared/common/item_list.txt), each found by its icon - the wiki's
icon file against every 32x32 GF icon (the closest one by far, pixel by pixel):

  12880-12895 Wężowy Czepiec+0..+15   ITEM_ARMOR / ARMOR_HEAD, level 120, every class; Obrona 27..233 (value1 15 +
                                      2 x value5, the wiki's column); the fixed main bonus Mag./krótkodys. atak
                                      1..16% = point 132 (APPLY_MELEE_MAGIC_ATTBONUS_PER) by the level; ONE random
                                      second bonus of the wiki's list ("1. Bonus") rolled when the helmet is made and
                                      kept through every refine (server-patches/czepiec - the serpent gear's yextra
                                      line, MT2009_PLUS_YOHARA_SETS_V1); bonuses 1-5 and 6/7 are any helmet's (the
                                      helmet attribute set, item_attr / item_attr_rare - nothing of its own);
                                      refine_proto 40500-40514 (+0 -> +15, the wiki's Yang and materials)
  31264 Ścięgno Balathora, 31265 Zroszony Młot, 31266 Skrzydło Balathora, 31267 Róg Balathora,
  31268 Oko Balathora, 31269 Łuska Balathora   ITEM_MATERIAL, stackable (200)

Existing items it uses: 50662 Jadeit Nocy, 31257 Wzór Wężowy, 31239/31240/31241 Połyskująca Biała / Nieb. / Krwawa
Perła, 30617 Agat, 30616 Dwutlenek Tytanu, 30618 Kamień Księżycowy, 95927 Gaya.

Writes (all GENERATED - edit this file, run it again):
  linux-port/docker/mariadb/playerbot/yohara_czepiec.sql    world.item_proto + world.refine_proto (INSERT IGNORE)
  linux-port/docker/game/cube.czepiec.txt                   Jaharr's (20421) recipe of Wężowy Czepiec+0, appended to
                                                            cube.txt by the Dockerfile (quest helm100 opens the window)
  tools/czepiec/czepiec_items.json                          the client's records, item_list, itemdesc rows and the
                                                            random bonus table (server-patches/czepiec/gen_edits.py,
                                                            client-patches/client-2.0.30/tools/czepiec)
  client-patches/client-2.0.30/root/ysets_hood.py           the client's copy of the random bonus table (ysets.py)
  client-patches/client-2.0.30/root/icon/item/<vnum>.tga    the GF icons

Example: python3 tools/czepiec/gen_czepiec.py
"""
import argparse
import json
import os
import shutil
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(os.path.dirname(HERE))
sys.path.insert(0, os.path.join(REPO, 'tools', 'yohara_items'))
import gen_yitems as Y  # noqa: E402  (the item row writer)

M = 'MT2009_PLUS_SERPENT_HOOD_V1'
SQL_OUT = os.path.join(REPO, 'linux-port', 'docker', 'mariadb', 'playerbot', 'yohara_czepiec.sql')
CUBE_OUT = os.path.join(REPO, 'linux-port', 'docker', 'game', 'cube.czepiec.txt')
JSON_OUT = os.path.join(HERE, 'czepiec_items.json')
CLIENT_ROOT = os.path.join(REPO, 'client-patches', 'client-2.0.30', 'root')
PY_OUT = os.path.join(CLIENT_ROOT, 'ysets_hood.py')
ICON_OUT = os.path.join(CLIENT_ROOT, 'icon', 'item')

ARMOR, HEAD, MATERIAL = 2, 1, 5
WEAR_HEAD = 2
ITEM_REFINEABLE = 1             # flag 1 as every refinable helmet / serpent piece of our world (12840, 21310)
POINT_MELEE_MAGIC_ATT_BONUS_PER = 132

HOOD = 12880
HOOD_NAME = 'Wężowy Czepiec'
HOOD_DESC = ('Hełm 120. poziomu od Strażnika Smoków Jaharra. Stały bonus: Mag./krótkodys. atak, rośnie z poziomem '
             'ulepszenia. Drugi bonus jest losowany przy wytworzeniu i zostaje przy ulepszaniu.')
# pl-wiki "Wężowy Czepiec": Bonus1 (Obrona) and Bonus2 (Magiczny/krótkodystansowy atak %), +0..+15
WIKI_DEF = [27, 31, 35, 45, 55, 75, 85, 97, 107, 121, 135, 151, 167, 187, 209, 233]
WIKI_ATT = [1, 1, 2, 3, 4, 4, 5, 6, 7, 9, 10, 11, 12, 13, 14, 16]
DEF_VALUE1 = 15                 # value1 15 + 2 x value5 = the wiki's Obrona (the helmets' rule, tools/yhelm100)
# the merchant's price ladder of the serpent armours (21310-21325): the same tier and line
SELL = [120000, 130000, 145000, 165000, 190000, 220000, 265000, 325000, 405000, 515000, 515000, 515000, 515000,
        515000, 515000, 515000]
GOLD = 120000                   # not sold by any NPC (wiki: "Cena" empty) - the serpent pieces' record value

# the materials: (vnum, name, wiki "Opis")
CHEST_TEXT = 'Ten materiał jest wymagany do wytworzenia Wężowego Czepca. Możesz go znaleźć w Mroźnej Skrzyni Balathora.'
MATERIALS = [
    (31264, 'Ścięgno Balathora', CHEST_TEXT),
    (31265, 'Zroszony Młot', 'Ten materiał jest wymagany do wytworzenia Wężowego Czepca. Możesz otrzymać go w '
                             'Sklepie Gaya.'),
    (31266, 'Skrzydło Balathora', CHEST_TEXT),
    (31267, 'Róg Balathora', CHEST_TEXT),
    (31268, 'Oko Balathora', CHEST_TEXT),
    (31269, 'Łuska Balathora', 'Ten materiał jest potrzebny do ulepszania Wężowego Czepca. Możesz go znaleźć w '
                               'Mroźnej Skrzyni Balathora+.'),
]
SCIEGNO, MLOT, SKRZYDLO, ROG, OKO, LUSKA = 31264, 31265, 31266, 31267, 31268, 31269
JADEIT_NOCY, WZOR_WEZOWY = 50662, 31257
PERLA_BIALA, PERLA_NIEB, PERLA_KRWAWA = 31239, 31240, 31241
AGAT, DWUTLENEK, KSIEZYCOWY = 30617, 30616, 30618

# refine_proto 40500-40514: the step +n -> +n+1 of Wężowy Czepiec+n (free in world.refine_proto and in every branch's
# SQL, 29 October 2026). pl-wiki "Koszt1..15" and "Ulepszacz-1/2/3-<level>"; the wiki gives no chances - the serpent
# armours' steps (refine_proto 40360-40374, the same tier) are taken.
REFINE0 = 40500
REFINE = [  # (cost, [(vnum, count)...]) for +1 .. +15
    (150000, [(OKO, 1), (MLOT, 1), (ROG, 2)]),
    (180000, [(OKO, 2), (MLOT, 2), (ROG, 4)]),
    (216000, [(OKO, 3), (MLOT, 3), (ROG, 6)]),
    (260000, [(OKO, 4), (MLOT, 5), (ROG, 8)]),
    (310000, [(OKO, 5), (MLOT, 7), (ROG, 10)]),
    (920000, [(OKO, 7), (MLOT, 10), (ROG, 15)]),
    (1110000, [(OKO, 10), (LUSKA, 1), (PERLA_KRWAWA, 5)]),
    (1330000, [(OKO, 12), (LUSKA, 1), (PERLA_NIEB, 5)]),
    (1600000, [(OKO, 15), (LUSKA, 1), (PERLA_BIALA, 5)]),
    (1920000, [(OKO, 20), (LUSKA, 3), (AGAT, 5)]),
    (2304000, [(OKO, 25), (LUSKA, 3), (DWUTLENEK, 5)]),
    (2764800, [(OKO, 30), (LUSKA, 3), (KSIEZYCOWY, 5)]),
    (3317700, [(OKO, 35), (LUSKA, 3), (AGAT, 7)]),
    (3981300, [(OKO, 40), (LUSKA, 3), (DWUTLENEK, 7)]),
    (4777500, [(OKO, 45), (LUSKA, 3), (KSIEZYCOWY, 7)]),
]
PROB = [90, 75, 60, 50, 40, 30, 25, 15, 8, 5, 5, 5, 5, 3, 3]     # refine_proto 40360-40374 (Płaszcz Wężowy)

# Jaharr's recipe (pl-wiki "Wężowy Czepiec", Uszlachetnianie: the result Wężowy Czepiec x1 from these, 200 Gaya,
# 20 000 000 Yang, 50%)
JAHARR = 20421
RECIPE = [(SCIEGNO, 2), (MLOT, 7), (SKRZYDLO, 2), (JADEIT_NOCY, 10), (WZOR_WEZOWY, 40)]
RECIPE_GOLD, RECIPE_GAYA, RECIPE_PCT = 20000000, 200, 50

# The random second bonus (pl-wiki "Możliwe wartości bonusów", 1. Bonus): (point, wiki name, rows of +0..+15 - the
# lowest and the highest value the wiki gives; one row where it gives one). Rolled once: a line and a row.
SM_LO = [1, 2, 3, 4, 6, 8, 10, 12, 14, 17, 19, 21, 23, 26, 30, 34]
SM_HI = [2, 3, 4, 6, 8, 10, 12, 14, 17, 20, 22, 24, 26, 29, 33, 38]
PCT_LO = [1, 1, 1, 1, 2, 3, 4, 5, 6, 8, 9, 11, 12, 14, 17, 19]
PCT_HI = [1, 2, 2, 2, 3, 4, 5, 6, 7, 10, 11, 13, 14, 16, 19, 22]
BLOCK = [1, 1, 1, 1, 1, 2, 2, 2, 3, 4, 5, 6, 7, 8, 9, 10]
DODGE = [1, 1, 1, 1, 2, 2, 2, 3, 3, 4, 5, 6, 7, 8, 10, 12]
# points (common/length.h; an apply is a point here): POINT_SUNGMA_STR/HP/MOVE/IMMUNE 184-187 (the serpent gear's
# "Wola SungMa (SIŁA/WIT/ODP/INT)", tools/ysets), POINT_HIT_PCT 197 (Precyzja), POINT_RESIST_MAGIC 77,
# POINT_RESIST_MONSTER_1000PCT 142 (thousandths: battle.cpp takes value / 1000 of a monster's blow - the wiki's % x 10;
# the client shows value / 10 %), POINT_BLOCK 67, POINT_DODGE 68 (arrows)
HOOD_LINE = [
    (184, 'Wola SungMa (SIŁA)', [SM_LO, SM_HI]),
    (185, 'Wola SungMa (WIT)', [SM_LO, SM_HI]),
    (186, 'Wola SungMa (ODP)', [SM_LO, SM_HI]),
    (187, 'Wola SungMa (INT)', [SM_LO, SM_HI]),
    (197, 'Precyzja', [PCT_LO, PCT_HI]),
    (77, 'Odporność na Magię', [PCT_LO, PCT_HI]),
    (142, 'Odporność na atak potworów', [[v * 10 for v in PCT_LO], [v * 10 for v in PCT_HI]]),
    (67, 'Szansa na Blok Ciosu', [BLOCK]),
    (68, 'Szansa na uniknięcie Strzały', [DODGE]),
]


def item(vnum, name, desc, **kw):
    d = dict(vnum=vnum, src=vnum, status=Y.ST, name=Y.ascii_name(name), locale_name=name, type=MATERIAL, subtype=0,
             stack=200, weight=0, size=1, antiflag=0, flag=Y.FLAGS['ITEM_STACKABLE'], wearflag=0, gold=1000,
             shop_buy_price=50, refined_vnum=0, refine_set=0, magic_pct=0, specular=0, socket_pct=0, addon_type=0,
             limittype0=0, limitvalue0=0, limittype1=0, limitvalue1=0, applytype0=0, applyvalue0=0, applytype1=0,
             applyvalue1=0, applytype2=0, applyvalue2=0, value0=0, value1=0, value2=0, value3=0, value4=0, value5=0,
             desc=desc, icon='icon/item/%d.tga' % vnum, list_type='ETC')
    d.update(kw)
    assert len(d['locale_name'].encode('cp1250')) <= 24, d['locale_name']
    return d


def items():
    out = []
    for lv in range(16):
        assert (WIKI_DEF[lv] - DEF_VALUE1) % 2 == 0, lv
        out.append(item(HOOD + lv, '%s+%d' % (HOOD_NAME, lv), HOOD_DESC, type=ARMOR, subtype=HEAD, stack=1,
                        flag=ITEM_REFINEABLE, wearflag=WEAR_HEAD, gold=GOLD, shop_buy_price=SELL[lv],
                        refined_vnum=HOOD + lv + 1 if lv < 15 else 0, refine_set=REFINE0 + lv if lv < 15 else 0,
                        magic_pct=15, limittype0=1, limitvalue0=120,
                        applytype0=POINT_MELEE_MAGIC_ATT_BONUS_PER, applyvalue0=WIKI_ATT[lv],
                        value1=DEF_VALUE1, value5=(WIKI_DEF[lv] - DEF_VALUE1) // 2,
                        icon='icon/item/%d.tga' % HOOD, list_type='ARMOR'))
    for v, name, desc in MATERIALS:
        out.append(item(v, name, desc))
    return out


def refines():
    rows = []
    assert len(REFINE) == len(PROB) == 15
    for lv, ((cost, mats), prob) in enumerate(zip(REFINE, PROB)):
        assert 1 <= len(mats) <= 5
        flat = []
        for v, n in mats + [(0, 0)] * (5 - len(mats)):
            flat += [v, n]
        rows.append([REFINE0 + lv] + flat + [cost, 0, 0, prob])
    return rows


def write_sql(its, refs):
    L = ['-- %s: Wężowy Czepiec (the owner, 29 October 2026; pl-wiki "Wężowy Czepiec") - GENERATED by' % M,
         '-- tools/czepiec/gen_czepiec.py, do not edit, rerun it. Every start (apply.sh, after balathor.sql), idempotent:',
         '-- INSERT IGNORE - a row the operator changed is kept. The vnums of the GF 26.1.11 client (Owsap has none):',
         '--   12880-12895 Wężowy Czepiec+0..+15 (level 120, every class; Obrona 27..233, Mag./krótkodys. atak 1..16%',
         '--     = point 132; its random second bonus is server-patches/czepiec\'s, its bonuses 1-5 and 6/7 any helmet\'s),',
         '--     refine_proto %d-%d (the wiki\'s Yang and materials, the serpent armours\' chances);' % (REFINE0, REFINE0 + 14),
         '--   31264 Ścięgno Balathora, 31265 Zroszony Młot, 31266 Skrzydło Balathora, 31267 Róg Balathora,',
         '--   31268 Oko Balathora, 31269 Łuska Balathora (materials, stack 200).',
         '-- Jaharr (20421) makes the helmet: game/cube.czepiec.txt. The materials: Mroźna Skrz. Balathora(+)',
         '-- (game/balathor/special_item_group.balathor.txt), Zroszony Młot also in the Gaya shop (quest ygaya).',
         '-- Each vnum and refine id was free in world.item_proto / refine_proto (29 October 2026).',
         'SET NAMES utf8mb4;',
         'INSERT IGNORE INTO world.item_proto (%s) VALUES' % ','.join('`%s`' % c for c in Y.COLS),
         ',\n'.join(Y.sqlrow(i) for i in its) + ';',
         'INSERT IGNORE INTO world.refine_proto (id,vnum0,count0,vnum1,count1,vnum2,count2,vnum3,count3,vnum4,count4,'
         'cost,src_vnum,result_vnum,prob) VALUES',
         ',\n'.join('(' + ','.join(str(x) for x in r) + ')' for r in refs) + ';']
    with open(SQL_OUT, 'w', encoding='utf-8', newline='\n') as f:
        f.write('\n'.join(L) + '\n')


def write_cube():
    L = ['# %s: GENERATED by tools/czepiec/gen_czepiec.py - do not edit. Appended to cube.txt by the' % M,
         '# Dockerfile after cube.helm100.txt; quest helm100 opens the window of Straznik Smokow Jaharr (20421).',
         '# pl-wiki "Wezowy Czepiec": 2 Sciegna Balathora, 7 Zroszonych Mlotow, 2 Skrzydla Balathora, 10 Jadeitow',
         '# Nocy, 40 Wzorow Wezowych, 200 Gaya and 20 000 000 Yang, 50% - a failure takes the materials, the Yang and',
         '# the Gaya. The helmet rolls its random second bonus when it is made (server-patches/czepiec).',
         '',
         '# Wezowy Czepiec+0',
         'section', 'npc\t%d' % JAHARR]
    L += ['item\t%d\t%d' % m for m in RECIPE]
    L += ['reward\t%d\t1' % HOOD, 'percent\t%d' % RECIPE_PCT, 'gold\t%d' % RECIPE_GOLD, 'gaya\t%d' % RECIPE_GAYA,
          'end', '']
    with open(CUBE_OUT, 'w', encoding='ascii', newline='\n') as f:
        f.write('\n'.join(L))


def hood_table():
    return [dict(point=p, name=n, rows=rows) for p, n, rows in HOOD_LINE]


def write_json(its):
    keys = ('vnum', 'name', 'locale_name', 'type', 'subtype', 'stack', 'weight', 'size', 'antiflag', 'flag',
            'wearflag', 'gold', 'shop_buy_price', 'refined_vnum', 'refine_set', 'magic_pct', 'specular', 'socket_pct',
            'limittype0', 'limitvalue0', 'limittype1', 'limitvalue1', 'applytype0', 'applyvalue0', 'applytype1',
            'applyvalue1', 'applytype2', 'applyvalue2', 'value0', 'value1', 'value2', 'value3', 'value4', 'value5')
    out = {'items': [dict((k, i[k]) for k in keys) for i in its],
           'item_list': dict((str(i['vnum']), '%d\t%s\t%s' % (i['vnum'], i['list_type'], i['icon'])) for i in its),
           'itemdesc': dict((str(i['vnum']), '%d\t%s\t%s' % (i['vnum'], i['locale_name'], Y.client_desc(i)))
                            for i in its),
           'hood': {'base': HOOD, 'levels': 16, 'line': hood_table()}}
    with open(JSON_OUT, 'w', encoding='utf-8', newline='\n') as f:
        json.dump(out, f, ensure_ascii=False, indent=0)
        f.write('\n')


def write_py():
    """the client's copy (Python 2, ASCII; ysets.py merges it into ysets_data's tables): the family "h" with one line"""
    L = ['# %s: GENERATED by tools/czepiec/gen_czepiec.py - do not edit. Wezowy Czepiec\'s random' % M,
         '# second bonus (pl-wiki "Wezowy Czepiec", 1. Bonus) - the server\'s copy: server-patches/czepiec. ysets.py',
         '# adds these to ysets_data.RANDOM_FAMILIES / RANDOM_GROUPS (the family "h": one line).',
         '',
         'RANDOM_FAMILIES = {%d: "h"}' % HOOD,
         '',
         '# kind -> [line 1] -> [(point, ((+0..+15) per row))] - the line\'s byte: bonus index + 1 | row << 4',
         'RANDOM_GROUPS = {',
         '\t"h": (',
         '\t\t(']
    for p, _n, rows in HOOD_LINE:
        # a tuple of rows - "(row,)" when there is one (a lone "(row)" would be the row itself)
        L.append('\t\t\t(%d, (%s,)),' % (p, ', '.join('(%s)' % ', '.join(str(x) for x in r) for r in rows)))
    L += ['\t\t),', '\t),', '}', '']
    with open(PY_OUT, 'wb') as f:
        f.write('\n'.join(L).encode('ascii'))


def copy_icons(gf):
    os.makedirs(ICON_OUT, exist_ok=True)
    for v in [HOOD] + [m[0] for m in MATERIALS]:
        s = os.path.join(gf, 'icon', 'item', '%d.tga' % v)
        assert os.path.isfile(s), s
        shutil.copyfile(s, os.path.join(ICON_OUT, '%d.tga' % v))


def check_gf_list(gf):
    """every vnum is in the GF client's item_list with its own icon (the hood's 16 levels share 12880.tga)"""
    rows = {}
    with open(os.path.join(gf, 'shared', 'common', 'item_list.txt'), 'rb') as f:
        for raw in f:
            t = raw.decode('cp1250', 'replace').rstrip('\r\n').split('\t')
            if len(t) >= 3 and t[0].strip().isdigit():
                rows[int(t[0])] = (t[1].strip(), t[2].strip())
    for lv in range(16):
        assert rows.get(HOOD + lv) == ('ARMOR', 'icon/item/%d.tga' % HOOD), (HOOD + lv, rows.get(HOOD + lv))
    for v, _n, _d in MATERIALS:
        assert rows.get(v) == ('ETC', 'icon/item/%d.tga' % v), (v, rows.get(v))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--gf', default='/opt/metin2/cache/gf/Gameforge_26.1.11/_client')
    a = ap.parse_args()
    check_gf_list(a.gf)
    for _p, _n, rows in HOOD_LINE:
        assert 1 <= len(rows) <= 5 and all(len(r) == 16 for r in rows)
    assert len(HOOD_LINE) <= 15                     # the line's byte keeps the bonus index in 4 bits
    its = items()
    refs = refines()
    write_sql(its, refs)
    write_cube()
    write_json(its)
    write_py()
    copy_icons(a.gf)
    print('items %d (Wezowy Czepiec+0..+15, materials 6), refine_proto %d-%d, 1 recipe at %d, random line %d bonuses'
          % (len(its), REFINE0, REFINE0 + 14, JAHARR, len(HOOD_LINE)))


if __name__ == '__main__':
    main()
