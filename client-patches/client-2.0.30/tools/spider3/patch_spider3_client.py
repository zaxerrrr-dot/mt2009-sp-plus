# -*- coding: utf-8 -*-
# MT2009_PLUS_SPIDER3_V1 (client data) - 3 Loch Pajakow (217) in the client's data:
#
#   gamedata/atlasinfo.txt  the row of the map's own folder, metin2_map_spiderdungeon3 51200 563200 3 3 (= the server's
#                           Setting.txt of metin2_map_spiderdungeon_03), in place of the base client's
#                           metin2_map_spiderdungeon_03 row over the same square: the client loads the FIRST row whose
#                           square holds the warp's position, and the old name's folder is in none of our packs (a warp
#                           there closed the client - MT2009_PLUS_SPIDER3_OFF_V1). stage_spider3.py says why the folder
#                           has a new name.
# Every vnum of the map (2071-2075, 10097, 10098, 30130) is in the client's mob_proto / npclist already.
# Idempotent: a second run changes nothing. build_spider3_packs.py calls atlasinfo() on the pack; by hand, on a plain
# copy:
#   python3 <repo>/client-patches/client-2.0.30/tools/spider3/patch_spider3_client.py atlasinfo.txt [--check]
import os
import sys

ROW = ('metin2_map_spiderdungeon3', 51200, 563200, 3, 3)
REPLACE = ('metin2_map_spiderdungeon_03',)


class Collision(Exception):
    pass


def atlas_rows():
    return ['%s\t%d\t%d\t%d\t%d' % ROW]


def atlasinfo(b):
    text = b.decode('cp1250')
    nl = '\r\n' if '\r\n' in text else '\n'
    lines = text.split(nl)
    tail = bool(lines) and lines[-1] == ''
    if tail:
        lines.pop()
    gone = set(n.lower() for n in REPLACE)
    want = atlas_rows()
    names = set(r.split('\t')[0].lower() for r in want)
    have, changed = {}, 0
    for l in lines:
        t = l.split()
        n = t[0].lower() if t else ''
        if n in gone:
            changed += 1
            continue
        if n in names:
            have[n] = l
            continue
    for r in want:
        n = r.split('\t')[0].lower()
        if n in have and have[n].split() == r.split():
            continue
        changed += 1
    if not changed:
        return b, 0
    # the row goes where the old one was, so no earlier row's square is passed over differently
    out, placed = [], False
    for l in lines:
        t = l.split()
        n = t[0].lower() if t else ''
        if n in gone or n in names:
            if not placed:
                out.extend(want)
                placed = True
            continue
        out.append(l)
    if not placed:
        out.extend(want)
    return (nl.join(out + ([''] if tail else []))).encode('cp1250'), changed


JOBS = {'gamedata/atlasinfo.txt': atlasinfo}
BY_FILE = dict((os.path.basename(k), f) for k, f in JOBS.items())


def main():
    args = [a for a in sys.argv[1:] if a != '--check']
    check = '--check' in sys.argv
    if not args:
        raise SystemExit('usage: patch_spider3_client.py <atlasinfo.txt> [--check]')
    for path in args:
        fn = BY_FILE[os.path.basename(path)]
        b = open(path, 'rb').read()
        nb, n = fn(b)
        if n and not check:
            open(path, 'wb').write(nb)
        print('%s: %d new/changed%s' % (os.path.basename(path), n, ' (check only)' if check else ''))


if __name__ == '__main__':
    main()
