#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""gen_refineglobal.py [--xlsx <sheet.xlsx>]

MT2009_PLUS_REFINE_GLOBAL_V1 - refining as on the global server for every item (the owner, 20 October 2026: "ulepszanie
ma byc jak na globalu dla kazdego przedmiotu"). Source: the owner's sheet Metin2_Ulepszanie_szanse_i_ulepszacze.xlsx
(metin2alerts.com/pl/wiki/upgrade-chance, read 16.10.2026), tab "Ulepszenia": one row a step - the item it starts
from, the item it makes (+n -> +n+1, or a "Przemiana": +9 -> the next item's +0), the chance ("Szansa bazowa" - the
Blacksmith's, the Blessing Scroll's and the Magic Stone's), the Yang and the materials of one attempt.

  --xlsx   reads the sheet again into tools/refineglobal/ulepszanie_global.json (needs openpyxl; the file is in the
           repo, so a plain run needs neither the sheet nor openpyxl)

Writes linux-port/docker/mariadb/playerbot/refine_global.sql (apply.sh, every start, after every other item step):
  - world.refine_proto 40000.. : one row per distinct recipe of the sheet (Yang, chance, materials), written every
    start (ON DUPLICATE KEY UPDATE - the generator owns them);
  - world.item_proto: every item of the sheet that we have gets the step's recipe (refine_set) and its next item
    (refined_vnum) when
      * its next item is the sheet's (refined_vnum = the result) - or, for a Przemiana, it had none (0);
      * the result item exists here;
      * every material exists here (a step whose material we lack stays as it is - listed by --report in the run).
    Steps without a chance in the sheet ("Brak danych") stay as they are.
The material vnums are the sheet's, except two we have under other vnums (Stabilne Sznury, Ciezkie Pasy - wiki_nowe).
MT2009_PLUS_SEONPYEONG_ELITE_V1 (the owner, 22 October 2026: Seon-Pyeong "as on the wiki"): the +9 -> next item steps
only Seon-Pyeong (20091) makes - dragged onto him, 100%, the stones and bonuses kept - take FIXED recipe ids 39900-39903
(ELITE below), the range the engine's IsEliteRefine knows (server-patches/seonpyeong): the Blacksmith, the guild and
Demon Tower smiths and the scrolls refuse them. Fixed, so a new read of the sheet cannot move them; the other recipes keep
their numbers (40000.., by first use) - a recipe used only by elite steps keeps its row, unused. ELITE also adds the
steps the sheet lacks (Partyzana+9 -> Pogromca Nieb. Smoka, the level-105 armours +9 -> the cyanite ones).
The client's item_proto takes the same fields from the same json (client-patches/client-2.0.30/tools/refineglobal).
Idempotent. Example: python3 tools/refineglobal/gen_refineglobal.py
"""
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(os.path.dirname(HERE))
DATA = os.path.join(HERE, 'ulepszanie_global.json')
SQL_OUT = os.path.join(REPO, 'linux-port', 'docker', 'mariadb', 'playerbot', 'refine_global.sql')
M = 'MT2009_PLUS_REFINE_GLOBAL_V1'
ID0 = 40000                 # our refine_proto ids 40000.. (item_proto.refine_set is a WORD: < 65536)
ID_MAX = 49999
# the sheet's vnum -> ours: the same item under another vnum here (tools/wikinowe, Autor: Digi Rasta)
MATERIAL_VNUM = {30612: 95601,     # Stabilne Sznury
                 30611: 95603}     # Ciezkie Pasy
# MT2009_PLUS_SEONPYEONG_ELITE_V1: Seon-Pyeong's steps (the pl-wiki "Wytwarzanie Broni / Zbroi / Butow", the
# owner's package of 21 October 2026): (fixed id, what, the sheet's +9 steps by their item, steps the sheet lacks
# (item, result) - they take the group's recipe). Every sheet step of a group must have the same recipe (checked).
# Keep 39900-39999 in step with constants.cpp IsEliteRefine (server-patches/seonpyeong/edits.json).
ELITE_ID0, ELITE_ID_MAX = 39900, 39999
ELITE = (
    (39900, 'weapons of level 65/66 +9 -> 80', (149, 159, 249, 1109, 2149, 5109, 6059, 7149),
     ((3139, 3180),)),          # Partyzana+9 -> Pogromca Nieb. Smoka+0 (cube.seon_pyeong.txt's recipe until now)
    (39901, 'body armours of level 66 and boots of 47-59 +9 -> 80',
     (11299, 11499, 11699, 11899, 15169, 15189, 15209, 15229), ()),
    (39902, 'weapons of level 80 +9 -> 87-105', (209, 279, 289, 2169, 3159, 4049, 5339, 6089, 7199), ()),
    (39903, 'weapons of level 87-105 and body armours of level 105-115 +9 -> cyanite',
     (479, 1349, 2379, 3199, 5349, 6099, 7379),
     # the level-105 armours (tools/zbroje105, MT2009_PLUS_ARMOR105_V1; the package's refine_proto 717 had this recipe)
     tuple((a + 9, c) for a, c in ((20760, 12050), (20770, 12060), (20780, 12070), (20790, 12080),
                                   (20810, 12050), (20820, 12060), (20830, 12070), (20840, 12080),
                                   (20860, 12050), (20870, 12060), (20880, 12070), (20890, 12080),
                                   (20910, 12050), (20920, 12060), (20930, 12070), (20940, 12080)))),
)
ELITE_ROWS = []              # their refine_proto rows (load() fills it)
MAT_RE = re.compile(r'^\s*(\d+)\s*×\s*(.+?)\s*\[(\d+)\]\s*$')


def extract(xlsx):
    import openpyxl
    wb = openpyxl.load_workbook(xlsx, read_only=False, data_only=True)
    ws = wb['Ulepszenia']
    head = None
    steps = {}
    for r in ws.iter_rows(values_only=True):
        if head is None:
            if r and r[0] == 'Przedmiot bazowy':
                head = list(r)
            continue
        if r[0] is None:
            continue
        d = dict(zip(head, r))
        mats = []
        if d['Ulepszacze / próba'] != 'Brak wymaganych ulepszaczy':
            for line in d['Ulepszacze / próba'].split('\n'):
                m = MAT_RE.match(line)
                assert m, line
                mats.append([int(m.group(3)), int(m.group(1))])
        prob = d['Szansa bazowa']
        prob = None if isinstance(prob, str) else int(round(prob * 100))
        st = dict(src=int(d['ID wejściowe']), res=int(d['ID wynikowe']), name=d['Z przedmiotu'],
                  to=d['Na przedmiot'], przemiana=d['Rodzaj etapu'] == 'Przemiana', prob=prob,
                  cost=int(d['Koszt Yang / próba']), mats=mats)
        old = steps.get(st['src'])
        assert old is None or old == st, (old, st)        # a step listed under two lines is the same step
        steps[st['src']] = st
    out = dict(source='metin2alerts.com/pl/wiki/upgrade-chance, read 16.10.2026 (the owner\'s sheet of 20.10.2026)',
               steps=[steps[k] for k in sorted(steps)])
    with open(DATA, 'w', encoding='utf-8', newline='\n') as f:
        json.dump(out, f, ensure_ascii=False, indent=0)
        f.write('\n')


def load():
    d = json.load(open(DATA, encoding='utf-8'))
    recipes, ids, steps, nochance = [], {}, [], 0
    for s in d['steps']:
        if s['prob'] is None:
            nochance += 1
            continue
        mats = [(MATERIAL_VNUM.get(v, v), c) for v, c in s['mats']]
        assert len(mats) <= 5, s
        key = (s['cost'], s['prob'], tuple(mats))
        if key not in ids:
            ids[key] = ID0 + len(recipes)
            recipes.append(key)
        steps.append(dict(src=s['src'], res=s['res'], rid=ids[key], tr=1 if s['przemiana'] else 0, mats=mats))
    assert ID0 + len(recipes) - 1 <= ID_MAX, len(recipes)
    ELITE_ROWS[:] = elite_steps(recipes, steps)     # MT2009_PLUS_SEONPYEONG_ELITE_V1
    return recipes, steps, nochance


def elite_steps(recipes, steps):
    """MT2009_PLUS_SEONPYEONG_ELITE_V1: Seon-Pyeong's steps onto their fixed ids, his steps the sheet lacks added;
    returns the fixed ids' refine_proto rows (each group's recipe - the sheet's)"""
    by_src = dict((s['src'], s) for s in steps)
    rows = []
    for rid, what, srcs, extra in ELITE:
        assert ELITE_ID0 <= rid <= ELITE_ID_MAX, rid
        mine = [by_src[v] for v in srcs if v in by_src]
        keys = set(recipes[s['rid'] - ID0] for s in mine)
        assert len(keys) == 1, (rid, what, keys)       # a group is one recipe
        cost, prob, mats = keys.pop()
        for s in mine:
            s['rid'] = rid
        for src, res in extra:
            assert src not in by_src, (rid, src, 'the sheet has this step now - move it to the group\'s items')
            steps.append(dict(src=src, res=res, rid=rid, tr=1, mats=list(mats)))
        m = list(mats) + [(0, 0)] * (5 - len(mats))
        rows.append([rid] + [x for p in m for x in p] + [cost, 0, 0, prob])
    return rows


def recipe_rows(recipes):
    rows = []
    for n, (cost, prob, mats) in enumerate(recipes):
        m = list(mats) + [(0, 0)] * (5 - len(mats))
        rows.append([ID0 + n] + [x for p in m for x in p] + [cost, 0, 0, prob])
    return rows


def main():
    if '--xlsx' in sys.argv:
        extract(sys.argv[sys.argv.index('--xlsx') + 1])
    recipes, steps, nochance = load()
    rows = recipe_rows(recipes) + ELITE_ROWS
    L = ['-- %s: refining as on the global server for every item (the owner, 20 October 2026). GENERATED by' % M,
         '-- tools/refineglobal/gen_refineglobal.py from tools/refineglobal/ulepszanie_global.json (the owner\'s sheet,',
         '-- metin2alerts upgrade-chance, read 16.10.2026) - do not edit, rerun it. apply.sh runs it every start after every',
         '-- other item step. %d steps with a chance, %d recipes (refine_proto %d-%d), %d steps without a chance left out.'
         % (len(steps), len(recipes), ID0, ID0 + len(recipes) - 1, nochance),
         '-- An item takes the step only where its next item is the sheet\'s (or, for a "+9 -> next item" step, it had',
         '-- none), the result exists here and every material exists here. Idempotent.',
         '-- MT2009_PLUS_SEONPYEONG_ELITE_V1: Seon-Pyeong\'s steps (only at him - constants.cpp IsEliteRefine) on the fixed',
         '-- recipes %d-%d (gen_refineglobal.py ELITE), %d of them added beyond the sheet.'
         % (ELITE_ID0, ELITE[-1][0], sum(len(e[3]) for e in ELITE)),
         'SET NAMES utf8mb4;',
         'USE world;',
         'INSERT INTO world.refine_proto (id,vnum0,count0,vnum1,count1,vnum2,count2,vnum3,count3,vnum4,count4,cost,'
         'src_vnum,result_vnum,prob) VALUES',
         ',\n'.join('(' + ','.join(str(x) for x in r) + ')' for r in rows),
         'ON DUPLICATE KEY UPDATE vnum0=VALUES(vnum0), count0=VALUES(count0), vnum1=VALUES(vnum1), count1=VALUES(count1),'
         ' vnum2=VALUES(vnum2), count2=VALUES(count2), vnum3=VALUES(vnum3), count3=VALUES(count3), vnum4=VALUES(vnum4),'
         ' count4=VALUES(count4), cost=VALUES(cost), src_vnum=0, result_vnum=0, prob=VALUES(prob);',
         'DROP TEMPORARY TABLE IF EXISTS tmp_refine_global;',
         'CREATE TEMPORARY TABLE tmp_refine_global (src INT UNSIGNED NOT NULL PRIMARY KEY, res INT UNSIGNED NOT NULL,'
         ' rid INT UNSIGNED NOT NULL, tr TINYINT NOT NULL);',
         'INSERT INTO tmp_refine_global (src,res,rid,tr) VALUES',
         ',\n'.join('(%d,%d,%d,%d)' % (s['src'], s['res'], s['rid'], s['tr']) for s in steps) + ';',
         '-- a step whose material is not in our item_proto stays as it is',
         'DROP TEMPORARY TABLE IF EXISTS tmp_refine_global_mat;',
         'CREATE TEMPORARY TABLE tmp_refine_global_mat (rid INT UNSIGNED NOT NULL, vnum INT UNSIGNED NOT NULL,'
         ' PRIMARY KEY (rid, vnum));',
         'INSERT IGNORE INTO tmp_refine_global_mat (rid,vnum) VALUES',
         ',\n'.join('(%d,%d)' % (r[0], v) for r in rows for v in r[1:11:2] if v) + ';',
         'DELETE s FROM tmp_refine_global s JOIN tmp_refine_global_mat m ON m.rid = s.rid'
         ' LEFT JOIN world.item_proto p ON p.vnum = m.vnum WHERE p.vnum IS NULL;',
         'UPDATE world.item_proto i JOIN tmp_refine_global s ON s.src = i.vnum JOIN world.item_proto r ON r.vnum = s.res',
         ' SET i.refined_vnum = s.res, i.refine_set = s.rid',
         ' WHERE (i.refined_vnum = s.res OR (s.tr = 1 AND i.refined_vnum = 0)) AND (i.refined_vnum <> s.res OR i.refine_set <> s.rid);',
         'DROP TEMPORARY TABLE tmp_refine_global_mat;',
         'DROP TEMPORARY TABLE tmp_refine_global;']
    with open(SQL_OUT, 'w', encoding='utf-8', newline='\n') as f:
        f.write('\n'.join(L) + '\n')
    print('steps %d (without a chance %d), recipes %d (%d-%d), +9 -> next item steps %d'
          % (len(steps), nochance, len(recipes), ID0, ID0 + len(recipes) - 1, sum(s['tr'] for s in steps)))


if __name__ == '__main__':
    main()
