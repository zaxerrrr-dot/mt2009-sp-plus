# Alchemia bez misji na 30 poziom

Poprawka silnika `game/src/char_affect.cpp` (`CHARACTER::LoadAffect`),
znacznik `MT2009_PLUS_DS_QUALIFY_ON_LOGIN_V1`. Nakładana raz, przy
przygotowaniu wydania (`tools/port/Apply-MT2009PlusEngine.ps1`);
`Apply-DsQualificationPatch.ps1` i linuksowy bliźniak
`apply_dsqualification.py` robią to samo.

## Co było nie tak

Plecak alchemii działał dopiero po misji u Alchemika na 30 poziom (efekt
`AFFECT_DRAGON_SOUL_QUALIFIED`, `ds.give_qualification()`). Bez niej:

- kamień z otwartego Cor Draconis nie trafiał do plecaka alchemii, tylko
  upadał na ziemię (`GetEmptyDragonSoulInventory` zwracało -1),
- kamienia z ziemi nie dało się podnieść,
- Corów z puli 51501–51999 nie dało się w ogóle otworzyć.

## Co robi poprawka

Przy wczytaniu efektów postaci (każde wejście do gry) prawdziwy gracz bez
kwalifikacji dostaje ją tym samym wywołaniem co w misji
(`DragonSoul_GiveQualification`). Klient widzi ten sam efekt co po misji.
Boty zostają bez zmian.

Misja `dragon_soul` działa dalej: za 10 Odłamków Smoczego Kamienia daje
Cor Draconis, a potem codzienne wymiany odłamków na Cory.
