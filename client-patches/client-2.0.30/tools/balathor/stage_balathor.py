# -*- coding: utf-8 -*-
# MT2009_PLUS_BALATHOR_V1 (client; Autor: dracaryS) - Krypta Balathora (420, the guild lair, 2x2 at 1152000 921600):
# the client files staged for build_balathor_packs.py, from the author's package (balathor-dracaryS part1/part2, unpacked
# under /opt/metin2/cache/balathor/p1 and p2 - only read, nothing of it is run) and, for what it lacks, the GF 26.1.11
# client (the package's files are the same models and effects). The method of ../ymeley/stage_ymeley.py.
#
#   docker run --rm -v /opt/metin2:/opt/metin2 m2pack-lzo python3 \
#     <repo>/client-patches/client-2.0.30/tools/balathor/stage_balathor.py [<staging dir>] [<work dir>] [<npclist.txt>]
#
# (in the m2pack-lzo image). The exe smoke client's pack "etc" is NOT the players' etc (3.0.4 counted its names as ours
# and shipped no boss window pictures: exception.Abort at the cinema) - its names are only counted in the manifest
# (etc_pack_names_staged), never taken as ours. Defaults:
# /opt/metin2/cache/yohara/balathor-staging, /opt/metin2/cache/yohara/cape301-work (c58.lst + x/property of the client
# we build on), the npclist of the chain's OUT (/opt/metin2/cache/cY/npc/npclist.txt, else c61's). Writes
# <staging>/add/<pack>/<in-pack name> ("d:/" as "d_/") and tools/balathor/balathor_manifest.json.
#
#   maps/metin2_map_balathor/..., its textureset, terrain textures, msenv          -> new pack balathor_map
#   property/guild_whitedragon/... the map objects' properties our pack lacks         -> pack property (added)
#   the map objects' models (zone/guild_whitedragon ...)                             -> new pack(s) balathor_obj
#   the lair's races our packs lack (npclist rows of the 20 vnums) and the effects
#   the exe / python name (the boss window, the egg and ice effects)                  -> new pack(s) balathor_mobs
#
# The map folder gets a name no client has, metin2_map_balathor (the package's metin2_map_guild_whitedragon_boss is
# GF's - a partial folder of that name in a base pack we have no listing of cannot be ruled out; the exe takes a file
# from the pack registered first), and the atlasinfo row names it (patch_balathor_client.py). setting.txt: ViewRadius
# 128 (our maps'), the msenv's GF "foglevel" as exe 2.0.25's Enable/NearDistance/FarDistance. GF has no atlas picture
# of the lair (a dungeon): none is staged. The whitedragon_cave_* / whitedragonvalley_* folders of the package belong to
# another dungeon and are not staged (only what the 20 races, the map and the named effects reach).
import collections
import hashlib
import io
import json
import os
import re
import shutil
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, '/opt/metin2/cache/arezzo-work/client/az58')
sys.path.insert(0, '/opt/metin2/cache/tcm/tz')
import gfres  # noqa: E402  (indexes the GF client at import)

gfres.GR2DIR = '/opt/metin2/cache/arezzo-work/client/az58/gr2'
gfres.GR2DEC = os.path.join(gfres.GR2DIR, 'gr2dec')

STAGING = sys.argv[1] if len(sys.argv) > 1 else '/opt/metin2/cache/yohara/balathor-staging'
WORK = sys.argv[2] if len(sys.argv) > 2 else '/opt/metin2/cache/yohara/cape301-work'
NPCLIST = sys.argv[3] if len(sys.argv) > 3 else next(
    (p for p in ('/opt/metin2/cache/cY/npc/npclist.txt', '/opt/metin2/cache/c61/chk/gamedata/npclist.txt')
     if os.path.exists(p)), None)
OURS_LST = os.path.join(WORK, 'c58.lst')
PRE_LST = '/opt/metin2/cache/tcm/gf28/ourpacks_pre.txt'
ETC_INDEX = '/opt/metin2/cache/exebuild/smoke/client/pack/etc.index'     # the full install's base pack "etc"
PKG = ['/opt/metin2/cache/balathor/p1/balathor-dracaryS/Binary', '/opt/metin2/cache/balathor/p2/balathor-dracaryS/Binary']
GR2_64 = b'\xe5\x9b\x49\x5e'
SPLIT = 26 * 1000 * 1000
MAP_PREFIXES = ('maps/', 'textureset/', 'd:/ymir work/terrainmaps/', 'd:/ymir work/environment/')
RACE_DIRS = ('guild', 'npc', 'npc2', 'npc_pet', 'npc_mount', 'monster', 'monster2')
norm = gfres.norm

with io.open(os.path.join(HERE, 'balathor_client.json'), encoding='utf-8') as _f:
    DATA = json.load(_f)
