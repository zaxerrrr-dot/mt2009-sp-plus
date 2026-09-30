# plan.json: which files of the Arezzo/GF trees go into which pack (MT2009 client 2.0.30, Arezzo phase 1).
# Maps 360 metin2_map_exp, 362 natural_map, 363 plechito_chamber_of_wisdom + the models our client lacks.
#   maps/<map>/...  -> pack maps       property/...      -> pack property (exe: objects only from pack/property)
#   other map assets -> NEW pack az_maps   mob models     -> NEW pack az_mobs
# A key that also exists in GF 26.1.11 is taken from GF (except maps/ and property/). Keys our packs already
# have (c28 listings + pre-import base listing) are skipped.
import os, re, json, collections
import common as c, gfres
RES = dict(c.AZ)
for k, p in c.GF.items():
    if not k.startswith(('maps/', 'property/')): RES[k] = p
gfres.GF = RES

# SpeedTree .spt: bark (full path) and composite leaf map (bare name, next to the .spt) are in the binary
RE_SPT = re.compile(rb'[\x20-\x7e]{3,200}?\.dds', re.I)
_refs = gfres.refs_of
def refs_of(key, path):
    if key.endswith('.spt'):
        out = set(); d = key.rsplit('/', 1)[0] + '/'
        for s in RE_SPT.findall(open(path, 'rb').read()):
            s = c.norm(s.decode('latin1'))
            if 'ymir work/' in s: out.add('d:/ymir work/' + s.split('ymir work/', 1)[1])
            else: out.add(d + s.rsplit('/', 1)[-1])
        return out
    return _refs(key, path)
gfres.refs_of = refs_of

def functional(b):
    """property text without the name and blank lines: equal -> the same object"""
    return sorted(l.strip() for l in c.prop_body(b) if l.strip() and not l.lower().startswith(b'propertyname'))

# natural_map: 3 plechi_env forest trunks are 64-bit Granny files (e59b495e) the 2.0.25 exe cannot read.
# Their two "Building" properties become SpeedTree "Tree" properties of the same Plechito forest set
# (ptf_tree00b / ptf_tree00a .spt, 32-bit, already used on the map), and the leaf-crown "Effect" objects
# standing on them (.mse/.mde meshes placed at the same spots) are taken out of the map's areadata.
TREE_SWAP = {2593667659: ('ptf_tree00b', 'd:/ymir work/tree/plechito_trees/ptf_tree00b.spt'),
             1519687220: ('ptf_tree00a', 'd:/ymir work/tree/plechito_trees/ptf_tree00a.spt')}
TREE_DROP = {2269369239, 3974574155}

plan = collections.defaultdict(dict); gens = collections.defaultdict(dict); report = {}
where = {}
def put(pack, k, src):
    if k in c.OURS or k in where or k.endswith('/server_attr'): return
    where[k] = pack; plan[pack][k] = src

