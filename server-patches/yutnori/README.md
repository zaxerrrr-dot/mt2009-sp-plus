# Yut Nori (Yutnori) – `MT2009_PLUS_YUTNORI_V1`

Mini gra Owsapa (v6.2.6, `minigame_yutnori.cpp`, `uiminigameyutnori.py`) w pełnej wersji: pakiety
182 w obie strony, układy struktur Owsapa, rzucający w 3D w oknie klienta (nowy exe). Logika gry jest
w nakładce `linux-port/overlays/playerbot/src/game/src/playerbot_yutnori.h` (dołączonej do
`playerbot_manager.cpp` po `playerbot_ingame_events.h`, tik co sekundę z `InGameEventTick`); tu są
tylko zmiany plików silnika, opisane w `edits.json`:

| Znacznik | Plik | Co robi |
|---|---|---|
| `MT2009_PLUS_YUTNORI_V1 (cg header)` | `packet.h` | `HEADER_CG_MINI_GAME_YUTNORI = 182` |
| `MT2009_PLUS_YUTNORI_V1 (gc header)` | `packet.h` | `HEADER_GC_MINI_GAME_YUTNORI = 182` |
| `MT2009_PLUS_YUTNORI_V1 (packet)` | `packet.h` | podnagłówki i struktury Owsapa (CG 3 B; GC: nagłówek 4 B + treść) |
| `MT2009_PLUS_YUTNORI_V1 (size)` | `packet_info.cpp` | rozmiar pakietu CG |
| `MT2009_PLUS_YUTNORI_V1 (input)` | `input_main.cpp` | `case HEADER_CG_MINI_GAME_YUTNORI` → `YutnoriPacket` |
| `MT2009_PLUS_YUTNORI_V1 (use)` | `char_item.cpp` | użycie 79507 / 79508 (USE_SPECIAL) → `YutnoriUseItem` |
| `MT2009_PLUS_YUTNORI_V1 (drop)` | `item_manager.cpp` | rzut na pień brzozy przy zabiciu potwora → `YutnoriKillRoll` |

- `Apply-YutnoriPatch.ps1` – Windows (`tools/port/Apply-MT2009PlusEngine.ps1`, po eventmanager,
  bo kotwiczy na jego liniach w `packet.h`);
- `apply_yutnori.py <game/src>` – Linux/VPS; oba czytają ten sam `edits.json`. Każda zmiana
  dopisuje swój kod obok kotwicy, którą zostawia nietkniętą (inne mini gry mogą kotwiczyć tak samo).

## Jak to działa

- **Start**: tylko w czasie eventu `yutnori` (menedżer eventów: harmonogram z paneli albo flaga
  `mini_game_yutnori`) i gdy znany jest sezon. Koszt Owsapa: 1 plansza (licznik
  `minigame_yutnori.board_count`) i 30 000 yang. Pień brzozy to licznik (`piece_count`, 28 → plansza),
  rzut przy zabiciu jak u Owsapa (`mini_game_yutnori_drop`, menedżer ustawia 100); przedmioty 79507/79508
  dodają się do liczników po użyciu.
- **Serwer pilnuje kolejki**: gra przyjmuje tylko ruch, na który czeka (rzut gracza, rzut komputera,
  ruch gracza, ruch komputera, koniec). Owsap pozwalał: ruszać się bez końca po Yut/Mo, rzucać zamiast
  ruszać (losowanie od nowa), grać po końcu gry, grać dalej po ostatnim rzucie "Wstecz do"; ruch
  komputera bez pionka do ruszenia zawieszał grę. Wszystko to naprawione; symulacja 50 000 gier z
  losowymi pakietami spoza kolejki (`sim.cpp` w notatkach agenta) – każda gra się kończy, żaden
  pakiet spoza kolejki niczego nie zmienia. Back-do z pola 16 wraca tam, skąd pionek przyszedł (Owsap
  zawsze na 29).
