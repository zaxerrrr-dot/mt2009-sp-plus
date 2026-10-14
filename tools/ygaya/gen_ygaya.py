#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""gen_ygaya.py [--owsap DIR] [--gf DIR]

MT2009_PLUS_GAYA_V1: Kamienie Gaya and the rest of Statua Wojownika (the owner, 14 October 2026, cache/yohara/
decyzje.md "14.10 ok. 8:10": "Kamienie Gaya - dodac", "Statua Wojownika - pozostale funkcje BEZ Tarczy Potepienia i
BEZ peta Feniks Ocalenia"), as the pl-wiki gives them ("Gaya", "System Gaya", "Kamyki", "Statua Wojownika",
"Portowy Sklep Gaya", "Wytwarzanie Skrzyn Zwierzakow"), with the official vnums and numbers of Owsap v6.2.6
(db/item_proto.txt, share/locale/uk/cube.txt "gem", gem_shop_table.txt), its Polish client's names and texts and the
GF 26.1.11 client's icons - the method of tools/yohara_maps4/gen_yitems4.py:

  95927 Gaya                       the currency as an item (our exe has no Gaya point / window): it cannot be
                                   dropped, sold, given or put in a shop (wiki: no trade between players), a stack
                                   holds the wiki's maximum 999 999; ground from 30 Kamyki (95926) + a Kamien Duszy
                                   +0..+3 + 15 000 Yang at Statua Wojownika - 70%, 3 Gaya (quest ygaya); spent in
                                   the cube ("gaya N", server-patches/gaya) and by the quests (Portowy Sklep Gaya,
                                   Tajemniczy Oltarz, Mistrz Chi); the icon is GF's icon/item/gem.tga;
  39063 Reset Sklepu Gaya          a new offer of the Gaya shop before the 5 hours (quest ygaya);
  39064 Rozszerzenie Sklepu Gaya   unlocks the shop's slots 4/5/6 (1/2/4 of them, for good - quest ygaya).

The elemental pet chests (53581-53586) and Kupon Zwierzaka Zywiolu (39117) are gone (the owner, 14 October 2026,
decyzje.md: "usunac Skrzynie Zywiolakow ze Statui Wojownika (pet tylko w ItemShopie)") - no recipe, no chest, no
coupon; the elemental pet is sold in the ItemShop only, as before.

Writes (all GENERATED - edit this file, run it again):
  linux-port/docker/mariadb/playerbot/yohara_gaya.sql             world.item_proto (INSERT IGNORE) + Kamyki's flags
  tools/ygaya/ygaya_items.json                                    the client's records, item_list, itemdesc
  client-patches/client-2.0.30/root/icon/item/<vnum>.tga          the GF icons

