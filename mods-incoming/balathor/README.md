# Balathor (gildyjne Leże Białego Smoka, dracaryS) – instrukcja wdrożenia na linię Yohara

Ten katalog to **przygotowany wsad**, a nie gotowy moduł. Nic tu nie jest jeszcze podpięte do budowy.
Źródło: `balathor-dracaryS-part1.zip` + `part2.zip` (metin2.forum). Wszystko, co tekstowe, jest już tutaj.
Binarnych plików klienta (~160 MB: modele, efekty, mapa) w repo nie ma, a ich lista jest w `client/ASSETS.txt`.

## Zasady oszczędzania tokenów (czytaj najpierw)

1. **Nie czytaj** `src/game/new/*.cpp` (3,5 tys. linii). Kopiujesz je 1:1 i kompilujesz. Otwierasz tylko
   linie wskazane przez błąd kompilatora.
2. Zmiany w istniejących plikach silnika są w `src/*/hunks/<katalog>__<plik>.hunks`. Każdy hunk to
   `@@ plik:linia`, kilka linii kotwicy (`  `) i linie do wstawienia (`+ `). Linie kotwicy z `# Add after` /
   `# Add before` / `# Add` są instrukcją autora, nie kodem. Do pliku docelowego szukasz kotwicy przez
   `grep -n`, a **nie czytasz całego pliku**.
3. Każdy krok kończy się jednym poleceniem weryfikującym (niżej). Nie powtarzaj analizy z tego README.
4. Zrobione już (nie powtarzaj): kolizje numerów sprawdzone na linii 2.x, `fire_arrow_vnum` zmieniony,
   hunki wycięte, lista assetów policzona.

## Co to jest

Gildia (lider, poz. ≥90, 2–16 członków) rejestruje się u **Strażnika Krainy Lodu (20395)** na **mapie 61
(Góra Sohan)**, czeka `register_wait_time`, a potem członkowie wchodzą (`Join Balathor`) na prywatną kopię mapy
**420 `metin2_map_guild_whitedragon_boss`** (2×2, baza 1152000 921600). Etapy: fale mobów → drzwi lodowe →
Balathor 6896 (jaja, kryształy lodu, wóz Hwacha 20493 strzelający Ognistymi Strzałami) → ukryty Balathor 6897 →
skrzynia 20492 z nagrodą. Konfiguracja bez kompilacji: `server/share/balathor.json`. Klient: okno HP/szału
bossa (`uiguildwhitedragon.py`), efekty ekranu, kamery cutscenek (`locale/common/camera/...`).

## Numery (sprawdzone na linii 2.x, 28.10.2026)

| Co | Numer | Stan |
|---|---|---|
| Mapa | 420 | wolna (zajęte: 158, 209, 301–304, 351–353, 358, 360–366, 419) |
| Pozycja atlasu | 1152000 921600, 2×2 | brak nakładania |
| Moby | 6896–6900 | wolne w `mob_proto` (te same liczby w `playerbot_names.sql` to ID botów – bez znaczenia) |
| NPC/kamienie | 20491–20499, 20507, 20815, 20868, 20869, 8635, 8636 | wolne w `mob_proto` (w `item_proto` to inne przedmioty – bez znaczenia) |
| Ognista Strzała | **30395** (w paczce 30345) | 30345 = „Ezoteryczne Drewno”, drop z moba 777. Już poprawione w `balathor.json` |
| Nagrody | 51501 ×3 (placeholder autora) | 51501 = „Cor Draconis (surowe)”. Ustawić prawdziwe nagrody (pytanie do właściciela) |
| NPC rejestracji | 20395 na mapie 61 | istnieje w `mob_proto` |

Na linii Yohara sprawdź tylko jej dodatkowe numery jednym poleceniem (pusty wynik = OK):
```
cd linux-port/docker/mariadb/playerbot && grep -l -E "^\s*\((6896|6897|6898|6899|6900|20491|20492|20493|20494|20495|20496|20497|20498|20499|20507|20815|20868|20869|8635|8636),.*" $(grep -l mob_proto *.sql); grep -l -E "^\s*\(30395," *.sql; grep -rn -E "^420[[:blank:]]" ../../game
```

## Mapa plików w tym katalogu

