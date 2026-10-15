# -*- coding: utf-8 -*-
# MT2009_PLUS_HELM100_V1 - checks the packs build_yhelm100_packs.py wrote (on the OUT of the whole Yohara chain):
#   the 84 items of tools/yhelm100/yhelm100_items.json: an item_proto record (dbdata) equal to the server's row
#   (yitem_record over a helmet / material template), an item_list line whose icon is in the repo's root/icon/item or
#   a pack, an itemdesc line; Jaharr 20421: his mob_proto record (gamedata) equal to the server's row, his npclist rows
#   (20421 old_magic_M2, 0 old_magic_M2 old_magic_M), the race's .msm d:/ymir work/npc/old_magic_m/old_magic_m2.msm with
#   the files it names (model, skin, motlist and motions) in a pack, and the yhelm100 pack in pack/Index.
#   docker run --rm -v /opt/metin2:/opt/metin2 m2pack-lzo python3 <repo>/client-patches/client-2.0.30/tools/yhelm100/verify_yhelm100.py \
#     <OUT pack dir> [<BASE pack dir>]
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, '/opt/metin2/cache/tcm/tz')
sys.path.insert(0, '/opt/metin2/cache/arezzo-work/client/az58')
sys.path.insert(0, HERE)
import m2pack  # noqa: E402
import packlib  # noqa: E402
import patch_yhelm100_client as pc  # noqa: E402

args = [a for a in sys.argv[1:] if not a.startswith('--')]
OUT = args[0]
BASE = args[1] if len(args) > 1 else '/opt/metin2/cache/cY/azbase'
ROOT_ICONS = os.path.normpath(os.path.join(HERE, '..', '..', 'root', 'icon', 'item'))
MODEL = 'd:/ymir work/npc/old_magic_m/'
fails = []
WHERE = {}
for _d in (BASE, OUT):          # OUT last: a pack there is the one the client gets
    for _f in os.listdir(_d):
        if _f.endswith('.index'):
            for e in m2pack.read_index(os.path.join(_d, _f))[2]:
                WHERE[e['name']] = (_d, _f[:-6])


def entry(pack, name):
    d = OUT if os.path.exists(os.path.join(OUT, pack + '.index')) else BASE
    f, v, ents = m2pack.read_index(os.path.join(d, pack + '.index'))
    dat = packlib.rd(os.path.join(d, pack + '.data'))
    for e in ents:
        if e['name'] == name:
            return m2pack.read_entry(dat, e)
    return None


def any_entry(name):
    if name not in WHERE:
        return None
    d, p = WHERE[name]
    f, v, ents = m2pack.read_index(os.path.join(d, p + '.index'))
    dat = packlib.rd(os.path.join(d, p + '.data'))
    for e in ents:
        if e['name'] == name:
            return m2pack.read_entry(dat, e)
    return None


d = pc.items_json()
ver, recs = pc.records(entry('dbdata', 'gamedata/item_proto'))
for v, r in sorted(pc.want_records(recs).items()):
    if recs.get(v) != r:
        fails.append('item_proto %d: not the server\'s record' % v)
lst = entry('gamedata', 'gamedata/item_list.txt').decode('cp1250').replace('\r\n', '\n').split('\n')
lst = dict((l.split('\t')[0].strip(), l) for l in lst if l.strip())
desc = entry('dbdata', 'locale/pl/itemdesc.txt').decode('cp1250').replace('\r\n', '\n').split('\n')
desc = dict((l.split('\t')[0].strip(), l) for l in desc if l.strip())
for k, line in d['item_list'].items():
    if lst.get(k, '').split() != line.split():
        fails.append('item_list %s: missing or other' % k)
    icon = line.split('\t')[2]
    if not os.path.isfile(os.path.join(ROOT_ICONS, os.path.basename(icon))) and icon not in WHERE:
        fails.append('item_list %s: icon %s not in root/icon/item nor in a pack' % (k, icon))
for k, line in d['itemdesc'].items():
    if desc.get(k) != line:
        fails.append('itemdesc %s: missing or other' % k)
mobs = pc.mob_recs(entry('gamedata', 'gamedata/mob_proto'))
for v, r in pc.want_mobs(mobs).items():
    if mobs.get(v) != r:
        fails.append('mob_proto %d: not the server\'s row' % v)
npcl = entry('gamedata', 'gamedata/npclist.txt')
if pc.npclist(npcl)[1]:
    fails.append('npclist: a row of %s missing' % pc.NPCLIST)
msm = MODEL + 'old_magic_m2.msm'
b = any_entry(msm)
if b is None:
    fails.append('%s: in no pack' % msm)
else:
    t = b.decode('latin-1')
    names = [MODEL + x.lower() for x in re.findall(r'"([^"\\/]+\.(?:gr2|dds))"', t, re.I)]
    names += [MODEL + 'motlist.txt']
    mot = any_entry(MODEL + 'motlist.txt')
    if mot:
        names += [MODEL + l.split()[2].lower() for l in mot.decode('latin-1').splitlines() if len(l.split()) >= 3]
    for n in names:
        if n not in WHERE:
            fails.append('%s: named by the race, in no pack' % n)
ix = open(os.path.join(OUT, 'Index'), 'rb').read() if os.path.exists(os.path.join(OUT, 'Index')) else b''
if os.path.exists(os.path.join(OUT, 'yhelm100.index')) and b'yhelm100' not in ix.split():
    fails.append('pack/Index: no yhelm100 line')
print('yhelm100: %d items, Jaharr, %d problem(s)' % (len(d['items']), len(fails)))
for f in fails:
    print('  ' + f)
sys.exit(1 if fails else 0)
