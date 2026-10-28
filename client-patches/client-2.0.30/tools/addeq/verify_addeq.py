# -*- coding: utf-8 -*-
# MT2009_PLUS_ADDEQ_V1 - checks the packs build_addeq_packs.py wrote (on the OUT of the whole Yohara chain):
#   the pack "addeq" in Index with the skill icon's .sub (its image the pack's own 32 x 32 DXT5), the unlock items of
#   tools/addeq/addeq.json: an item_proto record (dbdata) equal to the server's row (yitem_record over 39006), an
#   item_list line whose icon is in the repo's root/icon/item, an itemdesc line; the skill 200's skilldesc and
#   skilltable rows (dbdata); root/uiaddeq.py present.
#   docker run --rm -v /opt/metin2:/opt/metin2 m2pack-lzo python3 <repo>/client-patches/client-2.0.30/tools/addeq/verify_addeq.py \
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
import build_addeq_packs as bp  # noqa: E402
import patch_addeq_client as pc  # noqa: E402

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
for name, want in bp.files().items():
    got = entry(bp.PACK, name)
    if got != want:
        fails.append('%s: %s missing or other' % (bp.PACK, name))
sub = entry(bp.PACK, bp.SUB) or b''
m = re.search(br'image\s+"([^"]+)"', sub)
if not m or 'd:/ymir work/ui/' + m.group(1).decode('latin-1').lower() != bp.DDS:
    fails.append('%s: the .sub does not name %s' % (bp.PACK, bp.DDS))

# 2) the items
d = pc.data()
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

# 3) the skill 200
sd = rows(entry('dbdata', 'locale/pl/skilldesc.txt'))
st = rows(entry('dbdata', 'gamedata/skilltable.txt'))
if sd.get('200') != d['skilldesc']:
    fails.append('skilldesc 200: missing or other')
if st.get('200') != d['skilltable']:
    fails.append('skilltable 200: missing or other')
if not os.path.isfile(os.path.join(ROOT, 'uiaddeq.py')):
    fails.append('root/uiaddeq.py missing')

print('addeq: pack %s, %d items, skill 200, %d problem(s)' % (bp.PACK, len(d['items']), len(fails)))
for f in fails:
    print('  ' + f)
sys.exit(1 if fails else 0)
