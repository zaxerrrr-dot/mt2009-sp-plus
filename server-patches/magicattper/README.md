# Bonus peta „atak magiczny %” naprawdę działa

Poprawka silnika `game/src/char.cpp` (`CHARACTER::PointChange`), znacznik
`MT2009_PLUS_MAGIC_ATT_PER_V1`. Nakładana raz, przy przygotowaniu wydania
(`tools/port/Apply-MT2009PlusEngine.ps1`); `Apply-MagicAttPerPatch.ps1`
i linuksowy bliźniak `apply_magicattper.py` robią to samo.

Pet z bonusem `POINT_MAGIC_ATT_BONUS_PER` (131, procent ataku magicznego)
nigdy go nie dostawał: `PointChange` nie miał tego punktu i zapisywał tylko
„unknown point change type 131” (ponad tysiąc wpisów dziennie, odkąd boty
kupują pety), chociaż wzór obrażeń magicznych go czyta (`char_battle.cpp`).
Teraz jest obsługiwany jak jego bliźniak `POINT_MELEE_MAGIC_ATT_BONUS_PER`
(132), z limitem 100.
