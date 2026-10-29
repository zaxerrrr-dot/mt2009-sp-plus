# -*- coding: utf-8 -*-
# MT2009_PLUS_WEAPON_ELEMENT_V1 - checks the packs build_zywiolbroni_packs.py wrote (on the OUT of the whole Yohara
# chain): the pack "zywiolbroni" in Index; every effect element0x_*.mse the exe draws (welemfx.py) and every texture
# it names is in a pack (the new one or ours); the change window's buttons (uiscript/weaponelementchange.py) and their
# image; the scrolls of tools/zywiolbroni/zywiolbroni_items.json: an item_proto record (dbdata) equal to the server's
# row (yitem_record over 71084), an item_list line whose icon is in the repo's root/icon/item, an itemdesc line;
# Stróż Medali 20650 in mob_proto (gamedata, on_click 1) and npclist.txt; the root files present.
#   docker run --rm -v /opt/metin2:/opt/metin2 m2pack-lzo python3 \
#     <repo>/client-patches/client-2.0.30/tools/zywiolbroni/verify_zywiolbroni.py <OUT pack dir> [<BASE pack dir>]
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, '/opt/metin2/cache/tcm/tz')
sys.path.insert(0, '/opt/metin2/cache/arezzo-work/client/az58')
sys.path.insert(0, '/opt/metin2/cache/tcm/gf28')
sys.path.insert(0, HERE)
import m2pack  # noqa: E402
import packlib  # noqa: E402
import build_zywiolbroni_packs as bp  # noqa: E402
import patch_zywiolbroni_client as pc  # noqa: E402

args = [a for a in sys.argv[1:] if not a.startswith('--')]
OUT = args[0]
BASE = args[1] if len(args) > 1 else '/opt/metin2/cache/cY/azbase'
ROOT = os.path.normpath(os.path.join(HERE, '..', '..', 'root'))
ROOT_ICONS = os.path.join(ROOT, 'icon', 'item')
fails = []


def entry(pack, name):
    d = OUT if os.path.exists(os.path.join(OUT, pack + '.index')) else BASE
    if not os.path.exists(os.path.join(d, pack + '.index')):
        return None
    f, v, ents = m2pack.read_index(os.path.join(d, pack + '.index'))
    dat = packlib.rd(os.path.join(d, pack + '.data'))
    for e in ents:
        if e['name'] == name:
            return m2pack.read_entry(dat, e)
    return None


def rows(b):
    t = b.decode('cp1250').replace('\r\n', '\n').split('\n')
    return dict((l.split('\t')[0].strip(), l) for l in t if l.strip())


# 1) the pack and Index
ix_path = os.path.join(OUT, 'Index') if os.path.exists(os.path.join(OUT, 'Index')) else os.path.join(BASE, 'Index')
ix = [l.strip() for l in packlib.rd(ix_path).replace(b'\r\n', b'\n').split(b'\n')]
if bp.PACK.encode() not in ix:
    fails.append('Index: no line %s' % bp.PACK)
want, kept = bp.files(BASE, OUT)
for name, b in sorted(want.items()):
    if entry(bp.PACK, name) != b:
        fails.append('%s: %s missing or other' % (bp.PACK, name))
ours = set(bp.our_names(BASE, OUT))
import gfres  # noqa: E402
ours |= gfres.load_ours(bp.OURS_PRE)
for k in bp.EFFECTS:
    if k not in want and k not in ours:
        fails.append('effect %s in no pack' % k)
    src = gfres.GF.get(k)
    for r in (gfres.refs_of(k, src) if src else ()):
        if r not in want and r not in ours:
            fails.append('%s: %s in no pack' % (k, r))
for k in bp.MODEL:
    if k not in want and k not in ours:
        fails.append('model %s in no pack' % k)
    src = gfres.GF.get(k)
    for r in (gfres.refs_of(k, src) if src else ()):
        if r not in want and r not in ours:
            fails.append('%s: %s in no pack' % (k, r))
for n in bp.UI_SUBS:
    k = bp.UI_DIR + n + '.sub'
    sub = want.get(k) or b''
    if k in want and not re.search(br'image\s+"welem_event_001\.dds"', sub):
        fails.append('%s does not name welem_event_001.dds' % k)
if bp.UI_DDS not in want and bp.UI_DDS not in ours:
    fails.append('%s in no pack' % bp.UI_DDS)
script = open(os.path.join(ROOT, 'uiscript', 'weaponelementchange.py')).read()
for n in bp.UI_SUBS[:4]:
    if (bp.UI_DIR + n + '.sub') not in script:
        fails.append('uiscript/weaponelementchange.py does not name %s' % n)

# 2) the scrolls
d = pc.items_json()
ver, recs = pc.records(entry('dbdata', 'gamedata/item_proto'))
for v, r in sorted(pc.want_records(recs).items()):
    if recs.get(v) != r:
        fails.append("item_proto %d: not the server's record" % v)
lst = rows(entry('gamedata', 'gamedata/item_list.txt'))
desc = rows(entry('dbdata', 'locale/pl/itemdesc.txt'))
for k, line in d['item_list'].items():
    if lst.get(k, '').split() != line.split():
        fails.append('item_list %s: missing or other' % k)
    icon = line.split('\t')[2]
    if not os.path.isfile(os.path.join(ROOT_ICONS, os.path.basename(icon))):
        fails.append('item_list %s: icon %s not in root/icon/item' % (k, icon))
for k, line in d['itemdesc'].items():
    if desc.get(k) != line:
        fails.append('itemdesc %s: missing or other' % k)

# 3) Stróż Medali
mobs = pc.mob_records(entry('gamedata', 'gamedata/mob_proto'))
v, r = pc.want_mob(mobs)
if mobs.get(v) != r:
    fails.append('mob_proto %d: missing or other' % v)
npcl = (entry('gamedata', 'gamedata/npclist.txt') or b'').decode('cp1250', 'replace').replace('\r\n', '\n').split('\n')
if not any(l.split() == [str(v), d['npc']['npclist']] for l in npcl):
    fails.append('npclist.txt: no line "%d %s"' % (v, d['npc']['npclist']))

# 4) root
for f in ('welem.py', 'uiweaponelement.py', 'uiscript/weaponelementdialog.py', 'uiscript/weaponelementchange.py'):
    if not os.path.isfile(os.path.join(ROOT, f)):
        fails.append('root/%s missing' % f)
print('zywiolbroni: %d pack files (%d kept ours), %d items, %d problem(s)' % (len(want), len(kept), len(d['items']),
                                                                              len(fails)))
for f in fails:
    print('  ' + f)
sys.exit(1 if fails else 0)
