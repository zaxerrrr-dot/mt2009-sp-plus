# Śmierć tylko zsadza z wierzchowca – pieczęć zostaje w slocie

Poprawka silnika, znacznik `MT2009_PLUS_MOUNT_DEATH_KEEP_SEAL_V2` (zgłoszenie graczy z 10 listopada 2026:
„podczas śmierci pieczęć wierzchowca wychodzi ze slotu i automatycznie traci się bonus zestawu… trzeba włożyć
pieczęć ponownie”). Nakładana raz, przy przygotowaniu wydania (`tools/port/Apply-MT2009PlusEngine.ps1`);
`Apply-MountDeathPatch.ps1` (parametr `-SourceFile` = `char_battle.cpp`, `char.cpp` obok niego) i linuksowy
bliźniak `apply_mountdeath.py <game/src>` robią to samo. Obie zmiany są sprawdzane przed zapisem.

## Co było nie tak

- V1 (`MT2009_PLUS_MOUNT_DEATH_UNEQUIP_V1`, 25 września 2026) przy śmierci przekładała pieczęć ze slotu
  wierzchowca do ekwipunku – wtedy pieczęci zostawionej w slocie nie dało się znowu dosiąść. Od
  `mountquickswap` (3 października) Ctrl+G sam przywołuje brakującego wierzchowca i na niego wsiada, więc V1
  nie była już potrzebna, a zdjęta pieczęć zabierała bonus zestawu kostiumów (wierzchowiec to część zestawu).
- Sam kod silnika w `CHARACTER::Dead` też próbował zdjąć pieczęć (`UnEquipSpecialRideUniqueItem`) – udawało mu
  się wtedy, gdy postać nie była ogłuszona w chwili śmierci – i zostawiał `AFFECT_MOUNT`.

## Co robi poprawka

- `char_battle.cpp`, `CHARACTER::Dead`: przy śmierci na wierzchowcu z pieczęci zdejmowane są tylko efekty
  jazdy (`AFFECT_MOUNT`, `AFFECT_MOUNT_BONUS` – jak przy zwykłym zsiadaniu, `CMountActor::Unmount`). Pieczęć
  zostaje w slocie, bonus zestawu zostaje. Stary przedmiot unikatowy do jazdy (UNIQUE1/2) schodzi jak dotąd.
  Blok V1 jest usuwany z już załatanego pliku.
- `char.cpp`, `CHARACTER::ReviveInvisible` (każde wskrzeszenie: w miejscu, w mieście, w lochach): gracz z
  założoną pieczęcią, bez wierzchowca obok, dostaje go z powrotem (`CheckMount`, jak przy logowaniu). Nie przy
  samym logowaniu (logowanie woła `CheckMount` później), nie przed teleportem, nie w czasie jazdy, nie na mapie
  OX (113) ani na arenie. Ctrl+G wsiada, jak po każdym zsiadaniu.
- Boty: `MountPlayerBotCostume` (playerbot_movement.h) sam przywołuje wierzchowca, gdy go nie ma – działa jak
  dotąd; pieczęć z plecaka (`WearPlayerBotBoughtLook`) nie jest już potrzebna.
