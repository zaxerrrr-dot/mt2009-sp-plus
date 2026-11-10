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
# 3) the new pack yfinal_mobs + gamedata/npclist.txt - two Metins' looks (the list's items 4 and 15):
#    * Metin Szacunku (8063) and the other metinstone_east_02..05 races (Seoganland/Namgan/Wawoz): their .msm swap the
#      skin to "D:/Ymir Work/monster2/metinstone_east/metinstone_east_0N.dds" (ShapeData PathName), the staging put
#      those textures under monster/ only - a white model. The four textures, GF's own files, at that path.
#    * Metin Drzewnych Stworzen / Metin Lasu (PB 8136/8137, SZC 8126/8127; GF's race metinstone_16): the base client
#      already has a race file monster/metinstone/metinstone_16.msm of its own (2.0.28's npclist names the race), and
#      the exe takes a name from the pack registered first - the base one: a grey stone with its red glow instead of
#      the green Metin wrapped in vines. GF's metinstone_16.msm/.dds under a name no client has (RACE_TREE), the four
#      vnums' npclist lines pointed at it.
# 4) the same pack - motions the official motlists name but no client has (the list's items 11 and 6b; syserr
#    "cannot find motion file"): GF's motlist slips kept as they are (the staged packs stay GF's), the named file
#    added as a copy of the motion meant (MOTION_STANDINS): empire_caocao_boss / smhtower_knight / smhtower_soldier /
#    smhtower_soldier2 "normal_attack2msa" (no dot) = their normal_attack2.msa; snakevalley_pawn / snaketemple_pawn
#    FRONT_DAMAGE "back_damage.msa" = their front_damage.msa (they had no hit motion); the Christmas cloud mount's
#    WAIT1/WAIT2 (0 %) wait1.msa/wait2.msa = its wait.msa; maze_keingnoll_boss SPECIAL5 special_attack3_1.msa = its
#    special_attack3.msa; the ice dragon NPC's SPAWN drop.msa = its loop.msa (its WAIT). Not fixable here (no client has them): GF's encrypted
#    npc_yut_result_02.mse (pet_fenfire_01/02.mse: EFFECT_STANDINS); lion.psd is a developer path inside a base-client file.
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
               'yohara_pb_zywioly.sql', 'yohara_iluzja_zywioly.sql', 'yohara_crack_zywioly.sql',
               'yohara_crack2_zywioly.sql',  # MT2009_PLUS_YOHARA_CRACK2_V1
               'yohara_zaklety_zywioly.sql', 'yohara_meley_zywioly.sql']


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
# MT2009_PLUS_YOHARA_RASY_V1: the dungeons' *_zywioly.sql also fix races (bits 0-10, e.g. Jotun Thrym a devil) - not this
# step's bits (the race comes with each dungeon's own client rows), so they are recognised and skipped.
RACE_RE = re.compile(r'^UPDATE world\.mob_proto SET setRaceFlag = \(\(setRaceFlag \+ 0\) & ~2047\) \| (\d+) '
                     r'WHERE vnum IN \(([\d,]+)\) AND \(setRaceFlag \+ 0\) & 2047 <> \1;$')
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
            m = RACE_RE.match(l)
            if m:
                assert int(m.group(1)) & ~2047 == 0, (f, l[:120])
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


# -- 3) the Metins' looks ------------------------------------------------------------------------------------------
GF = '/opt/metin2/cache/gf/Gameforge_26.1.11/_client/d_/'
NEW_PACK = 'yfinal_mobs'
RACE_TREE = 'mt2009_metin_tree'
TREE_VNUMS = (8126, 8127, 8136, 8137)
TREE_DIR = 'd:/ymir work/monster/metinstone/'


def _gf(name):
    return open(GF + name[len('d:/'):], 'rb').read()


