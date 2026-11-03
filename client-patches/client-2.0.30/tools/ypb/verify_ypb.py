# -*- coding: utf-8 -*-
# MT2009_PLUS_YOHARA_PB_V1 - checks the packs build_ypb_packs.py wrote: everything the awakened bosses' maps (369
# Twierdza Czerwonego Smoka (PB), 370 Straznica Nemere (PB)) and the villages' statues name resolves to a name of the
# client (the OUT packs + the BASE listing c58.lst + the base client's pre-import listing): each copied map folder
# (setting.txt with its size / official base, mapproperty.txt with ParentMapName) and its PARENT (our 351/352 folder:
# setting.txt, every sector's files, the msenv, the textureset and its textures), the fortress' atlas picture, every
# race of spawned.txt (npclist -> .msm) and every name the staged text files give, the items' icons in
# client-2.0.30/root/icon/item; the new packs under the 29 MB limit and in Index; gamedata/dbdata: the 34 mob_proto
# rows of yohara_pb.sql, the two atlasinfo rows, the 23 items (a second patch must change nothing).
# Run in the m2pack-lzo image, on the OUT the whole chain (cape301 ... ydung4, ypb) was built into:
#   docker run --rm -v /opt/metin2:/opt/metin2 m2pack-lzo python3 <repo>/client-patches/client-2.0.30/tools/ypb/verify_ypb.py \
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
import patch_ypb_client as pc  # noqa: E402

args = [a for a in sys.argv[1:] if not a.startswith('--')]
OUT = args[0]
WORK = args[1] if len(args) > 1 else '/opt/metin2/cache/yohara/cape301-work'
NPCLIST = args[2] if len(args) > 2 else '/opt/metin2/cache/c61/chk/gamedata/npclist.txt'
PRE_LST = '/opt/metin2/cache/tcm/gf28/ourpacks_pre.txt'
ICONS = os.path.join(HERE, '..', '..', 'root', 'icon', 'item')
ZIP_LIMIT = 29 * 1024 * 1024
MAN = json.load(open(os.path.join(HERE, 'ypb_manifest.json'), encoding='utf-8'))
MAPS = [(369, 'metin2_map_boss_awaken_flame', 'metin2_map_n_flame_dungeon_01', (3, 3), (153600, 1971200)),
        (370, 'metin2_map_boss_awaken_snow', 'metin2_map_n_snow_dungeon_01', (4, 3), (230400, 1971200))]
RACE_DIRS = ('guild', 'npc', 'npc2', 'npc_pet', 'npc_mount', 'monster', 'monster2')
# GF's own broken references (the official client has the same): reported, not failed - the effect meshes our normal
# Razador / Nemere races' effects (gf_razador, gf_nemere: impact7.mse ...) already name, and two textures of GF's
# icegolem_boss_awake.msm with 8.3 names
KNOWN = {'d:/ymir work/effect/monster2/impact9.mde', 'd:/ymir work/effect/monster2/impact7.mde',
         'd:/ymir work/effect/monster2/impact10_red.mde', 'd:/ymir work/effect/monster2/mash_spell1.mde',
         'd:/ymir work/monster2/icegolem_boss_awake/_04_~1.dds', 'd:/ymir work/monster2/icegolem_boss_awake/_07_~1.dds'}


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
        (notes if k in KNOWN else fail).append('%s  (%s)' % (k, why))
        return False
    return True


def text(k):
    return CONTENT[k].decode('latin1') if k in CONTENT else None


