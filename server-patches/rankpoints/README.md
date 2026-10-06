# Punkty Rangi – owoce i dodatkowe rangi

Znaczniki: `MT2009_PLUS_RANK_POINTS_V1`, `MT2009_PLUS_RANK_POINTS_V2` (jedna skala). „Dodatkowe rangi” z Arezzo (owoce 80050–80054, ich ikony i nazwy,
nazwy rang i kolory z klienta Arezzo) z liczbami właściciela (6 października). Kod:
`linux-port/overlays/playerbot/src/game/src/playerbot_rank_points.h` (w jednostce `playerbot_manager.cpp`).

## Zmiany silnika (`edits.json`)

| Znacznik | Plik | Co robi |
|---|---|---|
| `MT2009_PLUS_RANK_POINTS_V1 (declare)` / `(table)` | `cmd.cpp` | komenda `/ranga` (każdy gracz, `POS_DEAD`) |
| `MT2009_PLUS_RANK_POINTS_V1 (kill)` | `char_battle.cpp` | po Kartach Potworów: `RankPointsOnKill` – owoc z Metina/bossa |
| `MT2009_PLUS_RANK_POINTS_V1 (use)` | `char_item.cpp` | początek `UseItemEx`, po Kartach Potworów: `RankPointsUseItem` – zjedzenie owocu |
| `MT2009_PLUS_RANK_POINTS_V1 (login)` | `input_login.cpp` | po Kartach Potworów: `RankPointsOnLogin` – punkty z bazy, bonus, tytuł |
| `MT2009_PLUS_RANK_POINTS_V1 (insert)` | `char.cpp` | `EncodeInsertPacket`: postać z rangą wchodzi w widok gracza – `RANGA tail <vid> <ranga>` |
| `MT2009_PLUS_RANK_POINTS_V1 (wiki)` | `item_manager.cpp` | wiki dropu: owoc Metina/bossa (1–2 szt., 30%) |
| `MT2009_PLUS_RANK_POINTS_V2 (alignment)` | `char_battle.cpp` | `CHARACTER::UpdateAlignment`: `RankPointsOnAlignment` – zwykła ranga przekracza 20 000 (w górę lub w dół): bonus, tytuł, `RANGA self` od razu |

Stosowanie po `server-patches/monstercard` i `server-patches/dropwiki` (kotwice to ich wiersze):
`Apply-RankPointsPatch.ps1 -SourceDir <game/src>` (Windows, `tools/port/Apply-MT2009PlusEngine.ps1`) albo
`python3 apply_rankpoints.py <game/src>` (Linux/VPS).

## Jak działa

- **Jedna skala (V2, właściciel 6.10: „rangi arezzo mają być kontynuacją punktów rangi zwykłej, które są do 20000,
  a od 20000 zaczynają się punkty arezzo”)**. Zwykła ranga gry (alignment, pokazywana `GetRealAlignment() / 10`,
  −20 000…+20 000) to dół skali; punkty Arezzo ponad nią są w bazie (`extra`, 0…180 000):
  - `suma = ranga zwykła`, dopóki ranga zwykła < 20 000;
  - `suma = 20 000 + extra`, gdy ranga zwykła stoi na maksimum (20 000).

  Gdy ranga zwykła spadnie poniżej 20 000 (zabicie gracza, umiejętność kupiona za rangę), `extra` zostaje
  zapisane, ale się nie liczy – suma to ranga zwykła, bonus i tytuł rangi znikają – aż ranga zwykła wróci do
  20 000 (wtedy `extra` od razu liczy się znowu). Rangi, bonusy, tytuły, `/ranga` i `RANGA self` – wszystko wg sumy.
- **Owoce** (Metiny i bossowie, 30%, 1–2 szt., wg poziomu **zabitego** potwora): Jabłko (80050) do 53 poz.,
  Gruszka (80051) 54–74, Winogrono (80052) 75–99, Arbuz (80053) 100–109, Ananas (80054) od 110. Gracz – na ziemi
  dla zabójcy (2 min), bot – do plecaka (pełny plecak: nic). Log `[RANGA_DROP]`.
- **Zakresy sumy** (owoc działa tylko w swoim; V2: zyski ×4 względem V1): Jabłko 0–20 000 (+200 do **zwykłej
  rangi** – `UpdateAlignment(+2000)`, do maksimum silnika), Gruszka 20 000–40 000 (+200), Winogrono 40 000–80 000
  (+400), Arbuz 80 000–120 000 (+400), Ananas 120 000–200 000 (+400) – te cztery do `extra`, więc dopiero przy
  zwykłej randze 20 000; maks. 200 000. Poza zakresem – odmowa z nazwą owocu potrzebnego teraz; przy ujemnej randze
  – „owoce działają od 0”. Log `[RANGA_USE]`, `[RANGA_TIER]`. `value0` w `item_proto` = 200/200/400/400/400
  (`apply.sh` podnosi stare 50/100 UPDATE-em; serwer liczy z własnej tabeli `FRUITS`).