```
server/share/balathor.json        -> <share>/locale/<locale>/balathor.json (czytany z LocaleService_GetBasePath())
server/share/map/index            1 linia: "420 metin2_map_guild_whitedragon_boss" (dopisać, nie podmieniać)
server/share/map/metin2_map_guild_whitedragon_boss/   Setting.txt, Town.txt, mapproperty.txt, server_attr
server/share/monster/guild_whitedragon*/              msm/msa dla serwera (zasięgi ataków)
server/share/quest/balathor.lua   quest "__balathor__" (zwykła składnia .quest)
server/share/quest/quest_functions  pełna lista autora; potrzebne są TYLKO linie guild.set_flag/get_flag/
                                    get_near_pids/get_near_count + wszystkie balathor.*
server/mob_proto.txt, mob_names.txt, item_proto.txt, item_names.txt   wiersze w formacie txt (autor)
src/game/new/                     balathor.cpp, balathor.h, balathor_manager.cpp, questlua_balathor.cpp
src/game/hunks/                   26 plików, 700 linii (game + db/ClientManagerEventFlag.cpp)
src/client/hunks/                 25 plików, 760 linii (EterLib, EterPythonLib, GameLib, UserInterface)
client/root/                      game.py, interfacemodule.py, ui.py, npclist.txt = SNIPPETY do wklejenia;
                                  uiguildwhitedragon.py = nowy plik
client/uiscript/guildwhitedragonlairwindow.py   nowy plik
client/data/                      atlasinfo.txt, locale_game.txt, item_desc.txt (snippety), camera/*.txt,
                                  textureset, map_setting.txt / map_mapproperty.txt (klientowe)
client/ASSETS.txt                 lista binariów z zipów (part1/part2, rozmiar, ścieżka)
```

## Kroki

### 0. Wsad

Zipy są u właściciela. Poproś o wrzucenie ich na hosta do `/opt/metin2/cache/balathor/` (albo do sesji) i rozpakuj:
`unzip -oq part1.zip -d p1; unzip -oq part2.zip -d p2`. Binaria są potrzebne dopiero w kroku 6.

### 1. Silnik serwera (game + db)

1. `cp src/game/new/* <game/src>/`. Dopisz `balathor.cpp balathor_manager.cpp questlua_balathor.cpp` do listy
   źródeł game (Makefile/CMake, tam gdzie są inne `questlua_*.cpp`).
2. Flaga: `#define __BALATHOR__` dopisz tam, gdzie linia Yohara trzyma swoje definy (`common/service.h` albo
   CMake `add_definitions`), **oraz dla db** (hunk `db__ClientManagerEventFlag.cpp`).
3. `json.hpp` (nlohmann, single header) musi być w include path game:
   `find <src> -name json.hpp`. Jeśli brak, dodaj wersję 3.11.x do `game/src` (lub `vendor`).
4. Hunki stosuj plik po pliku. Dla każdego pliku:
   `grep -n '<pierwsza linia kotwicy>' <plik docelowy>` → wstaw linie `+` w odpowiednim miejscu → następny.
   Ryzykowne (silnik MT2009 różni się od bazy autora): `char_battle.cpp` (84 linie), `char.cpp` (93),
   `char_state.cpp`, `questlua_guild.cpp` (nowe `guild.set_flag/get_flag` – sprawdź, czy linia Yohara nie
   ma już takich nazw: `grep -n '"get_flag"\|"set_flag"' questlua_guild.cpp`), `utils.cpp/h`
   (helpery – nie dubluj istniejących funkcji).
5. Konflikty z modułami playerbot: boty nie mogą dostać się na mapę 420. Sprawdź, czy linia Yohara ma
   listę map zabronionych dla botów/dungeonów (`grep -rn '419' linux-port/overlays/playerbot/src/game/src/*.h | head`)
   i dopisz tam 420.
6. Weryfikacja: build obrazu game kończy się sukcesem, a w syslog przy starcie nie ma `balathor.json` errorów.

### 2. Dane serwera

1. Mapa: skopiuj `server/share/map/metin2_map_guild_whitedragon_boss` do share obrazu tak, jak robią to inne
   moduły (`linux-port/docker/game/maps302/map`, kroki w `Dockerfile` przy `419 metin2_map_treasure_hunt`).
   Dopisz `420 metin2_map_guild_whitedragon_boss` do `map/index` idempotentnie (`grep -q ... || printf`).
   Mapa ma być na tym samym rdzeniu co inne nowe mapy (game3, `MT2009_PLUS_237_NEWCORE_V1`), a mapa 61 musi
   mieć możliwość warpu na ten rdzeń.
