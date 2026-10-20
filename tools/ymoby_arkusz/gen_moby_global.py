#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""gen_moby_global.py                      render the server and client files from moby_global.json
gen_moby_global.py extract --xlsx FILE [--db C] [--game C] [--package DIR]
                                           (re)read the sheet and our world, write moby_global.json

MT2009_PLUS_MOBY_GLOBAL_V1: the monsters before Yohara "as on the global server" - the owner's decision of 20 October
2026 on his sheet Metin2_Moby_statystyki_EXP_i_drop.xlsx (metin2alerts' mob pages, read 16 October 2026). Decisions:
moby_global_data.py; report: /opt/metin2/cache/yohara/porownanie-moby.md. Writes

  linux-port/docker/mariadb/playerbot/moby_global.sql     guarded UPDATEs of world.mob_proto (apply.sh): a column
                                                          changes only while it holds the value our world was made
                                                          with (world.sql = mob_proto.mt2009plus.sql); a value the
                                                          operator set (the panel's database editor) is kept
  linux-port/docker/game/moby_global/mob_drop_item.moby_global.txt
                                                          the sheet's drops our monsters lack (groups
                                                          MT2009_mglobal_<mob>, Type drop - merged with the mob's own)
  linux-port/docker/game/moby_global/mob_drop_item.moby_global.remove.txt
                                                          "<mob> <item> <count> <value>": the package's rows the sheet
                                                          does not list (the Dockerfile step cuts them and numbers
                                                          the group again); our own rows (MT2009_* / playerbot_*
                                                          groups, rows the Dockerfile added or changed), the special
                                                          groups (s<vnum>) and a quest's items stay
  tools/ymoby_arkusz/moby_global_client.json             the client's mob_proto records to change
                                                          (client-2.0.30/tools/mobyglobal)

What counts as ours: monsters of the sheet in world.mob_proto, not a Yohara row (mariadb/playerbot/yohara_*.sql,
shipdefense.sql - tools/ymoby_arkusz/gen_ymoby_arkusz.py), a monster or a Metin (type 0 / 2), the same monster by name
(a placeholder name - "NoNAme", "????" - counts as the same). A column a script of ours writes (an UPDATE of
world.mob_proto in mariadb/playerbot/*.sql or apply.sh) stays ours: the report lists where the sheet differs.

extract reads: the sheet (openpyxl - /opt/metin2/cache/xlsxenv/bin/python); world.mob_proto / item_proto /
refine_proto / shop_item of the running test world; the game image's mob_drop_item.image.txt (as built - the live
file may hold the operator's edits), special_item_group.image.txt, cube.txt, common_drop_item.txt, drop_wiki.txt; the
package's own mob_drop_item.txt and quests (--package: <server>/share/locale/poland); our quests (game/**.quest|lua).

Example: /opt/metin2/cache/xlsxenv/bin/python tools/ymoby_arkusz/gen_moby_global.py extract --xlsx Moby.xlsx
         python3 tools/ymoby_arkusz/gen_moby_global.py
"""
import argparse
import collections
import difflib
import json
import os
import re
import statistics
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import gen_ymoby_arkusz as Y  # noqa: E402
import moby_global_data as G  # noqa: E402
import ymoby_data as D  # noqa: E402

REPO = Y.REPO
DATA = os.path.join(HERE, 'moby_global.json')
CLIENT_OUT = os.path.join(HERE, 'moby_global_client.json')
SQL_OUT = os.path.join(Y.PB, 'moby_global.sql')
GAME = os.path.join(REPO, 'linux-port', 'docker', 'game', 'moby_global')
DROP_OUT = os.path.join(GAME, 'mob_drop_item.moby_global.txt')
REMOVE_OUT = os.path.join(GAME, 'mob_drop_item.moby_global.remove.txt')
GROUP = 'MT2009_mglobal_'
PACKAGE = '/opt/metin2/mt2009plustest/linux-port/docker/game/src/serverfiles/share/locale/poland'
OURS_GROUP = ('MT2009_', 'playerbot_')
SET_COLS = (('ai_flag', G.AI), ('setImmuneFlag', G.IMMUNE))
ALL_AI = ['AGGR', 'NOMOVE', 'COWARD', 'NOATTSHINSU', 'NOATTCHUNJO', 'NOATTJINNO', 'ATTMOB', 'BERSERK', 'STONESKIN',
          'GODSPEED', 'DEATHBLOW', 'REVIVE', 'IGNORE_LAST_ATTACK', 'NO_WANDER', 'SEE_OTHER_NPC', 'RETURN_LASTATTACK_POS',
          'LOOSE_AGGRO_ON_DISTANCE']
ALL_RACE = ['ANIMAL', 'UNDEAD', 'DEVIL', 'HUMAN', 'ORC', 'MILGYO', 'INSECT', 'FIRE', 'ICE', 'DESERT', 'TREE', 'SAVAGE',
            'ATT_FIRE', 'ATT_ICE', 'ATT_TEMPLE', 'ATT_EARTH', 'ATT_DARK']
ALL_IMMUNE = ['STUN', 'SLOW', 'FALL', 'CURSE', 'POISON', 'TERROR', 'REFLECT']
BITS = {'ai_flag': ALL_AI, 'setImmuneFlag': ALL_IMMUNE, 'setRaceFlag': ALL_RACE}


# -- extract --------------------------------------------------------------------------------------------------------
def sql_rows(path):
    """{vnum: {column: value}} of the INSERT rows of world.mob_proto in one of our SQL files"""
    t = open(path, encoding='utf-8').read()
    m = re.search(r'INSERT IGNORE INTO world\.mob_proto \(([^)]*)\) VALUES', t)
    cols = m.group(1).replace('`', '').split(',')
    out, s, i = {}, t, m.end()
    while True:
        j = s.find('\n(', i)
        if j < 0:
            break
        i, vals, cur, inq = j + 2, [], '', False
        while True:
            c = s[i]
            if inq:
                if c == '\\':
                    cur += s[i + 1]
                    i += 2
                    continue
                if c == "'":
                    inq = False
                else:
                    cur += c
                i += 1
                continue
            if c == "'":
                inq = True
            elif c == ',':
                vals.append(cur)
                cur = ''
            elif c == ')':
                vals.append(cur)
                i += 1
                break
            else:
                cur += c
            i += 1
        r = dict(zip(cols, [x.strip() for x in vals]))
        out[int(r['vnum'])] = r
    return out


def scripted_columns():
    """{vnum: {column: file}} - the columns of world.mob_proto our scripts write (not the elements' bits)"""
    import glob
    out = {}
    files = glob.glob(os.path.join(Y.PB, '*.sql')) + glob.glob(os.path.join(Y.PB, 'mod', '*.sql')) + \
        [os.path.join(Y.PB, 'apply.sh')]
    for f in files:
        if os.path.basename(f) in ('moby_global.sql', 'yohara_moby_arkusz.sql'):
            continue
        t = open(f, encoding='utf-8', errors='replace').read()
        for m in re.finditer(r'UPDATE\s+world\.mob_proto\s+SET\s+(.*?)\s+WHERE\s+(.*?)(;|"|$)', t, re.S | re.M):
            cols = set(c.strip('`') for c in re.findall(r'`?(\w+)`?\s*=', m.group(1))) - {'name', 'locale_name'}
            if cols <= {'setRaceFlag'}:
                continue
            where = re.sub(r"'[^']*'", '', m.group(2).split('AND')[0])
            for v in re.findall(r'\b(\d{3,5})\b', where):
                for c in cols:
                    out.setdefault(int(v), {}).setdefault(c, os.path.basename(f))
    return out


def groups(text):
    out, cur = [], None
    for line in text.split('\n'):
        p = line.split('--')[0].split()
        if not p or p[0].startswith('//'):
            continue
        if p[0] == 'Group':
            cur = dict(name=p[1] if len(p) > 1 else '', mob=None, type=None, rows=[])
        elif cur is None or p[0] == '{':
            continue
        elif p[0] == '}':
            out.append(cur)
            cur = None
        elif p[0] in ('Mob', 'Vnum'):
            cur['mob'] = int(p[1])
        elif p[0] == 'Type':
            cur['type'] = p[1].lower()
        elif p[0].isdigit() and len(p) >= 4:
            cur['rows'].append((p[1], int(p[2]), p[3]))
    return out


def extract(a):
    import openpyxl  # noqa: F401  (Y.read_sheet)
    import chestdrops as C
    wb_mobs, wb_drops = Y.read_sheet(a.xlsx)
    sheet = parse_sheet(a.xlsx)
    yohara = set()
    import glob
    for f in sorted(glob.glob(os.path.join(Y.PB, 'yohara_*.sql'))) + [os.path.join(Y.PB, 'shipdefense.sql')]:
        yohara.update(Y.sql_vnums(f))
    base = sql_rows(os.path.join(Y.PB, 'mob_proto.mt2009plus.sql'))
    scripted = scripted_columns()
    db = {}
    cols = [r[0] for r in Y.db_rows(a.db, 'SHOW COLUMNS FROM world.mob_proto')]
    for p in Y.db_rows(a.db, 'SELECT * FROM world.mob_proto'):
        r = dict(zip(cols, p))
        db[int(r['vnum'])] = r
    item = {}
    for p in Y.db_rows(a.db, 'SELECT vnum, locale_name, type FROM world.item_proto'):
        item[int(p[0])] = dict(name=p[1], type=int(p[2]))
    by_name = collections.defaultdict(list)
    for v, it in item.items():
        by_name[Y.norm(it['name'])].append(v)
    used = set()
    for p in Y.db_rows(a.db, 'SELECT vnum0, vnum1, vnum2, vnum3, vnum4 FROM world.refine_proto'):
        used.update(int(x) for x in p if x.isdigit())
    for q in ('SELECT item_vnum FROM player.shop_item', 'SELECT item_vnum FROM world.shop_item'):
        try:
            used.update(int(p[0]) for p in Y.db_rows(a.db, q + ' -- may be missing'))
        except Exception:
            pass
    loc = lambda n: Y.game_file(a.game, n).decode('utf-8', 'replace')  # noqa: E731
    img = groups(loc('mob_drop_item.image.txt'))
    sig = dict((g['mob'], [r[0] for r in g['rows']]) for g in groups(loc('special_item_group.image.txt')))
    for nums in re.findall(r'\b(\d{4,6})\b', loc('cube.txt')):
        used.add(int(nums))
    for g in img:
        used.update(int(r[0]) for r in g['rows'] if r[0].isdigit())
    for rows in sig.values():
        used.update(int(x) for x in rows if x.isdigit())
    common = Y.common_items(Y.game_file(a.game, 'common_drop_item.txt').decode('latin-1'))
    wiki = collections.defaultdict(set)
    for line in Y.game_file(a.game, 'drop_wiki.txt').decode('cp1250', 'replace').split('\n'):
        p = line.split()
        if len(p) >= 3 and p[0] == 'drop' and p[1].isdigit() and p[2].isdigit():
            wiki[int(p[1])].add(int(p[2]))
    pkg = collections.defaultdict(set)
    for g in groups(open(os.path.join(a.package, 'mob_drop_item.txt'), encoding='utf-8', errors='replace').read()):
        for r in g['rows']:
            pkg[(g['name'], g['mob'])].add(r)
    quest = set()
    for root in (os.path.join(a.package, 'quest'), os.path.join(REPO, 'linux-port', 'docker', 'game')):
        for d, _ds, fs in os.walk(root):
            if os.sep + 'object' in d:
                continue
            for f in fs:
                if f.endswith(('.quest', '.lua')):
                    t = open(os.path.join(d, f), encoding='latin-1').read()
                    quest.update(int(x) for x in re.findall(
                        r'(?:drop_item|give_item2?|count_item|remove_item|drop_item_with_ownership)\s*\(\s*(\d{4,6})', t))

    # -- the statistics
    fixes, conflicts, outside, ranks = [], [], [], []
    for v in sorted(sheet):
        e = sheet[v]
        if v not in db or v in yohara:
            continue
        o = db[v]
        if o['type'] not in ('0', '2'):
            outside.append([v, e['name'], 'NPC / obiekt'])
            continue
        ours = Y.norm(o['locale_name'])
        placeholder = not ours or ours == 'noname' or set(o['locale_name']) <= set('?')
        if not placeholder and v not in G.SAME_NAME and \
                difflib.SequenceMatcher(None, Y.norm(e['name']), ours).ratio() < 0.6:
            outside.append([v, e['name'], 'u nas inny potwor: ' + o['locale_name']])
            continue
        made = base.get(v, o)          # the value our world was made with
        for c in G.NUM:
            if e.get(c) is None:
                continue
            if c in scripted.get(v, {}):
                if float(o[c]) != float(e[c]):
                    conflicts.append([v, e['name'], c, o[c], e[c], scripted[v][c]])
                continue
            if float(made[c]) != float(e[c]):
                fixes.append([v, c, int(float(made[c])), int(e[c])])
        for c, keys in SET_COLS:
            have = [x for x in made[c].split(',') if x]
            want = [x for x in BITS[c] if (x in have and x not in keys) or (x in keys and x in e[c])]
            if set(want) != set(have):
                if c in scripted.get(v, {}):
                    conflicts.append([v, e['name'], c, made[c], ','.join(want), scripted[v][c]])
                else:
                    fixes.append([v, c, ','.join(x for x in BITS[c] if x in have), ','.join(want)])
        if e['race']:
            have = set(x for x in made['setRaceFlag'].split(',') if x) & set(G.RACE)
            if not have:
                fixes.append([v, 'setRaceFlag:' + e['race'], 0, 1])
            elif e['race'] not in have:
                conflicts.append([v, e['name'], 'race', ','.join(sorted(have)), e['race'], 'nasza rasa'])
        if e['rank'] is not None and int(o['rank']) != e['rank']:
            ranks.append([v, e['name'], int(o['rank']), e['rank']])
    # -- the drops
    pre = set(v for v in wb_drops if v in db and v not in yohara and db[v]['type'] in ('0', '2')
              and v not in set(x[0] for x in outside))

    def ours_of(off, name):
        for ex in (D.EXCLUDE, G.EXCLUDE):
            if off in ex:
                return None, ex[off]
        if off in C.SUBST and isinstance(C.SUBST[off][0], int):
            return C.SUBST[off][0], None
        if off in C.SKIP:
            return None, C.SKIP[off]
        if off in item and (off in D.SAME or Y.norm(item[off]['name']) == Y.norm(name)):
            return off, None
        same = by_name.get(Y.norm(name), [])
        if len(same) == 1:
            return same[0], None
        return None, ('our %d is another item (%s)' % (off, item[off]['name'])) if off in item else 'not in our world'

    def expand(tok, seen):
        if tok.isdigit():
            return {int(tok)}
        v = int(tok[1:]) if tok[1:].isdigit() else None
        if v is None or v in seen:
            return set()
        seen.add(v)
        out = set()
        for t in sig.get(v, []):
            out |= expand(t, seen)
        return out

    def kind(v):
        return 'stone' if db[v]['type'] == '2' else ('boss' if int(db[v]['rank']) >= 4 else 'normal')

    rows_of = collections.defaultdict(list)
    for g in img:
        if g['mob'] is None:
            continue
        for it, cnt, pct in g['rows']:
            mine = g['name'].startswith(OURS_GROUP) or (it, cnt, pct) not in pkg.get((g['name'], g['mob']), set())
            rows_of[g['mob']].append(dict(group=g['name'], item=it, count=cnt, pct=pct, type=g['type'], ours=mine))
    ref = collections.defaultdict(list)
    for v, rows in rows_of.items():
        if v in yohara or v not in db:
            continue
        for r in rows:
            if r['type'] == 'drop' and r['item'].isdigit():
                ref[(kind(v), int(r['item']))].append((r['count'], float(r['pct'])))
                ref[('any', int(r['item']))].append((r['count'], float(r['pct'])))
    adds, removes, kept, skipped = {}, [], [], collections.Counter()
    for v in sorted(pre):
        want = set()
        for off, name in wb_drops[v]:
            o, why = ours_of(off, name)
            if o is None:
                skipped[(off, name, why)] += 1
                continue
            if o in quest:
                skipped[(off, name, 'a quest gives / takes it')] += 1
                continue
            if item[o]['type'] == 5 and o not in used:
                skipped[(off, name, 'a material nothing of ours uses')] += 1
                continue
            want.add(o)
        have = set()
        for r in rows_of.get(v, []):
            have |= expand(r['item'], set())
        k = kind(v)
        rows = []
        for o in sorted(want - have - common - wiki[v]):
            same = ref.get((k, o))
            if same:
                cnt, val, how = int(statistics.median_low([c for c, _ in same])), statistics.median([p for _, p in same]), 'ours'
            elif ref.get(('any', o)):
                r_ = ref[('any', o)]
                cnt, val, how = int(statistics.median_low([c for c, _ in r_])), \
                    min(statistics.median([p for _, p in r_]), D.CAP[k]), 'ours-other-kind'
            else:
                cat = Y.category(o, item[o])
                cnt, val, how = 1, D.DEFAULT[cat][('normal', 'boss', 'stone').index(k)], 'default:' + cat
            if k == 'normal':          # an ordinary monster: at most CAP (0.5 %) for an added row
                val = min(val, D.CAP['normal'])
            rows.append([o, cnt, round(val, 4), item[o]['name'], how])
        if rows:
            adds[str(v)] = dict(name=db[v]['locale_name'], kind=k, rows=rows)
        for r in rows_of.get(v, []):
            if not r['item'].isdigit() or int(r['item']) in want:
                continue
            it = int(r['item'])
            if r['ours'] or it in quest:
                kept.append([v, it, item.get(it, {}).get('name', '?'), r['group'],
                             'quest' if it in quest and not r['ours'] else 'ours'])
            else:
                removes.append([v, it, r['count'], r['pct'], item.get(it, {}).get('name', '?'), r['group']])
    client = {}
    for v, c, old, new in fixes:
        client.setdefault(str(v), {})[c] = new
    json.dump(dict(source=re.sub(r'^[0-9a-f]{8}-', '', os.path.basename(a.xlsx)), fixes=fixes, conflicts=conflicts,
                   outside=outside, ranks=ranks, adds=adds, removes=removes, kept=kept,
                   skipped=sorted([list(k) + [n] for k, n in skipped.items()], key=lambda x: -x[3]),
                   test_world_differs=[[v, c, db[v][c]] for v, c, old, new in fixes
                                       if c in G.NUM and float(db[v][c]) != float(old)]),
              open(DATA, 'w', encoding='utf-8'), ensure_ascii=False, indent=0, sort_keys=True)
    print('extract: %d stat changes on %d monsters, %d conflicts kept, %d outside; drops: +%d rows on %d monsters, '
          '-%d rows on %d monsters, %d of ours kept' % (
              len(fixes), len(set(f[0] for f in fixes)), len(conflicts), len(outside),
              sum(len(x['rows']) for x in adds.values()), len(adds), len(removes), len(set(r[0] for r in removes)),
              len(kept)))


def parse_sheet(path):
    """{vnum: the sheet's stats in our columns}"""
    import openpyxl
    wb = openpyxl.load_workbook(path, read_only=False, data_only=True)
    rank = {'Poziom 1': 0, 'Poziom 2': 1, 'Poziom 3': 2, 'Poziom 4': 3, 'Boss': 4, 'Poziom 5': 5}
    ench = {'Omdlenie': 'enchant_stun', 'Otrucie': 'enchant_poison', 'Spowolnienie': 'enchant_slow',
            'Klątwę': 'enchant_curse', 'cios krytyczny': 'enchant_critical',
            'przeszywające Uderzenie': 'enchant_penetrate'}
    imm = {'Odporność na Omdlenia': 'STUN', 'Odporność na Spowolnienia': 'SLOW', 'Odporność na klątwę': 'CURSE',
           'Odporność na truciznę': 'POISON', 'Odporność na strach': 'TERROR'}
    ai = {'Agresywny': 'AGGR', 'Berserk — większe obrażenia przy niskim HP': 'BERSERK',
          'Kamienna skóra — redukcja obrażeń przy niskim HP': 'STONESKIN', 'Wskrzesza sojuszników': 'REVIVE',
          'Śmiertelny cios': 'DEATHBLOW', 'Wzrost szybkości ataku przy niskim HP': 'GODSPEED',
          'Ucieka przy niskim HP': 'COWARD'}
    race = {'devil': 'DEVIL', 'animal': 'ANIMAL', 'human': 'HUMAN', 'undead': 'UNDEAD', 'orc': 'ORC',
            'desert': 'DESERT', 'insect': 'INSECT', 'milgyo': 'MILGYO'}
    res = ['fist', 'resist_sword', 'resist_twohand', 'resist_dagger', 'resist_bell', 'resist_fan', 'resist_bow',
           'claw', 'resist_fire', 'resist_elect', 'resist_magic', 'resist_wind', 'resist_poison']
    code = {}
    for r in list(wb['Pełne statystyki'].iter_rows(values_only=True))[6:]:
        if isinstance(r[1], int) and r[2] == 'Kod rasy':
            code[r[1]] = r[3]
    resi = dict((r[1], r) for r in list(wb['Odporności'].iter_rows(values_only=True))[6:] if isinstance(r[1], int))
    out = {}
    for r in list(wb['Moby'].iter_rows(values_only=True))[6:]:
        if not isinstance(r[1], int):
            continue
        e = dict(name=r[0], level=r[2], rank=rank.get(r[3]), max_hp=r[4], exp=r[5], damage_min=r[7],
                 damage_max=r[8], ht=r[10], iq=r[11], st=r[12], dx=r[13], attack_speed=r[14], move_speed=r[15])
        e['def'] = r[9]
        m = re.match(r'%(\d+) / (\d+) s', str(r[16] or ''))
        if m:
            e['regen_percent'], e['regen_cycle'] = int(m.group(1)), int(m.group(2))
        for c in ench.values():
            e[c] = 0
        for x in str(r[21]).split(';'):
            for k, c in ench.items():
                if x.strip().startswith('Szansa na %s:' % k):
                    e[c] = int(x.split(':')[1].strip().rstrip('%'))
        e['setImmuneFlag'] = [imm[x.strip()] for x in str(r[20]).split(';') if x.strip() in imm]
        e['ai_flag'] = [ai[x.strip()] for x in str(r[22]).split(';') if x.strip() in ai]
        e['race'] = race.get(code.get(r[1]))
        rr = resi.get(r[1])
        for i, c in enumerate(res):
            if c.startswith('resist_'):
                e[c] = (rr[2 + i] or 0) if rr else 0
        out[r[1]] = e
    return out


# -- render ---------------------------------------------------------------------------------------------------------
def render():
    data = json.load(open(DATA, encoding='utf-8'))
    sql = [SQL_HEAD]
    for v, c, old, new in data['fixes']:
        if c.startswith('setRaceFlag:'):        # only onto a monster with no race of its own (bits 0-10)
            bit = 1 << BITS['setRaceFlag'].index(c.split(':')[1])
            sql.append('UPDATE world.mob_proto SET `setRaceFlag` = (`setRaceFlag` + 0) | %d WHERE vnum = %d AND '
                       '(`setRaceFlag` + 0) & 2047 = 0;' % (bit, v))
        elif c in BITS:                         # the whole flag set, while it is still the one the world was made with
            sql.append("UPDATE world.mob_proto SET `%s` = '%s' WHERE vnum = %d AND `%s` = '%s';" % (c, new, v, c, old))
        else:
            sql.append('UPDATE world.mob_proto SET `%s` = %d WHERE vnum = %d AND `%s` = %d;' % (c, new, v, c, old))
    with open(SQL_OUT, 'w', encoding='utf-8', newline='\n') as f:
        f.write('\n'.join(sql) + '\n')
    os.makedirs(GAME, exist_ok=True)
    out = [DROP_HEAD % dict(src=data['source'])]
    n = 0
    for v in sorted(data['adds'], key=int):
        a = data['adds'][v]
        out += ['Group\t%s%s' % (GROUP, v), '{', '\tMob\t%s\t-- %s' % (v, Y.ascii_pl(a['name'])), '\tType\tdrop']
        for i, (o, cnt, val, name, how) in enumerate(a['rows'], 1):
            out.append('\t%d\t%d\t%d\t%s\t-- %s' % (i, o, cnt, ('%.4f' % val).rstrip('0').rstrip('.'), Y.ascii_pl(name)))
            n += 1
        out.append('}')
    with open(DROP_OUT, 'w', encoding='utf-8', newline='\r\n') as f:
        f.write('\n'.join(out) + '\n')
    with open(REMOVE_OUT, 'w', encoding='utf-8', newline='\n') as f:
        f.write(REMOVE_HEAD)
        for v, it, cnt, pct, name, group in data['removes']:
            f.write('%d\t%d\t%d\t%s\t# %s (%s)\n' % (v, it, cnt, pct, Y.ascii_pl(name), group))
    client = {}
    for v, c, old, new in data['fixes']:
        client.setdefault(str(v), {})[c] = new
    with open(CLIENT_OUT, 'w', encoding='utf-8', newline='\n') as f:
        json.dump(client, f, indent=0, sort_keys=True)
        f.write('\n')
    print('render: %d UPDATEs; +%d drop rows in %d groups; -%d rows; client: %d monsters' % (
        len(data['fixes']), n, len(data['adds']), len(data['removes']), len(client)))


SQL_HEAD = """-- MT2009_PLUS_MOBY_GLOBAL_V1: the monsters before Yohara as on the global server (the owner, 20 October 2026; his
-- sheet Metin2_Moby_statystyki_EXP_i_drop.xlsx). GENERATED by tools/ymoby_arkusz/gen_moby_global.py - do not edit,
-- rerun it. HP, damage, EXP, level, defence, STR/DEX/VIT/INT, speeds, regeneration, the effects' chances, the eleven
-- resistances; the AI flags AGGR/BERSERK/STONESKIN/GODSPEED/DEATHBLOW/REVIVE/COWARD and the immunities
-- STUN/SLOW/CURSE/POISON/TERROR (the whole set, the other flags kept); a race flag where a monster had none (Zodiac 2676-2679 HUMAN, Tu-Gui
-- 7008-7010 ORC). Not here: rank, the elements (zywioly_moby*.sql), a column a script of ours writes (apply.sh, the
-- other files). Guarded: a column changes only while it holds the value the world was made with (world.sql /
-- mob_proto.mt2009plus.sql) - the operator's own value (the panel's database editor) is kept. Every start (apply.sh);
-- idempotent.
SET NAMES utf8mb4;"""

DROP_HEAD = """// MT2009_PLUS_MOBY_GLOBAL_V1: the drops of the owner's sheet of 20 October 2026 (%(src)s) that our monsters
// before Yohara lacked - the owner: "drop as in the sheet". GENERATED by tools/ymoby_arkusz/gen_moby_global.py - do
// not edit, rerun it. Added to the monster's own groups (Type drop). The sheet's vnums mapped to ours; out: what we
// lack, a quest's own items, materials nothing of ours uses, Sprochniala Skrzynia. The sheet gives no chances -
// TEMPORARY ones (tools/ymoby_arkusz/ymoby_data.py rule): the same item on our monsters of the same kind (normal /
// boss / Metin) -> the median of those rows, else of any kind (capped), else the kind's default by the item. A value
// v = v / 4 %% a kill before the level difference and the drop bonuses.
"""

REMOVE_HEAD = """# MT2009_PLUS_MOBY_GLOBAL_V1: the package's mob_drop_item rows the owner's sheet of 20 October 2026 does not list
# for that monster ("drop as in the sheet"). GENERATED by tools/ymoby_arkusz/gen_moby_global.py - do not edit.
# <mob> <item> <count> <value>: the game Dockerfile's step cuts exactly that row from that monster's groups (not
# MT2009_* / playerbot_* ones) and numbers the group again. Our own rows, the special groups and a quest's items stay.
"""


def main():
    if len(sys.argv) > 1 and sys.argv[1] == 'extract':
        sys.path.insert(0, os.path.join(REPO, 'tools', 'yohara_chestdrops'))
        ap = argparse.ArgumentParser()
        ap.add_argument('cmd')
        ap.add_argument('--xlsx', required=True)
        ap.add_argument('--db', default='mt2009plustest-db')
        ap.add_argument('--game', default='mt2009plustest-game')
        ap.add_argument('--package', default=PACKAGE)
        extract(ap.parse_args())
    render()


if __name__ == '__main__':
    main()
