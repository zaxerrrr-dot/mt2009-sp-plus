# -*- coding: utf-8 -*-
# MT2009_PLUS_MLODZI_BOHATEROWIE_V1 - checks the packs build_mlodzi_packs.py wrote (on the OUT of the whole Yohara chain):
#   the 48 weapons of tools/mlodzi/mlodzi_items.json: an item_proto record (dbdata) equal to the server's row
#   (yitem_record over the weapon template), an item_list line (gamedata) whose icon is in the repo's root/icon/item or
#   a pack, an itemdesc line (dbdata); every model the item_list lines name in a pack (32-bit GR2) and every texture
#   that model names (gf28/gfres.gr2_textures on the packed model) in a pack; the mlodzi pack in pack/Index.
#   docker run --rm -v /opt/metin2:/opt/metin2 m2pack-lzo python3 <repo>/client-patches/client-2.0.30/tools/mlodzi/verify_mlodzi.py \
#     <OUT pack dir> [<BASE pack dir>]
import os
import shutil
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, '/opt/metin2/cache/tcm/tz')
sys.path.insert(0, '/opt/metin2/cache/arezzo-work/client/az58')
sys.path.insert(0, '/opt/metin2/cache/tcm/gf28')
sys.path.insert(0, HERE)
import m2pack  # noqa: E402
import packlib  # noqa: E402
import patch_mlodzi_client as pc  # noqa: E402

args = [a for a in sys.argv[1:] if not a.startswith('--')]
OUT = args[0]
BASE = args[1] if len(args) > 1 else '/opt/metin2/cache/cY/azbase'
ROOT_ICONS = os.path.normpath(os.path.join(HERE, '..', '..', 'root', 'icon', 'item'))
GR2_64 = b'\xe5\x9b\x49\x5e'
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
models = set()
for k, line in d['item_list'].items():
    if lst.get(k, '').split('\t') != line.split('\t'):
        fails.append('item_list %s: missing or other' % k)
    cols = line.split('\t')
    icon = cols[2]
    if not os.path.isfile(os.path.join(ROOT_ICONS, os.path.basename(icon))) and icon not in WHERE:
        fails.append('item_list %s: icon %s not in root/icon/item nor in a pack' % (k, icon))
    models.add(cols[3].strip().lower())
if models != set(m.lower() for m in d['models']):
    fails.append('item_list models %s != json models %s' % (sorted(models), sorted(d['models'])))
for k, line in d['itemdesc'].items():
    if desc.get(k) != line:
        fails.append('itemdesc %s: missing or other' % k)

import gfres  # noqa: E402
tmp = tempfile.mkdtemp(prefix='verify_mlodzi')
try:
    for m in sorted(models):
        b = any_entry(m)
        if b is None:
            fails.append('%s: in no pack' % m)
            continue
        if b[:4] == GR2_64:
            fails.append('%s: a 64-bit GR2' % m)
            continue
        path = os.path.join(tmp, os.path.basename(m))
        open(path, 'wb').write(b)
        tex = gfres.gr2_textures(m, path)
        if m in gfres.GR2_FAIL or not tex:
            fails.append('%s: its textures cannot be read (%s)' % (m, gfres.GR2_FAIL.get(m, 'none named')))
        for t in sorted(tex):
            if t not in WHERE:
                fails.append('%s: texture %s in no pack' % (m, t))
finally:
    shutil.rmtree(tmp, ignore_errors=True)
ix = open(os.path.join(OUT, 'Index'), 'rb').read() if os.path.exists(os.path.join(OUT, 'Index')) else b''
if os.path.exists(os.path.join(OUT, 'mlodzi.index')) and b'mlodzi' not in ix.split():
    fails.append('pack/Index: no mlodzi line')
print('mlodzi: %d weapons, %d models, %d problem(s)' % (len(d['items']), len(models), len(fails)))
for f in fails:
    print('  ' + f)
sys.exit(1 if fails else 0)