- **Rangi i bonusy** (wg sumy; jedna ranga naraz, ukryte efekty typu 580 – zostają po śmierci; przeliczane przy
  logowaniu, po owocu, po `/ranga ustaw` i gdy zwykła ranga przekroczy 20 000 w którąkolwiek stronę):

  | Od | Ranga | Potwory | Ludzie | Metiny | Bossowie | Średnie obr. | PŻ |
  |---|---|---|---|---|---|---|---|
  | 21 000 | Waleczny | 10% | 10% | | | | 1000 |
  | 31 000 | Mocarny | 12% | 12% | | | | 1500 |
  | 41 000 | Potężny | 15% | 15% | | | | 1900 |
  | 51 000 | Władca | 18% | 18% | | | | 2200 |
  | 81 000 | Arcymistrz | 18% | 18% | 10% | | | 2900 |
  | 101 000 | Legenda | 18% | 18% | 15% | 10% | | 3500 |
  | 121 000 | Legenda | 18% | 18% | 15% | 15% | | 4000 |
  | 200 000 | Legenda | 20% | 20% | 18% | 18% | 10% | 5000 |

  Punkty: `POINT_ATTBONUS_MONSTER`, `_HUMAN`, `_STONE`, `_BOSS`, `POINT_NORMAL_HIT_DAMAGE_BONUS`, `POINT_MAX_HP`.
- **Tytuł nad głową**: od 21 000 nazwa rangi w jej kolorze w miejscu rangi za punkty (alignment). Klient:
  `root/rankpoints.py` (komendy `RANGA tail <vid> <ranga>`, `RANGA self <suma> <ranga>`), exe:
  `chrmgr.SetRankTitle` / `chrmgr.RegisterRankTitle` (`client-patches/exe`, `ENABLE_RANK_TITLE`). Starsze exe:
  tytuł nakładany co pół sekundy przez `textTail.AttachTitle`.
- **Okno postaci** (`uicharacter.py`, `rankpoints.BuildAlignmentToolTip`): dymek rangi pokazuje JEDNO „Punkty
  Rangi: <suma>” (poniżej 20 000 – bieżąca zwykła ranga klienta, wyżej – suma z `RANGA self`), nad nim nazwę
  rangi (albo tytuł zwykłej rangi), pod nim bonus, następną rangę i owoc na teraz. Serwer bez `RANGA self`: stary
  dymek.
- **Baza**: `player.mt2009_rank_points (pid, points, scale)` – w V2 `points` = `extra` (punkty ponad 20 000),
  `scale = 2`. **Migracja z V1** (tam `points` było całą osobną skalą 0–200 000): wiersze ze `scale = 1` (domyślna
  kolumny – V1 jej nie zapisywał, więc wiersz zapisany później przez stary plik binarny też się złapie) dostają
  `points = max(0, points − 20 000)`, `scale = 2` – raz przy pierwszym użyciu tabeli na rdzeniu (`EnsureTable`, log
  `[RANGA_MIGRATE]`) i jeszcze przy odczycie takiego wiersza. Idempotentne. Zwykła ranga – kolumna silnika
  `player.alignment`, bez zmian.
- **/ranga** – suma, ranga, bonus, owoc na teraz, zachowane punkty ponad 20 000 (gdy zwykła ranga spadła). GM
  (`GM_HIGH_WIZARD`): `/ranga ustaw <nick> <suma>` – poniżej 20 000 ustawia zwykłą rangę (i `extra` = 0), od 20 000
  zwykłą rangę na maksimum i `extra = suma − 20 000`.
- **Boty**: te same zasady (zakres wg sumy, Jabłko podnosi zwykłą rangę); owoce z ich zabójstw do plecaka; pasujący do zakresu zjadają przy najbliższym przeglądzie (co 20–40 s),
  pozostałe – na stragan (5 000 / 10 000 / 25 000 / 50 000 / 100 000 za szt. przed skalą arkusza) albo do kupca, gdy
  bot nie ma straganu.
- `M2_RANK_POINTS=0` w środowisku kontenera gry wyłącza całość (bez dropu, owoce nic nie robią, bonusy i tytuły
  schodzą przy następnym logowaniu).
