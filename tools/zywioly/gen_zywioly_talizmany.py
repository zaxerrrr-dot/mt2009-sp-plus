#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""MT2009_PLUS_ELEMENTS_V1 - writes linux-port/docker/mariadb/playerbot/zywioly_talizmany.sql from
zywioly_dane.py: the talismans +0..+200 of the six elements and Kwiat Zywiolu (world.item_proto),
their 1200 refine recipes (world.refine_proto 20001-21200), the talismans' own bonus set (the
`pendant` column of world.item_attr) and Mistrz's shop 9550. Autor: Digi Rasta (Zywioly i talizmany,
nowy-system 0.28.0, his narzedzia/talizmany_sql.py), with the owner's rules of 7 October 2026:
NO element resistance (nor anything else) in the bonus pools of bracelets, helmets, armour or any
other item - a new item_attr row has every column but `pendant` at 0, and an existing row gets its
`pendant` level only (a column no item but the talisman reads).

Usage:  python3 tools/zywioly/gen_zywioly_talizmany.py
"""
import binascii
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import zywioly_dane as d  # noqa: E402

REPO = os.path.dirname(os.path.dirname(HERE))
OUT = os.path.join(REPO, 'linux-port', 'docker', 'mariadb', 'playerbot', 'zywioly_talizmany.sql')

COLUMNS = ("vnum", "name", "locale_name", "type", "subtype", "stack", "weight", "size", "antiflag", "flag",
           "wearflag", "immuneflag", "gold", "shop_buy_price", "refined_vnum", "refine_set", "magic_pct",
           "specular", "socket_pct", "addon_type", "limittype0", "limitvalue0", "limittype1", "limitvalue1",
           "applytype0", "applyvalue0", "applytype1", "applyvalue1", "applytype2", "applyvalue2", "value0",
           "value1", "value2", "value3", "value4", "value5", "socket0", "socket1", "socket2", "socket3",
           "socket4", "socket5")

# The talisman's random bonuses (wiki "Talizman Ognia", his table): (point, prob, lv1..lv5, max level
# on the talisman). New rows only where the bonus has no row yet.
NEW_BONUSES = (
    ("POINT_BREAK_RESIST_SWORD", 10, (1, 2, 3, 4, 5), 5),
    ("POINT_BREAK_RESIST_TWOHAND", 10, (1, 2, 3, 4, 5), 5),
    ("POINT_BREAK_RESIST_DAGGER", 10, (1, 2, 3, 4, 5), 5),
    ("POINT_BREAK_RESIST_BELL", 10, (1, 2, 3, 4, 5), 5),
    ("POINT_BREAK_RESIST_FAN", 10, (1, 2, 3, 4, 5), 5),
    ("POINT_BREAK_RESIST_BOW", 10, (1, 2, 3, 4, 5), 5),
    ("POINT_ATTBONUS_INSECT", 15, (6, 12, 18, 24, 30), 5),
    ("POINT_ATTBONUS_DESERT", 15, (6, 12, 18, 24, 30), 5),
    ("POINT_RESIST_HUMAN", 15, (2, 4, 6, 8, 10), 5),
    ("POINT_RESIST_FIRE", 18, (5, 10, 15, 20, 25), 5),
    ("POINT_RESIST_ELEC", 18, (5, 10, 15, 20, 25), 5),
    ("POINT_RESIST_WIND", 18, (5, 10, 15, 20, 25), 5),
    ("POINT_RESIST_ICE", 18, (5, 10, 15, 20, 25), 5),
    ("POINT_RESIST_EARTH", 18, (5, 10, 15, 20, 25), 5),
    ("POINT_RESIST_DARK", 18, (5, 10, 15, 20, 25), 5),
)
# Rows the world has: only their talisman level (values shared with the rest of the gear):
# Silny p. Ludziom 1/2/3/5/10 -> up to 3 = 3%, Omdlenie 1/2/3/5/8 -> up to 5 = 8% (wiki max 8%).
EXISTING = (("POINT_ATTBONUS_HUMAN", 3), ("POINT_STUN_PCT", 5))
ATTR_COLUMNS = ("apply", "prob", "lv1", "lv2", "lv3", "lv4", "lv5", "weapon", "body", "wrist", "foots", "neck",
                "head", "shield", "ear", "costume_body", "costume_hair", "costume_weapon", "pendant", "glove")


def cp1250(s):
    return "_cp1250 X'%s'" % binascii.hexlify(s.encode('cp1250')).decode('ascii').upper()


def sql_value(x):
    if isinstance(x, tuple) and x and x[0] == 'cp1250':
        return cp1250(x[1])
    if isinstance(x, str):
        return "'" + x.replace("\\", "\\\\").replace("'", "''") + "'"
    return str(x)


def row(values):
    return "(" + ",".join(sql_value(x) for x in values) + ")"


def main():
    items, recipes = [], []
    for vnum, nr, n, nazwa, ascii_, punkt, opis, ikona in d.talizmany():
        first = d.TALIZMANY[nr][0]
        nxt = vnum + 1 if n < d.MAKS else 0
        rset = d.refine_set(nr, n)
        items.append((vnum, ascii_, ('cp1250', nazwa), d.ITEM_ARMOR, d.ARMOR_PENDANT, 1, 0, 1, 0, 0,
                      d.WEARABLE_PENDANT, "", d.TALIZMAN_CENA, d.TALIZMAN_CENA, nxt, rset, 0, 0, 0, 0,
                      d.LIMIT_LEVEL, d.poziom_gracza(n), 0, 0, punkt, n, 0, 0, 0, 0,
                      0, 0, 0, 0, 0, 0, -1, -1, -1, -1, -1, -1))
        if n < d.MAKS:
            recipes.append((rset, d.KWIAT, 10, d.ORNAMENT, 1, first, 1, 0, 0, 0, 0, d.oplata(n), 0, 0, 100))
    items.append((d.KWIAT, "Kwiat Zywiolu", ('cp1250', d.KWIAT_NAZWA), d.ITEM_MATERIAL, 0, d.STACK, 0, 1, 0,
                  d.ITEM_FLAG_STACKABLE, 0, "", d.KWIAT_CENA, d.KWIAT_SKUP, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
                  0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, -1, -1, -1, -1, -1, -1))

    ranges = " OR ".join("vnum BETWEEN %d AND %d" % (t[0], t[0] + d.MAKS) for t in d.TALIZMANY) + \
        " OR vnum = %d" % d.KWIAT
    r_lo, r_hi = d.REFINE_ID, d.REFINE_ID + 200 * len(d.TALIZMANY) - 1
    out = ["-- MT2009_PLUS_ELEMENTS_V1: the elements' talismans +0..+200 and Kwiat Zywiolu. Autor: Digi Rasta",
           "-- (Zywioly i talizmany, nowy-system 0.28.0). GENERATED by tools/zywioly/gen_zywioly_talizmany.py from",
           "-- zywioly_dane.py - do not edit. Every start (apply.sh), idempotent: our own vnum / id ranges are",
           "-- deleted and written again; the bonus pool of every other item stays as it is (owner, 7 October).",
           "DELETE FROM world.item_proto WHERE %s;" % ranges,
           "INSERT INTO world.item_proto (%s) VALUES" % ",".join("`%s`" % k for k in COLUMNS),
           ",\n".join(row(p) for p in items) + ";",
           "",
           "-- The Blacksmith's recipes: 10x Kwiat Zywiolu, 1x Ornament, 1x Talisman +0 of the element, the fee, 100%.",
           "DELETE FROM world.refine_proto WHERE id BETWEEN %d AND %d;" % (r_lo, r_hi),
           "INSERT INTO world.refine_proto (`id`,`vnum0`,`count0`,`vnum1`,`count1`,`vnum2`,`count2`,`vnum3`,"
           "`count3`,`vnum4`,`count4`,`cost`,`src_vnum`,`result_vnum`,`prob`) VALUES",
           ",\n".join(row(r) for r in recipes) + ";",
           "",
           "-- The talisman's own random bonuses (item_attr.pendant - read for ARMOR_PENDANT only). A new row has",
           "-- every other column 0, so no bracelet, helmet, armour or jewel can roll it; an existing row only",
           "-- gets its pendant level."]
    for apply, prob, lv, level in NEW_BONUSES:
        values = (apply, prob) + lv + (0,) * 11 + (level, 0)
        out.append("INSERT INTO world.item_attr (%s) SELECT %s FROM DUAL WHERE NOT EXISTS (SELECT 1 FROM "
                   "world.item_attr WHERE `apply` = '%s');" % (",".join("`%s`" % c for c in ATTR_COLUMNS),
                                                              ",".join(sql_value(x) for x in values), apply))
        out.append("UPDATE world.item_attr SET `pendant` = %d WHERE `apply` = '%s';" % (level, apply))
    for apply, level in EXISTING:
        out.append("UPDATE world.item_attr SET `pendant` = %d WHERE `apply` = '%s';" % (level, apply))
    out += ["",
            "-- Mistrz (20082): Kwiat Zywiolu by 1 and by 10 (quest zywioly, npc.open_shop()).",
            "REPLACE INTO world.shop (`vnum`,`name`,`npc_vnum`) VALUES (%d,'Mistrz - Kwiaty Zywiolu',%d);"
            % (d.SKLEP, d.MISTRZ),
            "DELETE FROM world.shop_item WHERE shop_vnum = %d;" % d.SKLEP,
            "INSERT INTO world.shop_item (`shop_vnum`,`item_vnum`,`count`) VALUES (%d,%d,1),(%d,%d,10);"
            % (d.SKLEP, d.KWIAT, d.SKLEP, d.KWIAT),
            ""]
    with open(OUT, 'w', encoding='ascii', newline='\n') as f:
        f.write("\n".join(out))
    print("written %s: %d items, %d recipes, %d new bonus rows" % (os.path.relpath(OUT, REPO), len(items),
                                                                    len(recipes), len(NEW_BONUSES)))


if __name__ == '__main__':
    main()
