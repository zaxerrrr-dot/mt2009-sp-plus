# -*- coding: utf-8 -*-
# MT2009_PLUS_GUILDSYS_V1 - checks the packs build_guildsys_packs.py wrote (on the OUT of the whole Yohara chain):
#   the four books: an item_proto record (dbdata) equal to the server's guildsys.sql row (yitem_record over 71095), an
#   item_list line whose icon is in the client (icon / root pack), an itemdesc line; the skilldesc and skilltable rows
#   158-160 (skilltable = the SQL's skill_proto rows); every file of client-2.0.30/guildsys/d_ in the root pack byte for
#   byte, every .sub's image there and inside the atlas; the skill icons the skilldesc rows name; the root python's
#   lists (playersettingmodule.py 158-160, uiaffectbar.py's icons).
#   docker run --rm -v /opt/metin2:/opt/metin2 m2pack-lzo python3 <repo>/client-patches/client-2.0.30/tools/guildsys/verify_guildsys.py \
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
import patch_guildsys_client as pc  # noqa: E402
import build_guildsys_packs as bp  # noqa: E402

args = [a for a in sys.argv[1:] if not a.startswith('--')]
OUT = args[0]
BASE = args[1] if len(args) > 1 else '/opt/metin2/cache/cY/azbase'
ROOT = os.path.normpath(os.path.join(HERE, '..', '..', 'root'))
fails = []
_packs = {}


def pack(name):
    if name not in _packs:
        d = OUT if os.path.exists(os.path.join(OUT, name + '.index')) else BASE
        f, v, ents = m2pack.read_index(os.path.join(d, name + '.index'))
        _packs[name] = (dict((e['name'], e) for e in ents), packlib.rd(os.path.join(d, name + '.data')))
    return _packs[name]


def entry(p, name):
    have, dat = pack(p)
    return m2pack.read_entry(dat, have[name]) if name in have else None


def lines(p, name):
    t = entry(p, name).decode('cp1250').replace('\r\n', '\n').split('\n')
    return dict((l.split('\t')[0].strip(), l) for l in t if l.strip())


ver, recs = pc.records(entry('dbdata', 'gamedata/item_proto'))
for v, r in sorted(pc.want_records(recs).items()):
    if recs.get(v) != r:
        fails.append('item_proto %d: not the server\'s record' % v)
lst = lines('gamedata', 'gamedata/item_list.txt')
icons = set(pack('icon')[0]) | set(pack('root')[0])
for line in pc.list_rows():
    k = line.split('\t')[0]
    if lst.get(k, '').split() != line.split():
        fails.append('item_list %s: missing or other' % k)
    if line.split('\t')[2] not in icons:
        fails.append('item_list %s: icon %s not in the icon / root pack' % (k, line.split('\t')[2]))
desc = lines('dbdata', 'locale/pl/itemdesc.txt')
for line in pc.desc_rows():
    if desc.get(line.split('\t')[0]) != line:
        fails.append('itemdesc %s: missing or other' % line.split('\t')[0])
sd = lines('dbdata', 'locale/pl/skilldesc.txt')
for line in pc.skilldesc_rows():
    if sd.get(line.split('\t')[0]) != line:
        fails.append('skilldesc %s: missing or other' % line.split('\t')[0])
st = lines('dbdata', 'gamedata/skilltable.txt')
for line in pc.skilltable_rows():
    if st.get(line.split('\t')[0]) != line:
        fails.append('skilltable %s: missing or other' % line.split('\t')[0])

files = bp.added_files()
n = 0
for p, fs in sorted(files.items()):
    for name, b in sorted(fs.items()):
        n += 1
        if entry(p, name) != b:
            fails.append('%s: %s missing or other' % (p, name))
root_names = set(pack('root')[0])
atlas = files['root'].get('d:/ymir work/ui/guildsys_common.dds')
ah, aw = struct.unpack('<II', atlas[12:20]) if atlas else (0, 0)
for name, b in sorted(files['root'].items()):
    if not name.endswith('.sub'):
        continue
    kv = dict(l.split(None, 1) for l in b.decode('cp1250').splitlines() if len(l.split(None, 1)) == 2)
    img = kv['image'].strip('"')
    if ('d:/ymir work/ui/' + img).lower() not in root_names:
        fails.append('%s: image %s not in the root pack' % (name, img))
    if not (0 <= int(kv['left']) < int(kv['right']) <= aw and 0 <= int(kv['top']) < int(kv['bottom']) <= ah):
        fails.append('%s: square outside the %dx%d atlas' % (name, aw, ah))
for vnum, name, text, icon, motion, ls in pc.SKILL_DESC:
    if ('d:/ymir work/ui/skill/common/guild/%s.sub' % icon) not in root_names:
        fails.append('skill %d: icon %s.sub not in the root pack' % (vnum, icon))
psm = open(os.path.join(ROOT, 'playersettingmodule.py'), 'rb').read().decode('latin-1')
if 'ACTIVE_GUILD_SKILL_INDEX_LIST = (152, 153, 154, 155, 156, 157, 158, 159, 160,)' not in psm:
    fails.append('root/playersettingmodule.py: the active guild skill list has not 158-160')
aff = open(os.path.join(ROOT, 'uiaffectbar.py'), 'rb').read().decode('latin-1')
for icon in ('guildsys_burza', 'guildsys_wola', 'guildsys_nieugietosc'):
    nm = 'd:/ymir work/ui/skill/common/affect/%s.sub' % icon
    if nm not in aff:
        fails.append('root/uiaffectbar.py: no %s' % nm)
    if nm not in root_names:
        fails.append('%s not in the root pack' % nm)
print('guildsys: 4 books, 3 skills, %d files of ours checked (atlas %dx%d), %d problem(s)' % (n, aw, ah, len(fails)))
for f in fails:
    print('  ' + f)
sys.exit(1 if fails else 0)
