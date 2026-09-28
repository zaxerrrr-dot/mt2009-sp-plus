# Klient 2.0.26: Smoczy Skowyt na cel

Względem klienta 2.0.25 (`client-patches/client-2.0.25`). Część serwerowa:
`server-patches/dragonroartarget` (zasięg 1800).

- `gamedata/gamedata/skilltable.txt` – Smoczy Skowyt (93) bez `SELFONLY`,
  zasięg celu 1800, jak Latający Talizman (91).
- `locale/locale/{pl,en}/skilldesc.txt` – Skowyt `ATTACK_SKILL|NEED_TARGET`
  zamiast `ATTACK_SKILL|STANDING_SKILL`: klient wymaga celu, sam podchodzi
  na zasięg i wysyła cel serwerowi.
