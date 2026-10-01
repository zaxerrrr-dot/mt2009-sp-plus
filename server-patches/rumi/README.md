# Rumi (Okey) Owsapa (1 października) – `MT2009_PLUS_RUMI_V1`

Karcianka Okey z Owsapa (v6.2.6, `minigame_rumi.cpp`, `__OKEY_EVENT_FLAG_RENEWAL__`,
`__RUMI_DEALER__`) z prawdziwymi pakietami (CG/GC 181) i nowym exe. Logika jest w nakładce
`linux-port/overlays/playerbot/src/game/src/playerbot_rumi.h` (dołączonej do
`playerbot_manager.cpp` po `playerbot_ingame_events.h`, tik co sekundę z `playerbot_events.h`);
tu są tylko zmiany plików silnika, opisane w `edits.json`:

| Znacznik | Plik | Co robi |
|---|---|---|
| `MT2009_PLUS_RUMI_V1 (cg header)`, `(gc header)` | `packet.h` | `HEADER_CG_MINI_GAME_RUMI = 181`, `HEADER_GC_MINI_GAME_RUMI = 181` |
| `MT2009_PLUS_RUMI_V1 (packet)` | `packet.h` | struktury i podnagłówki Owsapa (niżej) |
| `MT2009_PLUS_RUMI_V1 (size)` | `packet_info.cpp` | rozmiar CG 181 (7 B) |
| `MT2009_PLUS_RUMI_V1 (packet)` | `input_main.cpp` | `case HEADER_CG_MINI_GAME_RUMI` → `RumiPacket` |
| `MT2009_PLUS_RUMI_V1 (disconnect)` | `char.cpp` | `CHARACTER::Disconnect` → `RumiDisconnect` (rozliczenie gry przy wyjściu) |
| `MT2009_PLUS_RUMI_V1 (use)` | `char_item.cpp` | `UseItemEx` → `RumiUseItem` (79505, 79506), zaraz po goblinie |
| `MT2009_PLUS_RUMI_V1 (kill)` | `item_manager.cpp` | `CreateQuestDropItem` → `RumiOnKill` (karta za zabicie) |
| `MT2009_PLUS_RUMI_V1 (lua)`, `(table)` | `questlua_game.cpp` | `game.get_minigame_rumi_score`, `get_minigame_rumi_my_score`, `minigame_rumi_claim`, `minigame_rumi_pending`, `minigame_rumi_prize` |

- `Apply-RumiPatch.ps1` – Windows (`tools/port/Apply-MT2009PlusEngine.ps1`, po eventmanager,
  bo kotwiczy na jego liniach w `packet.h`);
- `apply_rumi.py <game/src>` – Linux/VPS; oba czytają ten sam `edits.json`.

Każda zmiana wstawia kod **obok** kotwicy (kotwica zostaje), więc łatki innych mini gier na tych
samych liniach dalej się nakładają. Zmiana już nałożona (jest jej znacznik) jest pomijana;
zmiana, której kodu nie ma dokładnie raz, przerywa całość, zanim cokolwiek zostanie zapisane.

## Pakiety (układ Owsapa bajt w bajt, `#pragma pack(1)`)

```
CG 181  { BYTE header; BYTE sub; BOOL bUseCard; BYTE bIndex; }                    7 B
        sub: 0 END, 1 START, 2 DECK_CARD_CLICK, 3 HAND_CARD_CLICK (bUseCard 1 = na stół,
             0 = wyrzuć; bIndex 0-4), 4 FIELD_CARD_CLICK (bIndex 0-2), 5 REQUEST_QUEST_FLAG
GC 181  { BYTE header; WORD size; BYTE sub; } + ciało (dynamiczny, size = 4 + ciało)
        0 END, 1 START                          – bez ciała
        2 SET_DECK        { BYTE bDeckCount; }
        3 SET_SCORE       { WORD wScore, wTotalScore; }
        4 MOVE_CARD       { BYTE bSrcPos, bSrcIndex, bSrcColor, bSrcNumber,
                            bDstPos, bDstIndex, bDstColor, bDstNumber; }
                          pos: 0 brak (wyrzucona), 1 talia, 2 ręka, 3 stół;
                          kolor 10 czerwony, 20 niebieski, 30 żółty; liczba 1-8
        5 SET_CARD_PIECE_FLAG, 6 SET_CARD_FLAG, 7 SET_QUEST_FLAG, 8 NO_MORE_GAIN
                          { WORD wCardPieceCount, wCardCount; }
```

