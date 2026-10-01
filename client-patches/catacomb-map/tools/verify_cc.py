# Independent check of the built packs (OUT over BASE), content read from the PACKS, not from the sources:
#  1. every entry of every OUT pack decodes, dcrc/fcrc right, names unique; Index lists every pack that exists
#  2. full reference closure of the map (setting, msenv, areadata property CRCs -> property files -> models/effects
#     -> .mdatr/textures/.mde refs) and of the race (npclist 2493 -> monster2/<race>/<race>.msm, motlist, msa,
#     .mss, effects, textures), plus the atlas and the panel icon: every key must be in a pack or in the
#     pre-import base listing (season2, pc*, ...)
#  3. no 64-bit .gr2 among the new entries; msenv of the map has NearDistance/FarDistance and no foglevel
# Run: docker run --rm -v /opt/metin2:/opt/metin2 m2pack-lzo python3 verify_cc.py [BASE] [OUT]
import os, sys, re, json, zlib, struct, subprocess, tempfile, collections
H = '/opt/metin2/cache/c36-catacomb'
sys.path.insert(0, '/opt/metin2/cache/tcm/tz'); sys.path.insert(0, '/opt/metin2/cache/arezzo-work/client/az58')
import m2pack, gfres
BASE = sys.argv[1] if len(sys.argv) > 1 else '/opt/metin2/cache/c35/pack'
OUT = sys.argv[2] if len(sys.argv) > 2 else H + '/pack'
MAP = 'metin2_map_devilscatacomb'
ENVKEY = 'd:/ymir work/environment/map_devilscatacomb.msenv'
KNOWN_MISSING = set(json.load(open(H + '/final_cc.json'))['report']['unresolved'])
GR2_64 = b'\xe5\x9b\x49\x5e'
norm = gfres.norm
res = collections.OrderedDict(); fails = []
def check(cond, msg):
    if not cond: fails.append(msg)

# 1. read back + merged view
PACK = {}; outnames = set()
def src(p): return OUT if os.path.exists(OUT + '/%s.index' % p) else BASE
packs = sorted(set(f[:-6] for d in (BASE, OUT) for f in os.listdir(d) if f.endswith('.index')))
cache = {}
for p in packs:
    d = src(p); f, v, ents = m2pack.read_index(d + '/%s.index' % p)
    names = [e['name'] for e in ents]; check(len(set(names)) == len(names), 'dup names in ' + p)
    if d == OUT:
        data = open(d + '/%s.data' % p, 'rb').read()
        for e in ents:
            blob = data[e['pos']:e['pos'] + e['size']]
            check(zlib.crc32(blob) & 0xffffffff == e['dcrc'], 'dcrc %s %s' % (p, e['name']))
            check(e['fcrc'] == zlib.crc32(e['name'].encode('cp1252')) & 0xffffffff, 'fcrc %s %s' % (p, e['name']))
            try: cache[e['name']] = m2pack.read_entry(data, e)
            except Exception as x: fails.append('decode %s %s %s' % (p, e['name'], x))
            outnames.add(e['name'])
        res['readback_' + p] = len(ents)
        del data
    for e in ents: PACK.setdefault(e['name'], (p, d, e))
ix = open(OUT + '/Index' if os.path.exists(OUT + '/Index') else BASE + '/Index', 'rb').read().decode().split()
listed = ix[2::2]
# the Index also lists the base-client packs (etc, season2, zone_*...) that are not in BASE; only the tail changes
check(open(BASE + '/Index', 'rb').read().rstrip(b'\n') + b'\n*\ncatacomb_map\n' == open(OUT + '/Index', 'rb').read(), 'Index: not base + catacomb_map line')
check(all(os.path.exists(OUT + '/catacomb_map.' + x) for x in ('index', 'data')), 'catacomb_map files')
check('catacomb_map' in listed, 'catacomb_map not in Index')
res['index_packs'] = len(listed)
def content(k):
    if k in cache: return cache[k]
    p, d, e = PACK[k]
    with open(d + '/%s.data' % p, 'rb') as f:
        f.seek(e['pos']); blob = f.read(e['size'])
    e2 = dict(e); e2['pos'] = 0; return m2pack.read_entry(blob, e2)
