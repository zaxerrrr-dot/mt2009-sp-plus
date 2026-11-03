# fishpuzzle – Event Rybacki - Puzzle (Wędkarskie Puzzle)

Znacznik: `MT2009_PLUS_FISH_PUZZLE_V1` (właściciel, 3.11.2026). Logika: `linux-port/overlays/playerbot/src/game/src/fish_puzzle.cpp`,
tu tylko haki (`gen_edits.py` → `edits.json`, `apply_fishpuzzle.py` / `Apply-FishPuzzlePatch.ps1`).

## Exe – bez zmian
Nasz exe (źródło `cache/client-build` = `yohara/exe-src8`, build `exe-out9`) **nie ma** pakietów eventu rybackiego
(`HEADER_CG/GC_FISH_EVENT`, `fish_event_grid_table`, `net.SendFishBoxUse` – brak w źródle i w stringach exe).
Ameria też ich nie ma (tylko osierocone `IsOpenJigsaw()` w `char_item.cpp` i `fish_event_desc.txt`), Owsap tylko dwa
uiscripty GF. Dlatego całość idzie kanałem komend czatu (jak worldboss, welem, relikty):

- klient → serwer: `/fishpuzzle open | box <1|2> | place <pole 0-23> | discard`
- serwer → klient (`game.py` „FP” → `uifishpuzzle.py`):
  `FP state <event 0/1> <próby> <element w ręce 0-7> <pudła> <pudła luks.> <elementy|->`, `FP open`,
  `FP piece <kształt> <próby>`, `FP done <próby> <vnum nagrody>`;
  elementy: po 2 znaki – kształt `1`-`7` i lewe górne pole `a`+0..23 (plansza 6×4, wierszami).

## Zasady (pl-wiki „Event Rybacki - Puzzle”, „Minigra: Wędkarskie Puzzle”)
- Podczas eventu udany połów (`fishing::ProcessFishingGameSuccess`) daje Pudło wędkarskich puzzli 25106 z szansą 30%
  (flaga `fish_puzzle_chance`, promile, domyślnie 300); z Rybimi Wnętrznościami (premium FISH_MIND albo grupa unikatowa
  10009: 71008, 72013-72015) zawsze, a wtedy 2% (`fish_puzzle_deluxe`, 20) na Luks. pudło 25107 zamiast zwykłego.
- Pudło otwiera się w oknie (każde = 1 próba): 25106 losowy z 6 kształtów, 25107 duży 3×2. Element kładzie się na
  planszy 6×4 (bez nachodzenia), prawy klik – odrzucenie. Pudło użyte z ekwipunku tylko otwiera okno.
- Pełna plansza: +30 000 PD i wg prób Zł. Skrzynia na Ryby (D) 83003 (≤10), (Ś) 83002 (11-24), (M) 83001 (≥25);
  otwierają się 3 / 2 / 1 raz (`ShipDefense_ChestKeep`), zawartość `special_item_group.fishpuzzle.txt`.
- Stan (plansza, element w ręce, próby, ukończone) w `player.fish_puzzle` (`fish_puzzle.sql`) – relog/zmiana kanału go zachowuje.
- Boty: nie dostają pudeł (połów bota pomijany), nie mogą grać (komenda i użycie odrzucone).

## Event
Rodzaj planera `fishpuzzle` (`KIND_FISHPUZZLE` 18, `KIND_MAX` 19), flaga `fish_puzzle_event` (1/0) +
7 dni `fish_puzzle_reward` po zaplanowanym evencie (lista eventów dalej otwiera okno). Ręcznie: `/eventflag fish_puzzle_event 1`.
Kalendarz SAPPHIRE (wiki): środa 00-12, sobota 12-16 – wiersze `event fishpuzzle 3 00:00 12:00 0` i
`event fishpuzzle 6 12:00 16:00 0` (server_profiles.txt – dodaje koordynator).

## Kolejność
Po `relikty` (hak użycia stoi pod blokiem reliktu), np. na końcu listy. Linux: `python3 apply_fishpuzzle.py <game/src>`;
Windows: `Apply-FishPuzzlePatch.ps1 -SourceDir <game/src>` (wołane na końcu `tools/port/Apply-MT2009PlusEngine.ps1`).
