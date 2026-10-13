# -*- coding: utf-8 -*-
# MT2009_PLUS_YOHARA_MAPS3_V1 - checks the packs build_ymaps3_packs.py wrote: everything Zejscie (394), Glebie (395),
# 1. poziom Swiatyni Wezy (390), Swiatynia Wezy (391), Tajemnicza Instancja (396) and Krolestwo Zywiolow (378-381) name
# resolves to a name of the client (the OUT packs + the BASE listing c58.lst + the base client's pre-import listing):
#   each map folder (setting.txt with its size/base/ViewRadius 128, mapproperty.txt, the msenv; every sector's
#   areadata/areaproperty/areaambiencedata/attr.atr/height.raw/tile.raw/water.wtr/minimap.dds/shadowmap.*), the
#   textureset and its textures, the msenv (fog as exe 2.0.25 reads it) and its skybox, the atlas (the two dungeons
#   have none), every object of every sector (areadata CRC -> a property of pack property -> its model/effect/tree
#   and, for a Building, the .mdatr), every race of the maps (npclist -> .msm) and every name the staged text files
#   give; the new packs under the 29 MB limit and in Index; gamedata/dbdata: the 131 mob_proto rows of
#   yohara_maps3.sql, the nine atlasinfo rows, npclist 10125, the 69 items (item_proto, item_list, itemdesc).
# Run in the m2pack-lzo image, on the OUT the whole chain (cape301, maps302, shipdefense, port368, ymaps, ymaps2,
# ymaps3) was built into:
#   docker run --rm -v /opt/metin2:/opt/metin2 m2pack-lzo python3 <repo>/client-patches/client-2.0.30/tools/ymaps3/verify_ymaps3.py \
#     <OUT pack dir> [<work dir with c58.lst>] [<npclist.txt>]
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, '/opt/metin2/cache/tcm/tz')
sys.path.insert(0, '/opt/metin2/cache/arezzo-work/client/az58')
sys.path.insert(0, os.path.join(HERE, '..', 'az58'))
sys.path.insert(0, HERE)
import m2pack  # noqa: E402
import packlib  # noqa: E402
import patch_ymaps3_client as pc  # noqa: E402

args = [a for a in sys.argv[1:] if not a.startswith('--')]
OUT = args[0]
WORK = args[1] if len(args) > 1 else '/opt/metin2/cache/yohara/cape301-work'
NPCLIST = args[2] if len(args) > 2 else '/opt/metin2/cache/c61/chk/gamedata/npclist.txt'
PRE_LST = '/opt/metin2/cache/tcm/gf28/ourpacks_pre.txt'
ZIP_LIMIT = 29 * 1024 * 1024
MAN = json.load(open(os.path.join(HERE, 'ymaps3_manifest.json'), encoding='utf-8'))
MAPS = [(394, 'metin2_map_whitedragoncave_02', (3, 3), (1152000, 1203200)),
        (395, 'metin2_map_whitedragoncave_boss', (2, 2), (1228800, 1203200)),
        (390, 'metin2_map_snake_temple_01', (3, 3), (0, 1638400)),
        (391, 'metin2_map_snake_temple_02', (3, 3), (76800, 1638400)),
        (396, 'metin2_map_anglar_dungeon_01', (6, 6), (153600, 1049600)),
        (378, 'metin2_map_elemental_01', (5, 5), (0, 921600)),
        (379, 'metin2_map_elemental_02', (5, 5), (128000, 921600)),
        (380, 'metin2_map_elemental_03', (5, 5), (256000, 921600)),
        (381, 'metin2_map_elemental_04', (1, 2), (384000, 921600))]
