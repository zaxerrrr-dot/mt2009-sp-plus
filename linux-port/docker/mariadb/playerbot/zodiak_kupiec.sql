-- MT2009_PLUS_ZODIAC_MERCHANT_V1 - the Kupiec Zodiaku (NPC 20451, shop 41, floor 40 of the Swiatynia Zodiaku) as the
-- pl-wiki lists him (the owner, 3 November 2026: "brakuje szkatulek odlamkow"). The shop's line price is
-- item_proto.gold x the line's count (shop.cpp), so the wiki's prices are the items' gold:
--   Pryzmat Ozywienia (Q) 33032  x200  3 000 000 Yang  -> gold 15 000   (the package had 14 500: 2 900 000)
--   Insygnia Zi..Gui 33001-33022 x50   1 000 000 Yang  -> gold 20 000   (already)
--   Pergamin Sfer 72329          x1    1 000 000 Yang  -> gold 1 000 000 (the package had 100 000)
--   Zdobna Skrz. z Odlamkiem 39068 x1  1 000 000 Yang  -> gold 1 000 000 (the line was missing; the item and its group
--                                       MT2009_yitems_39068 - the wiki's 11 shards + Ksiega Umiejetnosci - are
--                                       yohara_items.sql's / game/yohara_maps, which is why this runs after it)
-- Purchase limits (shop.cpp hooks (61)/(62)/(68), playerbot_zodiac_temple.cpp FProcessZodiacItem): every line once a
-- run, the chest five times. Guarded: a gold changes only from the old value - an operator's value stays. Idempotent.
UPDATE world.item_proto SET gold = 15000 WHERE vnum = 33032 AND gold = 14500;
UPDATE world.item_proto SET gold = 1000000 WHERE vnum = 72329 AND gold = 100000;
UPDATE world.item_proto SET gold = 1000000 WHERE vnum = 39068 AND gold = 0;
INSERT IGNORE INTO world.shop_item (shop_vnum, item_vnum, count) VALUES (41, 39068, 1);
