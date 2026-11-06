# gildiaexp – bez oddawania doświadczenia gildii na Poziomie Czempiona

Znacznik: `MT2009_PLUS_GUILD_OFFER_CHAMPION_V1`. Decyzja właściciela z 6.11.2026 (zgłoszenie gracza z vps3, 3.0.7-test):
„Jednak zrób zgodnie z wiki. Czyli na lvl championa nie można oddawać expa.”

## Błąd

`CGuild::OfferExp` sprawdza i zabiera **zwykłe** PD (`GetExp`, `PointChange(POINT_EXP, -x)`). Czempion widzi w kliencie
pasek Czempiona (`POINT_CONQUEROR_EXP`), a zwykły pasek 120 poziomu jest ukryty i po każdym zabiciu dopełnia się do
`next_exp − 1` (`MT2009_PLUS_CHAMPION_V1 (max level exp)`). Oddanie gildii brało więc PD z ukrytego paska: gracz nic nie
tracił, gildia dostawała darmowe PD (vps3, 6.11.2026 21:20:26–21:20:59: 7 ofiar, 1 132 221 700 PD → +11 322 217 PD
gildii, dwa awanse gildii; o 21:24:57 zwykły pasek znów 2 499 999 999).

## Zmiana (`edits.json`, `gen_edits.py`)

| Plik | Znacznik | Co |
|---|---|---|
| `guild.cpp` | `(refuse)` | `CGuild::OfferExp`: `conqueror_level >= 1` → odmowa, nic nie zabrane, gildia nic nie dostaje; gracz dostaje linię „[Gildia] Na Poziomie Czempiona nie mozna oddawac doswiadczenia gildii.” (tłumaczenia: `lang/*/40_server_custom.tsv`), bot – bez linii. Dotyczy okna gildii, questów (`guild.offer_exp`) i botów |
| `input_main.cpp` | `(no second line)` | Czempion nie dostaje drugiej linii „[Gildia] Przekazanie Punktów Doświadczenia nieudane.” |

Nakładka: `playerbot_guild.h` (`ManagePlayerBotGuildExp`) – bot-Czempion nie próbuje oddawać (bez logu, bez odmowy).
Poniżej Poziomu Czempiona bez zmian (także poprawka 120 z `MT2009_PLUS_PD_BONUS_V1`).

## Wdrożenie

Linux/VPS: `python3 apply_gildiaexp.py <game/src>` – po `czempion` i `pdbonus`, przed `logtrim` (lista łatek
`yohara-deploy.sh`); Windows: `Apply-GildiaExpPatch.ps1` (`tools/port/Apply-MT2009PlusEngine.ps1`, po `language`).
Edycja już nałożona jest pomijana; edycja, której stary kod nie występuje dokładnie raz, zatrzymuje całość.

## Klient (następna runda)

`root/uiguild.py` `__OnClickOfferButton` otwiera okno z limitem `player.GetStatus(player.EXP)` (zwykłe PD). Serwer i tak
odmawia; w kliencie wystarczy na Poziomie Czempiona (`player.GetStatus(player.CONQUEROR_LEVEL) >= 1`) pokazać komunikat
zamiast okna (albo wyszarzyć przycisk „Oddaj PD”).

Sprawdzone: `-fsyntax-only` `guild.cpp`, `input_main.cpp`, `playerbot_manager.cpp` na kopii drzewa serwera testowego
(obraz `m2-libs:check`), 6.11.2026.
