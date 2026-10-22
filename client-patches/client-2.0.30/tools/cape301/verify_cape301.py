# -*- coding: utf-8 -*-
# MT2009_PLUS_CAPE301_V1 - checks the packs build_cape301_packs.py wrote: everything map 301 names resolves to a
# name of the client (the OUT packs + the BASE listing c58.lst + the base client's pre-import listing):
#   the map folder (setting.txt, mapproperty.txt, the msenv copy; every sector's areadata/areaproperty/
#   areaambiencedata/attr.atr/height.raw/tile.raw/water.wtr/minimap.dds/shadowmap.*), the textureset and its
#   textures, the msenv (fog as exe 2.0.25 reads it) and its skybox, the atlas, every object of every sector
#   (areadata CRC -> a property of pack property -> its model/effect/tree and, for a Building, the .mdatr),
#   and every race of the map (npclist -> .msm -> what it names, recursively, as gfres.closure follows it).
# Run in the m2pack-lzo image:
#   docker run --rm -v /opt/metin2:/opt/metin2 m2pack-lzo python3 <repo>/client-patches/client-2.0.30/tools/cape301/verify_cape301.py \
#     <OUT pack dir> [<work dir with c58.lst>] [<npclist.txt>]
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, '/opt/metin2/cache/tcm/tz')
sys.path.insert(0, '/opt/metin2/cache/arezzo-work/client/az58')
sys.path.insert(0, os.path.join(HERE, '..', 'az58'))
import m2pack  # noqa: E402
import packlib  # noqa: E402

OUT = sys.argv[1]
WORK = sys.argv[2] if len(sys.argv) > 2 else '/opt/metin2/cache/yohara/cape301-work'
NPCLIST = sys.argv[3] if len(sys.argv) > 3 else '/opt/metin2/cache/c61/chk/gamedata/npclist.txt'
PRE_LST = '/opt/metin2/cache/tcm/gf28/ourpacks_pre.txt'
MAP = 'metin2_map_capedragonhead'
VNUMS = [3001, 3002, 3003, 3004, 3005, 3090, 3091, 3201, 3202, 3203, 3204, 3205, 3290, 3291,
         3501, 3502, 3503, 3504, 3505, 3590, 8051, 8052,
         9001, 9002, 9003, 9005, 9009, 9012, 10101, 10103, 20001, 20004, 20010, 20016, 20017,
         20029, 20030, 20047, 20057, 20058, 20059, 20349, 20373, 20377, 20378, 20380, 20381, 20382, 20383,
         30301, 30302, 30303, 30304, 30305]
RACE_DIRS = ('guild', 'npc', 'npc2', 'npc_pet', 'npc_mount', 'monster', 'monster2')
# GF's own broken references (the official client has the same): reported, not failed
KNOWN = {'d:/ymir work/zone/b/obj/512.jpg', 'd:/ymir work/zone/\xb0\xf8\xbf\xeb/hay_01.gr2'}


def norm(p):
    p = p.replace('\\', '/').strip().lower()
    while '//' in p:
        p = p.replace('//', '/')
    return p


CONTENT = {}
OWN = set()     # MT2009_PLUS_CAPE301_V1 (2.x, client67.sh): step 6 reads only the cape packs - OUT holds other builders' packs too
for p in sorted(f[:-6] for f in os.listdir(OUT) if f.endswith('.index')):
    f, v, ents = m2pack.read_index(os.path.join(OUT, p + '.index'))
    d = packlib.rd(os.path.join(OUT, p + '.data'))
    for e in ents:
        CONTENT.setdefault(e['name'], m2pack.read_entry(d, e))
        if p.startswith('cape_'):
            OWN.add(e['name'])
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
        known = k in KNOWN or ':/' in k[3:]          # a developer's path inside a GF file (horse_stop.msa)
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
assert (w, h) == (6, 6) and re.search(r'BasePosition\s+1024000\s+1664000', st), st
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
        for t in re.findall(r'"([^"]+\.dds)"', et, re.I):
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
nomdatr = set()      # GF ships no .mdatr for them either: no client collision (the server's server_attr still blocks)
for x in range(w):
    for y in range(h):
        a = text('%s%03d%03d/areadata.txt' % (mp, x, y)) or ''
        bodies = re.findall(r'Start Object\d+\r?\n(.*?)End Object', a, re.S)
        cnt = re.search(r'ObjectCount\s+(\d+)', a)
        assert cnt is None or int(cnt.group(1)) == len(bodies), (x, y)
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
                        md = (m[:i] if i > m.rfind('/') else m) + '.mdatr'
                        if md not in NAMES:
                            nomdatr.add(m)

# 6) the races, and everything the staged text files name
npc, alias = {}, {}
for l in open(NPCLIST, encoding='latin1'):
    t = l.split()
    if len(t) >= 3 and t[0] == '0':
        alias[t[1].lower()] = t[2].lower()
    elif len(t) >= 2 and t[0].isdigit():
        npc[int(t[0])] = t[1].lower()
for v in VNUMS:
    name = npc[v]
    folder = alias.get(name, name)
    cands = ['d:/ymir work/%s/%s/%s.msm' % (d, folder, name) for d in RACE_DIRS]
    if not any(c in NAMES for c in cands):
        notes.append('race %d %s: no .msm in our listing - the base client (npc/monster packs, no listing) must have it'
                     % (v, name))
RE_Q = re.compile(r'"([^"\r\n]+\.(?:gr2|dds|tga|mse|msa|msm|mss|wav|mp3|txt|msenv|mde|spt|mdatr))"', re.I)
for k, b in CONTENT.items():
    if k not in OWN or not k.endswith(('.msm', '.msa', '.mse', '.mss', '.prb', '.prd', '.pre', '.prt', '.msenv')) or k.startswith('property/'):
        continue
    t = b.decode('latin1')
    d = k.rsplit('/', 1)[0] + '/'
    for r in RE_Q.findall(t):
        r = norm(r)
        if not (r.startswith('d:/') or r.startswith(('sound/', 'textureset/', 'property/'))):
            r = 'd:/' + r if r.startswith('ymir work/') else d + r
        need(r, k)

print('objects checked: %d, properties in pack: %d, names known: %d' % (nobj, len(props), len(NAMES)))
print('Building/DungeonBlock models without .mdatr (none in GF either): %d' % len(nomdatr))
print('notes (%d):' % len(notes))
for n in sorted(set(notes)):
    print('  ' + n)
print('FAIL (%d):' % len(fail))
for f in sorted(set(fail)):
    print('  ' + f)
sys.exit(1 if fail else 0)
