# -*- coding: utf-8 -*-
# MT2009_PLUS_ARMOR105_V1 / MT2009_PLUS_GF_VALUES_V1 / MT2009_PLUS_GF_REFINE_V1 (client data) - the owner's package
# p-gf-po-3.0.1 in the client (the owner, 22 October 2026), the same data as the server:
#   dbdata   gamedata/item_proto     + the 209 records of tools/zbroje105/zbroje105.json (the level-105..115 armours, the
#                                      cyanite ones, their nine materials - every server column, the +9 -> cyanite step
#                                      on Seon-Pyeong's fixed recipe as zbroje105.sql); GF 25.2.17's magic_pct (record
#                                      offset 181), value0-5 (139) and level (limit 0's value, 115) of every item
#                                      tools/gfwartosci/gen_gfwartosci.py changes on the server (plan(): the same
#                                      exclusions - our generators' vnums stay); the fans' / Czarna Okragla Tarcza's
#                                      recipes and Pogromca+9 without a next item (refined_vnum 175, refine_set 179;
#                                      from the old value only)
#            locale/pl/itemdesc.txt  + the json's two descriptions (Padparadza, Boski Kwiat - in Polish)
#   gamedata gamedata/item_list.txt  + the json's 209 lines (the GF icons: client-patches/client-2.0.30/root/icon/item,
#                                      build57.py puts them into the root pack)
# BUILD ORDER: on the same OUT after yfinal and BEFORE refineglobal (it puts the owner's sheet's recipes - and
# Seon-Pyeong's fixed ones - on these records too) and protoglobal (it copies the final records) - clientY.sh:
#   docker run --rm -v /opt/metin2:/opt/metin2 m2pack-lzo python3 $T/gfint/build_gfint_pack.py \
#     $C/azbase $C/out/pack > $C/gfint.json
# --check measures only. Idempotent: a second run reports "unchanged". A record of a new vnum the client already has
# with other content stops the run (a collision).
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
sys.path.insert(0, os.path.join(REPO, 'tools', 'zbroje105'))
sys.path.insert(0, os.path.join(REPO, 'tools', 'gfwartosci'))
ITEM_KEY = (173217, 72619434, 408587239, 27973291)
RECORD = 184
NAME_PROTO, NAME_DESC, NAME_LIST = 'gamedata/item_proto', 'locale/pl/itemdesc.txt', 'gamedata/item_list.txt'
TEMPLATE = 20000            # Pancerz Diabel. Rogu+0: the bytes no column writes (all of them are written below)
LIMIT_LEVEL = 1


def fixed(b, size):
    assert len(b) < size, b
    return b + b'\0' * (size - len(b))


def record(template, w):
    """a full client record of one zbroje105.json row (the layout of tools/yohara/patch_yohara_client.py)"""
    r = bytearray(template)
    struct.pack_into('<II', r, 0, w['vnum'], 0)
    r[8:41] = fixed(w['name'].encode('latin-1'), 33)          # GF's bytes, as the server's row
    r[41:74] = fixed(w['locale_name'].encode('cp1250'), 33)
    struct.pack_into('<BBBB', r, 74, w['type'], w['subtype'], w['weight'], w['size'])
    struct.pack_into('<IIIII', r, 78, w['stack'], w['antiflag'], w['flag'], w['wearflag'], 0)
    struct.pack_into('<qq', r, 98, w['gold'], w['shop_buy_price'])
    struct.pack_into('<BiBi', r, 114, w['limittype0'], w['limitvalue0'], w['limittype1'], w['limitvalue1'])
    struct.pack_into('<BiBiBi', r, 124, w['applytype0'], w['applyvalue0'], w['applytype1'], w['applyvalue1'],
                     w['applytype2'], w['applyvalue2'])
    struct.pack_into('<6i', r, 139, *(w['value%d' % j] for j in range(6)))
    struct.pack_into('<3i', r, 163, 0, 0, 0)
    struct.pack_into('<IHBBB', r, 175, w['refined_vnum'], w['refine_set'], w['magic_pct'], w['specular'],
                     w['socket_pct'])
    return bytes(r)


