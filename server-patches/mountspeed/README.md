# Prędkość wszystkich wierzchowców, nie tylko Magma Manni

Poprawka silnika `game/src/char_player.cpp`
(`CCharacterPlayerData::GetAllowedMovementDistance`), znacznik
`MT2009_PLUS_MOUNT_SPEED_V1`. Nakładana raz, przy przygotowaniu wydania
(`tools/port/Apply-MT2009PlusEngine.ps1`); `Apply-MountSpeedPatch.ps1`
i linuksowy bliźniak `apply_mountspeed.py` robią to samo.

## Co było nie tak

Serwer sprawdza, czy postać nie przesunęła się dalej, niż pozwala jej
prędkość. Jeźdźcowi pozwala na jeden stały dystans, liczony pod bieg konia
bojowego (vnum 20104, prędkość animacji biegu 740,67). Magma Manni
(53201–53203) biega szybciej (1159,3), więc serwer cofał jeźdźca. Na głównym
serwerze naprawiono to 16 września: dystans jest mnożony przez prędkość
animacji wierzchowca podzieloną przez 740,67. Ale tylko dla tych trzech
numerów.

Z 246 wierzchowców (kostium, podtyp mount) 98 biega szybciej niż koń
bojowy, np. Manni/Manu 1159,3, Cerber 958,8. Na każdym z nich serwer cofał
tak samo jak kiedyś na Magma Manni.

## Co robi poprawka

Ta sama korekta obejmuje każdy wierzchowiec kostiumowy (rasa wierzchowca
założona w slocie `WEAR_COSTUME_MOUNT`), i tylko poszerza limit:
wierzchowiec wolniejszy od konia bojowego zostaje przy dotychczasowym
limicie, więc dla nikogo sprawdzanie nie staje się ostrzejsze. Prędkość
bierze się z tej samej animacji biegu (`.msa`), której używa klient, więc
serwer i klient liczą ten sam dystans.