2. `monster/guild_whitedragon*` → `<share>/locale/<locale>/monster/` (obok istniejących).
3. `balathor.json` → `<share>/locale/<locale>/`. Wartości pozycji to współrzędne lokalne (×100 robi kod).
4. `mob_proto`: 22 wiersze txt → INSERT do nowego `linux-port/docker/mariadb/playerbot/balathor.sql`
   w kolumnach jak w `mob_proto.mt2009plus.sql`. Nazwy PL (propozycja): 6896/6897 „Balathor”,
   6898 „Widmowy Wojownik”, 6899 „Widmowy Łucznik”, 6900 „Widmo Ognia”, 20491 „Zakazana Tablica”,
   20492 „Skrzynia Balathora”, 20493 „Hwacha”, 20494 „Lodowa Bariera”, 20495/20496 „Jajo Balathora”,
   20497 „Pęknięte Jajo Balathora”, 20498 „Kryształ Lodu”, 20815 „Duch Strażnika”. Dopisz plik do pętli w
   `apply.sh` jak inne `*.sql` modułów.
5. `item_proto`: Ognista Strzała **30395** (kolumny jak `item_proto.mt2009plus.sql`, typ ITEM_QUEST, stack,
   anti-drop/sell/give/myshop). Nazwa PL „Ognista Strzała”.
6. Quest: `balathor.lua` → `linux-port/docker/game/quest/balathor.quest`. Przetłumacz `say(...)` i nazwy
   opcji czatu na PL (to tylko stringi). Dodaj do `quest_list` i do `quest_functions` tylko brakujące funkcje.
7. Nagrody w `balathor.json` (`fail_rewards` / `success_rewards`): placeholder 51501 – zapytaj właściciela.
8. Pliki serwera dopisz do `launcher/server-update-files.mod.txt` (inaczej nie trafią do paczki aktualizacji).
9. Weryfikacja: `/goto` lub warp GM na 420, rejestracja gildii u 20395 na 61, przejście etapów.

### 3. Klient (exe)

Źródła exe: `client-patches/exe/`. Hunki z `src/client/hunks` stosuj jak w kroku 1.4. Flaga
`#define __BALATHOR__` w `Locale_inc.h` (hunk `UserInterface__Locale_inc.h` nie istnieje – dopisz ręcznie)
i eksport `app.__BALATHOR__ = 1` (hunk `UserInterface__PythonApplicationModule.cpp`).
Pliki silnika klienta, których jeszcze nie ma w `client-patches/exe`, trzeba skopiować z bazowych źródeł
klienta tak, jak robią to istniejące patche (sprawdź README `client-patches/exe`).

### 4. Klient (root/uiscript/locale)

- `uiguildwhitedragon.py` → root (nowy), `guildwhitedragonlairwindow.py` → uiscript (nowy).
- `game.py`, `interfacemodule.py`, `ui.py`, `npclist.txt` → wklej snippety w miejsca opisane w plikach.
  `npclist.txt` dopisz 20 linii.
- `locale_game.txt`, `item_desc.txt` (30345 → **30395**!), `atlasinfo.txt` → dopisz i przetłumacz na PL.
- `locale/common/camera/**` → do paczki locale.

### 5. Mapa klienta i binaria

Mapę z `map_patch/metin2_map_guild_whitedragon_boss` buduj tak jak `tools/zaklety237` (pełny folder mapy),
razem z `property/guild_whitedragon`, `zone/`, `terrainmaps/`, `textureset/`. Modele: `monster2/` i `npc2/`.
**Kopiuj tylko foldery używane przez `client/root/npclist.txt`** (guild_whitedragon*, metinstone_*whitedragon*,
whitedragon_guard, whitedragon_misa) + efekty. Foldery `whitedragon_cave_*` i `whitedragonvalley_*` należą
do innego dungeonu i Balathor ich nie używa – pomiń, jeśli efekty do nich nie odwołują się:
`grep -rl -i 'whitedragon_cave\|whitedragonvalley' p*/balathor-dracaryS/Binary/effect p*/balathor-dracaryS/Binary/monster2/ymir\ work/guild_* | head`.
Ikony: `icon/item/30345.tga` → zapisz jako `30395.tga`.

### 6. Wydanie

Na gałęzi roboczej, nie na main. Wersje i changelog robi wydający agent jak zwykle.

## Znane ryzyka

- Kod autora pisany pod inną bazę (turecka/marty). Spodziewaj się różnic nazw w `CHARACTER`
  (np. `GetGuild`, `IsGuildMaster`), w `CGuild` (lista członków) i w pakietach `ChatPacket`.
- `char_battle.cpp`: obrażenia od Hwachy/szał bossa. Sprawdź, czy nie koliduje z `MT2009_PLUS_*` w tym samym miejscu.
- Klient bez nowych hunków exe pokaże mapę i moby, ale bez okna bossa, efektów i cutscenek. Serwer musi
  mieć `__BALATHOR__`, inaczej quest nie ma funkcji `balathor.*`.
