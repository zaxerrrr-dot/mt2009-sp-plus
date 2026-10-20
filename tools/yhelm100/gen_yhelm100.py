#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""gen_yhelm100.py [--owsap DIR] [--gf DIR]

MT2009_PLUS_HELM100_V1: the level-100 helmets (the owner, 15 October 2026) as the pl-wiki gives them ("Hełmy na 100
poziom", each helmet's page, "Strażnik Smoków Jaharr", the materials' pages) with the official vnums and numbers of
Owsap v6.2.6 (Server/Server/db/item_proto.txt), the Polish names of its Polish client and the icons of the GF 26.1.11
client - the method of tools/ygloves/gen_ygloves.py:

  "...Smoków" - the attack helmets (Mag./krótkodys. atak 1..8% = APPLY_MELEE_MAGIC_ATTBONUS_PER, point 132):
    12690-12699 Stalowy Hełm Smoków+0..+9 (Wojownik)    12700-12709 Smoczy Kaptur+0..+9 (Ninja)
    12710-12719 Pancerny Hełm Smoków+0..+9 (Sura)       12720-12729 Smoczy Kapelusz+0..+9 (Szaman)
  "...Dragona" - the defensive helmets (Odp. na Obr. Um. 1..10% = APPLY_SKILL_DEFEND_BONUS, point 123):
    12730-12739 Stalowy Hełm Dragona+0..+9              12740-12749 Kaptur Dragona+0..+9
    12750-12759 Pancerny Hełm Dragona+0..+9             12760-12769 Kapelusz Dragona+0..+9
  level 100, Obrona 23..101 (value1 15 + 2 x value5 4..43 - the wiki's column), refined with our refine_proto
  22740-22748 = Owsap's 343-351 (MT2009_PLUS_REFINE_DATA_V1, the owner's upgrade sheet of 20 October: 1 200 .. 150 000
  Yang, 90..10%, from +4 the materials and Kosc Palca 30193 from +6 - our 343-351 are the level-80 helmets' rows
  without materials, which V1 shared); the wiki's bonus column is the item's
  apply - it differs from Owsap's only for the Dragona helmets +2 and +4..+6 (wiki 2/3/3/4%, Owsap 1/3/4/5%): the
  wiki's numbers are taken (the owner: "jak na wiki"). The Lycan's (12770-12779, 21550-21559) are left out.
  Materials (ITEM_MATERIAL, stackable): 30620 Czerwony Smoczy Róg, 30621 Czerwona Smocza Łuska, 30622 Plan Zbroi: Hełm,
  30630 Skrzydła Smoka.
  NPC 20421 Strażnik Smoków Jaharr (old_magic_M2 - the client's npclist has the race; the model:
  client-patches/client-2.0.30/tools/yhelm100) - our NPC numbers (tools/yohara_maps/gen_ymaps_sql.py npc_row; Owsap's
  mob_proto has no row for him). He makes the helmets (quest helm100) and stands in Yongan, Joan and Pyungmoo
  (linux-port/docker/game/Dockerfile).

Writes (all GENERATED - edit this file, run it again):
  linux-port/docker/mariadb/playerbot/yohara_helm100.sql     world.item_proto / mob_proto (INSERT IGNORE)
  tools/yhelm100/yhelm100_items.json                         the client's item records, item_list, itemdesc rows and
                                                             Jaharr's mob row (client-patches/client-2.0.30/tools/yhelm100)
  linux-port/docker/game/cube.helm100.txt                    Jaharr's cube window (MT2009_PLUS_HELM100_CUBE_V1, round
                                                             15.10 #3): 40 recipes, appended to cube.txt by the Dockerfile
  client-patches/client-2.0.30/root/icon/item/<icon>.tga     the GF icons (12690/12700/12710/12720 - the Dragona helmets
                                                             share them as on GF -, 30620, 30621, 30630; 30622.tga is
                                                             in our icon pack already)

Example: python3 tools/yhelm100/gen_yhelm100.py
"""
import argparse
import json
import os
import re
import shutil
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(os.path.dirname(HERE))
sys.path.insert(0, os.path.join(REPO, 'tools', 'yohara_items'))
sys.path.insert(0, os.path.join(REPO, 'tools', 'yohara_maps'))
import gen_yitems as Y  # noqa: E402  (the item row writer, the engine's flag numbers)
import gen_ymaps_sql as YM  # noqa: E402  (the mob row columns, our NPC numbers)

M = 'MT2009_PLUS_HELM100_V1'
SQL_OUT = os.path.join(REPO, 'linux-port', 'docker', 'mariadb', 'playerbot', 'yohara_helm100.sql')
JSON_OUT = os.path.join(HERE, 'yhelm100_items.json')
CUBE_OUT = os.path.join(REPO, 'linux-port', 'docker', 'game', 'cube.helm100.txt')
ICON_OUT = os.path.join(REPO, 'client-patches', 'client-2.0.30', 'root', 'icon', 'item')
HAVE_ICONS = set(('30622.tga',))            # in our icon pack (the base client)

ARMOR, HEAD, MATERIAL = 2, 1, 5
WEAR_HEAD = 2
ANTI = {'ANTI_MUSA': 4, 'ANTI_ASSASSIN': 8, 'ANTI_SURA': 16, 'ANTI_MUDANG': 32,
        'ANTI_WOLFMAN': 0}                  # no Lycan here; bit 18 is also ITEM_ANTIFLAG_DELETE in our engine
FLAGS = {'ITEM_TUNABLE': 1, 'ITEM_STACKABLE': 4}
LIMITS = {'LIMIT_NONE': 0, 'LEVEL': 1}
POINT_SKILL_DEFEND_BONUS, POINT_MELEE_MAGIC_ATT_BONUS_PER = 123, 132     # common/length.h (applies are points here)
APPLY = {'APPLY_SKILL_DEFEND_BONUS': POINT_SKILL_DEFEND_BONUS,
         'APPLY_MELEE_MAGIC_ATTBONUS_PER': POINT_MELEE_MAGIC_ATT_BONUS_PER}
OWSAP_REFINE0 = 343         # Owsap's refine_proto 343-351 (db/data/player.sql) - the helmets' official steps
REFINE0 = 22740             # ours 22740-22748 (MT2009_PLUS_REFINE_DATA_V1); our 343-351 are the level-80 helmets'
OLD_REFINE0 = 343           # V1's refine_set, moved to ours by an UPDATE on a world made before

# (base vnum, Polish name, family, input helmet base vnum) - the class follows the input helmet
HELMETS = [(12690, 'Stalowy Hełm Smoków', 'smokow', 12280), (12700, 'Smoczy Kaptur', 'smokow', 12400),
           (12710, 'Pancerny Hełm Smoków', 'smokow', 12540), (12720, 'Smoczy Kapelusz', 'smokow', 12680),
           (12730, 'Stalowy Hełm Dragona', 'dragona', 12280), (12740, 'Kaptur Dragona', 'dragona', 12400),
           (12750, 'Pancerny Hełm Dragona', 'dragona', 12540), (12760, 'Kapelusz Dragona', 'dragona', 12680)]
# the pl-wiki's "Bonus2" columns (+0..+9) and "Bonus1" (Obrona)
WIKI_BONUS = {'smokow': [1, 1, 2, 2, 3, 3, 4, 5, 6, 8], 'dragona': [1, 1, 2, 2, 3, 3, 4, 6, 8, 10]}
WIKI_DEF = [23, 27, 31, 41, 51, 61, 71, 81, 91, 101]
ICON_OF = {'smokow': 0, 'dragona': -40}     # GF item_list: 12730 -> 12690.tga ... 12760 -> 12720.tga
MATERIALS = [(30620, 'Czerwony Smoczy Róg'), (30621, 'Czerwona Smocza Łuska'), (30622, 'Plan Zbroi: Hełm'),
             (30630, 'Skrzydła Smoka')]
JAHARR = (20421, 'Dragon Watcher Jaharr', 'Strażnik Smoków Jaharr')
# MT2009_PLUS_HELM100_CUBE_V1: Jaharr's recipes (the numbers of quest helm100, the en-wiki's "Item Refinement" chances)
CUBE_FEE = 1000000
INPUT_NAME = {12280: 'Helm Mistrza Wojny', 12400: 'Pajeczy Kaptur', 12540: 'Magiczny Helm', 12680: 'Kapelusz Duszy'}
CUBE_NEEDS = {'smokow': [(30620, 5), (30621, 5), (30622, 10)],
              'dragona': [(30620, 5), (30621, 5), (30622, 5), (30630, 3)]}
CUBE_PCT = {'smokow': [30, 40, 50, 60, 70], 'dragona': [10, 20, 30, 40, 50]}     # the input's +5..+9


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
    items, icons = [], {}

    def base(vnum, o, name, text, **kw):
        d = dict(vnum=vnum, src=vnum, status=Y.ST, name=Y.ascii_name(name), locale_name=name, type=0, subtype=0,
                 stack=1, weight=0, size=int(o['Size']), antiflag=Y.flags(o['AntiFlags'], ANTI, 'antiflag'),
                 flag=Y.flags(o['Flags'], FLAGS, 'flag'), wearflag=0, gold=int(o['ShopBuyPrice']),
                 shop_buy_price=int(o['ShopSellPrice']), refined_vnum=0, refine_set=0,
                 magic_pct=int(o['AlterToMagicItemPercent']), specular=int(o['Specular']),
                 socket_pct=int(o['GainSocketPercent']), addon_type=0,
                 limittype0=LIMITS[o['LimitType0']], limitvalue0=int(o['LimitValue0']),
                 limittype1=LIMITS[o['LimitType1']], limitvalue1=int(o['LimitValue1']),
                 applytype0=0, applyvalue0=0, applytype1=0, applyvalue1=0, applytype2=0, applyvalue2=0,
                 desc=text, **dict(('value%d' % i, int(o['Value%d' % i])) for i in range(6)))
        d.update(kw)
        assert len(d['locale_name'].encode('cp1250')) <= 24, d['locale_name']
        return d

    notes = []
    for h0, pl, fam, src in HELMETS:
        for lv in range(10):
            v = h0 + lv
            o = proto[v]
            assert o['Type'] == 'ITEM_ARMOR' and o['SubType'] == 'ARMOR_HEAD' and o['WearFlags'] == 'WEAR_HEAD', v
            assert o['LimitType0'] == 'LEVEL' and int(o['LimitValue0']) == 100, v
            assert o['ApplyType0'] in APPLY and (APPLY[o['ApplyType0']] == POINT_SKILL_DEFEND_BONUS) == (fam == 'dragona'), v
            # the class of the input helmet (Owsap's AntiFlags of both)
            assert o['AntiFlags'] == proto[src]['AntiFlags'], (v, o['AntiFlags'], proto[src]['AntiFlags'])
            assert int(o['Value1']) + 2 * int(o['Value5']) == WIKI_DEF[lv], (v, o['Value1'], o['Value5'])
            assert int(o['RefinedVnum']) == (v + 1 if lv < 9 else 0), v
            assert int(o['RefineSet']) == (OWSAP_REFINE0 + lv if lv < 9 else 0), (v, o['RefineSet'])
            pl_owsap = desc[v][0].replace(' +', '+')
            assert pl_owsap == '%s+%d' % (pl, lv), (v, pl_owsap)
            bonus = WIKI_BONUS[fam][lv]
            if int(o['ApplyValue0']) != bonus:
                notes.append('%d: %s %d%% (Owsap %s)' % (v, o['ApplyType0'], bonus, o['ApplyValue0']))
            icon = '%d.tga' % (h0 + ICON_OF[fam])
            items.append(base(v, o, '%s+%d' % (pl, lv), desc[v][1], type=ARMOR, subtype=HEAD, wearflag=WEAR_HEAD,
                              refined_vnum=v + 1 if lv < 9 else 0, refine_set=REFINE0 + lv if lv < 9 else 0,
                              applytype0=APPLY[o['ApplyType0']], applyvalue0=bonus,
                              icon='icon/item/%s' % icon, list_type='ARMOR'))
            icons[icon] = icon
    for v, pl in MATERIALS:
        o = proto[v]
        assert o['Type'] == 'ITEM_MATERIAL' and 'ITEM_STACKABLE' in o['Flags'], v
        assert desc[v][0] == pl, (v, desc[v][0])
        items.append(base(v, o, pl, desc[v][1], type=MATERIAL, subtype=0, stack=200,
                          icon='icon/item/%d.tga' % v, list_type='ETC'))
        icons['%d.tga' % v] = '%d.tga' % v
    byv = dict((i['vnum'], i) for i in items)
    assert len(byv) == len(items) == 84
    mob = YM.npc_row(JAHARR[0], JAHARR[1], JAHARR[2], '')
    assert len(mob) == len(YM.COLS)
    refine = {}
    with open(os.path.join(a.owsap, 'Server/Server/db/data/player.sql'), encoding='latin-1') as f:
        for m in re.finditer(r'INSERT INTO `refine_proto` VALUES \(([^)]*)\);', f.read()):
            p = [int(x) for x in m.group(1).split(',')]
            refine[p[0]] = p
    refines = []
    for lv in range(9):
        r = refine[OWSAP_REFINE0 + lv]
        assert len(r) == 15 and r[12] == r[13] == 0, r
        refines.append([REFINE0 + lv] + r[1:])
    write_sql(items, mob, notes, refines)
    write_json(items, mob)
    write_cube(byv)
    copy_icons(icons, a.gf)
    print('items %d (helmets 80, materials 4), Jaharr %d; wiki bonus over Owsap: %d' % (len(items), JAHARR[0],
                                                                                           len(notes)))
    for n in notes:
        print('  ' + n)


def write_sql(items, mob, notes, refines):
    L = ['-- %s: the level-100 helmets (the owner, 15 October 2026; pl-wiki "Hełmy na 100 poziom") - GENERATED by' % M,
         '-- tools/yhelm100/gen_yhelm100.py, do not edit, rerun it. Every start (apply.sh, after the Yohara item files),',
         '-- idempotent: INSERT IGNORE - a row the operator changed is kept. Source: Owsap v6.2.6 db/item_proto.txt (the',
         '-- official vnums and numbers) in our columns, the Polish names of its Polish client:',
         '--   12690-12729 Stalowy Hełm Smoków / Smoczy Kaptur / Pancerny Hełm Smoków / Smoczy Kapelusz +0..+9',
         '--     (Mag./krótkodys. atak, point 132), 12730-12769 Stalowy Hełm / Kaptur / Pancerny Hełm / Kapelusz Dragona',
         '--     +0..+9 (Odp. na Obr. Um., point 123); level 100, refine_proto %d-%d = Owsap\'s 343-351' % (REFINE0, REFINE0 + 8),
         '--     (MT2009_PLUS_REFINE_DATA_V1; V1 had our 343-351, the level-80 helmets\' rows without materials);',
         '--     the bonus as the wiki gives it where Owsap differs: %s;' % ', '.join(n.split(':')[0] for n in notes),
         '--   30620 Czerwony Smoczy Róg, 30621 Czerwona Smocza Łuska, 30622 Plan Zbroi: Hełm, 30630 Skrzydła Smoka;',
         '--   20421 Strażnik Smoków Jaharr (an NPC - our NPCs\' numbers): quest helm100 makes the helmets.',
         '-- Each vnum was free in our world.item_proto / mob_proto (15 October 2026). No Lycan (12770-12779, 21550).',
         'SET NAMES utf8mb4;',
         'INSERT IGNORE INTO world.item_proto (%s) VALUES' % ','.join('`%s`' % c for c in Y.COLS),
         ',\n'.join(Y.sqlrow(i) for i in items) + ';',
         'INSERT IGNORE INTO world.mob_proto (%s) VALUES' % ','.join('`%s`' % c for c in YM.COLS),
         '(' + ','.join(str(x) for x in mob) + ');',
         '-- MT2009_PLUS_REFINE_DATA_V1: the helmets\' own steps; a world made before moves from 343-351 (only a row',
         '-- still on V1\'s step, so a refine_set the operator changed stays)',
         'INSERT IGNORE INTO world.refine_proto (id,vnum0,count0,vnum1,count1,vnum2,count2,vnum3,count3,vnum4,count4,'
         'cost,src_vnum,result_vnum,prob) VALUES',
         ',\n'.join('(' + ','.join(str(x) for x in r) + ')' for r in refines) + ';',
         'UPDATE world.item_proto SET refine_set = %d + vnum %% 10 WHERE vnum BETWEEN %d AND %d AND vnum %% 10 < 9'
         ' AND refine_set = %d + vnum %% 10;' % (REFINE0, HELMETS[0][0], HELMETS[-1][0] + 9, OLD_REFINE0)]
    with open(SQL_OUT, 'w', encoding='utf-8', newline='\n') as f:
        f.write('\n'.join(L) + '\n')


def write_cube(byv):
    """MT2009_PLUS_HELM100_CUBE_V1 (round 15.10 #3, the owner: "tak jak u innych NPC, np. Mistrz -> Wytwarzanie pasow"):
    Jaharr's cube window - one recipe an input helmet +5..+9 and a kind. The engine shows the five pluses of one
    helmet and kind as one row ("+5 or +6 ... or +9", Cube_InformationInitialize), so the window has 8 rows.
    The Dragona recipes come first: a window holding both kinds' materials (the wings too) makes the Dragona helmet -
    FN_find_cube takes the first recipe the window satisfies. "fail_keep" (server-patches/yhelm100): a failed Dragona
    attempt leaves the helmet."""
    L = ['# %s: GENERATED by tools/yhelm100/gen_yhelm100.py - do not edit. Appended to cube.txt by the' % M,
         '# Dockerfile; quest helm100 opens the window of Straznik Smokow Jaharr (20421). MT2009_PLUS_HELM100_CUBE_V1',
         '# (round 15.10 #3): a level-80 helmet +5..+9 -> the level-100 helmet +0, %d Yang:' % CUBE_FEE,
         '#   Dragona (defence): 5 horns, 5 scales, 5 plans, 3 wings, 10-50% by the plus - a failure keeps the helmet',
         '#     (fail_keep, server-patches/yhelm100); listed first, so a window with the wings makes a Dragona helmet;',
         '#   Smokow (attack): 5 horns, 5 scales, 10 plans, 30-70% by the plus - a failure takes the helmet too.',
         '']
    n = 0
    for fam in ('dragona', 'smokow'):
        for h0, pl, f, src in HELMETS:
            if f != fam:
                continue
            for plus in range(5, 10):
                inp = src + plus
                L.append('# %s+0 <- %s+%d' % (Y.ascii_name(pl), INPUT_NAME[src], plus))
                L += ['section', 'npc\t20421', 'item\t%d\t1' % inp]
                L += ['item\t%d\t%d' % m for m in CUBE_NEEDS[fam]]
                L += ['reward\t%d\t1' % h0, 'gold\t%d' % CUBE_FEE, 'percent\t%d' % CUBE_PCT[fam][plus - 5]]
                if fam == 'dragona':
                    L.append('fail_keep\t%d' % inp)
                L += ['end', '']
                n += 1
    assert n == 40
    with open(CUBE_OUT, 'w', encoding='ascii', newline='\n') as f:
        f.write('\n'.join(L))


def py_value(x):
    s = str(x)
    if s.startswith("'") and s.endswith("'"):
        return s[1:-1].replace("\\'", "'").replace('\\\\', '\\')
    try:
        return int(s)
    except ValueError:
        return float(s)


def write_json(items, mob):
    keys = ('vnum', 'name', 'locale_name', 'type', 'subtype', 'stack', 'weight', 'size', 'antiflag', 'flag',
            'wearflag', 'gold', 'shop_buy_price', 'refined_vnum', 'refine_set', 'magic_pct', 'specular', 'socket_pct',
            'limittype0', 'limitvalue0', 'limittype1', 'limitvalue1', 'applytype0', 'applyvalue0', 'applytype1',
            'applyvalue1', 'applytype2', 'applyvalue2', 'value0', 'value1', 'value2', 'value3', 'value4', 'value5')
    out = {'items': [dict((k, i[k]) for k in keys) for i in items],
           'item_list': dict((str(i['vnum']), '%d\t%s\t%s' % (i['vnum'], i['list_type'], i['icon'])) for i in items),
           'itemdesc': dict((str(i['vnum']), '%d\t%s\t%s' % (i['vnum'], i['locale_name'], Y.client_desc(i)))
                            for i in items),
           'mobs': [dict(zip(YM.COLS, (py_value(x) for x in mob)))],
           'npclist_have': {str(JAHARR[0]): 'old_magic_M2'}}
    with open(JSON_OUT, 'w', encoding='utf-8', newline='\n') as f:
        json.dump(out, f, ensure_ascii=False, indent=0)
        f.write('\n')


def copy_icons(icons, gf):
    os.makedirs(ICON_OUT, exist_ok=True)
    for dst, src in sorted(icons.items()):
        if dst in HAVE_ICONS:
            continue
        s = os.path.join(gf, 'icon', 'item', src)
        assert os.path.isfile(s), s
        shutil.copyfile(s, os.path.join(ICON_OUT, dst))


if __name__ == '__main__':
    main()
