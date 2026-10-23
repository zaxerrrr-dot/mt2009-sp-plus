# -*- coding: utf-8 -*-
# MT2009_PLUS_SKRZYNIE_UCZNIA_WIKI_V1 (client data) - the items of the level chests (Skrzynia Ucznia I .. Arcymistrza,
# the pl-wiki contents) the client did not know, from tools/skrzynie_ucznia/skrzynie_items.json (= the server's
# skrzynie_ucznia.sql and our world rows, tools/skrzynie_ucznia/gen_skrzynie_ucznia.py), the method of
# ../mlodzi/patch_mlodzi_client.py:
#
#   gamedata/item_proto (dbdata)   a full record each (../yohara/patch_yohara_client.py yitem_record over the record of
#                                  Mikstura Szybkosci 76012): the new 76009, 76016, 76026, 76034-76038, 56001, 38103,
#                                  the Appaloosa seal 56000 (the server had it, the client not) and 76017 / 76018 under
#                                  their right names (Mikstura Ataku +15 / +20);
#   gamedata/item_list.txt         their icon lines (the official client's icons; 56000.tga and 51639.tga travel in
#                                  client-2.0.30/root/icon/item), 71033 Maska Uczuc's (it had none) and 51639's;
#   locale/pl/itemdesc.txt (dbdata) their names and descriptions;
#   gamedata/mob_proto (gamedata)  the Appaloosa (20253, the seal's mount; npclist has its model pony/horse_normal02):
#                                  the record of Kon (20030) under its vnum and name, when the client has none.
# Idempotent: a second run changes nothing. By hand, on plain copies, in the m2pack-lzo image (MCOZ):
#   docker run --rm -v /opt/metin2:/opt/metin2 m2pack-lzo python3 \
#     <repo>/client-patches/client-2.0.30/tools/skrzynie/patch_skrzynie_client.py <file> ... [--check]   (by its name)
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
ITEMS_JSON = os.path.join(REPO, 'tools', 'skrzynie_ucznia', 'skrzynie_items.json')
MARKER = 'MT2009_PLUS_SKRZYNIE_UCZNIA_WIKI_V1'
TEMPLATE = 76012                    # Mikstura Szybkosci: an ITEM_USE record
MOB_KEY = (4813894, 18955, 552631, 6822045)
MOB_RECORD = 256
MOB_NAME, MOB_LOCALE_NAME, NAME_LEN = 4, 29, 25


def items_json():
    with io.open(ITEMS_JSON, encoding='utf-8') as f:
        d = json.load(f)
    assert d['marker'] == MARKER, d.get('marker')
    assert len(d['items']) == 13, len(d['items'])
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
    assert t[74] == 3, ('template', TEMPLATE, t[74])
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


def mob_proto(b):
    import m2pack
    m = items_json()['mob']
    magic, cnt, esize = struct.unpack_from('<4sII', b, 0)
    assert magic == b'MMPT', magic
    raw = m2pack.mcoz_decode(b[12:12 + esize], MOB_KEY)
    assert len(raw) == cnt * MOB_RECORD, (len(raw), cnt)
    recs = dict((struct.unpack_from('<I', raw, i * MOB_RECORD)[0], raw[i * MOB_RECORD:(i + 1) * MOB_RECORD])
                for i in range(cnt))
    if m['vnum'] in recs:
        return b, 0
    r = bytearray(recs[m['template']])
    struct.pack_into('<I', r, 0, m['vnum'])
    name = m['name'].encode('ascii')
    for at in (MOB_NAME, MOB_LOCALE_NAME):
        r[at:at + NAME_LEN] = name + b'\0' * (NAME_LEN - len(name))
    recs[m['vnum']] = bytes(r)
    out = b''.join(recs[v] for v in sorted(recs))
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
        raise SystemExit('usage: patch_skrzynie_client.py <item_list.txt|item_proto|itemdesc.txt|mob_proto> ... [--check]')
    for path in args:
        fn = BY_FILE[os.path.basename(path)]
        b = open(path, 'rb').read()
        nb, n = fn(b)
        if n and not check:
            open(path, 'wb').write(nb)
        print('%s: %d new/changed%s' % (os.path.basename(path), n, ' (check only)' if check else ''))


if __name__ == '__main__':
    main()
