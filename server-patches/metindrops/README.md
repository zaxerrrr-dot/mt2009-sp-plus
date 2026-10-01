# Drop z metinów i limit komend

Poprawka silnika (`game/src/item_manager.cpp`, `game/src/cmd.cpp`), nakładana
po `botsashdrop` i `raretoggle`. Znacznik: `MT2009_PLUS_METIN_DROPS_V1`.

- **Szarfa z metinów: 15%** (bossy dalej 80%). Silnik liczy metiny jako rangę
  boss, więc wcześniej każdy metin dawał szarfę z szansą 80% (1 października
  2026: „Szarfa z metinów 15%”).
- **Cor Draconis z metinów: 20%** (było 50%; bossy 80%, zabicie przez bota
  dalej 5%).
- **Limit komend:** polecenia, które klient wysyła sam (`autohunt_target`,
  `autohunt_loot`, `gmpanel_check_gm`, `kalendarz`, `ingame_event`), nie
  liczą się do limitu, a gracz ma 10 poleceń na pół sekundy zamiast 5.
  Wcześniej te zapytania zjadały limit i serwer odrzucał kliknięcia gracza
  (statystyki, okno towarzysza, „lochy open”).

Stosowanie: `Apply-MetinDropsPatch.ps1 -SourceDirectory <game/src>` (Windows)
albo `python3 apply_metindrops.py <game/src>` (Linux/VPS). Każdy krok
nakłada się raz; brak oczekiwanego kodu przerywa bez zmian.
