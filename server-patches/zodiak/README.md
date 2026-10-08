# Świątynia Zodiaku – `MT2009_PLUS_ZODIAC_V1`

**Autor: Digi Rasta** (paczka „nowy-system” 0.35.0, karta `SYSTEMY/zodiak.md`; na podstawie paczki WLsj24
„ZodiacTemple” 2.1–3.0 z metin2.dev i oficjalnych danych z 2019 r.). Mapa 358 `metin2_12zi_stage` (6×6 na
307200 1408000), prywatne piętra 3580000–3589999 na rdzeniu game1.

## Gdzie co jest

| Część | Miejsce |
|---|---|
| Logika (nowe pliki, wszystko w `#ifdef ENABLE_12ZI`) | `linux-port/overlays/playerbot/src/game/src/playerbot_zodiac_*`: `temple.h/.cpp` (klasy `CZodiac`, `CZodiacManager`, wersja 3.0), `ext.cpp` (definicje, które paczka wstawiała do plików silnika), `battle.cpp` (umiejętności bossów), `char.cpp` (tablica nagród), `questlua.cpp` (funkcje Lua), `regen.inc` (regeny mapy, dołączany do `regen.cpp`) |
| Haki w plikach silnika | `edits.json` (64 zmiany w 24 plikach, każda ze znacznikiem `MT2009_PLUS_ZODIAC_V1 (<n>)`); `apply_zodiak.py <game/src>` (Linux/VPS) i `Apply-ZodiakPatch.ps1` (Windows, ostatni krok `tools/port/Apply-MT2009PlusEngine.ps1`) czytają ten sam plik |
| Generator haków | `tools/zodiak/gen_zodiak_edits.py <zodiak_haki.py z paczki> <połatany game/src> <edits.json>` – kotwice paczki rozwiązane na naszym silniku po wszystkich innych łatkach |
| Baza | `linux-port/docker/mariadb/playerbot/zodiak.sql` (z `96_zodiak.sql` paczki; `apply.sh`, przed żywiołami) |
| Dane serwera | `linux-port/docker/game/zodiak/` (mapa, `data/dungeon/zodiac`, ruchy 45 potworów, `group.zodiak.txt`, `locale_string.zodiak.txt`) – krok `share: Swiatynia Zodiaku` w `Dockerfile` (+ `map_names[358]`, `/goto zodiac`) |
| Questy | `linux-port/docker/game/quest/zodiac_{temples,milbon,prism_mission,emergency_mission}.quest` (lista i funkcje `qc` w `Dockerfile`) |
| Rdzeń | `bin/m2-render-config`: 358 na game1 w obu układach |

`ENABLE_12ZI` (i `ENABLE_SERVERTIME_PORTAL_SPAWN`) wpada do `common/CommonDefines.h` jako **ostatnia** zmiana;
skrypt nie zapisuje niczego, jeśli choć jednej kotwicy nie ma dokładnie raz – makro nigdy nie przyjdzie bez haków.

## Zmiany silnika (`edits.json`)

