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

## Taktyka (walka jak na wojnie gildii)

`MT2009_PLUS_PVPFAN_WARSTYLE_V1` (właściciel, 10.11.2026, po obejrzeniu taktyki oddziałów: „laguje i skacze – trzy
kroki, stop, trzy kroki, skill, stop; ma walczyć jak normalne PvP botów albo wojna gildii: skille losowo, losowe
postacie, a nie przypisane, i naturalnie się rozchodzić”). Domyślna walka **wszystkich** kategorii. Bez zmian w
silniku – wszystko w `playerbot_pvpfan.h` (sekcja „the fight”).

**Przyczyna „zacinania”.** Boty wojny PVP Fan miały swój ruch w ogólnym przebiegu botów (`CPlayerBotManager::Update`),
który działa w budżecie czasu i przy dużej liczbie botów dochodzi do każdego bota co kilka przebiegów. Na serwerze
testowym (~1200 botów) 225 z 256 przebiegów na minutę kończyło budżet, pełny obieg trwał ~2 s, a boty PVP Fan były
wyłączone z „lekkiego” ticku pomiędzy (który botom na wojnie gildii prowadzi pościg i zwykłe ciosy). Każdy bot wojny
decydował, ruszał się, bił albo rzucał czar raz na ~2 s: krok do miejsca, gdzie wróg był, stop, czar, stop. Taktyka
oddziałów (odskoki co 0,4 s, punkty zborne przesuwane co 1 s, zatrzymania na miejscu w szyku, czekanie magów w
miejscu na czar, odwroty i przegrupowania – w wojnie z 10.11: 79 odskoków, 16 odwrotów i 10 przegrupowań w 25 s)
dokładała do tego ciągłe zmiany kierunku. Teraz boty wojny mają własny przebieg co tick menedżera (~0,24 s), poza
budżetem ogólnym, a ogólny przebieg je tylko pomija.

**Jak to wygląda teraz:**

- **Start bez zmian.** Drużyny stoją w szeregach po 10 przodem do środka, czekają na „gotowi”; szamani buffują swoich.
- **Losowy cel.** Każdy bot losuje przeciwnika spośród wrogów w promieniu ~18 m: bliżsi znacznie częściej (waga
  1 / (1 + d / 4,5 m)²), a ten, na którego idzie już kilku, trochę rzadziej – lekkie rozłożenie, nikt nikogo nie
  przydziela. Cel trzyma, aż padnie, ucieknie (dalej niż ~26 m albo poza arenę) albo minie losowe 8–15 s, wtedy losuje
  następnego. Nikogo w pobliżu: najbliższy wróg na arenie (szukany najwyżej co 2 s), a bez wrogów – w stronę środka.
- **Pościg i ciosy jak na wojnie gildii.** Ciągły pościg (nowy cel ruchu dopiero, gdy wróg się przesunął, bez
  zatrzymywania po drodze), buffy, wojownik doskakuje (Szarża / Uderzenie Miecza), Sura Magia i Szaman Leczenie
  rzucają czary z ~6 m i między czarami biją wręcz, Szaman Smok wchodzi w środek jak wojownik (jak na wojnie gildii),
  Ninja Skrytobójca podchodzi w ukryciu, łucznik strzela z ~8 m i odskakuje od wroga bliżej niż 4 m (najwyżej 3 razy
  na 8 s, jak na wojnie gildii). Bez stawania co chwilę i bez uciekania „w kółko”.
- **Losowe umiejętności.** Gotowe (po czasie odnowienia) umiejętności ataku są próbowane w losowej kolejności, nie w
  stałej rotacji.
- **Leczenie.** Szaman co 1,5–2,5 s patrzy na swoich w promieniu ~10 m: Szaman Leczenie leczy najsłabszego poniżej 60%,
  oba szamany nakładają brakujące buffy; poza tym walczą jak reszta.
- **Rozchodzenie się** wynika z losowych celów i granicy areny; bot za promieniem areny wraca jak dotąd. Wynik
  (ostatnia stojąca drużyna albo limit czasu) bez zmian.

**Wydajność.** Bez przeszukiwania całej wojny co tick: siatka przestrzenna (komórki ≥ 500) odbudowywana co 0,5 s
(także w czekaniu), losowanie celu z kilku komórek wokół bota tylko przy zmianie celu (bez celu co ~0,6 s), cała
arena najwyżej co 2 s i tylko dla bota bez nikogo w pobliżu, szamani co 1,5–2,5 s z komórek wokół siebie.

**Logi** (`PVPFAN:`): przy starcie `fight ... style=guild-war|squads-experimental`; co minutę `census fight` –
wylosowane cele (`picks`), porzucone cele (`ends_fell` / `ends_fled` / `ends_time`), na ilu wrogów rozkłada się
wojna (`targets`, `attacking`, `busiest`), odskoki łuczników, leczenia oraz przerwy między tickami jednego bota
(`tick_gap_avg_ms`, `tick_gap_max_ms`, `tick_gaps_over_600` – miara zacinania; powinno być ~240 ms i prawie zero
ponad 600); przy wyniku `fight summary`.

**Jak przetestować (serwer testowy):** kategoria `1` (50 Wojownik Ciało vs 50 Szaman Smok, mapa 21), panel Start,
Gotowi. Oczekiwane: płynny pościg bez „krok–stop”, `tick_gap_avg_ms` ~240, `targets` wyraźnie > 1 (cele rozłożone),
`ends_time` > 0 (zmiany celu po 8–15 s), walka wyraźnie dłuższa niż 25 s z 10.11. Potem kategoria mieszana (np. 3
drużyny: Wojownik Ciało, Ninja Łucznik, Sura Magia, Ninja Skrytobójca, Szaman Leczenie) – `heals` > 0, łucznicy
odskakują (`archer_steps`).

### Oddziały – eksperymentalne

`MT2009_PLUS_PVPFAN_TACTICS_V1` (alpha 2 z 8.11.2026) zostaje tylko jako opcja eksperymentalna: kolumna `tactics` = 2
(panel: „Oddziały – eksperymentalne”). Drużyna dzieli się na oddziały po `squad_size` botów, stoi w szyku oddziałów,
naciera szykiem na różne oddziały wroga, skrajne oskrzydlają; dystansowcy trzymają dystans i odskakują od walczących
wręcz bliżej niż `kite_distance`; ranni poniżej `retreat_hp` cofają się do uzdrowiciela i piją mikstury; oddział
poobijany, rozproszony albo w przewadze wroga się przegrupowuje. Logi `census tactics` i `tactics summary` jak dotąd.
Też korzysta z własnego przebiegu botów wojny, ale jego odskoki, punkty zborne i odwroty nadal zmieniają kierunek
ruchu częściej niż wojna gildii.

**Ustawienia** (panel → kategoria → Ustawienia; kolumny `pvpfan_category`, migracja w `pvpfan.sql` przy każdym starcie):
`tactics` (0 albo 1 = walka jak na wojnie gildii, domyślnie; 2 = oddziały eksperymentalne), a tylko przy `tactics` = 2:
`squad_size` (5; 2–12), `kite_distance` (400; 150–900, 0 = bez odskoków), `retreat_hp` (35; 5–80, 0 = bez odwrotów).
Domyślna wartość kolumny `tactics` to teraz 0 (`pvpfan.sql`); istniejące wiersze z 1 walczą jak na wojnie gildii bez
żadnej zmiany w bazie. Flaga `m2_pvpfan_tactics_off` = 1 (w grze albo wiersz `player.quest`) wyłącza oddziały we
wszystkich kategoriach, także w trwającej wojnie.

