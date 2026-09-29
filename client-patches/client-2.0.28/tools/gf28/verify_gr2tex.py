# MT2009 client 2.0.28: every texture a map object's / race's .gr2 names must be in the packs.
# Run in docker (m2pack-lzo) after build: reads the current c28 packs (+ the pre-import listing of the
# base packs we know), decodes each .gr2 (gr2/gr2dec, Oodle1) and lists missing textures.
# Maps: 351/352/Ochao/Treasure Island (our maps pack) + entrances 61/62 (GF areadata; base maps are
# not in our packs). Races: the Treasure Island waves (MOB_POOL) + goblin/chest.
import sys, os, re, tempfile, collections
sys.path.insert(0, '/opt/metin2/cache/tcm/tz'); sys.path.insert(0, '/opt/metin2/cache/tcm/gf28')
import m2pack, gfres
C = sys.argv[1] if len(sys.argv) > 1 else '/opt/metin2/cache/tcm/c28/pack'
PACK = {}   # name -> (pack, data, entry)
for p in sorted(f[:-6] for f in os.listdir(C) if f.endswith('.index')):
    if p == 'root': continue
    f, v, ents = m2pack.read_index(C + '/%s.index' % p); d = open(C + '/%s.data' % p, 'rb').read()
    for e in ents: PACK.setdefault(e['name'], (p, d, e))
BASE = gfres.load_ours('/opt/metin2/cache/tcm/gf28/ourpacks_pre.txt')
def raw(k): p, d, e = PACK[k]; return m2pack.read_entry(d, e)
def has(k): return k in PACK or k in BASE
TMP = tempfile.mkdtemp()
def gr2tex(k):
    if k in PACK:
        fn = os.path.join(TMP, 'x.gr2'); open(fn, 'wb').write(raw(k)); gfres._gr2cache.pop(fn, None)
        return gfres.gr2_textures(k, fn), PACK[k][0]
    if k in gfres.GF: return gfres.gr2_textures(k, gfres.GF[k]), 'base?(GF copy decoded)'
    return None, 'no model'
def txt(k):
    if k in PACK: return raw(k).decode('latin1')
    return open(gfres.GF[k], 'rb').read().decode('latin1') if k in gfres.GF else ''
PROP = {}
for k in PACK:
    if k.startswith('property/'):
        l = raw(k).replace(b'\r', b'').split(b'\n')
        if l and l[0].strip() == b'YPRT' and len(l) > 1: PROP.setdefault(int(l[1].strip()), k)
def crcs_ours(m):
    s = set()
    for k in PACK:
        if k.startswith('maps/%s/' % m) and k.endswith('/areadata.txt'):
            t = txt(k).replace('\r', '').split('\n')
            s |= {int(t[i + 2].split('#')[0]) for i, l in enumerate(t) if l.startswith('Start Object')}
    return s
def crcs_gf(m):
    s = set()
    for dp, dn, fn in os.walk(os.path.join(gfres.G, m)):
        for f in fn:
            if f.lower() == 'areadata.txt':
                t = open(os.path.join(dp, f), 'rb').read().decode('latin1').replace('\r', '').split('\n')
                s |= {int(t[i + 2].split('#')[0]) for i, l in enumerate(t) if l.startswith('Start Object')}
    return s
bad = 0
MAPS = [('351 metin2_map_n_flame_dungeon_01', crcs_ours('metin2_map_n_flame_dungeon_01')),
        ('352 metin2_map_n_snow_dungeon_01', crcs_ours('metin2_map_n_snow_dungeon_01')),
        ('Ochao metin2_map_mt_th_dungeon_01', crcs_ours('metin2_map_mt_th_dungeon_01')),
        ('419 metin2_map_treasure_hunt', crcs_ours('metin2_map_treasure_hunt')),
        ('62 metin2_map_n_flame_01 (GF areadata)', crcs_gf('metin2_map_n_flame_01')),
        ('61 map_n_snowm_01 (GF areadata)', crcs_gf('map_n_snowm_01'))]
