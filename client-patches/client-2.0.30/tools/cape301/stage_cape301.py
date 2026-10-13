# -*- coding: utf-8 -*-
# MT2009_PLUS_CAPE301_V1 - Przyladek Smoczego Ognia / Cape Dragon Head (map 301, Metin2_map_CapeDragonHead,
# 6x6 at 1024000 1664000): the client files staged for build_cape301_packs.py, from the GF 26.1.11 client
# (the map as the official game has it) and, for what GF lacks, the Ameria client sources.
#
#   python3 stage_cape301.py [<staging dir>] [<work dir>] [<npclist.txt>]       (host; no lzo needed)
#
# defaults: /opt/metin2/cache/yohara/cape301-staging, /opt/metin2/cache/yohara/cape301-work (c58.lst + x/property
# of the client we build on, written by ../atlantis/dump_base.py <BASE pack dir> <work dir>), the npclist of
# client 2.0.61 (/opt/metin2/cache/c61/chk/gamedata/npclist.txt; the race names, the "0 name folder" aliases).
# Writes <staging>/add/<pack>/<in-pack name> ("d:/" as "d_/") and tools/cape301/cape301_manifest.json.
#
# Our server has had the map since the base image (share/locale/poland/map/Metin2_map_CapeDragonHead, map index
# line "301 Metin2_map_CapeDragonHead", game2) and the client's atlasinfo.txt, localeinfo.py (MAP_CAPE),
# uimapnameshower.py (cape.tga) and locale_game.txt (MAP_CAPE "Przyladek Smoczego Ognia") already name it - but
# no pack had the map folder, so a player warped there (/warp 10905 17874) crashed.
#
#   maps/metin2_map_capedragonhead/...  -> new pack cape_map (36 sectors, setting/mapproperty, a msenv copy;
#                                          as catacomb_map holds maps/metin2_map_devilscatacomb)
#   property/...                        -> pack property (the exe loads map objects only from pack/property)
#   the races of the map that our packs lack (monster2/<race>/, npc/<race>/ ...) -> new pack cape_mobs
#   terrain textures, textureset, msenv, atlas         -> cape_map
#   the map objects' models (zone/, tree/, effect/ ...) -> new pack cape_obj (each pack's data under 29 MB)
#
# A name our client already has (dump listing + the base client's pre-import listing) is left out - ours wins.
# The base client's own packs (monster, monster2, npc, zone_*, map_*) have no listing on vps1: a race whose .msm
# is not in our listing is staged from GF even though the base client may have it - a name both have is then
# read from the base pack (earlier in Index; the exe keeps the first pack that registered a name).
# GF's msenv names "foglevel 1": exe 2.0.25 reads Enable/NearDistance/FarDistance only - the map's own older
# values (Ameria's capedragonhead.msenv: 20000 / 80000, the same colour) replace it.
# 64-bit GR2 (header e59b495e, exe 2.0.25 cannot read it): none may be staged; an object whose model is one is
# taken out of its sector's areadata.txt (generated copy, objects renumbered, closing ObjectCount line).
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

STAGING = sys.argv[1] if len(sys.argv) > 1 else '/opt/metin2/cache/yohara/cape301-staging'
WORK = sys.argv[2] if len(sys.argv) > 2 else '/opt/metin2/cache/yohara/cape301-work'
NPCLIST = sys.argv[3] if len(sys.argv) > 3 else '/opt/metin2/cache/c61/chk/gamedata/npclist.txt'
OURS_LST = os.path.join(WORK, 'c58.lst')
PRE_LST = '/opt/metin2/cache/tcm/gf28/ourpacks_pre.txt'
AMERIA = '/opt/metin2/ameria/ameria-prj-2025/tools/FoxFSArchiver/source'
MAP = 'metin2_map_capedragonhead'
SIZE = (6, 6)
GR2_64 = b'\xe5\x9b\x49\x5e'
FOG = (20000.0, 80000.0)
MAP_PACK = ('maps/', 'textureset/', 'd:/ymir work/terrainmaps/', 'd:/ymir work/environment/', 'd:/ymir work/ui/')
norm = gfres.norm

# Every vnum the server's map 301 spawns (npc.txt, regen/boss/stone.txt with group.txt and group_group.txt of
# the test server, 13 Oct 2026); 20025 is the invisible leader of the guard and horse groups (no model).
VNUMS = [3001, 3002, 3003, 3004, 3005, 3090, 3091, 3201, 3202, 3203, 3204, 3205, 3290, 3291,
         3501, 3502, 3503, 3504, 3505, 3590, 8051, 8052,
         9001, 9002, 9003, 9005, 9009, 9012, 10101, 10103, 20001, 20004, 20010, 20016, 20017,
         20029, 20030, 20047, 20057, 20058, 20059, 20349, 20373, 20377, 20378, 20380, 20381, 20382, 20383,
         30301, 30302, 30303, 30304, 30305]
