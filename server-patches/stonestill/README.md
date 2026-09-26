# Kamienie Metin stoją w miejscu

Poprawka silnika `game/src/char.cpp` (`CHARACTER::Goto`) i
`game/src/char_state.cpp` (`CHARACTER::StateBattle`), znacznik
`MT2009_PLUS_STONE_STILL_V1`. Nakładana raz, przy przygotowaniu wydania
(`tools/port/Apply-MT2009PlusEngine.ps1`); `Apply-StoneStillPatch.ps1` i
linuksowy bliźniak `apply_stonestill.py` robią to samo.

## Co było nie tak

Kamień Metin, któremu coś kazało iść (`Goto`), wchodził w stan ruchu, a z
niego w stan walki, którego kamień nie ma. W syserr pojawiało się wtedy
„Stone must not use battle state” setki razy na minutę, dopóki kamień stał.

## Co robi poprawka

`Goto` odmawia kamieniowi ruchu i raz zapisuje w syserr, z kim kamień walczył
i kto go synchronizował (żeby znaleźć przyczynę). Kamień, który mimo to
trafi w stan walki, wraca do zwykłego stanu spoczynku.
