# -*- coding: utf-8 -*-
"""MT2009_PLUS_BONUS67_V1: the 6th/7th bonus pool of both bonus modes (the pl-wiki "6. i 7. bonus" - the owner,
20 October 2026: "Bonusy 6/7 takie same w jednym i drugim trybie") and the 54 points it needed (198-251,
server-patches/bonusy67/gen_edits.py POINTS - the same order).

A row: (POINT_* name, prob, (lv1..lv5), {kind column: highest level there}). The levels: Owsap's item_attr_rare (10
levels) at its 2nd/4th/6th/8th/10th (or 1-5 where it has five), ending at the wiki's maximum of the kind; where Owsap
has no row (FIRST..FIFTH_ATTRIBUTE_BONUS, the gloves' lines) five equal steps up to the wiki's maximum. Weights equal
(18, as the official table) - Burza Szponow's line 0: it is the Lycan's skill and there is no Lycan here.
Kinds: weapon body wrist foots neck head shield ear costume_body costume_hair costume_weapon pendant glove.
"""

KINDS = ('weapon', 'body', 'wrist', 'foots', 'neck', 'head', 'shield', 'ear', 'costume_body', 'costume_hair',
         'costume_weapon', 'pendant', 'glove')
GEAR9 = ('weapon', 'body', 'wrist', 'foots', 'neck', 'head', 'shield', 'ear', 'pendant')
HITBUFF8 = ('weapon', 'body', 'wrist', 'foots', 'neck', 'head', 'shield', 'ear')


def kinds(names, level=5):
    return dict((k, level) for k in names)


# what the pool had (bonusy67_global.sql of MT2009_PLUS_RARE_WIKI_V1, the wiki's rows the engine had)
OLD_ROWS = [
    ('POINT_MAX_HP', 18, (100, 200, 300, 400, 500), kinds(GEAR9)),
    ('POINT_MAX_SP', 18, (10, 20, 40, 60, 80), kinds(GEAR9)),
    ('POINT_POISON_PCT', 18, (1, 2, 3, 4, 5), kinds(GEAR9)),
    ('POINT_POISON_REDUCE', 18, (1, 2, 3, 4, 5), kinds(GEAR9)),
    ('POINT_ATT_GRADE_BONUS', 18, (8, 15, 25, 35, 50), kinds(GEAR9)),
    ('POINT_MAGIC_ATT_GRADE_BONUS', 18, (8, 15, 25, 35, 50), kinds(GEAR9)),
    ('POINT_ATTBONUS_STONE', 18, (2, 4, 5, 7, 8), kinds(('weapon', 'neck', 'glove'))),
    ('POINT_DAMAGE_SP_RECOVER', 18, (1, 2, 3, 4, 5), dict(weapon=5, body=5, foots=3)),
    ('POINT_BLOCK', 18, (1, 2, 3, 4, 5), kinds(('shield',))),
    ('POINT_SUNGMA_PER_STR', 18, (2, 4, 6, 8, 15), dict(pendant=4, glove=5)),
    ('POINT_SUNGMA_PER_HP', 18, (2, 4, 6, 8, 15), dict(pendant=4, glove=5)),
    ('POINT_SUNGMA_PER_MOVE', 18, (2, 4, 6, 8, 15), dict(pendant=4, glove=5)),
    ('POINT_SUNGMA_PER_IMMUNE', 18, (2, 4, 6, 8, 15), dict(pendant=4, glove=5)),
]

