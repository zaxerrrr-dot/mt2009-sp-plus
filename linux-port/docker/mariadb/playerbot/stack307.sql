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

-- 2. Zwoj Skarbu (Stopien A) 70434 (the Yohara bosses' and chests' scroll): the wiki's scroll takes a champion into the
--    secret Swiatynia Enigma and lives 3 days (LIMIT_REAL_TIME 259200 - socket 0 holds each piece's own end, so no two
--    pieces ever stacked: the engine joins only pieces with the same sockets). This server has no such dungeon (the
--    scroll is a collectible and a seller's item - yohara_items.sql: "the secret dungeons of the treasure scrolls -
--    none here yet"), so the 3 days only threw the drop away. Without the limit the scroll keeps and stacks (200).
--    Should the dungeon come, the limit returns with it.
UPDATE world.item_proto SET flag = flag | 4, antiflag = antiflag & ~32768, stack = 200, limittype0 = 0, limitvalue0 = 0
 WHERE vnum = 70434;
--    The pieces players and bots hold already: their end time (socket 0, set at the drop) cleared, so they join the new
--    ones' stacks and are no longer taken when the old 3 days run out (the engine starts the expiry only for a proto
--    with LIMIT_REAL_TIME - after this the old end time would be a stray socket that splits the stacks).
UPDATE player.item SET socket0 = 0 WHERE vnum = 70434 AND socket0 <> 0;
