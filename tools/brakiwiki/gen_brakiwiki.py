#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""gen_brakiwiki.py [--owsap DIR] [--gf DIR]

MT2009_PLUS_BRAKI_WIKI_V1 - the Yohara items of cache/yohara/braki-yohara.md B9 "as on the global server" (the owner,
5 November 2026: "Dodaj zgodnie z Wiki Global"). Source: the pl-wiki ("Tajemniczy Talizman", "Talizmany",
"Kamien Rekawic Pln. W.", "Rekawice Weza (SILA/ODP/WIT/INT)", "Wytwarzanie Rekawic", "Ksiega Misji (W.Pln.W.)",
"Srebrne Plyty", "Stalowe Plyty"; the de / tr pages for the mission book's task), the official vnums and numbers of
Owsap v6.2.6 (Tools/Dump Proto item_proto.txt, db/data/player.sql), the icons of the GF 26.1.11 client.

  81561-81569 Tajemniczy Talizman+1..+9  the talisman of Tajemniczy Oltarz (81560, MT2009_PLUS_YOHARA_MAPS3_V1) refined
                                         to +9: level 120, the talisman slot; its two random base lines (a random Will
                                         SungMa 1-2 .. 21-24, a random element's power 1-30% .. 9-69%) are the engine's
                                         (server-patches/brakiwiki); the refine recipes are refine_global.sql's 40429-
                                         40437 (Tajemniczy Kamien, Topaz Woli / Polyskujace Perly, Esencja Talizmanu and a
                                         second Tajemniczy Talizman+0 - the wiki's "Talizmany" table)
  23050-23089 Rekawice Weza (SILA/ODP/WIT/INT)+0..+9
                                         level 120, the glove slot, 3 sockets for the Kamienie Demonow, the Will SungMa
                                         of the glove (6-9 .. 69-78, the wiki's columns = Owsap's ApplyRandomValue24) as
                                         its base attribute (the overlay's Mt2009GloveType), Obrona 16 + 2 x value5
                                         (the wiki's 15-17 .. 55-57: Owsap's value5 0..20, the middle of the base range -
                                         our engine has no random armour base); made at Mistrz Chi (cube.brakiwiki.txt)
                                         from the Sung Ma glove of the same Will +0..+9, Kamien Ksiezycowy, Agat,
                                         Dwutlenek Tytanu and 10 000 000 Yang, 30-100% by the plus; refined with Kamien
                                         Rekawic Pln. W. (refine_global.sql 40384-40392)

Writes (all GENERATED - edit this file, run it again):
  linux-port/docker/mariadb/playerbot/braki_wiki.sql        world.item_proto (INSERT IGNORE + guarded UPDATEs)
  linux-port/docker/game/brakiwiki/cube.brakiwiki.txt       Mistrz Chi's 40 recipes of the serpent gloves
  linux-port/docker/game/brakiwiki/mob_drop_item.brakiwiki.txt
                                                            Zolnierz Ochao's Stalowe Plyty (the wiki)
  tools/brakiwiki/brakiwiki_items.json                      the client's item records, item_list, itemdesc rows
                                                            (client-patches/client-2.0.30/tools/brakiwiki)
  client-patches/client-2.0.30/root/icon/item/<icon>.tga    the gloves' GF icons 23050/23060/23070/23080

Example: python3 tools/brakiwiki/gen_brakiwiki.py
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

M = 'MT2009_PLUS_BRAKI_WIKI_V1'
SQL_OUT = os.path.join(REPO, 'linux-port', 'docker', 'mariadb', 'playerbot', 'braki_wiki.sql')
GAME_DIR = os.path.join(REPO, 'linux-port', 'docker', 'game', 'brakiwiki')
CUBE_OUT = os.path.join(GAME_DIR, 'cube.brakiwiki.txt')
DROP_OUT = os.path.join(GAME_DIR, 'mob_drop_item.brakiwiki.txt')
JSON_OUT = os.path.join(HERE, 'brakiwiki_items.json')
ICON_OUT = os.path.join(REPO, 'client-patches', 'client-2.0.30', 'root', 'icon', 'item')

ARMOR, PENDANT, GLOVE = 2, 7, 8
WEAR_PENDANT, WEAR_GLOVE = 4096, 8192
LEVEL = 1
# Tajemniczy Talizman: the row of yohara_items3.sql's 81560 (the same columns), refine_global.sql's recipes
TALISMAN0, TALISMAN_REFINE0 = 81560, 40429
# the serpent gloves: (base vnum, the wiki's name, the Sung Ma glove they are made from)
GLOVES = [(23050, 'Rękawice Węża (SIŁA)', 23000), (23060, 'Rękawice Węża (ODP)', 23010),
          (23070, 'Rękawice Węża (WIT)', 23020), (23080, 'Rękawice Węża (INT)', 23030)]
GLOVE_REFINE0 = 40384                   # refine_global.sql (the sheet = Owsap 750-758, +8 the wiki's 200 stones)
GLOVE_DEF_BASE = 16                     # the wiki's Obrona 15-17 at +0: the middle
WIKI_DEF = [(15, 17), (17, 19), (19, 21), (23, 25), (27, 29), (31, 33), (35, 37), (39, 41), (43, 45), (55, 57)]
WIKI_WILL = [(6, 9), (10, 13), (14, 19), (19, 25), (24, 31), (30, 38), (36, 44), (42, 50), (49, 58), (69, 78)]
# Mistrz Chi (20823): the Sung Ma glove +0..+9, Kamien Ksiezycowy, Agat, Dwutlenek Tytanu, 10 000 000 Yang; the wiki
# gives "30-100%" - ours: 30% for +0 up to 100% for +9 in even steps
CHI = 20823
CUBE_MATS = [(30618, 1), (30617, 1), (30616, 1)]
CUBE_FEE = 10000000
CUBE_PCT = [30 + (70 * lv + 4) // 9 for lv in range(10)]
GLOVE_DESC = 'Przepełnione wolą SungMa.'
TALISMAN_DESC = ('Przepełniony wolą SungMa. Może mieć losową Wolę SungMa i moc losowego żywiołu; brakujące '
                 'bonusy podstawowe mogą pojawić się przy ulepszaniu.')
# items the client has, only their description (the "Na razie bez zastosowania" note of the first Yohara batches gone)
DESC_ONLY = {31244: ('Kamień Rękawic Płn. W.', 'Materiał do ulepszania Rękawic Węża.'),
             50336: ('Księga Misji (W.Płn.W.)', 'Zawiera misję w Wąwozie Północnego Wiatru, za którą otrzymasz '
                                                 'nagrodę, jeśli ją pomyślnie ukończysz. Od poziomu: 120.')}
# the wiki's "Stalowe Plyty": Zolnierz Ochao drops it (moby_global has only his Srebrne Plyty) - at their 0.5%
DROPS = [(6302, 'Zolnierz Ochao', [(30608, 1, 0.5, 'Stalowe Plyty')])]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--owsap', default='/opt/metin2/cache/owsap')
    ap.add_argument('--gf', default='/opt/metin2/cache/gf/Gameforge_26.1.11/_client')
    a = ap.parse_args()
    rows = Y.read_tsv(os.path.join(a.owsap, 'Tools/Tools/Dump Proto/share/item_proto.txt'))
    head = rows[0]
    proto = dict((int(r[0]), dict(zip(head, r))) for r in rows[1:] if r and r[0].isdigit())
    items = []

    def row(vnum, name, **kw):
        d = dict(vnum=vnum, name=Y.ascii_name(name), locale_name=name, type=ARMOR, subtype=0, stack=1, weight=0,
                 size=1, antiflag=0, flag=0, wearflag=0, gold=0, shop_buy_price=0, refined_vnum=0, refine_set=0,
                 magic_pct=0, specular=0, socket_pct=0, addon_type=0, limittype0=LEVEL, limitvalue0=0, limittype1=0,
                 limitvalue1=0, applytype0=0, applyvalue0=0, applytype1=0, applyvalue1=0, applytype2=0,
                 applyvalue2=0, value0=0, value1=0, value2=0, value3=0, value4=0, value5=0)
        d.update(kw)
        assert len(d['locale_name'].encode('cp1250')) <= 24, d['locale_name']
        return d

    for lv in range(10):
        v = TALISMAN0 + lv
        o = proto[v]
        assert o['Type'] == 'ITEM_ARMOR' and o['SubType'] == 'ARMOR_PENDANT' and o['WearFlags'] == 'WEAR_PENDANT', v
        assert o['LimitType0'] == 'LEVEL' and int(o['LimitValue0']) == 120, v
        assert (o['ApplyType0'], o['ApplyValue0'], o['ApplyType1'], o['ApplyValue1']) == \
            ('APPLY_RANDOM', '28', 'APPLY_RANDOM', '29'), v
        assert int(o['RefinedVnum']) == (v + 1 if lv < 9 else 0), v
        items.append(row(v, 'Tajemniczy Talizman+%d' % lv, subtype=PENDANT, wearflag=WEAR_PENDANT,
                         gold=int(o['ShopBuyPrice']), shop_buy_price=int(o['ShopSellPrice']),
                         refined_vnum=v + 1 if lv < 9 else 0, refine_set=TALISMAN_REFINE0 + lv if lv < 9 else 0,
                         limitvalue0=120, desc=TALISMAN_DESC, icon='icon/item/81560.tga', list_type='ETC'))
    icons = []
    for k, (g0, pl, src) in enumerate(GLOVES):
        icons.append('%d.tga' % g0)
        for lv in range(10):
            v = g0 + lv
            o = proto[v]
            assert o['Type'] == 'ITEM_ARMOR' and o['SubType'] == 'ARMOR_GLOVE' and o['WearFlags'] == 'WEAR_GLOVE', v
            assert o['LimitType0'] == 'LEVEL' and int(o['LimitValue0']) == 120 and int(o['GainSocketPercent']) == 3, v
            assert o['ApplyType0'] == 'APPLY_RANDOM' and int(o['ApplyValue0']) == 24 + k, v
            assert int(o['RefinedVnum']) == (v + 1 if lv < 9 else 0), v
            assert int(o['RefineSet']) == (750 + lv if lv < 9 else 0), v
            v5 = int(o['Value5'])
            lo, hi = WIKI_DEF[lv]
            # Owsap's value6 1500017 = the base 15..17 (min * 100000 + max), + 2 x value5 - the wiki's column
            assert int(o['Value6']) == 1500017 and (15 + 2 * v5, 17 + 2 * v5) == (lo, hi), (v, v5, o['Value6'])
            items.append(row(v, '%s+%d' % (pl, lv), subtype=GLOVE, wearflag=WEAR_GLOVE,
                             gold=int(o['ShopBuyPrice']), shop_buy_price=int(o['ShopSellPrice']),
                             refined_vnum=v + 1 if lv < 9 else 0, refine_set=GLOVE_REFINE0 + lv if lv < 9 else 0,
                             magic_pct=int(o['AlterToMagicItemPercent']), socket_pct=3, limitvalue0=120,
                             value1=GLOVE_DEF_BASE, value5=v5, desc=GLOVE_DESC, icon='icon/item/%d.tga' % g0,
                             list_type='ARMOR'))
    assert len(items) == 50
    write_sql(items)
    write_cube()
    write_drops()
    write_json(items)
    os.makedirs(ICON_OUT, exist_ok=True)
    for ic in icons:
        s = os.path.join(a.gf, 'icon', 'item', ic)
        assert os.path.isfile(s), s
        shutil.copyfile(s, os.path.join(ICON_OUT, ic))
    print('items %d (Tajemniczy Talizman+0..+9, Rekawice Weza 40), cube %d recipes, drops %d' % (
        len(items), 40, sum(len(d[2]) for d in DROPS)))


def write_sql(items):
    t0 = items[0]
    L = ['-- %s: the Yohara items of braki-yohara.md B9 as on the global server (the owner, 5 November 2026:' % M,
         '-- "Dodaj zgodnie z Wiki Global"). GENERATED by tools/brakiwiki/gen_brakiwiki.py - do not edit, rerun it.',
         '-- Every start (apply.sh, after the Yohara item files, before refine_global.sql), idempotent: INSERT IGNORE -',
         '-- a row the operator changed is kept; the UPDATEs change only a value still at the old one.',
         '--   81561-81569 Tajemniczy Talizman+1..+9 (Owsap\'s rows in our columns; the base lines: server-patches/brakiwiki);',
         '--   81560 Tajemniczy Talizman+0 (yohara_items3.sql) gets its next item 81561 - refine_global.sql then gives',
         '--     the wiki\'s recipe 40429 (refine_global only moves an item whose refined_vnum is the step\'s result);',
         '--   23050-23089 Rekawice Weza (SILA/ODP/WIT/INT)+0..+9 - level 120, Obrona value1 16 + 2 x value5 (the wiki\'s',
         '--     15-17 .. 55-57), 3 sockets; the Will is the glove\'s base attribute (the overlay); refine 40384-40392.',
         '-- Each vnum was free in our world.item_proto (5 November 2026).',
         'SET NAMES utf8mb4;',
         'INSERT IGNORE INTO world.item_proto (%s) VALUES' % ','.join('`%s`' % c for c in Y.COLS),
         ',\n'.join(Y.sqlrow(i) for i in items if i['vnum'] != t0['vnum']) + ';',
         "UPDATE world.item_proto SET refined_vnum=%d WHERE vnum=%d AND refined_vnum=0;" % (t0['vnum'] + 1, t0['vnum'])]
    with open(SQL_OUT, 'w', encoding='utf-8', newline='\n') as f:
        f.write('\n'.join(L) + '\n')


def write_cube():
    L = ['# %s: GENERATED by tools/brakiwiki/gen_brakiwiki.py - do not edit. Appended to cube.txt by the' % M,
         '# Dockerfile; Mistrz Chi (%d, Dongan - quest rekawice opens the window): the pl-wiki "Wytwarzanie Rekawic" /' % CHI,
         '# "Rekawice Weza (...)": the Sung Ma glove of the same Will +0..+9, Kamien Ksiezycowy, Agat, Dwutlenek Tytanu,',
         '# %d Yang -> Rekawice Weza+0; the wiki gives 30-100%% - ours by the plus: %s. A failure takes' % (
             CUBE_FEE, '/'.join(str(p) for p in CUBE_PCT)),
         '# everything ("W przypadku niepowodzenia przedmioty przepadaja").', '']
    n = 0
    for g0, pl, src in GLOVES:
        for plus in range(10):
            L.append('# %s+0 <- %s+%d' % (Y.ascii_name(pl), {23000: 'Rekawice Mocy', 23010: 'Zwinne Rekawice',
                                                             23020: 'Pancerne Rekawice', 23030: 'Ochronne Rekawice'}[src],
                                          plus))
            L += ['section', 'npc\t%d' % CHI, 'item\t%d\t1' % (src + plus)]
            L += ['item\t%d\t%d' % m for m in CUBE_MATS]
            L += ['reward\t%d\t1' % g0, 'gold\t%d' % CUBE_FEE, 'percent\t%d' % CUBE_PCT[plus], 'end', '']
            n += 1
    assert n == 40 and CUBE_PCT[0] == 30 and CUBE_PCT[9] == 100
    os.makedirs(GAME_DIR, exist_ok=True)
    with open(CUBE_OUT, 'w', encoding='ascii', newline='\n') as f:
        f.write('\n'.join(L))


def write_drops():
    L = ['// %s: GENERATED by tools/brakiwiki/gen_brakiwiki.py - do not edit. The pl-wiki\'s drops of' % M,
         '// braki-yohara.md B9 our monsters lacked (groups MT2009_bwiki_<mob>, Type drop - merged with the mob\'s own).',
         '']
    for mob, name, rows in DROPS:
        L += ['Group\tMT2009_bwiki_%d' % mob, '{', '\tMob\t%d\t-- %s' % (mob, name), '\tType\tdrop']
        for k, (v, c, p, n) in enumerate(rows, 1):
            L.append('\t%d\t%d\t%d\t%s\t-- %s' % (k, v, c, ('%g' % p), n))
        L += ['}', '']
    os.makedirs(GAME_DIR, exist_ok=True)
    with open(DROP_OUT, 'w', encoding='ascii', newline='\n') as f:
        f.write('\n'.join(L))


def write_json(items):
    keys = ('vnum', 'name', 'locale_name', 'type', 'subtype', 'stack', 'weight', 'size', 'antiflag', 'flag',
            'wearflag', 'gold', 'shop_buy_price', 'refined_vnum', 'refine_set', 'magic_pct', 'specular', 'socket_pct',
            'limittype0', 'limitvalue0', 'limittype1', 'limitvalue1', 'applytype0', 'applyvalue0', 'applytype1',
            'applyvalue1', 'applytype2', 'applyvalue2', 'value0', 'value1', 'value2', 'value3', 'value4', 'value5')
    desc = dict((str(i['vnum']), '%d\t%s\t%s' % (i['vnum'], i['locale_name'], i['desc'])) for i in items)
    desc.update((str(v), '%d\t%s\t%s' % (v, n, d)) for v, (n, d) in DESC_ONLY.items())
    for d in desc.values():
        for bad in ('metin2', 'gameforge', 'oficjaln'):
            assert bad not in d.lower(), d
    out = {'items': [dict((k, i[k]) for k in keys) for i in items],
           'item_list': dict((str(i['vnum']), '%d\t%s\t%s' % (i['vnum'], i['list_type'], i['icon'])) for i in items),
           'itemdesc': desc,
           'glove_will': dict((str(g0), WIKI_WILL) for g0, _pl, _s in GLOVES)}
    with open(JSON_OUT, 'w', encoding='utf-8', newline='\n') as f:
        json.dump(out, f, ensure_ascii=False, indent=0)
        f.write('\n')


if __name__ == '__main__':
    main()
