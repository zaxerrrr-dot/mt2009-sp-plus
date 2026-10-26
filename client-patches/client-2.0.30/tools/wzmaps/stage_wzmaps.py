# -*- coding: utf-8 -*-
# MT2009_PLUS_MAPS_WZ_V1 (client) - Wezowe Pole (80, metin2_map_snakefield, 4x4 at 1049600 716800) and Kraina Gigantow
# (70, metin2_map_giantland, 2x2 at 819200 716800): the client files staged for build_wzmaps_packs.py.
#
#   python3 stage_wzmaps.py [<staging dir>] [<work dir>] [<npclist.txt>]       (host; no lzo needed)
#
# defaults (the 2.x line): /opt/metin2/cache/wzmaps-2x-staging, /opt/metin2/cache/yohara/cape301-work (c58.lst +
# x/property of the client we build on), the npclist of client 2.0.67. Writes <staging>/add/<pack>/<in-pack name> ("d:/" as "d_/")
# and tools/wzmaps/wzmaps_manifest.json. The maps' vnums: linux-port/docker/game/maps_wz/spawned.txt
# (tools/maps_wz/gen_maps_wz.py).
#
# The terrain is the official one of the Ameria client sources (FoxFSArchiver/source/season/season1/metin2_map_wl_01,
# metin2_map_nusluck01 - the GF 26.1.11 client no longer has these maps) under new folder names, the server's
# (maps/metin2_map_snakefield, maps/metin2_map_giantland): the exe takes a file from the pack registered first, and our
# base client (no listing on this host) may carry an older metin2_map_nusluck01 - 4 % of its cells differ from the
# official server_attr the server uses now. A name no client has is always this terrain. setting.txt is written with
# the server's BasePosition (Ameria's says 0 0) and ViewRadius 128; mapproperty.txt has no ParentMapName.
#   maps/<folder>/..., the textureset and its terrain textures, the msenv, the atlas  -> new pack wzmaps_map
#   property/...                                                                       -> pack property (added)
#   the map objects' models (zone/, tree/, effect/ ...)                                -> new pack wzmaps_obj
#   the races of the maps our packs lack (Giants, ogres, golems)                       -> new pack wzmaps_mobs
# Resources: GF first, the Ameria sources fill the gaps (zone/nusluck ...). The textureset is Ameria's metin2_wl_01.txt
# (its terrain paints 19 slots) as textureset/metin2_snakefield.txt; the msenv is the base client's milgyo.msenv (the
# Hwang Temple's). The atlas: GF's atlas_resize pictures of metin2_map_wl_01 / nusluck01 under
# d:/ymir work/ui/atlas/<our folder>/atlas.sub.
import collections
import glob
import hashlib
import json
import os
import re
import shutil
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, '..', 'az58'))
import gfres  # noqa: E402  (indexes the GF client at import)

gfres.GR2DIR = '/opt/metin2/cache/arezzo-work/client/az58/gr2'
gfres.GR2DEC = os.path.join(gfres.GR2DIR, 'gr2dec')

STAGING = sys.argv[1] if len(sys.argv) > 1 else '/opt/metin2/cache/wzmaps-2x-staging'     # the 2.x line's
WORK = sys.argv[2] if len(sys.argv) > 2 else '/opt/metin2/cache/yohara/cape301-work'
NPCLIST = sys.argv[3] if len(sys.argv) > 3 else '/opt/metin2/cache/c67/chk/gamedata/npclist.txt'   # 2.0.67
OURS_LST = os.path.join(WORK, 'c58.lst')
PRE_LST = '/opt/metin2/cache/tcm/gf28/ourpacks_pre.txt'
AMERIA = '/opt/metin2/ameria/ameria-prj-2025/tools/FoxFSArchiver/source'
SEASON1 = os.path.join(AMERIA, 'season', 'season1')
GR2_64 = b'\xe5\x9b\x49\x5e'
SPLIT = 26 * 1000 * 1000
MAP_PREFIXES = ('maps/', 'textureset/', 'd:/ymir work/terrainmaps/', 'd:/ymir work/environment/', 'd:/ymir work/ui/')
norm = gfres.norm
REPO = os.path.normpath(os.path.join(HERE, '..', '..', '..', '..'))
SPAWNED = os.path.join(REPO, 'linux-port', 'docker', 'game', 'maps_wz', 'spawned.txt')
_vn = collections.defaultdict(set)
for _l in open(SPAWNED, encoding='utf-8'):
    _t = _l.split()
    if len(_t) == 2 and _t[0].isdigit():
        _vn[int(_t[0])].add(int(_t[1]))