RACE_DIRS = ('guild', 'npc', 'npc2', 'npc_pet', 'npc_mount', 'monster', 'monster2')

# ---------------------------------------------------------------- what our client has
OURS = set(gfres.load_ours(PRE_LST))
for l in open(OURS_LST, encoding='utf-8', errors='replace'):
    t = l.rstrip('\n').split(' ', 1)
    if len(t) == 2:
        OURS.add(norm(t[1]))


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
            elif top == 'map' or os.path.exists(os.path.join(sp, 'setting.txt')):
                pref = 'maps/' + sub.lower() + '/'
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


def model_of(text):
    for l in text.replace('\r', '').split('\n'):
        t = l.split(None, 1)
        if len(t) == 2 and t[0].lower().endswith('file'):
            return norm(t[1].strip().strip('"'))
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
AMPROP = {}
for k, p in AM.items():
    if k.startswith('property/'):
        c = prop_crc(p)
        if c is not None:
            AMPROP.setdefault(c, (k, p))

# ---------------------------------------------------------------- the map's objects
mkeys = sorted(k for k in GF if k.startswith('maps/%s/' % MAP))
sectors = sorted(k for k in mkeys if k.endswith('/areadata.txt'))
assert len(sectors) == SIZE[0] * SIZE[1], len(sectors)
add = collections.defaultdict(dict)       # pack -> key -> src
used = collections.Counter()
for s in sectors:
    t = open(GF[s], 'rb').read().decode('latin1').replace('\r', '')
    for body in re.findall(r'Start Object\d+\n(.*?)End Object\n', t, re.S):
        used[int(body.split('\n')[1].strip().split('#')[0])] += 1

prop_src = {}     # crc -> (key, path) of the property file to stage (GF, else Ameria)
drop = {}         # crc -> why
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
    if kp[0] in OURS:
        drop[crc] = 'property name %s is ours with another CRC' % kp[0]
        continue
    prop_src[crc] = kp

removed = collections.Counter()
for s in sectors:
    t = open(GF[s], 'rb').read().decode('latin1').replace('\r', '')
    head = t.split('Start Object', 1)[0]
    objs = re.findall(r'Start Object\d+\n(.*?)End Object\n', t, re.S)
    out = [b for b in objs if int(b.split('\n')[1].strip().split('#')[0]) not in drop]
    for b in objs:
        c = int(b.split('\n')[1].strip().split('#')[0])
        if c in drop:
            removed[c] += 1
    if len(out) != len(objs):
        txt = head + ''.join('Start Object%03d\n%sEnd Object\n' % (i, b) for i, b in enumerate(out))
        txt += '\nObjectCount %d\n' % len(out)
        add['cape_map'][s] = gen(s, crlf(txt).encode('latin1'))

# ---------------------------------------------------------------- the environment (exe 2.0.25 fog)
st = open(GF['maps/%s/setting.txt' % MAP], 'rb').read().decode('latin1')
ts = norm(re.search(r'TextureSet\s+(\S+)', st, re.I).group(1))
env = norm(re.search(r'Environment\s+(\S+)', st, re.I).group(1))
envkey = 'd:/ymir work/environment/' + env
et = open(GF[envkey], 'rb').read().decode('latin1').replace('\r', '')
et, n = re.subn(r'(?im)^([ \t]*)foglevel[ \t]+\d+[ \t]*$',
                lambda m: '%sEnable        1\n%sNearDistance  %.6f\n%sFarDistance   %.6f' % (
                    m.group(1), m.group(1), FOG[0], m.group(1), FOG[1]), et)
assert n == 1 and re.search(r'(?im)^\s*NearDistance', et) and not re.search(r'(?im)^\s*foglevel', et), env
envsrc = gen(envkey, crlf(et).encode('latin1'))

# ---------------------------------------------------------------- the closure of the map
seeds = set(k for k in mkeys if k not in add['cape_map'])
seeds |= {ts, 'd:/ymir work/ui/atlas/%s/atlas.sub' % MAP, 'd:/ymir work/ui/%s_atlas.dds' % MAP}
for crc, (k, p) in prop_src.items():
    RES[k] = p
    seeds.add(k)
    mdl = gfres.prop_attr_model(open(p, 'rb').read().decode('latin1'))
    if mdl and gfres.mdatr_of(mdl) in RES:
        seeds.add(gfres.mdatr_of(mdl))
