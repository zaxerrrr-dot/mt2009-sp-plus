# -*- coding: utf-8 -*-
# MT2009_PLUS_BIOLOGIST_YOHARA_V1 - checks the packs build_ybiolog_packs.py wrote (on the OUT of the whole Yohara chain):
#   the 3 items of tools/ybiolog/ybiolog_items.json: an item_proto record (dbdata) equal to the server's row
#   (yitem_record over the material template), an item_list line whose icon is in the repo's root/icon/item, an
#   itemdesc line.
#   docker run --rm -v /opt/metin2:/opt/metin2 m2pack-lzo python3 <repo>/client-patches/client-2.0.30/tools/ybiolog/verify_ybiolog.py \
#     <OUT pack dir> [<BASE pack dir>]
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, '/opt/metin2/cache/tcm/tz')
sys.path.insert(0, '/opt/metin2/cache/arezzo-work/client/az58')
sys.path.insert(0, HERE)
import m2pack  # noqa: E402
import packlib  # noqa: E402
import patch_ybiolog_client as pc  # noqa: E402

args = [a for a in sys.argv[1:] if not a.startswith('--')]
OUT = args[0]
BASE = args[1] if len(args) > 1 else '/opt/metin2/cache/cY/azbase'
ROOT = os.path.normpath(os.path.join(HERE, '..', '..', 'root'))
ROOT_ICONS = os.path.join(ROOT, 'icon', 'item')
fails = []


def entry(pack, name):
    d = OUT if os.path.exists(os.path.join(OUT, pack + '.index')) else BASE
    f, v, ents = m2pack.read_index(os.path.join(d, pack + '.index'))
    dat = packlib.rd(os.path.join(d, pack + '.data'))
    for e in ents:
        if e['name'] == name:
            return m2pack.read_entry(dat, e)
    return None


d = pc.items_json()
ver, recs = pc.records(entry('dbdata', 'gamedata/item_proto'))
want = pc.want_records(recs)
for v, r in sorted(want.items()):
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
    if not os.path.isfile(os.path.join(ROOT_ICONS, os.path.basename(icon))):
        fails.append('item_list %s: icon %s not in root/icon/item' % (k, icon))
for k, line in d['itemdesc'].items():
    if desc.get(k) != line:
        fails.append('itemdesc %s: missing or other' % k)
print('ybiolog: %d items, %d problem(s)' % (len(d['items']), len(fails)))
for f in fails:
    print('  ' + f)
sys.exit(1 if fails else 0)
