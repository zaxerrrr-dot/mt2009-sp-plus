#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""gen_yitems4.py [--owsap DIR] [--gf DIR]

MT2009_PLUS_YOHARA_ITEMS4_V1: the Yohara items the owner asked for on 14 October 2026 (cache/yohara/decyzje.md
"14.10 rano": "Przedmioty z wiki: Kamien Metin z Yohara, bransolety jadeitowe, Platynowa Skrzynia + Klucz - dodac wg
wiki; Symbol Krola Przepowiedni - NIE. Przebudzona Ksiega Zwierza = nasza skrzynka umiejetnosci peta"), as the
pl-wiki gives them, with the official vnums and numbers of Owsap v6.2.6 (Server/Server/db/item_proto.txt, refine_proto
of db/data/player.sql), the Polish names and descriptions of its Polish client and the icons of the GF 26.1.11
client - the method of tools/yohara_items/gen_yitems.py:

  14580-14589 Obrecz Jadeitu Mgly+0..+9    level 105 bracelets; Owsap's two APPLY_RANDOM lines - the wiki's "Precyzja"
  14590-14599 Obrecz Jadeitu Slonca+0..+9  (no precision point in our engine: left out) and the Sung Ma Will of the
  14600-14609 Obrecz Jadeitu Nocy+0..+9    bracelet (Mgly ODP, Slonca INT, Nocy WIT, Dymu SILA) - the 6th bonus slot,
  14610-14619 Obrecz Jadeitu Dymu+0..+9    rolled when one is made, carried by a refine (server-patches/obreczjadeitu,
                                           MT2009_PLUS_JADE_BRACELET_V1); refined at the blacksmith with Owsap's
                                           refine rows 810-818 (= the wiki's costs and plates) - ours 22701-22709;
                                           from Skrzynia z Bransoletka (83067) and Mistrz Chi in Dongan (quest
                                           yohara_mapy4: the wiki's "Wytwarzanie Bransolet" - 10 jade, 25/30 plates,
                                           2 Skazony Rdzen / 5 Kiel Argosa / 10 Luska Argosa, 1 000 000 Yang, 30%;
                                           Gaya we do not have);
  16580-16619 Kolia Jadeitu Mgly / Slonca / Nocy / Dymu+0..+9     MT2009_PLUS_JADE_JEWELLERY_V1 (the owner, 14 October:
  17570-17609 Klipsy Jadeitu Mgly / Slonca / Nocy / Dymu+0..+9    "naszyjniki i kolczyki jadeitowe wg wiki"): the
                                           necklaces and earrings of the same jade - level 105, Owsap's same two
                                           APPLY_RANDOM lines (server-patches/obreczjadeitu2: Precyzja + the Will of
                                           the jade, the wiki's ranges of each kind), the same refine rows 22701-22709
                                           (the wiki: 250 000 .. 650 000 Yang, the same plates and pearls) and the same
                                           recipes at Mistrz Chi (pl-wiki "Wytwarzanie Naszyjnikow" / "Wytwarzanie
                                           Kolczykow", quest yohara_mapy4); in the chests the owner's sheet of 15
                                           October 2026 names (tools/yohara_chestdrops, MT2009_PLUS_CHEST_DROPS_V1);
  72339 Kamien Metin z Yohara             a quest-use item (quest yohara_mapy4): a Yohara Metin (level 120+) next
                                           to the user, on a Yohara Sung Ma map, from the 1st Champion Level; from
                                           Skrzynia z Bransoletka and the Id. Skrzynie Kolczykow / Naszyjniku;
  83055 Plat. Skrzynia Skarbow / 83056 Plat. Klucz do Skrz. Sk.
                                           treasure box and key of the same value (5) - the key opens the box
                                           (char_item.cpp, as 83067 / 83054); from Losowa Skrzynia Skarbow / Los.
                                           Klucz do Skrz. Sk. (the second batch's chests); its contents the wiki's;
  95737 Przeb. Ksiega Zwierza              the wiki's item (official 55007 - ours is Transporter z Petem there) with
                                           the use of our pet skill book box (Skrzynia Ksiag Peta 55009,
                                           playerbot_newpet.h UseBookChest: one of the 22 books 55010-55031 at random)
                                           - a gift box of those 22 books; from the war chiefs the wiki names.

Writes (all GENERATED - edit this file, run it again):
  linux-port/docker/mariadb/playerbot/yohara_items4.sql                world.item_proto + refine_proto (INSERT IGNORE)
  linux-port/docker/game/yohara_maps4/special_item_group.yohara_items4.txt   83055's and 95737's contents
  tools/yohara_maps4/yohara_items4.json                                the client's records, item_list, itemdesc
  client-patches/client-2.0.30/root/icon/item/<icon>.tga               the GF icons (renamed where ours differ)
The drops and the chests of the batches before name these vnums: tools/yohara_items/gen_yitems2.py,
tools/yohara_maps3/gen_yitems3.py, tools/yohara_maps4/gen_ymaps4.py (ITEMS4 below).

Example: python3 tools/yohara_maps4/gen_yitems4.py
"""
import argparse
import json
import os
import re
import shutil
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(os.path.dirname(HERE))
sys.path.insert(0, os.path.join(REPO, 'tools', 'yohara_chestdrops'))
import chestdrops as CD  # noqa: E402  (MT2009_PLUS_CHEST_DROPS_V1: the chests' rows)
sys.path.insert(0, os.path.join(REPO, 'tools', 'yohara_items'))
import gen_yitems as Y  # noqa: E402  (the engine's numbers, the row writer)

SQL_OUT = os.path.join(REPO, 'linux-port', 'docker', 'mariadb', 'playerbot', 'yohara_items4.sql')
SIG_OUT = os.path.join(REPO, 'linux-port', 'docker', 'game', 'yohara_maps4', 'special_item_group.yohara_items4.txt')
JSON_OUT = os.path.join(HERE, 'yohara_items4.json')
ICON_OUT = os.path.join(REPO, 'client-patches', 'client-2.0.30', 'root', 'icon', 'item')

ST = Y.ST
TYPES = dict(Y.TYPES, ITEM_TREASURE_BOX=20, ITEM_TREASURE_KEY=21)
SUBTYPES = dict(Y.SUBTYPES, ARMOR_WRIST=3, ARMOR_NECK=5, ARMOR_EAR=6)
WEAR = dict(Y.WEAR, WEAR_WRIST=8, WEAR_NECK=32, WEAR_EAR=64)
REFINE_ID0 = 22701          # ours (Owsap's 810-818 are other rows here; the set system's are 22600-22659)

BRACELETS = [(14580, 'Mgły'), (14590, 'Słońca'), (14600, 'Nocy'), (14610, 'Dymu')]
# MT2009_PLUS_JADE_JEWELLERY_V1: the jade jewellery of each kind - (its armour subtype, its Polish name, the +0 of
# Mgly / Slonca / Nocy / Dymu - Owsap's vnums, free in our world on 14 October 2026)
JEWELLERY = [('ARMOR_WRIST', 'Obręcz', BRACELETS),
             ('ARMOR_NECK', 'Kolia', [(16580, 'Mgły'), (16590, 'Słońca'), (16600, 'Nocy'), (16610, 'Dymu')]),
             ('ARMOR_EAR', 'Klipsy', [(17570, 'Mgły'), (17580, 'Słońca'), (17590, 'Nocy'), (17600, 'Dymu')])]
# the Polish names the drops of the earlier batches use (ascii)
ITEMS4 = {72339: 'Kamien Metin z Yohara', 83055: 'Plat. Skrzynia Skarbow', 83056: 'Plat. Klucz do Skrz. Sk.',
          95737: 'Przeb. Ksiega Zwierza', 14580: 'Obrecz Jadeitu Mgly+0', 14590: 'Obrecz Jadeitu Slonca+0',
          14600: 'Obrecz Jadeitu Nocy+0', 14610: 'Obrecz Jadeitu Dymu+0'}

# Przeb. Ksiega Zwierza: our pet skill books (playerbot_newpet.h ITEM_BOOK_FIRST 55010, SKILL_COUNT 22)
PET_BOOKS = list(range(55010, 55032))


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
    refine = {}
    with open(os.path.join(a.owsap, 'Server/Server/db/data/player.sql'), encoding='latin-1') as f:
        for m in re.finditer(r'INSERT INTO `refine_proto` VALUES \(([^)]*)\);', f.read()):
            p = [int(x) for x in m.group(1).split(',')]
            refine[p[0]] = p
    items, refines, icons = [], [], {}

    def lim(o, k):
        # NEWWORLD_LEVEL (the Champion Level) is no item limit in our engine - the quest checks it (72339)
        t = o['LimitType%d' % k]
        return (0, 0) if t == 'NEWWORLD_LEVEL' else (Y.LIMITS[t], int(o['LimitValue%d' % k]))

    def base(vnum, o, name, text, **kw):
        anti = Y.flags(o['AntiFlags'], Y.ANTI, 'antiflag')
        flag = Y.flags(o['Flags'], Y.FLAGS, 'flag')
        d = dict(vnum=vnum, src=vnum, status=ST, name=Y.ascii_name(name), locale_name=name,
                 type=TYPES[o['Type']], subtype=SUBTYPES.get(o['SubType'], 0),
                 stack=200 if flag & Y.FLAGS['ITEM_STACKABLE'] else 1, weight=0, size=int(o['Size']), antiflag=anti,
                 flag=flag, wearflag=Y.flags(o['WearFlags'], WEAR, 'wearflag'), gold=int(o['ShopBuyPrice']),
                 shop_buy_price=int(o['ShopSellPrice']), refined_vnum=0, refine_set=0,
                 magic_pct=int(o['AlterToMagicItemPercent']), specular=int(o['Specular']),
                 socket_pct=int(o['GainSocketPercent']), addon_type=0,
                 limittype0=lim(o, 0)[0], limitvalue0=lim(o, 0)[1], limittype1=lim(o, 1)[0], limitvalue1=lim(o, 1)[1],
                 applytype0=0, applyvalue0=0, applytype1=0, applyvalue1=0, applytype2=0, applyvalue2=0,
                 desc=text, **dict(('value%d' % i, int(o['Value%d' % i])) for i in range(6)))
        d.update(kw)
        assert len(d['locale_name'].encode('cp1250')) <= 32, d['locale_name']
        return d

    # the bracelets, necklaces and earrings (+0..+9 of each): no item_proto apply - the two lines are the item's
    # (engine patch obreczjadeitu2)
    for subtype, noun, firsts in JEWELLERY:
        for b0, kind in firsts:
            for lv in range(10):
                v = b0 + lv
                o = proto[v]
                assert o['Type'] == 'ITEM_ARMOR' and o['SubType'] == subtype, v
                assert o['ApplyType0'] == 'APPLY_RANDOM' and o['ApplyType1'] == 'APPLY_RANDOM', v
                pl, text = desc[v]
                assert pl == '%s Jadeitu %s+%d' % (noun, kind, lv), (v, pl)
                rs = 0
                if lv < 9:
                    assert int(o['RefinedVnum']) == v + 1 and int(o['RefineSet']) == 810 + lv, (v, o['RefineSet'])
                    rs = REFINE_ID0 + lv
                items.append(base(v, o, pl, text, refined_vnum=v + 1 if lv < 9 else 0, refine_set=rs,
                                  icon='icon/item/%d.tga' % b0, list_type='ARMOR'))
                icons['%d.tga' % b0] = '%d.tga' % b0
    for lv in range(9):
        r = refine[810 + lv]
        # id, vnum0, count0, vnum1, count1, vnum2, count2, vnum3, count3, vnum4, count4, cost, src, result, prob
        refines.append(dict(id=REFINE_ID0 + lv, mats=[(r[1], r[2]), (r[3], r[4]), (r[5], r[6]), (r[7], r[8]),
                                                         (r[9], r[10])], cost=r[11], prob=r[14], src=810 + lv))
    # Kamien Metin z Yohara: a quest-use item (Owsap: a gift box of the engine's own kind); GF's icon is 71080.tga -
    # our 71080.tga is another picture: GF's under 72339.tga
    o = proto[72339]
    pl, text = desc[72339]
    items.append(base(72339, o, pl, text + ' Działa na mapach Yohary z Wolą SungMa.', type=TYPES['ITEM_QUEST'],
                      subtype=0, flag=Y.FLAGS['ITEM_QUEST_USE'], stack=1, icon='icon/item/72339.tga',
                      list_type='ETC'))
    icons['72339.tga'] = '71080.tga'
    # Plat. Skrzynia Skarbow / Plat. Klucz do Skrz. Sk.: treasure box / key of value 5
    for v in (83055, 83056):
        o = proto[v]
        pl, text = desc[v]
        assert int(o['Value0']) == 5, v
        items.append(base(v, o, pl, text, icon='icon/item/%d.tga' % v, list_type='ETC'))
        icons['%d.tga' % v] = '%d.tga' % v
    # Przeb. Ksiega Zwierza: no Owsap row (its vnum is GF's 55007, ours a pet transporter): a gift box as our 50120
    gb = dict(proto[50120])
    items.append(base(95737, gb, 'Przeb. Księga Zwierza',
                      'Przebudzona księga pełna wiedzy o zwierzętach. Otwórz ją, aby otrzymać losową Księgę Zwierza '
                      '(jak ze Skrzyni Ksiąg Peta).', type=TYPES['ITEM_GIFTBOX'], subtype=0, antiflag=0,
                      flag=Y.FLAGS['ITEM_STACKABLE'], stack=200, gold=0, shop_buy_price=0, value0=0,
                      icon='icon/item/95737.tga', list_type='ETC'))
    icons['95737.tga'] = '55007.tga'
    byv = dict((i['vnum'], i) for i in items)
    assert len(byv) == len(items) == 124
    write_sql(items, refines)
    write_json(items)
    copy_icons(icons, a.gf)
    write_sig()
    print('items %d (bracelets 40, necklaces 40, earrings 40, Kamien Metin z Yohara, Plat. Skrzynia / Klucz, Przeb. Ksiega Zwierza), refine '
          'rows %d (%d-%d)' % (len(items), len(refines), refines[0]['id'], refines[-1]['id']))


def write_sql(items, refines):
    L = ['-- MT2009_PLUS_YOHARA_ITEMS4_V1: Obrecze Jadeitu (14580-14619), Kolie Jadeitu (16580-16619) and Klipsy Jadeitu',
         '-- (17570-17609, MT2009_PLUS_JADE_JEWELLERY_V1), Kamien Metin z Yohara (72339), Plat. Skrzynia',
         '-- Skarbow / Plat. Klucz do Skrz. Sk. (83055/83056), Przeb. Ksiega Zwierza (95737) - the owner, 14 October 2026.',
         '-- GENERATED by tools/yohara_maps4/gen_yitems4.py - do not edit, rerun it. Every start (apply.sh), idempotent:',
         '-- INSERT IGNORE - a row the operator changed is kept. Source: Owsap v6.2.6 db/item_proto.txt (the official',
         '-- vnums and numbers), refine_proto 810-818 (db/data/player.sql) as ours %d-%d, the Polish names of its Polish'
         % (refines[0]['id'], refines[-1]['id']),
         '-- client. Every vnum and refine id was free in our world (14 October 2026, the test server). The bracelets have',
         '-- no item_proto apply: their Sung Ma Will line is the 6th bonus slot, rolled when one is made and carried by a',
         '-- refine (server-patches/obreczjadeitu, MT2009_PLUS_JADE_BRACELET_V1); the wiki\'s "Precyzja" line has no point',
         '-- in our engine. Przeb. Ksiega Zwierza (the official 55007 holds our Transporter z Petem) opens to one of our',
         '-- 22 pet skill books (special_item_group.yohara_items4.txt), as Skrzynia Ksiag Peta (55009) does.',
         'SET NAMES utf8mb4;',
         'INSERT IGNORE INTO world.item_proto (%s) VALUES' % ','.join('`%s`' % c for c in Y.COLS),
         ',\n'.join(Y.sqlrow(i) for i in items) + ';',
         'INSERT IGNORE INTO world.refine_proto (id,vnum0,count0,vnum1,count1,vnum2,count2,vnum3,count3,vnum4,count4,'
         'cost,src_vnum,result_vnum,prob) VALUES',
         ',\n'.join('(%d,%s,%d,0,0,%d)' % (r['id'], ','.join('%d,%d' % m for m in r['mats']), r['cost'], r['prob'])
                    for r in refines) + ';']
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


def write_sig():
    L = ['# MT2009_PLUS_YOHARA_ITEMS4_V1: Plat. Skrzynia Skarbow (83055, opened with Plat. Klucz do Skrz. Sk. 83056) - the',
         '# owner\'s sheet of 15 October 2026 (tools/yohara_chestdrops), one thing an opening, by weight; Przeb. Ksiega',
         '# Zwierza (95737) - one of our 22 pet skill books as Skrzynia Ksiag Peta (55009) gives. GENERATED by',
         '# tools/yohara_maps4/gen_yitems4.py.',
         '# Appended to special_item_group.txt by the Dockerfile (share: Yohara - Rozpadlina Dusz).', '']
    L += CD.comment(83055)          # MT2009_PLUS_CHEST_DROPS_V1: the owner's sheet of 15 October 2026
    L += ['Group\tMT2009_yitems4_83055', '{', '\tVnum\t83055 -- Plat. Skrzynia Skarbow']
    L += CD.group_lines(83055)
    L += ['}', '', 'Group\tMT2009_yitems4_95737', '{', '\tVnum\t95737 -- Przeb. Ksiega Zwierza (= Skrzynia Ksiag Peta)']
    for k, v in enumerate(PET_BOOKS, 1):
        L.append('\t%d\t%d\t1\t10' % (k, v))
    L += ['}', '']
    with open(SIG_OUT, 'w', encoding='utf-8', newline='\n') as f:
        f.write('\n'.join(L))


if __name__ == '__main__':
    main()
