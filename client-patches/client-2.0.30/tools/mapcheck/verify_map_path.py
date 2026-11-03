# -*- coding: utf-8 -*-
# MT2009_PLUS_MAP_PATH_CHECK_V1 (client, 2.x and Yohara) - what one map needs on a warp, compared between the client a
# build starts from and the client it makes. Written for the Demon Tower report of 23 October 2026 (client 2.0.68:
# "the client dies ~8 s after the warp into the tower"); kept as a check for every client build that adds packs.
#
#   docker run --rm -v /opt/metin2:/opt/metin2 m2pack-lzo python3 verify_map_path.py <old pack dir> <new pack dir> \
#       [<map folder> <x>,<y> [<vnum>,<vnum>...]]
#   (defaults: metin2_map_deviltower1 140600,832000 and the tower's monsters, Metin and guard)
#
# The pack dirs are FULL pack sets of our packs (e.g. /opt/metin2/cache/c67/pack and /opt/metin2/cache/c237/pack):
# the base client's own packs (zone_*, monster, npc ...) are not on vps1, so a name only they hold is not compared.
# Checks:
#   1. atlasinfo.txt of the new client: exactly one row covers <x>,<y> and it is <map>; no two rows overlap; every
#      row parses as "%s %d %d %d %d" (the exe's sscanf in CMapManager::__LoadMapInfoVector).
#   2. Index: the exe keeps the FIRST pack that registered a name (boost unordered_multimap, the new node goes right
#      after the first of its key - EterPack.cpp CEterFileDict::InsertItem/GetItem). A name a pack new in this
#      client shares with an earlier pack of ours is listed (it is never read from the new pack).
#   3. the map's file closure (the GF 26.1.11 client's map folder, its areadata objects' properties, textureset,
#      msenv, atlas, and the race folders of <vnum>s by npclist) - every name of it our packs hold must be
#      byte-identical in old and new, or it is listed (changed / new / gone; a new name that is byte-identical to
#      the classic client's file is only a note).
#   4. gamedata rows of the <vnum>s: npclist lines (race, folder alias) identical, a mob_proto record present (a
#      changed record is a note: values only).
# Output ends with "FAIL (n):" as the other verifiers; exit 1 on a failure.
import os
import re
import struct
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, '/opt/metin2/cache/c36')
sys.path.insert(0, '/opt/metin2/cache/tcm/tz')
sys.path.insert(0, '/opt/metin2/cache/arezzo-work/client/az58')
sys.path.insert(0, os.path.join(HERE, '..', 'az58'))
sys.path.insert(0, os.path.join(HERE, '..', 'zaklety237'))
import m2pack  # noqa: E402
import gfres  # noqa: E402  (indexes the GF client at import)
from patch_zaklety237_client import MOB_KEY, MOB_RECORD  # noqa: E402

gfres.GR2DIR = '/opt/metin2/cache/arezzo-work/client/az58/gr2'
gfres.GR2DEC = os.path.join(gfres.GR2DIR, 'gr2dec')

OLD, NEW = sys.argv[1], sys.argv[2]
MAP = sys.argv[3] if len(sys.argv) > 3 else 'metin2_map_deviltower1'
POS = tuple(int(v) for v in (sys.argv[4] if len(sys.argv) > 4 else '140600,832000').split(','))
# the tower's first floor (regen groups 1001-1008: 1001-1004, 1031), its Metin 8015, the later floors' bosses
# (1091-1093) and the guard who sends a player in (20348, map 65)
VNUMS = [int(v) for v in (sys.argv[5] if len(sys.argv) > 5 else
                          '1001,1002,1003,1004,1031,1091,1092,1093,8015,20348').split(',')]
TERRAIN = 25600
# the classic client's unpacked files (Arezzo's pack sources): a name a new pack brings that the base client most
# likely has too (and then keeps - first pack wins) is harmless when it is the same file
CLASSIC = '/opt/metin2/cache/arezzo/cpack/files/'
RACE_DIRS = ('guild', 'npc', 'npc2', 'npc_pet', 'npc_mount', 'monster', 'monster2')   # exe 2.0.25's race msm folders
fail, notes = [], []


