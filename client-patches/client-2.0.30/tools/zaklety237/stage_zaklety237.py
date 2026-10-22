# -*- coding: utf-8 -*-
# MT2009_PLUS_237_ZAKLETY_LAS_V1 (client, 2.x) - Zaklety Las (353, metin2_map_dawnmist_dungeon_01, 3x4, the official
# base 768000 1408000), the open forest past the Temple of Ochao, for the 2.x client (client67.sh line: base c55 + the
# build's OUT). The Yohara branch builds the forest as a COPIED map (../yzaklety: ParentMapName = the PB forest of
# ../yiluzja); the 2.x client has neither yiluzja nor ycrack, so here the forest is a FULL map folder of its own, made
# the way ../yiluzja made its PB forest (the method of ../ydung4 on the Yohara branch):
#   maps/metin2_map_dawnmist_dungeon_01/...   GF's own folder (setting.txt with the official base, mapproperty.txt
#                                             without ParentMapName, every sector; objects whose property/model no
#                                             client of ours has are taken out of areadata.txt and listed)
#   the textureset, terrain textures, msenv (exe 2.0.25 fog: Enable/Near/FarDistance instead of "foglevel"), atlas
#                                             -> new pack zaklety_map
#   property/...                              -> pack property (new names only)
#   the map objects' models                   -> new pack zaklety_obj (split under the 29 MB limit)
#   the races the forest shows our client lacks (trent_*, thunder_boss, metinstone_16, ...)
#                                             -> new pack zaklety_mobs (split)
# Sources: the GF 26.1.11 client and, for what GF lacks, the Ameria client sources.
#
#   python3 stage_zaklety237.py [<staging dir>] [<work dir>] [<npclist.txt>]       (host; no lzo needed)
#
# defaults: /opt/metin2/cache/las237-staging/stage, /opt/metin2/cache/las237-staging/work (c58.lst = the listing of the
# 2.x client we build on and x/property its property pack: ../atlantis/dump_base.py <client pack dir> <work dir>, made
# from /opt/metin2/cache/c67/pack for 2.0.67), the npclist of client 2.0.67 (+ the guards zaklety237_client.json adds).
# The earlier builders of this build (../cape301, ../maps302) count as ours: their manifests and staged properties.
# Writes <staging>/add/<pack>/<in-pack name> ("d:/" as "d_/") and zaklety237_manifest.json.
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

STAGING = sys.argv[1] if len(sys.argv) > 1 else '/opt/metin2/cache/las237-staging/stage'
WORK = sys.argv[2] if len(sys.argv) > 2 else '/opt/metin2/cache/las237-staging/work'
NPCLIST = sys.argv[3] if len(sys.argv) > 3 else '/opt/metin2/cache/c67/chk/gamedata/npclist.txt'
OURS_LST = os.path.join(WORK, 'c58.lst')
PRE_LST = '/opt/metin2/cache/tcm/gf28/ourpacks_pre.txt'
AMERIA = '/opt/metin2/ameria/ameria-prj-2025/tools/FoxFSArchiver/source'
GR2_64 = b'\xe5\x9b\x49\x5e'
SPLIT = 26 * 1000 * 1000
MAP_PREFIXES = ('maps/', 'textureset/', 'd:/ymir work/terrainmaps/', 'd:/ymir work/environment/', 'd:/ymir work/ui/')
norm = gfres.norm

# every vnum the forest shows (= the server's spawn files with their groups unfolded, the Metins' groups, the quests'
# bosses, the summons - the Yohara branch's linux-port/docker/game/yohara_zaklety/spawned.txt)
VNUMS = [6192, 6401, 6402, 6403, 6404, 6406, 6407, 6408, 6409, 6410, 6411, 6412, 6413, 6414, 8059, 8061, 9012,
         20160, 20161, 20162, 20412]
MAPS = [
    dict(index=353, folder='metin2_map_dawnmist_dungeon_01', src='metin2_map_dawnmist_dungeon_01', own=None,
         pack='zaklety_map', size=(3, 4), base=(768000, 1408000), fog=(5000.0, 20000.0), fog_on=1, vnums=VNUMS),
]
RACE_DIRS = ('guild', 'npc', 'npc2', 'npc_pet', 'npc_mount', 'monster', 'monster2')

# ---------------------------------------------------------------- what our client has (incl. the earlier builders)
OURS = set(gfres.load_ours(PRE_LST))
for l in open(OURS_LST, encoding='utf-8', errors='replace'):
    t = l.rstrip('\n').split(' ', 1)
    if len(t) == 2:
        OURS.add(norm(t[1]))
EARLIER = ('cape301', 'maps302')
EARLIER_STAGING = ['/opt/metin2/cache/yohara/%s/add/property/property' % d for d in ('cape301-staging', 'maps302-staging')]
EARLIER_NAMES = set()
EARLIER_REPLACED = set()
for d in EARLIER:
    man = json.load(open(os.path.join(HERE, '..', d, d + '_manifest.json'), encoding='utf-8'))
    EARLIER_NAMES |= set(e['name'] for p in man['packs'].values() for e in p)
    EARLIER_REPLACED |= set(man.get('replace', []))