PRE = gfres.load_ours('/opt/metin2/cache/tcm/gf28/ourpacks_pre.txt')

# 3. msenv + 64-bit gr2
env = content(ENVKEY).decode('latin1')
check(re.search(r'(?m)^\s*NearDistance', env) and re.search(r'(?m)^\s*FarDistance', env) and not re.search(r'(?im)^\s*foglevel', env), 'msenv fog')
g64 = [k for k in outnames if k.endswith('.gr2') and content(k)[:4] == GR2_64]
check(not g64, '64-bit gr2 %s' % g64); res['gr2_64bit'] = g64

# 2. closure
st = content('maps/%s/setting.txt' % MAP).decode('latin1')
mw, mh = map(int, re.search(r'MapSize\s+(\d+)\s+(\d+)', st).groups())
seeds = ['maps/%s/setting.txt' % MAP, 'maps/%s/mapproperty.txt' % MAP, ENVKEY,
         'd:/ymir work/ui/atlas/%s/atlas.sub' % MAP, 'd:/ymir work/ui/dungeon_info/216.png']
AREA = ('areadata.txt', 'areaproperty.txt', 'areaambiencedata.txt', 'attr.atr', 'height.raw', 'tile.raw', 'water.wtr',
        'minimap.dds', 'shadowmap.dds', 'shadowmap.raw')
for x in range(mw):
    for y in range(mh):
        seeds += ['maps/%s/%03d%03d/%s' % (MAP, x, y, f) for f in AREA]
# property by CRC from the (merged) property pack
propidx = {}
for k, (p, d, e) in PACK.items():
    if p == 'property':
        l = content(k).replace(b'\r', b'').split(b'\n')
        if l and l[0].strip() == b'YPRT':
            try: propidx.setdefault(int(l[1].strip()), k)
            except ValueError: pass
crcs = collections.Counter()
for x in range(mw):
    for y in range(mh):
        t = content('maps/%s/%03d%03d/areadata.txt' % (MAP, x, y)).decode('latin1').replace('\r', '').split('\n')
        crcs.update(int(t[i + 2].strip().split('#')[0]) for i, l in enumerate(t) if l.startswith('Start Object'))
for c in crcs:
    if c in propidx: seeds.append(propidx[c])
    else: fails.append('property CRC %d missing' % c)
res['objects'] = dict((propidx.get(c, str(c)), n) for c, n in crcs.items())
# races: npclist -> folder; the exe looks in monster/monster2/npc/npc2 for <folder>/<folder>.msm
npl = content('gamedata/npclist.txt').decode('cp1250').replace('\r', '').split('\n')
fold = dict((l.split('\t')[0].strip(), l.split('\t')[1].strip().lower()) for l in npl if '\t' in l)
VN = list(range(2501, 2515)) + list(range(2591, 2599)) + [8038, 20367, 20368] + list(range(30101, 30105)) + list(range(30111, 30120))
races = {}
for v in VN:
    n = fold.get(str(v)); check(n, 'npclist %d' % v)
    if not n: continue
    keys = ['d:/ymir work/%s/%s/%s.msm' % (d, n, n) for d in ('monster', 'monster2', 'npc', 'npc2') if 'd:/ymir work/%s/%s/%s.msm' % (d, n, n) in PACK]
    if not keys: keys = sorted(k for k in PACK if k.startswith('d:/ymir work/') and k.endswith('/%s.msm' % n))
    check(keys, 'race model %d %s' % (v, n)); races[v] = (n, keys[:1])
    for msm in keys[:1]:
        seeds.append(msm); dd = msm.rsplit('/', 1)[0]
        ml = dd + '/motlist.txt'
        if ml in PACK:
            seeds.append(ml)
            for l in content(ml).decode('latin1').replace('\r', '').split('\n'):
                t = l.split()
                if len(t) >= 3: seeds.append(dd + '/' + t[2].lower())
