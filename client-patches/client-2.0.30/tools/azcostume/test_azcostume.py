# -*- coding: utf-8 -*-
# MT2009_PLUS_AREZZO_COSTUME_SETS_V1 - every Arezzo set item is in the server rows and in the
# patched client data, and both say the same.
#
#   python3 test_azcostume.py <repo> <patched client data dir>
#
# <patched client data dir> = the layout patch_azcostume_client.py takes, after it ran (a scratch
# copy of the gamedata / dbdata files).  Checks: arezzo_costumes.sql (type, subtype, size, anti
# flags, values, no applies), the in-game and web ItemShop lines, costume_sets.txt and the client's
# costume_sets.py; in the client: a gf_official_costumes.txt / costume_attr_items.txt row equal in
# every column, an item_list.txt line with an icon (and the model of a weapon / sash skin), an
# itemdesc.txt line, the msm groups of a body / hair for each class of its sex, the skins' scale
# rows, and the glow lines.
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))


def rows_by_vnum(path, enc='cp1250'):
    out = {}
    for l in open(path, encoding=enc, errors='replace').read().replace('\r\n', '\n').split('\n'):
        p = l.split('\t')
        if p and p[0].strip().isdigit():
            out.setdefault(int(p[0]), []).append(p)
    return out


def main():
    repo, data = sys.argv[1], sys.argv[2]
    d = json.load(open(os.path.join(HERE, 'azcostume_items.json'), encoding='utf-8'))
    items = d['items']
    errors = []

    def check(cond, msg):
        if not cond:
            errors.append(msg)

    sql = open(os.path.join(repo, 'linux-port/docker/mariadb/playerbot/arezzo_costumes.sql'), encoding='utf-8').read()
    srv = {}
    for m in re.finditer(r"^\((\d+), '([^']*)', '[^']*', (.*)\),?;?$", sql, re.M):
        srv[int(m.group(1))] = [m.group(2)] + [int(x) for x in m.group(3).replace("''", '0').split(', ')]
    apply_sh = open(os.path.join(repo, 'linux-port/docker/mariadb/playerbot/apply.sh'), encoding='utf-8').read()
    ishop = set(int(v) for v in re.findall(r"\(\d+, (\d+), 1, 100, 'DRAGON_COIN', 0\)", apply_sh))
    web = open(os.path.join(repo, 'linux-port/docker/mariadb/playerbot/arezzo_costumes_webshop.sql'), encoding='utf-8').read()
    gf = rows_by_vnum(os.path.join(data, 'gamedata/gf_official_costumes.txt'))
    attr = rows_by_vnum(os.path.join(data, 'gamedata/costume_attr_items.txt'))
    il = rows_by_vnum(os.path.join(data, 'gamedata/item_list.txt'))
    desc = rows_by_vnum(os.path.join(data, 'locale/pl/itemdesc.txt'))
    scale = rows_by_vnum(os.path.join(data, 'gamedata/item_scale.txt'))
    shine = rows_by_vnum(os.path.join(data, 'gamedata/shiningtable.txt'))
    msm = {}
    for race in ('warrior_m', 'assassin_m', 'sura_m', 'shaman_m', 'warrior_w', 'assassin_w', 'sura_w', 'shaman_w'):
        t = open(os.path.join(data, 'gamedata/%s.msm' % race), encoding='cp1250').read()
        msm[race] = (set(int(x) for x in re.findall(r'ShapeIndex\s+(\d+)', t)),
                     set(int(x) for x in re.findall(r'HairIndex\s+(\d+)', t)))
        for kind in ('ShapeData', 'HairData'):
            cnt = int(re.search(r'%sCount\s+(\d+)' % kind, t).group(1))
            check(len(re.findall(r'Group %s\d+' % kind, t)) == cnt, '%s.msm: %s count' % (race, kind))
    for it in items:
        v = it['vnum']
        s = srv.get(v)
        check(s is not None, '%d: no server row' % v)
        if s:
            # name, type, subtype, stack, weight, size, antiflag, flag, ... applies at 22..27, values at 28..33
            check(s[0] == it['name'] and s[1] == it['type'] and s[2] == it['sub'] and s[5] == it['size']
                  and s[6] == it['anti'], '%d: server row differs %s' % (v, s[:8]))
            check(s[22:28] == [0] * 6, "%d: server applies %s" % (v, s[22:28]))
            check(s[28:34] == it["values"], "%d: server values %s" % (v, s[28:34]))
        check(v in ishop, '%d: no in-game ItemShop line' % v)
        check(('SELECT %d, ' % (1000000 + v)) in web, '%d: no web shop offer' % v)
        table = attr if it['kind'] == 'SashSkin' else gf
        row = table.get(v, [[]])[0]
        check(len(row) == 24 and row[1] == it['name'] and int(row[2]) == it['sub'] and int(row[3]) == it['size']
              and int(row[4]) == it['anti'] and [int(x) for x in row[10:16]] == [0] * 6
              and [int(x) for x in row[16:22]] == it['values'], '%d: client table row %s' % (v, row))
        line = il.get(v, [[]])[0]
        check(len(line) >= 3 and line[2] == it['icon'], '%d: item_list %s' % (v, line))
        if it['model']:
            check(len(line) >= 4 and line[3] == it['model'], '%d: item_list model %s' % (v, line))
        check(v in desc and desc[v][0][1] == it['name'], '%d: itemdesc' % v)
        if it['kind'] in ('ShapeData', 'HairData'):
            sex = '_m' if it['name'].endswith('(m)') else '_w'
            for race, (shapes, hairs) in msm.items():
                if race.endswith(sex):
                    check(v in (shapes if it['kind'] == 'ShapeData' else hairs), '%d: no msm group in %s' % (v, race))
        if it['kind'] == 'SashSkin':
            check(len(scale.get(v, [])) == 8, '%d: %d scale rows' % (v, len(scale.get(v, []))))
            check(85200 <= v <= 85299 and v % 1000 < 500, '%d: sash skin range' % v)
        if it['shining']:
            check(v in shine, '%d: no glow line' % v)
    # the sets: server file and the client copy
    txt = open(os.path.join(repo, 'linux-port/docker/game/costume_sets.txt'), encoding='utf-8').read().replace('\r\n', '\n')
    py = open(os.path.join(repo, 'client-patches/client-2.0.30/root/costume_sets.py'), encoding='latin-1').read()
    for s in d['sets']:
        line = '%s\t%s\t%s' % (s['name'], ','.join(map(str, s['bodies'])), ','.join(map(str, s['hairs'])))
        check(line in txt.split('\n'), 'costume_sets.txt: %s' % s['name'])
        check('((%s,), (%s,)),\t# %s' % (','.join(map(str, s['bodies'])), ','.join(map(str, s['hairs'])), s['name']) in py,
              'costume_sets.py: %s' % s['name'])
        check(len(s['bodies']) == 2 and len(s['hairs']) == 2, '%s: set size' % s['name'])
    # no new vnum in the old sets
    new = set(it['vnum'] for it in items)
    for l in txt.split('\n'):
        if l and not l.startswith('#') and l.split('\t')[0] not in set(s['name'] for s in d['sets']):
            olds = set(int(x) for x in re.findall(r'\d+', '\t'.join(l.split('\t')[1:])))
            check(not (olds & new), 'old set %s uses a new vnum' % l.split('\t')[0])
    print('%d items, %d sets checked; %d error(s)' % (len(items), len(d['sets']), len(errors)))
    for e in errors[:40]:
        print('  ', e)
    sys.exit(1 if errors else 0)


if __name__ == '__main__':
    main()
