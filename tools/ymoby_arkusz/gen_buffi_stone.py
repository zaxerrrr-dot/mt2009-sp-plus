#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""gen_buffi_stone.py                      render the drop file from buffi_stone.json
gen_buffi_stone.py extract [--db CONTAINER] [--game CONTAINER]
                                           (re)read our world, write buffi_stone.json

MT2009_PLUS_BUFFI_STONE_DROP_V1: Kamien Duchowy Buffi (61031, mariadb/playerbot/buffi.sql - trains Buffi's skills
G1 -> P) drops from every Metin and boss of Zaklety Las (353) and of every map above it, the whole of Yohara too (the
owner, 21 October 2026) - only one that drops the plain Kamien Duchowy (50513) too (the owner, 21 October: "jesli z bossa
nie dropi zwykly kamien duchowy, to niech nie dropi tez buffi"; MT2009_PLUS_BUFFI_STONE_DROP_V2). Chances by the rule of cache/yohara/PROCENTY.md (ymoby_data.py): the same kind of item on our
monsters of the same kind - here the plain Kamien Duchowy (50513): the median of its Type drop rows on our Metins
(type 2) and, apart, on our bosses (type 0, rank >= 4). Writes

  linux-port/docker/game/buffi_stone/mob_drop_item.buffi_stone.txt
                                           groups MT2009_buffistone_<mob> of Type drop (one row, 61031 x1) - the engine
                                           adds them to the monster's other drop groups (item_manager_read_tables.cpp)

Which monsters: every Metin / boss a spawn file of a map of MAPS places (the game image's map/<folder>/*.txt and
data/dungeon/<dir>/*, groups unfolded with group.txt / group_group.txt; the Yohara generators' spawned.txt), plus
QUEST - the ones only a quest or the core spawns. A monster any other map spawns too stays out (it would drop the stone
there as well), and so does one that drops 61031 already (directly or through a special group).

extract reads: world.mob_proto of the running test world (docker exec <db> mariadb); the game image's
mob_drop_item.image.txt (as built - the live file may hold the operator's edits), special_item_group.image.txt,
map/index, map/, group.txt, group_group.txt and /opt/metin2/share/data/dungeon (docker exec <game>); our own
MT2009_buffistone_ groups are ignored, so a second extract after a deploy gives the same file.

Example: python3 tools/ymoby_arkusz/gen_buffi_stone.py extract
         python3 tools/ymoby_arkusz/gen_buffi_stone.py
"""
import argparse
import collections
import io
import json
import os
import statistics
import subprocess
import sys
import tarfile

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import gen_ymoby_arkusz as Y  # noqa: E402

REPO = Y.REPO
DATA = os.path.join(HERE, 'buffi_stone.json')
GAME = os.path.join(REPO, 'linux-port', 'docker', 'game')
DROP_OUT = os.path.join(GAME, 'buffi_stone', 'mob_drop_item.buffi_stone.txt')
GROUP = 'MT2009_buffistone_'
STONE = 61031          # Kamien Duchowy Buffi
SAME = 50513           # Kamien Duchowy - the same kind of item (its chances give ours)

# -- the maps: Zaklety Las (353, from 95; monsters 100-123) and every map above it - the Yohara branch's maps and
#    dungeons and the dungeons from level 95 / with monsters over the forest's. Below it and so out: Swiatynia Ochao
#    (209, the way into the forest), Przyladek Smoczego Ognia / Zbocze Gautama / Zatoka Nefrytowa / Gora Grzmotow
#    (301-304, monsters 95-110), Swiatynia Zodiaku (358, from the Teleporter at any level - Metins 20-130), Leze Smoka
#    (208, Beran-Setaou 93), the world bosses (Boss Swiata - maps 61-64) -----------------------------------------------
MAPS = {
    351: 'Czysciec Ognia (Razador)', 352: 'Lodowa Kraina (Nemere)', 353: 'Zaklety Las + Erebu',
    356: 'Schronienie Meley', 366: 'Starozytna Dzungla', 367: 'Obrona Statku (Hydra)',
    368: 'Port Nowego Kontynentu', 369: 'Twierdza Czerwonego Smoka (PB)', 370: 'Straznica Nemere (PB)',
    371: 'Zaklety Las (PB) + Erebu (PB)', 373: 'Dongan', 374: 'Opuszczona Twierdza', 376: 'Seoganland',
    377: 'Namgan', 378: 'Krolestwo Zywiolow', 379: 'Krolestwo Zywiolow', 380: 'Krolestwo Zywiolow',
    381: 'Plaskowyz Sil Natury', 382: 'Jaskinie Gnolli 1', 383: 'Jaskinie Gnolli 2', 384: 'Jaskinie Gnolli 3',
    385: 'Przelecz Yilad', 386: 'Wieza Sung Mahi - hala', 387: 'Wieza Sung Mahi', 388: 'Wawoz Polnocnego Wiatru',
    389: 'Rozpadlina Dusz', 390: '1. poziom Swiatyni Wezy', 391: 'Swiatynia Wezy',
    393: 'Schronienie Polnocnego Wiatru', 394: 'Zejscie Polnocnego Wiatru', 395: 'Glebie Polnocnego Wiatru',
    396: 'Tajemnicza Instancja', 397: 'Plaskowyz Iluzji', 398: 'Grota Wygnancow 2 (PB)',
    404: 'Zaklety Las (SZC) + Erebu (SZC)', 405: 'Grota Wygnancow 2 (SZC)', 406: 'Twierdza Czerwonego Smoka (SZC)',
    407: 'Straznica Nemere (SZC)',
}
# data/dungeon/<dir> -> its map (a directory not here belongs to a map below the forest)
DUNGEON_DIRS = {
    'razador_mt': 351, 'flame_dungeon': 351, 'nemere_mt': 352, 'meley': 356, 'starozytna_dzungla': 366,
    'defense_wave': 367, 'razador_pb': 369, 'nemere_pb': 370, 'jotun_pb': 371, 'beran_pb': 398,
    'jotun_szc': 404, 'beran_szc': 405, 'razador_szc': 406, 'nemere_szc': 407,
}
# the Yohara generators' "<map> <vnum>" lists (maps_wz: Wezowe Pole / Kraina Gigantow - below)
SPAWNED = ['yohara_zaklety', 'yohara_maps2', 'yohara_maps3', 'yohara_maps4', 'yohara_lokacje', 'yohara_dung4',
           'yohara_meley', 'yohara_pb', 'yohara_iluzja', 'yohara_crack', 'yohara_crack2']
# spawned by a quest / the core only
QUEST = {
    6091: 351, 8057: 351,                         # razador_dungeon: Razador, Metin Czysccia
    6191: 352, 6151: 352, 8058: 352, 20399: 352,  # nemere_dungeon: Nemere, Szel, Metin Mrozu, Lodowy Filar
    9713: 366, 9714: 366,                         # starozytna_dzungla: Krolewska Sowa, Krolowa Dzungli
    3957: 367, 3958: 367, 3959: 367,              # obrona_statku: Potomstwo Hydry
    3965: 367,                                    # Skarb Hydry - the Hydra's reward on the deck (the core)
}
EXCLUDE = {
    3960: 'Hydra drops nothing on the ship (MT2009_PLUS_HYDRA_NO_DROP_V1) - Skarb Hydry 3965 has the row',
    3961: 'ditto', 3962: 'ditto', 3963: 'ditto', 3964: 'ditto',
}


# -- extract --------------------------------------------------------------------------------------------------------
def game_tar(container, paths):
    """{path: bytes} of the files under the given paths of the game image"""
    raw = subprocess.run(['docker', 'exec', container, 'tar', 'cf', '-', '-C', '/opt/metin2/share'] + paths,
                         stdout=subprocess.PIPE, check=True).stdout
    out = {}
    with tarfile.open(fileobj=io.BytesIO(raw)) as t:
        for m in t.getmembers():
            if m.isfile():
                out[m.name] = t.extractfile(m).read()
    return out


def mob_groups(text, group_group):
    """{group vnum: {mob vnums}} of group.txt (the leader and the members) or group_group.txt (the groups)"""
    out, cur = {}, None
    lead = None
    for line in text.split('\n'):
        p = line.split()
        if not p:
            continue
        if p[0] == 'Group':
            cur, lead = None, None
        elif p[0] == 'Leader' and p[-1].isdigit():
            lead = int(p[-1])
            if cur is not None:
                out[cur].add(lead)
        elif p[0] == 'Vnum' and len(p) > 1 and p[1].isdigit():
            cur = int(p[1])
            out.setdefault(cur, set())
            if lead is not None:
                out[cur].add(lead)
        elif cur is not None and p[0].isdigit():
            nums = [int(x) for x in p[1:] if x.isdigit()]
            if nums:
                out[cur].add(nums[0] if group_group else nums[-1])
    return out


def regen_mobs(text, groups, ggroups):
    """the monsters of a regen file (m / g / r / s lines, the aggressive "ga" kind too)"""
    out = set()
    for line in text.split('\n'):
        p = line.split()
        if len(p) < 11 or not p[-1].isdigit() or p[0][:1] not in 'mgrs' or len(p[0]) > 2:
            continue
        v = int(p[-1])
        if p[0][0] == 'm':
            out.add(v)
        elif p[0][0] == 'g':
            out |= groups.get(v, set())
        else:
            for g in ggroups.get(v, ()):
                out |= groups.get(g, set())
    return out


def extract(a):
    mob = {}
    for p in Y.db_rows(a.db, 'SELECT vnum, locale_name, type, `rank`, level FROM world.mob_proto'):
        mob[int(p[0])] = dict(name=p[1], type=int(p[2]), rank=int(p[3]), level=int(p[4]))

    def kind(v):
        m = mob.get(v)
        if not m or m['type'] not in (0, 2):
            return None
        return 'stone' if m['type'] == 2 else ('boss' if m['rank'] >= 4 else None)

    files = game_tar(a.game, ['locale/poland/map', 'locale/poland/group.txt', 'locale/poland/group_group.txt',
                              'data/dungeon'])
    txt = lambda n: files[n].decode('latin-1')  # noqa: E731
    groups = mob_groups(txt('locale/poland/group.txt'), False)
    ggroups = mob_groups(txt('locale/poland/group_group.txt'), True)
    folder = {}
    for line in txt('locale/poland/map/index').split('\n'):
        p = line.split()
        if len(p) == 2 and p[0].isdigit():
            folder[p[1]] = int(p[0])
    where = collections.defaultdict(set)          # mob -> the maps placing it (0: some map below the forest)
    for name, b in files.items():
        parts = name.split('/')
        if name.startswith('locale/poland/map/') and len(parts) == 5 and parts[4].endswith('.txt') \
                and '.image.' not in parts[4]:
            m = folder.get(parts[3], 0)
        elif name.startswith('data/dungeon/'):
            m = DUNGEON_DIRS.get(parts[2], 0) if len(parts) > 3 else 0
        else:
            continue
        for v in regen_mobs(b.decode('latin-1'), groups, ggroups):
            where[v].add(m if m in MAPS else 0)
    for d in SPAWNED:
        for line in open(os.path.join(GAME, d, 'spawned.txt'), encoding='utf-8'):
            p = line.split()
            if len(p) >= 2 and p[0].isdigit() and p[1].isdigit():
                where[int(p[1])].add(int(p[0]) if int(p[0]) in MAPS else 0)
    for v, m in QUEST.items():
        where[v].add(m)

    # the chances: Kamien Duchowy's Type drop rows on our Metins / bosses
    img = Y.game_file(a.game, 'mob_drop_item.image.txt').decode('utf-8', 'replace')
    sig = Y.game_file(a.game, 'special_item_group.image.txt').decode('utf-8', 'replace')
    import gen_moby_global as M
    special = dict((g['mob'], [r[0] for r in g['rows']]) for g in M.groups(sig))

    def expand(tok, seen):
        if tok.isdigit():
            return {int(tok)}
        v = int(tok[1:]) if tok[1:].isdigit() else None
        if v is None or v in seen:
            return set()
        seen.add(v)
        out = set()
        for t in special.get(v, []):
            out |= expand(t, seen)
        return out

    ref, has, plain = collections.defaultdict(list), set(), set()
    for g in M.groups(img):
        if g['mob'] is None or g['name'].startswith(GROUP):
            continue
        for it, cnt, pct in g['rows']:
            if g['type'] == 'drop' and it == str(SAME) and kind(g['mob']):
                ref[kind(g['mob'])].append((cnt, float(pct)))
            got = expand(it, set())
            if STONE in got:
                has.add(g['mob'])
            if SAME in got:
                plain.add(g['mob'])
    chance = {}
    for k in ('stone', 'boss'):
        rows = ref[k]
        chance[k] = dict(count=int(statistics.median_low([c for c, _ in rows])),
                         value=statistics.median([p for _, p in rows]), rows=len(rows))

    adds, out = {}, []
    for v in sorted(where):
        k = kind(v)
        if not k or not (where[v] - {0}):
            continue
        maps = sorted(where[v] - {0})
        why = EXCLUDE.get(v) or ('a map below the forest spawns it too' if 0 in where[v] else None) or \
            ('drops 61031 already' if v in has else None) or \
            ('no plain Kamien Duchowy (50513) in its drop' if v not in plain else None)
        if why:
            out.append([v, mob[v]['name'], maps, why])
            continue
        adds[str(v)] = dict(name=mob[v]['name'], kind=k, level=mob[v]['level'], maps=maps)
    json.dump(dict(chance=chance, adds=adds, out=out), open(DATA, 'w', encoding='utf-8'), ensure_ascii=False,
              indent=0, sort_keys=True)
    print('extract: Kamien Duchowy %d on %d Metin rows (median %s), %d on %d boss rows (median %s); +%d monsters '
          '(%d Metins, %d bosses), %d out' % (
              SAME, chance['stone']['rows'], chance['stone']['value'], SAME, chance['boss']['rows'],
              chance['boss']['value'], len(adds), sum(1 for x in adds.values() if x['kind'] == 'stone'),
              sum(1 for x in adds.values() if x['kind'] == 'boss'), len(out)))


# -- render ---------------------------------------------------------------------------------------------------------
def render():
    data = json.load(open(DATA, encoding='utf-8'))
    ch = data['chance']
    val = lambda k: ('%.4f' % ch[k]['value']).rstrip('0').rstrip('.')  # noqa: E731
    out = [DROP_HEAD % dict(sv=val('stone'), sp=ch['stone']['value'] / 4, sn=ch['stone']['rows'],
                            bv=val('boss'), bp=ch['boss']['value'] / 4, bn=ch['boss']['rows'])]
    for v in sorted(data['adds'], key=int):
        a = data['adds'][v]
        out += ['Group\t%s%s' % (GROUP, v), '{',
                '\tMob\t%s\t-- %s (%s)' % (v, Y.ascii_pl(a['name']), ', '.join(str(m) for m in a['maps'])),
                '\tType\tdrop',
                '\t1\t%d\t%d\t%s\t-- Kamien Duchowy Buffi' % (STONE, ch[a['kind']]['count'], val(a['kind'])),
                '}']
    os.makedirs(os.path.dirname(DROP_OUT), exist_ok=True)
    with open(DROP_OUT, 'w', encoding='utf-8', newline='\r\n') as f:
        f.write('\n'.join(out) + '\n')
    print('render: %d groups (%d Metins v=%s, %d bosses v=%s)' % (
        len(data['adds']), sum(1 for x in data['adds'].values() if x['kind'] == 'stone'), val('stone'),
        sum(1 for x in data['adds'].values() if x['kind'] == 'boss'), val('boss')))


DROP_HEAD = """// MT2009_PLUS_BUFFI_STONE_DROP_V1: Kamien Duchowy Buffi (61031) from every Metin and boss of Zaklety Las (353) and
// of every map above it, the whole of Yohara too (the owner, 21 October 2026). GENERATED by
// tools/ymoby_arkusz/gen_buffi_stone.py - do not edit, rerun it. Added to the monster's own groups (Type drop: the
// engine merges the groups of one monster). Chances (cache/yohara/PROCENTY.md rule): the median of Kamien Duchowy's
// (50513) rows on our monsters of the same kind - Metins v = %(sv)s (%(sp)g %%, %(sn)d rows), bosses v = %(bv)s
// (%(bp)g %%, %(bn)d rows). A value v = v / 4 %% a kill before the level difference and the drop bonuses. The maps
// after each monster.
"""


def main():
    if len(sys.argv) > 1 and sys.argv[1] == 'extract':
        ap = argparse.ArgumentParser()
        ap.add_argument('cmd')
        ap.add_argument('--db', default='mt2009plustest-db')
        ap.add_argument('--game', default='mt2009plustest-game')
        extract(ap.parse_args())
    render()


if __name__ == '__main__':
    main()
