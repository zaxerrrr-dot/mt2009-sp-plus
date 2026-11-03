# fishpuzzle – Event Rybacki - Puzzle (Wędkarskie Puzzle)

Znaczniki: `MT2009_PLUS_FISH_PUZZLE_V1` (właściciel, 3.11.2026) i `MT2009_PLUS_FISH_PUZZLE_V2` (paczka właściciela
„Mini Game Fish Event (17.3)” – „Jigsaw FULL + Fix Scale”, 3.11.2026: „w pełni jak na globalu, z tą paczką; jeśli
potrzebne exe, zrobimy w exe”). Logika: `linux-port/overlays/playerbot/src/game/src/fish_puzzle.cpp`, tu tylko haki
(`gen_edits.py` → `edits.json`, `apply_fishpuzzle.py` / `Apply-FishPuzzlePatch.ps1`).

## V2 – gra i pakiety z paczki, nowy exe
Kanał komend czatu z V1 (`/fishpuzzle open|box|place|discard`, `FP state|piece|done`) jest wycofany. Gra jest grą
paczki (jej `char.cpp` FishEvent*, `uiMiniGameFishEvent.py`), z jej pakietami – w nowym exe (`client-patches/exe`,
`ENABLE_FISH_EVENT`, build `cache/yohara/exe-out10`):

| Pakiet | Nagłówek | Treść |
|---|---|---|
| CG `HEADER_CG_FISH_EVENT_SEND` | **219** | `{BYTE header; BYTE sub;}` + `BOX_USE`(0): `BYTE okno, WORD pole` / `SHAPE_ADD`(1): `BYTE pole`, potem bajt sekwencji |
| GC `HEADER_GC_FISH_EVENT_INFO` | **223** | `{BYTE header; BYTE sub; DWORD a1; DWORD a2;}` = 10 B: `BOX_USE`(0) kształt, próby · `SHAPE_ADD`(1) pole, kształt · `GC_REWARD`(2) vnum · `GC_ENABLE`(3) baner 0/1, próby |

219 i 223 to numery paczki – wolne w naszym `packet.h` serwera i w `Packet.h` exe (zajęte m.in. 170/171, 181–183,
187, 196, 205–218, 220, 226, 238, 250–255). Stary exe rozłącza się na nieznanym nagłówku, więc serwer wysyła GC 223
dopiero po `/fishpuzzle hello` z roota (`uifishpuzzle.py`, tylko gdy `app.ENABLE_FISH_EVENT`); pudło użyte ze starego
klienta i stare komendy dostają komunikat „Wędkarskie Puzzle wymagają nowej wersji klienta”. Pudło użyte z ekwipunku
w nowym kliencie otwiera planszę (`FP open`). CG 219 bez hello jest odczytany i pominięty.

| Znacznik | Plik | Co robi |
|---|---|---|
| `V1 (catch)` | `fishing.cpp` | po `FishingSuccess` → `Mt2009FishPuzzleOnCatch` (bez zmian względem V1) |
| `V1 (use)` | `char_item.cpp` | `UseItemEx` → `Mt2009FishPuzzleUseItem` (25106/25107: `FP open` albo komunikat o kliencie) |
| `V1 (command declare)`, `(command table)` | `cmd.cpp` | `/fishpuzzle hello` |
| `V2 (cg header)`, `(gc header)`, `(packet)` | `packet.h` | 219 / 223, podnagłówki, struktury (+ `static_assert` 2 / 10 B) |
| `V2 (size)` | `packet_info.cpp` | rozmiar CG 219 (2 B + sekwencja, reszta dynamicznie) |
| `V2 (packet)` | `input_main.cpp` | `case HEADER_CG_FISH_EVENT_SEND` → `Mt2009FishEventPacket` |

Do tego `playerbot_ingame_events.h`: `InGameEventTick` woła `Mt2009FishEventTick` (zmiana stanu eventu → ENABLE i
plansza dla klientów po hello).

## Zasady (paczka)
- Podczas eventu **każdy** udany połów (`fishing::ProcessFishingGameSuccess`) daje **5** Pudeł wędkarskich puzzli
  25106 (flaga `fish_puzzle_boxes`); z Rybimi Wnętrznościami (premium FISH_MIND albo grupa unikatowa 10009: 71008,
  72013-72015) **10%** połowów daje zamiast tego 1 Luks. pudło 25107 (`fish_puzzle_deluxe`, promile, 100).
- Pudło przeciągnięte (albo pierwsze znalezione) do okna i otwarte = 1 próba: 25106 losowy kształt 1-6, 25107 duży 3×2
  (7). Element na myszy kładzie się na planszy 6×4 (pytanie „położyć?”), prawy klik – pytanie i wyrzucenie.
- Pełna plansza: +30 000 PD i wg prób Zł. Skrzynia na Ryby (D) 83003 (≤10), (Ś) 83002 (11-24), (M) 83001 (≥25) –
  paczka ma 25113/25112/25111 jako skrzynie GACHA bez zawartości; klient GF 26.1.11 ma te skrzynie jako 83001-83003
  (ikona 25111.tga), więc zostają nasze vnumy, zawartość `special_item_group.fishpuzzle.txt`, otwierają się 3/2/1 raz.
- Poprawione względem paczki: element w ręce znika po położeniu (w paczce można było kłaść ten sam w kółko), pole pudła
  czytane jako WORD (paczka czytała 1 znak), L-ki nie „zawijają się” przez prawą krawędź planszy, bez hello nic.
- Stan (plansza, element w ręce, próby, ukończone) w `player.fish_puzzle` (`fish_puzzle.sql`) – **nie** kolumny paczki
  `player.fish_slots`/`fish_use_count` (bez zmiany `TPlayerTable` i rdzenia db). Element w ręce przepada przy hello
  (nowe okno gry po logowaniu/teleporcie), jak w paczce po wylogowaniu.
- Przedmioty 25106/25107: antyflagi paczki (DROP | GIVE | MYSHOP = 73856), typ zostaje ITEM_QUEST (użycie otwiera okno).
- Boty: nie dostają pudeł, nie grają.

## Event
Rodzaj planera `fishpuzzle` (`KIND_FISHPUZZLE` 19, `KIND_MAX` 20), flaga `fish_puzzle_event` (1/0) + 7 dni
`fish_puzzle_reward` po zaplanowanym evencie (baner i plansza dalej dostępne). Ręcznie: `/eventflag fish_puzzle_event 1`
albo flaga paczki `/e enable_fish_event 1`. Kalendarz SAPPHIRE (wiki): środa 00-12, sobota 12-16 – w profilach SAPPHIRE
i EMERALD (`server_profiles.txt`).

## Kolejność
Po `relikty` (hak użycia stoi pod jego blokiem) i `switchbot` (haki pakietów stoją pod jego liniami), np. na końcu listy.
Linux: `python3 apply_fishpuzzle.py <game/src>`; Windows: `Apply-FishPuzzlePatch.ps1 -SourceDir <game/src>` (wołane na
końcu `tools/port/Apply-MT2009PlusEngine.ps1`).