MOTION_STANDINS = dict(
    [('d:/ymir work/monster2/%s/normal_attack2msa' % r, 'd:/ymir work/monster2/%s/normal_attack2.msa' % r)
     for r in ('empire_caocao_boss', 'smhtower_knight', 'smhtower_soldier', 'smhtower_soldier2')] +
    [('d:/ymir work/monster2/%s/back_damage.msa' % r, 'd:/ymir work/monster2/%s/front_damage.msa' % r)
     for r in ('snakevalley_pawn', 'snaketemple_pawn')] +
    [('d:/ymir work/npc_mount/christmas_2024_cloud/wait%d.msa' % n, 'd:/ymir work/npc_mount/christmas_2024_cloud/wait.msa')
     for n in (1, 2)] +
    [('d:/ymir work/monster2/maze_keingnoll_boss/special_attack3_1.msa',
      'd:/ymir work/monster2/maze_keingnoll_boss/special_attack3.msa'),
     ('d:/ymir work/npc2/whitedragon_npc_ice/drop.msa', 'd:/ymir work/npc2/whitedragon_npc_ice/loop.msa')])


# MT2009_PLUS_FENFIRE_EFFECT_V1 (the owner's syserr of 4 November 2026): the Halloween 2021 will-o'-the-wisp pet
# (npc_pet/halloween_2021_fenfire_01/02.msm, npclist 34150-34152) attaches pet_fenfire_01/02.mse to its bone "efff" -
# GF's encrypted files, in no client ("CEffectManager::RegisterEffect - LoadScript(...pet_fenfire_0N.mse) Error"). The
# GF pet flame of the three-eyed cat stands in: the orange one for _01, the blue one for _02 (its texture
# effect/monster2/12_a05_burn_01.dds is in the client - zodiak_maps).
EFFECT_STANDINS = {
    'd:/ymir work/effect/pet/pet_fenfire_01.mse': 'd:/ymir work/effect/pet/pet_cat3eye_fire.mse',
    'd:/ymir work/effect/pet/pet_fenfire_02.mse': 'd:/ymir work/effect/pet/pet_cat3eye_fire_blue.mse',
}


def motlist_missing(text, folder, exists):
    """[(line, file)] of a motlist whose file is in no pack (exists(name) -> bool)."""
    out = []
    for l in text.replace('\r', '').split('\n'):
        t = l.split()
        if len(t) >= 3 and not exists(folder + t[2].lower()):
            out.append((l.strip(), t[2]))
    return out


def new_pack_files():
    """{in-pack name: bytes} of yfinal_mobs."""
    out = {}
    for k, src in MOTION_STANDINS.items():
        out[k] = _gf(src)
    for k, src in EFFECT_STANDINS.items():
        out[k] = _gf(src)
    for n in range(2, 6):
        k = 'd:/ymir work/monster2/metinstone_east/metinstone_east_%02d.dds' % n
        out[k] = _gf(k)
    msm = _gf(TREE_DIR + 'metinstone_16.msm').decode('latin-1')
    assert msm.count('"metinstone_16.dds"') == 1, 'GF metinstone_16.msm changed'
    out[TREE_DIR + RACE_TREE + '.msm'] = msm.replace('"metinstone_16.dds"', '"%s.dds"' % RACE_TREE).encode('latin-1')
    out[TREE_DIR + RACE_TREE + '.dds'] = _gf(TREE_DIR + 'metinstone_16.dds')
    return out


def npclist(b):
    """The tree Metins' vnum lines -> RACE_TREE, its race line (source folder metinstone) added; line ends kept."""
    text = b.decode('cp1250')
    nl = '\r\n' if '\r\n' in text else '\n'
    lines = text.split(nl)
    tail = lines and lines[-1] == ''
    if tail:
        lines.pop()
    want = dict(('%d' % v, '%d\t%s' % (v, RACE_TREE)) for v in TREE_VNUMS)
    race = '0\t%s\tmetinstone' % RACE_TREE
    changed = 0
    seen = set()
    for i, l in enumerate(lines):
        t = l.split('\t')
        k = t[0].strip()
        if k in want:
            seen.add(k)
            if l != want[k]:
                lines[i] = want[k]
                changed += 1
        elif k == '0' and len(t) > 1 and t[1].strip() == RACE_TREE:
            seen.add(RACE_TREE)
    if RACE_TREE not in seen:
        # with the other race lines (the vnum-0 block at the top of the file)
        last0 = max([i for i, l in enumerate(lines) if l.split('\t')[0].strip() == '0'] or [-1])
        lines.insert(last0 + 1, race)
        changed += 1
    for k in sorted(set(want) - seen):
        lines.append(want[k])
        changed += 1
    if tail:
        lines.append('')
    return nl.join(lines).encode('cp1250'), changed
