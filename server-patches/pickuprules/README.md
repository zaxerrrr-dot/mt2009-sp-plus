# Filtr podnoszenia – dokładne reguły rodzaju (Autor: Vekirion)

Poprawka silnika z paczki Vekiriona „Sklepy offline i filtr podnoszenia” (13–15 października 2026),
znaczniki `MT2009_PLUS_PICKUP_RULES_V1` i `MT2009_PLUS_PICKUP_SYNC_V1` (każda zmiana ma własny
dopisek w nawiasie). Nakładana raz, przy przygotowaniu wydania (`tools/port/Apply-MT2009PlusEngine.ps1`,
po `auctionhouse`; kotwiczy na liniach filtra z `server-patches/playerqol`). `Apply-PickupRulesPatch.ps1`
i linuksowy bliźniak `apply_pickuprules.py <game/src>` czytają ten sam `edits.json`.

| Znacznik | Plik | Co |
|---|---|---|
| `MT2009_PLUS_PICKUP_RULES_V1 (rules)` | `char_item.cpp` | `Mt2009PlusPickupKindOf` (rodzaj po typie/podtypie), reguły gracza (do 40; przedmioty, ulepszenie, poziom, liczba bonusów, warunki bonusów: wszystkie / dowolny / co najmniej N, „brak lub powyżej” – `MT2009_PLUS_PICKUP_COND_ABSENT_V1`, „inne bonusy” – `MT2009_PLUS_PICKUP_OTHER_BONUSES_V1`), `/pickup_rules begin/add/items/end/clear`, `/pickup_items` (wyszukiwarka przedmiotów rodzaju), a w `Mt2009PlusPickupFilterAllows` rodzaj z regułami bierze tylko to, co pasuje do którejś z nich. `MT2009_PLUS_PICKUP_SYNC_V1`: rodzaje, dla których klient ma reguły, czekają na ziemi, aż reguły dojdą (logowanie, teleport). |
| `MT2009_PLUS_PICKUP_SYNC_V1 (fifth arg)` | `cmd_general.cpp` | 5. pole `/pickup_filter` – rodzaje z regułami |
| `MT2009_PLUS_PICKUP_RULES_V1 (commands)` | `cmd_general.cpp` | `do_pickup_rules` („PickupRulesAck N”), `do_pickup_items` |
| `(cmd declare)`, `(cmd table)` | `cmd.cpp` | deklaracje i wpisy komend |
| `MT2009_PLUS_PICKUP_SYNC_V1 (unthrottled)` | `cmd.cpp` | `pickup_filter` i `pickup_rules` poza limitem komend – limit gubił „/pickup_rules end” |

Reguły trzymane w pamięci po id postaci (jak sam filtr); klient (`uipickupfilter.py`,
`uipickupfilterrules.py`) wysyła je po każdym logowaniu i teleporcie. Działa dla Z, peta, Auto Łowów
i towarzysza (`Mt2009PlusPickupFilterAllows`). Stary klient nie wysyła reguł – nic się nie zmienia.
