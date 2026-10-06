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
