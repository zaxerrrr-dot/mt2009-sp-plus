-- MT2009_PLUS_CHANGE_LOOK_V1: Transmutacja (server-patches/transmutacja/README.md). Every start (apply.sh), idempotent:
-- ADD COLUMN IF NOT EXISTS, INSERT IGNORE. The db core of a release with the patch reads and writes player.item.transmutation
-- (the look: another item's vnum, 0 none) in every item SELECT / save of its own, of the Ikarus shop and of the
-- Kolekcjoner - this must run before the db core starts. The look of the hide-costume system needs no column (quest flags).
SET NAMES utf8mb4;

ALTER TABLE player.item
  ADD COLUMN IF NOT EXISTS `transmutation` int(10) unsigned NOT NULL DEFAULT 0 COMMENT 'MT2009_PLUS_CHANGE_LOOK_V1' AFTER `attrvalue6`;

-- ---- the window's tickets and the reversal items (the official vnums, GF 26.1.11 item_list.txt / Owsap item_proto;
-- free in our world, 14 October 2026). ITEM_USE / USE_SPECIAL (3/10), stack 200; the tickets go into the window at
-- Teowaden (no Yang), the reversals are dragged onto a transmuted item (flag APPLICABLE). Anti flags as Owsap's:
-- drop/give/pk-drop/private shop off, 72341 (the tradeable ticket) only drop, 72344 drop/give/private shop.
INSERT IGNORE INTO world.item_proto (`vnum`,`name`,`locale_name`,`type`,`subtype`,`stack`,`weight`,`size`,`antiflag`,`flag`,`wearflag`,`immuneflag`,`gold`,`shop_buy_price`,`refined_vnum`,`refine_set`,`magic_pct`,`specular`,`socket_pct`,`addon_type`,`limittype0`,`limitvalue0`,`limittype1`,`limitvalue1`,`applytype0`,`applyvalue0`,`applytype1`,`applyvalue1`,`applytype2`,`applyvalue2`,`value0`,`value1`,`value2`,`value3`,`value4`,`value5`,`socket0`,`socket1`,`socket2`,`socket3`,`socket4`,`socket5`) VALUES
(72325,'Transmutation Reversal','Anulacja Transmutacji',3,10,200,0,1,90240,16388,0,'',0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,-1,-1,-1,-1,-1,-1),
(72326,'Transmutation Ticket','Bilet Transmutacji',3,10,200,0,1,90240,4,0,'',0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,-1,-1,-1,-1,-1,-1),
(72341,'Transmutation Ticket (t)','Bilet Transmutacji (handlowy)',3,10,200,0,1,128,4,0,'',0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,-1,-1,-1,-1,-1,-1),
(72343,'Mount Transformation Reversal','Anulacja Polimorfii Wierzchowca',3,10,200,0,1,90240,16388,0,'',0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,-1,-1,-1,-1,-1,-1),
(72344,'Mount Transformation Ticket','Bilet Polimorfii Wierzchowca',3,10,200,0,1,73856,4,0,'',0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,-1,-1,-1,-1,-1,-1);