NO_ATLAS = ('metin2_map_whitedragoncave_boss', 'metin2_map_snake_temple_02')   # GF has no atlas picture for them
RACE_DIRS = ('guild', 'npc', 'npc2', 'npc_pet', 'npc_mount', 'monster', 'monster2')
# GF's own broken references (the official client has the same): reported, not failed
KNOWN = {'d:/ymir work/zone/b/obj/512.jpg', 'd:/ymir work/zone/\xb0\xf8\xbf\xeb/hay_01.gr2',
         # a Dongan object's mesh names a texture in no client (GF's own is not there either)
         'd:/ymir work/zone/dungeon/dawnmistwood_dungeon/mushroomc_a.dds',
         # GF's shape.msm of two NPC races names the later client's "season1\\" path; exe 2.0.25 loads the race's own
         # <name>.msm (staged, a d:/ymir work path) first, so shape.msm is never read
         'd:/ymir work/npc/chagirap/season1/npc/chagirap/chagirap.gr2',
         'd:/ymir work/npc/jinno_guard_bow/season1/npc/jinno_guard_bow/jinno_patrol_bow.gr2',
         # a model of the Serpent Temple's objects names a texture no client has (GF's own reference)
         'd:/ymir work/zone/geuglagsa/black.dds',
         # a motion of the Serpent Temple's warrior names an effect in no client (GF's sits in an encrypted blob)
         'd:/ymir work/effect/monster2/defense_medusa_n1_throw.mse'}


def norm(p):
    p = p.replace('\\', '/').strip().lower()
    while '//' in p:
        p = p.replace('//', '/')
    return p


fail = []
notes = []
CONTENT = {}
for p in sorted(f[:-6] for f in os.listdir(OUT) if f.endswith('.index')):
    f, v, ents = m2pack.read_index(os.path.join(OUT, p + '.index'))
    d = packlib.rd(os.path.join(OUT, p + '.data'))
    if p in MAN['new_packs'] and len(d) >= ZIP_LIMIT:
        fail.append('pack %s: data %d bytes, over the 29 MB limit' % (p, len(d)))
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
ix = [l.strip() for l in open(os.path.join(OUT, 'Index'), 'rb').read().decode('latin1').replace('\r', '').split('\n')]
for p in MAN['new_packs']:
    if p not in ix:
        fail.append('pack %s is not in Index' % p)
    if not os.path.exists(os.path.join(OUT, p + '.index')):
        fail.append('pack %s is not in OUT' % p)
for e in [e for p in MAN['packs'].values() for e in p]:
    if e['name'] not in CONTENT:
        fail.append('staged %s is in no pack of OUT' % e['name'])


def need(k, why):
    if k not in NAMES:
        known = k in KNOWN or ':/' in k[3:]          # a developer's path inside a GF file (horse_stop.msa)
        (notes if known else fail).append('%s  (%s)' % (k, why))
        return False
    return True


def text(k):
    return CONTENT[k].decode('latin1') if k in CONTENT else None


props = {}
for k, b in CONTENT.items():
    if k.startswith('property/'):
        l = b.replace(b'\r', b'').split(b'\n')
        if l and l[0].strip() == b'YPRT':
            props[int(l[1].strip())] = k
nobj = 0
nomdatr = set()      # GF ships no .mdatr for them either: no client collision (the server's server_attr still blocks)
for idx, MAP, size, basepos in MAPS:
    mp = 'maps/%s/' % MAP
    # 1) the map folder
    for k in ('setting.txt', 'mapproperty.txt'):
        need(mp + k, 'map %d' % idx)
    st = text(mp + 'setting.txt') or ''
    w, h = [int(x) for x in re.search(r'MapSize\s+(\d+)\s+(\d+)', st).groups()]
    assert (w, h) == size and re.search(r'BasePosition\s+%d\s+%d' % basepos, st), st
    vr = int(re.search(r'ViewRadius\s+(\d+)', st).group(1))
    if vr != 128:
        fail.append('%s setting.txt ViewRadius %d (ours: 128)' % (MAP, vr))
    SECT = ('areadata.txt', 'areaproperty.txt', 'areaambiencedata.txt', 'attr.atr', 'height.raw', 'tile.raw',
            'water.wtr', 'minimap.dds', 'shadowmap.dds', 'shadowmap.raw')
    for x in range(w):
        for y in range(h):
            for f in SECT:
                need('%s%03d%03d/%s' % (mp, x, y, f), 'sector')
    # 2) textureset
    ts = norm(re.search(r'TextureSet\s+(\S+)', st, re.I).group(1))
    need(ts, mp + 'setting.txt')
    for t in re.findall(r'"([^"]+\.dds)"', text(ts) or '', re.I):
        need(norm(t), ts)
    # 3) msenv
    env = norm(re.search(r'Environment\s+(\S+)', st, re.I).group(1))
    for k in (mp + env, 'd:/ymir work/environment/' + env):
        if need(k, mp + 'setting.txt') and k in CONTENT:
            et = text(k)
            if not (re.search(r'(?im)^\s*NearDistance', et) and re.search(r'(?im)^\s*FarDistance', et)) \
                    or re.search(r'(?im)^\s*foglevel', et):
                fail.append('%s: fog not as exe 2.0.25 reads it' % k)
            for t in re.findall(r'"([^"]+\.dds)"', et, re.I):
                need(norm(t), k)
    # 4) atlas
    sub = 'd:/ymir work/ui/atlas/%s/atlas.sub' % MAP
    if MAP not in NO_ATLAS and need(sub, 'atlas'):
        img = re.search(r'image\s+"([^"]+)"', text(sub) or '').group(1)
        need('d:/ymir work/ui/' + norm(img), sub)
    # 5) the objects
    for x in range(w):
        for y in range(h):
            a = text('%s%03d%03d/areadata.txt' % (mp, x, y)) or ''
            bodies = re.findall(r'Start Object\d+\r?\n(.*?)End Object', a, re.S)
            cnt = re.search(r'ObjectCount\s+(\d+)', a)
            assert cnt is None or int(cnt.group(1)) == len(bodies), (MAP, x, y)
            for body in bodies:
                nobj += 1
                crc = int(body.replace('\r', '').split('\n')[1].strip().split('#')[0])
                if crc not in props:
                    fail.append('%s: object CRC %d of sector %03d%03d: no property in pack property' % (MAP, crc, x, y))
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
# the OUT's own npclist (patch_ymaps3_client.npclist adds 10125) over the listing's
for l in (CONTENT.get('gamedata/npclist.txt') or b'').decode('latin1').splitlines():
    t = l.split()
    if len(t) >= 2 and t[0].isdigit():
        npc[int(t[0])] = t[1].lower()
