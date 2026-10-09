# -*- coding: utf-8 -*-
# MT2009_PLUS_ZODIAC_V1 - Swiatynia Zodiaku (map 358, metin2_12zi_stage): the client files staged for
# build_zodiak_packs.py, from the package nowy-system 0.35.0 ("Autor: Digi Rasta", klient_zodiak/ - its pack
# "nowy_system_zodiak", WLsj24 ZodiacTemple v2.1-3.0) and, for what it leaves out, the GF 26.1.11 client.
#
#   python3 stage_zodiak.py [<klient_zodiak dir>] [<staging dir>] [<work dir>]     (host; no lzo needed)
#
# defaults: /opt/metin2/cache/zodiak/gra/Serwer/nowy-system/klient_zodiak, /opt/metin2/cache/zodiak-staging,
# /opt/metin2/cache/zodiak-work (c58.lst + x/property of the client we build on, written by
# ../atlantis/dump_base.py <BASE pack dir> /opt/metin2/cache/zodiak-work; etc.lst - the old pack "etc", see below).
# Writes <staging>/add/<pack>/<in-pack name> ("d:/" as "d_/") and tools/zodiak/zodiak_manifest.json.
#
#   maps/metin2_12zi_stage/...    -> pack maps      (the 36 sectors, setting.txt, mapproperty.txt; as 158/351/360-366)
#   property/...                  -> pack property  (the exe loads map objects only from pack/property)
#   the races, their sounds, the weapon and armour models (monster2/monster/npc/pc*/item, sound/)
#                                 -> new packs zodiak_mobs and zodiak_mobs2 (split by race, each under 29 MB)
#   the rest (zone objects, effects, environments, terrain, textureset, UI, icons, the atlas)
#                                 -> new pack zodiak_maps
# The package's root scripts (ymir work/nowy_system/ui12zi.py, uiscript/*) are NOT staged: they are ours in
# client-patches/client-2.0.30/root (ui12zi.py, uiscript/bead.py, 12floorinfo.py, 12zirewardwindow.py).
#
# The package left out what ITS client had in other packs (351 files) - our client does not have all of them:
# the Zodiac weapons' models (d:/ymir work/item/weapon/0xxxx.gr2), the armour shape 25 (warrior/assassin/sura/
# shaman _6_1, both sexes) and 18 item icons come from GF here, with everything they name (gfres closure).
# A name our client already has (dump listing + the base client's pre-import listing) is left out - ours wins.
# A map object whose property CRC neither the package nor our property pack has is looked up in GF's property
# files (and staged with its model); what is still missing is reported (the package's ~10 "Load ERROR").
# 64-bit GR2 (header e59b495e, the exe cannot read it): none may be staged.
import collections
import hashlib
import json
import os
import re
import shutil
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, '..', 'az58'))
sys.path.insert(0, '/opt/metin2/cache/arezzo-work/client/az58')
import gfres  # noqa: E402  (indexes the GF client at import)

gfres.GR2DIR = '/opt/metin2/cache/arezzo-work/client/az58/gr2'
gfres.GR2DEC = os.path.join(gfres.GR2DIR, 'gr2dec')

PKG = sys.argv[1] if len(sys.argv) > 1 else '/opt/metin2/cache/zodiak/gra/Serwer/nowy-system/klient_zodiak'
STAGING = sys.argv[2] if len(sys.argv) > 2 else '/opt/metin2/cache/zodiak-staging'
WORK = sys.argv[3] if len(sys.argv) > 3 else '/opt/metin2/cache/zodiak-work'
OURS_LST = os.path.join(WORK, 'c58.lst')        # "<pack> <name>" of the client we build on (dump_base.py)
PRE_LST = '/opt/metin2/cache/tcm/gf28/ourpacks_pre.txt'
DATA = json.load(open(os.path.join(HERE, 'zodiak_client.json'), encoding='utf-8'))
MAP = 'metin2_12zi_stage'
GR2_64 = b'\xe5\x9b\x49\x5e'
norm = gfres.norm
SKIP = ('d:/ymir work/nowy_system/',)
MOB_DIRS = ('d:/ymir work/monster', 'd:/ymir work/npc', 'd:/ymir work/pc', 'd:/ymir work/item/', 'sound/')
ARMOUR_SHAPE = 25          # value3 of 19290-19299, 19490..., 19690..., 19890..., 21200...


