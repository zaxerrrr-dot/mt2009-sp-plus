# Obrona Statku (Hydra)

Loch „Obrona Statku” (oficjalny „defense wave”) przeniesiony z Owsapa v6.2.6
(`defense_wave.cpp`, `questlua_defense_wave.cpp`, Autor: Owsap) na nasz silnik r40250.
Plan: `cache/yohara/plan-hydra.md` (kroki 2–4: dane serwera, SQL, łatka C++).
Znacznik wszystkich zmian: `MT2009_PLUS_SHIP_DEFENSE_V1 (…)`.

Zmiany silnika opisuje `edits.json`; nakładane raz, przy przygotowaniu wydania
(`tools/port/Apply-MT2009PlusEngine.ps1`, jako ostatnia łatka – jej kotwice to linie,
które zostawiają lub dodają łatki Leża Smoka, Goblina i Zodiaku). `Apply-ShipDefensePatch.ps1`
i linuksowy bliźniak `apply_shipdefense.py` robią to samo. Zmiana już nałożona (jest jej
znacznik) jest pomijana; zmiana, której kodu nie ma dokładnie raz, przerywa całość, zanim
cokolwiek zostanie zapisane. Pliki zachowują swoje końce linii.

Cała logika jest w nakładce (`linux-port/overlays/playerbot/src/game/src/`):
`playerbot_ship_defense.h`, `playerbot_ship_defense.cpp` (statek, fale, haki),
`playerbot_ship_defense_questlua.cpp` (moduł `dw` dla questa). Nazwy `playerbot_*`, żeby
nakładka, kopia budowania i lista plików aktualizacji (`playerbot_*`) niosły je same.

## Jak to działa

- **Mapa 367** `metin2_map_defensewave` (u Owsapa 358 – u nas Świątynia Zodiaku), prywatne
  kopie 3670000–3679999, rdzeń Yohary game3 (`bin/m2-render-config`, MT2009_PLUS_YOHARA_CORE_V1; wcześniej game1). Dane: `linux-port/docker/game/shipdefense/`
  (krok Dockerfile „share: Obrona Statku”).
- **Bez dziedziczenia po CDungeon** (nasz nie ma metod wirtualnych, `Create` bez typu): statek to osobny
  obiekt `CShipDefense` na prywatny indeks mapy, przypinany do instancji lochu, gdy wchodzi na nią
  pierwsza osoba (`input_login.cpp`; bot drużyny – przy pierwszym kroku, `char.cpp`), usuwany razem
  z lochem (`CDungeonManager::Destroy`). Quest tworzy instancję jak inne nasze lochy (`d.new_jump_pids`).
- **Jedno zdarzenie co 1 s** na statek zamiast ~15 zdarzeń Owsapa: odliczania, fale, jaja, Potomstwo
  Hydry, lasery, przywołania kapp, osłabienie w fali 4, limit czasu, pasek HP masztu.
- **Pasek HP masztu** bez nowego pakietu i bez zmiany exe: komenda czatu
  `ShipMastHP <hp> <max>` do osób na statku (najwyżej raz na sekundę, tylko przy zmianie),
  `ShipMastHP 0 0` = ukryj. Klient: `client-patches/client-2.0.30/root/uishipdefense.py` (pasek „Maszt statku”
  u góry ekranu, pod oknem celu), wpis w `game.py`; okno śmierci na statku ma tylko „Odrodź się tutaj”
  (`uirestart.py`). Paczki mapy i modeli: `client-patches/client-2.0.30/tools/shipdefense/`.
- **Laser**: istniejący pakiet efektu (`defense_mini_laser.mse`) zamiast nowego `SE_*`; bez nowego afektu.

## Poprawione błędy Owsapa

| Owsap | U nas |
|---|---|
| jajo i głowa w intro dzielą jeden slot `m_pPurgeEvent` (drugie kasuje pierwsze) | osobne liczniki czasu w ticku |
| fala 4: osłabienie potworów nigdy nie startuje (`m_pDebuffEvent != NULL`) | startuje przy HP Hydry ≤ `debuff_hp_pct` (50%) |
| komunikat „masz 0 minut” na portal | prawdziwy czas (`end_time` / 60) |
| brak limitu czasu po starcie | `time_limit` (30 min) – potem porażka |
| laser nic nie robi | nadal domyślnie nic (`laser_mast_pct` = 0); > 0: nieprzechwycony laser zabiera masztowi tyle % HP |
| kappy z przywołań bez limitu | `summon_cap` (40) |
| 4. linia regenu na zablokowanej komórce (378,430) | przesunięta na 379,430 |

Intro fali 1 zostaje jak u Owsapa (pełny model Hydry 3961 przez 4 s): plan wskazywał „błąd 3961
zamiast 3963”, ale głowa 3963 ma tylko ruch „wait”, więc nie zagra intra – nie zmieniałem.

