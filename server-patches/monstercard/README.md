# Karty Potworów (Monster Card System)

**Autor systemu: Digi Rasta** (paczka „nowy-system” v0.25.2 – jego port paczki „Official-Monster-Card-System”,
Best Studio, na nasz silnik). System jest przeniesiony do MT2009 PLUS jako nasz kod – bez haków `zastosuj.py`:
zmiany silnika są tutaj (`edits.json`), reszta w naszych zwykłych miejscach (niżej). Znacznik:
`MT2009_PLUS_MONSTER_CARDS_V1`.

## Zmiany silnika (`edits.json`)

| Znacznik | Plik | Co robi |
|---|---|---|
| `MT2009_PLUS_MONSTER_CARDS_V1 (declare)` | `cmd.cpp` | deklaracja `do_cardmonster` |
| `MT2009_PLUS_MONSTER_CARDS_V1 (table)` | `cmd.cpp` | komenda `/cardmonster` (każdy gracz, `POS_DEAD`) |
| `MT2009_PLUS_MONSTER_CARDS_V1 (kill)` | `char_battle.cpp` | po `KillLog`: `MonsterCardOnKill(pkQuestKiller, this)` – karta z potwora puli (5%) i postęp misji (zabójstwo towarzysza liczy się właścicielowi) |
| `MT2009_PLUS_MONSTER_CARDS_V1 (use)` | `char_item.cpp` | początek `UseItemEx`, po Rumi: `MonsterCardUseItem` – użycie kart 50283/50284 |
| `MT2009_PLUS_MONSTER_CARDS_V1 (login)` | `input_login.cpp` | po `WeeklyRankOnLogin`: `MonsterCardOnLogin` – bonusy zestawów konta na postać (albo ich zdjęcie przy wyłączonym systemie) |

Funkcje są zdefiniowane w nakładce botów, `linux-port/overlays/playerbot/src/game/src/playerbot_monster_card.h`
(dane: `playerbot_monster_card_data.h`; oba w jednostce `playerbot_manager.cpp`), deklarowane w miejscu wywołania.

- `Apply-MonsterCardPatch.ps1` – Windows (`tools/port/Apply-MT2009PlusEngine.ps1`, po Drop wiki i rankingu
  tygodniowym – kotwice to ich wiersze);
- `apply_monstercard.py <game/src>` – Linux/VPS (np. przed buildem drzewa testowego:
  `python3 server-patches/monstercard/apply_monstercard.py <serwer>/linux-port/docker/game/src/server/game/src`);
  oba czytają ten sam `edits.json`.

Zmiana już nałożona (jest jej znacznik) jest pomijana; zmiana, której kodu nie ma dokładnie raz, przerywa
całość, zanim cokolwiek zostanie zapisane. Załatane pliki silnika jadą w paczce aktualizacji
(`launcher/server-update-files.mod.txt` – wszystkie cztery już tam są; `tools/New-M2UpdatePackage.ps1`
sprawdza znaczniki).

## Jak działa

- **Misja kart**: 3 cele z puli poziomu misji (15 poziomów, potem od 1; pule z 56 potworów, które mamy
  w `mob_proto` i które mają obrazek karty), zabicie wszystkich → Karta Potwora (50283, potwór w `socket1`)
  i kolejny poziom. Pierwszy reset misji w oknie 24 h darmowy, kolejne za Kartę Nowego Początku (72322);
  nowe cele za Kartę Nowego Układu (72323).
- **Drop**: potwór z puli daje swoją kartę z szansą 5% (na ziemi, 2 minuty tylko dla zabójcy).
- **Kolekcja** (na **konto**, `account_id`): użycie karty = +1 karta potwora; 9/21/30/60/90 kart → kolejna
  gwiazdka (0–5, „Ulepsz” w oknie). Funkcje gwiazdek: podgląd dropu (1★, z Drop wiki –
  `ITEM_MANAGER::GetDropWikiRows`, 20 pozycji na czacie), przemiana (3★, co 3 h; nie na OX), teleport
  w rejon potwora (4★, co 30 min; tylko mapy własnego królestwa i wspólne, nie w lochu), przywołanie
  (5★, co 12 h), rekrutacja (5★, co 24 h – potwór atakuje wskazanego gracza; **nigdy bota**), wymiana
  10 zebranych kart → karta handlowa 50284 (potwór w `socket0`).
