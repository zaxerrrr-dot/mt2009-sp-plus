# Dom Towarowy 2 – kupno części stosu i wyszukiwanie z polskimi literami

Silnikowa część nowej wersji Domu Towarowego (od Uxìĕ [DSO]): klient wysyłał już ilość w
`/flea_buy <właściciel> <id> <ilość> <widziana cena>` i umiał pokazać resztę stosu
(`FleaMarketStackUpdate`), ale serwer kupował tylko całe linie („Kupno czesci stosu nie jest
dostepne”). Zmiany są w `edits.json`, każda z własnym znacznikiem:

| Znacznik | Plik | Co robi |
|---|---|---|
| `MT2009_PLUS_SHOP_SEARCH_PL_V1` | `ikarus_shop_manager.cpp` | `StringToLower` zamienia też 9 polskich wielkich liter (CP1250) – nazwa zaczynająca się od „Ż”, „Ś”, „Ł”… pasuje do zapytania pisanego małymi literami (Dom Towarowy i zwykłe wyszukiwanie) |
| `MT2009_PLUS_SHOP_PART_STACK_V1 (gd lock)` | `common/tables.h` | `TSubPacketGDLockBuyItem.quantity` (0 = cała linia) |
| `MT2009_PLUS_SHOP_PART_STACK_V1 (dg buy)` | `common/tables.h` | `TSubPacketDGBuyItem`: `quantity`, `remainingCount`, `remainingYang` |
| `MT2009_PLUS_SHOP_PART_STACK_V1 (dg locked)` | `common/tables.h` | `TSubPacketDGLockedBuyItem`: `quantity`, `partYang` |
| `MT2009_PLUS_SHOP_PART_STACK_V1 (send)` | `db/src/ClientManager.h` | nowe (domyślne) parametry funkcji wysyłających |
| `… (parts)`, `(lock check)`, `(lock)`, `(locked)` | `db/src/ClientManagerIkarusShop.cpp` | blokada linii zapamiętuje kupowaną część i jej cenę; sprawdza ilość ponownie |
| `… (settle)` | `db/src/ClientManagerIkarusShop.cpp` | rozliczenie części: sprzedawca dostaje cenę części (minus podatek), linia zostaje z resztą stosu i resztą ceny (`UPDATE item SET count`, `ikashop_data`), oferty prywatne na linię są zwracane, wszystkie rdzenie dostają, co zostało |
| `… (send locked)`, `(send buy)` | `db/src/ClientManagerIkarusShop.cpp` | wypełnienie nowych pól pakietów |
| `… (decl)` | `ikarus_shop_manager.h` | nowe (domyślne) parametry |
| `… (input)` | `input_db.cpp` | przekazanie nowych pól |
| `… (buy)`, `(send)` | `ikarus_shop_manager.cpp` | `/flea_buy` z ilością mniejszą niż stos: cena części zaokrąglona w górę (jak podgląd w oknie), sprawdzenie Yang na część |
| `… (charge)`, `(pay)` | `ikarus_shop_manager.cpp` | kupujący płaci cenę części, którą policzył rdzeń bazy |
| `… (send lock)`, `(lock quantity)` | `ikarus_shop_manager.cpp` | ilość w pakiecie blokady |
| `… (recv buy)` | `ikarus_shop_manager.cpp` | kupujący dostaje część jako nowy przedmiot – do ekwipunku, a gdy ten zapełnił się w trakcie zakupu, pod nogi (własność 5 min); linia na każdym rdzeniu ma resztę stosu i ceny, goście sklepu i właściciel dostają odświeżony widok, okno Domu Towarowego – `FleaMarketStackUpdate` |

Zasady:

- Część stosu kupuje tylko Dom Towarowy (`/flea_buy`). Okno sklepu i boty kupują całe linie
  jak dotąd (ilość 0 w pakiecie = cała linia).
- Cena części = `ceil(cena * ilość / stos)`. Odmowa, gdy po zakupie reszta linii kosztowałaby
  mniej niż 1 Yang („Tego stosu nie da sie podzielic przy tej cenie - kup caly stos.”).
- Ilość większa niż stos: „W tym stosie nie ma juz tylu sztuk.” i okno dostaje aktualny stan linii.
- Bot-sprzedawca: częściowa sprzedaż trafia do jego historii (`playerbot_offline::NoteSold`
  z `partial = true`), ale linia zostaje w jego wiedzy o ladzie (`playerbot_offline_shop.h`).

Pliki:

- `Apply-ShopSearch2Patch.ps1` – Windows (`tools/port/Apply-MT2009PlusEngine.ps1`, po playerqol,
  bo kotwiczy na jego liniach blokady w `ClientManagerIkarusShop.cpp`);
- `apply_shopsearch2.py <game/src>` – Linux/VPS; oba czytają ten sam `edits.json`
  (ścieżki plików bazy i `common` są względne do `game/src`).

Zmiana pakietów GD/DG wymaga przebudowania **obu** rdzeni (game i db) – ze starym db nowy
game (i odwrotnie) źle odczyta pakiety zakupu. Klient (exe) bez zmian.
