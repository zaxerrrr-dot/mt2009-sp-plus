-- MT2009_PLUS_RIPOSTY_V1: Zwoj Zmiany Treningu (71000, yohara_items.sql - removes the ripostes and boosts and gives their
-- skill points back, quest riposty) in the ItemShop's "Bonusy" for 49 (the pl-wiki: 49 SM in the Item-Shop) while no offer of 71000 is there
-- (the operator's later price stays; a removed offer comes back on the next start).
SET NAMES utf8mb4;
INSERT IGNORE INTO itemshop.ishop_items (id, category, name_item, `desc`, price, currency, vnum, count, socket0, socket1, socket2, vnum_icon, date_added)
SELECT 1071000, 2, 'Zwój Zmiany Treningu', 'Usuwa wszystkie riposty i dopalacze (7. i 8. umiejętność) i oddaje ich punkty umiejętności - potem możesz wybrać nową ripostę.', 49, 'cash', 71000, 1, 0, 0, 0, '71000', NOW() FROM DUAL WHERE EXISTS (SELECT 1 FROM world.item_proto WHERE vnum = 71000) AND NOT EXISTS (SELECT 1 FROM itemshop.ishop_items WHERE vnum = 71000);
