# -*- coding: utf-8 -*-
# MT2009_PLUS_SHIP_DEFENSE_V1 (client) - Obrona Statku (Hydra; map 367, metin2_map_defensewave, 3x3 at 128000 486400):
# the client files staged for build_shipdefense_packs.py, from the GF 26.1.11 client (the ship as the official game
# has it) and, for what GF lacks, the Ameria client sources. The same approach as ../cape301/stage_cape301.py.
#
#   python3 stage_shipdefense.py [<staging dir>] [<work dir>] [<npclist.txt>]       (host; no lzo needed)
#
# defaults: /opt/metin2/cache/yohara/hydra-staging, /opt/metin2/cache/yohara/cape301-work (c58.lst + x/property of
# the client we build on, written by ../atlantis/dump_base.py <BASE pack dir> <work dir>), the npclist of client
# 2.0.61 (/opt/metin2/cache/c61/chk/gamedata/npclist.txt: it has 3949-3970 and 20432-20437 with the defensewave_*
# aliases already). Writes <staging>/add/<pack>/<in-pack name> ("d:/" as "d_/") and shipdefense_manifest.json.
#
#   maps/metin2_map_defensewave/...   -> new pack hydra_map (9 sectors, mapproperty, setting.txt with the server's
#                                        BasePosition 128000 486400 - GF's says 0 0 -, a msenv copy)
#   textureset, terrain textures, msenv, atlas (atlas.sub generated: GF has only the .dds), the ship's objects
#   (zone/defensewave: the hull, floor, masts ...)                                     -> hydra_map
#   property/defensewave/*.prd ...    -> pack property (the exe loads map objects only from pack/property)
#   the races of the ship (3949-3965, 3970, 20432-20437 and the wave mobs 3401/3402/3405/3601-3605 when our
#   listing has no .msm for them), every effect/monster2/defense_* (the server's laser defense_mini_laser.mse is
#   named by no .msa: seeded by name) and their sounds                                 -> new pack hydra_mobs
#
# A name our client already has (the dump listing + the base client's pre-import listing + what
# ../cape301/stage_cape301.py stages, since the build runs that first) is left out - ours wins.
# GF's msenv names "foglevel 14": exe 2.0.25 reads Enable/NearDistance/FarDistance only - 20000 / 80000 (as 301).
# A motlist.txt line whose .msa nobody has (the Hydra's "SPAWN drop.msa": GF ships none, Ameria neither) is taken
# out of a generated copy - the exe would log the missing file at every spawn.
# 64-bit GR2 (header e59b495e, exe 2.0.25 cannot read it): none may be staged.
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

gfres.GR2DIR = '/opt/metin2/cache/arezzo-work/client/az58/gr2'
gfres.GR2DEC = os.path.join(gfres.GR2DIR, 'gr2dec')

STAGING = sys.argv[1] if len(sys.argv) > 1 else '/opt/metin2/cache/yohara/hydra-staging'
WORK = sys.argv[2] if len(sys.argv) > 2 else '/opt/metin2/cache/yohara/cape301-work'
NPCLIST = sys.argv[3] if len(sys.argv) > 3 else '/opt/metin2/cache/c61/chk/gamedata/npclist.txt'
OURS_LST = os.path.join(WORK, 'c58.lst')
PRE_LST = '/opt/metin2/cache/tcm/gf28/ourpacks_pre.txt'
CAPE_MANIFEST = os.path.join(HERE, '..', 'cape301', 'cape301_manifest.json')
AMERIA = '/opt/metin2/ameria/ameria-prj-2025/tools/FoxFSArchiver/source'
MAP = 'metin2_map_defensewave'
SIZE = (3, 3)
BASE_POS = (128000, 486400)        # = linux-port/docker/game/shipdefense/map/metin2_map_defensewave/Setting.txt
GR2_64 = b'\xe5\x9b\x49\x5e'
FOG = (20000.0, 80000.0)
MAP_PACK, MOB_PACK = 'hydra_map', 'hydra_mobs'
norm = gfres.norm

