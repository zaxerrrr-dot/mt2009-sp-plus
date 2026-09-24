# Aktywacja alchemii dla graczy

Poprawka silnika `game/src/cmd.cpp` i `cmd_gm.cpp`, znacznik
`MT2009_PLUS_DS_PLAYER_CMD_V1`. Nakładana raz, przy przygotowaniu wydania
(`tools/port/Apply-MT2009PlusEngine.ps1`); `Apply-DsCommandPatch.ps1`
i linuksowy bliźniak `apply_dscommand.py` robią to samo.

## Co było nie tak

Klient włącza zestaw kamieni alchemii komendą `/dragon_soul activate <zestaw>`
(i zdejmuje go `/dragon_soul deactivate`). W silniku ta komenda była tylko dla
GM (`GM_IMPLEMENTOR`), więc zwykły gracz dostawał „Ta komenda nie istnieje”,
a GM mógł aktywować alchemię bez problemu.

## Co robi poprawka

- `/dragon_soul` jest komendą gracza (`GM_PLAYER`), więc aktywacja
  i dezaktywacja zestawu działają dla wszystkich;
- jej dwie opcje testowe (`o` – okno ulepszania alchemii z dowolnego miejsca,
  `c` – okno zmiany bonusów) zostają tylko dla GM.

Łączenie szarf (NPC 20011, `pc.open_acce`) oraz ulepszanie i zmiana bonusów
alchemii (NPC 20001, `ds.open_refine_window` / `ds.open_changeattr_window`)
nie mają blokady dla GM; wymagają tylko kwalifikacji alchemii, którą każdy
gracz dostaje przy wejściu do gry (`server-patches/dsqualification`).
