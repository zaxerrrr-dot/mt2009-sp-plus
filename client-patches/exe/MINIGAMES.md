# Mini gry Owsapa w exe – `MT2009_PLUS_MINIGAMES_V1`

Port z Owsap v6.2.6 (pełne prawa właściciela) do naszego `metin2client.exe`: Rumi (Okey), Yut Nori
(z modelem 3D w render target), Złap Króla (Catch the King) i Dzieci Kwiatów (Flower Event), plus
widżety/funkcje `wndMgr`, których używa `ui.py` Owsapa. Nazwy po stronie pythona są **dokładnie**
nazwami Owsapa, więc jego `uiminigame*.py`, `uiflowerevent.py` i uiscripty idą prawie bez zmian.

Definicje w `UserInterface/Locale_inc.h` (wyłączenie przywraca stare zachowanie):
`ENABLE_MINI_GAME_RUMI`, `ENABLE_OKEY_EVENT_FLAG_RENEWAL`, `ENABLE_MINI_GAME_YUTNORI`,
`ENABLE_YUTNORI_EVENT_FLAG_RENEWAL`, `ENABLE_MINI_GAME_CATCH_KING`, `ENABLE_CATCH_KING_EVENT_FLAG_RENEWAL`,
`ENABLE_FLOWER_EVENT`, `ENABLE_OWSAP_WNDMGR_EX` (widżety), `RENDER_TARGET`, `ENABLE_MOUSE_WHEEL_TOP_WINDOW`.

## 1. Pakiety (dla serwera)

Układy identyczne z `packet.h` serwera Owsapa, `#pragma pack(1)`, `BOOL` = 4 bajty (serwer -m32),
`bool` = 1 bajt, WORD/DWORD little endian. Każdy pakiet CG idzie z bajtem sekwencji jak wszystkie
inne (`SendSequence`), więc serwer liczy rozmiar w `packet_info.cpp` bez niego (jak zwykle).

### Klient → serwer (stały rozmiar)

| Nagłówek | Struktura | Rozmiar | Podnagłówki (`bSubHeader`) |
|---|---|---|---|
| `HEADER_CG_MINI_GAME_RUMI = 181` | `{BYTE bHeader; BYTE bSubHeader; BOOL bUseCard; BYTE bIndex;}` | **7** | 0 END (wyjście), 1 START, 2 DECK_CARD_CLICK, 3 HAND_CARD_CLICK (`bUseCard` 1 = zagraj, 0 = wyrzuć; `bIndex` = karta w ręce), 4 FIELD_CARD_CLICK (`bIndex` = karta na polu), 5 REQUEST_QUEST_FLAG |
| `HEADER_CG_MINI_GAME_YUTNORI = 182` | `{BYTE bHeader; BYTE bSubHeader; BYTE bArgument;}` | **3** | 0 START, 1 GIVEUP, 2 SET_PROB (arg = indeks prawdopodobieństwa), 3 CLICK_CHAR (arg = pionek), 4 THROW (arg = 1 gracz / 0 komputer), 5 MOVE (arg = pionek), 6 REQUEST_COM_ACTION, 7 REWARD, 8 REQUEST_QUEST_FLAG |
| `HEADER_CG_FLOWER_EVENT = 187` | `{BYTE bHeader; BYTE bSubHeader; BYTE bShootType; BYTE bExchangeKey;}` | **4** | 0 INFO_ALL (`bShootType` = 6 = SHOOT_TYPE_MAX, `bExchangeKey` 0), 1 EXCHANGE (`bShootType` 0..5, `bExchangeKey` = indeks ilości z listy okna: 1/10/50/100) |
| `HEADER_CG_MINI_GAME_CATCH_KING = 226` | `{BYTE bHeader; BYTE bSubHeader; BYTE bSubArgument;}` | **3** | 0 START (arg = liczba talii 1..5), 1 CLICK_HAND, 2 CLICK_CARD (arg = pole planszy), 3 REWARD, 4 REQUEST_QUEST_FLAG |

