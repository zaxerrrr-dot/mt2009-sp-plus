# -*- coding: utf-8 -*-
"""MT2009_PLUS_YOHARA_MELEY_V1: Schronienie Meley (Meley's Lair, the Dragon Queen Meley) - the owner, 15 October 2026
("dodaj loch Meley, drop zgodnie z wiki").

  356 metin2_map_n_flame_dragon   Schronienie Meley (1x1)   dungeon, quest meley_dungeon; entered at Strażnik Smoków
                                                            Dolnarr (20419) on Doyyumhwaji (62) at the wiki's 83,851

The pl-wiki has two versions: "Schronienie Meley (dla gildii)" (level 90, a guild of 4-16 online at the NPC with 600
ladder points, every 3 h - Przepustka (Meley) resets it -, 1 h for the four statues, a choice of Skrzynia Królowej
Meley / Skrzynia Sm. Strażników at Złota Smocza Skrzynia) and "(dla grup)" (level 75, a party of 4-8 with a Przepustka
each, every 30 min, an easier copy, Skrzynia Królowej Meley (Dla Grup) - Owsap's 50294: 5 x 200 Kamyki). The owner wants
the wiki's drops: the guild version's monsters, stages and two chests. A singleplayer world with bots has no guild of
four at the NPC, so the entry is the party one: alone or a party of up to 8 (the person's bots follow him in, as in
every dungeon here), level 90 (the guild version's), no ladder points and no pass - the fee and the day's count of our
dungeons instead (MT2009_PLUS_DUNGEON_FEE_V1: 7 500 000 Yang, 5 a day), no waiting for a person
(MT2009_PLUS_DUNGEON_NO_PLAYER_COOLDOWN_V1), the bots rest the wiki's 3 h.

Index 356: Owsap's (= official) for this map, free in every map of ours and of every worktree (15 October 2026); its
instances 3560000+. Base: GF's 307200 1510400 (= Owsap's Setting.txt) is OUR Świątynia Zodiaku's ground
(metin2_12zi_stage 307200 1408000 6x6) - moved to 281600 1510400, the nearest 1x1 overlapping no map of our client's
atlasinfo, no server Setting.txt and no map of GF's atlasinfo (the generator checks it). The server's Setting.txt and
the client's setting.txt / atlasinfo row carry the moved base (client-2.0.30/tools/ymeley). The terrain is GF's own
folder (no ParentMapName - a full map); the server_attr is GF's attr.atr cell for cell, but the cells under Meley
(130,77 - behind the arena's north wall, where Owsap's engine stands her) are opened so she can be spawned there.

Sources: the pl-wiki ("Schronienie Meley (dla gildii)" / "(dla grup)", "Królowa Smoków Meley", "Smocze Statuy",
"Jajo Smoka", "Smoczy Strażnik Idall", "Sługus Idalla", the magma monsters, "Pierścień Smoczego Ognia", "Skrzynia
Królowej Meley", "Skrzynia Sm. Strażników", "Czerwona Smocza Łuska", "Czerwony Smoczy Róg", "Plan Zbroi Hełm",
"Złota Smocza Skrzynia", "Strażnik Smoków Dolnarr"; cache: scratchpad wiki/meley), Owsap v6.2.6 (GuildDragonLair.lua -
the stages, counts, respawns, positions -, guild_dragonlair.cpp, db/mob_proto.txt, item_proto.txt, mob_names.txt,
group_builder/group/red_dragonlair.txt, special_item_group/dragonlair_chest.txt, map/metin2_map_n_flame_01/npc.txt),
GF 26.1.11 (the map, attr.atr, atlasinfo), Ameria's meleylair.lua (dracaryS - its own engine calls; not used).
"""

# -- elements (setRaceFlag bits 11-16, MT2009_PLUS_ELEMENTS_V1) ------------------------------------------------------
FIRE = 4096
ELEMENT_BITS = 2048 | 4096 | 8192 | 16384 | 32768 | 65536

