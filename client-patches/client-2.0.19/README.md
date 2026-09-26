# Klient 2.0.19: statusy botów nad głowami

Względem klienta 2.0.18 (`client-patches/client-2.0.18`):

- `playerbot_status_tail.py` – nowy: komenda serwera `PlayerBotStatus <vid>
  <hex>` rysuje status bota nad jego głową (a nie w historii czatu), a
  `PlayerBotTitle <vid> <osobowość>` jego tytuł osobowości (tylko z EXE, który
  ma `textTail.AttachPersonality`; starszy EXE tytuł pomija bez błędu);
- `game.py` – obsługa obu komend. Dotąd klient ich nie znał i zapisywał
  każdą jako „Unknown Server Command” w `syserr.txt`.

Pakowanie: podmienić `game.py` i dodać `playerbot_status_tail.py` w `root`
klienta 2.0.18, przepakować `root.data`/`root.index`.
