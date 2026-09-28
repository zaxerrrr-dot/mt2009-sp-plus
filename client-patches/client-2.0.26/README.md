# Klient 2.0.26: Smoczy Skowyt na cel, Alt+1 / Alt+2 zmienia kanał

Względem klienta 2.0.25 (`client-patches/client-2.0.25`). Część serwerowa:
`server-patches/dragonroartarget` (zasięg 1800).

- `gamedata/gamedata/skilltable.txt` – Smoczy Skowyt (93) bez `SELFONLY`,
  zasięg celu 1800, jak Latający Talizman (91).
- `locale/locale/{pl,en}/skilldesc.txt` – Skowyt `ATTACK_SKILL|NEED_TARGET`
  zamiast `ATTACK_SKILL|STANDING_SKILL`: klient wymaga celu, sam podchodzi
  na zasięg i wysyła cel serwerowi.
- `root/game.py` – Alt+1 / Alt+2 przenosi od razu na kanał 1 / 2
  (`/change_channel`, jak okno zmiany kanału, z tymi samymi warunkami:
  kanał musi istnieć na liście serwera, kanał premium tylko z subskrypcją).
