# Złap Króla (Catch the King) – `MT2009_PLUS_CATCH_KING_V1`

Mini gra Owsapa (v6.2.6, `minigame_catchking.cpp`, wariant z kartami w flagach questów)
podłączona do menedżera eventów (`server-patches/eventmanager`). Cała logika gry jest w
nakładce `linux-port/overlays/playerbot/src/game/src/playerbot_catchking.h` (dołączonej do
`playerbot_manager.cpp`); tu są tylko zmiany plików silnika, opisane w `edits.json`:

| Znacznik | Plik | Co robi |
|---|---|---|
| `MT2009_PLUS_CATCH_KING_V1 (cg header)` | `packet.h` | `HEADER_CG_MINI_GAME_CATCH_KING = 226` |
| `MT2009_PLUS_CATCH_KING_V1 (gc header)` | `packet.h` | `HEADER_GC_MINI_GAME_CATCH_KING = 238` |
| `MT2009_PLUS_CATCH_KING_V1 (packet)` | `packet.h` | struktury Owsapa: `TPacketCGMiniGameCatchKing` (3 B), `TPacketGCMiniGameCatchKing` (4 B), `…Result` (11 B), `…SetEndCard` (2 B), `…QuestFlag` (4 B) |
| `MT2009_PLUS_CATCH_KING_V1 (size)` | `packet_info.cpp` | rozmiar CG 226 (z bajtem sekwencji, jak wysyła klient Owsapa) |
| `MT2009_PLUS_CATCH_KING_V1 (input)` | `input_main.cpp` | `case HEADER_CG_MINI_GAME_CATCH_KING` → `CatchKingProcess` |
| `MT2009_PLUS_CATCH_KING_V1 (drop)` | `item_manager.cpp` | `CreateQuestDropItem`: karta za część zabójstw w czasie eventu (`CatchKingOnKill`) |
| `MT2009_PLUS_CATCH_KING_V1 (logout)` | `char.cpp` | `CHARACTER::Disconnect`: gra przerwana wylogowaniem / teleportem kończy się z punktami, Łup czeka na następne wejście (`CatchKingOnDisconnect`) |
| `MT2009_PLUS_CATCH_KING_V1 (declare)`, `(lua)`, `(table)` | `questlua_game.cpp` | `game.get_catchking_score(total)`, `game.get_catchking_myscore(total)`, `game.catchking_claim_reward()`, `game.catchking_use_item(vnum)`, `game.catchking_deliver()` |

- `Apply-CatchKingPatch.ps1` – Windows (`tools/port/Apply-MT2009PlusEngine.ps1`, po
  eventmanager, bo kotwiczy na jego liniach w `packet.h`);
- `apply_catchking.py <game/src>` – Linux/VPS; oba czytają ten sam `edits.json`.

Zmiana już nałożona (jest jej znacznik) jest pomijana; zmiana, której kodu nie ma dokładnie
raz, przerywa całość, zanim cokolwiek zostanie zapisane.

## Gra

- Event `catchking` z harmonogramu paneli (flaga Owsapa `mini_game_catchking`, NPC 20506 na
  mapach 1/21/41, 7-dniowe okno nagród `mini_game_catchking_reward` – `playerbot_ingame_events.h`).
- Karty: każde zabójstwo potwora lub metina przez gracza (nigdy bota) w czasie eventu losuje
  kartę (`mini_game_catchking_drop`, 100 = 1 % przy pełnym dropie, jak u Owsapa); 25 kart = Talia
  Królewska, najwyżej 999 talii (flagi `minigame_catchking.piece_count` / `pack_count`).
  Karta Królewska 79603 i Talia Królewska 79604 jako przedmioty też dodają kartę / talię.
- Gra: 1–5 talii i 30 000 yang za talię; serwer tasuje pole, wydaje karty, liczy punkty i
  sprawdza każde kliknięcie. 10–399 pkt: Brązowy Łup (50970), 400–549: Srebrny (50969), 550+:
  Złoty (50968) – po jednym na postawioną talię (`special_item_group.catchking.txt`).
- Ranking: `player.minigame_catchking` (sezon, pid; najlepszy i łączny wynik), sezon = flaga
  `mini_game_catchking_season` pisana przez rdzeń lidera. Po evencie przez 7 dni pierwsza
  dziesiątka (łączne punkty) odbiera przy stole Złote Łupy 10/5/3/1, raz na sezon.
- Karty, talie i rekord gracza należą do sezonu – przepadają, gdy zacznie się następny event.

## Poprawione względem Owsapa

Wynik poniżej 10 punktów blokował grę do relogu; nagrody nie dało się odebrać po końcu eventu
(talie i yang przepadały); wylogowanie w trakcie gry zabierało wszystko; „5 obok 5” liczyło też
odkrytą piątkę; SQL po nazwie postaci w `log.catck_king_event`; komunikat „999 talii” przy każdym
zabójstwie; nagroda za ranking była tylko opisana. Nieproszony pakiet GC 238 (karta z zabójstwa)
idzie tylko do klienta, który już wysłał CG 226 – stary exe nie zna nagłówka.

Quest: `linux-port/docker/game/quest/minigame_catchking.quest`; baza: `apply.sh`
(`MT2009_PLUS_CATCH_KING_V1`); klient: `client-patches/client-2.0.30` (`uiminigamecatchking.py`,
`uiscript/minigamecatchking*.py`, `catchking/`).
