# Klient 2.0.27: kalendarz eventów, Battle Pass, zestawy kostiumów, pozycje okien

Względem klienta 2.0.26 (`client-patches/client-2.0.26`). Część serwerowa:
`server-patches/playerqol` (`MT2009_PLUS_EVENT_CALENDAR_V1`,
`MT2009_PLUS_BATTLE_PASS_V1`, `MT2009_PLUS_COSTUME_SET_V1`) i
`linux-port/overlays/playerbot/src/game/src/playerbot_battlepass.h`.

- `root/uiwindowpos.py` (nowy) – pozycja okien ekwipunku, postaci i kostiumów
  zapamiętywana osobno dla każdej postaci (`autohunt/okna/<nick>.cfg`).
  Podpięte w `interfacemodule.py` i `uiinventory.py`.
- `root/uieventcalendar.py` (nowy) – kalendarz eventów (F11 albo przycisk na
  pasku): eventy z harmonogramu paneli (`/kalendarz`, odpowiedź
  `EventCalBegin/EventCal/EventCalEnd`), widok tygodniowy (Pn–Nd, dzisiejszy
  dzień podświetlony, godziny i ikony eventów), na górze pasek „TRWA TERAZ” /
  „DZIŚ SĄ EVENTY!”.
- `root/uibattlepass.py`, `root/uiscript/mt2009battlepass.py` (nowe) – okno
  Battle Passa w układzie i grafikach wybranego przez operatora okna
  (`root/mt2009_ui/battle_pass/`): lista misji z ikoną, paskiem i trzema
  nagrodami, przewijanie, szczegóły misji, podsumowanie i nagroda końcowa
  (Kupon SM 50). Nagrody misji przychodzą same po ukończeniu misji.
- `root/costume_sets.py` (nowy, generowany z serwerowego
  `linux-port/docker/game/costume_sets.txt`) i `root/uitooltip.py` –
  podpowiedź „Zestaw kostiumów” z pasującymi fryzurami / kostiumami.
- `root/uiscript/taskbar.py`, `root/uitaskbar.py` – przyciski Kalendarz
  (od ok. 1004 px szerokości ekranu) i Battle Pass (od ok. 1038 px).
- `root/game.py` – F11, odpowiedzi serwera kalendarza i Battle Passa.
- `root/mt2009_ui/` – grafiki kalendarza (kafelki dni, ikony eventów) i
  przycisków na pasku.