## Ustawienia (flagi zdarzeń `shipdef_<nazwa>`, 0 = domyślne, wartość ujemna = 0)

Domyślne wejścia to decyzje właściciela z 13.10.2026 (`cache/yohara/decyzje.md`): poziom 90, drużyna albo
solo, 5 000 000 Yang, bez przerwy, 10 wejść dziennie. Wszystko da się zmienić flagą bez kompilacji
(wartość ujemna = 0, np. `shipdef_fee -1` = za darmo); quest czyta je przez `dw.cfg("<nazwa>")`.

| Nazwa | Domyślnie | Co |
|---|---|---|
| `min_level` | 90 | poziom wejścia (quest) |
| `party_only` | 0 | 0: drużyna albo solo, 1: tylko drużyna (quest) |
| `fee` | 5000000 | opłata w yangach (quest) |
| `cooldown` | 0 | odpoczynek po wejściu, s – tylko boty (quest; ludzie nigdy nie czekają) |
| `daily_limit` | 10 | wejść dziennie na postać (quest) |
| `max_instances` | 8 | statków naraz na rdzeń – nieużywane: Rybak stoi na game2, statek na game3 (Yohara), `dw.count()` liczy tylko swój rdzeń |
| `idle_destroy` | 600 | nieuruszony statek zamyka się po, s |
| `time_limit` | 1800 | limit po starcie, s |
| `wave1_countdown` / `wave1_time` | 60 / 120 | odliczanie i czas fali 1, s |
| `wave_countdown` / `between_waves` | 10 / 6 | odliczanie fal 2–4 i przerwa po Hydrze, s |
| `end_time` / `lose_exit` | 300 / 10 | na portal po zwycięstwie / do wyjścia po porażce, s |
| `egg_first` / `egg_interval` / `egg_life` | 30 / 40 / 8 | Jajo Hydry, s |
| `spawn_respawn` | 30 | powrót zabitego Potomstwa Hydry, s |
| `summon_interval` / `summon_cap` | 30 / 40 | przywołania kapp |
| `laser_interval` / `laser_mast_pct` | 15 / 0 | laser |
| `repair_pct` / `repair_stun` | 1 / 5 | deska na maszt: % HP / ogłuszenie, s |
| `debuff_hp_pct` / `debuff_interval` | 50 / 10 | fala 4 |
| `chest_uses` | 3 | ile razy otwiera się Skrzynia Hydry (54705) |

## Zmiany w plikach silnika (`edits.json`)

| Znacznik | Plik | Co robi |
|---|---|---|
| `(destroy)` | `dungeon.cpp` | `CDungeonManager::Destroy` usuwa statek swojej instancji. |
| `(kill all)`, `(purge)` | `dungeon.cpp` | `d.kill_all` / `d.purge` nie ruszają masztu, steru, ścian, głów i portalu, póki statek trwa. |
| `(attack)` | `char_battle.cpp` | Głowy Hydry i intro nie atakują. |
| `(damage)` | `char_battle.cpp` | Głowy, intro i ster nie przyjmują obrażeń; deska (20437) traci 1 HP za cios (flaga COUNT Owsapa, której nasze `mob_proto` nie ma). |
| `(dead)` | `char_battle.cpp` | Śmierć masztu, Hydry, jaja, Potomstwa – zapisana, obsłużona w najbliższym ticku. |
| `(aggro)` | `char_battle.cpp` | Hydra i Potomstwo trzymają się masztu, kto by ich nie bił. |
| `(attack)` | `pvp.cpp` | Potwory statku mogą bić maszt (NPC); gracze nie. |
| `(range)` | `char.cpp` | Zasięg ataku na statku: Hydra +4500 (Owsap: +2000 i HitRange 2500, kolumna, której nasze `mob_proto` nie ma; stoi 2700 od masztu, poza pokładem), reszta +300 (Owsap). |
| `(move)` | `char.cpp` | Osoba na polu lasera przechwytuje go; bot drużyny przypina statek. |
| `(enter)` | `input_login.cpp` | Wejście na instancję: przypięcie statku, pasek HP masztu. |
| `(regen)` | `regen.cpp` | Potwór z regenu fali idzie na maszt. |
| `(ai)` | `sectree.cpp` | Potwory statku nie zasypiają, gdy nikt nie stoi obok. |
| `(idle)` | `char_state.cpp` | Potwór bez celu wraca do masztu (pomysł Amerii `FindVictimHydra`). |
| `(lua)` | `questlua.cpp` | Rejestracja modułu `dw`. |
| `(declare)`, `(table)` | `cmd.cpp` | Polecenie GM `/dw` (create, start, info, wave 1-4, end). |
| `(hydra chest)` | `char_item.cpp` | Skrzynia Hydry (54705) po udanym otwarciu zostaje, dopóki nie otwarto jej `chest_uses` razy (gniazdo 0 liczy otwarcia; `ShipDefense_ChestKeep`). |

