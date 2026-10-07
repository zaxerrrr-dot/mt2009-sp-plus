#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""MT2009_PLUS_ELEMENTS_V1 - the monsters' elements (setRaceFlag bits 11-16) by the owner's rules
(7 October 2026), replacing the blanket list of Digi Rasta's port ("Zywioly i talizmany",
nowy-system 0.28.0, Autor: Digi Rasta; his wiki list is zywioly_wiki.json here).

Rules:
  a. every boss (mob_proto rank >= 4, a monster) on Digi Rasta's wiki list gets its wiki element;
  b. ordinary monsters get an element only on these maps (every monster vnum their regen / boss /
     stone files spawn, groups and group-groups unfolded, the summons of those monsters; never a
     Metin stone or an NPC):
       Grota Wygnancow 1 (72) and 2 (73)            -> lightning
       Swiatynia Ochao (209), Zaczarowany Las (362) -> wind
     a boss there keeps its wiki element; one not on the wiki list takes the map's;
  c. dungeons - every monster and boss of the dungeon (its map files, its quest's regen files in
     data/dungeon/<dir>, the monster vnums >= 1000 its quest spawns itself, their summons), the
     dungeon's element winning over the wiki list:
       Nemere (352, nemere_dungeon.quest)                         -> ice
       Leze Smoka (208, Blue Dragon, blue_dragon_lair.quest)      -> lightning
       Starozytna Dzungla (366, starozytna_dzungla.quest)         -> wind
  d. nothing else has an element: the SQL clears bits 11-16 on every other mob.

A vnum carries its element everywhere it spawns; the report lists the mapped vnums that also
spawn on other maps or dungeons.

Input (the BUILT share of the game image - what the server really spawns):
  python3 tools/zywioly/gen_zywioly_moby.py --container mt2009plustest-game --mobs mobs.tsv
  python3 tools/zywioly/gen_zywioly_moby.py --share /path/to/opt/metin2/share --mobs mobs.tsv
mobs.tsv (world.mob_proto, tab separated: vnum rank type summon raceflag name):
  docker exec -i <db> mariadb -uroot -p... -N world --default-character-set=latin1 -e "select vnum,
    rank, type, summon, setRaceFlag+0, replace(convert(cast(convert(locale_name using latin1) as
    binary) using cp1250),'\\t',' ') from mob_proto order by vnum" > mobs.tsv
Output:
  linux-port/docker/mariadb/playerbot/zywioly_moby.sql  (apply.sh, every start)
  tools/zywioly/zywioly_moby.json                       ({vnum: bits}, the client tool's input:
                                                         client-patches/client-2.0.30/tools/zywioly)
  the report on stdout (--report FILE writes it too).
