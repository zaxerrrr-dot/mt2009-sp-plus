# Bonusy procentowe bez limitu 100

Poprawka silnika `game/src/char.cpp` (`CHARACTER::PointChange`), znacznik `MT2009_PLUS_MALL_BONUS_NOCAP_V1`.

Silnik obcinał do 100 bonusy: atak %, obrona %, doświadczenie %, yang % oraz atak wręcz/magiczny % (ostrzeżenie
„MALL_BONUS exceeded over 100” w syserr). Decyzja właściciela (10.11.2026): bonusy mają się sumować bez limitu.
Obcięcie było też błędne – przy nakładaniu dodawało mniej, a przy zdejmowaniu odejmowało całą wartość, więc bonus
mógł spaść poniżej tego, co postać faktycznie miała. Limit zostaje tylko dla odporności na przełamanie ogłuszenia
(szansa procentowa).

Linux: `python3 apply_mallbonus.py <game/src>` (wywoływane przy budowie, ostatnie na liście).