M = DATA['map']
SRC, FOLDER = M['source_folder'], M['folder']
SIZE, BASE = tuple(M['size']), tuple(M['base'])


# ---------------------------------------------------------------- the package, as in-pack names
def index_package(roots):
    m = {}
    for root in roots:
        for top in sorted(os.listdir(root)):
            tp = os.path.join(root, top)
            if not os.path.isdir(tp):
                continue
            for dp, dn, fn in os.walk(tp):
                for f in fn:
                    ap = os.path.join(dp, f)
                    rel = norm(os.path.relpath(ap, tp))
                    if top in ('effect', 'npc2', 'zone', 'terrainmaps', 'etc'):
                        assert rel.startswith('ymir work/'), ap
                        key = 'd:/' + rel
                    elif top == 'monster2':
                        assert rel.startswith('ymir work/'), ap
                        key = 'd:/ymir work/monster2/' + rel[len('ymir work/'):]
                    elif top in ('property', 'textureset'):
                        key = top + '/' + rel
                    elif top == 'map_patch':
                        key = 'maps/' + rel
                    else:
                        continue            # root, uiscript, locale, icon: the repo's copies (client-2.0.30/root)
                    assert key not in m, key
                    m[key] = ap
    return m


PK = index_package(PKG)
assert any(k.startswith('maps/%s/' % SRC) for k in PK), 'package not unpacked under ' + str(PKG)

# ---------------------------------------------------------------- what our client has (incl. the earlier builders)
OURS = set(gfres.load_ours(PRE_LST))
for l in open(OURS_LST, encoding='utf-8', errors='replace'):
    t = l.rstrip('\n').split(' ', 1)
    if len(t) == 2:
        OURS.add(norm(t[1]))
ETC_NAMES = set()
if os.path.exists(ETC_INDEX):
    import m2pack
    ETC_NAMES = set(e['name'] for e in m2pack.read_index(ETC_INDEX)[2])
# MT2009_PLUS_BALATHOR_UI_V2: ETC_NAMES are NOT ours (see the top) - only reported
EARLIER = set()
EARLIER_REPLACED = set()
for mp in sorted(__import__('glob').glob(os.path.join(HERE, '..', '*', '*_manifest.json'))):
    if os.path.basename(mp) == 'balathor_manifest.json':
        continue
    man = json.load(open(mp, encoding='utf-8'))
    packs = man.get('packs')
    if isinstance(packs, dict):
        for p in packs.values():
            if isinstance(p, list):
                for e in p:
                    if isinstance(e, dict) and 'name' in e:
                        EARLIER.add(e['name'])
    if isinstance(man.get('replace'), list):
        EARLIER_REPLACED |= set(man['replace'])
OURS |= EARLIER
for k in OURS:
    assert not k.startswith('maps/%s/' % FOLDER), k
EARLIER_STAGING = sorted(__import__('glob').glob('/opt/metin2/cache/yohara/*-staging/add/property/property')) + \
    sorted(__import__('glob').glob('/opt/metin2/cache/*-staging/add/property/property'))
# never our own staging (the default dir or another one of ours): its properties are what this run stages
EARLIER_STAGING = [d for d in EARLIER_STAGING if 'balathor-staging' not in d and
                   not os.path.abspath(d).startswith(os.path.abspath(STAGING) + os.sep)]

GF = dict(gfres.GF)
RES = dict(GF)
RES.update(PK)                      # the package wins; GF fills what it lacks
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
                OURPROP.setdefault(c, (root, os.path.join(dp, f)))
SRCPROP = {}
for k, p in sorted(RES.items(), key=lambda kp: (kp[0] not in PK, kp[0])):      # the package's first
    if k.startswith('property/'):
        c = prop_crc(p)
        if c is not None:
            SRCPROP.setdefault(c, (k, p))

add = collections.defaultdict(dict)       # group -> key -> src (group: 'map', 'property', 'obj', 'mobs')
manifest = {'maps': {}, 'packs': {}, 'unresolved': {}, 'races': {}, 'replace': []}

