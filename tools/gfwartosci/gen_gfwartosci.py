#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""gen_gfwartosci.py [--import <package dir>]

MT2009_PLUS_GF_VALUES_V1 (the owner, 22 October 2026: "wartosci jak na GF - akceptuje"): the values of GF 25.2.17 in
the vnums our world shares with it, where ours still had the world's own (the owner's package p-gf-po-3.0.1,
sql/3_wartosci_gf.sql - the fields 3.0.1 did not touch): items' magic_pct, value0-5 (attack / defence / shape) and
limitvalue0 (the level they need - the jewellery of Rubin / Granat / Szmaragd / Szafir at GF's 85 / 90 / 95 / 100, the
end of MT2009_PLUS_JEWELS75_V2's level 80), monsters' dam_multiply, battle_type, ai_flag, attack_range, setImmuneFlag
and a few exp / drain_sp values.
MT2009_PLUS_GF_REFINE_V1 (the owner, 22 October 2026): the package's sql/2_ulepszanie_poza_arkuszem.sql - the refining
the owner's sheet (tools/refineglobal) has no row for, by the pl-wiki's tables: Wachlarz Lezacego Smoka 7170-7178 and
Wachlarz 8 Trygramow 7180-7188 on refine_proto 30074-30089 (Odlamki Energii), Czarna Okragla Tarcza 13200-13208 on
2 / 344 / 897 / 898 / 1062-1064 / 30021 / 30017, and MT2009_PLUS_POGROMCA_V2: Pogromca Nieb. Smoka+9 (3189) goes no
further (GF: no next item - the owner's decision of 22 October; MT2009_PLUS_POGROMCA_V1's +9 -> Ostrze Slonca by 610
ends; Pogromca itself still comes from Partyzana+9 at Seon-Pyeong, tools/refineglobal ELITE).

What is NOT changed (each run works it out again from the repo, so a later generator is respected too):
  * a vnum one of our generators makes or rewrites - every INSERT / UPDATE of world.item_proto / world.mob_proto in
    linux-port/docker/mariadb/playerbot/*.sql except the package dumps and the files below (the Yohara sets 21210..
    whose value3 is our body shape, the Sung Ma glove stones 28146-28447, the Yohara monsters ...);
  * a monster's column the owner's sheets set (moby_global.sql, yohara_moby_arkusz.sql) or maps_wz.sql sets (level);
  * KEEP_MOBS: the Blue Dragon's stones 8031-8034 (apply.sh, ours - the owner); KEEP_ITEMS: vnums that are other
    items here (the mod's Kostium / Helm Wladcy Smierci ...).
Changed elsewhere to the same values, so nothing undoes them at a start: tools/wikinowe/wiki_nowe.json (the cyanite
weapons 500... and the boots 15440-15459), tools/noawaken (the seven families' rows on a new world), apply.sh's
MT2009_PLUS_JEWELS75_V3 (no level 80 any more) and MT2009_PLUS_POGROMCA_V2.

Writes (GENERATED - edit tools/gfwartosci/gf_wartosci.json or this file, run it again):
  linux-port/docker/mariadb/playerbot/gf_wartosci.sql   apply.sh, every start, after every item / monster step and
                                                        before refine_global.sql. Guarded: a column changes only while
                                                        it holds our old value (or the package dump's) - a value the
                                                        operator set in the panel stays. Idempotent.
The client's item records take the same item values (client-patches/client-2.0.30/tools/gfint, item_values()).

--import <dir>: (re)reads sql/3_wartosci_gf.sql and sql/2_ulepszanie_poza_arkuszem.sql into gf_wartosci.json.
Example: python3 tools/gfwartosci/gen_gfwartosci.py
"""
import glob
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(os.path.dirname(HERE))
DATA = os.path.join(HERE, 'gf_wartosci.json')
PB = os.path.join(REPO, 'linux-port', 'docker', 'mariadb', 'playerbot')
SQL_OUT = os.path.join(PB, 'gf_wartosci.sql')
M, MR = 'MT2009_PLUS_GF_VALUES_V1', 'MT2009_PLUS_GF_REFINE_V1'

# the package's dumps (the world's own rows - the guard's second old value) and the files that are not "a generator's
# own vnums": the global switches, the elements, the once-per-world noawaken, wiki_nowe (its json carries GF's values)
DUMPS = {'item_proto': 'item_proto.mt2009plus.sql', 'mob_proto': 'mob_proto.mt2009plus.sql'}
NOT_OWNED = {'item_proto.mt2009plus.sql', 'mob_proto.mt2009plus.sql', 'item_proto_global.sql', 'refine_global.sql',
             'noawaken.sql', 'wiki_nowe.sql', 'bonusy67_wiki.sql', 'bonusy_global.sql', 'bonusy_mt2009.sql',
             'zywioly_moby.sql', 'zywioly_moby_global.sql', 'gf_wartosci.sql'}
# files whose UPDATEs own only the columns they set (by vnum), not the whole row
FIELD_OWNERS = ('moby_global.sql', 'yohara_moby_arkusz.sql', 'maps_wz.sql')
KEEP_MOBS = dict((v, 'a Blue Dragon stone (apply.sh, ours)') for v in (8031, 8032, 8033, 8034))
# vnums that are other items here than on GF (the package's own list of icon collisions, klient/ikony/ikony.tsv):
# the mod's Kostium / Helm Wladcy Smierci - GF's values would be another item's
KEEP_ITEMS = dict((v, 'another item here than on GF (the mod\'s own)') for v in (
    30331, 30332, 30333, 30341, 41980, 41981, 45722, 49001, 49002, 49003, 49004, 49005, 49006, 50218, 72734,
    83032, 83033, 83034))
# rows the package left out that belong with its jewellery levels: Rubinowa Bransoleta +0..+9 - GF / Owsap 85 (the
# package had the necklace and the earrings of Rubin at 85, not the bracelet)
EXTRA_ITEMS = dict((str(v), {'limitvalue0': ['85', '80']}) for v in range(14500, 14510))
FLOAT_COLS = ('dam_multiply',)
SET_COLS = ('ai_flag', 'setImmuneFlag')


# -- import ---------------------------------------------------------------------------------------------------------
def import_package(pkg):
    t = open(os.path.join(pkg, 'sql', '3_wartosci_gf.sql'), 'rb').read().decode('latin-1')
    old, new = {}, {'item_proto': {}, 'mob_proto': {}}
    for line in t.splitlines():
        m = re.match(r'^-- (item_proto|mob_proto) (\d+): (.*)$', line)
        if m:
            for part in m.group(3).split('; '):
                c, ch = part.split(' ', 1)
                o, n = ch.split(' -> ')
                old[(m.group(1), m.group(2), c)] = (o, n)
            continue
        m = re.match(r"^UPDATE world\.(item_proto|mob_proto) SET (.*) WHERE `vnum` = '(\d+)';$", line)
        if m:
            for c, val in re.findall(r"`(\w+)` = '([^']*)'", m.group(2)):
                o, n = old[(m.group(1), m.group(3), c)]
                assert n == val, (m.groups(), c)
                new[m.group(1)].setdefault(m.group(3), {})[c] = [val, o]
    t = open(os.path.join(pkg, 'sql', '2_ulepszanie_poza_arkuszem.sql'), 'rb').read().decode('latin-1')
    ins = t[t.index('INSERT IGNORE INTO world.refine_proto'):t.index(';', t.index('INSERT IGNORE INTO world.refine_proto'))]
    refine_new = [[int(x) for x in re.findall(r"'(-?\d+)'", r)] for r in re.findall(r'^\((.*)\),?$', ins, re.M)]
    changes = {'refine_proto': {}, 'item_proto': {}}
    for line in t.splitlines():
        m = re.match(r'^-- (refine_proto|item_proto) (\d+): (.*)$', line)
        if m:
            for part in m.group(3).split('; '):
                c, ch = part.split(' ', 1)
                o, n = ch.split(' -> ')
                changes[m.group(1)].setdefault(m.group(2), {})[c] = [int(n), int(o)]
    out = dict(source='the owner\'s package p-gf-po-3.0.1 (21 October 2026): GF 25.2.17 - sql/3_wartosci_gf.sql '
                      '(values), sql/2_ulepszanie_poza_arkuszem.sql (refining); [GF value, our old value]',
               items=new['item_proto'], mobs=new['mob_proto'], refine_new=sorted(refine_new),
               refine_changes=changes['refine_proto'], item_refine=changes['item_proto'])
    with open(DATA, 'w', encoding='utf-8', newline='\n') as f:
        json.dump(out, f, ensure_ascii=False, indent=0, sort_keys=True)
        f.write('\n')


# -- what our generators own ----------------------------------------------------------------------------------------
def _vnums(text, table):
    """{vnum: set of columns or None (the whole row)} of the INSERTs / UPDATEs of world.<table> in one SQL file"""
    out = {}
    for m in re.finditer(r'INSERT(?: IGNORE)? INTO (?:world\.)?`?%s`?\s*\(([^)]*)\)\s*VALUES(.*?);\s*$' % table,
                         text, re.S | re.M):
        cols = [c.strip(' `\n') for c in m.group(1).split(',')]
        vi = cols.index('vnum') if 'vnum' in cols else 0
        for r in re.finditer(r'^\s*\((.*)\)\s*[,;]?\s*$', m.group(2), re.M):
            f = re.findall(r"'(?:[^'\\]|\\.|'')*'|[^,]+", r.group(1))
            try:
                out[int(f[vi].strip(" '"))] = None
            except (ValueError, IndexError):
                pass
    for m in re.finditer(r'UPDATE (?:world\.)?`?%s`?\s+(?:\w+\s+)?SET\s(.*?)\sWHERE\s(.*?);' % table, text, re.S):
        cols = set(re.findall(r'`?(\w+)`?\s*=\s*(?!=)', m.group(1)))
        vs = set(int(a) for a in re.findall(r'vnum\s*=\s*(\d+)', m.group(2)))
        for a, b in re.findall(r'vnum\s+BETWEEN\s+(\d+)\s+AND\s+(\d+)', m.group(2)):
            vs.update(range(int(a), int(b) + 1))
        for lst in re.findall(r'vnum\s+IN\s*\(([\d,\s]+)\)', m.group(2)):
            vs.update(int(x) for x in lst.split(',') if x.strip())
        for v in vs:
            if v not in out:
                out[v] = set(cols)
            elif out[v] is not None:
                out[v] |= cols
    return out


def owned():
    """{'item_proto' / 'mob_proto': {vnum: (file, None = the row | set of columns)}}"""
    own = {'item_proto': {}, 'mob_proto': {}}
    for path in sorted(glob.glob(os.path.join(PB, '*.sql'))):
        name = os.path.basename(path)
        if name in NOT_OWNED:
            continue
        text = open(path, 'rb').read().decode('utf-8', 'replace')
        for table in own:
            for v, cols in _vnums(text, table).items():
                if name not in FIELD_OWNERS:
                    cols = None
                prev = own[table].get(v)
                if prev is None or prev[1] is not None:
                    if cols is None:
                        own[table][v] = (name, None)
                    elif prev is None:
                        own[table][v] = (name, set(cols))
                    else:
                        own[table][v] = (prev[0], prev[1] | cols)
    return own


def dump_values(table):
    """{vnum: {column: value}} of the package dump (the guard's second old value)"""
    text = open(os.path.join(PB, DUMPS[table]), encoding='utf-8').read()
    m = re.search(r'INSERT IGNORE INTO world\.%s \(([^)]*)\) VALUES' % table, text)
    cols = [c.strip('` ') for c in m.group(1).split(',')]
    out = {}
    for r in re.finditer(r'^\((\d+),(.*)\)[,;]\s*$', text, re.M):
        f = re.findall(r"'(?:[^'\\]|\\.|'')*'|[^,]+", r.group(1) + ',' + r.group(2))
        if len(f) == len(cols):
            out[int(r.group(1))] = dict((c, x.strip("'")) for c, x in zip(cols, f))
    return out


# -- the values -------------------------------------------------------------------------------------------------------
_CACHE = {}


def plan():
    """(items, mobs, skipped): {vnum: {column: [GF, our old]}} after the exclusions; skipped: [(table, vnum, column,
    why)]"""
    if 'plan' in _CACHE:
        return _CACHE['plan']
    d = json.load(open(DATA, encoding='utf-8'))
    own = owned()
    items = dict((k, dict(v)) for k, v in d['items'].items())
    for k, v in EXTRA_ITEMS.items():
        assert k not in items, k
        items[k] = v
    out, skipped = {'item_proto': {}, 'mob_proto': {}}, []
    for table, src in (('item_proto', items), ('mob_proto', d['mobs'])):
        for k, cols in src.items():
            v = int(k)
            for c, pair in cols.items():
                o = own[table].get(v)
                if table == 'mob_proto' and v in KEEP_MOBS:
                    skipped.append((table, v, c, KEEP_MOBS[v]))
                elif table == 'item_proto' and v in KEEP_ITEMS:
                    skipped.append((table, v, c, KEEP_ITEMS[v]))
                elif o is not None and (o[1] is None or c in o[1]):
                    skipped.append((table, v, c, o[0]))
                else:
                    out[table].setdefault(v, {})[c] = pair
    _CACHE['plan'] = (out['item_proto'], out['mob_proto'], skipped)
    return _CACHE['plan']


def item_values(vnum):
    """{column: GF value (int)} of one item - for the generators that write the same rows (noawaken, the client)"""
    return dict((c, int(p[0])) for c, p in plan()[0].get(vnum, {}).items())


def item_refine():
    """{vnum: {column: [new, old]}} - refined_vnum / refine_set of MT2009_PLUS_GF_REFINE_V1"""
    return dict((int(k), v) for k, v in json.load(open(DATA, encoding='utf-8'))['item_refine'].items())


def _lit(c, x):
    if c in SET_COLS:
        return "'%s'" % x
    return x


def _guard(c, olds):
    if c in FLOAT_COLS:
        return '(%s)' % ' OR '.join('ABS(`%s` - %s) < 0.0001' % (c, o) for o in olds)
    if c in SET_COLS:
        return '`%s` IN (%s)' % (c, ', '.join("'%s'" % o for o in olds))
    return '`%s` IN (%s)' % (c, ', '.join(olds))


def main():
    if '--import' in sys.argv:
        import_package(sys.argv[sys.argv.index('--import') + 1])
    d = json.load(open(DATA, encoding='utf-8'))
    items, mobs, skipped = plan()
    dumps = {'item_proto': dump_values('item_proto'), 'mob_proto': dump_values('mob_proto')}
    L = ['-- %s / %s: GF 25.2.17\'s values and refining in the vnums our world shares with it (the owner, 22 October'
         % (M, MR),
         '-- 2026). GENERATED by tools/gfwartosci/gen_gfwartosci.py from tools/gfwartosci/gf_wartosci.json - do not edit,',
         '-- rerun it. apply.sh runs it every start after the other item / monster steps, before refine_global.sql.',
         '-- Guarded: a column changes only from our old value (or the package dump\'s) - an operator\'s value stays.',
         '-- %d items, %d monsters; left out (our generators\' / sheets\' / Blue Dragon\'s): %d columns.'
         % (len(items), len(mobs), len(skipped)),
         'SET NAMES utf8mb4;', '']
    for table, rows in (('item_proto', items), ('mob_proto', mobs)):
        L.append('-- %s' % table)
        for v in sorted(rows):
            sets = []
            for c in sorted(rows[v]):
                gf, ours = rows[v][c]
                olds = [ours]
                dv = dumps[table].get(v, {}).get(c)
                if dv is not None and dv != ours and dv != gf:
                    olds.append(dv)
                sets.append('`%s` = IF(%s, %s, `%s`)' % (c, _guard(c, olds), _lit(c, gf), c))
            L.append('UPDATE world.%s SET %s WHERE vnum = %d;' % (table, ', '.join(sets), v))
        L.append('')
    L.append('-- %s: refine_proto - the new recipes (INSERT IGNORE: a recipe the operator changed stays) and the changed'
             % MR)
    L.append('-- ones (from the old value only).')
    cols = ('id', 'vnum0', 'count0', 'vnum1', 'count1', 'vnum2', 'count2', 'vnum3', 'count3', 'vnum4', 'count4',
            'cost', 'src_vnum', 'result_vnum', 'prob')
    L.append('INSERT IGNORE INTO world.refine_proto (%s) VALUES' % ', '.join('`%s`' % c for c in cols))
    L.append(',\n'.join('(%s)' % ', '.join(str(x) for x in r) for r in d['refine_new']) + ';')
    for k in sorted(d['refine_changes'], key=int):
        ch = d['refine_changes'][k]
        L.append('UPDATE world.refine_proto SET %s WHERE id = %s AND %s;' % (
            ', '.join('`%s` = %d' % (c, n) for c, (n, o) in sorted(ch.items())), k,
            ' AND '.join('`%s` = %d' % (c, o) for c, (n, o) in sorted(ch.items()))))
    L.append('-- %s: the items\' recipes (Pogromca+9 3189: MT2009_PLUS_POGROMCA_V2, no next item)' % MR)
    for v, ch in sorted(item_refine().items()):
        L.append('UPDATE world.item_proto SET %s WHERE vnum = %d AND %s;' % (
            ', '.join('`%s` = %d' % (c, n) for c, (n, o) in sorted(ch.items())), v,
            ' AND '.join('`%s` = %d' % (c, o) for c, (n, o) in sorted(ch.items()))))
    with open(SQL_OUT, 'w', encoding='utf-8', newline='\n') as f:
        f.write('\n'.join(L) + '\n')
    by = {}
    for t, v, c, why in skipped:
        by.setdefault((t, why), set()).add(v)
    print('items %d (%d columns), monsters %d (%d columns), refine_proto +%d / %d changed, item recipes %d'
          % (len(items), sum(len(x) for x in items.values()), len(mobs), sum(len(x) for x in mobs.values()),
             len(d['refine_new']), len(d['refine_changes']), len(d['item_refine'])))
    for (t, why), vs in sorted(by.items()):
        vs = sorted(vs)
        print('  left out %s %s: %d vnums (%s%s)' % (t, why, len(vs), ', '.join(map(str, vs[:8])),
                                                    ' ...' if len(vs) > 8 else ''))


if __name__ == '__main__':
    main()