# -- monsters, bosses, stones: vnum -> (Polish name (pl-wiki), element) - the official vnums (Owsap's rows), every one
#    free in our world (15 October 2026); at most 24 bytes in cp1250. Owsap's names decide which is which where the
#    wiki's levels say the other ("Magma Golem" 6111 = de "Magmagolem" = Golem Lawy, "Magma Man" 6113 = de "Magmamann"
#    = Magmowy Golem); the levels stay Owsap's (the official rows). ------------------------------------------------
MOBS = {
    6110: ('Magmowy Yeti', FIRE),               # 103 PAWN
    6111: ('Golem Lawy', FIRE),                 # 107 KNIGHT
    6112: ('Magmowy Insekt', FIRE),             # 105 S_PAWN - stage 1 (12, back after 5 s)
    6113: ('Magmowy Golem', FIRE),              # 105 KNIGHT - stage 2 (12, back after 30 s)
    6114: ('Magmowy Kryształ', FIRE),           # 103 PAWN
    6115: ('Magmowy Wiwern', FIRE),             # 110 S_KNIGHT - stages 3 and 4 (12, back after 30 s)
    6116: ('Smoczy Strażnik Idall', FIRE),      # 113 BOSS - stage 3 (four, each with three of his men)
    6117: ('Sługus Idalla', FIRE),              # 97 S_KNIGHT
    6118: ('Smocza Statua', 0),                 # 120 STONE - the four statues (7 000 000 HP)
    6193: ('Królowa Smoków Meley', FIRE),       # 123 KING - not killed directly (pl-wiki)
    20422: ('Jajo Smoka', 0),                   # 120 STONE - stages 2-4 (four, back after 120 s)
}
# the pl-wiki's Basis-EXP over Owsap's (the guild rows give 0 for the magma monsters)
OVERRIDE = {
    6110: dict(Exp='124334'),
    6111: dict(Exp='128934'),
    6112: dict(Exp='135468'),
    6113: dict(Exp='137900'),
    6114: dict(Exp='517920'),
    6115: dict(Exp='116266'),
    6117: dict(Exp='514705'),
}

# -- NPCs: Owsap's numbers (free here) --------------------------------------------------------------------------------
NPCS = {
    20419: ('Dragon Guardian Dolnarr', 'Strażnik Smoków Dolnarr'),
    20420: ('Golden Dragon Chest', 'Złota Smocza Skrzynia'),
}
WATCHER, GOLD_CHEST, GATE, KING, STONE, EGG, BOSS, KNIGHT = 20419, 20420, 20388, 6193, 6118, 20422, 6116, 6117
# 20388 Smocza Brama is ours already (Razador's gates)

# -- the map ----------------------------------------------------------------------------------------------------------
MAP = dict(index=356, folder='metin2_map_n_flame_dragon', name='Schronienie Meley', size=(1, 1),
           base=(281600, 1510400), gf_base=(307200, 1510400), town=(127, 167), owsap='metin2_map_n_flame_dragon')
# Owsap's GuildDragonLair.lua PixelPosition (local cells)
STONES = [(123, 137), (123, 124), (136, 123), (137, 137)]
KING_CELL = (130, 77)
KING_OPEN = 3                           # the cells within 3 of her are opened in the server_attr
CENTER = (130, 130)
GATE_CELL = (129, 175)                  # Owsap: dir 5 (of 8) = 180 degrees
INSIDE = (127, 167)                     # the entry and Town.txt (inside the gate: a person who dies comes back in)
WATCHER_INSIDE = (134, 168)
# Doyyumhwaji (62): Strażnik Smoków Dolnarr at the wiki's 83,851 (Owsap's npc.txt, dir 3); the way out beside him
FLAME = dict(index=62, folder='metin2_map_n_flame_01', base=(588800, 614400), size=(6, 6))
WATCHER_CELL = (83, 851, 3)
LANDING = (84, 853)
MIN_LEVEL = 90
TIME_LIMIT = 60 * 60

# -- the stage monsters (Owsap's GuildDragonLair.Guild.Stage: MonsterVnum x MonsterCount, MonsterRespawnTime) and the
#    groups that bring the wiki's other monsters in (Owsap's red_dragonlair_1..3, ours 6337-6339 - free) ------------
GROUPS = {
    6337: ('red_dragonlair_1', [6111, 6110, 6114]),           # Golem Lawy with a Yeti and a Kryształ
    6338: ('red_dragonlair_2', [6009, 6006, 6007]),           # Ognisty Książę / Ognista Broda Żaru (ours, Razador's)
    6339: ('red_dragonlair_3', [6115, 6113]),                 # Magmowy Wiwern with a Magmowy Golem
}
STAGES = {
    1: dict(mob=6112, count=12, respawn=5, groups=[6337, 6337]),
    2: dict(mob=6113, count=12, respawn=30, groups=[6338, 6337]),
    3: dict(mob=6115, count=12, respawn=30, groups=[6339, 6337]),
}
GROUP_RESPAWN = 60

# -- the items: the official vnums where ours are free; where ours hold another item, new ones ----------------------
RED_HORN, RED_SCALE, HELM_PLAN = 30620, 30621, 30622        # = claude/yohara-helm100's rows (dedupe at the merge)
RING = 30340                            # official 30341 - ours is Zupa Grzybowa; 30340 is free here and in GF
CHEST_QUEEN = 54706                     # official 50270 - ours is Skrzynia Razadora
CHEST_GUARD = 54707                     # official 50271 - ours is Skrzynia Nemere
ITEM_SRC = {RED_HORN: 30620, RED_SCALE: 30621, HELM_PLAN: 30622, RING: 30341, CHEST_QUEEN: 50270, CHEST_GUARD: 50271}
