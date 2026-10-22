#!/usr/bin/env python3
"""yohara_bot_sungma_map.py - the Sung Ma maps' knowledge for the bots (MT2009_PLUS_BOT_YOHARA_MAPS_V1,
playerbot_yohara_bots.h, the table PLAYERBOT_SUNGMA_MAPS and the hubs PLAYERBOT_SUNGMA_HUBS_<map>).

The owner, 22 October 2026: "Przygotuj 100 botow z takim EQ jak do Hydry i wpusc je na mapy Yohary ... naucz je,
jak sie po nich poruszac, jakie sa mapy, na jakich poziomach Czempiona maja byc na jakich mapach, jakie statystyki
musza miec na kazda mape."

    yohara_bot_sungma_map.py <workdir> <mob.tsv> [out.inc]

<workdir> holds, for each Sung Ma map open to the bots, a directory named as the map (metin2_map_<name>/) with the
map's own files of the running world (share/locale/poland/map/<name>/: Setting.txt, Town.txt, npc.txt, regen.txt,
boss.txt, stone.txt) and its grid.bin (tools/arezzo_bot_map.py decode <server_attr> <grid.bin>, in the m2pack-lzo
image), and group.txt / group_group.txt of the locale. <mob.tsv>: "vnum level rank type max_hp name" (player.mob_proto).

On each map, on a 100-unit grid (a cell is blocked when any of its four 50-unit cells carries ATTR_BLOCK or
ATTR_OBJECT, as the bots' navigation reads them):
  * the arrival: Town.txt (the players' landing by the portal from the map before), snapped to open ground of the
    largest walkable piece;
  * the portals (npc.txt 10127-10225, the WARP monsters): each snapped beside itself - the bot walks to the one of
    the map it moves to before the warp (playerbot_yohara_bots.h, "the walk to the portal");
  * the hunting spots: the regen's spawn lines (m a monster, g a group of group.txt, r a group_group.txt's groups) clustered as arezzo_bot_map.py does (the densest CLUSTER window first, SPACING apart, snapped with
    SNAP_CLEAR open cells all round in the main piece), each with its monsters' levels and health;
  * a spot's floor in Champion levels: the map's band floor (BANDS), plus one level for every level its strongest
    ordinary monster stands over the map's weakest, plus two when its monsters carry 1.5 times the map's median
    health - at most the band's top; the two spots nearest the arrival keep the floor (a bot starts there);
  * the bosses (boss.txt): a row for a party (the boss's race; the bots' raid rule: a boss hub is a place while the
    boss stands).

MT2009_PLUS_BOT_YOHARA_MAPS_V2 (22 October, evening - the deaths on the higher maps):
  * a spot of PARTY_LINES spawn lines or more, on a map whose monsters stand at PARTY_MIN_LEVEL or over (Schronienie:
    124-125, four to a line, every one aggressive - 40-60 monsters round a spot), is a party's of three (the hub's
    party column; the lone bots' hub choice leaves it out). Yilad's dense spots (122-123) stay open: 1 of its 25 deaths
    of 22 October came while hunting, 24 on the walk to the portal;
  * the map's safe point (the revival's "restart in town", playerbot_yohara_sungma.h): the open ground of the arrival's
    piece within SAFE_RADIUS of it farthest from any spawn (regen, stone, boss; counted to SAFE_ENOUGH), the nearest to
    the arrival among equals - Zejscie's arrival stands 1 856 from a pack of four aggressive soldiers, Namgan's 2 815.

The rows' level columns hold 100 + the Champion level (TPlayerBotHuntingHub's BYTE; the hub choice compares them with
100 + the bot's Champion level on a Sung Ma map - PlayerBotHubLevel in playerbot_wandering.h).
One-shot analysis, not part of the build; the report goes to stdout.
"""
import sys, struct, math, os, collections
from array import array
from collections import deque

if len(sys.argv) < 3:
    sys.exit(__doc__)
WORK = sys.argv[1].rstrip('/')
MOB = sys.argv[2]
OUT = sys.argv[3] if len(sys.argv) > 3 else None

