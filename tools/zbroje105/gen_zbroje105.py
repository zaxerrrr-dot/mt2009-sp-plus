#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""gen_zbroje105.py [--import <package dir>]

MT2009_PLUS_ARMOR105_V1 (the owner, 17 / 22 October 2026: "zbroje 105-115 i Cyjanit jak na wiki"): the level-105..115
body armours of the pl-wiki "Wytwarzanie Zbroi" (16, four a class: Polarny Pancerz / Ubranie Zasadzki / ... - 20760-
20799, 20810-20849, 20860-20899, 20910-20949, +0..+9), the four cyanite armours of level 110-120 (12050-12089) and the
nine materials they need (Plan Zbroi 30601, Zlote / Miedziane / Brazowe Plyty 30605 / 30607 / 30609, Czarny / Bialy
Barwnik 30614 / 30615, Barwnik zloty metalik 30619, Padparadza 30625, Boski Kwiat 30628) - 209 items with the rows of
GF 25.2.17 (the owner's package p-gf-po-3.0.1, sql/1_zbroje_105.sql; the Lycan's left out), and their refining:
refine_proto 30091-30109 (+0..+8 by the pl-wiki; refine_global.sql puts the owner's sheet's recipes on top where it
has the step). The level-105 armours +9 -> the cyanite ones are Seon-Pyeong's: tools/refineglobal ELITE 39903 (the
package's refine_proto 717 had the same recipe; the rows' 717 becomes that id here).

How they are made and where the materials come from - the rest of MT2009_PLUS_ARMOR105_V1:
  game/cube.zbroje105.txt (Kawuco's 80 recipes: the level-90 armour +5..+9 -> a level-105 one), quest angmur (Admiral
  Angmur: the level-90 armour +9 -> a level-105 one, the bonuses kept), the drops - tools/yohara_zaklety (En-Tai,
  Bagjanamu, Jotun Thrym, Erebu's chests), tools/yohara_chestdrops (Razador / Nemere chests), tools/ymoby_arkusz (the
  owner's monster sheet), tools/worldboss (Skrzynka Tajemnic).

Writes (GENERATED - edit tools/zbroje105/zbroje105.json or this file, run it again):
  linux-port/docker/mariadb/playerbot/zbroje105.sql   apply.sh, every start, before refine_global.sql: INSERT IGNORE
                                                      (a row the operator changed stays)
  client-patches/client-2.0.30/root/icon/item/<vnum>.tga   the 29 GF icons our packs lack (GF 26.1.11 client;
                                                      build57.py puts every file there into the root pack)
The client's records, item_list and itemdesc lines come from the same json (client-patches/client-2.0.30/tools/
gfint/build_gfint_pack.py).

--import <dir>: (re)reads the owner's package (sql/1_zbroje_105.sql, klient/zbroje-105/...) into zbroje105.json; the
two English descriptions (30625, 30628) get the Polish ones of DESC_PL. A plain run needs only the json.