- **Zestawy** (17 z 42 paczki – reszta wymaga potworów, których nie mamy): ranga N zużywa N gwiazdek każdego
  potwora zestawu i wymaga ich co najmniej tyle; bonus jako `AFFECT_COLLECT`, jeden zestaw polowy naraz.
  Postęp jest na koncie, bonusy na postaci – uzgadniane przy wejściu i po każdej zmianie (flagi questa
  `karty_bonus.p<punkt>` trzymają, ile postać już dostała).
- **Bez bonusu obrażeń od gwiazdek** – wzór paczki był błędny (12× przy 9 kartach, dzielenie przez 0).
- **Boty**: nie mają kart – ich zabójstwa, użycia i komendy są pomijane.
- **Przełącznik** `M2_MONSTER_CARDS` (`docker-compose.yml`, środowisko kontenera gry; domyślnie 1): 0 = system
  wyłączony – brak dropu, karty nic nie robią, `/cardmonster` odpowiada `DISABLED` (klient zamyka okno
  i pisze komunikat), bonusy zestawów schodzą przy następnym wejściu postaci; tabele i postęp zostają.
  MT2009 Classic ustawia 0.

Tabele mają nazwy z paczki (`player.nowy_karty_misja`, `nowy_karty_status`, `nowy_karty_osiagniecia`), a flagi
bonusów jego nazwy – świat, który grał na jego paczce, zachowuje postęp i nic nie dostaje podwójnie.

## Protokół (bez nowych pakietów)

Klient → serwer: `/cardmonster <polecenie> [arg…]` – `2` stan, `3` cele misji, `4` nowa misja, `5` nagroda,
`6` nowe cele (72323), `7` reset misji, `8 <funkcja> <potwór> [nick]` (0 teleport, 1 przemiana, 2 podgląd
dropu – z potworem 0 dane kolekcji, 3 przywołanie, 4 rekrutacja, 5 wymiana, 6 awans), `9` teleport do
przywołanego rekrutacją, `10 <zestaw>` załóż/zdejmij zestaw, `11 <zestaw> <ranga>` zgłoś zestaw.
GM (`GM_HIGH_WIZARD`): `gm_misja` (cele zabite), `gm_gwiazdki <0-5>`, `gm_karta <potwór> <ile>`,
`gm_reset` (kasuje postęp konta), `gm_przeladuj`, `gm_info`.

Serwer → klient: `MONSTERCARDSYSTEM` + `ADD_DATA/Level/<n>`, `ADD_DATA/Cards/<3 cele>/<16 talii>/<3 zabite>`,
`NEW_MISSION/<16>`, `REC_MAINCARDS/<3 cele>/<3 miejsca>`, `SUCCES_KILL/<i>`, `SUCCES_MISSION`, `OPEN`,
`ADD_MOB_INFO/<potwór>/<zebrane>/<zabicia>/<potrzeba>/<gwiazdki>/<teleport>/<przemiana>/<przywołanie>`,
`ILLUSTRATION_READY`, `NEW_DROPP_GUI/<potwór>`, `ADD_DROPP/<vnum>/<min>/<szansa %>/<max>`,
`OPEN_DROPP_GUI/<pozycje poza listą>`, `ACHIEV_APPLY/<zestaw>/<0|1>`, `ACHIEV_REGIST/<zestaw>/<ranga>`,
`NO_NEW_ORDER/<s>`, `NO_NEED_STAGE/<★>`, `MISSION_FAIL/0/0`, `DISABLED` i komunikaty (`NO_NEW_MISSION`,
`NOT_ALL_MONSTERS_KILLED`, `NO_PROMOTION`, `NOT_ENOUGH_FOR_TRADE`, `PLAYER_DONT_EXIST`, `MOB_IS_ALREADY_DEAD`).

