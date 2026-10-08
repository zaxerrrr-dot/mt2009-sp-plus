# Przedmioty specjalne: stałe PD – `MT2009_PLUS_NS_SPECIAL_EXP_V1`

**Autor: Digi Rasta** (paczka „nowy-system” 0.28.1, `OPIS-ZMIAN.md` pkt 2.1). Przeniesione do MT2009 PLUS jako nasz kod.

## Co daje graczowi

Pierścienie z ItemShopu, Lizak, Medal i Amulet (grupa „special” 10050 → grupy bonusów 100000–100005 w
`linux-port/docker/game/special_item_group.unique_attr.txt`, `MT2009_PLUS_UNIQUE_RING_BONUS_V1`) dają **stałe** +30% / +50%
punktów doświadczenia, jak piszą wiki i opisy przedmiotów w kliencie – zamiast szansy N% na +30% PD (średnio +9…15%).

| grupa | przedmioty | PD |
|---|---|---|
| 100000 | Pierścień Siły Woli (71148) | +30% |
| 100001 | Pierścień Śmiercionośnej Mocy (71149) | +30% |
| 100002 | Medal Bohatera (71158) | +50% |
| 100003 | Pierścień Półksiężyca (71135), Lizak Potęgi (71136) | +50% |
| 100004 | Pierścień Radości (71143) | +50% |
| 100005 | Amulet Wiecznej Miłości (71145) | +30% |

Pozostałe bonusy tych grup bez zmian. Dwa takie przedmioty naraz sumują się (np. pierścień +30% i medal +50% = +80%).

## Jak

- Dane: pierwszy wiersz każdej z sześciu grup ma punkt **127** (`POINT_RAMADAN_CANDY_BONUS_EXP`) zamiast **83**
  (`POINT_EXP_DOUBLE_BONUS`). Punkt 127 wchodzi do obu wzorów PD (`char_battle.cpp`: `rateFactor` i `iExp`) jako stałe +N% i jest
  poza limitem 100% bonusów MALL (pety, wierzchowce).
- Silnik (`edits.json`, `char.cpp`, `CHARACTER::PointChange`): punkt 127 był ustawiany (`SetPoint(type, amount)`) – zdjęcie
  przedmiotu zostawiało −N% PD, a z dwóch przedmiotów liczył się ostatni. Teraz jest sumowany jak inne bonusy
  (`SetPoint(type, GetPoint(type) + amount)`). Bez tej zmiany dane z punktem 127 nie mogą wejść.

`Apply-SpecialExpPatch.ps1` – Windows (`tools/port/Apply-MT2009PlusEngine.ps1`); `apply_specialexp.py <game/src>` – Linux/VPS;
oba czytają ten sam `edits.json`.

## Sprawdzenie w grze

Ten sam potwór bez przedmiotu i z nim: PD ×1,3 (Siła Woli, Śmiercionośna Moc, Amulet) albo ×1,5 (Medal, Półksiężyc, Lizak,
Radość); po zdjęciu przedmiotu PD wracają do zwykłych (nie niżej).

## Poza zakresem

Czas Medalu Bohatera (24 h, wiki: 7 dni), „+5% bonusu kostiumu” z nowszej wiki (silnik nie ma tego punktu), przedmioty z wiki,
których nie ma w bazie (Lizak Magii, Amulet Nazara, Czekoladowy Amulet, Amulet Strażników).
