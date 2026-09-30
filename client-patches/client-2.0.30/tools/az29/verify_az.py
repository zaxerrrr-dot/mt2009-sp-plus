# Verify the Arezzo phase-1 client packs: BASE (current c28) overlaid by OUT. Run in docker (m2pack-lzo).
# Maps 360/362/363: every areadata object -> property (pack property) -> model/tree/effect -> textures,
# .mdatr, textureset -> textures, msenv -> skybox; races of the allocation: npclist folder -> .msm -> refs.
import sys, os, re, json, tempfile, collections
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, '/opt/metin2/cache/tcm/tz'); sys.path.insert(0, HERE)
import m2pack, gfres, patch_gamedata as pg
BASE = sys.argv[1] if len(sys.argv) > 1 else '/opt/metin2/cache/tcm/c28/pack'
OUT = sys.argv[2] if len(sys.argv) > 2 else '/opt/metin2/cache/arezzo-work/client/out/pack'
PACK = {}
for d in (OUT, BASE):      # OUT first: its copy of a pack wins
    for p in sorted(f[:-6] for f in os.listdir(d) if f.endswith('.index')):
        if any(v[0] == p and v[3] == OUT for v in PACK.values()) and d == BASE: continue
        f, v, ents = m2pack.read_index(d + '/%s.index' % p); data = open(d + '/%s.data' % p, 'rb').read()
        for e in ents: PACK.setdefault(e['name'], (p, data, e, d))
PRE = gfres.load_ours('/opt/metin2/cache/tcm/gf28/ourpacks_pre.txt')
GF = gfres.GF
AZROOT = '/opt/metin2/cache/arezzo/cpack/files'
def raw(k): p, d, e, _ = PACK[k]; return m2pack.read_entry(d, e)
TMP = tempfile.mkdtemp(); _n = [0]
def tmpfile(k):
    _n[0] += 1; fn = os.path.join(TMP, '%d_%s' % (_n[0], os.path.basename(k))); open(fn, 'wb').write(raw(k)); return fn
RE_SPT = re.compile(rb'[\x20-\x7e]{3,200}?\.dds', re.I)
def refs(k):
    if k.endswith('.spt'):
        out = set(); d = k.rsplit('/', 1)[0] + '/'
        for s in RE_SPT.findall(raw(k)):
            s = gfres.norm(s.decode('latin1'))
            out.add('d:/ymir work/' + s.split('ymir work/', 1)[1] if 'ymir work/' in s else d + s.rsplit('/', 1)[-1])
        return out
    fn = tmpfile(k); gfres._gr2cache.pop(fn, None)
    r = set(gfres.refs_of(k, fn)); s = gfres.sound_of(k)
    return r
status = collections.Counter(); missing = collections.defaultdict(set); assumed = set()
def walk(seeds, tag):
    seen = set(); todo = list(seeds)
    while todo:
        k = todo.pop()
        if k in seen or k.endswith('.psd'): continue
        seen.add(k)
        if k in PACK:
            status['in packs'] += 1
            for r in refs(k):
                if r not in seen: todo.append(r)
        elif k in PRE: status['base listing'] += 1
        elif k in GF: status['official (GF), assumed in the base client'] += 1; assumed.add(k)
        else: missing[tag].add(k)
    return seen