# The objects whose property our pack already has (all 219 of the map, 13 Oct 2026): their models, trees and
# effects are mostly NOT in our listing (zone/devils_dragon_island, zone/b, tree/b1_*: the base client's
# zone_* packs may have some) - what GF has is staged, what nobody has is reported.
REPLACE = {}      # our property files GF has fixed: ships_brokenbody00.prb names the developer's path
for crc in sorted(used):
    if crc not in OURPROP:
        continue
    p = OURPROP[crc]
    k = norm(os.path.relpath(p, os.path.join(WORK, 'x', 'property')))
    mdl = model_of(open(p, 'rb').read().decode('latin1'))
    if mdl and mdl not in OURS and mdl not in RES and crc in GFPROP and GFPROP[crc][0] == k:
        gmdl = model_of(open(GFPROP[crc][1], 'rb').read().decode('latin1'))
        if gmdl in RES or gmdl in OURS:
            p = REPLACE[k] = GFPROP[crc][1]
    for r in gfres.refs_of(k, p):
        seeds.add(r)
    mdl = gfres.prop_attr_model(open(p, 'rb').read().decode('latin1'))
    if mdl and gfres.mdatr_of(mdl) in RES:
        seeds.add(gfres.mdatr_of(mdl))
RES[envkey] = envsrc
seeds.add(envkey)
files, unres_map, _ = gfres.closure(sorted(seeds), OURS)
for k, src in files.items():
    if k in OURS or k.endswith('/server_attr'):
        continue
    if k.startswith('maps/') and not k.startswith('maps/%s/' % MAP):
        continue
    pack = 'property' if k.startswith('property/') else 'cape_map' if k.startswith(MAP_PACK) else 'cape_obj'
    add[pack].setdefault(k, src)
add['cape_map']['maps/%s/%s' % (MAP, env)] = envsrc
for k, p in REPLACE.items():
    add['property'][k] = p

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
for v in VNUMS:
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
        add['cape_mobs'][k] = s
    if u:
        unres_races[name] = sorted(u)

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

# ---------------------------------------------------------------- checks and the staging
bad64 = sorted(k for p in add for k, s in add[p].items() if k.endswith('.gr2') and open(s, 'rb').read(4) == GR2_64)
if bad64:
    raise SystemExit('64-bit GR2 staged: %s' % bad64)
for p in add:
    for k in add[p]:
        assert k == k.lower() and '\\' not in k, k
        assert k not in OURS or (p == 'property' and k in REPLACE), k
        assert len(k.encode('cp1252')) < 161, k
manifest = {'packs': {}, 'removed_objects': {}, 'unresolved': {}, 'races': races, 'replace': sorted(REPLACE),
            'objects': {'crc_used': len(used), 'ours': sum(1 for c in used if c in OURPROP),
                        'staged': len(prop_src), 'dropped': len(drop)}}
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
for crc, n in sorted(removed.items()):
    manifest['removed_objects'][str(crc)] = dict(objects=n, why=drop[crc])
# a property's "propertyname" value reads as a file name next to it (property/b/eff/volcano_bigsmoke.mse): not a file
manifest['unresolved']['map'] = sorted(u for u in unres_map if not u.endswith('.msenv') and not (
    u.startswith('property/') and not u.endswith(('.prb', '.prd', '.pre', '.prt', '.pra'))))
manifest['unresolved']['races'] = unres_races
manifest['unresolved']['effects'] = sorted(extra_missing)
json.dump(manifest, open(os.path.join(HERE, 'cape301_manifest.json'), 'w', encoding='utf-8'), indent=1, sort_keys=True,
          ensure_ascii=False)
for p in sorted(add):
    print('%-9s %4d files %6.2f MB' % (p, len(add[p]), sum(os.path.getsize(v) for v in add[p].values()) / 1e6))
print('objects: %s, removed %d: %s' % (manifest['objects'], sum(removed.values()), dict((c, drop[c]) for c in removed)))
print('races:', dict((v, r['status']) for v, r in races.items() if r['status'] != 'ours'))
print('unresolved map:', manifest['unresolved']['map'])
print('unresolved races:', unres_races)
print('unresolved effects:', manifest['unresolved']['effects'])
print('gr2 texture decode failures (BitKnit motions, no textures there): %d, models: %s' % (
    len(gfres.GR2_FAIL), sorted(k for k in gfres.GR2_FAIL if not re.search(r'/(wait|walk|run|normal_attack|special_attack|front_|back_|damage|dead|skill|spawn|die)[^/]*\.gr2$', k))))