# Every vnum the ship spawns (linux-port/docker/game/shipdefense/data/dungeon/defense_wave/*.txt, the C++ of
# playerbot_ship_defense.cpp, the quest obrona_statku): the ship's own races and the wave's tritons and crabs.
VNUMS = list(range(3949, 3966)) + [3970, 20432, 20433, 20434, 20435, 20436, 20437,
                                     3401, 3402, 3405, 3601, 3602, 3603, 3604, 3605]
RACE_DIRS = ('guild', 'npc', 'npc2', 'npc_pet', 'npc_mount', 'monster', 'monster2')
EFFECT_PREFIX = 'd:/ymir work/effect/monster2/defense_'

# ---------------------------------------------------------------- what our client has
OURS = set(gfres.load_ours(PRE_LST))
for l in open(OURS_LST, encoding='utf-8', errors='replace'):
    t = l.rstrip('\n').split(' ', 1)
    if len(t) == 2:
        OURS.add(norm(t[1]))
CAPE = set()
if os.path.exists(CAPE_MANIFEST):
    for p, ents in json.load(open(CAPE_MANIFEST, encoding='utf-8'))['packs'].items():
        CAPE.update(e['name'] for e in ents)
OURS |= CAPE


def index_ameria(root):
    m = {}
    if not os.path.isdir(root):
        return m
    for top in sorted(os.listdir(root)):
        tp = os.path.join(root, top)
        if not os.path.isdir(tp):
            continue
        for sub in os.listdir(tp):
            sp = os.path.join(tp, sub)
            if not os.path.isdir(sp):
                continue
            if sub.lower() == 'ymir work':
                pref = 'd:/ymir work/'
            elif sub.lower() in ('property', 'sound', 'textureset', 'icon'):
                pref = sub.lower() + '/'
            else:
                continue
            for dp, dn, fn in os.walk(sp):
                for f in fn:
                    ap = os.path.join(dp, f)
                    m.setdefault(norm(pref + os.path.relpath(ap, sp)), ap)
    return m


AM = index_ameria(AMERIA)
GF = dict(gfres.GF)
RES = dict((k, p) for k, p in AM.items() if not k.startswith(('maps/', 'property/')))
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


OURPROP = {}
for dp, dn, fn in os.walk(os.path.join(WORK, 'x', 'property')):
    for f in fn:
        c = prop_crc(os.path.join(dp, f))
        if c is not None:
            OURPROP[c] = os.path.join(dp, f)
GFPROP = {}
for k, p in GF.items():
    if k.startswith('property/'):
        c = prop_crc(p)
        if c is not None:
            GFPROP.setdefault(c, (k, p))

# ---------------------------------------------------------------- the map's objects
add = collections.defaultdict(dict)       # pack -> key -> src
mkeys = sorted(k for k in GF if k.startswith('maps/%s/' % MAP) and not k.endswith('/regen.txt'))
sectors = sorted(k for k in mkeys if k.endswith('/areadata.txt'))
assert len(sectors) == SIZE[0] * SIZE[1], len(sectors)
used = collections.Counter()
for s in sectors:
    t = open(GF[s], 'rb').read().decode('latin1').replace('\r', '')
    for body in re.findall(r'Start Object\d+\n(.*?)End Object\n', t, re.S):
        used[int(body.split('\n')[1].strip().split('#')[0])] += 1
prop_src = {}
missing_prop = []
for crc in sorted(used):
    if crc in OURPROP:
        continue
    kp = GFPROP.get(crc)
    if not kp:
        missing_prop.append(crc)
        continue
    assert kp[0] not in OURS, ('property name ours with another CRC', kp[0])
    prop_src[crc] = kp
assert not missing_prop, missing_prop