MAPS = [
    dict(index=80, folder='metin2_map_snakefield', src='metin2_map_wl_01', size=(4, 4), base=(1049600, 716800),
         fog=(100.0, 29000.0), fog_on=1),
    dict(index=70, folder='metin2_map_giantland', src='metin2_map_nusluck01', size=(2, 2), base=(819200, 716800),
         fog=(100.0, 29000.0), fog_on=1),
]
for _M in MAPS:
    _M['vnums'] = sorted(_vn[_M['index']])
    assert _M['vnums'], _M['index']
# the races to stage when our listing lacks them: the maps' monsters with models of their own (the cursed animals,
# the Metins, the warps and the Teleporter are the villages' / the base client's)
RACE_VNUMS = (1401, 1402, 1403, 1501, 1502, 1503, 1601, 1602, 1603)
RACE_DIRS = ('guild', 'npc', 'npc2', 'npc_pet', 'npc_mount', 'monster', 'monster2')
SETTING = ('ScriptType\tMapSetting\r\n\r\nCellScale\t200\r\nHeightScale\t0.500000\r\n\r\nViewRadius\t128\r\n\r\n'
           'MapSize\t%d\t%d\r\nBasePosition\t%d\t%d\r\nTextureSet\ttextureset\\metin2_snakefield.txt\r\n'
           'Environment\tmilgyo.msenv\r\n')

# ---------------------------------------------------------------- what our client has (incl. the earlier builders)
OURS = set(gfres.load_ours(PRE_LST))
for l in open(OURS_LST, encoding='utf-8', errors='replace'):
    t = l.rstrip('\n').split(' ', 1)
    if len(t) == 2:
        OURS.add(norm(t[1]))
EARLIER_NAMES = set()
for mp in sorted(glob.glob(os.path.join(HERE, '..', '*', '*_manifest.json'))):
    if os.path.basename(mp) == 'wzmaps_manifest.json':
        continue
    man = json.load(open(mp, encoding='utf-8'))
    packs = man.get('packs')
    if isinstance(packs, dict):
        for p in packs.values():
            if isinstance(p, list):
                EARLIER_NAMES |= set(e['name'] for e in p if isinstance(e, dict) and 'name' in e)
OURS |= EARLIER_NAMES
# MT2009_PLUS_MAPS_WZ_V1 (2.x line): the property folders the 2.x client build (/opt/metin2/cache/client237.sh and its
# successors) stages before this builder - not the Yohara line's (/opt/metin2/cache/yohara/*-staging: ymeley, ymaps ...,
# packs a 2.x client has not). EARLIER_NAMES above reads only this repo's manifests, so on the 2.x line it is the 2.x
# builders' names too.
EARLIER_STAGING = [p for p in ('/opt/metin2/cache/atlantis-staging/add/property/property',
                               '/opt/metin2/cache/zodiak-staging/add/property/property',
                               '/opt/metin2/cache/yohara/cape301-staging/add/property/property',
                               '/opt/metin2/cache/yohara/maps302-staging/add/property/property',
                               '/opt/metin2/cache/las237-staging/stage/add/property/property') if os.path.isdir(p)]


