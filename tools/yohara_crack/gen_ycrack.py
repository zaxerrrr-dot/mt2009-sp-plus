#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""gen_ycrack.py [--owsap DIR] [--gf DIR]          (host python3; no LZO needed)

MT2009_PLUS_YOHARA_CRACK_V1: everything the server needs for Statua Szczeliny Czasu and Zaklęty Las (SZC) (ycrack_data.py)
- GENERATED here, never edited by hand:

  linux-port/docker/game/yohara_crack/
    map/metin2_map_boss_crack_dawnmist/  Setting.txt (Owsap's = GF's: MapSize 3 4, BasePosition 332800 1817600),
                                         Town.txt (our entry cell), server_attr (= Zaklęty Las (PB)'s, the same terrain:
                                         GF's dawnmist_dungeon_01 - GF's crack folder has no sector of its own)
    data/dungeon/jotun_szc/*.txt         Owsap's crack_dawnmist_dungeon spawns (npc, regen, stone, boss) - its groups
                                         6401-6407 as ours 6178-6184, the boss group 6408 as 6193 (taken here)
    group.yohara_crack.txt               the eight groups (Owsap's members)
    plateau_npc.txt                      Statua Szczeliny Czasu's line of Płaskowyż Iluzji's npc.txt (the Dockerfile
                                         appends it)
    spawned.txt                          every vnum each map shows (the client builder ycrack reads it)
  linux-port/docker/mariadb/playerbot/
    yohara_crack.sql                     world.mob_proto (INSERT IGNORE) - the SZC monsters, bosses, Metins, NPCs; the
                                         Zegarek Kieszonkowy rows of Handlarka Iluzji's shop
    yohara_crack_zywioly.sql             their element (wind; after zywioly_moby.sql)
    yohara_items_crack.sql               world.item_proto (INSERT IGNORE) - Zegarek Kieszonkowy, the SZC quest items
  tools/yohara_crack/ycrack_client.json  the client's rows (client-2.0.30/tools/ycrack)
  client-patches/client-2.0.30/root/icon/item/<icon>.tga   the GF icons our packs lack

No drop file: the pl-wiki - "W tej lokacji potwory nie dają dropu ... ale w zamian dają więcej Doświadczenia" - the
engine drops nothing on map 404 (server-patches/szczelina) but Jotun Thrym (SZC)'s yang (tr-wiki). Every position the
quests and spawn files use is checked against the server_attr.
"""
import argparse
import csv
import json
import os
import re
import shutil
import struct
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(os.path.dirname(HERE))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(REPO, 'tools', 'yohara_maps'))
sys.path.insert(0, os.path.join(REPO, 'tools', 'yohara_items'))
sys.path.insert(0, os.path.join(REPO, 'tools', 'yohara_iluzja'))
import ycrack_data as D  # noqa: E402
from gen_ymaps_sql import COLS, row_of, npc_row  # noqa: E402
import gen_yitems as Y  # noqa: E402
import gen_yiluzja as YI  # noqa: E402  (client_grid, the PB forest's numbers)

M = 'MT2009_PLUS_YOHARA_CRACK_V1'
OUT = os.path.join(REPO, 'linux-port', 'docker', 'game', 'yohara_crack')
ILUZJA = os.path.join(REPO, 'linux-port', 'docker', 'game', 'yohara_iluzja')
PB = os.path.join(REPO, 'linux-port', 'docker', 'mariadb', 'playerbot')
SQL_OUT = os.path.join(PB, 'yohara_crack.sql')
ZYW_OUT = os.path.join(PB, 'yohara_crack_zywioly.sql')
ITEMS_OUT = os.path.join(PB, 'yohara_items_crack.sql')
JSON_OUT = os.path.join(HERE, 'ycrack_client.json')
ICON_OUT = os.path.join(REPO, 'client-patches', 'client-2.0.30', 'root', 'icon', 'item')
EARLIER_JSON = YI.EARLIER_JSON + [YI.JSON_OUT]

# -- the groups: Owsap's 6401-6408 (group.txt "crack_dawnmist_0x"); 6408-6412 are other groups here -------------------
GROUP_FIX = dict([(6401 + i, 6178 + i) for i in range(7)] + [(6408, 6193)])
REGEN = ['npc.txt', 'regen.txt', 'stone.txt', 'boss.txt']
SUB = 'jotun_szc'
# Władca En-Tai (SZC) - missions 6 and 7: Owsap's boss.txt group (him with his healers, 587,97, 5 min) and, as in
# Zaklęty Las (PB), one more of him in the field
EXTRA_FIELD = [(300, 300)]
# every position the quests use (= linux-port/docker/game/quest/jotun_szc.quest / szczelina_czasu.quest cfg())
QUEST_POINTS = dict(entry=[D.MAP['town']], npcs=[(495, 963), (680, 400), (125, 495), (615, 108)],
                    boss_room=[(99, 941)], boss=[(69, 941)], field=EXTRA_FIELD + [(587, 97)])
QUEST_SPAWNED = [20519, 20520, 20521, 20522, 4265, 4272, 4403]
SUMMONS = [4260, 4263, 4267, 4270, 4271]


def owsap_groups(a):
    t = open(os.path.join(a.owsap, 'share/locale/uk/group.txt'), encoding='latin-1').read().replace('\r', '')
    out = {}
    for m in re.finditer(r'Group\s+(\S+)\s*\{(.*?)\}', t, re.S):
        b = m.group(2)
        v = re.search(r'Vnum\s+(\d+)', b)
        if v and int(v.group(1)) in GROUP_FIX:
            lead = re.search(r'Leader\s+"?[^"\n]*"?\s+(\d+)', b)
            mem = [int(x) for x in re.findall(r'\n\s*\d+\s+"?[^"\n]*?"?\s+(\d+)\s*(?=\n|$)', b)]
            out[int(v.group(1))] = (m.group(1), [int(lead.group(1))] + mem)
    assert sorted(out) == sorted(GROUP_FIX), sorted(out)
    return out


def gen_map(a, report):
    m = D.MAP
    shutil.rmtree(os.path.join(OUT, 'map'), ignore_errors=True)       # README.md (by hand) stays
    shutil.rmtree(os.path.join(OUT, 'data'), ignore_errors=True)
    dst = os.path.join(OUT, 'map', m['folder'])
    os.makedirs(dst)
    st = open(os.path.join(a.owsap, 'share/locale/uk/map', m['owsap'], 'Setting.txt'), encoding='latin-1').read()
    assert re.search(r'MapSize\s+%d\s+%d' % m['size'], st) and re.search(r'BasePosition\s+%d\s+%d' % m['base'], st)
    gfst = open(os.path.join(a.gf, m['folder'], 'setting.txt'), encoding='latin-1').read()
    assert re.search(r'MapSize\s+%d\s+%d' % m['size'], gfst) and re.search(r'BasePosition\s+%d\s+%d' % m['base'], gfst)
    assert 'ParentMapName "%s"' % m['src'] in open(os.path.join(a.gf, m['folder'], 'mapproperty.txt'),
                                                   encoding='latin-1').read()
    assert sorted(os.listdir(os.path.join(a.gf, m['folder']))) == ['mapproperty.txt', 'setting.txt']
    # the PB forest's Setting.txt differs in BasePosition only
    pbst = open(os.path.join(ILUZJA, 'map', m['pb_folder'], 'Setting.txt'), encoding='latin-1', newline='').read()
    assert re.sub(r'BasePosition[^\r\n]*', '', pbst) == re.sub(r'BasePosition[^\r\n]*', '',
                                                             st.replace('\r\n', '\n').replace('\n', '\r\n'))
    open(os.path.join(dst, 'Setting.txt'), 'w', newline='').write(st.replace('\r\n', '\n').replace('\n', '\r\n'))
    open(os.path.join(dst, 'Town.txt'), 'w', newline='').write('%d\t%d\r\n' % m['town'])
    shutil.copyfile(os.path.join(ILUZJA, 'map', m['pb_folder'], 'server_attr'), os.path.join(dst, 'server_attr'))
    W, H, g, LW, LH, walk, own = YI.client_grid(a.gf, dict(m, own_attr=None))
    blocked = []
    for k, pts in QUEST_POINTS.items():
        for x, y in pts:
            assert 0 <= x < LW and 0 <= y < LH, (k, x, y)
            if not walk[y * LW + x]:
                blocked.append('%s %d,%d' % (k, x, y))
    assert not blocked, blocked
    report.append('%d %s: server_attr = %s\'s (terrain %s), quest points %d, none blocked' % (
        m['index'], m['folder'], m['pb_folder'], m['src'], sum(len(v) for v in QUEST_POINTS.values())))
    # the plateau: the statue's cell and the landing
    pm = dict(index=397, folder='metin2_map_labyrinth', src='metin2_map_labyrinth', size=(1, 1))
    W2, H2, g2, LW2, LH2, walk2, own2 = YI.client_grid(a.gf, pm)
    for x, y in (D.STATUE_CELL[:2], D.LANDING):
        assert walk2[y * LW2 + x], ('plateau', x, y)
    x, y, d = D.STATUE_CELL
    open(os.path.join(OUT, 'plateau_npc.txt'), 'w', newline='').write(
        'm\t%d\t%d\t0\t0\t0\t%d\t1m\t100\t1\t%d\r\n' % (x, y, d, D.STATUE))
    report.append('397 plateau: Statua Szczeliny Czasu %d,%d and the landing %d,%d walkable' % ((x, y) + D.LANDING))
    # the spawn files
    groups = owsap_groups(a)
    d2 = os.path.join(OUT, 'data', 'dungeon', SUB)
    os.makedirs(d2)
    n = b = 0
    for fn in REGEN:
        out = []
        for l in open(os.path.join(a.owsap, 'share/data/dungeon/crack_dawnmist_dungeon', fn), encoding='latin-1') \
                .read().replace('\r', '').split('\n'):
            t = l.split('\t')
            if len(t) < 11 or not t[1].strip().isdigit():
                continue
            v = int(t[-1])
            if t[0] in ('g', 'ga'):
                assert v in GROUP_FIX, (fn, l)
                v = GROUP_FIX[v]
            elif t[0] == 'm':
                assert v in D.MOBS or v in D.NPCS, (fn, l)
            else:
                raise SystemExit('%s: %s' % (fn, l))
            t[-1] = str(v)
            t[7] = t[7].replace('ss', 's')
            x, y = int(t[1]), int(t[2])
            assert 0 <= x < LW and 0 <= y < LH, (fn, l)
            n += 1
            b += 0 if walk[y * LW + x] else 1
            out.append('\t'.join(t))
        if fn == 'boss.txt':
            out += ['m\t%d\t%d\t5\t5\t0\t0\t300s\t100\t1\t4265' % p for p in EXTRA_FIELD]
        assert out, fn
        open(os.path.join(d2, fn), 'w', newline='').write(YI.crlf_text(out))
    report.append('data/dungeon/%s: %d spawn points, %d on a blocked centre (the engine finds a free cell around)'
                  % (SUB, n, b))
    # the groups
    L = ['// %s: the spawn groups of Zaklety Las (SZC) - Owsap\'s 6401-6407 as 6178-6184, 6408 as 6193.' % M,
         '// GENERATED by tools/yohara_crack/gen_ycrack.py - do not edit.']
    gm = {}
    for ov in sorted(groups):
        name, mobs = groups[ov]
        v = GROUP_FIX[ov]
        gm[v] = set(mobs)
        L += ['Group\tMT2009_ycr_%s' % name, '{', '\tLeader\t"%s"\t%d' % (YI.ascii_pl(D.MOBS[mobs[0]][0]), mobs[0]),
              '\tVnum\t%d' % v]
        for i, mob in enumerate(mobs[1:], 1):
            assert mob in D.MOBS, (v, mob)
            L.append('\t%d\t"%s"\t%d' % (i, YI.ascii_pl(D.MOBS[mob][0]), mob))
        L += ['}', '']
    open(os.path.join(OUT, 'group.yohara_crack.txt'), 'w', newline='\n').write('\n'.join(L))
    # spawned.txt
    vs = set(QUEST_SPAWNED) | set(SUMMONS)
    for fn in REGEN:
        for l in open(os.path.join(d2, fn), encoding='latin-1'):
            t = l.split()
            v = int(t[-1])
            vs |= gm[v] if t[0] in ('g', 'ga') else {v}
    assert vs <= set(D.MOBS) | set(D.NPCS), sorted(vs - set(D.MOBS) - set(D.NPCS))
    # 4268 / 4269 (Bojownik / Druid En-Tai (SZC-120)): the wiki's Metin Lasu (SZC) summons, no spawn of Owsap's - their
    # rows only (as 4348 / 4349 of the PB forest)
    assert set(D.MOBS) - vs == {4268, 4269}, sorted(set(D.MOBS) - vs)
    lines = ['# %s: every vnum each map shows (the spawn files with their groups unfolded + the quests\' spawns +' % M,
             '# the bosses\' summons) - the client builder (client-patches/client-2.0.30/tools/ycrack) reads it.',
             '# GENERATED by tools/yohara_crack/gen_ycrack.py.', '397 %d' % D.STATUE]
    lines += ['%d %d' % (m['index'], v) for v in sorted(vs)]
    open(os.path.join(OUT, 'spawned.txt'), 'w', newline='\n').write('\n'.join(lines) + '\n')


# ------------------------------------------------------------------------------------------------ mob_proto
SQL_HEAD = """-- %(m)s: Zaklety Las (SZC) (404, Jotun Thrym (SZC)) - the first Time Rift dungeon (the owner, 14 October 2026).
-- GENERATED by tools/yohara_crack/gen_ycrack.py - do not edit, rerun it. Every start (apply.sh, after yohara_iluzja.sql),
-- idempotent: INSERT IGNORE - a row the operator changed is kept. Every vnum was free in our world (14 October 2026).
-- %(n)d rows: %(mobs)d monsters, bosses and stones, %(npcs)d NPCs. Monsters: Owsap v6.2.6 db/mob_proto.txt (the official
-- "TR:" rows - more experience than the PB ones, the pl-wiki's "daja wiecej Doswiadczenia") in our r40250 columns
-- (tools/yohara_maps/gen_ymaps_sql.row_of; the experience Owsap's = the owner's sheet of 20 October); the pl-wiki over
-- Owsap: Jotun Thrym (SZC) summons Niszczyciel En-Tai (SZC-125) (4271); the tr-wiki: Jotun Thrym (SZC) drops 10-27 million Yang - nothing else
-- drops on map 404 (server-patches/szczelina). Names "SZC: ..." as the PB ones. Statua Szczeliny Czasu (20472) is
-- yohara_iluzja.sql's row. Handlarka Iluzji's shop (%(shop)d): Zegarek Kieszonkowy by 1, 10 and 100 (the pl-wiki).
-- The element: yohara_crack_zywioly.sql (after zywioly_moby.sql).
SET NAMES utf8mb4;

"""

ZHEAD = """-- %s: the element of Zaklety Las (SZC) - the pl-wiki's "Element Wiatru" (setRaceFlag bit 16384; Owsap's
-- AttWind 90 agrees). GENERATED by tools/yohara_crack/gen_ycrack.py. apply.sh runs it AFTER zywioly_moby.sql, which
-- clears bits 11-16 of every mob it does not list: idempotent.
SET NAMES utf8mb4;""" % M


def gen_mobs(a, report):
    en = {}
    for line in open(os.path.join(a.owsap, 'db', 'mob_names.txt'), encoding='latin-1'):
        p = line.rstrip('\r\n').split('\t')
        if len(p) >= 2 and p[0].isdigit():
            en[int(p[0])] = p[1]
    rows = {}
    for r in csv.DictReader(open(os.path.join(a.owsap, 'db', 'mob_proto.txt'), encoding='latin-1'), delimiter='\t'):
        if r['Vnum'].isdigit():
            rows[int(r['Vnum'])] = r
    lines = []
    for v in sorted(D.MOBS):
        pl, elem = D.MOBS[v]
        assert len(pl.encode('cp1250')) <= 24, pl
        r = dict(rows[v])
        assert r['Type'] in ('MONSTER', 'STONE'), (v, r['Type'])
        assert (r['AttWind'] == '90') == (elem == D.WIND), v
        assert r['MinGold'] == '0' and r['MaxGold'] == '0', v
        r.update(D.OVERRIDE.get(v, {}))
        lines.append(row_of(r, en[v][:24], pl))
    for v in sorted(D.NPCS):
        en_n, pl = D.NPCS[v]
        assert len(pl.encode('cp1250')) <= 24, pl
        src = rows.get(v)
        assert src and src['Type'] == 'NPC', v
        lines.append(npc_row(v, en_n[:24], pl, src['Folder']))
    assert len(set(t[0] for t in lines)) == len(lines)
    for t in lines:
        assert len(t) == len(COLS), (t[0], len(t))
    with open(SQL_OUT, 'w', encoding='utf-8', newline='\n') as f:
        f.write(SQL_HEAD % dict(m=M, n=len(lines), mobs=len(D.MOBS), npcs=len(D.NPCS), shop=D.MERCHANT_SHOP))
        f.write('INSERT IGNORE INTO world.mob_proto (%s) VALUES\n' % ','.join('`%s`' % c for c in COLS))
        f.write(',\n'.join('(%s)' % ','.join(str(x) for x in t) for t in lines) + ';\n')
        f.write('INSERT IGNORE INTO world.shop_item (`shop_vnum`,`item_vnum`,`count`) VALUES %s;\n' % ','.join(
            '(%d,%d,%d)' % (D.MERCHANT_SHOP, v, c) for v, c in D.WATCH_ROWS))
    winds = sorted(v for v, (pl, e) in D.MOBS.items() if e)
    none = sorted(v for v, (pl, e) in D.MOBS.items() if not e)
    L = [ZHEAD, '-- wiatr: %s' % ','.join(map(str, winds)),
         'UPDATE world.mob_proto SET setRaceFlag = ((setRaceFlag + 0) & ~%d) | %d WHERE vnum IN (%s);'
         % (D.ELEMENT_BITS, D.WIND, ','.join(map(str, winds))),
         '-- no element (the Metins): %s' % ','.join(map(str, none)),
         'UPDATE world.mob_proto SET setRaceFlag = (setRaceFlag + 0) & ~%d WHERE vnum IN (%s) AND '
         '(setRaceFlag + 0) & %d <> 0;' % (D.ELEMENT_BITS, ','.join(map(str, none)), D.ELEMENT_BITS)]
    with open(ZYW_OUT, 'w', encoding='utf-8', newline='\n') as f:
        f.write('\n'.join(L) + '\n')
    report.append('mob_proto rows: %d (monsters/Metins %d, NPCs %d); wind: %d vnums; shop rows %d' % (
        len(lines), len(D.MOBS), len(D.NPCS), len(winds), len(D.WATCH_ROWS)))
    return lines


# ------------------------------------------------------------------------------------------------ the items
DRYAD, TIMBER, DEW, EMERALD, AIDKIT = 31161, 31162, 31163, 31165, 31166
QUEST_ITEMS = [DRYAD, TIMBER, DEW, EMERALD, AIDKIT]
# the pl-wiki's names where Owsap's Polish client differs ("Zabij władcę En-Tai (SZC)": "Szlachetne Drewno (SZC)")
ITEM_NAMES = {TIMBER: 'Szlachetne Drewno (SZC)'}
ITEM_TEXT = {
    D.WATCH: 'Potrzebny, by wejść do lochu Szczeliny Czasu (Statua Szczeliny Czasu na Płaskowyżu Iluzji). Każdy członek '
             'grupy musi go mieć - znika przy wejściu.',
    TIMBER: 'Szlachetne Drewno (SZC) od Władcy En-Tai (SZC). Zanieś je Badaczowi Lasu (SZC).',
    DEW: 'Rosa En-Tai (SZC) od Niszczycieli En-Tai (SZC). Zanieś ją Zwiadowcy Lasu (SZC).',
    EMERALD: 'Drzewny Szmaragd (SZC) od Władcy En-Tai (SZC). Zanieś go Badaczowi Lasu (SZC).',
    AIDKIT: 'Apteczka (SZC) strażników Zaklętego Lasu (SZC).',
}
WATCH_GOLD = 25000                      # the pl-wiki "Handlarka Iluzji": 25.000 Yang a piece


def gen_items(a, report):
    rows = Y.read_tsv(os.path.join(a.owsap, 'db/item_proto.txt'))
    head = rows[0]
    proto = dict((int(r[0]), dict(zip(head, r))) for r in rows[1:] if r and r[0].isdigit())
    desc = {}
    for r in Y.read_tsv(os.path.join(os.path.dirname(os.path.dirname(a.owsap)),
                                     'Client/Client/pack/locale/locale/pl/itemdesc.txt')):
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
    for v in [D.WATCH] + QUEST_ITEMS:
        assert v not in earlier, v
        o = proto[v]
        pl, text = desc.get(v, ('', ''))
        name = ITEM_NAMES.get(v) or pl
        assert name and len(name.encode('cp1250')) <= 24, (v, name)
        typ = Y.TYPES[o['Type']]
        st = o['SubType']
        sub = YI.SUBTYPES[st] if st in YI.SUBTYPES else 0
        anti = Y.flags(o['AntiFlags'].replace('ANTI_MAIL', 'NONE'), Y.ANTI, 'antiflag')
        flag = Y.flags(o['Flags'], Y.FLAGS, 'flag')
        gold = int(o['ShopBuyPrice'])
        if v == D.WATCH:
            # the pl-wiki: NPC trade yes, players / shop / mail no, dropping yes, storage yes, stacking yes
            anti &= ~Y.ANTI['ANTI_DROP']
            gold = WATCH_GOLD
        if v == DRYAD:
            typ, sub = 18, 0            # the quest's item (Owsap: a material) - as Kamień Driad (PB)
        if typ == 18:
            flag |= Y.FLAGS['ITEM_QUEST_USE']
        text = ITEM_TEXT.get(v, text)
        icon = gf_list.get(v)
        assert icon, v
        items.append(dict(
            vnum=v, src=v, status=Y.ST, name=Y.ascii_name(name), locale_name=name, type=typ, subtype=sub,
            stack=200 if flag & Y.FLAGS['ITEM_STACKABLE'] else 1, weight=0, size=int(o['Size']), antiflag=anti,
            flag=flag, wearflag=0, gold=gold, shop_buy_price=int(o['ShopSellPrice']),
            refined_vnum=0, refine_set=0, magic_pct=0, specular=0, socket_pct=0, addon_type=0,
            limittype0=0, limitvalue0=0, limittype1=0, limitvalue1=0,
            applytype0=0, applyvalue0=0, applytype1=0, applyvalue1=0, applytype2=0, applyvalue2=0,
            value0=0, value1=0, value2=0, value3=0, value4=0, value5=0,
            icon='icon/item/' + os.path.basename(icon), icon_src=icon, desc=text, list_type='ETC', model=''))
    assert next(i for i in items if i['vnum'] == D.WATCH)['stack'] >= 100
    L = ['-- %s: Zegarek Kieszonkowy (the Time Rift dungeons\' ticket, Handlarka Iluzji) and the quest items of' % M,
         '-- Zaklety Las (SZC). GENERATED by tools/yohara_crack/gen_ycrack.py - do not edit, rerun it. Every start',
         '-- (apply.sh, after yohara_items_iluzja.sql), idempotent: INSERT IGNORE. Source: Owsap v6.2.6 db/item_proto.txt',
         '-- (the official vnums), the Polish names of its Polish client (Szlachetne Drewno: the pl-wiki\'s), the pl-wiki\'s',
         '-- price (25 000 Yang) and trade rules of Zegarek Kieszonkowy; every vnum free in our world (14 October 2026).',
         'SET NAMES utf8mb4;',
         'INSERT IGNORE INTO world.item_proto (%s) VALUES' % ','.join('`%s`' % c for c in Y.COLS),
         ',\n'.join(Y.sqlrow(i) for i in items) + ';']
    with open(ITEMS_OUT, 'w', encoding='utf-8', newline='\n') as f:
        f.write('\n'.join(L) + '\n')
    os.makedirs(ICON_OUT, exist_ok=True)
    added = 0
    for i in items:
        dst = os.path.join(ICON_OUT, os.path.basename(i['icon']))
        src = os.path.join(a.gf, i['icon_src'].replace('\\', '/'))
        assert os.path.isfile(src), src
        if not os.path.exists(dst):
            shutil.copyfile(src, dst)
            added += 1
    report.append('items %d (%s), icons copied %d' % (len(items), ', '.join(i['locale_name'] for i in items), added))
    return items


def write_client(mob_lines, items):
    keys = ('vnum', 'name', 'locale_name', 'type', 'subtype', 'stack', 'weight', 'size', 'antiflag', 'flag',
            'wearflag', 'gold', 'shop_buy_price', 'refined_vnum', 'refine_set', 'magic_pct', 'specular', 'socket_pct',
            'limittype0', 'limitvalue0', 'limittype1', 'limitvalue1', 'applytype0', 'applyvalue0', 'applytype1',
            'applyvalue1', 'applytype2', 'applyvalue2', 'value0', 'value1', 'value2', 'value3', 'value4', 'value5')
    m = D.MAP
    out = {'cols': list(COLS), 'rows': [list(t) for t in mob_lines],
           'elements': dict((str(v), e) for v, (pl, e) in D.MOBS.items()),
           'atlas': ['%s\t%d\t%d\t%d\t%d' % (m['folder'], m['base'][0], m['base'][1], m['size'][0], m['size'][1])],
           'items': [dict((k, i[k]) for k in keys) for i in items],
           'item_list': dict((str(i['vnum']), '%d\t%s\t%s' % (i['vnum'], i['list_type'], i['icon'])) for i in items),
           'itemdesc': dict((str(i['vnum']), '%d\t%s\t%s' % (i['vnum'], i['locale_name'], Y.client_desc(i)))
                            for i in items)}
    with open(JSON_OUT, 'w', encoding='utf-8', newline='\n') as f:
        json.dump(out, f, ensure_ascii=False, indent=0)
        f.write('\n')


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--owsap', default='/opt/metin2/cache/owsap/Server/Server')
    ap.add_argument('--gf', default='/opt/metin2/cache/gf/Gameforge_26.1.11/_client')
    a = ap.parse_args()
    report = []
    gen_map(a, report)
    mob_lines = gen_mobs(a, report)
    items = gen_items(a, report)
    write_client(mob_lines, items)
    print('\n'.join(report))


if __name__ == '__main__':
    main()
