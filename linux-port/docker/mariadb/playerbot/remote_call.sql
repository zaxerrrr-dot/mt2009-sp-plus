-- MT2009_PLUS_REMOTE_CALL_V1: Enasir - Dozorca / Handlarz (the remote call; the owner, 5 November 2026: "Dodaj jeszcze to";
-- server-patches/remotecall, the engine part linux-port/overlays/playerbot/src/game/src/remote_call.cpp, quest
-- remote_call). Every start (apply.sh), idempotent (INSERT IGNORE - a row the operator changed is kept).
--
-- The items (vnums of GF 26.1 - free in our world.item_proto on 5 November 2026; names as pl-wiki "System Enasira" /
-- "Dozorca Enasir (h)"): used from the inventory each adds its time to the character's service (the engine's use hook
-- takes them before the item's type - ITEM_QUEST like the title certificates, not GF's USE_AFFECT 706 / 707: the
-- services are real-time quest flags, not affects). value0 = the service (0 storeroom, 1 shop - the engine reads it by
-- vnum), value1 = its seconds (604800 = 7 days, GF's value); an item with socket0 > 0 adds socket0 seconds instead.
--   72368 Dozorca Enasir        storeroom, 7 days, no trade (GF: no drop / give / PK drop / private shop = 90240)
--   72369 Handlarz Enasir       shop,      7 days, no trade (the same)
--   72370 Dozorca Enasir (h)    storeroom, 7 days, tradeable (pl-wiki: NPC sale, trade, shop, drop, storeroom, stacking)
--   72371 Handlarz Enasir (h)   shop,      7 days, tradeable
-- Stackable (200), GF's LOG flag. The ItemShop's lines: apply.sh (ishop_once remote_call_50), after this file.
-- Enasir himself: mob 20874 (GF's vnum; client npclist "peddler_call"), an NPC that stands (NOMOVE), clicked = quest
-- remote_call - Kawuco's (20413) row with his name.
-- Client: client-patches/client-2.0.30/tools/remotecall (the same records, item_list, itemdesc, the mob's name).
SET NAMES utf8mb4;
INSERT IGNORE INTO world.item_proto (`vnum`,`name`,`locale_name`,`type`,`subtype`,`stack`,`weight`,`size`,`antiflag`,`flag`,`wearflag`,`immuneflag`,`gold`,`shop_buy_price`,`refined_vnum`,`refine_set`,`magic_pct`,`specular`,`socket_pct`,`addon_type`,`limittype0`,`limitvalue0`,`limittype1`,`limitvalue1`,`applytype0`,`applyvalue0`,`applytype1`,`applyvalue1`,`applytype2`,`applyvalue2`,`value0`,`value1`,`value2`,`value3`,`value4`,`value5`,`socket0`,`socket1`,`socket2`,`socket3`,`socket4`,`socket5`) VALUES
(72368,'Storekeeper Enasir','Dozorca Enasir',18,0,200,0,1,90240,8196,0,'',0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,604800,0,0,0,0,-1,-1,-1,-1,-1,-1),
(72369,'Merchant Enasir','Handlarz Enasir',18,0,200,0,1,90240,8196,0,'',0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,1,604800,0,0,0,0,-1,-1,-1,-1,-1,-1),
(72370,'Storekeeper Enasir (t)','Dozorca Enasir (h)',18,0,200,0,1,0,8196,0,'',0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,604800,0,0,0,0,-1,-1,-1,-1,-1,-1),
(72371,'Merchant Enasir (t)','Handlarz Enasir (h)',18,0,200,0,1,0,8196,0,'',0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,1,604800,0,0,0,0,-1,-1,-1,-1,-1,-1);
INSERT IGNORE INTO world.mob_proto (`vnum`,`name`,`locale_name`,`rank`,`type`,`battle_type`,`level`,`size`,`ai_flag`,`mount_capacity`,`setRaceFlag`,`setImmuneFlag`,`empire`,`folder`,`on_click`,`st`,`dx`,`ht`,`iq`,`damage_min`,`damage_max`,`max_hp`,`regen_cycle`,`regen_percent`,`gold_min`,`gold_max`,`exp`,`def`,`attack_speed`,`move_speed`,`aggressive_hp_pct`,`aggressive_sight`,`attack_range`,`drop_item`,`resurrection_vnum`,`enchant_curse`,`enchant_slow`,`enchant_poison`,`enchant_stun`,`enchant_critical`,`enchant_penetrate`,`enchant_fire`,`enchant_root`,`resist_sword`,`resist_twohand`,`resist_dagger`,`resist_bell`,`resist_fan`,`resist_bow`,`resist_fire`,`resist_elect`,`resist_magic`,`resist_wind`,`resist_poison`,`dam_multiply`,`summon`,`drain_sp`,`mob_color`,`polymorph_item`,`skill_level0`,`skill_vnum0`,`skill_level1`,`skill_vnum1`,`skill_level2`,`skill_vnum2`,`skill_level3`,`skill_vnum3`,`skill_level4`,`skill_vnum4`,`sp_berserk`,`sp_stoneskin`,`sp_godspeed`,`sp_deathblow`,`sp_revive`) VALUES
(20874,'Enasir','Enasir',5,1,0,1,'NONE','NOMOVE',0,'','STUN,SLOW,CURSE,TERROR',0,'',2,0,0,0,0,0,0,120,3,1,0,0,10,4,100,100,0,2000,175,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0.0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0);
