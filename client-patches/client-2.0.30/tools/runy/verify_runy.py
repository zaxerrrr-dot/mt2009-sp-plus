# -*- coding: utf-8 -*-
# MT2009_PLUS_RUNY_WYKUWANIA_V1 - checks the client part of Runy Wykuwania on the OUT of the whole Yohara chain:
#   gamedata/item_proto, gamedata/item_list.txt, locale/pl/itemdesc.txt: 79605-79659 exactly as patch_runy_client.py
#   writes them (tools/runy/runy_items.json) - a second patch changes nothing;
#   the root pack (OUT, else BASE): icon/item/79605..79609.tga, each the GF 26.1.11 file's bytes (= the repo's
#   client-2.0.30/root copy), no other pack of OUT / BASE with one of those names and other content; uicubeokno.py with
#   the crafting window's chance-raising slot ("/cube improve", MT2009_PLUS_NPC_CRAFT_WINDOW_V1) the runes go into.
#   docker run --rm -v /opt/metin2:/opt/metin2 m2pack-lzo python3 <repo>/client-patches/client-2.0.30/tools/runy/verify_runy.py \
#     <OUT pack dir> [<BASE pack dir>]
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, '/opt/metin2/cache/tcm/tz')
sys.path.insert(0, '/opt/metin2/cache/arezzo-work/client/az58')
sys.path.insert(0, HERE)
import m2pack  # noqa: E402
import packlib  # noqa: E402
import patch_runy_client as pc  # noqa: E402

args = [a for a in sys.argv[1:] if not a.startswith('--')]
OUT = args[0]
BASE = args[1] if len(args) > 1 else '/opt/metin2/cache/cY/azbase'
GF = '/opt/metin2/cache/gf/Gameforge_26.1.11/_client/'
fails = []
_dat = {}


def entries(pack):
    """({name: entry}, data) of pack from OUT, else BASE (None, None: in neither)"""
    for d in (OUT, BASE):
        if d and os.path.exists(os.path.join(d, pack + '.index')):
            f, v, ents = m2pack.read_index(os.path.join(d, pack + '.index'))
            if (d, pack) not in _dat:
                _dat[(d, pack)] = packlib.rd(os.path.join(d, pack + '.data'))
            return dict((e['name'], e) for e in ents), _dat[(d, pack)]
    return None, None


def read(pack, name):
    idx, dat = entries(pack)
    if idx is None or name not in idx:
        fails.append('%s: not in pack %s' % (name, pack))
        return None
    return m2pack.read_entry(dat, idx[name])


# 1) the data
for name, fn in sorted(pc.JOBS.items()):
    b = read(pc.PACK_OF[name], name)
    if b is None:
        continue
    nb, changed = fn(b)
    if changed:
        fails.append('%s: %d record(s) / line(s) of the runes differ from patch_runy_client.py' % (name, changed))
b = read('dbdata', 'gamedata/item_proto')
if b is not None:
    ver, recs = pc.records(b)
    for v in range(pc.FIRST, pc.LAST + 1):
        if v not in recs:
            fails.append('item_proto: no %d' % v)

# 2) the icons: in root, GF's bytes, nowhere else with other content
icons = pc.icons()
idx, dat = entries('root')
if idx is None:
    fails.append('root: no pack')
else:
    for n, repo_file in sorted(icons.items()):
        gf = open(GF + n, 'rb').read()
        if not os.path.exists(repo_file) or open(repo_file, 'rb').read() != gf:
            fails.append('%s: the repo copy is not the GF 26.1.11 file' % n)
        if n not in idx:
            fails.append('root: %s missing' % n)
        elif m2pack.read_entry(dat, idx[n]) != gf:
            fails.append('root %s: not the GF 26.1.11 file' % n)
    for d in (OUT, BASE):
        if not d or not os.path.isdir(d):
            continue
        for p in sorted(os.listdir(d)):
            if not p.endswith('.index') or p == 'root.index':
                continue
            ents = dict((e['name'].lower(), e) for e in m2pack.read_index(os.path.join(d, p))[2])
            for n in icons:
                if n in ents:
                    other = m2pack.read_entry(packlib.rd(os.path.join(d, p[:-6] + '.data')), ents[n])
                    if other != open(GF + n, 'rb').read():
                        fails.append('%s/%s has %s with other content' % (os.path.basename(d), p[:-6], n))
    if 'uicubeokno.py' not in idx:
        fails.append('root: uicubeokno.py missing')
    else:
        src = m2pack.read_entry(dat, idx['uicubeokno.py'])
        for pat in (b'MT2009_PLUS_NPC_CRAFT_WINDOW_V1', b'/cube improve %d'):
            if pat not in src:
                fails.append('root uicubeokno.py: no %r' % pat)

print('runy: %d items, %d icons, %s' % (pc.LAST - pc.FIRST + 1, len(icons), 'OK' if not fails else '%d FAIL' % len(fails)))
for f in fails:
    print('FAIL ' + f)
sys.exit(1 if fails else 0)
