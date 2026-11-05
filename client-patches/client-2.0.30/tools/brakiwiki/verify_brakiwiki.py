# -*- coding: utf-8 -*-
# MT2009_PLUS_BRAKI_WIKI_V1 - checks a built client: gamedata/item_proto (dbdata) carries Tajemniczy Talizman+0..+9
# (81560-81569) and Rekawice Weza 23050-23089 exactly as patch_brakiwiki_client.py leaves them (81560 -> 81561 ...
# 81568 -> 81569, the gloves' level 120, Obrona value1 16 / value5 0..20, 3 sockets), item_list.txt and itemdesc.txt
# have their lines (and 31244 / 50336's texts, without "Na razie bez zastosowania"), every icon they name is in some
# pack, and root/yoharagear.py knows the serpent gloves (when the root pack is there).
#   docker run --rm -v /opt/metin2:/opt/metin2 m2pack-lzo python3 <repo>/client-patches/client-2.0.30/tools/brakiwiki/verify_brakiwiki.py \
#     <OUT pack dir> [<BASE pack dir>]
# The last line: "brakiwiki verify: N checks, 0 failures".
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
    import patch_brakiwiki_client as pc
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

    d = pc.items_json()
    n = 'gamedata/item_proto'
    ok(n in names, 'no %s' % n)
    if n in names:
        ver, recs = pc.records(entry(n))
        want = pc.want_records(recs)
        for w in d['items']:
            v = w['vnum']
            ok(recs.get(v) == want[v], 'item_proto %d: not as the patch leaves it' % v)
            if v in recs:
                r = recs[v]
                ok(struct.unpack_from('<I', r, 175)[0] == (v + 1 if v % 10 < 9 else 0), 'item_proto %d: next item' % v)
                ok(struct.unpack_from('<Bi', r, 114) == (1, 120), 'item_proto %d: level 120' % v)
                if 23050 <= v <= 23089:
                    vals = struct.unpack_from('<6i', r, 139)
                    ok(vals[1] == 16 and vals[5] == (0, 1, 2, 4, 6, 8, 10, 12, 14, 20)[v % 10], 'item_proto %d: Obrona' % v)
                    ok(r[183] == 3, 'item_proto %d: 3 sockets' % v)
    for n, rows in (('gamedata/item_list.txt', pc.list_rows()), ('locale/pl/itemdesc.txt', pc.desc_rows())):
        ok(n in names, 'no %s' % n)
        if n in names:
            lines = entry(n).decode('cp1250').replace('\r\n', '\n').split('\n')
            for row in rows:
                ok(lines.count(row) == 1, '%s: %r x%d' % (n, row.split('\t')[0], lines.count(row)))
                ok('bez zastosowania' not in row, '%s: %r still "bez zastosowania"' % (n, row.split('\t')[0]))
    for icon in sorted(set(r.split('\t')[2] for r in pc.list_rows())):
        ok(icon in names, 'no icon %s in any pack' % icon)
    n = 'yoharagear.py'
    if n in names:
        t = entry(n).decode('latin-1')
        ok('MT2009_PLUS_BRAKI_WIKI_V1' in t and '23050: 184' in t, 'root yoharagear.py: no serpent gloves')
    for f in fails:
        print('FAIL', f)
    print('brakiwiki verify: %d checks, %d failures' % (checks[0], len(fails)))


if __name__ == '__main__':
    main()
