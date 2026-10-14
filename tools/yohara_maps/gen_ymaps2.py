#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""gen_ymaps2.py [--attr DIR] [--ameria DIR] [--check]

MT2009_PLUS_YOHARA_MAPS2_V1: the second batch of Yohara maps (the owner, 14 October 2026, cache/yohara/decyzje.md
"14.10"; plan cache/yohara/plan-mapy-yohary.md) - every server file of them, from the official data we have:

  376 Seoganland                    metin2_map_eastplain_02       3x6  Owsap v6.2.6's spawns + the wiki's rest
  377 Namgan                        metin2_map_eastplain_03       4x2  Owsap's spawns + the wiki's rest (GF positions)
  385 Przelecz Yilad                metin2_map_snakevalley        6x3  Ameria's spawns, the wiki's monsters/Metins
  388 Wawoz Polnocnego Wiatru       metin2_map_icecrystalcave     5x4  placed here (see below)
  393 Schronienie Polnocnego Wiatru metin2_map_whitedragoncave_01 6x6  Owsap's spawns

The official folder of Wawoz Polnocnego Wiatru (Northwind Canyon) is metin2_map_icecrystalcave, NOT
metin2_map_whitdragonvalley: the GF 26.1.11 client's npc_location_helper.txt names 388 icecrystalcave with the
Korean name of Owsap's portal 10139 "WawozPlnW." (whose target, 1106 15997, lies in icecrystalcave's square), its
map_mob_list.txt puts the wiki's Wawoz monsters (Zamarzniety Lis .. Wodz Wojenny 6770-6776/6882-6888, Metin Shiho
8066, Metin z Gumar 8077) on 388 at positions up to 1077,905 - outside a 3x3 map - and whitdragonvalley carries the
NPCs of the wiki's Rozpadlina Dusz (Straznik Rozpad. Dusz 20806, General Kohan 20808, Lowca Glow (Roz.Pln.W.) 20846)
and its monsters (389: the deer, leopards, yetis 6777-6783). Rozpadlina Dusz is not part of this batch (the owner).

Writes (all GENERATED - edit this file, run it again):
  linux-port/docker/game/yohara_maps2/map/<folder>/{Setting,Town,regen,boss,stone,npc}.txt (+ server_attr from --attr)
  linux-port/docker/game/yohara_maps2/group.yohara_maps2.txt, group_group.yohara_maps2.txt
  linux-port/docker/game/yohara_maps2/dongan_npc.yohara_maps2.txt   (the portal to Seoganland on Dongan, 373)
  linux-port/docker/mariadb/playerbot/yohara_maps2.sql               (world.mob_proto, INSERT IGNORE)
  linux-port/docker/game/yohara_maps2/README.md                       (what came from where; the spawn method)

server_attr: the GF client's attr.atr (tools/gf28 srvattr.py: grid_from_client + write_server, needs python-lzo -
the m2pack-lzo image), made once into --attr:
  docker run --rm -v /opt/metin2:/opt/metin2 m2pack-lzo python3 tools/yohara_maps/gen_ymaps2.py --attr-only OUT
The walkability this script checks every spawn against is read from the same attr.atr files (no lzo needed).

