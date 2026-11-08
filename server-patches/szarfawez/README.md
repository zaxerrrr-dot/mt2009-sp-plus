# szarfawez – bonusy bazowe broni i zbroi wężowych w szarfie

`MT2009_PLUS_SASH_SERPENT_V1` (zgłoszenie właściciela, 8.11.2026: „Bronie wężowe po absorpcji bonusów do szarfy nie dają
bonusów które są wbudowane w broń”).

**Przyczyna.** Broń wężowa (360/380/1210/2230/3250/5200/7330 +0..+15) i zbroja wężowa (21310/21330/21350/21370) nie mają
bonusów w `item_proto` (applytype0..2 = 0). Ich trzy losowe bonusy bazowe (`ysets`, pl-wiki BronieWezoweWartosci /
ZbrojeWezoweWartosci) są w `player.item_yextra` przedmiotu (bity 8-31). Absorpcja (`char.cpp RefineAcceMaterials`)
zapisuje w szarfie tylko vnum (`ACCE_ABSORBED_SOCKET`), kopiuje atrybuty i – przez `CopyAttributeTo` – yextra
(`Mt2009YSetsCopy`), ale ta odrzucała szarfę (`Mt2009YSetsTracked` = tylko części wężowe/zestawowe), więc bajty bonusów
ginęły razem z bronią; `ModifyPoints` szarfy daje tylko `aApplies` i wartości ataku/obrony wchłoniętego vnumu, a
`Mt2009YSetsItemPoints` patrzył na vnum samej szarfy. Atak bazowy, `aApplies` innych broni, atrybuty i żywioł broni
(`zywiolbroni`) szarfa dawała już wcześniej.

**Zmiana** (tylko `item.cpp` i `char.cpp`, bez nowych tabel i pakietów):

| Plik | Znacznik | Co |
|---|---|---|
| `item.cpp` | `(tracked)` | szarfa ma własny yextra (wczytywany przy ładowaniu, zapisywany przy zmianie) |
| `item.cpp` | `(helpers)` | rodzina wchłoniętej części; szarfa wchłonięta przed poprawką (bajty stracone) losuje 3 bonusy raz, dla rodzaju wchłoniętej części (jak część wężowa sprzed `ysets`), przed dodaniem punktów; czyszczenie przy odłączeniu |
| `item.cpp` | `(copy)` | absorpcja części wężowej → bity 8-31 na szarfę; łączenie szarf → nowa szarfa bierze je z pierwszej |
| `item.cpp` | `(points)`, `(points value)` | szarfa daje 3 bonusy wchłoniętej części na jej poziomie ulepszenia, każdy × % absorpcji (`CalcAcceBonus`, jak pozostałe wchłonięte linie: od 0,5 w górę, min. 1) |
| `item.cpp` | `(send all)` | wejście do gry i `/yitem`: stara szarfa z plecaka dostaje bonusy, klient je słyszy (`YITEM`) |
| `char.cpp` | `(detach)` | `CleanAcceAttr` (odłączenie): bonusy wężowe znikają z wchłoniętą częścią |

Klient (`client-patches/client-2.0.30/root`): `ysets.AppendAbsorbed` – tooltip szarfy, podgląd wyniku absorpcji i
łączenia pokazują 3 bonusy wężowe po przeliczeniu (tylko źródło; klient budowany raz na rundę).

**Nakładana jako ostatnia** (kotwice: kod `ysets` i `zywiolbroni`). Linux/VPS: `python3 apply_szarfawez.py <game/src>`;
Windows: `Apply-SzarfaWezPatch.ps1` (`tools/port/Apply-MT2009PlusEngine.ps1`, na końcu). `gen_edits.py` pisze `edits.json`
i sprawdza kotwice w drzewie testowym. Przy wdrożeniu dopisać `szarfawez` na końcu listy łatek.

## Sprawdzenie w grze

1. `/item 369` (Miecz Wężowy+9) – w tooltipie 3 losowe bonusy (kolor złoty), np. `Obrażenia ataku normalnego +13%`
   (122, rząd 0), `Szybkość ataku +20%` (17, rząd 0), `Obrażenia umiejętności +13%` (121, rząd 0).
2. Absorpcja do szarfy z 25%: podgląd i tooltip szarfy pokazują `+3%`, `+5%`, `+3%` (13 × 0,25 = 3,25 → 3; 20 × 0,25 = 5),
   obok wartości ataku 117 ((193 + 273) × 0,25 = 116,5 → 117) i atrybutów × 25%.
3. Założona szarfa: okno postaci – szybkość ataku +5 (i obrażenia normalne / umiejętności +3% w statystykach); zdjęcie
   zabiera dokładnie tyle samo. Relog / zmiana kanału – bonusy zostają (`player.item_yextra` z id szarfy).
4. Łączenie szarf (szarfa z bronią jako pierwsza) – nowa szarfa ma te same 3 linie przy nowym %.
5. Odłączenie (zwój odłączania) – linie znikają, wiersz `item_yextra` szarfy usunięty.
6. Szarfa z bronią wężową wchłoniętą przed poprawką: przy pierwszym założeniu / wejściu do gry dostaje 3 nowe
   losowe linie (log `SASH_SERPENT: sash ... had no lines - rolled ...`).
