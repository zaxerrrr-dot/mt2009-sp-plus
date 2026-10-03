# Kołczan z ItemShopu – nielimitowane strzały (MT2009_PLUS_QUIVER_V1)

Prośba właściciela (3 października): „Dodanie w item shopie kołczanu na strzały, za 100 SM na 14 dni.
Po założeniu w miejsce strzały, ninja ma nielimitowane strzały.”

**Kołczan** (vnum **8010**) to strzała (`ITEM_WEAPON` / `WEAPON_ARROW`, slot strzał) z limitem
`LIMIT_REAL_TIME` 1 209 600 s (14 dni). Silnikowy `ENABLE_QUIVER_SYSTEM` (`WEAPON_QUIVER`) zostaje
wyłączony – zmienia dwa pakiety, których klient 2.0.x nie zna. Zamiast tego regułą jest: **strzała
z limitem czasu rzeczywistego to kołczan** (zwykły stos strzał nigdy nie ma limitu czasu), więc kołczan
o innej długości to tylko nowy wiersz `item_proto`.

## Zmiany silnika (`edits.json`)

| Znacznik | Plik | Co robi |
|---|---|---|
| `MT2009_PLUS_QUIVER_V1 (helper)` | `char_battle.cpp` | `Mt2009PlusIsQuiver(item)` – strzała z limitem `LIMIT_REAL_TIME` |
| `MT2009_PLUS_QUIVER_V1 (count)` | `char_battle.cpp` | `GetArrowAndBow`: kołczan daje tyle strzał, ile prosi strzał (nie `MIN` z ilością 1); po upływie czasu (`socket0`) – 0, zanim zdarzenie wygaśnięcia go zabierze |
| `MT2009_PLUS_QUIVER_V1 (use)` | `char_battle.cpp` | `UseArrow`: kołczan nie traci strzał – ilość zostaje 1, nie schodzi ze slotu |

Każde zużycie strzały (zwykły strzał, umiejętności, strzały dodatkowe `MT2009_PLUS_ARCHER_MULTISHOT`)
idzie przez `UseArrow`, a każde sprawdzenie „czy ma strzały” przez `GetArrowAndBow`.

- `Apply-QuiverPatch.ps1` – Windows (`tools/port/Apply-MT2009PlusEngine.ps1`);
- `apply_quiver.py <game/src>` – Linux/VPS; oba czytają ten sam `edits.json`.

Zmiana już nałożona (jest jej znacznik) jest pomijana; zmiana, której kodu nie ma dokładnie raz,
przerywa całość, zanim cokolwiek zostanie zapisane.

## Reszta

- `linux-port/docker/mariadb/playerbot/apply.sh` – wiersz 8010 w `world.item_proto` (wartości Srebrnej
  Strzały: `value2` 100, `value3` 25, `value4` 1300, `value5` 2250 – zasięg i obrażenia działają, por.
  `MT2009_PLUS_ARROW_RANGE_V1`; bez progu poziomu; tylko ninja; bez wyrzucania, sprzedaży, handlu, sklepu
  i utraty przy śmierci PK; nie łączy się w stos), linia 10 sklepu w grze (`common.itemshop_items`, kategoria
  „Ekwipunek”, 100 SM) i pozycja sklepu WWW (`itemshop.ishop_items`, „Kon i pomoc”, 100 SM, ikona
  `img/item/08010.png`). Idempotentne; cena zmieniona ręcznie zostaje.
- Boty (`playerbot_gear.h`, `playerbot_economy.h`): `IsPlayerBotQuiver` – ta sama reguła; założony kołczan
  liczy się jako pełny zapas (bot nie kupuje strzał), przegląd ekwipunku go nie zdejmuje, kołczan z plecaka
  idzie przed każdym stosem, nigdy nie jest złomem. Boty go nie kupują.
- Klient: `client-patches/client-2.0.30/tools/quiver` (rekord `item_proto`, `item_list.txt`, `itemdesc.txt`,
  ikona `icon/item/08010.tga` – nowy wpis paczki `icon`).
