# -*- coding: utf-8 -*-
# MT2009_PLUS_SHIP_DEFENSE_V1 (client) - checks the packs build_shipdefense_packs.py wrote: everything the ship
# (map 367, metin2_map_defensewave) names resolves to a name of the client (the OUT packs + the BASE listing c58.lst
# + the base client's pre-import listing):
#   the map folder (setting.txt with MapSize 3 3 / BasePosition 128000 486400, mapproperty.txt, the msenv copy;
#   every sector's areadata/areaproperty/areaambiencedata/attr.atr/height.raw/tile.raw/water.wtr/minimap.dds/
#   shadowmap.*), the textureset and its textures, the msenv (fog as exe 2.0.25 reads it) and its skybox, the atlas,
#   every object of every sector (areadata CRC -> a property of pack property -> its model and, for a Building,
#   the .mdatr), every race of the ship (npclist -> .msm -> base model, motlist -> .msa -> .gr2, textures), every
#   staged text file's references (msm/msa/mse/mss/msenv, effect textures and meshes), the laser
#   d:/ymir work/effect/monster2/defense_mini_laser.mse, and the gamedata rows (mob_proto 24 races, atlasinfo).
# Run in the m2pack-lzo image:
#   docker run --rm -v /opt/metin2:/opt/metin2 m2pack-lzo python3 <repo>/client-patches/client-2.0.30/tools/shipdefense/verify_shipdefense.py \
#     <OUT pack dir> [<work dir with c58.lst>] [<npclist.txt>]
import json
import os
import re
import struct
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, '/opt/metin2/cache/tcm/tz')
sys.path.insert(0, '/opt/metin2/cache/arezzo-work/client/az58')
sys.path.insert(0, os.path.join(HERE, '..', 'az58'))
sys.path.insert(0, HERE)
import m2pack  # noqa: E402
import packlib  # noqa: E402
import patch_shipdefense_client as pc  # noqa: E402

OUT = sys.argv[1]
WORK = sys.argv[2] if len(sys.argv) > 2 else '/opt/metin2/cache/yohara/cape301-work'
NPCLIST = sys.argv[3] if len(sys.argv) > 3 else '/opt/metin2/cache/c61/chk/gamedata/npclist.txt'
PRE_LST = '/opt/metin2/cache/tcm/gf28/ourpacks_pre.txt'
MAP = 'metin2_map_defensewave'
VNUMS = list(range(3949, 3966)) + [3970, 20432, 20433, 20434, 20435, 20436, 20437,
                                     3401, 3402, 3405, 3601, 3602, 3603, 3604, 3605]
RACE_DIRS = ('guild', 'npc', 'npc2', 'npc_pet', 'npc_mount', 'monster', 'monster2')
LASER = 'd:/ymir work/effect/monster2/defense_mini_laser.mse'
# GF's own broken references (the official client has the same): reported, not failed
KNOWN = {'d:/ymir work/monster2/defensewave_medusa/ns~3.dds'}


def norm(p):
    p = p.replace('\\', '/').strip().lower()
    while '//' in p:
        p = p.replace('//', '/')
    return p


CONTENT = {}
for p in sorted(f[:-6] for f in os.listdir(OUT) if f.endswith('.index')):
    f, v, ents = m2pack.read_index(os.path.join(OUT, p + '.index'))
    d = packlib.rd(os.path.join(OUT, p + '.data'))
    for e in ents:
        CONTENT.setdefault(e['name'], m2pack.read_entry(d, e))
NAMES = set(CONTENT)
for l in open(os.path.join(WORK, 'c58.lst'), encoding='utf-8', errors='replace'):
    t = l.rstrip('\n').split(' ', 1)
    if len(t) == 2:
        NAMES.add(norm(t[1]))
for l in open(PRE_LST, encoding='utf-8', errors='replace'):
    t = l.rstrip('\n').split(' ', 3)
    if len(t) == 4:
        NAMES.add(norm(t[3]))

fail = []
notes = []


