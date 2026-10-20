-- MT2009_PLUS_MAPS_WZ_V1: Wezowe Pole (80) and Kraina Gigantow (70) - the Giants' and ogres' levels as the
-- pl-wiki has them (Niszczyciel 66, Wojownik z Toporem 73, Tysieczny Wojownik 77, Ogr Szaleniec 75); Ogr
-- Wojownik 71 / Ogr Rzeznik 73 as the global sheet, Owsap and Ameria (the wiki 68 / 70; the owner 20.10.2026,
-- MT2009_PLUS_OGRE_LEVEL_V1); ours were 76/83/87/78/80/85; the
-- golems 69/72/76 are the wiki's already). Only the level: HP, damage, exp and the rest stay ours. GENERATED
-- by tools/maps_wz/gen_maps_wz.py. Every start (apply.sh), idempotent. Every vnum the maps spawn, portal and
-- drop exists in our world already (15 October 2026, the test server): no INSERT.
SET NAMES utf8mb4;
UPDATE world.mob_proto SET level = 66 WHERE vnum = 1401 AND level <> 66;   -- Niszczyciel (was 76)
UPDATE world.mob_proto SET level = 73 WHERE vnum = 1402 AND level <> 73;   -- Wojownik z Toporem (was 83)
UPDATE world.mob_proto SET level = 77 WHERE vnum = 1403 AND level <> 77;   -- Tysieczny Wojownik (was 87)
UPDATE world.mob_proto SET level = 71 WHERE vnum = 1601 AND level <> 71;   -- Ogr Wojownik (was 78)
UPDATE world.mob_proto SET level = 73 WHERE vnum = 1602 AND level <> 73;   -- Ogr Rzeznik (was 80)
UPDATE world.mob_proto SET level = 75 WHERE vnum = 1603 AND level <> 75;   -- Ogr Szaleniec (was 85)
