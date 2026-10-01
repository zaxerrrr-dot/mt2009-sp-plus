# Złap Króla – dane klienta (`MT2009_PLUS_CATCH_KING_V1`)

Do dołożenia przy budowie paczek (nic tu nie jest jeszcze w paczkach):

- `item_list.add.txt` → `gamedata/item_list.txt` (CRLF): 79603, 79604 z ikonami GF, a Łupy
  50968–50970 na ikonach GF 50928–50930 (te numery są u nas Recepturami);
- `npclist.add.txt` → `npclist.txt`: `20506 king_npc`;
- `itemdesc.add.txt` → `locale/pl/itemdesc.txt` (CP1250, CRLF);
- `item_proto` klienta (5 wierszy, jak w `world.item_proto`, `apply.sh`):
  | vnum | nazwa | typ | podtyp | stack | antiflag | flag |
  |---|---|---|---|---|---|---|
  | 79603 | Karta Królewska | 18 (QUEST) | 0 | 200 | 204928 (DROP, GIVE, MYSHOP, SAFEBOX) | 4 |
  | 79604 | Talia Królewska | 18 | 0 | 200 | 204928 | 4 |
  | 50968 | Złoty Łup Królewski | 23 (GIFTBOX) | 0 | 200 | 0 | 4 |
  | 50969 | Srebrny Łup Królewski | 23 | 0 | 200 | 0 | 4 |
  | 50970 | Brązowy Łup Królewski | 23 | 0 | 200 | 0 | 4 |
- `mob_proto` klienta: 20506 „Złap Króla”, kopia NPC 20005 (typ NPC, NOMOVE);
- `assets.gf26.txt` – obrazy okna, ikony i model NPC z klienta GF 26.1.11 (sekcja „common”
  tylko tam, gdzie klientowi ich brak – nie nadpisywać naszych `ui/public`, `ui/pattern`).

Python (paczka root): `uiminigamecatchking.py`, `uiscript/minigamecatchkinggamepage.py`,
`uiscript/minigamecatchkingwaitingpage.py`, haki w `game.py` (metody okna gry wołane przez
exe, `Register()` po starcie huba eventów) i nagrody w `uiingameevent.py`; opis zasad
`locale/locale/pl/catchking_event_desc.txt`. Bez nowego exe (brak `net.SendMiniGameCatchKing`)
okno nie powstaje, a przycisk eventu mówi, że gra przyjdzie z aktualizacją.

Exe (osobny port): `net.SendMiniGameCatchKing(sub, arg)`,
`net.SendMiniGameCatchKingRequestQuestFlag()`, CG 226 {BYTE header, BYTE sub, BYTE arg} +
`SendSequence()`, GC 238 dynamiczny {BYTE header, WORD size, BYTE sub} → metody okna gry
`MiniGameCatchKingEventStart(bigScore)`, `MiniGameCatchKingSetHandCard(card)`,
`MiniGameCatchKingResultField(score, rowType, pos, value, keep, destroy, getReward, fiveNear)`,
`MiniGameCatchKingSetEndCard(pos, value)`, `MiniGameCatchKingReward(code)`,
`CatchKingFlagProcess(sub, (pieces, packs))` dla podnagłówków 5–8. Opcjonalnie
`item.ITEM_VNUM_CATCH_KING_PIECE/PACK` i `player.CATCHKING_GC_*` – python ma wartości zapasowe.
