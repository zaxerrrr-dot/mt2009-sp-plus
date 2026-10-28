#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""gen_cardbox.py [--owsap DIR] [--gf DIR]

MT2009_PLUS_MONSTER_CARD_BOXES_V1: the global server's four Monster Card boxes in the in-game ItemShop (the owner,
28 October 2026: "Add the global monster card boxes (silver / gold / platinum / Yohara card boxes, e.g. 83073 etc.)
to ItemShop V3").

The boxes (the vnums and flags: Owsap v6.2.6 db/item_proto.txt + item_names.txt; the icons: the GF 26.1.11 client,
whose item_list gives 83073 the picture 83033.tga and 83074 the picture 83034.tga - our 83033/83034 are the Yutnori
packs, so here every icon is saved under its box's own vnum). The contents and the prices: the global wikis (en / de /
tr / pl, read 28.10.2026):
  83036 Silver Monster Card Box   "may contain a Monster Card" - a card of the old continent or 1000 Yang; 25 SM;
                                  tradable (trade, shop, drop, storage, mail: yes)
  83037 Gold Monster Card Box     a card for sure, old continent only ("Enthaelt keine Monsterkarten von Yohara"); 35 SM;
                                  tradable
  83074 Plat. Monster Card Box    a card for sure "from all possible cards" (old and new continent, without the
                                  Moonshadow Vale's); 45 SM; no trade / shop / drop / storage / mail
  83073 Yohara Monster Card Box   a Yohara card for sure (without the Moonshadow Vale's); 150 SM; no trade / shop / drop
                                  / storage / mail
(the "Yohara Monster Card Box+", the Moonshadow Vale's cards too, is left out - our world has none of its monsters.)
Our pools: the mission levels of playerbot_monster_card_data.h - levels 1-15 = the old continent, 16-18 = Yohara
(MT2009_PLUS_MONSTER_CARDS_YOHARA_V1). The opening is the card system's own (playerbot_monster_card.h, OpenCardBox,
asked from MonsterCardUseItem, the engine's existing use hook): a Monster Card 50283 with the monster in socket 1, as
a mission gives it; no special_item_group (a giftbox group cannot set the card's monster). The silver box's chance
of a card is not on any wiki: 50% (SILVER_CARD_PERCENT there).

Writes (all GENERATED - edit this file, run it again):
  linux-port/docker/mariadb/playerbot/karty_pudelka.sql       world.item_proto (INSERT IGNORE; apply.sh step)
  tools/cardbox/cardbox.json                                  the client's records, item_list, itemdesc
  client-patches/client-2.0.30/root/icon/item/<vnum>.tga      the GF icons under the boxes' vnums
  linux-port/docker/itemshop/app/itemshop/img/item/<vnum>.png the web shops' pictures
  linux-port/docker/itemshop/app/shop3/include/db/client_itemdesc.json   the second ItemShop's descriptions (merged)

Example: python3 tools/cardbox/gen_cardbox.py
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
sys.path.insert(0, os.path.join(REPO, 'tools', 'itemshop3'))
import gen_shop_icons as GI  # noqa: E402  (TGA -> PNG, plain Python)
import glob  # noqa: E402

MARK = 'MT2009_PLUS_MONSTER_CARD_BOXES_V1'
# the unpacked GF 26.1.11 client (/opt/metin2/cache/gf/<its folder>/_client)
GF_DEFAULT = (sorted(glob.glob('/opt/metin2/cache/gf/*_26.1.11/_client')) or [''])[0]
SQL_OUT = os.path.join(REPO, 'linux-port', 'docker', 'mariadb', 'playerbot', 'karty_pudelka.sql')
JSON_OUT = os.path.join(HERE, 'cardbox.json')
ICON_OUT = os.path.join(REPO, 'client-patches', 'client-2.0.30', 'root', 'icon', 'item')
SHOP_IMG = os.path.join(REPO, 'linux-port', 'docker', 'itemshop', 'app', 'itemshop', 'img', 'item')
SHOP3_DESC = os.path.join(REPO, 'linux-port', 'docker', 'itemshop', 'app', 'shop3', 'include', 'db',
                          'client_itemdesc.json')
CARD_DATA = os.path.join(REPO, 'linux-port', 'overlays', 'playerbot', 'src', 'game', 'src',
                         'playerbot_monster_card_data.h')
CARD_CODE = os.path.join(os.path.dirname(CARD_DATA), 'playerbot_monster_card.h')

ITEM_GIFTBOX, ITEM_STACKABLE, STACK = 23, 4, 200
# ANTI_DROP | ANTI_GIVE | ANTI_PKDROP | ANTI_MYSHOP | ANTI_SAFEBOX (Owsap 83073 / 83074; the NPC buys it - no ANTI_SELL)
ANTI_BOUND = 128 | 8192 | 16384 | 65536 | 131072
OWSAP_BOUND = 'ANTI_DROP | ANTI_GIVE | ANTI_PKDROP | ANTI_MYSHOP | ANTI_SAFEBOX'
OLD_LEVELS = 15     # levels 1-15 the old continent, 16-18 Yohara (BOX_OLD_LEVELS in playerbot_monster_card.h)

USE_TEXT = u' Użyj karty, by dodać ją do swojej kolekcji (okno Kart Potworów, klawisz J).'
BOUND_TEXT = u' Nie można nim handlować ani go przechować w magazynie.'
BOXES = (
    dict(vnum=83036, name='Silver Monster Card Box', locale_name=u'Srebrne Pudełko Kart Potwora', anti=0, owsap_anti='NONE',
         owsap_name='Silver Monster Card Box', pool='old', price=25, index=627,
         desc=u'To srebrne pudełko zawiera losową Kartę Potwora albo 1000 Yang. Spróbuj szczęścia! Karty pochodzą '
              u'z poziomów misji 1-15 (bez potworów Yohary).' + USE_TEXT),
    dict(vnum=83037, name='Gold Monster Card Box', locale_name=u'Złote Pudełko Kart Potwora', anti=0, owsap_anti='NONE',
         owsap_name='Gold Monster Card Box', pool='old', price=35, index=628,
         desc=u'To złote pudełko zawsze zawiera jedną losową Kartę Potwora z poziomów misji 1-15 (bez potworów '
              u'Yohary).' + USE_TEXT),
    dict(vnum=83074, name='Plat. Monster Card Box', locale_name=u'Platynowe Pudełko Kart Potwora', anti=ANTI_BOUND,
         owsap_anti=OWSAP_BOUND, owsap_name='Plat. Monster Card Box', pool='all', price=45, index=629,
         desc=u'Platynowe pudełko zawsze zawiera jedną losową Kartę Potwora spośród wszystkich kart - z każdego '
              u'z 18 poziomów misji, także potworów Yohary.' + USE_TEXT + BOUND_TEXT),
    dict(vnum=83073, name='Yohara Monster Card Box', locale_name=u'Pudełko Kart Potworów Yohary', anti=ANTI_BOUND,
         owsap_anti=OWSAP_BOUND, owsap_name='Yohara Monster Card Box', pool='yohara', price=150, index=630,
         desc=u'To pudełko zawsze zawiera jedną losową Kartę Potwora Yohary - z poziomów misji 16-18.' + USE_TEXT
              + BOUND_TEXT),
)
# the GF client's picture of each box (shared/common/item_list.txt)
GF_ICON = {83036: 83036, 83037: 83037, 83073: 83033, 83074: 83034}
COLS = ('vnum', 'name', 'locale_name', 'type', 'subtype', 'stack', 'weight', 'size', 'antiflag', 'flag', 'wearflag',
        'immuneflag', 'gold', 'shop_buy_price', 'refined_vnum', 'refine_set', 'magic_pct', 'specular', 'socket_pct',
        'addon_type', 'limittype0', 'limitvalue0', 'limittype1', 'limitvalue1', 'applytype0', 'applyvalue0',
        'applytype1', 'applyvalue1', 'applytype2', 'applyvalue2', 'value0', 'value1', 'value2', 'value3', 'value4',
        'value5', 'socket0', 'socket1', 'socket2', 'socket3', 'socket4', 'socket5')


def item(b):
    return dict(vnum=b['vnum'], name=b['name'], locale_name=b['locale_name'], type=ITEM_GIFTBOX, subtype=0, stack=STACK,
                weight=0, size=1, antiflag=b['anti'], flag=ITEM_STACKABLE, wearflag=0, gold=0, shop_buy_price=0,
                refined_vnum=0, refine_set=0, magic_pct=0, specular=0, socket_pct=0, addon_type=0,
                limittype0=0, limitvalue0=0, limittype1=0, limitvalue1=0, applytype0=0, applyvalue0=0,
                applytype1=0, applyvalue1=0, applytype2=0, applyvalue2=0, value0=0, value1=0, value2=0, value3=0,
                value4=0, value5=0)


def sqlrow(i):
    out = []
    for c in COLS:
        if c == 'name':
            out.append("'%s'" % i['name'].replace("'", "''"))
        elif c == 'locale_name':
            out.append("_cp1250 X'%s'" % i['locale_name'].encode('cp1250').hex().upper())
        elif c == 'immuneflag':
            out.append("''")
        elif c.startswith('socket') and c != 'socket_pct':
            out.append('-1')
        else:
            out.append(str(i[c]))
    return '(' + ','.join(out) + ')'


def pools():
    """The mission levels' monsters (playerbot_monster_card_data.h LEVEL_POOL), as the box code draws them."""
    text = io.open(CARD_DATA, encoding='latin-1').read()
    body = text[text.index('LEVEL_POOL[LEVELS][DECK_SIZE]'):]
    body = body[body.index('{') + 1:body.index('};')]
    levels = [[int(x) for x in re.findall(r'\d+', row) if int(x)] for row in re.findall(r'\{([^{}]*)\}', body)]
    assert len(levels) == 18, len(levels)

    def uniq(rows):
        out = []
        for row in rows:
            for m in row:
                if m not in out:
                    out.append(m)
        return out
    old, yoh = uniq(levels[:OLD_LEVELS]), uniq(levels[OLD_LEVELS:])
    assert not set(old) & set(yoh), set(old) & set(yoh)
    code = io.open(CARD_CODE, encoding='latin-1').read()
    for b in BOXES:     # the C++ constants are these
        assert re.search(r'const DWORD BOX_\w+ = %d;' % b['vnum'], code), b['vnum']
    assert 'const int BOX_OLD_LEVELS = %d;' % OLD_LEVELS in code
    return dict(old=old, yohara=yoh, all=uniq(levels))


def check_owsap(owsap):
    """The global rows: ITEM_GIFTBOX, stackable, the antiflags above; the names in item_names.txt."""
    path = os.path.join(owsap, 'Server', 'Server', 'db', 'item_proto.txt')
    names = os.path.join(owsap, 'Server', 'Server', 'db', 'item_names.txt')
    if not os.path.isfile(path):
        print('note: no Owsap item_proto at %s - not compared' % path)
        return
    rows = [l.rstrip('\r\n').split('\t') for l in io.open(path, encoding='cp949', errors='replace')]
    head = rows[0]
    by = dict((r[0], dict(zip(head, r))) for r in rows[1:] if r and r[0].isdigit())
    nm = dict(l.rstrip('\r\n').split('\t', 1) for l in io.open(names, encoding='cp949', errors='replace')
              if '\t' in l and l.split('\t', 1)[0].isdigit())
    for b in BOXES:
        o = by[str(b['vnum'])]
        assert (o['Type'], o['Flags']) == ('ITEM_GIFTBOX', 'ITEM_STACKABLE'), (b['vnum'], o)
        assert o['AntiFlags'] == b['owsap_anti'], (b['vnum'], o['AntiFlags'])
        assert nm[str(b['vnum'])] == b['owsap_name'], (b['vnum'], nm[str(b['vnum'])])


def write_sql(items):
    L = ['-- %s: the four Monster Card boxes (83036 / 83037 / 83074 / 83073) - the owner, 28 October 2026. GENERATED' % MARK,
         '-- by tools/cardbox/gen_cardbox.py - do not edit, rerun it. Every start (apply.sh), idempotent: INSERT IGNORE - a',
         '-- row the operator changed (the Seban panel) is kept. The global vnums and flags (Owsap v6.2.6): ITEM_GIFTBOX,',
         '-- stackable; the silver and gold boxes tradable, the platinum and Yohara boxes bound (no trade / shop / drop /',
         '-- storage). Opened by the card system (playerbot_monster_card.h OpenCardBox) - no special_item_group.',
         'SET NAMES utf8mb4;',
         'INSERT IGNORE INTO world.item_proto (%s) VALUES' % ','.join('`%s`' % c for c in COLS),
         ',\n'.join(sqlrow(i) for i in items) + ';']
    with io.open(SQL_OUT, 'w', encoding='utf-8', newline='\n') as f:
        f.write('\n'.join(L) + '\n')


def write_json(items, pl):
    out = {'items': items,
           'item_list': dict((str(b['vnum']), '%d\tETC\ticon/item/%d.tga' % (b['vnum'], b['vnum'])) for b in BOXES),
           'itemdesc': dict((str(b['vnum']), '%d\t%s\t%s' % (b['vnum'], b['locale_name'], b['desc'])) for b in BOXES),
           'shop': dict((str(b['vnum']), dict(index=b['index'], price=b['price'], currency='DRAGON_COIN')) for b in BOXES),
           'pools': dict((str(b['vnum']), pl[b['pool']]) for b in BOXES)}
    for b in BOXES:
        for bad in ('metin2', 'game' 'forge', 'oficjaln'):
            assert bad not in b['desc'].lower(), b['vnum']
        assert len(b['locale_name'].encode('cp1250')) < 33
        b['desc'].encode('cp1250')
    with io.open(JSON_OUT, 'w', encoding='utf-8', newline='\n') as f:
        json.dump(out, f, ensure_ascii=False, indent=0, sort_keys=True)
        f.write('\n')


def write_shop3_desc():
    """The second ItemShop's tile text (shop3 tile.php reads client_itemdesc.json): the boxes' lines set, the rest kept."""
    with io.open(SHOP3_DESC, encoding='utf-8') as f:
        d = json.load(f)
    for b in BOXES:
        d[str(b['vnum'])] = b['desc']
    with io.open(SHOP3_DESC, 'w', encoding='utf-8', newline='\n') as f:
        json.dump(d, f, ensure_ascii=False, sort_keys=True, separators=(',', ':'))


def copy_icons(gf):
    os.makedirs(ICON_OUT, exist_ok=True)
    os.makedirs(SHOP_IMG, exist_ok=True)
    for b in BOXES:
        src = os.path.join(gf, 'icon', 'item', '%d.tga' % GF_ICON[b['vnum']])
        assert os.path.isfile(src), src
        shutil.copyfile(src, os.path.join(ICON_OUT, '%d.tga' % b['vnum']))
        w, h, rows = GI.tga_to_rgba(open(src, 'rb').read())
        open(os.path.join(SHOP_IMG, '%d.png' % b['vnum']), 'wb').write(GI.png(w, h, rows))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--owsap', default='/opt/metin2/cache/owsap')
    ap.add_argument('--gf', default=GF_DEFAULT)
    a = ap.parse_args()
    check_owsap(a.owsap)
    pl = pools()
    items = [item(b) for b in BOXES]
    write_sql(items)
    write_json(items, pl)
    write_shop3_desc()
    copy_icons(a.gf)
    print('%s: %d boxes; pools: old continent %d monsters, Yohara %d, all %d' %
          (MARK, len(BOXES), len(pl['old']), len(pl['yohara']), len(pl['all'])))


if __name__ == '__main__':
    main()
