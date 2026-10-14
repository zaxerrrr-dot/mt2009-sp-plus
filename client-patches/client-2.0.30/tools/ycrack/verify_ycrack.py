# -*- coding: utf-8 -*-
# MT2009_PLUS_YOHARA_CRACK_V1 - checks the packs build_ycrack_packs.py wrote: everything Zaklety Las (SZC) (404) names
# resolves to a name of the client (the OUT packs + the BASE listing c58.lst + the base client's pre-import listing):
# the copied map folder (setting.txt with its size / official base, mapproperty.txt with ParentMapName = our
# metin2_map_boss_awaken_dawnmist) and its PARENT (../yiluzja's full folder: setting.txt, every sector's files, the
# msenv, the textureset), the atlas picture, every race of spawned.txt (npclist -> .msm; Statua Szczeliny Czasu
# 20472 on the plateau too) and every name the staged text files give, the items' icons in client-2.0.30/root/icon/item;
# the new packs under the 29 MB limit and in Index; no atlasinfo row overlapping another; gamedata/dbdata: the 19
# mob_proto rows of yohara_crack.sql, the atlasinfo row, the 6 items (a second patch must change nothing).
# Run in the m2pack-lzo image, on the OUT the whole chain (cape301 ... ypb, yiluzja, ycrack) was built into:
#   docker run --rm -v /opt/metin2:/opt/metin2 m2pack-lzo python3 <repo>/client-patches/client-2.0.30/tools/ycrack/verify_ycrack.py \
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
import patch_ycrack_client as pc  # noqa: E402

args = [a for a in sys.argv[1:] if not a.startswith('--')]
OUT = args[0]
WORK = args[1] if len(args) > 1 else '/opt/metin2/cache/yohara/cape301-work'
NPCLIST = args[2] if len(args) > 2 else '/opt/metin2/cache/c61/chk/gamedata/npclist.txt'
PRE_LST = '/opt/metin2/cache/tcm/gf28/ourpacks_pre.txt'
ICONS = os.path.join(HERE, '..', '..', 'root', 'icon', 'item')
ZIP_LIMIT = 29 * 1024 * 1024
MAN = json.load(open(os.path.join(HERE, 'ycrack_manifest.json'), encoding='utf-8'))
MAPS = [(404, 'metin2_map_boss_crack_dawnmist', 'metin2_map_boss_awaken_dawnmist', (3, 4), (332800, 1817600))]
RACE_DIRS = ('guild', 'npc', 'npc2', 'npc_pet', 'npc_mount', 'monster', 'monster2')
# GF's own broken reference (the official client has the same; ../ypb lists it too): Jotun Thrym's thunder_boss names
# an effect mesh GF keeps only in an encrypted blob - the effect is not drawn, the race is
KNOWN = {'d:/ymir work/effect/monster2/impact10_red.mde'}


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
    if not re.search(r'ParentMapName\s+"%s"' % PARENT, prop):
        fail.append('%s mapproperty.txt: no ParentMapName "%s"' % (MAP, PARENT))
    # the parent: the exe reads Setting.txt, the sectors and the environment from its folder
    pp = 'maps/%s/' % PARENT
    need(pp + 'setting.txt', 'parent of %s' % MAP)
    need(pp + 'mapproperty.txt', 'parent of %s' % MAP)
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

# the atlasinfo: no two maps' rectangles overlap (an overlap crashes or confuses the client - cache/yohara/bledy-3.0.md 8)
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
        for n2, x2, y2, w2, h2 in rects:
            if n2 != n and x < x2 + w2 and x2 < x + w and y < y2 + h2 and y2 < y + h:
                fail.append('atlasinfo: %s overlaps %s' % (n, n2))
    print('atlasinfo rows: %d, overlaps of %s: %d' % (len(rects), MAPS[0][1], sum(1 for f in fail if 'overlaps' in f)))

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
