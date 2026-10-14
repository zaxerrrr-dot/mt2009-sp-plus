# -*- coding: utf-8 -*-
# MT2009_PLUS_YOHARA_FINAL_V1 - the last step of the Yohara client chain (the owner's test list of 14 October,
# cache/yohara/bledy-3.0.md items 8/8b/8c and 10): what build_yfinal_packs.py writes and verify_yfinal.py checks.
#
# 1) gamedata/atlasinfo.txt - the client picks the map to load by the warp's GLOBAL position: the FIRST atlasinfo row
#    whose square holds it (GameLib CMapManager / PythonBackground::Warp). Our base client (2.0.x, from the 2014
#    season2 client) carries rows the official 26.1.11 atlasinfo no longer has and no server map of ours uses (no
#    Setting.txt in any map index): copies of Grota Wygnancow 1/2 (season2/skipia_dungeon_01, skipia_dungeon_02) at
#    y 1356800/1510400/1664000, of its boss room (skipia_dungeon_boss 1100800/1203200, skipia_dungeon_boss2) and
#    season2/metin2_map_milgyo_a. They lie under the Yohara maps the official game put there - Przelecz Yilad,
#    Wawoz/Rozpadlina Polnocnego Wiatru, Swiatynia Wezy 1/2, Jaskinie Gnolli 1/2, Tajemnicza Instancja - so the client
#    loaded Grota Wygnancow's terrain and atlas on them, and on Tajemnicza Instancja milgyo_a, whose folder has no
#    MapProperty.txt ("CMapManager::LoadMap() Invalid Map Type" - the crash of 14 October 14:41). The rows go (DEAD);
#    the Yohara maps keep the official bases (= the servers' Setting.txt, quests, bots, panel untouched). Then no two
#    rows of the whole atlasinfo overlap (overlaps()).
# 2) gamedata/mob_proto - the monsters' element bits (dwRaceFlag bits 11-16, offset 83) = the server's end state:
#    apply.sh runs zywioly_moby.sql (clears bits 11-16 of every mob it does not list) and then the batches' own
#    *_zywioly.sql files in this order (ELEMENT_SQL). Every builder of the chain wrote its own rows' bits (or none);
#    this step makes the whole table equal to the server, so the target window's element icon shows on every map.
import os
import re

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.normpath(os.path.join(HERE, '..', '..', '..', '..'))
SQL_DIR = os.path.join(REPO, 'linux-port', 'docker', 'mariadb', 'playerbot')
ELEMENT_MASK = 0x1F800          # 129024
MOB_RECORD = 256
MOB_RACE_FLAG = 83
MOB_KEY = (4813894, 18955, 552631, 6822045)
CELL = 25600                    # CTerrainImpl::TERRAIN_XSIZE / TERRAIN_YSIZE

# (name, base x, base y) - rows of the base client no server map uses (see 1) above)
DEAD = [
    ('season2/metin2_map_milgyo_a', 153600, 1049600),
    ('season2/metin2_map_skipia_dungeon_01', 0, 1356800),
    ('season2/metin2_map_skipia_dungeon_01', 0, 1510400),
    ('season2/metin2_map_skipia_dungeon_01', 0, 1664000),
    ('metin2_map_skipia_dungeon_02', 153600, 1356800),
    ('metin2_map_skipia_dungeon_02', 153600, 1510400),
    ('metin2_map_skipia_dungeon_02', 153600, 1664000),
    ('metin2_map_skipia_dungeon_boss', 819200, 1100800),
    ('metin2_map_skipia_dungeon_boss', 819200, 1203200),
    ('metin2_map_skipia_dungeon_boss2', 819200, 1152000),
]

# apply.sh's order (linux-port/docker/mariadb/playerbot/apply.sh): zywioly_moby.sql, then these
ELEMENT_SQL = ['yohara_maps3_zywioly.sql', 'yohara_maps4_zywioly.sql', 'yohara_dung4_zywioly.sql',
               'yohara_pb_zywioly.sql', 'yohara_iluzja_zywioly.sql', 'yohara_crack_zywioly.sql']


def atlas_rows(text):
    """[(line index, name, x, y, w, h)] as the exe reads them (sscanf "%s %d %d %d %d")."""
    out = []
    for i, l in enumerate(text.replace('\r\n', '\n').split('\n')):
        t = l.split()
        if len(t) < 5:
            continue
        out.append((i, t[0], int(t[1]), int(t[2]), int(t[3]), int(t[4])))
    return out