- **Nagroda**: liczona przy końcu gry (nie po kliknięciu): 83030 (≥ 220 pkt), 83031 (150–219),
  83034 (< 150); komputer też "wygrywa" nagrodę gracza, ale tylko przy punktach > 0. Pudełko idzie do
  flagi `minigame_yutnori.pending_reward` od razu, wynik do `player.minigame_yutnori`. Przycisk
  "Nagroda", następny start albo następne otwarcie okna wydaje je raz (flaga zerowana przed
  wydaniem); przy pełnym ekwipunku flaga zostaje i gracz dostaje komunikat. Wyjście z gry / warp w
  trakcie gry: gra przepada (jak u Owsapa), zarobiona nagroda nie.
- **Sezon**: lider eventów zapisuje `mini_game_yutnori_season` (epoka startu eventu) przy starcie i
  `mini_game_yutnori_season_closed = 1` po końcu. Ranking, wyniki i nagrody top 10 są z bieżącego
  sezonu (Owsap sumował wszystkie eventy od zawsze).
- **NPC 20502** (Stół do Yutnori; stawia go menedżer eventów na mapach 1/21/41, w czasie eventu i
  7 dni okna nagród) – `quest/minigame_yutnori.quest`: "Zagraj" (otwiera okno klienta,
  `YutnoriOpen`), nagrody za grę, ranking (łączny / najlepsza gra), odbiór nagrody top 10 w oknie
  nagród (10/5/3/1× Złote Trofeum, raz na sezon). Bez sklepu, kostki i Sekretu Yutnori Owsapa.
- **Boty**: nie grają (pakiet tylko od klienta, nie `IsBot()`), ich zabicia nie dają pni.
- GM: `/ingame_event gm` pokazuje też stan Yut Nori (sezon, gry na rdzeniu, liczniki).

## Dane

| vnum | co | uwagi |
|---|---|---|
| 79507 | Pień Brzozy | ITEM_USE/USE_SPECIAL, bez handlu |
| 79508 | Plansza do Yutnori | j.w. |
| 83030 | Złote Trofeum Yutnori | GIFTBOX: 83032 + Cor Draconis (drogocenne) |
| 83031 | Srebrne Trofeum Yutnori | GIFTBOX: 83033 + 30% Zwój Błogosławieństwa |
| 83032 | Złoty Pakiet Yutnori | Owsapa 50920 (u nas Receptura) |
| 83033 | Srebrny Pakiet Yutnori | Owsapa 50921 (u nas Receptura) |
| 83034 | Brązowy Pakiet Yutnori | Owsapa 50922 (u nas Receptura) |
| NPC 20502 / 20505 | Stół do Yutnori / Pałeczki Yut | 20505 tylko model w oknie klienta |

- `linux-port/docker/mariadb/playerbot/apply.sh` – tabela `player.minigame_yutnori (season, pid,
  best_score, total_score, games, last_play)`, wiersze `item_proto` i `mob_proto` (INSERT IGNORE).
- `linux-port/docker/game/special_item_group.yutnori.txt` – zawartość pudełek (krok Dockerfile
  "share: Yut Nori boxes"); bez jajek, wierzchowców, kostiumów, szarf i broni.

## Klient

- python: `client-patches/client-2.0.30/root/uiminigameyutnori.py`, `uiscript/minigameyutnori*.py`,
  haki w `game.py` (`YutnoriProcess`, `YutnoriFlagProcess`, `YutnoriOpen`, `Register`, `Destroy`),
  przycisk w `uiingameevent.py`; opis zasad `locale/locale/pl/yutnori_event_desc.txt`, `itemdesc.txt`,
  `gamedata/item_list.txt`.
- exe (osobny port): nazwy Owsapa – `net.SendMiniGameYutnori*`, `player.YutnoriShow/ChangeMotion`,
  `app.YutnoriCreate`, `app.RENDER_TARGET_INDEX_YUTNORI`, `item.ITEM_VNUM_YUT_PIECE/BOARD`, `wndMgr`
  ruchome/skalowane obrazki i teksty, render target, `EnableFlash`, `ResetFrame`, `OnKeyFrame`.
  Bez nich przycisk wydarzenia mówi, że gra wymaga nowego klienta.
