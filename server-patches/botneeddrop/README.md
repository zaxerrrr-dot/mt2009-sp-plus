# botneeddrop – potrzebny przedmiot bota bez kary poziomu w dropie (Yohara 3.x)

Znacznik: `MT2009_PLUS_BOT_NEED_DROP_V1` (decyzja właściciela z 07.11.2026: „od teraz boty mogą otrzymywać potrzebne
przedmioty na każdym lvl. Czyli nie mają capa na drop -15%”).

- `item_manager.cpp`, `ITEM_MANAGER::CreateDropItem`:
  - gdy zabójcą jest **bot**, który czegoś teraz potrzebuje (`Mt2009PlusBotNeedDropKiller`), liczony jest drugi procent
    dropu – taki, jakby potwór miał poziom bota (`GetDropPct` z poziomem potwora podniesionym do poziomu bota: bez kary
    `PERCENT_LVDELTA` / `PERCENT_LVDELTA_BOSS`, wszystkie bonusy bez zmian);
  - wiersz grupy dropu (`mob_drop_item` „drop”), pula „kill” i drop etc z mob_proto: nadal **jeden rzut na wiersz**, jak
    dotąd; jeśli rzut nie mieści się w zwykłym (osłabionym) procencie, a mieści się w pełnym i przedmiot jest potrzebny
    botowi (`Mt2009PlusBotNeedsDropItem`), przedmiot wypada. W puli „kill” taki rzut daje wylosowany przedmiot tylko wtedy,
    gdy jest potrzebny (reszta puli zostaje przy osłabionej szansie). Zawartość grupy specjalnej nie jest znana przed
    rzutem – bez zmian;
  - `Mt2009PlusBotNeedDropNote` – licznik do cenzusu botów (`BOT_PETMAT: census ... need_drops= bypassed=`).
- Co jest „potrzebne”, decyduje nakładka botów (`linux-port/overlays/playerbot/src/game/src/playerbot_petmat.h`,
  `EPlayerBotNeedKind`): na razie materiał następnego etapu ewolucji peta (strażnik peta, etap otwarty, w torbie mniej niż
  wymaga etap). Kolejne rodzaje dopisuje się tam.
- **Gracze bez zmian**: dla osoby funkcje zwracają false, a liczba wywołań `number()` na wiersz jest ta sama.
- Wyłącznik: flaga eventu `m2_bot_petmat_drop_off 1` (albo `m2_bot_petmat_off 1` – całe MT2009_PLUS_BOT_PET_MATS_V1).

Kolejność: na końcu listy łatek (po `logtrim`). Definicje funkcji są w nakładce botów (playerbot_manager.cpp przez
playerbot_petmat.h) – łatka bez nakładki się nie zlinkuje.

Linux/VPS: `python3 apply_botneeddrop.py <game/src>` (bez bliźniaka PowerShell); `gen_edits.py` odtwarza `edits.json`.