OURS |= EARLIER_NAMES


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
    MAP, SRC, MP = M['folder'], M['src'], M['pack']

    def dst(k):
        return k.replace('maps/%s/' % SRC, 'maps/%s/' % MAP, 1)

    mkeys = sorted(k for k in GF if k.startswith('maps/%s/' % SRC))
    sectors = sorted(k for k in mkeys if k.endswith('/areadata.txt'))
    assert len(sectors) == M['size'][0] * M['size'][1], (SRC, len(sectors))
    # setting.txt: the awakened folder's (the official base; the parent's terrain, textureset, environment)
    st = open(GF['maps/%s/setting.txt' % MAP], 'rb').read().decode('latin1')
    assert re.search(r'MapSize\s+%d\s+%d' % M['size'], st) and \
        re.search(r'BasePosition\s+%d\s+%d' % M['base'], st), (MAP, st)
    srcst = open(GF['maps/%s/setting.txt' % SRC], 'rb').read().decode('latin1')
    for key in ('TextureSet', 'Environment', 'MapSize'):
        assert re.search(r'(?im)^%s\s+(.+)$' % key, st).group(1).strip().lower() == \
            re.search(r'(?im)^%s\s+(.+)$' % key, srcst).group(1).strip().lower(), (MAP, key)
    assert re.search(r'ViewRadius\s+(128|256)', st), MAP
    mprop = open(GF['maps/%s/mapproperty.txt' % SRC], 'rb').read().decode('latin1')
    assert 'parentmapname' not in mprop.lower(), SRC
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
        if mdl and mdl.endswith('.gr2') and mdl not in RES and mdl not in OURS:
            drop[crc] = 'model %s in no client we have' % mdl
            continue
        if kp[0] in OURS:
            drop[crc] = 'property name %s is ours with another CRC' % kp[0]
            continue
        prop_src[crc] = kp

    removed = collections.Counter()
    gen_keys = set()
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
            add[MP][dst(s)] = gen(dst(s), crlf(txt).encode('latin1'))
            gen_keys.add(s)
    # the folder's own files: setting.txt (the awakened one), mapproperty.txt (the parent's, no ParentMapName), the
    # grotto's own 000000/attr.atr (Beran's temple open)
    add[MP]['maps/%s/setting.txt' % MAP] = GF['maps/%s/setting.txt' % MAP]
    add[MP]['maps/%s/mapproperty.txt' % MAP] = GF['maps/%s/mapproperty.txt' % SRC]
    gen_keys |= {'maps/%s/setting.txt' % SRC, 'maps/%s/mapproperty.txt' % SRC}
    own_sectors = []
    if M['own']:
        for k in sorted(GF):
            if k.startswith('maps/%s/' % M['own']) and k.endswith('/attr.atr'):
                sk = k.replace('maps/%s/' % M['own'], 'maps/%s/' % SRC, 1)
                assert sk in GF, sk
                add[MP][dst(sk)] = GF[k]
                gen_keys.add(sk)
                own_sectors.append(k.split('/')[2])
        assert own_sectors, M['own']

    # the environment (exe 2.0.25 fog)
    ts = norm(re.search(r'TextureSet\s+(\S+)', st, re.I).group(1))
    env = norm(re.search(r'Environment\s+(\S+)', st, re.I).group(1))
    envkey = 'd:/ymir work/environment/' + env
    et = open(GF[envkey], 'rb').read().decode('latin1').replace('\r', '')
    et, n = re.subn(r'(?im)^([ \t]*)foglevel[ \t]+\d+[ \t]*$',
                    lambda m: '%sEnable        %d\n%sNearDistance  %.6f\n%sFarDistance   %.6f' % (
                        m.group(1), M['fog_on'], m.group(1), M['fog'][0], m.group(1), M['fog'][1]), et)
    assert n <= 1 and re.search(r'(?im)^\s*NearDistance', et) and not re.search(r'(?im)^\s*foglevel', et), env
    envsrc = gen(envkey, crlf(et).encode('latin1'))
    # GF keeps the folder's own msenv copy too (skipia_dungeon.msenv in the parent's folder): ours replaces it
    for k in list(mkeys):
        if k.endswith('.msenv'):
            gen_keys.add(k)

    # the atlas (exe 2.0.25 looks in ui/atlas/<map>/atlas.sub): GF's awakened folder's, naming the parent's picture
    sub = 'd:/ymir work/ui/atlas/%s/atlas.sub' % MAP
    alt = 'd:/ymir work/ui/atlas_resize/%s/atlas.sub' % MAP
    img = None
    if sub not in GF and alt in GF:
        GF[sub] = RES[sub] = GF[alt]
    if sub in GF:
        img = re.search(r'image\s+"([^"]+)"', open(GF[sub], 'rb').read().decode('latin1')).group(1)
        if 'd:/ymir work/ui/' + norm(img) not in RES and 'd:/ymir work/ui/' + norm(img) not in OURS:
            img = None
    # the terrain files under the awakened name
    for k in mkeys:
        if k in gen_keys:
            continue
        add[MP][dst(k)] = GF[k]
    seeds = {ts}
    if img:
        seeds |= {'d:/ymir work/ui/' + norm(img)}
        add[MP][sub] = GF[sub] if sub in GF else None
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
        er = next((r for r in EARLIER_STAGING if p.startswith(r + '/')), None)
        k = norm('property/' + os.path.relpath(p, er)) if er else \
            norm(os.path.relpath(p, os.path.join(WORK, 'x', 'property')))
        mdl = model_of(open(p, 'rb').read().decode('latin1'))
        if mdl and mdl not in OURS and mdl not in RES and crc in GFPROP and GFPROP[crc][0] == k \
                and k not in EARLIER_REPLACED:
            gmdl = model_of(open(GFPROP[crc][1], 'rb').read().decode('latin1'))
            if gmdl in RES or gmdl in OURS:
                p = REPLACE[k] = GFPROP[crc][1]
        for r in gfres.refs_of(k, p):
            seeds.add(r)
        mdl = gfres.prop_attr_model(open(p, 'rb').read().decode('latin1'))
        if mdl and gfres.mdatr_of(mdl) in RES:
            seeds.add(gfres.mdatr_of(mdl))
    env_ours = envkey in OURS
    if not env_ours:
        RES[envkey] = envsrc
        seeds.add(envkey)
    files, unres_map, _ = gfres.closure(sorted(seeds), OURS)
    for k, src in files.items():
        if k in OURS or k.endswith('/server_attr') or any(k in add[g] for g in add):
            continue
        if k.startswith('maps/'):
            continue
        grp = 'property' if k.startswith('property/') else MP if k.startswith(MAP_PREFIXES) else 'obj'
        add[grp][k] = src
    add[MP]['maps/%s/%s' % (MAP, env)] = envsrc      # the map folder's own copy (as our maps have)
    if not env_ours:
        add[MP][envkey] = envsrc
    add[MP] = dict((k, v) for k, v in add[MP].items() if v is not None)
    unres_all |= set(u for u in unres_map if not u.endswith('.msenv') and not (
        u.startswith('property/') and not u.endswith(('.prb', '.prd', '.pre', '.prt', '.pra'))))
    manifest['maps'][str(M['index'])] = dict(
        folder=MAP, terrain=SRC, own_attr=own_sectors, pack=MP, textureset=ts, environment=env,
        atlas_image=('d:/ymir work/ui/' + norm(img)) if img else None,
        objects=dict(crc_used=len(used), ours=sum(1 for c in used if c in OURPROP), staged=len(prop_src),
                     dropped=len(drop)),
        removed_objects=dict((str(c), dict(objects=n, why=drop[c])) for c, n in sorted(removed.items())))
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
for _v, _r in json.load(open(os.path.join(HERE, 'zaklety237_client.json'), encoding='utf-8')).get('npclist_add', {}).items():
    npc.setdefault(int(_v), _r.lower())     # the forest's guards 20160-20162 (patch_zaklety237_client.py adds the rows)
