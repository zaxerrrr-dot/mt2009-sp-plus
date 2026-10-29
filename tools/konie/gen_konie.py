#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""gen_konie.py [--gf DIR]

MT2009_PLUS_HORSE40_V1: the items of the horse past level 21 (server-patches/konie/README.md) - the pl-wiki's
"Pasza dla Konia", "Czer. Żeń-szeń (premium)", "Szlachetna Trawa", "Złota Księga Konia" and the horse skill books
("Jazda ..."), the vnums of the uploaded package "system_rozwoju_konia" (Best Studio; 03. Server/proto/tr) = the
GF 26.1.11 client's:

  50046 Szlachetna Trawa           ITEM_QUEST, quest use (konie_rozwoj: revives a horse of 31+), tradeable
  50047 Czer. Żeń-szeń (premium)   ITEM_QUEST, quest use (feeds the horse; the Black Steed / mighty horse eat it
                                   from the hand too), stack 200, tradeable; drops on the Sung Ma maps
  50048 Pasza dla Konia            ITEM_QUEST, stack 200, no drop / give / shop / storage (the wiki) - the window's feed
  50049 Złota Księga Konia         ITEM_QUEST, quest use (summons Potężny Koń Wojskowy), bound
  55050-55067 the horse skill books (already in world.item_proto as materials - yohara_items2.sql): type ITEM_QUEST
                                   and flag QUEST_USE added (quest konie_rozwoj teaches the skill), a new description
  83050 Zestaw Opieki nad Koniem   ITEM_GIFTBOX (Owsap's / GF's "Horse Care Kit" vnum): Pasza dla Konia x50,
                                   Czer. Żeń-szeń (premium) x5, Szlachetna Trawa (the wiki) - special_item_group
                                   (game/special_item_group.konie.txt); ItemShop 399 SM (the wiki), V3 and in-game
  20149-20151 Potężny Koń Wojskowy (mob_proto): copies of 20107 - apply.sh (the copy pattern it checks itself)