| Znacznik | Plik | Co |
|---|---|---|
| `(1)` | `common/length.h` | tryby czatu misji Zodiaku |
| `(2)` | `common/length.h` | efekty Zodiaku |
| `(3)` | `common/length.h` | AFFECT_CZ_UNLIMIT_ENTER |
| `(4)` | `common/length.h` | AFF_CZ_UNLIMIT_ENTER |
| `(5)` | `typedef.h` | LPZODIAC |
| `(6)` | `packet.h` | naglowek efektu Zodiaku |
| `(7)` | `packet.h` | pakiet efektu Zodiaku |
| `(8)` | `char.h` | Zodiak - skladowe 1 |
| `(9)` | `char.h` | Zodiak - skladowe 2 |
| `(10)` | `char.h` | Zodiak - skladowe 3 |
| `(11)` | `char.h` | Zodiak - skladowe 4 |
| `(12)` | `char.cpp` | include zodiac_temple.h |
| `(13)` | `char.cpp` | Zodiak - regen przy Destroy |
| `(14)` | `char.cpp` | Zodiak - Destroy |
| `(15)` | `char.cpp` | Zodiak - pozycja wyjscia |
| `(16)` | `char.cpp` | Zodiak - SetParty |
| `(17)` | `char.cpp` | Zodiak - OnClick |
| `(18)` | `dungeon.h` | Zodiak - metody |
| `(19)` | `dungeon.h` | Zodiak - skladowa |
| `(20)` | `party.h` | class CZodiac |
| `(21)` | `party.h` | Zodiak - Get/SetZodiac |
| `(22)` | `party.h` | Zodiak - skladowe |
| `(23)` | `party.h` | Zodiak - for_Only_party |
| `(24)` | `party.cpp` | include zodiac_temple.h |
| `(25)` | `party.cpp` | Zodiak - SetPartyNull |
| `(26)` | `party.cpp` | Zodiak - QuitParty |
| `(27)` | `party.cpp` | Zodiak - dolaczenie |
| `(28)` | `party.cpp` | Zodiak - blisko lidera 1 |
| `(29)` | `party.cpp` | Zodiak - blisko lidera 2 |
| `(30)` | `party.cpp` | Zodiak - blisko lidera 3 |
| `(31)` | `questmanager.h` | Zodiak - metody |
| `(32)` | `questmanager.h` | Zodiak - skladowa |
| `(33)` | `regen.h` | Zodiak - level |
| `(34)` | `regen.cpp` | Zodiak - MODE_LEVEL |
| `(35)` | `regen.cpp` | Zodiak - regen_zodiac |
| `(36)` | `char_manager.h` | Zodiak - spawn |
| `(37)` | `battle.cpp` | Zodiak - obrazenia potworow |
| `(38)` | `battle.cpp` | Zodiak - bez PvP |
| `(39)` | `char_battle.cpp` | include zodiac_temple.h |
| `(40)` | `char_battle.cpp` | Zodiak - smierc potwora |
| `(41)` | `char_battle.cpp` | Zodiak - smierc gracza |
| `(42)` | `char_battle.cpp` | Zodiak - wskrzeszony potwor |
| `(43)` | `char_battle.cpp` | Zodiak - koniec Dead |
| `(44)` | `char_battle.cpp` | Zodiak - Damage 1 |
| `(45)` | `char_battle.cpp` | Zodiak - Damage 2 |
| `(46)` | `char_state.cpp` | include zodiac_temple.h |
| `(47)` | `char_state.cpp` | Zodiak - boss |
| `(48)` | `char_item.cpp` | Zodiak - przedmioty 72327-72329 |
| `(49)` | `char_affect.cpp` | Zodiak - makro |
| `(50)` | `cmd.cpp` | Zodiak - deklaracje |
| `(51)` | `cmd.cpp` | Zodiak - polecenia |
| `(52)` | `cmd_general.cpp` | include zodiac_temple.h |
| `(53)` | `cmd_general.cpp` | Zodiak - restart |
| `(54)` | `input_login.cpp` | include zodiac_temple.h |
| `(55)` | `input_login.cpp` | Zodiak - SetZodiac |
| `(56)` | `input_login.cpp` | Zodiak - logowanie |
| `(57)` | `main.cpp` | include zodiac_temple.h |
| `(58)` | `main.cpp` | Zodiak - menedzer |
| `(59)` | `main.cpp` | Zodiak - Initialize |
| `(60)` | `questlua.cpp` | Zodiak - rejestracja |
| `(61)` | `shop.cpp` | Zodiak - limit zakupu |
| `(62)` | `shop.cpp` | Zodiak - licznik zakupu |
| `(63)` | `char_affect.cpp` | Zodiak - uzycie makra |
| `(64)` | `common/CommonDefines.h` | ENABLE_12ZI |

Numery wspólne z exe (muszą być takie same po obu stronach): pakiet **GC 220** `HEADER_GC_SEPCIAL_ZODIAC_EFFECT`
(header, type, type2, vid, x, y – 15 B), typy czatu `CHAT_TYPE_MISSION/SUB_MISSION/CLEAR_MISSION` = 13–15,
`SE_*` Zodiaku (15) od 39 po `SE_EFFECT_ACCE_EQUIP`, `AFFECT_CZ_UNLIMIT_ENTER` = 600, bit `AFF_CZ_UNLIMIT_ENTER` = 44.

## Kolizje sprawdzone 8.10.2026 (świat 2.28.0)

