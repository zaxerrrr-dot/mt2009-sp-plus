#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""gen_runy.py [--gf DIR]

MT2009_PLUS_RUNY_WYKUWANIA_V1 - Runy Wykuwania (forging runes) as the pl-wiki gives them ("Runy Wykuwania" and its 55
item pages "1 Runa Wykuwania Pasow" .. "5 Runa Wyk. Prz. d. Zw.", "System Gaya", "Yu-Hwan"; the de-wiki "1* / 2* / 5*
Schmiederune" only confirms the same numbers). The owner, 5 November 2026: "nie ma run wykuwania, dodalismy tylko okno
na te runy w oknie wytwarzania, wiec teraz tez dodaj wszystkie runy zgodnie z wiki". The window is
MT2009_PLUS_NPC_CRAFT_WINDOW_V1 (server-patches/gaya: "cube improve", locale/cube_improve.txt; root/uicubeokno.py's
"Podwyzsz szanse" slot) - it was there with the runes' lines commented out, their items missing.

  11 kinds x 5 grades = 55 items, the GF vnums 79605-79659 (GF 26.1.11 item_list.txt: five per kind, 1*..5*, the kinds
  in the wiki's order; the icons icon/item/79605..79609.tga by grade, every kind the same five)
  effect     the crafting window's chance-raising slot: +1 / +2 / +5 / +10 / +20 % on a recipe of the rune's category
             (cube_improve.txt), one rune used with every attempt (the window takes one item a try)
  1*         Portowy Sklep Gaya, row III (quest ygaya pool 3): 10 Gaya, Zest. Broni / Zest. Zbroi / Prz. d. Zw. 30 Gaya
  2*..5*     Yu-Hwan (20017) - two runes of the grade below + 2 / 4 / 6 / 10 Gaya + 200 000 / 400 000 / 600 000 /
             1 000 000 Yang, 40% (cube.runy.txt, his crafting window - quest mikstury_okno)
  5*         also Kolo Losu (Pasow, Broni, Zbroi, Akcesoriow, Rekawiczek - the wheels' sheet; kola-src/przedmioty.json)
  flags      1*-4*: sold to an NPC, no trade, no private shop, no drop, no storeroom, stack; 5*: trade, private shop,
             storeroom too, no drop (the wiki's table on every page; the one 1* Zbroi page that says "Tak" everywhere
             is the odd one out - its four siblings of 1* and its own 2*..4* say "Nie")
  not here   the wiki's other sources of 1* Pasow / 3* Akcesoriow (Czerw. / Zielona Skrzyneczka Losu, Srebrna / Zlota
             Skrzynia Proroka, Skrzynia Szczescia SM, Ruletka Dusz of Rytual Krwi, Loteria Tombola) - none of them is
             in this world (checked on the test server, 5 November 2026)

Type ITEM_QUEST (18) with no use flag, as other window items of ours (Bilet Kola Fortuny, Enasir): an ITEM_MATERIAL
of subtype 0 would go into the Ulepszacze storage (playerbot_ekwipunek.cpp), and the window's slot takes a bag item only.

Writes (all GENERATED - edit this file, run it again):
  linux-port/docker/mariadb/playerbot/runy_wykuwania.sql      world.item_proto (INSERT IGNORE) - apply.sh
  linux-port/docker/game/cube.runy.txt                        the 44 upgrades at Yu-Hwan - game/Dockerfile
  linux-port/docker/game/cube_improve.txt                     the runes' 55 lines (the block between the markers)
  tools/runy/runy_items.json                                  the client's records, item_list, itemdesc
  client-patches/client-2.0.30/root/icon/item/7960[5-9].tga   the GF icons (the root pack takes them)
  linux-port/docker/itemshop/app/itemshop/img/item/<vnum>.png the web icons (Kolo Losu's page)

Example: python3 tools/runy/gen_runy.py
"""
import argparse
import json
import os
import shutil
import struct
import sys
import zlib

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(os.path.dirname(HERE))
sys.path.insert(0, os.path.join(REPO, 'tools', 'yohara_items'))
import gen_yitems as Y  # noqa: E402  (the engine's numbers, the row writer)

MARK = 'MT2009_PLUS_RUNY_WYKUWANIA_V1'
SQL_OUT = os.path.join(REPO, 'linux-port', 'docker', 'mariadb', 'playerbot', 'runy_wykuwania.sql')
CUBE_OUT = os.path.join(REPO, 'linux-port', 'docker', 'game', 'cube.runy.txt')
IMPROVE = os.path.join(REPO, 'linux-port', 'docker', 'game', 'cube_improve.txt')
JSON_OUT = os.path.join(HERE, 'runy_items.json')
ICON_OUT = os.path.join(REPO, 'client-patches', 'client-2.0.30', 'root', 'icon', 'item')
WEB_OUT = os.path.join(REPO, 'linux-port', 'docker', 'itemshop', 'app', 'itemshop', 'img', 'item')

YU_HWAN = 20017
FIRST = 79605
GRADES = 5
BONUS = (1, 2, 5, 10, 20)                       # % - "Zwieksza szanse na powodzenie podczas wytwarzania ... o N%"
UP_GAYA = {2: 2, 3: 4, 4: 6, 5: 10}             # KosztGaya of the 2*..5* pages
UP_YANG = {2: 200000, 3: 400000, 4: 600000, 5: 1000000}
UP_PCT = 40                                     # SzansaNaWytworzenie
STACK = 200
# (the wiki's name after "N* ", the noun of its description, the window's category (cube.cpp: 0 armour 1 weapon
#  2 accessory 3 belt 5 other 7 weapon set 8 armour set 9 helmet set 10 pet 11 skill book 12 glove), 1* price in Gaya)
KINDS = [
    (u'Runa Wykuwania Pasów', u'pasów', 3, 10),
    (u'Runa Wykuwania Broni', u'broni', 1, 10),
    (u'Runa Wykuwania Zbroi', u'zbroi', 0, 10),
    (u'Runa Wyk. Poz. Prz.', u'pozostałych przedmiotów', 5, 10),
    (u'Runa Wyk. Akcesoriów', u'akcesoriów', 2, 10),
    (u'Runa Wyk. Ks. Um.', u'księgi umiejętności', 11, 10),
    (u'Runa Wyk. Zest. Broni', u'zestawów broni', 7, 30),
    (u'Runa Wyk. Zest. Hełm.', u'zestawów hełmów', 9, 10),
    (u'Runa Wyk. Zest. Zbroi', u'zestawów zbroi', 8, 30),
    (u'Runa Wyk. Rękawiczek', u'rękawiczek', 12, 10),
    (u'Runa Wyk. Prz. d. Zw.', u'przedmiotów dla zwierzaków', 10, 30),
]
A = Y.ANTI
F = Y.FLAGS
# 1*-4*: NPC yes, trade no, shop no, drop no, storeroom no, stack yes, mail no
BOUND = A['ANTI_DROP'] | A['ANTI_GIVE'] | A['ANTI_PKDROP'] | A['ANTI_MYSHOP'] | A['ANTI_SAFEBOX']
# 5*: NPC yes, trade yes, shop yes, drop no, storeroom yes, stack yes, mail yes
FREE = A['ANTI_DROP'] | A['ANTI_PKDROP']


def vnum_of(kind, grade):
    return FIRST + kind * GRADES + grade - 1


def runes():
    out = []
    for k, (name, noun, cat, price) in enumerate(KINDS):
        for g in range(1, GRADES + 1):
            pl = u'%d* %s' % (g, name)
            assert len(pl.encode('cp1250')) <= 24, pl
            text = u'Zwiększa szansę na powodzenie podczas wytwarzania %s o %d%%.' % (noun, BONUS[g - 1])
            text += u' Połóż ją w polu "Podwyższ szansę" okna wytwarzania - przy każdej próbie zużywa się jedna runa.'
            if g < GRADES:
                text += u' Dwie takie runy Yu-Hwan przekształci w runę %d* (40%%).' % (g + 1)
            else:
                text += u' Jest to maksymalny poziom runy.'
            out.append(dict(vnum=vnum_of(k, g), kind=k, grade=g, locale_name=pl, name=Y.ascii_name(pl), desc=text,
                            bonus=BONUS[g - 1], category=cat, gaya_price=price if g == 1 else 0,
                            icon='icon/item/%d.tga' % (FIRST + g - 1)))
    assert len(out) == 55 and out[-1]['vnum'] == 79659
    return out


def proto(r):
    d = dict(vnum=r['vnum'], name=r['name'], locale_name=r['locale_name'], type=Y.TYPES['ITEM_QUEST'], subtype=0,
             stack=STACK, weight=0, size=1, antiflag=FREE if r['grade'] == GRADES else BOUND, flag=F['ITEM_STACKABLE'],
             wearflag=0, gold=0, shop_buy_price=0, refined_vnum=0, refine_set=0, magic_pct=0, specular=0, socket_pct=0,
             addon_type=0, limittype0=0, limitvalue0=0, limittype1=0, limitvalue1=0, applytype0=0, applyvalue0=0,
             applytype1=0, applyvalue1=0, applytype2=0, applyvalue2=0, value0=0, value1=0, value2=0, value3=0, value4=0, value5=0)
    return d


def write_sql(rs):
    L = ['-- %s: Runy Wykuwania 79605-79659 (11 kinds x 1*..5*) - the owner, 5 November 2026 ("dodaj wszystkie' % MARK,
         '-- runy zgodnie z wiki"). GENERATED by tools/runy/gen_runy.py - do not edit, rerun it. Every start (apply.sh),',
         '-- idempotent: INSERT IGNORE - a row the operator changed is kept. The pl-wiki "Runy Wykuwania" and its item',
         '-- pages: the names, the 1/2/5/10/20% of the crafting window (cube_improve.txt), the flags: 1*-4* sold to an',
         '-- NPC only (no drop / give / private shop / storeroom), 5* also traded, sold in a private shop and stored (no',
         '-- drop); a stack of 200. ITEM_QUEST without a use: the bag keeps them (the window\'s slot takes a bag item);',
         '-- the bonus and category are cube_improve.txt\'s (the core reads it), not the row\'s values.',
         'SET NAMES utf8mb4;',
         'INSERT IGNORE INTO world.item_proto (%s) VALUES' % ','.join('`%s`' % c for c in Y.COLS),
         ',\n'.join(Y.sqlrow(proto(r)) for r in rs) + ';']
    with open(SQL_OUT, 'w', encoding='utf-8', newline='\n') as f:
        f.write('\n'.join(L) + '\n')


def write_cube(rs):
    by = dict((r['vnum'], r) for r in rs)
    L = ['# %s: Runy Wykuwania at Yu-Hwan (20017) - the pl-wiki "Runy Wykuwania" / the 2*..5* pages ("Wytwarzana' % MARK,
         '# z Run ... u Yu-Hwana"): two runes of one kind and grade > one of the next grade, 40%, Gaya 2 / 4 / 6 / 10 and',
         '# 200 000 / 400 000 / 600 000 / 1 000 000 Yang. GENERATED by tools/runy/gen_runy.py. Appended to cube.txt by',
         '# the game Dockerfile after cube.npc_okno.txt; Yu-Hwan\'s window opens by quest mikstury_okno.',
         '']
    n = 0
    for k in range(len(KINDS)):
        for g in range(2, GRADES + 1):
            src, dst = by[vnum_of(k, g - 1)], by[vnum_of(k, g)]
            L += ['# %s <- 2x %s (Yu-Hwan, wiki "%s")' % (Y.ascii_name(dst['locale_name']), Y.ascii_name(src['locale_name']),
                                                         Y.ascii_name(dst['locale_name']).replace('*', '')),
                  'section', 'npc\t%d' % YU_HWAN, 'item\t%d\t2' % src['vnum'], 'reward\t%d\t1' % dst['vnum'],
                  'percent\t%d' % UP_PCT, 'gold\t%d' % UP_YANG[g], 'gaya\t%d' % UP_GAYA[g], 'end', '']
            n += 1
    assert n == 44
    with open(CUBE_OUT, 'w', encoding='utf-8', newline='\n') as f:
        f.write('\n'.join(L))
    return n


def write_improve(rs):
    text = open(IMPROVE, encoding='utf-8').read()
    begin = '# %s BEGIN' % MARK
    end = '# %s END' % MARK
    block = [begin,
             '# Runy Wykuwania (pl-wiki "Runy Wykuwania"; 1* in Portowy Sklep Gaya, 2*-5* made at Yu-Hwan from two of the',
             '# lower one; tools/runy/gen_runy.py writes this block): +1 / +2 / +5 / +10 / +20 % on their category, every NPC.']
    for r in rs:
        block.append('%d\t%d\t%d\t\t# %s' % (r['vnum'], r['bonus'], r['category'], Y.ascii_name(r['locale_name'])))
    block.append(end)
    if begin in text:
        a = text.index(begin)
        b = text.index(end) + len(end)
        text = text[:a] + '\n'.join(block) + text[b:]
    else:
        # the commented-out lines of MT2009_PLUS_NPC_CRAFT_WINDOW_V1 (the items were missing) give way to the block
        lines = text.split('\n')
        keep = [l for l in lines if not (l.startswith('#796') or l.startswith('# Runy Wykuwania (pl-wiki')
                                         or l.startswith('# Their items (79605-79659)'))]
        while keep and keep[-1] == '':
            keep.pop()
        text = '\n'.join(keep) + '\n' + '\n'.join(block) + '\n'
    if not text.endswith('\n'):
        text += '\n'
    with open(IMPROVE, 'w', encoding='utf-8', newline='\n') as f:
        f.write(text)


def write_json(rs):
    keys = ('vnum', 'name', 'locale_name', 'type', 'subtype', 'stack', 'antiflag', 'flag', 'gold', 'shop_buy_price',
            'value0', 'value1')
    items = []
    for r in rs:
        p = proto(r)
        items.append(dict((k, p[k]) for k in keys))
    out = {'_note': '%s - GENERATED by tools/runy/gen_runy.py (the server: runy_wykuwania.sql); read by '
                    'client-patches/client-2.0.30/tools/runy/patch_runy_client.py' % MARK,
           'items': items,
           'item_list': dict((str(r['vnum']), '%d\tETC\t%s' % (r['vnum'], r['icon'])) for r in rs),
           'itemdesc': dict((str(r['vnum']), '%d\t%s\t%s' % (r['vnum'], r['locale_name'], r['desc'])) for r in rs),
           'gaya_shop': [[r['vnum'], 1, r['gaya_price']] for r in rs if r['grade'] == 1]}
    for d in out['itemdesc'].values():
        for bad in ('metin2', 'gameforge', 'oficjaln'):
            assert bad not in d.lower(), d
    with open(JSON_OUT, 'w', encoding='utf-8', newline='\n') as f:
        json.dump(out, f, ensure_ascii=False, indent=0)
        f.write('\n')


def tga_to_png(b):
    """GF's icons: 32-bit uncompressed TGA (type 2) -> PNG RGBA (no PIL on the host)"""
    idlen, cmtype, itype = b[0], b[1], b[2]
    w, h, bpp, desc = struct.unpack_from('<HHBB', b, 12)
    assert cmtype == 0 and itype == 2 and bpp == 32, (cmtype, itype, bpp)
    px = b[18 + idlen:18 + idlen + w * h * 4]
    rows = []
    for y in range(h):
        sy = y if desc & 0x20 else h - 1 - y
        line = px[sy * w * 4:(sy + 1) * w * 4]
        out = bytearray(b'\0')
        for x in range(w):
            bl, g, r, a = line[x * 4:x * 4 + 4]
            out += bytes((r, g, bl, a))
        rows.append(bytes(out))

    def chunk(t, d):
        return struct.pack('>I', len(d)) + t + d + struct.pack('>I', zlib.crc32(t + d) & 0xffffffff)
    return (b'\x89PNG\r\n\x1a\n' + chunk(b'IHDR', struct.pack('>IIBBBBB', w, h, 8, 6, 0, 0, 0))
            + chunk(b'IDAT', zlib.compress(b''.join(rows), 9)) + chunk(b'IEND', b''))


def write_icons(rs, gf):
    os.makedirs(ICON_OUT, exist_ok=True)
    pngs = {}
    for g in range(GRADES):
        name = '%d.tga' % (FIRST + g)
        src = os.path.join(gf, 'icon', 'item', name)
        assert os.path.isfile(src), src
        shutil.copyfile(src, os.path.join(ICON_OUT, name))
        pngs[FIRST + g] = tga_to_png(open(src, 'rb').read())
    for r in rs:
        with open(os.path.join(WEB_OUT, '%d.png' % r['vnum']), 'wb') as f:
            f.write(pngs[FIRST + r['grade'] - 1])


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--gf', default='/opt/metin2/cache/gf/Gameforge_26.1.11/_client')
    a = ap.parse_args()
    rs = runes()
    write_sql(rs)
    n = write_cube(rs)
    write_improve(rs)
    write_json(rs)
    write_icons(rs, a.gf)
    print('runes %d (%d-%d), Yu-Hwan recipes %d, cube_improve lines %d' % (len(rs), rs[0]['vnum'], rs[-1]['vnum'], n,
                                                                          len(rs)))


if __name__ == '__main__':
    main()
