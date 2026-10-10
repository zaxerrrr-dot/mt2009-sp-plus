# Drop wiki (MT2009_PLUS_DROP_WIKI_V1)

The owner's module of 3 October: a window (client root `uidropwiki.py`, key `/`
or the inventory sidebar's button) where a player types an item's name to see
which monsters drop it, how many and how often, or a monster's name to see what
it drops. Everything comes from the running server's own drop tables:

- `cmd.cpp`, `cmd_general.cpp` - `/drop_wiki`, `/drop_wiki find <i|m> <text>`,
  `/drop_wiki show <i|m> <vnum>`, answered with `DropWiki ...` chat commands;
- `item_manager.cpp`/`.h` - `ITEM_MANAGER::GetDropWikiRows(race, rows)`: the
  race's drop/kill/limit tables, the etc drop, a Metin's spirit stones and the
  world's extras, at the monster's own level with the server's mob item rate.

`apply_dropwiki.py <game/src>` (Linux) and `Apply-DropWikiPatch.ps1 -SourceDir`
(Windows) apply `edits.json`; each edit has its own marker and is skipped when
already there.

`MT2009_PLUS_RARE_DROP_SWITCHES_V1` (5 October): the wiki leaves out what the
database editor's rare drop switches hold back (Kupon SM, sash, Cor Draconis
from bosses / Metins and the game's own drop table rows of them;
`server-patches/raremobrules`).

`MT2009_PLUS_SASH_CLOTH_V1` (6 October): the sash row of a boss / Metin is Delikatne Sukno (80019) now,
at the sash's chance, as many as a killer at the monster's level gets (2 / 5 / 10 for 1-49 / 50-74 / 75+;
`server-patches/raremobrules`).

`MT2009_PLUS_DROP_WIKI_V2` (10 October, the owner: the wiki shows the new things by itself - weapons, refine
materials, monsters, dungeons): an item page also says where else the item comes from and what it is for,
a monster page where the monster lives and its element - built with the drop rows (at most every 30 s while
someone asks) from what this core loaded, so a new item, recipe, chest or shop shows up without a change here:

- `cube.cpp` - `Cube_GetRecipesForWiki()`: the NPC recipes as loaded (cube.txt);
- `shop_manager.h` - `CShopManager::GetShopMapForWiki()`: every NPC shop;
- `item_manager.cpp`/`.h` - `ITEM_MANAGER::GetDropWikiChests()`: every chest (a special item group whose
  number is an item, not type special) with what one opening gives (by weight, or each entry at its percent
  for type pct; a group inside a group by its share); and a boss's (5%) / Metin's (2%) Talisman +0 of its
  element (race flags, `server-patches/zywioly`) among its drop rows;
- `cmd_general.cpp` - the recipes both ways, refining (item_proto `refined_vnum` / `refine_set`, refine_proto:
  the step that makes the item, the next step, and the refine ladders a material is for - one line a
  ladder, first..last step), the chests both ways, the shops, the monsters' places (every map of map/index:
  regen.txt, boss.txt, stone.txt; the dungeon panel's bosses, dungeon_info.txt) and the locale file
  `drop_wiki.txt` (linux-port/docker/game): the drops only quests or the engine give (dungeon bosses' chests,
  the Zodiac Generals' Zlota Skrzynia, the Ochao boss), Mnich Milbon's exchanges (shown like a recipe) and the
  dungeons' regen files. The search finds every item and monster with something to show.

An item no source gives (no drop, recipe, chest, shop or exchange, and not refined from one that has) gets
no refine lines and is no search result for them alone - so the switched-off wiki recipes
(`MT2009_PLUS_NS_WIKI_RECIPES_OFF`: the Cyjanitowe weapons, Ogniste Buty, Buty Oceanu, Turmalin) leave no
ladder to nowhere. `/drop_wiki reload` (GM, high wizard or more) reads the map regens, `dungeon_info.txt`
and `drop_wiki.txt` again. The new answer lines come before the rows and an older client skips them
(protocol: the comment above `DropWikiMat` in `cmd_general.cpp`, and `uidropwiki.py`).
