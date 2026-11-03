# -*- coding: utf-8 -*-
# MT2009_PLUS_SMALL_BLESSING_V1 / MT2009_PLUS_SERVER_CONFIG_V1 (client data) - the items of the SAPPHIRE server
# configuration's calendar (linux-port/docker/seban-panel/server_profiles.txt) the client lacked, the method of
# ../zywiolbroni/patch_zywiolbroni_client.py:
#
#   gamedata/item_list.txt, gamedata/item_proto (dbdata), locale/pl/itemdesc.txt (dbdata)
#       the items of ysapph_items.json (= the server's world.item_proto rows): Male Blogoslawienstwo 72351 (new,
#       male_blogoslawienstwo.sql + server-patches/maleblog: 71052 with a 10% chance), Robin (lup) 53235 (the pet seal
#       of the costume pack: no record in the client) and Nugget (zielony) 71187 (the mount seal: the client's record
#       was an old "Pierscien Wielkanocny+7") - a full record each (../yohara/patch_yohara_client.py yitem_record),
#       their item_list lines (the GF icons 72351 / 71187 / 53233 in client-2.0.30/root/icon/item) and itemdesc lines;
#   gamedata/mob_proto (gamedata)
#       the pet Robin 34057 over the record of Ognisty Feniks 34001 and the mount Nugget 20238 over Dzik 20110 - the
#       names the client shows; gamedata/npclist.txt has "34057 halloween_bet_pet1" and "20238 chick_white3" already.
# A vnum the client has with another record is replaced (the records are the server's). Idempotent: a second run
# changes nothing. build_ysapph_packs.py calls these functions on the packs; by hand, on plain copies, in the
# m2pack-lzo image:
#   docker run --rm -v /opt/metin2:/opt/metin2 m2pack-lzo python3 \
#     <repo>/client-patches/client-2.0.30/tools/ysapph/patch_ysapph_client.py <file> ... [--check]   (by its name)
import io
import json
import os
import struct
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, '/opt/metin2/cache/tcm/tz')
sys.path.insert(0, os.path.join(HERE, '..', 'yohara'))
sys.path.insert(0, os.path.join(HERE, '..', 'monstercard'))
import patch_monstercard_client as base  # noqa: E402
import patch_yohara_client as py  # noqa: E402

ITEMS_JSON = os.path.join(HERE, 'ysapph_items.json')
ITEMS = 3
MOBS = 2
MOB_KEY = (4813894, 18955, 552631, 6822045)
MOB_RECORD = 256


def items_json():
    with io.open(ITEMS_JSON, encoding='utf-8') as f:
        d = json.load(f)
    assert len(d['items']) == ITEMS and len(d['mobs']) == MOBS, (len(d['items']), len(d['mobs']))
    return d


def records(b):
    import m2pack
    assert b[:4] == b'MIPX'
    ver, stride, cnt, size = struct.unpack_from('<IIII', b, 4)
    assert stride == base.RECORD, stride
    raw = m2pack.mcoz_decode(b[20:], base.ITEM_KEY)
    return ver, dict((struct.unpack_from('<I', raw, i * base.RECORD)[0], raw[i * base.RECORD:(i + 1) * base.RECORD])
                     for i in range(cnt))


def want_records(recs):
    return dict((w['vnum'], py.yitem_record(recs[w['template']], w)) for w in items_json()['items'])


def item_proto(b):
    import m2pack
    ver, recs = records(b)
    changed = 0
    for v, r in want_records(recs).items():
        if recs.get(v) != r:
            recs[v] = r
            changed += 1
    if not changed:
        return b, 0
    out = b''.join(recs[v] for v in sorted(recs))
    blob = m2pack.mcoz_encode(out, base.ITEM_KEY)
    return b'MIPX' + struct.pack('<IIII', ver, base.RECORD, len(recs), len(blob)) + blob, changed


def item_list(b):
    d = items_json()
    return base.set_rows(b, [d['item_list'][k] for k in sorted(d['item_list'], key=int)])


def itemdesc(b):
    d = items_json()
    return base.set_rows(b, [d['itemdesc'][k] for k in sorted(d['itemdesc'], key=int)])


def mob_records(b):
    import m2pack
    magic, cnt, esize = struct.unpack_from('<4sII', b, 0)
    assert magic == b'MMPT', magic
    raw = m2pack.mcoz_decode(b[12:12 + esize], MOB_KEY)
    assert len(raw) == cnt * MOB_RECORD, (len(raw), cnt)
    return dict((struct.unpack_from('<I', raw, i * MOB_RECORD)[0], raw[i * MOB_RECORD:(i + 1) * MOB_RECORD])
                for i in range(cnt))


def want_mobs(recs):
    out = {}
    for m in items_json()['mobs']:
        r = bytearray(recs[m['template']])
        struct.pack_into('<I', r, 0, m['vnum'])
        r[4:29] = base.fixed(m['name'], 25)
        r[29:54] = base.fixed(m['locale_name'], 25)
        out[m['vnum']] = bytes(r)
    return out


def mob_proto(b):
    import m2pack
    recs = mob_records(b)
    changed = 0
    for v, r in want_mobs(recs).items():
        if recs.get(v) != r:
            recs[v] = r
            changed += 1
    if not changed:
        return b, 0
    out = b''.join(recs[k] for k in sorted(recs))
    blob = m2pack.mcoz_encode(out, MOB_KEY)
    return struct.pack('<4sII', b'MMPT', len(recs), len(blob)) + blob, changed


# in-pack name -> function
JOBS = {'gamedata/item_list.txt': item_list, 'gamedata/item_proto': item_proto, 'locale/pl/itemdesc.txt': itemdesc,
        'gamedata/mob_proto': mob_proto}
BY_FILE = dict((os.path.basename(k), f) for k, f in JOBS.items())


def main():
    args = [a for a in sys.argv[1:] if a != '--check']
    check = '--check' in sys.argv
    if not args:
        raise SystemExit('usage: patch_ysapph_client.py <item_list.txt|item_proto|itemdesc.txt|mob_proto> ... [--check]')
    for path in args:
        fn = BY_FILE[os.path.basename(path)]
        b = open(path, 'rb').read()
        nb, n = fn(b)
        if n and not check:
            open(path, 'wb').write(nb)
        print('%s: %d new/changed%s' % (os.path.basename(path), n, ' (check only)' if check else ''))


if __name__ == '__main__':
    main()
