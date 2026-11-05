# -*- coding: utf-8 -*-
# MT2009_PLUS_GLOVES_V1 - checks the packs build_ygloves_packs.py wrote (on the OUT of the whole Yohara chain):
#   the 50 items of tools/ygloves/ygloves_items.json: an item_proto record (dbdata) equal to the server's row
#   (yitem_record over an armour / spirit stone template), an item_list line whose icon is in the repo's
#   root/icon/item or a pack, an itemdesc line without "(Na razie bez zastosowania".
#   docker run --rm -v /opt/metin2:/opt/metin2 m2pack-lzo python3 <repo>/client-patches/client-2.0.30/tools/ygloves/verify_ygloves.py \
#     <OUT pack dir> [<BASE pack dir>]
import os
import struct
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, '/opt/metin2/cache/tcm/tz')
sys.path.insert(0, '/opt/metin2/cache/arezzo-work/client/az58')
sys.path.insert(0, HERE)
import m2pack  # noqa: E402
import packlib  # noqa: E402
import patch_ygloves_client as pc  # noqa: E402

args = [a for a in sys.argv[1:] if not a.startswith('--')]
OUT = args[0]
BASE = args[1] if len(args) > 1 else '/opt/metin2/cache/cY/azbase'
ROOT_ICONS = os.path.normpath(os.path.join(HERE, '..', '..', 'root', 'icon', 'item'))
fails = []
PACK_NAMES = set()
for _d in (OUT, BASE):
    for _f in os.listdir(_d):
        if _f.endswith('.index'):
            PACK_NAMES.update(e['name'] for e in m2pack.read_index(os.path.join(_d, _f))[2])


def entry(pack, name):
    d = OUT if os.path.exists(os.path.join(OUT, pack + '.index')) else BASE
    f, v, ents = m2pack.read_index(os.path.join(d, pack + '.index'))
    dat = packlib.rd(os.path.join(d, pack + '.data'))
    for e in ents:
        if e['name'] == name:
            return m2pack.read_entry(dat, e)
    return None


# MT2009_PLUS_VERIFY_LATER_WRITERS_V1: refineglobal (a later step, the server's refine_global.sql the same) sets each
# item's refined_vnum / refine_set (record offset 175, 6 bytes) as on the global server - compared without them
REFINE = slice(175, 181)


def _norefine(r):
    return None if r is None else bytes(r[:REFINE.start]) + bytes(r[REFINE.stop:])


d = pc.items_json()
ver, recs = pc.records(entry('dbdata', 'gamedata/item_proto'))
want = pc.want_records(recs)
refined = 0
for v, r in sorted(want.items()):
    if recs.get(v) != r and _norefine(recs.get(v)) == _norefine(r):
        refined += 1
    elif recs.get(v) != r:
        fails.append('item_proto %d: not the server\'s record' % v)
lst = entry('gamedata', 'gamedata/item_list.txt').decode('cp1250').replace('\r\n', '\n').split('\n')
lst = dict((l.split('\t')[0].strip(), l) for l in lst if l.strip())
desc = entry('dbdata', 'locale/pl/itemdesc.txt').decode('cp1250').replace('\r\n', '\n').split('\n')
desc = dict((l.split('\t')[0].strip(), l) for l in desc if l.strip())
for k, line in d['item_list'].items():
    if lst.get(k, '').split() != line.split():
        fails.append('item_list %s: missing or other' % k)
    icon = line.split('\t')[2]
    if not os.path.isfile(os.path.join(ROOT_ICONS, os.path.basename(icon))) and icon not in PACK_NAMES:
        fails.append('item_list %s: icon %s not in root/icon/item nor in a pack' % (k, icon))
for k, line in d['itemdesc'].items():
    if desc.get(k) != line:
        fails.append('itemdesc %s: missing or other' % k)
for k in d['itemdesc']:
    if 'Na razie bez zastosowania' in desc.get(k, ''):
        fails.append('itemdesc %s: still "Na razie bez zastosowania"' % k)
print('ygloves: %d items, %d problem(s)' % (len(d['items']), len(fails)))
if refined:
    print('  note: %d item(s) with the refine step of refineglobal (global values, a later step)' % refined)
for f in fails:
    print('  ' + f)
sys.exit(1 if fails else 0)