def overlaps(text):
    rows = atlas_rows(text)
    bad = []
    for a in range(len(rows)):
        for b in range(a + 1, len(rows)):
            _, n1, x1, y1, w1, h1 = rows[a]
            _, n2, x2, y2, w2, h2 = rows[b]
            if x1 < x2 + w2 * CELL and x2 < x1 + w1 * CELL and y1 < y2 + h2 * CELL and y2 < y1 + h1 * CELL:
                bad.append(((n1, x1, y1, w1, h1), (n2, x2, y2, w2, h2)))
    return bad


def atlasinfo(b):
    """Drops the DEAD rows; keeps every other line and the file's line ends."""
    text = b.decode('cp1250')
    nl = '\r\n' if '\r\n' in text else '\n'
    lines = text.split(nl)
    dead = set(DEAD)
    keep = []
    for l in lines:
        t = l.split()
        if len(t) >= 5 and (t[0], int(t[1]), int(t[2])) in dead:
            continue
        keep.append(l)
    nb = nl.join(keep).encode('cp1250')
    return nb, len(lines) - len(keep)


SET_RE = re.compile(r'^UPDATE world\.mob_proto SET setRaceFlag = \(\(setRaceFlag \+ 0\) & ~129024\) \| (\d+) '
                    r'WHERE vnum IN \(([\d,]+)\);$')
CLR_RE = re.compile(r'^UPDATE world\.mob_proto SET setRaceFlag = \(setRaceFlag \+ 0\) & ~129024 WHERE vnum IN '
                    r'\(([\d,]+)\) AND \(setRaceFlag \+ 0\) & 129024 <> 0;$')
ALL_RE = re.compile(r'^UPDATE world\.mob_proto SET setRaceFlag = \(setRaceFlag \+ 0\) & ~129024 WHERE '
                    r'\(setRaceFlag \+ 0\) & 129024 <> 0 AND vnum NOT IN \(([\d,]+)\);$')


def server_elements():
    """{vnum: bits} - the element bits the server's mob_proto ends with (a vnum not in it: 0)."""
    have = set(f for f in os.listdir(SQL_DIR) if f.endswith('_zywioly.sql'))
    if have != set(ELEMENT_SQL):
        raise SystemExit('yfinal: the *_zywioly.sql files are %s, ELEMENT_SQL knows %s - add the new one in '
                         'apply.sh\'s order' % (sorted(have), ELEMENT_SQL))
    bits = {}
    for i, f in enumerate(['zywioly_moby.sql'] + ELEMENT_SQL):
        for l in open(os.path.join(SQL_DIR, f), encoding='utf-8'):
            l = l.strip()
            if not l.startswith('UPDATE'):
                continue
            m = SET_RE.match(l)
            if m:
                v = int(m.group(1))
                assert v & ~ELEMENT_MASK == 0, (f, v)
                for n in m.group(2).split(','):
                    bits[int(n)] = v
                continue
            m = CLR_RE.match(l)
            if m:
                for n in m.group(1).split(','):
                    bits[int(n)] = 0
                continue
            m = ALL_RE.match(l)
            if m and i == 0:
                keep = set(int(n) for n in m.group(1).split(','))
                for n in list(bits):
                    if n not in keep:
                        bits[n] = 0
                continue
            raise SystemExit('yfinal: %s - an UPDATE this step does not know: %s' % (f, l[:120]))
    return dict((k, v) for k, v in bits.items() if v)


def mob_records(b):
    import struct
    import m2pack
    magic, cnt, esize = struct.unpack_from('<4sII', b, 0)
    assert magic == b'MMPT', magic
    raw = bytearray(m2pack.mcoz_decode(b[12:12 + esize], MOB_KEY))
    assert len(raw) == cnt * MOB_RECORD, (len(raw), cnt)
    return cnt, raw


def mob_proto(b, want=None):
    import struct
    import m2pack
    want = server_elements() if want is None else want
    cnt, raw = mob_records(b)
    changed = 0
    for i in range(cnt):
        off = i * MOB_RECORD
        vnum = struct.unpack_from('<I', raw, off)[0]
        old = struct.unpack_from('<I', raw, off + MOB_RACE_FLAG)[0]
        new = (old & ~ELEMENT_MASK) | want.get(vnum, 0)
        if new != old:
            struct.pack_into('<I', raw, off + MOB_RACE_FLAG, new)
            changed += 1
    if not changed:
        return b, 0
    blob = m2pack.mcoz_encode(bytes(raw), MOB_KEY)
    return struct.pack('<4sII', b'MMPT', cnt, len(blob)) + blob, changed


def client_elements(b):
    """{vnum: bits} of a client mob_proto."""
    import struct
    cnt, raw = mob_records(b)
    out = {}
    for i in range(cnt):
        off = i * MOB_RECORD
        out[struct.unpack_from('<I', raw, off)[0]] = struct.unpack_from('<I', raw, off + MOB_RACE_FLAG)[0] & ELEMENT_MASK
    return out
