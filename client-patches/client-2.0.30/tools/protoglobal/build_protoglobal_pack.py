# -*- coding: utf-8 -*-
# MT2009_PLUS_GLOBAL_PROTO_V1 (client data) - the fixed item bonuses of M2_BONUS_MODE=global in the tooltips (the
# owner's list of 15 October 2026, item 19; server side: tools/protoglobal/gen_item_proto_global.py and apply.sh).
#
# The client reads every item's fixed bonuses from its item_proto (dbdata pack, gamedata/item_proto), which carries
# the mt2009 values. The exe's item.LoadItemTable(<file>) loads one more item_proto over the table: a vnum it has
# gets that record (CItemData::SetItemTableData), nothing else changes (the exe's own items after the loop - Smocze
# Kamienie, Magma Manni... - are written again as at the start). So two small item_protos with the same records (every item of the global list the client has):
#   gamedata/item_proto_global  the client's own record of each item, the three applies (offset 124, 5 bytes each:
#                               type BYTE + value LONG) being global mode's (tools/protoglobal/item_proto_global.json)
#   gamedata/item_proto_mt2009  the same records as the client's item_proto has them (back to mt2009 in the same
#                               session, e.g. after logging in to another server)
# and root protoglobal.py loads one when the server says "BonusMode 1" / "BonusMode 0" at login (game.py).
# Both go into the "gamedata" pack (not dbdata: the panel's database editor zips replace dbdata). The records are
# taken from the FINAL gamedata/item_proto (out/pack dbdata after every other step), so run this LAST of the item
# steps - after yfinal (clientY.sh):
#   docker run --rm -v /opt/metin2:/opt/metin2 m2pack-lzo python3 $T/protoglobal/build_protoglobal_pack.py \
#     $C/azbase $C/out/pack > $C/protoglobal.json
# --check measures only. Idempotent: a second run reports "unchanged".
import json
import os
import struct
import sys
import zlib

sys.path.insert(0, '/opt/metin2/cache/c36')
sys.path.insert(0, '/opt/metin2/cache/tcm/tz')
sys.path.insert(0, '/opt/metin2/cache/arezzo-work/client/az58')
HERE = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.normpath(os.path.join(HERE, '..', '..', '..', '..', 'tools', 'protoglobal', 'item_proto_global.json'))
ITEM_KEY = (173217, 72619434, 408587239, 27973291)
RECORD = 184
APPLY_OFF = 124
NAMES = ('gamedata/item_proto_global', 'gamedata/item_proto_mt2009')


def records(b):
    import m2pack
    assert b[:4] == b'MIPX'
    ver, stride, cnt, size = struct.unpack_from('<IIII', b, 4)
    assert ver == 1 and stride == RECORD, (ver, stride)
    raw = m2pack.mcoz_decode(b[20:], ITEM_KEY)
    return ver, dict((struct.unpack_from('<I', raw, i * RECORD)[0], raw[i * RECORD:(i + 1) * RECORD])
                     for i in range(cnt))


def applies(rec):
    return [list(struct.unpack_from('<Bi', rec, APPLY_OFF + 5 * i)) for i in range(3)]


def proto(ver, recs):
    import m2pack
    blob = m2pack.mcoz_encode(b''.join(recs[v] for v in sorted(recs)), ITEM_KEY)
    return b'MIPX' + struct.pack('<IIII', ver, RECORD, len(recs), len(blob)) + blob


def make(item_proto):
    data = json.load(open(DATA))
    ver, recs = records(item_proto)
    glob_, mine, report = {}, {}, dict(items=len(data), missing=[], ranged=[], client_not_mt2009=[])
    for k, d in sorted(data.items(), key=lambda x: int(x[0])):
        v = int(k)
        rec = recs.get(v)
        if rec is None:
            report['missing'].append(v)
            continue
        if struct.unpack_from('<I', rec, 4)[0]:
            report['ranged'].append(v)     # a vnum range would be listed twice in the exe's range list
            continue
        if applies(rec) != d['mt2009']:
            report['client_not_mt2009'].append(v)   # the client's record differs from the server's mt2009 row
        r = bytearray(rec)
        for i, (t, val) in enumerate(d['glob']):
            struct.pack_into('<Bi', r, APPLY_OFF + 5 * i, t, val)
        glob_[v] = bytes(r)
        mine[v] = rec
    report['written'] = len(glob_)
    return {NAMES[0]: proto(ver, glob_), NAMES[1]: proto(ver, mine)}, report


def main():
    import m2pack
    import packlib
    args = [a for a in sys.argv[1:] if not a.startswith('--')]
    check = '--check' in sys.argv
    base, out = args[:2]
    rd = packlib.rd

    def src_of(pack):
        return out if os.path.exists(os.path.join(out, pack + '.index')) else base

    f, v, dents = m2pack.read_index(os.path.join(src_of('dbdata'), 'dbdata.index'))
    ddat = rd(os.path.join(src_of('dbdata'), 'dbdata.data'))
    ip = m2pack.read_entry(ddat, [e for e in dents if e['name'] == 'gamedata/item_proto'][0])
    files, report = make(ip)

    src = src_of('gamedata')
    f, v, ents = m2pack.read_index(os.path.join(src, 'gamedata.index'))
    dat = rd(os.path.join(src, 'gamedata.data'))
    have = dict((e['name'], e) for e in ents)
    rep, add = {}, {}
    for n, b in files.items():
        if n in have:
            if m2pack.read_entry(dat, have[n]) != b:
                rep[n] = b
        else:
            add[n] = (b, 1)
    if not rep and not add:
        report['gamedata'] = 'unchanged'
    elif check:
        report['gamedata'] = dict(replace=sorted(rep), add=sorted(add))
    else:
        tmp_i, tmp_d = os.path.join(out, 'gamedata.index.pg'), os.path.join(out, 'gamedata.data.pg')
        r = packlib.repack_add_typed(os.path.join(src, 'gamedata.index'), os.path.join(src, 'gamedata.data'), rep, add,
                                     tmp_i, tmp_d, ents[-1]['raw'])
        os.replace(tmp_i, os.path.join(out, 'gamedata.index'))
        os.replace(tmp_d, os.path.join(out, 'gamedata.data'))
        f, v, nw = m2pack.read_index(os.path.join(out, 'gamedata.index'))
        nd = rd(os.path.join(out, 'gamedata.data'))
        got = {}
        for e in nw:
            assert zlib.crc32(nd[e['pos']:e['pos'] + e['size']]) & 0xffffffff == e['dcrc'], e['name']
            got[e['name']] = m2pack.read_entry(nd, e)
        for n, b in files.items():
            assert got[n] == b, n
        for e in ents:
            if e['name'] not in files:
                assert got[e['name']] == m2pack.read_entry(dat, e), e['name']
        # the global file read back: every record has the JSON's applies
        data = json.load(open(DATA))
        for vn, rec in records(got[NAMES[0]])[1].items():
            assert applies(rec) == data[str(vn)]['glob'], vn
        report['gamedata'] = dict(old=r[0], added=r[1], replaced=r[2], entries=len(nw))
    print(json.dumps(report, indent=1))


if __name__ == '__main__':
    main()
