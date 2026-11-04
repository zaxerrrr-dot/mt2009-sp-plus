-- MT2009_PLUS_MIKSTURY_V1 (the owner, 4 November 2026; cache/yohara/decyzje-lowienie-mikstury.md M5): Sok z Korzenia
-- Gango (50804) heals 50 HP as on the pl-wiki ("Sok z Korzenia Gango": +50 PZ) and in Owsap's row - the package had 90.
-- The client's tooltip reads value0 from its own item_proto (client-2.0.30/tools/zeliksiry). Every start (apply.sh),
-- idempotent: only a row still at the package's 90 is changed, so an operator's own value is kept.
-- (Lekarstwo Iluzji's 50% is game/cube.npc_okno.txt; the golden elixirs and Zlote Ziolo are yohara_eliksiry.sql.)
UPDATE world.item_proto SET value0=50 WHERE vnum=50804 AND type=3 AND subtype=11 AND value0=90;