Example: python3 tools/yohara_maps/gen_ymaps2.py --attr /path/to/attr --ameria /path/to/ameria/map
"""
import argparse
import collections
import csv
import math
import os
import random
import re
import shutil
import struct
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(os.path.dirname(HERE))
sys.path.insert(0, HERE)
import gen_ymaps_sql as m1  # noqa: E402  (the first batch's row writers and columns)

GF = '/opt/metin2/cache/gf/Gameforge_26.1.11/_client'
OWSAP = '/opt/metin2/cache/owsap/Server/Server'
OUT = os.path.join(REPO, 'linux-port', 'docker', 'game', 'yohara_maps2')
SQL_OUT = os.path.join(REPO, 'linux-port', 'docker', 'mariadb', 'playerbot', 'yohara_maps2.sql')
DEF_AMERIA = '/tmp/claude-0/-root/9f475014-d1bc-4cf4-a3e1-da3c380fc52c/scratchpad/ymaps2/home/srv1/share/locale/germany/map'

MAPS = collections.OrderedDict([
    (376, dict(folder='metin2_map_eastplain_02', name='Seoganland', size=(3, 6), base=(1152000, 435200))),
    (377, dict(folder='metin2_map_eastplain_03', name='Namgan', size=(4, 2), base=(1228800, 435200))),
    (385, dict(folder='metin2_map_snakevalley', name='Przełęcz Yilad', size=(6, 3), base=(0, 1408000))),
    (388, dict(folder='metin2_map_icecrystalcave', name='Wąwóz Północnego Wiatru', size=(5, 4), base=(0, 1510400))),
    (393, dict(folder='metin2_map_whitedragoncave_01', name='Schronienie Północnego Wiatru', size=(6, 6),
               base=(998400, 1203200))),
])
DONGAN = dict(folder='metin2_map_eastplain_01', size=(4, 5), base=(1049600, 435200))

# -- the monsters' Polish names (pl-wiki; 24 bytes of cp1250 at most). The wiki's element in brackets where both
#    variants of a monster fit, else the official in-game name (Owsap's Polish client) for both.
NAMES = {
    # Seoganland (ziemia) / Namgan (wiatr) - Owsap Att*: 6718-6724 earth, 6725-6731 wind
    6718: 'Myr Kovix (ziemia)', 6719: 'Myr Proletariusz', 6720: 'Myr Golem (ziemia)',
    6721: 'Myr Bojownik (ziemia)', 6722: 'Myr Czarodziej (ziemia)', 6723: 'Myr Weteran (ziemia)',
    6724: 'Myr Prymus (ziemia)',
    6725: 'Myr Kovix (wiatr)', 6726: 'Myr Proletariusz', 6727: 'Myr Golem (wiatr)',
    6728: 'Myr Bojownik (wiatr)', 6729: 'Myr Czarodziej (wiatr)', 6730: 'Myr Weteran (wiatr)',
    6731: 'Myr Prymus (wiatr)',
    # Przelecz Yilad - 6758-6764 dark, 6875-6881 earth
    6758: 'Skażony Żołnierz', 6759: 'Skażony Zadziora', 6760: 'Skażony Wojownik', 6761: 'Skażony Mnich',
    6762: 'Skażony Generał', 6763: 'Skażony Wódz', 6764: 'Skażony Wódz Wojenny',
    6875: 'Skażony Żołnierz', 6876: 'Skażony Zadziora', 6877: 'Skażony Wojownik', 6878: 'Skażony Mnich',
    6879: 'Skażony Generał', 6880: 'Skażony Wódz', 6881: 'Skażony Wódz Wojenny',
    # Wawoz Polnocnego Wiatru - 6770-6776 ice, 6882-6888 lightning (the wiki: "Zamarzniety Lis (blyskawice)" for
    # Owsap's 6882 "Bezduszny Lis")
    6770: 'Zamarznięty Lis', 6771: 'Zamarznięty Zwiadowca', 6772: 'Zamarznięty Wojownik',
    6773: 'Zamarznięty Łowca', 6774: 'Zamarznięty Generał', 6775: 'Zamarznięty Wódz',
    6776: 'Zamarznięty Wódz Wojenny',
    6882: 'Zamarznięty Lis', 6883: 'Zamarznięty Zwiadowca', 6884: 'Zamarznięty Wojownik',
    6885: 'Zamarznięty Łowca', 6886: 'Zamarznięty Generał', 6887: 'Zamarznięty Wódz',
    6888: 'Zamarznięty Wódz Wojenny',
    # Schronienie Polnocnego Wiatru - 6784-6789 ice
    6784: 'Żołnierz Schron. Płn. W.', 6785: 'Zadziora Schron. Płn. W.', 6786: 'Wojownik Schron. Płn. W.',
    6787: 'Czarownik Sch. Płn. W.', 6788: 'Generał Schron. Płn. W.', 6789: 'Wódz Wojenny Schronienia',
    # Metins
    8063: 'Metin Szacunku', 8064: 'Metin Uważności', 8065: 'Metin Jin', 8066: 'Metin Shiho', 8077: 'Metin z Gumar',
    8626: '1. Posterunek Myr', 8627: '2. Posterunek Myr',
}
# the elements (Owsap's Att* = the pl-wiki's "Zywiol"): tools/zywioly rule h (YOHARA_ELEMENTS2)
ELEMENT_OF = {}
for _v in range(6718, 6725):
    ELEMENT_OF[_v] = 'ziemia'
for _v in range(6725, 6732):
    ELEMENT_OF[_v] = 'wiatr'
for _v in range(6758, 6765):
    ELEMENT_OF[_v] = 'mrok'
for _v in range(6875, 6882):
    ELEMENT_OF[_v] = 'ziemia'
for _v in list(range(6770, 6777)) + list(range(6784, 6790)):
    ELEMENT_OF[_v] = 'lod'
for _v in range(6882, 6889):
    ELEMENT_OF[_v] = 'blyskawica'

# NPCs: our own NPC numbers (gen_ymaps_sql.npc_row); the veins as our Zyla Krysztalu Duszy (30301)
NPCS = {
    20804: 'Strażnik Węży', 20805: 'Strażnik Płn. Wiatru', 20814: 'Zagubiony Zwiadowca',
    20841: 'Łowca Głów', 20844: 'Statua Węży', 20845: 'Łowca Głów (Wąw.Płn.W.)', 20847: 'Łowca Głów (Schron.)',
    20850: 'Tajemniczy Ołtarz', 20851: 'Łowca Głów (Seoganland)', 20852: 'Łowca Głów (Namgan)',
    30310: 'Żyła Jadeitu Słońca', 30311: 'Żyła Jadeitu Nocy', 30312: 'Żyła Jadeitu Dymu',
    30313: 'Żyła Jadeitu Mgły',
}
VEINS = (30310, 30311, 30312, 30313)

# the portals (type WARP: "<name> <x> <y>", x/y = the global position / 100). Owsap's 10127-10140 with their
# official targets; 10139 is an NPC in Owsap (a quest gate) - a portal here; 10145/10146 are ours: Wawoz <->
# Schronienie stand in for the way through Rozpadlina Dusz (not here yet) - the wiki: Wawoz -> Rozpadlina ->
# Schronienie. Every name ASCII (the engine reads the target from the name).
WARPS = collections.OrderedDict([
    (10127, 'Dongan 10551 4881'),           # Seoganland -> Dongan (55,529)
    (10128, 'Seoganland 12218 4895'),       # Dongan -> Seoganland (698,543)
    (10129, 'Namgan 12780 4411'),           # Seoganland -> Namgan (492,59)
    (10130, 'Seoganland 12144 5555'),       # Namgan -> Seoganland (624,1203)
    (10136, 'PrzeleczYilad 303 14147'),     # Namgan -> Przelecz Yilad (303,67)
    (10137, 'Namgan 13184 4735'),           # Przelecz Yilad -> Namgan (896,383)
    (10139, 'WawozPlnW 1106 15997'),        # Przelecz Yilad -> Wawoz (1106,893)
    (10140, 'PrzeleczYilad 83 14763'),      # Wawoz -> Przelecz Yilad (83,683)
    (10145, None),                          # Wawoz -> Schronienie (filled in main: its Town)
    (10146, None),                          # Schronienie -> Wawoz (filled in main)
])

# -- groups ---------------------------------------------------------------------------------------------------
# Owsap's (copied, the official numbers; none is ours - the Dockerfile step checks): Seoganland 6185-6192 /
# group_group 6706-6710, Namgan 6711-6715 / 6715-6719, Schronienie 9150-9157 / 4030-4033.
OWSAP_GROUPS = list(range(6185, 6193)) + list(range(6711, 6716)) + list(range(9150, 9158))
OWSAP_GGROUPS = list(range(6706, 6711)) + list(range(6715, 6720)) + list(range(4030, 4034))
# ours for Wawoz (Owsap has no group of these monsters): four monsters a group, as Owsap's Seoganland
OUR_GROUPS = collections.OrderedDict([
    (9170, ('Wawoz_lod_01', [6770, 6770, 6771, 6771])),
    (9171, ('Wawoz_lod_02', [6772, 6772, 6773, 6771])),
    (9172, ('Wawoz_lod_03', [6773, 6774, 6772, 6770])),
    (9173, ('Wawoz_blysk_01', [6882, 6882, 6883, 6883])),
    (9174, ('Wawoz_blysk_02', [6884, 6884, 6885, 6883])),
    (9175, ('Wawoz_blysk_03', [6885, 6886, 6884, 6882])),
])
OUR_GGROUPS = collections.OrderedDict([
    (4040, ('wawoz_lod', [(9170, 1), (9171, 1), (9172, 1)])),
    (4041, ('wawoz_blysk', [(9173, 1), (9174, 1), (9175, 1)])),
])
GG_DONGAN = list(range(6700, 6706))       # the first batch's (Dongan's trolls, hounds, Dreczony Duch)


def ascii_pl(s):
    return s.translate(str.maketrans('ąćęłńóśźżĄĆĘŁŃÓŚŹŻ', 'acelnoszzACELNOSZZ'))


# -- the terrain --------------------------------------------------------------------------------------------------
class Grid:
    """The GF client's attr.atr of a map: one byte a metre (bit 0 block, bit 1 water)."""

    def __init__(self, folder, size):
        w, h = size
        self.W, self.H = w * 256, h * 256
        self.a = bytearray(self.W * self.H)
        for cy in range(h):
            for cx in range(w):
                b = open(os.path.join(GF, folder, '%03d%03d' % (cx, cy), 'attr.atr'), 'rb').read()
                assert struct.unpack_from('<3H', b, 0)[1:] == (256, 256), (folder, cx, cy)
                d = b[6:]
                for y in range(256):
                    o = (cy * 256 + y) * self.W + cx * 256
                    self.a[o:o + 256] = d[y * 256:(y + 1) * 256]

    def free(self, x, y):
        return 0 <= x < self.W and 0 <= y < self.H and not (self.a[y * self.W + x] & 3)

    def nearest_free(self, x, y, maxr=25):
        if self.free(x, y):
            return x, y
        for r in range(1, maxr + 1):
            best = None
            for dx in range(-r, r + 1):
                for dy in (-r, r) if abs(dx) != r else range(-r, r + 1):
                    if self.free(x + dx, y + dy):
                        d = dx * dx + dy * dy
                        if best is None or d < best[0]:
                            best = (d, x + dx, y + dy)
            if best:
                return best[1], best[2]
        return None

    def reach(self, seeds):
        """Every free metre connected (4-way) to the seeds."""
        W = self.W
        seen = bytearray(len(self.a))
        dq = collections.deque()
        for x, y in seeds:
            if self.free(x, y):
                seen[y * W + x] = 1
                dq.append(y * W + x)
        a = self.a
        while dq:
            i = dq.popleft()
            x, y = i % W, i // W
            for j, ok in ((i - 1, x > 0), (i + 1, x < W - 1), (i - W, y > 0), (i + W, y < self.H - 1)):
                if ok and not seen[j] and not (a[j] & 3):
                    seen[j] = 1
                    dq.append(j)
        return seen


