# Pieczęć wierzchowca schodzi do ekwipunku po śmierci

Poprawka silnika `game/src/char_battle.cpp` (`CHARACTER::Dead`), znacznik
`MT2009_PLUS_MOUNT_DEATH_UNEQUIP_V1`. Nakładana raz, przy przygotowaniu
wydania (`tools/port/Apply-MT2009PlusEngine.ps1`);
`Apply-MountDeathPatch.ps1` i linuksowy bliźniak `apply_mountdeath.py` robią
to samo.

## Co było nie tak

Gracz, który zginął na wierzchowcu z pieczęci (slot kostiumu wierzchowca),
spadał z niego, ale pieczęć zostawała w slocie i nie dało się na nią znowu
wsiąść – trzeba było ją zdjąć i założyć jeszcze raz.

## Co robi poprawka

Przy śmierci gracza i bota pieczęć z tego slotu schodzi do ekwipunku.
Po wstaniu zakładasz ją i jedziesz dalej. Przy pełnym ekwipunku pieczęć
zostaje w slocie (jak dotąd). Bot zakłada ją z plecaka sam, gdy slot
wierzchowca jest pusty (`WearPlayerBotBoughtLook`).