def patch_proto(b, rep):
    import m2pack
    import gen_zbroje105 as Z
    import gen_gfwartosci as G
    assert b[:4] == b'MIPX'
    ver, stride, cnt, size = struct.unpack_from('<IIII', b, 4)
    assert stride == RECORD, stride
    raw = m2pack.mcoz_decode(b[20:], ITEM_KEY)
    recs = dict((struct.unpack_from('<I', raw, i * RECORD)[0], bytearray(raw[i * RECORD:(i + 1) * RECORD]))
                for i in range(cnt))
    before = dict((v, bytes(r)) for v, r in recs.items())
    # 1. the level-105 armours
    d = Z.load()
    tpl = bytes(recs[TEMPLATE])
    for w in d['items']:
        new = record(tpl, w)
        old = recs.get(w['vnum'])
        if old is None:
            recs[w['vnum']] = bytearray(new)
            rep['added'] += 1
        elif bytes(old)[:98] != new[:98]:         # the identity (names, type, flags) - the rest may be refined later
            raise SystemExit('item_proto: %d is another item here (collision)' % w['vnum'])
    # 2. GF's values
    items, mobs, skipped = G.plan()
    for v, cols in sorted(items.items()):
        r = recs.get(v)
        if r is None:
            rep['values_no_record'].append(v)
            continue
        for c, (gf, ours) in cols.items():
            gf = int(gf)
            if c == 'magic_pct':
                r[181] = gf
            elif c.startswith('value'):
                struct.pack_into('<i', r, 139 + 4 * int(c[5]), gf)
            elif c == 'limitvalue0':
                if r[114] != LIMIT_LEVEL:
                    rep['level_not_limit0'].append(v)
                    continue
                struct.pack_into('<i', r, 115, gf)
            else:
                raise SystemExit('item_proto: no client field for %s' % c)
    # 3. the recipes of MT2009_PLUS_GF_REFINE_V1 (from the old value only)
    for v, cols in sorted(G.item_refine().items()):
        r = recs.get(v)
        if r is None:
            rep['refine_no_record'].append(v)
            continue
        nxt, rset = struct.unpack_from('<IH', r, 175)
        cur = {'refined_vnum': nxt, 'refine_set': rset}
        new = dict(cur)
        for c, (n, o) in cols.items():
            if cur[c] == o:
                new[c] = n
            elif cur[c] != n:
                rep['refine_other'].append([v, c, cur[c]])
        struct.pack_into('<IH', r, 175, new['refined_vnum'], new['refine_set'])
    rep['changed'] = sum(1 for v, r in recs.items() if before.get(v) != bytes(r))
    if not rep['changed']:
        return b
    blob = m2pack.mcoz_encode(b''.join(bytes(recs[v]) for v in sorted(recs)), ITEM_KEY)
    return b'MIPX' + struct.pack('<IIII', ver, RECORD, len(recs), len(blob)) + blob


def patch_lines(b, want, rep, key):
    """every line whose first column is one of want's keys becomes want's line (or it is appended); the file's line
    ends kept"""
    text = b.decode('cp1250')
    nl = '\r\n' if '\r\n' in text else '\n'
    lines = text.split(nl)
    tail = lines and lines[-1] == ''
    if tail:
        lines.pop()
    seen = set()
    for i, line in enumerate(lines):
        k = line.split('\t')[0].strip()
        if k in want:
            seen.add(k)
            if line != want[k]:
                lines[i] = want[k]
                rep[key] += 1
    for k in sorted(set(want) - seen, key=int):
        lines.append(want[k])
        rep[key] += 1
    return (nl.join(lines) + (nl if tail else '')).encode('cp1250')


def repack(pack, base, out, files, check):
    import m2pack
    import packlib
    src = out if os.path.exists(os.path.join(out, pack + '.index')) else base
    f, v, ents = m2pack.read_index(os.path.join(src, pack + '.index'))
    dat = packlib.rd(os.path.join(src, pack + '.data'))
    have = dict((e['name'], e) for e in ents)
    new = dict((n, fn(m2pack.read_entry(dat, have[n]))) for n, fn in files.items())
    rep = dict((n, b) for n, b in new.items() if b != m2pack.read_entry(dat, have[n]))
    if not rep:
        return 'unchanged'
    if check:
        return dict(replace=sorted(rep))
    tmp_i, tmp_d = os.path.join(out, pack + '.index.gi'), os.path.join(out, pack + '.data.gi')
    r = packlib.repack_add_typed(os.path.join(src, pack + '.index'), os.path.join(src, pack + '.data'), rep, {},
                                 tmp_i, tmp_d, ents[-1]['raw'])
    os.replace(tmp_i, os.path.join(out, pack + '.index'))
    os.replace(tmp_d, os.path.join(out, pack + '.data'))
    f, v, nw = m2pack.read_index(os.path.join(out, pack + '.index'))
    nd = packlib.rd(os.path.join(out, pack + '.data'))
    for e in nw:
        assert zlib.crc32(nd[e['pos']:e['pos'] + e['size']]) & 0xffffffff == e['dcrc'], (pack, e['name'])
        got = m2pack.read_entry(nd, e)
        assert got == (rep[e['name']] if e['name'] in rep else m2pack.read_entry(dat, have[e['name']])), e['name']
    return dict(old=r[0], added=r[1], replaced=r[2], entries=len(nw))


def main():
    import gen_zbroje105 as Z
    args = [a for a in sys.argv[1:] if not a.startswith('--')]
    check = '--check' in sys.argv
    base, out = args[:2]
    d = Z.load()
    rep = dict(added=0, changed=0, values_no_record=[], level_not_limit0=[], refine_no_record=[], refine_other=[],
               itemdesc=0, item_list=0)
    rep['dbdata'] = repack('dbdata', base, out, {
        NAME_PROTO: lambda b: patch_proto(b, rep),
        NAME_DESC: lambda b: patch_lines(b, d['itemdesc'], rep, 'itemdesc')}, check)
    rep['gamedata'] = repack('gamedata', base, out, {
        NAME_LIST: lambda b: patch_lines(b, d['item_list'], rep, 'item_list')}, check)
    print(json.dumps(rep, indent=1))


if __name__ == '__main__':
    main()