def index_tree(root):
    m = {}
    for top in os.listdir(root):
        tp = os.path.join(root, top)
        if not os.path.isdir(tp):
            continue
        pref = 'd:/ymir work/' if top.lower() == 'ymir work' else top.lower() + '/'
        for dp, dn, fn in os.walk(tp):
            for f in fn:
                ap = os.path.join(dp, f)
                m[norm(pref + os.path.relpath(ap, tp))] = ap
    return m


PK = dict((k, v) for k, v in index_tree(PKG).items() if not k.startswith(SKIP))
OURS = set(gfres.load_ours(PRE_LST))
# c58.lst (dump_base.py) and any other "<pack> <name>" listing in WORK - etc.lst: the old pack "etc" of the
# client (only the exebuild smoke client on vps1 has it - the players' clients do not, so the package's own
# files listed there, the 74 ui/game/12zi, ui/skill/common/affect ... files, are staged anyway). The other old packs (item, monster*, npc*, sound_*, zone_*, season1, terrain ...) have no listing
# on vps1: a name staged here that one of them also has is shadowed by it or shadows it with the same file.
for lst in [OURS_LST] + sorted(os.path.join(WORK, f) for f in os.listdir(WORK) if f.endswith('.lst') and f != 'c58.lst'):
    for l in open(lst, encoding='utf-8', errors='replace'):
        t = l.rstrip('\n').split(' ', 1)
        if len(t) == 2 and (lst == OURS_LST or norm(t[1]) not in PK):
            OURS.add(norm(t[1]))
GF = dict(gfres.GF)
RES = dict((k, p) for k, p in GF.items() if not k.startswith(('maps/', 'property/')))
RES.update(PK)                      # the package wins over GF
gfres.GF = RES

shutil.rmtree(STAGING, ignore_errors=True)
GEN = os.path.join(STAGING, 'gen')
os.makedirs(GEN)


def gen(key, data):
    p = os.path.join(GEN, key.replace('d:/', 'd_/', 1))
    os.makedirs(os.path.dirname(p), exist_ok=True)
    open(p, 'wb').write(data)
    return p


def prop_crc(path):
    b = open(path, 'rb').read().replace(b'\r', b'').split(b'\n')
    if b and b[0].strip() == b'YPRT' and len(b) > 1:
        try:
            return int(b[1].strip())
        except ValueError:
            return None
    return None


def prop_index(files):
    idx = {}
    for k, p in files.items():
        if k.startswith('property/'):
            c = prop_crc(p)
            if c is not None:
                idx[c] = (k, p)
    return idx


PROPS = prop_index(PK)
OURPROP = {}
for dp, dn, fn in os.walk(os.path.join(WORK, 'x', 'property')):
    for f in fn:
        c = prop_crc(os.path.join(dp, f))
        if c is not None:
            OURPROP[c] = os.path.join(dp, f)
GFPROP = prop_index(dict((k, p) for k, p in GF.items() if k.startswith('property/')))
clash = sorted(c for c in set(PROPS) & set(OURPROP)
               if open(PROPS[c][1], 'rb').read().replace(b'\r', b'') != open(OURPROP[c], 'rb').read().replace(b'\r', b''))
if clash:
    raise SystemExit('property CRC clash (other content) with our property pack: %s' % clash)

# ---------------------------------------------------------------- the map's objects and their properties
sectors = sorted(k for k in PK if k.startswith('maps/%s/' % MAP) and k.endswith('/areadata.txt'))
assert len(sectors) == 36, len(sectors)
used = collections.Counter()
for s in sectors:
    t = open(PK[s], 'rb').read().decode('latin1').replace('\r', '')
    for body in re.findall(r'Start Object\d+\n(.*?)End Object\n', t, re.S):
        used[int(body.split('\n')[1].strip().split('#')[0])] += 1
from_gf_prop = {}
missing_prop = {}
for crc, n in sorted(used.items()):
    if crc in PROPS or crc in OURPROP:
        continue
    if crc in GFPROP:
        from_gf_prop[crc] = GFPROP[crc]
    else:
        missing_prop[crc] = n

# ---------------------------------------------------------------- the closure
# only the properties the 36 sectors use (37 of the package's property/12temple files name models nowhere to
# be found and no object uses them)
PROP_USED = set(k for c, (k, p) in PROPS.items() if c in used)
seeds = set(k for k in PK if not k.startswith('property/') or k in PROP_USED)
for crc, (k, p) in from_gf_prop.items():
    RES[k] = p
    seeds.add(k)
for crc, (k, p) in [(c, v) for c, v in PROPS.items() if c in used] + list(from_gf_prop.items()):
    mdl = gfres.prop_attr_model(open(p, 'rb').read().decode('latin1'))
    if mdl and gfres.mdatr_of(mdl) in RES:
        seeds.add(gfres.mdatr_of(mdl))
