# Szarfy dla botów tak jak dla graczy

Poprawka silnika (`game/src/item_manager.cpp`, `game/src/char_item.cpp`),
nakładana po `botraredrop`.

- **Boss:** bot losuje szarfę z zabitego bossa z szansą gracza, **80%**
  (wcześniej 3%, `botraredrop` V2). Silnik liczy metiny jako rangę boss, więc
  dotyczy to też metinów. Szarfa trafia do plecaka bota, przy pełnym plecaku
  przepada.
- **Skrzynia bossa:** bot otwierający skrzynię bossa losuje unikatową szarfę
  (6–10%) tak jak gracz. Przy pełnym plecaku bota szarfa przepada, zamiast
  upaść na ziemię.
- Znacznik: `MT2009_PLUS_BOT_SASH_DROP_V1`.

Stosowanie: `Apply-BotSashDropPatch.ps1 -SourceDirectory <game/src>` (Windows)
albo `python3 apply_botsashdrop.py <game/src>` (Linux/VPS). Każdy krok
nakłada się raz; brak oczekiwanego kodu przerywa bez zmian.
