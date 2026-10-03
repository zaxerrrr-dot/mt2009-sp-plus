# Usuwanie misji (/usunmisje) – część silnika

Znacznik `MT2009_PLUS_CLEAR_MISSIONS_V1`, plik `game/src/questlua_pc.cpp`.

Okno `/usunmisje` (quest `usun_misje`, klient `root/uiusunmisje.py`) ustawia wybrane misje w ich stan
ukończenia. Sam stan nie zabiera listu z listy misji klienta ani strzałek z mapy – robi to `q.done()`
i `target.delete()` z wnętrza tamtego questa. Nowa funkcja Lua:

- `pc.clear_quest_letter("nazwa_questa")` – wysyła klientowi pakiet informacji o queście z „koniec”
  (to samo co `q.done()`), zdejmuje znacznik listu w stanie questa i usuwa wszystkie jego cele
  (`CTargetManager::DeleteTarget(..., NULL)`). Zwraca indeks questa (0 – nie ma takiego); klient zdejmuje
  nim przycisk listu z lewej strony ekranu.

Dzięki temu misje znikają od razu, bez teleportu i ekranu ładowania (wcześniej postać była
przeładowywana w tym samym miejscu).

Stosowanie: `Apply-ClearMissionsPatch.ps1 -SourceDir <game/src>` (Windows, wywołuje go
`tools/port/Apply-MT2009PlusEngine.ps1`) albo `python3 apply_clearmissions.py <game/src>` (Linux/VPS).
Każda zmiana z `edits.json` nakłada się raz; brak oczekiwanego kodu przerywa bez zmian.
