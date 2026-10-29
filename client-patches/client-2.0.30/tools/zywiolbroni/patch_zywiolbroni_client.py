# -*- coding: utf-8 -*-
# MT2009_PLUS_WEAPON_ELEMENT_V1 (client data) - Zaczarowanie Żywiołu Broni (server-patches/zywiolbroni) in the client's
# data, the method of ../czepiec/patch_czepiec_client.py:
#
#   gamedata/item_list.txt, gamedata/item_proto (dbdata), locale/pl/itemdesc.txt (dbdata)
#       the eight scrolls of tools/zywiolbroni/zywiolbroni_items.json (= the server's zywiol_broni.sql,
#       tools/zywiolbroni/gen_zywiolbroni.py): 56002-56007 Zwój Ognia / Lodu / Błyskawicy / Wiatru / Ziemi / Mroku,
#       56008 Zwój Klątwy, 56009 Zwój Zmiany - a full record each over Zaczarowanie Przedmiotu 71084 (an ITEM_USE scroll;
#       ../yohara/patch_yohara_client.py yitem_record), their item_list lines (the GF icons in client-2.0.30/root/icon/
#       item) and itemdesc lines;
#   gamedata/mob_proto (gamedata)
#       Stróż Medali 20650 (an NPC the click of which opens his shop) over the record of Teleporter 9012 (an NPC) - the
#       name the client shows; gamedata/npclist.txt has "20650 scholar_brown_M1" already (the alias of scholar_brown_M,
#       Mnich Milbon 20438's model).
# A vnum the client has with another record is replaced. Idempotent: a second run changes nothing.
# build_zywiolbroni_packs.py calls these functions on the packs; by hand, on plain copies, in the m2pack-lzo image:
#   docker run --rm -v /opt/metin2:/opt/metin2 m2pack-lzo python3 \
#     <repo>/client-patches/client-2.0.30/tools/zywiolbroni/patch_zywiolbroni_client.py <file> ... [--check]
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

REPO = os.path.normpath(os.path.join(HERE, '..', '..', '..', '..'))
ITEMS_JSON = os.path.join(REPO, 'tools', 'zywiolbroni', 'zywiolbroni_items.json')
ITEMS = 8
TEMPLATE = 71084        # Zaczarowanie Przedmiotu: ITEM_USE, stackable
MOB_KEY = (4813894, 18955, 552631, 6822045)
MOB_RECORD = 256
MOB_TEMPLATE = 9012     # Teleporter: an NPC
ON_CLICK_SHOP = 1


def items_json():
    with io.open(ITEMS_JSON, encoding='utf-8') as f:
        d = json.load(f)
    assert len(d['items']) == ITEMS, len(d['items'])
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
    t = recs[TEMPLATE]
    assert t[74] == 3, t[74]                      # the template is an ITEM_USE record
    return dict((w['vnum'], py.yitem_record(t, w)) for w in items_json()['items'])


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


def want_mob(recs):
    npc = items_json()['npc']
    r = bytearray(recs[MOB_TEMPLATE])
    struct.pack_into('<I', r, 0, npc['vnum'])
    r[4:29] = base.fixed('Medal Guardian', 25)
    r[29:54] = base.fixed(npc['name'], 25)
    r[138] = ON_CLICK_SHOP
    return npc['vnum'], bytes(r)


def mob_proto(b):
    import m2pack
    recs = mob_records(b)
    v, r = want_mob(recs)
    if recs.get(v) == r:
        return b, 0
    recs[v] = r
    out = b''.join(recs[k] for k in sorted(recs))
    blob = m2pack.mcoz_encode(out, MOB_KEY)
    return struct.pack('<4sII', b'MMPT', len(recs), len(blob)) + blob, 1


# in-pack name -> function
JOBS = {'gamedata/item_list.txt': item_list, 'gamedata/item_proto': item_proto, 'locale/pl/itemdesc.txt': itemdesc,
        'gamedata/mob_proto': mob_proto}
BY_FILE = dict((os.path.basename(k), f) for k, f in JOBS.items())


def main():
    args = [a for a in sys.argv[1:] if a != '--check']
    check = '--check' in sys.argv
    if not args:
        raise SystemExit('usage: patch_zywiolbroni_client.py <item_list.txt|item_proto|itemdesc.txt|mob_proto> ... '
                         '[--check]')
    for path in args:
        fn = BY_FILE[os.path.basename(path)]
        b = open(path, 'rb').read()
        nb, n = fn(b)
        if n and not check:
            open(path, 'wb').write(nb)
        print('%s: %d new/changed%s' % (os.path.basename(path), n, ' (check only)' if check else ''))


if __name__ == '__main__':
    main()
