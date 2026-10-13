# -*- coding: utf-8 -*-
# MT2009_PLUS_YOHARA_MAPS1_V1 (client data) - Dongan (373) and Opuszczona Twierdza (374) in the client's gamedata:
#
#   mob_proto     the 48 rows of linux-port/docker/mariadb/playerbot/yohara_maps.sql (monsters, Metins, NPCs, the gate
#                 portal 10144: names, Polish names, type/rank/battle/level, flags, stats, HP, resists) on the record of
#                 101 (monsters, stones) or 9012 (NPC, portal) - client 2.0.64 has none of them (the target window
#                 would show no name, no level); the layout and the writer are ../shipdefense/patch_shipdefense_client.py's;
#   atlasinfo.txt the two maps' rows (= the server's Setting.txt; they overlap none of ours).
# npclist.txt has every race already (client 2.0.61). APPEND ONLY: a vnum/map already there with other content is a
# collision and stops the run before anything is written. Idempotent: a second run changes nothing.
# MT2009_PLUS_ELEMENTS_V1 (Yohara): a record carries the monster's element - race flag bits 11-16 (offset 83) from
# tools/zywioly/zywioly_moby.json, the map of the server's zywioly_moby.sql (rule h: the wiki's / Owsap's element,
# Metins none). yohara_maps.sql has no element (zywioly_moby.sql, run last, sets it on the server), and the zywioly
# client patch runs before these rows exist - so the target window showed no element on 373/374 (the owner,
# 14 October). A row of an earlier build that differs only in those bits is rewritten.
#
# Both files live in the "gamedata" pack. Run on plain copies, in the m2pack-lzo image (MCOZ):
#   docker run --rm -v /opt/metin2:/opt/metin2 m2pack-lzo python3 \
#     <repo>/client-patches/client-2.0.30/tools/ymaps/patch_ymaps_client.py <mob_proto> [<atlasinfo.txt>] [--check]
# build_ymaps_packs.py calls the same functions on the gamedata pack.
import os
import re
import struct
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, '/opt/metin2/cache/tcm/tz')
sys.path.insert(0, os.path.join(HERE, '..', 'shipdefense'))
import patch_shipdefense_client as sd  # noqa: E402

SQL = os.path.join(HERE, '..', '..', '..', '..', 'linux-port', 'docker', 'mariadb', 'playerbot', 'yohara_maps.sql')
ATLAS = ['metin2_map_eastplain_01\t1049600\t435200\t4\t5',     # = linux-port/docker/game/yohara_maps/map/*/Setting.txt
         'metin2_map_empirecastle\t512000\t486400\t2\t2']
ROWS = 48
Collision = sd.Collision
MOBS_JSON = os.path.join(HERE, '..', '..', '..', '..', 'tools', 'zywioly', 'zywioly_moby.json')
RACE_FLAG = 83                 # the record's dwRaceFlag (= ../zywioly/patch_zywioly_client.py)
ELEMENT_MASK = 0x1F800         # bits 11-16


def elements():
    import json
    with open(MOBS_JSON) as f:
        return dict((int(k), v) for k, v in json.load(f).items())


def with_element(r, element):
    r = bytearray(r)
    old = struct.unpack_from('<I', r, RACE_FLAG)[0]
    struct.pack_into('<I', r, RACE_FLAG, (old & ~ELEMENT_MASK) | (element & ELEMENT_MASK))
    return bytes(r)


def sql_mobs(path=SQL):
    t = open(path, encoding='utf-8').read()
    m = re.search(r'INSERT IGNORE INTO world\.mob_proto \(([^)]*)\) VALUES', t)
    cols = [c.strip().strip('`') for c in m.group(1).split(',')]
    mobs = []
    for r in sd._values(t[m.end():]):
        assert len(r) == len(cols), r[:3]
        mobs.append(dict(zip(cols, r)))
    assert len(mobs) == ROWS, len(mobs)
    return mobs


def mob_proto(b):
    import m2pack
    magic, cnt, esize = struct.unpack_from('<4sII', b, 0)
    assert magic == b'MMPT', magic
    raw = m2pack.mcoz_decode(b[12:12 + esize], sd.MOB_KEY)
    assert len(raw) == cnt * sd.MOB_RECORD, (len(raw), cnt)
    R = sd.MOB_RECORD
    recs = dict((struct.unpack_from('<I', raw, i * R)[0], raw[i * R:(i + 1) * R]) for i in range(cnt))
    elem = elements()
    want = dict((w['vnum'], with_element(sd.mob_record(w, recs[101] if w['type'] in (0, 2) else recs[9012]),
                                         elem.get(w['vnum'], 0))) for w in sql_mobs())
    clash = [v for v, r in sorted(want.items()) if v in recs and with_element(recs[v], 0) != with_element(r, 0)]
    if clash:
        raise Collision('mob_proto: %d vnum(s) already in the client with other content: %s' % (len(clash), clash))
    new = dict((v, r) for v, r in want.items() if recs.get(v) != r)
    if not new:
        return b, 0
    recs.update(new)
    out = b''.join(recs[v] for v in sorted(recs))
    blob = m2pack.mcoz_encode(out, sd.MOB_KEY)
    return struct.pack('<4sII', b'MMPT', len(recs), len(blob)) + blob, len(new)


def atlasinfo(b):
    text = b.decode('cp1250')
    nl = '\r\n' if '\r\n' in text else '\n'
    lines = text.split(nl)
    tail = bool(lines) and lines[-1] == ''
    if tail:
        lines.pop()
    have = dict((l.split('\t')[0].strip().lower(), l) for l in lines if l.strip())
    new = []
    for row in ATLAS:
        k = row.split('\t')[0].lower()
        if k in have:
            if have[k].split() != row.split():
                raise Collision('atlasinfo.txt: %s already there as %r' % (k, have[k]))
            continue
        new.append(row)
    if not new:
        return b, 0
    return (nl.join(lines + new + ([''] if tail else []))).encode('cp1250'), len(new)


def main():
    args = [a for a in sys.argv[1:] if a != '--check']
    check = '--check' in sys.argv
    if not 1 <= len(args) <= 2:
        raise SystemExit('usage: patch_ymaps_client.py <mob_proto> [<atlasinfo.txt>] [--check]')
    for path, fn in zip(args, (mob_proto, atlasinfo)):
        if path == '-':
            continue
        b = open(path, 'rb').read()
        nb, n = fn(b)
        if n and not check:
            open(path, 'wb').write(nb)
        print('%s: %d new%s' % (os.path.basename(path), n, ' (check only)' if check else ''))


if __name__ == '__main__':
    main()
