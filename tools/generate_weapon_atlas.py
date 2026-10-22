#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""generate_weapon_atlas.py [--game CONTAINER] [--db CONTAINER] [--out FILE] [--check]

The bots' weapon atlas: linux-port/overlays/playerbot/src/game/src/playerbot_weapon_atlas.h (the header says what it is;
playerbot_weapon_goal.h reads it). Every weapon family of this world (world.item_proto, the +0 vnums), who may carry it
(the anti-flags), and where a bot can get one: a village merchant on a map the bots walk, the common drop of a monster
rank and level band that stands on such a map, a monster or a chest there, a Metin stone there, or only on maps no bot
goes to.

MT2009_PLUS_BOT_YOHARA_GEAR2_V1 (the owner, 22 October 2026: "Bronie i zbroje 96-120: zrodla to lochy PB, statuy
Plaskowyzu Iluzji, Statua Wezy itd. - przegeneruj atlas z tymi zrodlami, zeby boty je znaly"): the generator was never
in the repository (the header was made once, in update 0.2) - this is it again, with two sources more:
  0x40 craft    - made by an NPC: a cube recipe's reward (Statua Fabryki Broni 20473 / Kowala Zbroi 20474 on Plaskowyz
                  Iluzji - the Smok Mroku pieces -, Statua Wezy 20807 - the serpent ones -, Kawuco, Jaharr ...) or the
                  result of Seon-Pyeong's elite step (refine sets 39900-39999, 501, 530: a +9 dragged onto him - the
                  cyanite weapons); the source "mob" is the NPC, the map where it stands;
  0x80 dungeon  - dropped (or in a chest dropped) in a dungeon a bot enters only with a party or a person: the PB and SZC
                  dungeons, Meley, the Zodiac temple, the Demon Tower, the Catacomb ... (DUNGEON_DIRS / DUNGEON_MAPS).
A family whose only sources are these two is the market's for a bot (playerbot_weapon_goal.h asks the ledger).

