# kolaprzedmioty – Kamień Rytualny z Kół ItemShopu

`MT2009_PLUS_KOLA_ITEMS_V1` (20.10.2026, decyzja właściciela: nagroda kół „Kamień Rytualny” ma być prawdziwym
przedmiotem jak na serwerze globalnym, nie zamiennikiem).

**Kamień Rytualny – 25046** (na globalu to 25042, ale u nas 25042 to Magiczny Kamień). Przedmiot dodaje
`tools/kola_items/gen_kola_items.py` (`mariadb/playerbot/kola_items.sql`, dane klienta `tools/kola_items/kola_items.json`,
ikona GF `root/icon/item/25046.tga`). Działa jak na globalu (Owsap v6.2.6 `BLESSING_STONE`, wiki):

- ulepszanie zwojem (`ITEM_USE` / `USE_TUNING`), `value0 = 1` (`NO_REDUCTION_WHEN_FAIL_SCROLL` – jak nasz Magiczny
  Kamień 25042: przy porażce przedmiot nie znika i nie traci poziomu), `value1 = 15` – +15% szansy (silnik dodaje
  `value1` i w oknie ulepszania, i przy losowaniu),
- **tylko na przedmioty powyżej 80. poziomu** (`GetLevelLimit() > 80`) – tego silnik nie miał; to jedyna zmiana kodu.

Dwie edycje `char_item.cpp`, każda ze swoim znacznikiem:

- `(ritual stone)` – `CHARACTER::RefineItem`: kamień na przedmiocie do 80. poziomu – komunikat „Kamień Rytualny działa
  tylko na przedmioty powyżej 80. poziomu.” i nic się nie dzieje,
- `(ritual stone roll)` – `CHARACTER::DoRefineWithScroll`: to samo jeszcze raz przy samym losowaniu.

Klient (`root/uiinventory.py`, `MT2009_PLUS_KOLA_ITEMS_V1`) nie podświetla przedmiotów do 80. poziomu pod kamieniem.

Linux/VPS: `python3 apply_kolaprzedmioty.py <game/src>`; Windows: `Apply-KolaPrzedmiotyPatch.ps1 -SourceDir <game/src>`
(wołane przez `tools/port/Apply-MT2009PlusEngine.ps1`, na końcu). `edits.json` pisze `gen_edits.py` (z podanym
`<game/src>` sprawdza kotwice).