# ---------------------------------------------------------------- the map
mp = 'maps/%s/' % FOLDER
files = dict((mp + k[len('maps/%s/' % SRC):], p) for k, p in PK.items() if k.startswith('maps/%s/' % SRC))
sectors = sorted(k for k in files if k.endswith('/areadata.txt'))
assert len(sectors) == SIZE[0] * SIZE[1], len(sectors)
mpt = open(files[mp + 'mapproperty.txt'], 'rb').read().decode('latin1')
assert 'ParentMapName' not in mpt and re.search(r'MapType\s+"Outdoor"', mpt), mpt
st = open(files.pop(mp + 'setting.txt'), 'rb').read().decode('latin1').replace('\r', '')
assert re.search(r'MapSize\s+%d\s+%d' % SIZE, st) and re.search(r'BasePosition\s+%d\s+%d' % BASE, st), st
st2, n = re.subn(r'(?im)^(ViewRadius[ \t]+)\d+', lambda m: m.group(1) + str(M['view_radius']), st)
assert n == 1
add['map'][mp + 'setting.txt'] = gen(mp + 'setting.txt', crlf(st2).encode('latin1'))
ts = norm(re.search(r'TextureSet\s+(\S+)', st, re.I).group(1))
env = norm(re.search(r'Environment\s+(\S+)', st, re.I).group(1))
assert ts in RES, ts
envkey = 'd:/ymir work/environment/' + env
assert envkey not in OURS, envkey
et = open(RES[envkey], 'rb').read().decode('latin1').replace('\r', '')
et, n = re.subn(r'(?im)^([ \t]*)foglevel[ \t]+\d+[ \t]*$',
                lambda m: '%sEnable        %d\n%sNearDistance  %.6f\n%sFarDistance   %.6f' % (
                    m.group(1), M['fog_on'], m.group(1), M['fog'][0], m.group(1), M['fog'][1]), et)
assert n == 1 and re.search(r'(?im)^\s*NearDistance', et) and not re.search(r'(?im)^\s*foglevel', et), env
envsrc = gen(envkey, crlf(et).encode('latin1'))
RES[envkey] = envsrc

used = collections.Counter()
for s in sectors:
    t = open(files[s], 'rb').read().decode('latin1').replace('\r', '')
    for body in re.findall(r'Start Object\d+\n(.*?)End Object\n', t, re.S):
        used[crc_of_body(body)] += 1
prop_src, drop = {}, {}
for crc in sorted(used):
    if crc in OURPROP:
        continue
    kp = SRCPROP.get(crc)
    if not kp:
        drop[crc] = 'no property (our property pack, the package, GF)'
        continue
    mdl = model_of(open(kp[1], 'rb').read().decode('latin1'))
    if mdl and mdl.endswith('.gr2') and mdl in RES and open(RES[mdl], 'rb').read(4) == GR2_64:
        drop[crc] = '64-bit GR2 %s' % mdl
        continue
    if mdl and mdl.endswith('.gr2') and mdl not in RES and mdl not in OURS:
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
add['map'][mp + env] = envsrc               # the map folder's own copy (as our maps have)
add['map'][envkey] = envsrc
seeds = {ts}
for crc, (k, p) in prop_src.items():
    add['property'][k] = p
    seeds.add(k)
    mdl = gfres.prop_attr_model(open(p, 'rb').read().decode('latin1'))
    if mdl and gfres.mdatr_of(mdl) in RES:
        seeds.add(gfres.mdatr_of(mdl))
for crc in sorted(used):
    if crc not in OURPROP:
        continue
    root, p = OURPROP[crc]
    for r in gfres.refs_of('property/x.prb', p):
        seeds.add(r)
for r in gfres.refs_of(envkey, envsrc):
    seeds.add(r)
unres_all = set()
f2, unres_map, _ = gfres.closure(sorted(seeds), OURS)
for k, src in f2.items():
    if k in OURS or any(k in add[g] for g in add) or k.startswith('maps/'):
        continue
    grp = 'property' if k.startswith('property/') else 'map' if k.startswith(MAP_PREFIXES) else 'obj'
    add[grp][k] = src
unres_all |= set(u for u in unres_map if not u.endswith('.msenv') and not (
    u.startswith('property/') and not u.endswith(('.prb', '.prd', '.pre', '.prt', '.pra'))))
manifest['maps'][str(M['index'])] = dict(
    folder=FOLDER, source='package (dracaryS) ' + SRC, size=list(SIZE), base=list(BASE), pack='balathor_map',
    textureset=ts, environment=env, atlas_image=None,
    objects=dict(crc_used=len(used), ours=sum(1 for c in used if c in OURPROP), staged=len(prop_src),
                 dropped=len(drop)),
    removed_objects=dict((str(c), dict(objects=n, why=drop[c])) for c, n in sorted(removed.items())))

# ---------------------------------------------------------------- the races (npclist rows of the lair's vnums)
npc, alias = {}, {}
if NPCLIST:
    for l in open(NPCLIST, encoding='latin1'):
        t = l.split()
        if len(t) >= 3 and t[0] == '0':
            alias[t[1].lower()] = t[2].lower()
        elif len(t) >= 2 and t[0].isdigit():
            npc[int(t[0])] = t[1].lower()
