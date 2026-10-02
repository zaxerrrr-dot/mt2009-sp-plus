# System Legend botów (2 października)

Zmiany silnika opisane w `edits.json`, każda z własnym znacznikiem `MT2009_PLUS_LEGENDS_V1 (...)`.
Silnik tylko woła trzy funkcje nakładki botów (`playerbot_legends.h`); cała reszta systemu
(tiery, Legendy, Czempioni, reputacja, ogłoszenia, gildie Legend, PvP) jest w nakładce.

| Znacznik | Plik | Co robi |
|---|---|---|
| `MT2009_PLUS_LEGENDS_V1 (attack)` | `battle.cpp` | `CalcAttBonus`: bot z tierem bije mocniej – przeciw ludziom i przeciw potworom o promile swojego tieru (`PlayerBotLegendAttackBonus`). Dotyczy zwykłych ciosów, strzał i umiejętności. |
| `MT2009_PLUS_LEGENDS_V1 (exp)` | `char_battle.cpp` | `GiveExp`: bot z tierem dostaje więcej expa (×1,05 / ×1,125 / ×1,25 / ×1,25; `PlayerBotLegendExpBonus`). |
| `MT2009_PLUS_LEGENDS_V1 (death)` | `char_battle.cpp` | `CHARACTER::Dead`: śmierć dla Systemu Legend – gracz zabity przez bota z tierem (reputacja, licznik), Legenda albo Czempion pokonany przez gracza (ogłoszenie, bez nagrody), ostatni cios bossa (`PlayerBotLegendOnDeath`). |

Bez tej poprawki nakładka działa dalej (PŻ, ulepszanie, księgi, tytuły, Czempioni, PvP), tylko
bez trzech powyższych premii/zdarzeń.

## Tiery i premie (tylko boty)

| | Wyróżniający się | Specjalny | Chodząca Legenda | Czempion Królestwa |
|---|---|---|---|---|
| Ilu | ~4% botów | ~2% botów | 2 na królestwo | najwyżej 1 na królestwo |
| PŻ | +2,5% | +6% | +12,5% | +20% |
| Silny przeciw ludziom | +1,5% | +3,5% | +6% | +9% |
| Silny przeciw potworom | +1,5% | +3,5% | +6% | +7,5% |
| Exp | ×1,05 | ×1,125 | ×1,25 | ×1,25 |
| Jedna księga / Kamień Duchowy liczy się jak | 1 | 2 | 3 | 4 |
| Szansa ulepszenia (kowal i zwoje) | +5 pkt | +10 pkt | +15 pkt | +20 pkt |

Liczby są stałymi w `playerbot_types.h` (`PLAYERBOT_LEGEND_*`). Przełącznik `LEGENDS` w obu
panelach (domyślnie włączony) wyłącza cały system bez kasowania tierów
(`player.playerbot_legend`, `player.playerbot_legend_event`).

## Pliki

- `edits.json` – zmiany (plik, znacznik, stary i nowy kod);
- `Apply-LegendsPatch.ps1` – Windows (`tools/port/Apply-MT2009PlusEngine.ps1`);
- `apply_legends.py` – Linux/VPS: `python3 apply_legends.py <game/src>`; oba czytają ten sam `edits.json`.

Zmiana już nałożona (jest jej znacznik) jest pomijana; zmiana, której kodu nie
ma dokładnie raz, przerywa całość, zanim cokolwiek zostanie zapisane.
