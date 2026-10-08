# -*- coding: utf-8 -*-
# MT2009_PLUS_ATLANTYDA_V1 - Ruiny Atlantydy (map 158, plechito_summer2022_dungeon): the client files staged for
# build_atlantis_packs.py, from the package "Ruins of Atlantis [With quest]" (Plechito, summer 2022).
#
#   python3 stage_atlantis.py [<package Client dir>] [<staging dir>]     (host; no lzo needed)
#
# defaults: the unpacked package in the session scratchpad, staging /opt/metin2/cache/atlantis-staging.
# Writes <staging>/add/<pack>/<in-pack name> ("d:/" as "d_/") and tools/atlantis/atlantis_manifest.json
# (every entry: name, pack, source, size, sha1; plus the removed map objects and what is missing).
#
#   maps/plechito_summer2022_dungeon/...   -> pack maps      (the 9 sectors, setting.txt, mapproperty.txt and a
#                                                             copy of the msenv, as for 351/352/360-366)
#   property/...                           -> pack property  (the exe loads map objects only from pack/property)
#   the races (monster2/monster/npc plechito_summer2022/*)  -> new pack at_mobs (with their effects)
#   the rest (zone objects, effects, textureset, msenv, terrain, atlas, item icons) -> new pack at_maps
#
# A name our client already has (the c58 listing + the base client's pre-import listing) is left out - ours
# wins. A key that is also in the GF 26.1.11 client is taken from GF (az58's rule), but maps/ and property/.
# 64-bit GR2 (header e59b495e, exe 2.0.25 cannot read it): none may be staged. The map's objects whose
# models are 64-bit and have no 32-bit copy anywhere (zone/plechi_dungeon/water_dungeon/*, the Arezzo client
# has the same 64-bit files), and the 4 objects of CRC 1023488681 that have no property in the package, in
# our property pack, in Arezzo or GF, are taken out of the sectors' areadata.txt (generated copies, objects
# renumbered from 000) - as az29 did for the Enchanted Forest's crowns.
import collections
import hashlib
import json
import os
import re
import shutil
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, '..', 'az58'))
import gfres  # noqa: E402  (indexes the GF client at import)
import dxt  # noqa: E402

gfres.GR2DIR = '/opt/metin2/cache/arezzo-work/client/az58/gr2'
gfres.GR2DEC = os.path.join(gfres.GR2DIR, 'gr2dec')
if not os.path.exists(gfres.GR2DEC):
    gfres.GR2DIR = os.path.normpath(os.path.join(HERE, '..', '..', '..', 'client-2.0.28', 'tools', 'gf28', 'gr2'))
    gfres.GR2DEC = os.path.join('/opt/metin2/cache/atlantis-work', 'gr2dec')

PKG = sys.argv[1] if len(sys.argv) > 1 else \
    '/opt/metin2/cache/atlantis-package/Ruins of Atlantis [With quest]/Client'
STAGING = sys.argv[2] if len(sys.argv) > 2 else '/opt/metin2/cache/atlantis-staging'
OURS_LST = '/opt/metin2/cache/atlantis-work/c58.lst'      # "<pack> <name>" of client 2.0.58 (dump: README)
PRE_LST = '/opt/metin2/cache/tcm/gf28/ourpacks_pre.txt'
AREZZO = '/opt/metin2/cache/arezzo/cpack/files'
DATA = json.load(open(os.path.join(HERE, 'atlantis.json'), encoding='utf-8'))
MAP = DATA['map']['folder']
GR2_64 = b'\xe5\x9b\x49\x5e'
norm = gfres.norm

# the package's files, under their in-pack names
SKIP = ('locale/', 'root/', 'd:/ymir work/ui/game/questboard/', 'd:/ymir work/npc/plechito_animals/')


def index_tree(root, mapdirs):
    m = {}
    for top in os.listdir(root):
        tp = os.path.join(root, top)
        if not os.path.isdir(tp):
            continue
        if top.lower() == 'ymir work':
            pref = 'd:/ymir work/'
        elif top.lower() in mapdirs:
            pref = 'maps/' + top.lower() + '/'
        else:
            pref = top.lower() + '/'
        for dp, dn, fn in os.walk(tp):
            for f in fn:
                ap = os.path.join(dp, f)
                m[norm(pref + os.path.relpath(ap, tp))] = ap
    return m


