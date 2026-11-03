-- MT2009_PLUS_STACK307_V1 - a player's report on Yohara 3.0.7 (3 November 2026): "brak stackowania" of Zwoj Skarbu
-- (Stopien A) and the leadership books Charyzma / Inspiracja Nowicjusza / Adepta / Eksperta. Run by apply.sh after
-- drop307.sql (after every file that writes these rows). Idempotent: bit operations and plain values. PROTO_FROM_DB -
-- the cores read it at boot. The client's item_proto carries the same (client-patches/client-2.0.30/tools/ystack307/
-- patch_ystack307_client.py) - the client asks the flag itself whether a line stacks and splits.
--
-- Bits: flag 4 = ITEM_FLAG_STACKABLE; antiflag 32768 = ANTI_STACK (none of these has it - 70434's 16384 is ANTI_PKDROP).

-- 1. Charyzma / Inspiracja Nowicjusza / Adepta / Eksperta 50338-50343 (ITEM_USE / USE_SPECIAL, the leadership skill's
--    books, M1 .. G1): the wiki's "Laczenie: tak" - stacks of 200, as every skill book (Ksiegi Riposty, drop307.sql).
--    The package had flag 0 and stack 1.
UPDATE world.item_proto SET flag = flag | 4, antiflag = antiflag & ~32768, stack = 200
 WHERE vnum BETWEEN 50338 AND 50343;

-- 2. Zwoj Skarbu (Stopien A) 70434 stays as the wiki has it (no stacking, 3 days) - the owner, 3 November 2026; its drop
--    is switched off instead (MT2009_PLUS_ZWOJ_SKARBU_OFF_V1).