# map index, name, the Champion band (plan-boty-yohara.md 5.4 - the owner's plan of 21 October)
MAPS = [
    (374, 'metin2_map_empirecastle', 1, 5),
    (373, 'metin2_map_eastplain_01', 3, 10),
    (376, 'metin2_map_eastplain_02', 6, 12),
    (377, 'metin2_map_eastplain_03', 8, 15),
    (385, 'metin2_map_snakevalley', 12, 20),
    (388, 'metin2_map_icecrystalcave', 15, 22),
    (389, 'metin2_map_whitdragonvalley', 18, 25),
    (393, 'metin2_map_whitedragoncave_01', 22, 30),
    (394, 'metin2_map_whitedragoncave_02', 26, 30),
]
BLOCK = 0x81
WATER = 0x02
CLUSTER = 3600
SPACING = 5000
MAX_SPOTS = 20
SNAP_CLEAR = 5
CAP = 8
MAX_BOSSES = 4
CHAMBER_MIN = 1500
PARTY_LINES = 13        # MT2009_PLUS_BOT_YOHARA_MAPS_V2
PARTY_MIN_LEVEL = 124
SAFE_RADIUS = 100       # cells of 100 units
SAFE_ENOUGH = 6000

mob = {}
for l in open(MOB, errors='replace'):
    p = l.rstrip('\n').split('\t')
    if len(p) >= 5 and p[0].isdigit():
        mob[int(p[0])] = dict(level=int(p[1]), rank=int(p[2]), type=int(p[3]), hp=int(p[4]), name=p[5] if len(p) > 5 else '')


def groups(path):
    out = {}
    cur = None
    for l in open(path, errors='replace'):
        p = l.split()
        if not p:
            continue
        if p[0] == 'Group':
            cur = []
        elif p[0] == 'Vnum' and cur is not None:
            out[int(p[1])] = cur
        elif p[0] == 'Leader' and cur is not None:
            cur.append(int(p[-1]))
        elif p[0].isdigit() and cur is not None and len(p) >= 2:
            # group.txt: "<n> <name> <vnum>"; group_group.txt: "<n> <group vnum> <prob>"
            cur.append(int(p[-1]) if not path.endswith('group_group.txt') else int(p[1]))
    return out


G = groups(os.path.join(WORK, 'group.txt'))
GG = groups(os.path.join(WORK, 'group_group.txt'))


def members(kind, vnum):
    if kind == 'm':
        return [vnum]
    if kind == 'g':
        return G.get(vnum, [])
    if kind == 'r':	# a group_group: one of its groups at random
        out = []
        for g in GG.get(vnum, []):
            out += G.get(g, [])
        return out
    return []


