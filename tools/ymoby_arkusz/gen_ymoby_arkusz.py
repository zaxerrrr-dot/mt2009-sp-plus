#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""gen_ymoby_arkusz.py                     render the server files from ymoby_arkusz.json
gen_ymoby_arkusz.py extract --xlsx FILE [--db CONTAINER] [--game CONTAINER]
                                           (re)read the sheet and our world, write ymoby_arkusz.json

MT2009_PLUS_MOBY_ARKUSZ_V1: our Yohara monsters against the owner's sheet of 20 October 2026
(Metin2_Moby_statystyki_EXP_i_drop.xlsx - metin2alerts' mob pages read 16 October 2026: HP, EXP, SungMa EXP, stats,
resistances, elements, the "Lup" lists without chances). The decisions are ymoby_data.py; the comparison report is
cache/yohara/porownanie-moby.md. Writes

  linux-port/docker/mariadb/playerbot/yohara_moby_arkusz.sql   guarded UPDATEs of ymoby_data.FIXES (apply.sh, after
                                                               every Yohara mob file) - the source rows hold the new
                                                               values already, this moves a world made before
  linux-port/docker/game/yohara_arkusz/mob_drop_item.yohara_arkusz.txt
                                                               the sheet's drops our Yohara monsters lack (our vnums,
                                                               chances by ymoby_data's rule) - groups MT2009_yarkusz_<mob>
                                                               of Type drop: the engine adds them to the monster's other
                                                               drop groups (item_manager_read_tables.cpp)

extract reads: the sheet (openpyxl - /opt/metin2/cache/xlsxenv/bin/python), world.mob_proto / item_proto of the
running test world (docker exec <db> mariadb), the game image's assembled share/locale/poland mob_drop_item.txt,
common_drop_item.txt and drop_wiki.txt (docker exec <game>; our own MT2009_yarkusz_ groups are ignored, so a second
extract after a deploy gives the same file), the Yohara monsters = every mob_proto row of mariadb/playerbot/yohara_*.sql
and shipdefense.sql.

Example: /opt/metin2/cache/xlsxenv/bin/python tools/ymoby_arkusz/gen_ymoby_arkusz.py extract --xlsx Moby.xlsx
         python3 tools/ymoby_arkusz/gen_ymoby_arkusz.py