Sources read (read only): the running test world - world.item_proto / mob_proto / shop / shop_item (docker exec <db>
mariadb), and the game image's assembled share (docker exec <game> tar): locale/poland mob_drop_item.txt,
common_drop_item.txt, special_item_group.txt, cube.txt, group.txt, group_group.txt, map/index, map/*/{regen,stone,boss,
npc}.txt, data/dungeon/** spawn files.

--check: compare with the header in the repository (row by row, the changed rows listed) and write nothing.
Example: python3 tools/generate_weapon_atlas.py
"""
import argparse
import io
import os
import re
import subprocess
import sys
import tarfile
from collections import defaultdict

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(HERE)
OUT = os.path.join(REPO, 'linux-port', 'overlays', 'playerbot', 'src', 'game', 'src', 'playerbot_weapon_atlas.h')
SHARE = '/opt/metin2/share'
LOCALE = 'locale/poland'

SRC_MERCHANT, SRC_COMMON, SRC_DROP, SRC_CHEST, SRC_STONE, SRC_ELSEWHERE, SRC_CRAFT, SRC_DUNGEON = \
    0x01, 0x02, 0x04, 0x08, 0x10, 0x20, 0x40, 0x80
SRC_NAMES = ((SRC_MERCHANT, 'kupiec'), (SRC_COMMON, 'wspolny'), (SRC_DROP, 'potwor'), (SRC_CHEST, 'skrzynia'),
             (SRC_STONE, 'metin'), (SRC_ELSEWHERE, 'poza'), (SRC_CRAFT, 'wytwarzanie'), (SRC_DUNGEON, 'loch'))
CLS_WARRIOR, CLS_ASSASSIN, CLS_SURA, CLS_SHAMAN = 0x01, 0x02, 0x04, 0x08
ANTI_WARRIOR, ANTI_ASSASSIN, ANTI_SURA, ANTI_SHAMAN = 4, 8, 16, 32
WEAPON_SUBTYPES = (0, 1, 2, 3, 4, 5, 7)     # sword, dagger, bow, two-handed, bell, fan, lance (no Lycan claw, no arrows)
RANKS = ('PAWN', 'S_PAWN', 'KNIGHT', 'S_KNIGHT', 'BOSS', 'KING')
MOB_TYPE_MONSTER, MOB_TYPE_NPC, MOB_TYPE_STONE = 0, 1, 2
ELITE_SETS = set([501, 530]) | set(range(39900, 40000))     # constants.cpp IsEliteRefine (server-patches/seonpyeong)

# The maps the bots walk (fields and villages the travel draw, the handover and the Sung Ma bots use): a source there is
# the bot's own. Every other map with spawns is "poza" (elsewhere); a dungeon's also "loch".
BOT_MAPS = set([1, 3, 4, 5, 21, 23, 24, 25, 41, 43, 44, 45, 61, 62, 63, 64, 65, 67, 68, 70, 71, 72, 73, 80, 104, 108,
                109, 209, 301, 302, 303, 304, 353, 373, 374, 376, 377, 385, 388, 389, 393, 394])
# Dungeons a bot enters with a party or a person only (map index): a source there is "loch".
DUNGEON_MAPS = set([66, 79, 208, 216, 217, 351, 352, 356, 358, 363, 364, 365, 366, 158, 367, 368, 369, 370, 371, 378,
                    379, 380, 381, 382, 383, 384, 386, 387, 390, 391, 395, 396, 398, 404, 405, 406, 407])
# The quest dungeons' spawn folders (data/dungeon/<dir>) and the map each is an instance of.
DUNGEON_DIRS = {'beran_pb': 398, 'jotun_pb': 371, 'razador_pb': 369, 'nemere_pb': 370, 'jotun_szc': 404,
                'beran_szc': 405, 'razador_szc': 406, 'nemere_szc': 407, 'meley': 356, 'flame_dungeon': 351,
                'razador_mt': 351, 'nemere_mt': 352, 'devilcatacomb': 216, 'defense_wave': 367, 'zodiac': 358,
                'bluedragon_mt': 208, 'monkey': 108, 'wzgorze_wukonga': 364, 'ruiny_skorpiona': 365,
                'starozytna_dzungla': 366, 'ruiny_atlantydy': 158, 'biblioteka_wiedzy': 363}

PL = str.maketrans('ąćęłńóśźżĄĆĘŁŃÓŚŹŻ', 'acelnoszzACELNOSZZ')


def ascii_pl(s):
    return s.translate(PL).encode('ascii', 'replace').decode('ascii')


def db_rows(container, sql):
    out = subprocess.run(['docker', 'exec', '-i', container, 'sh', '-c',
                          'mariadb -uroot -p"$MARIADB_ROOT_PASSWORD" -B -N world'], input=sql.encode(),
                         stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, check=True).stdout.decode('utf-8')
    return [l.split('\t') for l in out.split('\n') if l]


def share_files(container):
    """{path relative to the share: bytes} - the locale files and every spawn file, one tar over docker exec"""
    script = ('cd %s && tar -cf - %s/mob_drop_item.txt %s/common_drop_item.txt %s/special_item_group.txt %s/cube.txt '
              '%s/group.txt %s/group_group.txt %s/map/index $(ls -d %s/map/*/ | sed "s#/\\$##" | while read d; do '
              'for f in regen.txt stone.txt boss.txt npc.txt; do [ -f "$d/$f" ] && echo "$d/$f"; done; done) '
              'data/dungeon' % ((SHARE,) + (LOCALE,) * 8))
    raw = subprocess.run(['docker', 'exec', container, 'sh', '-c', script], stdout=subprocess.PIPE,
                         stderr=subprocess.DEVNULL, check=True).stdout
    files = {}
    with tarfile.open(fileobj=io.BytesIO(raw)) as tar:
        for m in tar.getmembers():
            if m.isfile():
                files[m.name] = tar.extractfile(m).read()
    return files


def text(b):
    return b.decode('cp1250', 'replace').replace('\r', '')


