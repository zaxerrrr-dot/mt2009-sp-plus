# Which SpeedTree textures the exe will ask for (spt dir + NoExtension(name) + ".dds") on the Arezzo maps, and where they are.
import sys, os, re, json, collections
sys.path.insert(0, '/opt/metin2/cache/tcm/tz'); sys.path.insert(0, '/opt/metin2/cache/arezzo-work/client/az58')
import m2pack, gfres
BASE = '/opt/metin2/cache/tcm/c30/pack'
PACK = {}
for p in sorted(f[:-6] for f in os.listdir(BASE) if f.endswith('.index')):
    f, v, ents = m2pack.read_index(BASE + '/%s.index' % p); data = open(BASE + '/%s.data' % p, 'rb').read()
    for e in ents: PACK.setdefault(e['name'], (p, data, e))
def raw(k): p, d, e = PACK[k]; return m2pack.read_entry(d, e)
PRE = gfres.load_ours('/opt/metin2/cache/tcm/gf28/ourpacks_pre.txt')
GF = gfres.GF
AZ = '/opt/metin2/cache/arezzo/cpack/files/'
def azfile(k):
    p = AZ + k.replace('d:/ymir work/', 'ymir work/')
    return p if os.path.exists(p) else None
PROP = {}
for k in PACK:
    if k.startswith('property/'):
        b = raw(k).replace(b'\r', b'')
        l = b.split(b'\n')
        if l and l[0].strip() == b'YPRT' and len(l) > 1:
            try: PROP[int(l[1].strip())] = b.decode('latin1')
            except ValueError: pass
MAPS = ['natural_map', 'plechito_wukong_dungeon', 'plechito_easter2023_dungeon', 'plechito_scorpion_dungeon', 'metin2_map_exp', 'metin2_map_pustynia', 'plechito_chamber_of_wisdom']
RE = re.compile(rb'[\x20-\x7e]{3,200}?\.(?:tga|dds|bmp)', re.I)
out = {}
for m in MAPS:
    crcs = collections.Counter()
    for k in PACK:
        if k.startswith('maps/%s/' % m) and k.endswith('/areadata.txt'):
            for line in raw(k).decode('latin1').split('\n'):
                pass
            t = raw(k).decode('latin1').replace('\r', '').split('\n')
            for i, line in enumerate(t):
                if line.startswith('Start Object'):
                    try: crcs[int(t[i + 2].strip())] += 1
                    except (ValueError, IndexError): pass
    spts = collections.Counter(); kinds = collections.Counter()
    for c, n in crcs.items():
        pr = PROP.get(c)
        if not pr: kinds['noprop'] += n; continue
        mt = re.search(r'propertytype\s+"?(\w+)', pr, re.I); kinds[mt.group(1) if mt else '?'] += n
        ms = re.search(r'treefile\s+"([^"]+)"', pr, re.I)
        if ms: spts[gfres.norm(ms.group(1))] += n
    res = {'kinds': dict(kinds), 'spt': {}}
    for s, n in spts.items():
        d = s.rsplit('/', 1)[0] + '/'
        where_spt = 'pack' if s in PACK else ('pre' if s in PRE else ('gf' if s in GF else 'MISSING'))
        tex = {}
        if s in PACK:
            for x in set(RE.findall(raw(s))):
                x = x.decode('latin1').replace('\\', '/')
                base = x.rsplit('/', 1)[-1]
                cand = (d + base.rsplit('.', 1)[0] + '.dds').lower()
                tex[cand] = 'pack' if cand in PACK else ('pre' if cand in PRE else ('gf' if cand in GF else ('AZ-ONLY' if azfile(cand) else 'MISSING')))
        res['spt'][s] = {'objects': n, 'spt': where_spt, 'tex': tex}
    out[m] = res
json.dump(out, open('/opt/metin2/cache/arezzo-work/client/fix1/sptcheck.json', 'w'), indent=1)
for m, r in out.items():
    print('==', m, r['kinds'])
    for s, v in r['spt'].items():
        bad = {k: w for k, w in v['tex'].items() if w not in ('pack', 'pre')}
        print('  ', v['objects'], s, v['spt'], 'BAD:' if bad else 'ok', bad if bad else '')