"""
import argparse
import glob
import json
import os
import re
import statistics
import subprocess
import sys
import unicodedata

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(os.path.dirname(HERE))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(REPO, 'tools', 'yohara_chestdrops'))
import ymoby_data as D  # noqa: E402

DATA = os.path.join(HERE, 'ymoby_arkusz.json')
PB = os.path.join(REPO, 'linux-port', 'docker', 'mariadb', 'playerbot')
SQL_OUT = os.path.join(PB, 'yohara_moby_arkusz.sql')
DROP_OUT = os.path.join(REPO, 'linux-port', 'docker', 'game', 'yohara_arkusz', 'mob_drop_item.yohara_arkusz.txt')
GROUP = 'MT2009_yarkusz_'
LOCALE = '/opt/metin2/share/locale/poland'


def ascii_pl(s):
    return s.translate(str.maketrans('ąćęłńóśźżĄĆĘŁŃÓŚŹŻ', 'acelnoszzACELNOSZZ'))


def norm(s):
    return re.sub(r'[^a-z0-9]', '', unicodedata.normalize('NFKD', s.lower()).encode('ascii', 'ignore').decode())


# -- extract --------------------------------------------------------------------------------------------------------
def sql_vnums(path):
    """the vnums of the world.mob_proto rows of one of our SQL files"""
    out, cur = [], None
    for line in open(path, encoding='utf-8', errors='replace'):
        m = re.match(r'\s*(INSERT|REPLACE)\b.*?INTO\s+world\.(\w+)', line, re.I)
        if m:
            cur = m.group(2)
        elif re.match(r'\s*(UPDATE|DELETE|ALTER|SET)\b', line, re.I):
            cur = None
        if cur == 'mob_proto':
            m = re.match(r'\s*\((\d+),', line)
            if m:
                out.append(int(m.group(1)))
    return out


def db_rows(container, sql):
    out = subprocess.run(['docker', 'exec', '-i', container, 'sh', '-c',
                          'mariadb -uroot -p"$MARIADB_ROOT_PASSWORD" -B -N'], input=sql.encode(),
                         stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, check=True).stdout.decode('utf-8')
    return [l.split('\t') for l in out.split('\n') if l]


def game_file(container, name):
    return subprocess.run(['docker', 'exec', container, 'cat', '%s/%s' % (LOCALE, name)], stdout=subprocess.PIPE,
                          check=True).stdout


def drop_groups(text):
    """{mob: {item: [(group, type, count, value)]}} of a mob_drop_item.txt; our own groups left out"""
    out, cur = {}, None
    for line in text.split('\n'):
        p = line.split('--')[0].split()
        if not p:
            continue
        if p[0] == 'Group':
            cur = dict(name=p[1] if len(p) > 1 else '', mob=None, type=None, items=[])
        elif p[0] == '}' and cur:
            if cur['mob'] and not cur['name'].startswith(GROUP):
                for it, cnt, pct in cur['items']:
                    out.setdefault(cur['mob'], {}).setdefault(it, []).append((cur['name'], cur['type'], cnt, pct))
            cur = None
        elif cur is None or p[0] == '{':
            continue
        elif p[0] == 'Mob':
            cur['mob'] = int(p[1])
        elif p[0] == 'Type':
            cur['type'] = p[1].lower()
        elif p[0].isdigit() and len(p) >= 4 and p[1].isdigit():
            cur['items'].append((int(p[1]), int(p[2]), float(p[3])))
    return out


def common_items(text):
    out = set()
    for line in text.split('\n')[1:]:
        p = line.rstrip('\r').split('\t')
        for k in range(0, len(p) - 5, 6):
            if p[k + 4].strip().isdigit():
                out.add(int(p[k + 4]))
    return out


def read_sheet(path):
    import openpyxl
    wb = openpyxl.load_workbook(path, read_only=False, data_only=True)
    mobs, drops = {}, {}
    rows = list(wb['Moby'].iter_rows(values_only=True))
    head = list(rows[5])
    for r in rows[6:]:
        if isinstance(r[1], int):
            mobs[r[1]] = dict(zip(head, r))
    for r in list(wb['Drop'].iter_rows(values_only=True))[6:]:
        if isinstance(r[1], int) and isinstance(r[5], int):
            drops.setdefault(r[1], []).append((r[5], r[4]))
    return mobs, drops


def kind_of(row):
    if int(row['type']) == 2:
        return 'stone'
    return 'boss' if int(row['rank']) >= 4 else 'normal'


def category(vnum, item):
    if 27001 <= vnum <= 27125:
        return 'potion'
    if item['type'] in (1, 2):
        m = re.search(r'\+(\d+)$', item['name'])
        n = int(m.group(1)) if m else 0
        return 'gear+0-5' if n <= 5 else 'gear+%d' % min(n, 8)
    if item['type'] == 5 or 50721 <= vnum <= 50740 or 95733 <= vnum <= 95736:
        return 'material'
    return 'other'


def extract(a):
    import chestdrops as C
    sheet_mobs, sheet_drops = read_sheet(a.xlsx)
    yohara = set()
    for f in sorted(glob.glob(os.path.join(PB, 'yohara_*.sql'))) + [os.path.join(PB, 'shipdefense.sql')]:
        if os.path.basename(f) != os.path.basename(SQL_OUT):
            yohara.update(sql_vnums(f))
    no_drop = dict(D.NO_DROP_MOBS)
    for f in [D.NO_DROP_SQL] + D.NO_DROP_SQL_MORE:      # MT2009_PLUS_YOHARA_CRACK2_V1: the three other rifts
        for v in sql_vnums(os.path.join(PB, f)):
            no_drop.setdefault(v, 'the Time Rift (maps 404-407) drops nothing - server-patches/szczelina')
    mob = {}
    for p in db_rows(a.db, 'SELECT vnum, locale_name, `rank`, type, level FROM world.mob_proto'):
        mob[int(p[0])] = dict(name=p[1], rank=int(p[2]), type=int(p[3]), level=int(p[4]))
    item = {}
    for p in db_rows(a.db, 'SELECT vnum, locale_name, type FROM world.item_proto'):
        item[int(p[0])] = dict(name=p[1], type=int(p[2]))
    by_name = {}
    for v, it in item.items():
        by_name.setdefault(norm(it['name']), []).append(v)
    ours = drop_groups(game_file(a.game, 'mob_drop_item.txt').decode('utf-8', 'replace'))
    common = common_items(game_file(a.game, 'common_drop_item.txt').decode('latin-1'))
    wiki = {}
    for line in game_file(a.game, 'drop_wiki.txt').decode('cp1250', 'replace').split('\n'):
        p = line.split()
        if len(p) >= 3 and p[0] == 'drop' and p[1].isdigit() and p[2].isdigit():
            wiki.setdefault(int(p[1]), set()).add(int(p[2]))
    # the reference chances: the drop-type rows of our Yohara monsters, by kind
    ref = {}
    for m, its in ours.items():
        if m not in yohara or m not in mob:
            continue
        k = kind_of(mob[m])
        for it, gs in its.items():
            for g in gs:
                if g[1] == 'drop':
                    ref.setdefault((k, it), []).append((g[2], g[3]))
                    ref.setdefault(('any', it), []).append((g[2], g[3]))

    def ours_of(off, name):
        """the sheet's item -> (our vnum, None) or (None, why it stays out)"""
        if off in D.EXCLUDE:
            return None, D.EXCLUDE[off]
        if off in D.MAP:
            return D.MAP[off], None
        if off in C.SUBST and isinstance(C.SUBST[off][0], int):
            return C.SUBST[off][0], None
        if off in C.SKIP:
            return None, C.SKIP[off]
        if off in item and (off in D.SAME or norm(item[off]['name']) == norm(name)):
            return off, None
        same = by_name.get(norm(name), [])
        if len(same) == 1:
            return same[0], None
        if off in item:
            return None, 'our %d is another item (%s)' % (off, item[off]['name'])
        return None, 'not in our world'

    adds, skipped, out_mobs = {}, {}, {}
    for v in sorted(sheet_drops):
        if v not in yohara or v not in mob:
            continue
        if v in no_drop:
            out_mobs[v] = no_drop[v]
            continue
        k = kind_of(mob[v])
        have = set(ours.get(v, {})) | wiki.get(v, set()) | common
        rows = []
        for off, name in sheet_drops[v]:
            o, why = ours_of(off, name)
            if o is None:
                skipped.setdefault('%d %s' % (off, name), [why, 0])[1] += 1
                continue
            if o in have or any(r[0] == o for r in rows):
                continue
            if o in D.EXCLUDE:
                skipped.setdefault('%d %s' % (off, name), [D.EXCLUDE[o], 0])[1] += 1
                continue
            same = ref.get((k, o))
            if same:
                cnt = int(statistics.median_low([c for c, _ in same]))
                val = statistics.median([p for _, p in same])
                how = 'ours'
            elif ref.get(('any', o)):
                anyr = ref[('any', o)]
                cnt = int(statistics.median_low([c for c, _ in anyr]))
                val = min(statistics.median([p for _, p in anyr]), D.CAP[k])
                how = 'ours-other-kind'
            else:
                cat = category(o, item[o])
                cnt = 1
                val = D.DEFAULT[cat][('normal', 'boss', 'stone').index(k)]
                how = 'default:' + cat
            rows.append([o, cnt, round(val, 4), item[o]['name'], off, how])
        if rows:
            adds[v] = dict(name=mob[v]['name'], kind=k, rows=rows)
    stats = {}
    for v in sorted(yohara):
        if v in sheet_mobs:
            r = sheet_mobs[v]
            stats[v] = dict((k, r[k]) for k in ('Mob', 'Poziom', 'HP / PŻ', 'EXP', 'SungMa EXP'))
    json.dump(dict(source=re.sub(r'^[0-9a-f]{8}-', '', os.path.basename(a.xlsx)), adds=adds, skipped=skipped, no_drop=out_mobs, sheet=stats),
              open(DATA, 'w', encoding='utf-8'), ensure_ascii=False, indent=0, sort_keys=True)
    print('extract: %d monsters get %d rows; %d sheet items left out; %d monsters without a drop on purpose' % (
        len(adds), sum(len(x['rows']) for x in adds.values()), len(skipped), len(out_mobs)))


