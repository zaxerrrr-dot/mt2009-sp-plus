# Wytrzymałość potworów

Poprawka silnika (`game/src/char.cpp`, `game/src/questmanager.cpp`),
znacznik `MT2009_PLUS_MOB_HP_V1` (propozycja Frelika: „łatwy 80%”).

- **Życie potworów, bossów i Metinów jako procent** `max_hp` z `mob_proto`:
  flaga zdarzenia `m2_mob_hp` (10–300; 0 albo 100 = jak w grze). Ustawia ją
  okno POZIOM TRUDNOŚCI launchera (`M2_MONSTER_HP` w `.env`: `default`,
  `easy` = 80% albo procent) i karta „Wytrzymałość potworów” w panelu WWW.
- **Przy pojawieniu się** potwór albo kamień dostaje nowe życie
  (`CHARACTER::ComputePoints`).
- **Na żywo:** gdy flaga się zmienia (`CQuestManager::SetEventFlag`, na
  każdym rdzeniu), każdy stojący potwór i kamień dostaje nowe życie i
  zachowuje ten sam procent życia, jaki miał. W syslogu linia `MOB_HP:`.
- Postacie niezależne (w tym żyły rud i krzaki ziół), drzwi i nieruchome
  potwory bez ataku (bramy w lochach) zostają bez zmian, tak samo potwór,
  któremu loch sam ustawił życie (`UniqueSetMaxHP`). Doświadczenie i drop z
  jednego zabicia się nie zmieniają.

Stosowanie: `Apply-MobHpPatch.ps1 -SourceDirectory <game/src>` (Windows)
albo `python3 apply_mobhp.py <game/src>` (Linux/VPS). Każdy krok nakłada się
raz; brak oczekiwanego kodu przerywa bez zmian.
