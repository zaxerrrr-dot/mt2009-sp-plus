# pvpfan – PVP Fan: komenda `/pvpfan` i haki walki botów

`MT2009_PLUS_PVPFAN_V1` (decyzja właściciela, 7.11.2026: „PVP Fan” – wojny botów dla zabawy, np. 50 Wojowników Ciało
vs 50 Szamanów Smok). Cała logika jest w nakładce `linux-port/overlays/playerbot/src/game/src/playerbot_pvpfan.h`
(opis w nagłówku pliku), konfiguracja w panelu Seban (`Wydarzenia → PVP Fan`, `pvpfan.py`), tabele w
`linux-port/docker/mariadb/playerbot/pvpfan.sql`. Ta łatka dodaje tylko komendę GM i dwa haki silnika.

**Nakładana po `runyboty`** (kotwice: blok `ACMD(do_bot_runa)` i jego wiersz tabeli w `cmd.cpp`). Linux/VPS:
`python3 apply_pvpfan.py <game/src>`; Windows: `Apply-PvpFanPatch.ps1`. Edycja już nałożona jest pomijana; edycja,
której stary kod nie występuje dokładnie raz, zatrzymuje całość. Przy wdrożeniu dopisać `pvpfan` na końcu listy łatek.

| Plik | Co |
|---|---|
| `cmd.cpp` | `ACMD(do_pvpfan)` → `PlayerBotPvpFanCommand`, wiersz tabeli `pvpfan`, `GM_HIGH_WIZARD` |
| `battle.cpp` | `battle_is_attackable`: `PvpFanAttackable` przed strefą bezpieczną – boty wojny biją tylko boty innych drużyn tej samej wojny (królestwo, gildia, drużyna, tryb PK bez znaczenia), nikt inny ich nie bije i one nikogo innego (gracze tylko z opcją „gracze mogą dołączyć”); -1 = nie dotyczy |
| `char_battle.cpp` | `CHARACTER::Dead`: `PvpFanDeath` – śmierć na wojnie PVP Fan liczona jak w wojnie gildii (bez utraty rangi, bez wypadania przedmiotów); zabójstwo liczy wojna |

## Komendy (GM_HIGH_WIZARD)

- `/pvpfan` albo `/pvpfan lista` – kategorie (kod, stan, mapa, kanał, liczba postaci);
- `/pvpfan start <kod>` – boty kategorii logują się prosto na swoje miejsca areny, dostają ekwipunek, umiejętności,
  statystyki i mikstury, czekają;
- `/pvpfan gotowi <kod>` (też `ready`, `walka`) – odliczanie i walka do ostatniego bota jednej strony;
- `/pvpfan stop <kod>` – koniec w każdej chwili, boty wychodzą;
- `/pvpfan status <kod>` – stan, drużyny, żywi, zabójstwa;
- `/pvpfan tu <kod> [nr drużyny]` – środek areny (albo punkt startowy drużyny) z pozycji GM-a;
- `/pvpfan pozycja` – zapisuje pozycję GM-a jako podpowiedź w panelu.

Komenda na rdzeniu, który nie ma mapy areny (albo na innym kanale), trafia do kolejki `player.pvpfan_command` i
wykonuje ją rdzeń areny (co 3 s) – tak samo jak przyciski Start / Gotowi / Stop w panelu.

Przełączniki: `M2_PVPFAN` (domyślnie 1), flaga `m2_pvpfan_off` (gra albo wiersz `player.quest` z panelu),
`M2_PVPFAN_MAX_CATEGORY` (500), `M2_PVPFAN_MAX_TOTAL` (1000 na rdzeń), `M2_PVPFAN_SPAWN_PER_SEC` (20).
Logi: `PVPFAN:` (spis co minutę w trakcie wojny).
