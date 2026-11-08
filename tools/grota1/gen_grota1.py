#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""gen_grota1.py

Grota Wygnancow V1 (map 72, metin2_map_skipia_dungeon_01, 6x6, base 0 1203200, levels 81-89; one floor).

MT2009_PLUS_GROTA_THIN_V1 (8 November 2026): the owner, "Grota Wygnancow V1 i V2 - zmniejszyc spoty o 30% od tego co
jest teraz". V1's regen.txt was the package's (833 lines "r ... 80s", group_group 2401-2409, nothing of ours); the
map's regen.txt is now this file's output: the package's lines less 30% (tools/grota2/grota_thin.py - evenly, every
64 m square of the map its share, the most crowded lines first), every line kept as the package wrote it. The Ice
Witch (1192, boss.txt) and npc.txt untouched.

What this writes (GENERATED - edit this file, run it again; plain python3, no server_attr needed):
  linux-port/docker/game/grota1/regen.txt      - the map's regen.txt (Dockerfile step MT2009_PLUS_GROTA_THIN_V1)
  linux-port/docker/game/grota1/gen_report.txt - the counts and the bots' hubs (playerbot_wandering.h grottoV1Hubs)
"""
import collections
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.normpath(os.path.join(HERE, '..', '..'))
sys.path.insert(0, os.path.join(ROOT, 'tools', 'grota2'))
import grota_thin  # noqa: E402

OUT = os.path.join(ROOT, 'linux-port', 'docker', 'game', 'grota1')
MAP = 'metin2_map_skipia_dungeon_01'
SHARE = '/opt/metin2/mt2009plustest/linux-port/docker/game/src/serverfiles/share/locale/poland/'
PKG_LINES = 833
BASE_X, BASE_Y = 0, 1203200
REACH = 25
# playerbot_wandering.h grottoV1Hubs (x, y) - a bot's hunting hubs; each must keep lines round it
HUBS = [(22600, 1238000), (125600, 1295100), (34800, 1237800), (87600, 1258100), (9200, 1240000),
        (35000, 1212400), (61000, 1213000), (22900, 1219600), (53300, 1224600), (53500, 1341600),
        (92600, 1269100), (105900, 1213100), (123200, 1269300), (130900, 1309000), (23600, 1276500),
        (36900, 1225400), (103800, 1276400), (104400, 1295800), (124900, 1251400), (124100, 1333900),
        (28700, 1323000), (46400, 1310000), (60800, 1281800), (68200, 1308400), (140400, 1323600)]


def main():
    raw = open(os.path.join(SHARE, 'map', MAP, 'regen.txt'), encoding='latin-1').read().replace('\r', '').split('\n')
    pts = []
    for l in raw:
        f = l.split('\t')
        if f[0] == 'r':
            pts.append([int(f[1]), int(f[2]), int(f[3]), int(f[4]), int(f[10]), l])
    assert len(pts) == PKG_LINES, len(pts)
    kept, out = grota_thin.thin(pts)
    keep_ids = set(id(p) for p in kept)
    os.makedirs(OUT, exist_ok=True)
    with open(os.path.join(OUT, 'regen.txt'), 'w', newline='\r\n') as f:
        f.write('//MT2009_PLUS_GROTA_THIN_V1 (tools/grota1/gen_grota1.py, GENERATED): the package %d lines -> %d\n' % (
            len(pts), len(kept)))
        for p in pts:                      # the package's order, its lines as they were
            if id(p) in keep_ids:
                f.write(p[5] + '\n')
    rep = []
    rep.append('MT2009_PLUS_GROTA_THIN_V1 - Grota Wygnancow V1 (72, %s)' % MAP)
    rep.append('package: %d lines %s' % (len(pts), dict(sorted(collections.Counter(p[4] for p in pts).items()))))
    rep.append('final:   %d lines %s (%d out, %.1f%%)' % (
        len(kept), dict(sorted(collections.Counter(p[4] for p in kept).items())), len(out), 100.0 * len(out) / len(pts)))
    q = [(0, 768, 0, 768), (768, 1536, 0, 768), (0, 768, 768, 1536), (768, 1536, 768, 1536)]
    rep.append('quarters (x0-x1/y0-y1: before -> after): ' + ', '.join(
        '%d-%d/%d-%d: %d -> %d' % (a, b, c, d, sum(1 for p in pts if a <= p[0] < b and c <= p[1] < d),
                                   sum(1 for p in kept if a <= p[0] < b and c <= p[1] < d)) for a, b, c, d in q))
    rep.append('')
    rep.append('bots (grottoV1Hubs): lines within %d m straight, before -> after' % REACH)
    for hx, hy in HUBS:
        x, y = (hx - BASE_X) // 100, (hy - BASE_Y) // 100
        a, b = grota_thin.near(pts, x, y, REACH), grota_thin.near(kept, x, y, REACH)
        assert b > 0, (hx, hy)
        rep.append('  %7d %7d: %3d -> %3d' % (hx, hy, a, b))
    with open(os.path.join(OUT, 'gen_report.txt'), 'w') as f:
        f.write('\n'.join(rep) + '\n')
    print('\n'.join(rep))


if __name__ == '__main__':
    main()
