# Cor Draconis dołącza do stosu przy podnoszeniu

Poprawka silnika `game/src/char_item.cpp` (`CHARACTER::AutoStackItem`,
`CHARACTER::AutoStackItemProto`), znacznik `MT2009_PLUS_COR_AUTOSTACK_V1`.
Nakładana raz, przy przygotowaniu wydania, po `server-patches/corstack`
(`tools/port/Apply-MT2009PlusEngine.ps1`); `Apply-CorAutoStackPatch.ps1`
i linuksowy bliźniak `apply_corautostack.py` robią to samo.

## Co było nie tak

Cor Draconis podniesiony z ziemi (albo dany graczowi) lądował w osobnym
stosie, nawet gdy gracz miał już Cory w ekwipunku. Łączenie przez
przeciągnięcie działało (`server-patches/corstack`), ale automatyczne
łączenie przy podnoszeniu i dawaniu przedmiotu dalej sprawdzało flagi proto
(`ANTI_STACK`, `STACKABLE`), które część światów ma dla Corów ustawione
po staremu.

## Co robi poprawka

Dla tych samych Corów co `corstack` podniesiony albo otrzymany Cor dołącza
do stosu tego samego Cora w ekwipunku (do 200 sztuk w stosie). Pozostałe
przedmioty bez zmian.
