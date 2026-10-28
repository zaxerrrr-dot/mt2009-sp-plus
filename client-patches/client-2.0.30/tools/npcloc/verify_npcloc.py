# -*- coding: utf-8 -*-
# MT2009_PLUS_NPC_LOCATION_HELPER_V1 - checks the packs build_npcloc_packs.py wrote (on the OUT of the whole Yohara chain):
#   the three items: an item_proto record (dbdata) equal to the server's npc_location_helper.sql row (yitem_record over
#   71095), an item_list line whose icon is in the repo's root/icon/item, an itemdesc line; every data file of
#   client-2.0.30/npcloc/locale and every picture / effect file of client-2.0.30/npcloc/d_ in its pack byte for byte;
#   every .sub's image and the effect's mesh / textures present; the window's python in client-2.0.30/root
#   (uinpclocationhelper.py, uiscript/npclocationhelper_*.py) and the map list's point files present.
#   docker run --rm -v /opt/metin2:/opt/metin2 m2pack-lzo python3 <repo>/client-patches/client-2.0.30/tools/npcloc/verify_npcloc.py \
#     <OUT pack dir> [<BASE pack dir>] [--etc=<dir with the full install's etc.index>]
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, '/opt/metin2/cache/tcm/tz')
sys.path.insert(0, '/opt/metin2/cache/arezzo-work/client/az58')
sys.path.insert(0, HERE)
import m2pack  # noqa: E402
import packlib  # noqa: E402
import patch_npcloc_client as pc  # noqa: E402
import build_npcloc_packs as bp  # noqa: E402

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


ver, recs = pc.records(entry('dbdata', 'gamedata/item_proto'))
for v, r in sorted(pc.want_records(recs).items()):
    if recs.get(v) != r:
        fails.append('item_proto %d: not the server\'s record' % v)
lst = entry('gamedata', 'gamedata/item_list.txt').decode('cp1250').replace('\r\n', '\n').split('\n')
lst = dict((l.split('\t')[0].strip(), l) for l in lst if l.strip())
for line in pc.list_rows():
    k = line.split('\t')[0]
    if lst.get(k, '').split() != line.split():
        fails.append('item_list %s: missing or other' % k)
    icon = line.split('\t')[2]
    if not os.path.isfile(os.path.join(ROOT, icon)):
        fails.append('item_list %s: icon %s not in root/icon/item' % (k, icon))
desc = entry('dbdata', 'locale/pl/itemdesc.txt').decode('cp1250').replace('\r\n', '\n').split('\n')
desc = dict((l.split('\t')[0].strip(), l) for l in desc if l.strip())
for line in pc.desc_rows():
    if desc.get(line.split('\t')[0]) != line:
        fails.append('itemdesc %s: missing or other' % line.split('\t')[0])

files = bp.added_files()
n = 0
for p, fs in sorted(files.items()):
    for name, b in sorted(fs.items()):
        n += 1
        if entry(p, name) != b:
            fails.append('%s: %s missing or other' % (p, name))
# every picture / effect file the window uses (ui_assets.txt): ours (just checked) or the full install's base pack etc
etc_names = bp.etc_names()
root_names = set(pack('root')[0])
have = root_names | (etc_names or set())
assets = [l.strip() for l in open(os.path.join(HERE, 'ui_assets.txt')) if l.strip()]
for name in assets:
    if name in files['root']:
        continue
    if etc_names is None:
        if name not in root_names:
            fails.append('asset %s: not ours and the base pack etc is not here to check' % name)
    elif name not in have:
        fails.append('asset %s: neither ours nor in the base pack etc' % name)


def asset_bytes(name):
    if name in files['root']:
        return files['root'][name]
    if etc_names is not None and name in etc_names:
        if 'etc' not in _packs:
            f, v, ents = m2pack.read_index(os.path.join(bp.etc_dir(), 'etc.index'))
            _packs['etc'] = (dict((e['name'], e) for e in ents), packlib.rd(os.path.join(bp.etc_dir(), 'etc.data')))
        return entry('etc', name)
    return entry('root', name)


for name in assets:
    if not name.endswith('.sub') or name not in have and name not in files['root']:
        continue
    b = asset_bytes(name)
    img = [l.split('"')[1] for l in b.decode('cp1250').splitlines() if l.strip().lower().startswith('image')][0]
    if ('d:/ymir work/ui/' + img).lower() not in have:
        fails.append('%s: image %s neither ours nor in the base pack etc' % (name, img))
info = files['locale'].get('locale/common/map/npc_location_helper/npc_location_helper.txt', b'').decode('cp1250')
maps = [l.split('\t') for l in info.replace('\r', '').split('\n') if l.startswith('\t') and l.strip()[:1].isdigit()]
for m in maps:
    if m[11] == '1' and ('locale/common/map/%s_point.txt' % m[3].lower()) not in files['locale']:
        fails.append('map %s %s: no point file' % (m[1], m[3]))
for f in ('uinpclocationhelper.py', 'uiscript/npclocationhelper_atlaswindow.py',
          'uiscript/npclocationhelper_npcinfowindow.py', 'uiscript/npclocationhelper_mobinfowindow.py'):
    if not os.path.isfile(os.path.join(ROOT, f)):
        fails.append('root/%s missing' % f)
print('npcloc: 3 items, %d maps, %d files of ours checked, %d UI assets (base pack etc %s), %d problem(s)'
      % (len(maps), n, len(assets), 'checked' if etc_names is not None else 'not here', len(fails)))
for f in fails:
    print('  ' + f)
sys.exit(1 if fails else 0)