# (point, Polish name as the wiki has it - root/localeinfo_point.py, cp1250 there; the panel's name - the wiki's words,
# x = the value (MT2009_PLUS_BONUS67_WIKI_NAMES_V1); unit)
NEW_POINTS = [
    ('POINT_HIT_BUFF_ENCHANT_FIRE', u'Otrzymujesz moc ognia na %d sek. w walce', u'Otrzymujesz moc ognia na x sek. w walce', u's'),
    ('POINT_HIT_BUFF_ENCHANT_ICE', u'Otrzymujesz moc lodu na %d sek. w walce', u'Otrzymujesz moc lodu na x sek. w walce', u's'),
    ('POINT_HIT_BUFF_ENCHANT_ELEC', u'Otrzymujesz moc błyskawic na %d sek. w walce', u'Otrzymujesz moc błyskawic na x sek. w walce', u's'),
    ('POINT_HIT_BUFF_ENCHANT_WIND', u'Otrzymujesz moc wiatru na %d sek. w walce', u'Otrzymujesz moc wiatru na x sek. w walce', u's'),
    ('POINT_HIT_BUFF_ENCHANT_DARK', u'Otrzymujesz moc mroku na %d sek. w walce', u'Otrzymujesz moc mroku na x sek. w walce', u's'),
    ('POINT_HIT_BUFF_ENCHANT_EARTH', u'Otrzymujesz moc ziemi na %d sek. w walce', u'Otrzymujesz moc ziemi na x sek. w walce', u's'),
    ('POINT_HIT_BUFF_RESIST_FIRE', u'Otrzymujesz odporność na ogień na %d sek. w walce', u'Otrzymujesz odporność na ogień na x sek. w walce', u's'),
    ('POINT_HIT_BUFF_RESIST_ICE', u'Otrzymujesz odporność na lód na %d sek. w walce', u'Otrzymujesz odporność na lód na x sek. w walce', u's'),
    ('POINT_HIT_BUFF_RESIST_ELEC', u'Otrzymujesz odporność na błyskawice na %d sek. w walce', u'Otrzymujesz odporność na błyskawice na x sek. w walce', u's'),
    ('POINT_HIT_BUFF_RESIST_WIND', u'Otrzymujesz odporność na wiatr na %d sek. w walce', u'Otrzymujesz odporność na wiatr na x sek. w walce', u's'),
    ('POINT_HIT_BUFF_RESIST_DARK', u'Otrzymujesz odporność na mrok na %d sek. w walce', u'Otrzymujesz odporność na mrok na x sek. w walce', u's'),
    ('POINT_HIT_BUFF_RESIST_EARTH', u'Otrzymujesz odporność na ziemię na %d sek. w walce', u'Otrzymujesz odporność na ziemię na x sek. w walce', u's'),
    ('POINT_ATTBONUS_PER_MONSTER', u'Silny przeciwko potworom (+%d%% łącznej wartości)', u'Silny przeciwko potworom (+x% łącznej wartości)', u'%'),
    ('POINT_ATTBONUS_PER_STONE', u'Siła w walce z kamieniami Metin (+%d%% łącznej wartości)', u'Siła w walce z kamieniami Metin (+x% łącznej wartości)', u'%'),
    ('POINT_ATTBONUS_PER_CZ', u'Silny przeciwko potworom Zodiaku (+%d%% łącznej wartości)', u'Silny przeciwko potworom Zodiaku (+x% łącznej wartości)', u'%'),
    ('POINT_ATTBONUS_PER_MILGYO', u'Siła w walce z mistykami (+%d%% łącznej wartości)', u'Siła w walce z mistykami (+x% łącznej wartości)', u'%'),
    ('POINT_ATTBONUS_PER_ORC', u'Siła w walce z orkom (+%d%% łącznej wartości)', u'Siła w walce z orkom (+x% łącznej wartości)', u'%'),
    ('POINT_ATTBONUS_PER_DEVIL', u'Siła w walce diabłami (+%d%% łącznej wartości)', u'Siła w walce diabłami (+x% łącznej wartości)', u'%'),
    ('POINT_ATTBONUS_PER_INSECT', u'Siła w walce z insektami (+%d%% łącznej wartości)', u'Siła w walce z insektami (+x% łącznej wartości)', u'%'),
    ('POINT_ATTBONUS_PER_ANIMAL', u'Siła w walce ze zwierzętami (+%d%% łącznej wartości)', u'Siła w walce ze zwierzętami (+x% łącznej wartości)', u'%'),
    ('POINT_ENCHANT_PER_ELECT', u'Siła Błyskawic (+%d%% łącznej wartości)', u'Siła Błyskawic (+x% łącznej wartości)', u'%'),
    ('POINT_ENCHANT_PER_FIRE', u'Siła Ognia (+%d%% łącznej wartości)', u'Siła Ognia (+x% łącznej wartości)', u'%'),
    ('POINT_ENCHANT_PER_ICE', u'Siła Lodu (+%d%% łącznej wartości)', u'Siła Lodu (+x% łącznej wartości)', u'%'),
    ('POINT_ENCHANT_PER_WIND', u'Siła Wiatru (+%d%% łącznej wartości)', u'Siła Wiatru (+x% łącznej wartości)', u'%'),
    ('POINT_ENCHANT_PER_EARTH', u'Siła Ziemi (+%d%% łącznej wartości)', u'Siła Ziemi (+x% łącznej wartości)', u'%'),
    ('POINT_ENCHANT_PER_DARK', u'Siła Mroku (+%d%% łącznej wartości)', u'Siła Mroku (+x% łącznej wartości)', u'%'),
    ('POINT_RESIST_PER_HUMAN', u'Odporność na Ludzi (+%d%% łącznej wartości)', u'Odporność na Ludzi (+x% łącznej wartości)', u'%'),
    ('POINT_RESIST_PER_MAGIC', u'Odporność na Magię (+%d%% łącznej wartości)', u'Odporność na Magię (+x% łącznej wartości)', u'%'),
    ('POINT_RESIST_PER_ELEC', u'Odporność na Błyskawice (+%d%% łącznej wartości)', u'Odporność na Błyskawice (+x% łącznej wartości)', u'%'),
    ('POINT_RESIST_PER_FIRE', u'Odporność na Ogień (+%d%% łącznej wartości)', u'Odporność na Ogień (+x% łącznej wartości)', u'%'),
    ('POINT_RESIST_PER_ICE', u'Odporność na Lód (+%d%% łącznej wartości)', u'Odporność na Lód (+x% łącznej wartości)', u'%'),
    ('POINT_RESIST_PER_WIND', u'Odporność na Wiatr (+%d%% łącznej wartości)', u'Odporność na Wiatr (+x% łącznej wartości)', u'%'),
    ('POINT_RESIST_PER_EARTH', u'Odporność na Ziemię (+%d%% łącznej wartości)', u'Odporność na Ziemię (+x% łącznej wartości)', u'%'),
    ('POINT_RESIST_PER_DARK', u'Odporność na Mrok (+%d%% łącznej wartości)', u'Odporność na Mrok (+x% łącznej wartości)', u'%'),
    ('POINT_NORMAL_HIT_DEFEND_BONUS_BOSS_OR_MORE', u'Obrażenia od ataku bossów -%d%%', u'Obrażenia od ataku bossów -x%', u'%'),
    ('POINT_SKILL_DEFEND_BONUS_BOSS_OR_MORE', u'Obrażenia od umiejętności bossów -%d%%', u'Obrażenia od umiejętności bossów -x%', u'%'),
    ('POINT_NORMAL_HIT_DAMAGE_BONUS_BOSS_OR_MORE', u'Obrażenia od ataku przeciwko bossom +%d%%', u'Obrażenia od ataku przeciwko bossom +x%', u'%'),
    ('POINT_SKILL_DAMAGE_BONUS_BOSS_OR_MORE', u'Obrażenia od umiejętności przeciwko bossom +%d%%', u'Obrażenia od umiejętności przeciwko bossom +x%', u'%'),
    ('POINT_FIRST_ATTRIBUTE_BONUS', u'1. dodany bonus +%d%%', u'1. dodany bonus +x%', u'%'),
    ('POINT_SECOND_ATTRIBUTE_BONUS', u'2. dodany bonus +%d%%', u'2. dodany bonus +x%', u'%'),
    ('POINT_THIRD_ATTRIBUTE_BONUS', u'3. dodany bonus +%d%%', u'3. dodany bonus +x%', u'%'),
    ('POINT_FOURTH_ATTRIBUTE_BONUS', u'4. dodany bonus +%d%%', u'4. dodany bonus +x%', u'%'),
    ('POINT_FIFTH_ATTRIBUTE_BONUS', u'5. dodany bonus +%d%%', u'5. dodany bonus +x%', u'%'),
    ('POINT_GLOVE_FALL_RESIST', u'Podczas walki istnieje %d%% prawdopodobieństwa na odporność na upadek (czas regeneracji 60 sek.).', u'Podczas walki istnieje x% prawdopodobieństwa na odporność na upadek (czas regeneracji 60 sek.).', u'%'),
    ('POINT_GLOVE_LIGHTNING', u'Atakuj potwory w pobliżu podczas walki za pomocą błyskawic, których obrażenia odpowiadają obrażeniom od automatycznego ataku (czas regeneracji 15 sek.).', u'Atakuj potwory w pobliżu podczas walki za pomocą błyskawic, których obrażenia odpowiadają obrażeniom od automatycznego ataku (czas regeneracji 15 sek.).', u''),
    ('POINT_GLOVE_COOLDOWN_FINISH', u'W przypadku użycia Trzęsienia z prawdopodobieństwem %d%% skraca kolejny czas regeneracji Trzęsienia o 5 sekund.', u'W przypadku użycia Trzęsienia z prawdopodobieństwem x% skraca kolejny czas regeneracji Trzęsienia o 5 sekund.', u'%'),
    ('POINT_GLOVE_COOLDOWN_ILGWANGPYO', u'W przypadku użycia Światła Gwiazd z prawdopodobieństwem od %d%% skraca kolejny czas regeneracji Światła Gwiazd o 5 sekund.', u'W przypadku użycia Światła Gwiazd z prawdopodobieństwem od x% skraca kolejny czas regeneracji Światła Gwiazd o 5 sekund.', u'%'),
    ('POINT_GLOVE_COOLDOWN_PUNGLOEPO', u'W przypadku użycia Strzału Wichury z prawdopodobieństwem od %d%% skraca kolejny czas regeneracji Strzału Wichury o 5 sekund.', u'W przypadku użycia Strzału Wichury z prawdopodobieństwem od x% skraca kolejny czas regeneracji Strzału Wichury o 5 sekund.', u'%'),
    ('POINT_GLOVE_COOLDOWN_GEOMAGGWI', u'W przypadku użycia Piekielnego Ciosu z prawdopodobieństwem od %d%% skraca kolejny czas regeneracji Piekielnego Ciosu o 5 sekund.', u'W przypadku użycia Piekielnego Ciosu z prawdopodobieństwem od x% skraca kolejny czas regeneracji Piekielnego Ciosu o 5 sekund.', u'%'),
    ('POINT_GLOVE_COOLDOWN_MABEOBAGGWI', u'W przypadku użycia Fali Śmierci z prawdopodobieństwem od %d%% skraca kolejny czas regeneracji Fali Śmierci o 5 sekund.', u'W przypadku użycia Fali Śmierci z prawdopodobieństwem od x% skraca kolejny czas regeneracji Fali Śmierci o 5 sekund.', u'%'),
    ('POINT_GLOVE_COOLDOWN_METEO', u'W przypadku użycia Meteoru z prawdopodobieństwem od %d%% skraca kolejny czas regeneracji Meteoru o 5 sekund.', u'W przypadku użycia Meteoru z prawdopodobieństwem od x% skraca kolejny czas regeneracji Meteoru o 5 sekund.', u'%'),
    ('POINT_GLOVE_COOLDOWN_CHEONUN', u'W przypadku użycia Tarczy Eteru z prawdopodobieństwem od %d%% skraca kolejny czas regeneracji Tarczy Eteru o 5 sekund.', u'W przypadku użycia Tarczy Eteru z prawdopodobieństwem od x% skraca kolejny czas regeneracji Tarczy Eteru o 5 sekund.', u'%'),
    ('POINT_GLOVE_COOLDOWN_ILIPUNGU', u'W przypadku użycia Burzy Szponów z prawdopodobieństwem od %d%% skraca kolejny czas regeneracji Burzy Szponów o 5 sekund.', u'W przypadku użycia Burzy Szponów z prawdopodobieństwem od x% skraca kolejny czas regeneracji Burzy Szponów o 5 sekund.', u'%'),
    ('POINT_GLOVE_BASE_ATTR_PCT', u'Atrybuty podstawowe rękawic są zwiększone o %d %% (bonusy wbudowane rękawic)', u'Atrybuty podstawowe rękawic są zwiększone o x % (bonusy wbudowane rękawic)', u'%'),
]
FIRST_POINT = 198
assert len(NEW_POINTS) == 54

