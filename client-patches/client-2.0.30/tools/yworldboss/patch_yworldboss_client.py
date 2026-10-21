# -*- coding: utf-8 -*-
# MT2009_PLUS_WORLDBOSS_V1 (client data) - Boss Swiata in the client's data (the method of
# ../ymeley/patch_ymeley_client.py), from tools/worldboss/worldboss_client.json (tools/worldboss/gen_worldboss.py,
# the same rows as linux-port/docker/mariadb/playerbot/worldboss.sql):
#
#   gamedata/mob_proto      the 36 rows 4420-4479: the six world bosses (Azrael, Bagjanamu, Ogr Maximus, Polifem,
#                           Smoczy Straznik Idall, Zjawa Zoltego Tygrysa - "(BS)") and their five men each, on the
#                           record of 101, each with its element (race flag bits 11-16, offset 83);
#   gamedata/npclist.txt    nothing new when the client has the rows (client 2.0.61 has 4420-4479, the bosses'
#                           "w_*" models among them) - a missing row is added from the json's models / the GF list;
#   gamedata/item_list.txt, gamedata/item_proto (dbdata), locale/pl/itemdesc.txt (dbdata)
#                           Skrzynka Tajemnic 38015 (on Zagadkowa Szkatulka 50033's record), Kupon SM (20) 80031 and
#                           Kupon SM (10) 80032 (on Kupon SM (50) 80017's).
# APPEND ONLY for mob_proto / npclist: a vnum already there with other content (the element bits aside) is a
# collision and stops the run. Idempotent: a second run changes nothing.
# By hand, on plain copies, in the m2pack-lzo image (MCOZ):
#   docker run --rm -v /opt/metin2:/opt/metin2 m2pack-lzo python3 \
#     <repo>/client-patches/client-2.0.30/tools/yworldboss/patch_yworldboss_client.py <file> ... [--check]
import io
import json
import os
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
JSON = os.path.join(REPO, 'tools', 'worldboss', 'worldboss_client.json')
ROWS = 36
ITEMS = 3
RACE_FLAG = 83                 # the record's dwRaceFlag (= ../zywioly/patch_zywioly_client.py)
ELEMENT_MASK = 0x1F800         # bits 11-16
ITEM_TEMPLATE = {23: 50033, 18: 80017}     # the record a new item is laid over, by its type
GF_NPCLIST = '/opt/metin2/cache/c61/chk/gamedata/npclist.txt'
Collision = sd.Collision


def data():
    with io.open(JSON, encoding='utf-8') as f:
        d = json.load(f)
    assert len(d['rows']) == ROWS, len(d['rows'])
    assert len(d['items']) == ITEMS, len(d['items'])
    return d


def json_mobs():
    d = data()
    cols = d['cols']
    mobs = []
    for r in sd._values('(' + '),('.join(','.join(t) for t in d['rows']) + ');'):
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
    elem = dict((int(k), v) for k, v in data()['elements'].items())
    want = dict((w['vnum'], with_element(sd.mob_record(w, recs[101]), elem.get(w['vnum'], 0))) for w in json_mobs())
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


def npclist(b):
    """the bosses' and men's rows when missing (the models: the json for the bosses, client 2.0.61's list for the
    men); a row there with another model is a collision"""
    text = b.decode('cp1250')
    nl = '\r\n' if '\r\n' in text else '\n'
    lines = text.split(nl)
    tail = bool(lines) and lines[-1] == ''
    if tail:
        lines.pop()
    have = {}
    for l in lines:
        t = l.split()
        if len(t) >= 2 and t[0].isdigit():
            have[int(t[0])] = t[1].lower()
    gf = {}
    if os.path.exists(GF_NPCLIST):
        for l in open(GF_NPCLIST, encoding='latin-1'):
            t = l.split()
            if len(t) >= 2 and t[0].isdigit():
                gf[int(t[0])] = t[1].lower()
    d = data()
    want = dict((int(k), v) for k, v in d['models'].items())
    for boss in d['bosses']:
        for v in boss['minions']:
            if v not in have:
                assert v in gf, 'no model known for %d' % v
                want[v] = gf[v]
    new = []
    for v, model in sorted(want.items()):
        if v in have:
            if have[v] != model:
                raise Collision('npclist: %d is %r, not %r' % (v, have[v], model))
            continue
        new.append('%d\t%s' % (v, model))
    if not new:
        return b, 0
    return (nl.join(lines + new + ([''] if tail else []))).encode('cp1250'), len(new)


def item_proto(b):
    import m2pack
    assert b[:4] == b'MIPX'
    ver, stride, cnt, size = struct.unpack_from('<IIII', b, 4)
    assert stride == base.RECORD, stride
    raw = m2pack.mcoz_decode(b[20:], base.ITEM_KEY)
    recs = dict((struct.unpack_from('<I', raw, i * base.RECORD)[0], raw[i * base.RECORD:(i + 1) * base.RECORD])
                for i in range(cnt))
    changed = 0
    for w in data()['items']:
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
    d = data()
    return base.set_rows(b, [d['item_list'][k] for k in sorted(d['item_list'], key=int)])


def itemdesc(b):
    d = data()
    return base.set_rows(b, [d['itemdesc'][k] for k in sorted(d['itemdesc'], key=int)])


# in-pack name -> function
JOBS = {'gamedata/mob_proto': mob_proto, 'gamedata/npclist.txt': npclist, 'gamedata/item_list.txt': item_list,
        'gamedata/item_proto': item_proto, 'locale/pl/itemdesc.txt': itemdesc}
BY_FILE = dict((os.path.basename(k), f) for k, f in JOBS.items())


def main():
    args = [a for a in sys.argv[1:] if a != '--check']
    check = '--check' in sys.argv
    if not args:
        raise SystemExit('usage: patch_yworldboss_client.py <mob_proto|npclist.txt|item_list.txt|item_proto|'
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
