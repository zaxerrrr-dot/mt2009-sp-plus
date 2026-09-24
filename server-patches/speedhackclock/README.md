# Kontrola speedhacka odporna na skoki zegara Dockera

Poprawka silnika `game/src/input_main.cpp` (`CInputMain::Move`), znacznik
`MT2009_PLUS_SPEEDHACK_CLOCK_V1`. Nakładana raz, przy przygotowaniu wydania
(`tools/port/Apply-MT2009PlusEngine.ps1`); `Apply-SpeedHackClockPatch.ps1`
i linuksowy bliźniak `apply_speedhackclock.py` robią to samo.

## Co było nie tak

Serwer porównuje czas ruchu z klienta ze swoim zegarem. Jeśli ruch jest „z
przyszłości” o więcej niż 2% czasu od ostatniej synchronizacji (po 7 s to
~150 ms), zapisuje `SPEEDHACK: DETECTED!` i po 3 s rozłącza gracza – bez
komunikatu, klient wraca do ekranu logowania.

U gracza, którego zegar maszyny wirtualnej Dockera (WSL2) chodzi ~8% za
szybko i co kilkanaście sekund jest cofany o 2–3 s, każdy ruch po takim
cofnięciu był „z przyszłości” o ~1,5 s: wyrzucało go co pół minuty, w
dowolnym miejscu (zgłoszenie 24 września, `SPEEDHACK: DETECTED! ...
(delta -1500 7303)`).

## Co robi poprawka

Dodaje 5 s zapasu: rozłączenie dopiero, gdy ruch wyprzedza serwer o ponad
2% + 5 s. Skoki zegara maszyny wirtualnej mieszczą się w zapasie; prawdziwy
speedhack (gra przyspieszona o dziesiątki procent) wyprzedza serwer
szybciej i dalej jest wykrywany. Sprawdzenie „za wolnego zegara” (30 s)
bez zmian.

Zegar maszyny wirtualnej trzeba i tak naprawić po stronie komputera
(`wsl --update`, aktualny Docker Desktop) – jego skoki psują też boty
(masowe resety przez strażnika bezczynności).
