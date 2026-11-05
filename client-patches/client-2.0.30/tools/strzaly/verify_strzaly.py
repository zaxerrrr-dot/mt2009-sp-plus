# -*- coding: utf-8 -*-
# MT2009_PLUS_ARROWS_GLOBAL_V1 - checks a built client: gamedata/item_proto (dbdata) carries 8000-8005, 8010-8012 and
# 30395 exactly as patch_strzaly_client.py leaves them (the arrows' wiki values, no fade, the quivers' 25 / 4 and their
# limits / prices, Plonaca Strzala), item_list.txt has 8011 / 8012 with 8010's icon (and that icon is in some pack), and
# itemdesc.txt has the four lines.
#   docker run --rm -v /opt/metin2:/opt/metin2 m2pack-lzo python3 <repo>/client-patches/client-2.0.30/tools/strzaly/verify_strzaly.py \
#     <OUT pack dir> [<BASE pack dir>]
# The last line: "strzaly verify: N checks, 0 failures".
import os
import struct
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, '/opt/metin2/cache/tcm/tz')
sys.path.insert(0, '/opt/metin2/cache/arezzo-work/client/az58')
sys.path.insert(0, HERE)


def main():
    import m2pack
    import packlib
    import patch_strzaly_client as pc
    out = sys.argv[1]
    base = sys.argv[2] if len(sys.argv) > 2 else '/opt/metin2/cache/c55/pack'
    checks, fails = [0], []

    def ok(cond, what):
        checks[0] += 1
        if not cond:
            fails.append(what)

    names = {}
    for d in (base, out):
        if not os.path.isdir(d):
            continue
        for p in sorted(f[:-6] for f in os.listdir(d) if f.endswith('.index')):
            if d == base and os.path.exists(os.path.join(out, p + '.index')):
                continue
            for e in m2pack.read_index(os.path.join(d, p + '.index'))[2]:
                names[e['name']] = (d, p, e)
    dat = {}

    def entry(n):
        d, p, e = names[n]
        if (d, p) not in dat:
            dat[(d, p)] = packlib.rd(os.path.join(d, p + '.data'))
        return m2pack.read_entry(dat[(d, p)], e)

    n = 'gamedata/item_proto'
    ok(n in names, 'no %s' % n)
    if n in names:
        ver, stride, recs = pc.records(entry(n))
        for v in pc.ALL:
            ok(v in recs, 'item_proto: no %d' % v)
            if v in recs:
                tmpl = recs[v] if v not in pc.NEW_QUIVERS else recs.get(pc.QUIVER, recs[v])
                ok(pc.want(v, recs[v]) == recs[v], 'item_proto %d: not as the patch leaves it' % v)
                if v in pc.NEW_QUIVERS:
                    # the copy keeps 8010's flags, wear and level floor
                    ok(recs[v][74:98] == tmpl[74:98] and recs[v][119:124] == tmpl[119:124],
                       'item_proto %d: not a copy of %d' % (v, pc.QUIVER))
                    ok(struct.unpack_from('<Bi', recs[v], 114) == (7, pc.NEW_QUIVERS[v][0]), 'item_proto %d: limit' % v)
        for v, (level, magic, attack) in pc.ARROWS.items():
            if v in recs:
                ok(struct.unpack_from('<6i', recs[v], 139) == (0, magic, 0, attack, 0, 0), 'item_proto %d: values' % v)
    for n, rows in (('gamedata/item_list.txt', pc.list_rows()), ('locale/pl/itemdesc.txt', pc.desc_rows())):
        ok(n in names, 'no %s' % n)
        if n in names:
            lines = entry(n).decode('cp1250').replace('\r\n', '\n').split('\n')
            for row in rows:
                ok(lines.count(row) == 1, '%s: %r x%d' % (n, row.split('\t')[0], lines.count(row)))
    ok(pc.ICON in names, 'no icon %s in any pack' % pc.ICON)
    for f in fails:
        print('FAIL', f)
    print('strzaly verify: %d checks, %d failures' % (checks[0], len(fails)))


if __name__ == '__main__':
    main()