for v in sorted(int(x) for x in MAN['races']):
    if v not in npc:
        fail.append('race %d: no npclist row' % v)
        continue
    name = npc[v]
    folder = alias.get(name, name)
    cands = ['d:/ymir work/%s/%s/%s.msm' % (d, folder, name) for d in RACE_DIRS]
    if not any(c in NAMES for c in cands):
        notes.append('race %d %s: no .msm in our listing - the base client (npc/monster packs, no listing) must have it'
                     % (v, name))
RE_Q = re.compile(r'"([^"\r\n]+\.(?:gr2|dds|tga|mse|msa|msm|mss|wav|mp3|txt|msenv|mde|spt|mdatr))"', re.I)
staged = set(e['name'] for p in MAN['packs'].values() for e in p)
for k in staged:
    if not k.endswith(('.msm', '.msa', '.mse', '.mss', '.prb', '.prd', '.pre', '.prt', '.msenv')) or k.startswith('property/'):
        continue
    t = CONTENT[k].decode('latin1')
    d = k.rsplit('/', 1)[0] + '/'
    for r in RE_Q.findall(t):
        r = norm(r)
        if not (r.startswith('d:/') or r.startswith(('sound/', 'textureset/', 'property/'))):
            r = 'd:/' + r if r.startswith('ymir work/') else d + r
        need(r, k)

# 7) gamedata/dbdata: every row and item of this batch (a second patch must change nothing)
for n, fn in (('gamedata/mob_proto', pc.mob_proto), ('gamedata/atlasinfo.txt', pc.atlasinfo),
              ('gamedata/npclist.txt', pc.npclist), ('gamedata/item_list.txt', pc.item_list),
              ('gamedata/item_proto', pc.item_proto), ('locale/pl/itemdesc.txt', pc.itemdesc)):
    if n not in CONTENT:
        fail.append('%s not in OUT' % n)
        continue
    try:
        nb, added = fn(CONTENT[n])
        if added:
            fail.append('%s: %d row(s) missing' % (n, added))
    except pc.Collision as e:
        fail.append(str(e))

print('objects checked: %d, properties in pack: %d, names known: %d' % (nobj, len(props), len(NAMES)))
print('Building/DungeonBlock models without .mdatr (none in GF either): %d' % len(nomdatr))
print('notes (%d):' % len(set(notes)))
for n in sorted(set(notes)):
    print('  ' + n)
print('FAIL (%d):' % len(set(fail)))
for f in sorted(set(fail)):
    print('  ' + f)
sys.exit(1 if fail else 0)