Wolne: mapa 358 (`map/index`, katalog mapy), nagłówek 220 (serwer i nasze exe), przedmioty 300–309, 310–319 (Miecz Zodiaku – paczka go nie wymienia w rezerwacjach), 1180–1189,
2200–2209, 3220–3229, 5160–5169, 6120–6129, 7300–7309, 19290–19299, 19490–19499, 19690–19699, 19890–19899,
21200–21209, 33001–33033, 72327–72329; potwory 2600–2692, 2700–2735, 2750–2862, 2900–2937, NPC 20438–20464;
sklep 41 i NPC 20451; `skill_proto` 270–271; `refine_proto` 22401–22418; grupy (51, vnumy 2608–2937, nazwy
`Zodiac*`); katalogi `data/monster/12zi_*`, `cz_*`; `data/dungeon/zodiac`; kolumna `player.bead`, tabele `zodiac_npc*`.
Mapa 358 na game1: 46 map z `MAP_ALLOW_LIMIT` 48.

## Zmiany względem paczki

- pliki nowe jako `playerbot_zodiac_*` w nakładce (lista plików aktualizacji bierze `playerbot_*`), include'y w hakach zmienione;
- haki silnika jako `edits.json` (nasz mechanizm łatek) zamiast `zodiak_haki.py`; Dockerfile i `m2-render-config` edytowane w repo;
- `zodiak.sql` bez kasowania dawnych rodzin Zodiaku z `95_wiki_nowe.sql` paczki (u nas ich nie było);
- `apply.sh`: Zodiak przed żywiołami, więc zasady właściciela z 7.10 (żywioły potworów) obowiązują też w świątyni.

## Boty (`MT2009_PLUS_ZODIAC_BOTS_V1`, `playerbot_zodiac_bots.h`)

Boty z drużyny osoby idą z nią do świątyni (jak do innych lochów drużynowych, `playerbot_party_dungeon.h`):

- 358 jest jedną z map `IsPlayerBotPartyDungeonMap`; bot wchodzi za osobą na jej piętro (`FollowPlayerBotPersonIntoDungeon`
  przyjmuje piętro świątyni – to `CZodiac`, nie `CDungeon`), walczy obok niej i wychodzi z nią (wyjście awaryjne: dziedziniec 358);
- `CPlayerBotManager::WarpBot` po każdej zmianie mapy robi bota członkiem świątyni piętra, na którym stoi (`SetZodiac`;
  osoba dostaje to przy logowaniu z haka `input_login.cpp`), a poza świątynią czyści jej flagi śmierci;
- posągi (20452–20463) i działo (20464) zostawia osobie (bije je tylko, gdy osoba je bije);
- śmierć na piętrze: `restart_here` otworzyłby tylko okno wskrzeszenia, na które bot nie odpowie – bot wstaje za swoje
  Pryzmaty (33025/33032, cena osoby 1/2/4/8/10), a bez nich wstaje sam (log `PLAYERBOT_ZODIAC: stood up`);
- wejście płaci osoba: quest `zodiac_temples` nie liczy Animosfer bota z drużyny (`pc.is_playerbot()`).

Własne przejścia botów (bez osoby) – **jeszcze nie ma**. Potrzebne w `playerbot_dungeon_runs.h` / `_rules.h`:
klucz `zodiak` w `RUN_RULES` (pasmo poziomów, 4–8 botów), zbiórka przy portalu dnia na 358 (`data/dungeon/zodiac/days`,
portal 20439–20450 wg dnia tygodnia), wejście jak w questcie (`CZodiacManager::StartTemple` dla lidera z drużyną, Animosfery
botów: 12 z `bead` albo Znak Strażnika 72328), plan piętra wg misji (`ZodiacFloorMessage`: wszystkie potwory / Metiny /
boss bez śmierci / kupiec – bonusowe piętro do pominięcia), przycisk następnego piętra (`/nextfloor` lidera), Pryzmaty
botów z nagród albo z rynku, koniec po wybranym piętrze (`/jumpfloor`?), tsv z wynikami jak `playerbot_dungeon_runs.tsv`.
Bez testu na serwerze to zbyt dużo zgadywania – do zrobienia po pierwszym teście świątyni z osobą.

## Do sprawdzenia / znane braki

- receptury ulepszania broni i zbroi Zodiaku (22401–22418) wymagają materiałów 30611, 30612 (nie ma ich u nas ani w paczce)
  oraz 30616–30618 (przychodzą z „nowe rodziny z wiki” 0.33.0) – do decyzji właściciela;
- paczka nie sprawdziła w grze: efektów bossów (pakiet 220), pięter od 2F, Kupca, Pryzmatów, nagród, skoku piętra.
