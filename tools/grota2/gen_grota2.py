#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""gen_grota2.py [--png OUT.png]

MT2009_PLUS_GROTA2_REGEN_V1: Grota Wygnancow V2 (map 73, metin2_map_skipia_dungeon_02, 6x6, base 153600 1203200,
levels 85-95) had whole rooms and corridors without a single monster (the owner, 3 November 2026: "W grocie
wygnancow v2 jest bardzo duzo pustych spotow, komnat w ktorych nie ma w ogole potworow").

Why: the package's regen.txt (722 lines) is the OLD dump of the map (Owsap's europe set is the same file) and
  - 84 of them ("r ... 2410") are commented out, because our group_group.txt has no 2410 (the newer dump's
    skipia1_10: Vnum 2410 = groups 2417 + 2418, the same as 2409) - those points spawn nothing;
  - the newer dump of the same map (Owsap's uk set: 2017 lines = 708 of the old points twice + 599 points the
    old file does not have at all, 1307 places) fills most of what the old file leaves empty; its boss.txt has
    Dowodca Yonghan (2491) at five places, ours at one.
  On the map's own server_attr (one walkable piece of 733 thousand m2 plus an 9 thousand m2 island nobody reaches)
  half of the ground was more than 25 m of walking from any live spawn.

What this writes (GENERATED - edit this file, run it again):
  linux-port/docker/game/grota2/regen.grota2.txt - appended to the map's regen.txt by the Dockerfile step
      MT2009_PLUS_GROTA2_REGEN_V1, which also turns the 84 "//r ... 2410" lines into live "r ... 2409" lines
      (2410 == 2409 in the newer dump; no new group_group needed):
        1. every point of the newer dump the old file lacks, once (our file keeps each point once, the dump
           twice), its 2410 written as 2409, our 90 s (the package's own respawn here; the dump says 70 s);
           a centre on BLOCK is moved to the nearest free metre of the main piece (6 m at most, else left out);
        2. then, while some walkable metre of the main piece is more than FILL_REACH m of walking from every
           spawn, a point on the farthest such metre (with CLEAR m of free ground all round), the group_group of
           the nearest spawn by walking (so the inner Setaou 87-90 and the outer 91-97 rings stay as they are);
           not within SAFE m of the arrival and the NPCs.
  linux-port/docker/game/grota2/boss.grota2.txt - the newer dump's Dowodca Yonghan places we lack (our 20 min).
  linux-port/docker/game/grota2/gen_report.txt

Needs python-lzo for server_attr (the m2pack-lzo image has it):
  docker run --rm -v /opt/metin2:/opt/metin2 -w <worktree> m2pack-lzo python3 tools/grota2/gen_grota2.py \
      [--png /path/overview.png]
"""
import argparse
import collections
import os
import struct
import sys
import zlib

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.normpath(os.path.join(HERE, '..', '..'))
OUT = os.path.join(ROOT, 'linux-port', 'docker', 'game', 'grota2')

MAP = 'metin2_map_skipia_dungeon_02'
BASE = '/opt/metin2/mt2009plustest/linux-port/docker/game/src/serverfiles/share/locale/poland/map/' + MAP
NEWER = '/opt/metin2/cache/owsap/Server/Server/share/locale/uk/map/' + MAP
N = 1536                    # 6 x 256 m
ARRIVAL = (877, 721)        # PLAYERBOT_GROTTO_V2_ARRIVAL (241325, 1275425) and the way out 10079 at 881,726
NPCS = [(881, 726), (266, 175), (369, 294), (1003, 921)]
SAFE = 18
REACH = 25                  # the coverage the report measures
FILL_REACH = 40             # the fill: corridors stay as thin as the package keeps them
CLEAR = 2
MOVE_MAX = 6
TIME = '90s'
BOSS_TIME = '1200s'


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

    def clear(i, r):
        x, y = i % N, i // N
        if x < r or y < r or x >= N - r or y >= N - r:
            return False
        return all(main_[(y + dy) * N + x + dx] for dy in range(-r, r + 1) for dx in range(-r, r + 1))

    def nudge(x, y, r):
        best = None
        for dy in range(-r, r + 1):
            for dx in range(-r, r + 1):
                xx, yy = x + dx, y + dy
                if 0 <= xx < N and 0 <= yy < N and main_[yy * N + xx]:
                    d = dx * dx + dy * dy
                    if best is None or d < best[0]:
                        best = (d, xx, yy)
        return None if best is None else best[1:]

    base = lines(os.path.join(BASE, 'regen.txt'))
    newer = lines(os.path.join(NEWER, 'regen.txt'))
    live = []           # (x, y, vnum, origin)
    commented = 0
    for p in base:
        if p[0] == 'r':
            live.append((int(p[1]), int(p[2]), int(p[10]), 'base'))
        elif p[0] == '//r' and p[10] == '2410':
            live.append((int(p[1]), int(p[2]), 2409, '2410'))
            commented += 1
    have = set((x, y) for x, y, v, o in live)
    report = []
    restored = []
    dropped = []
    seen = set()
    for p in newer:
        if p[0] != 'r':
            continue
        x, y, v = int(p[1]), int(p[2]), int(p[10])
        if (x, y) in have or (x, y) in seen:
            continue
        seen.add((x, y))
        v = 2409 if v == 2410 else v
        if not main_[y * N + x]:
            m = nudge(x, y, MOVE_MAX)
            if m is None:
                dropped.append((x, y, v))
                continue
            report.append('  moved %d,%d -> %d,%d (BLOCK)' % (x, y, m[0], m[1]))
            x, y = m
        restored.append((x, y, v, 'newer'))
    live_all = live + restored

    # walking distance from every spawn, with the nearest spawn's group_group
    INF = 1 << 30
    dist = [INF] * (N * N)
    src = [0] * (N * N)

    def spread(pts):
        dq = collections.deque()
        for x, y, v, o in pts:
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

    spread(live_all)
    safe = set()
    for cx, cy in NPCS:
        for dy in range(-SAFE, SAFE + 1):
            for dx in range(-SAFE, SAFE + 1):
                if dx * dx + dy * dy <= SAFE * SAFE:
                    safe.add((cy + dy) * N + cx + dx)

    def uncovered_count(r=REACH):
        return sum(1 for i in range(N * N) if main_[i] and dist[i] > r)

    after_restore = uncovered_count()
    filled = []
    cand = [i for i in range(N * N) if main_[i] and i not in safe and clear(i, CLEAR)]
    while True:
        best = max(cand, key=lambda i: dist[i])
        if dist[best] <= FILL_REACH:
            break
        x, y = best % N, best // N
        v = src[best]
        filled.append((x, y, v, 'fill'))
        spread([(x, y, v, 'fill')])
    final_unc = uncovered_count()

    base_live = sum(1 for p in base if p[0] == 'r')
    os.makedirs(OUT, exist_ok=True)
    with open(os.path.join(OUT, 'regen.grota2.txt'), 'w', newline='\r\n') as f:
        f.write('// MT2009_PLUS_GROTA2_REGEN_V1 (tools/grota2/gen_grota2.py, GENERATED): the newer dump\'s points the '
                'package lacks (%d), then the rooms still empty (%d)\n' % (len(restored), len(filled)))
        for x, y, v, o in restored + filled:
            f.write('r\t%d\t%d\t10\t10\t0\t0\t%s\t100\t1\t%d\n' % (x, y, TIME, v))

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
    hdr.append('MT2009_PLUS_GROTA2_REGEN_V1 - Grota Wygnancow V2 (73, %s)' % MAP)
    hdr.append('main walkable piece %d m2; uncovered = more than %d m of walking from a spawn centre (fill: %d m)' % (
        walk_main, REACH, FILL_REACH))
    hdr.append('package: %d live r lines + %d commented 2410 (made 2409 by the Dockerfile step)' % (base_live, commented))
    unc0 = None
    # coverage of the package as it was (live lines only)
    for k in range(N * N):
        dist[k] = INF
    spread([p for p in live if p[3] == 'base'])
    unc0 = uncovered_count()
    hdr.append('uncovered before: %d m2 (%.0f%%)' % (unc0, 100.0 * unc0 / walk_main))
    hdr.append('after 2410 + the newer dump\'s %d points (%d left out on BLOCK): %d m2 (%.0f%%)' % (
        len(restored), len(dropped), after_restore, 100.0 * after_restore / walk_main))
    hdr.append('after %d fill points: %d m2 (%.1f%%)' % (len(filled), final_unc, 100.0 * final_unc / walk_main))
    hdr.append('restored by group_group: %s' % dict(collections.Counter(v for x, y, v, o in restored)))
    hdr.append('fill by group_group: %s' % dict(collections.Counter(v for x, y, v, o in filled)))
    hdr.append('bosses 2491 added: %s' % boss_add)
    for x, y, v in dropped:
        report.append('  left out %d,%d %d (BLOCK, nothing free within %d m)' % (x, y, v, MOVE_MAX))
    for x, y, v, o in filled:
        report.append('  + fill %d,%d group_group %d' % (x, y, v))
    with open(os.path.join(OUT, 'gen_report.txt'), 'w') as f:
        f.write('\n'.join(hdr + report) + '\n')
    print('\n'.join(hdr))

    if a.png:
        write_png(a.png, walk, main_, live, restored, filled, ours_boss, boss_add, REACH)


def write_png(path, walk, main_, live, restored, filled, ours_boss, boss_add, reach):
    # two panels (before | after), 2 m a pixel: black = BLOCK, grey = walkable, red = > reach m from any spawn
    S = 2
    n = N // S
    INF = 1 << 30

    def coverage(pts):
        d = [INF] * (N * N)
        dq = collections.deque()
        for x, y in pts:
            i = y * N + x
            if main_[i]:
                d[i] = 0
                dq.append(i)
        while dq:
            i = dq.popleft()
            for j in neighbours(i):
                if main_[j] and d[j] > d[i] + 1:
                    d[j] = d[i] + 1
                    dq.append(j)
        return d

    panels = []
    sets = [
        ([(x, y) for x, y, v, o in live if o == 'base'], [((x, y), (40, 200, 40)) for x, y, v, o in live if o == 'base'], ours_boss),
        ([(x, y) for x, y, v, o in live + restored + filled],
         [((x, y), (40, 200, 40) if o == 'base' else (60, 140, 255) if o in ('2410', 'newer') else (255, 220, 0))
          for x, y, v, o in live + restored + filled], ours_boss + boss_add),
    ]
    for pts, marks, bosses in sets:
        d = coverage(pts)
        img = [[(0, 0, 0)] * n for _ in range(n)]
        for yy in range(n):
            for xx in range(n):
                i = (yy * S) * N + xx * S
                if main_[i]:
                    img[yy][xx] = (200, 60, 60) if d[i] > reach else (120, 120, 120)
                elif walk[i]:
                    img[yy][xx] = (60, 60, 60)
        for (x, y), c in marks:
            for dy in (-1, 0, 1):
                for dx in (-1, 0, 1):
                    xx, yy = x // S + dx, y // S + dy
                    if 0 <= xx < n and 0 <= yy < n:
                        img[yy][xx] = c
        for x, y in bosses:
            for dy in range(-3, 4):
                for dx in range(-3, 4):
                    xx, yy = x // S + dx, y // S + dy
                    if 0 <= xx < n and 0 <= yy < n:
                        img[yy][xx] = (230, 0, 230)
        panels.append(img)
    gap = 8
    W = n * 2 + gap
    raw = bytearray()
    for yy in range(n):
        raw.append(0)
        row = panels[0][yy] + [(255, 255, 255)] * gap + panels[1][yy]
        for c in row:
            raw.extend(c)

    def chunk(t, data):
        c = struct.pack('>I', len(data)) + t + data
        return c + struct.pack('>I', zlib.crc32(t + data) & 0xffffffff)
    png = b'\x89PNG\r\n\x1a\n' + chunk(b'IHDR', struct.pack('>IIBBBBB', W, n, 8, 2, 0, 0, 0)) + \
        chunk(b'IDAT', zlib.compress(bytes(raw), 9)) + chunk(b'IEND', b'')
    open(path, 'wb').write(png)


if __name__ == '__main__':
    main()
