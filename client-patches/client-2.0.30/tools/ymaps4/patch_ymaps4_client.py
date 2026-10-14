# -*- coding: utf-8 -*-
# MT2009_PLUS_YOHARA_MAPS4_V1 (client data) - Rozpadlina Dusz in the client's data, and the owner's items of 14 October
# (MT2009_PLUS_YOHARA_ITEMS4_V1) - the method of ../ymaps3/patch_ymaps3_client.py:
#
#   gamedata/mob_proto      the 20 rows of linux-port/docker/mariadb/playerbot/yohara_maps4.sql (monsters, bosses, NPCs,
#                           portals) on the record of 101 (monsters) or 9012 (NPC, portal), each with its element - race
#                           flag bits 11-16 (offset 83) from tools/yohara_maps4/ymaps4_mobs.json (= the server's
#                           yohara_maps4_zywioly.sql); the second batch's stand-in portals 10145/10146 (no map spawns
#                           them, the server deletes their rows) go - only if they are those rows ("SchronPlnW ..." /
#                           "WawozPlnW ...");
#                           and the third batch's element bits as tools/yohara_maps3/ymaps3_mobs.json has them now
#                           (Duch Kamienia 3990: wind - the owner, 14 October), on its rows the client already has -
#                           so an OUT built before that change is right after this step alone;
#   gamedata/atlasinfo.txt  the map's row (= the server's Setting.txt; it overlaps none of ours);
#   gamedata/npclist.txt    nothing to add (client 2.0.61 has every race of the map) - kept for the build's jobs;
#   gamedata/item_list.txt, gamedata/item_proto, locale/pl/itemdesc.txt
#                           the 124 items of tools/yohara_maps4/yohara_items4.json (= the server's yohara_items4.sql,
#                           tools/yohara_maps4/gen_yitems4.py): a full record each over a template (Rubinowa Bransoleta+0
#                           14500 for the bracelets, Zelazna Szkatulka 50120 for the rest - ../yohara/patch_yohara_client.py
#                           yitem_record), its item_list line (the GF icons: client-2.0.30/root/icon/item) and its
#                           itemdesc line.
# APPEND ONLY for mob_proto/atlasinfo (but the two stand-in rows): a vnum/map already there with other content (the
# element bits aside) is a collision and stops the run. Idempotent: a second run changes nothing.
# build_ymaps4_packs.py calls these functions on the packs; by hand, on plain copies, in the m2pack-lzo image (MCOZ):
#   docker run --rm -v /opt/metin2:/opt/metin2 m2pack-lzo python3 \
#     <repo>/client-patches/client-2.0.30/tools/ymaps4/patch_ymaps4_client.py <file> ...   (by its name)
import io
import json
import os
import re
import struct
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, '/opt/metin2/cache/tcm/tz')
sys.path.insert(0, os.path.join(HERE, '..', 'shipdefense'))
sys.path.insert(0, os.path.join(HERE, '..', 'yohara'))
sys.path.insert(0, os.path.join(HERE, '..', 'monstercard'))
import patch_shipdefense_client as sd  # noqa: E402
import patch_monstercard_client as base  # noqa: E402
import patch_yohara_client as py  # noqa: E402

REPO = os.path.normpath(os.path.join(HERE, '..', '..', '..', '..'))
SQL = os.path.join(REPO, 'linux-port', 'docker', 'mariadb', 'playerbot', 'yohara_maps4.sql')
MOBS_JSON = os.path.join(REPO, 'tools', 'yohara_maps4', 'ymaps4_mobs.json')
ITEMS_JSON = os.path.join(REPO, 'tools', 'yohara_maps4', 'yohara_items4.json')
MOBS3_JSON = os.path.join(REPO, 'tools', 'yohara_maps3', 'ymaps3_mobs.json')
ATLAS = ['metin2_map_whitdragonvalley\t128000\t1510400\t3\t3']   # = linux-port/docker/game/yohara_maps4/map/*/Setting.txt
ROWS = 20
ITEMS = 124                    # 44 + the jade necklaces / earrings (MT2009_PLUS_JADE_JEWELLERY_V1)
ITEM_TEMPLATE = {2: 14500}     # by type: Rubinowa Bransoleta+0 for the jade jewellery, else py.TEMPLATE (50120)
REMOVE = {10145: b'SchronPlnW ', 10146: b'WawozPlnW '}
RACE_FLAG = 83                 # the record's dwRaceFlag (= ../zywioly/patch_zywioly_client.py)
ELEMENT_MASK = 0x1F800         # bits 11-16
Collision = sd.Collision


def mobs_json():
    with io.open(MOBS_JSON, encoding='utf-8') as f:
        return json.load(f)


def items_json():
    with io.open(ITEMS_JSON, encoding='utf-8') as f:
        d = json.load(f)
    assert len(d['items']) == ITEMS, len(d['items'])
    return d


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


def with_element(r, element):
    r = bytearray(r)
    old = struct.unpack_from('<I', r, RACE_FLAG)[0]
    struct.pack_into('<I', r, RACE_FLAG, (old & ~ELEMENT_MASK) | (element & ELEMENT_MASK))
    return bytes(r)