def spawn_line(kind, x, y, r, t, vnum, count=1, direction=0):
    return '%s\t%d\t%d\t%d\t%d\t0\t%d\t%s\t100\t%d\t%d' % (kind, x, y, r, r, direction, t, count, vnum)


def read_lines(path):
    out = []
    for l in open(path, encoding='latin-1'):
        l = l.rstrip('\r\n')
        t = l.split()
        if len(t) >= 11 and t[0] in ('m', 'g', 'r', 's') and not l.startswith('//'):
            out.append(t)
    return out


def fmt(t):
    return '\t'.join(t)


def nudged(grid, lines, what, rep, maxr=25):
    """Owsap's lines with every centre on free ground of the GF terrain (a blocked one moved to the nearest free m)."""
    out, moved = [], 0
    for t in lines:
        p = grid.nearest_free(int(t[1]), int(t[2]), maxr)
        if p is None:
            rep('  %s at %s,%s (%s): no free GF ground within %d m - left out' % (what, t[1], t[2], t[10], maxr))
            continue
        if p != (int(t[1]), int(t[2])):
            moved += 1
            t = list(t)
            t[1], t[2] = str(p[0]), str(p[1])
        out.append(fmt(t))
    if moved:
        rep('  %s: %d of Owsap\'s %d centres on blocked GF ground moved to the nearest free metre' % (what, moved, len(out)))
    return out


def gf_hints():
    """map index -> vnum -> [(x, y)] - GF's npc_location_helper map_mob_list (official spawn positions)."""
    out = collections.defaultdict(dict)
    for l in open(os.path.join(GF, 'shared/common/map/npc_location_helper/map_mob_list.txt'), encoding='latin-1'):
        t = l.split()
        if len(t) >= 3 and t[0].isdigit() and t[1].isdigit():
            pts = [tuple(int(v) for v in p.split(',')) for p in t[2:] if ',' in p]
            out[int(t[0])][int(t[1])] = pts
    return out


class Report:
    def __init__(self):
        self.lines = []

    def __call__(self, s):
        self.lines.append(s)
        print(s)


def check_free(grid, x, y, what, rep, maxr=25):
    p = grid.nearest_free(x, y, maxr)
    if p is None:
        raise SystemExit('%s at %d,%d: no free cell within %d m' % (what, x, y, maxr))
    if p != (x, y):
        rep('  %s: %d,%d is blocked -> %d,%d' % (what, x, y, p[0], p[1]))
    return p


# -- per map -------------------------------------------------------------------------------------------------------
def owsap_map(folder):
    return os.path.join(OWSAP, 'share/locale/uk/map', folder)


def veins(grid, reach, rng, kinds, n, avoid, rep):
    """n veins of the wiki's kinds at random reachable spots ("losowo" - the wiki), 40 m apart."""
    W = grid.W
    cells = [i for i in range(len(reach)) if reach[i]]
    rng.shuffle(cells)
    pts = []
    for i in cells:
        x, y = i % W, i // W
        if all((x - a) ** 2 + (y - b) ** 2 > 60 ** 2 for a, b in pts + avoid):
            pts.append((x, y))
            if len(pts) == n:
                break
    out = []
    for k, (x, y) in enumerate(pts):
        out.append(spawn_line('m', x, y, 30, '600s', kinds[k % len(kinds)]))
    rep('  veins: %d (%s), range 30, 600 s' % (len(out), ', '.join(NPCS[v] for v in kinds)))
    return out


