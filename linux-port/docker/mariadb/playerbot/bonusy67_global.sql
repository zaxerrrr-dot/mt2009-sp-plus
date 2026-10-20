-- MT2009_PLUS_RARE_WIKI_V1: the 6th/7th bonus pool (world.item_attr_rare - Seon-Hae and the Enchant 71051/71052) of
-- M2_BONUS_MODE=global, as the wiki's "6. i 7. bonus" lists it (the owner, 20 October 2026: "change all 6/7 bonuses
-- according to the wiki"), every bonus of it this engine has. apply.sh runs it when the world switches from mt2009 to
-- global - while world.item_attr_rare_mt2009 is empty (it holds the mt2009 pool exactly while this one is in
-- item_attr_rare) - never twice in a row: an operator's own edit made while global is on stays. First the pool as it
-- is (mt2009's: the owner's 1 October table) goes to world.item_attr_rare_mt2009 - bonusy67_mt2009.sql puts it back.
-- Items keep every bonus they have in both modes (player.item is never touched).
--
-- The wiki gives the highest value per item kind only; the steps are the official table's (Owsap item_attr_rare,
-- 10 levels; this engine has 5: its levels 2/4/6/8/10, or 1-5 where it has five). A kind column is the highest of
-- the 5 levels that kind may reach (0 = never there): the value there is the wiki's maximum for that kind.
--   Max HP 100/200/300/400/500, Max SP 10/20/40/60/80, poison chance and poison resistance 1-5%, attack value and
--   magic attack value 8/15/25/35/50 - weapon, armour, helmet, shield, bracelet, boots, necklace, earrings, talisman;
--   strong against Metin stones 2/4/5/7/8% - weapon, necklace (and the gloves of the wiki);
--   damage to mana ("% obrazen bedzie dodanych do PE", our transfer of the damage taken to mana) 1-5% - weapon and
--   armour 5%, boots 3%;
--   block chance (the shield's "x% szans na zablokowanie obrazen od ataku") 1-5% - shield;
--   Sung Ma Will STR/HP/MOVE/IMMUNE +x% (POINT_SUNGMA_PER_*, 193-196) 2/4/6/8/15 - talisman 8% (level 4), gloves 15%.
-- Gloves (23000-23039), Talizmany Woli and Obrecz Jadeitu keep their own lines in the 6th/7th slots: the engine never
-- adds a pool bonus to them (glove column for the record only).
-- What the wiki has and this engine lacks: /opt/metin2/cache/yohara/bonusy-6-7-wiki.md (the owner decides).
DROP TABLE IF EXISTS world.item_attr_rare_mt2009;
CREATE TABLE world.item_attr_rare_mt2009 LIKE world.item_attr_rare;
START TRANSACTION;
INSERT INTO world.item_attr_rare_mt2009 SELECT * FROM world.item_attr_rare;
DELETE FROM world.item_attr_rare;
INSERT INTO world.item_attr_rare (apply,prob,lv1,lv2,lv3,lv4,lv5,weapon,body,wrist,foots,neck,head,shield,ear,costume_body,costume_hair,costume_weapon,pendant,glove) VALUES
('POINT_MAX_HP',18,100,200,300,400,500,5,5,5,5,5,5,5,5,0,0,0,5,0),
('POINT_MAX_SP',18,10,20,40,60,80,5,5,5,5,5,5,5,5,0,0,0,5,0),
('POINT_POISON_PCT',18,1,2,3,4,5,5,5,5,5,5,5,5,5,0,0,0,5,0),
('POINT_POISON_REDUCE',18,1,2,3,4,5,5,5,5,5,5,5,5,5,0,0,0,5,0),
('POINT_ATT_GRADE_BONUS',18,8,15,25,35,50,5,5,5,5,5,5,5,5,0,0,0,5,0),
('POINT_MAGIC_ATT_GRADE_BONUS',18,8,15,25,35,50,5,5,5,5,5,5,5,5,0,0,0,5,0),
('POINT_ATTBONUS_STONE',18,2,4,5,7,8,5,0,0,0,5,0,0,0,0,0,0,0,5),
('POINT_DAMAGE_SP_RECOVER',18,1,2,3,4,5,5,5,0,3,0,0,0,0,0,0,0,0,0),
('POINT_BLOCK',18,1,2,3,4,5,0,0,0,0,0,0,5,0,0,0,0,0,0),
('POINT_SUNGMA_PER_STR',18,2,4,6,8,15,0,0,0,0,0,0,0,0,0,0,0,4,5),
('POINT_SUNGMA_PER_HP',18,2,4,6,8,15,0,0,0,0,0,0,0,0,0,0,0,4,5),
('POINT_SUNGMA_PER_MOVE',18,2,4,6,8,15,0,0,0,0,0,0,0,0,0,0,0,4,5),
('POINT_SUNGMA_PER_IMMUNE',18,2,4,6,8,15,0,0,0,0,0,0,0,0,0,0,0,4,5);
COMMIT;