for name, crcs in MAPS:
    models = set(); noprop = []
    for c in crcs:
        if c not in PROP: noprop.append(c); continue
        for l in txt(PROP[c]).replace('\r', '').split('\n'):
            t = l.split(None, 1)
            if len(t) == 2 and t[0].lower().endswith('file'):
                v = gfres.norm(t[1].strip().strip('"'))
                if v.endswith('.gr2'): models.add(v)
    miss = collections.defaultdict(set); nomodel = []; ntex = 0
    for g in sorted(models):
        tex, where = gr2tex(g)
        if tex is None: nomodel.append(g); continue
        for t in tex:
            ntex += 1
            if not has(t): miss[t].add(g)
    real = {t: g for t, g in miss.items() if t in gfres.GF}
    print('== %s: %d objects, %d without our property, %d gr2 models (%d not in our packs), %d texture refs, missing: %d (%d in GF)' % (
        name, len(crcs), len(noprop), len(models), len(nomodel), ntex, len(miss), len(real)))
    for t in sorted(miss): print('   missing %s %s <- %s' % (t, 'GF' if t in gfres.GF else '(not in GF either)', sorted(miss[t])[0]))
    bad += len(real)
# every .gr2 of the GF-import packs
miss = collections.defaultdict(set); n = 0
for k, (p, d, e) in PACK.items():
    if k.endswith('.gr2') and (p.startswith('gf_') or p in ('goblin', 'ochao')):
        tex, where = gr2tex(k); n += 1
        for t in tex or ():
            if not has(t): miss[t].add(k)
real = [t for t in miss if t in gfres.GF]
print('== all .gr2 in gf_*/goblin/ochao: %d models, missing textures: %d (%d in GF)' % (n, len(miss), len(real)))
for t in sorted(miss): print('   missing %s %s <- %s' % (t, 'GF' if t in gfres.GF else '(not in GF either)', sorted(miss[t])[0]))
bad += len(real)
# Treasure Island wave races
GOBLIN_VNUMS = [b + i for b in (3001, 3101, 3201, 3301, 3401, 3501, 3551, 3601, 3701, 3801) for i in range(5)] + [20856, 20857]   # playerbot_goblin.h MOB_POOL
npl = raw('gamedata/npclist.txt').decode('latin1').replace('\r', '').split('\n')
races = {}; alias = {}
for l in npl:
    t = l.split('\t')
    if len(t) >= 2 and t[0].strip().isdigit():
        v = int(t[0])
        if v == 0 and len(t) >= 3: alias[t[1].strip().lower()] = t[2].strip().lower()
        elif v: races.setdefault(v, t[1].strip())
rbad = 0
for v in GOBLIN_VNUMS:
    if v not in races: print('   race %d: NOT IN npclist' % v); rbad += 1; continue
    n = races[v].lower(); src = alias.get(n, n); msm = None
    for P in ('guild', 'npc', 'npc2', 'npc_pet', 'npc_mount', 'monster', 'monster2'):
        k = 'd:/ymir work/%s/%s/%s.msm' % (P, src, n)
        if has(k): msm = k; break
    if not msm: print('   race %d %s: no msm' % (v, n)); rbad += 1; continue
    d = msm.rsplit('/', 1)[0] + '/'; probs = []
    refs = gfres.RE_Q.findall(txt(msm)) if msm in PACK else []
    for r in refs:
        r = gfres.norm(r); r = r if r.startswith('d:/') else d + r
        if r.endswith('.gr2'):
            if not has(r): probs.append(r); continue
            tex, w = gr2tex(r)
            probs += [t for t in tex or () if not has(t) and t in gfres.GF]
    if not has(d + 'motlist.txt'): probs.append('motlist')
    else:
        for l in txt(d + 'motlist.txt').replace('\r', '').split('\n'):
            m = re.search(r'([\w\-\.]+\.msa)', l, re.I)
            if m and not has(d + m.group(1).lower()): probs.append(d + m.group(1).lower())
    rbad += bool(probs)
    print('   race %d %-20s %-60s %s %s' % (v, n, msm, PACK[msm][0] if msm in PACK else 'base', 'MISSING ' + ', '.join(probs) if probs else 'ok'))
print('RESULT: %d missing textures available in GF, %d races with problems; gr2 not decodable: %d (BitKnit motions)' % (bad, rbad, len(gfres.GR2_FAIL)))
