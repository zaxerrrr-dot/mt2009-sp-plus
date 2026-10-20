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

# (point, Polish name as the wiki has it - root/localeinfo_point.py, cp1250 there; the panel's name; unit)
NEW_POINTS = [
    ('POINT_HIT_BUFF_ENCHANT_FIRE', u'Otrzymujesz moc ognia na %d sek. w walce', u'Moc ognia w walce', u's'),
    ('POINT_HIT_BUFF_ENCHANT_ICE', u'Otrzymujesz moc lodu na %d sek. w walce', u'Moc lodu w walce', u's'),
    ('POINT_HIT_BUFF_ENCHANT_ELEC', u'Otrzymujesz moc błyskawic na %d sek. w walce', u'Moc błyskawic w walce', u's'),
    ('POINT_HIT_BUFF_ENCHANT_WIND', u'Otrzymujesz moc wiatru na %d sek. w walce', u'Moc wiatru w walce', u's'),
    ('POINT_HIT_BUFF_ENCHANT_DARK', u'Otrzymujesz moc mroku na %d sek. w walce', u'Moc mroku w walce', u's'),
    ('POINT_HIT_BUFF_ENCHANT_EARTH', u'Otrzymujesz moc ziemi na %d sek. w walce', u'Moc ziemi w walce', u's'),
    ('POINT_HIT_BUFF_RESIST_FIRE', u'Otrzymujesz odporność na ogień na %d sek. w walce', u'Odporność na ogień w walce', u's'),
    ('POINT_HIT_BUFF_RESIST_ICE', u'Otrzymujesz odporność na lód na %d sek. w walce', u'Odporność na lód w walce', u's'),
    ('POINT_HIT_BUFF_RESIST_ELEC', u'Otrzymujesz odporność na błyskawice na %d sek. w walce', u'Odporność na błyskawice w walce', u's'),
    ('POINT_HIT_BUFF_RESIST_WIND', u'Otrzymujesz odporność na wiatr na %d sek. w walce', u'Odporność na wiatr w walce', u's'),
    ('POINT_HIT_BUFF_RESIST_DARK', u'Otrzymujesz odporność na mrok na %d sek. w walce', u'Odporność na mrok w walce', u's'),
    ('POINT_HIT_BUFF_RESIST_EARTH', u'Otrzymujesz odporność na ziemię na %d sek. w walce', u'Odporność na ziemię w walce', u's'),
    ('POINT_ATTBONUS_PER_MONSTER', u'Silny przeciwko potworom (+%d%% łącznej wartości)', u'Silny przeciw potworom (+% łącznej)', u'%'),
    ('POINT_ATTBONUS_PER_STONE', u'Siła w walce z kamieniami Metin (+%d%% łącznej wartości)', u'Silny przeciw Metinom (+% łącznej)', u'%'),
    ('POINT_ATTBONUS_PER_CZ', u'Silny przeciwko potworom Zodiaku (+%d%% łącznej wartości)', u'Silny przeciw potworom Zodiaku (+% łącznej)', u'%'),
    ('POINT_ATTBONUS_PER_MILGYO', u'Siła w walce z mistykami (+%d%% łącznej wartości)', u'Silny przeciw mistykom (+% łącznej)', u'%'),
    ('POINT_ATTBONUS_PER_ORC', u'Siła w walce z orkami (+%d%% łącznej wartości)', u'Silny przeciw orkom (+% łącznej)', u'%'),
    ('POINT_ATTBONUS_PER_DEVIL', u'Siła w walce z diabłami (+%d%% łącznej wartości)', u'Silny przeciw diabłom (+% łącznej)', u'%'),
    ('POINT_ATTBONUS_PER_INSECT', u'Siła w walce z insektami (+%d%% łącznej wartości)', u'Silny przeciw insektom (+% łącznej)', u'%'),
    ('POINT_ATTBONUS_PER_ANIMAL', u'Siła w walce ze zwierzętami (+%d%% łącznej wartości)', u'Silny przeciw zwierzętom (+% łącznej)', u'%'),
    ('POINT_ENCHANT_PER_ELECT', u'Siła Błyskawic (+%d%% łącznej wartości)', u'Siła Błyskawic (+% łącznej)', u'%'),
    ('POINT_ENCHANT_PER_FIRE', u'Siła Ognia (+%d%% łącznej wartości)', u'Siła Ognia (+% łącznej)', u'%'),
    ('POINT_ENCHANT_PER_ICE', u'Siła Lodu (+%d%% łącznej wartości)', u'Siła Lodu (+% łącznej)', u'%'),
    ('POINT_ENCHANT_PER_WIND', u'Siła Wiatru (+%d%% łącznej wartości)', u'Siła Wiatru (+% łącznej)', u'%'),
    ('POINT_ENCHANT_PER_EARTH', u'Siła Ziemi (+%d%% łącznej wartości)', u'Siła Ziemi (+% łącznej)', u'%'),
    ('POINT_ENCHANT_PER_DARK', u'Siła Mroku (+%d%% łącznej wartości)', u'Siła Mroku (+% łącznej)', u'%'),
    ('POINT_RESIST_PER_HUMAN', u'Odporność na ludzi (+%d%% łącznej wartości)', u'Odporność na ludzi (+% łącznej)', u'%'),
    ('POINT_RESIST_PER_MAGIC', u'Odporność na magię (+%d%% łącznej wartości)', u'Odporność na magię (+% łącznej)', u'%'),
    ('POINT_RESIST_PER_ELEC', u'Odporność na błyskawice (+%d%% łącznej wartości)', u'Odporność na błyskawice (+% łącznej)', u'%'),
    ('POINT_RESIST_PER_FIRE', u'Odporność na ogień (+%d%% łącznej wartości)', u'Odporność na ogień (+% łącznej)', u'%'),
    ('POINT_RESIST_PER_ICE', u'Odporność na lód (+%d%% łącznej wartości)', u'Odporność na lód (+% łącznej)', u'%'),
    ('POINT_RESIST_PER_WIND', u'Odporność na wiatr (+%d%% łącznej wartości)', u'Odporność na wiatr (+% łącznej)', u'%'),
    ('POINT_RESIST_PER_EARTH', u'Odporność na ziemię (+%d%% łącznej wartości)', u'Odporność na ziemię (+% łącznej)', u'%'),
    ('POINT_RESIST_PER_DARK', u'Odporność na mrok (+%d%% łącznej wartości)', u'Odporność na mrok (+% łącznej)', u'%'),
    ('POINT_NORMAL_HIT_DEFEND_BONUS_BOSS_OR_MORE', u'Obrażenia od ataku bossów -%d%%', u'Obrażenia od ataku bossów (mniej)', u'%'),
    ('POINT_SKILL_DEFEND_BONUS_BOSS_OR_MORE', u'Obrażenia od umiejętności bossów -%d%%', u'Obrażenia od umiejętności bossów (mniej)', u'%'),
    ('POINT_NORMAL_HIT_DAMAGE_BONUS_BOSS_OR_MORE', u'Obrażenia od ataku przeciwko bossom +%d%%', u'Obrażenia od ataku przeciw bossom', u'%'),
    ('POINT_SKILL_DAMAGE_BONUS_BOSS_OR_MORE', u'Obrażenia od umiejętności przeciwko bossom +%d%%', u'Obrażenia od umiejętności przeciw bossom', u'%'),
    ('POINT_FIRST_ATTRIBUTE_BONUS', u'1. dodany bonus +%d%%', u'1. dodany bonus', u'%'),
    ('POINT_SECOND_ATTRIBUTE_BONUS', u'2. dodany bonus +%d%%', u'2. dodany bonus', u'%'),
    ('POINT_THIRD_ATTRIBUTE_BONUS', u'3. dodany bonus +%d%%', u'3. dodany bonus', u'%'),
    ('POINT_FOURTH_ATTRIBUTE_BONUS', u'4. dodany bonus +%d%%', u'4. dodany bonus', u'%'),
    ('POINT_FIFTH_ATTRIBUTE_BONUS', u'5. dodany bonus +%d%%', u'5. dodany bonus', u'%'),
    ('POINT_GLOVE_FALL_RESIST', u'Podczas walki %d%% szans na odporność na upadek (regeneracja 60 sek.)', u'Rękawice: odporność na upadek w walce', u'%'),
    ('POINT_GLOVE_LIGHTNING', u'Atakuj potwory w pobliżu błyskawicami (regeneracja 15 sek.)', u'Rękawice: błyskawice na potwory w pobliżu', u''),
    ('POINT_GLOVE_COOLDOWN_FINISH', u'Trzęsienie: %d%% szans na kolejną regenerację krótszą o 5 sek.', u'Rękawice: Trzęsienie -5 s odnowienia', u'%'),
    ('POINT_GLOVE_COOLDOWN_ILGWANGPYO', u'Światło Gwiazd: %d%% szans na kolejną regenerację krótszą o 5 sek.', u'Rękawice: Światło Gwiazd -5 s odnowienia', u'%'),
    ('POINT_GLOVE_COOLDOWN_PUNGLOEPO', u'Strzał Wichury: %d%% szans na kolejną regenerację krótszą o 5 sek.', u'Rękawice: Strzał Wichury -5 s odnowienia', u'%'),
    ('POINT_GLOVE_COOLDOWN_GEOMAGGWI', u'Piekielny Cios: %d%% szans na kolejną regenerację krótszą o 5 sek.', u'Rękawice: Piekielny Cios -5 s odnowienia', u'%'),
    ('POINT_GLOVE_COOLDOWN_MABEOBAGGWI', u'Fala Śmierci: %d%% szans na kolejną regenerację krótszą o 5 sek.', u'Rękawice: Fala Śmierci -5 s odnowienia', u'%'),
    ('POINT_GLOVE_COOLDOWN_METEO', u'Meteor: %d%% szans na kolejną regenerację krótszą o 5 sek.', u'Rękawice: Meteor -5 s odnowienia', u'%'),
    ('POINT_GLOVE_COOLDOWN_CHEONUN', u'Tarcza Eteru: %d%% szans na kolejną regenerację krótszą o 5 sek.', u'Rękawice: Tarcza Eteru -5 s odnowienia', u'%'),
    ('POINT_GLOVE_COOLDOWN_ILIPUNGU', u'Burza Szponów: %d%% szans na kolejną regenerację krótszą o 5 sek.', u'Rękawice: Burza Szponów -5 s odnowienia', u'%'),
    ('POINT_GLOVE_BASE_ATTR_PCT', u'Atrybuty podstawowe rękawic +%d%%', u'Rękawice: atrybuty podstawowe', u'%'),
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