def index_order(d):
    lines = open(os.path.join(d, 'Index'), 'rb').read().replace(b'\r', b'').split(b'\n')
    return [lines[i + 1].decode() for i in range(1, len(lines) - 1, 2) if lines[i + 1]]


class Packs(object):
    def __init__(self, d):
        self.d, self.order, self.where, self.ents, self.blobs = d, index_order(d), {}, {}, {}
        for p in self.order:
            if not os.path.exists(os.path.join(d, p + '.index')):
                continue
            ents = m2pack.read_index(os.path.join(d, p + '.index'))[2]
            self.ents[p] = dict((gfres.norm(e['name']), e) for e in ents)
            for n in self.ents[p]:
                self.where.setdefault(n, []).append(p)

    def read(self, name):
        name = gfres.norm(name)
        ps = self.where.get(name)
        if not ps:
            return None
        p = ps[0]                                   # the first registered pack wins
        if p not in self.blobs:
            self.blobs[p] = open(os.path.join(self.d, p + '.data'), 'rb').read()
        return m2pack.read_entry(self.blobs[p], self.ents[p][name])


def classic(name):
    p = CLASSIC + (name[3:] if name.startswith('d:/') else name)
    return open(p, 'rb').read() if os.path.exists(p) else None


old, new = Packs(OLD), Packs(NEW)
print('old: %d packs of ours (%d in Index), new: %d (%d in Index)' % (
    len(old.ents), len(old.order), len(new.ents), len(new.order)))

# 1. atlasinfo
rows = []
for i, l in enumerate((new.read('gamedata/atlasinfo.txt') or b'').decode('latin1').splitlines()):
    t = l.split()
    if not t:
        continue
    try:
        rows.append((t[0], int(t[1]), int(t[2]), int(t[3]) * TERRAIN, int(t[4]) * TERRAIN))
    except (IndexError, ValueError):
        fail.append('atlasinfo line %d does not parse: %r' % (i + 1, l))
cover = [r for r in rows if r[1] <= POS[0] < r[1] + r[3] and r[2] <= POS[1] < r[2] + r[4]]
first = cover[0][0] if cover else None                       # CPythonBackground::GlobalPositionToMapInfo: find_if
if first is None or first.lower() != MAP.lower():
    fail.append('atlasinfo: %d,%d is %s, not %s' % (POS[0], POS[1], first, MAP))
for r in cover[1:]:
    fail.append('atlasinfo: %d,%d is also inside %s %d %d' % (POS[0], POS[1], r[0], r[1], r[2]))
for a in range(len(rows)):
    for b in range(a + 1, len(rows)):
        A, B = rows[a], rows[b]
        if A[1] < B[1] + B[3] and B[1] < A[1] + A[3] and A[2] < B[2] + B[4] and B[2] < A[2] + A[4]:
            fail.append('atlasinfo: %s %d %d overlaps %s %d %d' % (A[0], A[1], A[2], B[0], B[1], B[2]))
print('atlasinfo: %d rows, %d,%d -> %s' % (len(rows), POS[0], POS[1], first))

# 2. names a pack new in this Index shares with an earlier pack (read from the earlier one)
added = [p for p in new.order if p not in old.order and p in new.ents]
shared = [(n, ps) for n, ps in new.where.items() if len(ps) > 1 and any(p in added for p in ps[1:])]
print('packs new in Index: %s; their names an earlier pack of ours holds: %d' % (' '.join(added) or '-', len(shared)))
for n, ps in sorted(shared)[:20]:
    notes.append('shadowed (read from %s): %s in %s' % (ps[0], n, ' '.join(ps[1:])))

# 3. the map's closure
mapdir = 'maps/' + MAP.lower() + '/'
seeds = [mapdir]
setting = (gfres.GF.get(mapdir + 'setting.txt') and open(gfres.GF[mapdir + 'setting.txt'], 'rb').read() or b'').decode('latin1')
m = re.search(r'TextureSet\s+(\S+)', setting)
if m:
    seeds.append(gfres.norm(m.group(1)))
m = re.search(r'Environment\s+(\S+)', setting)
if m:
    seeds += ['d:/ymir work/environment/' + m.group(1).lower(), mapdir + m.group(1).lower()]