def parse_groups(t, key):
    """[(key vnum, [(member fields...)], type)] of a Group { ... } file"""
    out, cur, items, kind = [], None, [], ''
    for line in t.split('\n'):
        s = line.split('--')[0].split('#')[0].strip()
        if not s:
            continue
        if s.startswith('Group'):
            cur, items, kind = None, [], ''
            continue
        if s == '{':
            continue
        if s == '}':
            if cur is not None:
                out.append((cur, items, kind))
            cur = None
            continue
        p = s.split()
        if p[0].lower() == key.lower() and len(p) > 1 and p[1].isdigit():
            cur = int(p[1])
        elif p[0].lower() == 'type' and len(p) > 1:
            kind = p[1].lower()
        elif p[0].isdigit():
            items.append(p)
    return out


def spawn_lines(t):
    """[(kind, vnum)] of a regen / stone / boss / npc file"""
    out = []
    for line in t.split('\n'):
        p = line.split('//')[0].split()
        if len(p) >= 11 and p[0] in ('m', 'g', 'r', 's', 'ma', 'ga') and p[10].isdigit():
            out.append((p[0][0], int(p[10])))
    return out


def load(game, db):
    files = share_files(game)
    loc = lambda n: text(files.get('%s/%s' % (LOCALE, n), b''))
    items = {}
    for r in db_rows(db, 'SELECT vnum, locale_name, type, subtype, limittype0, limitvalue0, limittype1, limitvalue1, '
                         'antiflag, refined_vnum, refine_set FROM item_proto'):
        v = int(r[0])
        lv = int(r[5]) if r[4] == '1' else (int(r[7]) if r[6] == '1' else 0)
        items[v] = dict(name=r[1], type=int(r[2]), sub=int(r[3]), level=lv, anti=int(r[8]), refined=int(r[9]),
                        rset=int(r[10]))
    mobs = {}
    for r in db_rows(db, 'SELECT vnum, locale_name, `rank`, type, level FROM mob_proto'):
        mobs[int(r[0])] = dict(name=r[1], rank=int(r[2]), type=int(r[3]), level=int(r[4]))
    shops = defaultdict(set)        # item vnum -> npc vnums selling it
    for r in db_rows(db, 'SELECT si.item_vnum, s.npc_vnum FROM shop_item si JOIN shop s ON s.vnum = si.shop_vnum'):
        shops[int(r[0])].add(int(r[1]))
    mapdirs = {}
    for line in loc('map/index').split('\n'):
        p = line.split()
        if len(p) >= 2 and p[0].isdigit():
            mapdirs[p[1].lower()] = int(p[0])
    # group / group_group: a group vnum -> member vnums; a group_group -> groups
    groups = dict((g, [int(m[1]) for m in mem if len(m) > 1 and m[1].isdigit()] +
                   [int(m[2]) for m in mem if len(m) > 2 and not m[1].isdigit() and m[2].isdigit()])
                  for g, mem, _ in parse_groups(loc('group.txt'), 'Vnum'))
    for g, mem, _ in parse_groups(loc('group.txt'), 'Leader'):
        pass
    leaders = {}
    for block in re.findall(r'\{([^}]*)\}', loc('group.txt')):
        m = re.search(r'Leader\s+\S+\s+(\d+)', block)
        v = re.search(r'Vnum\s+(\d+)', block)
        if m and v:
            leaders[int(v.group(1))] = int(m.group(1))
    for g, l in leaders.items():
        groups.setdefault(g, []).append(l)
    ggroups = dict((g, [int(m[1]) for m in mem if len(m) > 1 and m[1].isdigit()])
                   for g, mem, _ in parse_groups(loc('group_group.txt'), 'Vnum'))
    spawns = defaultdict(lambda: defaultdict(int))       # mob vnum -> map -> spawn lines
    npc_at = defaultdict(set)                            # npc vnum -> maps

    def add_spawn(mapidx, kind, vnum, is_npc_file):
        if kind == 'g':
            for m in groups.get(vnum, []):
                spawns[m][mapidx] += 1
        elif kind == 'r':
            for g in ggroups.get(vnum, []):
                for m in groups.get(g, []):
                    spawns[m][mapidx] += 1
        else:
            spawns[vnum][mapidx] += 1
            if is_npc_file:
                npc_at[vnum].add(mapidx)

    for path, b in files.items():
        p = path.split('/')
        if p[:3] == ['locale', 'poland', 'map'] and len(p) == 5:
            mi = mapdirs.get(p[3].lower())
            if mi is None:
                continue
        elif p[:2] == ['data', 'dungeon'] and len(p) >= 3:
            d = p[2].replace('_regen.txt', '') if len(p) == 3 else p[2]
            mi = DUNGEON_DIRS.get(d, 66 if d.startswith('deviltower') else None)
            if mi is None:
                continue
        else:
            continue
        for kind, vnum in spawn_lines(text(b)):
            add_spawn(mi, kind, vnum, p[-1] == 'npc.txt')
    drops = defaultdict(set)        # item vnum -> mob vnums dropping it
    for mob, mem, kind in parse_groups(loc('mob_drop_item.txt'), 'Mob'):
        for m in mem:
            if len(m) > 1 and m[1].isdigit():
                drops[int(m[1])].add(mob)
    chests = defaultdict(set)       # item vnum -> chest vnums holding it
    for chest, mem, kind in parse_groups(loc('special_item_group.txt'), 'Vnum'):
        for m in mem:
            if len(m) > 1 and m[1].isdigit():
                chests[int(m[1])].add(chest)
    common = []                     # (rank, min level, max level, vnum)
    for line in loc('common_drop_item.txt').split('\n')[1:]:
        p = line.split('\t')
        for k in range(4):
            c = p[k * 6:k * 6 + 6]
            if len(c) >= 5 and c[1].strip().isdigit() and c[4].strip().isdigit():
                common.append((k, int(c[1]), int(c[2]), int(c[4])))
    cube = defaultdict(set)         # reward vnum -> npc vnums
    npc = None
    for line in loc('cube.txt').split('\n'):
        p = line.split()
        if not p:
            continue
        if p[0] == 'npc' and len(p) > 1 and p[1].isdigit():
            npc = int(p[1])
        elif p[0] == 'reward' and len(p) > 1 and p[1].isdigit() and npc:
            cube[int(p[1])].add(npc)
        elif p[0] == 'section':
            npc = None
    return items, mobs, shops, spawns, npc_at, drops, chests, common, cube


