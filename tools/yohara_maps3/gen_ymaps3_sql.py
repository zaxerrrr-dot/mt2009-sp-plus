#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""gen_ymaps3_sql.py [--owsap DIR]

MT2009_PLUS_YOHARA_MAPS3_V1: the world.mob_proto rows of the third batch of Yohara places (ymaps3_data.py) -
monsters, bosses and Metins from Owsap v6.2.6's db/mob_proto.txt (the official vnums, levels, HP, damage, AI, resists)
in our r40250 columns with the Polish names of Owsap's Polish client (= the official ones), the NPCs on our own NPC
numbers (Owsap's NPC rows lack a column - tools/yohara_maps/gen_ymaps_sql.npc_row), the portals (WARP 3: global
coordinates / 100; GOTO 9: the map's own - the official names).

Writes
  linux-port/docker/mariadb/playerbot/yohara_maps3.sql          INSERT IGNORE (apply.sh, after yohara_maps.sql)
  linux-port/docker/mariadb/playerbot/yohara_maps3_zywioly.sql  the elements (apply.sh, after zywioly_moby.sql -
                                                                that file clears bits 11-16 of every mob it does
                                                                not list)
  tools/yohara_maps3/ymaps3_mobs.json                           the client's rows (client-2.0.30/tools/ymaps3)

Example: python3 tools/yohara_maps3/gen_ymaps3_sql.py
"""
import argparse
import csv
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(os.path.dirname(HERE))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(REPO, 'tools', 'yohara_maps'))
import ymaps3_data as D  # noqa: E402
from gen_ymaps_sql import COLS, row_of, npc_row, warp_row, q  # noqa: E402

SQL_OUT = os.path.join(REPO, 'linux-port', 'docker', 'mariadb', 'playerbot', 'yohara_maps3.sql')
ZYW_OUT = os.path.join(REPO, 'linux-port', 'docker', 'mariadb', 'playerbot', 'yohara_maps3_zywioly.sql')
JSON_OUT = os.path.join(HERE, 'ymaps3_mobs.json')


def ascii_pl(s):
    return s.translate(str.maketrans('ąćęłńóśźżĄĆĘŁŃÓŚŹŻ', 'acelnoszzACELNOSZZ'))


def portal_row(vnum, typ, name, pl):
    t = list(warp_row(vnum, name))
    t[2] = q(pl)
    t[4] = typ
    if typ == D.GOTO:      # our GOTO doors (10501...): rank 0, battle 0, level 1
        t[5], t[6] = 0, 1
    return tuple(t)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--owsap', default='/opt/metin2/cache/owsap/Server/Server')
    a = ap.parse_args()
    en = {}
    for line in open(os.path.join(a.owsap, 'db', 'mob_names.txt'), encoding='latin-1'):
        p = line.rstrip('\r\n').split('\t')
        if len(p) >= 2 and p[0].isdigit():
            en[int(p[0])] = p[1]
    rows = {}
    for r in csv.DictReader(open(os.path.join(a.owsap, 'db', 'mob_proto.txt'), encoding='latin-1'), delimiter='\t'):
        if r['Vnum'].isdigit():
            rows[int(r['Vnum'])] = r
    lines, client = [], []
    for v in sorted(D.MOBS):
        pl, elem, _place = D.MOBS[v]
        assert len(pl) <= 24, pl
        r = rows[v]
        assert r['Type'] in ('MONSTER', 'STONE'), (v, r['Type'])
        t = row_of(r, en.get(v) or ascii_pl(pl), pl)
        lines.append(t)
    for v in sorted(D.NPCS):
        pl = D.NPCS[v]
        assert len(pl) <= 24, pl
        folder = rows[v]['Folder'] if v in rows else ''
        lines.append(npc_row(v, en.get(v) or ascii_pl(pl), pl, folder))
    for v in sorted(D.PORTALS):
        typ, name, pl = D.PORTALS[v]
        assert len(name) <= 24 and len(pl) <= 24, (v, name, pl)
        lines.append(portal_row(v, typ, name, pl))
    for v in sorted(D.ZONE_MARKS):      # the ground zones' marker (server-patches/strefy): no name shown, no click
        t = list(npc_row(v, D.ZONE_MARKS[v], '', ''))
        t[14] = 0
        lines.append(tuple(t))
    vn = [t[0] for t in lines]
    assert len(vn) == len(set(vn))
    for t in lines:
        assert len(t) == len(COLS), (t[0], len(t))
        client.append([x for x in t])
    with open(SQL_OUT, 'w', encoding='utf-8', newline='\n') as f:
        f.write(HEADER % dict(n=len(lines), mobs=len(D.MOBS), npcs=len(D.NPCS), portals=len(D.PORTALS),
                            marks=len(D.ZONE_MARKS)))
        f.write('INSERT IGNORE INTO world.mob_proto (%s) VALUES\n' % ','.join('`%s`' % c for c in COLS))
        f.write(',\n'.join('(%s)' % ','.join(str(x) for x in t) for t in lines) + ';\n')
    # the elements, by bits
    by = {}
    for v, (pl, elem, _p) in D.MOBS.items():
        if elem:
            by.setdefault(elem, []).append(v)
    L = [ZHEAD]
    for elem in sorted(by):
        names = '+'.join(D.ELEMENT_NAME[b] for b in sorted(D.ELEMENT_NAME) if elem & b)
        L.append('-- %s: %s' % (names, ','.join(str(v) for v in sorted(by[elem]))))
        L.append('UPDATE world.mob_proto SET setRaceFlag = ((setRaceFlag + 0) & ~%d) | %d WHERE vnum IN (%s);'
                 % (D.ELEMENT_BITS, elem, ','.join(str(v) for v in sorted(by[elem]))))
    none = sorted(v for v, (pl, elem, _p) in D.MOBS.items() if not elem)
    L.append('-- no element (Metins, the Glebie eggs and crystal, Stroz Zywiolow - the wiki gives none): %s'
             % ','.join(str(v) for v in none))
    L.append('UPDATE world.mob_proto SET setRaceFlag = (setRaceFlag + 0) & ~%d WHERE vnum IN (%s) AND '
             '(setRaceFlag + 0) & %d <> 0;' % (D.ELEMENT_BITS, ','.join(str(v) for v in none), D.ELEMENT_BITS))
    with open(ZYW_OUT, 'w', encoding='utf-8', newline='\n') as f:
        f.write('\n'.join(L) + '\n')
    elements = dict((str(v), e) for v, (pl, e, _p) in D.MOBS.items())
    with open(JSON_OUT, 'w', encoding='utf-8', newline='\n') as f:
        json.dump(dict(cols=list(COLS), rows=client, elements=elements,
                       npclist_add=dict((str(k), v) for k, v in D.NPCLIST_ADD.items())), f, ensure_ascii=False,
                  indent=0)
        f.write('\n')
    print('mob_proto rows: %d (monsters/Metins %d, NPCs %d, portals %d); elements: %d vnums' % (
        len(lines), len(D.MOBS), len(D.NPCS), len(D.PORTALS), sum(len(x) for x in by.values())))


HEADER = """-- MT2009_PLUS_YOHARA_MAPS3_V1: the third batch of Yohara places (the owner, 14 October 2026) - Zejscie (394) and Glebie
-- (395) Polnocnego Wiatru, 1. poziom Swiatyni Wezy (390) and Swiatynia Wezy (391), Tajemnicza Instancja (396), Krolestwo
-- Zywiolow (378-381). GENERATED by tools/yohara_maps3/gen_ymaps3_sql.py - do not edit, rerun it. Every start
-- (apply.sh), idempotent: INSERT IGNORE - a row the operator changed is kept. Every vnum was free in our world (a
-- throwaway world after the whole apply.sh, 14 October 2026). %(n)d rows: %(mobs)d monsters, bosses and Metins, %(npcs)d
-- NPCs, %(portals)d portals, %(marks)d ground-zone marker (3975, server-patches/strefy).
-- Monsters: Owsap v6.2.6 db/mob_proto.txt (the official vnums) in our r40250 columns as tools/yohara_maps does it
-- (levels 115-135, HP, damage, defence as they are; exp 0 on the Sung Ma places - champion exp from
-- sungma_mob_exp.txt; the elemental realm's monsters keep Owsap's exp: no Sung Ma there); drop_item 0 (the drops:
-- game/yohara_maps3/mob_drop_item.yohara_maps3.txt); the elements: yohara_maps3_zywioly.sql (after zywioly_moby.sql).
-- Names: Owsap's Polish client (the official translation; 24 characters - "(lod, blyskawice)" does not fit, the
-- official client has none either). NPCs on our NPC numbers (Owsap's rows lack a column). Portals: the official
-- names "<place> x y" - WARP (3) global coordinates / 100, GOTO (9) the map's own (char.cpp FuncCheckWarp);
-- Owsap's 10109 (Turnioblysk) is our Przelecz, so it is 10125 here.
SET NAMES utf8mb4;

"""

ZHEAD = """-- MT2009_PLUS_YOHARA_MAPS3_V1: the elements of the third batch of Yohara places (setRaceFlag bits 11-16: 2048
-- lightning, 4096 fire, 8192 ice, 16384 wind, 32768 earth, 65536 dark) as on the pl-wiki ("Zywiol" of each monster;
-- Owsap's Att* columns agree but for Alastor (silny) 6791: wiki lightning, Owsap ice - the wiki wins). GENERATED by
-- tools/yohara_maps3/gen_ymaps3_sql.py. apply.sh runs it AFTER zywioly_moby.sql, which clears bits 11-16 of every
-- mob it does not list: idempotent, the end state is these bits on every start.
SET NAMES utf8mb4;"""

if __name__ == '__main__':
    main()
