# Świątynia Zodiaku – `MT2009_PLUS_ZODIAC_V1`

**Autor: Digi Rasta** (paczka „nowy-system” 0.35.0, karta `SYSTEMY/zodiak.md`; na podstawie paczki WLsj24
„ZodiacTemple” 2.1–3.0 z metin2.dev i oficjalnych danych z 2019 r.). Mapa 358 `metin2_12zi_stage` (6×6 na
307200 1408000), prywatne piętra 3580000–3589999 na rdzeniu game1.

## Gdzie co jest

| Część | Miejsce |
|---|---|
| Logika (nowe pliki, wszystko w `#ifdef ENABLE_12ZI`) | `linux-port/overlays/playerbot/src/game/src/playerbot_zodiac_*`: `temple.h/.cpp` (klasy `CZodiac`, `CZodiacManager`, wersja 3.0), `ext.cpp` (definicje, które paczka wstawiała do plików silnika), `battle.cpp` (umiejętności bossów), `char.cpp` (tablica nagród), `questlua.cpp` (funkcje Lua), `regen.inc` (regeny mapy, dołączany do `regen.cpp`) |
| Haki w plikach silnika | `edits.json` (65 zmian w 24 plikach, każda ze znacznikiem `MT2009_PLUS_ZODIAC_V1 (<n>)`); `apply_zodiak.py <game/src>` (Linux/VPS) i `Apply-ZodiakPatch.ps1` (Windows, ostatni krok `tools/port/Apply-MT2009PlusEngine.ps1`) czytają ten sam plik |
| Generator haków | (zmiana `(65)` dopisana ręcznie – generator jej nie zna) `tools/zodiak/gen_zodiak_edits.py <zodiak_haki.py z paczki> <połatany game/src> <edits.json>` – kotwice paczki rozwiązane na naszym silniku po wszystkich innych łatkach |
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
| `(65)` | `battle.cpp` | premia do obrażeń potworów w świątyni o połowę (decyzja właściciela 9.10): poziom ×4 powyżej 85, ×2,5 niżej (paczka: ×8 / ×5); osobna zmiana po `(37)`, więc przerabia też drzewo z dawnym hakiem |
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

Własne przejścia botów – `MT2009_PLUS_ZODIAC_RUNS_V1` (`playerbot_zodiac_runs.h`), na razie na polecenie operatora
(plik `playerbot_zodiac_test` w katalogu rdzenia game1 kanału, czytany co 5 s, potem `.done`):

```
now <znak 1-12|zi..hai|any> [ile]   przejście teraz          loop on|off       znak po znaku, bez końca
size <n>  level <n>  floor <n>      drużyna, min. poziom, piętro końcowe (domyślnie 5, 75, 40)
boost <pct>  prisms <n>  gap <s>    „dobry sprzęt testowy” (afekty 597-599: HP %, silny p. potworom %, obrona), Pryzmaty, przerwa (30, 30, 60)
allportals 1|0                      wszystkie portale codziennie (flaga zodiac_all_portals)
abort | status
```

Drużyna z jednego królestwa (najwyższy poziom liderem, Szaman z grupą umiejętności, jeśli wolny) staje przy portalu znaku na 358,
lider zakłada drużynę, wszyscy dostają mikstury, Pryzmaty i afekty testu, `StartTemple` wpuszcza drużynę. W środku lider bije Metiny,
potem potwory i bossów, na końcu posągi (nigdy działa), reszta walczy przy liderze; piętro zaliczone → `/jumpfloor`. Wyjście: koniec
świątyni, piętro końcowe albo 15 min bez nowego piętra; potem boty wracają na swoje miejsca, afekty i nadmiar Pryzmatów znikają.
Log: `ZODIAC_RUN:` w syslogu (called, gathered, entered, floor, next, pulled, out, closed, status), wiersz na przejście
w `playerbot_zodiac_runs.tsv` (czas, nr, znak, instancja, królestwo, ilu, poziomy, wynik, najwyższe piętro, sekundy,
„piętro:sekundy,…”, śmierci, wskrzeszenia Pryzmatem / bez, lider, nazwy). Samodzielne wyjścia botów „z zegara” (z płaceniem
Animosferami i Pryzmatami) – po teście.

## Żywioły (`MT2009_PLUS_ZODIAC_ELEMENTS_V1`, decyzja właściciela 9.10, jak wiki PL)

Każdy potwór, Metin i boss na piętrze świątyni ma żywioł swojego znaku: Zi – Mrok, Chou – Ziemia, Yin – Ogień, Mao – Wiatr,
Chen – Błyskawica, Si – Lód, Wu – Lód, Wei – Błyskawica, Shen – Ziemia, Yu – Wiatr, Xu – Mrok, Hai – Ogień.
Potwory i Metiny świątyni to te same vnumy w kilku znakach (`group.zodiak.txt`, `SpawnStone`), więc żywioł jest piętra:
`playerbot_elements.cpp` (`ElementsHasFlag`) czyta znak z `CZodiac` mapy potwora – obrażenia, odporność i drop Talizmanu +0
(boss 5%, Metin 2%) liczą się wg niego. Bossowie (2750–2862, po trzy na znak) mają żywioł także w `mob_proto`
(`tools/zywioly` reguła g → `zywioly_moby.json` / `zywioly_moby.sql`), więc klient pokazuje go przy celu; zwykłe potwory
i Metiny świątyni – bez znaku żywiołu w kliencie (ten sam vnum w różnych znakach).

## Ulepszanie broni i zbroi Zodiaku (`MT2009_PLUS_ZODIAC_ITEMS_V1`, wiki PL 9.10)

`refine_proto` 22401–22409 (zbroje: Niebieskie Pudło 1/2/4/…/200) i 22410–22418 (bronie: Czerwone Pudło), koszt 10 tys. … 2,56 mln
Yang jak na wiki; drugi materiał +1…+5: **Ciężkie Pasy (95603)** dla zbroi, **Stabilne Sznury (95601)** dla broni (paczka miała 30611/30612,
których u nas nie ma), +6/+7/+8: Dwutlenek Tytanu 30616, Agat 30617, Kamień Księżycowy 30618 (przedmioty z wiki 0.33.0).
Źródła z wiki, które mamy: Skrzynia Razadora / Nemere (już w grupach 951201/951202), Mag Ochao 6303 – Stabilne Sznury 1%
(`zodiak/mob_drop_item.zodiak.txt`). **Brak u nas (do decyzji właściciela):** Metin Drzewnych Stworzeń, Metin Chłodu, Metin
Purgatorium, Jotun Thrym, Książę Ochao, Goryl Ochao, Niszczyciel/Uzdrowiciel/Wojownik En-Tai, Skażony Mnich/Wódz (mrok), Kappa Łowca,
Ognisty Książę Żaru, Mroźny Książę, Bagjanamu, Wódz Wojenny Schronienia, potwory Inwazji Sung Ma, skrzynie Jotuna/Bagjanamu,
nagrody Dongan/Yilad/Zaklętego Lasu/Strażnicy Nemere/Twierdzy, Smocze Skrzynie, Złoty Łup Królewski, Skrzynia Kamienia
Księżycowego, Skrzynka Tajemnic, Złota Skrzynia Proroka i inne skrzynie eventowe.

## Do sprawdzenia / znane braki

- paczka nie sprawdziła w grze: efektów bossów (pakiet 220), pięter od 2F, Kupca, Pryzmatów, nagród, skoku piętra.
