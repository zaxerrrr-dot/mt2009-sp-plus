# -*- coding: utf-8 -*-
# MT2009_PLUS_SPIDER3_V1 (client) - 3 Loch Pajakow (217, metin2_map_spiderdungeon_03, 3x3 at 51200 563200): the client
# files staged for build_spider3_packs.py.
#
#   python3 stage_spider3.py [<staging dir>] [<work dir>]       (host; no lzo needed)
#
# defaults: /opt/metin2/cache/yohara/spider3-staging, /opt/metin2/cache/yohara/cape301-work (c58.lst + x/property of the
# client we build on). Writes <staging>/add/<pack>/<in-pack name> ("d:/" as "d_/") and tools/spider3/spider3_manifest.json.
#
# Why the client needs it: no client of this world could load map 217 (MT2009_PLUS_SPIDER3_OFF_V1, 1 October - a warp
# there closed the client). The client picks the map by the warp's position from gamedata/atlasinfo.txt (the row
# metin2_map_spiderdungeon_03 51200 563200 3 3 is there), and the folder that row names is in none of our packs.
# Our base client's map packs (map_*, zone_*) have no listing on this host, so a partial folder of that name in them
# cannot be ruled out - and the exe takes a file from the pack registered first. The terrain therefore goes in under
# a name no client has, metin2_map_spiderdungeon3, and the atlasinfo row is renamed to it (build_spider3_packs.py ->
# patch_spider3_client.py); the same for the textureset (textureset/metin2_spider3.txt = GF's metin2_map_spiderd.txt,
# two textures).
#
# The terrain is GF 26.1.11's metin2_map_spiderdungeon_03: its attr.atr agrees with our server_attr cell for cell
# (100.00 %, the srvattr check of 28 October). setting.txt is written with the server's BasePosition / MapSize,
# ViewRadius 128 and Environment dark.msenv (d:/ymir work/environment/dark.msenv - in our pack ochao already, written
# for exe 2.0.25); mapproperty.txt is GF's (Outdoor, no ParentMapName).
#   maps/<folder>/..., the textureset and its terrain textures, the atlas  -> new pack spider3_map
#   property/...                                                           -> pack property (added)
#   the map objects' models (zone/spider_dungeon ...) our listing lacks     -> new pack spider3_obj
# No race is staged: the five poison spiders 2071-2075 are spider_young / spider_poison / spider_redpoison /
# spider_nipper / spider_soldier (the first Spider Dungeon's), the portals 10097/10098 "warp", the Nagrobek 30130 an
# invisible quest NPC - all in the base client.
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

STAGING = sys.argv[1] if len(sys.argv) > 1 else '/opt/metin2/cache/yohara/spider3-staging'
WORK = sys.argv[2] if len(sys.argv) > 2 else '/opt/metin2/cache/yohara/cape301-work'
OURS_LST = os.path.join(WORK, 'c58.lst')
PRE_LST = '/opt/metin2/cache/tcm/gf28/ourpacks_pre.txt'
GR2_64 = b'\xe5\x9b\x49\x5e'
SPLIT = 26 * 1000 * 1000
MAP_PREFIXES = ('maps/', 'textureset/', 'd:/ymir work/terrainmaps/', 'd:/ymir work/environment/', 'd:/ymir work/ui/')
norm = gfres.norm

SRC = 'metin2_map_spiderdungeon_03'           # GF's folder
FOLDER = 'metin2_map_spiderdungeon3'          # ours (atlasinfo row renamed to it)
SIZE = (3, 3)
BASE = (51200, 563200)
TSKEY = 'textureset/metin2_spider3.txt'
TSSRC = 'textureset/metin2_map_spiderd.txt'
ENV = 'dark.msenv'
ENVKEY = 'd:/ymir work/environment/' + ENV
SETTING = ('ScriptType\tMapSetting\r\n\r\nCellScale\t200\r\nHeightScale\t0.500000\r\n\r\nViewRadius\t128\r\n\r\n'
           'MapSize\t%d\t%d\r\nBasePosition\t%d\t%d\r\nTextureSet\ttextureset\\metin2_spider3.txt\r\n'
           'Environment\t' + ENV + '\r\n')

