-- MT2009_PLUS_ELEMENT_STONES_V1: Kamien Ochrony Zywiolow (39120) and Kamien Mocy Zywiolow (39119) - the owner, 28 October 2026. GENERATED
-- by tools/kamienie_zywiolow/gen_kamienie_zywiolow.py - do not edit, rerun it. Every start (apply.sh), idempotent:
-- INSERT IGNORE - a row the operator changed (the Seban panel) is kept. The official vnums and flags (Owsap v6.2.6):
-- ITEM_UNIQUE in the unique slots, 7 days of real time, no drop / trade / private shop / storage. The six bonuses
-- of each (+10% resistance to / power of every element) are world.item_extra_apply lines (item_proto has room
-- for three; MT2009_PLUS_ITEM_EXTRA_APPLY_V1) - the table is made by apply.sh before this file runs.
SET NAMES utf8mb4;
INSERT IGNORE INTO world.item_proto (`vnum`,`name`,`locale_name`,`type`,`subtype`,`stack`,`weight`,`size`,`antiflag`,`flag`,`wearflag`,`immuneflag`,`gold`,`shop_buy_price`,`refined_vnum`,`refine_set`,`magic_pct`,`specular`,`socket_pct`,`addon_type`,`limittype0`,`limitvalue0`,`limittype1`,`limitvalue1`,`applytype0`,`applyvalue0`,`applytype1`,`applyvalue1`,`applytype2`,`applyvalue2`,`value0`,`value1`,`value2`,`value3`,`value4`,`value5`,`socket0`,`socket1`,`socket2`,`socket3`,`socket4`,`socket5`) VALUES
(39120,'Elemental Protection Stone',_cp1250 X'4B616D6965F1204F6368726F6E7920AF7977696FB3F377',16,0,1,0,1,254080,0,128,'',0,0,0,0,0,0,0,0,7,604800,0,0,0,0,0,0,0,0,0,0,0,0,0,0,-1,-1,-1,-1,-1,-1),
(39119,'Elemental Power Stone',_cp1250 X'4B616D6965F1204D6F637920AF7977696FB3F377',16,0,1,0,1,254080,0,128,'',0,0,0,0,0,0,0,0,7,604800,0,0,0,0,0,0,0,0,0,0,0,0,0,0,-1,-1,-1,-1,-1,-1);
INSERT IGNORE INTO world.item_extra_apply (vnum, slot, apply_type, apply_value) VALUES
(39120, 1, 76, 10),
(39120, 2, 75, 10),
(39120, 3, 133, 10),
(39120, 4, 78, 10),
(39120, 5, 134, 10),
(39120, 6, 135, 10),
(39119, 1, 178, 10),
(39119, 2, 179, 10),
(39119, 3, 180, 10),
(39119, 4, 181, 10),
(39119, 5, 182, 10),
(39119, 6, 183, 10);
