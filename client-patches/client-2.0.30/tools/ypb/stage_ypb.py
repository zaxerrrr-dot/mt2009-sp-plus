# -*- coding: utf-8 -*-
# MT2009_PLUS_YOHARA_PB_V1 (client) - the awakened bosses: Twierdza Czerwonego Smoka (PB) (369, metin2_map_boss_awaken_
# flame) and Strażnica Nemere (PB) (370, metin2_map_boss_awaken_snow), and the villages' Statua Iluzji / Statua
# Przebudzenia: the client files staged for build_ypb_packs.py, from the GF 26.1.11 client and, for what GF lacks, the
# Ameria client sources (the method of ../ydung4/stage_ydung4.py).
#
#   python3 stage_ypb.py [<staging dir>] [<work dir>] [<npclist.txt>]       (host; no lzo needed)
#
# defaults: /opt/metin2/cache/yohara/ypb-staging, /opt/metin2/cache/yohara/cape301-work (c58.lst of the client we
# build on), the npclist of client 2.0.61 (it has every race of the two maps and both statues). Writes
# <staging>/add/<pack>/<in-pack name> ("d:/" as "d_/") and tools/ypb/ypb_manifest.json. Every vnum each map shows:
# linux-port/docker/game/yohara_pb/spawned.txt (tools/yohara_pb/gen_ypb.py).
#
#   maps/<map>/setting.txt, mapproperty.txt    GF's: the folder of a COPIED map - "ParentMapName" names our
#                                              metin2_map_n_flame_dungeon_01 / metin2_map_n_snow_dungeon_01, whose
#                                              terrain, environment and minimap the exe loads (GameLib/MapBase.cpp
#                                              GetMapDataDirectory) -> pack ypb_maps
#   d:/ymir work/ui/atlas/<map>/atlas.sub      the fortress: the parent's atlas picture (ours, gf_razador); the
#                                              watchtower none (GF has no picture of it and neither have we)
#   the races our packs lack                   -> pack ypb_mobs (split under the 29 MB limit)
# The client build runs ../cape301 ... ../ydung4 BEFORE build_ypb_packs.py on the same OUT.
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

STAGING = sys.argv[1] if len(sys.argv) > 1 else '/opt/metin2/cache/yohara/ypb-staging'
WORK = sys.argv[2] if len(sys.argv) > 2 else '/opt/metin2/cache/yohara/cape301-work'
NPCLIST = sys.argv[3] if len(sys.argv) > 3 else '/opt/metin2/cache/c61/chk/gamedata/npclist.txt'
OURS_LST = os.path.join(WORK, 'c58.lst')
PRE_LST = '/opt/metin2/cache/tcm/gf28/ourpacks_pre.txt'
AMERIA = '/opt/metin2/ameria/ameria-prj-2025/tools/FoxFSArchiver/source'
GR2_64 = b'\xe5\x9b\x49\x5e'
SPLIT = 26 * 1000 * 1000
norm = gfres.norm

SPAWNED = os.path.join(HERE, '..', '..', '..', '..', 'linux-port', 'docker', 'game', 'yohara_pb', 'spawned.txt')
VNUMS = set()
for _l in open(SPAWNED, encoding='utf-8'):
    _t = _l.split()
    if len(_t) == 2 and _t[0].isdigit():
        VNUMS.add(int(_t[1]))
MAPS = [
    dict(index=369, folder='metin2_map_boss_awaken_flame', parent='metin2_map_n_flame_dungeon_01', size=(3, 3),
         base=(153600, 1971200), atlas_image='atlas_resize/metin2_map_n_flame_dungeon_01_atlas.dds'),
    dict(index=370, folder='metin2_map_boss_awaken_snow', parent='metin2_map_n_snow_dungeon_01', size=(4, 3),
         base=(230400, 1971200), atlas_image=None),
]
RACE_DIRS = ('guild', 'npc', 'npc2', 'npc_pet', 'npc_mount', 'monster', 'monster2')

# ---------------------------------------------------------------- what our client has (incl. the earlier builders)
OURS = set(gfres.load_ours(PRE_LST))
for l in open(OURS_LST, encoding='utf-8', errors='replace'):
    t = l.rstrip('\n').split(' ', 1)
    if len(t) == 2:
        OURS.add(norm(t[1]))
EARLIER = ('cape301', 'maps302', 'shipdefense', 'port368', 'ymaps', 'ymaps2', 'ymaps3', 'ymaps4', 'ysets', 'ydung4')
EARLIER_NAMES = set()
for d in EARLIER:
    man = json.load(open(os.path.join(HERE, '..', d, d + '_manifest.json'), encoding='utf-8'))
    EARLIER_NAMES |= set(e['name'] for p in man['packs'].values() for e in p)
