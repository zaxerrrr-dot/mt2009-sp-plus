# -*- coding: utf-8 -*-
# MT2009_PLUS_RIPOSTY_V1 - checks a built client for Riposty i Dopalacze (build_yriposty_packs.py):
#   - pack/Index names "yriposty", under the 29 MB zip limit;
#   - every icon the skilldesc rows name (ui/skill/passive/<icon>_01..03.sub) is in the client, its atlas too
#     (skill9_assassin.dds - the yskill9 pack's, yriposty_pahe.dds - ours);
#   - dbdata: locale/pl/skilldesc.txt and gamedata/skilltable.txt carry the rows 221-228 / 236-243 exactly as
#     patch_yriposty_client.py writes them, once each;
#   - the root pack has riposty.py, and playersettingmodule / uicharacter / uitooltip call it.
#   docker run --rm -v /opt/metin2:/opt/metin2 m2pack-lzo python3 <repo>/client-patches/client-2.0.30/tools/yriposty/verify_yriposty.py \
#     <OUT pack dir> [<BASE pack dir>]
# The last line: "yriposty verify: N checks, 0 failures".
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, '/opt/metin2/cache/tcm/tz')
sys.path.insert(0, '/opt/metin2/cache/arezzo-work/client/az58')
sys.path.insert(0, HERE)
ZIP_LIMIT = 29 * 1024 * 1024


def main():
    import m2pack
    import packlib
    import patch_yriposty_client as pc
    out = sys.argv[1]
    base = sys.argv[2] if len(sys.argv) > 2 else '/opt/metin2/cache/c55/pack'
    rd = packlib.rd
    checks, fails = [0], []

    def ok(cond, what):
        checks[0] += 1
        if not cond:
            fails.append(what)

    names = {}
    for d in (base, out):
        for p in sorted(f[:-6] for f in os.listdir(d) if f.endswith('.index')):
            if d == base and os.path.exists(os.path.join(out, p + '.index')):
                continue
            for e in m2pack.read_index(os.path.join(d, p + '.index'))[2]:
                names[e['name']] = (d, p, e)
    dat = {}

    def entry(n):
        d, p, e = names[n]
        if (d, p) not in dat:
            dat[(d, p)] = rd(os.path.join(d, p + '.data'))
        return m2pack.read_entry(dat[(d, p)], e)

    ix = rd(os.path.join(out, 'Index')).replace(b'\r\n', b'\n').split(b'\n')
    ok(b'yriposty' in ix, 'Index: no yriposty')
    ok(os.path.exists(os.path.join(out, 'yriposty.index')), 'no pack yriposty in OUT')
    if os.path.exists(os.path.join(out, 'yriposty.data')):
        ok(os.path.getsize(os.path.join(out, 'yriposty.data')) < ZIP_LIMIT, 'yriposty over 29 MB')
    for icon in pc.ICONS:
        for g in (1, 2, 3):
            k = 'd:/ymir work/ui/skill/passive/%s_0%d.sub' % (icon, g)
            ok(k in names, '%s missing' % k)
            if k in names:
                m = re.search(r'^image\s+"([^"]+)"', entry(k).decode('latin-1'), re.M | re.I)
                ok(m and ('d:/ymir work/ui/' + m.group(1).lower()) in names, '%s: atlas missing' % k)
    for n, fn in (('locale/pl/skilldesc.txt', pc.skilldesc), ('gamedata/skilltable.txt', pc.skilltable)):
        ok(n in names, 'dbdata: no %s' % n)
        if n in names:
            b = entry(n)
            ok(fn(b)[1] is False, '%s: the rows 221-243 are not the patch\'s' % n)
            rows = [l.split('\t')[0] for l in b.decode('cp1250').split('\r\n')]
            for v in pc.VNUMS:
                ok(rows.count(str(v)) == 1, '%s: row %d x%d' % (n, v, rows.count(str(v))))
    ok('riposty.py' in names, 'root: no riposty.py')
    for f, what in (('playersettingmodule.py', 'riposty.RegisterSlots'), ('uicharacter.py', 'riposty.SourceSlot'),
                    ('uitooltip.py', 'riposty.AppendToolTip')):
        ok(f in names and what.encode() in entry(f), 'root %s: no %s' % (f, what))
    for f in fails:
        print('FAIL', f)
    print('yriposty verify: %d checks, %d failures' % (checks[0], len(fails)))


if __name__ == '__main__':
    main()
