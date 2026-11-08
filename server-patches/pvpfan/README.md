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

## Taktyka (alpha 2)

`MT2009_PLUS_PVPFAN_TACTICS_V1` (właściciel, 8.11.2026: „ma wyglądać jak prawdziwa wojna, a nie dwie kule, które na
siebie wpadają”). Bez zmian w silniku – wszystko w `playerbot_pvpfan.h` (sekcja „tactics”). Boty nie są słabsze ani
bierniejsze: walka trwa dłużej dzięki ruchowi, odstępom, uciekaniu, odwrotom i rozkładaniu celów.

**Jak to wygląda:**

- **Oddziały.** Każda drużyna dzieli się na oddziały po `squad_size` botów (domyślnie 5), każdy z tą samą mieszanką
  klas. Na starcie oddziały stoją obok siebie w szeregu (przy wąskim froncie w dwóch liniach), w każdym oddziale z przodu
  walczący wręcz, za nimi dystansowcy, na końcu uzdrowiciele.
- **Natarcie szykiem.** Po „WALKA!” oddziały idą w szyku (punkt zborny prowadzi oddział) na swój cel – najbliższy oddział
  wroga, którego nie wziął już inny oddział tej drużyny, więc starcia wybuchają w kilku miejscach naraz. Skrajne
  oddziały szerokiego frontu oskrzydlają (zachodzą z boku, dopiero blisko celu skręcają na niego).
- **Starcie (potyczka).** Oddział ma wspólny cel (najsłabszy z oddziału wroga, najpierw uzdrowiciele i magowie) i bije
  go razem, ale na jednego bota idzie najwyżej ~4 (reszta bierze sąsiadów).
- **Role:**
  - *dystansowcy* (Ninja Łucznik, Sura Magia, Szaman Smok) trzymają dystans (łuk ~720, czary ~520–600), czekając na
    następny czar stoją w miejscu zamiast wchodzić w miecze; walczący wręcz bliżej niż `kite_distance` (400) = odskok w
    bok/do swojego oddziału, w obrębie areny (przy krawędzi wzdłuż niej) – najwyżej 2 odskoki na 6 s, potem walczą;
  - *walczący wręcz* skracają dystans (szarża, Uderzenie Miecza), wolą wspólny cel, bronią swoich dystansowców (biorą
    wroga, który do nich doszedł) i gonią magów/uzdrowicieli;
  - *Szaman Leczenie* stoi za oddziałem, leczy najsłabszego z oddziału (poniżej 60%), buffuje oddział, też odskakuje.
    Szamani buffują swój oddział także czekając na sygnał.
- **Odwrót rannego.** Bot poniżej `retreat_hp` (35%) cofa się do uzdrowiciela oddziału albo w stronę swojej strony,
  pije mikstury (gdy kategoria je pozwala), wraca przy 75% albo po 15 s; następny odwrót najwcześniej po 25 s. Bez
  mikstur i bez uzdrowiciela nie ma odwrotu (byłaby to tylko bierność); dwóch ostatnich z drużyny się nie cofa.
- **Przegrupowanie oddziału.** Po co najmniej 10 s starcia oddział poobijany (średnio < 45% HP, gdy może się podleczyć),
  rozproszony albo w przewadze wroga 2:1 cofa się ~10 m w stronę swojej strony, zbiera, leczy i po 3,5–9 s znowu
  naciera (nie częściej niż co 30 s). Wróg może go gonić. Resztka oddziału (≤ 1/3) dołącza do najbliższego oddziału.
- **Arena.** Wszystkie ruchy zostają w promieniu areny; bot za promieniem wraca jak dotąd.

**Ustawienia** (panel → kategoria → Ustawienia; kolumny `pvpfan_category`, migracja w `pvpfan.sql` przy każdym starcie):
`tactics` (1 = włączona), `squad_size` (5; 2–12), `kite_distance` (400; 150–900, 0 = bez odskoków), `retreat_hp`
(35; 5–80, 0 = bez odwrotów). Flaga `m2_pvpfan_tactics_off` = 1 (w grze albo wiersz `player.quest`) wyłącza taktykę
we wszystkich kategoriach, także w trwającej wojnie – walka jak przed alpha 2.

**Wydajność.** Bez przeszukiwania całej wojny przez każdego bota: siatka przestrzenna (komórki ≥ 500) odbudowywana co
0,5 s, decyzje oddziałów raz na sekundę dla całej wojny (O(boty + oddziały²)), wybór celu z kilku komórek wokół bota,
co ~1,5–2,2 s (bez celu co 0,4 s), sprawdzenie zagrożenia co 0,4 s, leczenie/buffy co 1,2 s tylko w obrębie oddziału.

**Logi** (`PVPFAN:`): co minutę `census tactics` – oddziały żywe (natarcie / starcie / przegrupowanie), miejsca
potyczek (`skirmish_spots`), średnia odległość między botami (`spread_pair`) i w oddziałach (`spread_squad`), odskoki,
odwroty, przegrupowania, leczenia, obrony (`peels`), połączenia oddziałów, średnia długość starcia
(`skirmish_avg_s`, `running_avg_s`, `war_avg_s`); przy wyniku `tactics summary`; pojedyncze decyzje (`squad`,
`kite`, `retreat`, `heal`, `merge`) ograniczone do jednej linii na minutę.

**Jak przetestować (serwer testowy):**

1. Kategoria `wcs` – 2 drużyny: 50 × Wojownik Ciało vs 50 × Szaman Smok (level 120, P, zestawy domyślne), arena
   o promieniu ≥ 5000, mikstury włączone, taktyka domyślna. `/pvpfan start wcs`, `/pvpfan gotowi wcs`. Oczekiwane:
   10 oddziałów na stronę w dwóch liniach, kilka miejsc starć (`skirmish_spots` ≥ 3 w pierwszych minutach), szamani
   odskakują (`kites` > 0), ranni się cofają (`retreats` > 0), walka wyraźnie dłuższa niż przed alpha 2.
2. Kategoria `mix3` – 3 drużyny po 30, każda mieszana (np. 6 Wojownik Ciało, 6 Ninja Łucznik, 6 Sura Magia, 6 Ninja
   Skrytobójca, 6 Szaman Leczenie): oddziały po 5 z uzdrowicielem z tyłu, `heals` > 0, `peels` > 0, potyczki na trzech
   frontach.
3. Porównanie: ta sama kategoria z `tactics` = 0 (albo `m2_pvpfan_tactics_off` = 1) – walka jak dotąd; w logu czas
   wojny (`result ... czas`) i `tactics summary`.
