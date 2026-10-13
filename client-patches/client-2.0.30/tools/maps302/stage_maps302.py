# -*- coding: utf-8 -*-
# MT2009_PLUS_YOHARA_MAPS302_V1 - Zbocze Gautama (302, metin2_map_dawnmistwood, 7x4 at 1177600 1664000), Nefrytowa
# Zatoka (303, metin2_map_BayBlackSand, 3x6 at 1049600 1510400) and Gromiste Gory (304, metin2_map_Mt_Thunder, 4x6 at
# 1126400 1510400): the client files staged for build_maps302_packs.py, from the GF 26.1.11 client (the maps as the
# official game has them) and, for what GF lacks, the Ameria client sources. The same method as
# ../cape301/stage_cape301.py (map 301), for several maps at once; cape301's own tooling and output are untouched.
#
#   python3 stage_maps302.py [<staging dir>] [<work dir>] [<npclist.txt>]       (host; no lzo needed)
#
# defaults: /opt/metin2/cache/yohara/maps302-staging, /opt/metin2/cache/yohara/cape301-work (c58.lst + x/property of
# the client we build on - 2.0.64 - written by ../atlantis/dump_base.py <BASE pack dir> <work dir>), the npclist of
# client 2.0.61 (/opt/metin2/cache/c61/chk/gamedata/npclist.txt).
# Writes <staging>/add/<pack>/<in-pack name> ("d:/" as "d_/") and tools/maps302/maps302_manifest.json.
#
# The client build runs ../cape301/build_cape301_packs.py BEFORE build_maps302_packs.py on the same OUT, so every
# name cape301 stages (cape301_manifest.json) counts as ours here: a texture, tree or race 301 already brings is
# not staged twice.
#
# The server has had the three maps since the base image (map index 302-304) and the client's atlasinfo.txt,
# localeinfo.py (MAP_DAWN/MAP_BAY/MAP_THUNDER), uimapnameshower.py (dawn/bay/thunder.tga) and locale_game.txt
# already name them - but no pack had the map folders.
#
#   maps/<map>/..., its textureset, terrain textures, msenv, atlas -> one new pack per map (gautama_map,
#                                                                       zatoka_map, gromiste_map)
#   property/...                                                    -> pack property (the exe reads it only there)
#   the map objects' models (zone/, tree/, effect/ ...)             -> new packs yohara_obj, yohara_obj2, ...
#   the races of the maps our packs lack                            -> new packs yohara_mobs, yohara_mobs2, ...
# A pack is split (name2, name3 ...) before its raw data passes SPLIT bytes (the 29 MB limit of a pack's data).
#
# GF's msenv names "foglevel N": exe 2.0.25 reads Enable/NearDistance/FarDistance only - each map's own older values
# (Ameria's <map>.msenv) replace it. GF's setting.txt of Dawnmistwood says ViewRadius 512 (the later client's): the
# server's and Ameria's 128 is written, as every other map of ours has. 64-bit GR2 (header e59b495e) is never
# staged; an object whose model is one is taken out of its sector's areadata.txt (generated copy).
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

STAGING = sys.argv[1] if len(sys.argv) > 1 else '/opt/metin2/cache/yohara/maps302-staging'
WORK = sys.argv[2] if len(sys.argv) > 2 else '/opt/metin2/cache/yohara/cape301-work'
NPCLIST = sys.argv[3] if len(sys.argv) > 3 else '/opt/metin2/cache/c61/chk/gamedata/npclist.txt'
OURS_LST = os.path.join(WORK, 'c58.lst')
PRE_LST = '/opt/metin2/cache/tcm/gf28/ourpacks_pre.txt'
CAPE_MANIFEST = os.path.join(HERE, '..', 'cape301', 'cape301_manifest.json')
AMERIA = '/opt/metin2/ameria/ameria-prj-2025/tools/FoxFSArchiver/source'
GR2_64 = b'\xe5\x9b\x49\x5e'
SPLIT = 26 * 1000 * 1000
MAP_PREFIXES = ('maps/', 'textureset/', 'd:/ymir work/terrainmaps/', 'd:/ymir work/environment/', 'd:/ymir work/ui/')
norm = gfres.norm

