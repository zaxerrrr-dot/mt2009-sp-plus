# -*- coding: utf-8 -*-
# MT2009_PLUS_BIOLOG_ELIKSIR_V1 / MT2009_PLUS_MIKSTURY_WYCOFANE_V1 - OUT after build_mikstury_packs.py: the 6 lines of
# locale/pl/itemdesc.txt (pack dbdata) exactly as patch_mikstury_client.py makes them, each vnum once, and the 6 items
# still in gamedata/item_proto and gamedata/item_list.txt (the client's own records - the tool does not write them).
#   docker run --rm -v /opt/metin2:/opt/metin2 m2pack-lzo python3 <repo>/client-patches/client-2.0.30/tools/mikstury/verify_mikstury.py \
#     <OUT pack dir>
import os
import struct
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, '/opt/metin2/cache/tcm/tz')
sys.path.insert(0, '/opt/metin2/cache/arezzo-work/client/az58')
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(HERE, '..', 'monstercard'))
import m2pack  # noqa: E402
import patch_mikstury_client as pc  # noqa: E402
import patch_monstercard_client as base  # noqa: E402

OUT = [a for a in sys.argv[1:] if not a.startswith('--')][0]
fails = []


def entries(pack):
    pi = os.path.join(OUT, pack + '.index')
    if not os.path.exists(pi):
        fails.append('OUT has no %s pack' % pack)
        return {}
    f, v, ents = m2pack.read_index(pi)
    dat = open(os.path.join(OUT, pack + '.data'), 'rb').read()
    return dict((e['name'], m2pack.read_entry(dat, e)) for e in ents)


have = {}
have.update(entries('gamedata'))
have.update(entries('dbdata'))
for name, job in sorted(pc.JOBS.items()):
    if name not in have:
        fails.append('%s missing' % name)
        continue
    nb, changed = job(have[name])
    if changed:
        fails.append('%s: %d line(s) not as the patcher makes them' % (name, changed))
vnums = [r[0] for r in pc.ROWS]
if 'locale/pl/itemdesc.txt' in have:
    keys = [l.split('\t')[0].strip() for l in have['locale/pl/itemdesc.txt'].decode('cp1250').splitlines()]
    for v in vnums:
        if keys.count(str(v)) != 1:
            fails.append('itemdesc.txt: %d line(s) of %d' % (keys.count(str(v)), v))
if 'gamedata/item_list.txt' in have:
    keys = set(l.split('\t')[0].strip() for l in have['gamedata/item_list.txt'].decode('cp1250').splitlines())
    for v in vnums:
        if str(v) not in keys:
            fails.append('item_list.txt: no line of %d' % v)
if 'gamedata/item_proto' in have:
    b = have['gamedata/item_proto']
    if b[:4] != b'MIPX':
        fails.append('item_proto: not MIPX')
    else:
        ver, stride, cnt, size = struct.unpack_from('<IIII', b, 4)
        raw = m2pack.mcoz_decode(b[20:], base.ITEM_KEY)
        recs = set(struct.unpack_from('<I', raw, i * stride)[0] for i in range(cnt))
        for v in vnums:
            if v not in recs:
                fails.append('item_proto: no record of %d' % v)

print('mikstury: %d itemdesc lines, %d problem(s)' % (len(pc.ROWS), len(fails)))
for x in fails:
    print('  ' + x)
sys.exit(1 if fails else 0)