# ---------------------------------------------------------------- what our client has (incl. the earlier builders)
OURS = set(gfres.load_ours(PRE_LST))
for l in open(OURS_LST, encoding='utf-8', errors='replace'):
    t = l.rstrip('\n').split(' ', 1)
    if len(t) == 2:
        OURS.add(norm(t[1]))
EARLIER = {}
for mp in sorted(__import__('glob').glob(os.path.join(HERE, '..', '*', '*_manifest.json'))):
    if os.path.basename(mp) == 'spider3_manifest.json':
        continue
    man = json.load(open(mp, encoding='utf-8'))
    packs = man.get('packs')
    if isinstance(packs, dict):
        for p in packs.values():
            if isinstance(p, list):
                for e in p:
                    if isinstance(e, dict) and 'name' in e:
                        EARLIER.setdefault(e['name'], os.path.basename(mp))
OURS |= set(EARLIER)
EARLIER_STAGING = sorted(__import__('glob').glob('/opt/metin2/cache/yohara/*-staging/add/property/property'))
assert ENVKEY in OURS, ENVKEY + ' is not in our listing'
for k in OURS:
    assert not k.startswith('maps/%s/' % FOLDER) and k != TSKEY, k

RES = dict(gfres.GF)
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
for k, p in RES.items():
    if k.startswith('property/'):
        c = prop_crc(p)
        if c is not None:
            GFPROP.setdefault(c, (k, p))

add = collections.defaultdict(dict)       # group -> key -> src (group: 'map', 'property', 'obj')
manifest = {'maps': {}, 'packs': {}, 'unresolved': {}, 'replace': []}
seeds = set()

srcdir = os.path.join(gfres.G, SRC)
mp = 'maps/%s/' % FOLDER
files = {}
for dp, dn, fn in os.walk(srcdir):
    for f in fn:
        rel = norm(os.path.relpath(os.path.join(dp, f), srcdir))
        if rel in ('regen.txt', 'setting.txt'):
            continue
        files[mp + rel] = os.path.join(dp, f)
sectors = sorted(k for k in files if k.endswith('/areadata.txt'))
assert len(sectors) == SIZE[0] * SIZE[1], len(sectors)
mpt = open(files[mp + 'mapproperty.txt'], 'rb').read().decode('latin1')
assert 'ParentMapName' not in mpt and re.search(r'MapType\s+"Outdoor"', mpt), mpt
st = open(os.path.join(srcdir, 'setting.txt'), 'rb').read().decode('latin1')
assert re.search(r'MapSize\s+%d\s+%d' % SIZE, st) and re.search(r'BasePosition\s+%d\s+%d' % BASE, st), st
assert re.search(r'TextureSet\s+textureset\\metin2_map_spiderd\.txt', st, re.I), st
add['map'][mp + 'setting.txt'] = gen(mp + 'setting.txt', (SETTING % (SIZE + BASE)).encode('latin1'))
used = collections.Counter()
for s in sectors:
    t = open(files[s], 'rb').read().decode('latin1').replace('\r', '')
    for body in re.findall(r'Start Object\d+\n(.*?)End Object\n', t, re.S):
        used[crc_of_body(body)] += 1
