# -*- coding: utf-8 -*-
# MT2009_PLUS_HORSE40_V1 - checks what build_konie_packs.py wrote (on the OUT of the whole Yohara chain):
#   konie.index / konie.data hold exactly the files of konie_files.json (size, sha256, entry type, crc, read-back);
#   pack/Index lists "konie" once; no other pack has one of its names; every image the root's horse files name
#   (uikonierozwoj.py, uiaffectbar.py) is in the pack; the dbdata / gamedata records of patch_konie_client.py are there
#   (50046-50049 = the server's rows, the books ITEM_QUEST + QUEST_USE, the mob records 20149-20151), the item_list
#   lines' icons are in root/icon/item, the itemdesc lines are the json's.
#   docker run --rm -v /opt/metin2:/opt/metin2 m2pack-lzo python3 <repo>/client-patches/client-2.0.30/tools/konie/verify_konie.py \
#     <OUT pack dir> [<BASE pack dir>]
import hashlib
import os
import re
import struct
import sys
import zlib

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, '/opt/metin2/cache/tcm/tz')
sys.path.insert(0, '/opt/metin2/cache/c36')
sys.path.insert(0, '/opt/metin2/cache/arezzo-work/client/az58')
sys.path.insert(0, HERE)
import m2pack  # noqa: E402
import packlib  # noqa: E402
import build_konie_packs as B  # noqa: E402
import patch_konie_client as pc  # noqa: E402

args = [a for a in sys.argv[1:] if not a.startswith('--')]
OUT = args[0]
BASE = args[1] if len(args) > 1 else '/opt/metin2/cache/cY/azbase'
ROOT = os.path.normpath(os.path.join(HERE, '..', '..', 'root'))
fails = []


def entry(pack, name):
    d = OUT if os.path.exists(os.path.join(OUT, pack + '.index')) else BASE
    f, v, ents = m2pack.read_index(os.path.join(d, pack + '.index'))
    dat = packlib.rd(os.path.join(d, pack + '.data'))
    for e in ents:
        if e['name'] == name:
            return m2pack.read_entry(dat, e)
    return None


want = B.manifest()
ip = os.path.join(OUT, B.PACK + '.index')
if not os.path.exists(ip):
    fails.append('no %s.index in %s' % (B.PACK, OUT))
else:
    f, v, ents = m2pack.read_index(ip)
    dat = packlib.rd(os.path.join(OUT, B.PACK + '.data'))
    names = [e['name'] for e in ents]
    if sorted(names) != sorted(want):
        fails.append('pack names differ: extra %s, missing %s' % (sorted(set(names) - set(want)),
                                                                   sorted(set(want) - set(names))))
    for e in ents:
        if zlib.crc32(dat[e['pos']:e['pos'] + e['size']]) & 0xffffffff != e['dcrc']:
            fails.append('%s: data crc' % e['name'])
            continue
        b = m2pack.read_entry(dat, e)
        w = want.get(e['name'])
        if w and (len(b) != w['size'] or hashlib.sha256(b).hexdigest() != w['sha256'] or e['ctype'] != w['ctype']):
            fails.append('%s: not the file of konie_files.json' % e['name'])

ix_path = os.path.join(OUT, 'Index') if os.path.exists(os.path.join(OUT, 'Index')) else os.path.join(BASE, 'Index')
lines = [l.strip() for l in packlib.rd(ix_path).replace(b'\r\n', b'\n').split(b'\n')]
if lines.count(B.PACK.encode()) != 1:
    fails.append('Index: "%s" listed %d times' % (B.PACK, lines.count(B.PACK.encode())))

for d in (BASE, OUT):
    for fn in os.listdir(d):
        if not fn.endswith('.index') or fn[:-6] == B.PACK:
            continue
        for e in m2pack.read_index(os.path.join(d, fn))[2]:
            if e['name'] in want:
                fails.append('%s also in %s/%s' % (e['name'], d, fn))

# the root's names of the pack's images
for py in ('uikonierozwoj.py', 'uiaffectbar.py'):
    text = open(os.path.join(ROOT, py), 'rb').read().decode('latin-1')
    for n in set(re.findall(r'd:/ymir work/ui/konie/[a-z0-9_]+\.(?:sub|dds)', text)):
        if n not in want:
            fails.append('%s names %s, not in the pack' % (py, n))

d = pc.items_json()
ver, recs = pc.records(entry('dbdata', 'gamedata/item_proto'))
for v, r in sorted(pc.want_records(recs).items()):
    if recs.get(v) != r:
        fails.append('item_proto %d: not the wanted record' % v)
    elif recs[v][74] != dict((w['vnum'], w['type']) for w in d['items']).get(v, 18):
        fails.append('item_proto %d: type %d' % (v, recs[v][74]))
mobs = pc.mob_records(entry('gamedata', 'gamedata/mob_proto'))
by = dict((struct.unpack_from('<I', r, 0)[0], r) for r in mobs)
for v, r in pc.want_mobs(mobs).items():
    if by.get(v) != r:
        fails.append('mob_proto %d: missing or other' % v)
lst = entry('gamedata', 'gamedata/item_list.txt').decode('cp1250').replace('\r\n', '\n').split('\n')
lst = dict((l.split('\t')[0].strip(), l) for l in lst if l.strip())
desc = entry('dbdata', 'locale/pl/itemdesc.txt').decode('cp1250').replace('\r\n', '\n').split('\n')
desc = dict((l.split('\t')[0].strip(), l) for l in desc if l.strip())
for k, line in d['item_list'].items():
    if lst.get(k, '').split() != line.split():
        fails.append('item_list %s: missing or other' % k)
    icon = line.split('\t')[2]
    if not os.path.isfile(os.path.join(ROOT, icon)):
        fails.append('item_list %s: icon %s not in root' % (k, icon))
for k, line in d['itemdesc'].items():
    if desc.get(k) != line:
        fails.append('itemdesc %s: missing or other' % k)
print('konie: %d files, %d items, %d books, %d horses, %d problem(s)' % (len(want), len(d['items']),
                                                                       len(d['books']['vnums']), len(d['mobs']['vnums']),
                                                                       len(fails)))
for f in fails:
    print('  ' + f)
sys.exit(1 if fails else 0)