# ---------------------------------------------------------------- setting.txt, msenv, atlas (generated)
skey = 'maps/%s/setting.txt' % MAP
st = open(GF[skey], 'rb').read().decode('latin1').replace('\r', '')
st, n = re.subn(r'(?m)^BasePosition\s+\d+\s+\d+\s*$', 'BasePosition\t%d\t%d' % BASE_POS, st)
assert n == 1, st
add[MAP_PACK][skey] = gen(skey, crlf(st).encode('latin1'))
ts = norm(re.search(r'TextureSet\s+(\S+)', st, re.I).group(1))
env = norm(re.search(r'Environment\s+(\S+)', st, re.I).group(1))
envkey = 'd:/ymir work/environment/' + env
et = open(GF[envkey], 'rb').read().decode('latin1').replace('\r', '')
et, n = re.subn(r'(?im)^([ \t]*)foglevel[ \t]+\d+[ \t]*$',
                lambda m: '%sEnable        1\n%sNearDistance  %.6f\n%sFarDistance   %.6f' % (
                    m.group(1), m.group(1), FOG[0], m.group(1), FOG[1]), et)
assert n == 1 and re.search(r'(?im)^\s*NearDistance', et) and not re.search(r'(?im)^\s*foglevel', et), env
envsrc = gen(envkey, crlf(et).encode('latin1'))
atlas_dds = 'd:/ymir work/ui/%s_atlas.dds' % MAP
atlas_sub = 'd:/ymir work/ui/atlas/%s/atlas.sub' % MAP
assert atlas_dds in GF and atlas_sub not in GF and atlas_sub not in OURS
add[MAP_PACK][atlas_sub] = gen(atlas_sub, crlf('title subImage\nversion 1.0\nimage "%s_atlas.dds"\nleft 0\ntop 0\n'
                                              'right 256\nbottom 256\n' % MAP).encode('latin1'))

# ---------------------------------------------------------------- the closure of the map
seeds = set(k for k in mkeys if k != skey) | {ts, atlas_dds}
for crc, (k, p) in prop_src.items():
    seeds.add(k)
    mdl = gfres.prop_attr_model(open(p, 'rb').read().decode('latin1'))
    if mdl and gfres.mdatr_of(mdl) in RES:
        seeds.add(gfres.mdatr_of(mdl))
for crc in used:
    if crc in OURPROP:
        k = norm(os.path.relpath(OURPROP[crc], os.path.join(WORK, 'x', 'property')))
        seeds |= gfres.refs_of(k, OURPROP[crc])
RES[envkey] = envsrc
seeds.add(envkey)
files, unres_map, _ = gfres.closure(sorted(seeds), OURS)
for k, src in files.items():
    if k in OURS or k.endswith('/server_attr') or k in add[MAP_PACK]:
        continue
    if k.startswith('maps/') and not k.startswith('maps/%s/' % MAP):
        continue
    add['property' if k.startswith('property/') else MAP_PACK].setdefault(k, src)
add[MAP_PACK]['maps/%s/%s' % (MAP, env)] = envsrc

# ---------------------------------------------------------------- the races and the effects
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
mob_seeds = []
for v in VNUMS:
    name = npc.get(v)
    if not name:
        races[v] = dict(status='no npclist row')
        continue
    folder = alias.get(name, name)
    cands = ['d:/ymir work/%s/%s/%s.msm' % (d, folder, name) for d in RACE_DIRS]
    have = next((c for c in cands if c in OURS), None)
    if have:
        races[v] = dict(race=name, msm=have, status='ours' if have not in CAPE else 'cape301')
        continue
    src = next((c for c in cands if c in RES), None)
    if not src:
        races[v] = dict(race=name, status='MISSING (not in our listing, GF or Ameria) - base client must have it')
        continue
    races[v] = dict(race=name, msm=src, status='staged')
    mob_seeds.append(src.rsplit('/', 1)[0] + '/')
effects = sorted(k for k in RES if k.startswith(EFFECT_PREFIX))
for sd in sorted(set(mob_seeds)) + [[e] for e in effects]:
    f, u, o = gfres.closure(sd if isinstance(sd, list) else [sd], OURS)
    for k, s in f.items():
        if k in OURS or any(k in add[p] for p in add):
            continue
        add[MOB_PACK][k] = s
    if u:
        unres_races[sd if isinstance(sd, str) else sd[0]] = sorted(u)

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

