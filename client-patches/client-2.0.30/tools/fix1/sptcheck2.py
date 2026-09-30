import sys, os, re, json, struct
sys.path.insert(0, '/opt/metin2/cache/tcm/tz'); sys.path.insert(0, '/opt/metin2/cache/arezzo-work/client/az58')
import m2pack, gfres
BASE = '/opt/metin2/cache/tcm/c30/pack'
PACK = {}
for p in sorted(f[:-6] for f in os.listdir(BASE) if f.endswith('.index')):
    f, v, ents = m2pack.read_index(BASE + '/%s.index' % p); data = open(BASE + '/%s.data' % p, 'rb').read()
    for e in ents: PACK.setdefault(e['name'], (p, data, e))
def raw(k): p, d, e = PACK[k]; return m2pack.read_entry(d, e)
PRE = gfres.load_ours('/opt/metin2/cache/tcm/gf28/ourpacks_pre.txt'); GF = gfres.GF
AZ = '/opt/metin2/cache/arezzo/cpack/files/'
TAGS = {2000: 'branch', 20002: 'composite', 17749: 'shadow'}
def strings(b):
    out = []
    for tag, name in TAGS.items():
        for m in re.finditer(re.escape(struct.pack('<I', tag)), b):
            i = m.end()
            if i + 4 > len(b): continue
            n = struct.unpack('<i', b[i:i + 4])[0]
            if 1 <= n <= 300:
                s = b[i + 4:i + 4 + n]
                if all(32 <= c < 127 or c >= 128 for c in s) and re.search(rb'[A-Za-z]', s):
                    out.append((name, s.decode('latin1')))
    return out
res = {}
for k in sorted(PACK):
    if not k.endswith('.spt'): continue
    b = raw(k); d = k.rsplit('/', 1)[0] + '/'
    row = {}
    for name, s in strings(b):
        base = re.split(r'[\\/]', s)[-1]
        base = base.rsplit('.', 1)[0] if '.' in base else base
        cand = (d + base + '.dds').lower()
        w = 'pack' if cand in PACK else ('pre' if cand in PRE else ('GF' if cand in GF else ('AZ' if os.path.exists(AZ + cand[3:]) else 'MISSING')))
        row[name] = (cand, w)
    res[k] = row
    if PACK[k][0].startswith('az_') or any(v[1] not in ('pack', 'pre') for v in row.values()):
        print(PACK[k][0], k, {n: v[0].rsplit('/', 1)[1] + ':' + v[1] for n, v in row.items()})
json.dump(res, open('/opt/metin2/cache/arezzo-work/client/fix1/sptcheck2.json', 'w'), indent=1)
