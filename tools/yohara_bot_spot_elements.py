#!/usr/bin/env python3
"""yohara_bot_spot_elements.py - the element mix of every Sung Ma spot for the bots (MT2009_PLUS_BOT_YSPOT_ELEMENT_V1,
playerbot_yohara_spot_element.h, the tables PLAYERBOT_YSPOT_MIX_<map>; the owner, 7 November 2026: "niech bot wybiera
takie expowisko na mapie, pod jaki zywiol jest ubrany").

    yohara_bot_spot_elements.py <playerbot_yohara_sungma.h> <spawn maps dir> <game data dir> <mob.tsv> [radius] [out.inc]

<spawn maps dir>: the test world's spawns (rates-spool spawns/base/maps: <map>/Setting.txt, <map>/regen.txt);
<game data dir>: linux-port/docker/game (its */group*.txt and */group_group*.txt); <mob.tsv>: world.mob_proto as
"vnum rank type level setRaceFlag+0 ai_flag+0 name" (mariadb -N -B). For each hub of PLAYERBOT_SUNGMA_HUBS_<map>
(boss rows left empty): the ordinary monsters (type 0, rank under 4) of the spawn lines within <radius> (default
3000, a square) of it - a group_group's groups averaged, the line's count - by their element mask (setRaceFlag bits
11-16: lightning (the set's SAVAGE), fire, ice, wind (ATT_TEMPLE), earth, dark). Prints the report; writes the C++ rows.
One-shot analysis, not part of the build."""
import sys, re, os, collections, glob

if len(sys.argv) < 5:
    sys.exit(__doc__)
HDR, SPOOL, GAME, MOBTSV = sys.argv[1:5]
RADIUS = int(sys.argv[5]) if len(sys.argv) > 5 else 3000
OUT = sys.argv[6] if len(sys.argv) > 6 else None
MAPS = [(374, 'metin2_map_empirecastle'), (373, 'metin2_map_eastplain_01'), (376, 'metin2_map_eastplain_02'),
        (377, 'metin2_map_eastplain_03'), (385, 'metin2_map_snakevalley'), (388, 'metin2_map_icecrystalcave'),
        (389, 'metin2_map_whitdragonvalley'), (393, 'metin2_map_whitedragoncave_01'), (394, 'metin2_map_whitedragoncave_02')]
EL = ['lightning', 'fire', 'ice', 'wind', 'earth', 'dark']

mob = {}
for l in open(MOBTSV, errors='replace'):
    p = l.rstrip('\n').split('\t')
    if len(p) >= 6 and p[0].isdigit():
        mob[int(p[0])] = dict(rank=int(p[1]), type=int(p[2]), level=int(p[3]), race=int(p[4]), name=p[6] if len(p) > 6 else '')


def mask(v):
    m = mob.get(v)
    return 0 if not m else (m['race'] >> 11) & 0x3f


def groups(paths, gg):
    out = {}
    cur = None
    for path in paths:
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
                cur.append(int(p[1]) if gg else int(p[-1]))
    return out


G = groups(sorted(glob.glob(GAME + '/*/group.*.txt')) + sorted(glob.glob(GAME + '/*/group.txt')), False)
GG = groups(sorted(glob.glob(GAME + '/*/group_group.*.txt')), True)
missing = collections.Counter()


def members(kind, vnum):
    """list of (vnum, weight)"""
    if kind == 'm':
        return [(vnum, 1.0)]
    if kind == 'g':
        if vnum not in G:
            missing[('g', vnum)] += 1
        return [(v, 1.0) for v in G.get(vnum, [])]
    if kind == 'r':
        gs = GG.get(vnum, [])
        if not gs:
            missing[('r', vnum)] += 1
        out = []
        for g in gs:
            if g not in G:
                missing[('g', g)] += 1
            out += [(v, 1.0 / len(gs)) for v in G.get(g, [])]
        return out
    return []