Exe wysyła: Rumi/Yut Nori zawsze; Złap Króla tylko gdy postać może działać (`__CanActMainInstance`, jak
Owsap; REQUEST_QUEST_FLAG zawsze, z `bSubArgument` = 0 – Owsap wysyłał tu śmieci); Kwiaty tylko gdy
`player.GetFlowerEventEnable()` (ustawiane z pythona po komendzie serwera `e_flower_drop <v>`).
**Serwer musi sprawdzać zakresy** (`bShootType`, `bExchangeKey`, `bIndex`, pola Złap Króla) – Owsap
tego nie robił (błąd OOB).

### Serwer → klient

Rumi, Yut Nori i Złap Króla są **dynamiczne**: nagłówek 4 bajty `{BYTE bHeader; WORD wSize; BYTE bSubHeader;}`,
`wSize` = cały pakiet (nagłówek + ciało), potem ciało zależne od podnagłówka. Kwiaty – **stały** 32 B.

| Nagłówek | Podnagłówek | Ciało | Python (metoda okna gry, jak Owsap) |
|---|---|---|---|
| `HEADER_GC_MINI_GAME_RUMI = 181` | 0 END | – | `MiniGameRumiEnd()` |
| | 1 START | – | `MiniGameRumiStart()` |
| | 2 SET_DECK | `BYTE bDeckCount` (1) | `MiniGameRumiSetDeckCount(n)` |
| | 3 SET_SCORE | `WORD wScore, wTotalScore` (4) | `MiniGameRumiIncreaseScore(score, total)` |
| | 4 MOVE_CARD | `BYTE src{Pos,Index,Color,Number}, dst{Pos,Index,Color,Number}` (8) | `MiniGameRumiMoveCard(8 x int)` |
| | 5 SET_CARD_PIECE_FLAG, 6 SET_CARD_FLAG, 7 SET_QUEST_FLAG, 8 NO_MORE_GAIN | `WORD wCardPieceCount, wCardCount` (4) | `MiniGameRumiFlagProcess(sub, (piece, count))` |
| `HEADER_GC_MINI_GAME_YUTNORI = 182` | 0 START, 1 STOP | – | `YutnoriProcess(sub, 0)` |
| | 2 SET_PROB | `BYTE bProbIndex` (1) | `YutnoriProcess(sub, prob)` |
| | 3 THROW | `bool bPC; BYTE bYut` (2) | `YutnoriProcess(sub, (pc, yut))` |
| | 4 MOVE | `bool bPC; BYTE bUnitIndex; bool bIsCatch; BYTE bStartIndex; BYTE bDestIndex` (5) | `YutnoriProcess(sub, (pc, unit, catch, start, dest))` |
| | 5 AVAILABLE_AREA | `BYTE bPlayerIndex, bAvailableIndex` (2) | `YutnoriProcess(sub, (player, avail))` |
| | 6 PUSH_CATCH_YUT | `bool bPC; BYTE bUnitIndex` (2) | `YutnoriProcess(sub, (pc, unit))` |
| | 7 SET_SCORE | `WORD wScore` (2) | `YutnoriProcess(sub, score)` |
| | 8 SET_REMAIN_COUNT | `BYTE bRemainCount` (1) | `YutnoriProcess(sub, n)` |
| | 9 PUSH_NEXT_TURN | `bool bPC; BYTE bState` (2) | `YutnoriProcess(sub, (pc, state))` |
| | 10 SET_YUT_PIECE_FLAG, 11 SET_YUT_BOARD_FLAG, 12 SET_QUEST_FLAG, 13 NO_MORE_GAIN | `WORD wYutPieceCount, wYutBoardCount` (4) | `YutnoriFlagProcess(sub, (piece, board))` |
| `HEADER_GC_MINI_GAME_CATCH_KING = 238` | 0 START | `DWORD dwBigScore` (4) | `MiniGameCatchKingEventStart(score)` |
| | 1 SET_CARD | `BYTE bCardNumber` (1) | `MiniGameCatchKingSetHandCard(n)` |
| | 2 RESULT_FIELD | `DWORD dwPoints; BYTE bRowType, bCardPos, bCardValue; bool bKeepFieldCard, bDestroyHandCard, bGetReward, bIsFiveNearBy` (**11**) | `MiniGameCatchKingResultField(8 wartości)` |
| | 3 SET_END_CARD | `BYTE bCardPos, bCardValue` (2) | `MiniGameCatchKingSetEndCard(pos, value)` |
| | 4 REWARD | `BYTE bReturnCode` (1) | `MiniGameCatchKingReward(code)` |
| | 5 SET_CARD_PIECE_FLAG, 6 SET_CARD_FLAG, 7 SET_QUEST_FLAG, 8 NO_MORE_GAIN | `WORD wPieceCount, wPackCount` (4) | `CatchKingFlagProcess(sub, (piece, pack))` |
| `HEADER_GC_FLOWER_EVENT = 187` (stały) | `{BYTE bHeader, bSubHeader, bChatType, bShootType; int aiShootCount[7];}` = **32 B** | 0 INFO_ALL → `FlowerEventProcess(0, (envelope, chrysanthemum, may_bell, daffodil, lily, sunflower))`; 1 GET_INFO: `bShootType` = 6 → `FlowerEventProcess(1, chatType)`, inaczej `FlowerEventProcess(1, (type, count))`; 2 UPDATE_INFO → `FlowerEventProcess(2, (type, count))` |

