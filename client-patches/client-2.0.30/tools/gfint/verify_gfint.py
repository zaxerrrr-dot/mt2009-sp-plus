# -*- coding: utf-8 -*-
# MT2009_PLUS_ARMOR105_V1 / MT2009_PLUS_GF_VALUES_V1 (client data) - checks a built OUT (after every step of clientY.sh)
# against the server's data: the 209 records of tools/zbroje105 (every byte but the recipe, which refineglobal sets),
# their item_list lines and the two itemdesc lines, GF's magic_pct / value0-5 / level of tools/gfwartosci's plan, the
# recipes of MT2009_PLUS_GF_REFINE_V1 and Seon-Pyeong's +9 -> cyanite step.
#   docker run --rm -v /opt/metin2:/opt/metin2 m2pack-lzo python3 $T/gfint/verify_gfint.py $C/out/pack
import os
import struct
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import build_gfint_pack as B  # noqa: E402  (paths, record layout)


def main():
    import m2pack
    import packlib
    import gen_zbroje105 as Z
    import gen_gfwartosci as G
    out = sys.argv[1]
    bad = []

    def entry(pack, name):
        f, v, e = m2pack.read_index(os.path.join(out, pack + '.index'))
        d = packlib.rd(os.path.join(out, pack + '.data'))
        return m2pack.read_entry(d, [x for x in e if x['name'] == name][0])

    b = entry('dbdata', B.NAME_PROTO)
    ver, stride, cnt, size = struct.unpack_from('<IIII', b, 4)
    raw = m2pack.mcoz_decode(b[20:], B.ITEM_KEY)
    recs = dict((struct.unpack_from('<I', raw, i * B.RECORD)[0], raw[i * B.RECORD:(i + 1) * B.RECORD])
                for i in range(cnt))
    d = Z.load()
    tpl = recs[B.TEMPLATE]
    for w in d['items']:
        r = recs.get(w['vnum'])
        want = B.record(tpl, w)
        if r is None:
            bad.append('no record %d' % w['vnum'])
        elif r[:175] != want[:175] or r[181:] != want[181:]:
            bad.append('record %d differs' % w['vnum'])
        elif w['refine_set'] >= 39900 and r[175:181] != want[175:181]:
            bad.append('record %d: not Seon-Pyeong\'s step' % w['vnum'])
    items, mobs, skipped = G.plan()
    for v, cols in items.items():
        r = recs.get(v)
        if r is None:
            continue
        for c, (gf, ours) in cols.items():
            got = (r[181] if c == 'magic_pct' else struct.unpack_from('<i', r, 139 + 4 * int(c[5]))[0]
                   if c.startswith('value') else struct.unpack_from('<i', r, 115)[0])
            if got != int(gf):
                bad.append('%d %s %d (GF %s)' % (v, c, got, gf))
    for v, cols in G.item_refine().items():
        nxt, rset = struct.unpack_from('<IH', recs[v], 175)
        cur = {'refined_vnum': nxt, 'refine_set': rset}
        if v == 3189 and cur != {'refined_vnum': 0, 'refine_set': 0}:
            bad.append('3189 still goes on: %r' % cur)
    il = entry('gamedata', B.NAME_LIST).decode('cp1250').replace('\r\n', '\n').split('\n')
    have = set(l.strip() for l in il)
    bad += ['item_list: no %s' % k for k, l in d['item_list'].items() if l not in have]
    desc = entry('dbdata', B.NAME_DESC).decode('cp1250').replace('\r\n', '\n').split('\n')
    have = set(desc)
    bad += ['itemdesc: no %s' % k for k, l in d['itemdesc'].items() if l not in have]
    print('gfint: %d records, %d items with GF values, %d problems' % (len(d['items']), len(items), len(bad)))
    for x in bad[:40]:
        print('  ' + x)
    sys.exit(1 if bad else 0)


if __name__ == '__main__':
    main()