def need(k, why):
    if k not in NAMES:
        known = k in KNOWN or ':/' in k[3:]
        (notes if known else fail).append('%s  (%s)' % (k, why))
        return False
    return True


def text(k):
    return CONTENT[k].decode('latin1') if k in CONTENT else None


# 1) the map folder
mp = 'maps/%s/' % MAP
for k in ('setting.txt', 'mapproperty.txt'):
    need(mp + k, 'map')
st = text(mp + 'setting.txt')
w, h = [int(x) for x in re.search(r'MapSize\s+(\d+)\s+(\d+)', st).groups()]
assert (w, h) == (3, 3) and re.search(r'BasePosition\s+128000\s+486400', st), st
SECT = ('areadata.txt', 'areaproperty.txt', 'areaambiencedata.txt', 'attr.atr', 'height.raw', 'tile.raw',
        'water.wtr', 'minimap.dds', 'shadowmap.dds', 'shadowmap.raw')
for x in range(w):
    for y in range(h):
        for f in SECT:
            need('%s%03d%03d/%s' % (mp, x, y, f), 'sector')
# 2) textureset
ts = norm(re.search(r'TextureSet\s+(\S+)', st, re.I).group(1))
need(ts, 'setting.txt')
for t in re.findall(r'"([^"]+\.dds)"', text(ts) or '', re.I):
    need(norm(t), ts)
# 3) msenv
env = norm(re.search(r'Environment\s+(\S+)', st, re.I).group(1))
for k in (mp + env, 'd:/ymir work/environment/' + env):
    if need(k, 'setting.txt') and k in CONTENT:
        et = text(k)
        assert re.search(r'(?im)^\s*NearDistance', et) and re.search(r'(?im)^\s*FarDistance', et) \
            and not re.search(r'(?im)^\s*foglevel', et), k
        for t in re.findall(r'"([^"]+\.(?:dds|tga))"', et, re.I):
            need(norm(t), k)
# 4) atlas
sub = 'd:/ymir work/ui/atlas/%s/atlas.sub' % MAP
if need(sub, 'atlas'):
    img = re.search(r'image\s+"([^"]+)"', text(sub) or '').group(1)
    need('d:/ymir work/ui/' + norm(img), sub)

# 5) the objects
props = {}
for k, b in CONTENT.items():
    if k.startswith('property/'):
        l = b.replace(b'\r', b'').split(b'\n')
        if l and l[0].strip() == b'YPRT':
            props[int(l[1].strip())] = k
nobj = 0
nomdatr = set()
for x in range(w):
    for y in range(h):
        a = text('%s%03d%03d/areadata.txt' % (mp, x, y)) or ''
        bodies = re.findall(r'Start Object\d+\r?\n(.*?)End Object', a, re.S)
        for body in bodies:
            nobj += 1
            crc = int(body.replace('\r', '').split('\n')[1].strip().split('#')[0])
            if crc not in props:
                fail.append('object CRC %d of sector %03d%03d: no property in pack property' % (crc, x, y))
                continue
            pt = text(props[crc])
            kv = dict((l.split(None, 1)[0].lower(), l.split(None, 1)[1].strip().strip('"'))
                      for l in pt.replace('\r', '').split('\n') if len(l.split(None, 1)) == 2)
            for key in ('buildingfile', 'dungeonblockfile', 'effectfile', 'treefile', 'ambiencefile'):
                if key in kv:
                    m = norm(kv[key])
                    need(m, props[crc])
                    if key in ('buildingfile', 'dungeonblockfile'):
                        i = m.rfind('.')
                        if (m[:i] if i > m.rfind('/') else m) + '.mdatr' not in NAMES:
                            nomdatr.add(m)

# 6) the races: npclist -> msm -> base model; motlist -> msa -> gr2
npc, alias = {}, {}
for l in open(NPCLIST, encoding='latin1'):
    t = l.split()
    if len(t) >= 3 and t[0] == '0':
        alias[t[1].lower()] = t[2].lower()
    elif len(t) >= 2 and t[0].isdigit():
        npc[int(t[0])] = t[1].lower()
