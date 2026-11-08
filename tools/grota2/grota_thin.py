#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""grota_thin.py - MT2009_PLUS_GROTA_THIN_V1 (8 November 2026): the Grotto of Exile's spots less 30%.

The owner, 8 November 2026: "Grota Wygnancow V1 i V2 - zmniejszyc spoty o 30% od tego co jest teraz".
Used by tools/grota2/gen_grota2.py (V2, its final lines) and tools/grota1/gen_grota1.py (V1, the package's lines).

thin(points, frac, cell): points are sequences whose [0], [1] are the centre in metres (the regen's cx, cy).
Evenly across the map, not a corner: the map is cut into CELL x CELL m squares walked row by row (a serpentine),
and every square gives up its share of the lines - the running total rounded, so the whole is exactly
round(len * frac) and no square loses more than its share plus one. Within a square the line taken out is the
most redundant one left - the nearest to another line still standing (anywhere, the next square too); the
global dump's twin points (one centre written twice) go first, so a room keeps its ground covered and only
gets thinner. Deterministic (ties: the lower y, x, group).
"""

CELL = 64


def thin(points, frac=0.30, cell=CELL):
    pts = list(points)
    n = len(pts)
    target = int(n * frac + 0.5)
    cells = {}
    for i, p in enumerate(pts):
        cells.setdefault((int(p[1]) // cell, int(p[0]) // cell), []).append(i)
    order = sorted(cells, key=lambda k: (k[0], k[1] if k[0] % 2 == 0 else -k[1]))
    alive = [True] * n
    # a coarse index for the nearest-neighbour search
    grid = {}
    G = 16
    for i, p in enumerate(pts):
        grid.setdefault((int(p[0]) // G, int(p[1]) // G), set()).add(i)

    def nearest(i):
        x, y = int(pts[i][0]), int(pts[i][1])
        gx, gy = x // G, y // G
        best = None
        r = 0
        while r < 1536 // G + 2:
            for ax in range(gx - r, gx + r + 1):
                for ay in range(gy - r, gy + r + 1):
                    if max(abs(ax - gx), abs(ay - gy)) != r:
                        continue
                    for j in grid.get((ax, ay), ()):
                        if j == i:
                            continue
                        d = (int(pts[j][0]) - x) ** 2 + (int(pts[j][1]) - y) ** 2
                        if best is None or d < best:
                            best = d
            # a ring further out cannot be nearer than r * G
            if best is not None and best <= (r * G) ** 2:
                break
            r += 1
        return best if best is not None else 1 << 40

    seen = 0
    removed = 0
    for k in order:
        idx = cells[k]
        seen += len(idx)
        quota = int(seen * frac + 0.5) - removed
        quota = max(0, min(quota, len(idx)))
        for _ in range(quota):
            cand = [i for i in idx if alive[i]]
            i = min(cand, key=lambda i: (nearest(i), int(pts[i][1]), int(pts[i][0]), int(pts[i][4]) if len(pts[i]) > 4 else 0))
            alive[i] = False
            grid[(int(pts[i][0]) // G, int(pts[i][1]) // G)].discard(i)
            removed += 1
    assert removed == target, (removed, target)
    kept = [p for i, p in enumerate(pts) if alive[i]]
    out = [p for i, p in enumerate(pts) if not alive[i]]
    return kept, out


def near(points, x, y, r):
    """lines whose centre is within r m (straight) of x, y"""
    return sum(1 for p in points if (int(p[0]) - x) ** 2 + (int(p[1]) - y) ** 2 <= r * r)
