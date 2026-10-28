-- MT2009_PLUS_GUILDSYS_V1: the guild system update (server-patches/guildsys/README.md, guildsys.cpp; on Guild Systems
-- compiled by Nazox). Every start (apply.sh), idempotent - no DROP, nothing of a guild is rewritten.
--
-- 1) The dates the Balathor port asks for (guild >= 24 h, the player in it >= 24 h):
--      player.guild.create_time         unix time the guild was founded
--      player.guild_member.join_time    unix time the member joined (a member who leaves and comes back: a new row)
--    INVISIBLE columns: the db core's positional "INSERT INTO guild_member VALUES(pid, guild, grade, 0, 0)" and every
--    SELECT * stay as they are. A row from before this file has 0 (an old guild / member - the 24 h rules pass);
--    a new row gets UNIX_TIMESTAMP() from the database itself (the column's default), so no engine INSERT changes.
-- 2) Balathor's guild skills on the free places 158-160 of the guild skill array (GF's vnums: 158 jin baekryong-ui
--    gaho, 159 gyeorui, 160 gyeongo): max level 10, only from their books (CGuild::SkillLevelUp refuses a point);
--    the engine gives the members on the caster's map an immunity affect for the duration (guildsys.cpp: 10 % a
--    level). The client's rows are tools/guildsys (skilldesc / skilltable) - change both together.
-- 3) The books (ITEM_USE / USE_SPECIAL, char_item.cpp -> GuildSysUseItem; the guild leader's):
--      50344 Ksiega: Burza Balathora, 50345 Ksiega: Wola Balathora, 50346 Ksiega: Nieugietosc Balathora (+1 level)
--      50347 Ksiega Zapomnienia Gildii (every point spent on the skills 151-157 back)
--    INSERT IGNORE - a row the operator changed (the Seban panel) is kept. Not sold anywhere: Balathor's chests give
--    the three books (the Balathor port), the forget book is the owner's to place (ItemShop / NPC).
SET NAMES utf8mb4;

ALTER TABLE player.guild
  ADD COLUMN IF NOT EXISTS `create_time` int(10) unsigned NOT NULL DEFAULT 0 INVISIBLE COMMENT 'MT2009_PLUS_GUILDSYS_V1';
ALTER TABLE player.guild ALTER COLUMN `create_time` SET DEFAULT (UNIX_TIMESTAMP());

ALTER TABLE player.guild_member
  ADD COLUMN IF NOT EXISTS `join_time` int(10) unsigned NOT NULL DEFAULT 0 INVISIBLE COMMENT 'MT2009_PLUS_GUILDSYS_V1';
ALTER TABLE player.guild_member ALTER COLUMN `join_time` SET DEFAULT (UNIX_TIMESTAMP());

INSERT INTO world.skill_proto (dwVnum, szName, bType, bLevelStep, bMaxLevel, bLevelLimit, szPointOn, szPointPoly, szSPCostPoly, szDurationPoly, szDurationSPCostPoly, szCooldownPoly, szMasterBonusPoly, szAttackGradePoly, setFlag, setAffectFlag, szPointOn2, szPointPoly2, szDurationPoly2, setAffectFlag2, szPointOn3, szPointPoly3, szDurationPoly3, setAffectFlag3, szGrandMasterAddSPCostPoly, prerequisiteSkillVnum, prerequisiteSkillLevel, eSkillType, iMaxHit, szSplashAroundDamageAdjustPoly, dwTargetRange, dwSplashRange) VALUES
  (158, 'BALATHOR_STORM', 0, 1, 10, 0, 'NONE', '', '100+150*k', '300+429*k', '', '600-300*k', '', '', '', 'NONE', 'NONE', '', '', 'NONE', '', '', '', 'NONE', '', 0, 0, 'NORMAL', 0, '1', 0, 0),
  (159, 'BALATHOR_WILL', 0, 1, 10, 0, 'NONE', '', '100+150*k', '300+429*k', '', '600-300*k', '', '', '', 'NONE', 'NONE', '', '', 'NONE', '', '', '', 'NONE', '', 0, 0, 'NORMAL', 0, '1', 0, 0),
  (160, 'BALATHOR_FIRMNESS', 0, 1, 10, 0, 'NONE', '', '100+150*k', '300+429*k', '', '600-300*k', '', '', '', 'NONE', 'NONE', '', '', 'NONE', '', '', '', 'NONE', '', 0, 0, 'NORMAL', 0, '1', 0, 0)
  ON DUPLICATE KEY UPDATE szName = VALUES(szName), bType = VALUES(bType), bLevelStep = VALUES(bLevelStep), bMaxLevel = VALUES(bMaxLevel), bLevelLimit = VALUES(bLevelLimit), szPointOn = VALUES(szPointOn), szPointPoly = VALUES(szPointPoly), szSPCostPoly = VALUES(szSPCostPoly), szDurationPoly = VALUES(szDurationPoly), szDurationSPCostPoly = VALUES(szDurationSPCostPoly), szCooldownPoly = VALUES(szCooldownPoly), szMasterBonusPoly = VALUES(szMasterBonusPoly), szAttackGradePoly = VALUES(szAttackGradePoly), setFlag = VALUES(setFlag), setAffectFlag = VALUES(setAffectFlag), szPointOn2 = VALUES(szPointOn2), szPointPoly2 = VALUES(szPointPoly2), szDurationPoly2 = VALUES(szDurationPoly2), setAffectFlag2 = VALUES(setAffectFlag2), szPointOn3 = VALUES(szPointOn3), szPointPoly3 = VALUES(szPointPoly3), szDurationPoly3 = VALUES(szDurationPoly3), setAffectFlag3 = VALUES(setAffectFlag3), szGrandMasterAddSPCostPoly = VALUES(szGrandMasterAddSPCostPoly), prerequisiteSkillVnum = VALUES(prerequisiteSkillVnum), prerequisiteSkillLevel = VALUES(prerequisiteSkillLevel), eSkillType = VALUES(eSkillType), iMaxHit = VALUES(iMaxHit), szSplashAroundDamageAdjustPoly = VALUES(szSplashAroundDamageAdjustPoly), dwTargetRange = VALUES(dwTargetRange), dwSplashRange = VALUES(dwSplashRange);

INSERT IGNORE INTO world.item_proto (`vnum`,`name`,`locale_name`,`type`,`subtype`,`stack`,`weight`,`size`,`antiflag`,`flag`,`wearflag`,`immuneflag`,`gold`,`shop_buy_price`,`refined_vnum`,`refine_set`,`magic_pct`,`specular`,`socket_pct`,`addon_type`,`limittype0`,`limitvalue0`,`limittype1`,`limitvalue1`,`applytype0`,`applyvalue0`,`applytype1`,`applyvalue1`,`applytype2`,`applyvalue2`,`value0`,`value1`,`value2`,`value3`,`value4`,`value5`,`socket0`,`socket1`,`socket2`,`socket3`,`socket4`,`socket5`) VALUES
(50344,'Balathor Storm Book',_cp1250 X'4B7369EA67613A204275727A612042616C6174686F7261',3,10,200,0,1,0,4,0,'',0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,158,0,0,0,0,0,0,0,0,0,0,0),
(50345,'Balathor Will Book',_cp1250 X'4B7369EA67613A20576F6C612042616C6174686F7261',3,10,200,0,1,0,4,0,'',0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,159,0,0,0,0,0,0,0,0,0,0,0),
(50346,'Balathor Firmness Book',_cp1250 X'4B7369EA67613A204E6965756769EA746F9CE62042616C6174686F7261',3,10,200,0,1,0,4,0,'',0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,160,0,0,0,0,0,0,0,0,0,0,0),
(50347,'Guild Forget Book',_cp1250 X'4B7369EA6761205A61706F6D6E69656E69612047696C646969',3,10,200,0,1,0,4,0,'',0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0);