def families(items):
    out = []
    for v, it in sorted(items.items()):
        if it['type'] != 1 or it['sub'] not in WEAPON_SUBTYPES or v % 10 != 0 or not it['name'].endswith('+0'):
            continue
        out.append(v)
    return out


def class_mask(anti):
    m = 0
    if not anti & ANTI_WARRIOR:
        m |= CLS_WARRIOR
    if not anti & ANTI_ASSASSIN:
        m |= CLS_ASSASSIN
    if not anti & ANTI_SURA:
        m |= CLS_SURA
    if not anti & ANTI_SHAMAN:
        m |= CLS_SHAMAN
    return m


def atlas(data):
    items, mobs, shops, spawns, npc_at, drops, chests, common, cube = data
    rows = []
    common_mobs = defaultdict(list)     # rank -> [(level, mob)] standing on a bot map
    for mob, maps in spawns.items():
        mp = mobs.get(mob)
        if mp and mp['type'] == MOB_TYPE_MONSTER and mp['rank'] < 4 and any(m in BOT_MAPS for m in maps):
            common_mobs[mp['rank']].append(mp['level'])
    for base in families(items):
        it = items[base]
        fam = [v for v in range(base, base + 10) if v in items and items[v]['type'] == 1]
        src = 0
        best = (0, 0, 0)        # spawn lines, mob, map
        maps_dropping = set()

        def mob_source(mob, flag_here):
            nonlocal src, best
            mp = mobs.get(mob)
            here = False
            if not spawns.get(mob):
                src |= SRC_ELSEWHERE | SRC_DUNGEON      # spawned by a quest only: a dungeon's boss, an event's
            for m, n in spawns.get(mob, {}).items():
                if m in BOT_MAPS:
                    here = True
                    if (n, -mob) > (best[0], -best[1]):
                        best = (n, mob, m)
                else:
                    src_flag = SRC_ELSEWHERE | (SRC_DUNGEON if m in DUNGEON_MAPS else 0)
                    src |= src_flag
                maps_dropping.add(m)
            if here:
                src |= flag_here if not (mp and mp['type'] == MOB_TYPE_STONE and flag_here == SRC_DROP) else SRC_STONE

        for v in fam:
            for npc in shops.get(v, ()):
                if any(m in BOT_MAPS for m in npc_at.get(npc, ())):
                    src |= SRC_MERCHANT
            for mob in drops.get(v, ()):
                mob_source(mob, SRC_DROP)
            for chest in chests.get(v, ()):
                if not drops.get(chest) and not chests.get(chest):
                    src |= SRC_ELSEWHERE | SRC_DUNGEON  # a chest no monster drops: a dungeon's or a quest's reward
                for mob in drops.get(chest, ()):
                    mob_source(mob, SRC_CHEST)
                for outer in chests.get(chest, ()):         # a chest inside a chest, one level
                    for mob in drops.get(outer, ()):
                        mob_source(mob, SRC_CHEST)
            for rank, lo, hi, cv in common:
                if cv == v and any(lo <= lv <= hi for lv in common_mobs.get(rank, ())):
                    src |= SRC_COMMON
            for npc in cube.get(v, ()):
                src |= SRC_CRAFT
                if best[1] == 0:
                    at = sorted(npc_at.get(npc, ()))
                    best = (0, npc, at[0] if at else 0)
        # Seon-Pyeong's elite step: a +9 whose refined vnum is this family's +0
        for v, src_it in items.items():
            if src_it['refined'] == base and src_it['rset'] in ELITE_SETS:
                src |= SRC_CRAFT
                if best[1] == 0:
                    best = (0, 20091, 64)
                break
        rows.append(dict(base=base, sub=it['sub'], level=it['level'], cls=class_mask(it['anti']), src=src,
                         mob=best[1], map=best[2], name=ascii_pl(it['name'])))
    return rows