RE_Q = re.compile(r'"([^"\r\n]+\.(?:gr2|dds|tga|mse|msa|msm|mss|wav|mp3|txt|msenv|mde|spt|mdatr|msf))"', re.I)
nraces = 0
for v in VNUMS:
    name = npc.get(v)
    if not name:
        fail.append('race %d: no npclist row' % v)
        continue
    folder = alias.get(name, name)
    cands = ['d:/ymir work/%s/%s/%s.msm' % (d, folder, name) for d in RACE_DIRS]
    msm = next((c for c in cands if c in NAMES), None)
    if not msm:
        fail.append('race %d %s: no .msm' % (v, name))
        continue
    nraces += 1
    if msm not in CONTENT:
        continue                    # ours from before (tritons, crabs, warp_blue): not re-checked
    d = msm.rsplit('/', 1)[0] + '/'
    ml = d + 'motlist.txt'
    if ml in CONTENT:
        for l in text(ml).replace('\r', '').split('\n'):
            t = l.split()
            if len(t) >= 3 and t[2].lower().endswith('.msa'):
                need(d + norm(t[2]), ml)
    elif ml not in NAMES:
        notes.append('race %d %s: no motlist.txt' % (v, name))
# 7) everything the staged text files name (the names of shipdefense_manifest.json)
STAGED = set(e['name'] for ents in json.load(open(os.path.join(HERE, 'shipdefense_manifest.json')))['packs'].values()
             for e in ents)
missing_staged = sorted(STAGED - set(CONTENT))
fail.extend('staged %s not in OUT' % k for k in missing_staged)
for k, b in CONTENT.items():
    if k not in STAGED:
        continue
    if not k.endswith(('.msm', '.msa', '.mse', '.mss', '.msenv', '.msf')) or k.startswith('property/'):
        continue
    t = b.decode('latin1')
    d = k.rsplit('/', 1)[0] + '/'
    for r in RE_Q.findall(t):
        r = norm(r)
        if not (r.startswith('d:/') or r.startswith(('sound/', 'textureset/', 'property/'))):
            r = 'd:/' + r if r.startswith('ymir work/') else d + r
        need(r, k)
for k, b in CONTENT.items():
    if k not in STAGED or not k.endswith(('.mde', '.mse')):
        continue
    for m in re.findall(rb'[A-Za-z]:[\\/][^\x00"\r\n]+?\.(?:dds|tga|png|jpg|mde)', b, re.I):
        need('d:' + m.decode('latin1').replace('\\', '/').lower()[2:], k)
need(LASER, 'server: playerbot_ship_defense.cpp LASER_EFFECT')

# 8) the gamedata rows
gd = CONTENT.get('gamedata/mob_proto')
if gd is None:
    fail.append('gamedata/mob_proto not in OUT')
else:
    nb, n = pc.mob_proto(gd)
    if n:
        fail.append('mob_proto: %d of the ship races missing' % n)
    magic, cnt, esize = struct.unpack_from('<4sII', gd, 0)
    raw = m2pack.mcoz_decode(gd[12:12 + esize], pc.MOB_KEY)
    have = set(struct.unpack_from('<I', raw, i * pc.MOB_RECORD)[0] for i in range(cnt))
    for v in VNUMS:
        if v not in have:
            fail.append('mob_proto: no record %d' % v)
ai = CONTENT.get('gamedata/atlasinfo.txt')
if ai is None or pc.atlasinfo(ai)[1]:
    fail.append('atlasinfo.txt: no %s row' % MAP)

print('objects checked: %d, properties in pack: %d, races: %d, names known: %d' % (nobj, len(props), nraces, len(NAMES)))
print('Building/DungeonBlock models without .mdatr (no client collision; the server_attr still blocks): %d %s' % (
    len(nomdatr), sorted(nomdatr)))
print('notes (%d):' % len(notes))
for n in sorted(set(notes)):
    print('  ' + n)
print('FAIL (%d):' % len(fail))
for f in sorted(set(fail)):
    print('  ' + f)
sys.exit(1 if fail else 0)
