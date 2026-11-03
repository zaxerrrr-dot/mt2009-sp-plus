#!/usr/bin/env python3
"""gen_edits.py [<game/src>] - writes edits.json of server-patches/pdbonus (MT2009_PLUS_PD_BONUS_V1, README.md) from
the code below; the developer's tool (the apply scripts read edits.json only). With a game/src dir it also checks that
every edit's code is there exactly once (or its marker is). Applied last (after ringfx): the anchors are the patched
engine's (specialexp's char.cpp case, the champion login line, the steal cap's GetLimitPoint)."""
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
M = 'MT2009_PLUS_PD_BONUS_V1'
E = []


def add(f, tag, old, new):
    E.append(dict(file=f, marker='%s (%s)' % (M, tag), old=old, new=new))


# 1. Pierscien Doswiadczenia (unique group 10000) and Rekawica Zlodzieja (10002): their bonus is a point now, so the
#    bonus window shows it and it adds up like every other experience / drop bonus.
add('item.cpp', 'unique points',
    "\t\tcase ITEM_UNIQUE:\n"
    "\t\t\t{\n"
    "\t\t\t\tif (0 != GetSIGVnum())\n",
    "\t\tcase ITEM_UNIQUE:\n"
    "\t\t\t{\n"
    "\t\t\t\t// MT2009_PLUS_PD_BONUS_V1 (unique points): the experience ring (unique group 10000 - Pierscien Doswiadczenia,\n"
    "\t\t\t\t// the map-90 Metins' one too) gives its +50% experience through POINT_RAMADAN_CANDY_BONUS_EXP - the point of\n"
    "\t\t\t\t// the lollipops, the amulets and the costume sets (GiveExp adds it to the rate like the server's exp rate) -\n"
    "\t\t\t\t// and the thief's glove (group 10002) its +100% item drop through POINT_MALL_ITEMBONUS (ITEM_MANAGER::GetDropPct;\n"
    "\t\t\t\t// 72006 still only on stones and bosses there). Both were fixed numbers in GiveExp / GetDropPct that no point\n"
    "\t\t\t\t// held, so the bonus window showed PD 0% / drop 0% with the ring or the glove on. Two items of one group\n"
    "\t\t\t\t// cannot be worn together (CItem::IsSameSpecialGroup), so a group counts once as before.\n"
    "\t\t\t\t{\n"
    "\t\t\t\t\tconst int iUniqueGroup = GetSpecialGroup();\n"
    "\t\t\t\t\tif (iUniqueGroup == UNIQUE_GROUP_RING_OF_EXP)\n"
    "\t\t\t\t\t\tm_pOwner->PointChange(POINT_RAMADAN_CANDY_BONUS_EXP, bAdd ? 50 : -50);\n"
    "\t\t\t\t\telse if (iUniqueGroup == UNIQUE_GROUP_DOUBLE_ITEM)\n"
    "\t\t\t\t\t\tm_pOwner->PointChange(POINT_MALL_ITEMBONUS, bAdd ? 100 : -100);\n"
    "\t\t\t\t}\n"
    "\t\t\t\tif (0 != GetSIGVnum())\n")

add('char_battle.cpp', 'ring rate',
    "\tif (to->IsEquipUniqueGroup(UNIQUE_GROUP_RING_OF_EXP))\n"
    "\t\trateFactor += 50;\n",
    "\t// MT2009_PLUS_PD_BONUS_V1 (ring rate): the experience ring's +50 is in POINT_RAMADAN_CANDY_BONUS_EXP below (item.cpp).\n")

add('char_battle.cpp', 'ring old formula',
    "\t\tif (to->IsEquipUniqueGroup(UNIQUE_GROUP_RING_OF_EXP) == true)\n"
    "\t\t{\n"
    "\t\t\tiExp += (iExp * 50 / 100);\n"
    "\t\t}\n",
    "\t\t// MT2009_PLUS_PD_BONUS_V1 (ring old formula): the ring's +50% is POINT_RAMADAN_CANDY_BONUS_EXP (item.cpp).\n")

add('item_manager.cpp', 'drop',
    "\tif (hasThiefGloves)\n"
    "\t\tAddToBonusItemDrop(item_drop_bonus, 100);\n",
    "\t// MT2009_PLUS_PD_BONUS_V1 (drop): POINT_MALL_ITEMBONUS - the worn thief's glove's +100 (item.cpp) and the used one's\n"
    "\t// affect (Rekawica Zlodzieja 71016 / 76037, +50: the point no code read, so that glove did nothing). 72006 against a\n"
    "\t// common monster: its +100 comes off again (hasThiefGloves is false then, as before).\n"
    "\t{\n"
    "\t\tint iMallItemBonus = pkKiller->GetPoint(POINT_MALL_ITEMBONUS);\n"
    "\t\tif (!hasThiefGloves && pkKiller->IsEquipUniqueGroup(UNIQUE_GROUP_DOUBLE_ITEM))\n"
    "\t\t\tiMallItemBonus -= 100;\n"
    "\t\tif (iMallItemBonus > 0)\n"
    "\t\t\tAddToBonusItemDrop(item_drop_bonus, iMallItemBonus);\n"
    "\t}\n")

# 2. POINT_MALL_ITEMBONUS adds up without the 100 cap (glove 100 + potion glove 50): the cap clipped the amount on the way
#    in and took the whole amount off on the way out - the point drifted below the truth.
add('char.cpp', 'item bonus cap',
    "\t\tcase POINT_MALL_EXPBONUS:\n"
    "\t\tcase POINT_MALL_ITEMBONUS:\n"
    "\t\tcase POINT_MALL_GOLDBONUS:\n",
    "\t\tcase POINT_MALL_EXPBONUS:\n"
    "\t\tcase POINT_MALL_GOLDBONUS:\n")