def index_ameria(root):
    """The FoxFS sources: <pack>/ymir work/... -> d:/ymir work/..., <pack>/{property,sound,textureset,icon}/... and the
    top folders property/, sound/, textureset/, icon/ themselves."""
    m = {}
    for top in sorted(os.listdir(root)):
        tp = os.path.join(root, top)
        if not os.path.isdir(tp) or top == 'season':
            continue
        roots = []
        if top.lower() in ('property', 'sound', 'textureset', 'icon'):
            roots.append((tp, top.lower() + '/'))
        for sub in os.listdir(tp):
            sp = os.path.join(tp, sub)
            if not os.path.isdir(sp):
                continue
            if sub.lower() == 'ymir work':
                roots.append((sp, 'd:/ymir work/'))
            elif sub.lower() in ('property', 'sound', 'textureset', 'icon') and top.lower() != sub.lower():
                roots.append((sp, sub.lower() + '/'))
        for base, pref in roots:
            for dp, dn, fn in os.walk(base):
                for f in fn:
                    ap = os.path.join(dp, f)
                    m.setdefault(norm(pref + os.path.relpath(ap, base)), ap)
    return m


AM = index_ameria(AMERIA)
GF = dict(gfres.GF)
RES = dict((k, p) for k, p in AM.items() if not k.startswith('property/'))
RES.update(GF)                      # GF wins; Ameria only fills gaps
gfres.GF = RES

shutil.rmtree(STAGING, ignore_errors=True)
GEN = os.path.join(STAGING, 'gen')
os.makedirs(GEN)


def gen(key, data):
    p = os.path.join(GEN, key.replace('d:/', 'd_/', 1))
    os.makedirs(os.path.dirname(p), exist_ok=True)
    open(p, 'wb').write(data)
    return p


def crlf(s):
    return s.replace('\r\n', '\n').replace('\n', '\r\n')


def prop_crc(path):
    b = open(path, 'rb').read().replace(b'\r', b'').split(b'\n')
    if b and b[0].strip() == b'YPRT' and len(b) > 1:
        try:
            return int(b[1].strip())
        except ValueError:
            return None
    return None


def model_of(text):
    for l in text.replace('\r', '').split('\n'):
        t = l.split(None, 1)
        if len(t) == 2 and t[0].lower().endswith('file'):
            return norm(t[1].strip().strip('"'))
    return None


def crc_of_body(body):
    return int(body.split('\n')[1].strip().split('#')[0])


OURPROP = {}
for root in [os.path.join(WORK, 'x', 'property')] + EARLIER_STAGING:
    for dp, dn, fn in os.walk(root):
        for f in fn:
            c = prop_crc(os.path.join(dp, f))
            if c is not None:
                OURPROP.setdefault(c, os.path.join(dp, f))
GFPROP = {}
for k, p in GF.items():
    if k.startswith('property/'):
        c = prop_crc(p)
        if c is not None:
            GFPROP.setdefault(c, (k, p))
AMPROP = {}
for k, p in AM.items():
    if k.startswith('property/'):
        c = prop_crc(p)
        if c is not None:
            AMPROP.setdefault(c, (k, p))

add = collections.defaultdict(dict)       # group -> key -> src (group: 'map', 'property', 'obj', 'mobs')
manifest = {'maps': {}, 'packs': {}, 'unresolved': {}, 'races': {}, 'replace': []}
unres_all = set()
seeds = set()
envkey = 'd:/ymir work/environment/milgyo.msenv'