def poisson(grid, reach, rng, target, avoid, keep_off=30):
    W = grid.W
    cells = [i for i in range(len(reach)) if reach[i]]
    area = len(cells)
    d = math.sqrt(area / float(target)) * 0.95
    for _ in range(12):
        rng2 = random.Random(1410)
        order = list(cells)
        rng2.shuffle(order)
        bucket = collections.defaultdict(list)
        cs = max(1, int(d))
        pts = []
        for i in order:
            x, y = i % W, i // W
            if any((x - a) ** 2 + (y - b) ** 2 < keep_off ** 2 for a, b in avoid):
                continue
            bx, by = x // cs, y // cs
            ok = True
            for gx in (bx - 1, bx, bx + 1):
                for gy in (by - 1, by, by + 1):
                    for a, b in bucket.get((gx, gy), ()):
                        if (x - a) ** 2 + (y - b) ** 2 < d * d:
                            ok = False
                            break
                    if not ok:
                        break
                if not ok:
                    break
            if ok:
                pts.append((x, y))
                bucket[(bx, by)].append((x, y))
        if abs(len(pts) - target) <= max(5, target // 40):
            return pts, d
        d *= math.sqrt(len(pts) / float(target))
    return pts, d


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--attr', help='a directory with the server_attr files (named by folder)')
    ap.add_argument('--attr-only', help='write the server_attr files into this directory and stop (python-lzo)')
    ap.add_argument('--ameria', default=DEF_AMERIA, help="Ameria's share/locale/germany/map")
    a = ap.parse_args()
    if a.attr_only:
        sys.path.insert(0, '/opt/metin2/cache/tcm/gf28/attr')
        import srvattr  # noqa: E402
        for idx, M in MAPS.items():
            W, H, g = srvattr.grid_from_client(os.path.join(GF, M['folder']), *M['size'])
            srvattr.write_server(os.path.join(a.attr_only, M['folder']), W, H, g)
        return
    rep = Report()
    rng = random.Random(14102026)
    hints = gf_hints()
    files = {}          # folder -> name -> list of lines
    used = set()        # every vnum spawned (for the SQL and the client)

    def put(folder, name, lines):
        files.setdefault(folder, {})[name] = lines

    # ---------------------------------------------------------------- Seoganland (376)
    M = MAPS[376]
    f, o = M['folder'], owsap_map(MAPS[376]['folder'])
    g = Grid(f, M['size'])
    rep('376 Seoganland (%s)' % f)
    regen = nudged(g, read_lines(os.path.join(o, 'regen.txt')), 'regen', rep)
    boss = nudged(g, read_lines(os.path.join(o, 'boss.txt')), 'boss', rep)
    # the wiki's Myr Weteran (ziemia) boss: Owsap spawns none - at GF's position of 6723 farthest from Prymus
    x, y = check_free(g, 400, 1100, 'Myr Weteran (ziemia)', rep)
    boss.append(spawn_line('m', x, y, 30, '3600s', 6723))
    stone = nudged(g, read_lines(os.path.join(o, 'stone.txt')), 'stone', rep)
    npc = []
    for t in read_lines(os.path.join(o, 'npc.txt')):
        if int(t[10]) == 4020:      # Wieza Sung Mahi (dungeon) - not here yet
            rep('  npc: 4020 Wieza Sung Mahi left out (the dungeon is not here)')
            continue
        npc.append(fmt(t))
    x, y = check_free(g, 700, 521, 'Lowca Glow (Seoganland)', rep)
    npc.append(spawn_line('m', x, y, 0, '1m', 20851, direction=1))
    reach = g.reach([(713, 565)])
    regen += veins(g, reach, rng, VEINS, 8, [(713, 565), (721, 573), (605, 1220)], rep)
    put(f, 'regen.txt', regen)
    put(f, 'boss.txt', boss)
    put(f, 'stone.txt', stone)
    put(f, 'npc.txt', npc)
    seog_density = sum(1 for l in regen if l.startswith('r')) / float(sum(reach))
    rep('  Owsap regen: %d group lines on %d reachable m2 -> %.6f a m2' % (
        sum(1 for l in regen if l.startswith('r')), sum(reach), seog_density))

    # ---------------------------------------------------------------- Namgan (377)
    M = MAPS[377]
    f, o = M['folder'], owsap_map(M['folder'])
    g = Grid(f, M['size'])
    rep('377 Namgan (%s)' % f)
    regen = nudged(g, read_lines(os.path.join(o, 'regen.txt')), 'regen', rep)
    # the wiki's monsters Owsap does not spawn here (GF's positions of 377): Dongan's trolls / hounds / Dreczony
    # Duch (their group_groups 6700-6705) and Seoganland's Myr (ziemia) (6706-6710)
    h = hints[377]
    troll_pts = sorted(set(p for v in (6700, 6701, 6702, 6703, 6704, 6705, 6710, 6711, 6712, 6713, 6714)
                           for p in h.get(v, [])))
    myr_pts = sorted(set(p for v in (6718, 6719, 6720, 6722) for p in h.get(v, [])))
    added = 0
    for k, (x, y) in enumerate(troll_pts):
        p = check_free(g, x, y, 'troll spawn', rep)
        if any(abs(p[0] - q[0]) < 8 and abs(p[1] - q[1]) < 8 for q in troll_pts[:k]):
            continue
        regen.append(spawn_line('r', p[0], p[1], 10, '10s', GG_DONGAN[k % len(GG_DONGAN)]))
        added += 1
    for k, (x, y) in enumerate(myr_pts):
        p = check_free(g, x, y, 'Myr (ziemia) spawn', rep)
        regen.append(spawn_line('r', p[0], p[1], 10, '10s', 6706 + k % 5))
        added += 1
    rep('  + %d group lines at GF positions (trolls/hounds/Dreczony Duch: Dongan groups; Myr (ziemia))' % added)
    boss = nudged(g, read_lines(os.path.join(o, 'boss.txt')), 'boss', rep)
    for v, pts in ((6730, [(170, 350), (600, 230)]), (6705, [(928, 150)])):
        for x, y in pts:
            x, y = check_free(g, x, y, NAMES.get(v, str(v)), rep)
            boss.append(spawn_line('m', x, y, 20, '3600s', v))
    stone = nudged(g, read_lines(os.path.join(o, 'stone.txt')), 'stone', rep)
    for v, pts in ((8067, [(700, 250)]), (8064, [(170, 360), (155, 98)]), (8063, [(470, 150)]), (8065, [(200, 350)])):
        for x, y in pts:
            x, y = check_free(g, x, y, 'Metin %d' % v, rep)
            stone.append(spawn_line('m', x, y, 30, '1800s', v))
    npc = nudged(g, read_lines(os.path.join(o, 'npc.txt')), 'npc', rep)
    reach = g.reach([(508, 57)])
    regen += veins(g, reach, rng, VEINS, 8, [(508, 57), (513, 55), (921, 383), (960, 242)], rep)
    put(f, 'regen.txt', regen)
    put(f, 'boss.txt', boss)
    put(f, 'stone.txt', stone)
    put(f, 'npc.txt', npc)

    # ---------------------------------------------------------------- Przelecz Yilad (385)
    M = MAPS[385]
    f = M['folder']
    am = os.path.join(a.ameria, f)
    g = Grid(f, M['size'])
    rep('385 Przelecz Yilad (%s) - Ameria' % f)
    # Ameria's single monsters (30 s), the element alternating line by line (the wiki: every monster in both,
    # mrok 6758-6764 / ziemia 6875-6881); Ameria spawns no Skazony Wojownik: GF's positions of 6760 carry six each
    pair = {6758: 6875, 6759: 6876, 6760: 6877, 6761: 6878, 6762: 6879}
    regen = []
    k = 0
    for t in read_lines(os.path.join(am, 'regen.txt')):
        v = int(t[10])
        assert v in pair, t
        x, y = check_free(g, int(t[1]), int(t[2]), 'Yilad regen', rep, maxr=40)
        t[1], t[2] = str(x), str(y)
        t[10] = str(v if k % 2 == 0 else pair[v])
        regen.append(fmt(t))
        k += 1
    for j, (x, y) in enumerate(hints[385].get(6760, [])):
        for n in range(6):
            p = check_free(g, x + (n % 3 - 1) * 8, y + (n // 3) * 8 - 4, 'Skazony Wojownik', rep, maxr=40)
            regen.append(spawn_line('m', p[0], p[1], 10, '30s', 6760 if (j + n) % 2 == 0 else 6877, direction=1))
    rep('  regen: %d monsters (Ameria %d + Skazony Wojownik %d)' % (len(regen), k, len(regen) - k))
    # bosses: Ameria's 11 hourly spots, the wiki's four bosses over them
    boss = []
    order = [6763, 6880, 6764, 6763, 6881, 6880, 6763, 6764, 6880, 6763, 6881]
    for j, t in enumerate(read_lines(os.path.join(am, 'boss.txt'))):
        x, y = check_free(g, int(t[1]), int(t[2]), 'Yilad boss', rep)
        boss.append(spawn_line('m', x, y, 10, '3600s', order[j % len(order)]))
    rep('  bosses: %d (Skazony Wodz / Wodz Wojenny, mrok and ziemia) on Ameria\'s spots, 1 h' % len(boss))
    # Metins: Ameria's three rings of 11 (10 s, a farm) - two spots of each ring (its first and the one farthest from
    # it), six in all, every 30 min (the owner, 14 October: "Yilad: 6 Metinow co 30 min"); the wiki's three Metins by
    # GF's positions: the east ring Shiho (8066 at 1120,470), the middle Jin (8065 at 920,300), the west Uwaznosci
    stone = []
    rings = collections.defaultdict(list)
    for t in read_lines(os.path.join(am, 'stone.txt')):
        x = int(t[1])
        rings[8066 if x > 1050 else 8064 if x < 400 else 8065].append((x, int(t[2])))
    for v, pts in sorted(rings.items()):
        far = max(pts, key=lambda p: (p[0] - pts[0][0]) ** 2 + (p[1] - pts[0][1]) ** 2)
        for x, y in (pts[0], far):
            x, y = check_free(g, x, y, 'Yilad Metin', rep)
            stone.append(spawn_line('m', x, y, 10, '1800s', v))
    rep('  Metins: %d (of Ameria\'s %d spots: two a ring), 30 min' % (
        len(stone), sum(len(p) for p in rings.values())))
    npc = []
    for t in read_lines(os.path.join(am, 'npc.txt')):
        x, y = check_free(g, int(t[1]), int(t[2]), 'Yilad NPC %s' % t[10], rep)
        npc.append(spawn_line('m', x, y, 0, '1m', int(t[10]), direction=int(t[6])))
    for v, (x, y) in ((10137, (288, 61)), (10139, (45, 690))):   # Owsap's places
        x, y = check_free(g, x, y, 'portal %d' % v, rep)
        npc.append(spawn_line('m', x, y, 0, '10s', v))
    town = (316, 68)
    reach = g.reach([town])
    regen += veins(g, reach, rng, (30311, 30313), 6, [town, (288, 61), (45, 690), (580, 110), (637, 494)], rep)
    put(f, 'regen.txt', regen)
    put(f, 'boss.txt', boss)
    put(f, 'stone.txt', stone)
    put(f, 'npc.txt', npc)

    # ---------------------------------------------------------------- Wawoz Polnocnego Wiatru (388)
    M = MAPS[388]
    f = M['folder']
    g = Grid(f, M['size'])
    rep('388 Wawoz Polnocnego Wiatru (%s) - placed here' % f)
    h = hints[388]
    arrive_yilad = (1106, 893)          # 10139's target
    p_back = check_free(g, 1140, 915, 'portal 10140 (to Yilad)', rep)
    p_shelter = check_free(g, 235, 270, 'portal 10145 (to Schronienie)', rep)
    arrive_shelter = check_free(g, 262, 300, 'arrival from Schronienie', rep)
    npcs = [(20805, check_free(g, 503, 456, 'Straznik Pln. Wiatru', rep)),
            (20845, check_free(g, 1117, 871, 'Lowca Glow (Waw.Pln.W.)', rep))]
    reach = g.reach([arrive_yilad])
    assert reach[p_shelter[1] * g.W + p_shelter[0]] and reach[arrive_shelter[1] * g.W + arrive_shelter[0]]
    avoid = [arrive_yilad, p_back, p_shelter, arrive_shelter] + [p for _, p in npcs]
    target = int(round(seog_density * sum(reach)))
    pts, d = poisson(g, reach, rng, target, avoid)
    ice_h = [p for v in range(6770, 6775) for p in h.get(v, [])]
    bl_h = [p for v in range(6882, 6887) for p in h.get(v, [])]

    def nearest(p, hs):
        return min((p[0] - q[0]) ** 2 + (p[1] - q[1]) ** 2 for q in hs)
    regen = []
    n_ice = 0
    for x, y in sorted(pts, key=lambda p: (p[1], p[0])):
        ice = nearest((x, y), ice_h) <= nearest((x, y), bl_h)
        n_ice += ice
        regen.append(spawn_line('r', x, y, 10, '10s', 4040 if ice else 4041))
    rep('  regen: %d group lines (target %d = Seoganland\'s density x %d reachable m2; %.1f m apart), %d ice / %d '
        'lightning by the nearest GF position of each kind' % (len(regen), target, sum(reach), d, n_ice,
                                                                len(regen) - n_ice))
    # bosses: GF's two positions (all four bosses), two more spots each element away from them
    boss = []
    for v, (x, y) in ((6775, (580, 750)), (6887, (850, 850)), (6776, (560, 770)), (6888, (870, 830))):
        x, y = check_free(g, x, y, 'boss %d' % v, rep)
        boss.append(spawn_line('m', x, y, 20, '3600s', v))
    far = sorted(pts, key=lambda p: -min((p[0] - q[0]) ** 2 + (p[1] - q[1]) ** 2 for q in [(580, 750), (850, 850)] +
                                         avoid))
    extra = []
    for p in far:
        if all((p[0] - q[0]) ** 2 + (p[1] - q[1]) ** 2 > 250 ** 2 for q in extra):
            extra.append(p)
        if len(extra) == 2:
            break
    for p in extra:
        ice = nearest(p, ice_h) <= nearest(p, bl_h)
        boss.append(spawn_line('m', p[0], p[1], 20, '3600s', 6775 if ice else 6887))
    rep('  bosses: %d (Zamarzniety Wodz / Wodz Wojenny, lod and blyskawice), 1 h' % len(boss))
    # Metins: GF's positions (Shiho 8066 x3, Gumar 8077 x1) and more spots to Seoganland's share (17 on 18 sectors)
    stone = []
    for v, pl in ((8066, h.get(8066, [])), (8077, h.get(8077, []))):
        for x, y in pl:
            x, y = check_free(g, x, y, 'Metin %d' % v, rep)
            stone.append(spawn_line('m', x, y, 30, '1800s', v))
    want = int(round(17 / 18.0 * 20))
    more = []
    taken = [(int(l.split('\t')[1]), int(l.split('\t')[2])) for l in stone]
    for p in far:
        if all((p[0] - q[0]) ** 2 + (p[1] - q[1]) ** 2 > 120 ** 2 for q in taken + more + avoid):
            more.append(p)
        if len(more) + len(stone) >= want:
            break
    for k, p in enumerate(more):
        stone.append(spawn_line('m', p[0], p[1], 30, '1800s', 8077 if k % 2 == 0 else 8066))
    rep('  Metins: %d (Shiho / z Gumar), 30 min' % len(stone))
    npc = [spawn_line('m', p[0], p[1], 0, '1m', v, direction=1) for v, p in npcs]
    npc.append(spawn_line('m', p_back[0], p_back[1], 0, '10s', 10140))
    npc.append(spawn_line('m', p_shelter[0], p_shelter[1], 0, '10s', 10145))
    regen += veins(g, reach, rng, (30312, 30311, 30310), 6, avoid, rep)
    put(f, 'regen.txt', regen)
    put(f, 'boss.txt', boss)
    put(f, 'stone.txt', stone)
    put(f, 'npc.txt', npc)
    waw_back = arrive_shelter

    # ---------------------------------------------------------------- Schronienie Polnocnego Wiatru (393)
    M = MAPS[393]
    f, o = M['folder'], owsap_map(M['folder'])
    g = Grid(f, M['size'])
    rep('393 Schronienie Polnocnego Wiatru (%s)' % f)
    regen = nudged(g, read_lines(os.path.join(o, 'regen.txt')), 'regen', rep)
    boss = nudged(g, read_lines(os.path.join(o, 'boss.txt')), 'boss', rep)
    npc = []
    for t in read_lines(os.path.join(o, 'npc.txt')):
        x, y = check_free(g, int(t[1]), int(t[2]), 'NPC %s' % t[10], rep)
        npc.append(spawn_line('m', x, y, 0, '1m', int(t[10]), direction=int(t[6])))
    town = (80, 640)
    p_wawoz = check_free(g, 62, 622, 'portal 10146 (to Wawoz)', rep)
    p_hunter = check_free(g, 98, 628, 'Lowca Glow (Schron.)', rep)
    npc.append(spawn_line('m', p_hunter[0], p_hunter[1], 0, '1m', 20847, direction=1))
    npc.append(spawn_line('m', p_wawoz[0], p_wawoz[1], 0, '10s', 10146))
    put(f, 'regen.txt', regen)
    put(f, 'boss.txt', boss)
    put(f, 'stone.txt', [])
    put(f, 'npc.txt', npc)
    WARPS[10145] = 'SchronPlnW %d %d' % (M['base'][0] // 100 + town[0], M['base'][1] // 100 + town[1])
    WARPS[10146] = 'WawozPlnW %d %d' % (MAPS[388]['base'][0] // 100 + waw_back[0],
                                         MAPS[388]['base'][1] // 100 + waw_back[1])
    for v, n in WARPS.items():
        assert len(n) <= 24, n

    # ---------------------------------------------------------------- Dongan (373): the portal to Seoganland
    g = Grid(DONGAN['folder'], DONGAN['size'])
    x, y = check_free(g, 40, 531, 'Dongan portal 10128', rep)
    dongan_npc = [spawn_line('m', x, y, 0, '10s', 10128)]

    # every spawn on free ground: report the centres that are not (the engine tries again inside the range)
    for idx, M in MAPS.items():
        g = Grid(M['folder'], M['size'])
        bad = 0
        for name, lines in files[M['folder']].items():
            for l in lines:
                t = l.split('\t')
                if not g.free(int(t[1]), int(t[2])):
                    bad += 1
        rep('%d %s: %d spawn centre(s) on blocked ground' % (idx, M['folder'], bad))
        assert bad == 0, M['folder']

    write_all(files, dongan_npc, a.attr, hints, rep)


def group_blocks(path):
    text = open(path, encoding='latin-1').read().replace('\r', '')
    out = {}
    for name, body in re.findall(r'Group\s+(\S+)\s*\{(.*?)\n\}', text, re.S):
        v = re.search(r'Vnum\s+(\d+)', body)
        if v:
            out[int(v.group(1))] = (name, [l.split() for l in body.split('\n') if l.split() and l.split()[0] != 'Vnum'])
    return out


def write_all(files, dongan_npc, attr, hints, rep):
    # groups
    og = group_blocks(os.path.join(OWSAP, 'share/locale/uk/group.txt'))
    ogg = group_blocks(os.path.join(OWSAP, 'share/locale/uk/group_group.txt'))
    L = ['// MT2009_PLUS_YOHARA_MAPS2_V1: Seoganland (376), Namgan (377), Schronienie Polnocnego Wiatru (393) - Owsap',
         '// v6.2.6 group.txt; Wawoz Polnocnego Wiatru (388) - ours (tools/yohara_maps/gen_ymaps2.py; GENERATED)']
    members = set()
    for v in OWSAP_GROUPS:
        name, mem = og[v]
        L += ['Group\tMT2009_ymaps2_%s' % name, '{', '\tVnum\t%d' % v]
        for t in mem:
            mob = int(t[-1])
            assert mob in NAMES, (v, mob)
            members.add(mob)
            L.append('\t%s\t"%s"\t%d' % (t[0], ascii_pl(NAMES[mob]), mob))
        L += ['}', '']
    for v, (name, mobs) in OUR_GROUPS.items():
        L += ['Group\tMT2009_ymaps2_%s' % name, '{', '\tVnum\t%d' % v]
        for k, mob in enumerate(mobs):
            members.add(mob)
            L.append('\t%s\t"%s"\t%d' % ('Leader' if k == 0 else str(k), ascii_pl(NAMES[mob]), mob))
        L += ['}', '']
    os.makedirs(OUT, exist_ok=True)
    open(os.path.join(OUT, 'group.yohara_maps2.txt'), 'w', newline='\n').write('\n'.join(L))
    L = ['// MT2009_PLUS_YOHARA_MAPS2_V1: Owsap v6.2.6 group_group.txt (6706-6710 Seoganland, 6715-6719 Namgan, 4030-4033',
         '// Schronienie) and ours (4040/4041 Wawoz) - the "r" lines of regen.txt (tools/yohara_maps/gen_ymaps2.py)']
    for v in OWSAP_GGROUPS:
        name, mem = ogg[v]
        L += ['Group\tMT2009_ymaps2_%s' % name, '{', '\tVnum\t%d' % v]
        for t in mem:
            assert int(t[1]) in OWSAP_GROUPS, (v, t)
            L.append('\t%s\t%s\t%s' % (t[0], t[1], t[2]))
        L += ['}', '']
    for v, (name, mem) in OUR_GGROUPS.items():
        L += ['Group\tMT2009_ymaps2_%s' % name, '{', '\tVnum\t%d' % v]
        for k, (gv, w) in enumerate(mem, 1):
            L.append('\t%d\t%d\t%d' % (k, gv, w))
        L += ['}', '']
    open(os.path.join(OUT, 'group_group.yohara_maps2.txt'), 'w', newline='\n').write('\n'.join(L))

    # the map folders
    spawned = set(members)
    for idx, M in MAPS.items():
        d = os.path.join(OUT, 'map', M['folder'])
        if os.path.isdir(d):
            shutil.rmtree(d)
        os.makedirs(d)
        src = os.path.join(GF, M['folder'], 'setting.txt')
        st = open(src, encoding='latin-1').read().replace('\r\n', '\n')
        st = re.sub(r'(?m)^ViewRadius\s+\d+', 'ViewRadius\t128', st)
        assert re.search(r'MapSize\s+%d\s+%d' % M['size'], st), M
        assert re.search(r'BasePosition\s+%d\s+%d' % M['base'], st), M
        keep = [l for l in st.split('\n') if l.split() and l.split()[0] in (
            'ScriptType', 'CellScale', 'HeightScale', 'ViewRadius', 'MapSize', 'BasePosition', 'TextureSet',
            'Environment')]
        setting = []
        for l in keep:
            setting.append(l.strip())
            if l.split()[0] in ('ScriptType', 'HeightScale', 'ViewRadius'):
                setting.append('')
        open(os.path.join(d, 'Setting.txt'), 'w', newline='\n').write('\n'.join(setting) + '\n')
        town = {376: '713 565', 377: '508 57', 385: '316 68', 388: '1106 893', 393: '80 640'}[idx]
        open(os.path.join(d, 'Town.txt'), 'w', newline='\n').write(town + '\n')
        for name, lines in files[M['folder']].items():
            open(os.path.join(d, name), 'w', newline='\n').write('\n'.join(lines) + ('\n' if lines else ''))
            for l in lines:
                t = l.split('\t')
                if t[0] == 'm':
                    spawned.add(int(t[10]))
        if attr:
            shutil.copyfile(os.path.join(attr, M['folder']), os.path.join(d, 'server_attr'))
    open(os.path.join(OUT, 'dongan_npc.yohara_maps2.txt'), 'w', newline='\n').write('\n'.join(dongan_npc) + '\n')
    for l in dongan_npc:
        spawned.add(int(l.split('\t')[10]))
    # Namgan's Dongan groups name the first batch's monsters - their rows are yohara_maps.sql's
    new = sorted(v for v in spawned if v in NAMES or v in NPCS or v in WARPS)
    rest = sorted(v for v in spawned if v not in new)
    rep('spawned vnums of this batch: %d new (%s ...), %d of the first batch: %s' % (len(new), new[:6], len(rest), rest))
    write_sql(new, rep)
    open(os.path.join(OUT, 'spawned.txt'), 'w', newline='\n').write(per_map_text(files))
    open(os.path.join(OUT, 'gen_report.txt'), 'w', newline='\n').write('\n'.join(rep.lines) + '\n')


def members_of():
    og = group_blocks(os.path.join(OWSAP, 'share/locale/uk/group.txt'))
    ogg = group_blocks(os.path.join(OWSAP, 'share/locale/uk/group_group.txt'))
    groups = dict((v, [int(t[-1]) for t in og[v][1]]) for v in OWSAP_GROUPS)
    groups.update((v, mobs) for v, (n, mobs) in OUR_GROUPS.items())
    gg = dict((v, [int(t[1]) for t in ogg[v][1]]) for v in OWSAP_GGROUPS)
    gg.update((v, [gv for gv, w in mem]) for v, (n, mem) in OUR_GGROUPS.items())
    return groups, gg


DONGAN_GG = {   # the first batch's group_groups / groups (Owsap) - Namgan uses them
    6700: [6145, 6146, 6147], 6701: [6146, 6147, 6148], 6702: [6146, 6148, 6149], 6703: [6147, 6149, 6152],
    6704: [6147, 6149, 6152], 6705: [6149, 6152]}
DONGAN_G = {6145: [6701, 6712, 6713], 6146: [6700, 6713, 6712], 6147: [6700, 6711, 6713, 6712],
            6148: [6711, 6712, 6713], 6149: [6702, 6710, 6703, 6704], 6150: [6711, 6710, 6713, 6704],
            6151: [6702, 6703, 6712, 6704], 6152: [6710]}


def per_map_text(files):
    groups, gg = members_of()
    groups.update(DONGAN_G)
    gg.update(DONGAN_GG)
    out = ['# MT2009_PLUS_YOHARA_MAPS2_V1: every vnum each map spawns (GENERATED by tools/yohara_maps/gen_ymaps2.py;',
           '# the client builder client-patches/client-2.0.30/tools/ymaps2 reads it): <map index> <vnum>']
    for idx, M in MAPS.items():
        vs = set()
        for name, lines in files[M['folder']].items():
            for l in lines:
                t = l.split('\t')
                v = int(t[10])
                if t[0] == 'r':
                    for gv in gg[v]:
                        vs.update(groups[gv])
                elif t[0] == 'g':
                    vs.update(groups[v])
                else:
                    vs.add(v)
        out += ['%d %d' % (idx, v) for v in sorted(vs)]
    out.append('373 10128')
    return '\n'.join(out) + '\n'


def write_sql(vnums, rep):
    en = {}
    for line in open(os.path.join(OWSAP, 'db/mob_names.txt'), encoding='latin-1'):
        p = line.rstrip('\r\n').split('\t')
        if len(p) >= 2 and p[0].isdigit():
            en[int(p[0])] = p[1]
    rows = {}
    for r in csv.DictReader(open(os.path.join(OWSAP, 'db/mob_proto.txt'), encoding='latin-1'), delimiter='\t'):
        if r['Vnum'].isdigit():
            rows[int(r['Vnum'])] = r
    lines = []
    for v in vnums:
        if v in WARPS:
            t = m1.warp_row(v, WARPS[v])
        elif v in NPCS:
            assert len(NPCS[v].encode('cp1250')) <= 24, NPCS[v]
            t = m1.npc_row(v, ascii_pl(en.get(v, NPCS[v])), NPCS[v], '')
        else:
            assert len(NAMES[v].encode('cp1250')) <= 24, NAMES[v]
            r = dict(rows[v])
            if r['Type'] == 'STONE':
                r['RaceFlags'] = ''          # Owsap's OUTPOST (8626/8627): a plain Metin here
            t = m1.row_of(r, ascii_pl(en.get(v, NAMES[v])), NAMES[v])
        assert len(t) == len(m1.COLS), (v, len(t))
        lines.append('(%s)' % ','.join(str(x) for x in t))
    with open(SQL_OUT, 'w', encoding='utf-8', newline='\n') as f:
        f.write(SQL_HEADER)
        f.write('INSERT IGNORE INTO world.mob_proto (%s) VALUES\n' % ','.join('`%s`' % c for c in m1.COLS))
        f.write(',\n'.join(lines) + ';\n')
    rep('yohara_maps2.sql: %d rows' % len(lines))


SQL_HEADER = """-- MT2009_PLUS_YOHARA_MAPS2_V1: the second batch of Yohara maps - Seoganland (376), Namgan (377), Przelecz Yilad
-- (385), Wawoz Polnocnego Wiatru (388) and Schronienie Polnocnego Wiatru (393): their monsters, bosses, Metins, NPCs,
-- jade veins and portals. GENERATED by tools/yohara_maps/gen_ymaps2.py - do not edit, rerun it. Every start
-- (apply.sh, after yohara_maps.sql), idempotent: INSERT IGNORE - a row the operator changed is kept. Every vnum was
-- free in our world.mob_proto (14 October 2026, the test server).
-- Source: Owsap v6.2.6 db/mob_proto.txt (the official vnums), in our r40250 columns as gen_ymaps_sql.py does it:
-- levels 119-130, HP, damage and defence as Owsap's (the owner, 13 October: "PZ potworow jak w zrodle"), exp 0 as
-- official - champion experience only (sungma_mob_exp.txt). The pl-wiki's Polish names; the element ("mrok",
-- "ziemia", "wiatr", "lod", "blyskawice") is set by zywioly_moby.sql (tools/zywioly rule h, YOHARA_ELEMENTS2).
-- NPCs (Lowca Glow x5, Straznik Wezy, Statua Wezy, Straznik Pln. Wiatru, Zagubiony Zwiadowca, Tajemniczy Oltarz) on
-- our NPC numbers - they stand where the official ones stand, no quests yet. The jade veins 30310-30313 likewise
-- (mining.cpp: server-patches/jadeit). Portals 10127-10140 with Owsap's targets (10139 is a quest NPC there),
-- 10145/10146 ours: Wawoz <-> Schronienie in place of the way through Rozpadlina Dusz (not here yet).
SET NAMES utf8mb4;

"""

if __name__ == '__main__':
    main()