add('char.cpp', 'item bonus sum',
    "\t\tcase POINT_RAMADAN_CANDY_BONUS_EXP:\n"
    "\t\t\t// MT2009_PLUS_NS_SPECIAL_EXP_V1",
    "\t\tcase POINT_MALL_ITEMBONUS:\n"
    "\t\t\t// MT2009_PLUS_PD_BONUS_V1 (item bonus sum): the worn thief's glove (+100, item.cpp) and the used one (+50) together\n"
    "\t\t\t// - no 100 cap here: a clipped amount on the way in came off whole on the way out.\n"
    "\t\t\tSetPoint(type, GetPoint(type) + amount);\n"
    "\t\t\tval = GetPoint(type);\n"
    "\t\t\tbreak;\n"
    "\n"
    "\t\tcase POINT_RAMADAN_CANDY_BONUS_EXP:\n"
    "\t\t\t// MT2009_PLUS_NS_SPECIAL_EXP_V1")

# 3. Experience given away at the top level (the guild's offering): it never left the character.
add('char.cpp', 'exp given away',
    "\t\t\t\t\tif (FindAffect(AFFECT_EXP_BLOCK))\n"
    "\t\t\t\t\t\treturn;\n"
    "\n"
    "\t\t\t\t\t// MT2009_PLUS_CHAMPION_V1 (max level exp)",
    "\t\t\t\t\tif (FindAffect(AFFECT_EXP_BLOCK))\n"
    "\t\t\t\t\t\treturn;\n"
    "\n"
    "\t\t\t\t\t// MT2009_PLUS_PD_BONUS_V1 (exp given away): experience taken (the guild's offering, a death) is taken at\n"
    "\t\t\t\t\t// every level. The top level's branch below is for experience gained: with the bar full (one point short)\n"
    "\t\t\t\t\t// it returned at once, so a level 120 offered his experience to the guild again and again and never lost\n"
    "\t\t\t\t\t// any (CGuild::OfferExp checked the amount, the guild got it, the bar stayed full). Below the top level the\n"
    "\t\t\t\t\t// path below did the same subtraction (the level steps only ever go up).\n"
    "\t\t\t\t\tif (amount < 0)\n"
    "\t\t\t\t\t{\n"
    "\t\t\t\t\t\tSetExp(exp + amount);\n"
    "\t\t\t\t\t\tval = GetExp();\n"
    "\t\t\t\t\t\tbreak;\n"
    "\t\t\t\t\t}\n"
    "\n"
    "\t\t\t\t\t// MT2009_PLUS_CHAMPION_V1 (max level exp)")

# 4. POINT_ERROR type 114: a young heroes' weapon (21900-21975, "Wartosc ataku +20..50%") and Atak Boga Smokow (+15/20)
#    or the world boss's buff legitimately sum to 65-70; the log's threshold was 50 while PointChange caps it at 100.
add('char.cpp', 'mall att error',
    "\t\tcase POINT_MALL_ATTBONUS:\n"
    "\t\tcase POINT_MALL_DEFBONUS:\n"
    "\t\t\tlimit = 20;\n"
    "\t\t\tmax_val = 50;\n",
    "\t\tcase POINT_MALL_ATTBONUS:\n"
    "\t\tcase POINT_MALL_DEFBONUS:\n"
    "\t\t\tlimit = 20;\n"
    "\t\t\t// MT2009_PLUS_PD_BONUS_V1 (mall att error): the error threshold is PointChange's own cap (100) - a young heroes'\n"
    "\t\t\t// weapon (+50) with Atak Boga Smokow (+15/20) is 65-70 by the rules and flooded syserr with POINT_ERROR type 114\n"
    "\t\t\t// on every hit. What counts in a hit stays the limit above.\n"
    "\t\t\tmax_val = 100;\n")

# 5. The bonus maxima of this world (item_attr / item_attr_rare as loaded) for the tooltip's gold line (mt2009_attrmax.cpp).
add('input_login.cpp', 'attr max login',
    "\t{ void ChampionOnLogin(LPCHARACTER); ChampionOnLogin(ch); }\n",
    "\t{ void ChampionOnLogin(LPCHARACTER); ChampionOnLogin(ch); }\n"
    "\t// MT2009_PLUS_PD_BONUS_V1 (attr max login): the bonus maxima of this world's item_attr / item_attr_rare (the bonus\n"
    "\t// mode and the panel's editor included) as \"AttrMax\" command lines - the tooltip's gold maximum (mt2009_attrmax.cpp).\n"
    "\t{ void Mt2009AttrMaxOnLogin(LPCHARACTER); Mt2009AttrMaxOnLogin(ch); }\n")

json.dump(E, open(os.path.join(HERE, 'edits.json'), 'w'), indent=1)
print('pdbonus: %d edits' % len(E))
if len(sys.argv) > 1:
    bad = 0
    for e in E:
        t = open(os.path.join(sys.argv[1], e['file']), encoding='latin-1').read().replace('\r\n', '\n')
        if e['marker'] not in t and t.count(e['old']) != 1:
            print('%s: %s - the code is there %d times' % (e['file'], e['marker'], t.count(e['old'])))
            bad += 1
    print('check: %s' % ('OK' if not bad else '%d problem(s)' % bad))
    sys.exit(1 if bad else 0)
