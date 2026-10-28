# kupon100 – rzut na kupon z Metinów i bossów daje Kupon SM (100)

Znacznik: `MT2009_PLUS_DROP_COUPON_100_V1` (właściciel, 28.10.2026: „zamiast kuponu SM z dropu – kupon 100 SM”).

- `item_manager.cpp`: rzut na kupon z Metina / bossa (CONFIG `DRAGON_COIN_STONE_PERMILLE`, domyślnie 3 ‰,
  i `DRAGON_COIN_BOSS_PERMILLE`, domyślnie 50 ‰; przełącznik `MT2009_PLUS_RARE_DROP_SM`) daje Kupon SM (100) 80014
  zamiast Kuponu SM (50) 80017. Szanse bez zmian.
- Podgląd dropu potwora i wiki dropu pokazują 80014; lista podnoszenia Auto Łowów ma 80014 i nadal 80017
  (Kupon SM (50) dają inne źródła: Battle Pass, Koło Fortuny, World Boss – bez zmian).

Kolejność: na końcu, po `raremobrules`, `playerqol` i `dropwiki` (kotwiczy na ich liniach z 80017).

Linux/VPS: `python3 apply_kupon100.py <game/src>`; Windows: `Apply-Kupon100Patch.ps1 -SourceDir <game/src>`
(wołane na końcu `tools/port/Apply-MT2009PlusEngine.ps1`).
