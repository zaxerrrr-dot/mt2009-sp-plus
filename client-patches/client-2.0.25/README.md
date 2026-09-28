# Klient 2.0.25: ukrywanie kostiumów

Względem klienta 2.0.24 (`client-patches/client-2.0.24`). Część serwerowa:
`server-patches/playerqol` (`MT2009_PLUS_COSTUME_HIDE_V1`).

- `root/uicostumehide.py` (nowy) – ustawienie „ukryte kostiumy” w
  `autohunt/kostiumy.cfg`, wysyłane na serwer po każdym wejściu do gry
  i przeniesieniu (`/kostiumy_ukryj <0|1>`) oraz po każdym kliknięciu.
  Kostiumy zostają założone i dają bonusy; wszyscy widzą zbroję i broń
  spod kostiumu.
- `root/uiinventory.py` – przycisk „Ukryj kostiumy” / „Pokaż kostiumy” pod
  slotami okna kostiumów (okno wyższe o 26 px).
- `root/game.py` – synchronizacja przy wejściu do gry, odpowiedź
  `CostumeHiddenAck`.
