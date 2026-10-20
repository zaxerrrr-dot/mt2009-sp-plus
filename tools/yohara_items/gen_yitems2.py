#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""gen_yitems2.py [--owsap DIR] [--gf DIR]

MT2009_PLUS_YOHARA_ITEMS2_V1: the items and drops of the second batch of Yohara maps - Seoganland (376), Namgan
(377), Przelecz Yilad (385), Wawoz Polnocnego Wiatru (388), Schronienie Polnocnego Wiatru (393); the owner, 14 October
2026 (cache/yohara/decyzje.md "14.10": "Wszystko wg wiki: drop, rudy, NPC, bossowie, zywioly"). The method of
gen_yitems.py (the first batch): every item the pl-wiki lists as a drop of these maps' monsters and Metins that our
world lacks, with the official vnums and numbers of Owsap v6.2.6 (Server/Server/db/item_proto.txt) and the Polish
names of its Polish client (= the official translation), the icons of the GF 26.1.11 client. The wiki pages:
cache/yohara/wiki/*.raw (monsters, Metins; the chests: tools/yohara_chestdrops); the percents are ours (the wiki gives none)
- official-like rarity (the owner, 14 October: the first batch's drop was "strasznie przesadzony"): a monster's
material a few tenths of a percent, a rare thing well under a tenth; a boss's a few percent; nothing compensates the
test server's 500% drop event. This batch's own files - the first batch's (gen_yitems.py) are retuned elsewhere.

Writes (all GENERATED - edit this file, run it again):
  linux-port/docker/mariadb/playerbot/yohara_items2.sql              world.item_proto + crafting_proto (INSERT IGNORE)
  linux-port/docker/game/yohara_maps2/mob_drop_item.yohara_maps2.txt   the drops of the batch's monsters and Metins
  linux-port/docker/game/yohara_maps2/special_item_group.yohara_items2.txt  the new chests' contents
  tools/yohara_items/yohara_items2.json                               the client's rows (patch_yohara_client.py)
  client-patches/client-2.0.30/root/icon/item/<icon>.tga              the GF icons our client packs do not have

Example: python3 tools/yohara_items/gen_yitems2.py
"""
import argparse
import json
import os
import shutil
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(os.path.dirname(HERE))
sys.path.insert(0, os.path.join(REPO, 'tools', 'yohara_chestdrops'))
import chestdrops as CD  # noqa: E402  (MT2009_PLUS_CHEST_DROPS_V1: the chests' rows)
sys.path.insert(0, HERE)
import gen_yitems as y1  # noqa: E402  (the first batch: the engine's numbers, the SQL row writer)

SQL_OUT = os.path.join(REPO, 'linux-port', 'docker', 'mariadb', 'playerbot', 'yohara_items2.sql')
DROP_OUT = os.path.join(REPO, 'linux-port', 'docker', 'game', 'yohara_maps2', 'mob_drop_item.yohara_maps2.txt')
SIG_OUT = os.path.join(REPO, 'linux-port', 'docker', 'game', 'yohara_maps2', 'special_item_group.yohara_items2.txt')
JSON_OUT = os.path.join(HERE, 'yohara_items2.json')
ICON_OUT = y1.ICON_OUT
# icons whose GF name our packs already use (perhaps for another picture): the GF picture under a name of ours
RENAME_ICONS = {50527: 'yohara_50527.tga', 83067: 'yohara_83067.tga'}

TYPES = dict(y1.TYPES, ITEM_TREASURE_BOX=20, ITEM_TREASURE_KEY=21, ITEM_GIFTBOX=23)
SUBTYPES = dict(y1.SUBTYPES, SPECIAL_MAP=0)
ST = y1.ST
need = y1.need

ITEMS = []


def add(vnum, src=None, name=None, status=ST, **over):
    ITEMS.append(dict(vnum=vnum, src=src or vnum, name=name, status=status, over=over))


MAT = dict(type='ITEM_MATERIAL', subtype='MATERIAL_LEATHER')
JADE = y1.JADE
SERPENT = 'the Serpent equipment of Yohara (Bron/Zbroja Wezowa) and its refining - none here yet'
NORTHWIND = 'the Northwind equipment (Kamien Broni / Rekawic / Szlifierski Pln. Wiatru, Kowadlo) - none here yet'
HERBS = y1.HERBS
# the jade ores of the veins (server-patches/jadeit) and the fourth jade
for v in (50641, 50642, 50643, 50644):                  # Ruda Jadeitu Slonca / Nocy / Dymu / Mgly
    add(v, type='ITEM_SPECIAL', subtype='0')            # as our ores 50601-50619 (type 6)
add(50663, status=need(JADE))                           # Jadeit Dymu (50661/50662/50664: the first batch)
# materials of the Serpent / Northwind sets and their refining
add(31228, tradeable=1)                                              # Luska Argosa - Obrecz Jadeitu Dymu (quest yohara_mapy4)
for v in (31233, 31234, 31257, 31258):                  # Kamien Wezowy(+), Wzor Wezowy, Jedwab Wezowy
    add(v, status=need(SERPENT))
add(70428, status=need(SERPENT), **MAT)                 # Pyl Wezowy (Owsap: USE_SPECIAL, a quest use)
for v in (31236, 31237, 31242, 31243, 31244, 31259, 31263):
    add(v, status=need(NORTHWIND))                      # Biala Smocza Luska, Kamienie Pln. W., Kowadlo
for v in (31239, 31240, 31241):                         # Polyskujaca Biala / Nieb. / Krwawa Perla
    add(v, status=need(JADE + ' (the pearls of the Northwind jewellery)'))
add(31238, type='ITEM_GIFTBOX', subtype='0')            # Polyskujaca Muszla - a chest (special_item_group)
# herbs of the elements (wiki: wind Kwiat Polnocnego Wiatru, earth Ziemne Pnacze, lightning Piorunowe Ziolo; our
# 50735 / 50736 are Korzen Weza / Jaskiniowy Grzyb, so 95735 / 95736 here as the first batch's 957xx)
add(95735, src=50735, status=need(HERBS + '; 50735 is our Korzen Weza, so 95735'))
add(95736, src=50736, status=need(HERBS + '; 50736 is our Jaskiniowy Grzyb, so 95736'))
add(50737, status=need(HERBS))
add(50739, status=need(HERBS))                          # Pusty Eliksir Mocy
add(50740, status=need(HERBS))                          # Pusty Eliksir Odp.
# chests and keys
add(83065, type='ITEM_GIFTBOX', subtype='0')            # Losowa Skrzynia Skarbow
add(83066, type='ITEM_GIFTBOX', subtype='0')            # Los. Klucz do Skrz. Sk.
add(83067)                                              # Skrzynia z Bransoletka (TREASURE_BOX 4)
add(83054)                                              # Idealny Klucz (TREASURE_KEY 4)
add(70410)   # Zamarzniety Klucz - Glebie Polnocnego Wiatru (quest ymaps3_glebie: 3 a person; fix 3.0 #9 - no 'bez zastosowania')
# the rest
# Mikstura Talentu: the 9th skills' G1 -> P (MT2009_PLUS_SKILL9_TALENT_V1, quest mikstura_talentu, the pl-wiki)
add(50527, desc='Potrzebna, by udoskonalić 9. umiejętność od G1 do P - każdy stopień wymaga jednej udanej próby '
    '(szansa ok. 30%, Rada Pustelnika ją zwiększa). Zużywa punkty rangi (nieudana próba mniej), nie działa przy randze '
    '-19 000 i niższej. Można jej używać co 8-12 godzin (Zwój Egzorcyzmu skraca czas oczekiwania).')
add(50336, status=need('the mission books of Wawoz Polnocnego Wiatru - none here yet'))
add(72740, status=need('the mercenaries (Licencja Najemnika) - none here yet'), **MAT)
for v in (49991, 49992, 49993):                         # Ognista Runa Aury (10/50/100)
    add(v, status=need('the aura costume (Runy Aury) - none here yet'), **MAT)
add(70401, status=need('the Northwind guild quest (Sztandar Czaszki) - none here yet'))
PET = 'the pet system of Yohara (its riding books, level books) - ours is the older one'
add(55003, status=need(PET))                            # Ksiega Mlodego Zwierza
for v in range(55050, 55068):                           # Jazda Konna (...) / Jazda (...): 18 pet skill books
    add(v, status=need(PET), **MAT)

# items we have (official vnums) under the wiki's names in the drop file
EXISTING = {
    27007: 'Czerwona Mikstura (XXL)', 27008: 'Niebieska Mikstura (XXL)', 27987: 'Malz', 27990: 'Kawalek Kamienia',
    27992: 'Biala Perla', 27993: 'Niebieska Perla', 27994: 'Krwawa Perla', 25040: 'Zwoj Blogoslawienstwa',
    28046: 'Kamien Demonow+0', 31216: 'Plyta z Surowego Metalu', 31217: 'Rog Trolla', 31218: 'Plyta ze Stali Kuzniczej',
    31224: 'Plyta ze Stali Ozdobnej', 31245: 'Twarda Skora', 31246: 'Wzor Rekawicy', 31247: 'Czerwona Runa SungMa',
    31248: 'Liliowa Runa SungMa', 31249: 'Niebieska Runa SungMa', 31250: 'Zielona Runa SungMa', 31251: 'Utwardzacz Skory',
    31252: 'Utwardzacz Skory+', 39002: 'Pierscien Doswiadczenia', 39068: 'Zdobna Skrz. z Odlamkiem',
    39078: 'Szary Lsniacy Odlamek', 39079: 'Zielony Lsniacy Odlamek', 39080: 'Zolty Lsniacy Odlamek',
    39081: 'Swiety Fragment (120)', 50043: 'Klucz Nimfy Wodnej', 50124: 'Sprochniala Skrzynia', 50300: 'Ksiega Umiejetnosci',
    50323: 'Skrzynia Ksiag: Riposta', 50324: 'Skrzynia Ksiag: Dopalacz', 50325: 'Ksiega Precyzji', 50338: 'Charyzma Nowicjusza',
    50339: 'Charyzma Adepta', 50340: 'Charyzma Eksperta', 50341: 'Inspiracja Nowicjusza', 50342: 'Inspiracja Adepta',
    50343: 'Inspiracja Eksperta', 50513: 'Kamien Duchowy', 50525: 'Kamien Duchowy+', 50528: 'Szkatulka Yohara',
    50529: 'Skrzynia Ksiag (9.skill)', 50661: 'Jadeit Slonca', 50662: 'Jadeit Nocy', 50664: 'Jadeit Mgly',
    50738: 'Mroczny Ciern', 55001: 'Odzywka (Proteinowa Przekaska)', 55009: 'Skrzynia Ksiag Zwierza (Peta)',
    70014: 'Pigulka Krwi', 70037: 'Ksiega Zapomnienia', 70038: 'Peleryna Mestwa', 70048: 'Peleryna Maskujaca',
    70408: 'Tajemniczy Bilet', 70434: 'Zwoj Skarbu (Stopien A)', 72006: 'Rekawica Zlodzieja', 72353: 'Topaz Woli',
    72354: 'Przenosna Zyla Jadeitu', 90006: 'Kamien Duszy', 95601: 'Stabilne Sznury', 95734: 'Mrozny Korzonek',
    95926: 'Kamyki', 81000: 'Talizman Woli SILA+0', 81250: 'Talizman Woli ODP+0', 81300: 'Talizman Woli WIT+0',
    81550: 'Talizman Woli INT+0',
}
for _v in range(50569, 50576):
    EXISTING[_v] = 'Ksiega 9. umiejetnosci (%d)' % _v
# the items of MT2009_PLUS_YOHARA_ITEMS4_V1 (tools/yohara_maps4/gen_yitems4.py, yohara_items4.sql): the chests and
# the war chiefs below name them
EXISTING.update({72339: 'Kamien Metin z Yohara', 83055: 'Plat. Skrzynia Skarbow', 83056: 'Plat. Klucz do Skrz. Sk.',
                 95737: 'Przeb. Ksiega Zwierza', 14580: 'Obrecz Jadeitu Mgly+0', 14590: 'Obrecz Jadeitu Slonca+0',
                 14600: 'Obrecz Jadeitu Nocy+0', 14610: 'Obrecz Jadeitu Dymu+0'})
for _v, _n in ((39013, 'Blogoslawienstwo Smoka'), (71004, 'Medal Smoka'), (71017, 'Medal Szczescia'),
               (39031, 'Mikstura Pospiechu'), (72010, 'Pioro Ptaka Milosci'), (72013, 'Rybie Wnetrznosci'),
               (50037, 'Heksagonalna Szkatulka'), (50249, 'Skrzynia Triumfu'), (50007, 'Srebrna Szkatulka'),
               (50006, 'Zlota Szkatulka'), (50009, 'Srebrny Klucz'), (50008, 'Zloty Klucz')):
    EXISTING[_v] = _n
# weapons (our names): +0 bases
WEAPONS = {'Ekstazyjny Wachlarz': 7150, 'Demoniczne Ostrze': 250, 'Zlodziej Dusz': 3150, 'Bambusowy Dzwon': 5120,
           'Lwi Miecz': 190, 'Skrzydla Demona Chakr.': 1130, 'Zatruty Miecz': 180, 'Miecz Zadlo': 170,
           'Noz Siamese': 1120, 'Luk Niebieskiego Smoka': 2180, 'Dzwon Nieba I Ziemi': 5100, 'Smoczy Noz': 1100,
           'Wachlarz Zbawienia': 7140, 'Miecz Bojowy': 140, 'Miecz Szponu Ducha': 150,
           'Olbrz. Luk Zolt. Smoka': 2140, 'Magnetyczne Ostrze': 3140}


def build(a):
    rows = y1.read_tsv(os.path.join(a.owsap, 'Server/Server/db/item_proto.txt'))
    head = rows[0]
    proto = dict((int(r[0]), dict(zip(head, r))) for r in rows[1:] if r and r[0].isdigit())
    desc = {}
    for r in y1.read_tsv(os.path.join(a.owsap, 'Client/Client/pack/locale/locale/pl/itemdesc.txt')):
        if len(r) >= 2 and r[0].strip().isdigit():
            desc[int(r[0])] = (r[1].strip(), r[2].strip() if len(r) > 2 else '')
    gf_list = {}
    for r in y1.read_tsv(os.path.join(a.gf, 'shared/common/item_list.txt')):
        if len(r) >= 3 and r[0].strip().isdigit():
            gf_list[int(r[0])] = r[2].strip()
    items = []
    for it in ITEMS:
        o = proto[it['src']]
        ov = it['over']
        pl, text = desc.get(it['src'], ('', ''))
        text = ov.get('desc', text)
        name = it['name'] or pl
        assert name and len(name.encode('cp1250')) <= 32, (it['vnum'], name)
        typ = TYPES[ov.get('type', o['Type'])]
        sub = SUBTYPES[ov.get('subtype', o['SubType'])]
        anti = y1.flags(o['AntiFlags'], y1.ANTI, 'antiflag')
        if it['status'] != ST or ov.get('tradeable'):   # tradeable: kept as the world's row has it
            anti &= ~y1.ANTI_TRADE
        flag = y1.flags(o['Flags'], y1.FLAGS, 'flag')
        if 'type' in ov and ov['type'] == 'ITEM_MATERIAL':
            flag |= y1.FLAGS['ITEM_STACKABLE']
        for i in range(3):
            t = o['ApplyType%d' % i]
            assert t in ('A_NONE', 'APPLY_NONE'), (it['vnum'], t)
        lim = [(y1.LIMITS[o['LimitType0']], int(o['LimitValue0'])), (y1.LIMITS[o['LimitType1']], int(o['LimitValue1']))]
        values = [int(o['Value%d' % i]) for i in range(6)]
        if typ == 5 and o['Type'] != 'ITEM_MATERIAL':
            values = [0] * 6        # a stand-in material carries none of its old type's values
        stackable = bool(flag & y1.FLAGS['ITEM_STACKABLE'])
        icon = gf_list.get(it['src'])
        assert icon, it['vnum']
        icon_file = os.path.basename(icon)
        if it['vnum'] != it['src']:
            icon_file = '%d.tga' % it['vnum']
        icon_file = RENAME_ICONS.get(it['vnum'], icon_file)
        items.append(dict(
            vnum=it['vnum'], src=it['src'], status=it['status'], name=y1.ascii_name(name), locale_name=name,
            type=typ, subtype=sub, stack=200 if stackable else 1, weight=0, size=int(o['Size']), antiflag=anti,
            flag=flag, wearflag=0, gold=int(o['ShopBuyPrice']), shop_buy_price=int(o['ShopSellPrice']),
            refined_vnum=0, refine_set=0, magic_pct=int(o['AlterToMagicItemPercent']),
            specular=int(o['Specular']), socket_pct=int(o['GainSocketPercent']), addon_type=0,
            limittype0=lim[0][0], limitvalue0=lim[0][1], limittype1=lim[1][0], limitvalue1=lim[1][1],
            applytype0=0, applyvalue0=0, applytype1=0, applyvalue1=0, applytype2=0, applyvalue2=0,
            **dict(('value%d' % i, values[i]) for i in range(6)),
            icon='icon/item/' + icon_file, icon_src=icon, desc=text, list_type='ETC'))
    return items


# -- the crafting: the jade (server-patches/jadeit): 100 ore -> 1 jade at a guild alchemist (20060-20072)
CRAFT = [(50661, '50641,100'), (50662, '50642,100'), (50663, '50643,100'), (50664, '50644,100')]


def write_sql(items):
    L = ['-- MT2009_PLUS_YOHARA_ITEMS2_V1: the items that drop in Seoganland (376), Namgan (377), Przelecz Yilad (385),',
         '-- Wawoz Polnocnego Wiatru (388) and Schronienie Polnocnego Wiatru (393) on the pl-wiki and were missing here',
         '-- (the owner, 14 October 2026). GENERATED by tools/yohara_items/gen_yitems2.py - do not edit, rerun it. Every',
         '-- start (apply.sh, after yohara_items.sql), idempotent: INSERT IGNORE - a row the operator changed is kept.',
         '-- Source: Owsap v6.2.6 db/item_proto.txt (the official vnums and numbers) in our columns, the Polish names of',
         '-- its Polish client. Each vnum was free in our world.item_proto (14 October 2026); our 50735 / 50736 hold',
         '-- other items, so Piorunowe Ziolo / Kwiat Polnocnego Wiatru are 95735 / 95736 here. An item whose system we',
         '-- do not have is tradeable and does nothing yet - its row says what it waits for:']
    for i in items:
        if i['status'] != ST:
            L.append('--   %d %s - %s' % (i['vnum'], i['name'], i['status'][len('needs: '):]))
    L.append('-- The jade (server-patches/jadeit, MT2009_PLUS_JADE_VEINS_V1): Ruda Jadeitu 50641-50644 from the veins, 100')
    L.append('-- of it smelted into Jadeit 50661-50664 by a guild alchemist (crafting_proto, 60 000 Yang, 60%).')
    L.append('SET NAMES utf8mb4;')
    L.append('INSERT IGNORE INTO world.item_proto (%s) VALUES' % ','.join('`%s`' % c for c in y1.COLS))
    L.append(',\n'.join(y1.sqlrow(i) for i in items) + ';')
    L.append('INSERT IGNORE INTO world.crafting_proto (vnum, item_vnum, count, price, chance, recipe, req_progress, '
             'req_level, recipe_vnum) VALUES')
    L.append(',\n'.join("(%d, %d, 1, 60000, 60, '%s', 0, 0, 0)" % (v, v, r) for v, r in CRAFT) + ';')
    with open(SQL_OUT, 'w', encoding='utf-8', newline='\n') as f:
        f.write('\n'.join(L) + '\n')


def write_json(items):
    keys = ('vnum', 'name', 'locale_name', 'type', 'subtype', 'stack', 'weight', 'size', 'antiflag', 'flag',
            'wearflag', 'gold', 'shop_buy_price', 'refined_vnum', 'refine_set', 'magic_pct', 'specular', 'socket_pct',
            'limittype0', 'limitvalue0', 'limittype1', 'limitvalue1', 'applytype0', 'applyvalue0', 'applytype1',
            'applyvalue1', 'applytype2', 'applyvalue2', 'value0', 'value1', 'value2', 'value3', 'value4', 'value5')
    out = {'items': [dict((k, i[k]) for k in keys) for i in items],
           'item_list': dict((str(i['vnum']), '%d\t%s\t%s' % (i['vnum'], i['list_type'], i['icon'])) for i in items),
           'itemdesc': dict((str(i['vnum']), '%d\t%s\t%s' % (i['vnum'], i['locale_name'], y1.client_desc(i)))
                            for i in items)}
    with open(JSON_OUT, 'w', encoding='utf-8', newline='\n') as f:
        json.dump(out, f, ensure_ascii=False, indent=0)
        f.write('\n')


def copy_icons(items, gf):
    os.makedirs(ICON_OUT, exist_ok=True)
    for i in items:
        dst = os.path.join(ICON_OUT, os.path.basename(i['icon']))
        src = os.path.join(gf, i['icon_src'].replace('\\', '/'))
        assert os.path.isfile(src), src
        if not os.path.exists(dst) or open(dst, 'rb').read() != open(src, 'rb').read():
            shutil.copyfile(src, dst)


# -- the chests (special_item_group): one thing an opening, by weight (the wiki's contents; ours the weights) ------
def chests():
    # MT2009_PLUS_CHEST_DROPS_V1: the rows and their chances - the owner's sheet of 15 October 2026
    # (tools/yohara_chestdrops: the official vnums mapped to ours, what we lack left out and the rest renormalised)
    return [(vnum, title, CD.table(vnum)[0]) for vnum, title in (
        (31238, 'Polyskujaca Muszla'),
        (83065, 'Losowa Skrzynia Skarbow - another chest inside'),
        (83066, 'Los. Klucz do Skrz. Sk. - a key or Yang'),
        (83067, 'Skrzynia z Bransoletka (Idealny Klucz 83054)'))]


def write_sig(byv):
    L = ['# MT2009_PLUS_YOHARA_ITEMS2_V1: the chests among the drops of Seoganland, Namgan, Przelecz Yilad, Wawoz and',
         '# Schronienie Polnocnego Wiatru - their contents and chances from the owner\'s sheet of 15 October 2026, by weight.',
         '# GENERATED by tools/yohara_items/gen_yitems2.py - do not edit. Appended to special_item_group.txt by the',
         '# Dockerfile (share: Yohara - Seoganland, Namgan, ...).', '']
    for vnum, title, rows in chests():
        L += CD.comment(vnum)
        L += ['Group\tMT2009_yitems2_%d' % vnum, '{', '\tVnum\t%d -- %s' % (vnum, title)]
        for k, (v, c, w, nm) in enumerate(rows, 1):
            L.append('\t%d\t%s\t%d\t%d -- %s' % (k, v, c, w, nm))
        L += ['}', '']
    with open(SIG_OUT, 'w', encoding='utf-8', newline='\n') as f:
        f.write('\n'.join(L))


# -- the drops ----------------------------------------------------------------------------------------------------
# percents a kill (mob_drop_item "drop"); official-like: see the header
WILL = [(81000, 1, 0.05), (81300, 1, 0.05), (81250, 1, 0.05), (81550, 1, 0.05)]
TOPAZ = (72353, 1, 0.4)
PLATES = [(31216, 1, 0.25), (31218, 1, 0.25), (31224, 1, 0.25), (31217, 1, 0.25)]
VEIN = (72354, 1, 0.05)
HERB = {'ziemia': (50737, 1, 0.5), 'wiatr': (95736, 1, 0.5), 'mrok': (50738, 1, 0.5), 'lod': (95734, 1, 0.5),
        'blyskawica': (95735, 1, 0.5)}
LUCENT = [(39078, 1, 0.05), (39079, 1, 0.05), (39080, 1, 0.05)]
RANDOM_CHEST = [(83065, 1, 0.1), (83066, 1, 0.1)]
RUNES = [(31247, 1, 0.03), (31248, 1, 0.03), (31249, 1, 0.03), (31250, 1, 0.03)]


def weapons(names, plus, pct):
    return [(WEAPONS[n] + plus, 1, pct, '%s+%d' % (n, plus)) for n in names]


def myr(element):          # Myr (wiki: Seoganland, Namgan)
    return WILL + [TOPAZ] + PLATES + [VEIN, HERB[element]]


def tainted(rank):        # Skazony ... (Przelecz Yilad)
    r = WILL + [TOPAZ] + PLATES + [(95601, 1, 0.25, 'Stabilne Sznury')] + RANDOM_CHEST
    if rank != 'wojownik':
        r.append(VEIN)
    if rank == 'general':
        r += LUCENT + [(50529, 1, 0.03), (39068, 1, 0.05)]
    return r


def frozen(element):      # Zamarzniety ... (Wawoz Polnocnego Wiatru)
    return [(39078, 1, 0.05)] + WILL + [(31233, 1, 0.25), (31234, 1, 0.08), (27987, 1, 0.4), (49991, 1, 0.15),
                                       (31216, 1, 0.25), (31217, 1, 0.25), TOPAZ, (31251, 1, 0.15),
                                       (31252, 1, 0.05), (31257, 1, 0.15), (50336, 1, 0.05), HERB[element],
                                       (50739, 1, 0.25), (50740, 1, 0.25), (50529, 1, 0.03), (39068, 1, 0.05)] + \
        RANDOM_CHEST


SHELTER_COMMON = [(31238, 1, 0.15), (31244, 1, 0.1), (31251, 1, 0.15), (31252, 1, 0.05), (95734, 1, 0.5),
                  (50739, 1, 0.25), (50740, 1, 0.25), (50529, 1, 0.03), (83067, 1, 0.03), (83054, 1, 0.03),
                  (50662, 1, 0.08), (50663, 1, 0.08)] + RANDOM_CHEST
# MT2009_PLUS_NO_ROTTEN_CHEST_V1: no Sprochniala Skrzynia (50124) from any drop (the owner, 15 October 2026, fix 7)


def shelter(weps, extra):
    return weapons(weps, 0, 0.03) + SHELTER_COMMON + list(extra)


BOSS_WEAPONS9 = ['Dzwon Nieba I Ziemi', 'Smoczy Noz', 'Wachlarz Zbawienia', 'Miecz Bojowy', 'Miecz Szponu Ducha',
                 'Olbrz. Luk Zolt. Smoka', 'Magnetyczne Ostrze']
BOSS_RUNES = [(31247, 1, 4), (31248, 1, 4), (31249, 1, 4), (31250, 1, 4)]
CHARISMA = [(50338, 1, 3), (50339, 1, 1.5), (50340, 1, 0.75)]


def myr_boss(element, king):
    r = weapons(BOSS_WEAPONS9, 5, 2) + weapons(BOSS_WEAPONS9, 6, 0.5) + \
        [(27007, 10, 40, 'Czerwona Mikstura (XXL) x10'), (27008, 10, 40, 'Niebieska Mikstura (XXL) x10'),
         (72353, 2, 25, 'Topaz Woli x2')] + BOSS_RUNES + \
        [(31216, 2, 8), (31218, 2, 8), (31224, 2, 8), (31217, 2, 8), (31228, 1, 5), (31245, 1, 4), (31246, 1, 4),
         (31251, 1, 4), (31252, 1, 2), (50662, 1, 3), (50513, 1, 10), (95926, 50, 10, 'Kamyki x50'), (50325, 1, 3),
         (50300, 1, 10), (70048, 1, 8), (70038, 20, 10, 'Peleryna Mestwa x20'), (39002, 1, 5), (70014, 1, 10),
         (72006, 1, 5), (50528, 1, 8)] + CHARISMA
    if king:
        r += [(70434, 1, 2), HERB[element][:2] + (10,)]
    return r


def tainted_boss(war):
    r = weapons(BOSS_WEAPONS9, 5, 2) + weapons(BOSS_WEAPONS9, 6, 0.5) if not war else []
    r += [(72353, 2, 25, 'Topaz Woli x2')] + BOSS_RUNES + [(31251, 1, 4), (31252, 1, 2), (31257, 1, 8),
                                                           (31258, 1, 5), (95601, 2, 15, 'Stabilne Sznury x2'),
                                                           (50513, 1, 10), (95926, 50, 10, 'Kamyki x50'),
                                                           (50325, 1, 3), (50300, 1, 10), (70048, 1, 8),
                                                           (50528, 1, 8), (50529, 1, 3)]
    if war:
        r += [(31216, 2, 8), (31218, 2, 8), (31224, 2, 8), (50663, 1, 3), (70428, 1, 3), (31238, 1, 8),
              (70408, 1, 2), (70434, 1, 2), (95737, 1, 2)]
    else:
        r += [(72006, 1, 5), (39002, 1, 5)] + CHARISMA
    return r


def frozen_boss(element, war):
    w = ['Miecz Zadlo', 'Demoniczne Ostrze', 'Noz Siamese'] + ([] if war else ['Ekstazyjny Wachlarz', 'Zlodziej Dusz',
                                                                               'Luk Niebieskiego Smoka'])
    r = weapons(w, 5, 2) + weapons(w, 6, 0.5) + [(72353, 2, 25, 'Topaz Woli x2'), (31251, 1, 4), (31252, 1, 2),
                                                 (31257, 1, 8), (31238, 1, 8)] + BOSS_RUNES + \
        [(31245, 1, 4), (31258, 1, 5), (72740, 1, 2), (50527, 1, 3), (72006, 1, 5), (39002, 1, 5), HERB[element][:2] + (10,),
         (50529, 1, 3), (50528, 1, 8), (50339, 1, 1.5), (50340, 1, 0.75)]
    if war:
        r += [(39081, 1, 3), (49991, 3, 10, 'Ognista Runa Aury (10) x3'), (31217, 2, 8), (31246, 1, 4),
              (25040, 1, 5), (50300, 1, 10), (50325, 1, 3), (95926, 50, 10, 'Kamyki x50'), (28046, 1, 2),
              (50338, 1, 3), (50663, 1, 3), (70014, 1, 10), (70048, 1, 8), (70038, 20, 10, 'Peleryna Mestwa x20'),
              (70434, 1, 2), (95737, 1, 2)]
        if element == 'lod':
            r.append((31259, 1, 3))
    else:
        r += [(39078, 1, 3), (50336, 1, 5), (50739, 2, 10, 'Pusty Eliksir Mocy x2'),
              (50740, 2, 10, 'Pusty Eliksir Odp. x2'), (39068, 1, 5), (95601, 2, 15, 'Stabilne Sznury x2')] + WILL_B
    return r


WILL_B = [(81000, 1, 3), (81300, 1, 3), (81250, 1, 3), (81550, 1, 3)]


def metin(kind):
    r = [(27007, 5, 100, 'Czerwona Mikstura (XXL) x5'), (27008, 5, 100, 'Niebieska Mikstura (XXL) x5')] + \
        [(v, 1, 0.5) for v in range(50569, 50576)] + \
        [(50341, 1, 1), (50342, 1, 0.5), (50343, 1, 0.25), (28046, 1, 2), (50513, 1, 10), (50525, 1, 2),
         (50325, 1, 2), (50300, 1, 10), (70014, 1, 10), (50324, 1, 1), (50323, 1, 1), (50043, 1, 1)]
    if kind in ('jin', 'shiho', 'gumar'):
        r += [(70037, 1, 2), (55003, 1, 1)]
    if kind in ('jin', 'shiho', 'uwaznosc'):
        r.append((70408, 1, 1))
    if kind in ('szacunek', 'uwaznosc'):
        r += [(50527, 1, 2), (39002, 1, 2), (50662, 1, 2)]
    if kind == 'szacunek':
        r += [(50661, 1, 2), (50529, 1, 2), (50528, 1, 3)]
    return r


OUTPOST = [(27007, 5, 100, 'Czerwona Mikstura (XXL) x5'), (27008, 5, 100, 'Niebieska Mikstura (XXL) x5')] + \
    [(v, 1, 1) for v in (81000, 81300, 81250, 81550)] + [(39068, 1, 3), (50513, 1, 10), (50525, 1, 2)]


def drops():
    d = []
    for base, el in ((6718, 'ziemia'), (6725, 'wiatr')):
        for k, nm in enumerate(('Myr Kovix', 'Myr Proletariusz', 'Myr Golem', 'Myr Bojownik', 'Myr Czarodziej')):
            d.append((base + k, '%s (%s)' % (nm, el), myr(el)))
        d.append((base + 5, 'Myr Weteran (%s)' % el, myr_boss(el, False)))
        d.append((base + 6, 'Myr Prymus (%s)' % el, myr_boss(el, True)))
    for base, el in ((6758, 'mrok'), (6875, 'ziemia')):
        for k, (nm, rank) in enumerate((('Skazony Zolnierz', 'pawn'), ('Skazony Zadziora', 'pawn'),
                                        ('Skazony Wojownik', 'wojownik'), ('Skazony Mnich', 'pawn'),
                                        ('Skazony General', 'general'))):
            d.append((base + k, '%s (%s)' % (nm, el), tainted(rank)))
        d.append((base + 5, 'Skazony Wodz (%s)' % el, tainted_boss(False)))
        d.append((base + 6, 'Skazony Wodz Wojenny (%s)' % el, tainted_boss(True)))
    for base, el in ((6770, 'lod'), (6882, 'blyskawica')):
        for k, nm in enumerate(('Zamarzniety Lis', 'Zamarzniety Zwiadowca', 'Zamarzniety Wojownik',
                                'Zamarzniety Lowca', 'Zamarzniety General')):
            d.append((base + k, '%s (%s)' % (nm, el), frozen(el)))
        d.append((base + 5, 'Zamarzniety Wodz (%s)' % el, frozen_boss(el, False)))
        d.append((base + 6, 'Zamarzniety Wodz Wojenny (%s)' % el, frozen_boss(el, True)))
    # Schronienie Polnocnego Wiatru (the wiki's pages of each)
    d.append((6784, 'Zolnierz Schron. Pln. W. (lod)', shelter(['Demoniczne Ostrze', 'Zlodziej Dusz', 'Lwi Miecz',
                                                               'Zatruty Miecz'], [(31246, 1, 0.08)] + RUNES)))
    d.append((6785, 'Zadziora Schron. Pln. W. (lod)', shelter(
        ['Ekstazyjny Wachlarz', 'Demoniczne Ostrze', 'Bambusowy Dzwon', 'Lwi Miecz'],
        [(31241, 1, 0.02), (31242, 1, 0.08), (31246, 1, 0.08), (39081, 1, 0.03)] + RUNES + LUCENT)))
    d.append((6786, 'Wojownik Schron. Pln. W. (lod)', shelter(
        ['Ekstazyjny Wachlarz', 'Demoniczne Ostrze', 'Zlodziej Dusz', 'Bambusowy Dzwon', 'Lwi Miecz',
         'Skrzydla Demona Chakr.'],
        [(31241, 1, 0.02), (31242, 1, 0.08), (31259, 1, 0.03), (31246, 1, 0.08), (39081, 1, 0.03)] + RUNES + LUCENT)))
    d.append((6787, 'Czarownik Schron. Pln. W. (lod)', shelter(
        ['Luk Niebieskiego Smoka'], [(27992, 1, 0.05), (27993, 1, 0.05), (27994, 1, 0.05)])))
    d.append((6788, 'General Schron. Pln. W. (lod)', shelter(
        ['Ekstazyjny Wachlarz', 'Demoniczne Ostrze', 'Zlodziej Dusz', 'Bambusowy Dzwon', 'Lwi Miecz',
         'Skrzydla Demona Chakr.', 'Zatruty Miecz'],
        WILL + [(31216, 1, 0.25), (31218, 1, 0.25), (31224, 1, 0.25), (31259, 1, 0.03), (31239, 1, 0.02),
                (31240, 1, 0.02), (31241, 1, 0.02), (55001, 1, 0.05)] + RUNES)))
    shelter_boss = weapons(['Ekstazyjny Wachlarz', 'Noz Siamese', 'Demoniczne Ostrze',
                            'Luk Niebieskiego Smoka', 'Miecz Zadlo', 'Zlodziej Dusz'], 5, 2) + \
        weapons(['Ekstazyjny Wachlarz', 'Noz Siamese', 'Demoniczne Ostrze', 'Luk Niebieskiego Smoka', 'Miecz Zadlo',
                 'Zlodziej Dusz'], 6, 0.5) + \
        [(31236, 1, 3), (31243, 1, 2), (31242, 1, 5), (28046, 1, 3), (50513, 1, 10), (90006, 1, 5), (31237, 1, 5),
         (31244, 1, 5), (31263, 1, 3), (50527, 1, 3), (95734, 5, 10, 'Mrozny Korzonek x5'), (49992, 1, 2),
         (49993, 1, 1), (39002, 1, 5), (31239, 1, 2), (31240, 1, 2), (31241, 1, 2), (31238, 1, 8), (72006, 1, 5),
         (55009, 1, 3), (83067, 1, 5), (70401, 1, 2), (39081, 1, 3), (72353, 2, 25, 'Topaz Woli x2'),
         (83065, 1, 5), (83066, 1, 5), (70434, 1, 2), (95737, 1, 2)] + [(v, 1, 0.3) for v in range(55050, 55068)]
    d.append((6789, 'Wodz Wojenny Schronienia (lod)', shelter_boss))
    # Metins
    d.append((8063, 'Metin Szacunku', metin('szacunek')))
    d.append((8064, 'Metin Uwaznosci', metin('uwaznosc')))
    d.append((8065, 'Metin Jin', metin('jin')))
    d.append((8066, 'Metin Shiho', metin('shiho')))
    d.append((8077, 'Metin z Gumar', metin('gumar')))
    d.append((8626, '1. Posterunek Myr', OUTPOST))
    d.append((8627, '2. Posterunek Myr', OUTPOST))
    return d


KEY_BOSSES = [(6789, 'Wodz Wojenny Schronienia (lod)')]


def write_drops(byv):
    L = ['// MT2009_PLUS_YOHARA_MAPS2_V1 / MT2009_PLUS_YOHARA_ITEMS2_V1: drops of Seoganland (376), Namgan (377), Przelecz',
         '// Yilad (385), Wawoz Polnocnego Wiatru (388) and Schronienie Polnocnego Wiatru (393) - the pl-wiki lists of each',
         '// monster, boss and Metin (cache/yohara/wiki/*.raw) with the items yohara_items2.sql adds. GENERATED by',
         '// tools/yohara_items/gen_yitems2.py - do not edit. The wiki gives no odds; ours are official-like (the owner,',
         '// 14 October): a monster - a Talizman Woli 0.05% each, Topaz Woli 0.4%, a plate / Rog Trolla 0.25%, the',
         '// element\'s herb 0.5%, a rare thing 0.03-0.1%; a boss (hourly) - weapons +5 2% / +6 0.5% each, materials',
         '// 3-10%, Topaz Woli x2 25%; a Metin - the potions always, a 9th-skill book 0.5% each. Nothing is raised for the',
         '// test server\'s drop event. Left out, as in the first batch: the Odlamki 39070-39077 (the Seon-Hae event drops',
         '// them by level) and the Lycan\'s Szpon Gryfa / Szpon Skarabeusza / Jastrzebi / Kolczasty Szpon (no Lycan);',
         '// not in our world nor in Owsap\'s Polish data: Symbol Krola Przepowiedni (the owner: not added). The first',
         '// batch\'s monsters on Namgan (trolls, hounds, Dreczony Duch, Natanan) and Metin Swiadomosc keep their drops',
         '// (mob_drop_item.yohara_maps.txt). The Dockerfile step stops the build if any of these has a group already.',
         '// Wodz Wojenny Schronienia (6789) gives exactly one Zamarzniety Klucz a kill (a "limit" group at 100 - the',
         '// owner, 14 October). The war chiefs\' Przeb. Ksiega Zwierza (95737) and the chests\' bracelets, Kamien Metin',
         '// z Yohara, Plat. Skrzynia / Klucz: MT2009_PLUS_YOHARA_ITEMS4_V1 (yohara_items4.sql).', '']
    n = 0
    sys.path.insert(0, os.path.join(REPO, 'tools', 'yskill9'))
    import talent  # noqa: E402  (MT2009_PLUS_SKILL9_TALENT_V1: Mikstura Talentu's rows)
    for v, nm, rows in talent.with_talent(drops()):
        L += ['Group\tMT2009_ymaps2_%d' % v, '{', '\tMob\t%d\t-- %s' % (v, nm), '\tType\tdrop']
        seen = set()
        for k, r in enumerate(rows, 1):
            iv, c, p = r[:3]
            assert (iv, c) not in seen, (v, iv)
            seen.add((iv, c))
            if len(r) > 3:
                name = r[3]
            else:
                name = (byv[iv]['name'] if iv in byv else EXISTING[iv]) + (' x%d' % c if c > 1 else '')
            L.append('\t%d\t%d\t%d\t%g\t-- %s' % (k, iv, c, p, name))
        L += ['}', '']
        n += 1
    # Zamarzniety Klucz (70410): exactly one from every Wodz Wojenny Schronienia (the owner, 14 October 2026) - a
    # "limit" group (item_manager: pct x 10000 against 1..1000000 - 100 is every kill, no level fade and no drop
    # event multiplies it), apart from the "drop" group above
    for v, nm in KEY_BOSSES:
        L += ['Group\tMT2009_ymaps2_%d_klucz' % v, '{', '\tMob\t%d\t-- %s' % (v, nm), '\tType\tlimit',
              '\tlevel_limit\t1', '\t1\t70410\t1\t100\t-- Zamarzniety Klucz (always one)', '}', '']
    with open(DROP_OUT, 'w', encoding='utf-8', newline='\n') as f:
        f.write('\n'.join(L))
    return n


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--owsap', default='/opt/metin2/cache/owsap')
    ap.add_argument('--gf', default='/opt/metin2/cache/gf/Gameforge_26.1.11/_client')
    a = ap.parse_args()
    items = build(a)
    byv = dict((i['vnum'], i) for i in items)
    assert len(byv) == len(items)
    assert not set(byv) & set(EXISTING), set(byv) & set(EXISTING)
    write_sql(items)
    write_json(items)
    copy_icons(items, a.gf)
    write_sig(byv)
    n = write_drops(byv)
    print('items %d (%d work as official, %d need a system), drop groups %d, chests %d, crafting %d' % (
        len(items), sum(1 for i in items if i['status'] == ST), sum(1 for i in items if i['status'] != ST), n,
        len(chests()), len(CRAFT)))
    for i in items:
        if i['status'] != ST:
            print('  %d %s: %s' % (i['vnum'], i['name'], i['status']))


if __name__ == '__main__':
    main()
