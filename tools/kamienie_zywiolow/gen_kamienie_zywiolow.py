#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""gen_kamienie_zywiolow.py [--owsap DIR] [--gf DIR]

MT2009_PLUS_ELEMENT_STONES_V1: Kamien Ochrony Zywiolow and Kamien Mocy Zywiolow (the owner, 28 October 2026: "Dodaj do
itemshopu przedmioty Kamien Ochrony Zywiolow oraz Kamien Mocy Zywiolow. Kazdy mozna zalozyc osobno, idzie w slot tam
gdzie inne talizmany - lizaki, amulety, pierscienie. Mozna zalozyc tylko jeden z nich. Wszystkie boty Yohary wyposaz w
ten ochronny.").

The pl-wiki ("Kamien Ochrony Zywiolow", "Kamien Mocy Zywiolow", read 28.10.2026): a shining amulet, +10% resistance to
every element / 10% power of every element, 7 days counted also while not worn, Item-Shop 65 SM; NPC sale yes, trade
with a player no, private shop no, drop no, storage no, not combinable, no mail. The official vnums (Owsap v6.2.6
db/item_proto.txt, the GF 26.1.11 client's item_list and icons - the wiki's pictures are the GF icons 39119 / 39120,
pixel for pixel): 39119 "Elemental lolly (power)" = Kamien Mocy, 39120 "Elemental lolly (resistance)" = Kamien Ochrony -
ITEM_UNIQUE, WEAR_UNIQUE, REAL_TIME 604800, ANTI_DROP | ANTI_GIVE | ANTI_PKDROP | ANTI_STACK | ANTI_MYSHOP |
ANTI_SAFEBOX. The vnums were free in our world.item_proto (28 October 2026).

The six bonuses: item_proto has room for three (the engine's TItemTable and the client exe's record alike), so all six
are lines of world.item_extra_apply (MT2009_PLUS_ITEM_EXTRA_APPLY_V1, slots 1-6): CItem::ModifyPoints wears them like
the proto's own (server-patches/enginefixes, item.cpp), the bots' gear scoring counts them, the client's tooltip shows
them from gamedata/item_extra_apply.txt of the dbdata pack. Points: the resistances POINT_RESIST_ELEC 76 / FIRE 75 /
ICE 133 / WIND 78 / EARTH 134 / DARK 135, the powers POINT_ENCHANT_ELECT..DARK 178-183 (the talismans' and the
elixirs' points, server-patches/zywioly). Only one of the two at a time: playerbot_element_stones.cpp
(Mt2009ElementStoneRefuseEquip, called from CHARACTER::CanEquipNow's first hook) refuses the second with a message.

Writes (all GENERATED - edit this file, run it again):
  linux-port/docker/mariadb/playerbot/kamienie_zywiolow.sql   world.item_proto + world.item_extra_apply (INSERT IGNORE)
  tools/kamienie_zywiolow/kamienie_zywiolow.json              the client's records, item_list, itemdesc, extra lines
  client-patches/client-2.0.30/root/icon/item/3911{9,0}.tga   the GF icons
  client-patches/client-2.0.30/dbdata/gamedata/item_extra_apply.txt   the six lines of each (the Seban panel's dbdata
                                                              zip makes the same lines from the database)
  linux-port/docker/itemshop/app/itemshop/img/item/3911{9,0}.png   the web shops' pictures (the GF icon as PNG)

Example: python3 tools/kamienie_zywiolow/gen_kamienie_zywiolow.py
"""
import argparse
import io
import json
import os
import shutil
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(os.path.dirname(HERE))
sys.path.insert(0, os.path.join(REPO, 'tools', 'itemshop3'))
import gen_shop_icons as GI  # noqa: E402  (TGA -> PNG, plain Python)

MARK = 'MT2009_PLUS_ELEMENT_STONES_V1'
SQL_OUT = os.path.join(REPO, 'linux-port', 'docker', 'mariadb', 'playerbot', 'kamienie_zywiolow.sql')
JSON_OUT = os.path.join(HERE, 'kamienie_zywiolow.json')
ICON_OUT = os.path.join(REPO, 'client-patches', 'client-2.0.30', 'root', 'icon', 'item')
EXTRA_TXT = os.path.join(REPO, 'client-patches', 'client-2.0.30', 'dbdata', 'gamedata', 'item_extra_apply.txt')
SHOP_IMG = os.path.join(REPO, 'linux-port', 'docker', 'itemshop', 'app', 'itemshop', 'img', 'item')

ITEM_UNIQUE, WEARABLE_UNIQUE, LIMIT_REAL_TIME, DAYS7 = 16, 128, 7, 604800
# ANTI_DROP | ANTI_GIVE | ANTI_PKDROP | ANTI_STACK | ANTI_MYSHOP | ANTI_SAFEBOX (Owsap; the wiki: no trade, no shop, no
# drop, no storage; the NPC buys it - no ANTI_SELL)
ANTIFLAG = 128 | 8192 | 16384 | 32768 | 65536 | 131072
OWSAP_ANTI = 'ANTI_DROP | ANTI_GIVE | ANTI_PKDROP | ANTI_STACK | ANTI_MYSHOP | ANTI_SAFEBOX'
VALUE = 10
# the order of the tooltip: lightning, fire, ice, wind, earth, darkness
RESIST = (76, 75, 133, 78, 134, 135)        # POINT_RESIST_ELEC, FIRE, ICE, WIND, EARTH, DARK
POWER = (178, 179, 180, 181, 182, 183)      # POINT_ENCHANT_ELECT, FIRE, ICE, WIND, EARTH, DARK
TIME_TEXT = (u' Czas użytkowania: 7 dni - mija także wtedy, gdy kamień nie jest noszony. Można nosić tylko jeden '
             u'Kamień Żywiołów naraz (Ochrony albo Mocy). Nie można nim handlować ani go przechować w magazynie.')
STONES = (
    dict(vnum=39120, name='Elemental Protection Stone', locale_name=u'Kamień Ochrony Żywiołów', points=RESIST,
         owsap=u'(저항)',
         desc=u'Połyskujący amulet daje ci +10% odporności na wszystkie żywioły: błyskawice, ogień, lód, wiatr, ziemię '
              u'i mrok.' + TIME_TEXT),
    dict(vnum=39119, name='Elemental Power Stone', locale_name=u'Kamień Mocy Żywiołów', points=POWER,
         owsap=u'(강함)',
         desc=u'Połyskujący amulet daje ci 10% mocy wszystkich żywiołów: błyskawic, ognia, lodu, wiatru, ziemi i mroku.'
              + TIME_TEXT),
)
COLS = ('vnum', 'name', 'locale_name', 'type', 'subtype', 'stack', 'weight', 'size', 'antiflag', 'flag', 'wearflag',
        'immuneflag', 'gold', 'shop_buy_price', 'refined_vnum', 'refine_set', 'magic_pct', 'specular', 'socket_pct',
        'addon_type', 'limittype0', 'limitvalue0', 'limittype1', 'limitvalue1', 'applytype0', 'applyvalue0',
        'applytype1', 'applyvalue1', 'applytype2', 'applyvalue2', 'value0', 'value1', 'value2', 'value3', 'value4',
        'value5', 'socket0', 'socket1', 'socket2', 'socket3', 'socket4', 'socket5')


def ascii_name(s):
    return s.translate(str.maketrans(u'ąćęłńóśźżĄĆĘŁŃÓŚŹŻ', 'acelnoszzACELNOSZZ'))


def item(s):
    return dict(vnum=s['vnum'], name=s['name'], locale_name=s['locale_name'], type=ITEM_UNIQUE, subtype=0, stack=1,
                weight=0, size=1, antiflag=ANTIFLAG, flag=0, wearflag=WEARABLE_UNIQUE, gold=0, shop_buy_price=0,
                refined_vnum=0, refine_set=0, magic_pct=0, specular=0, socket_pct=0, addon_type=0,
                limittype0=LIMIT_REAL_TIME, limitvalue0=DAYS7, limittype1=0, limitvalue1=0, applytype0=0, applyvalue0=0,
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


def check_owsap(owsap):
    """The official rows: ITEM_UNIQUE, WEAR_UNIQUE, REAL_TIME 604800 and the antiflags above."""
    path = os.path.join(owsap, 'Server', 'Server', 'db', 'item_proto.txt')
    if not os.path.isfile(path):
        print('note: no Owsap item_proto at %s - not compared' % path)
        return
    rows = [l.rstrip('\r\n').split('\t') for l in io.open(path, encoding='cp949', errors='replace')]
    head = rows[0]
    by = dict((r[0], dict(zip(head, r))) for r in rows[1:] if r and r[0].isdigit())
    for s in STONES:
        o = by[str(s['vnum'])]
        assert (o['Type'], o['WearFlags'], o['LimitType0'], o['LimitValue0']) == \
            ('ITEM_UNIQUE', 'WEAR_UNIQUE', 'REAL_TIME', str(DAYS7)), (s['vnum'], o)
        assert o['AntiFlags'] == OWSAP_ANTI, (s['vnum'], o['AntiFlags'])
        assert o['Name'].endswith(s['owsap']), (s['vnum'], o['Name'])


def write_sql(items):
    L = ['-- %s: Kamien Ochrony Zywiolow (39120) and Kamien Mocy Zywiolow (39119) - the owner, 28 October 2026. GENERATED' % MARK,
         '-- by tools/kamienie_zywiolow/gen_kamienie_zywiolow.py - do not edit, rerun it. Every start (apply.sh), idempotent:',
         '-- INSERT IGNORE - a row the operator changed (the Seban panel) is kept. The official vnums and flags (Owsap v6.2.6):',
         '-- ITEM_UNIQUE in the unique slots, 7 days of real time, no drop / trade / private shop / storage. The six bonuses',
         '-- of each (+10% resistance to / power of every element) are world.item_extra_apply lines (item_proto has room',
         '-- for three; MT2009_PLUS_ITEM_EXTRA_APPLY_V1) - the table is made by apply.sh before this file runs.',
         'SET NAMES utf8mb4;',
         'INSERT IGNORE INTO world.item_proto (%s) VALUES' % ','.join('`%s`' % c for c in COLS),
         ',\n'.join(sqlrow(i) for i in items) + ';',
         'INSERT IGNORE INTO world.item_extra_apply (vnum, slot, apply_type, apply_value) VALUES']
    vals = []
    for s in STONES:
        for n, p in enumerate(s['points']):
            vals.append('(%d, %d, %d, %d)' % (s['vnum'], n + 1, p, VALUE))
    L.append(',\n'.join(vals) + ';')
    with io.open(SQL_OUT, 'w', encoding='utf-8', newline='\n') as f:
        f.write('\n'.join(L) + '\n')


def write_json(items):
    out = {'items': items,
           'item_list': dict((str(s['vnum']), '%d\tETC\ticon/item/%d.tga' % (s['vnum'], s['vnum'])) for s in STONES),
           'itemdesc': dict((str(s['vnum']), '%d\t%s\t%s' % (s['vnum'], s['locale_name'], s['desc'])) for s in STONES),
           'extra_apply': dict((str(s['vnum']), [[p, VALUE] for p in s['points']]) for s in STONES)}
    for s in STONES:
        for bad in ('metin2', 'gameforge', 'oficjaln'):
            assert bad not in s['desc'].lower(), s['vnum']
        assert len(s['locale_name'].encode('cp1250')) < 33
    with io.open(JSON_OUT, 'w', encoding='utf-8', newline='\n') as f:
        json.dump(out, f, ensure_ascii=False, indent=0, sort_keys=True)
        f.write('\n')


def write_extra_txt():
    """The client's gamedata/item_extra_apply.txt (repository copy, CRLF, ASCII; the format the Seban panel's dbdata zip
    writes - its "#" header, then vnum<TAB>point<TAB>value): the stones' lines replaced, the rest as it is."""
    raw = io.open(EXTRA_TXT, 'rb').read().decode('ascii')
    lines = raw.replace('\r\n', '\n').split('\n')
    if lines and lines[-1] == '':
        lines.pop()
    mine = set(str(s['vnum']) for s in STONES)
    lines = [l for l in lines if l.split('\t')[0] not in mine]
    for s in sorted(STONES, key=lambda x: x['vnum']):
        lines += ['%d\t%d\t%d' % (s['vnum'], p, VALUE) for p in s['points']]
    io.open(EXTRA_TXT, 'wb').write(('\r\n'.join(lines) + '\r\n').encode('ascii'))


def copy_icons(gf):
    os.makedirs(ICON_OUT, exist_ok=True)
    os.makedirs(SHOP_IMG, exist_ok=True)
    for s in STONES:
        src = os.path.join(gf, 'icon', 'item', '%d.tga' % s['vnum'])
        assert os.path.isfile(src), src
        shutil.copyfile(src, os.path.join(ICON_OUT, '%d.tga' % s['vnum']))
        w, h, rows = GI.tga_to_rgba(open(src, 'rb').read())
        open(os.path.join(SHOP_IMG, '%d.png' % s['vnum']), 'wb').write(GI.png(w, h, rows))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--owsap', default='/opt/metin2/cache/owsap')
    ap.add_argument('--gf', default='/opt/metin2/cache/gf/Gameforge_26.1.11/_client')
    a = ap.parse_args()
    check_owsap(a.owsap)
    items = [item(s) for s in STONES]
    write_sql(items)
    write_json(items)
    write_extra_txt()
    copy_icons(a.gf)
    print('%s: %d stones, %d extra bonus lines' % (MARK, len(STONES), sum(len(s['points']) for s in STONES)))


if __name__ == '__main__':
    main()