# Every vnum the server spawns on each map (npc.txt, regen/boss/stone.txt resolved through group.txt and
# group_group.txt of the test server, 13 Oct 2026; npc.txt of 302 with the Temple guard 20426).
MAPS = [
    dict(index=302, folder='metin2_map_dawnmistwood', pack='gautama_map', size=(7, 4), base=(1177600, 1664000),
         fog=(1000.0, 35000.0), view_radius=128,
         vnums=[3101, 3102, 3103, 3104, 3105, 3301, 3302, 3303, 3304, 3305, 3390, 3391, 3801, 3802, 3803, 3804, 3805,
                3890, 3891, 3905, 3906, 3907, 3908, 3909, 3910, 3911, 3912, 3913, 8054, 8056, 10104, 20047, 20057,
                20058, 20059, 20374, 20375, 20426, 30301, 30302, 30303, 30304, 30305]),
    dict(index=303, folder='metin2_map_bayblacksand', pack='zatoka_map', size=(3, 6), base=(1049600, 1510400),
         fog=(1000.0, 30000.0), view_radius=None,
         vnums=[3401, 3402, 3403, 3404, 3405, 3490, 3491, 3501, 3502, 3503, 3504, 3505, 3590, 3591, 3601, 3602, 3603,
                3604, 3605, 3690, 3691, 8052, 8053, 10100, 20047, 20057, 20058, 20059, 20374, 20375, 20379, 30301,
                30302, 30303, 30304, 30305]),
    dict(index=304, folder='metin2_map_mt_thunder', pack='gromiste_map', size=(4, 6), base=(1126400, 1510400),
         fog=(8000.0, 40000.0), view_radius=None,
         vnums=[3101, 3102, 3103, 3104, 3105, 3190, 3191, 3551, 3552, 3553, 3554, 3555, 3595, 3596, 3701, 3702, 3703,
                3704, 3705, 3790, 3791, 3904, 8054, 8055, 10102, 10105, 20047, 20057, 20058, 20059, 30301, 30302,
                30303, 30304, 30305]),
]
RACE_DIRS = ('guild', 'npc', 'npc2', 'npc_pet', 'npc_mount', 'monster', 'monster2')
# Property files whose model path is wrong in every client (ours, GF, Ameria): the model sits one folder deeper. The
# property is replaced by a fixed copy (same CRC) and the model staged - else the object is missing from the map.
FIXES = {
    'property/devils_dragon_island/thing/bone/bone_whale_tail00.prb':      # 2 objects of Nefrytowa Zatoka
        ('d:/ymir work/zone/devils_dragon_island/bone_whale_tail00.gr2',
         'd:/ymir work/zone/devils_dragon_island/bone/bone_whale_tail00.gr2'),
}

# ---------------------------------------------------------------- what our client has (incl. cape301's packs)
OURS = set(gfres.load_ours(PRE_LST))
for l in open(OURS_LST, encoding='utf-8', errors='replace'):
    t = l.rstrip('\n').split(' ', 1)
    if len(t) == 2:
        OURS.add(norm(t[1]))
CAPE = json.load(open(CAPE_MANIFEST, encoding='utf-8'))
CAPE_NAMES = set(e['name'] for p in CAPE['packs'].values() for e in p)
OURS |= CAPE_NAMES
CAPE_REPLACED = set(CAPE.get('replace', []))
CAPE_STAGING = '/opt/metin2/cache/yohara/cape301-staging'


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


def crc_of_body(body):
    return int(body.split('\n')[1].strip().split('#')[0])


OURPROP = {}
for root in (os.path.join(WORK, 'x', 'property'), os.path.join(CAPE_STAGING, 'add', 'property', 'property')):
    for dp, dn, fn in os.walk(root):
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

add = collections.defaultdict(dict)       # group -> key -> src (group: a map's pack, 'property', 'obj', 'mobs')
manifest = {'maps': {}, 'packs': {}, 'unresolved': {}, 'races': {}, 'replace': []}
REPLACE = {}
unres_all = set()

