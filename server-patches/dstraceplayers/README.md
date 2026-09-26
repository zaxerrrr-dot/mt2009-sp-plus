# Diagnostyka zakładania kamieni alchemii tylko dla graczy

Poprawka silnika `game/src/char_item.cpp` (`CHARACTER::EquipItem`), znacznik
`MT2009_PLUS_DS_TRACE_PLAYERS_V1`. Nakładana raz, przy przygotowaniu wydania
(`tools/port/Apply-MT2009PlusEngine.ps1`); `Apply-DsTracePlayersPatch.ps1`
i linuksowy bliźniak `apply_dstraceplayers.py` robią to samo.

## Co było nie tak

Silnik zapisywał do syserr osiem linii diagnostyki (`[DS_EQUIP_TRACE]`) przy
każdym założeniu kamienia alchemii. Boty zakładają kamienie przez cały dzień,
więc te linie zasypywały syserr.

## Co robi poprawka

Diagnostyka działa dalej dla graczy, a dla botów jest wyłączona.
