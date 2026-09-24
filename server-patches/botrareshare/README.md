# Cor Draconis i szarfa z podziału dropu trafiają do plecaka bota

Poprawka silnika `game/src/char_battle.cpp` (`CHARACTER::Reward`), znacznik
`MT2009_PLUS_BOT_RARE_SHARE_V1`. Nakładana raz, przy przygotowaniu wydania
(`tools/port/Apply-MT2009PlusEngine.ps1`); `Apply-BotRareSharePatch.ps1`
i linuksowy bliźniak `apply_botrareshare.py` robią to samo.

## Co było nie tak

Gdy z Metina lub bossa wypada kilka przedmiotów, silnik rozdaje własność po
kolei wszystkim postaciom, które zadały co najmniej 10% obrażeń — także
botom. Cor Draconis (albo szarfa), który przypadł botowi, leżał na ziemi
z jego nazwą: bot nie może podnieść Cora (`char_item.cpp`, `PickupItem`,
blokada przed zabieraniem Corów graczy), a gracz nie mógł go wziąć, dopóki
nie wygasła ochrona właściciela. Zdarzało się to zwłaszcza, gdy Metina bił
gracz razem z botami: wtedy Cor wypada z szansą gracza (50–80%).

## Co robi poprawka

Cor Draconis albo szarfa, które przy tym podziale przypadną botowi, trafiają
od razu do jego plecaka — tak jak drop z jego własnego zabójstwa
(`server-patches/botraredrop`, V3). Przy pełnym plecaku przepadają. Blokada
podnoszenia Corów z ziemi przez boty zostaje. Każde takie przekazanie jest
w syslogu jako `[DS_COR_DROP] share to bag`.
