#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""gen_ypb.py [--owsap DIR] [--gf DIR] [--attr DIR]     (in the m2pack-lzo image: server_attr is LZO)

MT2009_PLUS_YOHARA_PB_V1: everything the server needs for the awakened bosses - Razador (PB) and Nemere (PB)
(ypb_data.py) - GENERATED here, never edited by hand:

  linux-port/docker/game/yohara_pb/
    map/<folder>/Setting.txt, Town.txt   Owsap's (= the GF client's MapSize / BasePosition); Town = our entry cell
    map/<folder>/server_attr             the GF client's attr.atr of the parent map (tools/gf28/srvattr.py) - the
                                         terrain our 351 / 352 walk on
    data/dungeon/razador_pb/fd_*.txt     the fortress' zones: Owsap's awaken_flame_dungeon spawn points, its own
                                         groups of groups 6101-6103 (the PB monsters 4300-4308)
    data/dungeon/nemere_pb/sd_*.txt      the watchtower's floors: Owsap's awaken_snow_dungeon points and groups
                                         6121-6132 (its 1st floor named the TR groups 6071/6072/6075 - here the PB
                                         ones 6121/6122/6125)
    group.yohara_pb.txt                  groups 6101-6112, 6121-6132 (Owsap's, = the official ones)
    group_group.yohara_pb.txt            groups of groups 6101-6103
    mob_drop_item.yohara_pb.txt          the bosses' and stones' drops (the pl-wiki's lists, our odds)
    special_item_group.yohara_pb.txt     Skrzynia Razadora (PB), Skrzynia Nemere (PB), Skrzynia Przebudzenia
    spawned.txt                          every vnum each map shows (the client builder ypb reads it)
  linux-port/docker/mariadb/playerbot/
    yohara_pb.sql                        world.mob_proto (INSERT IGNORE) - monsters, bosses, stones, NPCs
    yohara_pb_zywioly.sql                their elements (after zywioly_moby.sql)
    yohara_items_pb.sql                  world.item_proto (INSERT IGNORE) - the items our world lacked
  tools/yohara_pb/ypb_client.json        the client's rows (client-2.0.30/tools/ypb)
  client-patches/client-2.0.30/root/icon/item/<icon>.tga   the GF icons our packs lack

Every position the quests and spawn files use is checked against the server_attr made here (a blocked centre is
reported). Example:
  docker run --rm -v /opt/metin2:/opt/metin2 m2pack-lzo python3 /opt/metin2/git/<tree>/tools/yohara_pb/gen_ypb.py
"""
import argparse
import csv
import json
import os
import re
import shutil
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(os.path.dirname(HERE))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(REPO, 'tools', 'yohara_maps'))
sys.path.insert(0, os.path.join(REPO, 'tools', 'yohara_items'))
sys.path.insert(0, os.path.join(REPO, 'client-patches', 'client-2.0.28', 'tools', 'gf28'))
import ypb_data as D  # noqa: E402
from gen_ymaps_sql import COLS, row_of, npc_row, q  # noqa: E402
import gen_yitems as Y  # noqa: E402

OUT = os.path.join(REPO, 'linux-port', 'docker', 'game', 'yohara_pb')
PB = os.path.join(REPO, 'linux-port', 'docker', 'mariadb', 'playerbot')
SQL_OUT = os.path.join(PB, 'yohara_pb.sql')
ZYW_OUT = os.path.join(PB, 'yohara_pb_zywioly.sql')
ITEMS_OUT = os.path.join(PB, 'yohara_items_pb.sql')
JSON_OUT = os.path.join(HERE, 'ypb_client.json')
ICON_OUT = os.path.join(REPO, 'client-patches', 'client-2.0.30', 'root', 'icon', 'item')
EARLIER_JSON = [os.path.join(REPO, 'tools', 'yohara_items', 'yohara_items.json'),
                os.path.join(REPO, 'tools', 'yohara_items', 'yohara_items2.json'),
                os.path.join(REPO, 'tools', 'yohara_maps3', 'yohara_items3.json'),
                os.path.join(REPO, 'tools', 'yohara_maps4', 'yohara_items4.json'),
                os.path.join(REPO, 'tools', 'yohara_dung4', 'yohara_items_d4.json'),
                os.path.join(REPO, 'tools', 'ysets', 'yohara_sets.json')]

# -- the groups (Owsap's group.txt, = the official ones): vnum -> (name, [leader, members...]) ----------------------
GROUPS = {
    6101: ('awaken_fire_dungeon_1', [4300, 4300]),
    6102: ('awaken_fire_dungeon_2', [4301, 4300]),
    6103: ('awaken_fire_dungeon_3', [4301, 4301]),
    6104: ('awaken_fire_dungeon_4', [4302, 4301]),
    6105: ('awaken_fire_dungeon_5', [4302, 4302]),
    6106: ('awaken_fire_dungeon_6', [4303, 4302, 4301, 4301]),
    6107: ('awaken_fire_dungeon_7', [4304, 4303, 4303, 4301, 4301]),
    6108: ('awaken_fire_dungeon_8', [4305, 4304, 4303, 4303]),
    6109: ('awaken_fire_dungeon_9', [4306, 4305, 4305, 4304, 4304]),
    6110: ('awaken_fire_dungeon_10', [4307, 4306, 4305, 4305]),
    6111: ('awaken_fire_dungeon_11', [4308, 4307, 4307, 4306, 4306]),
    6112: ('awaken_fire_dungeon_boss', [4411, 4308, 4308, 4307, 4307, 4307, 4306, 4306, 4306, 4305, 4305, 4305]),
    6121: ('awaken_ice_dungeon_1', [4320, 4320, 4320]),
    6122: ('awaken_ice_dungeon_2', [4321, 4320, 4320]),
    6123: ('awaken_ice_dungeon_3', [4321, 4321, 4321]),
    6124: ('awaken_ice_dungeon_4', [4322, 4321, 4321]),
    6125: ('awaken_ice_dungeon_5', [4322, 4322, 4322]),
    6126: ('awaken_ice_dungeon_6', [4323, 4322, 4321, 4321]),
    6127: ('awaken_ice_dungeon_7', [4324, 4323, 4323, 4321, 4321]),
    6128: ('awaken_ice_dungeon_8', [4325, 4324, 4323, 4323]),
    6129: ('awaken_ice_dungeon_9', [4326, 4325, 4325, 4323, 4323]),
    6130: ('awaken_ice_dungeon_10', [4324, 4323, 4322, 4322]),
    6131: ('awaken_ice_dungeon_11', [4325, 4324, 4324, 4322, 4322]),
    6132: ('awaken_ice_dungeon_boss', [4412, 4328, 4328, 4327, 4327, 4327, 4326, 4326, 4325, 4325, 4325, 4325]),
}
GROUP_GROUPS = {
    6101: ('awaken_fire_dungeon_1', [6101, 6102, 6103, 6104, 6105]),
    6102: ('awaken_fire_dungeon_2', [6105, 6106, 6107, 6108, 6109]),
    6103: ('awaken_fire_dungeon_3', [6107, 6108, 6109, 6110, 6111]),
}
# Owsap's awaken_snow_dungeon/sd_1.txt and sd_2.txt name three TR (crack) groups - the PB ones of the same monsters
GROUP_FIX = {6071: 6121, 6072: 6122, 6075: 6125}
REGEN = {
    'razador_pb': ('awaken_flame_dungeon', ['fd_a', 'fd_b', 'fd_c', 'fd_d', 'fd_e', 'fd_f', 'fd_fild_boss'], 369),
    'nemere_pb': ('awaken_snow_dungeon', ['sd_%d' % i for i in range(1, 11)], 370),
}
# every position the quests use (= linux-port/docker/game/quest/razador_pb.quest / nemere_pb.quest cfg())
QUEST_POINTS = {
    369: dict(entry=[(342, 584)], gorge=[(350, 360)], boss_room=[(685, 710)], boss=[(686, 637)],
              grave=[(686, 639)], stone2=[(195, 352)], ignator=[(470, 175)],
              stones5=[(486, 345), (511, 336), (525, 349), (521, 365), (503, 372), (486, 365), (500, 354)],
              metin6=[(511, 480)]),
    370: dict(entry=[(171, 270)], lion=[(172, 261)],
              rooms=[(422, 261), (764, 264), (175, 532), (421, 535), (748, 540), (305, 708), (571, 701), (851, 693),
                     (927, 395)],
              szel4=[(160, 490), (215, 440), (140, 425)],
              cubes=[(449, 488), (455, 445), (419, 422), (382, 444), (389, 488)], metin6=[(747, 494)],
              szel7=[(302, 678), (281, 657), (303, 635), (324, 656)], pillar=[(849, 660)], lion10=[(849, 641)],
              boss=[(927, 333)]),
}
QUEST_SPAWNED = {
    369: [20531, 20532, 20533, 20534, 20535, 4309, 4411, 8134],
    370: [20536, 20537, 4329, 8135, 20538, 4412],
}


def ascii_pl(s):
    return s.translate(str.maketrans('ąćęłńóśźżĄĆĘŁŃÓŚŹŻ', 'acelnoszzACELNOSZZ'))


def crlf_text(lines):
    return '\r\n'.join(lines) + '\r\n' if lines else ''


# ------------------------------------------------------------------------------------------------ the maps
def walk_grid(gf, m):
    import srvattr as sa
    W, H, g = sa.grid_from_client(os.path.join(gf, m['parent']), m['size'][0], m['size'][1])
    LW, LH = W // 2, H // 2
    walk = bytearray(LW * LH)
    for y in range(LH):
        row = 2 * y * W
        for x in range(LW):
            walk[y * LW + x] = 0 if g[row + 2 * x] & 1 else 1
    return W, H, g, LW, LH, walk


def gen_maps(a, report):
    import srvattr as sa
    shutil.rmtree(os.path.join(OUT, 'map'), ignore_errors=True)
    shutil.rmtree(os.path.join(OUT, 'data'), ignore_errors=True)
    walks = {}
    for m in D.MAPS:
        folder = m['folder']
        dst = os.path.join(OUT, 'map', folder)
        os.makedirs(dst)
        st = open(os.path.join(a.owsap, 'share/locale/uk/map', folder, 'Setting.txt'), encoding='latin-1').read()
        assert re.search(r'MapSize\s+%d\s+%d' % m['size'], st) and \
            re.search(r'BasePosition\s+%d\s+%d' % m['base'], st), folder
        gfst = open(os.path.join(a.gf, folder, 'setting.txt'), encoding='latin-1').read()
        assert re.search(r'MapSize\s+%d\s+%d' % m['size'], gfst) and \
            re.search(r'BasePosition\s+%d\s+%d' % m['base'], gfst), folder
        assert 'ParentMapName "%s"' % m['parent'] in open(os.path.join(a.gf, folder, 'mapproperty.txt'),
                                                          encoding='latin-1').read(), folder
        open(os.path.join(dst, 'Setting.txt'), 'w', newline='').write(st.replace('\r\n', '\n').replace('\n', '\r\n'))
        open(os.path.join(dst, 'Town.txt'), 'w', newline='').write('%d\t%d\r\n' % m['town'])
        W, H, g, LW, LH, walk = walk_grid(a.gf, m)
        sa.write_server(os.path.join(dst, 'server_attr'), W, H, g)
        walks[m['index']] = (LW, LH, walk)
        # the same terrain as our 351 / 352: how far our server_attr of the parent is from this one (blocked bits)
        ours = os.path.join(a.attr, m['parent'], 'server_attr')
        if os.path.exists(ours):
            w2, h2, secs = sa.read_server(ours)
            W2, H2, g2 = sa.grid_from_server(w2, h2, secs)
            diff = sum(1 for i in range(min(len(g), len(g2))) if (g[i] & 1) != (g2[i] & 1)) if (W2, H2) == (W, H) else -1
            report.append('%d %s: server_attr %dx%d cells, blocked bits differing from our %s: %d' % (
                m['index'], folder, W, H, m['parent'], diff))
        blocked = []
        for k, pts in QUEST_POINTS[m['index']].items():
            for x, y in pts:
                assert 0 <= x < LW and 0 <= y < LH, (folder, k, x, y)
                if not walk[y * LW + x]:
                    blocked.append('%s %d,%d' % (k, x, y))
        report.append('%d quest points: %d, blocked: %s' % (
            m['index'], sum(len(v) for v in QUEST_POINTS[m['index']].values()), blocked or 'none'))
    # the rooms' spawn files
    for sub, (src, names, idx) in REGEN.items():
        LW, LH, walk = walks[idx]
        dst = os.path.join(OUT, 'data', 'dungeon', sub)
        os.makedirs(dst)
        nblk = ntot = 0
        for n in names:
            p = os.path.join(a.owsap, 'share/data/dungeon', src, n + '.txt')
            out = []
            for l in open(p, encoding='latin-1').read().replace('\r', '').split('\n'):
                t = l.split('\t')
                if len(t) < 11 or not t[1].strip().isdigit():
                    continue
                v = int(t[-1])
                v = GROUP_FIX.get(v, v)
                if t[0] == 'r':
                    assert v in GROUP_GROUPS, (n, l)
                elif t[0] in ('ga', 'g'):
                    assert v in GROUPS, (n, l)
                else:
                    raise SystemExit('%s: %s' % (n, l))
                t[-1] = str(v)
                x, y = int(t[1]), int(t[2])
                assert 0 <= x < LW and 0 <= y < LH, (n, l)
                ntot += 1
                if not walk[y * LW + x]:
                    nblk += 1
                out.append('\t'.join(t))
            assert out, n
            open(os.path.join(dst, n + '.txt'), 'w', newline='').write(crlf_text(out))
        report.append('data/dungeon/%s: %d files, %d spawn points, %d on a blocked centre (the engine finds a free '
                      'cell around)' % (sub, len(names), ntot, nblk))


def write_groups():
    L = ['// MT2009_PLUS_YOHARA_PB_V1: the spawn groups of Twierdza Czerwonego Smoka (PB) and Straznica Nemere (PB) -',
         '// Owsap v6.2.6\'s (= the official ones). GENERATED by tools/yohara_pb/gen_ypb.py - do not edit.']
    for v, (name, mobs) in sorted(GROUPS.items()):
        L += ['Group\tMT2009_ypb_%s' % name, '{', '\tLeader\t"%s"\t%d' % (ascii_pl(D.MOBS[mobs[0]][0]), mobs[0]),
              '\tVnum\t%d' % v]
        for i, mob in enumerate(mobs[1:], 1):
            assert mob in D.MOBS, (v, mob)
            L.append('\t%d\t"%s"\t%d' % (i, ascii_pl(D.MOBS[mob][0]), mob))
        L += ['}', '']
    open(os.path.join(OUT, 'group.yohara_pb.txt'), 'w', newline='\n').write('\n'.join(L))
    L = ['// MT2009_PLUS_YOHARA_PB_V1: the groups of groups of Twierdza Czerwonego Smoka (PB) - Owsap v6.2.6\'s (= the',
         '// official ones). GENERATED by tools/yohara_pb/gen_ypb.py - do not edit.']
    for v, (name, gs) in sorted(GROUP_GROUPS.items()):
        L += ['Group\tMT2009_ypb_%s' % name, '{', '\tVnum\t%d' % v]
        for i, gv in enumerate(gs, 1):
            assert gv in GROUPS
            L.append('\t%d\t%d\t1' % (i, gv))
        L += ['}', '']
    open(os.path.join(OUT, 'group_group.yohara_pb.txt'), 'w', newline='\n').write('\n'.join(L))


def write_spawned():
    lines = ['# MT2009_PLUS_YOHARA_PB_V1: every vnum each map of the awakened bosses shows (the rooms\' spawn files with',
             '# their groups unfolded + the quests\' spawns) and the villages\' statues - the client builder',
             '# (client-patches/client-2.0.30/tools/ypb) reads it. GENERATED by tools/yohara_pb/gen_ypb.py.']
    gm = dict((v, set(m)) for v, (n, m) in GROUPS.items())
    gg = dict((v, set(x for g in gs for x in gm[g])) for v, (n, gs) in GROUP_GROUPS.items())
    for sub, (src, names, idx) in REGEN.items():
        vs = set(QUEST_SPAWNED[idx])
        for n in names:
            for l in open(os.path.join(OUT, 'data', 'dungeon', sub, n + '.txt'), encoding='latin-1'):
                t = l.split()
                v = int(t[-1])
                vs |= gg[v] if t[0] == 'r' else gm[v]
        # the bosses' summons (mob_proto "summon": Razador (PB) 4307, Nemere (PB) 4327)
        vs |= {4307} if idx == 369 else {4327}
        lines += ['%d %d' % (idx, v) for v in sorted(vs)]
    for idx, folder, name, s1, s2 in D.STATUES:
        lines += ['%d 20470' % idx, '%d 20471' % idx]
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
        lines.append(row_of(r, en[v][:24], pl))
    for v in sorted(D.NPCS):
        pl = D.NPCS[v]
        assert len(pl.encode('cp1250')) <= 24, pl
        assert rows[v]['Type'] in ('NPC', 'DOOR'), (v, rows[v]['Type'])
        lines.append(npc_row(v, en[v][:24], pl, rows[v]['Folder']))
    vn = [t[0] for t in lines]
    assert len(vn) == len(set(vn))
    for t in lines:
        assert len(t) == len(COLS), (t[0], len(t))
    with open(SQL_OUT, 'w', encoding='utf-8', newline='\n') as f:
        f.write(SQL_HEAD % dict(n=len(lines), mobs=len(D.MOBS), npcs=len(D.NPCS)))
        f.write('INSERT IGNORE INTO world.mob_proto (%s) VALUES\n' % ','.join('`%s`' % c for c in COLS))
        f.write(',\n'.join('(%s)' % ','.join(str(x) for x in t) for t in lines) + ';\n')
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
    L.append('-- no element (the Metins and the pillar - the wiki gives a Metin none): %s' % ','.join(map(str, none)))
    L.append('UPDATE world.mob_proto SET setRaceFlag = (setRaceFlag + 0) & ~%d WHERE vnum IN (%s) AND '
             '(setRaceFlag + 0) & %d <> 0;' % (D.ELEMENT_BITS, ','.join(map(str, none)), D.ELEMENT_BITS))
    with open(ZYW_OUT, 'w', encoding='utf-8', newline='\n') as f:
        f.write('\n'.join(L) + '\n')
    report.append('mob_proto rows: %d (monsters/Metins %d, NPCs %d); elements: %d vnums' % (
        len(lines), len(D.MOBS), len(D.NPCS), sum(len(x) for x in by.values())))
    return lines


SQL_HEAD = """-- MT2009_PLUS_YOHARA_PB_V1: the awakened bosses - Twierdza Czerwonego Smoka (PB) (369) and Straznica Nemere (PB)
-- (370), the statues of the villages - the owner, 14 October 2026. GENERATED by tools/yohara_pb/gen_ypb.py - do not
-- edit, rerun it. Every start (apply.sh), idempotent: INSERT IGNORE - a row the operator changed is kept. Every vnum
-- was free in our world (the test server's world, 14 October 2026). %(n)d rows: %(mobs)d monsters, bosses and stones,
-- %(npcs)d NPCs. Monsters: Owsap v6.2.6 db/mob_proto.txt (the official vnums, levels 110-130, HP, damage, exp - the
-- pl-wiki's 4 732 952 of the two bosses -, the bosses' summons 4307 / 4327: "Przywoluje ... (maks. 3)") in our r40250
-- columns (tools/yohara_maps/gen_ymaps_sql.row_of); not Sung Ma maps - ordinary exp. Names: Owsap's Polish client
-- (the official translation, "PB: ..."). NPCs on our NPC numbers (gen_ymaps_sql.npc_row; Smocza Brama, Owsap's DOOR,
-- an NPC as our 20388). The elements: yohara_pb_zywioly.sql (after zywioly_moby.sql).
SET NAMES utf8mb4;

"""

ZHEAD = """-- MT2009_PLUS_YOHARA_PB_V1: the elements of the awakened bosses' dungeons (setRaceFlag bits 11-16: 4096 fire, 8192
-- ice) as on the pl-wiki ("Zywiol": the fortress' monsters fire, the watchtower's ice; Owsap's AttFire / AttIce
-- agree). GENERATED by tools/yohara_pb/gen_ypb.py. apply.sh runs it AFTER zywioly_moby.sql, which clears bits 11-16
-- of every mob it does not list: idempotent, the end state is these bits.
SET NAMES utf8mb4;"""


# ------------------------------------------------------------------------------------------------ the items
SUBTYPES = dict(Y.SUBTYPES, USE_POTION_NODELAY=11)
CRAFT = 'needs: the awakened gear crafting (Statua Iluzji / Statua Fabryki Broni / Kowala Zbroi) - none here yet'
STONES = 'needs: the crafting of the awakened gear and of the Dark Dragon gear +0 (Statua Iluzji) - none here yet'
HELM = 'needs: the dragon helmets (Helm Smoka Mroku ...) - none here yet'
ITEMS = []


def add(vnum, name=None, status=Y.ST, **over):
    ITEMS.append(dict(vnum=vnum, name=name, status=status, over=over))


for _v in (31108, 31109, 31110, 31111, 31112):  # Maly / Drobny / Ladny / Zacny / Silny Kam. Przebudzenia
    add(_v, status=STONES)
add(31113, status='needs: the awakening stones\' upgrading (Statua Iluzji) - none here yet')   # Dusza Przebudzenia
for _v in (31114, 31115, 31117, 31120):             # Zwykla Skora, Kowadlo, Cienka Przedza, Srodek Scierny
    add(_v, status=CRAFT)
add(31121, status=HELM)                             # Stal
add(31149, status=HELM)                             # Mocny Sznur
add(31141, name='Skrzynia Razadora (PB)')           # the chests (special_item_group)
add(31142, name='Skrzynia Nemere (PB)')
add(31143)                                          # Skrzynia Przebudzenia
add(31144)                                          # Lekarstwo Iluzji - 500 HP and 500 SP at once, level 80
add(31145)                                          # Liscie Zycia - 20 = Lekarstwo Iluzji at Baek-Go (quest)
add(31146)                                          # Ksiazka Przebudzenia - the ticket
for _v in (31187, 31188, 31189, 31190, 31191):      # the quest items of the two dungeons
    add(_v)

# items we have (official vnums or ours): their names in the drop files
EXISTING = {
    31122: 'Plotno', 31123: 'Cienka Skora', 31124: 'Cienka Nic', 31125: 'Gruba Nic', 31126: 'Czaszka Smoka',
    31127: 'Smoczy Zab', 31128: 'Rog Razadora', 31129: 'Rog Nemere', 31130: 'Ostre Kolce', 31131: 'Jedwab',
    31132: 'Odlamki', 31133: 'Zwykly Barwnik', 31134: 'Ulepszony Barwnik', 31135: 'Wyjatkowy Barwnik',
    31136: 'Prosty Kamien Chaosu', 31137: 'Ladny Kamien Chaosu', 31138: 'Wspanialy Kamien Chaosu',
    50513: 'Kamien Duchowy', 50525: 'Kamien Duchowy+', 27992: 'Biala Perla', 27993: 'Niebieska Perla',
    27994: 'Krwawa Perla', 100700: 'Smoczy Plomien (B)', 100701: 'Smoczy Plomien', 25040: 'Zwoj Blogoslawienstwa',
    27003: 'Czerwona Mikstura(D)', 71095: 'Przepustka', 70048: 'Peleryna Maskujaca (our Plaszcz Uciekiniera)',
    70012: 'Lza Bogini', 71015: 'Pierscien Doswiadczenia', 39002: 'Pierscien Doswiadczenia (1 h)',
    70038: 'Peleryna Mestwa', 50120: 'Zelazna Szkatulka', 50124: 'Sprochniala Skrzynia', 'gold': 'Yang', 'exp': 'EXP',
}


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
    for it in ITEMS:
        v = it['vnum']
        assert v not in earlier, v
        o = proto[v]
        pl, text = desc.get(v, ('', ''))
        name = it['name'] or pl
        assert name and len(name.encode('cp1250')) <= 24, (v, name)
        typ = Y.TYPES[o['Type']]
        st = o['SubType']
        sub = SUBTYPES[st] if st in SUBTYPES else 0
        assert st in SUBTYPES or st in ('UNK23_1', '0'), (v, st)
        anti = Y.flags(o['AntiFlags'].replace('ANTI_MAIL', 'NONE'), Y.ANTI, 'antiflag')   # no mail here
        if it['status'] != Y.ST:
            anti &= ~Y.ANTI_TRADE
        flag = Y.flags(o['Flags'], Y.FLAGS, 'flag')
        if typ == 18:
            flag |= Y.FLAGS['ITEM_QUEST_USE']
        wear = Y.flags(o['WearFlags'], Y.WEAR, 'wearflag')
        lim = [(Y.LIMITS[o['LimitType%d' % k]], int(o['LimitValue%d' % k])) for k in (0, 1)]
        for i in range(3):
            assert o['ApplyType%d' % i] in ('A_NONE', 'APPLY_NONE'), (v, o['ApplyType%d' % i])
        values = [int(o['Value%d' % i]) for i in range(6)]
        if typ in (5, 18):
            values = [0] * 6
        icon = gf_list.get(v)
        assert icon, v
        items.append(dict(
            vnum=v, src=v, status=it['status'], name=Y.ascii_name(name), locale_name=name, type=typ, subtype=sub,
            stack=200 if flag & Y.FLAGS['ITEM_STACKABLE'] else 1, weight=0, size=int(o['Size']), antiflag=anti,
            flag=flag, wearflag=wear, gold=int(o['ShopBuyPrice']), shop_buy_price=int(o['ShopSellPrice']),
            refined_vnum=int(o['RefinedVnum']), refine_set=int(o['RefineSet']),
            magic_pct=int(o['AlterToMagicItemPercent']), specular=int(o['Specular']),
            socket_pct=int(o['GainSocketPercent']), addon_type=0,
            limittype0=lim[0][0], limitvalue0=lim[0][1], limittype1=lim[1][0], limitvalue1=lim[1][1],
            applytype0=0, applyvalue0=0, applytype1=0, applyvalue1=0, applytype2=0, applyvalue2=0,
            **dict(('value%d' % i, values[i]) for i in range(6)),
            icon='icon/item/' + os.path.basename(icon), icon_src=icon, desc=text,
            list_type='ETC'))
    byv = dict((i['vnum'], i) for i in items)
    assert len(byv) == len(items)
    # SQL
    L = ['-- MT2009_PLUS_YOHARA_PB_V1: the items of the awakened bosses (Razador (PB), Nemere (PB)) that our world did',
         '-- not have - the chests, the materials of their drop lists, Lekarstwo Iluzji / Liscie Zycia, the ticket',
         '-- Ksiazka Przebudzenia and the two dungeons\' quest items. GENERATED by tools/yohara_pb/gen_ypb.py - do not',
         '-- edit, rerun it. Every start (apply.sh, after yohara_sets.sql - the chests hold its Dark Dragon materials',
         '-- 31122-31138), idempotent: INSERT IGNORE. Source: Owsap v6.2.6 db/item_proto.txt (the official vnums and',
         '-- numbers), the Polish names of its Polish client (the chests "(PB)" as on the pl-wiki - the normal ones are',
         '-- ours already); every vnum free in our world and every earlier Yohara batch (14 October 2026). An item whose',
         '-- system we do not have is an inert, tradeable material and does nothing yet - its row says what it waits for:']
    for i in items:
        if i['status'] != Y.ST:
            L.append('--   %d %s - %s' % (i['vnum'], i['name'], i['status'][len('needs: '):]))
    L += ['-- Left out: the awakened gear\'s plans (PB: Plan Helmu / Ostrza / Wachlarza ... 31196-31213 - no awakened gear',
          '-- here), Torba Emocji (the emotion packs, as every Yohara batch).',
          'SET NAMES utf8mb4;',
          'INSERT IGNORE INTO world.item_proto (%s) VALUES' % ','.join('`%s`' % c for c in Y.COLS),
          ',\n'.join(Y.sqlrow(i) for i in items) + ';']
    with open(ITEMS_OUT, 'w', encoding='utf-8', newline='\n') as f:
        f.write('\n'.join(L) + '\n')
    # icons
    os.makedirs(ICON_OUT, exist_ok=True)
    for i in items:
        dst = os.path.join(ICON_OUT, os.path.basename(i['icon']))
        src = os.path.join(a.gf, i['icon_src'].replace('\\', '/'))
        assert os.path.isfile(src), src
        if not os.path.exists(dst):
            shutil.copyfile(src, dst)
    write_sig(byv)
    write_drops(byv)
    report.append('items %d (%d work, %d wait for a system)' % (
        len(items), sum(1 for i in items if i['status'] == Y.ST), sum(1 for i in items if i['status'] != Y.ST)))
    return items


def nm(byv, v, c=1):
    n = (EXISTING['gold'] + ' %d' % c) if v == 'gold' else (EXISTING['exp'] + ' %d' % c) if v == 'exp' else \
        (byv[v]['name'] if v in byv else EXISTING[v])
    return n + (' x%d' % c if c > 1 and v not in ('gold', 'exp') else '')


# -- the chests: one thing an opening, by weight (ours - the wiki lists the contents, not the odds) -----------------
def chests():
    common = [(31136, 1, 6), (31137, 1, 4), (31138, 1, 2), (31113, 2, 8), (31114, 2, 8), (31122, 2, 10),
              (31108, 5, 10), (31109, 1, 6), (31123, 2, 10), (31124, 2, 10), (31117, 2, 8), (31149, 2, 8),
              (31133, 1, 6), (31134, 1, 4), (31135, 1, 2), (31121, 1, 8), (50513, 1, 8), (50525, 1, 4),
              (27992, 1, 6), (27993, 1, 5), (27994, 1, 4), (100700, 1, 3), (25040, 1, 6), (31144, 5, 8)]
    raz = common + [(31128, 2, 6), (31131, 1, 6), (31125, 2, 8)]
    nem = [(v, 2 if v == 31134 else c, w) for v, c, w in common] + [(31115, 2, 8), (31129, 1, 6), (71095, 1, 4)]
    nem = [(v, 2 if v == 31121 else c, w) for v, c, w in nem]
    awa = [(27992, 1, 6), (31123, 2, 8), (27003, 50, 10), (31109, 1, 6), (50513, 1, 8), (31144, 1, 8),
           (31110, 1, 4), (31108, 2, 8), (31149, 2, 8), (70048, 1, 4), (70038, 20, 6), (31122, 2, 8), (71095, 1, 4),
           (31112, 1, 1), (100701, 1, 2), (31111, 1, 2), (25040, 1, 6), (50120, 1, 4), ('gold', 400000, 8),
           ('exp', 800000, 8)]
    return [
        (31141, 'Skrzynia Razadora (PB) - Razador (PB); the pl-wiki\'s list (left out: Torba Emocji)', raz),
        (31142, 'Skrzynia Nemere (PB) - Nemere (PB); the pl-wiki\'s list (left out: Torba Emocji)', nem),
        (31143, 'Skrzynia Przebudzenia - Razador (PB), Nemere (PB); the pl-wiki\'s list (left out: Miedziane / Zlote '
                'Plyty - not ours)', awa),
    ]


def write_sig(byv):
    L = ['# MT2009_PLUS_YOHARA_PB_V1: the chests of the awakened bosses - their contents as on their pl-wiki pages, one',
         '# thing an opening, by weight (ours: the wiki gives no odds). GENERATED by tools/yohara_pb/gen_ypb.py - do not',
         '# edit. Appended to special_item_group.txt by the Dockerfile (share: Yohara PB).', '']
    for vnum, title, rows in chests():
        assert vnum in byv
        L += ['Group\tMT2009_ypb_%d' % vnum, '{', '\tVnum\t%d -- %s' % (vnum, title)]
        for k, (v, c, w) in enumerate(rows, 1):
            if v not in ('gold', 'exp'):
                assert v in byv or v in EXISTING, (vnum, v)
            L.append('\t%d\t%s\t%d\t%d -- %s' % (k, v, c, w, nm(byv, v, c)))
        L += ['}', '']
    with open(os.path.join(OUT, 'special_item_group.yohara_pb.txt'), 'w', encoding='utf-8', newline='\n') as f:
        f.write('\n'.join(L))


# -- the drops (mob_drop_item, Type drop: vnum, count, percent): the pl-wiki's lists of each boss; the odds ours,
#    official-like (each boss its chests always - Nemere (PB) "Skrzynia Nemere (PB) (x4)", "Skrzynia Przebudzenia
#    (x3)", Razador (PB) the same; the rest 10-50). The test server's 500% drop event is not compensated for. -------
def drops():
    return [
        (4411, 'PB: Razador', [(31141, 4, 100), (31143, 3, 100), (31124, 2, 30), (31117, 2, 30), (31109, 1, 20),
                               (31125, 2, 30), (31145, 5, 50), (31108, 3, 40), (50513, 1, 15), (70012, 1, 10),
                               (39002, 1, 10), (50124, 1, 20)]),
        (4412, 'PB: Nemere', [(31142, 4, 100), (31143, 3, 100), (31124, 2, 30), (31109, 1, 20), (31108, 3, 40),
                              (31132, 2, 25), (31145, 5, 50), (31120, 2, 30), (50513, 1, 15), (70048, 1, 10),
                              (71015, 1, 10), (50124, 1, 20)]),
        (8135, 'PB: Metin Chlodu', [(50513, 1, 30)]),
        (20538, 'PB: Kolumna Smoka Pln.', [(50513, 1, 30)]),
    ]


def write_drops(byv):
    L = ['// MT2009_PLUS_YOHARA_PB_V1: drops of the awakened bosses - the pl-wiki lists ("Razador (PB)", "Nemere (PB)",',
         '// "Metin Chlodu (PB)", "Kolumna Smoka Polnocy (PB)"). GENERATED by tools/yohara_pb/gen_ypb.py - do not edit.',
         '// The percents are ours, official-like. Left out: the awakened gear\'s plans (PB: Plan ... - no awakened gear',
         '// here), Ciezkie Pasy / Ksiega Umiejetnosci of Metin Chlodu (no such items here). The monsters drop nothing',
         '// on the wiki - their Zlota Zebatka / Kamien Maat / Mrozny Klucz / Gwiazda Polnocy / Klucz Lod. Kwiatu (PB)',
         '// are the quests\' (razador_pb, nemere_pb).', '']
    for v, n, rows in drops():
        assert v in D.MOBS, v
        L += ['Group\tMT2009_ypb_%d' % v, '{', '\tMob\t%d\t-- %s' % (v, ascii_pl(n)), '\tType\tdrop']
        for k, (iv, c, p) in enumerate(rows, 1):
            assert iv in byv or iv in EXISTING, (v, iv)
            L.append('\t%d\t%d\t%d\t%s\t-- %s' % (k, iv, c, '%g' % p, nm(byv, iv, c)))
        L += ['}', '']
    with open(os.path.join(OUT, 'mob_drop_item.yohara_pb.txt'), 'w', encoding='utf-8', newline='\n') as f:
        f.write('\n'.join(L))


# ------------------------------------------------------------------------------------------------ the client
def write_client(mob_lines, items):
    keys = ('vnum', 'name', 'locale_name', 'type', 'subtype', 'stack', 'weight', 'size', 'antiflag', 'flag',
            'wearflag', 'gold', 'shop_buy_price', 'refined_vnum', 'refine_set', 'magic_pct', 'specular', 'socket_pct',
            'limittype0', 'limitvalue0', 'limittype1', 'limitvalue1', 'applytype0', 'applyvalue0', 'applytype1',
            'applyvalue1', 'applytype2', 'applyvalue2', 'value0', 'value1', 'value2', 'value3', 'value4', 'value5')
    out = {'cols': list(COLS), 'rows': [list(t) for t in mob_lines],
           'elements': dict((str(v), e) for v, (pl, e, _p) in D.MOBS.items()),
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
    ap.add_argument('--attr', default='/tmp/claude-0/-root/9f475014-d1bc-4cf4-a3e1-da3c380fc52c/scratchpad/pb/live/attr',
                    help='our share\'s map folders (server_attr of 351/352) to compare with - optional')
    a = ap.parse_args()
    report = []
    os.makedirs(OUT, exist_ok=True)
    gen_maps(a, report)
    write_groups()
    write_spawned()
    mob_lines = gen_mobs(a, report)
    items = gen_items(a, report)
    write_client(mob_lines, items)
    print('\n'.join(report))
    for i in items:
        if i['status'] != Y.ST:
            print('  %d %s: %s' % (i['vnum'], i['name'], i['status']))


if __name__ == '__main__':
    main()