PK = dict((k, v) for k, v in index_tree(PKG, {MAP}).items() if not k.startswith(SKIP))
AZ = index_tree(AREZZO, set(d.lower() for d in os.listdir(AREZZO)
                            if os.path.exists(os.path.join(AREZZO, d, 'setting.txt'))))
OURS = set(gfres.load_ours(PRE_LST))
for l in open(OURS_LST, encoding='utf-8', errors='replace'):
    t = l.rstrip('\n').split(' ', 1)
    if len(t) == 2:
        OURS.add(norm(t[1]))

RES = dict(AZ)
RES.update(PK)
for k, p in gfres.GF.items():
    if not k.startswith(('maps/', 'property/')):
        RES[k] = p
gfres.GF = RES

GEN = os.path.join(STAGING, 'gen')
shutil.rmtree(STAGING, ignore_errors=True)
os.makedirs(GEN)


def gen(key, data):
    p = os.path.join(GEN, key.replace('d:/', 'd_/', 1))
    os.makedirs(os.path.dirname(p), exist_ok=True)
    open(p, 'wb').write(data)
    return p


# ---------------------------------------------------------------- the map's objects
def prop_index(files):
    idx = {}
    for k, p in files.items():
        if not k.startswith('property/'):
            continue
        b = open(p, 'rb').read().replace(b'\r', b'').split(b'\n')
        if b and b[0].strip() == b'YPRT' and len(b) > 1:
            idx[int(b[1].strip())] = (k, p)
    return idx


PROPS = prop_index(PK)
OURPROP = {}
for dp, dn, fn in os.walk('/opt/metin2/cache/atlantis-work/x/property'):
    for f in fn:
        b = open(os.path.join(dp, f), 'rb').read().replace(b'\r', b'').split(b'\n')
        if b and b[0].strip() == b'YPRT' and len(b) > 1:
            try:
                OURPROP[int(b[1].strip())] = os.path.join(dp, f)
            except ValueError:
                pass
clash = sorted(set(PROPS) & set(OURPROP))
if clash:
    raise SystemExit('property CRC clash with our property pack: %s' % clash)

sectors = sorted(k for k in PK if k.startswith('maps/%s/' % MAP) and k.endswith('/areadata.txt'))
assert len(sectors) == DATA['map']['size'][0] * DATA['map']['size'][1], sectors
removed = collections.Counter()
removed_why = {}
kept = collections.Counter()
add = collections.defaultdict(dict)       # pack -> key -> src


def model_of(text):
    for l in text.replace('\r', '').split('\n'):
        t = l.split(None, 1)
        if len(t) == 2 and t[0].lower().endswith('file'):
            return norm(t[1].strip().strip('"'))
    return None


def drop_reason(crc):
    if crc not in PROPS:
        return 'no property (package, our property pack, Arezzo, GF)'
    k, p = PROPS[crc]
    mdl = model_of(open(p, 'rb').read().decode('latin1'))
    if mdl and mdl.endswith('.gr2') and mdl in PK and open(PK[mdl], 'rb').read(4) == GR2_64:
        return '64-bit GR2 %s (no 32-bit copy in Arezzo or GF)' % mdl
    return None


for s in sectors:
    t = open(PK[s], 'rb').read().decode('latin1').replace('\r', '')
    head, objs = t.split('Start Object', 1)[0], re.findall(r'Start Object\d+\n(.*?)End Object\n', t, re.S)
    out = []
    for body in objs:
        crc = int(body.split('\n')[1].strip().split('#')[0])
        why = drop_reason(crc)
        if why:
            removed[crc] += 1
            removed_why[crc] = why
            continue
        kept[crc] += 1
        out.append(body)
    if len(out) != len(objs):
        txt = head + ''.join('Start Object%03d\n%sEnd Object\n' % (i, b) for i, b in enumerate(out))
        # MT2009_PLUS_ATLANTYDA_TERRAIN_V1: the closing 'ObjectCount N' (CArea::__Load_LoadObject: without it
        # 'File Format ... ERROR 2' and no object of the sector loads - test client 2.0.59, sectors 000000/001001).
        txt += '\nObjectCount %d\n' % len(out)
        add['maps'][s] = gen(s, txt.replace('\n', '\r\n').encode('latin1'))

