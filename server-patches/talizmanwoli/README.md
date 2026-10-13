# talizmanwoli – dwie linie bonusu Talizmanów Woli

`MT2009_PLUS_WILL_TALISMAN_V1` (13.10.2026, decyzja właściciela: „losowa druga linia bonusu jak w grze”).

Talizmany Woli (81000–81009 SIŁA, 81250–81259 ODP, 81300–81309 WIT, 81550–81559 INT) mają – jak na wiki
(„Talizman Woli SIŁA”, pl/de) – dwa bonusy podstawowe:

| linia | bonus | +0 | +1 | +2 | +3 | +4 | +5 | +6 | +7 | +8 | +9 |
|---|---|---|---|---|---|---|---|---|---|---|---|
| 1 | Wola Sung Ma talizmanu (zwykła) | 1 | 1 | 3 | 5 | 7 | 9 | 11 | 14 | 17 | 21 |
| 1 | Wola Sung Ma (rzadka) | 2 | 3 | 4 | 6 | 8 | 10 | 13 | 16 | 19 | 24 |
| 2 | Moc losowego żywiołu (zwykła) % | 1 | 2 | 3 | 4 | 5 | 6 | 7 | 8 | 9 | 15 |
| 2 | Moc losowego żywiołu (rzadka) % | 2 | 3 | 4 | 5 | 6 | 7 | 8 | 9 | 10 | 17 |

Wola: SIŁA = `POINT_SUNGMA_STR` (184), ODP = `POINT_SUNGMA_MOVE` (186), WIT = `POINT_SUNGMA_HP` (185),
INT = `POINT_SUNGMA_IMMUNE` (187). Żywioł: 178–183 (Błyskawica, Ogień, Lód, Wiatr, Ziemia, Mrok – `MT2009_PLUS_ELEMENTS_V1`).

- Linie są bonusami 6. i 7. przedmiotu (`ITEM_ATTRIBUTE_RARE_START`) – klient pokazuje je w dymku jak każdy bonus
  (nazwy 178–187 w `localeinfo_point.py`). Item_proto talizmanów nie ma już stałego bonusu (`yohara_items.sql`
  zeruje `applytype0` starych wierszy).
- Nowy talizman (drop, skrzynia, sklep, GM `/item`): każda linia jest z szansą 80% („z podstawowym bonusem lub bez
  niego”), wartość rzadka z szansą 10% („w rzadkich przypadkach do +2 Woli / do 2% mocy żywiołu w +0”), żywioł losowy.
  Flagi panelu: `will_tal_line_pct`, `will_tal_rare_pct` (0 = domyślne).
- Ulepszenie (`CopyAttributeTo`): linie przechodzą na nowy poziom w tym samym wierszu (zwykła/rzadka), a brakująca
  linia jest dodawana („talizman z mniej niż 2 bonusami otrzymuje brakujące przy ulepszaniu”). 5 zwykłych bonusów
  zostaje bez zmian.
- Przedmioty 6/7 bonusu (71051/71052, Seon-Hae) nie zmieniają tych linii (`AddRareAttribute*`/`ChangeRareAttribute*`
  odmawiają; przedmiot nie jest zużywany).

Pliki: `item_attribute.cpp`, `item_manager.cpp` (8 edycji, każda ze swoim znacznikiem). Po patchu `czempion`
(`POINT_SUNGMA_*`).

- Linux/VPS: `python3 apply_talizmanwoli.py <game/src>`; Windows: `Apply-TalizmanWoliPatch.ps1 -SourceDir <game/src>`
  (wołane przez `tools/port/Apply-MT2009PlusEngine.ps1`). `gen_edits.py` tworzy `edits.json` z kodu w nim.
