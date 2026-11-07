#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""gen_ymeley.py [--owsap DIR] [--gf DIR]          (in the m2pack-lzo image: server_attr is LZO)

MT2009_PLUS_YOHARA_MELEY_V1: everything the server needs for Schronienie Meley (ymeley_data.py) - GENERATED here,
never edited by hand:

  linux-port/docker/game/yohara_meley/
    map/metin2_map_n_flame_dragon/   Setting.txt (Owsap's = GF's MapSize 1 1, the base moved to 281600 1510400),
                                     Town.txt (the arena's entry, inside the gate), server_attr (GF's attr.atr cell for
                                     cell, Meley's cells opened - ymeley_data.py)
    data/dungeon/meley/stage1..3.txt the stages' monsters (Owsap's GuildDragonLair.lua: 12 of the stage's monster at the
                                     four statues, back after 5 / 30 s; Ognisty Książę Żaru's group in stages 2-3)
    data/monster/<folder>/           Owsap's motions of the races our share lacks (the dragon, Idall, the wyvern, the
                                     crystal, the statue, the egg)
    group.yohara_meley.txt           groups 6337-6339 (Owsap's red_dragonlair_1..3 - the statue's / the egg's summons)
    flame_npc.txt                    Strażnik Smoków Dolnarr's line of Doyyumhwaji's npc.txt (the Dockerfile appends it)
    mob_drop_item.yohara_meley.txt   the pl-wiki's drop lists of the magma monsters and Jajo Smoka - TEMPORARY rates
    special_item_group.yohara_meley.txt  Skrzynia Królowej Meley / Skrzynia Sm. Strażników - the wiki's contents,
                                     TEMPORARY equal weights, three things an opening
    spawned.txt                      every vnum the map shows (the client builder ymeley reads it)
  linux-port/docker/mariadb/playerbot/
    yohara_meley.sql                 world.mob_proto (INSERT IGNORE) - the lair's monsters, Meley, the statues, the egg,
                                     Dolnarr and the golden chest
    yohara_meley_zywioly.sql         their element (fire; after zywioly_moby.sql)
    yohara_items_meley.sql           world.item_proto (INSERT IGNORE) - Pierścień Smoczego Ognia (30340) and the two
                                     chests (54706 / 54707); the dragon materials 30620-30622 are yohara_helm100.sql's
  tools/yohara_meley/ymeley_client.json  the client's rows (client-2.0.30/tools/ymeley)
  client-patches/client-2.0.30/root/icon/item/30340.tga   GF's ring icon (30341.tga) under the ring's vnum

Every position the quest and the spawn files use is checked against the server_attr made here, the base against our
client's atlasinfo, every server Setting.txt of the test share and GF's atlasinfo. Example:
  docker run --rm -v /opt/metin2:/opt/metin2 m2pack-lzo python3 /opt/metin2/git/wt-meley/tools/yohara_meley/gen_ymeley.py
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
sys.path.insert(0, os.path.join(REPO, 'tools', 'yohara_iluzja'))
sys.path.insert(0, os.path.join(REPO, 'client-patches', 'client-2.0.28', 'tools', 'gf28'))
import ymeley_data as D  # noqa: E402
from gen_ymaps_sql import COLS, row_of, npc_row  # noqa: E402
import gen_yitems as Y  # noqa: E402
import gen_yiluzja as YI  # noqa: E402  (client_grid, ascii_pl, crlf_text)

M = 'MT2009_PLUS_YOHARA_MELEY_V1'
OUT = os.path.join(REPO, 'linux-port', 'docker', 'game', 'yohara_meley')
PB = os.path.join(REPO, 'linux-port', 'docker', 'mariadb', 'playerbot')
SQL_OUT = os.path.join(PB, 'yohara_meley.sql')
ZYW_OUT = os.path.join(PB, 'yohara_meley_zywioly.sql')
ITEMS_OUT = os.path.join(PB, 'yohara_items_meley.sql')
JSON_OUT = os.path.join(HERE, 'ymeley_client.json')
ICON_OUT = os.path.join(REPO, 'client-patches', 'client-2.0.30', 'root', 'icon', 'item')
# MT2009_PLUS_YZAKLETY_GEN_SAFE_V1: the repo's client atlas (was a client build's temporary check folder, since gone)
OUR_ATLAS = os.path.join(REPO, 'client-patches', 'client-2.0.30', 'gamedata', 'gamedata', 'atlasinfo.txt')
# the server Setting.txt bases of the test share (docker exec mt2009plustest-game ... - name, MapSize, BasePosition),
# taken 15 October 2026; and the atlas rows of every Yohara generator's client json (maps the client gets later)
SERVER_BASES = os.path.join(HERE, 'server_bases.txt')
MOTIONS = ['reddragon_room_boss2', 'reddragon_room_human_boss', 'reddragon_room_fly', 'magma_crystal',
           'metinstone_reddragon_statue', 'metinstone_egg']
SUB = 'meley'
QUEST_POINTS = dict(entry=[D.INSIDE], stones=D.STONES, center=[D.CENTER], gate=[D.GATE_CELL],
                    watcher=[D.WATCHER_INSIDE])
QUEST_SPAWNED = [D.STONE, D.KING, D.EGG, D.BOSS, D.KNIGHT, D.GATE, D.WATCHER, D.GOLD_CHEST]
SUMMONS = [D.KNIGHT]                    # Idall's SummonVnum


def overlaps(base, size, rows):
    x0, y0 = base
    x1, y1 = x0 + size[0] * 25600, y0 + size[1] * 25600
    return [n for n, a0, b0, w, h in rows if a0 < x1 and x0 < a0 + w * 25600 and b0 < y1 and y0 < b0 + h * 25600]


def atlas_rows(a):
    ours, gf, srv = [], [], []
    for l in open(OUR_ATLAS, encoding='latin-1'):
        t = l.split()
        if len(t) >= 5 and t[1].isdigit():
            ours.append((t[0], int(t[1]), int(t[2]), int(t[3]), int(t[4])))
    for p in sorted(os.listdir(os.path.join(REPO, 'tools'))):
        d = os.path.join(REPO, 'tools', p)
        if not os.path.isdir(d) or p == 'yohara_meley':
            continue
        for f in os.listdir(d):
            if f.endswith('.json'):
                try:
                    j = json.load(open(os.path.join(d, f), encoding='utf-8'))
                except ValueError:
                    continue
                for r in (j.get('atlas') or []) if isinstance(j, dict) else []:
                    t = r.split('\t')
                    ours.append((t[0], int(t[1]), int(t[2]), int(t[3]), int(t[4])))
    for l in open(os.path.join(a.gf, 'shared/common/atlasinfo.txt'), encoding='latin-1'):
        t = l.split()
        if len(t) >= 5 and t[1].isdigit():
            gf.append((t[0], int(t[1]), int(t[2]), int(t[3]), int(t[4])))
    for l in open(SERVER_BASES, encoding='utf-8'):
        m = re.match(r'(\S+)\s+MapSize\s+(\d+)\s+(\d+)\s+BasePosition\s+(\d+)\s+(\d+)', l)
        if m:
            srv.append((m.group(1), int(m.group(4)), int(m.group(5)), int(m.group(2)), int(m.group(3))))
    assert len(ours) > 100 and len(gf) > 100 and len(srv) > 100, (len(ours), len(gf), len(srv))
    return ours, gf, srv


def gen_map(a, report):
    import srvattr as sa
    m = D.MAP
    for sub in ('map', 'data'):
        shutil.rmtree(os.path.join(OUT, sub), ignore_errors=True)       # README.md (by hand) stays
    dst = os.path.join(OUT, 'map', m['folder'])
    os.makedirs(dst)
    osrc = os.path.join(a.owsap, 'share/locale/uk/map', m['owsap'])
    st = open(os.path.join(osrc, 'Setting.txt'), encoding='latin-1').read()
    assert re.search(r'MapSize\s+%d\s+%d' % m['size'], st) and re.search(r'BasePosition\s+%d\s+%d' % m['gf_base'], st)
    gfst = open(os.path.join(a.gf, 'shared/common/atlasinfo.txt'), encoding='latin-1').read()
    assert re.search(r'(?m)^%s\s+%d\s+%d\s+%d\s+%d' % ((m['folder'],) + m['gf_base'] + m['size']), gfst)
    assert 'ParentMapName' not in open(os.path.join(a.gf, m['folder'], 'mapproperty.txt'), encoding='latin-1').read()
    ours, gf, srv = atlas_rows(a)
    bad = overlaps(m['base'], m['size'], ours) + overlaps(m['base'], m['size'], srv)
    bad = [f for f in bad if f != m['folder']] + overlaps(m['base'], m['size'], gf)
    assert not bad, ('the base overlaps', bad)
    assert overlaps(m['gf_base'], m['size'], ours), 'the official base is free - use it'
    st = re.sub(r'BasePosition\s+\d+\s+\d+', 'BasePosition\t%d\t%d' % m['base'], st)
    open(os.path.join(dst, 'Setting.txt'), 'w', newline='').write(st.replace('\r\n', '\n').replace('\n', '\r\n'))
    open(os.path.join(dst, 'Town.txt'), 'w', newline='').write('%d\t%d\r\n' % m['town'])
    W, H, g, LW, LH, walk, own = YI.client_grid(a.gf, dict(m, src=m['folder'], own_attr=None))
    # Meley's cells: GF's arena wall - opened (the server only: nobody walks there, the walls around stay)
    kx, ky = D.KING_CELL
    opened = 0
    for y in range(2 * (ky - D.KING_OPEN), 2 * (ky + D.KING_OPEN) + 2):
        for x in range(2 * (kx - D.KING_OPEN), 2 * (kx + D.KING_OPEN) + 2):
            if g[y * W + x] & 1:
                opened += 1
            g[y * W + x] &= ~1 & 0xff
    sa.write_server(os.path.join(dst, 'server_attr'), W, H, g)
    W2, H2, g2 = sa.grid_from_server(*sa.read_server(os.path.join(dst, 'server_attr')))
    assert (W2, H2) == (W, H) and g2 == g
    blocked = []
    for k, pts in QUEST_POINTS.items():
        for x, y in pts:
            assert 0 <= x < LW and 0 <= y < LH, (k, x, y)
            if not walk[y * LW + x]:
                blocked.append('%s %d,%d' % (k, x, y))
    assert not blocked, blocked
    # nobody can walk to Meley: no walkable cell links her opened square with the arena (a flood from the entry)
    seen, todo = set([D.INSIDE]), [D.INSIDE]
    while todo:
        x, y = todo.pop()
        for nx, ny in ((x + 1, y), (x - 1, y), (x, y + 1), (x, y - 1)):
            if 0 <= nx < LW and 0 <= ny < LH and (nx, ny) not in seen and not (g[2 * ny * W + 2 * nx] & 1):
                seen.add((nx, ny))
                todo.append((nx, ny))
    assert (kx, ky) not in seen and all(p in seen for p in D.STONES + [D.CENTER, D.GATE_CELL]), 'Meley reachable'
    report.append('%d %s: base %d %d (GF\'s %d %d is our Zodiac temple\'s; no overlap in our atlas, the server bases or '
                  'GF\'s atlas), server_attr %dx%d cells = GF attr.atr, %d cells opened under Meley (%d,%d - not '
                  'reachable from the arena), quest points %d walkable' % (
                      m['index'], m['folder'], m['base'][0], m['base'][1], m['gf_base'][0], m['gf_base'][1], W, H,
                      opened, kx, ky, sum(len(v) for v in QUEST_POINTS.values())))
    # Doyyumhwaji: Dolnarr's cell and the landing (GF's metin2_map_n_flame_01 attr.atr = ours)
    fm = D.FLAME
    W3, H3, g3, LW3, LH3, walk3, own3 = YI.client_grid(a.gf, dict(fm, src=fm['folder'], own_attr=None))
    x, y, d = D.WATCHER_CELL
    assert walk3[y * LW3 + x] and walk3[D.LANDING[1] * LW3 + D.LANDING[0]], ('62', x, y, D.LANDING)
    open(os.path.join(OUT, 'flame_npc.txt'), 'w', newline='').write(
        'm\t%d\t%d\t0\t0\t0\t%d\t1m\t100\t1\t%d\r\n' % (x, y, d, D.WATCHER))
    report.append('62 %s: Dolnarr %d,%d and the landing %d,%d walkable' % ((fm['folder'], x, y) + D.LANDING))
    # the stages' spawn files: 12 of the stage's monster, three at each statue (Owsap: the statue's cell, the engine
    # puts each beside it), back after the stage's respawn; the extra groups between the statues
    d2 = os.path.join(OUT, 'data', 'dungeon', SUB)
    os.makedirs(d2)
    for s, cfg in sorted(D.STAGES.items()):
        out = []
        for i in range(cfg['count']):
            x, y = D.STONES[i % len(D.STONES)]
            out.append('m\t%d\t%d\t3\t3\t0\t0\t%ds\t100\t1\t%d' % (x, y, cfg['respawn'], cfg['mob']))
        for gv in cfg['groups']:
            x, y = D.CENTER
            out.append('g\t%d\t%d\t6\t6\t0\t0\t%ds\t100\t1\t%d' % (x, y, D.GROUP_RESPAWN, gv))
        open(os.path.join(d2, 'stage%d.txt' % s), 'w', newline='').write(YI.crlf_text(out))
    report.append('data/dungeon/%s: stage1-3.txt (%s)' % (SUB, ', '.join(
        '%d x %d / %ds' % (c['count'], c['mob'], c['respawn']) for s, c in sorted(D.STAGES.items()))))
    # the motions our share lacks (the test share has ice_snow_* - Nemere's monsters' folders)
    mot = os.path.join(OUT, 'data', 'monster')
    for f in MOTIONS:
        s = os.path.join(a.owsap, 'share/data/monster', f)
        assert os.path.isfile(os.path.join(s, 'motlist.txt')), f
        if os.path.isfile(os.path.join(s, 'run.msa')):
            acc = re.search(r'^Accumulation\s+[-0-9.]+\s+-[0-9]', open(os.path.join(s, 'run.msa'), encoding='latin-1')
                            .read(), re.M)
            assert acc, ('run.msa without Accumulation', f)
        shutil.copytree(s, os.path.join(mot, f))
    report.append('data/monster: %s (Owsap\'s motions)' % ', '.join(MOTIONS))


def owsap_groups(a):
    t = open(os.path.join(a.owsap, 'share/locale/uk/group_builder/group/red_dragonlair.txt'),
             encoding='latin-1').read().replace('\r', '')
    out = {}
    for m in re.finditer(r'Group\s+(\S+)\s*\{(.*?)\}', t, re.S):
        b = m.group(2)
        v = int(re.search(r'Vnum\s+(\d+)', b).group(1))
        lead = re.search(r'Leader\s+"?[^"\n]*"?\s+(\d+)', b)
        mem = [int(x) for x in re.findall(r'\n\s*\d+\s+"?[^"\n]*?"?\s+(\d+)\s*(?=\n|$)', b)]
        out[v] = (m.group(1), [int(lead.group(1))] + mem)
    return out


def write_groups(a, rows):
    og = owsap_groups(a)
    assert og == D.GROUPS, og
    L = ['// %s: the spawn groups of Schronienie Meley - Owsap\'s red_dragonlair_1..3 (6337-6339, free here):' % M,
         '// the statues\' and the eggs\' summons (their rows\' attack / move speed) and the stages\' extra group.',
         '// GENERATED by tools/yohara_meley/gen_ymeley.py - do not edit.']
    names = dict((v, n) for v, (n, e) in D.MOBS.items())
    names.update({6006: 'Ognisty Golem', 6007: 'Ognista Broda Zaru', 6009: 'Ognisty Ksiaze Zaru'})
    for v, (name, mobs) in sorted(D.GROUPS.items()):
        L += ['Group\tMT2009_yml_%s' % name, '{', '\tLeader\t"%s"\t%d' % (YI.ascii_pl(names[mobs[0]]), mobs[0]),
              '\tVnum\t%d' % v]
        for i, mob in enumerate(mobs[1:], 1):
            L.append('\t%d\t"%s"\t%d' % (i, YI.ascii_pl(names[mob]), mob))
        L += ['}', '']
    open(os.path.join(OUT, 'group.yohara_meley.txt'), 'w', newline='\n').write('\n'.join(L))
    # the statues and eggs summon these groups (Owsap's rows: MoveSpeed / AttackSpeed = the group vnums)
    for v in (D.STONE, D.EGG):
        assert {int(rows[v]['MoveSpeed']), int(rows[v]['AttackSpeed'])} == {6337, 6339}, v


def write_spawned(report):
    vs = set(QUEST_SPAWNED) | set(SUMMONS)
    for s, cfg in D.STAGES.items():
        vs.add(cfg['mob'])
        for gv in cfg['groups']:
            vs |= set(D.GROUPS[gv][1])
    for gv in (6337, 6339):
        vs |= set(D.GROUPS[gv][1])
    known = set(D.MOBS) | set(D.NPCS) | {D.GATE, 6006, 6007, 6009}
    assert vs <= known, sorted(vs - known)
    assert set(D.MOBS) - vs == set(), sorted(set(D.MOBS) - vs)
    lines = ['# %s: every vnum the map shows (the stages\' spawn files and groups unfolded, the statues\' and' % M,
             '# eggs\' groups, the quest\'s spawns, Idall\'s men) - the client builder (client-patches/client-2.0.30/',
             '# tools/ymeley) reads it; "62 20419" is Dolnarr on Doyyumhwaji. GENERATED by tools/yohara_meley/gen_ymeley.py.',
             '62 %d' % D.WATCHER]
    lines += ['%d %d' % (D.MAP['index'], v) for v in sorted(vs)]
    open(os.path.join(OUT, 'spawned.txt'), 'w', newline='\n').write('\n'.join(lines) + '\n')
    report.append('spawned: %d vnums on 356, Dolnarr on 62' % len(vs))


# ------------------------------------------------------------------------------------------------ mob_proto
SQL_HEAD = """-- %(m)s: Schronienie Meley (356, metin2_map_n_flame_dragon) - the Dragon Queen's lair (the owner, 15 October
-- 2026). GENERATED by tools/yohara_meley/gen_ymeley.py - do not edit, rerun it. Every start (apply.sh), idempotent:
-- INSERT IGNORE - a row the operator changed is kept. Every vnum was free in our world (15 October 2026).
-- %(n)d rows: %(mobs)d monsters, bosses and stones (Owsap v6.2.6 db/mob_proto.txt - the guild lair's official rows
-- - in our r40250 columns, tools/yohara_maps/gen_ymaps_sql.row_of; the Polish names and the Basis-EXP of the pl-wiki
-- where Owsap's guild rows give none) and %(npcs)d NPCs (Straznik Smokow Dolnarr, Zlota Smocza Skrzynia - Owsap's
-- numbers, our NPCs' figures). 20388 Smocza Brama is ours (Razador). The element: yohara_meley_zywioly.sql.
SET NAMES utf8mb4;

"""

ZHEAD = """-- %s: the element of Schronienie Meley - the pl-wiki's "Element Ognia" of every monster, Idall and Meley
-- (setRaceFlag bit 4096); the statues and the eggs none. GENERATED by tools/yohara_meley/gen_ymeley.py. apply.sh runs
-- it AFTER zywioly_moby.sql, which clears bits 11-16 of every mob it does not list: idempotent.
SET NAMES utf8mb4;""" % M


def owsap_rows(a):
    rows = {}
    for r in csv.DictReader(open(os.path.join(a.owsap, 'db', 'mob_proto.txt'), encoding='latin-1'), delimiter='\t'):
        if r['Vnum'].isdigit():
            rows[int(r['Vnum'])] = r
    return rows


def gen_mobs(a, rows, report):
    en = {}
    for line in open(os.path.join(a.owsap, 'db', 'mob_names.txt'), encoding='latin-1'):
        p = line.rstrip('\r\n').split('\t')
        if len(p) >= 2 and p[0].isdigit():
            en[int(p[0])] = p[1]
    lines = []
    for v in sorted(D.MOBS):
        pl, elem = D.MOBS[v]
        assert len(pl.encode('cp1250')) <= 24, pl
        r = dict(rows[v])
        assert r['Type'] in ('MONSTER', 'STONE'), (v, r['Type'])
        assert r['MinGold'] == '0' and r['MaxGold'] == '0', v
        assert (r['AttFire'] != '0') == (elem == D.FIRE), (v, r['AttFire'])
        r.update(D.OVERRIDE.get(v, {}))
        lines.append(row_of(r, en.get(v, pl)[:24], pl))
    for v in sorted(D.NPCS):
        en_n, pl = D.NPCS[v]
        assert len(pl.encode('cp1250')) <= 24, pl
        assert rows[v]['Type'] == 'NPC', v
        lines.append(npc_row(v, en_n[:24], pl, ''))
    assert len(set(t[0] for t in lines)) == len(lines)
    for t in lines:
        assert len(t) == len(COLS), (t[0], len(t))
    with open(SQL_OUT, 'w', encoding='utf-8', newline='\n') as f:
        f.write(SQL_HEAD % dict(m=M, n=len(lines), mobs=len(D.MOBS), npcs=len(D.NPCS)))
        f.write('INSERT IGNORE INTO world.mob_proto (%s) VALUES\n' % ','.join('`%s`' % c for c in COLS))
        f.write(',\n'.join('(%s)' % ','.join(str(x) for x in t) for t in lines) + ';\n')
    fire = sorted(v for v, (pl, e) in D.MOBS.items() if e == D.FIRE)
    none = sorted(v for v, (pl, e) in D.MOBS.items() if not e)
    L = [ZHEAD, '-- ogien: %s' % ','.join(map(str, fire)),
         'UPDATE world.mob_proto SET setRaceFlag = ((setRaceFlag + 0) & ~%d) | %d WHERE vnum IN (%s);'
         % (D.ELEMENT_BITS, D.FIRE, ','.join(map(str, fire))),
         '-- no element (the statues, the eggs): %s' % ','.join(map(str, none)),
         'UPDATE world.mob_proto SET setRaceFlag = (setRaceFlag + 0) & ~%d WHERE vnum IN (%s) AND '
         '(setRaceFlag + 0) & %d <> 0;' % (D.ELEMENT_BITS, ','.join(map(str, none)), D.ELEMENT_BITS)]
    with open(ZYW_OUT, 'w', encoding='utf-8', newline='\n') as f:
        f.write('\n'.join(L) + '\n')
    report.append('mob_proto rows: %d (monsters/stones %d, NPCs %d); fire %d' % (len(lines), len(D.MOBS), len(D.NPCS),
                                                                             len(fire)))
    return lines


# ------------------------------------------------------------------------------------------------ the items
ITEM_TEXT = {
    D.RING: 'Otacza cię aura przepełniona energią. Pierścień wykuty ze smoczego ognia zniszczy w mgnieniu oka statuy '
            'w Schronieniu Meley - gdy statuy zaświecą na niebiesko, stań przy statui i kliknij pierścień prawym '
            'przyciskiem myszy. Znika po wyjściu ze Schronienia.',
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
    items = []
    for v in (D.RING, D.CHEST_QUEEN, D.CHEST_GUARD):
        src = D.ITEM_SRC[v]
        o = proto[src]
        name, text = desc[src]
        assert name and len(name.encode('cp1250')) <= 24, (v, name)
        if v == D.RING:
            # the pl-wiki: NPC trade, players, shop, storage no; dropping yes; stacking yes. A quest item (used
            # beside a statue - meley_dungeon; the client drags an item onto an NPC only, the statue is a stone),
            # gone when its owner leaves the lair
            typ, sub = 18, 0
            anti = Y.ANTI['ANTI_SELL'] | Y.ANTI['ANTI_GIVE'] | Y.ANTI['ANTI_MYSHOP'] | Y.ANTI['ANTI_SAFEBOX']
            flag = Y.FLAGS['ITEM_STACKABLE'] | Y.FLAGS['ITEM_QUEST_USE']      # the quest's "use" beside a statue
            icon, model = 'icon/item/%d.tga' % v, ''
            gf_icon = gf_list[src]
        else:
            # a chest opened once (the pl-wiki: "Ze skrzyni dropi kilka losowych przedmiotów", stacking yes, trade
            # yes) - our 54706 / 54707: the official 50270 / 50271 are our Skrzynia Razadora / Nemere
            assert o['Type'] == 'ITEM_GIFTBOX', v
            typ, sub, anti = 23, 0, 0
            flag = Y.FLAGS['ITEM_STACKABLE']
            icon, model = gf_list[src], 'd:/ymir work/item/etc/boss_box.gr2'      # icon/item/50270.tga - ours too
            gf_icon = None
        items.append(dict(
            vnum=v, src=src, status=Y.ST, name=Y.ascii_name(name), locale_name=name, type=typ, subtype=sub,
            stack=200 if flag & Y.FLAGS['ITEM_STACKABLE'] else 1, weight=0, size=int(o['Size']), antiflag=anti,
            flag=flag, wearflag=0, gold=0, shop_buy_price=int(o['ShopSellPrice']),
            refined_vnum=0, refine_set=0, magic_pct=0, specular=0, socket_pct=0, addon_type=0,
            limittype0=0, limitvalue0=0, limittype1=0, limitvalue1=0,
            applytype0=0, applyvalue0=0, applytype1=0, applyvalue1=0, applytype2=0, applyvalue2=0,
            value0=0, value1=0, value2=0, value3=0, value4=0, value5=0,
            icon=icon, icon_src=gf_icon, desc=ITEM_TEXT.get(v, text), list_type='ETC', model=model))
    L = ['-- %s: Pierscien Smoczego Ognia (30340 - the official 30341 is our Zupa Grzybowa) and the two chests' % M,
         '-- of Schronienie Meley: Skrzynia Krolowej Meley (54706) and Skrzynia Sm. Straznikow (54707) - the official',
         '-- 50270 / 50271 are our Skrzynia Razadora / Nemere. GENERATED by tools/yohara_meley/gen_ymeley.py - do not',
         '-- edit, rerun it. Every start (apply.sh), idempotent: INSERT IGNORE. Source: Owsap v6.2.6 db/item_proto.txt',
         '-- (30341, 50270, 50271), the Polish names and texts of its Polish client, the pl-wiki\'s trade rules. Every',
         '-- vnum free in our world and in GF\'s item_list (15 October 2026). Czerwony Smoczy Rog (30620), Czerwona',
         '-- Smocza Luska (30621) and Plan Zbroi: Helm (30622) are yohara_helm100.sql\'s rows.',
         'SET NAMES utf8mb4;',
         'INSERT IGNORE INTO world.item_proto (%s) VALUES' % ','.join('`%s`' % c for c in Y.COLS),
         ',\n'.join(Y.sqlrow(i) for i in items) + ';']
    with open(ITEMS_OUT, 'w', encoding='utf-8', newline='\n') as f:
        f.write('\n'.join(L) + '\n')
    os.makedirs(ICON_OUT, exist_ok=True)
    src = os.path.join(a.gf, gf_list[D.ITEM_SRC[D.RING]].replace('\\', '/'))
    assert os.path.isfile(src), src
    shutil.copyfile(src, os.path.join(ICON_OUT, '%d.tga' % D.RING))
    report.append('items %d (%s), the ring\'s icon = GF %s' % (len(items), ', '.join(i['locale_name'] for i in items),
                                                              gf_list[D.ITEM_SRC[D.RING]]))
    return items


# -- items we have, by the pl-wiki's name (checked on the test server's world.item_proto, 15 October 2026) ----------
HAVE = {
    27992: 'Biala Perla', 27993: 'Niebieska Perla', 27994: 'Krwawa Perla', 30011: 'Klab', 30031: 'Ornament',
    30035: 'Krem Do Twarzy', 30042: 'Pazur Tygrysa', 30080: 'Ksiega Klatw+', 30083: 'Nieznane Lekarstwo+',
    30089: 'Futro Yeti+', 30192: 'Mleczny Sok', 30193: 'Kosc Palca', 30194: 'Orkowa Maczuga', 30550: 'Niebieski Rzemyk',
    39004: 'Kula Blogoslawienstwa', 50513: 'Kamien Duchowy', 55003: 'Ksiega Mlodego Zwierza',
    55004: 'Ksiega Dzikiego Zwierza', 55005: 'Ksiega Dzielnego Zwierza', 55411: 'Jajo Exedyara',
    55406: 'Czerwone Jajo Smoka', 70031: 'Broszura Szermierki', 100700: 'Smoczy Plomien (B)',
    50323: 'Skrzynia Ksiag: Riposta', 50324: 'Skrzynia Ksiag: Dopalacz',
    460: 'Runiczny Miecz', 1340: 'Kolec Pieciu Elementow', 2370: 'Luk Feniksa', 3190: 'Ostrze Slonca',
    5340: 'Dzwon Smoczego Ducha', 7370: 'Wachlarz Lezac. Smoka',
    12284: 'Helm Mistrza Wojny+4', 12285: 'Helm Mistrza Wojny+5', 12286: 'Helm Mistrza Wojny+6',
    12404: 'Pajeczy Kaptur+4', 12405: 'Pajeczy Kaptur+5', 12406: 'Pajeczy Kaptur+6',
    12544: 'Magiczny Helm+4', 12545: 'Magiczny Helm+5', 12546: 'Magiczny Helm+6',
    12684: 'Kapelusz Duszy+4', 12685: 'Kapelusz Duszy+5', 12686: 'Kapelusz Duszy+6',
    15374: 'Buty Euforii+4', 15375: 'Buty Euforii+5', 15376: 'Buty Euforii+6',
    15434: 'Buty Zimorodka+4', 15435: 'Buty Zimorodka+5', 15436: 'Buty Zimorodka+6',
    # claude/yohara-helm100 (yohara_helm100.sql, merged into claude/yohara-3 on 15 October)
    D.RED_HORN: 'Czerwony Smoczy Rog', D.RED_SCALE: 'Czerwona Smocza Luska', D.HELM_PLAN: 'Plan Zbroi: Helm',
}

# -- the chests: the pl-wiki's lists, one bullet = one equal share (TEMP - PROCENTY.md: the owner's sheet will give
#    the real chances), a bullet with variants (+4/+5/+6, x5/x10, 10-60 mln Yang) splits its share; DRAWS things an
#    opening (the wiki: "kilka losowych przedmiotów"). Left out - not in our world: Helm Zielonego Lasu (21544-21546 -
#    the Lycan's), Wladca Smokow (6090). MT2009_PLUS_GROWTH_PET_V1 (4 November 2026): Ksiega Dzikiego / Dzielnego
#    Zwierza (55004 / 55005) are ours now - a bullet each, like Ksiega Mlodego Zwierza; the queen's chest also gives
#    Jajo Exedyara (55411) at half the share of Czerwone Jajo Smoka (a row (vnum, count, weight) keeps its own weight)
#    - our stand-in for the Dragon Kings, whom this world lacks. Kufer / Skrzynia Riposty
#    / Dopalacza (the official 50296-50299, five books / five chests of books): our Skrzynia Ksiag: Riposta /
#    Dopalacz (50323 / 50324) - one for a Skrzynia, five for a Kufer. ---------------------------------------------
SHARE = 12
DRAWS = 3


def chest_bullets():
    queen = [
        [(55406, 1)], [(27994, 1)], [(27993, 1)], [(27992, 1)], [(D.HELM_PLAN, 1)], [(30194, 5)], [(30011, 5)],
        [(30089, 5)], [(30083, 5)], [(30035, 5)], [(30192, 5)], [(D.RED_SCALE, 3)], [(D.RED_HORN, 3)], [(30550, 5)],
        [(39004, 1)], [(50513, 1)], [(55003, 1)], [(55004, 1)], [(55005, 1)], [(50324, 5)], [(50323, 5)],
        [(55411, 1, SHARE // 2)],
        [(15374, 1), (15375, 1), (15376, 1)], [(15434, 1), (15435, 1), (15436, 1)],
        [(12404, 1), (12405, 1), (12406, 1)], [(12684, 1), (12685, 1), (12686, 1)],
        [(12284, 1), (12285, 1), (12286, 1)], [(12544, 1), (12545, 1), (12546, 1)],
        [(2370, 1)], [(460, 1)], [(7370, 1)], [(5340, 1)], [(70031, 1)],
        [('gold', 10000000)], [('gold', 20000000)], [('gold', 30000000)], [('gold', 60000000)],
    ]
    guard = [
        [(27992, 1)], [(15374, 1), (15375, 1), (15376, 1)], [(D.RED_SCALE, 3)], [(D.RED_HORN, 3)],
        [(30089, 5), (30089, 10)], [(12284, 1), (12285, 1), (12286, 1)], [(30011, 5), (30011, 10)], [(1340, 1)],
        [(30193, 5)], [(30035, 10)], [(27994, 1)], [(30080, 10)], [(55003, 1)], [(55004, 1)], [(55005, 1)],
        [(50324, 5)],
        [(12544, 1), (12545, 1), (12546, 1)], [(30192, 5)], [(27993, 1)], [(30550, 5), (30550, 10)], [(30083, 10)],
        [(30194, 2)], [(30031, 10)], [(3190, 1)], [(30042, 2)], [(D.HELM_PLAN, 5)], [(460, 1)], [(50324, 1)],
        [(50323, 1)], [(100700, 1)],
        [('gold', 10000000), ('gold', 20000000), ('gold', 30000000), ('gold', 60000000)],
    ]
    return [(D.CHEST_QUEEN, 'Skrzynia Krolowej Meley', queen), (D.CHEST_GUARD, 'Skrzynia Sm. Straznikow', guard)]


def nm(byv, v, c=1):
    if v == 'gold':
        return 'Yang %d' % c
    n = byv[v]['name'] if v in byv else HAVE[v]
    return n + (' x%d' % c if c > 1 else '')


def write_sig(byv):
    L = ['# %s: the chests of Schronienie Meley - Skrzynia Krolowej Meley (54706) and Skrzynia Sm. Straznikow' % M,
         '# (54707), the pl-wiki\'s lists. Each is a Pct group of %d lines at 100%%: %d things an opening, each from the' % (
             DRAWS, DRAWS),
         '# nested group (95470x) by weight. TEMP - PROCENTY.md: every bullet of the wiki an equal share (%d), its' % SHARE,
         '# variants splitting it; the owner\'s sheet will give the chances. GENERATED by tools/yohara_meley/gen_ymeley.py',
         '# - do not edit. Appended to special_item_group.txt by the Dockerfile.', '']
    for vnum, title, bullets in chest_bullets():
        nested = 900000 + vnum
        L += ['Group\tMT2009_yml_%d' % vnum, '{', '\tVnum\t%d -- %s' % (vnum, title), '\tType\tPct']
        for k in range(1, DRAWS + 1):
            L.append('\t%d\ts%d\t1\t100 -- TEMP - PROCENTY.md: draw %d of %d' % (k, nested, k, DRAWS))
        L += ['}', 'Group\tMT2009_yml_%d_rows' % vnum, '{',
              '\tVnum\t%d -- %s - the wiki\'s rows, TEMP - PROCENTY.md: equal shares' % (nested, title)]
        k = 0
        for b in bullets:
            assert SHARE % len(b) == 0, b
            for e in b:
                v, c = e[:2]
                w = e[2] if len(e) > 2 else SHARE // len(b)
                assert v == 'gold' or v in byv or v in HAVE, v
                k += 1
                L.append('\t%d\t%s\t%d\t%d -- %s (TEMP - PROCENTY.md)' % (k, v, c, w, nm(byv, v, c)))
        L += ['}', '']
    with open(os.path.join(OUT, 'special_item_group.yohara_meley.txt'), 'w', encoding='utf-8', newline='\n') as f:
        f.write('\n'.join(L))


# -- the drops (mob_drop_item, Type drop: vnum, count, percent): the pl-wiki's list of each monster - TEMP rates
#    (the owner, 15 October: materials 20-30%, rare 10%; PROCENTY.md "Do ustalenia" 5). Pierscien Smoczego Ognia is
#    the quest's (meley_dungeon: Owsap's DropPct - 5% of a stage monster in stages 1-2, 1% in 3-4 - for every magma
#    monster, given to a person). Magmowy Insekt, Idall, Slugus Idalla, Meley and the statues: none on the wiki. -----
def drops():
    mats = [(D.RED_SCALE, 1, 25), (D.HELM_PLAN, 1, 20), (D.RED_HORN, 1, 25)]
    return [
        (6110, 'Magmowy Yeti', mats),
        (6111, 'Golem Lawy', mats),
        (6113, 'Magmowy Golem', mats),
        (6114, 'Magmowy Krysztal', mats),
        (6115, 'Magmowy Wiwern', mats),
        (D.EGG, 'Jajo Smoka', [(50513, 1, 10)]),
    ]


# a "drop" line's percent P is P/4 % a kill (P * 10000 against the engine's 4 000 000, times the level difference and
# the drop bonus - item_manager.cpp): the chances above are a kill's, the file gets four times them
FILE_PER_PCT = 4


def write_drops(byv):
    L = ['// %s: drops of Schronienie Meley - the pl-wiki\'s lists ("Magmowy Yeti", "Magmowy Wiwern", "Golem' % M,
         '// Lawy", "Magmowy Golem", "Magmowy Krysztal": Czerwona Smocza Luska, Plan Zbroi Helm, Czerwony Smoczy Rog;',
         '// "Jajo Smoka": Kamien Duchowy). GENERATED by tools/yohara_meley/gen_ymeley.py - do not edit.',
         '// TEMP - PROCENTY.md: the wiki gives no chances - ours for now (materials 20-30%, rare 10% a kill). A line\'s',
         '// percent P is P/4 % a kill (the engine rolls P * 10000 against 4 000 000), so the file holds four times the',
         '// chance: 100 = 25%, 80 = 20%, 40 = 10% (before the level difference and the drop bonus).', '']
    for v, n, rows in drops():
        assert v in D.MOBS, v
        L += ['Group\tMT2009_yml_%d' % v, '{', '\tMob\t%d\t-- %s' % (v, n), '\tType\tdrop']
        for k, (iv, c, p) in enumerate(rows, 1):
            assert iv in byv or iv in HAVE, (v, iv)
            L.append('\t%d\t%d\t%d\t%s\t-- %s - %g%% a kill (TEMP - PROCENTY.md)' % (
                k, iv, c, '%g' % (p * FILE_PER_PCT), nm(byv, iv, c), p))
        L += ['}', '']
    with open(os.path.join(OUT, 'mob_drop_item.yohara_meley.txt'), 'w', encoding='utf-8', newline='\n') as f:
        f.write('\n'.join(L))


def write_client(mob_lines, items):
    keys = ('vnum', 'name', 'locale_name', 'type', 'subtype', 'stack', 'weight', 'size', 'antiflag', 'flag',
            'wearflag', 'gold', 'shop_buy_price', 'refined_vnum', 'refine_set', 'magic_pct', 'specular', 'socket_pct',
            'limittype0', 'limitvalue0', 'limittype1', 'limitvalue1', 'applytype0', 'applyvalue0', 'applytype1',
            'applyvalue1', 'applytype2', 'applyvalue2', 'value0', 'value1', 'value2', 'value3', 'value4', 'value5')
    m = D.MAP

    def lst(i):
        return '%d\t%s\t%s' % (i['vnum'], i['list_type'], i['icon']) + ('\t' + i['model'] if i['model'] else '')
    out = {'cols': list(COLS), 'rows': [list(t) for t in mob_lines],
           'elements': dict((str(v), e) for v, (pl, e) in D.MOBS.items()),
           'atlas': ['%s\t%d\t%d\t%d\t%d' % (m['folder'], m['base'][0], m['base'][1], m['size'][0], m['size'][1])],
           'base': list(m['base']), 'gf_base': list(m['gf_base']),
           'items': [dict((k, i[k]) for k in keys) for i in items],
           'item_list': dict((str(i['vnum']), lst(i)) for i in items),
           'itemdesc': dict((str(i['vnum']), '%d\t%s\t%s' % (i['vnum'], i['locale_name'], Y.client_desc(i)))
                            for i in items),
           'icons_added': ['icon/item/%d.tga' % D.RING]}
    with open(JSON_OUT, 'w', encoding='utf-8', newline='\n') as f:
        json.dump(out, f, ensure_ascii=False, indent=0)
        f.write('\n')


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--owsap', default='/opt/metin2/cache/owsap/Server/Server')
    ap.add_argument('--gf', default='/opt/metin2/cache/gf/Gameforge_26.1.11/_client')
    a = ap.parse_args()
    report = []
    rows = owsap_rows(a)
    gen_map(a, report)
    write_groups(a, rows)
    write_spawned(report)
    mob_lines = gen_mobs(a, rows, report)
    items = gen_items(a, report)
    byv = dict((i['vnum'], i) for i in items)
    write_drops(byv)
    write_sig(byv)
    write_client(mob_lines, items)
    report.append('drops: %d groups; chests: %d (%d draws an opening)' % (len(drops()), len(chest_bullets()), DRAWS))
    print('\n'.join(report))


if __name__ == '__main__':
    main()
