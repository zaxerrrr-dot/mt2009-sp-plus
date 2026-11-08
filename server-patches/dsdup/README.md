# dsdup – Smocze Kamienie: bonusy dodatkowe bez powtórzeń

Znacznik: `MT2009_PLUS_DS_DISTINCT_ATTR_V1` (zgłoszenie gracza z 8.11.2026: po Smoczym Płomieniu (100700/100701,
`MATERIAL_DS_CHANGE_ATTR`) Mityczny Ametyst miał dwa razy „Siła w walce z kamieniami Metin +4%”).

## Przyczyna
`DSManager::DoChangeAttribute` czyści kamień przez `CItem::ClearAttribute()`, które zeruje tylko sloty 0–4
(`MAX_NORM_ATTR_NUM` = 5). Kamień legendarny/mityczny ma `add_max` 3, więc trzeci bonus dodatkowy leży w slocie 5
(indeks 5 = 6. bonus). Po przelosowaniu na 0–2 bonusy dodatkowe stary slot 5 zostawał obok nowych – przy tym samym typie
bonus był dwa razy (dla Ametystu z 4 bonusami dodatkowymi: 18,75% przelosowań, gdy slot 5 był już zajęty).
`MakeDistinctRandomNumberSet` sam w sobie nie daje powtórzeń (harness: 10 mln losowań na n = 1..3, 0 duplikatów;
`fnumber(0, range)` sprawdzony dla wszystkich 2^31−2 wyjść silnika – zawsze `< range`).

## Poprawka
- `PutAttributes` czyści wszystkie 7 slotów przed losowaniem (każda ścieżka: przelosowanie, nowy kamień, naprawa).
- `MakeDistinctRandomNumberSet`: zawsze coś wybiera, nigdy nie powtarza indeksu, fallback na ostatni niewybrany.
- twarda blokada w `PutAttributes`: bonus dodatkowy równy podstawowemu lub wcześniejszemu dodatkowemu jest
  dolosowywany z pozostałych (wagi z tabeli), wpis `[DS_ATTR] ... repeats a bonus` w syslogu.
- `playerbot_pvpfan.h` (overlay): zestaw PvP czyści też sloty 5–6 przed wpisaniem bonusów zestawu.

## Naprawa istniejących kamieni
Przy wczytaniu postaci (`input_db.cpp ItemLoad`) i magazynu (`char.cpp`) kamień z powtórzonym bonusem dodatkowym
dostaje powtórzony bonus przelosowany na typ, którego nie ma (wagi i wartość z tabeli kamienia, `DSStoneTable`),
zanim zostanie założony. Pierwszy z powtórzonych zostaje, reszta kamienia bez zmian. Wpis
`[DS_ATTR] RepairDuplicateAttributes` w syslogu. Domyślnie WŁĄCZONA; wyłączenie: flaga `m2_ds_dup_repair_off 1`.

Kolejność: po `bonusyglobal` (`DSStoneTable`) – na końcu listy w `yohara-deploy.sh`.
