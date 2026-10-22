# -*- coding: utf-8 -*-
# MT2009_PLUS_237_GLOBAL_MODE_V1 (client data, the 2.x line) - the tooltips and the refine checks of the server's
# M2_BONUS_MODE=global (the owner, 22 October 2026: "the whole global setting in env"). The client's item_proto (dbdata
# pack, gamedata/item_proto) keeps the mt2009 values; this step writes two small item_protos into the "gamedata" pack
# (not dbdata: the panel's database editor zips replace dbdata), which root protoglobal.py loads over the table when
# the server says "BonusMode 1" / "BonusMode 0" at login (game.py, quest zywioly):
#   gamedata/item_proto_global  the client's own record of every item global mode changes, with
#                               * the fixed applies of tools/protoglobal/item_proto_global.json (offset 124, 3 x type
#                                 BYTE + value LONG) - not an item that needs a point the 2.x engine lacks (>= 184),
#                                 as apply.sh leaves those;
#                               * the refine step of the owner's upgrade sheet (offset 175: refined_vnum DWORD, refine_set
#                                 WORD) by the server's rule (tools/globalmode/gen_globalmode_2x.py): a step with a chance,
#                                 the item, its result and every material in the client's item_proto, the item's next
#                                 item the sheet's (or none for a "+9 -> next item" step); Seon-Pyeong's steps left out;
#   gamedata/item_proto_mt2009  the same records as the client's item_proto has them.
# The exe's item.LoadItemTable(<file>) overwrites the records of the vnums it has (CItemData::SetItemTableData); a
# client without these files keeps showing mt2009 (the server counts global anyway).
# Run on the same OUT after every step that writes gamedata/item_proto (the last of the item steps of the 2.x build,
# e.g. after wikinowe/build_wikinowe_pack.py in client67.sh):
#   docker run --rm -v /opt/metin2:/opt/metin2 m2pack-lzo python3 $T/globalmode/build_globalmode_pack.py \
#     $C/azbase $C/out/pack > $C/globalmode.json
# --check measures only. Idempotent: a second run reports "unchanged".
import json
import os
import struct
import sys
import zlib

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.normpath(os.path.join(HERE, '..', '..', '..', '..'))
sys.path.insert(0, os.path.join(HERE, '..', 'protoglobal'))
sys.path.insert(0, os.path.join(REPO, 'tools', 'refineglobal'))
import build_protoglobal_pack as P  # noqa: E402  (records, applies, proto; it sets the m2pack paths)

MAX_POINT = 184          # the 2.x engine's POINT_MAX_NUM (183 = POINT_ENCHANT_DARK)
REFINE_OFF = 175


def make(item_proto):
    import gen_refineglobal as R
    data = json.load(open(P.DATA))
    ver, recs = P.records(item_proto)
    glob_ = {}
    rep = dict(applies=0, applies_missing=0, applies_ranged=0, applies_2x_point=0, refine=0, refine_no_item=0,
               refine_no_result=0, refine_no_material=0, refine_other_next=0, refine_same=0, elite_left_out=0)

    def rec_of(v):
        if v not in glob_:
            glob_[v] = bytearray(recs[v])
        return glob_[v]

    for k, d in sorted(data.items(), key=lambda x: int(x[0])):
        v = int(k)
        if v not in recs:
            rep['applies_missing'] += 1
            continue
        if struct.unpack_from('<I', recs[v], 4)[0]:
            rep['applies_ranged'] += 1         # a vnum range would be listed twice in the exe's range list
            continue
        if any(t >= MAX_POINT for t, val in d['glob']):
            rep['applies_2x_point'] += 1
            continue
        r = rec_of(v)
        for i, (t, val) in enumerate(d['glob']):
            struct.pack_into('<Bi', r, P.APPLY_OFF + 5 * i, t, val)
        rep['applies'] += 1
    recipes, steps, nochance = R.load()
    for s in steps:
        if R.ELITE_ID0 <= s['rid'] <= R.ELITE_ID_MAX:
            rep['elite_left_out'] += 1
            continue
        if s['src'] not in recs:
            rep['refine_no_item'] += 1
            continue
        if s['res'] not in recs:
            rep['refine_no_result'] += 1
            continue
        if any(v not in recs for v, c in s['mats']):
            rep['refine_no_material'] += 1
            continue
        if struct.unpack_from('<I', recs[s['src']], 4)[0]:
            continue
        nxt, rset = struct.unpack_from('<IH', recs[s['src']], REFINE_OFF)
        if not (nxt == s['res'] or (s['tr'] and nxt == 0)):
            rep['refine_other_next'] += 1
            continue
        if (nxt, rset) == (s['res'], s['rid']):
            rep['refine_same'] += 1
            continue
        struct.pack_into('<IH', rec_of(s['src']), REFINE_OFF, s['res'], s['rid'])
        rep['refine'] += 1
    glob_ = dict((v, bytes(r)) for v, r in glob_.items() if bytes(r) != recs[v])
    mine = dict((v, recs[v]) for v in glob_)
    rep['written'] = len(glob_)
    return {P.NAMES[0]: P.proto(ver, glob_), P.NAMES[1]: P.proto(ver, mine)}, rep


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
        tmp_i, tmp_d = os.path.join(out, 'gamedata.index.gm'), os.path.join(out, 'gamedata.data.gm')
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
        # both files read back: the same vnums, the mt2009 one equal to the client's item_proto
        g = P.records(got[P.NAMES[0]])[1]
        m = P.records(got[P.NAMES[1]])[1]
        full = P.records(ip)[1]
        assert sorted(g) == sorted(m)
        for vn, rec in m.items():
            assert rec == full[vn], vn
        report['gamedata'] = dict(old=r[0], added=r[1], replaced=r[2], entries=len(nw))
    print(json.dumps(report, indent=1))


if __name__ == '__main__':
    main()