# the items' icons and models (item_list rows of the new vnums)
new_items = set(str(w['vnum']) for w in DATA['przedmioty'] if w['vnum'] not in DATA['istnieja'])
for v, row in DATA['item_list'].items():
    if v in new_items:
        for f in row.split('\t')[2:]:
            if f.strip():
                seeds.add(norm(f))
# the armour shape 25 of every msm of our client (the msm lines: PathName + Model/SourceSkin, and the LODs)
SHAPE_FILES = {'warrior_m': 'd:/ymir work/pc/warrior/', 'warrior_w': 'd:/ymir work/pc2/warrior/',
               'assassin_m': 'd:/ymir work/pc2/assassin/', 'assassin_w': 'd:/ymir work/pc/assassin/',
               'sura_m': 'd:/ymir work/pc/sura/', 'sura_w': 'd:/ymir work/pc2/sura/',
               'shaman_m': 'd:/ymir work/pc2/shaman/', 'shaman_w': 'd:/ymir work/pc/shaman/'}
for msm, d in SHAPE_FILES.items():
    race = msm.split('_')[0]
    for suf in ('.gr2', '.dds', '_lod_01.gr2', '_lod_02.gr2', '_lod_03.gr2'):
        k = '%s%s_6_1%s' % (d, race, suf)
        if k in RES:
            seeds.add(k)
st = open(PK['maps/%s/setting.txt' % MAP], 'rb').read().decode('latin1')
ENVS = [norm(e) for e in re.findall(r'(?im)^\s*Environment\d*\s+(\S+)', st)]
for env in ENVS:
    seeds.add('d:/ymir work/environment/' + env)
files, unresolved, ours_hit = gfres.closure(sorted(seeds), OURS)

# the textures an effect mesh (.mde) or script (.mse) names with a full path (the closure does not read them)
extra_missing = set()
for _ in range(2):
    for k, src in list(files.items()):
        if not k.endswith(('.mde', '.mse')):
            continue
        for m in re.findall(rb'[A-Za-z]:[\\/][^\x00"\r\n]+?\.(?:dds|tga|png|jpg|mde)', open(src, 'rb').read(), re.I):
            t = 'd:' + m.decode('latin1').replace('\\', '/').lower()[2:]
            if t in OURS or t in files:
                continue
            if t in RES:
                files[t] = RES[t]
            else:
                extra_missing.add(t)

add = collections.defaultdict(dict)
for k, src in files.items():
    if k in OURS and not k.startswith('maps/%s/' % MAP):
        continue
    if k.endswith('/server_attr'):
        continue
    if k.startswith('maps/'):
        pack = 'maps'
    elif k.startswith('property/'):
        pack = 'property'
    elif k.startswith(MOB_DIRS):
        pack = 'zodiak_mobs'
    else:
        pack = 'zodiak_maps'
    add[pack][k] = src

# zodiak_mobs is over the 29 MB zip limit in one pack (35 MB packed): the races go into zodiak_mobs and
# zodiak_mobs2 by name, a race's model, motions, effects and sounds together (the key after monster2/, monster/,
# npc/), the first ~18 MB raw into zodiak_mobs; weapons, armours and common sounds stay in zodiak_mobs.
def race_of(k):
    m = re.match(r'(?:d:/ymir work|sound)/(?:monster2?|npc2?)/([^/]+)/', k)
    return m.group(1) if m else None


races = collections.defaultdict(int)
for k, src in add['zodiak_mobs'].items():
    if race_of(k):
        races[race_of(k)] += os.path.getsize(src)
first, total = set(), sum(os.path.getsize(v) for k, v in add['zodiak_mobs'].items() if not race_of(k))
for r in sorted(races):
    if total + races[r] > 18.0e6:
        break
    first.add(r)
    total += races[r]
for k in [k for k in add['zodiak_mobs'] if race_of(k) and race_of(k) not in first]:
    add['zodiak_mobs2'][k] = add['zodiak_mobs'].pop(k)

# a copy of every msenv in the map's folder, as for 158/351/360-366 (setting.txt names them bare)
for env in ENVS:
    add['maps']['maps/%s/%s' % (MAP, env)] = RES['d:/ymir work/environment/' + env]
manifest_unres_skip = set('maps/%s/%s' % (MAP, env) for env in ENVS)

