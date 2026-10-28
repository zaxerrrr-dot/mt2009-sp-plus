-- MT2009_PLUS_COSTUME_ATTR_GLOBAL_V1 (the owner, 28 October 2026: "Zmien bonusy w wizerunkach broni, fryzurach i
-- kostiumach na takie jak na globalu; maksymalne wartosci takie same jak na innym eq, np. Max PZ 2000 jak na zbroi"):
-- the bonus pools of Wizerunki broni+ (costume_weapon), Fryzury+ (costume_hair) and Kostiumy+ (costume_body) - what
-- 70063 Transformuj Kostium (1-3 bonuses) and 70064 Zaczaruj Kostium (the same count again) roll - as the global
-- wiki lists them. The engine has one row per bonus (prob, lv1..lv5) and a highest level per kind of item; a costume
-- line takes the values of the row, so its highest level here is the highest the bonus reaches on the ordinary
-- equipment (weapon, armour, bracelet, boots, necklace, helmet, shield, earrings) in this world's bonus mode - Max HP
-- 2000 as on the armour in global mode (1500 in mt2009 mode), the stats 12, the monsters' races 20%, the weapon
-- resistances 15%... A bonus no ordinary piece rolls: level 5, except fire / lightning / wind resistance (mt2009
-- mode: on the talisman only, 5/10/15/20/25) - level 3, 15% as the global maximum.
-- Not in this engine (no such point): bleeding attack (weapon skin, hairstyle) and resistance to claws (weapon skin,
-- costume) - the global lists have them for the Lycan, whom this server does not have.
-- The weapon skin's list is the wiki's full list (the owner's second screenshot, ending with the claws): no attack
-- speed and no double items there.
--
-- apply.sh runs it once per world (marker costume_attr_global_v1 in world.mt2009_plus_once) and again after every
-- switch of M2_BONUS_MODE (bonusy_global.sql / bonusy_mt2009.sql rewrite the rows the levels are read from); a later
-- edit of the costume columns in the panel stays until then. Items keep the bonuses they have (player.item is never
-- touched) - a line the pools no longer have stays on its costume until the costume is rolled again.
START TRANSACTION;
-- mt2009 mode has no row for the chance of an experience bonus (bonusy_global.sql adds it in global mode): a row
-- for the weapon skin only, every ordinary kind 0 (bonusy_global.sql gives it its global kinds when the world
-- switches).
INSERT INTO world.item_attr (apply, prob, lv1, lv2, lv3, lv4, lv5, weapon, body, wrist, foots, neck, head, shield, ear)
SELECT n.a, n.p, 2, 4, 6, 8, 20, 0, 0, 0, 0, 0, 0, 0, 0 FROM (
    SELECT 'POINT_EXP_DOUBLE_BONUS' AS a, 10 AS p) AS n
 WHERE NOT EXISTS (SELECT 1 FROM world.item_attr AS x WHERE x.apply = n.a);
UPDATE world.item_attr SET costume_body = 0, costume_hair = 0, costume_weapon = 0;
-- Wizerunek broni+: Max HP, Max SP, Vitality, Intelligence, Strength, Dexterity, casting speed, poison, stun, slow,
-- arrow dodge, movement speed, critical and piercing hit, strong against animals, half-humans, orcs, mystics, undead
-- and devils, double yang, experience bonus, resistance to swords, two-handed weapons, daggers, arrows, bells, fans.
UPDATE world.item_attr
   SET costume_weapon = LEAST(5, IF(GREATEST(weapon, body, wrist, foots, neck, head, shield, ear) > 0,
                                    GREATEST(weapon, body, wrist, foots, neck, head, shield, ear), 5))
 WHERE apply IN ('POINT_MAX_HP', 'POINT_MAX_SP', 'POINT_HT', 'POINT_IQ', 'POINT_ST', 'POINT_DX',
    'POINT_CASTING_SPEED', 'POINT_POISON_PCT', 'POINT_STUN_PCT', 'POINT_SLOW_PCT', 'POINT_DODGE', 'POINT_MOV_SPEED',
    'POINT_CRITICAL_PCT', 'POINT_PENETRATE_PCT', 'POINT_ATTBONUS_ANIMAL', 'POINT_ATTBONUS_HUMAN', 'POINT_ATTBONUS_ORC',
    'POINT_ATTBONUS_MILGYO', 'POINT_ATTBONUS_UNDEAD', 'POINT_ATTBONUS_DEVIL', 'POINT_GOLD_DOUBLE_BONUS',
    'POINT_EXP_DOUBLE_BONUS', 'POINT_RESIST_SWORD', 'POINT_RESIST_TWOHAND', 'POINT_RESIST_DAGGER', 'POINT_RESIST_BOW',
    'POINT_RESIST_BELL', 'POINT_RESIST_FAN');
-- Fryzura+: resistance to wind, fire, lightning and magic, strong against mystics, animals, undead, half-humans, orcs
-- and devils, arrow dodge, damage to SP and to HP, poison, HP and SP regeneration, attack speed.
UPDATE world.item_attr
   SET costume_hair = LEAST(5, IF(GREATEST(weapon, body, wrist, foots, neck, head, shield, ear) > 0,
                                  GREATEST(weapon, body, wrist, foots, neck, head, shield, ear),
                                  IF(apply IN ('POINT_RESIST_FIRE', 'POINT_RESIST_ELEC', 'POINT_RESIST_WIND'), 3, 5)))
 WHERE apply IN ('POINT_RESIST_WIND', 'POINT_RESIST_FIRE', 'POINT_RESIST_ELEC', 'POINT_RESIST_MAGIC',
    'POINT_ATTBONUS_MILGYO', 'POINT_ATTBONUS_ANIMAL', 'POINT_ATTBONUS_UNDEAD', 'POINT_ATTBONUS_HUMAN',
    'POINT_ATTBONUS_ORC', 'POINT_ATTBONUS_DEVIL', 'POINT_DODGE', 'POINT_STEAL_SP', 'POINT_STEAL_HP', 'POINT_POISON_PCT',
    'POINT_HP_REGEN', 'POINT_SP_REGEN', 'POINT_ATT_SPEED');
-- Kostium+: resistance to bells, fans, daggers, arrows, two-handed weapons and swords, attack value, resistance to
-- lightning, wind and fire, damage to SP and to HP, reflecting a blow, Max HP, Max SP, casting speed, resistance to
-- magic.
UPDATE world.item_attr
   SET costume_body = LEAST(5, IF(GREATEST(weapon, body, wrist, foots, neck, head, shield, ear) > 0,
                                  GREATEST(weapon, body, wrist, foots, neck, head, shield, ear),
                                  IF(apply IN ('POINT_RESIST_FIRE', 'POINT_RESIST_ELEC', 'POINT_RESIST_WIND'), 3, 5)))
 WHERE apply IN ('POINT_RESIST_BELL', 'POINT_RESIST_FAN', 'POINT_RESIST_DAGGER', 'POINT_RESIST_BOW',
    'POINT_RESIST_TWOHAND', 'POINT_RESIST_SWORD', 'POINT_ATT_GRADE_BONUS', 'POINT_RESIST_ELEC', 'POINT_RESIST_WIND',
    'POINT_RESIST_FIRE', 'POINT_STEAL_SP', 'POINT_STEAL_HP', 'POINT_REFLECT_MELEE', 'POINT_MAX_HP', 'POINT_MAX_SP',
    'POINT_CASTING_SPEED', 'POINT_RESIST_MAGIC');
INSERT IGNORE INTO world.mt2009_plus_once (name) VALUES ('costume_attr_global_v1');
COMMIT;
