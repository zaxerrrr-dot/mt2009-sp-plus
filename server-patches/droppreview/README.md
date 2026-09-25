# Podgląd dropu bez przedmiotów o znikomej szansie

Poprawka silnika `game/src/item_manager.cpp`
(`ITEM_MANAGER::GetPossibleMobDropItems`, okno „Możliwy drop”), znacznik
`MT2009_PLUS_DROP_PREVIEW_MIN_V1`. Nakładana raz, przy przygotowaniu wydania
(`tools/port/Apply-MT2009PlusEngine.ps1`); `Apply-DropPreviewPatch.ps1`
i linuksowy bliźniak `apply_droppreview.py` robią to samo.

## Co było nie tak

Lista pokazywała każdy przedmiot o szansie co najmniej 1 na 4 000 000
zabójstw. Wspólny drop zależy od poziomu zabójcy, więc postać na 35 poziomie
widziała przy Dzikim Psie (1 poziom) bronie +2 i bransolety +4.

## Co robi poprawka

Przedmiot ze wspólnego dropu, grupy dropu potwora, grupy rękawic złodzieja
i dropu „etc” trafia na listę tylko przy szansie co najmniej **1 na 10 000
zabójstw**. Sam drop się nie zmienia – zmienia się tylko to, co pokazuje okno.
