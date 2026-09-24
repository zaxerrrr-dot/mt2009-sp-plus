# Wierzchowce bez limitu czasu nie są „wygasłe”

Poprawka silnika `game/src/MountSystem.cpp` (`MountItem_GetRemainingSeconds`),
znacznik `MT2009_PLUS_MOUNT_PERMANENT_V1`. Nakładana raz, przy przygotowaniu
wydania (`tools/port/Apply-MT2009PlusEngine.ps1`); `Apply-MountPermanentPatch.ps1`
i linuksowy bliźniak `apply_mountpermanent.py` robią to samo.

## Co było nie tak

Serwer liczy czas jazdy z `socket0` pieczęci: przy pierwszym użyciu albo przy
stworzeniu przedmiotu z limitem `LIMIT_REAL_TIME` /
`LIMIT_REAL_TIME_START_FIRST_USE` silnik wpisuje tam datę wygaśnięcia.
Pieczęcie bez takiego limitu w `item_proto` nigdy jej nie dostają (`socket0`
= 0), a `0` było traktowane jak „wygasła”. Nowa pieczęć od razu pisała
„Ta pieczec wierzchowca juz wygasla.” i nie dało się na niej jeździć.

Dotyczy 9 pieczęci: Dzik, Wilk, Tygrys i Lew (niebieskie, 71115–71121),
Biały Lew (71124), Dzik Wojenny, Wilk Wojenny, Szarżujący Tygrys i Waleczny
Lew (71125–71128). Pozostałe wierzchowce mają limit czasu i działają jak dotąd.

## Co robi poprawka

Pieczęć, której proto nie ma limitu czasu rzeczywistego, jest bezterminowa:
jazda i bonusy pieczęci trwają bez końca (`INFINITE_AFFECT_DURATION`), aż do
zsiadania. Pieczęcie z limitem działają bez zmian.
