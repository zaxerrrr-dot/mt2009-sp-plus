# -*- coding: utf-8 -*-
# MT2009_PLUS_REFINE_GLOBAL_V1 (client data) - refining as on the global server for every item (the owner, 20 October
# 2026; server side: tools/refineglobal/gen_refineglobal.py -> refine_global.sql, apply.sh). The client's item_proto
# (dbdata pack, gamedata/item_proto) carries each item's next item and recipe (record offset 175: refined_vnum DWORD,
# refine_set WORD); the next item decides whether a scroll can be used on it (a "+9 -> next item" step the sheet adds).
# The same json and the same rule as the server: a step of the sheet with a chance, the item, its result and every
# material in the client's item_proto, and the item's next item the sheet's (or none for a "+9 -> next item" step) ->
# refined_vnum = the result, refine_set = the sheet's recipe id. Every other field stays.
# Runs on the same OUT after yfinal and BEFORE protoglobal (protoglobal copies the final records) - clientY.sh:
#   docker run --rm -v /opt/metin2:/opt/metin2 m2pack-lzo python3 $T/refineglobal/build_refineglobal_pack.py \
#     $C/azbase $C/out/pack > $C/refineglobal.json
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
REPO = os.path.normpath(os.path.join(HERE, '..', '..', '..', '..'))
sys.path.insert(0, os.path.join(REPO, 'tools', 'refineglobal'))
ITEM_KEY = (173217, 72619434, 408587239, 27973291)
RECORD = 184
REFINE_OFF = 175
NAME = 'gamedata/item_proto'


def patch(b):
    import m2pack
    import gen_refineglobal as G
    assert b[:4] == b'MIPX'
    ver, stride, cnt, size = struct.unpack_from('<IIII', b, 4)
    assert stride == RECORD, stride
    raw = bytearray(m2pack.mcoz_decode(b[20:], ITEM_KEY))
    pos = dict((struct.unpack_from('<I', raw, i * RECORD)[0], i * RECORD) for i in range(cnt))
    recipes, steps, nochance = G.load()
    rep = dict(steps=len(steps), no_item=0, no_result=0, no_material=0, other_next=0, same=0, changed=0, przemiana=0)
    for s in steps:
        off = pos.get(s['src'])
        if off is None:
            rep['no_item'] += 1
            continue
        if s['res'] not in pos:
            rep['no_result'] += 1
            continue
        if any(v not in pos for v, c in s['mats']):
            rep['no_material'] += 1
            continue
        nxt, rset = struct.unpack_from('<IH', raw, off + REFINE_OFF)
        if not (nxt == s['res'] or (s['tr'] and nxt == 0)):
            rep['other_next'] += 1
            continue
        if (nxt, rset) == (s['res'], s['rid']):
            rep['same'] += 1
            continue
        if nxt != s['res']:
            rep['przemiana'] += 1
        struct.pack_into('<IH', raw, off + REFINE_OFF, s['res'], s['rid'])
        rep['changed'] += 1
    if not rep['changed']:
        return b, rep
    blob = m2pack.mcoz_encode(bytes(raw), ITEM_KEY)
    return b'MIPX' + struct.pack('<IIII', ver, stride, cnt, len(blob)) + blob, rep


def main():
    import m2pack
    import packlib
    args = [a for a in sys.argv[1:] if not a.startswith('--')]
    check = '--check' in sys.argv
    base, out = args[:2]
    rd = packlib.rd
    pack = 'dbdata'
    src = out if os.path.exists(os.path.join(out, pack + '.index')) else base
    f, v, ents = m2pack.read_index(os.path.join(src, pack + '.index'))
    dat = rd(os.path.join(src, pack + '.data'))
    have = dict((e['name'], e) for e in ents)
    b = m2pack.read_entry(dat, have[NAME])
    nb, report = patch(b)
    if nb == b:
        report[pack] = 'unchanged'
    elif check:
        report[pack] = dict(replace=[NAME])
    else:
        rep = {NAME: nb}
        tmp_i, tmp_d = os.path.join(out, pack + '.index.rg'), os.path.join(out, pack + '.data.rg')
        r = packlib.repack_add_typed(os.path.join(src, pack + '.index'), os.path.join(src, pack + '.data'), rep, {},
                                     tmp_i, tmp_d, ents[-1]['raw'])
        os.replace(tmp_i, os.path.join(out, pack + '.index'))
        os.replace(tmp_d, os.path.join(out, pack + '.data'))
        f, v, nw = m2pack.read_index(os.path.join(out, pack + '.index'))
        nd = rd(os.path.join(out, pack + '.data'))
        for e in nw:
            assert zlib.crc32(nd[e['pos']:e['pos'] + e['size']]) & 0xffffffff == e['dcrc'], (pack, e['name'])
            got = m2pack.read_entry(nd, e)
            assert got == (rep[e['name']] if e['name'] in rep else m2pack.read_entry(dat, have[e['name']])), e['name']
        report[pack] = dict(old=r[0], added=r[1], replaced=r[2], entries=len(nw))
    print(json.dumps(report, indent=1))


if __name__ == '__main__':
    main()