# ---------------------------------------------------------------- the closure
seeds = set(k for k in PK if k.startswith('maps/%s/' % MAP))
st = open(PK['maps/%s/setting.txt' % MAP], 'rb').read().decode('latin1')
ts = norm(re.search(r'TextureSet\s+(\S+)', st, re.I).group(1))
env = norm(re.search(r'Environment\s+(\S+)', st, re.I).group(1))
seeds |= {ts, 'd:/ymir work/environment/' + env}
envtxt = open(RES['d:/ymir work/environment/' + env], 'rb').read().decode('latin1')
assert re.search(r'(?im)^\s*NearDistance', envtxt) and re.search(r'(?im)^\s*FarDistance', envtxt) \
    and not re.search(r'(?im)^\s*foglevel', envtxt), env
for crc in kept:
    k, p = PROPS[crc]
    seeds.add(k)
    mdl = gfres.prop_attr_model(open(p, 'rb').read().decode('latin1'))
    if mdl and gfres.mdatr_of(mdl) in RES:
        seeds.add(gfres.mdatr_of(mdl))
files, unres_map, oh_map = gfres.closure(sorted(seeds), OURS)
for k, src in files.items():
    if k in OURS or k.endswith('/server_attr'):
        continue
    if k in add['maps']:
        continue
    pack = 'maps' if k.startswith('maps/') else 'property' if k.startswith('property/') else 'at_maps'
    add[pack][k] = src
add['maps']['maps/%s/%s' % (MAP, env)] = RES['d:/ymir work/environment/' + env]
# MT2009_PLUS_ATLANTYDA_TERRAIN_V1: the terrain lies flat at the height of the room's floor (height.raw 32767,
# the room DungeonBlock at z 16383.5) with one black texture (dark.dds): drawn, it covers the floor - the test
# client 2.0.59 showed a dark blue plain with no ground ("atlantyda nie ma tekstur"). The Plechito dungeons'
# own way, as Wukong's and the Scorpion's setting.txt: TerrainVisible 0 (MapOutdoorLoad.cpp reads it).
if not re.search(r'(?im)^\s*TerrainVisible', st):
    stv = st.rstrip('\r\n') + '\r\nTerrainVisible\t0\r\n'
    add['maps']['maps/%s/setting.txt' % MAP] = gen('maps/%s/setting.txt' % MAP, stv.encode('latin1'))

# the races: npclist alias plechito_summer2022/<dir>; the msm is <base>/plechito_summer2022/<dir>/<race>.msm
RACEDIR = {'plechi_summ2022_stone1a': 'plechi_summ2022_stone1', 'plechi_summ2022_stone1b': 'plechi_summ2022_stone1'}
races = {}
unres_races = {}
for m in DATA['mobs']:
    race = m['race']
    d = 'plechito_summer2022/' + RACEDIR.get(race, race)
    base = next((b for b in ('monster2', 'monster', 'npc', 'npc2') if 'd:/ymir work/%s/%s/%s.msm' % (b, d, race) in PK), None)
    if not base:
        raise SystemExit('race %s: no msm in the package' % race)
    races[m['vnum']] = dict(race=race, alias=d, msm='d:/ymir work/%s/%s/%s.msm' % (base, d, race))
    f, u, o = gfres.closure(['d:/ymir work/%s/%s/' % (base, d)], OURS)
    for k, src in f.items():
        if k in OURS:
            continue
        if not any(k in add[p] for p in add):
            add['at_mobs'][k] = src
    if u:
        unres_races[race] = sorted(u)

# item icons
for it in DATA['items']:
    k = norm(it['icon'])
    if k not in OURS:
        add['at_maps'][k] = PK[k]