races, unres_races = {}, {}
for v in DATA['vnums']:
    name = npc.get(v) or DATA['npclist_expected'][str(v)]
    folder = alias.get(name, name)
    cands = ['d:/ymir work/%s/%s/%s.msm' % (d, folder, folder) for d in RACE_DIRS]
    have = next((c for c in cands if c in OURS), None)
    if have:
        races[v] = dict(race=name, msm=have, status='ours' if have not in EARLIER else 'earlier builder')
        continue
    src = next((c for c in cands if c in RES), None)
    if not src:
        races[v] = dict(race=name, status='MISSING (not in our listing, the package or GF)')
        continue
    races[v] = dict(race=name, msm=src, status='staged')
    f, u, o = gfres.closure([src.rsplit('/', 1)[0] + '/'], OURS)
    for k, s in f.items():
        if k in OURS or any(k in add[p] for p in add):
            continue
        add['mobs'][k] = s
    if u:
        unres_races[name] = sorted(u)

# ---------------------------------------------------------------- the effects / pictures the exe and python name
# the boss window and the frost (root uiscript/guildwhitedragonlairwindow.py, uiguildwhitedragon.py): the package's
# whole ui/game/guild_white_dragon_lair folder, ui/whitedragon_damage_01.dds and the atlases its .sub cut
UI_NAMES = sorted(k for k in PK if k.startswith(DATA['ui_dir'])) + list(DATA.get('ui_files', []))
assert len([k for k in UI_NAMES if k.endswith('.sub')]) >= 18, UI_NAMES


def sub_image(key, src):
    """the picture a .sub cuts (EterLib GrpSubImage: version 1.0 -> "d:/ymir work/ui/" + image)"""
    b = open(src, 'rb').read()
    m = re.search(rb'(?im)^\s*image\s+"([^"]+)"', b)
    assert m, key
    img = norm(m.group(1).decode('latin1'))
    if re.search(rb'(?im)^\s*version\s+2\.0', b):
        return key.rsplit('/', 1)[0] + '/' + img
    return norm('d:/ymir work/ui/' + img)


for k in DATA['effects'] + UI_NAMES:
    if k in OURS:
        continue
    assert k in RES, k
    if k.endswith('.sub'):
        add['mobs'][k] = RES[k]
        t = sub_image(k, RES[k])
        assert t in RES or t in OURS, (k, t)
        if t not in OURS:
            add['mobs'][t] = RES[t]
        continue
    f, u, o = gfres.closure([k], OURS)
    for kk, ss in f.items():
        if kk in OURS or any(kk in add[p] for p in add):
            continue
        add['mobs'][kk] = ss
    unres_all |= set(u)

# the textures an effect mesh (.mde) or script (.mse) names with a full path (the closure does not read them)
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
PACK_OF_GROUP = {'map': 'balathor_map', 'obj': 'balathor_obj', 'mobs': 'balathor_mobs', 'property': 'property'}
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
manifest['etc_pack_names'] = len(ETC_NAMES)
manifest['etc_pack_names_staged'] = sum(1 for p in packs for k in packs[p] if k in ETC_NAMES)
manifest['ui'] = sorted(set(k for k in UI_NAMES) | set(t for p in packs for t in packs[p]
                                                      if t.startswith('d:/ymir work/ui/') and p != 'property'))
for p in packs:
    ents = []
    for k in sorted(packs[p]):
        src = packs[p][k]
        dst = os.path.join(STAGING, 'add', p, k.replace('d:/', 'd_/', 1))
        os.makedirs(os.path.dirname(dst), exist_ok=True)
        shutil.copyfile(src, dst)
        b = open(src, 'rb').read()
        where = 'gen' if src.startswith(GEN) else 'package' if src.startswith(tuple(PKG)) else \
            'gf' if src.startswith(gfres.G) else src
        ents.append(dict(name=k, source=where, size=len(b), sha1=hashlib.sha1(b).hexdigest()))
    manifest['packs'][p] = ents
manifest['unresolved']['map'] = sorted(unres_all)
manifest['unresolved']['races'] = unres_races
manifest['unresolved']['effects'] = sorted(extra_missing)
json.dump(manifest, open(os.path.join(HERE, 'balathor_manifest.json'), 'w', encoding='utf-8'), indent=1,
          sort_keys=True, ensure_ascii=False)
for p in packs:
    print('%-14s %4d files %6.2f MB' % (p, len(packs[p]), sum(os.path.getsize(v) for v in packs[p].values()) / 1e6))
m = manifest['maps'][str(M['index'])]
print(M['index'], m['folder'], 'objects:', m['objects'], 'removed:', m['removed_objects'])
print('smoke etc names (not ours) staged:', manifest['etc_pack_names_staged'], 'of', len(ETC_NAMES))
print('races:', dict((v, r['status']) for v, r in races.items()))
print('unresolved map:', manifest['unresolved']['map'])
print('unresolved races:', unres_races)
print('unresolved effects:', manifest['unresolved']['effects'])
shutil.rmtree(GEN, ignore_errors=True)       # the generated files are copied under add/ already
