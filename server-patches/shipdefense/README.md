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
  kopie 3670000–3679999, rdzeń game1 (`bin/m2-render-config`). Dane: `linux-port/docker/game/shipdefense/`
  (krok Dockerfile „share: Obrona Statku”).
- **Bez dziedziczenia po CDungeon** (nasz nie ma metod wirtualnych, `Create` bez typu): statek to osobny
  obiekt `CShipDefense` na prywatny indeks mapy, przypinany do instancji lochu, gdy wchodzi na nią
  pierwsza osoba (`input_login.cpp`; bot drużyny – przy pierwszym kroku, `char.cpp`), usuwany razem
  z lochem (`CDungeonManager::Destroy`). Quest tworzy instancję jak inne nasze lochy (`d.new_jump_pids`).
- **Jedno zdarzenie co 1 s** na statek zamiast ~15 zdarzeń Owsapa: odliczania, fale, jaja, Potomstwo
  Hydry, lasery, przywołania kapp, osłabienie w fali 4, limit czasu, pasek HP masztu.
- **Pasek HP masztu** bez nowego pakietu i bez zmiany exe: komenda czatu
  `ShipMastHP <hp> <max>` do osób na statku (najwyżej raz na sekundę, tylko przy zmianie),
  `ShipMastHP 0 0` = ukryj. Obsługa w pythonie klienta – krok 8.
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

Decyzje właściciela jeszcze nie zapadły – wszystko da się zmienić flagą bez kompilacji; quest czyta
je przez `dw.cfg("<nazwa>")`.

| Nazwa | Domyślnie | Co |
|---|---|---|
| `min_level` | 90 | poziom wejścia (quest) |
| `party_only` | 0 | 0: drużyna albo solo, 1: tylko drużyna (quest) |
| `fee` | 0 | opłata w yangach (quest) |
| `cooldown` | 1800 | odnowienie po starcie, s (quest) |
| `daily_limit` | 0 | wejść dziennie, 0 = bez limitu (quest) |
| `max_instances` | 8 | statków naraz na rdzeń (quest: `dw.count()`) |
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

## Moduł `dw` (dla questa, krok 5)

`dw.cfg(nazwa)`, `dw.map_index()`, `dw.count()`, `dw.find(indeks)`, `dw.start()`, `dw.is_started()`,
`dw.wave()`, `dw.state()` (0 czeka, 1 odliczanie, 2 fala, 3 przerwa, 4 wygrana, 5 porażka, 6 koniec),
`dw.mast_hp_pct()`, `dw.set_alliance_hp_pct(n)` (deska: +n% HP masztu, 0 = `repair_pct`), `dw.close()`.
Wygrana ustawia flagę lochu `shipdef_won` = 1. Nazwy są dopisane do `quest_functions` w Dockerfile.

Questa jeszcze nie ma (krok 5): rybak/wejście, ster („Rozpocznij obronę”), deska z Potomstwa
(`when 3957/3958/3959.kill` → `20437`), drop deski 31107, `20434.take`, portal 3949, nagrody.

## Test GM (bez questa)

`/dw create` (tylko na rdzeniu z mapą 367 – game1) → `/dw start` → `/dw info`, `/dw wave 4`, `/dw end`.
