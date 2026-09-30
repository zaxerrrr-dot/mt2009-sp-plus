# plan58.json: which files go into which pack (MT2009 client 2.0.30, Arezzo phases 5-8).
#   maps/<map>/...  -> pack maps        property/... -> pack property (exe: objects only from pack/property)
#   other map assets -> NEW packs az_maps2 (361) / az_maps3 (364-366)
#   Plechito races -> NEW packs az_mobs2 (Wukong) / az_mobs3 (pyramid) / az_mobs4 (scorpion + jungle)
# A key that also exists in GF 26.1.11 is taken from GF (except maps/ and property/). Keys our packs already have
# (current c30 listing + the pre-import base listing) are skipped.
import os, re, json, collections
import common58 as c, gfres
RES = dict(c.AZ)
for k, p in c.GF.items():
    if not k.startswith(('maps/', 'property/')): RES[k] = p
gfres.GF = RES
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
    return sorted(l.strip() for l in c.prop_body(b) if l.strip() and not l.lower().startswith(b'propertyname'))
GR2_64 = b'\xe5\x9b\x49\x5e'
plan = collections.defaultdict(dict); report = {}; where = {}; bad64 = set()
def put(pack, k, src):
    if k in c.OURS or k in where or k.endswith('/server_attr'): return
    if k.endswith('.gr2') and open(src, 'rb').read(4) == GR2_64: bad64.add(k)
    where[k] = pack; plan[pack][k] = src
offmodel = {}
# pack sizes: each new pack's zip stays well under GitHub's per-file limit
MAPPACK = {'metin2_map_pustynia': 'az_maps2', 'plechito_wukong_dungeon': 'az_maps3', 'plechito_scorpion_dungeon': 'az_maps3',
           'plechito_easter2023_dungeon': 'az_maps3'}
for m in c.MAPS:
    seeds = {'maps/%s/' % m}
    st = open(os.path.join(c.A, m, 'setting.txt'), 'rb').read().decode('latin1')
    ts = re.search(r'TextureSet\s+(\S+)', st, re.I).group(1); env = re.search(r'Environment\s+(\S+)', st, re.I).group(1)
    seeds.add(c.norm(ts)); seeds.add('d:/ymir work/environment/' + c.norm(env))
    crcs = collections.Counter()
    for f in c.map_areadata(m): crcs.update(c.map_crcs_file(f))
    stat = collections.Counter(); newprops = {}
    for crc in sorted(crcs):
        k, p = c.AZPROP[crc]; b = open(p, 'rb').read()
        if crc in c.OURPROP:
            ok, op = c.OURPROP[crc]
            if functional(open(op, 'rb').read()) != functional(b):
                raise SystemExit('property CRC clash %d %s <-> %s: renumber needed' % (crc, k, ok))
            stat['ours (same object)'] += 1
            for l in b.decode('latin1').replace('\r', '').split('\n'):
                t = l.split(None, 1)
                if len(t) == 2 and t[0].lower().endswith('file') and t[1].strip().strip('"'):
                    v = c.norm(t[1].strip().strip('"'))
                    if v not in c.GF: seeds.add(v)
                    elif v.endswith('.gr2'): offmodel.setdefault(m, set()).add(v)
            model = gfres.prop_attr_model(b.decode('latin1'))
            if model and model in c.GF and gfres.mdatr_of(model) in c.GF: offmodel.setdefault(m, set()).add(gfres.mdatr_of(model))
            elif model and gfres.mdatr_of(model) in c.AZ: seeds.add(gfres.mdatr_of(model))
            continue
        assert k not in c.OURS, k
        newprops[k] = p; seeds.add(k); stat['new'] += 1
        model = gfres.prop_attr_model(b.decode('latin1'))
        if model and gfres.mdatr_of(model) in RES: seeds.add(gfres.mdatr_of(model))
    files, unres, oh = gfres.closure(sorted(seeds), c.OURS)
    for k, src in sorted(files.items()):
        if k.startswith('property/') and k not in newprops: continue
        pack = 'maps' if k.startswith('maps/') else 'property' if k.startswith('property/') else MAPPACK[m]
        put(pack, k, src)
    tex = set()
    for k in offmodel.get(m, ()):
        if k.endswith('.gr2'): tex |= gfres.refs_of(k, c.GF[k])
        else: tex.add(k)
    gfres.GF = dict(c.GF)
    f2, u2, o2 = gfres.closure(sorted(tex), c.OURS)
    gfres.GF = RES
    for k, src in sorted(f2.items()): put(MAPPACK[m], k, src)
    unres |= set(u2)
    report[m] = dict(crcs=len(crcs), objects=sum(crcs.values()), props=dict(stat), files=len(files), already=len(oh),
                     official_objects=len([k for k in offmodel.get(m, ()) if k.endswith('.gr2')]),
                     unresolved=sorted(u for u in unres if not u.endswith('.msenv')))
# races: the Arezzo npclist alias -> the race folder; monster2 copy when there is one (the .msm paths point there)
AL = {}
for l in open(c.A + '/npclist.txt', 'rb').read().decode('latin1').replace('\r', '').split('\n'):
    t = l.split()
    if len(t) >= 3 and t[0] == '0': AL[t[1].lower()] = t[2].lower().replace('\\', '/')
RACEPACK = {5: 'az_mobs2', 8: 'az_mobs3', 6: 'az_mobs4', 7: 'az_mobs4'}
races = {}; aliases = {}
for m in c.ALLOC['mobs']:
    if m.get('phase') not in c.PHASES: continue
    fo = m['client_folder'].lower(); src = AL.get(fo, fo)
    if fo != src: aliases[fo] = src
    base = None
    for b in ('monster2', 'monster', 'npc2', 'npc'):
        if 'd:/ymir work/%s/%s/%s.msm' % (b, src, fo) in c.AZ: base = b; break
    if not base: raise SystemExit('race %s: no msm' % fo)
    msm = 'd:/ymir work/%s/%s/%s.msm' % (base, src, fo)
    if msm in c.OURS:
        races[m['vnum']] = 'ours ' + msm; continue
    if fo == 'jinno_patrol_spear':
        races[m['vnum']] = 'base client'; continue
    if src == 'metinstone':   # a stone in the official metinstone folder: only its own msm and what it names
        seeds = [msm]
    else:
        seeds = ['d:/ymir work/%s/%s/' % (base, src), 'sound/%s/%s/' % (base, src)]
    files, unres, oh = gfres.closure(seeds, c.OURS)
    for k, s in sorted(files.items()): put(RACEPACK[m['phase']], k, s)
    races[m['vnum']] = dict(msm=msm, files=len(files), unresolved=sorted(unres))
json.dump(dict(plan=plan, report=report, races=races, aliases=aliases, bad64=sorted(bad64), gr2_fail=gfres.GR2_FAIL),
          open(c.HERE + '/plan58.json', 'w'), indent=1, sort_keys=True)
for p, f in sorted(plan.items()):
    print('%-10s %5d files %6.1f MB' % (p, len(f), sum(os.path.getsize(v) for v in f.values()) / 1e6))
for k, r in report.items(): print(k, {x: r[x] for x in r if x != 'unresolved'}, '\n   UNRES', r['unresolved'][:30])
print('64-bit gr2:', sorted(bad64))
print('aliases:', aliases)
for v, r in races.items():
    if isinstance(r, dict) and r['unresolved']: print('race', v, r['msm'], 'UNRES', r['unresolved'][:10])
