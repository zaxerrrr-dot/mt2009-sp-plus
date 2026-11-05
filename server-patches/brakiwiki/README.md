# brakiwiki – Tajemniczy Talizman i Rękawice Węża jak na wiki

`MT2009_PLUS_BRAKI_WIKI_V1` (5.11.2026, właściciel: „Dodaj zgodnie z Wiki Global” – lista
`cache/yohara/braki-yohara.md`, B9). Dane: `tools/brakiwiki/gen_brakiwiki.py` (`braki_wiki.sql`,
`game/brakiwiki/`), receptury ulepszania: `refine_global.sql` (`tools/refineglobal`, `WIKI_MATS`).

## Tajemniczy Talizman (81560–81569)

Wiki: „Tajemniczy Talizman”, „Talizmany” (tabela Talizmanów SungMa), Owsap `APPLY_RANDOM 28 / 29`
(`ApplyRandomValue28 / 29`). Dwie linie podstawowe w 6. i 7. slocie bonusów (jak Talizmany Woli):

| linia | +0 | +1 | +2 | +3 | +4 | +5 | +6 | +7 | +8 | +9 |
|---|---|---|---|---|---|---|---|---|---|---|
| Wola SungMa losowej cechy (SIŁ/WIT/ODP/INT), zwykła / rzadka | 1/2 | 1/3 | 3/4 | 5/6 | 7/8 | 9/10 | 11/13 | 14/16 | 17/19 | 21/24 |
| Moc losowego żywiołu, 11 wierszy % | 1–30 | 1–31 | 2–32 | 3–33 | 4–34 | 5–36 | 6–59 | 7–62 | 8–65 | 9–69 |

- Nowy talizman: każda linia z szansą `will_tal_line_pct` (80; wiki: „z podstawowym bonusem lub bez niego”),
  Wola – losowa cecha, wiersz rzadki z `will_tal_rare_pct` (10); żywioł – losowy, wiersz 1 (1% w +0), z
  `will_tal_rare_pct` jeden z wierszy 2–11 („w rzadkich przypadkach 1–30% w +0”).
- Ulepszenie (`CopyAttributeTo`): linie przechodzą na nowy poziom w tym samym wierszu; brakująca linia
  pojawia się z szansą `will_tal_line_pct` („mogą pojawić się po podniesieniu talizmanu”).
- Przedmioty 6/7 bonusu nie zmieniają tych linii (`AddRareAttribute*`/`ChangeRareAttribute*` odmawiają).
- 5 zwykłych bonusów – zestaw talizmanów (`ATTRIBUTE_SET_PENDANT`), jak u Talizmanów Woli.

## Rękawice Węża (23050–23089)

Obrona rękawic (wiki 15–17 … 55–57: `value1` 16 + 2 × `value5`) – pętla pancerza w `char.cpp` liczy też
`ARMOR_GLOVE` (Rękawice Sung Ma mają obie wartości 0 – bez zmian). Wola rękawic (6–9 … 69–78) – nakładka
`playerbot_yohara_gear.cpp` (`Mt2009GloveType`, `GloveWillRange`, ten sam znacznik).

## Edycje (9, każda ze swoim znacznikiem)

| plik | edycja |
|---|---|
| `item_attribute.cpp` | funkcje, `(refine)`, `(change rare)`, `(change rare 2)`, `(add rare)`, `(add rare 2)` |
| `item_manager.cpp` | `(declare)`, `(new)` |
| `char.cpp` | `(glove armour)` |

Po `talizmanwoli` i `rekawice` (kotwice to ich linie); na końcu listy (po `sesja`).

- Linux/VPS: `python3 apply_brakiwiki.py <game/src>`; Windows: `Apply-BrakiWikiPatch.ps1 -SourceDir <game/src>`
  (`tools/port/Apply-MT2009PlusEngine.ps1`). `gen_edits.py` tworzy `edits.json`.
