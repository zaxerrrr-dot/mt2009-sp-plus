#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""gen_maps_wz.py [--ameria DIR] [--client DIR]

MT2009_PLUS_MAPS_WZ_V1: Wezowe Pole and Kraina Gigantow (the owner, 15 October 2026 on the Yohara line; the 2.x line
takes them over on 26 October 2026, hosted by game3 - bin/m2-render-config) - the two old official maps as the
pl-wiki has them ("Wezowe Pole", "Kraina Gigantow" and every monster / Metin page):

  80  Wezowe Pole      metin2_map_snakefield  4x4 at 1049600 716800  (official folder metin2_map_WL_01, index 69 -
                                                                       ours is Przelecz, metin2_map_wl_pass)
  70  Kraina Gigantow  metin2_map_giantland   2x2 at 819200 716800   (official folder metin2_map_nusluck01, index 70)

The official server files (Ameria's share - serverfiles/home.tar.gz, share/locale/germany/map/metin2_map_WL_01 and
metin2_map_nusluck01; = our base share's, which carries them as well) give everything: the terrain (server_attr),
the spawns (regen.txt: group_group 1101-1104 = the cursed wolves, boars, bears and tigers of the first part, 1401/1402
= Niszczyciel and the ogres, 1501-1504 = the golems of the second; 1451-1453 = the Giants and ogres of Kraina
Gigantow), Kraina's Metins Pung-Ma / Ma-An (stone.txt) and the NPCs (Teleporter 9012 at the wiki's 245,580; the
portals 10030 -> Pustynia Yongbi, 10032 -> Kraina Gigantow at the wiki's 93,350, Kraina's 10031 -> Wezowe Pole).
Ameria's regen.txt repeats every line three times (its own density): one of each is the official file (= our base
share's 529 / 155 lines); the times are the base share's (the cursed animals 180 s, the rest 120 s; Kraina 15/20/25 s;
the Metins 30 min). Kraina keeps our base share's herb bushes (group_group 20611 "gigant_herbs", three lines of its
stone.txt). The folders get names of their own (the client map folders of tools/wzmaps: a name no client has, so
the terrain the client draws is always the one shipped with these server_attr files - client-2.0.30/tools/wzmaps).