# 1. maps
res = {}
for mid, m in pg.ALLOC['maps'].items():
    name = m['name']; tag = '%s %s' % (mid, name)
    ad = [k for k in PACK if k.startswith('maps/%s/' % name) and k.endswith('/areadata.txt')]
    assert len(ad) == m['size'][0] * m['size'][1], (name, len(ad))
    PROP = {}
    for k in PACK:
        if k.startswith('property/'):
            l = raw(k).replace(b'\r', b'').split(b'\n')
            if l and l[0].strip() == b'YPRT' and len(l) > 1: PROP.setdefault(int(l[1].strip()), k)
    crcs = collections.Counter(); noprop = set()
    for k in ad:
        t = raw(k).decode('latin1').replace('\r', '').split('\n')
        for i, l in enumerate(t):
            if l.startswith('Start Object'): crcs[int(t[i + 2].split('#')[0])] += 1
    seeds = set(); mdatr = []
    for c, n in crcs.items():
        if c not in PROP: noprop.add(c); continue
        seeds.add(PROP[c])
        txt = raw(PROP[c]).decode('latin1'); mdl = gfres.prop_attr_model(txt)
        if mdl:
            md = gfres.mdatr_of(mdl)
            if md in PACK or md in PRE: mdatr.append((md, 'ok'))
            elif md in GF or os.path.exists(os.path.join(AZROOT, md.replace('d:/ymir work/', 'ymir work/'))): mdatr.append((md, 'MISSING (source has one)'))
    st = raw('maps/%s/setting.txt' % name).decode('latin1')
    ts = re.search(r'TextureSet\s+(\S+)', st, re.I).group(1); env = re.search(r'Environment\s+(\S+)', st, re.I).group(1)
    seeds |= {gfres.norm(ts), 'd:/ymir work/environment/' + gfres.norm(env), 'maps/%s/%s' % (name, gfres.norm(env)),
              'd:/ymir work/ui/atlas/%s/atlas.sub' % name, 'd:/ymir work/ui/%s_atlas.dds' % name}
    for k in PACK:
        if k.startswith('maps/%s/' % name): seeds.add(k)
    walk(seeds, tag)
    res[tag] = dict(objects=sum(crcs.values()), crcs=len(crcs), without_property=sorted(noprop),
                    mdatr_ok=sum(1 for x in mdatr if x[1] == 'ok'), mdatr_missing=[x for x in mdatr if x[1] != 'ok'])
# 2. races
npl = dict((l.split('\t')[0].strip(), l.split('\t')[1].strip()) for l in raw('gamedata/npclist.txt').decode('cp1250').split('\r\n') if '\t' in l)
alias = {}
for l in raw('gamedata/npclist.txt').decode('cp1250').split('\r\n'):
    t = l.split('\t')
    if len(t) >= 3 and t[0].strip() == '0': alias[t[1].strip().lower()] = t[2].strip().lower()
BASEMODELS = ('spider_', 'jinno_patrol_spear')   # base-client models (official monsters/NPCs already on our maps)
races = {}
for m in pg.ALLOC['mobs']:
    fo = npl[str(m['vnum'])].lower(); src = alias.get(fo, fo)
    hit = None
    for b in ('monster', 'monster2', 'npc', 'npc2', 'npc_pet', 'npc_mount', 'guild'):
        k = 'd:/ymir work/%s/%s/%s.msm' % (b, src, fo)
        if k in PACK or k in PRE: hit = k; break
    if hit:
        walk([hit, hit.rsplit('/', 1)[0] + '/motlist.txt'], 'race %d %s' % (m['vnum'], fo)); races[m['vnum']] = 'ok ' + hit + ' (' + PACK.get(hit, ('base',))[0] + ')'
    elif fo.startswith(BASEMODELS): races[m['vnum']] = 'base client model ' + fo + ' (not listed on the VPS; used by official mobs on our maps)'
    else: races[m['vnum']] = 'MISSING ' + fo
az_src = lambda k: os.path.exists(os.path.join(AZROOT, k.replace('d:/ymir work/', 'ymir work/')))
out = dict(maps=res, races=races, status=dict(status),
           missing=dict((t, sorted('%s%s' % (k, ' (Arezzo lacks it too)' if not az_src(k) else ' (ARREZO HAS IT)') for k in v)) for t, v in missing.items()),
           assumed_base_official=sorted(assumed))
json.dump(out, open(HERE + '/verify_az.json', 'w'), indent=1)
print(json.dumps(dict((k, v) for k, v in out.items() if k != 'assumed_base_official'), indent=1))
print('assumed in base client (official GF files, not in our listings):', len(assumed))