for M in MAPS:
    MAP, MP = M['folder'], M['pack']
    mkeys = sorted(k for k in GF if k.startswith('maps/%s/' % MAP))
    sectors = sorted(k for k in mkeys if k.endswith('/areadata.txt'))
    assert len(sectors) == M['size'][0] * M['size'][1], (MAP, len(sectors))
    st = open(GF['maps/%s/setting.txt' % MAP], 'rb').read().decode('latin1')
    assert re.search(r'MapSize\s+%d\s+%d' % M['size'], st) and \
        re.search(r'BasePosition\s+%d\s+%d' % M['base'], st), (MAP, st)
    used = collections.Counter()
    for s in sectors:
        t = open(GF[s], 'rb').read().decode('latin1').replace('\r', '')
        for body in re.findall(r'Start Object\d+\n(.*?)End Object\n', t, re.S):
            used[crc_of_body(body)] += 1

    prop_src = {}
    drop = {}
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
    gen_sectors = set()
    for s in sectors:
        t = open(GF[s], 'rb').read().decode('latin1').replace('\r', '')
        head = t.split('Start Object', 1)[0]
        objs = re.findall(r'Start Object\d+\n(.*?)End Object\n', t, re.S)
        out = [b for b in objs if crc_of_body(b) not in drop]
        for b in objs:
            if crc_of_body(b) in drop:
                removed[crc_of_body(b)] += 1
        if len(out) != len(objs):
            txt = head + ''.join('Start Object%03d\n%sEnd Object\n' % (i, b) for i, b in enumerate(out))
            txt += '\nObjectCount %d\n' % len(out)
            add[MP][s] = gen(s, crlf(txt).encode('latin1'))
            gen_sectors.add(s)

    # setting.txt: the view radius our other maps have (GF's later client draws 512 for Dawnmistwood)
    if M['view_radius'] is not None:
        st2, n = re.subn(r'(?im)^(ViewRadius[ \t]+)\d+', lambda m: m.group(1) + str(M['view_radius']), st)
        assert n == 1, MAP
        if st2 != st:
            k = 'maps/%s/setting.txt' % MAP
            add[MP][k] = gen(k, crlf(st2.replace('\r', '')).encode('latin1'))
            gen_sectors.add(k)

    # the environment (exe 2.0.25 fog)
    ts = norm(re.search(r'TextureSet\s+(\S+)', st, re.I).group(1))
    env = norm(re.search(r'Environment\s+(\S+)', st, re.I).group(1))
    envkey = 'd:/ymir work/environment/' + env
    et = open(GF[envkey], 'rb').read().decode('latin1').replace('\r', '')
    et, n = re.subn(r'(?im)^([ \t]*)foglevel[ \t]+\d+[ \t]*$',
                    lambda m: '%sEnable        1\n%sNearDistance  %.6f\n%sFarDistance   %.6f' % (
                        m.group(1), m.group(1), M['fog'][0], m.group(1), M['fog'][1]), et)
    assert n == 1 and re.search(r'(?im)^\s*NearDistance', et) and not re.search(r'(?im)^\s*foglevel', et), env
    envsrc = gen(envkey, crlf(et).encode('latin1'))

    # the atlas: atlas.sub names its image beside d:/ymir work/ui/
    sub = 'd:/ymir work/ui/atlas/%s/atlas.sub' % MAP
    img = re.search(r'image\s+"([^"]+)"', open(GF[sub], 'rb').read().decode('latin1')).group(1)
    seeds = set(k for k in mkeys if k not in gen_sectors)
    seeds |= {ts, sub, 'd:/ymir work/ui/' + norm(img)}
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
        if p.startswith(CAPE_STAGING):
            k = norm(os.path.relpath(p, os.path.join(CAPE_STAGING, 'add', 'property')))
        else:
            k = norm(os.path.relpath(p, os.path.join(WORK, 'x', 'property')))
        if k in FIXES:
            bad, good = FIXES[k]
            txt = open(p, 'rb').read().decode('latin1')
            assert ('"%s"' % bad) in txt.lower() and good in RES, (k, bad, good)
            i = txt.lower().index('"%s"' % bad)
            p = REPLACE[k] = REPLACE.get(k) or gen(k, (txt[:i] + '"%s"' % good + txt[i + len(bad) + 2:]).encode('latin1'))
        mdl = model_of(open(p, 'rb').read().decode('latin1'))
        if mdl and mdl not in OURS and mdl not in RES and crc in GFPROP and GFPROP[crc][0] == k \
                and k not in CAPE_REPLACED:
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
        if k in OURS or k.endswith('/server_attr') or any(k in add[g] for g in add):
            continue
        if k.startswith('maps/') and not k.startswith('maps/%s/' % MAP):
            continue
        grp = 'property' if k.startswith('property/') else MP if k.startswith(MAP_PREFIXES) else 'obj'
        add[grp][k] = src
    add[MP]['maps/%s/%s' % (MAP, env)] = envsrc
    add[MP][envkey] = envsrc
    unres_all |= set(u for u in unres_map if not u.endswith('.msenv') and not (
        u.startswith('property/') and not u.endswith(('.prb', '.prd', '.pre', '.prt', '.pra'))))
    manifest['maps'][str(M['index'])] = dict(
        folder=MAP, pack=MP, textureset=ts, environment=env, atlas_image='d:/ymir work/ui/' + norm(img),
        objects=dict(crc_used=len(used), ours=sum(1 for c in used if c in OURPROP), staged=len(prop_src),
                     dropped=len(drop)),
        removed_objects=dict((str(c), dict(objects=n, why=drop[c])) for c, n in sorted(removed.items())),
        generated=sorted(gen_sectors))
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
for v in sorted(set(v for M in MAPS for v in M['vnums'])):
    name = npc.get(v)
    if not name:
        races[v] = dict(status='no npclist row')
        continue
    folder = alias.get(name, name)
    cands = ['d:/ymir work/%s/%s/%s.msm' % (d, folder, name) for d in RACE_DIRS]
    have = next((c for c in cands if c in OURS), None)
    if have:
        races[v] = dict(race=name, msm=have, status='ours' if have not in CAPE_NAMES else 'cape301')
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
PACK_OF_GROUP = {'obj': 'yohara_obj', 'mobs': 'yohara_mobs', 'property': 'property'}
packs = collections.OrderedDict()
for grp in [M['pack'] for M in MAPS] + ['obj', 'mobs', 'property']:
    base = PACK_OF_GROUP.get(grp, grp)
    if grp == 'property':
        packs['property'] = dict(add[grp])
        continue
    # keep a folder together: sorted by name, a new pack when the next file would pass SPLIT
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
        assert k not in OURS or (p == 'property' and k in REPLACE), k
        assert len(k.encode('cp1252')) < 161, k
        assert k not in seen, k
        seen.add(k)