# the atlas (the minimap of every sector stitched, 3x3 x 256 -> 256x256 DXT1, as gen58 for 2x2/3x3)
w, h = DATA['map']['size']
W, H, big = dxt.stitch(os.path.join(PKG, MAP), w, h)
side = 512 if max(w, h) >= 4 else 256
k = 'd:/ymir work/ui/%s_atlas.dds' % MAP
p = os.path.join(GEN, k.replace('d:/', 'd_/'))
os.makedirs(os.path.dirname(p), exist_ok=True)
dxt.write_dxt1(p, side, side, dxt.downscale(W, H, big, side, side))
add['at_maps'][k] = p
k2 = 'd:/ymir work/ui/atlas/%s/atlas.sub' % MAP
add['at_maps'][k2] = gen(k2, ('title subImage\r\nversion 1.0\r\nimage "%s_atlas.dds"\r\nleft 0\r\ntop 0\r\nright %d\r\nbottom %d\r\n'
                             % (MAP, side, side)).encode())

# MT2009_PLUS_ATLANTYDA_TERRAIN_V1: the textures an effect mesh (.mde, binary) or an effect script (.mse) names
# with a full "D:\\ymir work\\..." path - the closure above does not read them, so shine00.mde (the light shafts of
# floor 2, shine.mse) came without shine.dds and drew as flat blue planes (test client 2.0.59), and the bosses'
# water tornadoes, flower00a.mde and underwater_plant08b.mde lacked theirs too. Staged in the pack of the file
# that names them; what neither our client nor the package has is reported.
mde_missing = set()
for _ in range(2):
    for p in list(add):
        for k, src in list(add[p].items()):
            if not k.endswith(('.mde', '.mse')):
                continue
            for m in re.findall(rb'[A-Za-z]:[\\/][^\x00"\r\n]+?\.(?:dds|tga|png|jpg|mde)', open(src, 'rb').read(), re.I):
                t = m.decode('latin1').replace('\\', '/').lower()
                t = 'd:' + t[2:]
                if t in OURS or any(t in add[q] for q in add):
                    continue
                if t in PK:
                    add[p][t] = PK[t]
                else:
                    mde_missing.add(t)

# ---------------------------------------------------------------- checks and the staging
bad64 = sorted(k for p in add for k, s in add[p].items() if k.endswith('.gr2') and open(s, 'rb').read(4) == GR2_64)
if bad64:
    raise SystemExit('64-bit GR2 staged: %s' % bad64)
for p in add:
    for k in add[p]:
        assert k == k.lower() and '\\' not in k, k
        assert k not in OURS or k.startswith('maps/%s/' % MAP), k
manifest = {'packs': {}, 'removed_objects': {}, 'unresolved': {}, 'races': races}
for p in sorted(add):
    ents = []
    for k in sorted(add[p]):
        src = add[p][k]
        dst = os.path.join(STAGING, 'add', p, k.replace('d:/', 'd_/', 1))
        os.makedirs(os.path.dirname(dst), exist_ok=True)
        shutil.copyfile(src, dst)
        b = open(src, 'rb').read()
        rel = os.path.relpath(src, PKG) if src.startswith(PKG) else src
        ents.append(dict(name=k, source=rel, size=len(b), sha1=hashlib.sha1(b).hexdigest()))
    manifest['packs'][p] = ents
for crc, n in sorted(removed.items()):
    manifest['removed_objects'][str(crc)] = dict(objects=n, why=removed_why[crc])
ignore = ('.msenv',)
manifest['unresolved']['map'] = sorted(u for u in unres_map if not u.endswith(ignore))
manifest['unresolved']['races'] = unres_races
manifest['unresolved']['effects'] = sorted(mde_missing)
json.dump(manifest, open(os.path.join(HERE, 'atlantis_manifest.json'), 'w', encoding='utf-8'), indent=1, sort_keys=True,
          ensure_ascii=False)
for p in sorted(add):
    print('%-9s %4d files %6.2f MB' % (p, len(add[p]), sum(os.path.getsize(v) for v in add[p].values()) / 1e6))
print('objects kept %d, removed %d: %s' % (sum(kept.values()), sum(removed.values()),
                                          dict((c, removed_why[c]) for c in removed)))
print('unresolved map:', manifest['unresolved']['map'])
print('unresolved races:', unres_races)
print('gr2 texture decode failures:', gfres.GR2_FAIL)
