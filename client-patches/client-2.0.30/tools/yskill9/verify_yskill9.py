# -*- coding: utf-8 -*-
# MT2009_PLUS_SKILL9_V1 - checks a built client for the 9th skills (build_yskill9_packs.py):
#   - pack/Index names every new pack of yskill9_manifest.json, each under the 29 MB zip limit;
#   - every motion of the 7 skills on the 8 race folders (pc/, pc2/ x 4 classes: <motion>.gr2 and the four grades'
#     .msa) is in a pack, and so is every file an .msa / .mse / .msf / .sub of the new packs names (effects, models,
#     textures, the icons' atlases) - in the new packs or anywhere else in the client (BASE + OUT, or the base packs'
#     listing ourpacks_pre.txt for the packs not on this host);
#   - dbdata: locale/pl/skilldesc.txt and gamedata/skilltable.txt carry the rows 176-182 (and Precyzja's 246) exactly
#     as patch_yskill9_client.py writes them; Precyzja's support icon hit_attribute.sub is there, its atlas too.
#   docker run --rm -v /opt/metin2:/opt/metin2 m2pack-lzo python3 <repo>/client-patches/client-2.0.30/tools/yskill9/verify_yskill9.py \
#     <OUT pack dir> [<BASE pack dir>]
# The last line: "yskill9 verify: N checks, 0 failures".
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, '/opt/metin2/cache/tcm/tz')
sys.path.insert(0, '/opt/metin2/cache/arezzo-work/client/az58')
sys.path.insert(0, HERE)
PRE_LST = '/opt/metin2/cache/tcm/gf28/ourpacks_pre.txt'
ZIP_LIMIT = 29 * 1024 * 1024
EXT = 'gr2|dds|tga|mse|msa|mss|wav|mde|msf|sub'
RE_Q = re.compile(r'"([^"\r\n]+\.(?:%s))"' % EXT, re.I)


def norm(p):
    p = p.replace('\\', '/').strip().lower()
    while '//' in p:
        p = p.replace('//', '/')
    return p


def main():
    import m2pack
    import packlib
    import patch_yskill9_client as pc
    out = sys.argv[1]
    base = sys.argv[2] if len(sys.argv) > 2 else '/opt/metin2/cache/c55/pack'
    man = json.load(open(os.path.join(HERE, 'yskill9_manifest.json'), encoding='utf-8'))
    rd = packlib.rd
    checks, fails = [0], []

    def ok(cond, what):
        checks[0] += 1
        if not cond:
            fails.append(what)

    names, src = {}, {}
    for d in (base, out):
        for p in sorted(f[:-6] for f in os.listdir(d) if f.endswith('.index')):
            if d == base and os.path.exists(os.path.join(out, p + '.index')):
                continue
            for e in m2pack.read_index(os.path.join(d, p + '.index'))[2]:
                names[e['name']] = (d, p, e)
    pre = set()
    for l in open(PRE_LST, encoding='utf-8', errors='replace'):
        t = l.rstrip('\n').split(' ', 3)
        if len(t) == 4:
            pre.add(norm(t[3]))
    have = set(names) | pre
    dat = {}

    def entry(n):
        d, p, e = names[n]
        if (d, p) not in dat:
            dat[(d, p)] = rd(os.path.join(d, p + '.data'))
        return m2pack.read_entry(dat[(d, p)], e)

    ix = rd(os.path.join(out, 'Index')).replace(b'\r\n', b'\n').split(b'\n')
    for p in man['new_packs']:
        ok(p.encode() in ix, 'Index: no %s' % p)
        ok(os.path.exists(os.path.join(out, p + '.index')), 'no pack %s in OUT' % p)
        if os.path.exists(os.path.join(out, p + '.data')):
            ok(os.path.getsize(os.path.join(out, p + '.data')) < ZIP_LIMIT, '%s over 29 MB' % p)
    for v, motions in man['motions'].items():
        for k in motions:
            ok(k in have, 'skill %s: motion %s missing' % (v, k))
    # what the new packs' text files name
    for p in man['new_packs']:
        for e in man['packs'][p]:
            k = e['name']
            ok(k in names, 'staged %s not in the client' % k)
            if k not in names or not k.endswith(('.msa', '.mse', '.msf', '.sub')):
                continue
            txt = entry(k).decode('latin-1')
            if k.endswith('.sub'):
                m = re.search(r'^image\s+"([^"]+)"', txt, re.M | re.I)
                ok(m and ('d:/ymir work/ui/' + norm(m.group(1))) in have, '%s: atlas missing' % k)
                continue
            for r in RE_Q.findall(txt):
                r = norm(r)
                if r.endswith('.psd'):
                    continue
                if not (r.startswith('d:/') or r.startswith('sound/')):
                    r = k.rsplit('/', 1)[0] + '/' + r
                ok(r in have, '%s names %s - not in the client' % (k, r))
    # dbdata rows
    for n, fn in (('locale/pl/skilldesc.txt', pc.skilldesc), ('gamedata/skilltable.txt', pc.skilltable)):
        ok(n in names, 'dbdata: no %s' % n)
        if n in names:
            b = entry(n)
            ok(fn(b)[1] is False, '%s: the rows 176-182/246 are not the patch\'s' % n)
            rows = [l.split('\t')[0] for l in b.decode('cp1250').split('\r\n')]
            for v in pc.ALL_VNUMS:
                ok(rows.count(str(v)) == 1, '%s: row %d x%d' % (n, v, rows.count(str(v))))
    # MT2009_PLUS_PRECISION_SKILL_V1: Precyzja's support icon and its atlas
    icon = pc.PRECISION_ICON
    ok(icon in names and entry(icon) == pc.PRECISION_ICON_SUB, '%s missing or not the patch\'s' % icon)
    ok('d:/ymir work/ui/skill9_common.dds' in have, '%s: atlas skill9_common.dds missing' % icon)
    for f in fails:
        print('FAIL', f)
    print('yskill9 verify: %d checks, %d failures' % (checks[0], len(fails)))


if __name__ == '__main__':
    main()
