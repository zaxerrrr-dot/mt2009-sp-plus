#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""gen_kola_items.py [--owsap DIR] [--gf DIR]

MT2009_PLUS_KOLA_ITEMS_V1: the ItemShop wheels' prizes the server lacked (the owner, 20 October 2026):

  25046 Kamien Rytualny   the global server's Ritual Stone (25042 there - our 25042 is Magiczny Kamien, so it lives at
                          25046 here): a refine scroll (ITEM_USE / USE_TUNING) with the Magic Stone's protection
                          (value0 1 = NO_REDUCTION_WHEN_FAIL_SCROLL: a failure neither destroys nor downgrades) and
                          +15% (value1 - Owsap v6.2.6 BLESSING_STONE: prob + 15, keep grade), only on an item above
                          level 80 (server-patches/kolaprzedmioty); no drop / give / shop (Owsap's flags), stacks.
                          Name and text: Owsap's Polish client; the icon: GF 26.1.11 icon/item/25042.tga.

and the Polish names of Smoczy Plomien (B) / Smoczy Plomien (100700/100701; the owner, 20 October: they were
"Flame of the Dragon (B)" / "Flame of the Dragon" in world.item_proto) - item_proto.mt2009plus.sql has them now, and an
UPDATE renames a world that still has the English ones (a name the operator changed is kept).

The wheels' "Blogoslawienstwo" is our 71052 (Blogoslaw. Przedmiotu - it changes the 6th/7th bonus; the owner,
20 October) - no new item.

Writes (all GENERATED - edit this file, run it again):
  linux-port/docker/mariadb/playerbot/kola_items.sql        world.item_proto (INSERT IGNORE) + the two renames
  tools/kola_items/kola_items.json                          the client's records, item_list, itemdesc
  client-patches/client-2.0.30/root/icon/item/25046.tga     the GF icon

Example: python3 tools/kola_items/gen_kola_items.py
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

SQL_OUT = os.path.join(REPO, 'linux-port', 'docker', 'mariadb', 'playerbot', 'kola_items.sql')
JSON_OUT = os.path.join(HERE, 'kola_items.json')
ICON_OUT = os.path.join(REPO, 'client-patches', 'client-2.0.30', 'root', 'icon', 'item')

RITUAL_STONE = 25046           # server-patches/kolaprzedmioty/gen_edits.py
RITUAL_STONE_SRC = 25042       # the global / Owsap vnum
USE_TUNING = 2
NO_REDUCTION_WHEN_FAIL_SCROLL = 1
RITUAL_BONUS = 15              # Owsap BLESSING_STONE: MINMAX(1, prob + 15, 100), keep grade
RENAMES = ((100700, u'Flame of the Dragon (B)', u'Smoczy Płomień (B)'),
           (100701, u'Flame of the Dragon', u'Smoczy Płomień'))


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

    o = proto[RITUAL_STONE_SRC]
    assert (o['Type'], o['SubType'], o['Value0']) == ('ITEM_USE', 'USE_TUNING', '7'), o   # BLESSING_STONE
    pl, text = desc[RITUAL_STONE_SRC]
    assert pl == u'Kamień Rytualny', pl
    assert u'powyżej poziomu 80' in text, text
    items = [dict(vnum=RITUAL_STONE, src=RITUAL_STONE_SRC, status=Y.ST, name=Y.ascii_name(pl), locale_name=pl,
                  type=Y.TYPES['ITEM_USE'], subtype=USE_TUNING, stack=200, weight=0, size=1,
                  antiflag=Y.flags(o['AntiFlags'], Y.ANTI, 'antiflag'), flag=Y.flags(o['Flags'], Y.FLAGS, 'flag'),
                  wearflag=0, gold=0, shop_buy_price=0, refined_vnum=0, refine_set=0, magic_pct=0, specular=0,
                  socket_pct=0, addon_type=0, limittype0=0, limitvalue0=0, limittype1=0, limitvalue1=0,
                  applytype0=0, applyvalue0=0, applytype1=0, applyvalue1=0, applytype2=0, applyvalue2=0,
                  value0=NO_REDUCTION_WHEN_FAIL_SCROLL, value1=RITUAL_BONUS, value2=0, value3=0, value4=0, value5=0,
                  desc=text + u' Zwiększa szansę na ulepszenie o 15%.',
                  icon='icon/item/%d.tga' % RITUAL_STONE, list_type='ETC')]
    write_sql(items)
    write_json(items + flame_records())
    copy_icons({'%d.tga' % RITUAL_STONE: '%d.tga' % RITUAL_STONE_SRC}, a.gf)   # 100700.tga is in the base client's root pack
    print('items %d (Kamien Rytualny %d), renames %d' % (len(items), RITUAL_STONE, len(RENAMES)))


