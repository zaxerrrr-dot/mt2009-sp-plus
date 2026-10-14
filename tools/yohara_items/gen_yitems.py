#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""gen_yitems.py [--owsap DIR] [--gf DIR]

MT2009_PLUS_YOHARA_ITEMS1_V1: every item the pl-wiki lists as a drop of the monsters and Metins of Opuszczona
Twierdza (374) and Dongan (373) that our world did not have (the owner, 13 October 2026, cache/yohara/decyzje.md:
"dodajemy WSZYSTKIE przedmioty, ktore dropia na dodawanych mapach"), with the official vnums and numbers of Owsap
v6.2.6 (Server/Server/db/item_proto.txt, refine_proto of db/data/player.sql) and the Polish names and descriptions of
its Polish client (Client/Client/pack/locale/locale/pl/itemdesc.txt = the official translation), the icons of the GF
26.1.11 client. The wiki pages (cache/yohara/wiki/*.raw, wiki/items/*.raw) give the drop lists and the chests'
contents; the percents are ours (the wiki gives none).

Writes (all GENERATED - edit this file, run it again):
  linux-port/docker/mariadb/playerbot/yohara_items.sql            world.item_proto / refine_proto (INSERT IGNORE)
  linux-port/docker/game/yohara_maps/mob_drop_item.yohara_maps.txt  the 31 monsters' and Metins' drops
  linux-port/docker/game/yohara_maps/special_item_group.yohara_items.txt  the five chests' contents
  tools/yohara_items/yohara_items.json                            the client's records, item_list and itemdesc rows
                                                                  (client-patches/client-2.0.30/tools/yohara/
                                                                  patch_yohara_client.py reads it)
  client-patches/client-2.0.30/root/icon/item/<icon>.tga          the GF icons our client packs do not have

Example: python3 tools/yohara_items/gen_yitems.py
"""
import argparse
import json
import os
import re
import shutil
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(os.path.dirname(HERE))
SQL_OUT = os.path.join(REPO, 'linux-port', 'docker', 'mariadb', 'playerbot', 'yohara_items.sql')
DROP_OUT = os.path.join(REPO, 'linux-port', 'docker', 'game', 'yohara_maps', 'mob_drop_item.yohara_maps.txt')
SIG_OUT = os.path.join(REPO, 'linux-port', 'docker', 'game', 'yohara_maps', 'special_item_group.yohara_items.txt')
JSON_OUT = os.path.join(HERE, 'yohara_items.json')
ICON_OUT = os.path.join(REPO, 'client-patches', 'client-2.0.30', 'root', 'icon', 'item')
# the icons the client packs already have (2.0.55 packs, every pack's index; cache/c55/pack) - none is added again
HAVE_ICONS = set(('book_07.tga', '50526.tga', 'boss_box.tga'))
# icons whose name our packs use for another picture (the old books 50323/50324): the GF picture under a new name
RENAME_ICONS = {50323: 'yohara_50323.tga', 50324: 'yohara_50324.tga'}

# -- our engine's numbers (common/item_length.h) ---------------------------------------------------------------
TYPES = {'ITEM_ARMOR': 2, 'ITEM_USE': 3, 'ITEM_MATERIAL': 5, 'ITEM_METIN': 10, 'ITEM_UNIQUE': 16,
         'ITEM_SKILLBOOK': 17, 'ITEM_QUEST': 18, 'ITEM_TREASURE_KEY': 21, 'ITEM_GIFTBOX': 23, 'ITEM_SPECIAL': 6}
SUBTYPES = {'ARMOR_PENDANT': 7, 'USE_POTION': 0, 'USE_SPECIAL': 10, 'USE_PUT_INTO_ACCESSORY_SOCKET': 21,
            'MATERIAL_LEATHER': 0, 'QUEST_NONE': 0, 'UNK23_1': 0, '0': 0}
ANTI = {'ANTI_FEMALE': 1, 'ANTI_MALE': 2, 'ANTI_WARRIOR': 4, 'ANTI_ASSASSIN': 8, 'ANTI_SURA': 16,
        'ANTI_SHAMAN': 32, 'ANTI_GET': 64, 'ANTI_DROP': 128, 'ANTI_SELL': 256, 'ANTI_SAVE': 4096,
        'ANTI_GIVE': 8192, 'ANTI_PKDROP': 16384, 'ANTI_STACK': 32768, 'ANTI_MYSHOP': 65536,
        'ANTI_SAFEBOX': 131072}
ANTI_TRADE = 128 | 8192 | 65536 | 131072        # drop, give, shop, storage - cleared on an item without its system
FLAGS = {'ITEM_STACKABLE': 4, 'ITEM_SLOW_QUERY': 16, 'ITEM_IRREMOVABLE': 256, 'ITEM_CONFIRM_WHEN_USE': 512,
         'ITEM_QUEST_USE': 1024, 'LOG': 8192, 'ITEM_APPLICABLE': 16384}
WEAR = {'WEAR_PENDANT': 4096, 'WEAR_UNIQUE': 128, 'WEAR_GLOVE': 8192}
LIMITS = {'L_NONE': 0, 'LIMIT_NONE': 0, 'LEVEL': 1, 'REAL_TIME': 7}
# APPLY_SUNGMA_STR/HP/MOVE/IMMUNE = POINT_SUNGMA_* 184-187: the exe branch claude/yohara-exe (commit 599a7e73,
# client-patches/exe/Server/common/length.h, UserInterface/Mt2009Champion.cpp item.APPLY_SUNGMA_*) and the server's
# czempion patch (an apply is a point in this engine: CItem::ModifyPoints -> PointChange(apply type)).
APPLY_SUNGMA_STR, APPLY_SUNGMA_HP, APPLY_SUNGMA_MOVE, APPLY_SUNGMA_IMMUNE = 184, 185, 186, 187

ST = 'ok'   # works as it does officially


def need(system):
    return 'needs: ' + system


# -- the items: (vnum, Owsap source vnum, Polish name or None (= the Polish client's), status, overrides) --------
ITEMS = []


def add(vnum, src=None, name=None, status=ST, **over):
    ITEMS.append(dict(vnum=vnum, src=src or vnum, name=name, status=status, over=over))


GLOVES = 'the Sung Ma gloves (Chaegirab\'s crafting, Owsap\'s Sung-Ma Power Gloves) - none here yet'
JADE = 'the jade jewellery of Yohara (Klipsy/Kolia/Obrecz Jadeitu ...) and its crafting - none here yet'
add(72353)                                                            # Topaz Woli - the talismans' refine
for v in (31216, 31218):                                              # Plyty: Surowego Metalu, Stali Kuzniczej
    add(v, status=need(JADE))
add(31224, status=need(JADE))   # wiki drop lists: "Plyta ze Stali Obronnej" - its page shows 31224's icon (Ozdobnej)
add(31217, status=need(JADE))                                         # Rog Trolla
add(31227, status=need(JADE))                                         # Kiel Argosa
add(31226, status=need('the Skazony Rdzen\'s quest/crafting (Seoganland) - none here yet'))
for v in (31245, 31246, 31247, 31248, 31249, 31251, 31252):           # Twarda Skora .. Utwardzacz Skory+
    add(v, status=need(GLOVES))
add(31250, name='Zielona Runa SungMa', status=need(GLOVES))           # wiki's name (Owsap's PL: Zolta)
HERBS = 'herbalism (the elixirs of Yohara) - none here yet'
add(50738, status=need(HERBS))                                        # Mroczny Ciern
# our 50733 / 50734 / 50926 are other items (Bursztynowy Platek, Perlowe Wiechy, a recipe): 957xx / 95926 here
add(95733, src=50733, status=need(HERBS + '; 50733 is our Bursztynowy Platek, so 95733'))
add(95734, src=50734, status=need(HERBS + '; 50734 is our Perlowe Wiechy, so 95734'))
# MT2009_PLUS_GAYA_V1: Kamyki work now (Statua Wojownika grinds them into Gaya, quest ygaya, tools/ygaya)
add(95926, src=50926, desc='Zbieraj Kamyki i oszlifuj je u Statuy Wojownika w Porcie Nowego Kontynentu w drogocenne '
    'Gaya (30 Kamyków, Kamień Duszy +0 do +3 i 15 000 Yang - szansa 70%, 3 Gaya).')  # 50926 is our recipe, so 95926
# MT2009_PLUS_SEONHAE_LUCENT_V1 (fix 3.0 #9): the lucent shards are Seon-Hae's material of the item levels 30, 75 and
# 105 (pl-wiki "6. i 7. bonus" table; playerbot_seonhae.h MaterialVnum, client uiseonhae.py) - the wiki's own lines
LUCENT_DESC = {
    39078: 'Materiał umożliwiający z pewnym prawdopodobieństwem dodanie 6. lub 7. bonusu u Seon-Hae - do przedmiotów '
           'na 30. poziom. Jeden odłamek daje 2% szansy, najwyżej 10 naraz (20%).',
    39079: 'Materiał umożliwiający z pewnym prawdopodobieństwem dodanie 6. lub 7. bonusu u Seon-Hae - do przedmiotów '
           'na 75. poziom. Jeden odłamek daje 2% szansy, najwyżej 10 naraz (20%).',
    39080: 'Materiał umożliwiający z pewnym prawdopodobieństwem dodanie 6. lub 7. bonusu u Seon-Hae - do przedmiotów '
           'na 105. poziom (Zodiaku, biżuteria 105, Talizmany Woli), broni, zbroi i hełmów na 96. poziom (Smoka Mroku) '
           'oraz talizmanów. Jeden odłamek daje 2% szansy, najwyżej 10 naraz (20%).',
}
for v in (39078, 39079, 39080):                                       # Lsniace Odlamki
    add(v, desc=LUCENT_DESC[v], tradeable=True)            # pl-wiki: Handlowanie z Graczem - Tak
for v in (50661, 50662, 50664):                                       # Jadeit Slonca, Nocy, Mgly
    add(v, status=need(JADE))
# chests - their contents: special_item_group.yohara_items.txt
add(50528)                                                            # Szkatulka Yohara
add(50529)                                                            # Skrzynia Ksiag (9.skill)
add(50323)                                                            # Skrzynia Ksiag: Riposta
add(50324)                                                            # Skrzynia Ksiag: Dopalacz
add(39068)                                                            # Zdobna Skrz. z Odlamkiem
NINTH = 'the 9th skills (skill_proto 176-183) - none here yet'
for v in range(50569, 50576):                                         # 9th skill books (50576 = Lycan's: no Lycan)
    add(v)                                    # MT2009_PLUS_SKILL9_V1 (server-patches/skill9): they work now
WARD = 'the boost / ward skills (Riposty i Dopalacze, skill_proto 221-244) - none here yet'
for v in list(range(50516, 50524)) + list(range(50560, 50568)):       # their books (the Lycan's 50524 / 50568 out)
    add(v, status=need(WARD))
add(50525, status=need(WARD + ' (their master levels)'))              # Kamien Duchowy+
add(50325, status=need('the skill Precyzja (142) - not in our skill_proto'))   # Ksiega Precyzji
for v in range(50338, 50344):                                         # Charyzma / Inspiracja x3
    add(v, status=need('the leadership books Charyzma / Inspiracja - none here yet'))
add(28046, name='Kamień Demonów+0', status=need(GLOVES + ' (a Sung Ma stone; our engine has no METIN_SUNGMA)'),
    type='ITEM_MATERIAL', subtype='MATERIAL_LEATHER', wear='NONE', refined=0, refine_set=0)
add(72354, status=need('the jade veins (Zyly Jadeitu, mining) - none here yet'),
    type='ITEM_MATERIAL', subtype='MATERIAL_LEATHER')                # Przenosna Zyla Jadeitu (Owsap: a summon box)
add(50043, status=need('Skrzynia Nimfy Wodnej - none here yet'))      # Klucz Nimfy Wodnej
add(70408, status=need('Tajemnicza Instancja (dungeon) - none here yet'))   # Tajemniczy Bilet
add(70434, status=need('the secret dungeons of the treasure scrolls - none here yet'),
    type='ITEM_MATERIAL', subtype='MATERIAL_LEATHER')                # Zwoj Skarbu (Stopien A): Owsap's subtype is not ours
# Talizmany Woli +0..+9 - the talisman slot (MT2009_PLUS_ELEMENTS_V1), refined with Topaz Woli
TALISMANS = ((81000, 'SIŁA', APPLY_SUNGMA_STR), (81250, 'ODP', APPLY_SUNGMA_MOVE), (81300, 'WIT', APPLY_SUNGMA_HP),
             (81550, 'INT', APPLY_SUNGMA_IMMUNE))
# No item_proto apply (MT2009_PLUS_WILL_TALISMAN_V1, server-patches/talizmanwoli): Owsap's APPLY_RANDOM 10..13 / 14 -
# the Sung Ma Will of the talisman's stat and an element's power, each a common or a rare row of apply_random_table
# (Will 1,1,3,5,7,9,11,14,17,21 / 2,3,4,6,8,10,12,16,19,24; element 1..9,15 / 2..10,17 %) - are the item's own 6th/7th
# bonus slots, rolled by the engine when a talisman is made and carried by a refine.
REFINE_ID0 = 22501      # our refine_proto ids (Owsap's 680-715 are taken here)
for base, stat, apply in TALISMANS:
    for lv in range(10):
        add(base + lv, src=81000 + lv if base == 81000 else base + lv, name='Talizman Woli %s+%d' % (stat, lv))

# items we have whose name the official one replaces (MT2009_PLUS_YOHARA_ITEMS1_V1 rename; the client's records:
# client-patches/client-2.0.30/tools/yohara/patch_yohara_client.py reads 'renamed' of yohara_items.json)
RENAMED = ((27007, 'Czerwona Mikstura (XXL)'), (27008, 'Niebieska Mikstura (XXL)'))

# items we have (official vnums): their names in the drop file
EXISTING = {39002: 'Pierscien Doswiadczenia (1 h)', 72006: 'Rekawica Zlodzieja (3 h)',
            70048: 'Peleryna Maskujaca (our Plaszcz Uciekiniera)'}


def read_tsv(path):
    with open(path, 'rb') as f:
        return [l.decode('cp1250', 'replace').rstrip('\r\n').split('\t') for l in f]


def flags(s, table, what):
    v = 0
    for t in (x.strip() for x in s.split('|')):
        if t in ('NONE', '', '0'):
            continue
        if t in ('ITEM_TUNABLE', 'ANTI_QUICKSLOT'):
            continue    # not in our engine
        if t not in table:
            raise SystemExit('%s: unknown %s' % (t, what))
        v |= table[t]
    return v


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--owsap', default='/opt/metin2/cache/owsap')
    ap.add_argument('--gf', default='/opt/metin2/cache/gf/Gameforge_26.1.11/_client')
    a = ap.parse_args()
    rows = read_tsv(os.path.join(a.owsap, 'Server/Server/db/item_proto.txt'))
    head = rows[0]
    proto = dict((int(r[0]), dict(zip(head, r))) for r in rows[1:] if r and r[0].isdigit())
    desc = {}
    for r in read_tsv(os.path.join(a.owsap, 'Client/Client/pack/locale/locale/pl/itemdesc.txt')):
        if len(r) >= 2 and r[0].strip().isdigit():
            desc[int(r[0])] = (r[1].strip(), r[2].strip() if len(r) > 2 else '')
    gf_list = {}
    for r in read_tsv(os.path.join(a.gf, 'shared/common/item_list.txt')):
        if len(r) >= 3 and r[0].strip().isdigit():
            gf_list[int(r[0])] = r[2].strip()
    refine = {}
    with open(os.path.join(a.owsap, 'Server/Server/db/data/player.sql'), encoding='latin-1') as f:
        for m in re.finditer(r'INSERT INTO `refine_proto` VALUES \(([^)]*)\);', f.read()):
            p = [int(x) for x in m.group(1).split(',')]
            refine[p[0]] = p

    items, refines = [], []
    for it in ITEMS:
        o = proto[it['src']]
        ov = it['over']
        pl, text = desc.get(it['src'], ('', ''))
        text = ov.get('desc', text)
        name = it['name'] or pl
        assert name and len(name.encode('cp1250')) <= 32, (it['vnum'], name)
        typ = TYPES[ov.get('type', o['Type'])]
        sub = SUBTYPES[ov.get('subtype', o['SubType'])]
        anti = flags(o['AntiFlags'], ANTI, 'antiflag')
        if it['status'] != ST or ov.get('tradeable'):
            anti &= ~ANTI_TRADE        # an item without its system: at least tradeable (the owner's rule)
        flag = flags(o['Flags'], FLAGS, 'flag')
        wear = flags(ov.get('wear', o['WearFlags']), WEAR, 'wearflag')
        refined = ov.get('refined', int(o['RefinedVnum']))
        refine_set = ov.get('refine_set', int(o['RefineSet']))
        lim = [(LIMITS[o['LimitType0']], int(o['LimitValue0'])), (LIMITS[o['LimitType1']], int(o['LimitValue1']))]
        applies = list(ov.get('apply', ()))
        for i in range(3):
            t = o['ApplyType%d' % i]
            if not applies or len(applies) <= i:
                if t not in ('A_NONE', 'APPLY_NONE', 'A_RANDOM', 'APPLY_RANDOM'):
                    raise SystemExit('%d: apply %s not mapped' % (it['vnum'], t))
        applies += [(0, 0)] * (3 - len(applies))
        values = [int(o['Value%d' % i]) for i in range(6)]
        if typ == 2 and sub == 7:       # Talizman Woli: our talismans' own refine ids, the next level
            lv = it['vnum'] % 10
            refined = it['vnum'] + 1 if lv < 9 else 0
            src_set = int(o['RefineSet'])
            if lv < 9:
                rid = REFINE_ID0 + len(refines)
                r = refine[src_set]
                assert r[1] == 72353, r
                # Owsap's second material is the same talisman again (vnum1 = the source's own vnum): left out -
                # our refine would count the talisman being refined as that material (the wiki: Topaz Woli only)
                refines.append(dict(id=rid, vnum0=72353, count0=r[2], cost=r[11], prob=r[14], src=it['vnum']))
                refine_set = rid
            else:
                refine_set = 0
        stackable = bool(flag & FLAGS['ITEM_STACKABLE'])
        icon = gf_list.get(it['src']) or gf_list.get(it['src'] + 1)    # 81000 has no line of its own in GF's list
        assert icon, it['vnum']
        icon_file = os.path.basename(icon)
        if it['vnum'] != it['src']:     # renumbered (a vnum of ours holds another item): its own icon name
            icon_file = '%d.tga' % it['vnum']
        icon_file = RENAME_ICONS.get(it['vnum'], icon_file)
        items.append(dict(
            vnum=it['vnum'], src=it['src'], status=it['status'], name=ascii_name(name), locale_name=name,
            type=typ, subtype=sub, stack=200 if stackable else 1, weight=0, size=int(o['Size']), antiflag=anti,
            flag=flag, wearflag=wear, gold=int(o['ShopBuyPrice']), shop_buy_price=int(o['ShopSellPrice']),
            refined_vnum=refined, refine_set=refine_set, magic_pct=int(o['AlterToMagicItemPercent']),
            specular=int(o['Specular']), socket_pct=int(o['GainSocketPercent']), addon_type=0,
            limittype0=lim[0][0], limitvalue0=lim[0][1], limittype1=lim[1][0], limitvalue1=lim[1][1],
            applytype0=applies[0][0], applyvalue0=applies[0][1], applytype1=applies[1][0],
            applyvalue1=applies[1][1], applytype2=applies[2][0], applyvalue2=applies[2][1],
            **dict(('value%d' % i, values[i]) for i in range(6)),
            icon='icon/item/' + icon_file, icon_src=icon, desc=text,
            list_type='ARMOR' if typ == 2 else 'ETC'))
    byv = dict((i['vnum'], i) for i in items)
    assert len(byv) == len(items)

    write_sql(items, refines)
    write_json(items)
    copy_icons(items, a.gf)
    write_sig(byv)
    write_drops(byv)
    print('items %d (%d work as official, %d need a system), refine rows %d' % (
        len(items), sum(1 for i in items if i['status'] == ST), sum(1 for i in items if i['status'] != ST),
        len(refines)))
    for i in items:
        if i['status'] != ST:
            print('  %d %s: %s' % (i['vnum'], i['name'], i['status']))


def ascii_name(s):
    tr = str.maketrans('ąćęłńóśźżĄĆĘŁŃÓŚŹŻ', 'acelnoszzACELNOSZZ')
    return s.translate(tr)


COLS = ('vnum', 'name', 'locale_name', 'type', 'subtype', 'stack', 'weight', 'size', 'antiflag', 'flag', 'wearflag',
        'immuneflag', 'gold', 'shop_buy_price', 'refined_vnum', 'refine_set', 'magic_pct', 'specular', 'socket_pct',
        'addon_type', 'limittype0', 'limitvalue0', 'limittype1', 'limitvalue1', 'applytype0', 'applyvalue0',
        'applytype1', 'applyvalue1', 'applytype2', 'applyvalue2', 'value0', 'value1', 'value2', 'value3', 'value4',
        'value5', 'socket0', 'socket1', 'socket2', 'socket3', 'socket4', 'socket5')


def sqlrow(i):
    out = []
    for c in COLS:
        if c == 'name':
            out.append("'%s'" % i['name'].replace("'", "''"))
        elif c == 'locale_name':
            out.append("_cp1250 X'%s'" % i['locale_name'].encode('cp1250').hex().upper())
        elif c == 'immuneflag':
            out.append("''")
        elif c.startswith('socket') and c != 'socket_pct':
            out.append('-1')
        else:
            out.append(str(i[c]))
    return '(' + ','.join(out) + ')'


def write_sql(items, refines):
    L = ['-- MT2009_PLUS_YOHARA_ITEMS1_V1: the items that drop in Opuszczona Twierdza (374) and Dongan (373) on the pl-wiki',
         '-- and were missing here (the owner, 13 October 2026). GENERATED by tools/yohara_items/gen_yitems.py - do not',
         '-- edit, rerun it. Every start (apply.sh), idempotent: INSERT IGNORE - a row the operator changed is kept.',
         '-- Source: Owsap v6.2.6 db/item_proto.txt (the official vnums and numbers) in our columns, the Polish names of its',
         '-- Polish client (= the official ones; Zielona Runa SungMa as the wiki), our engine\'s numbers. Each vnum was free',
         '-- in our world.item_proto (13 October 2026); our 50733/50734/50926 hold other items, so Ognisty Lisc,',
         '-- Mrozny Korzonek and Kamyki are 95733/95734/95926 here. An item whose system we do not have is tradeable',
         '-- (drop/give/shop/storage allowed) and does nothing yet - its row says what it waits for:']
    for i in items:
        if i['status'] != ST:
            L.append('--   %d %s - %s' % (i['vnum'], i['name'], i['status'][len('needs: '):]))
    L.append('-- Talizmany Woli (81000-81009 SILA, 81250-81259 ODP, 81300-81309 WIT, 81550-81559 INT): the talisman slot of')
    L.append('-- MT2009_PLUS_ELEMENTS_V1, level 105, no item_proto apply: their two standard lines - Sung Ma Will of the stat')
    L.append('-- (APPLY_SUNGMA_STR/MOVE/HP/IMMUNE = 184/186/185/187) and an element\'s power (178-183), each common or rare -')
    L.append('-- are the item\'s 6th/7th bonus slots (MT2009_PLUS_WILL_TALISMAN_V1, server-patches/talizmanwoli), refined with Topaz')
    L.append('-- Woli (6..54, 1-5 mln Yang, 70-20%%) - refine_proto %d-%d (Owsap\'s 680-715 are other rows here).'
             % (refines[0]['id'], refines[-1]['id']))
    L.append('SET NAMES utf8mb4;')
    L.append('INSERT IGNORE INTO world.item_proto (%s) VALUES' % ','.join('`%s`' % c for c in COLS))
    L.append(',\n'.join(sqlrow(i) for i in items) + ';')
    L.append('INSERT IGNORE INTO world.refine_proto (id,vnum0,count0,vnum1,count1,vnum2,count2,vnum3,count3,vnum4,'
             'count4,cost,src_vnum,result_vnum,prob) VALUES')
    L.append(',\n'.join('(%d,%d,%d,0,0,0,0,0,0,0,0,%d,0,0,%d)' % (r['id'], r['vnum0'], r['count0'], r['cost'],
                                                                     r['prob']) for r in refines) + ';')
    # the owner (13 October): 27007/27008 under their official names - the "(XXL)" the wiki and the Yohara chests
    # use (item_proto.mt2009plus.sql had "(XL)"; its INSERT IGNORE never renames a row that is there)
    # MT2009_PLUS_WILL_TALISMAN_V1: the first rows had the common Will as their apply 0 - gone (the lines are the item's)
    L.append('UPDATE world.item_proto SET applytype0=0, applyvalue0=0 WHERE vnum IN (%s) AND applytype0<>0;'
             % ','.join(str(b + lv) for b, _s, _a in TALISMANS for lv in range(10)))
    for vnum, pl in RENAMED:
        L.append("UPDATE world.item_proto SET locale_name='%s' WHERE vnum=%d AND locale_name<>'%s';" % (pl, vnum, pl))
    with open(SQL_OUT, 'w', encoding='utf-8', newline='\n') as f:
        f.write('\n'.join(L) + '\n')


def write_json(items):
    keys = ('vnum', 'name', 'locale_name', 'type', 'subtype', 'stack', 'weight', 'size', 'antiflag', 'flag',
            'wearflag', 'gold', 'shop_buy_price', 'refined_vnum', 'refine_set', 'magic_pct', 'specular', 'socket_pct',
            'limittype0', 'limitvalue0', 'limittype1', 'limitvalue1', 'applytype0', 'applyvalue0', 'applytype1',
            'applyvalue1', 'applytype2', 'applyvalue2', 'value0', 'value1', 'value2', 'value3', 'value4', 'value5')
    out = {'items': [dict((k, i[k]) for k in keys) for i in items],
           'item_list': dict((str(i['vnum']), '%d\t%s\t%s' % (i['vnum'], i['list_type'], i['icon'])) for i in items),
           'itemdesc': dict((str(i['vnum']), '%d\t%s\t%s' % (i['vnum'], i['locale_name'], client_desc(i)))
                            for i in items),
           'renamed': dict((str(v), pl) for v, pl in RENAMED)}
    with open(JSON_OUT, 'w', encoding='utf-8', newline='\n') as f:
        json.dump(out, f, ensure_ascii=False, indent=0)
        f.write('\n')


def client_desc(i):
    d = re.sub(r'\s*\|\s*', ' ', i['desc'].replace('\t', ' ')).strip()
    for bad in ('Metin2', 'Gameforge'):
        assert bad.lower() not in d.lower(), (i['vnum'], d)
    if i['status'] != ST:
        d = (d + ' ' if d else '') + '(Na razie bez zastosowania - przyjdzie z kolejną aktualizacją Yohary.)'
    return d


def copy_icons(items, gf):
    os.makedirs(ICON_OUT, exist_ok=True)
    done = set()
    for i in items:
        dst = os.path.basename(i['icon'])
        if dst in HAVE_ICONS or dst in done:
            continue
        src = os.path.join(gf, i['icon_src'].replace('\\', '/'))
        assert os.path.isfile(src), src
        shutil.copyfile(src, os.path.join(ICON_OUT, dst))
        done.add(dst)


# -- the chests (special_item_group): one thing an opening, by weight --------------------------------------------
JEWEL3 = ((17543, 'Szmaragdowe Kolczyki+3'), (14543, 'Szmaragdowa Bransoleta+3'), (16543, 'Szmaragdowy Naszyjnik+3'),
          (17523, 'Granatowe Kolczyki+3'), (14523, 'Granatowa Bransoleta+3'), (16523, 'Granatowy Naszyjnik+3'),
          (17503, 'Rubinowe Kolczyki+3'), (14503, 'Rubinowa Bransoleta+3'), (16503, 'Rubinowy Naszyjnik+3'),
          (17563, 'Szafirowe Kolczyki+3'), (14563, 'Szafirowa Bransoleta+3'), (16563, 'Szafirowy Naszyjnik+3'),
          (14573, 'Bransoleta z Turmalinu+3'), (16573, 'Naszyjnik z Turmalinu+3'))
TEAR = ((17200, 'Kolczyki Z Niebian.Lez'), (14200, 'Bransol. Z Niebian.Lez'), (16200, 'Naszyj. Z Niebian.Lez'))
ARMOR567 = ((11690, 'Zbr. Plyt. Czar. Magii'), (11290, 'Zbroja Z Czarnej Stali'), (11490, 'Ubranie Czarn. Wiatru'),
            (11890, 'Czarna Szata'))
ARMOR3 = ((20003, 'Pancerz Diabel. Rogu+3'), (20503, 'Pancerz Koscioplytowy+3'), (20253, 'Szata Smoczego Jezdzca+3'),
          (20753, 'Zlote Ubranie+3'))
WEAPON567 = ((3140, 'Magnetyczne Ostrze'), (2140, 'Olbrz. Luk Zolt. Smoka'), (1100, 'Smoczy Noz'),
             (5100, 'Dzwon Nieba I Ziemi'), (7140, 'Wachlarz Zbawienia'), (150, 'Miecz Szponu Ducha'),
             (140, 'Miecz Bojowy'))
WEAPON3 = ((7173, 'Wachlarz Lezac. Smoka+3'), (463, 'Runiczny Miecz+3'), (3193, 'Ostrze Slonca+3'),
           (2373, 'Luk Feniksa+3'), (5343, 'Dzwon Smoczego Ducha+3'), (1343, 'Kolec Pieciu Elementow+3'),
           (473, 'Klinga Smoczego Kla+3'))


def chests(byv):
    def n(v):
        return byv[v]['name'] if v in byv else ''
    g = []
    # Szkatulka Yohara (pl-wiki "Szkatulka Yohara"): left out - Szklo Detekcji (60004), Male Blogoslawienstwo (72351),
    # the Jade Mist jewels (14580/16580/17570; no jade jewellery here), the Lycan's Szpon Gryfa, Zbroja Nocnego Cienia,
    # Zbroja Dowodcy, Wladca Smokow (no Lycan here)
    s = [(31216, 1, 60), (31224, 1, 60), (31218, 1, 60), (72353, 1, 60), (31217, 1, 60), (31245, 1, 60),
         (50325, 1, 30), (50529, 1, 30), (71130, 1, 30, 'Przepustka (zdatna do handlu)'), (80019, 1, 30, 'Delikatne Sukno'),
         (39004, 1, 20, 'Kula Blogoslawienstwa (zdatna do handlu)'),
         (27007, 50, 60, 'Czerwona Mikstura (XXL) x50'), (27008, 30, 60, 'Niebieska Mikstura (XXL) x30')]
    s += [(v, 1, 15) for v in (81000, 81550, 81250, 81300)]
    s += [(v, 1, 8, nm) for v, nm in JEWEL3]
    for base, nm in TEAR + ARMOR567 + WEAPON567:
        s += [(base + lv, 1, w, '%s+%d' % (nm, lv)) for lv, w in ((5, 5), (6, 3), (7, 2))]
    s += [(v, 1, 8, nm) for v, nm in ARMOR3 + WEAPON3]
    g.append((50528, 'Szkatulka Yohara', s))
    s = [(v, 1, 8) for v in range(50569, 50576)]
    s += [('gold', 500000, 30, 'Yang 500 000'), (27007, 50, 30, 'Czerwona Mikstura (XXL) x50'),
          (27008, 30, 30, 'Niebieska Mikstura (XXL) x30')]
    g.append((50529, 'Skrzynia Ksiag (9.skill) - the Lycan\'s Burza Szponow (50576) out', s))
    g.append((50323, 'Skrzynia Ksiag: Riposta - the Lycan\'s Wilczy Dech (50524) out',
              [(v, 1, 10) for v in range(50516, 50524)]))
    g.append((50324, 'Skrzynia Ksiag: Dopalacz - the Lycan\'s Wilczy Dech (50568) out',
              [(v, 1, 10) for v in range(50560, 50568)]))
    s = [(v, 1, 8, nm) for v, nm in ((39070, 'Szary Odlamek'), (39071, 'Bialy Odlamek'), (39072, 'Zielony Odlamek'),
                                     (39073, 'Zolty Odlamek'), (39074, 'Niebieski Odlamek'),
                                     (39075, 'Fioletowy Odlamek'), (39076, 'Czerwony Odlamek'),
                                     (39077, 'Teczowy Odlamek'))]
    s += [(v, 1, 4) for v in (39078, 39079, 39080)] + [(50300, 1, 40, 'Ksiega Umiejetnosci')]
    g.append((39068, 'Zdobna Skrz. z Odlamkiem', s))
    out = []
    for vnum, title, rows in g:
        rr = []
        for r in rows:
            v, c, w = r[:3]
            nm = r[3] if len(r) > 3 else n(v)
            assert nm, (vnum, v)
            rr.append((v, c, w, nm))
        out.append((vnum, title, rr))
    return out


def write_sig(byv):
    L = ['# MT2009_PLUS_YOHARA_ITEMS1_V1: the chests among the drops of Opuszczona Twierdza and Dongan - their contents',
         '# as on their pl-wiki pages (cache/yohara/wiki/items), one thing an opening, by weight (ours: the wiki gives no',
         '# odds; Owsap has no group for them). GENERATED by tools/yohara_items/gen_yitems.py - do not edit.',
         '# Appended to special_item_group.txt by the Dockerfile (share: Yohara - Opuszczona Twierdza, Dongan).', '']
    for vnum, title, rows in chests(byv):
        L.append('Group\tMT2009_yitems_%d' % vnum)
        L.append('{')
        L.append('\tVnum\t%d -- %s' % (vnum, title))
        for k, (v, c, w, nm) in enumerate(rows, 1):
            L.append('\t%d\t%s\t%d\t%d -- %s' % (k, v, c, w, nm))
        L.append('}')
        L.append('')
    with open(SIG_OUT, 'w', encoding='utf-8', newline='\n') as f:
        f.write('\n'.join(L))


# -- the drops (mob_drop_item, Type drop: vnum, count, percent) ---------------------------------------------------
POT = [(27007, 10, 2, 'Czerwona Mikstura (XXL) x10'), (27008, 10, 2, 'Niebieska Mikstura (XXL) x10')]
WILL = [(v, 1, 0.04) for v in (81000, 81300, 81250, 81550)]
UPG = [(72353, 1, 1), (31216, 1, 0.5), (31218, 1, 0.5), (31224, 1, 0.5), (31217, 1, 0.5)]
HERB = {'mrok': (50738, 1, 0.5), 'lod': (95734, 1, 0.5), 'ogien': (95733, 1, 0.5)}
VEIN = (72354, 1, 0.04)
BOSS_WEAPONS = [(v + lv, 1, w, '%s+%d' % (nm, lv)) for v, nm in WEAPON567[::-1] for lv, w in ((5, 30), (6, 20))]


def mob(element, herbs=True, vein=True, pots=True, extra=()):
    r = (POT if pots else []) + WILL + UPG
    if herbs:
        r = r + [HERB[element]]
    if vein:
        r = r + [VEIN]
    return r + list(extra)


BOSS_UPG = [(72353, 2, 40), (31247, 1, 10), (31248, 1, 10), (31249, 1, 10), (31250, 1, 10), (31216, 2, 20),
            (31218, 2, 20), (31224, 2, 20), (31217, 2, 20)]
BOSS_COMMON = [(50513, 1, 15, 'Kamien Duchowy'), (70038, 20, 15, 'Peleryna Mestwa x20'), (39002, 1, 20),
               (70014, 1, 25, 'Pigulka Krwi'), (50528, 1, 20)]
BIG_POTS = [(27003, 10, 200, 'Czerwona Mikstura(D) x10'), (27002, 50, 100, 'Czerwona Mikstura(S) x50'),
            (27007, 50, 100, 'Czerwona Mikstura (XXL) x50'), (27006, 20, 150, 'Niebieska Mikstura(D) x20'),
            (27005, 30, 100, 'Niebieska Mikstura(S) x30'), (27008, 30, 100, 'Niebieska Mikstura (XXL) x30')]
LEATHER = [(31251, 1, 10), (31252, 1, 5)]
CHARISMA = [(50338, 1, 5), (50339, 1, 3), (50340, 1, 2)]
INSPIRATION = [(50341, 1, 5), (50342, 1, 3), (50343, 1, 2)]
TROLL_BOSS = [(31227, 1, 15), (31245, 1, 10), (31246, 1, 10)]


def drops():
    d = []
    # Opuszczona Twierdza - the wiki's (mrok) pages; the (lod) ones (no page) the same with the ice herb
    for v, nm in ((6686, 'Jin Bing'), (6687, 'Zolnierz Ki'), (6688, 'Zolnierz Mao'), (6689, 'Zolnierz Gong'),
                  (6690, 'Mag Frontowy')):
        d.append((v, nm + ' (mrok)', mob('mrok')))
        d.append((v + 7, nm + ' (lod)', mob('lod')))
    # Dongan - Piekielny Pies and the trolls (the wiki: the trolls give no potion; ours kept them); Dreczony Duch
    for v, nm in ((6700, 'Piekielny Pies'), (6701, 'Troll Zolnierz'), (6702, 'Troll Wojownik'),
                  (6703, 'Troll Strzelec'), (6704, 'Troll Szamanka')):
        d.append((v, nm + ' (mrok)', mob('mrok')))
        d.append((v + 11, nm + ' (ogien)', mob('ogien')))
    d.append((6710, 'Dreczony Duch', POT + UPG[:1] + [(95601, 1, 1, 'Stabilne Sznury')] + UPG[1:] +
              [(39080, 1, 0.06), (39078, 1, 0.06), (39079, 1, 0.06), HERB['mrok'], WILL[3]]))
    # bosses: weapons +5/+6 (the Lycan's Szpon Gryfa / Szpon Skarabeusza out - no Lycan here)
    kao = BOSS_WEAPONS + BOSS_UPG + LEATHER + [(95601, 1, 20, 'Stabilne Sznury')] + CHARISMA + \
        [(50513, 1, 15, 'Kamien Duchowy'), (70048, 1, 15, 'Peleryna Maskujaca'), (70038, 20, 15, 'Peleryna Mestwa x20'),
         (39002, 1, 20), (70014, 1, 25, 'Pigulka Krwi'), (50528, 1, 20), (50529, 1, 10)]
    d.append((6691, 'Kao (mrok)', kao))
    d.append((6698, 'Kao (lod)', kao))
    bao = BOSS_WEAPONS + BIG_POTS + BOSS_UPG + LEATHER + [(95601, 1, 20, 'Stabilne Sznury')] + CHARISMA + \
        [(50513, 1, 15, 'Kamien Duchowy'), (50300, 1, 25, 'Ksiega Umiejetnosci'), (70048, 1, 15, 'Peleryna Maskujaca'),
         (70038, 20, 15, 'Peleryna Mestwa x20'), (39002, 1, 20), (70014, 1, 25, 'Pigulka Krwi'), (72006, 1, 20),
         (50528, 1, 20), (50529, 1, 10), (95926, 50, 20, 'Kamyki x50'), (95734, 5, 15, 'Mrozny Korzonek x5'),
         (70434, 1, 5)]
    d.append((6692, 'Krol Bao (misja)', bao))
    d.append((6699, 'Krol Bao', bao))
    argos = BOSS_WEAPONS + BIG_POTS + BOSS_UPG + TROLL_BOSS + LEATHER + \
        [(50662, 1, 10), (50661, 1, 10), (50513, 1, 15, 'Kamien Duchowy'), (95926, 50, 20, 'Kamyki x50'),
         (50325, 1, 10), (50300, 1, 25, 'Ksiega Umiejetnosci'), (70048, 1, 15, 'Peleryna Maskujaca'),
         (70038, 20, 15, 'Peleryna Mestwa x20'), (39002, 1, 20), (70014, 1, 25, 'Pigulka Krwi'), (72006, 1, 20),
         (50528, 1, 20), (50338, 1, 5), (70408, 1, 5), (70434, 1, 5)]
    d.append((6706, 'Argos (mrok)', argos))
    d.append((6717, 'Argos (ogien)', argos + [(95733, 1, 15)]))
    natanan = BOSS_WEAPONS + BIG_POTS + BOSS_UPG + TROLL_BOSS + LEATHER + \
        [(50513, 1, 15, 'Kamien Duchowy'), (50325, 1, 10), (39002, 1, 20), (72006, 1, 20), (50528, 1, 20),
         (50529, 1, 10)] + CHARISMA + INSPIRATION
    d.append((6705, 'Natanan (mrok)', natanan))
    d.append((6716, 'Natanan (ogien)', natanan))
    # Metins
    d.append((8067, 'Metin Swiadomosc', [(27007, 5, 200, 'Czerwona Mikstura (XXL) x5'),
                                         (27008, 5, 200, 'Niebieska Mikstura (XXL) x5')] +
              [(v, 1, 1) for v in range(50569, 50576)] + INSPIRATION +
              [(50664, 1, 10), (28046, 1, 10), (50513, 1, 50, 'Kamien Duchowy'), (50525, 1, 5), (50325, 1, 10),
               (50300, 1, 50, 'Ksiega Umiejetnosci'), (70014, 1, 50, 'Pigulka Krwi'), (50324, 1, 5), (50323, 1, 5),
               (50043, 1, 5), (50662, 1, 10), (50661, 1, 10), (72354, 1, 5)]))
    d.append((8625, 'Posterunek Trolli', [(27007, 5, 200, 'Czerwona Mikstura (XXL) x5'),
                                          (27008, 5, 200, 'Niebieska Mikstura (XXL) x5')] +
              [(v, 1, 2) for v in (81000, 81300, 81250, 81550)] +
              [(39068, 1, 10), (50513, 1, 50, 'Kamien Duchowy'), (50525, 1, 5)]))
    return d


def write_drops(byv):
    L = ['// MT2009_PLUS_YOHARA_MAPS1_V1 / MT2009_PLUS_YOHARA_ITEMS1_V1: drops of Opuszczona Twierdza (374) and Dongan (373) -',
         '// the pl-wiki lists of each monster and Metin (cache/yohara/wiki/*.raw) with the items yohara_items.sql adds',
         '// (the owner, 13 October 2026: every item that drops there). GENERATED by tools/yohara_items/gen_yitems.py -',
         '// do not edit. Owsap gives these monsters no drop. The wiki gives the counts, not the odds - the percents are',
         '// ours: a boss as Czerwony Wodz (3591, MT2009_panel_3591_drop); a monster (the owner, 14 October: the first',
         '// lists were "strasznie przesadzone", 7.55% a kill at 100%) its potions 2 (x10), Topaz Woli 1, a plate or Rog',
         '// Trolla 0.5, the element\'s herb 0.5 (dark Mroczny Ciern, ice Mrozny Korzonek, fire Ognisty Lisc - the wiki\'s',
         '// rule), a Talizman Woli +0 0.04 each, Przenosna Zyla Jadeitu 0.04. A "drop" percent P is P/400 a kill at',
         '// mob_item 100 (P * 10000 * rate against 4 000 000): 0.93% a kill for something not a potion (Topaz 0.25%,',
         '// a plate 0.125%, a talisman 1 in 2 500 kills), 1.0% for the potions - the Cape\'s monsters (3001-3705) 0.5%.',
         '// The Dockerfile step',
         '// "Yohara: Opuszczona Twierdza, Dongan" stops the build if any of these monsters has a group already.',
         '// Left out: Odlamki 39070-39077 (wiki: every monster) stay with the Seon-Hae event, which drops them by level;',
         '// the Lycan\'s Szpon Gryfa / Szpon Skarabeusza (no Lycan here); Lekarstwo (Dongan) of the quest Metin.', '']
    sys.path.insert(0, os.path.join(REPO, 'tools', 'yskill9'))
    import talent  # noqa: E402  (MT2009_PLUS_SKILL9_TALENT_V1: Mikstura Talentu's rows)
    for v, nm, rows in talent.with_talent(drops(), named=True):
        L.append('Group\tMT2009_ymaps_%d' % v)
        L.append('{')
        L.append('\tMob\t%d\t-- %s' % (v, nm))
        L.append('\tType\tdrop')
        for k, r in enumerate(rows, 1):
            iv, c, p = r[:3]
            name = r[3] if len(r) > 3 else (byv[iv]['name'] if iv in byv else EXISTING[iv]) + (' x%d' % c if c > 1 else '')
            ps = ('%g' % p)
            L.append('\t%d\t%d\t%d\t%s\t-- %s' % (k, iv, c, ps, name))
        L.append('}')
        L.append('')
    with open(DROP_OUT, 'w', encoding='utf-8', newline='\n') as f:
        f.write('\n'.join(L))


if __name__ == '__main__':
    main()