The way in, as the wiki says: Pustynia Yongbi's bottom-right portal (1477,1357 - our base share's 10108 to Przelecz,
metin2_map_wl_pass) leads to Wezowe Pole (10029 "Wezowe_Pole 10590 7262"); Wezowe Pole's 10030 back to the desert
(3519 6223), its 10032 to Kraina Gigantow (8283 7635), Kraina's 10031 back to Wezowe Pole. Przelecz (69) is removed
since (MT2009_PLUS_PASS69_OFF_V1, the Dockerfile step after the maps' one).
Town.txt: where a player comes in (the official 92,90 / 85,466 stand on the portal back out - a restart there was a
warp to the desert / Wezowe Pole).

Writes (GENERATED - edit this file, run it again):
  linux-port/docker/game/maps_wz/map/<folder>/{Setting,Town,regen,npc,stone}.txt, server_attr (Ameria's, as it is)
  linux-port/docker/game/maps_wz/links.maps_wz.txt          the desert's portal line (the Dockerfile step swaps it in)
  linux-port/docker/game/maps_wz/mob_drop_item.maps_wz.txt  the wiki's drops our groups lack (merged "drop" groups)
  linux-port/docker/game/maps_wz/spawned.txt, gen_report.txt
  linux-port/docker/mariadb/playerbot/maps_wz.sql            the wiki's levels of the Giants and ogres
  tools/maps_wz/maps_wz_mobs.json                            the same for the client (client-2.0.30/tools/wzmaps)

  tar xzf /opt/metin2/ameria/ameria-prj-2025/serverfiles/home.tar.gz -C <dir> --wildcards \\
      'home/srv1/share/locale/germany/map/metin2_map_WL_01/*' 'home/srv1/share/locale/germany/map/metin2_map_nusluck01/*'
  python3 tools/maps_wz/gen_maps_wz.py --ameria <dir>/home/srv1/share/locale/germany/map
"""
import argparse
import collections
import json
import os
import re
import shutil
import struct
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(os.path.dirname(HERE))
OUT = os.path.join(REPO, 'linux-port', 'docker', 'game', 'maps_wz')
SQL_OUT = os.path.join(REPO, 'linux-port', 'docker', 'mariadb', 'playerbot', 'maps_wz.sql')
JSON_OUT = os.path.join(HERE, 'maps_wz_mobs.json')
DEF_AMERIA = '/tmp/claude-0/-root/9f475014-d1bc-4cf4-a3e1-da3c380fc52c/scratchpad/wz/ameria/home/srv1/share/locale/germany/map'
DEF_CLIENT = '/opt/metin2/ameria/ameria-prj-2025/tools/FoxFSArchiver/source/season/season1'
GF = '/opt/metin2/cache/gf/Gameforge_26.1.11/_client'

SNAKE = dict(index=80, folder='metin2_map_snakefield', official='metin2_map_WL_01', client='metin2_map_wl_01',
             name='Wężowe Pole', size=(4, 4), base=(1049600, 716800), lines=529)
GIANT = dict(index=70, folder='metin2_map_giantland', official='metin2_map_nusluck01', client='metin2_map_nusluck01',
             name='Kraina Gigantów', size=(2, 2), base=(819200, 716800), lines=155)
DESERT = dict(index=63, folder='metin2_map_n_desert_01', size=(6, 6), base=(204800, 486400))
# the base share's respawn times (Ameria's 30 s for the second part are its own)
TIMES = {1101: '180s', 1102: '180s', 1103: '180s', 1104: '180s'}
TIME_DEFAULT = '120s'
GIANT_TIMES = {1451: '15s', 1452: '20s', 1453: '25s'}
STONE_TIME = '1800s'
HERBS = ['r\t246\t264\t100\t100\t0\t0\t1200s\t100\t1\t20611',     # our base share's "gigant_herbs" bushes
         'r\t315\t214\t100\t100\t0\t0\t1210s\t100\t1\t20611',
         'r\t302\t266\t100\t100\t0\t0\t1220s\t100\t2\t20611']
# portals (WARP rows of our world.mob_proto, "<name> x y", global / 100)
P_DESERT_IN = 10029     # Wezowe_Pole 10590 7262   (desert -> here)
P_TO_DESERT = 10030     # Pust._Yongbi 3519 6223   (here -> desert)
P_FROM_GIANT = 10031    # Wezowe_Pole 10590 7262   (Kraina -> here)
P_TO_GIANT = 10032      # KrainaGigantow 8283 7635 (here -> Kraina)
P_PASS = 10108          # Przelecz 6201 11875      (the desert's portal of our base share, replaced by 10029)
DESERT_PORTAL = (1477, 1357)
TARGET = {P_DESERT_IN: (10590, 7262), P_FROM_GIANT: (10590, 7262), P_TO_DESERT: (3519, 6223),
          P_TO_GIANT: (8283, 7635)}
DESERT_ARRIVAL_FROM_10030 = (3519 - 2048, 6223 - 4864)     # 1471,1359

# -- the wiki's levels (Ameria's / Owsap's: 1601 71, 1602 73 - the wiki 68 / 70); the golems are the wiki's already --
# MT2009_PLUS_OGRE_LEVEL_V1: the ogres 1601 / 1602 at the global sheet's 71 / 73 (= Ameria / Owsap), the owner,
# 20 October 2026 (tools/ymoby_arkusz/moby_global_data.py) - the 15 October wiki's 68 / 70 overridden
LEVELS = collections.OrderedDict([(1401, 66), (1402, 73), (1403, 77), (1601, 71), (1602, 73), (1603, 75)])
OUR_LEVELS = {1401: 76, 1402: 83, 1403: 87, 1601: 78, 1602: 80, 1603: 85}       # 15 October 2026, the test server

# -- the drops: what each wiki page lists and our mob_drop_item.txt does not drop yet (the official groups - kill
#    groups of the armours +1..+4, herbs, Kamienny Grot, the Metins' panel groups - stay as they are). The wiki gives
#    no chances: ours, temporary (cache/yohara/PROCENTY.md item 8). A "drop" value v is v/4 % a kill (4 000 000 range,
#    the level difference and the drop bonuses on top). Left out: Zwoj Ewolucji / Mutacji 50067/50068 (no use in our
#    world - the Mega Wierzchowce's training quests are _unused), Certyfikat Tugyisa / Kamien Duszy Tugyi (the
#    Biologist's quest drops them itself), Szpon Skarabeusza / Zbroja Nocnego Cienia (Lycan items, not in our world).
MAT = 2          # 0.5 % - Orkowa Maczuga, Piasek Kwarcowy (the official commented-out lines had 1)
EQ = 0.8         # 0.2 % - a weapon / armour / jewel of the wiki's list at +0
HERB = 2         # 0.5 % - as the official herb lines
NAMES = {30194: 'Orkowa Maczuga', 30195: 'Piasek Kwarcowy', 70104: 'Marmur Polimorfii (Kula Polimorfii)',
         50007: 'Srebrna Szkatulka', 8002: 'Kamienna Strzala', 50721: 'Kwiat Brzoskwini', 50725: 'Bez',
         50727: 'Roza Alpejska', 50728: 'Morwa', 50723: 'Kwiat Kaki', 50722: 'Pokrzywa',
         5060: 'Magiczny Dzwon+0', 5080: 'Stalowy Robaczy Dzwon+0', 11680: 'Duchowa Zbroja Plyt.+0',
         100: 'Krwawy Miecz+0', 90: 'Miecz Barbarzyncy+0', 3100: 'Miecz Dwunastu Duchow+0', 3080: 'Olbrz. Topor+0',
         130: 'Pol-ksiezycowy Miecz+0', 3140: 'Magnetyczne Ostrze+0', 1110: 'Noz Blyskawicy+0',
         17160: 'Krysztalowe Kolczyki+0', 15180: 'Deszczowe Buty+0', 11270: 'Zlota Zbroja Plytowa+0',
         11290: 'Zbroja Z Czarnej Stali+0', 11490: 'Ubranie Czarn. Wiatru+0', 11690: 'Zbr. Plyt. Czar. Magii+0',
         11890: 'Czarna Szata+0'}
MOB_NAMES = {1401: 'Niszczyciel', 1402: 'Wojownik z Toporem', 1403: 'Tysieczny Wojownik', 1501: 'Skalny Golem',
             1502: 'Kamienny Golem', 1503: 'Olbrzymi Skalny Golem', 1601: 'Ogr Wojownik', 1602: 'Ogr Rzeznik',
             1603: 'Ogr Szaleniec'}
DROPS = collections.OrderedDict([
    # Niszczyciel: Magiczny Dzwon, Stalowy Robaczy Dzwon, Duchowa Zbroja Plytowa (Kwiat Kaki is there)
    (1401, [(5060, 1, EQ), (5080, 1, EQ), (11680, 1, EQ)]),
    # Wojownik z Toporem: Krwawy Miecz, Miecz Dwunastu Duchow, Krysztalowe Kolczyki, Deszczowe Buty, Kula Polimorfii
    # (Zlota Zbroja Plytowa: its +3/+4 kill group)
    (1402, [(100, 1, EQ), (3100, 1, EQ), (17160, 1, EQ), (15180, 1, EQ), (70104, 1, 1)]),
    # Tysieczny Wojownik: Noz Blyskawicy, Krwawy Miecz, the black armours, Kula Polimorfii (the level-70 weapons, Bez
    # and the 86+ items are there)
    (1403, [(1110, 1, EQ), (100, 1, EQ), (11890, 1, EQ), (11490, 1, EQ), (11290, 1, EQ), (11690, 1, EQ),
            (70104, 1, 1)]),
    # Skalny Golem: Krwawy Miecz, Miecz Barbarzyncy, Miecz Dwunastu Duchow, Olbrzymi Topor, Piasek Kwarcowy
    (1501, [(100, 1, EQ), (90, 1, EQ), (3100, 1, EQ), (3080, 1, EQ), (30195, 1, MAT)]),
    # Kamienny Golem: Kamienna Strzala x100, Magiczny Dzwon, Stalowy Robaczy Dzwon, Duchowa Zbroja Plytowa, Piasek
    (1502, [(8002, 100, 1), (5060, 1, EQ), (5080, 1, EQ), (11680, 1, EQ), (30195, 1, MAT)]),
    # Olbrzymi Skalny Golem: Piasek Kwarcowy, Srebrna Szkatulka (Kwiat Kaki is there)
    (1503, [(30195, 1, MAT), (50007, 1, 1)]),
    # Ogr Wojownik: Orkowa Maczuga, Bez, Kwiat Brzoskwini, Roza Alpejska, Kula Polimorfii (Morwa is there)
    (1601, [(30194, 1, MAT), (50725, 1, HERB), (50721, 1, HERB), (50727, 1, HERB), (70104, 1, 1)]),
    # Ogr Rzeznik: Orkowa Maczuga, Magnetyczne Ostrze (Kwiat Brzoskwini and the armours +1/+2 are there)
    (1602, [(30194, 1, MAT), (3140, 1, EQ)]),
    # Ogr Szaleniec: Magiczny Dzwon, Pol-ksiezycowy Miecz, the black armours (Magnetyczne Ostrze +0 and Pokrzywa are)
    (1603, [(5060, 1, EQ), (130, 1, EQ), (11690, 1, EQ), (11290, 1, EQ), (11490, 1, EQ), (11890, 1, EQ)]),
])


class Report:
    def __init__(self):
        self.lines = []

    def __call__(self, s):
        self.lines.append(s)
        print(s)


class Grid:
    """A client map's attr.atr: one byte a metre (bit 0 block, bit 1 water - walkable: a bridge or a shallow carries
    water without block; these maps' bytes carry 0xC8 in their high bits too)."""

    def __init__(self, folder, size):
        w, h = size
        self.W, self.H = w * 256, h * 256
        self.a = bytearray(self.W * self.H)
        for cy in range(h):
            for cx in range(w):
                b = open(os.path.join(folder, '%03d%03d' % (cx, cy), 'attr.atr'), 'rb').read()
                assert struct.unpack_from('<3H', b, 0)[1:] == (256, 256), (folder, cx, cy)
                d = b[6:]
                for y in range(256):
                    o = (cy * 256 + y) * self.W + cx * 256
                    self.a[o:o + 256] = d[y * 256:(y + 1) * 256]

    def free(self, x, y):
        return 0 <= x < self.W and 0 <= y < self.H and not (self.a[y * self.W + x] & 1)

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
                if ok and not seen[j] and not (a[j] & 1):
                    seen[j] = 1
                    dq.append(j)
        return seen


def read_lines(path):
    out = []
    for l in open(path, encoding='latin-1'):
        t = l.rstrip('\r\n').split()
        if len(t) >= 11 and t[0] in ('m', 'g', 'r', 's') and not l.startswith('//'):
            out.append(t)
    return out


def check_free(grid, x, y, what, rep, maxr=25):
    p = grid.nearest_free(x, y, maxr)
    if p is None:
        raise SystemExit('%s at %d,%d: no free cell within %d m' % (what, x, y, maxr))
    if p != (x, y):
        rep('  %s: %d,%d is blocked -> %d,%d' % (what, x, y, p[0], p[1]))
    return p


def dist(a, b):
    return ((a[0] - b[0]) ** 2 + (a[1] - b[1]) ** 2) ** 0.5


def official_regen(M, am, grid, times, rep):
    """Ameria's regen.txt, one of each repeated line, the base share's times, centres on free ground (a centre on
    blocked ground spawns nothing: moved to the nearest free metre - the official file has 98 of Wezowe Pole's 529 on
    the terrain's rock, 36 of them 51-74 m from open ground)."""
    seen, out, moved = set(), [], collections.Counter()
    for t in read_lines(os.path.join(am, M['official'], 'regen.txt')):
        key = tuple(t[:7]) + tuple(t[8:])
        if key in seen:
            continue
        seen.add(key)
        assert t[0] == 'r', t
        x, y = int(t[1]), int(t[2])
        p = grid.nearest_free(x, y, 80)
        assert p is not None, t
        if p != (x, y):
            d = dist(p, (x, y))
            moved['<=10 m' if d <= 10 else '<=25 m' if d <= 25 else '%d-%d m' % (25, 80)] += 1
        t = list(t)
        t[1], t[2] = str(p[0]), str(p[1])
        t[7] = times.get(int(t[10]), TIME_DEFAULT)
        out.append('\t'.join(t))
    assert len(out) == M['lines'], (M['folder'], len(out))
    cnt = collections.Counter(int(l.split('\t')[10]) for l in out)
    rep('  regen: %d lines (Ameria\'s %d / 3), group_group %s; %d centre(s) on blocked ground moved to the nearest '
        'free metre (%s)' % (len(out), len(seen) * 3, dict(sorted(cnt.items())), sum(moved.values()),
                              ', '.join('%s %d' % kv for kv in sorted(moved.items())) or '-'))
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--ameria', default=DEF_AMERIA, help="Ameria's share/locale/germany/map")
    ap.add_argument('--client', default=DEF_CLIENT, help="Ameria's client season1 folder (the maps' attr.atr)")
    a = ap.parse_args()
    rep = Report()
    files = {}

    # ---- Wezowe Pole
    M = SNAKE
    rep('%d Wezowe Pole (%s = the official %s), %dx%d at %d %d' % (M['index'], M['folder'], M['official'],
                                                                 M['size'][0], M['size'][1], M['base'][0], M['base'][1]))
    g = Grid(os.path.join(a.client, M['client']), M['size'])
    regen = official_regen(M, a.ameria, g, TIMES, rep)
    npc_in = read_lines(os.path.join(a.ameria, M['official'], 'npc.txt'))
    want = {P_TO_DESERT: (92, 89), P_TO_GIANT: (92, 349), 9012: (245, 580)}
    assert dict((int(t[10]), (int(t[1]), int(t[2]))) for t in npc_in) == want, npc_in
    npc = []
    for t in npc_in:
        v = int(t[10])
        x, y = check_free(g, int(t[1]), int(t[2]), 'NPC %d' % v, rep)
        npc.append('m\t%d\t%d\t0\t0\t0\t%s\t%s\t100\t1\t%d' % (x, y, t[6], t[7], v))
    arrival = (TARGET[P_DESERT_IN][0] - M['base'][0] // 100, TARGET[P_DESERT_IN][1] - M['base'][1] // 100)
    assert g.free(*arrival), arrival
    assert dist(arrival, want[P_TO_DESERT]) * 100 > 300, 'the arrival must be out of the portal\'s 300-unit reach'
    reach = g.reach([arrival])
    for v, p in want.items():
        assert reach[p[1] * g.W + p[0]], ('NPC %d not reachable from the arrival' % v)
    arr_giant = (TARGET[P_TO_GIANT][0] - GIANT['base'][0] // 100, TARGET[P_TO_GIANT][1] - GIANT['base'][1] // 100)
    rep('  NPCs: Teleporter 9012 %s, 10030 (Pustynia Yongbi) %s, 10032 (Kraina Gigantow) %s; Town %d,%d (the arrival '
        'from the desert and from Kraina, %.1f m from 10030)' % (want[9012], want[P_TO_DESERT], want[P_TO_GIANT],
                                                                  arrival[0], arrival[1],
                                                                  dist(arrival, want[P_TO_DESERT])))
    unreach = sum(1 for l in regen if not reach[int(l.split('\t')[2]) * g.W + int(l.split('\t')[1])])
    rep('  %d of %d spawn lines on ground not walkable from the arrival (the wiki: the second part lies behind the '
        'river and the hills - its bridge in the south)' % (unreach, len(regen)))
    files[M['folder']] = dict(regen=regen, npc=npc, stone=[], town=arrival, M=M)

    # ---- Kraina Gigantow
    M = GIANT
    rep('%d Kraina Gigantow (%s = the official %s), %dx%d at %d %d' % (M['index'], M['folder'], M['official'],
                                                                      M['size'][0], M['size'][1], M['base'][0],
                                                                      M['base'][1]))
    g2 = Grid(os.path.join(a.client, M['client']), M['size'])
    regen2 = official_regen(M, a.ameria, g2, GIANT_TIMES, rep)
    npc_in = read_lines(os.path.join(a.ameria, M['official'], 'npc.txt'))
    assert [(int(t[10]), int(t[1]), int(t[2])) for t in npc_in] == [(P_FROM_GIANT, 82, 467)], npc_in
    x, y = check_free(g2, 82, 467, 'NPC 10031', rep)
    npc2 = ['m\t%d\t%d\t0\t0\t0\t4\t1m\t100\t1\t%d' % (x, y, P_FROM_GIANT)]
    assert g2.free(*arr_giant) and dist(arr_giant, (x, y)) * 100 > 300, arr_giant
    reach2 = g2.reach([arr_giant])
    assert reach2[y * g2.W + x]
    stones = read_lines(os.path.join(a.ameria, M['official'], 'stone.txt'))
    assert sorted(int(t[10]) for t in stones) == [8024, 8025], stones
    stone2 = []
    for t in stones:
        sx, sy = check_free(g2, int(t[1]), int(t[2]), 'Metin %s' % t[10], rep)
        assert reach2[sy * g2.W + sx]
        stone2.append('m\t%d\t%d\t%s\t%s\t0\t0\t%s\t100\t1\t%s' % (sx, sy, t[3], t[4], STONE_TIME, t[10]))
    for l in HERBS:
        t = l.split('\t')
        t[1], t[2] = [str(c) for c in check_free(g2, int(t[1]), int(t[2]), 'herb bushes 20611', rep)]
        stone2.append('\t'.join(t))
    unreach = sum(1 for l in regen2 if not reach2[int(l.split('\t')[2]) * g2.W + int(l.split('\t')[1])])
    rep('  NPC: 10031 (Wezowe Pole) %d,%d; Town %d,%d (the arrival from Wezowe Pole, %.1f m from 10031); Metins: '
        'Pung-Ma 8024 / Ma-An 8025 (%s), the herb bushes 20611 x3; %d of %d spawn lines not walkable from the arrival'
        % (x, y, arr_giant[0], arr_giant[1], dist(arr_giant, (x, y)), STONE_TIME, unreach, len(regen2)))
    files[M['folder']] = dict(regen=regen2, npc=npc2, stone=stone2, town=arr_giant, M=M)

    # ---- the desert's portal: our base share's 10108 (to Przelecz) at the bottom right becomes 10029
    gd = Grid(os.path.join(GF, DESERT['folder']), DESERT['size'])
    dp = check_free(gd, DESERT_PORTAL[0], DESERT_PORTAL[1], 'desert portal 10029', rep)
    da = DESERT_ARRIVAL_FROM_10030
    assert gd.free(*da) and dist(dp, da) * 100 > 300, (dp, da)
    dreach = gd.reach([(130, 1408)])     # Town.txt's first point (768,768 is rock in GF's attr.atr)
    assert dreach[dp[1] * gd.W + dp[0]] and dreach[da[1] * gd.W + da[0]]
    link = 'm\t%d\t%d\t0\t0\t0\t4\t1m\t100\t1\t%d' % (dp[0], dp[1], P_DESERT_IN)
    rep('desert (63): 10029 at %d,%d in place of our base share\'s 10108 (Przelecz) - %.1f m from where 10030 puts a '
        'player down (%d,%d), both on the town\'s ground (GF\'s attr.atr)' % (dp[0], dp[1], dist(dp, da), da[0], da[1]))

    # ---- write
    for folder, f in files.items():
        M = f['M']
        d_ = os.path.join(OUT, 'map', folder)
        if os.path.isdir(d_):
            shutil.rmtree(d_)
        os.makedirs(d_)
        st = open(os.path.join(a.ameria, M['official'], 'Setting.txt'), encoding='latin-1').read()
        assert re.search(r'MapSize\s+%d\s+%d' % M['size'], st) and re.search(r'BasePosition\s+%d\s+%d' % M['base'], st)
        setting = ['ScriptType\tMapSetting', '', 'CellScale\t200', 'HeightScale\t0.500000', '', 'ViewRadius\t128', '',
                   'MapSize\t%d\t%d' % M['size'], 'BasePosition\t%d\t%d' % M['base'],
                   'TextureSet\ttextureset\\metin2_wl_01.txt', 'Environment\tmilgyo.msenv']
        for k in ('TextureSet', 'Environment'):
            assert re.search(r'%s\s+%s' % (k, re.escape([l for l in setting if l.startswith(k)][0].split('\t')[1])),
                             st), (folder, k)
        open(os.path.join(d_, 'Setting.txt'), 'w', newline='\n').write('\n'.join(setting) + '\n')
        open(os.path.join(d_, 'Town.txt'), 'w', newline='\n').write('%d %d\n' % f['town'])
        for name in ('regen', 'npc', 'stone'):
            if f[name]:
                open(os.path.join(d_, name + '.txt'), 'w', newline='\n').write('\n'.join(f[name]) + '\n')
        shutil.copyfile(os.path.join(a.ameria, M['official'], 'server_attr'), os.path.join(d_, 'server_attr'))
        hdr = open(os.path.join(d_, 'server_attr'), 'rb').read(8)
        assert struct.unpack('<2i', hdr) == (M['size'][0] * 4, M['size'][1] * 4), (folder, hdr)   # 64 m sectrees
    open(os.path.join(OUT, 'links.maps_wz.txt'), 'w', newline='\n').write(
        '# MT2009_PLUS_MAPS_WZ_V1 (GENERATED by tools/maps_wz/gen_maps_wz.py): <map index> <folder> <npc.txt line> -\n'
        '# the Dockerfile step puts it in place of the line of the vnum named last (our base share\'s 10108)\n'
        '%d\t%s\t%s\t%d\n' % (DESERT['index'], DESERT['folder'], link, P_PASS))
    write_drops(rep)
    write_sql(rep)
    vs = set()
    gg = {1101: [127, 128, 129], 1102: [129, 130, 131], 1103: [131, 132, 133], 1104: [134, 135, 136],
          1401: [1401, 1601], 1402: [1401, 1601, 1602], 1451: [1401, 1601, 1602],
          1452: [1401, 1601, 1602, 1402, 1603], 1453: [1601, 1402, 1602, 1603, 1403],
          1501: [1501, 1502], 1502: [1501, 1502], 1503: [1501, 1502, 1503], 1504: [1502, 1503]}
    groups = {127: [131], 128: [132, 131], 129: [133], 130: [134, 133], 131: [135], 132: [138], 133: [139],
              134: [140, 139], 135: [141], 136: [143, 141], 1401: [1401], 1402: [1402], 1403: [1403], 1501: [1501],
              1502: [1502], 1503: [1503], 1601: [1601], 1602: [1602], 1603: [1603]}
    out = ['# MT2009_PLUS_MAPS_WZ_V1: every vnum each map spawns (GENERATED by tools/maps_wz/gen_maps_wz.py; our',
           '# group_group.txt / group.txt rows of the official groups): <map index> <vnum>']
    for folder, f in files.items():
        vs = set()
        for l in f['regen']:
            for grp in gg[int(l.split('\t')[10])]:
                vs.update(groups[grp])
        for l in f['npc'] + f['stone']:
            v = int(l.split('\t')[10])
            if v != 20611:
                vs.add(v)
            else:
                vs.update((20608, 20609, 20610))
        out += ['%d %d' % (f['M']['index'], v) for v in sorted(vs)]
    out.append('%d %d' % (DESERT['index'], P_DESERT_IN))
    open(os.path.join(OUT, 'spawned.txt'), 'w', newline='\n').write('\n'.join(out) + '\n')
    open(os.path.join(OUT, 'gen_report.txt'), 'w', newline='\n').write('\n'.join(rep.lines) + '\n')


def write_drops(rep):
    L = ['// MT2009_PLUS_MAPS_WZ_V1: Wezowe Pole (80) and Kraina Gigantow (70) - what the pl-wiki page of each monster',
         '// lists and our mob_drop_item.txt did not drop (its official groups stay). GENERATED by',
         '// tools/maps_wz/gen_maps_wz.py - do not edit. "drop" groups join the mob\'s other drop group(s) (the reader',
         '// merges them). The wiki gives no chances: temporary ones (cache/yohara/PROCENTY.md item 8) - v/4 % a kill:',
         '// Orkowa Maczuga / Piasek Kwarcowy %g, a herb %g, the wiki\'s weapons / armours / jewels at +0 %g.' % (
             MAT, HERB, EQ), '']
    n = 0
    for v, rows in DROPS.items():
        L += ['Group\tMT2009_maps_wz_%d' % v, '{', '\tMob\t%d\t-- %s' % (v, MOB_NAMES[v]), '\tType\tdrop']
        seen = set()
        for k, (iv, c, p) in enumerate(rows, 1):
            assert iv not in seen, (v, iv)
            seen.add(iv)
            L.append('\t%d\t%d\t%d\t%g\t-- %s%s' % (k, iv, c, p, NAMES[iv], ' x%d' % c if c > 1 else ''))
            n += 1
        L += ['}', '']
    open(os.path.join(OUT, 'mob_drop_item.maps_wz.txt'), 'w', encoding='utf-8', newline='\n').write('\n'.join(L))
    mats = ['%s %d (%s)' % (NAMES[iv], iv, ','.join(str(v) for v, rows in DROPS.items() if any(r[0] == iv for r in rows)))
            for iv in (30194, 30195)]
    rep('drops: %d groups, %d rows; materials: %s' % (len(DROPS), n, '; '.join(mats)))


def write_sql(rep):
    L = ['-- MT2009_PLUS_MAPS_WZ_V1: Wezowe Pole (80) and Kraina Gigantow (70) - the Giants\' and ogres\' levels as the',
         '-- pl-wiki has them (Niszczyciel 66, Wojownik z Toporem 73, Tysieczny Wojownik 77, Ogr Szaleniec 75); Ogr',
         '-- Wojownik 71 / Ogr Rzeznik 73 as the global sheet, Owsap and Ameria (the wiki 68 / 70; the owner 20.10.2026,',
         '-- MT2009_PLUS_OGRE_LEVEL_V1); ours were 76/83/87/78/80/85; the',
         '-- golems 69/72/76 are the wiki\'s already). Only the level: HP, damage, exp and the rest stay ours. GENERATED',
         '-- by tools/maps_wz/gen_maps_wz.py. Every start (apply.sh), idempotent. Every vnum the maps spawn, portal and',
         '-- drop exists in our world already (15 October 2026, the test server): no INSERT.', 'SET NAMES utf8mb4;']
    for v, lv in LEVELS.items():
        L.append('UPDATE world.mob_proto SET level = %d WHERE vnum = %d AND level <> %d;   -- %s (was %d)' % (
            lv, v, lv, MOB_NAMES[v], OUR_LEVELS[v]))
    open(SQL_OUT, 'w', encoding='utf-8', newline='\n').write('\n'.join(L) + '\n')
    with open(JSON_OUT, 'w', encoding='utf-8', newline='\n') as f:
        json.dump(dict(levels=dict((str(v), lv) for v, lv in LEVELS.items()),
                       atlas=[[SNAKE['folder'], SNAKE['base'][0], SNAKE['base'][1], SNAKE['size'][0], SNAKE['size'][1]],
                              [GIANT['folder'], GIANT['base'][0], GIANT['base'][1], GIANT['size'][0], GIANT['size'][1]]],
                       atlas_replace=['metin2_map_wl_01', 'metin2_map_nusluck01']), f, indent=1)
        f.write('\n')
    rep('maps_wz.sql: %d level rows; maps_wz_mobs.json for the client' % len(LEVELS))


if __name__ == '__main__':
    main()