src = open(HDR).read()
hubs = {}
for idx, _ in MAPS:
    m = re.search(r'PLAYERBOT_SUNGMA_HUBS_%d\[\] = \{(.*?)\n\t\};' % idx, src, re.S)
    rows = re.findall(r'\{ (\d+), (\d+), (\d+), (\d+), (true|false), (\d+) \}', m.group(1))
    hubs[idx] = [(int(r[0]), int(r[1]), int(r[2]), r[4] == 'true', int(r[5])) for r in rows]

table = []
for idx, name in MAPS:
    BX = BY = 0
    for l in open(os.path.join(SPOOL, name, 'Setting.txt'), errors='replace'):
        p = l.split()
        if p and p[0] == 'BasePosition':
            BX, BY = int(p[1]), int(p[2])
    lines = []
    for l in open(os.path.join(SPOOL, name, 'regen.txt'), errors='replace'):
        p = l.split()
        if len(p) < 11 or p[0] not in ('m', 'g', 'r'):
            continue
        x, y = BX + int(p[1]) * 100, BY + int(p[2]) * 100
        cnt = max(1, int(p[9]))
        ms = []
        for v, w in members(p[0], int(p[10])):
            mm = mob.get(v)
            if not mm or mm['type'] != 0 or mm['rank'] >= 4:
                continue
            ms.append((v, w * cnt))
        lines.append((x, y, ms))
    mapmix = collections.Counter()
    for x, y, ms in lines:
        for v, w in ms:
            mapmix[mask(v)] += w
    rows = []
    for i, (hx, hy, lv, party, boss) in enumerate(hubs[idx]):
        if boss:
            rows.append(None)
            continue
        mix = collections.Counter()
        names = collections.Counter()
        for x, y, ms in lines:
            if abs(x - hx) <= RADIUS and abs(y - hy) <= RADIUS:
                for v, w in ms:
                    mix[mask(v)] += w
                    names[v] += w
        rows.append((hx, hy, mix, names))
    table.append((idx, name, rows, mapmix))


def fmt(mix):
    tot = sum(mix.values())
    if not tot:
        return 'none'
    parts = []
    for m, w in sorted(mix.items(), key=lambda kv: -kv[1]):
        nm = '+'.join(EL[b] for b in range(6) if m >> b & 1) or 'neutral'
        parts.append('%s %d' % (nm, round(100 * w / tot)))
    return ', '.join(parts)


for idx, name, rows, mapmix in table:
    print('== %d %s  map: %s' % (idx, name, fmt(mapmix)))
    for i, r in enumerate(rows):
        if r is None:
            continue
        hx, hy, mix, names = r
        print('  hub %2d (%d,%d) n=%.0f: %s   | %s' % (i, hx, hy, sum(mix.values()), fmt(mix),
              ', '.join('%d' % v for v, _ in names.most_common(4))))
print('missing groups:', dict(missing))

# the C++ rows: per hub up to 4 (mask, percent) pairs
if OUT:
    out = []
    for idx, name, rows, mapmix in table:
        out.append('\t// map %d (%s): the whole map %s' % (idx, name, fmt(mapmix)))
        out.append('\tconst TPlayerBotYSpotMix PLAYERBOT_YSPOT_MIX_%d[] = {' % idx)
        for i, r in enumerate(rows):
            if r is None:
                out.append('\t\t{ 0, 0, { { 0, 0 }, { 0, 0 }, { 0, 0 }, { 0, 0 } } },\t// %d: a boss' % i)
                continue
            hx, hy, mix, names = r
            tot = sum(mix.values())
            pairs = sorted(mix.items(), key=lambda kv: -kv[1])[:4]
            pct = [round(100 * w / tot) if tot else 0 for m, w in pairs]
            if tot and pct:
                pct[0] += 100 - sum(round(100 * w / tot) for m, w in sorted(mix.items(), key=lambda kv: -kv[1]))
            cells = ['{ %d, %d }' % (m, p) for (m, w), p in zip(pairs, pct)]
            while len(cells) < 4:
                cells.append('{ 0, 0 }')
            out.append('\t\t{ %d, %d, { %s } },\t// %d: %s' % (hx, hy, ', '.join(cells), i, fmt(mix)))
        out.append('\t};')
    open(OUT, 'w').write('\n'.join(out) + '\n')
