#!/usr/bin/env python3
# MT2009_PLUS_KOLA_V1: checks the wheels (kola.json, przedmioty.json, the seed in itemshop_schema.sql) against the
# owner's sheet (xlsx with the sheets Koła, Poziomy, Nagrody, Pola, Mechanika - plain zipfile, no openpyxl needed):
#   - the six wheels, tiers and spin costs
#   - every pool entry 1:1 in order (source id, count, weight) for each wheel/tier/pool
#   - the field layout: main (special) fields, key fields, field pictures
#   - the mechanics constants (930 s per higher tier, 4 keys, key fields 3/7/11/15)
#   - every source id has our vnum; with --db also that the vnum is in world.item_proto
# and lists the stand-ins (status zamiennik) - the sheet's items we still do not have.
# Wheels added later have their own sheet (EXTRA: one xlsx per wheel with the sheets Poziomy, Nagrody wg puli,
# Szanse na obrot, plus the simulator's config/<id>.json for the field pictures) - checked the same way, and the
# per-spin win chance of every prize recomputed from our pools against the sheet's "Wygrana / obrot".
#   python3 linux-port/docker/itemshop/kola-src/verify_sheet.py [sheet.xlsx] [--db mt2009plustest-db]
# Exit code 0 = everything as the sheet; the key-field chance (ours 40%, panel setting) is reported, not failed.
import json, os, re, subprocess, sys, zipfile
import xml.etree.ElementTree as ET

HERE = os.path.dirname(os.path.abspath(__file__))
CFG = os.path.join(HERE, '..', 'app', 'itemshop', 'kola', 'kola.json')
MAP = os.path.join(HERE, 'przedmioty.json')
SQL = os.path.join(HERE, '..', '..', 'mariadb', 'playerbot', 'itemshop_schema.sql')
DEFAULT_XLSX = '/opt/metin2/cache/yohara/kola-losu-arkusz-2026-11-05.xlsx'
# wheel id -> (its sheet, the simulator's config) - MT2009_PLUS_KOLA_V1 wheel 246 (the owner, 5 Nov 2026)
EXTRA = {
    '246': ('/opt/metin2/cache/yohara/kolo246/kolo246.xlsx',
            '/opt/metin2/cache/yohara/kolo246/symulator/wheel-kit/config/246.json'),
}
NS = {'m': 'http://schemas.openxmlformats.org/spreadsheetml/2006/main',
      'r': 'http://schemas.openxmlformats.org/officeDocument/2006/relationships'}


def read_xlsx(path):
    z = zipfile.ZipFile(path)
    shared = []
    if 'xl/sharedStrings.xml' in z.namelist():
        for si in ET.fromstring(z.read('xl/sharedStrings.xml')).findall('m:si', NS):
            shared.append(''.join(t.text or '' for t in si.iter('{%s}t' % NS['m'])))
    rels = {r.get('Id'): r.get('Target') for r in ET.fromstring(z.read('xl/_rels/workbook.xml.rels'))}
    sheets = {}
    for s in ET.fromstring(z.read('xl/workbook.xml')).find('m:sheets', NS):
        target = rels[s.get('{%s}id' % NS['r'])].lstrip('/')
        target = target if target.startswith('xl/') else 'xl/' + target
        rows = []
        for row in ET.fromstring(z.read(target)).iter('{%s}row' % NS['m']):
            vals = {}
            for c in row.findall('m:c', NS):
                v = c.find('m:v', NS)
                if c.get('t') == 's':
                    val = shared[int(v.text)]
                elif c.get('t') == 'inlineStr':
                    val = ''.join(t.text or '' for t in c.iter('{%s}t' % NS['m']))
                else:
                    val = v.text if v is not None else None
                if val is not None:
                    col = 0
                    for ch in re.match('[A-Z]+', c.get('r')).group():
                        col = col * 26 + ord(ch) - 64
                    vals[col - 1] = val
            if vals:
                rows.append([vals.get(i, '') for i in range(max(vals) + 1)])
        sheets[s.get('name')] = rows
    return sheets