Indeksy kwiatów (`aiShootCount`, `bShootType`): 0 ENVELOPE (nasiona), 1 CHRYSANTHEMUM, 2 MAY_BELL,
3 DAFFODIL, 4 LILY, 5 SUNFLOWER, 6 = SHOOT_TYPE_MAX. `bChatType` = `EFlowerEventChatType` Owsapa
(0 NOT_ENOUGH_SHOOT_COUNT … 15 ENVELOPE_MAX, 16 MAX).

Poprawki po stronie exe względem Owsapa: każde ciało pakietu dynamicznego jest sprawdzane co do
rozmiaru (za krótkie = log w syserr i pominięcie, strumień zostaje zsynchronizowany); `bShootType` z
UPDATE_INFO/GET_INFO spoza 0..5 nie czyta poza tablicą.

**Stary exe (2.0.25) rozłącza się na nieznanym nagłówku** – serwer może wysyłać te pakiety tylko
klientowi, który ma nowy exe. Wszystkie GC poza Kwiatami są odpowiedziami na CG (gracz otworzył grę),
więc wystarczy nie wysyłać ich bez zapytania. Dla Kwiatów (i ewentualnych komunikatów przy zabiciu)
python może zgłosić możliwość w istniejącym `/ingame_event hello <caps>` (np. bit 4, gdy istnieje
`app.MT2009_MINIGAMES`).

Efekt Kwiatów: nie ma `SE_FLOWER_EVENT` (enum `SE_*` jest we wspólnym `common/length.h`, którego exe
nie zmieniamy) – serwer daje `ch->SpecificEffectPacket("d:/ymir work/effect/etc/buff/buff_item15_flower.mse")`.
`chrmgr.EFFECT_FLOWER_EVENT` istnieje (rejestracja w `playersettingmodule.py` Owsapa nie wywali się).

Przedmioty-żetony (wolne u nas): 79505/79506 karta/talia Okey, 79507/79508 gałązka/plansza Yut,
79603/79604 karta/talia Króla (`item.ITEM_VNUM_*`). Afekty: `chr.NEW_AFFECT_FLOWER_EVENT` = 570,
`chr.NEW_AFFECT_HALLOWEEN_EVENT` = 575.

