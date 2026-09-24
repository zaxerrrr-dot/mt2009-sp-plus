# Cory Draconis łączą się w stosy

Poprawka silnika `game/src/char_item.cpp` (`CHARACTER::MoveItem`), znacznik
`IsStackableCorDraconisVnum`. Nakładana raz, przy przygotowaniu wydania
(`tools/port/Apply-MT2009PlusEngine.ps1`); `Apply-CorStackPatch.ps1`
i linuksowy bliźniak `apply_corstack.py` robią to samo.

Zmiana przygotowana przez Codex na serwerze testowym
(`custom-patches/cor_stack_move.patch` i `apply_cor_stack_source.sh`,
24 września) – tu przeniesiona do repozytorium i do wydania bez zmian treści.

## Co było nie tak

Nowsze dane klienta mają Cory Draconis jako przedmioty stackowane, ale proto
serwera części z nich ma jeszcze `ANTI_STACK` (albo nie ma flagi
`STACKABLE`). Serwer nie łączył więc dwóch Corów przeciągniętych na siebie
i nie pozwalał oddzielić części stosu.

## Co robi poprawka

Dla Corów 50252, 50255–50260, 51501–51510, 51541, 51548, 51549, 51562, 51569,
51576, 51583, 51590, 51597, 51604, 51611, 51618, 51625, 51632 i 76040
`MoveItem` pomija `ANTI_STACK` / brak `STACKABLE`: przeciągnięcie na ten sam
Cor łączy stos, a przesunięcie z liczbą oddziela część. Pozostałe przedmioty
bez zmian.
