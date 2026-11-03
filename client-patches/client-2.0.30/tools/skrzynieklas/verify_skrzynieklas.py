# -*- coding: utf-8 -*-
# MT2009_PLUS_CLASS_CHESTS_V1 - the eight class chests in OUT (build_skrzynieklas_packs.py): the 16 records of
# gamedata/item_proto, their item_list.txt and itemdesc.txt lines exactly as patch_skrzynieklas_client.py makes them,
# pack "skrzynieklas" with the 9 icons every item_list line names, listed in pack/Index, and no other pack of OUT with
# one of those icon names.
#   docker run --rm -v /opt/metin2:/opt/metin2 m2pack-lzo python3 <repo>/client-patches/client-2.0.30/tools/skrzynieklas/verify_skrzynieklas.py \
#     <OUT pack dir>
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, '/opt/metin2/cache/tcm/tz')
sys.path.insert(0, '/opt/metin2/cache/arezzo-work/client/az58')
sys.path.insert(0, HERE)
import m2pack  # noqa: E402
import patch_skrzynieklas_client as pc  # noqa: E402
import build_skrzynieklas_packs as B  # noqa: E402

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
        fails.append('%s: %d record(s) / line(s) not as the patcher makes them' % (name, changed))
icons = entries(B.ICON_PACK)
want = set(i[4] for i in pc.items())
if set(icons) != want:
    fails.append('%s: icons %s, want %s' % (B.ICON_PACK, sorted(icons), sorted(want)))
for n, b in icons.items():
    if not (len(b) > 18 and b[2] in (2, 10) and (b[12] | b[13] << 8) == 32 and (b[14] | b[15] << 8) == 32):
        fails.append('%s: not a 32x32 true-colour TGA' % n)
for p in sorted(x[:-6] for x in os.listdir(OUT) if x.endswith('.index')):
    if p == B.ICON_PACK:
        continue
    for e in m2pack.read_index(os.path.join(OUT, p + '.index'))[2]:
        if e['name'] in want:
            fails.append('%s: also in %s (OUT)' % (e['name'], p))
ix = open(os.path.join(OUT, 'Index'), 'rb').read() if os.path.exists(os.path.join(OUT, 'Index')) else b''
if B.ICON_PACK.encode() not in [l.strip() for l in ix.replace(b'\r\n', b'\n').split(b'\n')]:
    fails.append('pack/Index: no %s line' % B.ICON_PACK)

print('skrzynieklas: %d items, %d icons, %d problem(s)' % (len(pc.items()), len(icons), len(fails)))
for x in fails:
    print('  ' + x)
sys.exit(1 if fails else 0)