propnote = {}
offmodel = {}
for m in c.MAPS:
    seeds = {'maps/%s/' % m}
    st = open(os.path.join(c.A, m, 'setting.txt'), 'rb').read().decode('latin1')
    ts = re.search(r'TextureSet\s+(\S+)', st, re.I).group(1); env = re.search(r'Environment\s+(\S+)', st, re.I).group(1)
    seeds.add(c.norm(ts)); seeds.add('d:/ymir work/environment/' + c.norm(env))
    crcs = collections.Counter()
    for f in c.map_areadata(m): crcs.update(c.map_crcs_file(f))
    stat = collections.Counter(); newprops = {}
    for crc in sorted(crcs):
        if crc in TREE_DROP: stat['dropped (leaf effect on a 64-bit trunk)'] += 1; continue
        k, p = c.AZPROP[crc]; b = open(p, 'rb').read()
        if crc in TREE_SWAP:
            name, spt = TREE_SWAP[crc]
            txt = 'YPRT\n%d\npropertyname\t\t"%s"\npropertytype\t\t"Tree"\ntreefile\t\t"%s"\ntreesize\t\t"1000.000000"\ntreevariance\t\t"0.000000"\n' % (crc, name, spt)
            nk = 'property/prt/%d.prt' % crc
            gens['property'][nk] = c.gen(nk, c.crlf(txt).encode('latin1')); where[nk] = 'property'
            seeds.add(spt); stat['64-bit trunk -> SpeedTree'] += 1; continue
        if crc in c.OURPROP:
            ok, op = c.OURPROP[crc]
            if functional(open(op, 'rb').read()) == functional(b):
                stat['ours (same object)'] += 1
                propnote.setdefault(m, []).append((crc, k, ok, 'same' if c.prop_body(open(op, 'rb').read()) == c.prop_body(b) else 'same object, name/blank lines differ'))
                # the model stays the base client's; only an Arezzo-only file it names is added
                for l in b.decode('latin1').replace('\r', '').split('\n'):
                    t = l.split(None, 1)
                    if len(t) == 2 and t[0].lower().endswith('file') and t[1].strip().strip('"'):
                        v = c.norm(t[1].strip().strip('"'))
                        if v not in c.GF: seeds.add(v)
                        elif v.endswith('.gr2'):
                            # official model, assumed in the base client (as 2.0.28 did for the entrance maps
                            # 61/62): its textures and its .mdatr (collision / walkable height) come from GF
                            offmodel.setdefault(m, set()).add(v)
                model = gfres.prop_attr_model(b.decode('latin1'))
                if model and model in c.GF and gfres.mdatr_of(model) in c.GF: offmodel.setdefault(m, set()).add(gfres.mdatr_of(model))
                elif model and gfres.mdatr_of(model) in c.AZ: seeds.add(gfres.mdatr_of(model))   # GF has no collision for it, Arezzo made one
                continue
            raise SystemExit('property CRC clash %d %s <-> %s: renumber needed' % (crc, k, ok))
        assert k not in c.OURS, k
        newprops[k] = p; seeds.add(k); stat['new'] += 1
        model = gfres.prop_attr_model(b.decode('latin1'))
        if model and gfres.mdatr_of(model) in RES: seeds.add(gfres.mdatr_of(model))
    files, unres, oh = gfres.closure(sorted(seeds), c.OURS)
    for k, src in sorted(files.items()):
        if k.startswith('property/') and k not in newprops: continue   # only the map's own objects
        pack = 'maps' if k.startswith('maps/') else 'property' if k.startswith('property/') else 'az_maps'
        put(pack, k, src)
    tex = set()
    for k in offmodel.get(m, ()):
        if k.endswith('.gr2'): tex |= gfres.refs_of(k, c.GF[k])
        else: tex.add(k)
    gfres.GF = dict(c.GF)
    f2, u2, o2 = gfres.closure(sorted(tex), c.OURS)
    gfres.GF = RES
    for k, src in sorted(f2.items()): put('az_maps', k, src)
    unres |= set(u2)
    report[m + '@official_objects'] = dict(models=len([k for k in offmodel.get(m, ()) if k.endswith('.gr2')]), files=len(f2), already=len(o2))
    report[m] = dict(crcs=len(crcs), objects=sum(crcs.values()), props=dict(stat), files=len(files), already=len(oh),
                     unresolved=sorted(u for u in unres if not u.endswith('.msenv')), gf=sum(1 for k in files if files[k] in c.GF.values()))

# models the client lacks: Arges / Polifem (9606/9607 -> cyclops_boss / cyclops_boss2), official GF folders
MOBS = ['cyclops_boss', 'cyclops_boss2']
seeds = []
for n in MOBS: seeds += ['d:/ymir work/monster2/%s/' % n, 'sound/monster2/%s/' % n]
gfres.GF = dict(c.GF)
files, unres, oh = gfres.closure(seeds, c.OURS)
for k, src in sorted(files.items()): put('az_mobs', k, src)
report['az_mobs'] = dict(files=len(files), already=len(oh), unresolved=sorted(unres))
json.dump(dict(plan=plan, gens=gens, report=report, propnote=propnote, gr2_fail=gfres.GR2_FAIL), open(c.HERE + '/plan.json', 'w'), indent=1, sort_keys=True)
for p, f in sorted(plan.items()):
    print('%-10s %5d files %6.1f MB' % (p, len(f), sum(os.path.getsize(v) for v in f.values()) / 1e6))
for k, r in report.items(): print(k, {x: r[x] for x in r if x != 'unresolved'}, '\n   UNRES', r.get('unresolved'))
