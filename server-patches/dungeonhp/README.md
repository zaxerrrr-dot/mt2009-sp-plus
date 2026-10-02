# Życie potworów w lochu

Poprawka silnika (`game/src/questlua_dungeon.cpp`), znacznik
`MT2009_PLUS_DUNGEON_MOB_HP_V1` (właściciel, 2 października: Biblioteka
Wiedzy).

- **`d.count_players()`** - ilu graczy (razem z botami) jest teraz w
  wybranej instancji lochu (`d.select` albo loch postaci).
- **`d.mob_hp_percent(vnum, procent)`** - każdy żywy potwór albo Metin o tym
  vnumie w tej instancji dostaje maksymalne życie razy procent (1-1000) i
  zachowuje ten sam procent życia, jaki miał; zwraca, ilu zmieniono. Te same
  potwory na zwykłych mapach zostają bez zmian. W syslogu linia
  `DUNGEON_MOB_HP:`.
- Wytrzymałość potworów ze świata (`server-patches/mobhp`, flaga `m2_mob_hp`)
  nie nadpisuje potwora zmienionego tutaj.

Użycie: `quest/biblioteka_wiedzy.quest` - Metiny (8006) 55% życia, Baronówna
Pająków (9706) 100% / 150% / 200% / 300% dla 1 / 2 / 3 / 4+ graczy.

Stosowanie: `Apply-DungeonHpPatch.ps1 -SourceDirectory <game/src>` (Windows)
albo `python3 apply_dungeonhp.py <game/src>` (Linux/VPS). Każdy krok nakłada
się raz; brak oczekiwanego kodu przerywa bez zmian.
