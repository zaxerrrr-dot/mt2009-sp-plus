# -*- coding: utf-8 -*-
# MT2009_PLUS_QUEST_RENEWAL_V1 - checks what build_questren_packs.py wrote (on the OUT of the whole Yohara chain):
#   the pack "questren" in Index (unless every picture is in the client already) with the 13 pictures of quest_re/ the
#   root's questrenewal.py names, each reachable in some pack with the same bytes; the board's frame
#   d:/ymir work/ui/pattern/border_a_*.tga (uiscript/characterwindow.py) in some pack; the root files present with the
#   feature's markers.
#   docker run --rm -v /opt/metin2:/opt/metin2 m2pack-lzo python3 <repo>/client-patches/client-2.0.30/tools/questren/verify_questren.py \
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
import build_questren_packs as bp  # noqa: E402

args = [a for a in sys.argv[1:] if not a.startswith('--')]
OUT = args[0]
BASE = args[1] if len(args) > 1 else '/opt/metin2/cache/cY/azbase'
ROOT = os.path.normpath(os.path.join(HERE, '..', '..', 'root'))
PATTERN = ['d:/ymir work/ui/pattern/border_a_%s.tga' % p for p in
           ('left_top', 'right_top', 'left_bottom', 'right_bottom', 'top', 'left', 'right', 'bottom', 'center')]
fails = []

# every name of OUT (first) and BASE -> (dir, pack, entry)
where = {}
for d in (OUT, BASE):
    if not os.path.isdir(d):
        continue
    for p in sorted(f[:-6] for f in os.listdir(d) if f.endswith('.index')):
        if d == BASE and os.path.exists(os.path.join(OUT, p + '.index')):
            continue
        for e in m2pack.read_index(os.path.join(d, p + '.index'))[2]:
            where.setdefault(e['name'], (d, p, e))
cache = {}


def entry(name):
    if name not in where:
        return None
    d, p, e = where[name]
    if (d, p) not in cache:
        cache[(d, p)] = packlib.rd(os.path.join(d, p + '.data'))
    return m2pack.read_entry(cache[(d, p)], e)


# 1) the pictures and Index
packs = set()
for name, want in sorted(bp.files().items()):
    if entry(name) != want:
        fails.append('%s missing or other' % name)
    elif name in where:
        packs.add(where[name][1])
if bp.PACK in packs:
    ix_path = os.path.join(OUT, 'Index') if os.path.exists(os.path.join(OUT, 'Index')) else os.path.join(BASE, 'Index')
    ix = [l.strip() for l in packlib.rd(ix_path).replace(b'\r\n', b'\n').split(b'\n')]
    if bp.PACK.encode() not in ix:
        fails.append('Index: no line %s' % bp.PACK)

# 2) the board's frame
for name in PATTERN:
    if name not in where:
        fails.append('%s is in no pack (the quest board frame)' % name)

# 3) the root
need = {'questrenewal.py': 'MT2009_PLUS_QUEST_RENEWAL_V1', 'uicharacter.py': 'questrenewal.QuestList',
        'interfacemodule.py': 'QuestRenewalTakeLetter', 'game.py': '"QuestCategory"',
        os.path.join('uiscript', 'characterwindow.py'): 'Quest_Renewal_List'}
for f, marker in sorted(need.items()):
    p = os.path.join(ROOT, f)
    if not os.path.isfile(p):
        fails.append('root/%s missing' % f)
    elif marker.encode() not in open(p, 'rb').read():
        fails.append('root/%s: no %s' % (f, marker))
src = open(os.path.join(ROOT, 'questrenewal.py'), 'rb').read().decode('cp1250') if os.path.isfile(os.path.join(ROOT, 'questrenewal.py')) else ''
named = set(re.findall(r'"([a-z0-9_]+\.tga)"', src))
for n in named:
    if n not in bp.IMAGES:
        fails.append('questrenewal.py names %s, which the pack does not carry' % n)

print('questren: %d pictures (packs %s), frame %d, %d problem(s)' % (len(bp.IMAGES), ','.join(sorted(packs)) or '-',
                                                                   len(PATTERN), len(fails)))
for f in fails:
    print('  ' + f)
sys.exit(1 if fails else 0)