for idx, MAP, PARENT, size, basepos in MAPS:
    mp = 'maps/%s/' % MAP
    for k in ('setting.txt', 'mapproperty.txt'):
        need(mp + k, 'map %d' % idx)
    st = text(mp + 'setting.txt') or ''
    w, h = [int(x) for x in re.search(r'MapSize\s+(\d+)\s+(\d+)', st).groups()]
    if (w, h) != size or not re.search(r'BasePosition\s+%d\s+%d' % basepos, st):
        fail.append('%s setting.txt: size/base %s' % (MAP, st[:80]))
    prop = text(mp + 'mapproperty.txt') or ''
    # MT2009_PLUS_COPIED_MAPS_V1 (../ycopymaps, 3.0.7: 369/370 too): the parent's sectors and environment are in the
    # map's own folder now - our exe reads a ParentMapName without "maps/" (LoadSetting failed, no terrain, no
    # environment: syserr "mc_pEnvironmentData is NULL" every frame); before that step the parent's folder is checked.
    if re.search(r'ParentMapName\s+"%s"' % PARENT, prop):
        pp = 'maps/%s/' % PARENT
        need(pp + 'setting.txt', 'parent of %s' % MAP)
        need(pp + 'mapproperty.txt', 'parent of %s' % MAP)
    elif 'ParentMapName' in prop:
        fail.append('%s mapproperty.txt: a ParentMapName other than "%s"' % (MAP, PARENT))
        pp = mp
    else:
        pp = mp
    for x in range(w):
        for y in range(h):
            for f in ('areadata.txt', 'areaproperty.txt', 'attr.atr', 'height.raw', 'tile.raw', 'water.wtr',
                      'minimap.dds', 'shadowmap.dds', 'shadowmap.raw'):
                need('%s%03d%03d/%s' % (pp, x, y, f), 'sector of the parent %s' % PARENT)
    ts = norm(re.search(r'TextureSet\s+(\S+)', st, re.I).group(1))
    need(ts, mp + 'setting.txt')
    env = norm(re.search(r'Environment\s+(\S+)', st, re.I).group(1))
    need(pp + env, mp + 'setting.txt (the parent\'s folder)')
    sub = 'd:/ymir work/ui/atlas/%s/atlas.sub' % MAP
    am = MAN['maps'][str(idx)]['atlas_image']
    if am:
        if need(sub, 'atlas'):
            img = re.search(r'image\s+"([^"]+)"', text(sub) or '').group(1)
            need('d:/ymir work/ui/' + norm(img), sub)

# the races, and everything the staged text files name
npc, alias = {}, {}
for l in open(NPCLIST, encoding='latin1'):
    t = l.split()
    if len(t) >= 3 and t[0] == '0':
        alias[t[1].lower()] = t[2].lower()
    elif len(t) >= 2 and t[0].isdigit():
        npc[int(t[0])] = t[1].lower()
for v in sorted(int(x) for x in MAN['races']):
    if v not in npc:
        fail.append('race %d: no npclist row' % v)
        continue
    name = npc[v]
    folder = alias.get(name, name)
    cands = ['d:/ymir work/%s/%s/%s.msm' % (d, folder, name) for d in RACE_DIRS]
    if not any(c in NAMES for c in cands):
        fail.append('race %d %s: no .msm' % (v, name))
RE_Q = re.compile(r'"([^"\r\n]+\.(?:gr2|dds|tga|mse|msa|msm|mss|wav|mp3|txt|msenv|mde|spt|mdatr))"', re.I)
staged = set(e['name'] for p in MAN['packs'].values() for e in p)
for k in staged:
    if not k.endswith(('.msm', '.msa', '.mse', '.mss', '.msenv', '.txt')):
        continue
    t = CONTENT[k].decode('latin1')
    d = k.rsplit('/', 1)[0] + '/'
    for r in RE_Q.findall(t):
        r = norm(r)
        if not (r.startswith('d:/') or r.startswith(('sound/', 'textureset/', 'property/'))):
            r = 'd:/' + r if r.startswith('ymir work/') else d + r
        need(r, k)

# the items' icons (the root pack carries client-2.0.30/root)
for it in pc.items_json()['items']:
    line = pc.items_json()['item_list'][str(it['vnum'])]
    icon = line.split('\t')[2]
    if not os.path.isfile(os.path.join(ICONS, os.path.basename(icon))):
        fail.append('icon %s of %d not in client-2.0.30/root/icon/item' % (icon, it['vnum']))

# gamedata/dbdata: every row and item of this batch (a second patch must change nothing)
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

print('names known: %d, races: %d, staged: %d' % (len(NAMES), len(MAN['races']), len(staged)))
print('notes (%d):' % len(set(notes)))
for n in sorted(set(notes)):
    print('  ' + n)
print('FAIL (%d):' % len(set(fail)))
for f in sorted(set(fail)):
    print('  ' + f)
sys.exit(1 if fail else 0)