races = {}
unres_races = {}
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
PACK_OF_GROUP = {'obj': 'zaklety_obj', 'mobs': 'zaklety_mobs', 'property': 'property'}
packs = collections.OrderedDict()
for grp in [M['pack'] for M in MAPS] + ['obj', 'mobs', 'property']:
    base = PACK_OF_GROUP.get(grp, grp)
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
        dstp = os.path.join(STAGING, 'add', p, k.replace('d:/', 'd_/', 1))
        os.makedirs(os.path.dirname(dstp), exist_ok=True)
        shutil.copyfile(src, dstp)
        b = open(src, 'rb').read()
        where = 'gen' if src.startswith(GEN) else 'gf' if src.startswith(gfres.G) else 'ameria' if src.startswith(AMERIA) else src
        ents.append(dict(name=k, source=where, size=len(b), sha1=hashlib.sha1(b).hexdigest()))
    manifest['packs'][p] = ents
manifest['unresolved']['map'] = sorted(unres_all)
manifest['unresolved']['races'] = unres_races
manifest['unresolved']['effects'] = sorted(extra_missing)
json.dump(manifest, open(os.path.join(HERE, 'zaklety237_manifest.json'), 'w', encoding='utf-8'), indent=1, sort_keys=True,
          ensure_ascii=False)
for p in packs:
    print('%-13s %4d files %6.2f MB' % (p, len(packs[p]), sum(os.path.getsize(v) for v in packs[p].values()) / 1e6))
for i, m in manifest['maps'].items():
    print(i, m['folder'], m['terrain'], 'own attr', m['own_attr'], 'objects:', m['objects'], 'removed:', m['removed_objects'])
print('races:', dict((v, r['status']) for v, r in races.items() if r['status'] != 'ours'))
print('unresolved map:', manifest['unresolved']['map'])
print('unresolved races:', unres_races)
print('unresolved effects:', manifest['unresolved']['effects'])
