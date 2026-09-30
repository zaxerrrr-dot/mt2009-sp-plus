# For every Arezzo directory we took files from: the files there that no pack of ours has (c30 + base listing).
import sys, os, json, collections
sys.path.insert(0, '/opt/metin2/cache/tcm/tz'); sys.path.insert(0, '/opt/metin2/cache/arezzo-work/client/az58')
import m2pack, gfres
BASE = '/opt/metin2/cache/tcm/c30/pack'
NAMES = set()
for p in sorted(f[:-6] for f in os.listdir(BASE) if f.endswith('.index')):
    f, v, ents = m2pack.read_index(BASE + '/%s.index' % p)
    for e in ents: NAMES.add(e['name'])
PRE = gfres.load_ours('/opt/metin2/cache/tcm/gf28/ourpacks_pre.txt')
AZ = '/opt/metin2/cache/arezzo/cpack/files/'
used = collections.defaultdict(set)
for fj in ('/opt/metin2/cache/arezzo-work/client/az29/final.json', '/opt/metin2/cache/arezzo-work/client/az58/final58.json'):
    for pack, m in json.load(open(fj))['add'].items():
        for k, src in m.items():
            if src.startswith(AZ) and k.startswith('d:/ymir work/'):
                used[os.path.dirname(src)].add(pack)
res = {}
for d, packs in sorted(used.items()):
    miss = []
    for f in sorted(os.listdir(d)):
        full = os.path.join(d, f)
        if not os.path.isfile(full): continue
        key = gfres.norm('d:/' + full[len(AZ):])
        if key not in NAMES and key not in PRE:
            miss.append((key, os.path.getsize(full)))
    if miss:
        res[d[len(AZ):]] = {'packs': sorted(packs), 'missing': miss}
tot = 0
for d, v in res.items():
    s = sum(x[1] for x in v['missing']); tot += s
    exts = collections.Counter(os.path.splitext(x[0])[1] for x in v['missing'])
    print('%-70s %-22s %4d files %7.1f KB %s' % (d, ','.join(v['packs']), len(v['missing']), s / 1024, dict(exts)))
print('TOTAL %.1f MB' % (tot / 1048576))
json.dump(res, open('/opt/metin2/cache/arezzo-work/client/fix1/dirsweep.json', 'w'), indent=1)
