#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""gen_yitems_d4.py [--owsap DIR] [--gf DIR]

MT2009_PLUS_YOHARA_DUNG4_V1: the items of Jaskinie Gnolli and Wieza Sung Mahi (ydung4_data.py) - every item the pl-wiki
lists as a drop of the caves' monsters and bosses, the chests' contents and the tower's task items, that our world did
not have; the official vnums and numbers of Owsap v6.2.6 (Server/Server/db/item_proto.txt), the Polish names and
descriptions of its Polish client (= the official translation), the icons of the GF 26.1.11 client - the method of
tools/yohara_maps3/gen_yitems3.py. The wiki gives no odds: the percents are ours, official-like (rare; the test
server's 500% drop event is not compensated for).

Writes (all GENERATED - edit this file, run it again):
  linux-port/docker/mariadb/playerbot/yohara_items_d4.sql               world.item_proto (INSERT IGNORE)
  linux-port/docker/game/yohara_dung4/mob_drop_item.yohara_dung4.txt    the caves' monsters' and bosses' drops
  linux-port/docker/game/yohara_dung4/special_item_group.yohara_dung4.txt the four chests' contents
  tools/yohara_dung4/yohara_items_d4.json                               the client's records, item_list, itemdesc
  client-patches/client-2.0.30/root/icon/item/<icon>.tga                the GF icons our packs lack

Left out (no system / no item here - the owner's rule: nothing invented): Odlamki 39070-39077 (the Seon-Hae event's,
as every Yohara batch), Bohat. Ksiega Zwierza (no vnum in any source), Torba Emocji and Akcja Piekielnej Wiezy (the
emotion packs), Szklo Detekcji, Male Blogoslawienstwo / Blogoslawienstwo (a 6th/7th bonus changer - our
USE_CHANGE_ATTRIBUTE2 is an ordinary changer), Spirala Czasu (the biologist's waiting time), Mikstura Ataku +20, the
jade necklaces / earrings / bracelets of Skrzynia Labiryntowa, EXP Czempiona from a chest.

Example: python3 tools/yohara_dung4/gen_yitems_d4.py
"""
import argparse
import json
import os
import shutil
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(os.path.dirname(HERE))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(REPO, 'tools', 'yohara_items'))
import gen_yitems as Y  # noqa: E402  (the engine's numbers, the row writer)
import ydung4_data as D  # noqa: E402

SQL_OUT = os.path.join(REPO, 'linux-port', 'docker', 'mariadb', 'playerbot', 'yohara_items_d4.sql')
DROP_OUT = os.path.join(REPO, 'linux-port', 'docker', 'game', 'yohara_dung4', 'mob_drop_item.yohara_dung4.txt')
SIG_OUT = os.path.join(REPO, 'linux-port', 'docker', 'game', 'yohara_dung4', 'special_item_group.yohara_dung4.txt')
JSON_OUT = os.path.join(HERE, 'yohara_items_d4.json')
ICON_OUT = os.path.join(REPO, 'client-patches', 'client-2.0.30', 'root', 'icon', 'item')
EARLIER_JSON = [os.path.join(REPO, 'tools', 'yohara_items', 'yohara_items.json'),
                os.path.join(REPO, 'tools', 'yohara_items', 'yohara_items2.json'),
                os.path.join(REPO, 'tools', 'yohara_maps3', 'yohara_items3.json')]
HAVE_ICONS = set(('boss_box.tga',))     # Skrzynia Labiryntowa's: our packs have it (tools/yohara_items)

ST = Y.ST
TYPES = dict(Y.TYPES, ITEM_TREASURE_BOX=20, ITEM_TREASURE_KEY=21, ITEM_PET=37, ITEM_RESOURCE=14)
SUBTYPES = dict(Y.SUBTYPES, USE_REMOVE_AFFECT=0, UNIQUE_NONE=0)
LIMIT_CONQUEROR_LEVEL = 10     # common/item_length.h (MT2009_PLUS_CHAMPION_V2, czempion): Owsap's NEWWORLD_LEVEL


def need(s):
    return 'needs: ' + s


ITEMS = []


def add(vnum, src=None, name=None, status=ST, **over):
    ITEMS.append(dict(vnum=vnum, src=src or vnum, name=name, status=status, over=over))


QUEST = dict(type='ITEM_QUEST', subtype='QUEST_NONE')
GLOVES = 'the Sung Ma gloves (Wytwarzanie Rekawic) - none here yet'
add(30606, status=need('the armour crafting of the En-Tai / Ochao (Srebrne Plyty) - none here yet'))
add(30608, status=need('the armour crafting of the En-Tai / Ochao (Stalowe Plyty) - none here yet'))
add(31225, status=need(GLOVES))                               # Kamien Runiczny - the 50th floor's reward
for v in (31253, 31254, 31255, 31256):                        # Skrzynia Mistrza Gnolli / Ahtrina, Zdobiona Zlotem,
    add(v)                                                    # Labiryntowa - chests (special_item_group)
add(70403, **QUEST)                                           # Zagadkowy Klucz - the tower's task (quest)
add(70404, **QUEST)                                           # Kam. Pieczeci Sunga Mahi - the tower's task (quest)
add(70405, **QUEST)                                           # Antidotum SungMa - the tower's curse (quest)

# items we have (official vnums or ours): their names in the drop file
EXISTING = {
    81000: 'Talizman Woli SILA+0', 81300: 'Talizman Woli WIT+0', 81250: 'Talizman Woli ODP+0',
    81550: 'Talizman Woli INT+0', 31217: 'Rog Trolla', 31245: 'Twarda Skora', 31246: 'Wzor Rekawicy',
    31247: 'Czerwona Runa SungMa', 31248: 'Liliowa Runa SungMa', 31249: 'Niebieska Runa SungMa',
    31250: 'Zielona Runa SungMa', 31251: 'Utwardzacz Skory', 31252: 'Utwardzacz Skory+', 50737: 'Ziemne Pnacze',
    39080: 'Zolty Lsniacy Odlamek', 50513: 'Kamien Duchowy', 70401: 'Sztandar Czaszki',
    70434: 'Zwoj Skarbu (Stopien A)', 27003: 'Czerwona Mikstura(D)', 27002: 'Czerwona Mikstura(S)',
    27006: 'Niebieska Mikstura(D)', 27005: 'Niebieska Mikstura(S)', 27007: 'Czerwona Mikstura (XXL)',
    27008: 'Niebieska Mikstura (XXL)', 50338: 'Charyzma Nowicjusza', 50339: 'Charyzma Adepta',
    50340: 'Charyzma Eksperta', 50341: 'Inspiracja Nowicjusza', 50342: 'Inspiracja Adepta',
    50343: 'Inspiracja Eksperta', 50529: 'Skrzynia Ksiag (9.skill)', 95926: 'Kamyki', 71095: 'Przepustka',
    71130: 'Przepustka (zdatna do handlu)', 27992: 'Biala Perla', 27993: 'Niebieska Perla', 27994: 'Krwawa Perla',
    71015: 'Pierscien Doswiadczenia', 70014: 'Pigulka Krwi', 70043: 'Rekawica Zlodzieja', 100700: 'Smoczy Plomien (B)',
    80019: 'Delikatne Sukno', 31216: 'Plyta z Surowego Metalu', 31218: 'Plyta ze Stali Kuzniczej',
    31224: 'Plyta ze Stali Ozdobnej', 50325: 'Ksiega Precyzji', 72353: 'Topaz Woli', 'gold': 'Yang',
}


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
    gf_list = {}
    for r in Y.read_tsv(os.path.join(a.gf, 'shared/common/item_list.txt')):
        if len(r) >= 3 and r[0].strip().isdigit():
            gf_list[int(r[0])] = r[2].strip()
    earlier = set()
    for p in EARLIER_JSON:
        earlier |= set(i['vnum'] for i in json.load(open(p, encoding='utf-8'))['items'])
    items = []
    for it in ITEMS:
        assert it['vnum'] not in earlier, it['vnum']
        o = proto[it['src']]
        ov = it['over']
        pl, text = desc.get(it['src'], ('', ''))
        name = it['name'] or pl
        assert name and len(name.encode('cp1250')) <= 24, (it['vnum'], name)
        typ = TYPES[ov.get('type', o['Type'])]
        st = ov.get('subtype', o['SubType'])
        sub = SUBTYPES.get(st, 0) if st not in ('UNK23_1', 'UNK23_2', 'UNK17_1') else 0
        if typ == 23 and o['SubType'] not in ('UNK23_1', '0'):
            raise SystemExit('%d: giftbox subtype %s' % (it['vnum'], o['SubType']))
        anti = Y.flags(o['AntiFlags'], Y.ANTI, 'antiflag')
        if it['status'] != ST:
            anti &= ~Y.ANTI_TRADE
        flag = Y.flags(o['Flags'], Y.FLAGS, 'flag')
        if typ == 18:
            flag |= Y.FLAGS['ITEM_QUEST_USE']
        wear = Y.flags(ov.get('wear', o['WearFlags']), Y.WEAR, 'wearflag')
        lim = []
        for k in (0, 1):
            t = o['LimitType%d' % k]
            if t == 'NEWWORLD_LEVEL':
                lim.append((LIMIT_CONQUEROR_LEVEL, int(o['LimitValue%d' % k])))
            else:
                lim.append((Y.LIMITS.get(t, 0), int(o['LimitValue%d' % k])))
        for i in range(3):
            t = o['ApplyType%d' % i]
            if t not in ('A_NONE', 'APPLY_NONE'):
                raise SystemExit('%d: apply %s not mapped' % (it['vnum'], t))
        values = [int(o['Value%d' % i]) for i in range(6)]
        if typ in (5, 18):                              # an inert material / a quest item keeps no values
            values = [0] * 6
        stackable = bool(flag & Y.FLAGS['ITEM_STACKABLE'])
        icon = gf_list.get(it['src'])
        assert icon, it['vnum']
        icon_file = os.path.basename(icon)
        items.append(dict(
            vnum=it['vnum'], src=it['src'], status=it['status'], name=Y.ascii_name(name), locale_name=name,
            type=typ, subtype=sub, stack=200 if stackable else 1, weight=0, size=int(o['Size']), antiflag=anti,
            flag=flag, wearflag=wear, gold=int(o['ShopBuyPrice']), shop_buy_price=int(o['ShopSellPrice']),
            refined_vnum=int(o['RefinedVnum']), refine_set=int(o['RefineSet']),
            magic_pct=int(o['AlterToMagicItemPercent']), specular=int(o['Specular']),
            socket_pct=int(o['GainSocketPercent']), addon_type=0,
            limittype0=lim[0][0], limitvalue0=lim[0][1], limittype1=lim[1][0], limitvalue1=lim[1][1],
            applytype0=0, applyvalue0=0, applytype1=0, applyvalue1=0, applytype2=0, applyvalue2=0,
            **dict(('value%d' % i, values[i]) for i in range(6)),
            icon='icon/item/' + icon_file, icon_src=icon, desc=text, list_type='ETC'))
    byv = dict((i['vnum'], i) for i in items)
    assert len(byv) == len(items)
    write_sql(items)
    write_json(items)
    copy_icons(items, a.gf)
    write_sig(byv)
    write_drops(byv)
    print('items %d (%d work, %d need a system)' % (len(items), sum(1 for i in items if i['status'] == ST),
                                                    sum(1 for i in items if i['status'] != ST)))
    for i in items:
        if i['status'] != ST:
            print('  %d %s: %s' % (i['vnum'], i['name'], i['status']))


def write_sql(items):
    L = ['-- MT2009_PLUS_YOHARA_DUNG4_V1: the items of Jaskinie Gnolli and Wieza Sung Mahi that our world did not have -',
         '-- drops, the chests, the tower\'s task items. GENERATED by tools/yohara_dung4/gen_yitems_d4.py - do not edit,',
         '-- rerun it. Every start (apply.sh), idempotent: INSERT IGNORE. Source: Owsap v6.2.6 db/item_proto.txt (the',
         '-- official vnums and numbers), the Polish names of its Polish client; every vnum free in our world (the test',
         '-- server\'s world and every earlier Yohara batch, 14 October 2026). The chests open from the 1st Poziom',
         '-- Czempiona (LIMIT_CONQUEROR_LEVEL 10 = Owsap\'s NEWWORLD_LEVEL). An item whose system we do not have is an',
         '-- inert, tradeable material and does nothing yet - its row says what it waits for:']
    for i in items:
        if i['status'] != ST:
            L.append('--   %d %s - %s' % (i['vnum'], i['name'], i['status'][len('needs: '):]))
    L.append('SET NAMES utf8mb4;')
    L.append('INSERT IGNORE INTO world.item_proto (%s) VALUES' % ','.join('`%s`' % c for c in Y.COLS))
    L.append(',\n'.join(Y.sqlrow(i) for i in items) + ';')
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


def copy_icons(items, gf):
    os.makedirs(ICON_OUT, exist_ok=True)
    for i in items:
        if os.path.basename(i['icon']) in HAVE_ICONS:
            continue
        dst = os.path.join(ICON_OUT, os.path.basename(i['icon']))
        src = os.path.join(gf, i['icon_src'].replace('\\', '/'))
        assert os.path.isfile(src), src
        if not os.path.exists(dst):
            shutil.copyfile(src, dst)


def nm(byv, v, c=1):
    n = byv[v]['name'] if v in byv else EXISTING[v]
    return n + (' x%d' % c if c > 1 else '')


# -- the chests (special_item_group): one thing an opening, by weight (ours: the wiki gives no odds); what our world
#    lacks is left out (the head of this file) ---------------------------------------------------------------------
RUNES = [(31247, 1, 10), (31248, 1, 10), (31249, 1, 10), (31250, 1, 10)]
LEATHER = [(31251, 1, 10), (31252, 1, 6), (31245, 1, 12), (31245, 2, 6), (31246, 1, 12), (31246, 2, 6)]
CHARISMA = [(50338, 1, 6), (50339, 1, 4), (50340, 1, 2), (50341, 1, 6), (50342, 1, 4), (50343, 1, 2)]


def chests(byv):
    g = []
    g.append((31253, 'Skrzynia Mistrza Gnolli (Gnoll Kapitan) - left out: Torba Emocji, Mikstura Ataku +20, EXP '
                     'Czempiona',
              LEATHER + RUNES + [(70401, 1, 6), (50513, 1, 8), (27006, 20, 10), (27003, 20, 10), (50529, 1, 3),
                                 ('gold', 200000, 10), ('gold', 400000, 6)] + CHARISMA))
    g.append((31254, 'Skrzynia Mistrza Ahtrina (Ahtrin Kapitan) - left out: Torba Emocji, Szklo Detekcji, EXP '
                     'Czempiona',
              LEATHER + RUNES + [(70401, 1, 6), (50513, 1, 8), (95926, 50, 8), (71095, 1, 6), (50529, 1, 3),
                                 (50338, 1, 6), (50340, 1, 2), (50341, 1, 6), (50343, 1, 2), (27006, 50, 10),
                                 (27003, 50, 10), ('gold', 200000, 10), ('gold', 400000, 6)]))
    g.append((31255, 'Skrzynia Zdobiona Zlotem (Ahtrin Wielki Mistrz (mrok)) - left out: Male Blogoslawienstwo, '
                     'Torba Emocji, EXP Czempiona',
              [(27992, 1, 6), (27993, 1, 6), (27994, 1, 4), (27003, 50, 10), (27006, 50, 10), (50513, 1, 8),
               (71015, 1, 6), (70014, 1, 6), (70043, 1, 6), (50529, 1, 3), (100700, 1, 2), ('gold', 200000, 10),
               ('gold', 400000, 6)] + LEATHER + RUNES + CHARISMA))
    g.append((31256, 'Skrzynia Labiryntowa (Ahtrin Wielki Mistrz) - left out: the jade necklaces, bracelets and '
                     'earrings (Kolia / Obrecz / Klipsy Jadeitu Slonca, Mgly)',
              [(80019, 1, 8), (31251, 1, 10), (31224, 1, 8), (31218, 1, 8), (31216, 1, 8), (50325, 1, 4),
               (72353, 1, 8), (27007, 50, 10), (27008, 50, 10), (81000, 1, 3), (81300, 1, 3), (81550, 1, 3),
               (81250, 1, 3), (71130, 1, 6), ('gold', 500000, 10)] + RUNES))
    out = []
    for vnum, title, rows in g:
        assert vnum in byv, vnum
        rr = []
        for v, c, w in rows:
            if v != 'gold':
                assert v in byv or v in EXISTING, (vnum, v)
            rr.append((v, c, w, (EXISTING['gold'] + ' %d' % c) if v == 'gold' else nm(byv, v, c)))
        out.append((vnum, title, rr))
    return out


def write_sig(byv):
    L = ['# MT2009_PLUS_YOHARA_DUNG4_V1: the chests of Jaskinie Gnolli - their contents as on their pl-wiki pages',
         '# (Skrzynia Mistrza Gnolli, Skrzynia Mistrza Ahtrina, Skrzynia Zdobiona Zlotem, Skrzynia Labiryntowa), one',
         '# thing an opening, by weight (ours: the wiki gives no odds). GENERATED by tools/yohara_dung4/gen_yitems_d4.py',
         '# - do not edit. Appended to special_item_group.txt by the Dockerfile (share: Yohara - Jaskinie Gnolli, Wieza',
         '# Sung Mahi).', '']
    for vnum, title, rows in chests(byv):
        L.append('Group\tMT2009_ydung4_%d' % vnum)
        L.append('{')
        L.append('\tVnum\t%d -- %s' % (vnum, title))
        for k, (v, c, w, n) in enumerate(rows, 1):
            L.append('\t%d\t%s\t%d\t%d -- %s' % (k, v, c, w, n))
        L.append('}')
        L.append('')
    with open(SIG_OUT, 'w', encoding='utf-8', newline='\n') as f:
        f.write('\n'.join(L))


# -- the drops (mob_drop_item, Type drop: vnum, count, percent) ----------------------------------------------------
# The scale of the earlier batches (mob_drop_item.yohara_maps3.txt): a monster - a Talizman Woli 0.05 each, a plate /
# Rog Trolla 0.25, Twarda Skora / Wzor Rekawicy 0.15, the herb 0.5, Zolty Lsniacy Odlamek 0.04; a boss (hourly,
# 2-, 3-hourly) its chest always, the rest 2-30 (the test server's 500% event multiplies these; not compensated).
WILL = [(v, 1, 0.05) for v in (81000, 81300, 81250, 81550)]
UPG = [(31217, 1, 0.25), (30606, 1, 0.25), (30608, 1, 0.25), (31245, 1, 0.15), (31246, 1, 0.15)]
LUCENT = [(39080, 1, 0.04)]
HERB = [(50737, 1, 0.5)]
POTIONS = [(27003, 30, 30), (27002, 50, 30), (27006, 20, 30), (27005, 30, 30)]


def drops():
    d = []
    gnoll = WILL + LUCENT + UPG + HERB
    ahtrin = WILL + LUCENT + UPG
    for v in (6800, 6801, 6802, 6803, 6806, 6807, 6808, 6809):
        d.append((v, D.MOBS[v][0], gnoll))
    for v in (6810, 6811, 6812, 6813, 6816, 6817, 6818):
        d.append((v, D.MOBS[v][0], ahtrin))
    d.append((6804, 'Mistrz Gnolli', [(31245, 1, 10), (50513, 1, 15)]))
    d.append((6805, 'Gnoll Kapitan', [(31253, 1, 100)] + POTIONS +
              [(31245, 1, 10), (31246, 1, 10), (70401, 1, 5), (70434, 1, 5)]))
    d.append((6814, 'Ahtrin Kapitan (lvl-126)', [(31254, 1, 100), (31245, 1, 10), (50513, 1, 15)]))
    d.append((6815, 'Ahtrin Kapitan (lvl-127)', [(31254, 1, 100)] + POTIONS +
              [(31245, 1, 10), (31246, 1, 10), (70401, 1, 8)]))
    d.append((6819, 'Ahtrin Wielki Mistrz (ziemia)', [(31256, 1, 100), (31245, 1, 15), (31246, 1, 15),
                                                       (50513, 1, 20), (70434, 1, 8)]))
    d.append((6820, 'Ahtrin Wielki Mistrz (mrok)', [(31256, 1, 100), (31255, 3, 100)] + POTIONS +
              [(31247, 1, 10), (31248, 1, 10), (31249, 1, 10), (31250, 1, 10), (31245, 1, 15), (31246, 1, 15),
               (70401, 1, 10), (70434, 1, 10)]))
    return d


def write_drops(byv):
    L = ['// MT2009_PLUS_YOHARA_DUNG4_V1: drops of Jaskinie Gnolli - the pl-wiki lists of each monster and boss with the',
         '// items yohara_items_d4.sql adds. GENERATED by tools/yohara_dung4/gen_yitems_d4.py - do not edit. Owsap gives',
         '// these monsters no drop. The percents are ours, official-like - the earlier batches\' scale: a monster - a',
         '// Talizman Woli 0.05 each, a plate / Rog Trolla 0.25, Twarda Skora / Wzor Rekawicy 0.15, Ziemne Pnacze 0.5 (the',
         '// gnolls), Zolty Lsniacy Odlamek 0.04; a boss its chest always (Skrzynia Zdobiona Zlotem x3), the rest 5-30.',
         '// Left out: Odlamki 39070-39077 (the Seon-Hae event\'s), Bohat. Ksiega Zwierza (no vnum). Wieza Sung Mahi\'s',
         '// monsters drop nothing on the wiki - its keys, seal stones and antidotes are the quest\'s (wieza_sung_mahi).', '']
    for v, n, rows in drops():
        assert v in D.MOBS, v
        L.append('Group\tMT2009_ydung4_%d' % v)
        L.append('{')
        L.append('\tMob\t%d\t-- %s' % (v, Y.ascii_name(n)))
        L.append('\tType\tdrop')
        seen = set()
        k = 0
        for iv, c, p in rows:
            if iv in seen:
                continue
            seen.add(iv)
            assert iv in byv or iv in EXISTING, (v, iv)
            k += 1
            L.append('\t%d\t%d\t%d\t%s\t-- %s' % (k, iv, c, '%g' % p, nm(byv, iv, c)))
        L.append('}')
        L.append('')
    with open(DROP_OUT, 'w', encoding='utf-8', newline='\n') as f:
        f.write('\n'.join(L))


if __name__ == '__main__':
    main()
