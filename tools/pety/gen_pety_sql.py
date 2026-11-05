#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""MT2009_PLUS_GROWTH_PET_V1 - writes, from tools/pety/pety_data.py:
  linux-port/docker/mariadb/playerbot/pety.sql            the tables, the items, the mobs, the skill proto, the migration
  linux-port/overlays/playerbot/src/game/src/growth_pet_data.h   the same tables for the game (C++)
  tools/pety/pety_items.json                               the item records for the client pack builder
Run from anywhere: python3 tools/pety/gen_pety_sql.py [--check]  (--check: fail when a written file would change)."""
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.abspath(os.path.join(HERE, '..', '..'))
sys.path.insert(0, HERE)
import pety_data as D  # noqa: E402

SQL_OUT = os.path.join(REPO, 'linux-port/docker/mariadb/playerbot/pety.sql')
H_OUT = os.path.join(REPO, 'linux-port/overlays/playerbot/src/game/src/growth_pet_data.h')
JSON_OUT = os.path.join(HERE, 'pety_items.json')

ITEM_PET, ITEM_MATERIAL, ITEM_GIFTBOX = 37, 5, 23
PET_EGG, PET_UPBRINGING, PET_BAG, PET_FEEDSTUFF, PET_SKILL, PET_SKILL_DEL_BOOK, PET_NAME_CHANGE, PET_EXPFOOD, \
    PET_SKILL_ALL_DEL_BOOK, PET_EXPFOOD_PER, PET_ATTR_DETERMINE, PET_ATTR_CHANGE, PET_PAY, PET_PRIMIUM_FEEDSTUFF = range(14)
A_DROP, A_SELL, A_GIVE, A_PKDROP, A_STACK, A_MYSHOP = 1 << 7, 1 << 8, 1 << 13, 1 << 14, 1 << 15, 1 << 16
F_STACK = 1 << 2
LIMIT_REAL_TIME = 7

MIGRATED_ID_BASE = 0xF0000000   # pet ids of the old system's pets (never an item id)
NAMES_MARKER = 'pety:names_v1'  # the items' names (pl-wiki) put on an existing world once; bump on a rename
# The owner's Yohara list 3.0.14, item 3: the treats stack to 200 like the other pet consumables (Smakolyk 55028,
# Smakolyk+ 55031; Smaczny Smakolyk 55042 already did). A world that wrote pety:items_v1 gets the new stack / flags once.
STACK_MARKER = 'pety:stack_v2'
STACK_VNUMS = (55028, 55031)
# Item 9: Zaczaruj zwierzaka 55033 as a Battle Pass reward (pl-wiki: "System przepustki bojowej") - the third reward of
# the last mission of the seeded Metin / monster / fish chains (6, 9, 12), once and only where that reward is free.
BP_MARKER = 'pety:bp_enchant_v1'
BP_MISSIONS = (6, 9, 12)


def item(vnum, name, desc, type_, subtype, stack=200, antiflag=0, gold=0, sell=0, limit=(0, 0), values=(0,) * 6,
         icon=None):
    flag = F_STACK if stack > 1 else 0
    if stack <= 1:
        stack = 1
        antiflag |= A_STACK
    v = list(values) + [0] * (6 - len(values))
    return dict(vnum=vnum, name=name, desc=desc, type=type_, subtype=subtype, stack=stack, antiflag=antiflag, flag=flag,
                gold=gold, shop_buy_price=sell, limittype0=limit[0], limitvalue0=limit[1], values=v,
                icon=icon or ('icon/item/%d.tga' % vnum))


def items():
    out = []
    out.append(item(55001, u"Odżywka",
                    u"Przeciągnij na pieczęć zwierzaka: odnawia czas trwania do 100%. Martwego zwierzaka ożywia "
                    u"(50% czasu trwania, wiek od nowa). Potrzebna też do rozwoju zwierzaka.",
                    ITEM_PET, PET_FEEDSTUFF, gold=50000, sell=500))
    out.append(item(55002, u"Klatka Transportowa",
                    u"Przeciągnij pieczęć zwierzaka na klatkę: zwierzak może zmienić właściciela przez 30 dni i nie "
                    u"starzeje się w klatce. Prawy przycisk myszy na klatce ze zwierzakiem wyjmuje go.",
                    ITEM_PET, PET_BAG, stack=1, antiflag=A_SELL | A_MYSHOP | A_DROP | A_PKDROP))
    books = [(55003, u"Księga Młodego Zwierza", u"Dziki"), (55004, u"Księga Dzikiego Zwierza", u"Dzielny"),
             (55005, u"Księga Dzielnego Zwierza", u"Bohaterski"), (55006, u"Bohat. Księga Zwierza", u"Przebudzony"),
             (55007, u"Przeb. Księga Zwierza", u"Mocny")]
    for vnum, name, stage in books:
        out.append(item(vnum, name, u"Potrzebna do rozwoju zwierzaka domowego do stopnia „%s”." % stage,
                        ITEM_MATERIAL, 0, gold=10000, sell=1000))
    out.append(item(55008, u"Pergamin Nazwy Zwierzaka",
                    u"Zmienia imię zwierzaka domowego (100.000 Yang).", ITEM_PET, PET_NAME_CHANGE,
                    antiflag=A_GIVE | A_MYSHOP | A_DROP | A_PKDROP))
    out.append(item(55009, u"Skrzynia Ksiąg Zwierza", u"Zawiera jedną losową księgę umiejętności zwierzaka.",
                    ITEM_GIFTBOX, 0, gold=10000, sell=1000))
    for sid in sorted(D.SKILLS):
        s = D.SKILLS[sid]
        out.append(item(s[8], s[7], u"Uczy zwierzaka (od stopnia „Bohaterski”) umiejętności „%s”: %s" % (s[0], s[9]),
                        ITEM_PET, PET_SKILL, stack=1, values=(sid,), gold=10000, sell=1000,
                        icon='icon/item/%d.tga' % (55011 if s[2] == D.AUTO else 55012)))
    out.append(item(55028, u"Smakołyk", u"Daje zwierzakowi 80.000 PD przedmiotu (okno „Przedmiot EXP”).",
                    ITEM_PET, PET_EXPFOOD, antiflag=A_SELL | A_DROP | A_PKDROP, values=(80000,)))
    out.append(item(55029, u"Reverti Zwierza", u"Usuwa wszystkie umiejętności zwierzaka (prawy przycisk myszy przy "
                    u"otwartym oknie zwierzaka).", ITEM_PET, PET_SKILL_ALL_DEL_BOOK))
    out.append(item(55030, u"Revertus Zwierza", u"Usuwa jedną wybraną umiejętność zwierzaka (przeciągnij na "
                    u"umiejętność).", ITEM_PET, PET_SKILL_DEL_BOOK))
    out.append(item(55031, u"Smakołyk+", u"Daje zwierzakowi 5% PD przedmiotu potrzebnych do następnego poziomu.",
                    ITEM_PET, PET_EXPFOOD_PER, antiflag=A_SELL | A_DROP | A_PKDROP, values=(5,)))
    out.append(item(55032, u"Sfera Losu Zwierzaka", u"Pokazuje typ zwierzaka (przycisk „Sfera losu” w oknie "
                    u"zwierzaka).", ITEM_PET, PET_ATTR_DETERMINE, gold=10000, sell=1000, icon='icon/item/55033.tga'))
    out.append(item(55033, u"Zaczaruj zwierzaka", u"Losuje od nowa typ zwierzaka (1-8), jego czas trwania i - gdy "
                    u"nie zna umiejętności - liczbę miejsc na umiejętności.", ITEM_PET, PET_ATTR_CHANGE,
                    antiflag=A_DROP | A_PKDROP, icon='icon/item/55032.tga'))
    out.append(item(55042, u"Smaczny Smakołyk", u"Prawy przycisk myszy: 200.000 PD dla zwierzaka (poziom 1-105) albo "
                    u"1.200 PD czempiona dla zwierzaka z poziomem czempiona.", ITEM_PET, PET_EXPFOOD,
                    values=(200000, 1200, 1), icon='icon/item/55040.tga'))
    out.append(item(55100, u"Boska Odżywka", u"Ożywia martwego zwierzaka z pełnym czasem trwania; zachowuje 80% "
                    u"wieku (zakładka „Wskrzeszanie” okna innego, żywego zwierzaka).", ITEM_PET, PET_PRIMIUM_FEEDSTUFF,
                    antiflag=A_DROP | A_PKDROP))
    out.append(item(55400, u"Skrzynka na Zwierzaka", u"Zawiera losowe jajo zwierzaka domowego.", ITEM_GIFTBOX, 0,
                    gold=10000, sell=1000))
    for sp in D.SPECIES:
        idx, egg, seal, pet, eggname, young, hero, champ, hatch, enchant, slots, maxtype = sp
        out.append(item(egg, eggname, u"Prawy przycisk myszy: wykluwa zwierzaka „%s” (100.000 Yang i imię). Jajo "
                        u"można też dać zwierzakowi do jedzenia albo włożyć w miejsce potencjału zwierzaka czempiona."
                        % pet, ITEM_PET, PET_EGG, stack=1, limit=(LIMIT_REAL_TIME, D.EGG_LIFE_SECONDS),
                        values=(seal, 0, 0, D.HATCH_PRICE), gold=10000, sell=5000))
        out.append(item(seal, u"%s (pieczęć)" % pet, u"Prawy przycisk myszy: przywołuje albo odwołuje zwierzaka.",
                        ITEM_PET, PET_UPBRINGING, stack=1, antiflag=A_GIVE | A_MYSHOP | A_DROP | A_PKDROP,
                        values=(young, 0, 0, hero, champ)))
    return out


def mobs():
    out = []
    for sp in D.SPECIES:
        idx, egg, seal, pet = sp[:4]
        for vnum in sp[5:8]:
            out.append((vnum, pet))
    return out


def cp1250_hex(text):
    return "_cp1250 X'%s'" % text.encode('cp1250').hex().upper()


def ascii_name(text):
    import unicodedata
    t = unicodedata.normalize('NFKD', text.replace(u'ł', 'l').replace(u'Ł', 'L'))
    return ''.join(c for c in t if ord(c) < 128)[:32].replace("'", '')


COLS = ("`vnum`,`name`,`locale_name`,`type`,`subtype`,`stack`,`weight`,`size`,`antiflag`,`flag`,`wearflag`,"
        "`immuneflag`,`gold`,`shop_buy_price`,`refined_vnum`,`refine_set`,`magic_pct`,`specular`,`socket_pct`,"
        "`addon_type`,`limittype0`,`limitvalue0`,`limittype1`,`limitvalue1`,`applytype0`,`applyvalue0`,`applytype1`,"
        "`applyvalue1`,`applytype2`,`applyvalue2`,`value0`,`value1`,`value2`,`value3`,`value4`,`value5`,`socket0`,"
        "`socket1`,`socket2`,`socket3`,`socket4`,`socket5`")


def item_row(it):
    v = it['values']
    return ("(%d,'%s',%s,%d,%d,%d,0,1,%d,%d,0,'',%d,%d,0,0,0,0,0,0,%d,%d,0,0,0,0,0,0,0,0,%d,%d,%d,%d,%d,%d,0,0,0,0,0,0)"
            % (it['vnum'], ascii_name(it['name']), cp1250_hex(it['name']), it['type'], it['subtype'], it['stack'],
               it['antiflag'], it['flag'], it['gold'], it['shop_buy_price'], it['limittype0'], it['limitvalue0'],
               v[0], v[1], v[2], v[3], v[4], v[5]))


def gen_sql():
    its = items()
    L = []
    w = L.append
    w("-- MT2009_PLUS_GROWTH_PET_V1: System Zwierzat Domowych (server-patches/pety/README.md). GENERATED by")
    w("-- tools/pety/gen_pety_sql.py from tools/pety/pety_data.py - edit those, not this file. Run by apply.sh at every start;")
    w("-- idempotent. The one-time steps keep their marker in player.playerbot_migrations ('pety:...').")
    w("SET NAMES utf8mb4;")
    w("")
    w("-- The pets (one row a pet; its id is socket 2 of its seal or of the Klatka Transportowa it travels in). state:")
    w("-- 1 in a seal, 2 in a cage, 3 an old-system pet waiting for its seal (given at the owner's next login).")
    w("CREATE TABLE IF NOT EXISTS player.growth_pet (")
    w("\tid INT UNSIGNED NOT NULL PRIMARY KEY,")
    w("\towner_id INT UNSIGNED NOT NULL DEFAULT 0,")
    w("\tvnum INT UNSIGNED NOT NULL DEFAULT 0,")
    w("\tstate TINYINT UNSIGNED NOT NULL DEFAULT 1,")
    w("\tname VARBINARY(24) NOT NULL DEFAULT '',")
    w("\tsize TINYINT UNSIGNED NOT NULL DEFAULT 0,")
    w("\tlevel SMALLINT UNSIGNED NOT NULL DEFAULT 1,")
    w("\tlevel_step TINYINT UNSIGNED NOT NULL DEFAULT 0,")
    w("\tevolution TINYINT UNSIGNED NOT NULL DEFAULT 1,")
    w("\ttype TINYINT UNSIGNED NOT NULL DEFAULT 0,")
    w("\thp INT UNSIGNED NOT NULL DEFAULT 0, sp INT UNSIGNED NOT NULL DEFAULT 0, def INT UNSIGNED NOT NULL DEFAULT 0,")
    w("\thp_apply INT UNSIGNED NOT NULL DEFAULT 0, sp_apply INT UNSIGNED NOT NULL DEFAULT 0,")
    w("\tdef_apply INT UNSIGNED NOT NULL DEFAULT 0, age_apply INT UNSIGNED NOT NULL DEFAULT 0,")
    w("\tskill0_lock TINYINT UNSIGNED NOT NULL DEFAULT 1, skill0 TINYINT UNSIGNED NOT NULL DEFAULT 0,")
    w("\tskill0_level TINYINT UNSIGNED NOT NULL DEFAULT 0,")
    w("\tskill1_lock TINYINT UNSIGNED NOT NULL DEFAULT 1, skill1 TINYINT UNSIGNED NOT NULL DEFAULT 0,")
    w("\tskill1_level TINYINT UNSIGNED NOT NULL DEFAULT 0,")
    w("\tskill2_lock TINYINT UNSIGNED NOT NULL DEFAULT 1, skill2 TINYINT UNSIGNED NOT NULL DEFAULT 0,")
    w("\tskill2_level TINYINT UNSIGNED NOT NULL DEFAULT 0,")
    w("\texp BIGINT UNSIGNED NOT NULL DEFAULT 0, item_exp BIGINT UNSIGNED NOT NULL DEFAULT 0,")
    w("\tbirthday INT UNSIGNED NOT NULL DEFAULT 0, end_time INT UNSIGNED NOT NULL DEFAULT 0,")
    w("\tmax_time INT UNSIGNED NOT NULL DEFAULT 0,")
    w("\ttype_known TINYINT UNSIGNED NOT NULL DEFAULT 0,")
    w("\tchampion_level TINYINT UNSIGNED NOT NULL DEFAULT 0, champion_exp BIGINT UNSIGNED NOT NULL DEFAULT 0,")
    w("\tchampion_item_exp BIGINT UNSIGNED NOT NULL DEFAULT 0,")
    w("\tchamp_res INT UNSIGNED NOT NULL DEFAULT 0, champ_block INT UNSIGNED NOT NULL DEFAULT 0,")
    w("\tchamp_prec INT UNSIGNED NOT NULL DEFAULT 0, champ_res_apply INT UNSIGNED NOT NULL DEFAULT 0,")
    w("\tchamp_block_apply INT UNSIGNED NOT NULL DEFAULT 0, champ_prec_apply INT UNSIGNED NOT NULL DEFAULT 0,")
    w("\tpot0_egg INT UNSIGNED NOT NULL DEFAULT 0, pot0_skill TINYINT UNSIGNED NOT NULL DEFAULT 0,")
    w("\tpot0_end INT UNSIGNED NOT NULL DEFAULT 0, pot1_egg INT UNSIGNED NOT NULL DEFAULT 0,")
    w("\tpot1_skill TINYINT UNSIGNED NOT NULL DEFAULT 0, pot1_end INT UNSIGNED NOT NULL DEFAULT 0,")
    w("\tupdated TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,")
    w("\tKEY owner_state (owner_id, state)")
    w(") ENGINE=InnoDB DEFAULT CHARSET=cp1250;")
    w("")
    w("-- The skill proto (the wiki's tables; read by the db core at boot and sent to every game core). pet_vnum 0 = every")
    w("-- species; a species row overrides it (its specialty). value_t1..t8 = the skill level 20 value at pet level 105")
    w("-- per pet type; level_curve = the values of skill levels 1..20 at pet level 105 without a specialty; grow_levels =")
    w("-- the pet levels at which a level-20 value grows by one unit (empty = continuously, 80 % at 81); activate = the")
    w("-- chance (%) of an auto skill by skill level; duration = tenths of a second by skill level.")
    w("CREATE TABLE IF NOT EXISTS player.growth_pet_skill_proto (")
    w("\tpet_vnum INT UNSIGNED NOT NULL DEFAULT 0,")
    w("\tskill_vnum TINYINT UNSIGNED NOT NULL,")
    w("\tname VARBINARY(32) NOT NULL DEFAULT '',")
    w("\ttype ENUM('NONE','PASSIVE','AUTO') NOT NULL DEFAULT 'PASSIVE',")
    w("\tcooldown INT UNSIGNED NOT NULL DEFAULT 0,")
    w("\tpoint_on VARCHAR(64) NOT NULL DEFAULT '',")
    w("\tunit VARCHAR(8) NOT NULL DEFAULT '%10',")
    for t in range(1, 9):
        w("\tvalue_t%d INT UNSIGNED NOT NULL DEFAULT 0," % t)
    w("\tlevel_curve VARCHAR(160) NOT NULL DEFAULT '',")
    w("\tgrow_levels VARCHAR(160) NOT NULL DEFAULT '',")
    w("\tactivate VARCHAR(100) NOT NULL DEFAULT '',")
    w("\tduration VARCHAR(100) NOT NULL DEFAULT '',")
    w("\tPRIMARY KEY (pet_vnum, skill_vnum)")
    w(") ENGINE=InnoDB DEFAULT CHARSET=cp1250;")
    w("")
    # ---- the migration (before the items change their meaning) ----
    w("-- ---- One time: the old New Pet System (MT2009_PLUS_NEW_PET_V1, player.newpet_pet) -> growth pets ----------------")
    w("-- (the owner's decisions of 4 November 2026: species, name and level kept; the type rolled as at a hatching (the")
    w("-- game finalises a state-3 row when it hands out the seal); the skills are not carried over.) Every old pet item")
    w("-- in the bags, the storerooms, the shops (Ikarus), the item awards and the ItemShop becomes a wiki item (the")
    w("-- mapping: server-patches/pety/README.md). One transaction: all or nothing; the marker last.")
    w("DELIMITER //")
    w("BEGIN NOT ATOMIC")
    w("\tDECLARE has_old INT DEFAULT 0;")
    w("\tDECLARE EXIT HANDLER FOR SQLEXCEPTION BEGIN ROLLBACK; RESIGNAL; END;")
    w("\tIF (SELECT COUNT(*) FROM player.playerbot_migrations WHERE name = 'pety:migracja_v1') = 0 THEN")
    w("\t\tSELECT COUNT(*) INTO has_old FROM information_schema.TABLES WHERE TABLE_SCHEMA = 'player' AND TABLE_NAME = 'newpet_pet';")
    w("\t\tSTART TRANSACTION;")
    w("\t\tIF has_old > 0 THEN")
    w("\t\t\t-- the pets: id 0xF0000000 + the old id, state 3 (a seal at the next login) or 2 (packed in a transporter)")
    w("\t\t\tINSERT IGNORE INTO player.growth_pet (id, owner_id, vnum, state, name, level, evolution, type, birthday,")
    w("\t\t\t\t\tend_time, max_time)")
    w("\t\t\tSELECT %d + n.id, IF(n.packed, 0, n.pid), n.egg + 300, IF(n.packed, 2, 3), n.name, LEAST(GREATEST(n.level, 1), 105)," % MIGRATED_ID_BASE)
    w("\t\t\t\t\tCASE WHEN n.level >= 81 AND n.evolution >= 3 THEN 4 WHEN n.level >= 81 THEN 3 WHEN n.level >= 41 THEN 2 ELSE 1 END,")
    w("\t\t\t\t\t0, IF(n.created > 0, n.created, UNIX_TIMESTAMP()), 0, 0")
    w("\t\t\tFROM player.newpet_pet n WHERE n.egg BETWEEN 55401 AND 55414;")
    w("\t\t\t-- a transporter with a pet (55007, socket0 = the old id) -> Klatka Transportowa with the pet (30 days)")
    w("\t\t\tUPDATE player.item SET socket2 = IF(socket0 > 0, %d + socket0, 0), socket0 = IF(socket0 > 0, UNIX_TIMESTAMP() + %d, 0)," % (MIGRATED_ID_BASE, D.BAG_LIFE_SECONDS))
    w("\t\t\t\tsocket1 = IF(socket0 > 0, UNIX_TIMESTAMP(), 0), vnum = 55002, count = 1 WHERE vnum = 55007;")
    w("\t\t\t-- (player.newpet_pet stays as it was - nothing reads it any more; a backup of the old pets)")
    w("\t\tEND IF;")
    mapping = OLD_ITEM_MAP
    w("\t\t-- the old items (counts multiplied where one old item is several new ones)")
    for old, (new, mult, _why) in sorted(mapping.items()):
        if new == old and mult == 1:
            continue
        for tbl in ('player.item', 'player.item_award'):
            if new:
                w("\t\tUPDATE %s SET vnum = %d, count = count * %d WHERE vnum = %d;" % (tbl, new, mult, old))
            else:
                w("\t\tDELETE FROM %s WHERE vnum = %d;" % (tbl, old))
    w("\t\t-- the eggs: 7 days from now (the wiki's egg life; the old ones had none)")
    w("\t\tUPDATE player.item SET socket0 = UNIX_TIMESTAMP() + %d WHERE vnum BETWEEN 55401 AND 55414 AND socket0 < UNIX_TIMESTAMP();" % D.EGG_LIFE_SECONDS)
    w("\t\t-- an empty Transporter Peta (55002) stays an empty Klatka Transportowa")
    w("\t\tUPDATE player.item SET socket0 = 0, socket1 = 0, socket2 = 0 WHERE vnum = 55002 AND socket2 = 0;")
    w("\t\t-- the ItemShop (in game): the old pet page lines go; the wiki's lines are added by apply.sh (ishop_once pety_*)")
    w("\t\tDELETE FROM common.itemshop_items WHERE vnum BETWEEN 55000 AND 55999;")
    w("\t\t-- (Kolo Losu: its source kola-src/przedmioty.json has the new vnums - the seed rewrites the wheel at every start)")
    w("\t\t-- the elixirs and the slot key are no items any more")
    w("\t\tDELETE FROM world.item_proto WHERE vnum BETWEEN 55101 AND 55118;")
    w("\t\tINSERT INTO player.playerbot_migrations (name, done_at) VALUES ('pety:migracja_v1', NOW());")
    w("\t\tCOMMIT;")
    w("\tEND IF;")
    w("END//")
    w("DELIMITER ;")
    w("")
    # ---- items ----
    w("-- ---- The items (official vnums: GF 26.1.11 item_list; names and rules: pl-wiki) -----------------------------------")
    w("-- Once (pety:items_v1) every row is written whole (the old system used these vnums for other items); afterwards")
    w("-- INSERT IGNORE only - a row the operator changed is kept.")
    w("DELIMITER //")
    w("BEGIN NOT ATOMIC")
    w("\tIF (SELECT COUNT(*) FROM player.playerbot_migrations WHERE name = 'pety:items_v1') = 0 THEN")
    w("\t\tDELETE FROM world.item_proto WHERE vnum IN (%s);" % ','.join(str(it['vnum']) for it in its))
    w("\t\tINSERT INTO player.playerbot_migrations (name, done_at) VALUES ('pety:items_v1', NOW());")
    w("\tEND IF;")
    w("END//")
    w("DELIMITER ;")
    w("INSERT IGNORE INTO world.item_proto (%s) VALUES" % COLS)
    w(",\n".join(item_row(it) for it in its) + ";")
    w("")
    # ---- names ----
    w("-- ---- The items' names = the pl-wiki's item pages (System Zwierzat Domowych), once more: %s -------------------"
      % NAMES_MARKER)
    w("-- A world that wrote pety:items_v1 earlier keeps its rows (INSERT IGNORE); a later every-start rename of these")
    w("-- vnums (the old ishop5 block of apply.sh: 55033 / 55034 -> Reverti / Revertus Zwierza) is fixed here. Once a")
    w("-- marker - an operator's later rename stays; a new name in pety_data / gen_pety_sql = a new marker.")
    w("DELIMITER //")
    w("BEGIN NOT ATOMIC")
    w("\tIF (SELECT COUNT(*) FROM player.playerbot_migrations WHERE name = '%s') = 0 THEN" % NAMES_MARKER)
    for it in its:
        w("\t\tUPDATE world.item_proto SET name = '%s', locale_name = %s WHERE vnum = %d;"
          % (ascii_name(it['name']), cp1250_hex(it['name']), it['vnum']))
    w("\t\tINSERT INTO player.playerbot_migrations (name, done_at) VALUES ('%s', NOW());" % NAMES_MARKER)
    w("\tEND IF;")
    w("END//")
    w("DELIMITER ;")
    w("")
    # ---- stack (3.0.14) ----
    w("-- ---- The treats stack to 200 (the owner's Yohara list 3.0.14, item 3), once on a world that has the rows: %s ------"
      % STACK_MARKER)
    w("DELIMITER //")
    w("BEGIN NOT ATOMIC")
    w("\tIF (SELECT COUNT(*) FROM player.playerbot_migrations WHERE name = '%s') = 0 THEN" % STACK_MARKER)
    for it in its:
        if it['vnum'] in STACK_VNUMS:
            assert it['stack'] == 200 and not it['antiflag'] & A_STACK, it['vnum']
            w("\t\tUPDATE world.item_proto SET stack = %d, antiflag = antiflag & ~%d, flag = flag | %d WHERE vnum = %d;"
              % (it['stack'], A_STACK, F_STACK, it['vnum']))
    w("\t\tINSERT INTO player.playerbot_migrations (name, done_at) VALUES ('%s', NOW());" % STACK_MARKER)
    w("\tEND IF;")
    w("END//")
    w("DELIMITER ;")
    w("")
    # ---- battle pass (3.0.14) ----
    w("-- ---- Zaczaruj zwierzaka 55033 in the Battle Pass (item 9 of the 3.0.14 list; pl-wiki: battle pass), once: %s. The"
      % BP_MARKER)
    w("-- table is the game core's (playerbot_battlepass.h creates and seeds it); before it exists nothing happens and the")
    w("-- marker waits. Only a free third reward of missions %s - an operator's own reward is kept." % ', '.join(map(str, BP_MISSIONS)))
    w("DELIMITER //")
    w("BEGIN NOT ATOMIC")
    w("\tIF (SELECT COUNT(*) FROM player.playerbot_migrations WHERE name = '%s') = 0 AND (SELECT COUNT(*) FROM" % BP_MARKER)
    w("\t\t\tinformation_schema.TABLES WHERE TABLE_SCHEMA = 'player' AND TABLE_NAME = 'battlepass_mission') > 0 THEN")
    w("\t\tUPDATE player.battlepass_mission SET reward3_vnum = 55033, reward3_count = 1 WHERE id IN (%s) AND reward3_vnum = 0;"
      % ', '.join(map(str, BP_MISSIONS)))
    w("\t\tINSERT INTO player.playerbot_migrations (name, done_at) VALUES ('%s', NOW());" % BP_MARKER)
    w("\tEND IF;")
    w("END//")
    w("DELIMITER ;")
    w("")
    w("-- ---- The pet mobs (young / heroic / champion; clones of 34001 like the ItemShop pets; the client's npclist has")
    w("-- their models - client-patches/client-2.0.30/tools/pety) ----------------------------------------------------------")
    w("DROP TEMPORARY TABLE IF EXISTS world.gp_mob;")
    w("CREATE TEMPORARY TABLE world.gp_mob AS SELECT * FROM world.mob_proto WHERE vnum = 34001 LIMIT 1;")
    for vnum, name in mobs():
        w("UPDATE world.gp_mob SET vnum = %d, name = '%s', locale_name = %s;" % (vnum, ascii_name(name)[:24], cp1250_hex(name)))
        w("INSERT IGNORE INTO world.mob_proto SELECT * FROM world.gp_mob;")
    w("DROP TEMPORARY TABLE IF EXISTS world.gp_mob;")
    w("")
    # ---- skill proto ----
    w("-- ---- The skill proto (once whole: pety:skill_proto_v1; afterwards INSERT IGNORE) ------------------------------------")
    w("DELIMITER //")
    w("BEGIN NOT ATOMIC")
    w("\tIF (SELECT COUNT(*) FROM player.playerbot_migrations WHERE name = 'pety:skill_proto_v1') = 0 THEN")
    w("\t\tDELETE FROM player.growth_pet_skill_proto;")
    w("\t\tINSERT INTO player.playerbot_migrations (name, done_at) VALUES ('pety:skill_proto_v1', NOW());")
    w("\tEND IF;")
    w("END//")
    w("DELIMITER ;")
    rows = []
    for pet_vnum, sid, vals, curve, grow in skill_rows():
        s = D.SKILLS[sid]
        rows.append("(%d,%d,%s,'%s',%d,'%s','%s',%s,'%s','%s','%s','%s')" % (
            pet_vnum, sid, cp1250_hex(s[0]), 'AUTO' if s[2] == D.AUTO else 'PASSIVE', s[3], s[4], s[6],
            ','.join(str(v) for v in vals), ','.join(str(v) for v in curve),
            '' if grow is None else ','.join(str(v) for v in grow),
            ','.join(str(v) for v in D.ACTIVATE.get(sid, [])), ','.join(str(v) for v in D.DURATION.get(sid, []))))
    w("INSERT IGNORE INTO player.growth_pet_skill_proto (pet_vnum, skill_vnum, name, type, cooldown, point_on, unit, "
      + ', '.join('value_t%d' % t for t in range(1, 9)) + ", level_curve, grow_levels, activate, duration) VALUES")
    w(",\n".join(rows) + ";")
    w("")
    w("-- ---- Sfera Losu Zwierzaka at Handlarka Roznosci (10.000 Yang, pl-wiki): see apply.sh (the shop's vnum is looked up)")
    return "\n".join(L) + "\n"


# Old item -> (new vnum or 0 = removed, count multiplier, why). Same vnum + 1 = the item stays (its meaning is the
# wiki's now).
OLD_ITEM_MAP = {
    55001: (55001, 1, u"Proteinowa Przekąska -> Odżywka (the same use: life energy)"),
    55002: (55002, 1, u"Transporter Peta (empty) -> Klatka Transportowa (empty)"),
    55003: (55003, 1, u"Księga Młodego Zwierza (stays)"),
    55008: (55008, 1, u"Zwój Imienia Peta -> Pergamin Nazwy Zwierzaka (the same use)"),
    55009: (55009, 1, u"Skrzynia Ksiąg Peta -> Skrzynia Ksiąg Zwierza (a random new book)"),
    55032: (55028, 1, u"Smakołyk (old 55032) -> Smakołyk 55028"),
    55033: (55029, 1, u"Pet Reverti (forget all) -> Reverti Zwierza"),
    55034: (55030, 1, u"Pet Revertus (forget one) -> Revertus Zwierza"),
    55035: (55031, 1, u"Smakołyk+ (old 55035) -> Smakołyk+ 55031"),
    55036: (55033, 1, u"Klucz Miejsca Umiejętności -> Zaczaruj zwierzaka (re-rolls the skill slots)"),
    95737: (55007, 1, u"Przeb. Księga Zwierza (the old giftbox stand-in) -> the material 55007"),
}
for _v in range(55010, 55032):
    OLD_ITEM_MAP[_v] = (55009, 1, u"an old skill book (dracaryS' skills) -> Skrzynia Ksiąg Zwierza (a random wiki book)")
for _b, _new in ((55101, 55028), (55108, 55028), (55115, 55028)):
    OLD_ITEM_MAP[_b] = (_new, 1, u"elixir S -> 1 Smakołyk")
    OLD_ITEM_MAP[_b + 1] = (_new, 2, u"elixir M -> 2 Smakołyk")
    OLD_ITEM_MAP[_b + 2] = (55031, 1, u"elixir L -> 1 Smakołyk+")
    OLD_ITEM_MAP[_b + 3] = (55031, 2, u"elixir XL -> 2 Smakołyk+")


def skill_rows():
    """(pet_vnum (0 = all), skill, values per type, level curve, grow levels)."""
    for sid in sorted(D.SKILLS):
        curve = D.SKILLS[sid][5]
        v20 = curve[-1]
        yield 0, sid, [v20] * 8, curve, D.GROWTH_LEVELS[sid]
    for sp in D.SPECIES:
        idx, seal = sp[0], sp[2]
        spec = D.SPECIALTY.get(idx, {})
        grow_sp = D.GROWTH_LEVELS_SPECIES.get(idx, {})
        for sid in sorted(set(spec) | set(grow_sp)):
            curve = D.SKILLS[sid][5]
            vals = spec.get(sid, [curve[-1]] * 8)
            yield seal, sid, vals, curve, grow_sp.get(sid, D.GROWTH_LEVELS[sid])


def gen_header():
    L = []
    w = L.append
    w("// MT2009_PLUS_GROWTH_PET_V1: GENERATED by tools/pety/gen_pety_sql.py from tools/pety/pety_data.py - do not edit.")
    w("#ifndef __INC_MT2009_GROWTH_PET_DATA_H__")
    w("#define __INC_MT2009_GROWTH_PET_DATA_H__")
    w("")
    w("namespace growth_pet_data")
    w("{")
    w("\tstruct Species { BYTE idx; DWORD egg; DWORD seal; const char* name; DWORD mob[3]; BYTE hatchMin, hatchMax, "
      "enchantMin, enchantMax, slotMin, slotMax, maxType; };")
    w("\tconst Species SPECIES[] = {")
    for sp in D.SPECIES:
        idx, egg, seal, pet, eggname, young, hero, champ, hatch, enchant, slots, maxtype = sp
        w("\t\t{ %d, %d, %d, \"%s\", { %d, %d, %d }, %d, %d, %d, %d, %d, %d, %d },"
          % (idx, egg, seal, c_cp1250(pet), young, hero, champ, hatch[0], hatch[1], enchant[0], enchant[1], slots[0],
             slots[1], maxtype))
    w("\t};")
    w("\tconst size_t SPECIES_COUNT = sizeof(SPECIES) / sizeof(SPECIES[0]);")
    w("")
    w("\t// level 1..105: mob exp (90 %%), item exp (10 %%)")
    w("\tconst unsigned long long EXP[105][2] = {")
    for a, b in D.EXP:
        w("\t\t{ %dULL, %dULL }," % (a, b))
    w("\t};")
    w("\t// champion level 1..30: champion exp, item exp")
    w("\tconst unsigned long long CHAMPION_EXP[30][2] = {")
    for a, b in D.CHAMPION_EXP:
        w("\t\t{ %dULL, %dULL }," % (a, b))
    w("\t};")
    w("")
    w("\t// per type 1..8: { every, min, max } x { HP, DEF, SP } (0.001 %%)")
    w("\tconst WORD TYPE_GAIN[8][3][3] = {")
    for t in range(1, 9):
        w("\t\t{ %s }," % ', '.join('{ %d, %d, %d }' % g for g in D.TYPE_GAIN[t]))
    w("\t};")
    w("\t// per type 1..8: { every, min, max } x { Wola SungMa (ODP), Przebicie bloku, Precyzja } (champion levels)")
    w("\tconst WORD CHAMPION_TYPE_GAIN[8][3][3] = {")
    for t in range(1, 9):
        w("\t\t{ %s }," % ', '.join('{ %d, %d, %d }' % g for g in D.CHAMPION_TYPE_GAIN[t]))
    w("\t};")
    w("\tconst WORD START_STAT_MIN = %d, START_STAT_MAX = %d, CHAMPION_START_MIN = %d, CHAMPION_START_MAX = %d;"
      % (D.START_STAT + D.CHAMPION_START_STAT))
    w("\tconst WORD AGE_BONUS_MAX_DAYS = %d, STAT_FIRST_LEVEL = %d;" % (D.AGE_BONUS_MAX_DAYS, D.STAT_FIRST_LEVEL))
    w("")
    w("\t// evolution to stage 2..6: { level (champion level for 6), age days, materials { vnum, count } x up to 9 }")
    w("\tstruct Evolution { BYTE stage; WORD level; WORD ageDays; DWORD items[9][2]; };")
    w("\tconst Evolution EVOLUTION[] = {")
    for stage in sorted(D.EVOLUTION):
        lv, age, mats = D.EVOLUTION[stage]
        mats = list(mats) + [(0, 0, '')] * (9 - len(mats))
        w("\t\t{ %d, %d, %d, { %s } }," % (stage, lv, age, ', '.join('{ %d, %d }' % (m[0], m[1]) for m in mats[:9])))
    w("\t};")
    w("\tconst char* const STAGE_NAMES[7] = { \"\", %s };" % ', '.join('"%s"' % c_cp1250(D.STAGES[i]) for i in range(1, 7)))
    w("")
    w("\t// potential skills an egg gives (by the egg's species index 1..14), 0-terminated")
    w("\tconst BYTE POTENTIAL[15][8] = {")
    w("\t\t{ 0 },")
    for i in range(1, 15):
        w("\t\t{ %s, 0 }," % ', '.join(str(x) for x in D.POTENTIAL[i]))
    w("\t};")
    w("}")
    w("")
    w("#endif")
    return "\n".join(L) + "\n"


def c_cp1250(text):
    out = []
    for b in text.encode('cp1250'):
        out.append(chr(b) if 32 <= b < 127 and chr(b) not in '"\\' else '\\x%02x" "' % b)
    return ''.join(out)


def gen_json():
    return json.dumps(dict(items=items(), mobs=[dict(vnum=v, name=n) for v, n in mobs()],
                           skills={sid: dict(name=s[0], icon=s[1], kind='AUTO' if s[2] == D.AUTO else 'PASSIVE',
                                             cooldown=s[3], desc=s[9], book=s[8], book_name=s[7], unit=s[6])
                                   for sid, s in D.SKILLS.items()},
                           species=[dict(idx=s[0], egg=s[1], seal=s[2], name=s[3], egg_name=s[4], mobs=list(s[5:8]))
                                    for s in D.SPECIES],
                           stages=D.STAGES), ensure_ascii=False, indent=1, sort_keys=True) + "\n"


def main():
    check = '--check' in sys.argv
    outs = [(SQL_OUT, gen_sql()), (H_OUT, gen_header()), (JSON_OUT, gen_json())]
    bad = 0
    for path, text in outs:
        data = text.encode('utf-8') if path != H_OUT else text.encode('latin-1')
        old = open(path, 'rb').read() if os.path.exists(path) else None
        if old == data:
            continue
        if check:
            print('would change: %s' % path)
            bad = 1
            continue
        open(path, 'wb').write(data)
        print('wrote %s' % path)
    sys.exit(bad)


if __name__ == '__main__':
    main()