## Moduł `dw` (dla questa, krok 5)

`dw.cfg(nazwa)`, `dw.map_index()`, `dw.count()`, `dw.find(indeks)`, `dw.start()`, `dw.is_started()`,
`dw.wave()`, `dw.state()` (0 czeka, 1 odliczanie, 2 fala, 3 przerwa, 4 wygrana, 5 porażka, 6 koniec),
`dw.mast_hp_pct()`, `dw.set_alliance_hp_pct(n)` (deska: +n% HP masztu, 0 = `repair_pct`), `dw.close()`.
Wygrana ustawia flagę lochu `shipdef_won` = 1. Nazwy są dopisane do `quest_functions` w Dockerfile.

Quest: `linux-port/docker/game/quest/obrona_statku.quest` (krok 5, poniżej).

## Quest `obrona_statku` (krok 5)

Wzorzec Leża Smoka (`blue_dragon_lair.quest`): Rybak 9009 na Przylądku Smoczego Ognia (301, rdzeń game2,
838,1187) → „Obrona Statku (Hydra)” → `d.new_jump_pids(367, …)` dla gracza albo przywódcy z ludźmi drużyny
stojącymi obok (30 pól); boty drużyny dołączały same (`playerbot_party_dungeon.h`: 367 jest mapą lochu
drużyny, wyjście do Rybaka) - od MT2009_PLUS_YOHARA_CORE_V1 statek jest na rdzeniu Yohary, a bot nie przechodzi
między rdzeniami, więc boty już nie wchodzą. Sprawdza poziom, limit dzienny, Yang i wierzchowca każdego człowieka; płaci się
przy pierwszym wejściu do nowej instancji (GM i boty za darmo); „Wróć do lochu” po rozłączeniu
(`mt2009_keep_until` = `idle_destroy` + `time_limit` + 120 s). Ster 20436: „Rozpocznij obronę masztu”
(`dw.start()`, tylko przywódca lub solo), „Zejdź ze statku”. Potomstwo Hydry (3957-3959) zostawia deskę
20437 w miejscu śmierci, zbita deska daje Deskę Naprawczą 31107, przeciągnięta na maszt 20434 –
`dw.set_alliance_hp_pct(0)`. Hydra 3962: panel lochów (`d.update_ranking("hydra", czas od startu)`, wpis
`hydra` w `arezzo/dungeon_info.txt`) i trwała flaga przejścia ludzi drużyny na statku:
`obrona_statku.completed` (liczba), `completed_at` (czas), `completed_at_120` = 1 przy poziomie 120+
(pod przyszły poziom Mistrza); kto nie był w drużynie zabójcy, dostaje ją przy portalu 3949 (klik → po
zwycięstwie wybór: Port Nowego Kontynentu 368 albo ląd 301). Boty flagi nie dostają (decyzja: na razie nie).

Pułapki kompilatora `qc` (sprawdzone): napis kończący się polską literą (`"…obronę"`) wywala `qc` bez
komunikatu, a `dw.state()` jest błędem składni (`state` to słowo kluczowe `qc`) – w queście `dw["state"]()`.

## Nagrody (krok 6)

Decyzja właściciela z 13.10.2026. Pliki w `linux-port/docker/game/shipdefense/`, dopisywane przez Dockerfile
(krok „share: Obrona Statku”, który przerywa budowę, gdy 3965, 54705 albo 72058 ma już grupę):
- `mob_drop_item.shipdefense.txt` – Skarb Hydry (3965), jedna grupa `limit` (zwykły procent na zabicie, bez
  mnożników poziomu i dropu): Skrzynia Hydry 3 × 100% + 3 × 50% (zawsze 3–6, średnio 4,5) i reszta listy wiki
  z naszymi procentami (średnio ok. 3,5 przedmiotu więcej) oraz Pakiet Kamieni Duszy (72058) 1 × 100% +
  6 × 50% (oficjalne „do 7”: zawsze 1–7, średnio 4);
- `special_item_group.shipdefense.txt` – Skrzynia Hydry (54705): jeden przedmiot na otwarcie, wagi na 1000,
  Magiczny Kamień 40 (dokładnie 4%), Pakiet Kamieni Duszy ×3 60 (zabrane po 10 z Zwoju Błogosławieństwa,
  Zaczarowania, Wzmocnienia, Przepustki i obu Klejnotów). Skrzynia otwiera się 3 razy (`chest_uses`),
  podpowiedź klienta (`client-patches/client-2.0.30/root/uitooltip.py`) pokazuje pozostałe otwarcia;