for M in MAPS:
    MAP = M['folder']
    srcdir = os.path.join(SEASON1, M['src'])
    mp = 'maps/%s/' % MAP
    files = {}
    for dp, dn, fn in os.walk(srcdir):
        for f in fn:
            rel = norm(os.path.relpath(os.path.join(dp, f), srcdir))
            if rel in ('regen.txt', 'setting.txt'):
                continue          # the server's spawns (Ameria ships them in the client) / written below
            files[mp + rel] = os.path.join(dp, f)
    sectors = sorted(k for k in files if k.endswith('/areadata.txt'))
    assert len(sectors) == M['size'][0] * M['size'][1], (MAP, len(sectors))
    mpt = open(files[mp + 'mapproperty.txt'], 'rb').read().decode('latin1')
    assert 'ParentMapName' not in mpt and re.search(r'MapType\s+"Outdoor"', mpt), mpt
    st = open(os.path.join(srcdir, 'setting.txt'), 'rb').read().decode('latin1')
    assert re.search(r'MapSize\s+%d\s+%d' % M['size'], st) and re.search(r'TextureSet\s+textureset\\metin2_wl_01\.txt',
                                                                          st, re.I), (MAP, st)   # -> ours, below
    add['map'][mp + 'setting.txt'] = gen(mp + 'setting.txt', (SETTING % (M['size'] + M['base'])).encode('latin1'))
    used = collections.Counter()
    for s in sectors:
        t = open(files[s], 'rb').read().decode('latin1').replace('\r', '')
        for body in re.findall(r'Start Object\d+\n(.*?)End Object\n', t, re.S):
            used[crc_of_body(body)] += 1
    prop_src, drop = {}, {}
    for crc in sorted(used):
        if crc in OURPROP:
            continue
        kp = GFPROP.get(crc) or AMPROP.get(crc)
        if not kp:
            drop[crc] = 'no property (our property pack, GF, Ameria)'
            continue
        mdl = model_of(open(kp[1], 'rb').read().decode('latin1'))
        if mdl and mdl.endswith('.gr2') and mdl in RES and open(RES[mdl], 'rb').read(4) == GR2_64:
            drop[crc] = '64-bit GR2 %s' % mdl
            continue
        if mdl and mdl not in RES and mdl not in OURS:
            # the model is in no client we have (GF's own sits in an encrypted blob; the shye bushes' .spt): the
            # object is taken out of its sector rather than standing there as a missing model
            drop[crc] = 'model %s in no client we have' % mdl
            continue
        if kp[0] in OURS:
            drop[crc] = 'property name %s is ours with another CRC' % kp[0]
            continue
        prop_src[crc] = kp
    removed = collections.Counter()
    for s in sectors:
        t = open(files[s], 'rb').read().decode('latin1').replace('\r', '')
        head = t.split('Start Object', 1)[0]
        objs = re.findall(r'Start Object\d+\n(.*?)End Object\n', t, re.S)
        out = [b for b in objs if crc_of_body(b) not in drop]
        for b in objs:
            if crc_of_body(b) in drop:
                removed[crc_of_body(b)] += 1
        if len(out) != len(objs):
            txt = head + ''.join('Start Object%03d\n%sEnd Object\n' % (i, b) for i, b in enumerate(out))
            txt += '\nObjectCount %d\n' % len(out)
            files[s] = gen(s, crlf(txt).encode('latin1'))
    for k, p in files.items():
        add['map'][k] = p
    for crc, (k, p) in prop_src.items():
        RES[k] = p
        seeds.add(k)
        mdl = gfres.prop_attr_model(open(p, 'rb').read().decode('latin1'))
        if mdl and gfres.mdatr_of(mdl) in RES:
            seeds.add(gfres.mdatr_of(mdl))
    for crc in sorted(used):
        if crc not in OURPROP:
            continue
        p = OURPROP[crc]
        for r in gfres.refs_of('property/x.prb', p):
            seeds.add(r)
        mdl = gfres.prop_attr_model(open(p, 'rb').read().decode('latin1'))
        if mdl and gfres.mdatr_of(mdl) in RES:
            seeds.add(gfres.mdatr_of(mdl))
    # the minimap/shadow textures etc. are the folder's own files; the textureset: below
    # the atlas (GF's atlas_resize picture of the official folder, staged where exe 2.0.25 looks)
    gsub = 'd:/ymir work/ui/atlas_resize/%s/atlas.sub' % M['src']
    img = None
    if gsub in GF:
        img = norm(re.search(r'image\s+"([^"]+)"', open(GF[gsub], 'rb').read().decode('latin1')).group(1))
        if 'd:/ymir work/ui/' + img in RES:
            sub = 'd:/ymir work/ui/atlas/%s/atlas.sub' % MAP
            add['map'][sub] = GF[gsub]
            seeds.add('d:/ymir work/ui/' + img)
        else:
            img = None
    manifest['maps'][str(M['index'])] = dict(
        folder=MAP, source='ameria season1/' + M['src'], pack='wzmaps_map', textureset='textureset/metin2_snakefield.txt',
        environment='milgyo.msenv', atlas_image=('d:/ymir work/ui/' + img) if img else None,
        objects=dict(crc_used=len(used), ours=sum(1 for c in used if c in OURPROP), staged=len(prop_src),
                     dropped=len(drop)),
        removed_objects=dict((str(c), dict(objects=n, why=drop[c])) for c, n in sorted(removed.items())))
    for crc, (k, p) in prop_src.items():
        add['property'][k] = p

