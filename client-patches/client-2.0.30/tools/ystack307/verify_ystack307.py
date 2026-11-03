# MT2009_PLUS_STACK307_V1 / MT2009_PLUS_EKWIPUNEK_KEYS_V1 / MT2009_PLUS_COLLECTOR_TOPAZ_V1 - checks a built client:
#   - gamedata/item_proto (dbdata): 50338-50343 stack (70434 left as it is) (STACKABLE, no ANTI_STACK, stack 200), 70434 without
#     its limit - exactly as patch_ystack307_client.py leaves them;
#   - the root pack: uiekwipunek.py routes the treasure boxes and keys to the chests (TREASURE_TYPES, IsKeyOnBox) and
#     uicollector.py takes Topaz Woli 72353.
#   docker run --rm -v /opt/metin2:/opt/metin2 m2pack-lzo python3 <repo>/client-patches/client-2.0.30/tools/ystack307/verify_ystack307.py \
#     <OUT pack dir> [<BASE pack dir>]
# The last line: "ystack307 verify: N checks, 0 failures".
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
    import patch_ystack307_client as pc
    out = sys.argv[1]
    base = sys.argv[2] if len(sys.argv) > 2 else '/opt/metin2/cache/c55/pack'
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
            dat[(d, p)] = packlib.rd(os.path.join(d, p + '.data'))
        return m2pack.read_entry(dat[(d, p)], e)

    n = 'gamedata/item_proto'
    ok(n in names, 'no %s' % n)
    if n in names:
        ver, stride, recs = pc.records(entry(n))
        seen = {}
        for r in recs:
            v = struct.unpack_from('<I', r, 0)[0]
            if v in pc.RULES:
                seen[v] = seen.get(v, 0) + 1
                ok(pc.want(r) == r, 'item_proto %d: not as the patch leaves it' % v)
        for v in pc.RULES:
            ok(seen.get(v) == 1, 'item_proto %d x%d' % (v, seen.get(v, 0)))
    for f, what in (('uiekwipunek.py', b'TREASURE_TYPES'), ('uiekwipunek.py', b'IsKeyOnBox(srcVnum, dstVnum)'),
                    ('uicollector.py', b'vnum == 72353')):
        ok(f in names and what in entry(f), 'root %s: no %s' % (f, what.decode()))
    for f in fails:
        print('FAIL', f)
    print('ystack307 verify: %d checks, %d failures' % (checks[0], len(fails)))


if __name__ == '__main__':
    main()
