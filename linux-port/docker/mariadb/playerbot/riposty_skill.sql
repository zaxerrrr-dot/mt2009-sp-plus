-- MT2009_PLUS_RIPOSTY_V1: Riposty i Dopalacze - the passive 7th and 8th skills of every character (pl-wiki "Umiejetnosci -
-- Riposty i Dopalacze"; server-patches/riposty/README.md). skill_proto 221-228 (Riposta: Wir Miecza, Zasadzka, Uderzenie
-- Palcem, Strzelajacy Smok, Duchowe Uderzenie, Ognista Strzala, Mroczne Uderzenie, Przywolanie Blyskawicy) and 236-243
-- (Dopalacz: the same skills) - Owsap's rows (db/data/player.sql): type 6 (the class skill points, SkillLevelUp's
-- POINT_SKILL), levels 0-40 by points to M1, books, Kamien Duchowy+ (quest riposty). The polys 24*k / 16*k are only
-- what GF's rows say: the engine takes the wiki's values from playerbot_riposty.cpp (riposty::Percent - GF's skill
-- power table, whatever ours is). The Lycan's 229 / 244 are left out (no Lycan here). Idempotent: the rows are
-- written whole every run.
-- Zwoj Zmiany Treningu (71000) is yohara_items.sql's, its ItemShop offer riposty_itemshop.sql.
SET NAMES utf8mb4;
INSERT INTO world.skill_proto (dwVnum, szName, bType, bLevelStep, bMaxLevel, bLevelLimit, szPointOn, szPointPoly, szSPCostPoly, szDurationPoly, szDurationSPCostPoly, szCooldownPoly, szMasterBonusPoly, szAttackGradePoly, setFlag, setAffectFlag, szPointOn2, szPointPoly2, szDurationPoly2, setAffectFlag2, szPointOn3, szPointPoly3, szDurationPoly3, setAffectFlag3, szGrandMasterAddSPCostPoly, prerequisiteSkillVnum, prerequisiteSkillLevel, eSkillType, iMaxHit, szSplashAroundDamageAdjustPoly, dwTargetRange, dwSplashRange)
  VALUES (221, 'ANTI_PALBANG', 6, 1, 1, 0, 'NONE', '24*k', '', '', '', '', '24*k', '', '', 'NONE', 'NONE', '', '', 'NONE', '', '', '', 'NONE', '', 0, 0, 'NORMAL', 1, '1', 1000, 0),
  (222, 'ANTI_AMSEOP', 6, 1, 1, 0, 'NONE', '24*k', '', '', '', '', '24*k', '', '', 'NONE', 'NONE', '', '', 'NONE', '', '', '', 'NONE', '', 0, 0, 'NORMAL', 1, '1', 1000, 0),
  (223, 'ANTI_SWAERYUNG', 6, 1, 1, 0, 'NONE', '24*k', '', '', '', '', '24*k', '', '', 'NONE', 'NONE', '', '', 'NONE', '', '', '', 'NONE', '', 0, 0, 'NORMAL', 1, '1', 1000, 0),
  (224, 'ANTI_YONGBI', 6, 1, 1, 0, 'NONE', '24*k', '', '', '', '', '24*k', '', '', 'NONE', 'NONE', '', '', 'NONE', '', '', '', 'NONE', '', 0, 0, 'NORMAL', 1, '1', 1000, 0),
  (225, 'ANTI_GIGONGCHAM', 6, 1, 1, 0, 'NONE', '24*k', '', '', '', '', '24*k', '', '', 'NONE', 'NONE', '', '', 'NONE', '', '', '', 'NONE', '', 0, 0, 'NORMAL', 1, '1', 1000, 0),
  (226, 'ANTI_HWAJO', 6, 1, 1, 0, 'NONE', '24*k', '', '', '', '', '24*k', '', '', 'NONE', 'NONE', '', '', 'NONE', '', '', '', 'NONE', '', 0, 0, 'NORMAL', 1, '1', 1000, 0),
  (227, 'ANTI_MARYUNG', 6, 1, 1, 0, 'NONE', '24*k', '', '', '', '', '24*k', '', '', 'NONE', 'NONE', '', '', 'NONE', '', '', '', 'NONE', '', 0, 0, 'NORMAL', 1, '1', 1000, 0),
  (228, 'ANTI_BYEURAK', 6, 1, 1, 0, 'NONE', '24*k', '', '', '', '', '24*k', '', '', 'NONE', 'NONE', '', '', 'NONE', '', '', '', 'NONE', '', 0, 0, 'NORMAL', 1, '1', 1000, 0),
  (236, 'HELP_PALBANG', 6, 1, 1, 0, 'NONE', '16*k', '', '', '', '', '16*k', '', '', 'NONE', 'NONE', '', '', 'NONE', '', '', '', 'NONE', '', 0, 0, 'NORMAL', 1, '1', 1000, 0),
  (237, 'HELP_AMSEOP', 6, 1, 1, 0, 'NONE', '16*k', '', '', '', '', '16*k', '', '', 'NONE', 'NONE', '', '', 'NONE', '', '', '', 'NONE', '', 0, 0, 'NORMAL', 1, '1', 1000, 0),
  (238, 'HELP_SWAERYUNG', 6, 1, 1, 0, 'NONE', '16*k', '', '', '', '', '16*k', '', '', 'NONE', 'NONE', '', '', 'NONE', '', '', '', 'NONE', '', 0, 0, 'NORMAL', 1, '1', 1000, 0),
  (239, 'HELP_YONGBI', 6, 1, 1, 0, 'NONE', '16*k', '', '', '', '', '16*k', '', '', 'NONE', 'NONE', '', '', 'NONE', '', '', '', 'NONE', '', 0, 0, 'NORMAL', 1, '1', 1000, 0),
  (240, 'HELP_GIGONGCHAM', 6, 1, 1, 0, 'NONE', '16*k', '', '', '', '', '16*k', '', '', 'NONE', 'NONE', '', '', 'NONE', '', '', '', 'NONE', '', 0, 0, 'NORMAL', 1, '1', 1000, 0),
  (241, 'HELP_HWAJO', 6, 1, 1, 0, 'NONE', '16*k', '', '', '', '', '16*k', '', '', 'NONE', 'NONE', '', '', 'NONE', '', '', '', 'NONE', '', 0, 0, 'NORMAL', 1, '1', 1000, 0),
  (242, 'HELP_MARYUNG', 6, 1, 1, 0, 'NONE', '16*k', '', '', '', '', '16*k', '', '', 'NONE', 'NONE', '', '', 'NONE', '', '', '', 'NONE', '', 0, 0, 'NORMAL', 1, '1', 1000, 0),
  (243, 'HELP_BYEURAK', 6, 1, 1, 0, 'NONE', '16*k', '', '', '', '', '16*k', '', '', 'NONE', 'NONE', '', '', 'NONE', '', '', '', 'NONE', '', 0, 0, 'NORMAL', 1, '1', 1000, 0)
  ON DUPLICATE KEY UPDATE szName = VALUES(szName), bType = VALUES(bType), bLevelStep = VALUES(bLevelStep), bMaxLevel = VALUES(bMaxLevel), bLevelLimit = VALUES(bLevelLimit), szPointOn = VALUES(szPointOn), szPointPoly = VALUES(szPointPoly), szSPCostPoly = VALUES(szSPCostPoly), szDurationPoly = VALUES(szDurationPoly), szDurationSPCostPoly = VALUES(szDurationSPCostPoly), szCooldownPoly = VALUES(szCooldownPoly), szMasterBonusPoly = VALUES(szMasterBonusPoly), szAttackGradePoly = VALUES(szAttackGradePoly), setFlag = VALUES(setFlag), setAffectFlag = VALUES(setAffectFlag), szPointOn2 = VALUES(szPointOn2), szPointPoly2 = VALUES(szPointPoly2), szDurationPoly2 = VALUES(szDurationPoly2), setAffectFlag2 = VALUES(setAffectFlag2), szPointOn3 = VALUES(szPointOn3), szPointPoly3 = VALUES(szPointPoly3), szDurationPoly3 = VALUES(szDurationPoly3), setAffectFlag3 = VALUES(setAffectFlag3), szGrandMasterAddSPCostPoly = VALUES(szGrandMasterAddSPCostPoly), prerequisiteSkillVnum = VALUES(prerequisiteSkillVnum), prerequisiteSkillLevel = VALUES(prerequisiteSkillLevel), eSkillType = VALUES(eSkillType), iMaxHit = VALUES(iMaxHit), szSplashAroundDamageAdjustPoly = VALUES(szSplashAroundDamageAdjustPoly), dwTargetRange = VALUES(dwTargetRange), dwSplashRange = VALUES(dwSplashRange);
