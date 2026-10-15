-- MT2009_PLUS_KAWUCO_V1 (the owner, 15 October 2026): Kawuco (20413), the boots NPC of Przyladek Smoczego Ognia (the
-- pl-wiki's "Kawuco": 301, 662,1224; game/Dockerfile spawns him, quest/kawuco.quest opens his cube window, cube.buty.txt
-- holds his recipes). Owsap v6.2.6 db/mob_proto.txt's row (the official vnum; an NPC, NOMOVE, level 1) in our columns,
-- as Theowahdan's in yohara_maps.sql. The client draws him as japanese_pirate_2 (its npclist has the line; tools/kawuco
-- names him in its mob_proto). Every start (apply.sh), idempotent: INSERT IGNORE - a row the operator changed is kept.
-- 20413 checked free in our world.mob_proto (15 October 2026).
SET NAMES utf8mb4;

INSERT IGNORE INTO world.mob_proto (`vnum`,`name`,`locale_name`,`rank`,`type`,`battle_type`,`level`,`size`,`ai_flag`,`mount_capacity`,`setRaceFlag`,`setImmuneFlag`,`empire`,`folder`,`on_click`,`st`,`dx`,`ht`,`iq`,`damage_min`,`damage_max`,`max_hp`,`regen_cycle`,`regen_percent`,`gold_min`,`gold_max`,`exp`,`def`,`attack_speed`,`move_speed`,`aggressive_hp_pct`,`aggressive_sight`,`attack_range`,`drop_item`,`resurrection_vnum`,`enchant_curse`,`enchant_slow`,`enchant_poison`,`enchant_stun`,`enchant_critical`,`enchant_penetrate`,`enchant_fire`,`enchant_root`,`resist_sword`,`resist_twohand`,`resist_dagger`,`resist_bell`,`resist_fan`,`resist_bow`,`resist_fire`,`resist_elect`,`resist_magic`,`resist_wind`,`resist_poison`,`dam_multiply`,`summon`,`drain_sp`,`mob_color`,`polymorph_item`,`skill_level0`,`skill_vnum0`,`skill_level1`,`skill_vnum1`,`skill_level2`,`skill_vnum2`,`skill_level3`,`skill_vnum3`,`skill_level4`,`skill_vnum4`,`sp_berserk`,`sp_stoneskin`,`sp_godspeed`,`sp_deathblow`,`sp_revive`) VALUES
(20413,'Kawuco','Kawuco',5,1,0,1,'NONE','NOMOVE',0,'','STUN,SLOW,CURSE,TERROR',0,'',2,0,0,0,0,0,0,120,3,1,0,0,10,4,100,100,0,2000,175,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0.0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0);
