# Klient 2.0.25: ukrywanie kostiumów, Towarzysz „Dołącza”, 15 kont, strona „Ślub”

Względem klienta 2.0.24 (`client-patches/client-2.0.24`). Część serwerowa:
`server-patches/playerqol` (`MT2009_PLUS_COSTUME_HIDE_V1`).

- `root/uicostumehide.py` (nowy) – ustawienie „ukryte kostiumy” w
  `autohunt/kostiumy.cfg`, wysyłane na serwer po każdym wejściu do gry
  i przeniesieniu (`/kostiumy_ukryj <0|1>`) oraz po każdym kliknięciu.
  Kostiumy zostają założone i dają bonusy; wszyscy widzą zbroję i broń
  spod kostiumu, a zamiast kostiumu fryzury domyślną fryzurę postaci.
- `root/uiinventory.py` – przycisk „Ukryj kostiumy” / „Pokaż kostiumy” pod
  slotami okna kostiumów (okno wyższe o 26 px).
- `root/game.py` – synchronizacja przy wejściu do gry, odpowiedź
  `CostumeHiddenAck`.
- `root/uisidekick.py` – przycisk „Dołącza: tak/nie” w polu „Grupa” okna
  Towarzysza (`/towarzysz grupa 1|0`): dołącza do grupy właściciela także
  wtedy, gdy prowadzi ją ktoś inny. Pole `party` na końcu `SidekickInfo`
  (po `lead role leadership`); okno wyższe o 4 px.
- `root/intrologin.py` – 15 zapisanych kont (5 stron po 3, F1–F3 z widocznej
  strony).
- `root/offlineshopmanage.py` – przycisk „Auto cena” pod sugestią botów
  (domyślnie wyłączony).
- `root/uiitemshop.py` – strona „Ślub” w ItemShopie (indeksy 201–299).