- ten sam plik – Pakiet Kamieni Duszy (72058, oficjalny vnum, ikona `icon/item/27999.tga`, skrzynka 23,
  stos 200; `shipdefense.sql`): jeden kamień duszy na otwarcie, losowany jak kamień z Metina
  (`CHARACTER::DetermineDropMetinStone`): rodzaj – jeden z 14 (28030–28043) po równo, stopień – średnia
  wierszy `aStoneDrop` (Metiny 8005–8014): +0 16,9%, +1 27,3%, +2 34,6%, +3 19,0%, +4 2,2%
  (70 wierszy, suma wag 14000).
Pierścień Hydry (70303) wrócił do nagród (właściciel, 13.10.2026 wieczorem; `MT2009_PLUS_YOHARA_PORT_V1`):
Skarb Hydry 1 × 30% + 1 × 10% (0–2 jak na wiki: 63% / 34% / 3%), Skrzynia Hydry waga 30 (3%) – po 10 z Zwoju
Błogosławieństwa (80→70), Notatki Przywódcy i Czerwonego Konaru (60→50); Magiczny Kamień nadal dokładnie 40 (4%),
suma 1000. Pierścień: 3 teleporty do Portu Nowego Kontynentu (368), potem znika (quest `port_yohary`).
Spirala Czasu (72347) celowo NIE jest nagrodą.
Brakujące u nas przedmioty i zamienniki są wypisane w nagłówkach obu plików. Klient: Deska Naprawcza,
Skrzynia Hydry i Pakiet Kamieni Duszy w `item_proto`, `item_list.txt` i `itemdesc.txt` oraz pusty opis
Magicznego Kamienia – `client-patches/client-2.0.30/tools/yohara/patch_yohara_client.py`.

## Magiczny Kamień

Decyzja właściciela z 13.10.2026: Magiczny Kamień (**25042**, `USE_TUNING`, `value0` = 1 =
`NO_REDUCTION_WHEN_FAIL_SCROLL`) działa tak, jak silnik ma to od zawsze: szansa kowala, materiały i Yang
jak u kowala, a przy porażce przedmiot nie znika i nie traci poziomu. Łatka go nie zmienia, opis
przedmiotu zostaje (linie „Typ przedmiotu / Max. poziom” pod nim dopisywał błędnie uitooltip.py –
MT2009_PLUS_REFINE_TOOLTIP_V1). Wypada ze Skrzyni Hydry (4%).

## Test GM (bez questa)

`/dw create` (tylko na rdzeniu z mapą 367 – game3, Yohara) → `/dw start` → `/dw info`, `/dw wave 4`, `/dw end`.

## Port Nowego Kontynentu (368) – `MT2009_PLUS_YOHARA_PORT_V1`

Decyzja właściciela z 13.10.2026 wieczorem. `metin2_map_defensewave_port` (Owsap 359) jako mapa 368, 3x3 na
128000 563200, rdzeń game2 obok 301 (`bin/m2-render-config`). Dane: `linux-port/docker/game/yohara_port/`
(krok Dockerfile „share: Port Nowego Kontynentu”): `server_attr` zrobiony z `attr.atr` klienta GF 26.1.11
(`tools/gf28/srvattr.py`, 100% komórek – plik Owsapa blokuje 2244 komórki więcej, cały plac z NPC, i całą mapę
oznacza jako wodę), Setting/Town Owsapa, `npc.txt` tylko z Posągiem Wojownika (20433, 241 574). Bez potworów
i Metinów; kowale zestawów (20475–20479), sklep i pozostałe funkcje posągu – później.

Wejście od poziomu 90: portal 3949 po wygranej, Rybak 9009 („Port Nowego Kontynentu”, gdy `obrona_statku.completed`
> 0) albo Pierścień Hydry. Posąg: „Zostań Czempionem” / „Poziom Czempiona” (`czempion`), „Ranking lochów”
(`cmdchat DungeonInfo show` – otwiera panel wypraw, `client-patches/client-2.0.30/root/dungeoninfo.py`) i „Wróć na
Przylądek Smoczego Ognia” (do Rybaka) – quest `port_yohary`, który pilnuje też poziomu 90 przy wejściu na mapę.
Klient: paczki mapy `client-patches/client-2.0.30/tools/port368/`.

## Exe 3.0 (`MT2009_PLUS_SHIP_DEFENSE_V2`, 13.10.2026)

Opcjonalne poprawki exe z planu weszły do exe Yohary (`client-patches/exe/README.md`): `IS_HUGE_RACE` dla Hydry 3960–3962
(nie jest odpychana, efekt trafienia w miejscu ciosu, zasięg umiejętności −200) i – na `metin2_defensewave` – umiejętność
w olbrzymią rasę (albo z `IGNORE_BLOCK`) nie sprawdza, czy cel stoi na blokadzie (Hydra stoi w morzu; Owsap `IsIgnoreBlock`).
Serwer bez zmian.
