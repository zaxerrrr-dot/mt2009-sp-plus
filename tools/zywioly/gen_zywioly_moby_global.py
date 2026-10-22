#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""MT2009_PLUS_GLOBAL_BONUS_V1 - the monsters' elements of M2_BONUS_MODE=global (the owner, 14 October 2026:
"tryb global = zywioly na WSZYSTKICH potworach, jak w oryginalnej grze"; tryb mt2009 = zywioly jak dotad).

mt2009 mode is gen_zywioly_moby.py's set (zywioly_moby.sql) plus the Yohara batches' *_zywioly.sql. global mode
adds, on top of it, every monster's element of the original data:

  * the bulk source is Owsap's official mob_proto (the AttElec/AttFire/AttIce/AttWind/AttEarth/AttDark columns,
    = the pl-wiki "Zywiol" pages; it agrees with every vnum of Tieru's 2.2.31 list - lightning: Setaou, Dowodca
    Yonghan, Niszczyciel, Ogry, Cyklopi..., wind: Fanatycy, Zabi Zolnierze, Krolowa Pajakow, Olbrzymi Zolw...);
    a monster with two elements (six in the data) keeps both bits;
  * the official element WINS over the mt2009 rules (wiki bosses, the map and dungeon rules, the boss overrides) -
    e.g. the Grota's ice monsters 1131-1137 are ice, not the map's lightning;
  * a monster the official data gives no element keeps its mt2009 one (the owner's boss overrides stay);
  * our copies of official monsters (apply.sh's "AS SELECT * FROM world.mob_proto WHERE vnum = X ... SET vnum = Y",
    the Grota / Cyclops / Spider copies 9601-9715, 4550-4559) take the source's official element when the copy
    has none in mt2009 and is a true copy (the same name in --mobs; the Arezzo reskins - mummies, scorpions,
    monkeys made from the Cyclopes - are other monsters and get nothing; a copy the owner gave an element keeps it);
  * NOT touched: the Yohara batches (every vnum of a *_zywioly.sql file and gen_zywioly_moby's YOHARA_ELEMENTS*:
    their elements are the wiki's already - the owner: keep them), the Zodiac bosses 2750-2862 and the temple
    (the floor's element at run time), Ruiny Atlantydy (rule f, the owner's whole-dungeon lightning), NPCs and
    Metin stones of the base game (the owner's rule: no Metin has an element).

Output:
  linux-port/docker/mariadb/playerbot/zywioly_moby_global.sql   apply.sh, every start in global mode, AFTER
                                                                zywioly_moby.sql and every *_zywioly.sql
  tools/zywioly/zywioly_moby_global.json                        {vnum: bits} - the vnums global mode changes
  client-patches/client-2.0.30/root/zywioly_global.py           the same dict for uitarget.py's element icon
                                                                (the client's mob_proto carries the mt2009 bits;
                                                                the server's "BonusMode 1" switches to this)
Usage:
  python3 tools/zywioly/gen_zywioly_moby_global.py [--owsap .../mob_proto.txt] [--mobs mobs.tsv] [--report FILE]
mobs.tsv: as gen_zywioly_moby.py's (the report's names and the copies' names - needed for the copies).
"""
import argparse
import csv
import glob
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(os.path.dirname(HERE))
sys.path.insert(0, HERE)
import gen_zywioly_moby as base  # noqa: E402

PB = os.path.join(REPO, 'linux-port', 'docker', 'mariadb', 'playerbot')
APPLY_SH = os.path.join(PB, 'apply.sh')
MT2009_JSON = os.path.join(HERE, 'zywioly_moby.json')
SQL_OUT = os.path.join(PB, 'zywioly_moby_global.sql')
JSON_OUT = os.path.join(HERE, 'zywioly_moby_global.json')
PY_OUT = os.path.join(REPO, 'client-patches', 'client-2.0.30', 'root', 'zywioly_global.py')
OWSAP = '/opt/metin2/cache/owsap/Server/Server/db/mob_proto.txt'

COLUMNS = (('AttElec', base.ELEC), ('AttFire', base.FIRE), ('AttIce', base.ICE), ('AttWind', base.WIND),
           ('AttEarth', base.EARTH), ('AttDark', base.DARK))
ZODIAC = range(2750, 2863)


def official(path):
    """{vnum: (type, bits)} of Owsap's mob_proto.txt"""
    out = {}
    with open(path, encoding='latin-1', newline='') as f:
        rows = csv.reader(f, delimiter='\t', quoting=csv.QUOTE_NONE)
        head = next(rows)
        ix = dict((k, i) for i, k in enumerate(head))
        for r in rows:
            if len(r) < len(head) or not r[ix['Vnum']].strip().isdigit():
                continue
            bits = 0
            for col, bit in COLUMNS:
                if r[ix[col]].strip() not in ('', '0'):
                    bits |= bit
            out[int(r[ix['Vnum']])] = (r[ix['Type']].strip(), bits)
    return out


def yohara_vnums():
    out = set()
    for path in glob.glob(os.path.join(PB, '*_zywioly.sql')):
        for m in re.finditer(r'vnum IN \(([\d,\s]+)\)', open(path, encoding='utf-8').read()):
            out.update(int(x) for x in m.group(1).replace(' ', '').split(',') if x)
    # MT2009_PLUS_237_GLOBAL_MODE_V1: the 2.x line has no Yohara element rules (gen_zywioly_moby.py without h / h2)
    for _, vs in tuple(getattr(base, 'YOHARA_ELEMENTS', ())) + tuple(getattr(base, 'YOHARA_ELEMENTS2', ())):
        out.update(vs)
    return out


def atlantis_vnums():
    return set(m['vnum'] for m in json.load(open(base.ATLANTIS, encoding='utf-8'))['mobs'])


def copies():
    """[(source, copy)] of apply.sh's mob_proto copies (the awk of its migrate_copies)"""
    out, src = [], None
    for line in open(APPLY_SH, encoding='utf-8', errors='replace'):
        m = re.search(r'AS SELECT \* FROM world\.mob_proto WHERE vnum = (\d+)', line)
        if m:
            src = int(m.group(1))
            continue
        m = re.search(r'SET vnum = (\d+)', line)
        if src is not None and m:
            out.append((src, int(m.group(1))))
            src = None
    return out


def ids(vs):
    return ','.join(str(v) for v in sorted(vs))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--owsap', default=OWSAP)
    ap.add_argument('--mobs', help='world.mob_proto TSV (names in the report)')
    ap.add_argument('--report')
    a = ap.parse_args()

    off = official(a.owsap)
    mt = dict((int(k), v) for k, v in json.load(open(MT2009_JSON)).items())
    mobs = base.load_mobs(a.mobs) if a.mobs else {}
    keep = yohara_vnums() | atlantis_vnums() | set(ZODIAC)

    result, why = {}, {}
    for v, (typ, bits) in sorted(off.items()):
        if not bits or typ != 'MONSTER' or v in keep:
            continue
        if mt.get(v) != bits:
            result[v], why[v] = bits, 'official' + (' (mt2009 %s)' % base.NAMES.get(mt[v], mt[v]) if v in mt else '')
    for src, cp in copies():
        if cp in keep or cp in mt or cp in result:
            continue
        # a true copy only (the same name): the Arezzo reskins of the Cyclopes (mummies, scorpions, monkeys) are
        # other monsters - no element from the source
        if not mobs or src not in mobs or cp not in mobs or mobs[src]['name'] != mobs[cp]['name']:
            continue
        typ, bits = off.get(src, ('', 0))
        if bits and typ == 'MONSTER':
            result[cp], why[cp] = bits, 'copy of %d (official)' % src

    def name(bits):
        return '+'.join(base.NAMES[b] for b in (base.ELEC, base.FIRE, base.ICE, base.WIND, base.EARTH, base.DARK)
                        if bits & b)

    out = ['Monster elements, global mode (MT2009_PLUS_GLOBAL_BONUS_V1): %d vnums over the mt2009 set' % len(result)]
    for bit in (base.ELEC, base.FIRE, base.ICE, base.WIND, base.EARTH, base.DARK):
        out.append('  %-10s %4d' % (base.NAMES[bit], sum(1 for b in result.values() if b & bit)))
    out.append('  changed from an mt2009 element: %d' % sum(1 for v in result if v in mt))
    out.append('  copies: %d' % sum(1 for w in why.values() if w.startswith('copy')))
    out.append('Mapping:')
    for v in sorted(result):
        out.append('  %d\t%s\t%s\t%s' % (v, name(result[v]), why[v], mobs.get(v, {}).get('name', '')))
    report = '\n'.join(out) + '\n'
    sys.stdout.write(report)
    if a.report:
        open(a.report, 'w', encoding='utf-8').write(report)

    sql = ['-- MT2009_PLUS_GLOBAL_BONUS_V1: the monsters\' elements of M2_BONUS_MODE=global (setRaceFlag bits 11-16).',
           '-- GENERATED by tools/zywioly/gen_zywioly_moby_global.py - do not edit. apply.sh runs it in global mode only,',
           '-- after zywioly_moby.sql and every *_zywioly.sql (mt2009 mode needs nothing: zywioly_moby.sql clears the bits',
           '-- of every mob it does not list at every start, so switching back restores the mt2009 elements).',
           '-- Official data (Owsap mob_proto Att* = the pl-wiki) over the mt2009 set; Yohara, Zodiac, Atlantyda untouched.']
    sql += ['-- ' + line.strip() for line in out[1:9]]
    groups = {}
    for v, bits in result.items():
        groups.setdefault(bits, []).append(v)
    for bits in sorted(groups):
        sql.append('UPDATE world.mob_proto SET setRaceFlag = ((setRaceFlag + 0) & ~%d) | %d WHERE vnum IN (%s);'
                   % (base.MASK, bits, ids(groups[bits])))
    with open(SQL_OUT, 'w', encoding='utf-8', newline='\n') as f:
        f.write('\n'.join(sql) + '\n')
    with open(JSON_OUT, 'w', encoding='utf-8', newline='\n') as f:
        json.dump(dict((str(v), result[v]) for v in sorted(result)), f, indent=0)
        f.write('\n')
    # MT2009_PLUS_237_GLOBAL_MODE_V1: no coding line - the client's Python has no cp1250 codec ('unknown encoding:
    # cp1250' stopped the login screen, the Yohara line's 2c4847d3); the file is ASCII
    py = ['# MT2009_PLUS_GLOBAL_BONUS_V1: the monsters\' elements of the server\'s M2_BONUS_MODE=global that the client\'s',
          '# mob_proto (the mt2009 elements) does not carry - {vnum: race flag bits 11-16}. uitarget.py reads it while',
          '# the server said "BonusMode 1" (game.py). GENERATED by tools/zywioly/gen_zywioly_moby_global.py.',
          'ELEMENTS = {']
    line = '\t'
    for v in sorted(result):
        item = '%d: %d, ' % (v, result[v])
        if len(line) + len(item) > 110:
            py.append(line.rstrip())
            line = '\t'
        line += item
    if line.strip():
        py.append(line.rstrip())
    py.append('}')
    with open(PY_OUT, 'wb') as f:
        f.write(('\r\n'.join(py) + '\r\n').encode('ascii'))
    sys.stderr.write('written %s, %s, %s\n' % tuple(os.path.relpath(p, REPO) for p in (SQL_OUT, JSON_OUT, PY_OUT)))


if __name__ == '__main__':
    main()