Writes (GENERATED - edit this file, run it again):
  linux-port/docker/mariadb/playerbot/konie.sql   world.item_proto (INSERT IGNORE + the books' guarded UPDATE)
  tools/konie/konie_items.json                   the client's records, item_list and itemdesc rows
                                                 (client-patches/client-2.0.30/tools/konie)
  linux-port/docker/game/special_item_group.konie.txt   the kit's group (appended by the Dockerfile)
  client-patches/client-2.0.30/root/icon/item/50046-50049.tga, 83050.tga   the GF icons (--gf)
"""
import argparse
import json
import os
import shutil
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(os.path.dirname(HERE))
sys.path.insert(0, os.path.join(REPO, 'tools', 'yohara_items'))
import gen_yitems as Y  # noqa: E402

M = 'MT2009_PLUS_HORSE40_V1'
SQL_OUT = os.path.join(REPO, 'linux-port', 'docker', 'mariadb', 'playerbot', 'konie.sql')
SIG_OUT = os.path.join(REPO, 'linux-port', 'docker', 'game', 'special_item_group.konie.txt')
KIT = 83050
KIT_ITEMS = ((50048, 50, 'Pasza dla Konia'), (50047, 5, 'Czer. Zen-szen (premium)'), (50046, 1, 'Szlachetna Trawa'))
JSON_OUT = os.path.join(HERE, 'konie_items.json')
ICON_OUT = os.path.join(REPO, 'client-patches', 'client-2.0.30', 'root', 'icon', 'item')
GF = '/opt/metin2/cache/gf/Gameforge_26.1.11/_client'

QUEST = 18
GIFTBOX = 23
STACK, QUEST_USE, LOG = 4, 1024, 8192
ANTI_DROP, ANTI_SELL, ANTI_GIVE, ANTI_PKDROP, ANTI_STACK, ANTI_MYSHOP, ANTI_SAFEBOX = 128, 256, 8192, 16384, 32768, \
    65536, 131072

NEW = [
    (50046, 'Szlachetna Trawa', dict(stack=1, flag=QUEST_USE, gold=1000, shop_buy_price=0),
     'Legendarne zioło, którym wyjątkowo zdolni jeźdźcy ożywiają Potężnego Konia Wojskowego (koń od 31 poziomu). '
     'Kliknij prawym przyciskiem myszy, gdy twój koń nie żyje.'),
    (50047, 'Czer. Żeń-szeń (premium)', dict(stack=200, flag=STACK | QUEST_USE, gold=1000, shop_buy_price=0, value0=3),
     'Duszony żeń-szeń premium - jedyna pasza Potężnego Konia Wojskowego (koń od 31 poziomu). Kliknij prawym '
     'przyciskiem myszy, aby nakarmić przywołanego konia, albo podaj go koniowi. Wypada z potworów Yohary.'),
    (50048, 'Pasza dla Konia', dict(stack=200, flag=STACK, gold=100, shop_buy_price=0,
                                    antiflag=ANTI_DROP | ANTI_GIVE | ANTI_PKDROP | ANTI_MYSHOP | ANTI_SAFEBOX),
     'Potrzebna do rozwoju konia od 21 poziomu: karmisz nią konia w oknie rozwoju u Stajennego (doświadczenie konia), '
     'a próba awansu zjada 50 sztuk. Otrzymasz ją u Stajennego (codziennie, "Pasza dla konia").'),
    (50049, 'Złota Księga Konia', dict(stack=1, flag=QUEST_USE, gold=0, shop_buy_price=0, value0=3,
                                       antiflag=ANTI_DROP | ANTI_SELL | ANTI_GIVE | ANTI_PKDROP | ANTI_STACK |
                                       ANTI_MYSHOP | ANTI_SAFEBOX),
     'Przywołuje Potężnego Konia Wojskowego (koń od 31 poziomu). Potrzebujesz 300 PE, by jej użyć. Otrzymasz ją u '
     'Stajennego po zadaniu "Złota Księga Konia".'),
    (KIT, 'Zestaw Opieki nad Koniem', dict(type=GIFTBOX, stack=200, flag=STACK, gold=0, shop_buy_price=0),
     'Ten zestaw zawiera wszystko, czego potrzebuje troskliwy właściciel konia: 50 Paszy dla Konia, 5 Czer. '
     'Żeń-szeni (premium) i Szlachetną Trawę na wypadek, gdyby twój rumak poległ na polu bitwy. Kliknij prawym '
     'przyciskiem myszy, aby otworzyć.'),
]

# the books: vnum -> (the skill's description; the book already exists as a material)
BOOK_DESC = 'Rozwija umiejętności konne. Kliknij prawym przyciskiem myszy, aby twój koń (od 21 poziomu) nauczył się ' \
            'umiejętności: %s Jedna umiejętność od 21 poziomu konia, druga od 31; poziom 1-20 w oknie rozwoju konia ' \
            '(1000 Gaya i 20 000 000 Yang za poziom), zapomnienie za darmo u Stajennego. Działa na każdym wierzchowcu.'
BOOKS = [
    (55050, 'Jazda (Zwinne Kopyta)', 'zwiększa na krótko prędkość ruchu, gdy walczysz z grzbietu wierzchowca.'),
    (55051, 'Jazda Konna (PD)', 'zwiększa zdobywane doświadczenie podczas jazdy.'),
    (55052, 'Jazda (Gwałt. Wichura)', 'zwiększa na krótko prędkość ataku, gdy walczysz z grzbietu wierzchowca.'),
    (55053, 'Jazda (Bezszelest. Chód)', 'daje na krótko Lekki Krok, gdy walczysz pieszo.'),
    (55054, 'Jazda (Nieśmiertelność)', 'na kilka sekund chroni przed obrażeniami, gdy PŻ jeźdźca spadną poniżej 30%.'),
    (55055, 'Jazda (Brak Odrzutu)', 'z szansą 1% przy ataku chroni na kilkanaście sekund przed odrzuceniem.'),
    (55056, 'Jazda Konna (losowo)', 'losowa: silny przeciwko półludziom, zwierzętom, orkom, mistykom, nieumarłym, '
                                    'diabłom, potworom pustyni, insektom albo wszystkim potworom.'),
    (55057, 'Jazda Konna (Wojownik)', 'zwiększa obrażenia zadawane wojownikom podczas jazdy.'),
    (55058, 'Jazda Konna (Ninja)', 'zwiększa obrażenia zadawane ninja podczas jazdy.'),
    (55059, 'Jazda Konna (Sura)', 'zwiększa obrażenia zadawane surom podczas jazdy.'),
    (55060, 'Jazda Konna (Szaman)', 'zwiększa obrażenia zadawane szamanom podczas jazdy.'),
    (55061, 'Jazda Konna (Likan)', 'zwiększa obrażenia zadawane likanom (w tym świecie nie ma Likanów - '
                                   'nie można się jej nauczyć).'),
    (55062, 'Jazda (umiej. konne)', 'zwiększa obrażenia umiejętności konnych.'),
    (55063, 'Jazda (W. SungMa. SIŁA)', 'zwiększa na krótko Wolę SungMa (SIŁA), gdy walczysz z grzbietu wierzchowca.'),
    (55064, 'Jazda (W. SungMa. WIT)', 'zwiększa na krótko Wolę SungMa (WIT), gdy walczysz z grzbietu wierzchowca.'),
    (55065, 'Jazda (W. SungMa. ODP)', 'zwiększa na krótko Wolę SungMa (ODP), gdy walczysz z grzbietu wierzchowca.'),
    (55066, 'Jazda (W. SungMa. INT)', 'zwiększa na krótko Wolę SungMa (INT), gdy walczysz z grzbietu wierzchowca.'),
    (55067, 'Jazda Konna (Precyzja)', 'zwiększa precyzję podczas jazdy.'),
]
BOOK_ICON = {55051: 55051, 55056: 55051, 55057: 55051, 55058: 55051, 55059: 55051, 55060: 55051, 55061: 55051,
             55062: 55051, 55067: 55051}   # the GF item_list: the others show 55050.tga


def item(vnum, name, desc, **kw):
    d = dict(vnum=vnum, src=vnum, status=Y.ST, name=Y.ascii_name(name), locale_name=name, type=QUEST, subtype=0,
             stack=200, weight=0, size=1, antiflag=0, flag=STACK, wearflag=0, gold=1000, shop_buy_price=0,
             refined_vnum=0, refine_set=0, magic_pct=0, specular=0, socket_pct=0, addon_type=0, limittype0=0,
             limitvalue0=0, limittype1=0, limitvalue1=0, applytype0=0, applyvalue0=0, applytype1=0, applyvalue1=0,
             applytype2=0, applyvalue2=0, value0=0, value1=0, value2=0, value3=0, value4=0, value5=0, desc=desc,
             icon='icon/item/%d.tga' % vnum, list_type='ETC')
    d.update(kw)
    assert len(d['locale_name'].encode('cp1250')) <= 24, d['locale_name']
    return d


def items():
    return [item(v, n, desc, **kw) for v, n, kw, desc in NEW]


def write_sql(its):
    books = ','.join(str(b[0]) for b in BOOKS)
    L = ['-- %s: the items of the horse past level 21 (server-patches/konie/README.md) - GENERATED by' % M,
         '-- tools/konie/gen_konie.py, do not edit, rerun it. Every start (apply.sh), idempotent: INSERT IGNORE - a row the',
         '-- operator changed is kept; the books get ITEM_QUEST and QUEST_USE only while they are still materials (type 5).',
         '--   50046 Szlachetna Trawa, 50047 Czer. Żeń-szeń (premium), 50048 Pasza dla Konia, 50049 Złota Księga Konia',
         '--   (the package\'s / GF\'s vnums - free in world.item_proto on 29 October 2026), the books 55050-55067',
         '--   (yohara_items2.sql) taught by quest konie_rozwoj.',
         'SET NAMES utf8mb4;',
         'INSERT IGNORE INTO world.item_proto (%s) VALUES' % ','.join('`%s`' % c for c in Y.COLS),
         ',\n'.join(Y.sqlrow(i) for i in its) + ';',
         'UPDATE world.item_proto SET type = %d, flag = flag | %d WHERE vnum IN (%s) AND type = 5;' % (QUEST, QUEST_USE,
                                                                                                    books)]
    with open(SQL_OUT, 'w', encoding='utf-8', newline='\n') as f:
        f.write('\n'.join(L) + '\n')


def write_sig():
    L = ['# %s: GENERATED by tools/konie/gen_konie.py - do not edit. Zestaw Opieki nad Koniem (%d, pl-wiki' % (M, KIT),
         '# "Zestaw Opieki nad Koniem": Pasza dla Konia x50, Czer. Zen-szen (premium) x5, Szlachetna Trawa). Type Pct:',
         '# every line 100 - the box gives all three. Appended to special_item_group.txt by the Dockerfile (once, after any',
         '# group of the same vnum is cut out).',
         'Group\tmt2009_konie_zestaw_opieki',
         '{',
         '\tVnum\t%d -- Zestaw Opieki nad Koniem' % KIT,
         '\tType\tPct']
    for i, (v, n, name) in enumerate(KIT_ITEMS):
        L.append('\t%d\t%d\t%d\t100 -- %s' % (i + 1, v, n, name))
    L.append('}')
    with open(SIG_OUT, 'w', encoding='ascii', newline='\n') as f:
        f.write('\n'.join(L) + '\n')


def write_json(its):
    keys = ('vnum', 'name', 'locale_name', 'type', 'subtype', 'stack', 'weight', 'size', 'antiflag', 'flag',
            'wearflag', 'gold', 'shop_buy_price', 'refined_vnum', 'refine_set', 'magic_pct', 'specular', 'socket_pct',
            'limittype0', 'limitvalue0', 'limittype1', 'limitvalue1', 'applytype0', 'applyvalue0', 'applytype1',
            'applyvalue1', 'applytype2', 'applyvalue2', 'value0', 'value1', 'value2', 'value3', 'value4', 'value5')
    desc = dict((str(i['vnum']), '%d\t%s\t%s' % (i['vnum'], i['locale_name'], Y.client_desc(i))) for i in its)
    for v, n, d in BOOKS:
        text = BOOK_DESC % d
        for bad in ('Metin2', 'Gameforge'):
            assert bad.lower() not in text.lower()
        desc[str(v)] = '%d\t%s\t%s' % (v, n, text)
    out = {'marker': M,
           'items': [dict((k, i[k]) for k in keys) for i in its],
           'books': {'vnums': [b[0] for b in BOOKS], 'type': QUEST, 'flag_add': QUEST_USE},
           'item_list': dict((str(i['vnum']), '%d\t%s\t%s' % (i['vnum'], i['list_type'], i['icon'])) for i in its),
           'itemdesc': desc,
           'kit_type': GIFTBOX,
           'mobs': {'template': 20107, 'vnums': [20149, 20150, 20151], 'locale_name': 'Potężny Koń Wojskowy'}}
    for v, n, d in BOOKS:
        out['item_list'][str(v)] = '%d\tETC\ticon/item/%d.tga' % (v, BOOK_ICON.get(v, 55050))
    with open(JSON_OUT, 'w', encoding='utf-8', newline='\n') as f:
        json.dump(out, f, ensure_ascii=False, indent=1, sort_keys=True)
        f.write('\n')


def copy_icons(gf):
    os.makedirs(ICON_OUT, exist_ok=True)
    for v, n, kw, d in NEW:
        src = os.path.join(gf, 'icon', 'item', '%d.tga' % v)
        dst = os.path.join(ICON_OUT, '%d.tga' % v)
        if os.path.isfile(src):
            shutil.copyfile(src, dst)
        assert os.path.isfile(dst), dst


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--gf', default=GF)
    a = ap.parse_args()
    its = items()
    write_sql(its)
    write_json(its)
    write_sig()
    copy_icons(a.gf)
    print('konie: %d new items, %d books' % (len(its), len(BOOKS)))


if __name__ == '__main__':
    main()