# the textureset: Ameria's metin2_wl_01.txt (19 textures - its terrain's tile.raw uses slots up to 19; the official
# one, GF's, has 17 and other textures) under a name of its own, so a base client's metin2_wl_01.txt is never taken
TSKEY = 'textureset/metin2_snakefield.txt'
add['map'][TSKEY] = gen(TSKEY, open(os.path.join(AMERIA, 'textureset', 'metin2_wl_01.txt'), 'rb').read())
RES[TSKEY] = add['map'][TSKEY]
seeds.add(TSKEY)
# the environment: milgyo.msenv - the Hwang Temple's (65) of the base client, read from d:/ymir work/environment/ (no
# copy in the map folders: GF's names clouds no client has)
env_ours = envkey in OURS
files, unres_map, _ = gfres.closure(sorted(seeds), OURS)
for k, src in files.items():
    if k in OURS or any(k in add[g] for g in add):
        continue
    if k.startswith('maps/'):
        continue
    grp = 'property' if k.startswith('property/') else 'map' if k.startswith(MAP_PREFIXES) else 'obj'
    add[grp][k] = src
unres_all |= set(u for u in unres_map if not u.endswith('.msenv') and not (
    u.startswith('property/') and not u.endswith(('.prb', '.prd', '.pre', '.prt', '.pra'))))

# ---------------------------------------------------------------- the races
npc = {}
alias = {}
for l in open(NPCLIST, encoding='latin1'):
    t = l.split()
    if len(t) >= 3 and t[0] == '0':
        alias[t[1].lower()] = t[2].lower()
    elif len(t) >= 2 and t[0].isdigit():
        npc[int(t[0])] = t[1].lower()
races = {}
unres_races = {}
for v in RACE_VNUMS:
    assert any(v in M['vnums'] for M in MAPS), v
    name = npc.get(v)
    if not name:
        races[v] = dict(status='no npclist row')
        continue
    folder = alias.get(name, name)
    cands = ['d:/ymir work/%s/%s/%s.msm' % (d, folder, name) for d in RACE_DIRS]
    have = next((c for c in cands if c in OURS), None)
    if have:
        races[v] = dict(race=name, msm=have, status='ours')
        continue
    src = next((c for c in cands if c in RES), None)
    if not src:
        races[v] = dict(race=name, status='MISSING (not in our listing, GF or Ameria) - base client must have it')
        continue
    races[v] = dict(race=name, msm=src, status='staged')
    f, u, o = gfres.closure([src.rsplit('/', 1)[0] + '/'], OURS)
    for k, s in f.items():
        if k in OURS or any(k in add[p] for p in add):
            continue
        add['mobs'][k] = s
    if u:
        unres_races[name] = sorted(u)