## 2. Python API (nowe w exe)

### `net`
`SendMiniGameRumiExit()`, `SendMiniGameRumiStart()`, `SendMiniGameRumiDeckCardClick()`,
`SendMiniGameRumiHandCardClick(bUse, index)`, `SendMiniGameRumiFieldCardClick(index)`,
`SendMiniGameRumiRequestQuestFlag()`;
`SendMiniGameYutnoriStart()`, `SendMiniGameYutnoriGiveup()`, `SendMiniGameYutnoriProb(i)`,
`SendMiniGameYutnoriCharClick(i)`, `SendMiniGameYutnoriThrow(pc)`, `SendMiniGameYutnoriMove(i)`,
`SendMiniGameYutnoriReward()`, `SendMiniGameYutnoriRequestComAction()`, `SendMiniGameYutnoriRequestQuestFlag()`;
`SendMiniGameCatchKing(sub, arg)`, `SendMiniGameCatchKingRequestQuestFlag()`;
`SendFlowerEventRequestInfo()`, `SendFlowerEventExchange(shootType, exchangeKey)`;
stałe `FLOWER_EVENT_SUBHEADER_GC_INFO_ALL/GET_INFO/UPDATE_INFO`.

### `player`
`Set/GetRumiGame`, `Set/GetMiniGameOkeyNormal`, `Set/GetCatchKingGame`, `Set/GetFlowerEventEnable`,
`YutnoriShow(bool)`, `YutnoriChangeMotion(i)` (0 WAIT, 1 STAND_UP, 2 DEAD, 3 NORMAL_ATTACK, 4 SPAWN,
5 SPECIAL_1 rasy 20505; koniec ruchu → `YutnoriProcess(10, 0)` okna gry), `GetLevel()`;
stałe `MINIGAME_RUMI/YUTNORI/CATCHKING/ROULETTE`, `FLOWER_EVENT`, `SNOWFLAKE_STICK_EVENT`,
`MINIGAME_TYPE_MAX`, `RUMI_GC_SUBHEADER_*_FLAG/NO_MORE_GAIN`, `YUTNORI_GC_SUBHEADER_*`,
`CATCHKING_GC_*`, `SHOOT_*`, `FLOWER_EVENT_*` (jak Owsap).

### `app`
`YutnoriCreate()` (tworzy render target i model 20505 – wołać raz po wejściu do gry, jak `game.py` Owsapa);
stałe `ENABLE_MINI_GAME_RUMI/YUTNORI/CATCH_KING`, `ENABLE_*_EVENT_FLAG_RENEWAL`, `ENABLE_FLOWER_EVENT`,
`ENABLE_MOUSE_WHEEL_TOP_WINDOW` = 1; `ENABLE_SUMMER_EVENT_ROULETTE`, `ENABLE_SNOWFLAKE_STICK_EVENT`,
`ENABLE_CHATTING_WINDOW_RENEWAL`, `ENABLE_EVENT_BANNER_REWARD_LIST_RENEWAL` = 0; `RENDER_TARGET` = 1,
`RENDER_TARGET_INDEX_YUTNORI`; `MT2009_MINIGAMES` = 1 (wykrywanie nowego exe).

### `item`, `chr`, `chrmgr`, `grpImage`
`item.ITEM_VNUM_RUMI_CARD_PIECE/PACK`, `ITEM_VNUM_YUT_PIECE/BOARD`, `ITEM_VNUM_CATCH_KING_PIECE/PACK`;
`chr.NEW_AFFECT_FLOWER_EVENT`, `chr.NEW_AFFECT_HALLOWEEN_EVENT`; `chrmgr.EFFECT_FLOWER_EVENT`;
`grpImage.GetGraphicImagePointer(handle)` (karty Rumi do `wndMgr.SetSlot`).