manifest['races'] = dict((str(v), r) for v, r in races.items())
manifest['replace'] = sorted(REPLACE)
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
manifest['unresolved']['map'] = sorted(unres_all)
manifest['unresolved']['races'] = unres_races
manifest['unresolved']['effects'] = sorted(extra_missing)
json.dump(manifest, open(os.path.join(HERE, 'maps302_manifest.json'), 'w', encoding='utf-8'), indent=1, sort_keys=True,
          ensure_ascii=False)
for p in packs:
    print('%-13s %4d files %6.2f MB' % (p, len(packs[p]), sum(os.path.getsize(v) for v in packs[p].values()) / 1e6))
for i, m in manifest['maps'].items():
    print(i, m['folder'], 'objects:', m['objects'], 'removed:', m['removed_objects'])
print('races:', dict((v, r['status']) for v, r in races.items() if r['status'] != 'ours'))
print('unresolved map:', manifest['unresolved']['map'])
print('unresolved races:', unres_races)
print('unresolved effects:', manifest['unresolved']['effects'])
print('gr2 texture decode failures (BitKnit motions, no textures there): %d, models: %s' % (
    len(gfres.GR2_FAIL), sorted(k for k in gfres.GR2_FAIL if not re.search(r'/(wait|walk|run|normal_attack|special_attack|front_|back_|damage|dead|skill|spawn|die)[^/]*\.gr2$', k))))
