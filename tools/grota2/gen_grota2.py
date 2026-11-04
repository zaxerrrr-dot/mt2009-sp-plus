#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""gen_grota2.py [--png OUT.png]

Grota Wygnancow V2 (map 73, metin2_map_skipia_dungeon_02, 6x6, base 153600 1203200, levels 87-97).

MT2009_PLUS_GROTA2_REGEN_V1 (3 November 2026): whole rooms and corridors had no monster (the owner: "W grocie
wygnancow v2 jest bardzo duzo pustych spotow, komnat w ktorych nie ma w ogole potworow"). The package's regen.txt
(722 lines) is the OLD dump of the map, 84 of its lines ("r ... 2410") commented out; V1 kept it, made the 84 lines
2409 and appended the newer dump's points once each plus fill points.

MT2009_PLUS_GROTA2_REGEN_V2 (4 November 2026): "like the global server" (the owner, with the players' map of the
global Grota V2: "Biale i niebieskie spoty sa najlepsze, z najtrudniejszymi potworami"). The map's regen.txt is
now this file whole:
  1. the newer dump of the map (Owsap's uk set, a dump of the global server: 2017 lines - the 708 old points
     twice, which is the global density, plus 599 newer points), line for line, its 2410 written as 2409 (the same
     groups 2417 + 2418; our group_group has no 2410), its 70 s; a centre on BLOCK moved to the nearest free metre
     of the main piece (6 m at most, else left out);
  2. while a walkable metre of the main piece is more than FILL_REACH m of walking from every spawn, a point on
     the farthest such metre (CLEAR m free all round, not within SAFE m of the arrival and the NPCs), the
     group_group of the nearest spawn by walking - V1's fix of the empty rooms, kept;
  3. the spots of the players' map (SPOTS below; their rooms found on the server_attr): every line whose centre
     is in a spot's room is taken out and the room gets its spot's monsters on a grid of points across it -
       white (MK 1/2 and the five white rooms) and blue (PRESUB 1-3): the hardest - Komendant (2414: 97 with two
         Magistrates) and Magistrat (2413: 95) groups, half and half;
       green (SOBA 1, 1', 2): Soldat + Bogenschuetze - 2411 and 2412, half and half;
       red (MAXIMAXI) and orange (EISSOBA 2, 950:950): the dump's own groups there, topped up;
     at least MIN_PER_ROOM lines in a spot's room (more where the dump already has more).
  The bosses: the dump's Dowodca Yonghan (2491) places we lack (boss.grota2.txt, our 20 min). The ghosts (30121 -
  the Blue Dragon lair, the players' map's "Krysztalowa Komnata (GV3)"; 30122), Szkielet-Sura 5 (30128) and the
  way out (10079) are the package's npc.txt, where the global map has them.

What this writes (GENERATED - edit this file, run it again):
  linux-port/docker/game/grota2/regen.txt  - the map's regen.txt (Dockerfile step MT2009_PLUS_GROTA2_REGEN_V2)
  linux-port/docker/game/grota2/boss.grota2.txt - appended to the map's boss.txt
  linux-port/docker/game/grota2/gen_report.txt  - what was where, and the bots' hubs (playerbot_wandering.h)

Needs python-lzo for server_attr (the m2pack-lzo image has it):
  docker run --rm -v /opt/metin2:/opt/metin2 -w <worktree> m2pack-lzo python3 tools/grota2/gen_grota2.py \
      [--png /path/overview.png]
"""
import argparse
import collections
import os
import struct
import zlib

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.normpath(os.path.join(HERE, '..', '..'))
OUT = os.path.join(ROOT, 'linux-port', 'docker', 'game', 'grota2')

MAP = 'metin2_map_skipia_dungeon_02'
SHARE = '/opt/metin2/mt2009plustest/linux-port/docker/game/src/serverfiles/share/locale/poland/'
BASE = SHARE + 'map/' + MAP
NEWER = '/opt/metin2/cache/owsap/Server/Server/share/locale/uk/map/' + MAP
N = 1536                    # 6 x 256 m
BASE_X, BASE_Y = 153600, 1203200
ARRIVAL = (877, 721)        # PLAYERBOT_GROTTO_V2_ARRIVAL (241325, 1275425) and the way out 10079 at 881,726
NPCS = [(881, 726), (266, 175), (369, 294), (1003, 921)]
SAFE = 30                   # no fill point this near the arrival, the ghosts and the skeleton
REACH = 25                  # the coverage the report measures
FILL_REACH = 40
CLEAR = 2
MOVE_MAX = 6
TIME = '70s'                # the dump's
BOSS_TIME = '1200s'
ROOM_CORE = 14              # a room: ground with 14 m free all round (the corridors are about 20 m wide)
MIN_PER_ROOM = 14

HARD = (2414, 2413)
SOBA = (2411, 2412)
# The players' map of the global Grota V2 (the owner, 4 November 2026; its coordinates are the map's own metres,
# 2 m a pixel): name, colour, the rooms (a point in each), the groups (None: the dump's own).
SPOTS = [
    ('SOBA 1 (680:175)', 'green', [(683, 174), (685, 260)], SOBA),
    ('SOBA 1 (1111:175)', 'green', [(1114, 174), (1113, 258)], SOBA),
    ('SOBA 2 (915:250)', 'green', [(913, 259), (915, 357)], SOBA),
    ('MAXIMAXI (250:414)', 'red', [(248, 276), (249, 414)], None),
    ('PRESUB 1 (400:740)', 'blue', [(396, 739)], HARD),
    ('PRESUB 2 (400:1000)', 'blue', [(395, 1004)], HARD),
    ('PRESUB 3 (600:1000)', 'blue', [(597, 1005)], HARD),
    ('EISSOBA 2 (750:1000)', 'orange', [(751, 929), (753, 1014)], None),
    ('950:950', 'orange', [(938, 927)], None),
    ('MK 1 (200:730)', 'white', [(148, 729), (246, 729)], HARD),
    ('MK 2 (200:1050)', 'white', [(148, 1054), (244, 1055)], HARD),
    ('white 485:262', 'white', [(485, 262)], HARD),
    ('white 747:347', 'white', [(747, 347)], HARD),
    ('white 1330:269', 'white', [(1330, 269)], HARD),
    ('white 1078:637', 'white', [(1078, 637)], HARD),
    ('white 565:839', 'white', [(565, 839)], HARD),
]
LEVEL = {2401: 87, 2402: 89, 2403: 89, 2404: 90, 2411: 91, 2412: 93, 2413: 95, 2414: 97}


def read_walk(path):
    import lzo
    b = open(path, 'rb').read()
    w, h = struct.unpack_from('<2i', b, 0)
    o = 8
    sec = 128
    W = w * sec
    g = bytearray(W * h * sec)
    for sy in range(h):
        for sx in range(w):
            n = struct.unpack_from('<i', b, o)[0]
            o += 4
            raw = lzo.decompress(b[o:o + n], False, sec * sec * 4)
            o += n
            v = struct.unpack('<%dI' % (sec * sec), raw)
            for y in range(sec):
                r = (sy * sec + y) * W + sx * sec
                g[r:r + sec] = bytes(x & 0xff for x in v[y * sec:(y + 1) * sec])
    assert o == len(b) and W == 2 * N
    walk = bytearray(N * N)
    for y in range(N):
        r = 2 * y * W
        for x in range(N):
            # a metre is free when none of its four 50-unit cells is BLOCK
            if not (g[r + 2 * x] | g[r + 2 * x + 1] | g[r + W + 2 * x] | g[r + W + 2 * x + 1]) & 1:
                walk[y * N + x] = 1
    return walk


def lines(path):
    out = []
    for l in open(path, encoding='latin-1'):
        p = l.strip().split()
        if len(p) >= 11:
            out.append(p)
    return out


def neighbours(i):
    x = i % N
    if x > 0:
        yield i - 1
    if x < N - 1:
        yield i + 1
    if i >= N:
        yield i - N
    if i < N * N - N:
        yield i + N


def clearance(main_):
    """Chessboard metres to the nearest ground off the main piece."""
    INF = 1 << 20
    d = [INF if main_[i] else 0 for i in range(N * N)]
    for y in range(N):
        for x in range(N):
            i = y * N + x
            if d[i]:
                m = d[i]
                for dx, dy in ((-1, 0), (0, -1), (-1, -1), (1, -1)):
                    xx, yy = x + dx, y + dy
                    m = min(m, d[yy * N + xx] + 1) if 0 <= xx < N and 0 <= yy < N else 0
                d[i] = m
    for y in range(N - 1, -1, -1):
        for x in range(N - 1, -1, -1):
            i = y * N + x
            if d[i]:
                m = d[i]
                for dx, dy in ((1, 0), (0, 1), (1, 1), (-1, 1)):
                    xx, yy = x + dx, y + dy
                    m = min(m, d[yy * N + xx] + 1) if 0 <= xx < N and 0 <= yy < N else 0
                d[i] = m
    return d


def find_rooms(clear):
    seen = bytearray(N * N)
    rooms = []
    for s in range(N * N):
        if clear[s] >= ROOM_CORE and not seen[s]:
            st = [s]
            seen[s] = 1
            x0 = y0 = N
            x1 = y1 = 0
            while st:
                i = st.pop()
                x, y = i % N, i // N
                x0, x1, y0, y1 = min(x0, x), max(x1, x), min(y0, y), max(y1, y)
                for j in neighbours(i):
                    if not seen[j] and clear[j] >= ROOM_CORE:
                        seen[j] = 1
                        st.append(j)
            k = ROOM_CORE - 1
            rooms.append((x0 - k, y0 - k, x1 + k, y1 + k))
    return rooms


def group_levels():
    """group_group vnum -> the levels of its groups' members (leaders included), from the package's files."""
    groups = {}
    cur = None
    lead = None
    for l in open(SHARE + 'group.txt', encoding='latin-1'):
        p = l.split()
        if not p:
            continue
        if p[0] == '{':
            lead = None
        elif p[0] == '}':
            cur = None
            lead = None
        elif p[0] == 'Leader' and p[-1].isdigit():
            lead = int(p[-1])
        elif p[0] == 'Vnum' and len(p) >= 2:
            cur = groups.setdefault(int(p[1]), [])
            if lead is not None:
                cur.append(lead)
        elif cur is not None and p[0].isdigit() and len(p) >= 2 and p[-1].isdigit():
            cur.append(int(p[-1]))
    gg = {}
    cur = None
    for l in open(SHARE + 'group_group.txt', encoding='latin-1'):
        p = l.split()
        if not p:
            continue
        if p[0] == 'Vnum' and len(p) >= 2:
            cur = gg.setdefault(int(p[1]), [])
        elif cur is not None and len(p) >= 3 and p[0].isdigit():
            cur.extend(groups.get(int(p[1]), []))
        elif p[0] == '}':
            cur = None
    return {k: [LEVEL[m] for m in v if m in LEVEL] for k, v in gg.items()}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--png')
    a = ap.parse_args()
    walk = read_walk(os.path.join(BASE, 'server_attr'))

    # the main walkable piece (from the arrival)
    main_ = bytearray(N * N)
    s = ARRIVAL[1] * N + ARRIVAL[0]
    assert walk[s]
    main_[s] = 1
    q = [s]
    while q:
        k = q.pop()
        for j in neighbours(k):
            if walk[j] and not main_[j]:
                main_[j] = 1
                q.append(j)
    clear_m = clearance(main_)
    rooms = find_rooms(clear_m)

    def clear(i, r):
        return clear_m[i] > r

    def nudge(x, y, r, need=0):
        best = None
        for dy in range(-r, r + 1):
            for dx in range(-r, r + 1):
                xx, yy = x + dx, y + dy
                if 0 <= xx < N and 0 <= yy < N and main_[yy * N + xx] and clear_m[yy * N + xx] > need:
                    d = dx * dx + dy * dy
                    if best is None or d < best[0]:
                        best = (d, xx, yy)
        return None if best is None else best[1:]

    report = []
    # 1. the dump, line for line
    dump = []           # [x, y, sx, sy, vnum, origin]
    dropped = []
    moved = 0
    for p in lines(os.path.join(NEWER, 'regen.txt')):
        if p[0] != 'r':
            continue
        x, y, sx, sy, v = int(p[1]), int(p[2]), int(p[3]), int(p[4]), int(p[10])
        v = 2409 if v == 2410 else v
        if not main_[y * N + x]:
            m = nudge(x, y, MOVE_MAX)
            if m is None:
                dropped.append((x, y, v))
                continue
            report.append('  moved %d,%d -> %d,%d (BLOCK)' % (x, y, m[0], m[1]))
            moved += 1
            x, y = m
        dump.append([x, y, sx, sy, v, 'dump'])

    # walking distance from every spawn, with the nearest spawn's group_group
    INF = 1 << 30
    dist = [INF] * (N * N)
    src = [0] * (N * N)

    def spread(pts):
        dq = collections.deque()
        for x, y, sx, sy, v, o in pts:
            i = y * N + x
            if main_[i] and dist[i] > 0:
                dist[i] = 0
                src[i] = v
                dq.append(i)
        while dq:
            i = dq.popleft()
            nd = dist[i] + 1
            for j in neighbours(i):
                if main_[j] and dist[j] > nd:
                    dist[j] = nd
                    src[j] = src[i]
                    dq.append(j)

    def uncovered_count(r=REACH):
        return sum(1 for i in range(N * N) if main_[i] and dist[i] > r)

    # the package as it is (for the report)
    pkg = [[int(p[1]), int(p[2]), 10, 10, int(p[10]), 'pkg'] for p in lines(os.path.join(BASE, 'regen.txt'))
           if p[0] == 'r']
    spread(pkg)
    unc_pkg = uncovered_count()
    dist = [INF] * (N * N)

    # 2. the fill
    spread(dump)
    unc_dump = uncovered_count()
    safe = set()
    for cx, cy in NPCS:
        for dy in range(-SAFE, SAFE + 1):
            for dx in range(-SAFE, SAFE + 1):
                if dx * dx + dy * dy <= SAFE * SAFE:
                    safe.add((cy + dy) * N + cx + dx)
    filled = []
    cand = [i for i in range(N * N) if main_[i] and i not in safe and clear(i, CLEAR)]
    while True:
        best = max(cand, key=lambda i: dist[i])
        if dist[best] <= FILL_REACH:
            break
        x, y = best % N, best // N
        v = src[best]
        filled.append([x, y, 10, 10, v, 'fill'])
        spread([(x, y, 10, 10, v, 'fill')])

    # 3. the spots
    def room_of(x, y):
        inside = [r for r in rooms if r[0] <= x <= r[2] and r[1] <= y <= r[3]]
        pool = inside or rooms
        return min(pool, key=lambda r: ((r[0] + r[2]) / 2 - x) ** 2 + ((r[1] + r[3]) / 2 - y) ** 2)

    def in_room(r, x, y):
        return r[0] <= x <= r[2] and r[1] <= y <= r[3]

    def grid(r, n):
        """Up to n points across a room, each with 5 m of free ground all round, the middle ones first."""
        m = 12
        k = 1
        while k * k < n:
            k += 1
        pts = []
        for j in range(k):
            for i in range(k):
                x = int(round(r[0] + m + (i + 0.5) * (r[2] - r[0] - 2 * m) / k))
                y = int(round(r[1] + m + (j + 0.5) * (r[3] - r[1] - 2 * m) / k))
                if not clear(y * N + x, 5):
                    nn = nudge(x, y, 6, 5)
                    if nn is None:
                        continue
                    x, y = nn
                pts.append((x, y))
        cx, cy = (r[0] + r[2]) / 2, (r[1] + r[3]) / 2
        pts.sort(key=lambda p: (p[0] - cx) ** 2 + (p[1] - cy) ** 2)
        assert pts, r
        return pts

    live = dump + filled
    spot_lines = []
    spot_rows = []
    lv = group_levels()
    taken = set()
    for name, colour, centres, groups in SPOTS:
        srooms = [room_of(x, y) for x, y in centres]
        before = collections.Counter()
        mine_all = []
        per_room = []
        for r in srooms:
            mine = [p for p in live if in_room(r, p[0], p[1]) and id(p) not in taken]
            for p in mine:
                taken.add(id(p))
                before[p[4]] += 1
            per_room.append((r, mine))
            mine_all += mine
        common = collections.Counter(p[4] for p in mine_all).most_common(1)[0][0] if mine_all else 2409
        for r, mine in per_room:
            n = max(MIN_PER_ROOM, len(mine))
            if groups is None:
                vs = [p[4] for p in mine] + [common] * (n - len(mine))
            else:
                vs = [groups[i % len(groups)] for i in range(n)]
            pts = grid(r, n)
            for i, v in enumerate(vs):
                x, y = pts[i % len(pts)]
                spot_lines.append([x, y, 10, 10, v, 'spot'])
        after = collections.Counter(p[4] for p in spot_lines if any(in_room(r, p[0], p[1]) for r in srooms))
        levels = sorted(l for v, c in after.items() for _ in range(c) for l in lv.get(v, []))
        median = levels[len(levels) // 2] if levels else 0
        spot_rows.append((name, colour, srooms, before, after, median))
    final = [p for p in live if id(p) not in taken] + spot_lines
    for p in final:
        assert main_[p[1] * N + p[0]], p

    dist = [INF] * (N * N)
    spread(final)
    unc_final = uncovered_count()

    os.makedirs(OUT, exist_ok=True)
    old = os.path.join(OUT, 'regen.grota2.txt')
    if os.path.exists(old):
        os.remove(old)
    with open(os.path.join(OUT, 'regen.txt'), 'w', newline='\r\n') as f:
        f.write('//MT2009_PLUS_GROTA2_REGEN_V2 (tools/grota2/gen_grota2.py, GENERATED): the global dump %d lines, '
                'fill %d, the spots of the global map %d (%d lines out)\n' % (
                    len(dump), len(filled), len(spot_lines), len(taken)))
        f.write('//type\tcx\tcy\tsx\tsy\tz\tdir\ttime\tpercent\tcount\tvnum\n')
        for x, y, sx, sy, v, o in sorted(final, key=lambda p: (p[1] // 50, p[0], p[1], p[4])):
            f.write('r\t%d\t%d\t%d\t%d\t0\t0\t%s\t100\t1\t%d\n' % (x, y, sx, sy, TIME, v))

    ours_boss = [(int(p[1]), int(p[2])) for p in lines(os.path.join(BASE, 'boss.txt')) if p[0] == 'm']
    boss_add = []
    for p in lines(os.path.join(NEWER, 'boss.txt')):
        if p[0] != 'm' or p[10] != '2491':
            continue
        x, y = int(p[1]), int(p[2])
        if any(abs(x - bx) <= 15 and abs(y - by) <= 15 for bx, by in ours_boss):
            continue
        if not main_[y * N + x]:
            m = nudge(x, y, MOVE_MAX)
            if m is None:
                report.append('  boss %d,%d left out (BLOCK)' % (x, y))
                continue
            x, y = m
        boss_add.append((x, y))
    with open(os.path.join(OUT, 'boss.grota2.txt'), 'w', newline='\r\n') as f:
        for x, y in boss_add:
            f.write('m\t%d\t%d\t10\t10\t0\t0\t%s\t100\t1\t2491\n' % (x, y, BOSS_TIME))

    walk_main = sum(main_)
    hdr = []
    hdr.append('MT2009_PLUS_GROTA2_REGEN_V2 - Grota Wygnancow V2 (73, %s)' % MAP)
    hdr.append('main walkable piece %d m2; uncovered = more than %d m of walking from a spawn centre (fill: %d m)' % (
        walk_main, REACH, FILL_REACH))
    hdr.append('package: %d live r lines, uncovered %d m2 (%.0f%%)' % (len(pkg), unc_pkg, 100.0 * unc_pkg / walk_main))
    hdr.append('global dump: %d lines (%d moved off BLOCK, %d left out), uncovered %d m2 (%.0f%%)' % (
        len(dump), moved, len(dropped), unc_dump, 100.0 * unc_dump / walk_main))
    hdr.append('fill: %d points %s' % (len(filled), dict(collections.Counter(p[4] for p in filled))))
    hdr.append('final: %d lines %s, uncovered %d m2 (%.1f%%)' % (
        len(final), dict(sorted(collections.Counter(p[4] for p in final).items())), unc_final,
        100.0 * unc_final / walk_main))
    hdr.append('bosses 2491 added: %s' % boss_add)
    hdr.append('')
    hdr.append('spots (rooms x0-x1/y0-y1; group_group: lines before -> after; the median level of the monsters):')
    hubs = []
    for name, colour, srooms, before, after, median in spot_rows:
        hdr.append('  %-22s %-6s %s' % (name, colour, ' '.join('%d-%d/%d-%d' % (r[0], r[2], r[1], r[3]) for r in srooms)))
        hdr.append('      %s -> %s, median %d' % (dict(sorted(before.items())), dict(sorted(after.items())), median))
        for r in srooms:
            cx, cy = (r[0] + r[2]) // 2, (r[1] + r[3]) // 2
            if not clear(cy * N + cx, 5):
                cx, cy = nudge(cx, cy, 10, 5)
            hubs.append((BASE_X + cx * 100, BASE_Y + cy * 100, median - 3, name))
    hdr.append('')
    hdr.append('bots (grottoV2Hubs, a spot room\'s middle with 5 m free all round; the band = the median less three):')
    for x, y, m, name in hubs:
        hdr.append('  { %7d, %7d, %d, 255, false, 0 },\t// %s' % (x, y, m, name))
    for x, y, v in dropped:
        report.append('  left out %d,%d %d (BLOCK, nothing free within %d m)' % (x, y, v, MOVE_MAX))
    for x, y, sx, sy, v, o in filled:
        report.append('  + fill %d,%d group_group %d' % (x, y, v))
    with open(os.path.join(OUT, 'gen_report.txt'), 'w') as f:
        f.write('\n'.join(hdr + report) + '\n')
    print('\n'.join(hdr))

    if a.png:
        write_png(a.png, walk, main_, final, ours_boss + boss_add, REACH)


COLOURS = {2408: (150, 255, 150), 2409: (0, 160, 0), 2411: (0, 220, 255), 2412: (60, 90, 255),
           2413: (255, 150, 0), 2414: (255, 0, 0)}


def write_png(path, walk, main_, final, bosses, reach):
    # 2 m a pixel: black = BLOCK, grey = walkable, dark red = > reach m from any spawn; spawns by group_group
    S = 2
    n = N // S
    INF = 1 << 30
    d = [INF] * (N * N)
    dq = collections.deque()
    for p in final:
        i = p[1] * N + p[0]
        if main_[i]:
            d[i] = 0
            dq.append(i)
    while dq:
        i = dq.popleft()
        for j in neighbours(i):
            if main_[j] and d[j] > d[i] + 1:
                d[j] = d[i] + 1
                dq.append(j)
    img = [[(0, 0, 0)] * n for _ in range(n)]
    for yy in range(n):
        for xx in range(n):
            i = (yy * S) * N + xx * S
            if main_[i]:
                img[yy][xx] = (120, 40, 40) if d[i] > reach else (90, 90, 90)
            elif walk[i]:
                img[yy][xx] = (40, 40, 40)
    for p in final:
        c = COLOURS.get(p[4], (255, 255, 0))
        for dy in (-1, 0, 1):
            for dx in (-1, 0, 1):
                xx, yy = p[0] // S + dx, p[1] // S + dy
                if 0 <= xx < n and 0 <= yy < n:
                    img[yy][xx] = c
    for x, y in bosses:
        for dy in range(-3, 4):
            for dx in range(-3, 4):
                xx, yy = x // S + dx, y // S + dy
                if 0 <= xx < n and 0 <= yy < n:
                    img[yy][xx] = (230, 0, 230)
    raw = bytearray()
    for yy in range(n):
        raw.append(0)
        for c in img[yy]:
            raw.extend(c)

    def chunk(t, data):
        c = struct.pack('>I', len(data)) + t + data
        return c + struct.pack('>I', zlib.crc32(t + data) & 0xffffffff)
    png = b'\x89PNG\r\n\x1a\n' + chunk(b'IHDR', struct.pack('>IIBBBBB', n, n, 8, 2, 0, 0, 0)) + \
        chunk(b'IDAT', zlib.compress(bytes(raw), 9)) + chunk(b'IEND', b'')
    open(path, 'wb').write(png)


if __name__ == '__main__':
    main()
