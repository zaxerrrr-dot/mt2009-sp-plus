# rekawice – Rękawice Sung Ma i Kamienie Demonów

`MT2009_PLUS_GLOVES_V1` (14.10.2026, decyzja właściciela z „14.10 ok. 8:10”: „Rękawice Sung Ma – dodać”). Druga runda
exe Yohary (`client-patches/exe`, `MT2009_PLUS_YOHARA_EXE2_V1`). Wiki PL: „Rękawice”, „Rękawice Mocy”, „Zwinne
Rękawice”, „Pancerne Rękawice”, „Ochronne Rękawice”, „Kamień Demonów”, „Kamień Mocy”, „Twarda Skóra”, „Wzór
Rękawicy”, „Utwardzacz Skóry(+)”, „Zielona Runa SungMa”.

## Przedmioty (`yohara_gloves.sql`, `tools/ygloves/gen_ygloves.py`)

| vnum | przedmiot | Wola SungMa (6. bonus) |
|---|---|---|
| 23000–23009 | Rękawice Mocy +0…+9 | SIŁA (`POINT_SUNGMA_STR`) |
| 23010–23019 | Zwinne Rękawice +0…+9 | ODP (`POINT_SUNGMA_MOVE`) |
| 23020–23029 | Pancerne Rękawice +0…+9 | WIT (`POINT_SUNGMA_HP`) |
| 23030–23039 | Ochronne Rękawice +0…+9 | INT (`POINT_SUNGMA_IMMUNE`) |
| 28046, 28146 … 28446 | Kamień Demonów +0…+4 | losowa Wola 1 / 3 / 6 / 9 / 15 |
| 28047, 28147 … 28447 | Kamień Mocy Demonów +0…+4 | jak wyżej, 30% szans na podwójną |

- Rękawice: `ITEM_ARMOR` / `ARMOR_GLOVE` (8), `WEARABLE_GLOVE`, poziom 105, 3 puste gniazda (`socket_pct` 3), bez
  `applytype` – Wola to 6. bonus przedmiotu, losowana przy powstaniu z zakresu wiki (+0 3–7, +1 5–11, +2 9–17,
  +3 14–22, +4 19–28, +5 24–34, +6 29–40, +7 34–46, +8 39–52, +9 58–63), przy ulepszeniu przechodzi w to samo miejsce
  zakresu nowego poziomu; przedmioty 6/7 bonusu jej nie zmieniają. 5 zwykłych bonusów – `item_attr.glove`
  (`ATTRIBUTE_SET_GLOVE`; lista Owsapa: PE, WIT/INT/SIŁ/ZRE, trucizna/omdlenie/spowolnienie, kradzież PŻ/PE,
  odbicie, odporność na truciznę, ludzie, Precyzja – `yohara_gloves.sql`).
- Ulepszanie u kowala: `refine_proto` 22720–22728 = Owsap 800–808 = wiki (Utwardzacz Skóry 10…200, od +5
  Utwardzacz Skóry+, +6 Biała Perła, +7 Kamień Księżycowy, +8 Niebieska, +9 Krwawa Perła; 250 000–650 000 Yang).
- Wytwarzanie: Mistrz Chi w Dongan (quest `rekawice`): 10 Run SungMa koloru rękawic (Czerwona 31247, Liliowa 31248,
  Niebieska 31249, Zielona 31250), 25 Twardej Skóry, 5 Wzorów Rękawicy, Kamień Runiczny, 100 Gaya, 10 mln Yang,
  szansa 75%.
- **Licencja na Rękawice** (72352, misja „Aresztowanie”) – nie ma: rękawice zakłada każdy od 105. poziomu.
  Rękawice Węża (23050+, materiały Wąwozu Płn. Wiatru) – nie w tej rundzie.

## Kamienie Demonów (`METIN_SUNGMA` = 2)

- Tylko do rękawic (i do rękawic nic innego): przeciągnięcie na rękawice w ekwipunku (nie założone), wolne gniazdo.
- Szansa `glove_stone_pct` (flaga zdarzeń, domyślnie 30 – oficjalna szansa kamienia); porażka zostawia Pęknięty
  Kamień (28960 – usuwa go Księga Obróbki Kamienia albo nieudane ulepszenie, jak u kowala).
- Wola losowa spośród tych, których inne kamienie rękawic nie mają (Owsap), wartość wg poziomu kamienia (wiki „Kamień
  Mocy”: 1, 3, 6, 9, 15); Kamień Mocy Demonów – podwójna z szansą `glove_stone_double_pct` (30).
- W gnieździe zostaje liczba Owsapa `apply × 10000 + poziom × 1000 + rodzaj × 100 + wartość` (np. SIŁA +15 z Kamienia
  Demonów+4: 184 × 10000 + 4 × 1000 + 1 × 100 + 15 = 1 844 115); `CItem::ModifyPoints` daje z niej Wolę
  (`Mt2009GearSocketPoints`), dymek klienta pokazuje ikonę i nazwę kamienia z jego Wolą (`root/yoharagear.py`).
  Ulepszenie rękawic zachowuje kamienie (jak kamienie duszy).

## Silnik

| plik | edycja |
|---|---|
| `common/CommonDefines.h` | `(define)`: `#define ENABLE_GLOVE_SYSTEM` – `WEAR_GLOVE` 26 (miejsce na ekwipunek), `ATTRIBUTE_SET_GLOVE` (db czyta `item_attr.glove`), kod rękawic silnika |
| `common/item_length.h` | `(metin)`: `METIN_SUNGMA` |
| `item.cpp` | `(declare)`, `(socket points)` |
| `item_manager.cpp` | `(declare)`, `(new)` – Wola nowych rękawic |
| `item_attribute.cpp` | `(declare)`, `(refine)`, `(change rare)`, `(change rare 2)`, `(add rare)`, `(add rare 2)` |
| `char_item.cpp` | `(stone)` – `ITEM_METIN` w `UseItemEx` |

13 edycji, każda ze swoim znacznikiem (`gen_edits.py [<game/src>]` tworzy `edits.json` i sprawdza kotwice); logika:
`playerbot_yohara_gear.cpp` (nakładka). **db i game z tej samej budowy** (`ENABLE_GLOVE_SYSTEM` zmienia odczyt
`item_attr`). Po `precyzja`.

- Linux/VPS: `python3 apply_rekawice.py <game/src>`; Windows: `Apply-RekawicePatch.ps1 -SourceDir <game/src>`
  (`tools/port/Apply-MT2009PlusEngine.ps1`).

## Klient

Exe (`ENABLE_GLOVE_SYSTEM`: `item.EQUIPMENT_GLOVE` = początek wyposażenia + 26, `METIN_SUNGMA` w `player.CanAttachMetin`);
root: miejsce rękawic w oknie ekwipunku (prawa kolumna pod naszyjnikiem; przycisk Smoczych Kamieni pomniejszony
między strzałą a kolczykami), dymki rękawic i kamieni (`uitooltip.py`, `yoharagear.py`); dane klienta przedmiotów:
`client-2.0.30/tools/ygloves` (po `../yohara` i `../ymaps3`, które piszą 28046/28047 jako materiały).
