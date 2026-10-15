#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""verify_chestdrops.py [--db CONTAINER]

MT2009_PLUS_CHEST_DROPS_V1: checks that every chest of the owner's sheet (chestdrops.py) has exactly one group in
linux-port/docker/game (any special_item_group*.txt below it) and that its rows are chestdrops.py's - the generated
files and the hand-made ones (shipdefense: 54705, 72058; special_item_group.dungeons.txt: the official Razador /
Nemere chests, nested groups 950270 / 950275 of 50270 / 50271, and Skrzynia Berana-Setaou 54700 with its pl-wiki
rows - MT2009_PLUS_BERAN_CHEST_V1); that every group of those files is numbered 1..N;
that no awk of the Dockerfile still adds rows to a sheet chest; and, with --db, that every vnum written is in
world.item_proto (docker exec CONTAINER mariadb ...).

Example: python3 tools/yohara_chestdrops/verify_chestdrops.py --db mt2009plustest-db
"""
import argparse
import glob
import os
import re
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(os.path.dirname(HERE))
GAME = os.path.join(REPO, 'linux-port', 'docker', 'game')
sys.path.insert(0, HERE)
import chestdrops as CD  # noqa: E402

# our chest -> the group holding the sheet's table (the Pct chests open it as their line 1)
NESTED = {50270: 950270, 50271: 950275}


def groups(path):
    """[(group vnum, [row lines]), ...] of a special_item_group file"""
    out, cur = [], None
    for line in open(path, encoding='utf-8', errors='replace'):
        line = line.rstrip('\r\n')
        m = re.match(r'\s*Vnum\s+(\d+)', line)
        if m and cur is not None:
            cur[0] = int(m.group(1))
            continue
        if re.match(r'Group\s', line):
            cur = [None, []]
            continue
        if line.startswith('}') and cur is not None:
            out.append((cur[0], cur[1]))
            cur = None
            continue
        if cur is not None and re.match(r'\s*\d+\s', line):
            cur[1].append(line)
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--db', help='the MariaDB container to check the vnums against (world.item_proto)')
    a = ap.parse_args()
    bad = []
    files = sorted(glob.glob(os.path.join(GAME, '**', 'special_item_group*.txt'), recursive=True))
    found = {}
    for f in files:
        for g, rows in groups(f):
            nums = [int(r.split()[0]) for r in rows]
            if nums != list(range(1, len(nums) + 1)):
                bad.append('%s: group %s numbered %s' % (os.path.relpath(f, REPO), g, nums))
            found.setdefault(g, []).append((f, rows))
    used = set()
    for chest in sorted(CD.sheet()):
        g = NESTED.get(chest, chest)
        if len(found.get(g, [])) != 1:
            bad.append('chest %d: %d groups %d' % (chest, len(found.get(g, [])), g))
            continue
        f, rows = found[g][0]
        want = CD.group_lines(chest)
        if [r.strip() for r in rows] != [w.strip() for w in want]:
            bad.append('chest %d: %s differs from chestdrops.py' % (chest, os.path.relpath(f, REPO)))
        rr, _ = CD.table(chest)
        used.update(int(v) for v, _, _, _ in rr if v not in ('gold', 'exp'))
        if abs(sum(w for _, _, w, _ in rr) - CD.SCALE) > len(rr):
            bad.append('chest %d: weights sum %d' % (chest, sum(w for _, _, w, _ in rr)))
    for chest in (50270, 50271):
        f, rows = found[chest][0]
        if not any(r.split()[1] == 's%d' % NESTED[chest] and r.split()[3] == '100' for r in rows):
            bad.append('chest %d does not open s%d at 100%%' % (chest, NESTED[chest]))
    for awk in glob.glob(os.path.join(GAME, '**', 'special_item_group*.awk'), recursive=True):
        txt = open(awk, encoding='utf-8').read()
        for chest in CD.sheet():
            if re.search(r'v == "%d"' % chest, txt):
                bad.append('%s still adds rows to %d' % (os.path.relpath(awk, REPO), chest))
    if a.db:
        q = 'select vnum from world.item_proto where vnum in (%s)' % ','.join(map(str, sorted(used)))
        res = subprocess.run(['docker', 'exec', a.db, 'sh', '-c',
                              'mariadb -uroot -p"$MARIADB_ROOT_PASSWORD" -N -B -e "%s"' % q],
                             capture_output=True, text=True, check=True).stdout.split()
        missing = sorted(used - set(int(x) for x in res))
        if missing:
            bad.append('not in world.item_proto: %s' % missing)
    print('chests %d, files %d, vnums %d%s' % (len(CD.sheet()), len(files), len(used),
                                                ', checked against ' + a.db if a.db else ''))
    if bad:
        print('\n'.join(bad))
        sys.exit(1)
    print('OK')


if __name__ == '__main__':
    main()