def mob_proto(b):
    import m2pack
    magic, cnt, esize = struct.unpack_from('<4sII', b, 0)
    assert magic == b'MMPT', magic
    raw = m2pack.mcoz_decode(b[12:12 + esize], sd.MOB_KEY)
    assert len(raw) == cnt * sd.MOB_RECORD, (len(raw), cnt)
    R = sd.MOB_RECORD
    recs = dict((struct.unpack_from('<I', raw, i * R)[0], raw[i * R:(i + 1) * R]) for i in range(cnt))
    elem = dict((int(k), v) for k, v in mobs_json()['elements'].items())
    want = dict((w['vnum'], with_element(sd.mob_record(w, recs[101] if w['type'] in (0, 2) else recs[9012]),
                                         elem.get(w['vnum'], 0))) for w in sql_mobs())
    clash = [v for v, r in sorted(want.items()) if v in recs and with_element(recs[v], 0) != with_element(r, 0)]
    if clash:
        raise Collision('mob_proto: %d vnum(s) already in the client with other content: %s' % (len(clash), clash))
    new = dict((v, r) for v, r in want.items() if recs.get(v) != r)
    with io.open(MOBS3_JSON, encoding='utf-8') as f:
        for k, e in json.load(f)['elements'].items():
            v = int(k)
            if v in recs and v not in want and recs[v] != with_element(recs[v], e):
                new[v] = with_element(recs[v], e)
    gone = [v for v, name in sorted(REMOVE.items()) if v in recs and recs[v][4:4 + len(name)] == name]
    if not new and not gone:
        return b, 0
    recs.update(new)
    for v in gone:
        del recs[v]
    out = b''.join(recs[v] for v in sorted(recs))
    blob = m2pack.mcoz_encode(out, sd.MOB_KEY)
    return struct.pack('<4sII', b'MMPT', len(recs), len(blob)) + blob, len(new) + len(gone)


def _append_rows(b, rows, key):
    text = b.decode('cp1250')
    nl = '\r\n' if '\r\n' in text else '\n'
    lines = text.split(nl)
    tail = bool(lines) and lines[-1] == ''
    if tail:
        lines.pop()
    have = dict((key(l), l) for l in lines if l.strip() and not l.lstrip().startswith(('#', '//')))
    new = []
    for row in rows:
        k = key(row)
        if k in have:
            if have[k].split() != row.split():
                raise Collision('%r already there as %r' % (k, have[k]))
            continue
        new.append(row)
    if not new:
        return b, 0
    return (nl.join(lines + new + ([''] if tail else []))).encode('cp1250'), len(new)


def atlasinfo(b):
    return _append_rows(b, ATLAS, lambda l: l.split('\t')[0].strip().lower())


def npclist(b):
    return b, 0


def item_proto(b):
    import m2pack
    assert b[:4] == b'MIPX'
    ver, stride, cnt, size = struct.unpack_from('<IIII', b, 4)
    assert stride == base.RECORD, stride
    raw = m2pack.mcoz_decode(b[20:], base.ITEM_KEY)
    recs = dict((struct.unpack_from('<I', raw, i * base.RECORD)[0], raw[i * base.RECORD:(i + 1) * base.RECORD])
                for i in range(cnt))
    changed = 0
    for w in items_json()['items']:
        r = py.yitem_record(recs[ITEM_TEMPLATE.get(w['type'], py.TEMPLATE)], w)
        if recs.get(w['vnum']) != r:
            recs[w['vnum']] = r
            changed += 1
    if not changed:
        return b, 0
    out = b''.join(recs[v] for v in sorted(recs))
    blob = m2pack.mcoz_encode(out, base.ITEM_KEY)
    return b'MIPX' + struct.pack('<IIII', ver, stride, len(recs), len(blob)) + blob, changed


def item_list(b):
    d = items_json()
    return base.set_rows(b, [d['item_list'][k] for k in sorted(d['item_list'], key=int)])


def itemdesc(b):
    d = items_json()
    return base.set_rows(b, [d['itemdesc'][k] for k in sorted(d['itemdesc'], key=int)])


# in-pack name -> function
JOBS = {'gamedata/mob_proto': mob_proto, 'gamedata/atlasinfo.txt': atlasinfo, 'gamedata/npclist.txt': npclist,
        'gamedata/item_list.txt': item_list, 'gamedata/item_proto': item_proto, 'locale/pl/itemdesc.txt': itemdesc}
BY_FILE = dict((os.path.basename(k), f) for k, f in JOBS.items())


def main():
    args = [a for a in sys.argv[1:] if a != '--check']
    check = '--check' in sys.argv
    if not args:
        raise SystemExit('usage: patch_ymaps4_client.py <mob_proto|atlasinfo.txt|item_list.txt|item_proto|'
                         'itemdesc.txt> ... [--check]')
    for path in args:
        fn = BY_FILE[os.path.basename(path)]
        b = open(path, 'rb').read()
        nb, n = fn(b)
        if n and not check:
            open(path, 'wb').write(nb)
        print('%s: %d new/changed%s' % (os.path.basename(path), n, ' (check only)' if check else ''))


if __name__ == '__main__':
    main()
