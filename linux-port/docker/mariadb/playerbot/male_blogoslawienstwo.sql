-- MT2009_PLUS_SMALL_BLESSING_V1: Male Blogoslawienstwo 72351 (the owner, 3 November 2026 - the SAPPHIRE server
-- configuration's calendar drops it from every Metin and boss on Tuesday 16-20 and Thursday 12-16). The official
-- item (GF / Ameria SMALL_ORISON, the same vnum and icon): Blogoslawienstwo Przedmiotu 71052 with a 10% chance to
-- change the 6th and 7th bonus (server-patches/maleblog). As 71052 (ITEM_USE / USE_SPECIAL, applicable to an item,
-- confirm on use, stacks of 200); after the pl-wiki: no trade with players, no private shop, no drop, no safebox,
-- sold to an NPC (antiflag GIVE | DROP | MYSHOP | SAFEBOX). The vnum was free in our world.item_proto (3 November
-- 2026). Every start (apply.sh), idempotent: INSERT IGNORE - a row the operator changed is kept.
-- Client: client-patches/client-2.0.30/tools/ysapph (item_proto record, item_list line, itemdesc, GF icon).
SET NAMES utf8mb4;
INSERT IGNORE INTO world.item_proto (`vnum`,`name`,`locale_name`,`type`,`subtype`,`stack`,`weight`,`size`,`antiflag`,`flag`,`wearflag`,`immuneflag`,`gold`,`shop_buy_price`,`refined_vnum`,`refine_set`,`magic_pct`,`specular`,`socket_pct`,`addon_type`,`limittype0`,`limitvalue0`,`limittype1`,`limitvalue1`,`applytype0`,`applyvalue0`,`applytype1`,`applyvalue1`,`applytype2`,`applyvalue2`,`value0`,`value1`,`value2`,`value3`,`value4`,`value5`,`socket0`,`socket1`,`socket2`,`socket3`,`socket4`,`socket5`) VALUES
(72351,'Male Blogoslawienstwo',_cp1250 X'4D61B3652042B36F676F73B361776965F17374776F',3,10,200,0,1,204928,24580,0,'',150000,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,-1,-1,-1,-1,-1,-1);
