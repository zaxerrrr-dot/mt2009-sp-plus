#!/usr/bin/env python3
"""yohara_bot_lootrun_map.py - the 90-level maps' loot-run knowledge for the bots
(MT2009_PLUS_BOT_YOHARA_LOOTRUN_V1, playerbot_yohara_bots.h).

    yohara_bot_lootrun_map.py <mapdir> <map_index> [out.inc [group.txt]]

<mapdir> holds the map's own files: grid.bin (server_attr decoded by
tools/arezzo_bot_map.py decode, one byte per 50-unit cell), Setting.txt,
Town.txt, stone.txt, boss.txt (the final ones of the game container,
/opt/metin2/share/locale/poland/map/<name>/); group.txt (the container's
/opt/metin2/share/locale/poland/group.txt) names the leader of a boss.txt
"g" line - the boss a spot exists for is the monster, not its group.

A loot run is no hunt: the bot goes from Metin to Metin and to the bosses and
leaves the ordinary monsters alone (the owner, 21 October 2026: "mapy na 90 lvl
- tylko drop, Metiny i bossowie, bez expienia"). So the spots are not the
regen's clusters but the stone.txt and boss.txt points, each snapped to a
100-unit cell with SNAP_CLEAR open cells all round on the walkable piece of the
arrival (Town.txt), and the arrival itself snapped the same way. Points off
that piece are reported and left out. It prints a report and writes the C++
rows (playerbot_yohara_bots.h) to out.inc. One-shot analysis, not part of the
build.
"""
import sys, struct
from collections import deque

if len(sys.argv) < 3:
    sys.exit(__doc__)
D = sys.argv[1].rstrip('/'); MAPIDX = int(sys.argv[2]); OUT = sys.argv[3] if len(sys.argv) > 3 else None
GROUPS = sys.argv[4] if len(sys.argv) > 4 else None
BLOCK = 0x81      # ATTR_BLOCK | ATTR_OBJECT, as the bots' navigation reads them
SNAP_CLEAR = 3    # a spot stands with three open 100-unit cells all round
SNAP_RADIUS = 40  # looked for this many 100-unit cells round the point
MERGE = 3000      # two stone points nearer than this make one spot


def rd(name):
    try:
        return [l.split() for l in open(D + '/' + name, errors='replace') if l.strip() and not l.startswith('//')]
    except FileNotFoundError:
        return []


LEADER = {}
if GROUPS:
    import re
    for b in re.findall(r'\{(.*?)\}', open(GROUPS, encoding='cp1250', errors='replace').read(), re.S):
        L = re.search(r'Leader\s+.*?\s(\d+)\s*$', b, re.M); V = re.search(r'Vnum\s+(\d+)', b)
        if L and V:
            LEADER[int(V.group(1))] = int(L.group(1))

BX = BY = None
for f in rd('Setting.txt'):
    if f[0] == 'BasePosition':
        BX, BY = int(f[1]), int(f[2])
raw = open(D + '/grid.bin', 'rb').read()
W50, H50 = struct.unpack_from('<ii', raw, 0)
g50 = raw[8:]
W, H = W50 // 2, H50 // 2
blocked = bytearray(W * H)
for y in range(H):
    for x in range(W):
        a = (2 * y) * W50 + 2 * x
        if (g50[a] | g50[a + 1] | g50[a + W50] | g50[a + W50 + 1]) & BLOCK:
            blocked[y * W + x] = 1


def free(cx, cy):
    return 0 <= cx < W and 0 <= cy < H and not blocked[cy * W + cx]


def clear(cx, cy, r):
    for dy in range(-r, r + 1):
        for dx in range(-r, r + 1):
            if not free(cx + dx, cy + dy):
                return False
    return True


def snap(cx, cy, piece=None):
    best = None
    for r in range(0, SNAP_RADIUS + 1):
        for dy in range(-r, r + 1):
            for dx in range(-r, r + 1):
                if max(abs(dx), abs(dy)) != r:
                    continue
                x, y = cx + dx, cy + dy
                if clear(x, y, SNAP_CLEAR) and (piece is None or piece[y * W + x]):
                    d = dx * dx + dy * dy
                    if best is None or d < best[0]:
                        best = (d, x, y)
        if best:
            return best[1], best[2]
    return None


def world(cx, cy):
    return BX + cx * 100 + 50, BY + cy * 100 + 50


town = rd('Town.txt')
tcx, tcy = int(town[0][0]), int(town[0][1])
arr = snap(tcx, tcy)
if not arr:
    sys.exit('no open cell by the arrival')
piece = bytearray(W * H)
q = deque([arr]); piece[arr[1] * W + arr[0]] = 1; n = 1
while q:
    x, y = q.popleft()
    for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
        nx, ny = x + dx, y + dy
        if free(nx, ny) and not piece[ny * W + nx]:
            piece[ny * W + nx] = 1; n += 1; q.append((nx, ny))
walkable = W * H - sum(blocked)
print('map %d base (%d,%d) grid %dx%d walkable %.1f%% arrival piece %d cells (%.1f%% of walkable)' %
      (MAPIDX, BX, BY, W, H, 100.0 * walkable / (W * H), n, 100.0 * n / max(1, walkable)))
ax, ay = world(*arr)
print('arrival (Town %d,%d) -> (%d,%d)' % (tcx, tcy, ax, ay))

rows = []   # (x, y, boss, race, what)
def add(kind, f):
    cx, cy, race = int(f[1]), int(f[2]), int(f[-1])
    if kind == 'boss' and f[0] == 'g':
        if race not in LEADER:
            print('  boss group %d: no leader known (pass group.txt), left out' % race)
            return
        race = LEADER[race]
    p = snap(cx, cy, piece)
    if not p:
        print('  %s %d at cell (%d,%d): off the arrival piece, left out' % (kind, race, cx, cy))
        return
    x, y = world(*p)
    if kind == 'stone':
        for r in rows:
            if not r[2] and abs(r[0] - x) + abs(r[1] - y) < MERGE:
                return
    rows.append((x, y, kind == 'boss', race if kind == 'boss' else 0, '%s %d cell %d,%d' % (kind, race, cx, cy)))
for f in rd('boss.txt'):
    add('boss', f)
for f in rd('stone.txt'):
    add('stone', f)
print('spots %d (%d bosses)' % (len(rows), sum(1 for r in rows if r[2])))
lines = ['\t// map %d: arrival (%d, %d); %d spots - tools/yohara_bot_lootrun_map.py' % (MAPIDX, ax, ay, len(rows)),
         '\tconst TPlayerBotHuntingHub PLAYERBOT_YOHARA_LOOT_HUBS_%d[] = {' % MAPIDX]
for x, y, boss, race, what in rows:
    # bNeedsParty stays false: a loot run is one bot's (the boss hub is
    # chosen while the boss stands - wBossRace - by a bot on its own)
    lines.append('\t\t{ %d, %d, PLAYERBOT_YOHARA_LOOT_MIN_LEVEL, 255, false, %d },\t// %s' %
                 (x, y, race, what))
lines.append('\t};')
print('\n'.join(lines))
if OUT:
    open(OUT, 'w').write('\n'.join(lines) + '\n')
    print('written', OUT)