prop_src, drop = {}, {}
for crc in sorted(used):
    if crc in OURPROP:
        continue
    kp = GFPROP.get(crc)
    if not kp:
        drop[crc] = 'no property (our property pack, GF)'
        continue
    mdl = model_of(open(kp[1], 'rb').read().decode('latin1'))
    if mdl and mdl.endswith('.gr2') and mdl in RES and open(RES[mdl], 'rb').read(4) == GR2_64:
        drop[crc] = '64-bit GR2 %s' % mdl
        continue
    if mdl and mdl not in RES and mdl not in OURS:
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
# the atlas: GF's atlas_resize picture of the official folder, staged where exe 2.0.25 looks
gsub = 'd:/ymir work/ui/atlas_resize/%s/atlas.sub' % SRC
img = None
if gsub in RES:
    img = norm(re.search(r'image\s+"([^"]+)"', open(RES[gsub], 'rb').read().decode('latin1')).group(1))
    if 'd:/ymir work/ui/' + img in RES:
        add['map']['d:/ymir work/ui/atlas/%s/atlas.sub' % FOLDER] = RES[gsub]
        seeds.add('d:/ymir work/ui/' + img)
    else:
        img = None
assert img, 'no atlas picture for ' + SRC
for crc, (k, p) in prop_src.items():
    add['property'][k] = p
# the textureset: GF's metin2_map_spiderd.txt under a name of its own
add['map'][TSKEY] = gen(TSKEY, open(RES[TSSRC], 'rb').read())
RES[TSKEY] = add['map'][TSKEY]
gfres.GF[TSKEY] = add['map'][TSKEY]
seeds.add(TSKEY)

files2, unres_map, _ = gfres.closure(sorted(seeds), OURS)
for k, src in files2.items():
    if k in OURS or any(k in add[g] for g in add):
        continue
    if k.startswith('maps/'):
        continue
    grp = 'property' if k.startswith('property/') else 'map' if k.startswith(MAP_PREFIXES) else 'obj'
    add[grp][k] = src
unres = sorted(u for u in unres_map if not u.endswith('.msenv') and not (
    u.startswith('property/') and not u.endswith(('.prb', '.prd', '.pre', '.prt', '.pra'))))

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
PACK_OF_GROUP = {'map': 'spider3_map', 'obj': 'spider3_obj', 'property': 'property'}
packs = collections.OrderedDict()
for grp in ('map', 'obj', 'property'):
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
manifest['maps']['217'] = dict(
    folder=FOLDER, source='GF 26.1.11 ' + SRC, size=list(SIZE), base=list(BASE), pack='spider3_map', textureset=TSKEY,
    environment=ENV, atlas_image='d:/ymir work/ui/' + img,
    atlas_row_from='metin2_map_spiderdungeon_03',
    objects=dict(crc_used=len(used), ours=sum(1 for c in used if c in OURPROP), staged=len(prop_src), dropped=len(drop)),
    removed_objects=dict((str(c), dict(objects=n, why=drop[c])) for c, n in sorted(removed.items())))
manifest['new_packs'] = [p for p in packs if p != 'property' and packs[p]]
for p in packs:
    ents = []
    for k in sorted(packs[p]):
        src = packs[p][k]
        dst = os.path.join(STAGING, 'add', p, k.replace('d:/', 'd_/', 1))
        os.makedirs(os.path.dirname(dst), exist_ok=True)
        shutil.copyfile(src, dst)
        b = open(src, 'rb').read()
        where = 'gen' if src.startswith(GEN) else 'gf' if src.startswith(gfres.G) else src
        ents.append(dict(name=k, source=where, size=len(b), sha1=hashlib.sha1(b).hexdigest()))
    manifest['packs'][p] = ents
manifest['environment'] = dict(key=ENVKEY, ours=True)
manifest['unresolved']['map'] = unres
manifest['unresolved']['effects'] = sorted(extra_missing)
json.dump(manifest, open(os.path.join(HERE, 'spider3_manifest.json'), 'w', encoding='utf-8'), indent=1, sort_keys=True,
          ensure_ascii=False)
for p in packs:
    print('%-13s %4d files %6.2f MB' % (p, len(packs[p]), sum(os.path.getsize(v) for v in packs[p].values()) / 1e6))
m = manifest['maps']['217']
print(217, m['folder'], 'objects:', m['objects'], 'removed:', m['removed_objects'], 'atlas:', m['atlas_image'])
print('unresolved map:', unres)
print('unresolved effects:', manifest['unresolved']['effects'])
