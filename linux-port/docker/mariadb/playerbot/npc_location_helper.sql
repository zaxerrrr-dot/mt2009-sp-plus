-- MT2009_PLUS_NPC_LOCATION_HELPER_V1: Lokalizator NPC (the improved map; Autor: Best Studio) - the three items of the
-- system. Every start (apply.sh), idempotent: INSERT IGNORE - a row the operator changed (the Seban panel) is kept.
--   79667 Lokalizator NPC        - ITEM_USE / USE_SPECIAL: not needed any more (MT2009_PLUS_NPC_LOCATION_HELPER_V2,
--                                  28 October 2026: every character has the improved map); using one only says so
--                                  and keeps it. Not sold anywhere.
--   79669 Kamien Teleportacji    - the stone the map's "teleport to the NPC" spends (bound to the character).
--   79668 Kamien Teleportacji+   - the same stone, tradeable; the bound one is spent first.
-- A teleport costs 1 stone on the same map, 2 in the same region (map index / 10), 3 elsewhere; 5 minutes cooldown
-- (server-patches/npcloc, npc_location_helper.cpp). The client's records (item_proto / item_list / itemdesc) are made
-- from this file by client-patches/client-2.0.30/tools/npcloc/patch_npcloc_client.py - change both together.
SET NAMES utf8mb4;
INSERT IGNORE INTO world.item_proto (`vnum`,`name`,`locale_name`,`type`,`subtype`,`stack`,`weight`,`size`,`antiflag`,`flag`,`wearflag`,`immuneflag`,`gold`,`shop_buy_price`,`refined_vnum`,`refine_set`,`magic_pct`,`specular`,`socket_pct`,`addon_type`,`limittype0`,`limitvalue0`,`limittype1`,`limitvalue1`,`applytype0`,`applyvalue0`,`applytype1`,`applyvalue1`,`applytype2`,`applyvalue2`,`value0`,`value1`,`value2`,`value3`,`value4`,`value5`,`socket0`,`socket1`,`socket2`,`socket3`,`socket4`,`socket5`) VALUES
(79667,'NPC Finder',_cp1250 X'4C6F6B616C697A61746F72204E5043',3,10,1,0,1,90240,0,0,'',100000,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0),
(79668,'Teleportation Stone+',_cp1250 X'4B616D6965F12054656C65706F727461636A692B',5,0,200,0,1,0,4,0,'',20000,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0),
(79669,'Teleportation Stone',_cp1250 X'4B616D6965F12054656C65706F727461636A69',5,0,200,0,1,221312,4,0,'',10000,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0);