def render(rows):
    L = ['// playerbot_weapon_atlas.h - generated by tools/generate_weapon_atlas.py.',
         '// Every weapon family of this world (world.item_proto, +0 vnums), who may',
         '// carry it (the anti-flags), and where a bot can get one: a village merchant',
         '// on a map the bots walk, the common drop of a monster rank and level band',
         '// that stands on such a map, a monster or a chest there, or only on maps no',
         '// bot goes to. Read with world.mob_proto, world.shop and the spawn files of',
         '// every map. Do not edit by hand; run the generator.',
         '// MT2009_PLUS_BOT_YOHARA_GEAR2_V1: two sources more - made by an NPC (a cube',
         '// recipe, Seon-Pyeong\'s +9 step; the "mob" is the NPC) and a dungeon a bot',
         '// enters only with a party or a person (the PB / SZC dungeons, Meley ...).',
         '#ifndef PLAYERBOT_WEAPON_ATLAS_H',
         '#define PLAYERBOT_WEAPON_ATLAS_H',
         '',
         'namespace',
         '{',
         '\tconst WORD PLAYERBOT_WEAPON_SOURCE_MERCHANT = 0x01;',
         '\tconst WORD PLAYERBOT_WEAPON_SOURCE_COMMON = 0x02;',
         '\tconst WORD PLAYERBOT_WEAPON_SOURCE_DROP = 0x04;',
         '\tconst WORD PLAYERBOT_WEAPON_SOURCE_CHEST = 0x08;',
         '\tconst WORD PLAYERBOT_WEAPON_SOURCE_STONE = 0x10;',
         '\tconst WORD PLAYERBOT_WEAPON_SOURCE_ELSEWHERE = 0x20;',
         '\tconst WORD PLAYERBOT_WEAPON_SOURCE_CRAFT = 0x40;     // MT2009_PLUS_BOT_YOHARA_GEAR2_V1',
         '\tconst WORD PLAYERBOT_WEAPON_SOURCE_DUNGEON = 0x80;   // MT2009_PLUS_BOT_YOHARA_GEAR2_V1',
         '\tconst BYTE PLAYERBOT_WEAPON_CLASS_WARRIOR = 0x01;',
         '\tconst BYTE PLAYERBOT_WEAPON_CLASS_ASSASSIN = 0x02;',
         '\tconst BYTE PLAYERBOT_WEAPON_CLASS_SURA = 0x04;',
         '\tconst BYTE PLAYERBOT_WEAPON_CLASS_SHAMAN = 0x08;',
         '',
         '\tstruct TPlayerBotWeaponFamily',
         '\t{',
         '\t\tDWORD dwBaseVnum;   // the +0 of the family',
         '\t\tBYTE bSubType;',
         '\t\tBYTE bLevel;',
         '\t\tBYTE bClassMask;    // PLAYERBOT_WEAPON_CLASS_*',
         '\t\tWORD wSources;      // PLAYERBOT_WEAPON_SOURCE_*',
         '\t\tDWORD dwSourceMob;  // the monster on a bot map with the most spawn points (a crafted one\'s NPC), 0 if none',
         '\t\tWORD wSourceMap;    // where that monster stands, 0 if none',
         '\t};',
         '',
         '\tconst TPlayerBotWeaponFamily PLAYERBOT_WEAPON_ATLAS[] = {']
    for r in rows:
        names = ','.join(n for f, n in SRC_NAMES if r['src'] & f) or 'brak'
        L.append('\t\t{ %5d, %d, %3d, 0x%02x, 0x%02x, %5d, %3d },\t// %s (%s)' % (
            r['base'], r['sub'], r['level'], r['cls'], r['src'], r['mob'], r['map'], r['name'], names))
    L += ['\t};', '}', '', '#endif', '']
    return '\n'.join(L)


