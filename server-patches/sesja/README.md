# sesja – Sesja farmienia

`MT2009_PLUS_FARM_SESSION_V1` (właściciel, 5.11.2026: paczka „p-sesja-farmienia”, Autor: Digi Rasta, znacznik
`DR_FARM_SESSION_V1`). Port na linię Yohara 3.x – przeniesione tylko bloki `DR_FARM_SESSION_V1` (wspólne pliki paczki
niosą też bloki p-sidekick-shop, p-dropek i p-lucznicy-strzaly – tych tu nie ma). Wygląd okna według zrzutów właściciela.

**Nakładana jako OSTATNIA** (po `pety`). Linux/VPS: `python3 apply_sesja.py <game/src>`; Windows: `Apply-SesjaPatch.ps1`
(`tools/port/Apply-MT2009PlusEngine.ps1`, na końcu). Edycja już nałożona jest pomijana; edycja, której stary kod nie
występuje dokładnie raz, zatrzymuje całość, zanim cokolwiek zostanie zapisane. `gen_edits.py [<game/src>]` pisze
`edits.json` (35 edycji) i sprawdza kotwice.

## Co robi

- Gracz zaczyna sesję (1/2/4/8 godz. albo bez limitu), sesja liczy czas w grze (stoi przy wylogowaniu, zmianie kanału
  i rdzenia), doświadczenie, Yang, przedmioty i zabicia – osobno potwory, Metiny i bossy; do tego przedmioty
  i zabicia wg rodzaju, mapy. Pauza, wznowienie, zakończenie; limit kończy sesję sam (FarmResult 6).
- Przedmiot liczy się, gdy trafi do torby (podniesienie: także dla właściciela w drużynie; przedmiot podany od razu
  przez nagrodę zabicia – karta, owoc rangi, runa, autoloot). Yang z zabicia – w chwili wpłaty (także udziały drużyny).
- Historia: 50 ostatnich zakończonych sesji (tabela trzyma 100). Statystyki: suma, okres (dziś / 7 dni), rekordy,
  kategorie, top przedmiotów, najczęściej zabijani, mapy.
- **Boty nigdy się nie liczą**: `DrFarmIsHuman` = nie deskryptor bota (`DESC::IsBot`) i nie zarejestrowany PID bota
  (`CPlayerBotManager::IsRegisteredBotPID`, jak ranking tygodniowy). Wejście bota nie robi zapytania.

## Tabele (bez SQL – rdzeń kanału robi je przy starcie, `CREATE TABLE IF NOT EXISTS`)

`player.dr_farm_session` (+ nasza kolumna `yang_last`), `player.dr_farm_item`, `player.dr_farm_mob`,
`player.dr_farm_map`. Syslog: `DR_FARM: table ready` (raz na rdzeń); błąd: `DR_FARM: the table <n> cannot be created`.

## Silnik (`edits.json`) i nakładka

Nakładka: `linux-port/overlays/playerbot/src/game/src/dr_farm_session.cpp` / `.h` (całe pod `#ifdef DR_FARM_SESSION_V1`;
Makefile bierze `$(wildcard *.cpp)`, więc plik kompiluje się sam).

| Plik | Miejsce | Co |
|---|---|---|
| `common/CommonDefines.h` | po `ENABLE_CHANGELOOK_SYSTEM` | `#define DR_FARM_SESSION_V1` (`DR_FARM_DEBUG` – tylko ręcznie w buildzie testowym) |
| 7 plików | include | `dr_farm_session.h` (zamiast deklaracji w bloku – żadnej pułapki przestrzeni nazw) |
| `main.cpp` | po `OXEvent_manager.Initialize()` | `DrFarmInit()` – tabele |
| `cmd.cpp`, `cmd_general.cpp` | obok `towarzysz` | `/sesja` (`do_sesja` → `DrFarmCommand`) |
| `input_login.cpp` | `Entergame`, po `SendSpecialFlagsToClient` | `DrFarmOnEnterGame` (bez botów) |
| `char.cpp` | `Disconnect`, po `CatchKingOnDisconnect` | `DrFarmOnDisconnect` |
| `item.cpp` | `SetOwnership` | `DrFarmTagOwner` |
| `char_battle.cpp` | `Reward` po `KillLog`; przed `RewardGold`; po `CreateDropItem`; `RewardGold` (Yang na ziemi, 2 miejsca); `GiveExp` (ENABLE_NEWEXP_CALCULATION) | zabicie + zakres nagród, zakres dropu, znaczniki dropu, Yang na ziemi, doświadczenie |
| `char_item.cpp` | `GiveGold` (3), `PickupItem` (przed blokiem Gai i 4 miejsca sukcesu + Yang), `AutoGiveItem` (obie wersje, 5) | Yang, podniesienia, przedmioty podane od razu |

## Protokół (CHAT_TYPE_COMMAND, linia ≤ 480 B, `static_assert`)

Paczka: `FarmInfo`, `FarmResult`, `FarmItems`, `FarmDone`, `FarmHist`, `FarmHistEnd`, `FarmStatSum/Per/Rec/Cat/Top/Mob/Map`,
`FarmStatEnd` (opis w nagłówku `dr_farm_session.cpp`). **Nasze dodatki** (okno ze zrzutów):
- `FarmInfo … <yang_last>` – czas ostatniego Yang (dymek wiersza Yang „Ostatni drop”); starszy klient czyta tylko
  pola, które zna.
- `FarmSpark <minuta> 40 <c1> … <c40>` – przedmioty w ostatnich 40 minutach czasu aktywnego (wykres
  „Przedmioty (maks. N)”), tylko pamięć; przed każdym `FarmDone` sesji.
- `FarmStatAll <n> <vnum>:<kat>:<ilość> …` – sumy 300 najczęstszych przedmiotów z kategorią (własne kategorie gracza
  w oknie zabierają swoje przedmioty z sześciu kategorii serwera).

## Klient (root, `client-patches/client-2.0.30/root`)

`uifarmsession.py` (nowy), `game.py` (komendy `Farm*`, klawisz), `interfacemodule.py` (`wndFarmSession`),
`keybind.py`. **Klawisz Y** (wiersz `player_stat`, „Sesja farmienia”) – Y był wierszem starego okna statystyk, więc
wolnego klawisza nie trzeba; stare okno („Ogólne” paczki) ma własny wiersz `player_stat_general` bez klawisza.
Zakładka „Ogólne” paczki odpada (zrzuty: trzy zakładki). Wygląd rysowany w kodzie (plansza klienta + paski i teksty) –
bez nowych obrazków.

## Sprawdzenie

`python3 gen_edits.py <game/src>` (kotwice), kompilacja TU (`dr_farm_session.cpp`, `char_battle.cpp`, `char_item.cpp`,
`item.cpp`, `char.cpp`, `input_login.cpp`, `main.cpp`, `cmd.cpp`, `cmd_general.cpp`: rc=0, `nm` – symbole `DrFarm*`
globalne, bez przestrzeni nazw). Na serwerze testowym: syslog `DR_FARM: table ready`, w grze Y → „1 godz.”, zabicia
i podniesienia rosną, `/sesja stat` w czacie nic nie psuje (odpowiedź idzie do okna).