### `wndMgr` (nazwy z `ui.py` Owsapa)
Okna: `RegisterMoveTextLine`, `RegisterMoveImageBox`, `RegisterMoveScaleImageBox`, `RegisterCircle`,
`RegisterRenderTarget`, `SetRenderTarget(hWnd, index)`.
Ruch: `SetMoveSpeed`, `SetMovePosition`, `MoveStart`, `MoveStop`, `GetMove`, `SetMaxScale`,
`SetMaxScaleRate` (wołać po `SetMovePosition`), `SetScalePivotCenter`; po dojściu okno woła `OnEndMove()`.
Tekst: `GetTextLineCount`, `GetLineHeight`, `SetLineHeight`, `DisableEnterToken`, stała
`TEXT_HORIZONTAL_ALIGN_ARABIC` (= prawo).
Obrazki: `ResetFrame` (+ wywołanie `OnKeyFrame(frame)` przy każdej klatce AniImageBox), `SetAniImgScale`,
`SetRenderingRectWithScale`, `LeftRightReverseImageBox`, `SetCoolTimeImageBox`, `SetStartCoolTimeImageBox`.
Przyciski: `EnableFlash`/`DisableFlash` (miga obraz „over”), `IsDisable`, `Over`, `GetButtonImageWidth/Height`,
`SetAlwaysToolTip`, `SetButtonScale`, `SetButtonDiffuseColor`, `LeftRightReverse`.
Okna: `IsRendering`, `SetWheelTopWindow(hWnd)` / `ClearWheelTopWindow(hWnd)` (okno dostaje
`OnMouseWheelButtonUp/Down()` przed innymi; zwraca True = zużyte).
Sloty: `HideSlotButton`, `IsActiveSlot`, `IsLockSlot`, `GetSlotGlobalPosition`, `GetSlotLocalPosition`,
`StoreSlotCoolTime`, `RestoreSlotCoolTime`, `SetSlotImage`, `SetSlotScale`, `SetBaseImageScale`,
`SetCorverButtonScale`, `SetSlotCoverImage`, `EnableSlotCoverImage`, `SetSecondSlotCoverImage`,
`EnableSecondSlotCoverImage`, `AppendHighLightImage`, `EnableHighLightImage`, `DisableHighLightImage`,
`SetSlotRealNumber`, `SetSlotHighlightedGreeen`, `DisableSlotHighlightedGreen`.
W odróżnieniu od Owsapa każda funkcja sprawdza typ okna (zły uchwyt = nic, a nie crash).

Różnice / uproszczenia: `TextLine` nie dzieli tekstu po `\n` (Owsap WJ_MULTI_TEXTLINE –
nie przenoszone, bo zmieniłoby wszystkie istniejące okna); `GetTextLineCount` = linie zawinięte
(limit width) + liczba `\n`, `SetLineHeight` zmienia odstęp linii zawijanego tekstu (multi-line),
`DisableEnterToken` nic nie robi. Hub `uiminigame.py` Owsapa potrzebuje modułu `ingameEventSystem`
Owsapa – u nas jest własny (`MT2009_PLUS_EVENT_MANAGER_V1`), hub trzeba podpiąć pod nasz.

## 3. Render target / Yut Nori 3D
`EterLib/RenderTargetManager.*`, `EterLib/GrpRenderTargetTexture.*` (port na Direct3D 9),
`UserInterface/PythonYutnoriManager.*`. Tekstura A8R8G8B8 w rozmiarze okna gry powstaje przy
`app.YutnoriCreate()` (nie przy starcie – błąd nie blokuje gry), zwalniana/odtwarzana przy resecie
urządzenia. Model: rasa **20505** (`npclist`: `20505 yut`, katalog `d:/ymir work/npc/yut/` z GF), kamera
`DEFAULT_YUTNORI_CAMERA`. Bez modelu `YutnoriChangeMotion` od razu zgłasza koniec ruchu, więc gra
działa (bez animacji).