Example: python3 tools/zbroje105/gen_zbroje105.py
"""
import json
import os
import re
import shutil
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(os.path.dirname(HERE))
DATA = os.path.join(HERE, 'zbroje105.json')
SQL_OUT = os.path.join(REPO, 'linux-port', 'docker', 'mariadb', 'playerbot', 'zbroje105.sql')
ICON_DIR = os.path.join(REPO, 'client-patches', 'client-2.0.30', 'root', 'icon', 'item')
GF_ICONS = '/opt/metin2/cache/gf/Gameforge_26.1.11/_client/icon/item'
sys.path.insert(0, os.path.join(REPO, 'tools', 'refineglobal'))
import gen_refineglobal as RG  # noqa: E402  (ELITE: Seon-Pyeong's fixed recipe ids)

M = 'MT2009_PLUS_ARMOR105_V1'
COLS = ('vnum', 'name', 'locale_name', 'type', 'subtype', 'stack', 'weight', 'size', 'antiflag', 'flag', 'wearflag',
        'immuneflag', 'gold', 'shop_buy_price', 'refined_vnum', 'refine_set', 'magic_pct', 'specular', 'socket_pct',
        'addon_type', 'limittype0', 'limitvalue0', 'limittype1', 'limitvalue1', 'applytype0', 'applyvalue0',
        'applytype1', 'applyvalue1', 'applytype2', 'applyvalue2', 'value0', 'value1', 'value2', 'value3', 'value4',
        'value5', 'socket0', 'socket1', 'socket2', 'socket3', 'socket4', 'socket5')
STR_COLS = ('name', 'locale_name', 'immuneflag')
REFINE_COLS = ('id', 'vnum0', 'count0', 'vnum1', 'count1', 'vnum2', 'count2', 'vnum3', 'count3', 'vnum4', 'count4',
               'cost', 'src_vnum', 'result_vnum', 'prob')
GF_CYANITE_REFINE = 717         # the package's (GF's) id of the +9 -> cyanite recipe: ELITE 39903 here
# the package's two English descriptions in Polish (the owner, 22 October 2026)
DESC_PL = {
    30625: u'Kryształy padparadży to rzadkie i niezwykle wykwintne czerwone szafiry. Służą do ulepszania ekwipunku.',
    30628: u'Święty kwiat z ogrodu Smoczego Boga. Służy do ulepszania ekwipunku.',
}


def cyanite_id():
    ids = [rid for rid, what, srcs, extra in RG.ELITE if any(s == 20769 for s, r in extra)]
    assert len(ids) == 1, ids
    return ids[0]


def import_package(pkg):
    t = open(os.path.join(pkg, 'sql', '1_zbroje_105.sql'), 'rb').read().decode('latin-1')
    rows = [re.findall(r"'((?:[^'\\]|\\.)*)'", r) for r in re.findall(r"^\((.*)\)[,;]$", t, re.M)]
    items, refine = [], []
    for f in rows:
        if len(f) == len(COLS):
            d = dict(zip(COLS, f))
            for c in COLS:
                if c == 'locale_name':
                    d[c] = d[c].encode('latin-1').decode('cp1250')
                elif c not in STR_COLS:
                    d[c] = int(d[c])
            items.append(d)          # 'name': GF's Korean bytes, kept as latin-1 text (written back as they were)
        else:
            assert len(f) == len(REFINE_COLS), f
            refine.append([int(x) for x in f])
    vnums = set(i['vnum'] for i in items)
    il = {}
    for line in open(os.path.join(pkg, 'klient', 'zbroje-105', 'gamedata', 'gamedata', 'item_list.txt'),
                     'rb').read().decode('cp1250').splitlines():
        p = line.split('\t')
        if p[0].strip().isdigit() and int(p[0]) in vnums:
            il[p[0].strip()] = line.strip()
    desc = {}
    for line in open(os.path.join(pkg, 'klient', 'zbroje-105', 'dbdata', 'locale', 'pl', 'itemdesc.txt'),
                     'rb').read().decode('cp1250').splitlines():
        p = line.split('\t')
        if p[0].strip().isdigit() and int(p[0]) in vnums:
            v = int(p[0])
            desc[str(v)] = '%d\t%s\t%s' % (v, p[1], DESC_PL.get(v, p[2] if len(p) > 2 else ''))
    assert len(il) == len(items) and set(desc) == set(str(v) for v in DESC_PL), (len(il), sorted(desc))
    out = dict(source='the owner\'s package p-gf-po-3.0.1 (21 October 2026): GF 25.2.17 rows, sql/1_zbroje_105.sql',
               items=sorted(items, key=lambda i: i['vnum']), refine=sorted(refine), item_list=il, itemdesc=desc)
    with open(DATA, 'w', encoding='utf-8', newline='\n') as f:
        json.dump(out, f, ensure_ascii=True, indent=0, sort_keys=True)
        f.write('\n')


def load():
    """the json with the +9 -> cyanite rows on Seon-Pyeong's fixed recipe"""
    d = json.load(open(DATA, encoding='utf-8'))
    cid = cyanite_id()
    for i in d['items']:
        if i['refine_set'] == GF_CYANITE_REFINE:
            i['refine_set'] = cid
    d['refine'] = [r for r in d['refine'] if r[0] != GF_CYANITE_REFINE]
    return d


def sql_val(c, v):
    if c in STR_COLS:
        b = v.encode('latin-1') if c == 'name' else v.encode('cp1250')
        return b"'" + b.replace(b'\\', b'\\\\').replace(b"'", b"\\'") + b"'"
    return str(v).encode()


def main():
    if '--import' in sys.argv:
        import_package(sys.argv[sys.argv.index('--import') + 1])
    d = load()
    items, refine = d['items'], d['refine']
    head = ['-- %s: the level-105..115 body armours, the cyanite ones (110-120) and their nine materials - %d items'
            % (M, len(items)),
            '-- of GF 25.2.17 (the owner\'s package of 21 October 2026), their refine_proto %d-%d. GENERATED by'
            % (refine[0][0], refine[-1][0]),
            '-- tools/zbroje105/gen_zbroje105.py from tools/zbroje105/zbroje105.json - do not edit, rerun it. apply.sh runs it',
            '-- every start before refine_global.sql (which puts the owner\'s sheet\'s recipes on their steps and Seon-Pyeong\'s',
            '-- %d on the +9 -> cyanite step). INSERT IGNORE: a row the operator changed stays. SET NAMES binary: the' % cyanite_id(),
            '-- names are GF\'s bytes (cp1250 columns).',
            'SET NAMES binary;']
    L = [x.encode('ascii') for x in head]
    L.append(('INSERT IGNORE INTO world.item_proto (%s) VALUES' % ', '.join('`%s`' % c for c in COLS)).encode())
    L.append(b',\n'.join(b'(' + b', '.join(sql_val(c, i[c]) for c in COLS) + b')' for i in items) + b';')
    L.append(('INSERT IGNORE INTO world.refine_proto (%s) VALUES' % ', '.join('`%s`' % c for c in REFINE_COLS)).encode())
    L.append(b',\n'.join(('(%s)' % ', '.join(str(x) for x in r)).encode() for r in refine) + b';')
    with open(SQL_OUT, 'wb') as f:
        f.write(b'\n'.join(L) + b'\n')
    copied = 0
    icons = sorted(set(l.split('\t')[2] for l in d['item_list'].values()))
    for icon in icons:
        dst = os.path.join(ICON_DIR, os.path.basename(icon))
        if not os.path.exists(dst):
            src = os.path.join(GF_ICONS, os.path.basename(icon))
            assert os.path.exists(src), ('no GF icon', icon)
            shutil.copyfile(src, dst)
            copied += 1
    print('items %d, refine_proto %d (%d-%d), +9 -> cyanite on %d: %d, icons %d (copied %d)'
          % (len(items), len(refine), refine[0][0], refine[-1][0], cyanite_id(),
             sum(1 for i in items if i['refine_set'] == cyanite_id()), len(icons), copied))


if __name__ == '__main__':
    main()