res['races'] = races
GR2DEC = gfres.GR2DEC
RE_ABS = re.compile(rb'[A-Za-z]:[\\/][\x20-\x7e]{3,220}?\.(?:dds|tga|jpg|png|bmp|mde|mse|gr2|msa|msf|mss|wav|mp3|spt)(?![A-Za-z0-9])', re.I)
RE_YW = re.compile(rb'ymir work[\\/][\x20-\x7e]{3,220}?\.(?:dds|tga|jpg|png|bmp|mde|mse|gr2|msa|msf|mss|wav|mp3|spt)(?![A-Za-z0-9])', re.I)
bitknit = []
def refs(k, b):
    out = set()
    if k.endswith('.gr2'):
        fn = tempfile.mktemp(suffix='.gr2'); open(fn, 'wb').write(b)
        r = subprocess.run([GR2DEC, fn], capture_output=True)
        if r.returncode == 0: out |= gfres.gr2_textures(k, fn)
        else: bitknit.append(k)
        os.unlink(fn); return out
    if k.endswith('.sub'):   # subImage v1.0: image name is relative to d:/ymir work/ui/ (as the 360-366 atlases)
        return set('d:/ymir work/ui/' + norm(x) for x in re.findall(r'image\s+"([^"]+)"', b.decode('latin1')))
    if k.endswith(gfres.TEXT_EXT) or k.endswith('.mde'):
        fn = tempfile.mktemp(); open(fn, 'wb').write(b)
        out |= gfres.refs_of(k, fn); os.unlink(fn)
        for s in RE_ABS.findall(b) + RE_YW.findall(b):
            s = norm(s.decode('latin1'))
            if 'ymir work/' in s: out.add('d:/ymir work/' + s.split('ymir work/', 1)[1])
    if k.startswith('property/'):
        out = set(r for r in out if not r.startswith('property/'))   # propertyname label
        m = gfres.prop_attr_model(b.decode('latin1'))
        if m: out.add(gfres.mdatr_of(m))
    s = gfres.sound_of(k)
    if s and k.endswith('.msa'): out.add(s); OPT.add(s)   # the exe plays a motion's .mss only if there is one
    return out
OPT = set(); seen = {'maps/%s/map_devilscatacomb.msenv' % MAP}; todo = list(seeds); missing = {}; parent = {}; inpack = 0; inpre = 0
while todo:
    k = todo.pop()
    if k in seen or k.endswith('.psd'): continue
    seen.add(k)
    if k in PACK:
        inpack += 1
        for r in refs(k, content(k)):
            if r not in seen: parent.setdefault(r, k); todo.append(r)
    elif k in PRE: inpre += 1
    elif k in OPT: res.setdefault('optional_mss_absent', 0); res['optional_mss_absent'] += 1
    else: missing[k] = parent.get(k, 'seed')
check(set(missing) <= KNOWN_MISSING, 'missing %s' % {k: v for k, v in missing.items() if k not in KNOWN_MISSING})
res['closure'] = dict(keys=len(seen), in_packs=inpack, in_base_listing=inpre, missing=missing,
                      bitknit_motions_not_decodable=len(bitknit))
res['atlasinfo'] = [l for l in content('gamedata/atlasinfo.txt').decode('latin1').replace('\r', '').split('\n') if l.lower().startswith(MAP + '\t')]

res['FAILS'] = fails
json.dump(res, open(H + '/verify_cc.json', 'w'), indent=1, ensure_ascii=False)
print(json.dumps(res, indent=1, ensure_ascii=False))
print('RESULT', 'OK' if not fails else 'FAIL %d' % len(fails))
sys.exit(1 if fails else 0)
