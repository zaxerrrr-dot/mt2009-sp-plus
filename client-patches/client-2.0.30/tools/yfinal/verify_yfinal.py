# -*- coding: utf-8 -*-
# MT2009_PLUS_YOHARA_FINAL_V1 - checks the client the whole Yohara chain built (yfinal_data.py):
#   * gamedata/atlasinfo.txt: no DEAD row, no two rows overlap; every map of the servers' Yohara map indexes
#     (every linux-port/docker/game/*/map/*/Setting.txt) has its row with the Setting.txt's base/size;
#   * gamedata/mob_proto: every monster's element bits = the server's (zywioly_moby.sql + *_zywioly.sql); a monster
#     with an element on the server but no client row is listed as a problem too.
#   docker run --rm -v /opt/metin2:/opt/metin2 m2pack-lzo python3 <repo>/client-patches/client-2.0.30/tools/yfinal/verify_yfinal.py \
#     <OUT pack dir> [<BASE pack dir>]
import glob
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, '/opt/metin2/cache/tcm/tz')
sys.path.insert(0, '/opt/metin2/cache/arezzo-work/client/az58')
sys.path.insert(0, HERE)
import m2pack  # noqa: E402
import packlib  # noqa: E402
import yfinal_data as yd  # noqa: E402

args = [a for a in sys.argv[1:] if not a.startswith('--')]
OUT = args[0]
BASE = args[1] if len(args) > 1 else '/opt/metin2/cache/cY/azbase'
fails = []


def entry(pack, name):
    d = OUT if os.path.exists(os.path.join(OUT, pack + '.index')) else BASE
    f, v, ents = m2pack.read_index(os.path.join(d, pack + '.index'))
    dat = packlib.rd(os.path.join(d, pack + '.data'))
    for e in ents:
        if e['name'] == name:
            return m2pack.read_entry(dat, e)
    return None


atlas = entry('gamedata', 'gamedata/atlasinfo.txt').decode('cp1250')
rows = yd.atlas_rows(atlas)
dead = set(yd.DEAD)
for i, n, x, y, w, h in rows:
    if (n, x, y) in dead:
        fails.append('atlasinfo: dead row %s %d %d' % (n, x, y))
for a, b in yd.overlaps(atlas):
    fails.append('atlasinfo overlap: %s <-> %s' % (a, b))
byname = {}
for i, n, x, y, w, h in rows:
    byname.setdefault(n.lower(), []).append((x, y, w, h))
GAME = os.path.join(yd.REPO, 'linux-port', 'docker', 'game')
nmaps = 0
for st in sorted(glob.glob(os.path.join(GAME, '*', 'map', '*', 'Setting.txt'))):
    batch = st[len(GAME) + 1:].split(os.sep)[0]
    folder = os.path.basename(os.path.dirname(st))
    kv = {}
    for l in open(st, encoding='latin-1'):
        t = l.split()
        if len(t) >= 3 and t[0] in ('BasePosition', 'MapSize'):
            kv[t[0]] = (int(t[1]), int(t[2]))
    if 'BasePosition' not in kv:
        continue
    nmaps += 1
    want = kv['BasePosition'] + kv['MapSize']
    if want not in byname.get(folder.lower(), []):
        fails.append('atlasinfo: %s (%s) has no row %s (has %s)' % (folder, batch, want, byname.get(folder.lower())))
srv = yd.server_elements()
cli = yd.client_elements(entry('gamedata', 'gamedata/mob_proto'))
for v in sorted(set(srv) | set(cli)):
    s, c = srv.get(v, 0), cli.get(v, 0)
    if v not in cli:
        fails.append('mob_proto %d: element %#x on the server, no client row' % (v, s))
    elif s != c:
        fails.append('mob_proto %d: client element %#x, server %#x' % (v, c, s))
# 3) the Metins' looks: the new pack's files (as the GF client has them), its Index line, the npclist lines
np = yd.NEW_PACK
want_files = yd.new_pack_files()
if not os.path.exists(os.path.join(OUT, np + '.index')):
    fails.append('%s: no pack' % np)
else:
    f, v, e2 = m2pack.read_index(os.path.join(OUT, np + '.index'))
    d2 = packlib.rd(os.path.join(OUT, np + '.data'))
    if dict((e['name'], m2pack.read_entry(d2, e)) for e in e2) != want_files:
        fails.append('%s: not the GF files' % np)
ix = packlib.rd(os.path.join(OUT, 'Index') if os.path.exists(os.path.join(OUT, 'Index')) else os.path.join(BASE, 'Index'))
if np.encode() not in [l.strip() for l in ix.replace(b'\r\n', b'\n').split(b'\n')]:
    fails.append('Index: no %s' % np)
npc = entry('gamedata', 'gamedata/npclist.txt')
if yd.npclist(npc)[1]:
    fails.append('npclist: the tree Metins not on %s' % yd.RACE_TREE)
print('yfinal: %d atlas rows, %d server maps of the repo, %d monsters with an element; %d problem(s)' % (
    len(rows), nmaps, len(srv), len(fails)))
for f in fails:
    print('  ' + f)
sys.exit(1 if fails else 0)
