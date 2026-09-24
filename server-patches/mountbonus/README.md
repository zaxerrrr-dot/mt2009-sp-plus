# Bonusy wierzchowca naliczane raz, a nie przy każdej jeździe

Poprawka silnika `game/src/MountSystem.cpp` (`CMountActor::Mount`), znacznik
`MT2009_PLUS_MOUNT_BONUS_ONCE_V1`. Nakładana raz, przy przygotowaniu wydania
(`tools/port/Apply-MT2009PlusEngine.ps1`); `Apply-MountBonusPatch.ps1`
i linuksowy bliźniak `apply_mountbonus.py` robią to samo.

## Co było nie tak

Przy wsiadaniu silnik zdejmował stare bonusy pieczęci wierzchowca
(`AFFECT_MOUNT_BONUS`) tylko przez `Unmount()`, a ta nic nie robi, gdy postać
już nie jest uznawana za siedzącą na wierzchowcu. Kto stracił siodło inaczej
niż przez zsiadanie (śmierć, teleport), zachowywał bonusy, a każde kolejne
wsiadanie dokładało następny komplet — np. Tygrys Śniegu (+30%
doświadczenia) aż do limitu 100% („MALL_BONUS exceeded over 100” w syserr).
Wyszło na botach, które wsiadają i zsiadają co chwilę, ale dotyczyło też
graczy.

## Co robi poprawka

Przed nałożeniem bonusów pieczęci silnik zawsze zdejmuje poprzednie, więc
bonusy wierzchowca są liczone dokładnie raz.
