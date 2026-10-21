# -*- coding: utf-8 -*-
# MT2009_PLUS_YOHARA_CRACK2_V1 (client) - the three other Time Rift dungeons: Grota Wygnańców 2 (SZC) (405,
# metin2_map_boss_crack_skipia), Twierdza Czerwonego Smoka (SZC) (406, metin2_map_boss_crack_flame), Strażnica Nemere
# (SZC) (407, metin2_map_boss_crack_snow): the races our packs lack, staged for build_ycrack2_packs.py from the GF
# 26.1.11 client and, for what GF lacks, the Ameria client sources (the method of ../ycrack/stage_ycrack.py).
#
#   python3 stage_ycrack2.py [<staging dir>] [<work dir>] [<npclist.txt>]       (host; no lzo needed)
#
# defaults: /opt/metin2/cache/yohara/ycrack2-staging, /opt/metin2/cache/yohara/cape301-work (c58.lst of the client we
# build on), the npclist of client 2.0.61 (it has every race of the three maps). Writes <staging>/add/<pack>/<in-pack
# name> ("d:/" as "d_/") and tools/ycrack2/ycrack2_manifest.json. Every vnum the maps show:
# linux-port/docker/game/yohara_crack2/spawned.txt (tools/yohara_crack2/gen_ycrack2.py).
#
# The map folders are NOT staged: GF's crack folders are COPIED maps (ParentMapName = metin2_map_skipia_dungeon_02 /
# metin2_map_n_flame_dungeon_01 / metin2_map_n_snow_dungeon_01), which our exe cannot load (it reads the parent
# without "maps/" - ../ycopymaps, MT2009_PLUS_COPIED_MAPS_V1). build_ycrack2_packs.py writes each folder whole from
# the PB twin's terrain already in the packs (manifest "maps").
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

STAGING = sys.argv[1] if len(sys.argv) > 1 else '/opt/metin2/cache/yohara/ycrack2-staging'
WORK = sys.argv[2] if len(sys.argv) > 2 else '/opt/metin2/cache/yohara/cape301-work'
NPCLIST = sys.argv[3] if len(sys.argv) > 3 else '/opt/metin2/cache/c61/chk/gamedata/npclist.txt'
OURS_LST = os.path.join(WORK, 'c58.lst')
PRE_LST = '/opt/metin2/cache/tcm/gf28/ourpacks_pre.txt'
AMERIA = '/opt/metin2/ameria/ameria-prj-2025/tools/FoxFSArchiver/source'
GR2_64 = b'\xe5\x9b\x49\x5e'
SPLIT = 26 * 1000 * 1000
norm = gfres.norm

SPAWNED = os.path.join(HERE, '..', '..', '..', '..', 'linux-port', 'docker', 'game', 'yohara_crack2', 'spawned.txt')
VNUMS = set()
for _l in open(SPAWNED, encoding='utf-8'):
    _t = _l.split()
    if len(_t) == 2 and _t[0].isdigit():
        VNUMS.add(int(_t[1]))
# index -> the map, its terrain's folder in our packs (the PB twin's parent / the PB grotto's full folder), the PB
# twin (its atlas.sub, if it has one, names the same picture), the size and the official base (= the server)
MAPS = [
    dict(index=405, folder='metin2_map_boss_crack_skipia', terrain='metin2_map_boss_awaken_skipia',
         pb='metin2_map_boss_awaken_skipia', size=(6, 6), base=(0, 1817600)),
    dict(index=406, folder='metin2_map_boss_crack_flame', terrain='metin2_map_n_flame_dungeon_01',
         pb='metin2_map_boss_awaken_flame', size=(3, 3), base=(153600, 1817600)),
    dict(index=407, folder='metin2_map_boss_crack_snow', terrain='metin2_map_n_snow_dungeon_01',
         pb='metin2_map_boss_awaken_snow', size=(4, 3), base=(230400, 1817600)),
]
RACE_DIRS = ('guild', 'npc', 'npc2', 'npc_pet', 'npc_mount', 'monster', 'monster2')

