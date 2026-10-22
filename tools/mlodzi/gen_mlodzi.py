#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""gen_mlodzi.py [--gf DIR]

MT2009_PLUS_MLODZI_BOHATEROWIE_V1: Bronie dla Mlodych Bohaterow (the owner, 22 October 2026; the pl-wiki page
"Bronie dla Mlodych Bohaterow"): the 48 weapons of the four classes we have (the Lycan's claws x6 are left out) with
the OFFICIAL vnums and numbers:

  21900 + 10 * (tier - 1) + kind      tier 1..8 = level 1, 10, 20 ... 70
                                      kind 0 miecz (Wojownik, Ninja, Sura), 1 sztylet (Ninja), 2 luk (Ninja),
                                      3 bron dwureczna (Wojownik), 4 dzwon (Szaman), 5 wachlarz (Szaman)

Sources (all in this folder, copied once - the generator never reads a database):
  official_item_proto.tsv     the official item_proto rows 21900-21976 (cache/owsap5 player.item_proto, the MyISAM
                              table of the official data, dumped 22 October 2026): type/subtype/size, the class
                              antiflags, LIMIT_LEVEL, LIMIT_REAL_TIME 1296000, the three applies (APPLY_ATT_SPEED,
                              APPLY_CRITICAL_PCT, APPLY_MALL_ATTBONUS) and value0-5 (magic attack value1-2, attack
                              value3-4, + value5 to both);
  gf_item_list.tsv            the GF 26.1.11 client's item_list rows (icon and model: every tier shares the tier-1
                              weapon's icon/model of its kind, 21900-21905);
  gf_itemdesc_pl.tsv          the GF Polish client's names and descriptions (cache/arezzo/cpack locale/pl/itemdesc.txt);
  wiki_bronie_mlodych_bohaterow.raw   the pl-wiki page (action=raw) - every weapon's attack / magic attack, attack
                              speed, critical chance, attack value % and average damage are CHECKED against it (the
                              wiki rounds a few: a difference is printed, the official row is kept);
  owner_weapons.json          the owner's package (young_heroes/data/weapons.json) - checked the same way.

Our changes to the official rows (the owner's rules, 22 October 2026: no bonuses, no changes, no trade, no soul
stones, gone after 15 days also when worn):
  * antiflag: the class bits (ANTI_MUSA/ASSASSIN/SURA/MUDANG) + DROP | SELL | GIVE | PKDROP | MYSHOP | SAFEBOX (the
    official row has DROP | GIVE | MYSHOP | SAFEBOX and its own no-changelook / no-reinforce / no-enchant / no-sash
    bits, which our engine has not - server-patches/mlodzi refuses those paths by vnum); never ANTI_SAVE, never bit 18
    (ITEM_ANTIFLAG_DELETE here, ANTI_WOLFMAN officially);
  * magic_pct 0 (officially 15: no random bonuses when made), socket_pct 0, refined_vnum / refine_set 0, addon 0;
  * the applies as our POINT_* numbers (item_proto's applytype is a point here): 7 -> 17, 15 -> 40, 64 -> 114;
  * the average damage (+10 .. +30 %) is not in the row: playerbot_mlodzi.cpp sets it as the weapon's attribute 0
    when it is given (as officially).

Writes (GENERATED - edit this file, run it again):
  linux-port/docker/mariadb/playerbot/mlodzi_bohaterowie.sql   world.item_proto (INSERT IGNORE + the guarded
                                                               restriction columns), apply.sh every start
  tools/mlodzi/mlodzi_items.json                               the client's records, item_list and itemdesc rows and
                                                               the models (client-patches/client-2.0.30/tools/mlodzi)
  client-patches/client-2.0.30/root/icon/item/2190[0-5].tga    the GF icons

Example: python3 tools/mlodzi/gen_mlodzi.py
"""
import argparse
import io
import json
import os
import re
import shutil
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(os.path.dirname(HERE))
sys.path.insert(0, os.path.join(REPO, 'tools', 'yohara_items'))
import gen_yitems as Y  # noqa: E402  (the item row writer)

M = 'MT2009_PLUS_MLODZI_BOHATEROWIE_V1'
SQL_OUT = os.path.join(REPO, 'linux-port', 'docker', 'mariadb', 'playerbot', 'mlodzi_bohaterowie.sql')
JSON_OUT = os.path.join(HERE, 'mlodzi_items.json')
ICON_OUT = os.path.join(REPO, 'client-patches', 'client-2.0.30', 'root', 'icon', 'item')

WEAPON = 1
KINDS = {0: 'miecz', 1: 'sztylet', 2: 'luk', 3: 'dwureczna', 4: 'dzwon', 5: 'wachlarz'}
TIER_LEVELS = [1, 10, 20, 30, 40, 50, 60, 70]
LIFE = 1296000                                  # 15 days, LIMIT_REAL_TIME
AVERAGE = [10, 13, 16, 19, 22, 25, 28, 30]      # the wiki's "Srednie obrazenia" (the item's attribute 0)
LIMIT_LEVEL, LIMIT_REAL_TIME = 1, 7
WEAR_WEAPON = 16
CLASS_BITS = 4 | 8 | 16 | 32                    # ANTI_MUSA, ANTI_ASSASSIN, ANTI_SURA, ANTI_MUDANG
NO_TRADE = 128 | 256 | 8192 | 16384 | 65536 | 131072   # DROP, SELL, GIVE, PKDROP, MYSHOP, SAFEBOX
ANTI_SAVE = 4096
# official APPLY_* -> our POINT_* (common/length.h): ATT_SPEED 17, CRITICAL_PCT 40, MALL_ATTBONUS 114
APPLY_TO_POINT = {0: 0, 7: 17, 15: 40, 64: 114}
WIKI_SECTIONS = {'Broń jednoręczna': 0, 'Broń dwuręczna': 3, 'Wachlarze': 5, 'Dzwony': 4, 'Sztylety': 1, 'Łuki': 2}
NOTE = ('Broń dla Młodych Bohaterów: znika 15 dni po otrzymaniu (także założona). Nie można jej ulepszać, '
        'zmieniać ani dodawać bonusów, wkładać kamieni duszy, wymieniać, sprzedawać ani odkładać do magazynu.')


def read_tsv(name):
    rows = []
    with io.open(os.path.join(HERE, name), encoding='utf-8') as f:
        for line in f:
            line = line.rstrip('\n')
            if line and not line.startswith('#'):
                rows.append(line.split('\t'))
    return rows


def official():
    rows = read_tsv('official_item_proto.tsv')
    head = rows[0]
    out = {}
    for r in rows[1:]:
        d = dict(zip(head, r))
        out[int(d['vnum'])] = dict((k, (int(v) if k not in ('locale_name', 'immuneflag') else v)) for k, v in d.items())
    return out


def wiki_rows():
    """{(kind, level): {'atk': (lo, hi), 'mag': (lo, hi) | None, 'speed', 'crit', 'attpct', 'avg'}}"""
    with io.open(os.path.join(HERE, 'wiki_bronie_mlodych_bohaterow.raw'), encoding='utf-8') as f:
        text = f.read()
    out = {}
    for sec in re.split(r'\n===', text)[1:]:
        title = sec.split('===', 1)[0].strip()
        if title not in WIKI_SECTIONS:
            continue
        kind = WIKI_SECTIONS[title]
        for blk in sec.split('\n|-')[1:]:
            cells = [c.strip() for c in blk.split('\n| ')]
            lv = [c for c in cells if c.strip().isdigit()]
            if not lv:
                continue
            nums = lambda pat: [tuple(int(x) for x in re.findall(r'\d+', m.group(1)))
                                for m in re.finditer(pat + r'\s*<font color="green">([^<]*)</font>', blk)]
            atk = nums(r'\*Wartość ataku')
            mag = nums(r'\*Wartość magicznego ataku')
            out[(kind, int(lv[0]))] = dict(
                atk=atk[0] if atk else None, attpct=atk[1][0] if len(atk) > 1 else None,
                mag=mag[0] if mag else None,
                speed=(nums(r'\*Szybkość ataku') or [(None,)])[0][0],
                crit=(nums(r'\*Szansa na cios krytyczny') or [(None,)])[0][0],
                avg=(nums(r'\*Średnie obrażenia') or [(None,)])[0][0])
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--gf', default='/opt/metin2/cache/gf/Gameforge_26.1.11/_client')
    a = ap.parse_args()
    off = official()
    names = dict((int(r[0]), (r[1], r[2] if len(r) > 2 else '')) for r in read_tsv('gf_itemdesc_pl.tsv'))
    lst = dict((int(r[0]), r) for r in read_tsv('gf_item_list.tsv'))
    wiki = wiki_rows()
    with io.open(os.path.join(HERE, 'owner_weapons.json'), encoding='utf-8') as f:
        owner = dict((w['vnum'], w) for w in json.load(f))
    items, notes = [], []
    for t, level in enumerate(TIER_LEVELS):
        for kind in sorted(KINDS):
            v = 21900 + 10 * t + kind
            o = off[v]
            assert o['type'] == WEAPON and o['subtype'] == kind and o['wearflag'] == WEAR_WEAPON, v
            assert o['limittype0'] == LIMIT_LEVEL and o['limitvalue0'] == (0 if t == 0 else level), (v, o['limitvalue0'])
            assert o['limittype1'] == LIMIT_REAL_TIME and o['limitvalue1'] == LIFE, v
            assert o['applytype3'] == 0 and [o['applytype%d' % i] for i in range(3)] == [7, 15, 64], v
            pl, desc = names[v]
            assert len(pl.encode('cp1250')) <= 32, pl
            for bad in ('metin2', 'gameforge', 'oficjaln'):
                assert bad not in (pl + desc).lower(), (v, pl)
            gl = lst[v]
            assert gl[1] == 'WEAPON' and gl[2] == 'icon/item/%d.tga' % (21900 + kind), gl
            model = gl[3]
            assert model == 'd:/ymir work/item/weapon/%d.gr2' % (21900 + kind), gl
            vals = [o['value%d' % i] for i in range(6)]
            # the checks against the wiki and the owner's package (a difference is a note, the official row stays)
            w = wiki.get((kind, level))
            if w is None:
                notes.append('%d %s: not on the wiki page' % (v, pl))
            else:
                atk = (vals[3] + vals[5], vals[4] + vals[5])
                mag = (vals[1] + vals[5], vals[2] + vals[5]) if vals[1] or vals[2] else None
                got = dict(atk=atk, mag=mag, speed=o['applyvalue0'], crit=o['applyvalue1'], attpct=o['applyvalue2'],
                           avg=AVERAGE[t])
                for k in ('atk', 'mag', 'speed', 'crit', 'attpct', 'avg'):
                    if w[k] is not None and w[k] != got[k]:
                        notes.append('%d %s: %s wiki %s, official %s' % (v, pl, k, w[k], got[k]))
            ow = owner.get(v)
            if ow and (ow['values'] != vals or ow['fixed_instance_average_damage'] != AVERAGE[t]):
                notes.append('%d %s: the owner\'s package %s / %s, official %s / %s'
                             % (v, pl, ow['values'], ow['fixed_instance_average_damage'], vals, AVERAGE[t]))
            anti = (o['antiflag'] & CLASS_BITS) | NO_TRADE
            assert not anti & ANTI_SAVE and not anti & (1 << 18)
            d = dict(vnum=v, name=Y.ascii_name(pl), locale_name=pl, type=WEAPON, subtype=kind, stack=1, weight=0,
                     size=o['size'], antiflag=anti, flag=0, wearflag=WEAR_WEAPON, gold=0, shop_buy_price=0,
                     refined_vnum=0, refine_set=0, magic_pct=0, specular=o['specular'], socket_pct=0, addon_type=0,
                     limittype0=LIMIT_LEVEL, limitvalue0=o['limitvalue0'], limittype1=LIMIT_REAL_TIME, limitvalue1=LIFE,
                     applytype0=APPLY_TO_POINT[o['applytype0']], applyvalue0=o['applyvalue0'],
                     applytype1=APPLY_TO_POINT[o['applytype1']], applyvalue1=o['applyvalue1'],
                     applytype2=APPLY_TO_POINT[o['applytype2']], applyvalue2=o['applyvalue2'],
                     tier=t + 1, level=level, kind=kind, average=AVERAGE[t], model=model,
                     icon='icon/item/%d.tga' % (21900 + kind), list_type='WEAPON',
                     desc=(desc + ' ' if desc else '') + NOTE,
                     **dict(('value%d' % i, vals[i]) for i in range(6)))
            items.append(d)
    assert len(items) == 48
    write_sql(items)
    write_json(items)
    copy_icons(a.gf)
    print('items %d (8 tiers x 6 kinds, no Lycan); %d note(s) against the wiki / the owner\'s package:' % (len(items), len(notes)))
    for n in notes:
        print('  ' + n)


def write_sql(items):
    vn = ','.join(str(i['vnum']) for i in items)
    L = ['-- %s: Bronie dla Mlodych Bohaterow (21900-21975, no Lycan) - the owner, 22 October 2026.' % M,
         '-- GENERATED by tools/mlodzi/gen_mlodzi.py - do not edit, rerun it. Every start (apply.sh), idempotent.',
         '-- The official rows (tools/mlodzi/official_item_proto.tsv) with our restrictions: no trade / drop / sale /',
         '-- shop / storage (antiflag), no random bonus (magic_pct 0), no sockets (socket_pct 0), no refine',
         '-- (refined_vnum 0), LIMIT_LEVEL and LIMIT_REAL_TIME 1296000 (15 days from the grant, also while worn).',
         '-- The average damage is the weapon\'s attribute 0, set when given (playerbot_mlodzi.cpp); quest',
         '-- mlodzi_bohaterowie offers them, server-patches/mlodzi refuses the bonus / transmutation paths.',
         'SET NAMES utf8mb4;',
         'INSERT IGNORE INTO world.item_proto (%s) VALUES' % ','.join('`%s`' % c for c in Y.COLS),
         ',\n'.join(Y.sqlrow(i) for i in items) + ';',
         '-- the restrictions hold even on a row that was there before (an operator\'s or an older one): only the',
         '-- columns that make the weapon tradeable, refinable, socketable or permanent',
         'UPDATE world.item_proto SET antiflag = (antiflag & %d) | %d, refined_vnum = 0, refine_set = 0, magic_pct = 0, '
         'socket_pct = 0, addon_type = 0, limittype1 = %d, limitvalue1 = %d WHERE vnum IN (%s) AND type = %d AND '
         '(antiflag & %d <> %d OR refined_vnum <> 0 OR magic_pct <> 0 OR socket_pct <> 0 OR limittype1 <> %d OR '
         'limitvalue1 <> %d);'
         % (CLASS_BITS, NO_TRADE, LIMIT_REAL_TIME, LIFE, vn, WEAPON, NO_TRADE, NO_TRADE, LIMIT_REAL_TIME, LIFE)]
    with open(SQL_OUT, 'w', encoding='utf-8', newline='\n') as f:
        f.write('\n'.join(L) + '\n')


def write_json(items):
    keys = ('vnum', 'name', 'locale_name', 'type', 'subtype', 'stack', 'weight', 'size', 'antiflag', 'flag',
            'wearflag', 'gold', 'shop_buy_price', 'refined_vnum', 'refine_set', 'magic_pct', 'specular', 'socket_pct',
            'limittype0', 'limitvalue0', 'limittype1', 'limitvalue1', 'applytype0', 'applyvalue0', 'applytype1',
            'applyvalue1', 'applytype2', 'applyvalue2', 'value0', 'value1', 'value2', 'value3', 'value4', 'value5',
            'tier', 'level', 'kind', 'average')
    out = {'marker': M,
           'items': [dict((k, i[k]) for k in keys) for i in items],
           'item_list': dict((str(i['vnum']), '%d\t%s\t%s\t%s' % (i['vnum'], i['list_type'], i['icon'], i['model']))
                             for i in items),
           'itemdesc': dict((str(i['vnum']), '%d\t%s\t%s' % (i['vnum'], i['locale_name'], Y.client_desc(
               dict(i, status=Y.ST)))) for i in items),
           'models': sorted(set(i['model'] for i in items)),
           'icons': sorted(set(i['icon'] for i in items))}
    with open(JSON_OUT, 'w', encoding='utf-8', newline='\n') as f:
        json.dump(out, f, ensure_ascii=False, indent=0)
        f.write('\n')


def copy_icons(gf):
    os.makedirs(ICON_OUT, exist_ok=True)
    for kind in KINDS:
        name = '%d.tga' % (21900 + kind)
        s = os.path.join(gf, 'icon', 'item', name)
        assert os.path.isfile(s), s
        shutil.copyfile(s, os.path.join(ICON_OUT, name))


if __name__ == '__main__':
    main()
