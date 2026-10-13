# -*- coding: utf-8 -*-
# MT2009_PLUS_YOHARA_PORT_V1 (client) - Port Nowego Kontynentu (map 368, metin2_map_defensewave_port, 3x3 at
# 128000 563200): the client files staged for build_port368_packs.py, from the GF 26.1.11 client (the port as the
# official game has it) and, for what GF lacks, the Ameria client sources. The same approach as
# ../shipdefense/stage_shipdefense.py.
#
#   python3 stage_port368.py [<staging dir>] [<work dir>]       (host; no lzo needed)
#
# defaults: /opt/metin2/cache/yohara/port-staging, /opt/metin2/cache/yohara/cape301-work (c58.lst + x/property of the
# client we build on, written by ../atlantis/dump_base.py <BASE pack dir> <work dir>). Writes
# <staging>/add/<pack>/<in-pack name> ("d:/" as "d_/") and port368_manifest.json.
#
#   maps/metin2_map_defensewave_port/... -> new pack port_map (9 sectors, mapproperty, setting.txt with the server's
#                                           BasePosition 128000 563200 - GF's says 0 0 -, the msenv copy)
#   the atlas (GF's atlas.sub and .dds), the port's objects and their textures  -> port_map
#   property/... the port's object properties our client lacks   -> pack property (the exe loads map objects only
#                                                                    from pack/property)
# The port shares its textureset (metin2_map_defensewave.txt) and msenv (defensewave_blue.msenv) with the ship, and
# its only NPC, the Statua Wojownika (20433, defensewave_statue), is a race of the ship: all of that comes with
# ../shipdefense (hydra_map, hydra_mobs). A name our client already has - the dump listing, the base client's
# pre-import listing and what ../cape301, ../maps302 and ../shipdefense stage (the build runs them first) - is left
# out: ours wins.
# GF's msenv names "foglevel 14": exe 2.0.25 reads Enable/NearDistance/FarDistance only - 20000 / 80000 (as 301 and
# the ship; the map's own copy is generated the same way as the ship's, byte for byte).
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

STAGING = sys.argv[1] if len(sys.argv) > 1 else '/opt/metin2/cache/yohara/port-staging'
WORK = sys.argv[2] if len(sys.argv) > 2 else '/opt/metin2/cache/yohara/cape301-work'
OURS_LST = os.path.join(WORK, 'c58.lst')
PRE_LST = '/opt/metin2/cache/tcm/gf28/ourpacks_pre.txt'
BEFORE = [os.path.join(HERE, '..', d, d + '_manifest.json') for d in ('cape301', 'maps302', 'shipdefense')]
AMERIA = '/opt/metin2/ameria/ameria-prj-2025/tools/FoxFSArchiver/source'
MAP = 'metin2_map_defensewave_port'
SIZE = (3, 3)
BASE_POS = (128000, 563200)        # = linux-port/docker/game/yohara_port/map/metin2_map_defensewave_port/Setting.txt
GR2_64 = b'\xe5\x9b\x49\x5e'
FOG = (20000.0, 80000.0)
MAP_PACK = 'port_map'
norm = gfres.norm

# ---------------------------------------------------------------- what our client has
OURS = set(gfres.load_ours(PRE_LST))
for l in open(OURS_LST, encoding='utf-8', errors='replace'):
    t = l.rstrip('\n').split(' ', 1)
    if len(t) == 2:
        OURS.add(norm(t[1]))
EARLIER = {}
for mf in BEFORE:
    for p, ents in json.load(open(mf, encoding='utf-8'))['packs'].items():
        for e in ents:
            EARLIER[e['name']] = e['sha1']
OURS |= set(EARLIER)


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
EARLYPROP = {}                      # properties an earlier builder stages (the ship's property/defensewave/...)
for k in EARLIER:
    if k.startswith('property/') and k in GF:
        c = prop_crc(GF[k])
        if c is not None:
            EARLYPROP[c] = k

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
    if crc in OURPROP or crc in EARLYPROP:
        continue
    kp = GFPROP.get(crc)
    if not kp:
        missing_prop.append(crc)
        continue
    assert kp[0] not in OURS, ('property name ours with another CRC', kp[0])
    prop_src[crc] = kp
assert not missing_prop, missing_prop

# ---------------------------------------------------------------- setting.txt, msenv copy, atlas (generated)
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
envdata = crlf(et).encode('latin1')
envsrc = gen(envkey, envdata)
if envkey in EARLIER:               # the ship stages the same file: it must be the very same bytes
    assert EARLIER[envkey] == hashlib.sha1(envdata).hexdigest(), envkey
assert ts in OURS, ts               # the ship's textureset (../shipdefense)
atlas_dds = 'd:/ymir work/ui/%s_atlas.dds' % MAP
atlas_sub = 'd:/ymir work/ui/atlas/%s/atlas.sub' % MAP
assert atlas_dds in GF and atlas_sub not in OURS
SUB = crlf('title subImage\nversion 1.0\nimage "%s_atlas.dds"\nleft 0\ntop 0\nright 256\nbottom 256\n' % MAP).encode('latin1')
if atlas_sub in GF:                 # GF ships this one (the ship's it does not); it must say what we would write
    assert open(GF[atlas_sub], 'rb').read() == SUB, atlas_sub
    add[MAP_PACK][atlas_sub] = GF[atlas_sub]
else:
    add[MAP_PACK][atlas_sub] = gen(atlas_sub, SUB)

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
        assert k not in OURS, k
        assert len(k.encode('cp1252')) < 161, k
manifest = {'packs': {}, 'unresolved': {},
            'objects': {'crc_used': len(used), 'ours': sum(1 for c in used if c in OURPROP),
                        'earlier_builders': sum(1 for c in used if c in EARLYPROP and c not in OURPROP),
                        'staged': len(prop_src)}}
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
manifest['unresolved']['effects'] = sorted(extra_missing)
json.dump(manifest, open(os.path.join(HERE, 'port368_manifest.json'), 'w', encoding='utf-8'), indent=1,
          sort_keys=True, ensure_ascii=False)
for p in sorted(add):
    print('%-10s %4d files %6.2f MB' % (p, len(add[p]), sum(os.path.getsize(v) for v in add[p].values()) / 1e6))
print('objects:', manifest['objects'])
print('unresolved map:', manifest['unresolved']['map'])
print('unresolved effect textures:', manifest['unresolved']['effects'])
print('ameria files:', sorted(e['name'] for p in manifest['packs'].values() for e in p if e['source'] == 'ameria'))
