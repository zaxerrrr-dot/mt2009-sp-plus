# Juki konne działają także na wierzchowcu

Poprawka silnika `game/src/char.cpp` (`CHARACTER::CanUseHorseInventory`),
znacznik `MT2009_PLUS_SADDLEBAG_MOUNT_V1`. Nakładana raz, przy przygotowaniu
wydania (`tools/port/Apply-MT2009PlusEngine.ps1`);
`Apply-SaddlebagMountPatch.ps1` i linuksowy bliźniak
`apply_saddlebagmount.py` robią to samo.

## Co było

Juki konne (piąta strona ekwipunku) były dostępne tylko przy przywołanym
koniu albo w czasie jazdy na koniu.

## Co robi poprawka

Juki są dostępne także w czasie jazdy na wierzchowcu z pieczęci. Warunkiem
nadal jest posiadanie konia (poziom konia co najmniej 1).