def table(rows, first):
    # header row = the one starting with `first`; data rows follow it
    for i, r in enumerate(rows):
        if r and r[0] == first:
            head = r
            return [dict(zip(head, x + [''] * (len(head) - len(x)))) for x in rows[i + 1:] if x and x[0]]
    raise SystemExit('header %r not found' % first)


def num(x):
    f = float(x)
    return int(f) if f == int(f) else f


def tier_rows(rows):
    # the per-wheel sheets have notes under their tables
    return [r for r in table(rows, 'Poziom') if r['Poziom'].isdigit()]


def ints(text):
    return [int(x) for x in re.findall(r'\d+', text or '')]


def check_wheel_sheet(wid, xlsx, kit, cfg, errors):
    """One later wheel against its own sheet; returns {(tier, pool): [(src, count, weight)]}."""
    if not os.path.exists(xlsx) or not os.path.exists(kit):
        errors.append('wheel %s: sheet %s or simulator config %s is missing' % (wid, xlsx, kit))
        return {}
    sh = read_xlsx(xlsx)
    ours = cfg['wheels'].get(wid)
    if not ours:
        errors.append('wheel %s is not in kola.json' % wid)
        return {}
    title = sh['Poziomy'][0][0]
    name, _, sid = title.rpartition(' · ')
    if sid.strip() != wid or name.strip() != ours['name']:
        errors.append('wheel %s: sheet title %r, ours %s %r' % (wid, title, wid, ours['name']))
    if int(wid) not in cfg['rotation']['order']:
        errors.append('wheel %s is not in the rotation' % wid)
    tiers = tier_rows(sh['Poziomy'])
    max_tier = max(int(r['Poziom']) for r in tiers)
    for r in tiers:
        t = r['Poziom']
        if int(num(r['Koszt SM'])) != int(ours['costs'].get(t, -1)):
            errors.append('cost %s/%s: sheet %s, ours %s' % (wid, t, r['Koszt SM'], ours['costs'].get(t)))
        if int(num(r['Pól razem'])) != 16:
            errors.append('fields %s/%s: sheet %s, ours 16' % (wid, t, r['Pól razem']))
        if ints(r['Pola główne']) != cfg['special_fields'].get(t):
            errors.append('main fields %s/%s: sheet %s, ours %s' % (wid, t, r['Pola główne'], cfg['special_fields'].get(t)))
        keys = ints(r['Pola kluczy'])
        if int(t) < max_tier:
            if keys != cfg['key_fields'] or int(num(r['Trafień do awansu'])) != int(cfg['keys_needed']):
                errors.append('keys %s/%s: sheet %s / %s, ours %s / %s' % (wid, t, keys, r['Trafień do awansu'],
                                                                           cfg['key_fields'], cfg['keys_needed']))
        elif keys:
            errors.append('keys %s/%s: the top tier has key fields in the sheet' % (wid, t))
        if r['Limit (s)'] not in ('', '0') and int(num(r['Limit (s)'])) != int(cfg['tier_seconds']):
            errors.append('tier seconds %s/%s: sheet %s, ours %s' % (wid, t, r['Limit (s)'], cfg['tier_seconds']))
    if sorted(ours['costs'], key=int) != [r['Poziom'] for r in sorted(tiers, key=lambda r: int(r['Poziom']))]:
        errors.append('tiers %s: sheet %s, ours %s' % (wid, [r['Poziom'] for r in tiers], sorted(ours['costs'])))

    # Nagrody wg puli: every pool 1:1 in order (the sheet's chance in the pool x 100 = the source weight)
    pools = {}
    for r in tier_rows(sh['Nagrody wg puli']):
        pool = {'Główna': 'special', 'Zwykła': 'standard'}[r['Pula']]
        pools.setdefault((r['Poziom'], pool), []).append(
            (r['ID Item Shop'], int(num(r['Ilość'])), num(round(float(r['Szansa w puli']) * 100, 6))))
    for (t, pool), entries in sorted(pools.items()):
        mine = [(str(a), int(b), num(c)) for a, b, c in ours['prizes'].get(t, {}).get(pool, [])]
        if mine != entries:
            errors.append('pool %s/%s/%s differs: sheet %d entries, ours %d' % (wid, t, pool, len(entries), len(mine)))
    for t, p in ours['prizes'].items():
        for pool in ('special', 'standard'):
            if p[pool] and (t, pool) not in pools:
                errors.append('pool %s/%s/%s is not in the sheet' % (wid, t, pool))

    # Szanse na obrot: the win chance per spin from our pools (field share x weight share), per prize variant
    won = {}
    for t, p in ours['prizes'].items():
        n_special = len(cfg['special_fields'][t])
        for pool, share in (('special', n_special / 16.0), ('standard', (16 - n_special) / 16.0)):
            total = sum(float(e[2]) for e in p[pool])
            for src, count, weight in p[pool]:
                k = (t, str(src), int(count))
                won[k] = won.get(k, 0.0) + share * float(weight) / total
    sheet_won = {}
    for r in tier_rows(sh['Szanse na obrót']):
        k = (r['Poziom'], r['ID Item Shop'], int(num(r['Ilość'])))
        sheet_won[k] = sheet_won.get(k, 0.0) + float(r['Wygrana / obrót'])
    for k in sorted(set(won) | set(sheet_won)):
        if abs(won.get(k, 0.0) - sheet_won.get(k, 0.0)) > 1e-9:
            errors.append('win chance %s/%s source %s x%d: sheet %.6f, ours %.6f' % (
                wid, k[0], k[1], k[2], sheet_won.get(k, 0.0), won.get(k, 0.0)))

    # field pictures and the background: the simulator's config (the sheet has none)
    sim = json.load(open(kit, encoding='utf-8'))
    for tier in sim['tiers']:
        t = str(tier['level'])
        want = ['i_' + x.rsplit('.', 1)[0] + '.png' for x in tier['previewIcons']]
        if ours['fields'].get(t) != want:
            errors.append('field pictures %s/%s differ from the simulator' % (wid, t))
        if tier['specialPositions'] != cfg['special_fields'].get(t):
            errors.append('main fields %s/%s: simulator %s, ours %s' % (wid, t, tier['specialPositions'], cfg['special_fields'].get(t)))
    img = os.path.join(os.path.dirname(CFG), 'img')
    for t, names in ours['fields'].items():
        for n in names + [ours['bg']]:
            if not os.path.exists(os.path.join(img, n)):
                errors.append('wheel %s: picture img/%s is missing' % (wid, n))
    for p in ours['prizes'].values():
        for pool in p.values():
            for src, _, _ in pool:
                im = (cfg['src_items'].get(str(src)) or {}).get('img')
                if not im or not os.path.exists(os.path.join(img, im)):
                    errors.append('wheel %s: source item %s has no picture' % (wid, src))
    print('wheel %s %s: %d tiers, costs %s, %d prize entries (sheet %s)' % (
        wid, ours['name'], len(tiers), '/'.join(str(ours['costs'][t]) for t in sorted(ours['costs'], key=int)),
        sum(len(v) for v in pools.values()), os.path.basename(xlsx)))
    return pools


