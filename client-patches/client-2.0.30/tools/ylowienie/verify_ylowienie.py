# -*- coding: utf-8 -*-
# MT2009_PLUS_FISHING_GLOBAL_V1 - checks the packs build_ylowienie_packs.py wrote (on the OUT of the whole Yohara chain):
#   tools/yohara_lowienie/yohara_lowienie.json: every record patch_ylowienie_client.py wants (the new items = the
#   server's rows, the rods Wedka+1..+20, the grilled fish, Kula Rybaka) in gamedata/item_proto (dbdata); the new items'
#   item_list lines with their icon in the repo's root/icon/item or the base's icon pack; the itemdesc lines; no text
#   naming the game or its publisher.
#   docker run --rm -v /opt/metin2:/opt/metin2 m2pack-lzo python3 <repo>/client-patches/client-2.0.30/tools/ylowienie/verify_ylowienie.py \
#     <OUT pack dir> [<BASE pack dir>]
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, '/opt/metin2/cache/tcm/tz')
sys.path.insert(0, '/opt/metin2/cache/arezzo-work/client/az58')
sys.path.insert(0, HERE)
import m2pack  # noqa: E402
import packlib  # noqa: E402
import patch_ylowienie_client as pc  # noqa: E402

args = [a for a in sys.argv[1:] if not a.startswith('--')]
OUT = args[0]
BASE = args[1] if len(args) > 1 else '/opt/metin2/cache/cY/azbase'
ROOT_ICONS = os.path.normpath(os.path.join(HERE, '..', '..', 'root', 'icon', 'item'))
fails = []

# MT2009_PLUS_GROWTH_PET_V1: the pet system's json owns these vnums (tools/pety: build_pety_packs.py runs later and rewrites
# their records and lines on purpose; pety/verify_pety.py checks them) - skipped here
import json as _json  # noqa: E402
PETY_VNUMS = set(int(i['vnum']) for i in _json.load(open(os.path.join(HERE, '..', '..', '..', '..', 'tools', 'pety', 'pety_items.json'),
                                                           encoding='utf-8'))['items'])

def pack_dir(pack):
    return OUT if os.path.exists(os.path.join(OUT, pack + '.index')) else BASE


def entry(pack, name):
    d = pack_dir(pack)
    f, v, ents = m2pack.read_index(os.path.join(d, pack + '.index'))
    dat = packlib.rd(os.path.join(d, pack + '.data'))
    for e in ents:
        if e['name'] == name:
            return m2pack.read_entry(dat, e)
    return None


def icon_names():
    names = set()
    for d in (OUT, BASE, '/opt/metin2/cache/c55/pack'):
        p = os.path.join(d, 'icon.index')
        if os.path.exists(p):
            f, v, ents = m2pack.read_index(p)
            names.update(e['name'].lower() for e in ents)
    return names


d = pc.items_json()
ver, recs = pc.records(entry('dbdata', 'gamedata/item_proto'))
want = pc.want_records(recs)
for v, r in sorted(want.items()):
    if v in PETY_VNUMS:
        continue
    if recs.get(v) != r:
        fails.append('item_proto %d: not the wanted record' % v)
lst = entry('gamedata', 'gamedata/item_list.txt').decode('cp1250').replace('\r\n', '\n').split('\n')
lst = dict((l.split('\t')[0].strip(), l) for l in lst if l.strip())
desc = entry('dbdata', 'locale/pl/itemdesc.txt').decode('cp1250').replace('\r\n', '\n').split('\n')
desc = dict((l.split('\t')[0].strip(), l) for l in desc if l.strip())
packed_icons = None
for k, line in d['item_list'].items():
    if lst.get(k, '').split() != line.split():
        fails.append('item_list %s: missing or other' % k)
    icon = line.split('\t')[2]
    if not os.path.isfile(os.path.join(ROOT_ICONS, os.path.basename(icon))):
        if packed_icons is None:
            packed_icons = icon_names()
        if icon.lower() not in packed_icons:
            fails.append('item_list %s: icon %s neither in root/icon/item nor in an icon pack' % (k, icon))
for row in pc.desc_rows():
    k = row.split('\t')[0]
    if int(k) in PETY_VNUMS:
        continue
    if desc.get(k) != row:
        fails.append('itemdesc %s: missing or other' % k)
    for bad in ('metin2', 'gameforge', 'oficjaln'):
        if bad in row.lower():
            fails.append('itemdesc %s: names "%s"' % (k, bad))
print('ylowienie: %d records, %d item_list lines, %d itemdesc lines, %d problem(s)'
      % (len(want), len(d['item_list']), len(pc.desc_rows()), len(fails)))
for f in fails:
    print('  ' + f)
sys.exit(1 if fails else 0)
