# -*- coding: utf-8 -*-
# MT2009_PLUS_MAPS_WZ_V1 (client data) - Wezowe Pole (80) and Kraina Gigantow (70) in the client's data:
#
#   gamedata/mob_proto      the level byte (offset 57 of the 256-byte record, as ../rznm/patch_rznm_client.py) of the
#                           Giants and ogres 1401-1403 / 1601-1603 = the server's (mariadb/playerbot/maps_wz.sql, the
#                           pl-wiki's: 66/73/77, the ogres 71/73 as the global sheet, 75) - the target window shows the client's level; nothing else
#                           of the record changes. Every other vnum of the maps is in the client already;
#   gamedata/atlasinfo.txt  the rows of the maps' own folders (= the server's Setting.txt: metin2_map_snakefield
#                           1049600 716800 4 4, metin2_map_giantland 819200 716800 2 2) in place of the base
#                           client's metin2_map_WL_01 / metin2_map_nusluck01 rows over the same squares (the client
#                           loads the FIRST row whose square holds the warp's position - those would load the old
#                           folders; nusluck01's said 4x4 for a 2x2 map). The data: tools/maps_wz/maps_wz_mobs.json.
# Idempotent: a second run changes nothing. build_wzmaps_packs.py calls these functions on the packs; by hand, on plain
# copies, in the m2pack-lzo image (MCOZ):
#   docker run --rm -v /opt/metin2:/opt/metin2 m2pack-lzo python3 \
#     <repo>/client-patches/client-2.0.30/tools/wzmaps/patch_wzmaps_client.py <mob_proto|atlasinfo.txt> ... [--check]
import io
import json
import os
import struct
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, '/opt/metin2/cache/cli')
sys.path.insert(0, '/opt/metin2/cache/tcm/tz')
REPO = os.path.normpath(os.path.join(HERE, '..', '..', '..', '..'))
MOBS_JSON = os.path.join(REPO, 'tools', 'maps_wz', 'maps_wz_mobs.json')
MOB_KEY = (4813894, 18955, 552631, 6822045)
MOB_RECORD = 256
MOB_LEVEL = 57


class Collision(Exception):
    pass


def data():
    with io.open(MOBS_JSON, encoding='utf-8') as f:
        return json.load(f)


def mob_proto(b):
    import m2pack
    levels = dict((int(k), v) for k, v in data()['levels'].items())
    magic, cnt, esize = struct.unpack_from('<4sII', b, 0)
    assert magic == b'MMPT', magic
    raw = bytearray(m2pack.mcoz_decode(b[12:12 + esize], MOB_KEY))
    assert len(raw) == cnt * MOB_RECORD, (len(raw), cnt)
    seen, changed = set(), 0
    for i in range(cnt):
        off = i * MOB_RECORD
        v = struct.unpack_from('<I', raw, off)[0]
        if v not in levels:
            continue
        seen.add(v)
        if raw[off + MOB_LEVEL] != levels[v]:
            raw[off + MOB_LEVEL] = levels[v]
            changed += 1
    missing = sorted(set(levels) - seen)
    if missing:
        raise Collision('mob_proto: not in the client: %s' % missing)
    if not changed:
        return b, 0
    blob = m2pack.mcoz_encode(bytes(raw), MOB_KEY)
    return struct.pack('<4sII', b'MMPT', cnt, len(blob)) + blob, changed


def atlas_rows():
    return ['%s\t%d\t%d\t%d\t%d' % tuple(r) for r in data()['atlas']]


def atlasinfo(b):
    d = data()
    text = b.decode('cp1250')
    nl = '\r\n' if '\r\n' in text else '\n'
    lines = text.split(nl)
    tail = bool(lines) and lines[-1] == ''
    if tail:
        lines.pop()
    gone = set(n.lower() for n in d['atlas_replace'])
    want = atlas_rows()
    names = set(r.split('\t')[0].lower() for r in want)
    keep, have, changed = [], {}, 0
    for l in lines:
        t = l.split()
        n = t[0].lower() if t else ''
        if n in gone:
            changed += 1
            continue
        if n in names:
            have[n] = l
            continue                      # put back below, in our order
        keep.append(l)
    for r in want:
        n = r.split('\t')[0].lower()
        if n in have and have[n].split() == r.split():
            continue
        changed += 1
    if not changed:
        return b, 0
    return (nl.join(keep + want + ([''] if tail else []))).encode('cp1250'), changed


JOBS = {'gamedata/mob_proto': mob_proto, 'gamedata/atlasinfo.txt': atlasinfo}
BY_FILE = dict((os.path.basename(k), f) for k, f in JOBS.items())


def main():
    args = [a for a in sys.argv[1:] if a != '--check']
    check = '--check' in sys.argv
    if not args:
        raise SystemExit('usage: patch_wzmaps_client.py <mob_proto|atlasinfo.txt> ... [--check]')
    for path in args:
        fn = BY_FILE[os.path.basename(path)]
        b = open(path, 'rb').read()
        nb, n = fn(b)
        if n and not check:
            open(path, 'wb').write(nb)
        print('%s: %d new/changed%s' % (os.path.basename(path), n, ' (check only)' if check else ''))


if __name__ == '__main__':
    main()