# motlist.txt: a motion nobody ships (GF, Ameria, our client) leaves the generated copy
motlist_fixed = {}
for p in list(add):
    for k, src in list(add[p].items()):
        if not k.endswith('/motlist.txt'):
            continue
        d = k.rsplit('/', 1)[0] + '/'
        lines = open(src, 'rb').read().decode('latin1').replace('\r', '').split('\n')
        keep, gone = [], []
        for l in lines:
            t = l.split()
            if len(t) >= 3 and t[2].lower().endswith('.msa'):
                m = d + norm(t[2])
                if m not in OURS and not any(m in add[q] for q in add):
                    gone.append(l.strip())
                    continue
            keep.append(l)
        if gone:
            add[p][k] = gen(k, crlf('\n'.join(keep).rstrip('\n') + '\n').encode('latin1'))
            motlist_fixed[k] = gone
for k in motlist_fixed:
    d = k.rsplit('/', 1)[0] + '/'
    for v in list(unres_races.values()):
        for m in [m for m in v if m.startswith(d) and m.endswith('.msa')]:
            v.remove(m)
unres_races = dict((k, v) for k, v in unres_races.items() if v)

# ---------------------------------------------------------------- checks and the staging
bad64 = sorted(k for p in add for k, s in add[p].items() if k.endswith('.gr2') and open(s, 'rb').read(4) == GR2_64)
if bad64:
    raise SystemExit('64-bit GR2 staged: %s' % bad64)
for p in add:
    for k in add[p]:
        assert k == k.lower() and '\\' not in k, k
        assert k not in OURS, k
        assert len(k.encode('cp1252')) < 161, k
assert 'd:/ymir work/effect/monster2/defense_mini_laser.mse' in add[MOB_PACK]
manifest = {'packs': {}, 'unresolved': {}, 'races': dict((str(v), r) for v, r in races.items()),
            'motlist_removed': motlist_fixed,
            'objects': {'crc_used': len(used), 'ours': sum(1 for c in used if c in OURPROP), 'staged': len(prop_src)}}
for p in sorted(add):
    ents = []
    for k in sorted(add[p]):
        src = add[p][k]
        dst = os.path.join(STAGING, 'add', p, k.replace('d:/', 'd_/', 1))
        os.makedirs(os.path.dirname(dst), exist_ok=True)
        shutil.copyfile(src, dst)
        b = open(src, 'rb').read()
        where = 'gen' if src.startswith(GEN) else 'gf' if src.startswith(gfres.G) else 'ameria' if src.startswith(AMERIA) else src
        ents.append(dict(name=k, source=where, size=len(b), sha1=hashlib.sha1(b).hexdigest()))
    manifest['packs'][p] = ents
manifest['unresolved']['map'] = sorted(u for u in unres_map if not u.endswith('.msenv') and not (
    u.startswith('property/') and not u.endswith(('.prb', '.prd', '.pre', '.prt', '.pra'))))
manifest['unresolved']['races'] = unres_races
manifest['unresolved']['effects'] = sorted(extra_missing)
json.dump(manifest, open(os.path.join(HERE, 'shipdefense_manifest.json'), 'w', encoding='utf-8'), indent=1,
          sort_keys=True, ensure_ascii=False)
for p in sorted(add):
    print('%-10s %4d files %6.2f MB' % (p, len(add[p]), sum(os.path.getsize(v) for v in add[p].values()) / 1e6))
print('objects:', manifest['objects'])
print('races:', dict((v, r['status']) for v, r in races.items() if r['status'] != 'ours'))
print('motlist lines removed:', motlist_fixed)
print('unresolved map:', manifest['unresolved']['map'])
print('unresolved races/effects:', unres_races)
print('unresolved effect textures:', manifest['unresolved']['effects'])
print('ameria files:', sorted(e['name'] for p in manifest['packs'].values() for e in p if e['source'] == 'ameria'))
print('gr2 texture decode failures (BitKnit motions, no textures there): %d, models: %s' % (
    len(gfres.GR2_FAIL), sorted(k for k in gfres.GR2_FAIL if not re.search(
        r'/(wait|walk|run|normal_attack|special_attack|front_|back_|damage|dead|skill|spawn|die)[^/]*\.gr2$', k))))
