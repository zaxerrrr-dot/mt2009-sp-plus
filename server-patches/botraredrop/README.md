# Drop Cor Draconis i szarf także dla botów

Poprawka silnika do reguł dropu MT2009 Plus z metinów i bossów
(`game/src/item_manager.cpp`, `ITEM_MANAGER::CreateDropItem`).

## Co było nie tak

Cor Draconis (metin 50%, boss 80%) i szarfa (boss 80%) powstawały tylko
wtedy, gdy potwora zabił **prawdziwy gracz**: oba bloki miały warunek
`!pkKiller->GetDesc()->IsBot()`. Gdy zabijał bot, przedmiot w ogóle nie
powstawał, więc boty nie miały czego wystawić: licznik
`PLAYERBOT_MARKET: rare goods` pokazywał stale `cor=0`.

## Co robi poprawka

- **Warunek:** z obu bloków znika `!IsBot()`. Zabójstwo bota losuje Cor i
  szarfę z **tymi samymi szansami** co zabójstwo gracza.
- **Do plecaka, nie na ziemię:** przedmiot z zabójstwa bota trafia prosto do
  jego plecaka (`AutoGiveItem`). Przy pełnym plecaku upada obok bota.
- **Blokada podnoszenia bez zmian:** `char_item.cpp` (`PickupItem`) dalej nie
  pozwala botowi podnieść Cor Draconis z ziemi, więc boty nie zabierają
  Corów, które wypadły graczom.
- Dalej działa logika botów z `playerbot_*` (PR #9): bot Cora nie otwiera,
  szarfy nie zakłada, wystawia je na stragan, a po 12 h bez sprzedaży
  oddaje kupcowi (`rare_unsold`).
- W logu `[DS_COR_DROP] ... is_bot=1` i `[SZARFA_DROP]` z nazwą bota.

## Pliki

- `Apply-BotRareDropPatch.ps1` – Windows; wywołuje go `start-server.ps1`
  przed każdą budową (tak jak `offlineshopsearch`).
- `apply_botraredrop.py` – Linux/VPS: `python3 apply_botraredrop.py
  linux-port/docker/game/src/server/game/src`, potem `docker compose build game`.

Obie wersje robią te same cztery podmiany, oznaczają plik markerem
`MT2009_PLUS_BOT_RARE_DROP_V1` (drugie uruchomienie nic nie zmienia),
zachowują końcówki linii (CRLF/LF) i nie zmieniają niczego, jeśli
oczekiwanego kodu nie ma.
