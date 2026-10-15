#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""gen_yiluzja.py [--owsap DIR] [--gf DIR]     (in the m2pack-lzo image: server_attr is LZO)

MT2009_PLUS_YOHARA_ILUZJA_V1: everything the server needs for Płaskowyż Iluzji, Beran-Setaou (PB) and Jotun Thrym (PB)
(yiluzja_data.py) - GENERATED here, never edited by hand:

  linux-port/docker/game/yohara_iluzja/
    map/<folder>/Setting.txt, Town.txt   Owsap's (= the GF client's MapSize / BasePosition); Town = our entry cell
    map/<folder>/server_attr             the GF client's attr.atr (tools/gf28/srvattr.py): the plateau's own; the
                                         grotto = GF's metin2_map_skipia_dungeon_02 with the awakened map's own
                                         000000/attr.atr (Beran's temple open); the forest = GF's dawnmist_dungeon_01
    map/metin2_map_labyrinth/npc.txt     the plateau's NPCs (the pl-wiki's cells)
    data/dungeon/beran_pb/*.txt          Owsap's awaken_skipia_dungeon spawns (npc, regen, boss - the temple's stones
                                         and Beran's group 4292 are the quest's: one stone of each, Beran's VID)
    data/dungeon/jotun_pb/*.txt          Owsap's awaken_dawnmist_dungeon spawns (npc, regen - its groups 6411-6417 as
                                         ours 6171-6177 -, stone; boss: Władca En-Tai (PB) in the field)
    group.yohara_iluzja.txt              groups 4281-4292 (Owsap's), 6171-6177 (Owsap's 6411-6417 - taken here)
    group_group.yohara_iluzja.txt        groups of groups 4281-4287 (Owsap's)
    mob_drop_item.yohara_iluzja.txt      the pl-wiki's drop lists (+ the de-wiki's plan sources), our odds
    special_item_group.yohara_iluzja.txt Skrzynia Berana-Setaou (PB), Skrzynia Jotuna Thryma (PB)
    cube.yohara_iluzja.txt               Statua Iluzji (the awakening stones), Statua Fabryki Broni (the Dark Dragon
                                         weapons), Statua Kowala Zbroi (the dragon armours and helmets) - Owsap's cube
    spawned.txt                          every vnum each map shows (the client builder yiluzja reads it)
  linux-port/docker/mariadb/playerbot/
    yohara_iluzja.sql                    world.mob_proto (INSERT IGNORE) - monsters, bosses, stones, NPCs; the shop
    yohara_iluzja_zywioly.sql            their elements (after zywioly_moby.sql)
    yohara_items_iluzja.sql              world.item_proto + refine_proto (INSERT IGNORE) - the items our world lacked
  tools/yohara_iluzja/yiluzja_client.json  the client's rows (client-2.0.30/tools/yiluzja)
  client-patches/client-2.0.30/root/icon/item/<icon>.tga   the GF icons our packs lack

Every position the quests and spawn files use is checked against the server_attr made here. Example:
  docker run --rm -v /opt/metin2:/opt/metin2 m2pack-lzo python3 /opt/metin2/git/<tree>/tools/yohara_iluzja/gen_yiluzja.py
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
sys.path.insert(0, os.path.join(REPO, 'tools', 'yohara_chestdrops'))
import chestdrops as CD  # noqa: E402  (MT2009_PLUS_CHEST_DROPS_V1: the chests' rows)
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(REPO, 'tools', 'yohara_maps'))
sys.path.insert(0, os.path.join(REPO, 'tools', 'yohara_items'))
sys.path.insert(0, os.path.join(REPO, 'tools', 'ysets'))
sys.path.insert(0, os.path.join(REPO, 'client-patches', 'client-2.0.28', 'tools', 'gf28'))
import yiluzja_data as D  # noqa: E402
from gen_ymaps_sql import COLS, row_of, npc_row, q  # noqa: E402
import gen_yitems as Y  # noqa: E402
import gen_ysets as YS  # noqa: E402  (the Yohara gear's engine numbers: armour flags, apply points)

M = 'MT2009_PLUS_YOHARA_ILUZJA_V1'
OUT = os.path.join(REPO, 'linux-port', 'docker', 'game', 'yohara_iluzja')
PB = os.path.join(REPO, 'linux-port', 'docker', 'mariadb', 'playerbot')
SQL_OUT = os.path.join(PB, 'yohara_iluzja.sql')
ZYW_OUT = os.path.join(PB, 'yohara_iluzja_zywioly.sql')
ITEMS_OUT = os.path.join(PB, 'yohara_items_iluzja.sql')
JSON_OUT = os.path.join(HERE, 'yiluzja_client.json')
ICON_OUT = os.path.join(REPO, 'client-patches', 'client-2.0.30', 'root', 'icon', 'item')
EARLIER_JSON = [os.path.join(REPO, 'tools', 'yohara_items', 'yohara_items.json'),
                os.path.join(REPO, 'tools', 'yohara_items', 'yohara_items2.json'),
                os.path.join(REPO, 'tools', 'yohara_maps3', 'yohara_items3.json'),
                os.path.join(REPO, 'tools', 'yohara_maps4', 'yohara_items4.json'),
                os.path.join(REPO, 'tools', 'yohara_dung4', 'yohara_items_d4.json'),
                os.path.join(REPO, 'tools', 'ysets', 'yohara_sets.json'),
                os.path.join(REPO, 'tools', 'yohara_pb', 'ypb_client.json'),
                os.path.join(REPO, 'tools', 'ygaya', 'ygaya_items.json')]

# -- the groups (Owsap's group.txt): vnum -> (name, [leader, members...]); Owsap's dawnmist groups 6411-6417 are
#    other groups here (group.txt / group_group.txt) - ours 6171-6177 ------------------------------------------------
GROUPS = {
    4281: ('awaken_skipia_01', [4281, 4280, 4280, 4280]),
    4282: ('awaken_skipia_02', [4282, 4281, 4281, 4280, 4280]),
    4283: ('awaken_skipia_03', [4283, 4282, 4281, 4280]),
    4284: ('awaken_skipia_04', [4284, 4282, 4282, 4281, 4280]),
    4285: ('awaken_skipia_05', [4285, 4283, 4283, 4283]),
    4286: ('awaken_skipia_06', [4286, 4284, 4283, 4283, 4283]),
    4287: ('awaken_skipia_07', [4287, 4284, 4284, 4283, 4283]),
    4288: ('awaken_skipia_08', [4288, 4285, 4284, 4283, 4283]),
    4289: ('awaken_skipia_09', [4289, 4285, 4284, 4283, 4283]),
    4290: ('awaken_skipia_10', [4290, 4286, 4285, 4285, 4283, 4283, 4283]),
    4291: ('awaken_skipia_11', [4286, 4286, 4285, 4285, 4284, 4284, 4283, 4283, 4283]),
    4292: ('awaken_skipia_boss', [4410, 4286, 4286, 4283, 4283, 4283]),
    6171: ('awaken_dawnmist_01', [4340, 4340, 4340, 4340]),
    6172: ('awaken_dawnmist_02', [4341, 4340, 4340]),
    6173: ('awaken_dawnmist_03', [4341, 4341, 4341, 4341]),
    6174: ('awaken_dawnmist_04', [4342, 4341, 4341]),
    6175: ('awaken_dawnmist_05', [4342, 4342, 4342, 4342]),
    6176: ('awaken_dawnmist_06', [4343, 4342, 4341, 4341]),
    6177: ('awaken_dawnmist_07', [4344, 4343, 4343, 4341, 4341]),
}
GROUP_GROUPS = {
    4281: ('awaken_skipia_01', [4281, 4282]),
    4282: ('awaken_skipia_02', [4283, 4284]),
    4283: ('awaken_skipia_03', [4283, 4284]),
    4284: ('awaken_skipia_04', [4285, 4286]),
    4285: ('awaken_skipia_05', [4287, 4288]),
    4286: ('awaken_skipia_06', [4289, 4290]),
    4287: ('awaken_skipia_07', [4290, 4291]),
}
GROUP_FIX = dict((6411 + i, 6171 + i) for i in range(7))
# Owsap's file -> (our sub folder, our file, map index, what to leave out)
REGEN = [
    ('awaken_skipia_dungeon', 'npc.txt', 'beran_pb', 'npc.txt', 398),
    ('awaken_skipia_dungeon', 'regen.txt', 'beran_pb', 'regen.txt', 398),
    ('awaken_skipia_dungeon', 'boss.txt', 'beran_pb', 'boss.txt', 398),
    ('awaken_dawnmist_dungeon', 'npc.txt', 'jotun_pb', 'npc.txt', 371),
    ('awaken_dawnmist_dungeon', 'regen.txt', 'jotun_pb', 'regen.txt', 371),
    ('awaken_dawnmist_dungeon', 'stone.txt', 'jotun_pb', 'stone.txt', 371),
]
# Owsap's dawnmist boss.txt names a group 4352 that does not exist (Bagjanamu is the quest's); Władca En-Tai (PB)
# (4345) - the investigations 6 and 7 - is spawned by nothing in Owsap: two of him in the field here, 5 min respawn
JOTUN_FIELD = [(587, 97), (300, 300)]
# every position the quests use (= linux-port/docker/game/quest/beran_pb.quest / jotun_pb.quest /
# plaskowyz_iluzji.quest cfg())
QUEST_POINTS = {
    397: dict(entry=[(125, 125)], landing=[(150, 95)], npcs=[(x, y) for v, x, y, d in D.PLATEAU_NPCS]),
    398: dict(entry=[(877, 722)], ghost=[(263, 180)], boss_room=[(225, 173)],
              stones=[(170, 160), (190, 180), (170, 182), (192, 160)], boss=[(181, 173)]),
    371: dict(entry=[(478, 970)], npcs=[(495, 963), (680, 400), (125, 495), (615, 108)], boss_room=[(99, 941)],
              boss=[(69, 941)], field=JOTUN_FIELD),
}
QUEST_SPAWNED = {
    397: [v for v, x, y, d in D.PLATEAU_NPCS],
    398: [20530, 8130, 8131, 8132, 8133, 4410, 4287, 4288, 4289, 4290],
    371: [20539, 20540, 20541, 20542, 4345, 4352, 4413],
}
SUMMONS = {398: [4280, 4286], 371: [4340, 4343, 4347, 4350, 4351]}   # mob_proto "summon" of the bosses / captains


def ascii_pl(s):
    return s.translate(str.maketrans('ąćęłńóśźżĄĆĘŁŃÓŚŹŻ', 'acelnoszzACELNOSZZ'))


def crlf_text(lines):
    return '\r\n'.join(lines) + '\r\n' if lines else ''


# ------------------------------------------------------------------------------------------------ the maps
def client_grid(gf, m):
    """the server grid (50-unit cells) of the client's attr.atr: GF's terrain folder, a sector of the awakened map's
    own folder (own_attr) instead of the terrain's where it has one"""
    mw, mh = m['size']
    W, H = mw * 512, mh * 512
    g = bytearray(W * H)
    own = []
    for cy in range(mh):
        for cx in range(mw):
            sec = '%03d%03d' % (cx, cy)
            p = os.path.join(gf, m['src'], sec, 'attr.atr')
            if m.get('own_attr') and os.path.isfile(os.path.join(gf, m['own_attr'], sec, 'attr.atr')):
                p = os.path.join(gf, m['own_attr'], sec, 'attr.atr')
                own.append(sec)
            b = open(p, 'rb').read()
            mg, aw, ah = struct.unpack_from('<3H', b, 0)
            assert (aw, ah) == (256, 256), p
            d = b[6:]
            for y in range(256):
                for x in range(256):
                    v = d[y * 256 + x]
                    if v:
                        gx, gy = cx * 512 + x * 2, cy * 512 + y * 2
                        for dy in (0, 1):
                            o = (gy + dy) * W + gx
                            g[o] = v
                            g[o + 1] = v
    LW, LH = W // 2, H // 2
    walk = bytearray(LW * LH)
    for y in range(LH):
        row = 2 * y * W
        for x in range(LW):
            walk[y * LW + x] = 0 if g[row + 2 * x] & 1 else 1
    return W, H, g, LW, LH, walk, own


def gen_maps(a, report):
    import srvattr as sa
    shutil.rmtree(os.path.join(OUT, 'map'), ignore_errors=True)
    shutil.rmtree(os.path.join(OUT, 'data'), ignore_errors=True)
    walks = {}
    for m in D.MAPS:
        folder = m['folder']
        dst = os.path.join(OUT, 'map', folder)
        os.makedirs(dst)
        st = open(os.path.join(a.owsap, 'share/locale/uk/map', m['owsap'], 'Setting.txt'), encoding='latin-1').read()
        assert re.search(r'MapSize\s+%d\s+%d' % m['size'], st) and \
            re.search(r'BasePosition\s+%d\s+%d' % m['base'], st), folder
        gfst = open(os.path.join(a.gf, folder, 'setting.txt'), encoding='latin-1').read()
        assert re.search(r'MapSize\s+%d\s+%d' % m['size'], gfst) and \
            re.search(r'BasePosition\s+%d\s+%d' % m['base'], gfst), folder
        if m['src'] != folder:
            assert 'ParentMapName "%s"' % m['src'] in open(os.path.join(a.gf, folder, 'mapproperty.txt'),
                                                          encoding='latin-1').read(), folder
            srcst = open(os.path.join(a.gf, m['src'], 'setting.txt'), encoding='latin-1').read()
            assert re.search(r'MapSize\s+%d\s+%d' % m['size'], srcst), m['src']
        open(os.path.join(dst, 'Setting.txt'), 'w', newline='').write(st.replace('\r\n', '\n').replace('\n', '\r\n'))
        open(os.path.join(dst, 'Town.txt'), 'w', newline='').write('%d\t%d\r\n' % m['town'])
        W, H, g, LW, LH, walk, own = client_grid(a.gf, m)
        sa.write_server(os.path.join(dst, 'server_attr'), W, H, g)
        walks[m['index']] = (LW, LH, walk)
        blocked = []
        for k, pts in QUEST_POINTS[m['index']].items():
            for x, y in pts:
                assert 0 <= x < LW and 0 <= y < LH, (folder, k, x, y)
                if not walk[y * LW + x]:
                    blocked.append('%s %d,%d' % (k, x, y))
        assert not blocked, (folder, blocked)
        report.append('%d %s: server_attr %dx%d cells (terrain %s%s), quest points %d, none blocked' % (
            m['index'], folder, W, H, m['src'], (', own attr.atr ' + ','.join(own)) if own else '',
            sum(len(v) for v in QUEST_POINTS[m['index']].values())))
    # the plateau's NPCs
    open(os.path.join(OUT, 'map', 'metin2_map_labyrinth', 'npc.txt'), 'w', newline='').write(crlf_text(
        ['m\t%d\t%d\t0\t0\t0\t%d\t1m\t100\t1\t%d' % (x, y, d, v) for v, x, y, d in D.PLATEAU_NPCS]))
    # the dungeons' spawn files
    stats = {}
    for src, fn, sub, out_fn, idx in REGEN:
        LW, LH, walk = walks[idx]
        dst = os.path.join(OUT, 'data', 'dungeon', sub)
        os.makedirs(dst, exist_ok=True)
        out = []
        for l in open(os.path.join(a.owsap, 'share/data/dungeon', src, fn), encoding='latin-1').read() \
                .replace('\r', '').split('\n'):
            t = l.split('\t')
            if len(t) < 11 or not t[1].strip().isdigit():
                continue
            v = int(t[-1])
            v = GROUP_FIX.get(v, v)
            if t[0] == 'r':
                if v == 8130:
                    continue            # the temple's stones: the quest spawns one of each (beran_pb)
                assert v in GROUP_GROUPS, (fn, l)
            elif t[0] == 'ga' and v == 4292:
                continue                # Beran-Setaou (PB) with his guard: the quest spawns the group (his VID)
            elif t[0] in ('ga', 'g'):
                assert v in GROUPS, (fn, l)
            elif t[0] == 'm':
                assert v in D.MOBS or v in D.NPCS, (fn, l)
            else:
                raise SystemExit('%s: %s' % (fn, l))
            t[-1] = str(v)
            t[7] = t[7].replace('ss', 's')          # Owsap's "3600ss"
            x, y = int(t[1]), int(t[2])
            assert 0 <= x < LW and 0 <= y < LH, (fn, l)
            s = stats.setdefault(sub, [0, 0])
            s[0] += 1
            if not walk[y * LW + x]:
                s[1] += 1
            out.append('\t'.join(t))
        assert out, fn
        open(os.path.join(dst, out_fn), 'w', newline='').write(crlf_text(out))
    # Jotun's forest: Władca En-Tai (PB) in the field (see JOTUN_FIELD)
    open(os.path.join(OUT, 'data', 'dungeon', 'jotun_pb', 'boss.txt'), 'w', newline='').write(crlf_text(
        ['m\t%d\t%d\t5\t5\t0\t0\t300s\t100\t1\t4345' % p for p in JOTUN_FIELD]))
    for sub, (n, b) in sorted(stats.items()):
        report.append('data/dungeon/%s: %d spawn points, %d on a blocked centre (the engine finds a free cell around)'
                      % (sub, n, b))


def write_groups():
    L = ['// %s: the spawn groups of Grota Wygnanców 2 (PB) (Owsap\'s 4281-4292) and Zaklety Las (PB) (Owsap\'s' % M,
         '// 6411-6417 as 6171-6177). GENERATED by tools/yohara_iluzja/gen_yiluzja.py - do not edit.']
    for v, (name, mobs) in sorted(GROUPS.items()):
        L += ['Group\tMT2009_yil_%s' % name, '{', '\tLeader\t"%s"\t%d' % (ascii_pl(D.MOBS[mobs[0]][0]), mobs[0]),
              '\tVnum\t%d' % v]
        for i, mob in enumerate(mobs[1:], 1):
            assert mob in D.MOBS, (v, mob)
            L.append('\t%d\t"%s"\t%d' % (i, ascii_pl(D.MOBS[mob][0]), mob))
        L += ['}', '']
    open(os.path.join(OUT, 'group.yohara_iluzja.txt'), 'w', newline='\n').write('\n'.join(L))
    L = ['// %s: the groups of groups of Grota Wygnanców 2 (PB) - Owsap\'s 4281-4287. GENERATED by' % M,
         '// tools/yohara_iluzja/gen_yiluzja.py - do not edit.']
    for v, (name, gs) in sorted(GROUP_GROUPS.items()):
        L += ['Group\tMT2009_yil_gg_%s' % name, '{', '\tVnum\t%d' % v]
        for i, gv in enumerate(gs, 1):
            assert gv in GROUPS
            L.append('\t%d\t%d\t1' % (i, gv))
        L += ['}', '']
    open(os.path.join(OUT, 'group_group.yohara_iluzja.txt'), 'w', newline='\n').write('\n'.join(L))


def write_spawned():
    lines = ['# %s: every vnum each map of Plaskowyz Iluzji and its two dungeons shows (the spawn files with their' % M,
             '# groups unfolded + the quests\' spawns + the bosses\' summons) - the client builder',
             '# (client-patches/client-2.0.30/tools/yiluzja) reads it. GENERATED by tools/yohara_iluzja/gen_yiluzja.py.']
    gm = dict((v, set(mm)) for v, (n, mm) in GROUPS.items())
    gg = dict((v, set(x for g in gs for x in gm[g])) for v, (n, gs) in GROUP_GROUPS.items())
    for m in D.MAPS:
        idx = m['index']
        vs = set(QUEST_SPAWNED[idx]) | set(SUMMONS.get(idx, []))
        for src, fn, sub, out_fn, i2 in REGEN + [(None, None, 'jotun_pb', 'boss.txt', 371)]:
            if i2 != idx:
                continue
            for l in open(os.path.join(OUT, 'data', 'dungeon', sub, out_fn), encoding='latin-1'):
                t = l.split()
                v = int(t[-1])
                vs |= gg[v] if t[0] == 'r' else gm[v] if t[0] in ('g', 'ga') else {v}
        lines += ['%d %d' % (idx, v) for v in sorted(vs)]
    open(os.path.join(OUT, 'spawned.txt'), 'w', newline='\n').write('\n'.join(lines) + '\n')


# ------------------------------------------------------------------------------------------------ mob_proto
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
        pl, elem, _p = D.MOBS[v]
        assert len(pl.encode('cp1250')) <= 24, pl
        r = rows[v]
        assert r['Type'] in ('MONSTER', 'STONE'), (v, r['Type'])
        # the element: the pl-wiki's = Owsap's AttElec / AttWind 90
        assert (r['AttElec'] == '90') == (elem == D.ELEC) and (r['AttWind'] == '90') == (elem == D.WIND), v
        lines.append(row_of(r, en[v][:24], pl))
    for v in sorted(D.NPCS):
        en_n, pl = D.NPCS[v]
        assert len(pl.encode('cp1250')) <= 24, pl
        src = rows.get(9013 if v == D.MERCHANT else v)
        assert src and src['Type'] == 'NPC', v
        lines.append(npc_row(v, en_n[:24], pl, src['Folder']))
    vn = [t[0] for t in lines]
    assert len(vn) == len(set(vn))
    for t in lines:
        assert len(t) == len(COLS), (t[0], len(t))
    with open(SQL_OUT, 'w', encoding='utf-8', newline='\n') as f:
        f.write(SQL_HEAD % dict(n=len(lines), mobs=len(D.MOBS), npcs=len(D.NPCS), shop=D.MERCHANT_SHOP,
                               npc=D.MERCHANT))
        f.write('INSERT IGNORE INTO world.mob_proto (%s) VALUES\n' % ','.join('`%s`' % c for c in COLS))
        f.write(',\n'.join('(%s)' % ','.join(str(x) for x in t) for t in lines) + ';\n')
        f.write("INSERT IGNORE INTO world.shop (`vnum`,`name`,`npc_vnum`) VALUES (%d,'Handlarka Iluzji',%d);\n"
                % (D.MERCHANT_SHOP, D.MERCHANT))
        f.write('INSERT IGNORE INTO world.shop_item (`shop_vnum`,`item_vnum`,`count`) VALUES %s;\n' % ','.join(
            '(%d,%d,%d)' % (D.MERCHANT_SHOP, v, c) for v, c in D.MERCHANT_ITEMS))
    by = {}
    for v, (pl, elem, _p) in D.MOBS.items():
        if elem:
            by.setdefault(elem, []).append(v)
    L = [ZHEAD]
    for elem in sorted(by):
        L.append('-- %s: %s' % (D.ELEMENT_NAME[elem], ','.join(str(v) for v in sorted(by[elem]))))
        L.append('UPDATE world.mob_proto SET setRaceFlag = ((setRaceFlag + 0) & ~%d) | %d WHERE vnum IN (%s);'
                 % (D.ELEMENT_BITS, elem, ','.join(str(v) for v in sorted(by[elem]))))
    none = sorted(v for v, (pl, elem, _p) in D.MOBS.items() if not elem)
    L.append('-- no element (the Metins - the wiki gives a Metin none): %s' % ','.join(map(str, none)))
    L.append('UPDATE world.mob_proto SET setRaceFlag = (setRaceFlag + 0) & ~%d WHERE vnum IN (%s) AND '
             '(setRaceFlag + 0) & %d <> 0;' % (D.ELEMENT_BITS, ','.join(map(str, none)), D.ELEMENT_BITS))
    with open(ZYW_OUT, 'w', encoding='utf-8', newline='\n') as f:
        f.write('\n'.join(L) + '\n')
    report.append('mob_proto rows: %d (monsters/Metins %d, NPCs %d); elements: %d vnums' % (
        len(lines), len(D.MOBS), len(D.NPCS), sum(len(x) for x in by.values())))
    return lines


SQL_HEAD = """-- MT2009_PLUS_YOHARA_ILUZJA_V1: Plaskowyz Iluzji (397) and the two remaining awakened bosses - Grota Wygnancow 2
-- (PB) (398, Beran-Setaou (PB)) and Zaklety Las (PB) (371, Jotun Thrym (PB)) - the owner, 14 October 2026. GENERATED by
-- tools/yohara_iluzja/gen_yiluzja.py - do not edit, rerun it. Every start (apply.sh), idempotent: INSERT IGNORE - a row
-- the operator changed is kept. Every vnum was free in our world and in every Yohara batch (14 October 2026).
-- %(n)d rows: %(mobs)d monsters, bosses and stones, %(npcs)d NPCs. Monsters: Owsap v6.2.6 db/mob_proto.txt (the official
-- vnums, levels 107-135, HP, damage, exp, the bosses' summons) in our r40250 columns (tools/yohara_maps/
-- gen_ymaps_sql.row_of). Names: Owsap's Polish client ("PB: ..."). NPCs on our NPC numbers (gen_ymaps_sql.npc_row);
-- Handlarka Iluzji is Owsap's 9013 - ours is Pomocnik Zdarzen - as %(npc)d; her shop %(shop)d (the pl-wiki's rows we
-- have; prices: the items' own). Statua Szczeliny Czasu (20472): the row only - the crack dungeons are not added.
-- The elements: yohara_iluzja_zywioly.sql (after zywioly_moby.sql).
SET NAMES utf8mb4;

"""

ZHEAD = """-- MT2009_PLUS_YOHARA_ILUZJA_V1: the elements of the two awakened dungeons (setRaceFlag bits 11-16: 2048 lightning,
-- 16384 wind) as on the pl-wiki ("Zywiol": Beran-Setaou (PB) and the Setaou / Yonghan lightning, Jotun Thrym (PB) and
-- the En-Tai wind; Owsap's AttElec / AttWind agree). GENERATED by tools/yohara_iluzja/gen_yiluzja.py. apply.sh runs it
-- AFTER zywioly_moby.sql, which clears bits 11-16 of every mob it does not list: idempotent.
SET NAMES utf8mb4;"""


# ------------------------------------------------------------------------------------------------ the items
SUBTYPES = dict(Y.SUBTYPES, USE_POTION_NODELAY=11)
PLANS = [31196, 31197, 31198, 31199, 31200, 31201, 31203, 31204, 31205, 31206, 31207, 31209, 31210, 31211, 31212]
# 31202 Plan Pazura, 31208 Plan Zbroi Likana, 31213 Plan Helmu Likana: the Lycan's - no Lycan here
HELMETS = (12780, 12800, 12820, 12840)         # Helm Smoka Mroku / Wiatru / Magii, Boskiego Smoka; 12860: the Lycan's
HELMET_REFINE_SRC = 661                         # Owsap refine_proto 661-675 (= the pl-wiki "Helm Smoka Mroku")
HELMET_REFINE_ID0 = 22660                       # ours: ysets 22600-22659, yohara_items4 from 22701
CHEST_BERAN, CHEST_JOTUN = 31139, 31140
KEY, DRYAD, TIMBER, DEW, SPIRIT, EMERALD, AIDKIT = 31180, 31181, 31182, 31183, 31184, 31185, 31186
MEDAL = 31118                                   # Oznaka Slawy (the dragon armours' recipes, Jotun Thrym (PB))
ITEM_NAMES = {}                                  # Owsap's Polish names (the chests without "(PB)": 24 bytes)
ITEM_TEXT = {
    TIMBER: 'Szlachetne Drzewo (PB) od Władcy En-Tai (PB). Zanieś je Badaczowi Lasu (PB).',
    DEW: 'Rosa En-Tai (PB) od Niszczycieli En-Tai (PB). Zanieś ją Zwiadowcy Lasu (PB).',
    SPIRIT: 'Duch Ziemi (PB) - zapiski strażników Zaklętego Lasu (PB).',
    EMERALD: 'Drzewny Szmaragd (PB) od Władcy En-Tai (PB). Zanieś go Badaczowi Lasu (PB).',
    AIDKIT: 'Apteczka (PB) strażników Zaklętego Lasu (PB).',
}
# items we have (official vnums or ours): their names in the drop files
EXISTING = {
    31108: 'Maly Kamien Przebudzenia', 31109: 'Drobny Kam. Przebudzenia', 31110: 'Ladny Kam. Przebudzenia',
    31111: 'Zacny Kam. Przebudzenia', 31112: 'Silny Kam. Przebudzenia', 31113: 'Dusza Przebudzenia',
    31114: 'Zwykla Skora', 31115: 'Kowadlo', 31117: 'Cienka Przedza', 31120: 'Srodek Scierny', 31121: 'Stal',
    31122: 'Plotno', 31123: 'Cienka Skora', 31124: 'Cienka Nic', 31125: 'Gruba Nic', 31126: 'Czaszka Smoka',
    31127: 'Smoczy Zab', 31130: 'Ostre Kolce', 31131: 'Jedwab', 31132: 'Odlamki', 31133: 'Zwykly Barwnik',
    31134: 'Ulepszony Barwnik', 31135: 'Wyjatkowy Barwnik', 31136: 'Prosty Kamien Chaosu',
    31137: 'Ladny Kamien Chaosu', 31138: 'Wspanialy Kamien Chaosu', 31143: 'Skrzynia Przebudzenia',
    31144: 'Lekarstwo Iluzji', 31145: 'Liscie Zycia', 31149: 'Mocny Sznur',
    50513: 'Kamien Duchowy', 50525: 'Kamien Duchowy+', 27992: 'Biala Perla', 27993: 'Niebieska Perla',
    27994: 'Krwawa Perla', 100700: 'Smoczy Plomien (B)', 25040: 'Zwoj Blogoslawienstwa', 71095: 'Przepustka',
    70012: 'Lza Bogini', 50124: 'Sprochniala Skrzynia', 27102: 'Zielona Mikstura(D)', 27105: 'Fioletowa Mikstura(D)',
    'gold': 'Yang', 'exp': 'EXP',
}
# the Dark Dragon gear the statues craft (Owsap cube.txt npc 20473 / 20474 = pl-wiki "Wytwarzanie Broni / Zbroi"):
# (reward, plan) - the Lycan's left out
WEAPON_RECIPES = [(320, 31196), (340, 31197), (1190, 31198), (2210, 31199), (3230, 31200), (5170, 31201),
                  (7310, 31203)]
ARMOUR_RECIPES = [(21210, 31204), (21230, 31205), (21250, 31206), (21270, 31207)]
HELMET_RECIPES = [(12780, 31209), (12800, 31210), (12820, 31211), (12840, 31212)]
STONES = [(31108, 2), (31109, 5), (31110, 10), (31111, 15), (31112, 25)]   # the awakening stone -> the chance %
CRAFT_GOLD = 2500000
# Statua Iluzji: the awakening stones (Owsap cube npc 20470 = pl-wiki "Plaskowyz Iluzji" "Przedmioty bonusowe")
STONE_RECIPES = [(31108, 5, 31109, 200000, 45), (31109, 3, 31110, 300000, 35), (31110, 2, 31111, 400000, 30),
                 (31111, 1, 31112, 500000, 25)]


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
    # the materials, plans, chests and the quest items (the method of tools/yohara_pb/gen_ypb.py gen_items)
    for v in [MEDAL] + PLANS + [CHEST_BERAN, CHEST_JOTUN, KEY, DRYAD, TIMBER, DEW, SPIRIT, EMERALD, AIDKIT]:
        assert v not in earlier, v
        o = proto[v]
        pl, text = desc.get(v, ('', ''))
        name = ITEM_NAMES.get(v) or pl
        assert name and len(name.encode('cp1250')) <= 24, (v, name)
        typ = Y.TYPES[o['Type']]
        st = o['SubType']
        sub = SUBTYPES[st] if st in SUBTYPES else 0
        assert st in SUBTYPES or st in ('UNK23_1', '0'), (v, st)
        anti = Y.flags(o['AntiFlags'].replace('ANTI_MAIL', 'NONE'), Y.ANTI, 'antiflag')
        flag = Y.flags(o['Flags'], Y.FLAGS, 'flag')
        if typ == 18:
            flag |= Y.FLAGS['ITEM_QUEST_USE']
        if v in (KEY, DRYAD):
            typ, sub = 18, 0            # the quests' items (Owsap: a material) - no drop / give for the stone
        if v in PLANS:
            text = text or ('Plan wytwarzania ekwipunku Smoka Mroku (Statua Fabryki Broni / Statua Kowala Zbroi '
                            'na Płaskowyżu Iluzji).')
        if v in ITEM_TEXT:
            text = ITEM_TEXT[v]
        icon = gf_list.get(v)
        assert icon, v
        items.append(dict(
            vnum=v, src=v, status=Y.ST, name=Y.ascii_name(name), locale_name=name, type=typ, subtype=sub,
            stack=200 if flag & Y.FLAGS['ITEM_STACKABLE'] else 1, weight=0, size=int(o['Size']), antiflag=anti,
            flag=flag, wearflag=0, gold=int(o['ShopBuyPrice']), shop_buy_price=int(o['ShopSellPrice']),
            refined_vnum=0, refine_set=0, magic_pct=0, specular=0, socket_pct=0, addon_type=0,
            limittype0=0, limitvalue0=0, limittype1=0, limitvalue1=0,
            applytype0=0, applyvalue0=0, applytype1=0, applyvalue1=0, applytype2=0, applyvalue2=0,
            value0=0, value1=0, value2=0, value3=0, value4=0, value5=0,
            icon='icon/item/' + os.path.basename(icon), icon_src=icon, desc=text, list_type='ETC', model=''))
    # the dragon helmets +0..+15 (the gear of tools/ysets: gen_ysets.py's numbers; a refine set of their own)
    refine = {}
    with open(os.path.join(os.path.dirname(a.owsap), 'Server', 'db', 'data', 'player.sql'), encoding='latin-1') as f:
        for mm in re.finditer(r'INSERT INTO `refine_proto` VALUES \(([^)]*)\);', f.read()):
            p = [int(x) for x in mm.group(1).split(',')]
            refine[p[0]] = p
    refines = []
    for lv in range(15):
        r = refine[HELMET_REFINE_SRC + lv]
        refines.append(dict(id=HELMET_REFINE_ID0 + lv, mats=[(r[1 + 2 * i], r[2 + 2 * i]) for i in range(5)
                                                              if r[1 + 2 * i]], cost=r[11], prob=r[14]))
    gfl = {}
    for r in Y.read_tsv(os.path.join(a.gf, 'shared/common/item_list.txt')):
        if len(r) >= 3 and r[0].strip().isdigit():
            gfl[int(r[0])] = [x.strip() for x in r[1:]]
    for base in HELMETS:
        for lv in range(16):
            v = base + lv
            assert v not in earlier, v
            o = proto[v]
            pl, text = desc[v]
            assert pl.endswith('+%d' % lv) and len(pl.encode('cp1250')) <= 24, (v, pl)
            assert o['Type'] == 'ITEM_ARMOR' and o['SubType'] == 'ARMOR_HEAD', v
            assert o['LimitType0'] == 'LEVEL' and o['LimitType1'] == 'LIMIT_NONE', v
            assert int(o['RefinedVnum']) == (v + 1 if lv < 15 else 0), v
            assert int(o['RefineSet']) == (HELMET_REFINE_SRC + lv if lv < 15 else 0), v
            applies = []
            for i in range(3):
                t, val = o['ApplyType%d' % i], int(o['ApplyValue%d' % i])
                applies.append((0, 0) if t == 'APPLY_NONE' else (YS.APPLY_NAMES[t], val))
            gl = gfl[v]
            items.append(dict(
                vnum=v, src=v, status=Y.ST, name=Y.ascii_name(pl), locale_name=pl, type=YS.TYPES['ITEM_ARMOR'],
                subtype=YS.SUBTYPES['ARMOR_HEAD'], stack=1, weight=0, size=int(o['Size']),
                antiflag=YS.flags(o['AntiFlags'], YS.ANTI), flag=YS.flags(o['Flags'], YS.FLAGS),
                wearflag=YS.flags(o['WearFlags'], YS.WEAR), gold=int(o['ShopBuyPrice']),
                shop_buy_price=int(o['ShopSellPrice']), refined_vnum=v + 1 if lv < 15 else 0,
                refine_set=HELMET_REFINE_ID0 + lv if lv < 15 else 0, magic_pct=int(o['AlterToMagicItemPercent']),
                specular=int(o['Specular']), socket_pct=int(o['GainSocketPercent']), addon_type=0,
                limittype0=1, limitvalue0=int(o['LimitValue0']), limittype1=0, limitvalue1=0,
                applytype0=applies[0][0], applyvalue0=applies[0][1], applytype1=applies[1][0],
                applyvalue1=applies[1][1], applytype2=applies[2][0], applyvalue2=applies[2][1],
                **dict(('value%d' % i, int(o['Value%d' % i])) for i in range(6)),
                icon=gl[1], icon_src=gl[1], desc=text, list_type=gl[0], model=''))
    byv = dict((i['vnum'], i) for i in items)
    assert len(byv) == len(items)
    # SQL
    L = ['-- %s: the items of Plaskowyz Iluzji and of the awakened Beran-Setaou / Jotun Thrym that our world did' % M,
         '-- not have - Oznaka Slawy, the plans of the Dark Dragon gear (PB: Plan ...), the two chests, the dungeons\' quest',
         '-- items, the dragon helmets +0..+15 (Helm Smoka Mroku / Wiatru / Magii, Helm Boskiego Smoka; refine_proto %d-%d'
         % (refines[0]['id'], refines[-1]['id']),
         '-- = Owsap 661-675). GENERATED by tools/yohara_iluzja/gen_yiluzja.py - do not edit, rerun it. Every start',
         '-- (apply.sh, after yohara_items_pb.sql), idempotent: INSERT IGNORE. Source: Owsap v6.2.6 db/item_proto.txt (the',
         '-- official vnums and numbers; the helmets in our columns as tools/ysets/gen_ysets.py writes the dragon armours),',
         '-- the Polish names of its Polish client; every vnum free in our world and every earlier Yohara batch (14 October',
         '-- 2026). Left out: the Lycan\'s plans (31202, 31208, 31213) and helmet (12860-12875) - no Lycan here.',
         'SET NAMES utf8mb4;',
         'INSERT IGNORE INTO world.item_proto (%s) VALUES' % ','.join('`%s`' % c for c in Y.COLS),
         ',\n'.join(Y.sqlrow(i) for i in items) + ';',
         'INSERT IGNORE INTO world.refine_proto (id,vnum0,count0,vnum1,count1,vnum2,count2,vnum3,count3,vnum4,count4,'
         'cost,src_vnum,result_vnum,prob) VALUES']
    rr = []
    for r in refines:
        mm = r['mats'] + [(0, 0)] * (5 - len(r['mats']))
        rr.append('(%d,%s,%d,0,0,%d)' % (r['id'], ','.join('%d,%d' % x for x in mm), r['cost'], r['prob']))
    L.append(',\n'.join(rr) + ';')
    with open(ITEMS_OUT, 'w', encoding='utf-8', newline='\n') as f:
        f.write('\n'.join(L) + '\n')
    # icons
    os.makedirs(ICON_OUT, exist_ok=True)
    done = set()
    for i in items:
        dst = os.path.join(ICON_OUT, os.path.basename(i['icon']))
        if dst in done:
            continue
        done.add(dst)
        src = os.path.join(a.gf, i['icon_src'].replace('\\', '/'))
        assert os.path.isfile(src), src
        if not os.path.exists(dst):
            shutil.copyfile(src, dst)
    write_sig(byv)
    write_drops(byv)
    write_cube(byv)
    report.append('items %d (materials/plans/chests/quest %d, helmets %d), refine rows %d' % (
        len(items), len(items) - 16 * len(HELMETS), 16 * len(HELMETS), len(refines)))
    return items


def nm(byv, v, c=1):
    n = (EXISTING['gold'] + ' %d' % c) if v == 'gold' else (EXISTING['exp'] + ' %d' % c) if v == 'exp' else \
        (byv[v]['name'] if v in byv else EXISTING[v])
    return n + (' x%d' % c if c > 1 and v not in ('gold', 'exp') else '')


# -- the chests: one thing an opening, by weight (ours - the wiki lists the contents, not the odds) -----------------
def chests():
    # MT2009_PLUS_CHEST_DROPS_V1: the rows and their chances - the owner's sheet of 15 October 2026
    # (tools/yohara_chestdrops: the official vnums mapped to ours, what we lack left out and the rest renormalised)
    return [(vnum, title, CD.table(vnum)[0]) for vnum, title in (
        (CHEST_BERAN, 'Skrzynia Berana-Setaou (PB) - Beran-Setaou (PB)'),
        (CHEST_JOTUN, 'Skrzynia Jotuna Thryma (PB) - Jotun Thrym (PB)'))]


def write_sig(byv):
    L = ['# %s: the chests of Beran-Setaou (PB) and Jotun Thrym (PB) - their contents as on their pl-wiki pages,' % M,
         '# one thing an opening, by weight (the owner\'s sheet of 15 October 2026). GENERATED by',
         '# tools/yohara_iluzja/gen_yiluzja.py - do not edit. Appended to special_item_group.txt by the Dockerfile',
         '# (share: Plaskowyz Iluzji).', '']
    for vnum, title, rows in chests():
        assert vnum in byv
        L += CD.comment(vnum)
        L += ['Group\tMT2009_yil_%d' % vnum, '{', '\tVnum\t%d -- %s' % (vnum, title)]
        for k, (v, c, w, n) in enumerate(rows, 1):
            L.append('\t%d\t%s\t%d\t%d -- %s' % (k, v, c, w, n))
        L += ['}', '']
    with open(os.path.join(OUT, 'special_item_group.yohara_iluzja.txt'), 'w', encoding='utf-8', newline='\n') as f:
        f.write('\n'.join(L))


# -- the drops (mob_drop_item, Type drop: vnum, count, percent): the pl-wiki's lists of each boss and monster, the
#    plans' sources of the de-wiki ("EW: ...entwurf") where the pl-wiki has none; the odds ours, official-like (each
#    boss its chests always: Beran-Setaou (PB) "Skrzynia Berana-Setaou (PB) (x2)", "Skrzynia Przebudzenia"; Jotun
#    Thrym (PB) "(x4)", "(x3)"). The test server's 500% drop event is not compensated for. --------------------------
def drops():
    return [
        (4410, 'PB: Beran-Setaou', [(CHEST_BERAN, 2, 100), (31143, 1, 100), (31124, 2, 30), (31117, 2, 30),
                                     (31123, 2, 30), (31145, 5, 50), (31149, 2, 30), (31132, 2, 25), (31120, 2, 30),
                                     (31121, 2, 30), (31109, 1, 20), (31108, 3, 40), (31210, 1, 12), (31212, 1, 12),
                                     (31205, 1, 12), (31207, 1, 12), (31198, 1, 8), (31201, 1, 8), (50513, 1, 15),
                                     (50124, 1, 20)]),
        (4413, 'PB: Jotun Thrym', [(CHEST_JOTUN, 4, 100), (31143, 3, 100), (31124, 2, 30), (31109, 1, 20),
                                    (31125, 2, 30), (31145, 5, 50), (31108, 3, 40), (31132, 2, 25), (MEDAL, 3, 40),
                                    (31210, 1, 12), (31211, 1, 12), (31197, 1, 12), (31200, 1, 12), (31198, 1, 12),
                                    (31121, 2, 30), (31120, 2, 30), (70012, 1, 10)]),
        (4352, 'PB: Bagjanamu', [(31204, 1, 10), (31206, 1, 10), (31143, 1, 30)]),
        (4345, 'PB: Wladca En-Tai', [(27105, 10, 30), (27102, 10, 30), (31123, 2, 25), (31115, 2, 25),
                                     (31120, 2, 25), (31143, 1, 15)]),
        (4344, 'PB: Niszczyciel En-Tai (113)', [(31117, 1, 2), (31123, 1, 2), (31115, 1, 2), (31149, 1, 2),
                                                (MEDAL, 1, 2), (31122, 1, 2), (31120, 1, 2), (31109, 1, 0.5),
                                                (31108, 1, 1), (31209, 1, 0.5), (31196, 1, 0.5), (31197, 1, 0.5)]),
        (4351, 'PB: Niszczyciel En-Tai (125)', [(31201, 1, 0.5)]),
        (4342, 'PB: Druid En-Tai (111)', [(31203, 1, 0.3)]),
        (4348, 'PB: Bojownik En-Tai (120)', [(31212, 1, 0.3)]),
        (8137, 'PB: Metin Lasu', [(31199, 1, 3), (31207, 1, 3), (50513, 1, 10)]),
        (8136, 'PB: Metin Drz. Stworzen', [(50513, 1, 10)]),
        (4283, 'PB: Zolnierz Setaou', [(31200, 1, 0.2), (31204, 1, 0.2)]),
        (4285, 'PB: Magistrat Setaou', [(31212, 1, 0.3), (31207, 1, 0.3)]),
        (4282, 'PB: Mistyk Setaou', [(31212, 1, 0.3), (31207, 1, 0.3)]),
    ]


def write_drops(byv):
    L = ['// %s: drops of Grota Wygnancow 2 (PB) and Zaklety Las (PB) - the pl-wiki lists ("Beran-Setaou (PB)",' % M,
         '// "Jotun Thrym (PB)", "Wladca En-Tai (PB)", "Niszczyciel En-Tai (PB-113)") and, for the plans of the Dark Dragon',
         '// gear the pl-wiki gives no source of, the de-wiki\'s ("EW: Bogenentwurf" ...). GENERATED by',
         '// tools/yohara_iluzja/gen_yiluzja.py - do not edit. The percents are ours, official-like. Left out: the Lycan\'s',
         '// plans, Torba Emocji. Kręty Klucz / Apteczka / Rosa / Szlachetne Drzewo / Drzewny Szmaragd (PB) are the quests\'.',
         '']
    for v, n, rows in drops():
        assert v in D.MOBS, v
        L += ['Group\tMT2009_yil_%d' % v, '{', '\tMob\t%d\t-- %s' % (v, ascii_pl(n)), '\tType\tdrop']
        for k, (iv, c, p) in enumerate(rows, 1):
            assert iv in byv or iv in EXISTING, (v, iv)
            L.append('\t%d\t%d\t%d\t%s\t-- %s' % (k, iv, c, '%g' % p, nm(byv, iv, c)))
        L += ['}', '']
    with open(os.path.join(OUT, 'mob_drop_item.yohara_iluzja.txt'), 'w', encoding='utf-8', newline='\n') as f:
        f.write('\n'.join(L))


def write_cube(byv):
    L = ['# %s: GENERATED by tools/yohara_iluzja/gen_yiluzja.py - do not edit. Appended to the share\'s cube.txt' % M,
         '# by the Dockerfile (quest plaskowyz_iluzji opens each window). Source: Owsap cube.txt npc 20470 / 20473 / 20474',
         '# = the pl-wiki ("Plaskowyz Iluzji", "Statua Iluzji", "Wytwarzanie Broni", "Wytwarzanie Zbroi"): the awakening',
         '# stone of a recipe is its chance - 2 / 5 / 10 / 15 / 25%. The Lycan\'s pieces are left out.', '']
    L.append('# -- Statua Iluzji (20470): the awakening stones from the stone below and Dusza Przebudzenia')
    for src, n, dst, gold, pct in STONE_RECIPES:
        L += ['section', 'npc\t20470', 'item\t%d\t%d' % (src, n), 'item\t31113\t1', 'reward\t%d\t1' % dst,
              'gold\t%d' % gold, 'percent\t%d' % pct, 'end', '']
    L.append('# -- Statua Fabryki Broni (20473): the Dark Dragon weapons +0 - 10 Kowadlo, 5 plans, 5 Srodek Scierny, 5 Stal')
    for reward, plan in WEAPON_RECIPES:
        assert plan in byv
        for stone, pct in STONES:
            L += ['section', 'npc\t20473', 'item\t31115\t10', 'item\t%d\t5' % plan, 'item\t31120\t5',
                  'item\t31121\t5', 'item\t%d\t1' % stone, 'reward\t%d\t1' % reward, 'gold\t%d' % CRAFT_GOLD,
                  'percent\t%d' % pct, 'end', '']
    L.append('# -- Statua Kowala Zbroi (20474): the dragon armours +0 - 10 Zwykla Skora, 5 plans, 5 Cienka Przedza,')
    L.append('#    5 Oznaka Slawy; the dragon helmets +0 - 10 Zwykla Skora, 5 plans, 5 Cienka Przedza, 5 Stal')
    for reward, plan in ARMOUR_RECIPES + HELMET_RECIPES:
        assert plan in byv
        fourth = MEDAL if reward >= 20000 else 31121
        for stone, pct in STONES:
            L += ['section', 'npc\t20474', 'item\t31114\t10', 'item\t%d\t5' % plan, 'item\t31117\t5',
                  'item\t%d\t5' % fourth, 'item\t%d\t1' % stone, 'reward\t%d\t1' % reward,
                  'gold\t%d' % CRAFT_GOLD, 'percent\t%d' % pct, 'end', '']
    with open(os.path.join(OUT, 'cube.yohara_iluzja.txt'), 'w', encoding='utf-8', newline='\n') as f:
        f.write('\n'.join(L))


def check_cube_against_owsap(a, report):
    """our recipes = Owsap's (materials, counts, gold, percent) for every reward we keep"""
    t = open(os.path.join(a.owsap, 'share/locale/uk/cube.txt'), encoding='latin-1').read().replace('\r', '')
    ow = set()
    for s in re.findall(r'section\n(.*?)\nend', t, re.S):
        d = [x.split('\t') for x in s.split('\n') if x.strip() and not x.startswith('#')]
        npc = [x[1] for x in d if x[0] == 'npc']
        if not npc or npc[0] not in ('20470', '20473', '20474'):
            continue
        ow.add((npc[0], tuple(sorted((x[1], x[2]) for x in d if x[0] == 'item')),
                tuple((x[1], x[2]) for x in d if x[0] == 'reward'), tuple(x[1] for x in d if x[0] == 'gold'),
                tuple(x[1] for x in d if x[0] == 'percent')))
    ours = open(os.path.join(OUT, 'cube.yohara_iluzja.txt'), encoding='utf-8').read()
    n = 0
    for s in re.findall(r'section\n(.*?)\nend', ours, re.S):
        d = [x.split('\t') for x in s.split('\n') if x.strip()]
        key = ([x[1] for x in d if x[0] == 'npc'][0], tuple(sorted((x[1], x[2]) for x in d if x[0] == 'item')),
               tuple((x[1], x[2]) for x in d if x[0] == 'reward'), tuple(x[1] for x in d if x[0] == 'gold'),
               tuple(x[1] for x in d if x[0] == 'percent'))
        assert key in ow, key
        n += 1
    report.append('cube recipes %d, every one equal to Owsap\'s (of its %d for these statues)' % (n, len(ow)))


# ------------------------------------------------------------------------------------------------ the client
def write_client(mob_lines, items):
    keys = ('vnum', 'name', 'locale_name', 'type', 'subtype', 'stack', 'weight', 'size', 'antiflag', 'flag',
            'wearflag', 'gold', 'shop_buy_price', 'refined_vnum', 'refine_set', 'magic_pct', 'specular', 'socket_pct',
            'limittype0', 'limitvalue0', 'limittype1', 'limitvalue1', 'applytype0', 'applyvalue0', 'applytype1',
            'applyvalue1', 'applytype2', 'applyvalue2', 'value0', 'value1', 'value2', 'value3', 'value4', 'value5')
    out = {'cols': list(COLS), 'rows': [list(t) for t in mob_lines],
           'elements': dict((str(v), e) for v, (pl, e, _p) in D.MOBS.items()),
           'npclist_add': dict((str(k), v) for k, v in D.NPCLIST_ADD.items()),
           'atlas': ['%s\t%d\t%d\t%d\t%d' % (m['folder'], m['base'][0], m['base'][1], m['size'][0], m['size'][1])
                     for m in D.MAPS],
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
    os.makedirs(OUT, exist_ok=True)
    gen_maps(a, report)
    write_groups()
    write_spawned()
    mob_lines = gen_mobs(a, report)
    items = gen_items(a, report)
    check_cube_against_owsap(a, report)
    write_client(mob_lines, items)
    print('\n'.join(report))


if __name__ == '__main__':
    main()
