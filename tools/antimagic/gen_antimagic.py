#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""gen_antimagic.py

MT2009_PLUS_ANTI_RESIST_MAGIC_V1: Kamien Duszy Antymagii (bron) and Bialy Kamien Antymagii (zbroja) - the owner, 28 October
2026: "Add the new soul stones. Drop like all the other stones." (the package "Anti Magic penetrate stone",
/opt/metin2/cache/antimagic). The owner's correction the same day: the stones work in PvP only and no bot seats them.

The package's vnums, values and slots: 28044 (WEAR_WEAPON) / 28045 (WEAR_BODY), +N = 28044 + 100*N / 28045 + 100*N for
+0..+9 (our other soul stones keep +6..+9 at 28g00+k - these keep the package's numbers at every grade, free in our
world.item_proto); APPLY_ANTI_RESIST_MAGIC 5/8/12/17/25/30/35/40/45/50 (item_proto.txt of the package) - our point 252
(server-patches/antimagic, POINT_ANTI_RESIST_MAGIC). The rest as our soul stones (28043 Kamien Duszy Przysp.):
ITEM_METIN, METIN_NORMAL, stack 200, flag 4, the prices 2 500 .. 80 000 for +0..+5 and 0 for +6..+9 (as our
28600..28913 - the blacksmith's steps make them), value5 = the stone's kind (no two of a kind in one item): 31 bron / 32 zbroja (17-30 are the 14 kinds).
Names after ours: "Kamien Duszy Antymagii+N" for the weapon, "Bialy Kamien Antymagii+N" for the armour (the package's
changelog 0.1: the armour stone is white).

Writes (all GENERATED - edit this file, run it again):
  linux-port/docker/mariadb/playerbot/antymagia.sql   world.item_proto (INSERT IGNORE), apply.sh
  tools/antimagic/antimagic.json                       the client's records, item_list, itemdesc
                                                       (client-patches/client-2.0.30/tools/antimagic)
The icons (client-2.0.30/root/icon/item/28044.tga, 28045.tga) are the package's, copied by hand.

Example: python3 tools/antimagic/gen_antimagic.py
"""
import io
import json
import os

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(os.path.dirname(HERE))
MARK = 'MT2009_PLUS_ANTI_RESIST_MAGIC_V1'
SQL_OUT = os.path.join(REPO, 'linux-port', 'docker', 'mariadb', 'playerbot', 'antymagia.sql')
JSON_OUT = os.path.join(HERE, 'antimagic.json')

POINT_ANTI_RESIST_MAGIC = 252
ITEM_METIN, METIN_NORMAL = 10, 0
WEARABLE_BODY, WEARABLE_WEAPON = 1, 16
VALUES = (5, 8, 12, 17, 25, 30, 35, 40, 45, 50)          # the package, +0..+9
PRICES = (2500, 5000, 10000, 20000, 40000, 80000, 0, 0, 0, 0)   # +6..+9: 0 as our 28600..28913
KINDS = (
    dict(base=28044, code='stone_anti_m_w', pl=u'Kamień Duszy Antymagii', wear=WEARABLE_WEAPON, kind=31,
         icon='icon/item/28044.tga',
         desc=u'Kamień duszy do broni. Twoje umiejętności magiczne pomijają część odporności na magię innego gracza '
              u'(tylko w walce z graczami). Sura korzysta z połowy tej wartości.'),
    dict(base=28045, code='stone_anti_m_a', pl=u'Biały Kamień Antymagii', wear=WEARABLE_BODY, kind=32,
         icon='icon/item/28045.tga',
         desc=u'Kamień duszy do zbroi. Twoje umiejętności magiczne pomijają część odporności na magię innego gracza '
              u'(tylko w walce z graczami). Sura korzysta z połowy tej wartości.'),
)
COLS = ('vnum', 'name', 'locale_name', 'type', 'subtype', 'stack', 'weight', 'size', 'antiflag', 'flag', 'wearflag',
        'immuneflag', 'gold', 'shop_buy_price', 'refined_vnum', 'refine_set', 'magic_pct', 'specular', 'socket_pct',
        'addon_type', 'limittype0', 'limitvalue0', 'limittype1', 'limitvalue1', 'applytype0', 'applyvalue0',
        'applytype1', 'applyvalue1', 'applytype2', 'applyvalue2', 'value0', 'value1', 'value2', 'value3', 'value4',
        'value5', 'socket0', 'socket1', 'socket2', 'socket3', 'socket4', 'socket5')


def items():
    out = []
    for g in range(10):
        for k in KINDS:
            out.append(dict(vnum=k['base'] + 100 * g, name='%s+%d' % (k['code'], g),
                            locale_name=u'%s+%d' % (k['pl'], g), type=ITEM_METIN, subtype=METIN_NORMAL, stack=200,
                            weight=0, size=1, antiflag=0, flag=4, wearflag=k['wear'], gold=PRICES[g],
                            shop_buy_price=PRICES[g], refined_vnum=0, refine_set=0, magic_pct=0, specular=0,
                            socket_pct=0, addon_type=0, limittype0=0, limitvalue0=0, limittype1=0, limitvalue1=0,
                            applytype0=POINT_ANTI_RESIST_MAGIC, applyvalue0=VALUES[g], applytype1=0, applyvalue1=0,
                            applytype2=0, applyvalue2=0, value0=0, value1=0, value2=0, value3=0, value4=0,
                            value5=k['kind']))
    return out


def sqlrow(i):
    out = []
    for c in COLS:
        if c == 'name':
            out.append("'%s'" % i['name'])
        elif c == 'locale_name':
            out.append("_cp1250 X'%s'" % i['locale_name'].encode('cp1250').hex().upper())
        elif c == 'immuneflag':
            out.append("''")
        elif c.startswith('socket') and c != 'socket_pct':
            out.append('-1')
        else:
            out.append(str(i[c]))
    return '(' + ','.join(out) + ')'


def main():
    its = items()
    for i in its:
        assert len(i['locale_name'].encode('cp1250')) < 32, i['locale_name']
    L = ['-- %s: Kamien Duszy Antymagii (bron, 28044 + 100*N) and Bialy Kamien Antymagii (zbroja, 28045 + 100*N),' % MARK,
         '-- +0..+9 - the owner, 28 October 2026 ("Add the new soul stones. Drop like all the other stones."; the package',
         '-- "Anti Magic penetrate stone"). GENERATED by tools/antimagic/gen_antimagic.py - do not edit, rerun it. Every start',
         '-- (apply.sh), idempotent: INSERT IGNORE - a row the operator changed (the Seban panel) is kept. applytype0 252 =',
         '-- POINT_ANTI_RESIST_MAGIC (server-patches/antimagic): a player\'s magic skill on another player ignores x points of',
         '-- the victim\'s magic resistance (a Sura x/2; PvP only). The rest as our soul stones (28043); value5 = the kind.',
         'SET NAMES utf8mb4;',
         'INSERT IGNORE INTO world.item_proto (%s) VALUES' % ','.join('`%s`' % c for c in COLS),
         ',\n'.join(sqlrow(i) for i in its) + ';']
    with io.open(SQL_OUT, 'w', encoding='ascii', newline='\n') as f:
        f.write(u'\n'.join(L) + u'\n')
    d = dict(items=its,
             item_list=dict((str(i['vnum']), '%d\tETC\t%s' % (i['vnum'], KINDS[g % 2]['icon']))
                            for g, i in enumerate(its)),
             itemdesc=dict((str(i['vnum']), u'%d\t%s\t%s' % (i['vnum'], i['locale_name'], KINDS[g % 2]['desc']))
                           for g, i in enumerate(its)))
    with io.open(JSON_OUT, 'w', encoding='utf-8', newline='\n') as f:
        f.write(json.dumps(d, indent=0, sort_keys=True, ensure_ascii=False) + u'\n')
    print('antimagic: %d items -> %s, %s' % (len(its), os.path.relpath(SQL_OUT, REPO), os.path.relpath(JSON_OUT, REPO)))


if __name__ == '__main__':
    main()