# MT2009_PLUS_KOLA_ITEMS_V2 (the owner, 21 October 2026: "to jest chyba zly plomien smoka, musi byc ten co faktycznie
# dziala do naszej alchemii"): 100701 is the right one - MATERIAL_DS_CHANGE_ATTR, the material the Alchemy window's
# bonus change (DSManager::DoChangeAttribute) takes; 100700 is its bound twin. But the client's item_proto lacked both,
# so the exe made them up (GameLib/ItemManager.cpp, aDragonSoulUtilityItems) as "Plomien Smoka(+)" in UTF-8 - a
# garbled name in game. The client gets the server's records (item_proto.mt2009plus.sql) and a text.
FLAME_DESC = u'Zmienia bonusy mitycznego Smoczego Kamienia w oknie Smoczej Alchemii (zakładka zmiany bonusów).'


def flame_records():
    import ast
    src = os.path.join(REPO, 'linux-port', 'docker', 'mariadb', 'playerbot', 'item_proto.mt2009plus.sql')
    out = []
    for line in open(src, encoding='utf-8'):
        for vnum, en, pl in RENAMES:
            if line.startswith('(%d,' % vnum):
                row = dict(zip(Y.COLS, ast.literal_eval(line.strip().rstrip(',;'))))
                assert (row['type'], row['subtype'], row['locale_name']) == (5, 8, pl), row
                row.update(status=Y.ST, desc=FLAME_DESC, icon='icon/item/100700.tga', list_type='ETC')
                out.append(row)
    assert len(out) == len(RENAMES), out
    return out


def write_sql(items):
    L = ['-- MT2009_PLUS_KOLA_ITEMS_V1: the ItemShop wheels\' prizes the server lacked (the owner, 20 October 2026). GENERATED',
         '-- by tools/kola_items/gen_kola_items.py - do not edit, rerun it. Every start (apply.sh), idempotent: INSERT IGNORE -',
         '-- a row the operator changed is kept. Kamien Rytualny (25046; the global 25042 is our Magiczny Kamien): Owsap v6.2.6',
         '-- db/item_proto.txt (its flags) and its Polish client (name, text); the Magic Stone\'s protection (value0 1) with +15%',
         '-- (value1), only above level 80 (server-patches/kolaprzedmioty). 25046 was free in our world (20 October 2026).',
         '-- Smoczy Plomien (B) / Smoczy Plomien (100700/100701): their Polish names where the world still has the English ones.',
         'SET NAMES utf8mb4;',
         'INSERT IGNORE INTO world.item_proto (%s) VALUES' % ','.join('`%s`' % c for c in Y.COLS),
         ',\n'.join(Y.sqlrow(i) for i in items) + ';']
    for vnum, en, pl in RENAMES:
        L.append("UPDATE world.item_proto SET locale_name=_cp1250 X'%s' WHERE vnum=%d AND locale_name=_cp1250 X'%s';"
                 % (pl.encode('cp1250').hex().upper(), vnum, en.encode('cp1250').hex().upper()))
    with open(SQL_OUT, 'w', encoding='utf-8', newline='\n') as f:
        f.write('\n'.join(L) + '\n')


def write_json(items):
    keys = ('vnum', 'name', 'locale_name', 'type', 'subtype', 'stack', 'weight', 'size', 'antiflag', 'flag',
            'wearflag', 'gold', 'shop_buy_price', 'refined_vnum', 'refine_set', 'magic_pct', 'specular', 'socket_pct',
            'limittype0', 'limitvalue0', 'limittype1', 'limitvalue1', 'applytype0', 'applyvalue0', 'applytype1',
            'applyvalue1', 'applytype2', 'applyvalue2', 'value0', 'value1', 'value2', 'value3', 'value4', 'value5')
    out = {'items': [dict((k, i[k]) for k in keys) for i in items],
           'item_list': dict((str(i['vnum']), '%d\t%s\t%s' % (i['vnum'], i['list_type'], i['icon'])) for i in items),
           'itemdesc': dict((str(i['vnum']), '%d\t%s\t%s' % (i['vnum'], i['locale_name'], Y.client_desc(i)))
                            for i in items)}
    with open(JSON_OUT, 'w', encoding='utf-8', newline='\n') as f:
        json.dump(out, f, ensure_ascii=False, indent=0)
        f.write('\n')


def copy_icons(icons, gf):
    os.makedirs(ICON_OUT, exist_ok=True)
    for dst, src in sorted(icons.items()):
        s = os.path.join(gf, 'icon', 'item', src)
        assert os.path.isfile(s), s
        shutil.copyfile(s, os.path.join(ICON_OUT, dst))


if __name__ == '__main__':
    main()