# -- render ---------------------------------------------------------------------------------------------------------
def render():
    data = json.load(open(DATA, encoding='utf-8'))
    sheet = data['sheet']
    col_of = {'level': 'Poziom', 'max_hp': 'HP / PŻ', 'exp': 'EXP'}
    sql = [SQL_HEAD]
    for v, col, old, new in D.FIXES:
        k = col_of.get(col)
        if k:      # the sheet must say so
            assert sheet[str(v)][k] == new, (v, col, sheet[str(v)][k], new)
        sql.append('UPDATE world.mob_proto SET `%s` = %d WHERE vnum = %d AND `%s` = %d;  -- %s' % (
            col, new, v, col, old, ascii_pl(sheet[str(v)]['Mob'])))
    with open(SQL_OUT, 'w', encoding='utf-8', newline='\n') as f:
        f.write('\n'.join(sql) + '\n')
    out = [DROP_HEAD % dict(src=data['source'])]
    n = 0
    for v in sorted(data['adds'], key=int):
        a = data['adds'][v]
        assert len(a['rows']) < 256, v
        out.append('Group\t%s%s' % (GROUP, v))
        out.append('{')
        out.append('\tMob\t%s\t-- %s' % (v, ascii_pl(a['name'])))
        out.append('\tType\tdrop')
        for i, (o, cnt, val, name, off, how) in enumerate(a['rows'], 1):
            out.append('\t%d\t%d\t%d\t%s\t-- %s%s' % (i, o, cnt, ('%.4f' % val).rstrip('0').rstrip('.'),
                                                       ascii_pl(name), '' if o == off else ' (sheet %d)' % off))
            n += 1
        out.append('}')
    os.makedirs(os.path.dirname(DROP_OUT), exist_ok=True)
    with open(DROP_OUT, 'w', encoding='utf-8', newline='\r\n') as f:
        f.write('\n'.join(out) + '\n')
    print('render: %d UPDATEs; %d drop groups, %d rows' % (len(D.FIXES), len(data['adds']), n))


