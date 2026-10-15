# -*- coding: utf-8 -*-
# MT2009_PLUS_YOHARA_MELEY_V1 - checks the packs build_ymeley_packs.py wrote: everything Schronienie Meley (356) names
# resolves to a name of the client (the OUT packs + the BASE listing c58.lst + the base client's pre-import listing):
# the map folder (setting.txt with its size and OUR base 281600 1510400, ViewRadius 128, mapproperty.txt without a
# ParentMapName, the msenv; every sector's files), the textureset and its textures, the msenv (fog as exe 2.0.25 reads
# it), the atlas, every object of the sector (areadata CRC -> property -> model/effect/tree, .mdatr), every race of
# spawned.txt (npclist -> .msm) and every name the staged text files give; the new packs under the 29 MB limit and in
# Index; the atlasinfo: the lair's row overlapping no other row; the items' icons; gamedata/dbdata: the 13 mob_proto
# rows of yohara_meley.sql, the atlasinfo row, the 3 items (a second patch must change nothing).
# Run in the m2pack-lzo image, on the OUT the whole chain (cape301 ... yzaklety, ymeley) was built into:
#   docker run --rm -v /opt/metin2:/opt/metin2 m2pack-lzo python3 <repo>/client-patches/client-2.0.30/tools/ymeley/verify_ymeley.py \
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
import patch_ymeley_client as pc  # noqa: E402

args = [a for a in sys.argv[1:] if not a.startswith('--')]
OUT = args[0]
WORK = args[1] if len(args) > 1 else '/opt/metin2/cache/yohara/cape301-work'
NPCLIST = args[2] if len(args) > 2 else '/opt/metin2/cache/c61/chk/gamedata/npclist.txt'
PRE_LST = '/opt/metin2/cache/tcm/gf28/ourpacks_pre.txt'
ZIP_LIMIT = 29 * 1024 * 1024
MAN = json.load(open(os.path.join(HERE, 'ymeley_manifest.json'), encoding='utf-8'))
MAPS = [(356, 'metin2_map_n_flame_dragon', (1, 1), (281600, 1510400))]
# the maps GF has no atlas picture for (the manifest's atlas_image)
NO_ATLAS = tuple(m['folder'] for m in MAN['maps'].values() if not m['atlas_image'])
EXTRA = []
ICONS = os.path.join(HERE, '..', '..', 'root', 'icon', 'item')
RACE_DIRS = ('guild', 'npc', 'npc2', 'npc_pet', 'npc_mount', 'monster', 'monster2')
# GF's own broken references (the official client has the same; Ameria too): reported, not failed
KNOWN = {'d:/ymir work/effect/monster2/redd_smorke.mse',                     # Meley's special attack names it
         'd:/ymir work/monster2/reddragon_room_boss2/normal_attack.msa',     # her motlist; she never moves to attack
         'd:/ymir work/npc/old_magic_m/old_magic_m.dds'}                     # Dolnarr's model's texture name


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
    if (w, h) != size or not re.search(r'BasePosition\s+%d\s+%d' % basepos, st):
        fail.append('%s setting.txt: size/base not %s %s' % (MAP, size, basepos))
    if 'ParentMapName' in (text(mp + 'mapproperty.txt') or ''):
        fail.append('%s mapproperty.txt: a ParentMapName (our exe cannot read a copied map)' % MAP)
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
# the OUT's own npclist (patch_ymeley_client.npclist: nothing new) over the listing's
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

# the atlasinfo: the lair's row overlaps no other map (an overlap crashes or confuses the client - bledy-3.0.md 8)
if 'gamedata/atlasinfo.txt' in CONTENT:
    rects = []
    for l in CONTENT['gamedata/atlasinfo.txt'].decode('cp1250').splitlines():
        t = l.split()
        if len(t) >= 5 and t[1].isdigit():
            rects.append((t[0].lower(), int(t[1]), int(t[2]), int(t[3]) * 25600, int(t[4]) * 25600))
    mine = [r for r in rects if r[0] == MAPS[0][1]]
    if len(mine) != 1:
        fail.append('atlasinfo: %d rows of %s' % (len(mine), MAPS[0][1]))
    for n, x, y, w, h in mine:
        if (x, y) != MAPS[0][3]:
            fail.append('atlasinfo: %s at %d %d' % (n, x, y))
        for n2, x2, y2, w2, h2 in rects:
            if n2 != n and x < x2 + w2 and x2 < x + w and y < y2 + h2 and y2 < y + h:
                fail.append('atlasinfo: %s overlaps %s' % (n, n2))
    print('atlasinfo rows: %d, overlaps of %s: %d' % (len(rects), MAPS[0][1], sum(1 for f in fail if 'overlaps' in f)))

# the items' icons (client-2.0.30/root's icon/item, or the icon pack: the chests' 50270.tga / 50271.tga)
for it in pc.items_json()['items']:
    icon = pc.items_json()['item_list'][str(it['vnum'])].split('\t')[2]
    if not os.path.isfile(os.path.join(ICONS, os.path.basename(icon))) and norm(icon) not in NAMES:
        fail.append('icon %s of %d not in client-2.0.30/root/icon/item nor in the client' % (icon, it['vnum']))

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