Exe (Owsap, `RecvMiniGameRumi`) woła na oknie gry: `MiniGameRumiStart()`, `MiniGameRumiEnd()`,
`MiniGameRumiSetDeckCount(n)`, `MiniGameRumiIncreaseScore(score, total)`,
`MiniGameRumiMoveCard(8 liczb)`, `MiniGameRumiFlagProcess(sub, (pieces, sets))`; python:
`net.SendMiniGameRumiStart/Exit/DeckCardClick/HandCardClick(use, i)/FieldCardClick(i)/RequestQuestFlag`.
Stałe `player.RUMI_GC_SUBHEADER_*` są opcjonalne (python ma wartości 5-8).

**GC 181 idzie tylko do klienta, który sam wysłał CG 181** na tym rdzeniu (python wysyła
`REQUEST_QUEST_FLAG` zaraz po wejściu do gry) – stary exe zatrzymałby się na nieznanym nagłówku.
Do innych klientów liczniki kart idą liniami czatu.

## Gra i nagrody

- Event: `InGameEventIsActive("rumi")` (harmonogram, flaga `mini_game_okey_normal`, zwykłe
  skrzynie 50275-50277) albo `("rumi_xmas")` (flaga GM-a `mini_game_okey`, świąteczne 50267-50269).
  Stół 20417 stawia menedżer eventów na mapach 1/21/41 (event + 7 dni okna nagród).
- Karta (licznik `minigame_rumi.card_piece_count`) za zabicie potwora: rzut Owsapa
  `GetDropPerKillPct(50, 100, delta, "mini_game_okey_drop")`; 24 karty = zestaw
  (`minigame_rumi.card_count`, najwyżej 999). Przedmioty 79505 (+1 karta, tylko w czasie eventu)
  i 79506 (+1 zestaw). Boty nie zbierają kart i nie grają.
- Gra: 30 000 Yang + 1 zestaw. Koniec gry na żądanie gracza: skrzynia wg wyniku (400+ złota,
  300-399 srebrna, mniej brązowa); wynik idzie do `player.mt2009_rumi_score` (pid, sezon).
- Sezon = event + jego okno nagród. Rdzeń-lider pisze flagi `mini_game_okey_season` (epoka
  początku), `mini_game_okey_season_state` (1 event, 2 okno nagród, 0 nic) i
  `mini_game_okey_season_kind` (1 zwykłe, 2 świąteczne). Pierwsza dziesiątka sezonu (suma
  punktów) odbiera u stołu złote skrzynie: 10/5/3/1×7 – raz na sezon (`minigame_rumi.claimed`).

## Poprawki względem Owsapa

- dobieranie kart tylko przy pustym stole (u Owsapa ręka + stół mogły mieć więcej niż 5 kart, a
  nieudana trójka wracała na rękę tylko częściowo – karty ginęły);
- wylogowanie / warp / zmiana kanału w trakcie gry: gra jest rozliczona (punkty liczą się,
  skrzynia czeka w fladze `minigame_rumi.pending_<vnum>` i przychodzi przy następnym logowaniu
  albo otwarciu okna) – u Owsapa przepadały Yang, zestaw i wynik;
- gra jest usuwana z listy, zanim skrzynia zostanie wydana (brak podwójnej nagrody), a nagroda
  rankingu jest oznaczana przed wydaniem;
- ranking per sezon (u Owsapa jedna tabela na zawsze, nagroda co 7 dni zamiast raz na event);
- zapis wyniku asynchroniczny; zapytania rankingu po `pid` i sezonie;
- GC 181 tylko do exe, które go zna (wyżej).

## Dane

- `linux-port/docker/mariadb/playerbot/apply.sh` (`MT2009_PLUS_RUMI_V1`): tabela
  `player.mt2009_rumi_score`, przedmioty 79505, 79506, 50267-50269, 50275-50277, NPC 20417
  (kopia 20005, `okey_npc`).
- `linux-port/docker/game/special_item_group.rumi.txt` (+ krok w `Dockerfile`): skrzynie (grupy
  Pct) i ich pule 950401-950403 – do edycji.
- `linux-port/docker/game/quest/minigame_rumi.quest` (+ lista w `Dockerfile`).
- Klient: `client-patches/client-2.0.30` (README, sekcja Rumi).