OURS |= EARLIER_NAMES


def index_ameria(root):
    m = {}
    for top in sorted(os.listdir(root)) if os.path.isdir(root) else []:
        tp = os.path.join(root, top)
        if not os.path.isdir(tp):
            continue
        for sub in os.listdir(tp):
            sp = os.path.join(tp, sub)
            if not os.path.isdir(sp) or sub.lower() != 'ymir work':
                continue
            for dp, dn, fn in os.walk(sp):
                for f in fn:
                    ap = os.path.join(dp, f)
                    m.setdefault(norm('d:/ymir work/' + os.path.relpath(ap, sp)), ap)
    return m


AM = index_ameria(AMERIA)
GF = dict(gfres.GF)
RES = dict(AM)
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


add = collections.defaultdict(dict)       # group -> key -> src
manifest = {'maps': {}, 'packs': {}, 'unresolved': {}, 'races': {}, 'replace': []}

# ---------------------------------------------------------------- the two copied maps
for M in MAPS:
    MAP = M['folder']
    st_k, mp_k = 'maps/%s/setting.txt' % MAP, 'maps/%s/mapproperty.txt' % MAP
    st = open(GF[st_k], 'rb').read().decode('latin1')
    mp = open(GF[mp_k], 'rb').read().decode('latin1')
    assert re.search(r'MapSize\s+%d\s+%d' % M['size'], st) and re.search(r'BasePosition\s+%d\s+%d' % M['base'], st)
    assert re.search(r'ParentMapName\s+"%s"' % M['parent'], mp), mp
    assert re.search(r'ViewRadius\s+(128|256)', st), st
    # the parent must be ours: its folder, terrain and environment
    for k in ('maps/%s/setting.txt' % M['parent'], 'maps/%s/000000/attr.atr' % M['parent'],
              'maps/%s/%s.msenv' % (M['parent'], M['parent'])):
        assert k in OURS, k
    for k in (st_k, mp_k):
        assert k not in OURS, k
        add['maps'][k] = GF[k]
    if M['atlas_image']:
        assert 'd:/ymir work/ui/' + M['atlas_image'] in OURS, M['atlas_image']
        sub = 'd:/ymir work/ui/atlas/%s/atlas.sub' % MAP
        gfsub = open(GF['d:/ymir work/ui/atlas_resize/%s/atlas.sub' % MAP], 'rb').read().decode('latin1')
        txt = re.sub(r'image\s+"[^"]+"', 'image "%s"' % M['atlas_image'], gfsub)
        add['maps'][sub] = gen(sub, txt.encode('latin1'))
    manifest['maps'][str(M['index'])] = dict(folder=MAP, parent=M['parent'], atlas_image=M['atlas_image'])

# ---------------------------------------------------------------- the races
npc, alias = {}, {}
for l in open(NPCLIST, encoding='latin1'):
    t = l.split()
    if len(t) >= 3 and t[0] == '0':
        alias[t[1].lower()] = t[2].lower()
    elif len(t) >= 2 and t[0].isdigit():
        npc[int(t[0])] = t[1].lower()
races, unres_races = {}, {}
for v in sorted(VNUMS):
    name = npc.get(v)
    if not name:
        races[v] = dict(status='no npclist row')
        continue
    folder = alias.get(name, name)
    cands = ['d:/ymir work/%s/%s/%s.msm' % (d, folder, name) for d in RACE_DIRS]
    have = next((c for c in cands if c in OURS), None)
    if have:
        races[v] = dict(race=name, msm=have, status='ours' if have not in EARLIER_NAMES else 'earlier builder')
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
PACK_OF_GROUP = {'maps': 'ypb_maps', 'mobs': 'ypb_mobs'}
packs = collections.OrderedDict()
for grp in ('maps', 'mobs'):
    base = PACK_OF_GROUP[grp]
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
manifest['new_packs'] = [p for p in packs if packs[p]]
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
manifest['unresolved']['races'] = unres_races
manifest['unresolved']['effects'] = sorted(extra_missing)
json.dump(manifest, open(os.path.join(HERE, 'ypb_manifest.json'), 'w', encoding='utf-8'), indent=1, sort_keys=True,
          ensure_ascii=False)
for p in packs:
    print('%-13s %4d files %6.2f MB' % (p, len(packs[p]), sum(os.path.getsize(v) for v in packs[p].values()) / 1e6))
print('races:', dict((v, r['status']) for v, r in races.items() if r['status'] != 'ours'))
print('unresolved races:', unres_races)
print('unresolved effects:', manifest['unresolved']['effects'])
