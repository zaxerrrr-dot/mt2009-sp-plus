# superstone – event Super Kamieni (dodatkowe kamienie Metin)

Znacznik: `MT2009_PLUS_SUPERSTONE_V1`, define `ENABLE_SUPERSTONE_EVENT` w `common/service.h` (właściciel, 29.10.2026,
poprawki 3.0.7 pkt 6).

- `char_manager.cpp` (`CHARACTER_MANAGER::SpawnMob`, przed `return (ch);`): gdy kamień (`CHAR_TYPE_STONE`) pojawia się
  na mapie świata (`lMapIndex < 10000` – nigdy loch ani inna instancja), jest pokazany (`bShow`) i flaga
  `superstone_event` > 0, obok niego staje `MIN(flaga, 4)` dodatkowych kamieni tej samej rasy w tym samym miejscu,
  każdy z losowym obrotem (`SpawnExtraStones`; `ENABLE_WJ_SHOW_MOB_INFO` u nas nie istnieje, więc bez `bAggressive`).
- Dodatkowe kamienie są niezależne: nie mają regenu (regen dostaje tylko kamień zwracany przez `SpawnMob` –
  `SetRegen` i licznik `regen->count` bez zmian), dropią i dają exp jak zwykłe kamienie, po prostu giną.
- Limit: na mapę i rasę żyje najwyżej (flaga) × (żywe kamienie, przy których je postawiono) dodatkowych – kamień
  odrodzony przez regen, którego poprzednie dodatkowe dalej stoją, dostaje tylko brakujące. Nic się nie mnoży.
- `questmanager.cpp` (`SetEventFlag`): flaga `superstone_event` spada do 0 → dodatkowe kamienie z pełnym HP znikają
  (`SuperStoneEventOff`), bite zostają i giną normalnie.
- Uwaga: metiny wielkanocne (8041–8050) liczą się do limitu `EASTER_METINS_PER_MAP` (regen.cpp) razem z dodatkowymi.

Włączanie: `/eventflag superstone_event 1..4` (0 = koniec) albo panel – kalendarz eventów, rodzaj
„Super Kamienie Metin” z poziomem 1–4 (`playerbot_events.h` / `playerbot_ingame_events.h` zapisuje flagę na
starcie i 0 na końcu).

Kolejność: na końcu (po `czepiec`). Linux/VPS: `python3 apply_superstone.py <game/src>`; Windows:
`Apply-SuperStonePatch.ps1 -SourceDir <game/src>` (wołane na końcu `tools/port/Apply-MT2009PlusEngine.ps1`).
