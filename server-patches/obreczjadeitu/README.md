# obreczjadeitu – linia Woli SungMa Obręczy Jadeitu

`MT2009_PLUS_JADE_BRACELET_V1` (14.10.2026, decyzja właściciela: „bransolety jadeitowe – dodać wg wiki”).

Obręcze Jadeitu (bransolety, poziom 105; pl-wiki „Obręcz Jadeitu Mgły / Słońca / Nocy / Dymu”) mają dwa bonusy
podstawowe, losowe („istnieje prawdopodobieństwo, że nie będzie żadnego z nich”): Precyzję i Wolę SungMa obręczy.
U Owsapa to `APPLY_RANDOM 5` + `6..9` (`apply_random_table`, wartości `ApplyRandomValue5/6`).

| obręcz | vnum | Wola |
|---|---|---|
| Mgły | 14580–14589 | ODP (`POINT_SUNGMA_MOVE`) |
| Słońca | 14590–14599 | INT (`POINT_SUNGMA_IMMUNE`) |
| Nocy | 14600–14609 | WIT (`POINT_SUNGMA_HP`) |
| Dymu | 14610–14619 | SIŁA (`POINT_SUNGMA_STR`) |

| Wola | +0 | +1 | +2 | +3 | +4 | +5 | +6 | +7 | +8 | +9 |
|---|---|---|---|---|---|---|---|---|---|---|
| zwykła | 1 | 3 | 5 | 7 | 9 | 11 | 13 | 15 | 18 | 21 |
| rzadka | 2 | 4 | 6 | 8 | 10 | 12 | 14 | 17 | 20 | 24 |

(= wiki: 1–2 … 21–24.)

- Linia to 6. bonus przedmiotu (`ITEM_ATTRIBUTE_RARE_START`), jak linie Talizmanów Woli (`server-patches/talizmanwoli`)
  – klient pokazuje ją w dymku jak każdy bonus.
- Nowa obręcz (drop, skrzynia, Mistrz Chi, GM `/item`): linia z szansą `will_tal_line_pct` (80%), rzadka wartość z
  szansą `will_tal_rare_pct` (10%) – flagi panelu Talizmanów Woli.
- Ulepszenie (`CopyAttributeTo`): linia przechodzi na nowy poziom w tym samym wierszu, brakująca jest dodawana.
  Przedmioty 6/7 bonusu jej nie zmieniają.
- **Precyzja** (druga linia wiki, `APPLY_HIT_PCT`) – ten silnik nie ma takiego punktu: pominięta.

Pliki: `item_attribute.cpp`, `item_manager.cpp` (8 edycji, każda ze swoim znacznikiem) – **po** patchu
`talizmanwoli` (edycje stoją obok jego kodu i używają jego funkcji szans).

- Linux/VPS: `python3 apply_obreczjadeitu.py <game/src>`; Windows: `Apply-ObreczJadeituPatch.ps1 -SourceDir <game/src>`
  (wołane przez `tools/port/Apply-MT2009PlusEngine.ps1`). `gen_edits.py` tworzy `edits.json` z kodu w nim.
- Sprawdzone: `-fsyntax-only` obu plików na drzewie serwera testowego (obraz `m2-libs:check`), 14.10.2026.
