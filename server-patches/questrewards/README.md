# Nagrody z questów – część silnika

Znacznik `MT2009_PLUS_QUEST_REWARD_OVERRIDES_V1`, pliki `game/src/questlua_pc.cpp`,
`questlua_affect.cpp`, `questlua_quest.cpp`, `questlua_global.cpp`; cała logika w nakładce
`linux-port/overlays/playerbot/src/game/src/playerbot_quest_rewards.h/.cpp`.

Panel Sebana, Edytor bazy danych → **Questy** (`dbeditor/quests.py`), pozwala zmienić nagrodę questa bez
ruszania skompilowanego questa: zamiast przedmiotu X dać Y × N, yang i doświadczenie × mnożnik albo stała
kwota, inny bonus stały Biologa (`affect.add_collect`), oraz **dodatkowe** nagrody (przedmiot × ilość, yang,
doświadczenie, bonus) do istniejącej nagrody albo do przejścia questa w dany stan.

Jak to działa:

- Panel zapisuje `quests/quests.custom.txt` w wolumenie spool; przed startem rdzeni `m2-quests apply`
  (gra, `linux-port/docker/game/bin/m2-quests`) sprawdza plik i przepisuje reguły nagród do
  `locale/poland/quest/reward_overrides.txt`.
- Każdy rdzeń wczytuje ten plik przy pierwszej nagrodzie. Wywołania dodane tą łatką siedzą na początku
  funkcji nagród, zaraz po odczytaniu argumentów:
  - `pc.give_item2`, `pc.give_item` → `OnItem` (vnum, ilość; inny przedmiot, inna ilość albo nic; ilość
    większa niż jeden stos jest dawana w kilku stosach),
  - `pc.change_money` / `changemoney` / `change_gold`, `pc.give_gold` → `OnGold` (tylko kwota > 0 –
    opłata zostaje opłatą),
  - `pc.give_exp2`, `pc.give_exp`, `pc.give_exp_perc` → `OnExp` (kwota, którą wywołanie daje),
  - `affect.add_collect` → `OnBonus` (typ POINT_* i wartość – bonusy Biologa),
  - `set_state` / `setstate` i `set_quest_state` na własnym queście → `OnState` (tylko dodatkowe nagrody).
- Quest rozpoznawany jest po bieżącym queście gracza (`CQuestManager::GetCurrentPC()->GetCurrentQuestName()`),
  nagroda po **oryginalnych argumentach** wywołania („przedmiot 50109 questa collect_quest_lv30”, „bonus
  POINT_MOV_SPEED 10”), a nie po stanie – Biolog robi `set_state(__complete)` przed rozdaniem nagród.
- Każda zmiana trafia do syslog: `QUEST_REWARD_OVERRIDE <quest>: ...`.
- Zmiana działa dla nagród wydanych po restarcie. Bonusy już dane zostają – `affect.add_collect` sumuje
  wszystkie wywołania w jeden efekt na typ POINT, więc nie da się ich przeliczyć wstecz.

Stosowanie: `Apply-QuestRewardsPatch.ps1 -SourceDir <game/src>` (Windows, wywołuje go
`tools/port/Apply-MT2009PlusEngine.ps1`) albo `python3 apply_questrewards.py <game/src>` (Linux/VPS).
Każda zmiana z `edits.json` nakłada się raz; brak oczekiwanego kodu przerywa bez zmian. Pliki nakładki
(`playerbot_quest_rewards.*`) kopiuje do drzewa silnika zwykła synchronizacja nakładki (`playerbot_*`).
