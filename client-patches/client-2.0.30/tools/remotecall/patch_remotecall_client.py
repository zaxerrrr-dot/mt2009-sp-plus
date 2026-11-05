# -*- coding: utf-8 -*-
# MT2009_PLUS_REMOTE_CALL_V1 - Enasir (Dozorca / Handlarz) in the client's data (server-patches/remotecall/README.md).
# One list: items.json here (names and descriptions as pl-wiki "System Enasira" / "Dozorca Enasir (h)"); the server's
# rows are linux-port/docker/mariadb/playerbot/remote_call.sql - keep the two equal.
#
#   gamedata/item_proto (dbdata)    72368-72371: ITEM_QUEST, stack 200, antiflags 90240 (bound: no drop / give /
#                                   PK drop / private shop) or 0 ("(h)"), flags 8196 (stackable, log), value0 = the
#                                   service (0 storeroom, 1 shop), value1 = 604800 s (7 days); name and locale name
#                                   the Polish name (as ../pety's item_record)
#   gamedata/item_list.txt          <vnum>\tETC\ticon/item/<GF icon 72368 or 72369>.tga (the icons: pack "remotecall")
#   locale/pl/itemdesc.txt (dbdata) <vnum>\t<name>\t<description>
#   gamedata/mob_proto              20874 Enasir: a copy of 9003's record (Handlarka Roznosci, an NPC that stands) with
#                                   the vnum, the name and the model folder "peddler_call" (GF 26.1.11's npclist row
#                                   "20874 peddler_call" is in gamedata/npclist.txt already - checked, not written)
# A record or line that is there with other content is rewritten (these vnums are Enasir's); idempotent.
#
#   docker run --rm -v /opt/metin2:/opt/metin2 m2pack-lzo python3 \
#     <repo>/client-patches/client-2.0.30/tools/remotecall/patch_remotecall_client.py <item_proto|item_list.txt|itemdesc.txt|mob_proto> ...
import io
import json
import os
import struct
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, '/opt/metin2/cache/tcm/tz')
sys.path.insert(0, os.path.join(HERE, '..', 'monstercard'))
sys.path.insert(0, os.path.join(HERE, '..', 'shipdefense'))
import patch_monstercard_client as base  # noqa: E402
import patch_shipdefense_client as sd  # noqa: E402

ITEM_QUEST = 18
STACK = 200
FLAGS = 4 | 8192                    # ITEM_FLAG_STACKABLE | ITEM_FLAG_LOG
ANTI_BOUND = 128 | 8192 | 16384 | 65536   # drop, give, PK drop, private shop = 90240
SECONDS = 604800                    # 7 days (GF's value)
MOB_VNUM = 20874
MOB_NAME = u'Enasir'
MOB_FOLDER = 'peddler_call'
MOB_TEMPLATE = 9003                 # Handlarka Roznosci - an NPC that stands
NPCLIST_ROW = u'20874\tpeddler_call'


def items():
    with io.open(os.path.join(HERE, 'items.json'), encoding='utf-8') as f:
        return json.load(f)['items']


def item_record(it):
    for k in ('pl', 'desc'):
        assert '\t' not in it[k] and '\n' not in it[k] and '\r' not in it[k], (it['vnum'], k)
    assert len(it['pl'].encode('cp1250')) < 33, it['pl']
    r = bytearray(base.RECORD)
    struct.pack_into('<II', r, 0, it['vnum'], 0)
    r[8:41] = base.fixed(it['pl'], 33)
    r[41:74] = base.fixed(it['pl'], 33)
    struct.pack_into('<BBBB', r, 74, ITEM_QUEST, 0, 0, 1)                      # type, subtype, weight 0, size 1
    anti = 0 if it['trade'] else ANTI_BOUND
    struct.pack_into('<IIIII', r, 78, STACK, anti, FLAGS, 0, 0)                 # stack, anti, flags, wear, immune
    struct.pack_into('<qq', r, 98, 0, 0)                                        # buy, sell
    struct.pack_into('<BiBi', r, 114, 0, 0, 0, 0)
    struct.pack_into('<6i', r, 139, it['kind'], SECONDS, 0, 0, 0, 0)
    return bytes(r)