NEW_ROWS = []
for p in NEW_POINTS[0:12]:
    # wiki: every kind but the talisman and the gloves, 5 s; Owsap 1-5 s
    NEW_ROWS.append((p[0], 18, (1, 2, 3, 4, 5), kinds(HITBUFF8)))
for name, values in (
        ('POINT_ATTBONUS_PER_MONSTER', (2, 4, 5, 7, 10)),	# wiki 10, Owsap 1..7,10
        ('POINT_ATTBONUS_PER_STONE', (2, 4, 5, 7, 12)),		# wiki 12, Owsap 1..7,12
        ('POINT_ATTBONUS_PER_CZ', (2, 4, 6, 10, 20)),		# wiki 20, Owsap 1..7,10,20
        ('POINT_ATTBONUS_PER_MILGYO', (2, 4, 6, 10, 20)),	# wiki 20 (Owsap 15)
        ('POINT_ATTBONUS_PER_ORC', (2, 4, 6, 10, 20)),
        ('POINT_ATTBONUS_PER_DEVIL', (2, 4, 6, 10, 20)),
        ('POINT_ATTBONUS_PER_INSECT', (2, 4, 6, 10, 20)),	# wiki 20, Owsap 20
        ('POINT_ATTBONUS_PER_ANIMAL', (2, 4, 5, 7, 10)),	# wiki 10 (Owsap 15)
        ('POINT_ENCHANT_PER_ELECT', (2, 4, 6, 10, 15)),		# wiki 15, Owsap 1..7,10,15
        ('POINT_ENCHANT_PER_FIRE', (2, 4, 6, 10, 15)),
        ('POINT_ENCHANT_PER_ICE', (2, 4, 6, 10, 15)),
        ('POINT_ENCHANT_PER_WIND', (2, 4, 6, 10, 15)),
        ('POINT_ENCHANT_PER_EARTH', (2, 4, 6, 10, 15)),
        ('POINT_ENCHANT_PER_DARK', (2, 4, 6, 10, 15))):
    NEW_ROWS.append((name, 18, values, kinds(('weapon',))))