Example: python3 tools/ygaya/gen_ygaya.py
"""
import argparse
import json
import os
import shutil
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(os.path.dirname(HERE))
sys.path.insert(0, os.path.join(REPO, 'tools', 'yohara_items'))
import gen_yitems as Y  # noqa: E402  (the engine's numbers, the row writer)

SQL_OUT = os.path.join(REPO, 'linux-port', 'docker', 'mariadb', 'playerbot', 'yohara_gaya.sql')
JSON_OUT = os.path.join(HERE, 'ygaya_items.json')
ICON_OUT = os.path.join(REPO, 'client-patches', 'client-2.0.30', 'root', 'icon', 'item')

GAYA = 95927
GAYA_MAX = 999999                                # wiki "Gaya": "Gracz moze posiadac maksymalnie 999.999 Gaya"
KAMYKI = 95926                                   # tools/yohara_items/gen_yitems.py (Owsap 50926 is our recipe)
A = Y.ANTI
F = Y.FLAGS
NO_TRADE = A['ANTI_DROP'] | A['ANTI_SELL'] | A['ANTI_GIVE'] | A['ANTI_PKDROP'] | A['ANTI_MYSHOP']
# Kamyki (wiki: player trade yes, NPC no, shop no, drop yes) - Owsap's ANTI_PKDROP | ANTI_MYSHOP now that it works
KAMYKI_ANTI = A['ANTI_PKDROP'] | A['ANTI_MYSHOP']
# no pet chests / coupon any more (the owner, 14 October 2026): 39117 and 53581-53586 stay free


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--owsap', default='/opt/metin2/cache/owsap')
    ap.add_argument('--gf', default='/opt/metin2/cache/gf/Gameforge_26.1.11/_client')
    a = ap.parse_args()
    rows = Y.read_tsv(os.path.join(a.owsap, 'Server/Server/db/item_proto.txt'))
    head = rows[0]
    proto = dict((int(r[0]), dict(zip(head, r))) for r in rows[1:] if r and r[0].isdigit())
    desc = {}
    for r in Y.read_tsv(os.path.join(a.owsap, 'Client/Client/pack/locale/locale/pl/itemdesc.txt')):
        if len(r) >= 2 and r[0].strip().isdigit():
            desc[int(r[0])] = (r[1].strip(), r[2].strip() if len(r) > 2 else '')
    items, icons = [], {}

    def item(vnum, name, text, typ, sub, stack, anti, flag, icon_src, **kw):
        d = dict(vnum=vnum, src=vnum, status=Y.ST, name=Y.ascii_name(name), locale_name=name, type=typ, subtype=sub,
                 stack=stack, weight=0, size=1, antiflag=anti, flag=flag, wearflag=0, gold=0, shop_buy_price=0,
                 refined_vnum=0, refine_set=0, magic_pct=0, specular=0, socket_pct=0, addon_type=0,
                 limittype0=0, limitvalue0=0, limittype1=0, limitvalue1=0, applytype0=0, applyvalue0=0,
                 applytype1=0, applyvalue1=0, applytype2=0, applyvalue2=0, value0=0, value1=0, value2=0, value3=0,
                 value4=0, value5=0, desc=text, icon='icon/item/%d.tga' % vnum, list_type='ETC')
        d.update(kw)
        assert len(name.encode('cp1250')) <= 32, name
        items.append(d)
        icons['%d.tga' % vnum] = icon_src

    item(GAYA, u'Gaya', u'Drogocenna waluta Yohary. Oszlifuj 30 Kamyków u Statuy Wojownika w Porcie Nowego '
         u'Kontynentu (z Kamieniem Duszy +0 do +3 i 15 000 Yang - szansa 70%), a otrzymasz 3 Gaya. Płacisz nią '
         u'w Portowym Sklepie Gaya, u kowali zestawów, u Statuy Węży, Tajemniczego Ołtarza i Mistrza Chi. '
         u'Nie można jej wymieniać z innymi graczami.',
         Y.TYPES['ITEM_MATERIAL'], 0, GAYA_MAX, NO_TRADE, F['ITEM_STACKABLE'], 'gem.tga')
    for v in (39063, 39064):
        o = proto[v]
        assert o['Type'] == 'ITEM_USE' and 'ANTI_MYSHOP' in o['AntiFlags'], v
        pl, text = desc[v]
        # a quest item here (the shop of quest ygaya takes it); Owsap's flags: no drop, no shop
        item(v, pl, text + u' Użyj w Portowym Sklepie Gaya (Statua Wojownika w Porcie Nowego Kontynentu).',
             Y.TYPES['ITEM_QUEST'], 0, 200, Y.flags(o['AntiFlags'], A, 'antiflag'),
             F['ITEM_STACKABLE'] | F['ITEM_QUEST_USE'], '%d.tga' % v)
    assert len(items) == 3
    write_sql(items)
    write_json(items)
    copy_icons(icons, a.gf)
    print('items %d (Gaya %d, the shop\'s Reset / Rozszerzenie)' % (len(items), GAYA))


def write_sql(items):
    L = ['-- MT2009_PLUS_GAYA_V1: Gaya (95927, the currency as an item), Reset / Rozszerzenie Sklepu Gaya (39063/39064)',
         '-- - the owner, 14 October 2026 (cache/yohara/decyzje.md "14.10 ok. 8:10": Kamienie Gaya, Statua Wojownika;',
         '-- later that day: no elemental pet chests / Kupon Zwierzaka Zywiolu - the pet is in the ItemShop only). GENERATED by',
         '-- tools/ygaya/gen_ygaya.py - do not edit, rerun it. Every start (apply.sh), idempotent: INSERT IGNORE - a row',
         '-- the operator changed is kept. Source: the pl-wiki ("Gaya", "System Gaya", "Kamyki", "Wytwarzanie Skrzyn',
         '-- Zwierzakow") and Owsap v6.2.6 db/item_proto.txt (the official vnums and flags), the Polish names of its',
         '-- Polish client. Every vnum was free in our world (14 October 2026, the test server). Gaya cannot be traded',
         '-- (no drop / sale / give / shop), a stack holds 999 999 (the wiki\'s maximum). Kamyki (95926, MT2009_PLUS_',
         '-- YOHARA_ITEMS1_V1) work now: Owsap\'s flags (no shop, no PK drop) instead of the "no system yet" ones.',
         'SET NAMES utf8mb4;',
         'INSERT IGNORE INTO world.item_proto (%s) VALUES' % ','.join('`%s`' % c for c in Y.COLS),
         ',\n'.join(Y.sqlrow(i) for i in items) + ';',
         'UPDATE world.item_proto SET antiflag=%d WHERE vnum=%d AND antiflag<>%d;' % (KAMYKI_ANTI, KAMYKI, KAMYKI_ANTI)]
    with open(SQL_OUT, 'w', encoding='utf-8', newline='\n') as f:
        f.write('\n'.join(L) + '\n')


def write_json(items):
    keys = ('vnum', 'name', 'locale_name', 'type', 'subtype', 'stack', 'weight', 'size', 'antiflag', 'flag',
            'wearflag', 'gold', 'shop_buy_price', 'refined_vnum', 'refine_set', 'magic_pct', 'specular', 'socket_pct',
            'limittype0', 'limitvalue0', 'limittype1', 'limitvalue1', 'applytype0', 'applyvalue0', 'applytype1',
            'applyvalue1', 'applytype2', 'applyvalue2', 'value0', 'value1', 'value2', 'value3', 'value4', 'value5')
    out = {'items': [dict((k, i[k]) for k in keys) for i in items],
           'item_list': dict((str(i['vnum']), '%d\t%s\t%s' % (i['vnum'], i['list_type'], i['icon'])) for i in items),
           'itemdesc': dict((str(i['vnum']), '%d\t%s\t%s' % (i['vnum'], i['locale_name'], Y.client_desc(i)))
                            for i in items),
           # Kamyki's record and line (tools/yohara_items/yohara_items.json has them too - the same values)
           'kamyki_antiflag': KAMYKI_ANTI}
    with open(JSON_OUT, 'w', encoding='utf-8', newline='\n') as f:
        json.dump(out, f, ensure_ascii=False, indent=0)
        f.write('\n')


def copy_icons(icons, gf):
    os.makedirs(ICON_OUT, exist_ok=True)
    for dst, src in sorted(icons.items()):
        s = os.path.join(gf, 'icon', 'item', src)
        assert os.path.isfile(s), s
        shutil.copyfile(s, os.path.join(ICON_OUT, dst))


if __name__ == '__main__':
    main()