seeds.append('d:/ymir work/ui/atlas/%s/' % MAP.lower())
crcs = set()
for k, p in gfres.GF.items():
    if k.startswith(mapdir) and k.endswith('/areadata.txt'):
        t = open(p, 'rb').read().decode('latin1').splitlines()
        crcs.update(t[i + 2].split()[0] for i, l in enumerate(t) if l.startswith('Start Object') and i + 2 < len(t))
props = {}
for n in new.where:
    if n.startswith('property/') and n != 'property/reserve':
        b = new.read(n).split(b'\n')
        if len(b) > 1 and b[0].strip() == b'YPRT':
            props.setdefault(b[1].strip().decode(), n)
seeds += [props[c] for c in crcs if c in props]
missing = sorted(c for c in crcs if c not in props)
if missing:
    notes.append('%s: %d object CRC(s) with no property in pack property: %s' % (MAP, len(missing), ' '.join(missing[:10])))
npc = (new.read('gamedata/npclist.txt') or b'').decode('latin1').splitlines()
src, race = {}, {}
for l in npc:
    t = l.split()
    if len(t) >= 2 and t[0].isdigit():
        if t[0] == '0' and len(t) >= 3:
            src[t[1].lower()] = t[2].lower()
        else:
            race[int(t[0])] = t[1].lower()
for v in VNUMS:
    if v not in race:
        notes.append('npclist: no row for %d' % v)
        continue
    folder = src.get(race[v], race[v])
    seeds += ['d:/ymir work/%s/%s/' % (top, folder) for top in RACE_DIRS]
files, unres, _ = gfres.closure(seeds, set())
names = set(files) | set(unres) | set(n for n in new.where if n.startswith(mapdir)) | set(n for n in old.where if n.startswith(mapdir))
same = changed = known = 0
for n in sorted(names):
    a, b = old.read(n), new.read(n)
    if a is None and b is None:
        continue
    if a == b:
        same += 1
        continue
    where = ' '.join(new.where.get(n, old.where.get(n, [])))
    if a is None and classic(n) == b:
        known += 1
        notes.append('%s: new in this client (%s), byte-identical to the classic client' % (n, where))
        continue
    changed += 1
    fail.append('%s: %s (%s)' % (n, 'new in this client' if a is None else 'gone' if b is None else 'changed', where))
print('%s closure: %d names, %d held by our packs and identical, %d new but as the classic client, %d differ' % (
    MAP, len(names), same, known, changed))


# 4. gamedata rows
def mobs(p):
    b = p.read('gamedata/mob_proto')
    magic, cnt, es = struct.unpack_from('<4sII', b, 0)
    raw = m2pack.mcoz_decode(b[12:12 + es], MOB_KEY)
    return dict((struct.unpack_from('<I', raw, i * MOB_RECORD)[0], raw[i * MOB_RECORD:(i + 1) * MOB_RECORD])
                for i in range(cnt))


def npcrows(p):
    out = {}
    for l in (p.read('gamedata/npclist.txt') or b'').decode('latin1').splitlines():
        t = l.split()
        if t and t[0].isdigit():
            out.setdefault(int(t[0]) if t[0] != '0' else t[1].lower(), l.strip())
    return out


mo, mn, no, nn = mobs(old), mobs(new), npcrows(old), npcrows(new)
for v in VNUMS:
    if v not in mn:
        fail.append('mob_proto: no record of %d' % v)
    elif mo.get(v) != mn.get(v):                 # values only (stats, resistances): a note, the race is npclist's
        notes.append('mob_proto %d: bytes %s differ' % (v, ','.join(
            str(i) for i in range(MOB_RECORD) if mo.get(v, bytes(MOB_RECORD))[i] != mn[v][i])[:60]))
    if no.get(v) != nn.get(v):
        fail.append('npclist %d: %r -> %r' % (v, no.get(v), nn.get(v)))
    r = race.get(v)
    if r and no.get(r) != nn.get(r):
        fail.append('npclist alias %s: %r -> %r' % (r, no.get(r), nn.get(r)))
print('gamedata rows of %d vnum(s) compared' % len(VNUMS))

print('notes (%d):' % len(notes))
for n in notes:
    print('  ' + n)
print('FAIL (%d):' % len(fail))
for f in fail:
    print('  ' + f)
sys.exit(1 if fail else 0)