for name, values in (
        ('POINT_RESIST_PER_HUMAN', (1, 2, 3, 4, 5)),		# wiki 5 (Owsap 10)
        ('POINT_RESIST_PER_MAGIC', (2, 4, 6, 10, 15)),		# wiki 15, Owsap 1..7,10,15
        ('POINT_RESIST_PER_ELEC', (2, 4, 5, 7, 10)),		# wiki 10, Owsap 1..7,10
        ('POINT_RESIST_PER_FIRE', (2, 4, 5, 7, 10)),
        ('POINT_RESIST_PER_ICE', (2, 4, 5, 7, 10)),
        ('POINT_RESIST_PER_WIND', (2, 4, 5, 7, 10)),
        ('POINT_RESIST_PER_EARTH', (2, 4, 5, 7, 10)),
        ('POINT_RESIST_PER_DARK', (2, 4, 5, 7, 10))):
    NEW_ROWS.append((name, 18, values, kinds(('body',))))
NEW_ROWS += [
    # wiki: armour, shield, gloves 5% / necklace, gloves 5%; Owsap 1-5
    ('POINT_NORMAL_HIT_DEFEND_BONUS_BOSS_OR_MORE', 18, (1, 2, 3, 4, 5), kinds(('body', 'shield', 'glove'))),
    ('POINT_SKILL_DEFEND_BONUS_BOSS_OR_MORE', 18, (1, 2, 3, 4, 5), kinds(('body', 'shield', 'glove'))),
    ('POINT_NORMAL_HIT_DAMAGE_BONUS_BOSS_OR_MORE', 18, (1, 2, 3, 4, 5), kinds(('neck', 'glove'))),
    ('POINT_SKILL_DAMAGE_BONUS_BOSS_OR_MORE', 18, (1, 2, 3, 4, 5), kinds(('neck', 'glove'))),
]
for p in NEW_POINTS[38:43]:
    # wiki: helmet, earrings, boots, shield 25% (no official row)
    NEW_ROWS.append((p[0], 18, (5, 10, 15, 20, 25), kinds(('head', 'ear', 'foots', 'shield'))))
NEW_ROWS += [
    # the gloves (wiki, no official row): fall resistance 75%, the lightning (no value), the cooldown lines 75%,
    # the built-in attributes 25%
    ('POINT_GLOVE_FALL_RESIST', 18, (15, 30, 45, 60, 75), kinds(('glove',))),
    ('POINT_GLOVE_LIGHTNING', 18, (1, 1, 1, 1, 1), kinds(('glove',))),
]
for p in NEW_POINTS[45:53]:
    NEW_ROWS.append((p[0], 0 if p[0] == 'POINT_GLOVE_COOLDOWN_ILIPUNGU' else 18, (15, 30, 45, 60, 75), kinds(('glove',))))
NEW_ROWS.append(('POINT_GLOVE_BASE_ATTR_PCT', 18, (5, 10, 15, 20, 25), kinds(('glove',))))
assert len(NEW_ROWS) == 54 and [r[0] for r in NEW_ROWS] == [p[0] for p in NEW_POINTS]