## Gdzie jest reszta

- dane: `linux-port/docker/mariadb/playerbot/apply.sh` (3 tabele, przedmioty 50283, 50284, 72322, 72323 –
  `INSERT IGNORE`, przy każdym pełnym przebiegu);
- przełącznik: `linux-port/docker/docker-compose.yml`, `.env.example` (`M2_MONSTER_CARDS`);
- klient: `client-patches/client-2.0.30/root` (`monstercard.py`, `monstercard_data.py`, `monstercard_text.py`,
  `uimonstercard.py`, `uiscript/monstercard*.py`, `ui.py`, `uitooltip.py`, `game.py`, `keybind.py`, menu pod Esc,
  ikony `icon/item/`), grafiki `client-patches/client-2.0.30/atlas/d_/ymir work/ui/game/monster_card/**`
  i `public_mcard_*.dds`, wiersze przedmiotów `client-patches/client-2.0.30/tools/monstercard`
  (`README.md` klienta, sekcja „Karty Potworów”). Tabele potworów są w dwóch miejscach:
  `playerbot_monster_card_data.h` i `monstercard_data.py` – zmieniaj oba.

## Otwarte (decyzje właściciela)

- Źródło Kart Nowego Początku / Nowego Układu (72322/72323) – na razie tylko `/i` (paczka: drop z potworów
  puli, sklep albo nagroda).
- Rekrutacja: w świecie botów jedynymi „innymi graczami” są boty – tu nigdy nie są celem; zostawić funkcję
  tylko dla ludzi czy ją zdjąć?
- 17 z 42 zestawów (reszta potrzebuje potworów spoza bazy); bonusy to wartości oficjalne – do przeglądu po teście.
- Teleport tylko do 20 z 56 potworów (punkty z paczki); resztę można dopisać z `regen.txt`.
- Okno paczki nie ma przycisków podglądu dropu i rekrutacji (serwer je obsługuje: `/cardmonster 8 2 <potwór>`,
  `8 4 <potwór> <nick>`); „Ruch” (2★) bez modelu 3D nic nie robi.
- Model 3D potwora wymaga exe z `player.Mt2009Model*` (README klienta) – bez niego obrazek karty ×2.

## Test w grze (konto GM)

1. Start: `apply.sh` bez ostrzeżenia „Monster Card”; w bazie 3 tabele `nowy_karty_*` i 4 przedmioty;
   w logu gry `MONSTER_CARDS: on`.
2. Esc → „Karty Potworów”: okno, zakładka „Misja kart” → „Przyjmij misję” → 3 cele; `/cardmonster gm_info`.
3. Zabić cel (poziom 1: Cung-Mok 151, Mu-Rang 152, Lykos 191…) → „Pokonałeś potwora”; `/cardmonster gm_misja`;
   „Odbierz kartę potwora” → 50283 w ekwipunku, opis z nazwą i obrazkiem potwora.
4. `/i 50283`, użyć → „Karta potwora X: 1/9”; `/cardmonster gm_karta 151 9` → „Ulepsz” → gwiazdka.
5. `/cardmonster gm_gwiazdki 5` → teleport (4★), przemiana (3★), przywołanie (5★), wymiana 10 kart → 50284.
6. Zakładka „Bonusy zestawów” → zgłoś zestaw 1 (151, 152) → statystyka postaci rośnie; relog i druga postać
   konta – bonus jest; zdjęcie zestawu – bonus schodzi.
7. `M2_MONSTER_CARDS=0` + restart: okno pisze „Karty Potworów są wyłączone”, bonus schodzi po wejściu.
8. Boty zabijające potwory puli: brak kart na ziemi od ich zabójstw, brak wierszy w `nowy_karty_status` dla ich kont.