# MT2009_PLUS_ZODIAC_WEAPON_MODELS_V1: the Zodiac blade/sword (00300), dagger (01180) and glaive (03220) models
# under new names - the players' old item pack has weapon/00300.gr2, 01180.gr2, 03220.gr2 of the dead old items
# 300/1180/3220 and shadows GF's (patch_zodiak_client.py MODEL_RENAME points item_list at these names).
for _old, _new in (('00300', 'zodiak_00300'), ('01180', 'zodiak_01180'), ('03220', 'zodiak_03220')):
    _src = GF['d:/ymir work/item/weapon/%s.gr2' % _old]
    assert open(_src, 'rb').read(4) != GR2_64, _src
    add['zodiak_mobs']['d:/ymir work/item/weapon/%s.gr2' % _new] = _src
    add['zodiak_mobs'].pop('d:/ymir work/item/weapon/%s.gr2' % _old, None)
for _t in ('d:/ymir work/item/weapon/weapon_12zi_6th_01.dds',):
    if not any(_t in add[_p] for _p in add) and _t not in OURS:
        add['zodiak_mobs'][_t] = RES[_t]

# the atlas: GF's 352x352 picture under our names (d:/ymir work/ui/<map>_atlas.dds + ui/atlas/<map>/atlas.sub)
ga = GF.get('d:/ymir work/ui/atlas_resize/%s_atlas.dds' % MAP)
if ga and 'd:/ymir work/ui/%s_atlas.dds' % MAP not in OURS:
    add['zodiak_maps']['d:/ymir work/ui/%s_atlas.dds' % MAP] = ga
    k2 = 'd:/ymir work/ui/atlas/%s/atlas.sub' % MAP
    add['zodiak_maps'][k2] = gen(k2, ('title subImage\r\nversion 1.0\r\nimage "%s_atlas.dds"\r\nleft 0\r\ntop 0\r\n'
                                      'right 352\r\nbottom 352\r\n' % MAP).encode())

# ---------------------------------------------------------------- checks and the staging
bad64 = sorted(k for p in add for k, s in add[p].items() if k.endswith('.gr2') and open(s, 'rb').read(4) == GR2_64)
if bad64:
    raise SystemExit('64-bit GR2 staged: %s' % bad64)
for p in add:
    for k in add[p]:
        assert k == k.lower() and '\\' not in k, k
manifest = {'packs': {}, 'unresolved': {}, 'properties_from_gf': {}, 'properties_missing': {}}
for p in sorted(add):
    ents = []
    for k in sorted(add[p]):
        src = add[p][k]
        dst = os.path.join(STAGING, 'add', p, k.replace('d:/', 'd_/', 1))
        os.makedirs(os.path.dirname(dst), exist_ok=True)
        shutil.copyfile(src, dst)
        b = open(src, 'rb').read()
        if src.startswith(PKG):
            rel = 'PKG:' + os.path.relpath(src, PKG)
        elif src.startswith(STAGING):
            rel = 'GEN:' + os.path.relpath(src, GEN)
        else:
            rel = 'GF:' + os.path.relpath(src, '/opt/metin2/cache/gf/Gameforge_26.1.11/_client')
        ents.append(dict(name=k, source=rel, size=len(b), sha1=hashlib.sha1(b).hexdigest()))
    manifest['packs'][p] = ents
manifest['properties_from_gf'] = dict((str(c), k) for c, (k, p) in sorted(from_gf_prop.items()))
manifest['properties_missing'] = dict((str(c), n) for c, n in sorted(missing_prop.items()))
ignore = ('.psd',)
manifest['unresolved']['refs'] = sorted(u for u in unresolved if not u.endswith(ignore) and u not in manifest_unres_skip)
manifest['unresolved']['effects'] = sorted(extra_missing)
manifest['gr2_decode_failures'] = gfres.GR2_FAIL
json.dump(manifest, open(os.path.join(HERE, 'zodiak_manifest.json'), 'w', encoding='utf-8'), indent=1, sort_keys=True,
          ensure_ascii=False)
for p in sorted(add):
    src = collections.Counter(e['source'].split(':', 1)[0] for e in manifest['packs'][p])
    print('%-12s %4d files %6.2f MB  %s' % (p, len(add[p]), sum(os.path.getsize(v) for v in add[p].values()) / 1e6,
                                           dict(src)))
print('properties: %d CRCs used, %d from GF, %d missing everywhere (%d objects)' % (
    len(used), len(from_gf_prop), len(missing_prop), sum(missing_prop.values())))
print('unresolved refs (%d):' % len(manifest['unresolved']['refs']), manifest['unresolved']['refs'][:60])
print('unresolved effect textures:', sorted(extra_missing))
print('gr2 texture decode failures:', len(gfres.GR2_FAIL))