def read_header(path):
    rows = {}
    for line in open(path, encoding='ascii', errors='replace'):
        m = re.match(r'\s*\{\s*(\d+),\s*(\d+),\s*(\d+),\s*0x([0-9a-f]+),\s*0x([0-9a-f]+),\s*(\d+),\s*(\d+)\s*\},\s*// (.*)$',
                     line)
        if m:
            rows[int(m.group(1))] = (int(m.group(3)), int(m.group(4), 16), int(m.group(5), 16), int(m.group(6)),
                                     int(m.group(7)), m.group(8).strip())
    return rows


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--game', default='mt2009plustest-game')
    ap.add_argument('--db', default='mt2009plustest-db')
    ap.add_argument('--out', default=OUT)
    ap.add_argument('--check', action='store_true')
    a = ap.parse_args()
    rows = atlas(load(a.game, a.db))
    if a.check:
        old = read_header(a.out)
        same = changed = new = 0
        for r in rows:
            o = old.get(r['base'])
            if o is None:
                new += 1
                print('new     %5d lv%3d src=0x%02x mob=%d map=%d %s' % (r['base'], r['level'], r['src'], r['mob'], r['map'],
                                                                    r['name']))
            elif (o[0], o[1], o[2] & 0x3f) == (r['level'], r['cls'], r['src'] & 0x3f):
                same += 1
            else:
                changed += 1
                print('changed %5d %s -> lv%d cls=0x%02x src=0x%02x mob=%d map=%d' % (r['base'], o, r['level'], r['cls'],
                                                                                   r['src'], r['mob'], r['map']))
        gone = sorted(set(old) - set(r['base'] for r in rows))
        print('rows=%d same=%d changed=%d new=%d gone=%s' % (len(rows), same, changed, new, gone))
        return
    with open(a.out, 'w', encoding='ascii', newline='\n') as f:
        f.write(render(rows))
    print('%s: %d families' % (os.path.relpath(a.out, REPO), len(rows)))


if __name__ == '__main__':
    main()
