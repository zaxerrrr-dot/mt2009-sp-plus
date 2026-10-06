# Punkty Rangi – owoce i dodatkowe rangi

Znacznik: `MT2009_PLUS_RANK_POINTS_V1`. „Dodatkowe rangi” z Arezzo (owoce 80050–80054, ich ikony i nazwy,
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

Stosowanie po `server-patches/monstercard` i `server-patches/dropwiki` (kotwice to ich wiersze):
`Apply-RankPointsPatch.ps1 -SourceDir <game/src>` (Windows, `tools/port/Apply-MT2009PlusEngine.ps1`) albo
`python3 apply_rankpoints.py <game/src>` (Linux/VPS).

## Jak działa

- **Owoce** (Metiny i bossowie, 30%, 1–2 szt., wg poziomu **zabitego** potwora): Jabłko (80050) do 53 poz.,
  Gruszka (80051) 54–74, Winogrono (80052) 75–99, Arbuz (80053) 100–109, Ananas (80054) od 110. Gracz – na ziemi
  dla zabójcy (2 min), bot – do plecaka (pełny plecak: nic). Log `[RANGA_DROP]`.
- **Zakresy** (owoc działa tylko w swoim): Jabłko 0–20 000 (+50), Gruszka 20 000–40 000 (+50), Winogrono
  40 000–80 000 (+100), Arbuz 80 000–120 000 (+100), Ananas 120 000–200 000 (+100); maks. 200 000. Poza zakresem –
  odmowa z nazwą owocu potrzebnego teraz. Log `[RANGA_USE]`, `[RANGA_TIER]`.
- **Rangi i bonusy** (jedna ranga naraz, ukryte efekty typu 580 – zostają po śmierci; przeliczane przy
  logowaniu):

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
  `root/rankpoints.py` (komendy `RANGA tail <vid> <ranga>`, `RANGA self <punkty> <ranga>`), exe:
  `chrmgr.SetRankTitle` / `chrmgr.RegisterRankTitle` (`client-patches/exe`, `ENABLE_RANK_TITLE`). Starsze exe:
  tytuł nakładany co pół sekundy przez `textTail.AttachTitle`.
- **Baza**: `player.mt2009_rank_points (pid, points)`.
- **/ranga** – punkty, ranga, bonus, owoc na teraz. GM (`GM_HIGH_WIZARD`): `/ranga ustaw <nick> <punkty>`.
- **Boty**: owoce z ich zabójstw do plecaka; pasujący do zakresu zjadają przy najbliższym przeglądzie (co 20–40 s),
  pozostałe – na stragan (5 000 / 10 000 / 25 000 / 50 000 / 100 000 za szt. przed skalą arkusza) albo do kupca, gdy
  bot nie ma straganu.
- `M2_RANK_POINTS=0` w środowisku kontenera gry wyłącza całość (bez dropu, owoce nic nie robią, bonusy i tytuły
  schodzą przy następnym logowaniu).