def main():
    args = [a for a in sys.argv[1:]]
    db = None
    if '--db' in args:
        i = args.index('--db')
        db = args[i + 1]
        del args[i:i + 2]
    xlsx = args[0] if args else DEFAULT_XLSX
    sh = read_xlsx(xlsx)
    cfg = json.load(open(CFG, encoding='utf-8'))
    mapping = json.load(open(MAP, encoding='utf-8'))
    errors = []

    # Koła / Poziomy: wheels, tiers, costs, keys, tier seconds
    lv = table(sh['Poziomy'], 'Koło')
    sheet_wheels = {}
    for r in lv:
        w = sheet_wheels.setdefault(r['ID koła'], {'name': r['Koło'], 'costs': {}})
        w['costs'][r['Poziom']] = num(r['Koszt obrotu'])
        if r['Pola dające klucz'] not in ('0', '') and num(r['Klucze do awansu']) != int(cfg['keys_needed']):
            errors.append('keys to advance %s/%s: sheet %s, ours %s' % (r['ID koła'], r['Poziom'], r['Klucze do awansu'], cfg['keys_needed']))
        if num(r['Limit poziomu (sekundy)']) not in (0, int(cfg['tier_seconds'])):
            errors.append('tier seconds %s/%s: sheet %s, ours %s' % (r['ID koła'], r['Poziom'], r['Limit poziomu (sekundy)'], cfg['tier_seconds']))
        keys = [int(x) for x in r['Pozycje kluczy (1–16)'].split(',')]
        if keys != cfg['key_fields']:
            errors.append('key fields %s/%s: sheet %s, ours %s' % (r['ID koła'], r['Poziom'], keys, cfg['key_fields']))
    if set(sheet_wheels) | set(EXTRA) != set(cfg['wheels']):
        errors.append('wheels: sheets %s, ours %s' % (sorted(set(sheet_wheels) | set(EXTRA)), sorted(cfg['wheels'])))
    for wid, w in sheet_wheels.items():
        ours = cfg['wheels'].get(wid)
        if not ours:
            continue
        oc = {k: int(v) for k, v in ours['costs'].items()}
        if oc != w['costs']:
            errors.append('costs %s: sheet %s, ours %s' % (wid, w['costs'], oc))
        if ours['name'] != w['name']:
            errors.append('name %s: sheet %s, ours %s' % (wid, w['name'], ours['name']))

    # Nagrody: every pool 1:1 in order
    pools = {}
    for r in table(sh['Nagrody'], 'Koło'):
        pools.setdefault((r['ID koła'], r['Poziom'], r['Kod puli']), []).append(
            (r['ID Item Shopu w źródle'], int(num(r['Ilość'])), num(r['Waga źródłowa'])))
    n_entries = sum(len(v) for v in pools.values())
    for (wid, t, pool), entries in sorted(pools.items()):
        ours = [(str(a), int(b), num(c)) for a, b, c in cfg['wheels'].get(wid, {}).get('prizes', {}).get(t, {}).get(pool, [])]
        if ours != entries:
            errors.append('pool %s/%s/%s differs: sheet %d entries, ours %d' % (wid, t, pool, len(entries), len(ours)))
    for wid, w in cfg['wheels'].items():
        if wid in EXTRA:
            continue
        for t, p in w['prizes'].items():
            for pool in ('special', 'standard'):
                if p[pool] and (wid, t, pool) not in pools:
                    errors.append('pool %s/%s/%s is not in the sheet' % (wid, t, pool))

    # Pola: main fields, key fields, pictures
    fields = {}
    for r in table(sh['Pola'], 'Koło'):
        f = fields.setdefault((r['ID koła'], r['Poziom']), {})
        f[int(r['Pozycja pola (1–16)'])] = (r['Pula nagrody'], r['Ikona klucza'] == 'Tak',
                                            r['URL tekstury pola'].rsplit('/', 1)[-1].split('.')[0])
    for (wid, t), f in sorted(fields.items()):
        special = [p for p in sorted(f) if f[p][0] == 'special']
        if special != cfg['special_fields'].get(t):
            errors.append('main fields %s/%s: sheet %s, ours %s' % (wid, t, special, cfg['special_fields'].get(t)))
        pics = cfg['wheels'].get(wid, {}).get('fields', {}).get(t, [])
        for p in sorted(f):
            if len(pics) < p or f[p][2] not in pics[p - 1]:
                errors.append('field picture %s/%s/%d differs' % (wid, t, p))

    # the wheels with their own sheet
    for wid, (xlsx_w, kit) in sorted(EXTRA.items()):
        for (t, pool), entries in check_wheel_sheet(wid, xlsx_w, kit, cfg, errors).items():
            pools[(wid, t, pool)] = entries
    n_entries = sum(len(v) for v in pools.values())

    # przedmioty.json: our vnum for every source id
    srcs = sorted({e[0] for v in pools.values() for e in v})
    for s in srcs:
        m = mapping.get(s)
        if not m or not m.get('vnum'):
            errors.append('source %s has no vnum in przedmioty.json' % s)
    # MT2009_PLUS_RUNY_WYKUWANIA_V1 (5 November 2026): the Runy Wykuwania are real items now (tools/runy/gen_runy.py,
    # 79605-79659, five grades a kind) - a sheet's "5* Runa Wykuwania ..." is a 5* rune, never a stand-in again
    RUNE_5 = {u'Pasów': 79609, u'Broni': 79614, u'Zbroi': 79619, u'Akcesoriów': 79629, u'Rękawic': 79654}
    runes = 0
    for s in srcs:
        sname = (cfg['src_items'].get(s) or {}).get('name') or ''
        if not sname.startswith(u'5* Runa Wykuwania '):
            continue
        runes += 1
        m = mapping.get(s) or {}
        want = RUNE_5.get(sname[len(u'5* Runa Wykuwania '):])
        if want is None:
            errors.append('source %s %s: a forging rune kind not in RUNE_5' % (s, sname))
        elif m.get('vnum') != want or m.get('status') != 'ok':
            errors.append('source %s %s: must be the 5* rune %d with status ok (now %s %s)'
                          % (s, sname, want, m.get('vnum'), m.get('status')))
    if runes != len(RUNE_5):
        errors.append('the sheet has %d "5* Runa Wykuwania" sources, expected %d' % (runes, len(RUNE_5)))
    if db:
        vn = sorted({int(mapping[s]['vnum']) for s in srcs if mapping.get(s, {}).get('vnum')})
        sql = 'SELECT vnum FROM world.item_proto WHERE vnum IN (%s);' % ','.join(map(str, vn))
        out = subprocess.run(['docker', 'exec', '-i', db, 'sh', '-c',
                              'mariadb -uroot -p"$MARIADB_ROOT_PASSWORD" -N'], input=sql, capture_output=True, text=True)
        have = {int(x) for x in out.stdout.split()}
        for v in vn:
            if v not in have:
                errors.append('vnum %d is not in world.item_proto' % v)

    # the seed in itemshop_schema.sql has every entry
    text = open(SQL, encoding='utf-8').read()
    seed = text[text.index('-- MT2009_PLUS_KOLA_V1 SEED BEGIN'):text.index('-- MT2009_PLUS_KOLA_V1 SEED END')]
    rows = len(re.findall(r"^  \(\d+, \d+, [01], \d+, '", seed, re.M))
    if rows != n_entries:
        errors.append('seed has %d pool rows, the sheet %d - run gen_kola_sql.py' % (rows, n_entries))

    print('sheets: %d + %d wheels, %d prize entries, %d source items' % (len(sheet_wheels), len(EXTRA), n_entries, len(srcs)))
    for line in [x for x in table(sh['Mechanika'], 'Koło / zakres') if x['Parametr / reguła'] == 'Klucze i awans']:
        print('key-field chance: sheet 4/16 = 25%, ours the panel setting key_chance (default 40, MT2009_PLUS_KOLA_KEYS_V1)')
    stand = {}
    for s in srcs:
        m = mapping.get(s) or {}
        if m.get('status') == 'zamiennik':
            stand.setdefault(m.get('src_name'), set()).add('%s %s x%s' % (m['vnum'], m['name'], m.get('count_mul') or 1))
    print('stand-ins (sheet items we do not have): %d' % len(stand))
    for k in sorted(stand):
        print('  %s -> %s' % (k, '; '.join(sorted(stand[k]))))
    for e in errors:
        print('ERROR ' + e)
    print('OK' if not errors else '%d error(s)' % len(errors))
    return 1 if errors else 0


if __name__ == '__main__':
    sys.exit(main())