"""
import argparse
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(os.path.dirname(HERE))
QUESTS = os.path.join(REPO, 'linux-port', 'docker', 'game', 'quest')
SQL_OUT = os.path.join(REPO, 'linux-port', 'docker', 'mariadb', 'playerbot', 'zywioly_moby.sql')
JSON_OUT = os.path.join(HERE, 'zywioly_moby.json')
WIKI = os.path.join(HERE, 'zywioly_wiki.json')

ELEC, FIRE, ICE, WIND, EARTH, DARK = (1 << 11), (1 << 12), (1 << 13), (1 << 14), (1 << 15), (1 << 16)
MASK = ELEC | FIRE | ICE | WIND | EARTH | DARK
NAMES = {ELEC: 'Blyskawica', FIRE: 'Ogien', ICE: 'Lod', WIND: 'Wiatr', EARTH: 'Ziemia', DARK: 'Mrok'}
MOB_MONSTER, MOB_STONE = 0, 2
RANK_BOSS = 4

# (label, map indexes, element)
MAP_RULES = (
    ('Grota Wygnancow 1/2', (72, 73), ELEC),
    ('Swiatynia Ochao + Zaczarowany Las', (209, 362), WIND),
)
# (label, map index, data/dungeon dirs, quest, extra lua (enemy = vnum lines), element)
DUNGEON_RULES = (
    ('Nemere', 352, ('nemere_mt',), 'nemere_dungeon.quest', None, ICE),
    ('Leze Smoka (Blue Dragon)', 208, ('bluedragon_mt',), 'blue_dragon_lair.quest', 'BlueDragon.lua', ELEC),
    ('Starozytna Dzungla', 366, ('starozytna_dzungla',), 'starozytna_dzungla.quest', None, WIND),
)
SHARE_PARTS = ('locale/poland/map', 'locale/poland/group.txt', 'locale/poland/group_group.txt',
               'locale/poland/special_spawns.txt', 'locale/poland/BlueDragon.lua', 'data/dungeon')
SKIP_MAP_FILES = ('setting.txt', 'town.txt', 'mapproperty.txt')


def read_text(path):
    with open(path, 'rb') as f:
        return f.read().decode('cp1250', 'replace')


def load_mobs(path):
    mobs = {}
    for line in read_text(path).splitlines():
        p = line.split('\t')
        if len(p) < 5 or not p[0].strip().isdigit():
            continue
        mobs[int(p[0])] = dict(rank=int(p[1]), type=int(p[2]), summon=int(p[3] or 0), flag=int(p[4]),
                               name=p[5] if len(p) > 5 else '')
    return mobs


def load_blocks(path):
    """group.txt / group_group.txt: {vnum: [member tokens lines]} (CTextFileLoader blocks)"""
    blocks, cur, depth = {}, None, 0
    if not os.path.isfile(path):
        return blocks
    for raw in read_text(path).splitlines():
        line = raw.split('--')[0].strip()
        if not line:
            continue
        if line.startswith('{'):
            depth += 1
            cur = {'vnum': None, 'rows': []}
            continue
        if line.startswith('}'):
            depth -= 1
            if cur and cur['vnum'] is not None:
                blocks[cur['vnum']] = cur['rows']
            cur = None
            continue
        if cur is None:
            continue
        tok = re.split(r'[\t ]+', line)
        key = tok[0].lower()
        if key == 'vnum' and len(tok) > 1 and tok[1].isdigit():
            cur['vnum'] = int(tok[1])
        elif key == 'leader' or key.isdigit():
            cur['rows'].append((key, [t for t in line.split('\t')[1:] if t.strip()] or tok[1:]))
    return blocks


class Share(object):
    def __init__(self, root):
        self.root = root
        loc = os.path.join(root, 'locale', 'poland')
        self.groups = {}
        for v, rows in load_blocks(os.path.join(loc, 'group.txt')).items():
            mem = []
            for key, toks in rows:
                # Leader <name> <vnum> / <n> <name> <vnum>: LoadGroup reads the second token
                nums = [t.strip() for t in toks if t.strip().isdigit()]
                if nums:
                    mem.append(int(nums[-1]))
            self.groups[v] = mem
        self.group_groups = {}
        for v, rows in load_blocks(os.path.join(loc, 'group_group.txt')).items():
            self.group_groups[v] = [int(toks[0].strip()) for key, toks in rows
                                    if key != 'leader' and toks and toks[0].strip().isdigit()]
        self.maps = {}
        for line in read_text(os.path.join(loc, 'map', 'index')).splitlines():
            p = line.split()
            if len(p) >= 2 and p[0].isdigit():
                self.maps[int(p[0])] = p[1]
        self.loc = loc

    def unfold(self, kind, vnum):
        if kind in ('m', 's'):
            return [vnum]
        if kind == 'g':
            return list(self.groups.get(vnum, []))
        if kind == 'r':
            out = []
            for g in self.group_groups.get(vnum, []):
                out += self.groups.get(g, [])
            return out
        return []

    def regen_file(self, path):
        out = set()
        if not os.path.isfile(path):
            return out
        for line in read_text(path).splitlines():
            line = line.strip()
            if not line or line.startswith('/') or line.startswith('#'):
                continue
            p = line.split()
            if len(p) < 11 or p[0][0] not in 'mgrs' or not p[10].isdigit():
                continue
            out.update(self.unfold(p[0][0], int(p[10])))
        return out

    def map_vnums(self, index):
        d = os.path.join(self.loc, 'map', self.maps.get(index, ''))
        out = set()
        if index not in self.maps or not os.path.isdir(d):
            return out
        for f in sorted(os.listdir(d)):
            fl = f.lower()
            if not fl.endswith('.txt') or '.image.' in fl or fl in SKIP_MAP_FILES:
                continue
            out |= self.regen_file(os.path.join(d, f))
        return out

    def dungeon_dir_vnums(self, name):
        d = os.path.join(self.root, 'data', 'dungeon', name)
        out = set()
        if os.path.isdir(d):
            for f in sorted(os.listdir(d)):
                if f.lower().endswith('.txt'):
                    out |= self.regen_file(os.path.join(d, f))
        return out

    def special_spawns(self):
        """{map index: set(vnums)} of special_spawns.txt"""
        out = {}
        path = os.path.join(self.loc, 'special_spawns.txt')
        if not os.path.isfile(path):
            return out
        cur = None
        for raw in read_text(path).splitlines():
            line = raw.split('#')[0].strip()
            if line.startswith('{'):
                cur = {}
            elif line.startswith('}'):
                if cur and 'map_index' in cur:
                    v = cur.get('spawn_vnum') or cur.get('vnum')
                    kind = {'mob': 'm', 'group': 'g', 'group_group': 'r'}.get(cur.get('spawn_type', 'mob'), 'm')
                    if v:
                        out.setdefault(cur['map_index'], set()).update(self.unfold(kind, v))
                cur = None
            elif cur is not None:
                p = line.split()
                if len(p) >= 2 and p[0].lower() in ('vnum', 'spawn_vnum', 'map_index') and p[1].isdigit():
                    cur[p[0].lower()] = int(p[1])
                elif len(p) >= 2 and p[0].lower() == 'spawn_type':
                    cur['spawn_type'] = p[1].lower()
        return out


def quest_vnums(path, mobs, share):
    """monster vnums >= 1000 written in a dungeon quest (comments out) and the groups of its
    'groups = {...}' tables / d.spawn_group(<literal>) - coordinates are under 1000"""
    if not os.path.isfile(path):
        return set()
    t = re.sub(r'--[^\n]*', '', read_text(path))
    out = set()
    for x in re.findall(r'(?<![\w.])(\d{4,5})(?![\w.])', t):
        v = int(x)
        if v in mobs and mobs[v]['type'] == MOB_MONSTER:
            out.add(v)
    for body in re.findall(r'groups\s*=\s*\{([^}]*)\}', t):
        for x in re.findall(r'\d+', body):
            out.update(share.unfold('g', int(x)))
    for x in re.findall(r'spawn_group\(\s*(\d+)', t):
        out.update(share.unfold('g', int(x)))
    return out


def lua_enemies(path):
    out = set()
    if path and os.path.isfile(path):
        t = re.sub(r'--[^\n]*', '', read_text(path))
        out.update(int(x) for x in re.findall(r'\.enemy\s*=\s*(\d+)', t))
    return out


def monsters(vnums, mobs):
    return set(v for v in vnums if v in mobs and mobs[v]['type'] == MOB_MONSTER)


def with_summons(vnums, mobs):
    out, todo = set(vnums), list(vnums)
    while todo:
        s = mobs.get(todo.pop(), {}).get('summon', 0)
        if s and s in mobs and mobs[s]['type'] == MOB_MONSTER and s not in out:
            out.add(s)
            todo.append(s)
    return out


def copy_from_container(name, dest):
    for part in SHARE_PARTS:
        target = os.path.join(dest, part)
        os.makedirs(os.path.dirname(target), exist_ok=True)
        r = subprocess.run(['docker', 'cp', '%s:/opt/metin2/share/%s' % (name, part), target],
                           stdout=subprocess.DEVNULL, stderr=subprocess.PIPE)
        if r.returncode != 0 and not part.endswith(('special_spawns.txt', 'BlueDragon.lua')):
            sys.exit('docker cp %s: %s' % (part, r.stderr.decode('utf-8', 'replace').strip()))


def ids(vs):
    return ','.join(str(v) for v in sorted(vs))


def main():
    ap = argparse.ArgumentParser()
    src = ap.add_mutually_exclusive_group(required=True)
    src.add_argument('--share', help='a copy of the game image\'s /opt/metin2/share')
    src.add_argument('--container', help='a game container (running or stopped) to copy the share from')
    ap.add_argument('--mobs', required=True, help='world.mob_proto TSV (see the header)')
    ap.add_argument('--report', help='also write the report here')
    a = ap.parse_args()

    tmp = None
    root = a.share
    if a.container:
        tmp = tempfile.mkdtemp(prefix='zywioly-share-')
        copy_from_container(a.container, tmp)
        root = tmp
    try:
        share = Share(root)
        mobs = load_mobs(a.mobs)
        wiki = dict((int(k), v) for k, v in json.load(open(WIKI)).items())
        rep = []
        result, why = {}, {}

        # a. the wiki's bosses
        for v, bits in sorted(wiki.items()):
            m = mobs.get(v)
            if m and m['type'] == MOB_MONSTER and m['rank'] >= RANK_BOSS:
                result[v], why[v] = bits, 'wiki boss'

        # b. the maps
        map_sets = {}
        for label, idxs, elem in MAP_RULES:
            vs = set()
            for i in idxs:
                vs |= share.map_vnums(i)
                vs |= share.special_spawns().get(i, set())
            vs = with_summons(monsters(vs, mobs), mobs)
            map_sets[label] = vs
            for v in sorted(vs):
                if mobs[v]['rank'] >= RANK_BOSS and v in wiki:
                    continue  # a boss keeps its wiki element
                if v in result and result[v] != elem and why[v].startswith('map'):
                    rep.append('CONFLICT %d %s: %s (%s) vs %s (%s)' % (v, mobs[v]['name'], NAMES[result[v]], why[v],
                                                                       NAMES[elem], label))
                result[v], why[v] = elem, 'map ' + label

        # c. the dungeons (win over everything above)
        dun_sets = {}
        for label, idx, dirs, quest, lua, elem in DUNGEON_RULES:
            vs = share.map_vnums(idx) | share.special_spawns().get(idx, set())
            for d in dirs:
                vs |= share.dungeon_dir_vnums(d)
            vs |= quest_vnums(os.path.join(QUESTS, quest), mobs, share)
            vs |= lua_enemies(os.path.join(share.loc, lua) if lua else None)
            vs = with_summons(monsters(vs, mobs), mobs)
            dun_sets[label] = vs
            for v in sorted(vs):
                if v in result and result[v] != elem:
                    rep.append('override %d %s: %s (%s) -> %s (%s)' % (v, mobs[v]['name'], NAMES[result[v]], why[v],
                                                                      NAMES[elem], label))
                result[v], why[v] = elem, 'dungeon ' + label

        # where else every vnum spawns (maps of the index, dungeon dirs, special spawns)
        elsewhere = {}
        rule_maps = set(i for _, idxs, _ in MAP_RULES for i in idxs) | set(r[1] for r in DUNGEON_RULES)
        rule_dirs = set(d for r in DUNGEON_RULES for d in r[2])
        for i, name in sorted(share.maps.items()):
            if i in rule_maps:
                continue
            for v in share.map_vnums(i) | share.special_spawns().get(i, set()):
                elsewhere.setdefault(v, set()).add('%d %s' % (i, name))
        ddir = os.path.join(root, 'data', 'dungeon')
        if os.path.isdir(ddir):
            for d in sorted(os.listdir(ddir)):
                if d in rule_dirs:
                    continue
                vs = share.dungeon_dir_vnums(d) if os.path.isdir(os.path.join(ddir, d)) else \
                    share.regen_file(os.path.join(ddir, d))
                for v in vs:
                    elsewhere.setdefault(v, set()).add('data/dungeon/' + d)

        # the report
        out = ['Monster elements (MT2009_PLUS_ELEMENTS_V1): %d vnums' % len(result)]
        for bit in (ELEC, FIRE, ICE, WIND, EARTH, DARK):
            vs = [v for v, b in result.items() if b == bit]
            out.append('  %-10s %4d  (wiki bosses %d)' % (NAMES[bit], len(vs),
                                                        sum(1 for v in vs if why[v] == 'wiki boss')))
        for label, vs in list(map_sets.items()) + list(dun_sets.items()):
            out.append('  %s: %d monsters' % (label, len(vs)))
        cleared = sorted(v for v, m in mobs.items() if m['flag'] & MASK and v not in result)
        out.append('  bits cleared on %d other mobs (they had an element bit in the DB now)' % len(cleared))
        out += rep
        out.append('Overlaps (a rule vnum that spawns elsewhere too - it carries the element there):')
        for v in sorted(result):
            if why[v] == 'wiki boss' or v not in elsewhere:
                continue
            out.append('  %d %s [%s, %s]: %s' % (v, mobs[v]['name'], NAMES[result[v]], why[v],
                                                ', '.join(sorted(elsewhere[v]))))
        out.append('Mapping:')
        for v in sorted(result):
            out.append('  %d\t%s\t%s\t%s' % (v, NAMES[result[v]], why[v], mobs[v]['name']))
        report = '\n'.join(out) + '\n'
        sys.stdout.write(report)
        if a.report:
            open(a.report, 'w', encoding='utf-8').write(report)

        # the SQL
        sql = ['-- MT2009_PLUS_ELEMENTS_V1: the monsters\' elements (setRaceFlag bits 11-16 = lightning, fire,',
               '-- ice, wind, earth, dark; in the column\'s SET: SAVAGE, ATT_FIRE, ATT_ICE, ATT_TEMPLE, ATT_EARTH,',
               '-- ATT_DARK). Autor: Digi Rasta (Zywioly i talizmany, nowy-system 0.28.0) - by the owner\'s rules of',
               '-- 7 October 2026 (tools/zywioly/gen_zywioly_moby.py: wiki bosses, Grota Wygnancow 1/2, Swiatynia',
               '-- Ochao, Zaczarowany Las, the dungeons Nemere, Leze Smoka, Starozytna Dzungla). GENERATED - do not',
               '-- edit; rerun the generator. Every start (apply.sh), idempotent: bits 11-16 cleared on every other',
               '-- mob, set on these.']
        for line in out[1:7]:
            sql.append('-- ' + line.strip())
        sql.append('UPDATE world.mob_proto SET setRaceFlag = (setRaceFlag + 0) & ~%d WHERE (setRaceFlag + 0) & %d <> 0'
                   ' AND vnum NOT IN (%s);' % (MASK, MASK, ids(result)))
        for bit in (ELEC, FIRE, ICE, WIND, EARTH, DARK):
            vs = [v for v, b in result.items() if b == bit]
            if vs:
                sql.append('UPDATE world.mob_proto SET setRaceFlag = ((setRaceFlag + 0) & ~%d) | %d WHERE vnum IN (%s);'
                           % (MASK, bit, ids(vs)))
        with open(SQL_OUT, 'w', encoding='utf-8', newline='\n') as f:
            f.write('\n'.join(sql) + '\n')
        with open(JSON_OUT, 'w', encoding='utf-8', newline='\n') as f:
            json.dump(dict((str(v), result[v]) for v in sorted(result)), f, indent=0, sort_keys=False)
            f.write('\n')
        sys.stderr.write('written %s, %s\n' % (os.path.relpath(SQL_OUT, REPO), os.path.relpath(JSON_OUT, REPO)))
    finally:
        if tmp:
            shutil.rmtree(tmp, ignore_errors=True)


if __name__ == '__main__':
    main()
