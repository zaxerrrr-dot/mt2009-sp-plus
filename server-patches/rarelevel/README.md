# Cor Draconis i szarfy tylko z potworów w zasięgu poziomu

Poprawka silnika `game/src/item_manager.cpp` (`ITEM_MANAGER::CreateDropItem`),
znacznik `MT2009_PLUS_RARE_LEVEL_V1`. Nakładana raz, przy przygotowaniu
wydania (`tools/port/Apply-MT2009PlusEngine.ps1`), po `botraredrop`;
`Apply-RareLevelPatch.ps1` i linuksowy bliźniak `apply_rarelevel.py` robią
to samo.

## Co było nie tak

Drop Cor Draconis (Metin 50%, boss 80%) i szarfy (boss 80%) nie patrzył na
poziom: postać na 90 poziomie rozbijała Metina 5 poziomu i dostawała szarfę.

## Co robi poprawka

Cor i szarfa wypadają tylko wtedy, gdy Metin albo boss ma **najwyżej 15
poziomów mniej** niż zabójca (`poziom zabójcy <= poziom potwora + 15`).
Potwór wyższy od zabójcy daje drop bez ograniczenia. Dotyczy graczy i botów;
szanse się nie zmieniają. Szarfy ze skrzyń bossów (otwierane przedmiotem,
nie zabiciem) bez zmian.
