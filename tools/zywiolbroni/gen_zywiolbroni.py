#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""gen_zywiolbroni.py [--gf DIR]

MT2009_PLUS_WEAPON_ELEMENT_V1: Zaczarowanie Żywiołu Broni (pl-wiki "Zaczarowanie Żywiołu Broni", "Stróż Medali",
"Zwój Klątwy", "Zwój Zmiany"; based on the "[System] Elemental Spell" package by WorldArd, rewritten for our engine -
server-patches/zywiolbroni). The vnums are the official ones (GF 26.1.11 client item_list / npclist, Owsap's names):

  56002 Zwój Ognia, 56003 Zwój Lodu, 56004 Zwój Błyskawicy, 56005 Zwój Wiatru, 56006 Zwój Ziemi, 56007 Zwój Mroku
        ITEM_USE / 37 (our USE_ELEMENT_UPGRADE - the engine's subtypes end at 36, USE_AFFECT_TARGET), value0 = the
        element's point (POINT_ENCHANT_ELECT..DARK 178-183)
  56008 Zwój Klątwy   ITEM_USE / 38 (USE_ELEMENT_DOWNGRADE)
  56009 Zwój Zmiany   ITEM_USE / 39 (USE_ELEMENT_CHANGE)
        all: stack 200, no drop / trade / NPC sale / private shop / storage / PK drop (the wiki: "nie do handlu z NPC,
        graczem, sklepu, nie do upuszczenia, nie do magazynu")
  20650 Stróż Medali  (client npclist: scholar_brown_M1) - his shop 9560 sells the eight scrolls; on_click 1 (shop)

The prices are linux-port/docker/game/zywiolbroni/weapon_element.txt's (one config place): item_proto.gold of a scroll =
its shop price there (the engine reads the same file and keeps the shop at it, server-patches/zywiolbroni).

Writes (all GENERATED - edit this file or the config, run it again):
  linux-port/docker/mariadb/playerbot/zywiol_broni.sql   world.item_proto / mob_proto / shop / shop_item (INSERT
                                                         IGNORE / REPLACE), player.item_element (IF NOT EXISTS)
  tools/zywiolbroni/zywiolbroni_items.json               the client's records: item_proto rows, item_list, itemdesc,
                                                         the NPC's name (client-patches/client-2.0.30/tools/zywiolbroni)
  client-patches/client-2.0.30/root/icon/item/5600x.tga  the GF icons (= the package's)

Example: python3 tools/zywiolbroni/gen_zywiolbroni.py
"""
import argparse
import json
import os
import shutil
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(os.path.dirname(HERE))
sys.path.insert(0, os.path.join(REPO, 'tools', 'yohara_items'))
import gen_yitems as Y  # noqa: E402  (the item row writer)

M = 'MT2009_PLUS_WEAPON_ELEMENT_V1'
CONFIG = os.path.join(REPO, 'linux-port', 'docker', 'game', 'zywiolbroni', 'weapon_element.txt')
SQL_OUT = os.path.join(REPO, 'linux-port', 'docker', 'mariadb', 'playerbot', 'zywiol_broni.sql')
JSON_OUT = os.path.join(HERE, 'zywiolbroni_items.json')
ICON_OUT = os.path.join(REPO, 'client-patches', 'client-2.0.30', 'root', 'icon', 'item')
GF_DEFAULT = '/opt/metin2/cache/gf/Gameforge_26.1.11/_client'

ITEM_USE = 3
USE_ELEMENT_UPGRADE, USE_ELEMENT_DOWNGRADE, USE_ELEMENT_CHANGE = 37, 38, 39
# antiflags: DROP | SELL | GIVE | PKDROP | MYSHOP | SAFEBOX
ANTI = (1 << 7) | (1 << 8) | (1 << 13) | (1 << 14) | (1 << 16) | (1 << 17)
FLAG = (1 << 2) | (1 << 13)        # ITEM_FLAG_STACKABLE | ITEM_FLAG_LOG (as 71084 and the other scrolls)
NPC = 20650
NPC_NAME = 'Stróż Medali'
SHOP = 9560

# vnum, element (our 1..6: 1 Błyskawica 178, 2 Ogień 179, 3 Lód 180, 4 Wiatr 181, 5 Ziemia 182, 6 Mrok 183), name,
# the element's genitive for the description
SCROLLS = [
    (56002, 2, 'Zwój Ognia', 'Fire Scroll', 'Ognia'),
    (56003, 3, 'Zwój Lodu', 'Ice Scroll', 'Lodu'),
    (56004, 1, 'Zwój Błyskawicy', 'Lightning Scroll', 'Błyskawicy'),
    (56005, 4, 'Zwój Wiatru', 'Wind Scroll', 'Wiatru'),
    (56006, 5, 'Zwój Ziemi', 'Earth Scroll', 'Ziemi'),
    (56007, 6, 'Zwój Mroku', 'Darkness Scroll', 'Mroku'),
]
CURSE = (56008, 'Zwój Klątwy', 'Curse Scroll')
CHANGE = (56009, 'Zwój Zmiany', 'Change Scroll')


def config():
    c = {}
    with open(CONFIG, encoding='ascii') as f:
        for line in f:
            line = line.split('#', 1)[0].split()
            if line:
                c.setdefault(line[0], []).append(line[1:])
    one = lambda k: int(c[k][0][0])  # noqa: E731
    return dict((k, one(k)) for k in ('price_element', 'price_curse', 'price_change', 'fee_element', 'fee_curse',
                                       'fee_change', 'min_refine', 'guild_level_element', 'guild_level_special'))


def money(v):
    return '{:,}'.format(v).replace(',', ' ')


def item(vnum, name, pl, desc, subtype, gold, value0=0):
    d = dict(vnum=vnum, src=vnum, status=Y.ST, name=name, locale_name=pl, type=ITEM_USE, subtype=subtype,
             stack=200, weight=0, size=1, antiflag=ANTI, flag=FLAG, wearflag=0, gold=gold,
             shop_buy_price=0, refined_vnum=0, refine_set=0, magic_pct=0, specular=0, socket_pct=0, addon_type=0,
             limittype0=0, limitvalue0=0, limittype1=0, limitvalue1=0, applytype0=0, applyvalue0=0, applytype1=0,
             applyvalue1=0, applytype2=0, applyvalue2=0, value0=value0, value1=0, value2=0, value3=0, value4=0,
             value5=0, desc=desc, icon='icon/item/%d.tga' % vnum, list_type='ETC')
    assert len(pl.encode('cp1250')) <= 24, pl
    return d


def items(cfg):
    out = []
    for vnum, elem, pl, en, gen in SCROLLS:
        desc = ('Przeciągnij na broń ulepszoną co najmniej do +%d, aby nadać jej Żywioł %s albo podnieść jego poziom '
                '(najwyżej +3; tylko zwojem tego samego żywiołu). Każdy poziom dodaje losową Siłę %s i Wartość Ataku. '
                'Opłata w oknie: %s Yang za próbę. Próba może się nie powieść - broń zostaje nienaruszona.'
                % (cfg['min_refine'], gen, gen, money(cfg['fee_element'])))
        out.append(item(vnum, en, pl, desc, USE_ELEMENT_UPGRADE, cfg['price_element'], 177 + elem))
    fee = (' Opłata w oknie: %s Yang.' % money(cfg['fee_curse'])) if cfg['fee_curse'] else ''
    out.append(item(CURSE[0], CURSE[2], CURSE[1],
                    'Przeciągnij na broń z Zaczarowaniem Żywiołu, aby obniżyć jego poziom o 1 (z +1 żywioł znika '
                    'razem z jego bonusami). Zawsze się udaje.' + fee, USE_ELEMENT_DOWNGRADE, cfg['price_curse']))
    out.append(item(CHANGE[0], CHANGE[2], CHANGE[1],
                    'Przeciągnij na broń z Zaczarowaniem Żywiołu, aby zmienić żywioł na inny. Poziom i wartości '
                    'bonusów zostają. Opłata w oknie: %s Yang. Zawsze się udaje.' % money(cfg['fee_change']),
                    USE_ELEMENT_CHANGE, cfg['price_change']))
    return out


MOB_COLS = ('vnum,name,locale_name,rank,type,battle_type,level,size,ai_flag,mount_capacity,setRaceFlag,setImmuneFlag,'
            'empire,folder,on_click,st,dx,ht,iq,damage_min,damage_max,max_hp,regen_cycle,regen_percent,gold_min,'
            'gold_max,exp,def,attack_speed,move_speed,aggressive_hp_pct,aggressive_sight,attack_range,drop_item,'
            'resurrection_vnum,enchant_curse,enchant_slow,enchant_poison,enchant_stun,enchant_critical,'
            'enchant_penetrate,enchant_fire,enchant_root,resist_sword,resist_twohand,resist_dagger,resist_bell,'
            'resist_fan,resist_bow,resist_fire,resist_elect,resist_magic,resist_wind,resist_poison,dam_multiply,'
            'summon,drain_sp,mob_color,polymorph_item,skill_level0,skill_vnum0,skill_level1,skill_vnum1,skill_level2,'
            'skill_vnum2,skill_level3,skill_vnum3,skill_level4,skill_vnum4,sp_berserk,sp_stoneskin,sp_godspeed,'
            'sp_deathblow,sp_revive')


def mob_row():
    # the set blacksmiths' row (yohara_sets.sql 20475: an NPC of level 1 that does not move), on_click 1 = the shop
    return ("(%d,'Medal Guardian',_cp1250 X'%s',2,1,0,1,'NONE','NOMOVE',0,'','STUN,SLOW,TERROR',0,'',1,0,0,0,0,0,0,"
            "120,3,1,0,0,10,4,100,100,0,2000,150,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0.0,0,0,0,0,0,0,0,0,0,0,"
            "0,0,0,0,0,0,0,0,0,0)" % (NPC, NPC_NAME.encode('cp1250').hex().upper()))


def write_sql(its):
    L = ['-- %s: Zaczarowanie Żywiołu Broni (the owner, 29 October 2026) - GENERATED by' % M,
         '-- tools/zywiolbroni/gen_zywiolbroni.py, do not edit, rerun it. Every start (apply.sh), idempotent.',
         '-- The official vnums (GF 26.1.11 / Owsap names): 56002-56007 the element scrolls (ITEM_USE / 37, value0 = the',
         '-- element point 178-183), 56008 Zwój Klątwy (38), 56009 Zwój Zmiany (39) - no drop / trade / NPC sale / shop /',
         '-- storage; 20650 Stróż Medali (an NPC whose click opens shop %d) on the guild lands - npc.txt of' % SHOP,
         '-- metin2_map_guild_01..03 (the Dockerfile). The prices: game/zywiolbroni/weapon_element.txt (the engine keeps',
         '-- the shop at them; item_proto.gold is the same number). Each vnum was free in world.item_proto / mob_proto',
         '-- and shop %d in world.shop (29 October 2026).' % SHOP,
         '-- player.item_element: each enchanted weapon (or the sash that absorbed it) by item id - the element (1',
         '-- Błyskawica .. 6 Mrok), the level 0-3 and the values each level rolled (server-patches/zywiolbroni reads it',
         '-- when the item loads, writes it when it changes; player.item is not touched).',
         'SET NAMES utf8mb4;',
         'INSERT IGNORE INTO world.item_proto (%s) VALUES' % ','.join('`%s`' % c for c in Y.COLS),
         ',\n'.join(Y.sqlrow(i) for i in its) + ';',
         '-- a row made by an earlier run keeps up with the config prices (the operator changes them in weapon_element.txt)']
    for i in its:
        L.append('UPDATE world.item_proto SET gold=%d WHERE vnum=%d AND gold<>%d;' % (i['gold'], i['vnum'], i['gold']))
    L += ['INSERT IGNORE INTO world.mob_proto (%s) VALUES' % MOB_COLS,
          mob_row() + ';',
          "REPLACE INTO world.shop (`vnum`,`name`,`npc_vnum`) VALUES (%d,'Straznik Medali - Zwoje Zywiolow',%d);"
          % (SHOP, NPC),
          'DELETE FROM world.shop_item WHERE shop_vnum = %d;' % SHOP,
          'INSERT INTO world.shop_item (`shop_vnum`,`item_vnum`,`count`) VALUES %s;'
          % ','.join('(%d,%d,1)' % (SHOP, i['vnum']) for i in its),
          'CREATE TABLE IF NOT EXISTS player.item_element (',
          '  id INT UNSIGNED NOT NULL PRIMARY KEY,',
          '  type TINYINT UNSIGNED NOT NULL DEFAULT 0,',
          '  grade TINYINT UNSIGNED NOT NULL DEFAULT 0,',
          '  att0 TINYINT UNSIGNED NOT NULL DEFAULT 0, att1 TINYINT UNSIGNED NOT NULL DEFAULT 0,'
          ' att2 TINYINT UNSIGNED NOT NULL DEFAULT 0,',
          '  pow0 TINYINT UNSIGNED NOT NULL DEFAULT 0, pow1 TINYINT UNSIGNED NOT NULL DEFAULT 0,'
          ' pow2 TINYINT UNSIGNED NOT NULL DEFAULT 0',
          ') ENGINE=InnoDB;']
    with open(SQL_OUT, 'w', encoding='utf-8', newline='\n') as f:
        f.write('\n'.join(L) + '\n')


def write_json(its):
    keys = ('vnum', 'name', 'locale_name', 'type', 'subtype', 'stack', 'weight', 'size', 'antiflag', 'flag',
            'wearflag', 'gold', 'shop_buy_price', 'refined_vnum', 'refine_set', 'magic_pct', 'specular', 'socket_pct',
            'limittype0', 'limitvalue0', 'limittype1', 'limitvalue1', 'applytype0', 'applyvalue0', 'applytype1',
            'applyvalue1', 'applytype2', 'applyvalue2', 'value0', 'value1', 'value2', 'value3', 'value4', 'value5')
    out = {'items': [dict((k, i[k]) for k in keys) for i in its],
           'item_list': dict((str(i['vnum']), '%d\t%s\t%s' % (i['vnum'], i['list_type'], i['icon'])) for i in its),
           'itemdesc': dict((str(i['vnum']), '%d\t%s\t%s' % (i['vnum'], i['locale_name'], Y.client_desc(i)))
                            for i in its),
           'npc': {'vnum': NPC, 'name': NPC_NAME, 'npclist': 'scholar_brown_M1', 'shop': SHOP}}
    with open(JSON_OUT, 'w', encoding='utf-8', newline='\n') as f:
        json.dump(out, f, ensure_ascii=False, indent=0)
        f.write('\n')


def copy_icons(its, gf):
    os.makedirs(ICON_OUT, exist_ok=True)
    for i in its:
        src = os.path.join(gf, 'icon', 'item', '%d.tga' % i['vnum'])
        assert os.path.isfile(src), src
        dst = os.path.join(ICON_OUT, '%d.tga' % i['vnum'])
        if not os.path.isfile(dst) or open(dst, 'rb').read() != open(src, 'rb').read():
            shutil.copyfile(src, dst)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--gf', default=GF_DEFAULT)
    a = ap.parse_args()
    cfg = config()
    its = items(cfg)
    write_sql(its)
    write_json(its)
    if os.path.isdir(a.gf):
        copy_icons(its, a.gf)
    print('zywiolbroni: %d items, NPC %d, shop %d' % (len(its), NPC, SHOP))


if __name__ == '__main__':
    main()