o = []
o.append('\t// tools/yohara_bot_sungma_map.py (22 October 2026, MT2009_PLUS_BOT_YOHARA_MAPS_V2), the test world\'s map files - PLAYERBOT_SUNGMA_HUBS_<map>:')
o.append('\t// x, y, 100 + the Champion floor, 255, a party\'s, the boss\'s race.')
summary = []
for idx, name, lo, hi in MAPS:
    D = os.path.join(WORK, name)

    def rd(fn):
        try:
            return [l.split() for l in open(os.path.join(D, fn), errors='replace') if l.strip() and not l.startswith('//')]
        except FileNotFoundError:
            return []
    BX = BY = None
    for p in rd('Setting.txt'):
        if p[0] == 'BasePosition':
            BX, BY = int(p[1]), int(p[2])
    d = open(os.path.join(D, 'grid.bin'), 'rb').read()
    FW, FH = struct.unpack_from('<ii', d)
    fg = d[8:]
    W, H = FW // 2, FH // 2
    N = W * H
    blk = bytearray(N)
    for y in range(H):
        r0 = (2 * y) * FW
        r1 = r0 + FW
        for x in range(W):
            if (fg[r0 + 2 * x] | fg[r0 + 2 * x + 1] | fg[r1 + 2 * x] | fg[r1 + 2 * x + 1]) & BLOCK:
                blk[y * W + x] = 1
    clr = bytearray([CAP]) * N
    q = deque()
    for i in range(N):
        x, y = i % W, i // W
        if blk[i]:
            clr[i] = 0
            q.append(i)
        elif x == 0 or y == 0 or x == W - 1 or y == H - 1:
            clr[i] = 1
            q.append(i)
    while q:
        j = q.popleft()
        x, y = j % W, j // W
        c = clr[j]
        if c >= CAP:
            continue
        for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            X, Y = x + dx, y + dy
            if 0 <= X < W and 0 <= Y < H:
                k = Y * W + X
                if clr[k] > c + 1:
                    clr[k] = c + 1
                    q.append(k)
    comp = array('i', [0]) * N
    sizes = [0]
    for s in range(N):
        if blk[s] or comp[s]:
            continue
        cid = len(sizes)
        comp[s] = cid
        n = 0
        st = [s]
        while st:
            j = st.pop()
            n += 1
            x, y = j % W, j // W
            for dx in (-1, 0, 1):
                for dy in (-1, 0, 1):
                    if not dx and not dy:
                        continue
                    X, Y = x + dx, y + dy
                    if 0 <= X < W and 0 <= Y < H:
                        k = Y * W + X
                        if blk[k] or comp[k]:
                            continue
                        if dx and dy and (blk[y * W + X] or blk[Y * W + x]):
                            continue
                        comp[k] = cid
                        st.append(k)
        sizes.append(n)
    main = max(range(1, len(sizes)), key=lambda c: sizes[c])

    def w2c(wx, wy):
        return ((wx - BX) // 100, (wy - BY) // 100)

    def c2w(cx, cy):
        return (BX + cx * 100 + 50, BY + cy * 100 + 50)

    def snap(cx, cy, minclr, want=None, r=40):
        best = None
        for dy in range(-r, r + 1):
            for dx in range(-r, r + 1):
                X, Y = cx + dx, cy + dy
                if 0 <= X < W and 0 <= Y < H:
                    k = Y * W + X
                    if clr[k] >= minclr and (want is None or comp[k] == want):
                        dd = dx * dx + dy * dy
                        if best is None or dd < best[0]:
                            best = (dd, X, Y)
        return (best[1], best[2]) if best else None
    town = [(int(p[0]), int(p[1])) for p in rd('Town.txt')][0]
    tc = w2c(BX + town[0] * 100, BY + town[1] * 100)
    arr = snap(tc[0], tc[1], 4, main) or snap(tc[0], tc[1], 2, main, 80) or snap(tc[0], tc[1], 1, None, 120)
    if not arr:
        sys.exit('map %d: no open ground near its Town.txt %s' % (idx, town))
    if comp[arr[1] * W + arr[0]] != main:
        # the landing stands in a piece of its own (a cave's first chamber): that piece is the bots' map
        main = comp[arr[1] * W + arr[0]]
        arr = snap(tc[0], tc[1], 3, main, 80) or arr
    portals = []
    for p in rd('npc.txt'):
        if p[0] == 'm' and len(p) >= 11 and 10127 <= int(p[-1]) <= 10225:
            c = snap(*w2c(BX + int(p[1]) * 100, BY + int(p[2]) * 100), 3, main, 30)
            portals.append((int(p[-1]), int(p[1]), int(p[2]), c2w(*c) if c else None))
    # the spawn lines: world point, members
    lines = []
    for p in rd('regen.txt'):
        if len(p) < 11 or p[0] not in ('m', 'r', 'g'):
            continue
        ms = [v for v in members(p[0], int(p[-1])) if v in mob and mob[v]['type'] == 0 and mob[v]['rank'] < 4]
        if not ms:
            continue
        lines.append((BX + int(p[1]) * 100, BY + int(p[2]) * 100, ms))
    # A map built in chambers the terrain does not join (Zejscie Polnocnego Wiatru: its rooms joined by the portals
    # 10203-10225 only): every piece of CHAMBER_MIN cells is ground - the bot hunts the room it stands in and the
    # cores move it between the rooms (the chamber hop, playerbot_yohara_bots.h).
    walkable = sum(1 for i in range(N) if not blk[i])
    chambered = sizes[main] * 2 < walkable
    pieces = set(c for c in range(1, len(sizes)) if sizes[c] >= CHAMBER_MIN) if chambered else {main}

    def piece_of(wx, wy):
        c = w2c(wx, wy)
        for want in pieces:
            if snap(c[0], c[1], 1, want, 12):
                return want
        return 0
    lost = 0
    keep = []
    for ln in lines:
        pc = piece_of(ln[0], ln[1])
        if pc:
            keep.append(ln + (pc,))
        else:
            lost += 1
    lvls = sorted(mob[v]['level'] for ln in keep for v in ln[2])
    hps = sorted(mob[v]['hp'] for ln in keep for v in ln[2])
    lvmin = lvls[0] if lvls else 120
    hpmed = hps[len(hps) // 2] if hps else 1
    rem = list(keep)
    hubs = []
    while rem and len(hubs) < MAX_SPOTS:
        best = None
        for sx, sy, _, _ in rem:
            n = sum(1 for tx, ty, _, _ in rem if abs(tx - sx) < CLUSTER and abs(ty - sy) < CLUSTER)
            if best is None or n > best[0]:
                best = (n, sx, sy)
        n, sx, sy = best
        if n < 3:
            break
        near = [r for r in rem if abs(r[0] - sx) < CLUSTER and abs(r[1] - sy) < CLUSTER]
        mx = sum(r[0] for r in near) // len(near)
        my = sum(r[1] for r in near) // len(near)
        pc = collections.Counter(r[3] for r in near).most_common(1)[0][0]
        c = snap(*w2c(mx, my), SNAP_CLEAR, pc) or snap(*w2c(mx, my), 3, pc) or snap(*w2c(mx, my), 2, pc)
        if c:
            hx, hy = c2w(*c)
            if all(math.hypot(hx - h['x'], hy - h['y']) >= SPACING for h in hubs):
                vs = [v for r in near for v in r[2]]
                top = max(mob[v]['level'] for v in vs)
                hp = sorted(mob[v]['hp'] for v in vs)[len(vs) // 2]
                hubs.append(dict(x=hx, y=hy, n=n, top=top, hp=hp,
                                 mobs=collections.Counter(v for r in near for v in r[2]).most_common(2)))
        rem = [r for r in rem if not (abs(r[0] - sx) < CLUSTER + 400 and abs(r[1] - sy) < CLUSTER + 400)]
    ax, ay = c2w(*arr)
    hubs.sort(key=lambda h: math.hypot(h['x'] - ax, h['y'] - ay))
    for i, h in enumerate(hubs):
        f = lo + max(0, h['top'] - lvmin) + (2 if h['hp'] * 2 >= hpmed * 3 else 0)
        h['floor'] = lo if i < 2 else min(hi, f)
        # MT2009_PLUS_BOT_YOHARA_MAPS_V2: the densest of the strong maps - a party's
        h['party'] = h['n'] >= PARTY_LINES and lvmin >= PARTY_MIN_LEVEL
    # MT2009_PLUS_BOT_YOHARA_MAPS_V2: the safe point by the arrival
    spawns = [(BX + int(p[1]) * 100, BY + int(p[2]) * 100) for fn in ('regen.txt', 'stone.txt', 'boss.txt')
              for p in rd(fn) if len(p) >= 11 and p[0] in ('m', 'g', 'r', 's')]
    seen = {arr}
    q = deque([arr])
    safe = None
    while q:
        cx, cy = q.popleft()
        if clr[cy * W + cx] >= 3:
            wx, wy = c2w(cx, cy)
            md = min((math.hypot(wx - a, wy - b) for a, b in spawns), default=99999)
            key = (min(md, SAFE_ENOUGH) // 250, -math.hypot(wx - ax, wy - ay))
            if safe is None or key > safe[0]:
                safe = (key, wx, wy, int(md))
        for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            X, Y = cx + dx, cy + dy
            if (X, Y) not in seen and abs(X - arr[0]) <= SAFE_RADIUS and abs(Y - arr[1]) <= SAFE_RADIUS and \
                    0 <= X < W and 0 <= Y < H and not blk[Y * W + X]:
                seen.add((X, Y))
                q.append((X, Y))
    amd = int(min((math.hypot(ax - a, ay - b) for a, b in spawns), default=99999))
    bosses = []
    for p in rd('boss.txt'):
        if len(p) < 11:
            continue
        ms = [v for v in members(p[0], int(p[-1])) if v in mob]
        lead = max(ms, key=lambda v: (mob[v]['rank'], mob[v]['hp'])) if ms else 0
        if not lead:
            continue
        c = snap(*w2c(BX + int(p[1]) * 100, BY + int(p[2]) * 100), 3, None if chambered else main, 20)
        # at most MAX_BOSSES points a map, 3 000 apart (Schronienie's War Chiefs stand at twelve of the sheet's points)
        if c and len(bosses) < MAX_BOSSES and all(math.hypot(c2w(*c)[0] - b[0][0], c2w(*c)[1] - b[0][1]) >= 3000 for b in bosses):
            bosses.append((c2w(*c), lead))
    if chambered:
        print('map %d: chambered - %d pieces of %d+ cells' % (idx, len(pieces), CHAMBER_MIN))
    print('map %d %s base (%d,%d) grid %dx%d main %d cells; regen lines %d (outside the main piece %d); monsters %d-%d, '
          'median health %d; band %d-%d' % (idx, name, BX, BY, W, H, sizes[main], len(lines), lost, lvmin, lvls[-1] if lvls else 0,
                                           hpmed, lo, hi))
    print('  arrival (Town %d,%d) -> (%d,%d), nearest spawn %d; safe point (%d,%d), nearest spawn %d' % (
        town[0], town[1], ax, ay, amd, safe[1], safe[2], safe[3]))
    for pv, px, py, pw in portals:
        print('  portal %d at %d,%d -> %s' % (pv, px, py, pw))
    o.append('\t// map %d (%s): arrival (%d, %d); monsters %d-%d; band %d-%d; %d spots, %d bosses' % (
        idx, name, ax, ay, lvmin, lvls[-1] if lvls else 0, lo, hi, len(hubs), len(bosses)))
    o.append('\tconst TPlayerBotHuntingHub PLAYERBOT_SUNGMA_HUBS_%d[] = {' % idx)
    for h in hubs:
        ms = ', '.join('%d %s' % (v, mob[v]['name']) for v, _ in h['mobs'])
        print('  spot (%d,%d) lines %d top %d hp %d floor %d%s  %s' % (h['x'], h['y'], h['n'], h['top'], h['hp'], h['floor'],
                                                                     ' party' if h['party'] else '', ms))
        o.append('\t\t{ %d, %d, %d, 255, %s, 0 },\t// %d lines, to %d, %dk HP: %s%s' % (
            h['x'], h['y'], 100 + h['floor'], 'true' if h['party'] else 'false', h['n'], h['top'], h['hp'] // 1000, ms,
            ' (V2: a party\'s - dense)' if h['party'] else ''))
    for (bx, by), v in bosses:
        print('  boss %d %s (%d,%d) level %d hp %d' % (v, mob[v]['name'], bx, by, mob[v]['level'], mob[v]['hp']))
        o.append('\t\t{ %d, %d, %d, 255, true, %d },\t// boss %s, %d, %dk HP' % (
            bx, by, 100 + min(hi, lo + 2), v, mob[v]['name'], mob[v]['level'], mob[v]['hp'] // 1000))
    o.append('\t};')
    summary.append((idx, ax, ay, portals, safe[1], safe[2], safe[3], amd))
if OUT:
    o.append('\t// arrivals and portals (cell centres beside them):')
    for idx, ax, ay, portals, _, _, _, _ in summary:
        o.append('\t//   %d arrival (%d, %d); portals %s' % (idx, ax, ay, ', '.join(
            '%d (%d, %d)' % (pv, pw[0], pw[1]) for pv, _, _, pw in portals if pw)))
    # MT2009_PLUS_BOT_YOHARA_MAPS_V2: the safe points (the revival)
    o.append('\t// the safe points by the arrivals (the revival) - map, x, y; the nearest spawn from it / from the arrival:')
    o.append('\tconst TPlayerBotSungmaSafePoint PLAYERBOT_SUNGMA_SAFE_POINTS[] = {')
    for idx, ax, ay, portals, sx, sy, smd, amd in summary:
        o.append('\t\t{ %d, %d, %d },\t// %d / %d' % (idx, sx, sy, smd, amd))
    o.append('\t};')
    open(OUT, 'w').write('\n'.join(o) + '\n')
    print('written', OUT)