def item_proto(b):
    import m2pack
    assert b[:4] == b'MIPX'
    ver, stride, cnt, size = struct.unpack_from('<IIII', b, 4)
    assert stride == base.RECORD, stride
    raw = m2pack.mcoz_decode(b[20:], base.ITEM_KEY)
    recs = dict((struct.unpack_from('<I', raw, i * base.RECORD)[0], raw[i * base.RECORD:(i + 1) * base.RECORD])
                for i in range(cnt))
    changed = 0
    for it in items():
        r = item_record(it)
        if recs.get(it['vnum']) != r:
            recs[it['vnum']] = r
            changed += 1
    if not changed:
        return b, 0
    out = b''.join(recs[v] for v in sorted(recs))
    blob = m2pack.mcoz_encode(out, base.ITEM_KEY)
    return b'MIPX' + struct.pack('<IIII', ver, stride, len(recs), len(blob)) + blob, changed


def list_rows():
    return [u'%d\tETC\ticon/item/%d.tga' % (it['vnum'], it['icon']) for it in items()]


def desc_rows():
    return [u'%d\t%s\t%s' % (it['vnum'], it['pl'], it['desc']) for it in items()]


def item_list(b):
    return base.set_rows(b, list_rows())


def itemdesc(b):
    return base.set_rows(b, desc_rows())


def mob_record(tmpl):
    r = bytearray(tmpl)
    struct.pack_into('<I', r, 0, MOB_VNUM)
    r[4:29] = sd.fixed(MOB_NAME, 25)
    r[29:54] = sd.fixed(MOB_NAME, 25)
    r[140:204] = sd.fixed(MOB_FOLDER, 64)
    return bytes(r)


def mob_records(b):
    import m2pack
    magic, cnt, esize = struct.unpack_from('<4sII', b, 0)
    assert magic == b'MMPT', magic
    R = sd.MOB_RECORD
    raw = m2pack.mcoz_decode(b[12:12 + esize], sd.MOB_KEY)
    assert len(raw) == cnt * R, (len(raw), cnt)
    return dict((struct.unpack_from('<I', raw, i * R)[0], raw[i * R:(i + 1) * R]) for i in range(cnt))


def mob_proto(b):
    import m2pack
    recs = mob_records(b)
    assert MOB_TEMPLATE in recs, 'mob_proto: no %d (the template)' % MOB_TEMPLATE
    r = mob_record(recs[MOB_TEMPLATE])
    if recs.get(MOB_VNUM) == r:
        return b, 0
    recs[MOB_VNUM] = r
    out = b''.join(recs[v] for v in sorted(recs))
    blob = m2pack.mcoz_encode(out, sd.MOB_KEY)
    return struct.pack('<4sII', b'MMPT', len(recs), len(blob)) + blob, 1


def npclist_ok(b):
    """gamedata/npclist.txt has GF's row for Enasir (the repo's gamedata has it)"""
    return any(l.split() == NPCLIST_ROW.split() for l in b.decode('cp1250').replace('\r', '').split('\n'))


# the pack builder's jobs: an entry's name -> fn(bytes) -> (new bytes, changes)
JOBS = {'gamedata/item_list.txt': item_list, 'gamedata/mob_proto': mob_proto,
        'gamedata/item_proto': item_proto, 'locale/pl/itemdesc.txt': itemdesc}
PACK_OF = {'gamedata/item_list.txt': 'gamedata', 'gamedata/mob_proto': 'gamedata',
           'gamedata/item_proto': 'dbdata', 'locale/pl/itemdesc.txt': 'dbdata'}
BY_FILE = dict((os.path.basename(k), f) for k, f in JOBS.items())


def main():
    if len(sys.argv) < 2:
        raise SystemExit('usage: patch_remotecall_client.py <item_proto|item_list.txt|itemdesc.txt|mob_proto> ...')
    for path in sys.argv[1:]:
        fn = BY_FILE.get(os.path.basename(path))
        if fn is None:
            raise SystemExit('%s: not one of %s' % (path, sorted(BY_FILE)))
        with open(path, 'rb') as f:
            data, changed = fn(f.read())
        if changed:
            with open(path, 'wb') as f:
                f.write(data)
        print('%s: %d change(s)' % (path, changed))


if __name__ == '__main__':
    main()