OURS = set(gfres.load_ours(PRE_LST))
for l in open(OURS_LST, encoding='utf-8', errors='replace'):
    t = l.rstrip('\n').split(' ', 1)
    if len(t) == 2:
        OURS.add(norm(t[1]))
EARLIER = ('cape301', 'maps302', 'shipdefense', 'port368', 'ymaps', 'ymaps2', 'ymaps3', 'ymaps4', 'ysets', 'ydung4',
           'ypb', 'yiluzja', 'ycrack')
EARLIER_NAMES = set()
for d in EARLIER:
    man = json.load(open(os.path.join(HERE, '..', d, d + '_manifest.json'), encoding='utf-8'))
    EARLIER_NAMES |= set(e['name'] for p in man['packs'].values() for e in p)
OURS |= EARLIER_NAMES
# the terrain folders must be ours already (the PB grotto: ../yiluzja; the fortress / watchtower: the base client)
for M in MAPS:
    for k in ('maps/%s/setting.txt' % M['terrain'], 'maps/%s/000000/attr.atr' % M['terrain']):
        assert k in OURS, k
    assert 'maps/%s/setting.txt' % M['folder'] not in OURS, M['folder']


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
os.makedirs(STAGING)
add = collections.defaultdict(dict)       # group -> key -> src
manifest = {'maps': {}, 'packs': {}, 'unresolved': {}, 'races': {}}
for M in MAPS:
    manifest['maps'][str(M['index'])] = dict(folder=M['folder'], terrain=M['terrain'], pb=M['pb'],
                                             size=list(M['size']), base=list(M['base']))

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
packs = collections.OrderedDict()
n, cur, size = 1, {}, 0
for k in sorted(add['mobs']):
    s = os.path.getsize(add['mobs'][k])
    if cur and size + s > SPLIT:
        packs['ycrack2_mobs' if n == 1 else 'ycrack2_mobs%d' % n] = cur
        n, cur, size = n + 1, {}, 0
    cur[k] = add['mobs'][k]
    size += s
if cur:
    packs['ycrack2_mobs' if n == 1 else 'ycrack2_mobs%d' % n] = cur
for p in packs:
    for k in packs[p]:
        assert k == k.lower() and '\\' not in k and k not in OURS and len(k.encode('cp1252')) < 161, k
manifest['races'] = dict((str(v), r) for v, r in races.items())
# ycrack2_maps: written by build_ycrack2_packs.py from the packs themselves (no staged file)
manifest['new_packs'] = ['ycrack2_maps'] + [p for p in packs if packs[p]]
for p in packs:
    ents = []
    for k in sorted(packs[p]):
        src = packs[p][k]
        dst = os.path.join(STAGING, 'add', p, k.replace('d:/', 'd_/', 1))
        os.makedirs(os.path.dirname(dst), exist_ok=True)
        shutil.copyfile(src, dst)
        b = open(src, 'rb').read()
        where = 'gf' if src.startswith(gfres.G) else 'ameria' if src.startswith(AMERIA) else src
        ents.append(dict(name=k, source=where, size=len(b), sha1=hashlib.sha1(b).hexdigest()))
    manifest['packs'][p] = ents
manifest['unresolved']['races'] = unres_races
manifest['unresolved']['effects'] = sorted(extra_missing)
json.dump(manifest, open(os.path.join(HERE, 'ycrack2_manifest.json'), 'w', encoding='utf-8'), indent=1, sort_keys=True,
          ensure_ascii=False)
for p in packs:
    print('%-13s %4d files %6.2f MB' % (p, len(packs[p]), sum(os.path.getsize(v) for v in packs[p].values()) / 1e6))
print('races:', dict((v, r['status']) for v, r in races.items() if r['status'] != 'ours'))
print('unresolved races:', unres_races)
print('unresolved effects:', manifest['unresolved']['effects'])