extra_missing = set()
for _ in range(2):
    for p in list(add):
        for k, src in list(add[p].items()):
            if not k.endswith(('.mde', '.mse')):
                continue
            for m in re.findall(rb'[A-Za-z]:[\\/][^\x00"\r\n]+?\.(?:dds|tga|png|jpg|mde)', open(src, 'rb').read(), re.I):
                t = 'd:' + m.decode('latin1').replace('\\', '/').lower()[2:]
                if t in OURS or any(t in add[q] for q in add):
                    continue
                if t in RES:
                    add[p][t] = RES[t]
                else:
                    extra_missing.add(t)

# ---------------------------------------------------------------- packs (split under the 29 MB limit)
bad64 = sorted(k for p in add for k, s in add[p].items() if k.endswith('.gr2') and open(s, 'rb').read(4) == GR2_64)
if bad64:
    raise SystemExit('64-bit GR2 staged: %s' % bad64)
PACK_OF_GROUP = {'map': 'wzmaps_map', 'obj': 'wzmaps_obj', 'mobs': 'wzmaps_mobs', 'property': 'property'}
packs = collections.OrderedDict()
for grp in ('map', 'obj', 'mobs', 'property'):
    base = PACK_OF_GROUP[grp]
    if grp == 'property':
        packs['property'] = dict(add[grp])
        continue
    n, cur, size = 1, {}, 0
    for k in sorted(add[grp]):
        s = os.path.getsize(add[grp][k])
        if cur and size + s > SPLIT:
            packs[base if n == 1 else '%s%d' % (base, n)] = cur
            n, cur, size = n + 1, {}, 0
        cur[k] = add[grp][k]
        size += s
    if cur:
        packs[base if n == 1 else '%s%d' % (base, n)] = cur
seen = set()
for p in packs:
    for k in packs[p]:
        assert k == k.lower() and '\\' not in k, k
        assert k not in OURS, k
        assert len(k.encode('cp1252')) < 161, k
        assert k not in seen, k
        seen.add(k)
manifest['races'] = dict((str(v), r) for v, r in races.items())
manifest['new_packs'] = [p for p in packs if p != 'property' and packs[p]]
for p in packs:
    ents = []
    for k in sorted(packs[p]):
        src = packs[p][k]
        dst = os.path.join(STAGING, 'add', p, k.replace('d:/', 'd_/', 1))
        os.makedirs(os.path.dirname(dst), exist_ok=True)
        shutil.copyfile(src, dst)
        b = open(src, 'rb').read()
        where = 'gen' if src.startswith(GEN) else 'gf' if src.startswith(gfres.G) else 'ameria' if src.startswith(AMERIA) else src
        ents.append(dict(name=k, source=where, size=len(b), sha1=hashlib.sha1(b).hexdigest()))
    manifest['packs'][p] = ents
manifest['environment'] = dict(key=envkey, ours=env_ours)
manifest['unresolved']['map'] = sorted(unres_all)
manifest['unresolved']['races'] = unres_races
manifest['unresolved']['effects'] = sorted(extra_missing)
json.dump(manifest, open(os.path.join(HERE, 'wzmaps_manifest.json'), 'w', encoding='utf-8'), indent=1, sort_keys=True,
          ensure_ascii=False)
for p in packs:
    print('%-13s %4d files %6.2f MB' % (p, len(packs[p]), sum(os.path.getsize(v) for v in packs[p].values()) / 1e6))
for i, m in manifest['maps'].items():
    print(i, m['folder'], 'objects:', m['objects'], 'removed:', m['removed_objects'], 'atlas:', m['atlas_image'])
print('environment %s: %s' % (envkey, 'in our listing' if env_ours else 'the base client\'s (Hwang)'))
print('races:', dict((v, r['status']) for v, r in races.items()))
print('unresolved map:', manifest['unresolved']['map'])
print('unresolved races:', unres_races)
print('unresolved effects:', manifest['unresolved']['effects'])