SQL_HEAD = """-- MT2009_PLUS_MOBY_ARKUSZ_V1: our Yohara monsters brought to the owner's sheet of 20 October 2026
-- (Metin2_Moby_statystyki_EXP_i_drop.xlsx). GENERATED by tools/ymoby_arkusz/gen_ymoby_arkusz.py from ymoby_data.FIXES -
-- do not edit, rerun it. The rows' own files (shipdefense.sql, tools/yohara_crack, yohara_zaklety, yohara_maps3) hold
-- the new values already (INSERT IGNORE); this moves a world made before. Guarded: only a row that still has our old
-- value changes - one the operator set himself is kept. Every start (apply.sh, after every Yohara mob file); idempotent.
SET NAMES utf8mb4;"""

DROP_HEAD = """// MT2009_PLUS_MOBY_ARKUSZ_V1: the drops of the owner's sheet of 20 October 2026 that our Yohara monsters lacked
// (%(src)s, the "Lup" lists - no chances there).
// GENERATED by tools/ymoby_arkusz/gen_ymoby_arkusz.py - do not edit, rerun it. Added to the monster's own groups
// (Type drop: the engine merges the groups of one monster); our own rows stay. The sheet's vnums mapped to ours
// (tools/yohara_chestdrops SUBST, ymoby_data); what we lack, the quests' task items and Sprochniala Skrzynia stay out;
// the Time Rift (404) and Skarb Hydry keep no drop. Chances (ymoby_data.py): the same item on our Yohara monsters of
// the same kind -> the median of those rows, else of any kind (capped), else the kind's default by the item. A value
// v = v / 4 %% a kill before the level difference and the drop bonuses (as the other Yohara drop files). Temporary -
// cache/yohara/PROCENTY.md.
"""


def main():
    if len(sys.argv) > 1 and sys.argv[1] == 'extract':
        ap = argparse.ArgumentParser()
        ap.add_argument('cmd')
        ap.add_argument('--xlsx', required=True)
        ap.add_argument('--db', default='mt2009plustest-db')
        ap.add_argument('--game', default='mt2009plustest-game')
        extract(ap.parse_args())
    render()


if __name__ == '__main__':
    main()
