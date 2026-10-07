# System pasów (Pasy) – `MT2009_PLUS_BELTS_V1`

**Autor: Digi Rasta** (paczka „nowy-system” v0.27.0–0.28.0, karta `SYSTEMY/pasy.md`). Przeniesione do MT2009 PLUS
jako nasz kod – bez haków `zastosuj.py`: silnik tutaj (`edits.json`), dane serwera w `linux-port/docker/game`,
klient w `client-patches`.

## Co daje graczowi

- **Pasy 18000–18089** (9 rodzin, w bazie od dawna) zakłada się w polu pasa w ekwipunku (`MT2009_PLUS_BELT_SLOT_V1`).
- **Ekwipunek pasa 4×4** (okno przy ekwipunku – nowe exe z `ENABLE_NEW_EQUIPMENT_SYSTEM`): mikstury i pieczone ryby
  pod ręką. Ile pól jest otwartych, zależy od stopnia pasa (`value0` 0–7, rośnie z ulepszeniem u Kowala): +0 – żadne, +1 – 1 pole,
  Lniany/Skórzany +9 – 6 pól, pasy 103+ +9 – 16 pól. Pasa z przedmiotami w środku nie da się zdjąć.
- **Wytwarzanie u Mistrza (20082)** – nowy NPC przy Kowalu w M1 i M3 każdego królestwa, opcja „Wytwarzanie pasów”
  → okno kostki z 9 recepturami (`cube.pasy.txt`, przepisane z oficjalnego `cube.txt`, gdzie stały u Yu-Hwana i
  Jae-Seon Kima, których kostki żaden quest nie otwiera).
- **Odłamki Energii (51001)** – u Alchemika (20001): przedmiot od 35 poziomu (broń bez strzał, zbroja, biżuteria)
  przeciągnięty na NPC przez gracza od 35 poziomu rozkłada się na 0–15 odłamków (oficjalne tabele,
  `quest/energia_alchemik.quest`).
- **Kamienie Płomienia (30524) i Lodowego Płomienia (30525)** – Skrzynia Razadora / Nemere: nowa pozycja 60%
  (grupy 951101 / 951102 w `special_item_group.dungeons.txt`): 2× kamień (40), 10× Odłamek (50), Pas Lniany+0 (10).
- Ulepszanie pasów u Kowala – oficjalne `refine_proto`, bez zmian.

## Zmiana silnika (`edits.json`)

| Znacznik | Plik | Co robi |
|---|---|---|
| `MT2009_PLUS_BELTS_V1 (belt potions)` | `belt_inventory_helper.h` | `CanMoveIntoBeltInventory`: oprócz `ITEM_USE` (mikstury, `USE_ABILITY_UP`) także `ITEM_POTION` (zielone/fioletowe mikstury, część ryb) i pieczone ryby 27863–27883 |

Reszta serwera pasa (zakładanie do `WEAR_BELT`, pola `BELT_INVENTORY_SLOT_START` 287–302, blokada zdjęcia) jest
w silniku od zawsze; numery pól są takie same w exe (`c_Belt_Inventory_Slot_Start` = 225 + 32 + 12 + 18).

- `Apply-PasyPatch.ps1` – Windows (`tools/port/Apply-MT2009PlusEngine.ps1`, po `digirasta-fixes`);
- `apply_pasy.py <game/src>` – Linux/VPS; oba czytają ten sam `edits.json`.

Zmiana już nałożona (jest jej znacznik) jest pomijana; zmiana, której kodu nie ma dokładnie raz, przerywa
całość, zanim cokolwiek zostanie zapisane.

## Poza zakresem

Kryształ Energii (51002, exe nie ma `ENABLE_ENERGY_SYSTEM`), kostka Jae-Seon Kima (63 inne receptury), pasy z
Turmalinu/Tytanowe (nie ma ich w bazie), wytwarzanie pasów przez boty (boty zakładają pasy, które mają – jak każdy
inny element wyposażenia).
