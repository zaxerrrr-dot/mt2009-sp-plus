# autohuntpass – Auto Łowy 7 / 14 dni liczone w dniach kalendarzowych

Znacznik: `MT2009_PLUS_AUTOHUNT_PASS_V1` (właściciel, 24.10.2026, runda 5b sklepu V3: bilety Auto Łowy „jak na globalu”).

- `cmd_general.cpp` (`/autohunt_target`, `/autohunt_loot`): gdy świat wymaga biletu (`m2_autohunt_item`), Auto Łowy
  działają także wtedy, gdy postać ma w ekwipunku Auto Łowy (7 dni) 72800 lub (14 dni) 72801 – przedmioty z czasem
  rzeczywistym (od zakupu); po upływie czasu silnik usuwa przedmiot i następne polecenie dostaje „AutoHuntOff item”.
- Bilet 8 h (31073) bez zmian: afekt 560 liczony w grze (`autohunt_time.quest`).

Linux/VPS: `python3 apply_autohuntpass.py <game/src>`; Windows: `Apply-AutoHuntPassPatch.ps1 -SourceDir <game/src>`
(wołane na końcu `tools/port/Apply-MT2009PlusEngine.ps1`).
