# Wyszukiwarka sklepów: szukanie jednego, klikniętego przedmiotu

Poprawka do okna „Wyszukiwarka przedmiotów” (Ikarus offline shop, `SUBHEADER_CG_SHOP_SEARCH`). Przetestowana na 2.0.94 (klient 2.0.21).

## Co było nie tak

W oknie wybiera się kategorię i podkategorię (np. Rybołówstwo → Inne), a po prawej widać ikony przedmiotów z tej grupy. Ikon nie dało się kliknąć, a „Szukaj” znajdował każdy sklep, który miał cokolwiek z całej grupy. Nie dało się więc wyszukać np. samego Małża (27987).

Przyczyna:

- Klient zawsze wysyłał `ikashop.SendSearchItem(searchIndex, 0)`, czyli tylko kategorię, a drugie pole `socket0` było puste.
- Serwer w `CShopManager::RecvShopSearchItemClientPacket` traktuje `itemVnum` jako numer kategorii. Sprawdzenie `shop->HasItem(itemVnum, socket0)` było zakomentowane, więc zawsze szedł przez `SearchItemsByCategory`.

## Jak to działa po poprawce

- **Wybór przedmiotu:** klik w ikonę zaznacza przedmiot (podświetlenie slotu), a drugi klik go odznacza. Zmiana kategorii lub podkategorii czyści wybór.
- **Szukanie:** „Szukaj” z zaznaczonym przedmiotem znajduje tylko sklepy offline i stragany botów, które mają dokładnie ten przedmiot (vnum i socket0, więc przy księgach także konkretną umiejętność). Bez zaznaczenia szuka całej kategorii, tak jak dotąd.
- **Podświetlenie w sklepie:** po wejściu do znalezionego sklepu podświetla się tylko wybrany przedmiot (`OFFLINESHOP_LAST_SEARCHED_ITEMS`).

**Struktura pakietu się nie zmienia.** Wybrany przedmiot jedzie w polu `socket0` jako `vnum * 1000 + socket0 przedmiotu`, a `0` oznacza całą kategorię. Dzięki temu:

- stary klient z nowym serwerem szuka po staremu,
- nowy klient ze starym serwerem też szuka po staremu, bo serwer ignoruje to pole,
- nie trzeba ruszać C++ klienta (`ikashop.SendSearchItem` już przyjmuje dwa inty).

Serwer sprawdza wybrany vnum przez `ITEM_MANAGER::GetTable` i odrzuca pakiet z nieistniejącym przedmiotem. Wszystkie limity (cooldown 10 s, zasięg 7500, 400 wyników, flood check) zostają bez zmian.

## Pliki

- `server-ikarus_shop_manager.patch`: `game/src/ikarus_shop_manager.cpp`, 26 linii, plik ma końcówki CRLF.
- `client-offlineshopsearch.patch`: `root/offlineshopsearch.py`, plik ma końcówki CRLF.

Obie łatki są w formacie `diff -u` ze ścieżkami `a/...` i `b/...`. Nakłada się je komendą `patch -p1`: dla serwera z katalogu z `game/src`, dla klienta z katalogu, w którym jest rozpakowany `root`.

## Zmiany w serwerze (`ikarus_shop_manager.cpp`)

1. `PlayerBotSearchStalls(...)` dostaje dwa opcjonalne parametry `DWORD selectedVnum = 0, int selectedSocket0 = 0`. Przy wybranym przedmiocie stragan pasuje przez `view.HasItem(selectedVnum, selectedSocket0)`, a bez wyboru jak dotąd przez `PlayerBotMatchShopCategory`.
2. W `RecvShopSearchItemClientPacket`, zaraz po sprawdzeniu `itemVnum >= SHOP_SEARCH_CATEGORY_MAX * SHOP_CATEGORY_MAX_SUB`, dochodzi dekodowanie:
   ```cpp
   DWORD selectedVnum = 0;
   int selectedSocket0 = 0;
   if (socket0 > 0)
   {
       selectedVnum = static_cast<DWORD>(socket0 / 1000);
       selectedSocket0 = socket0 % 1000;
       if (!ITEM_MANAGER::instance().GetTable(selectedVnum))
           return false;
   }
   ```
3. Pętla po sklepach offline zmienia warunek:
   ```cpp
   if (selectedVnum != 0 ? !shop->HasItem(selectedVnum, selectedSocket0)
           : !SearchItemsByCategory(itemVnum, shop))
       continue;
   ```
4. Wywołanie `PlayerBotSearchStalls(ch, itemVnum, m_shopSearchFilters, foundShops, selectedVnum, selectedSocket0);`.

## Zmiany w kliencie (`root/offlineshopsearch.py`)

1. `search_category(category, sub_category=-1, isSearchAttr=False, selectedItem=None)`. Gdy `selectedItem` (krotka `(vnum, socket0)`, socket0 w zakresie 0-999) jest podany, wysyła `ikashop.SendSearchItem(searchIndex, vnum * 1000 + socket0)`, a do `constInfo.OFFLINESHOP_LAST_SEARCHED_ITEMS` trafia tylko ten przedmiot.
2. `ShopSearchWindow`:
   - pole `self.selectedItemIndex = -1`,
   - `SetSelectItemSlotEvent` i `SetUnselectItemSlotEvent` na `ItemSlot` wskazują na `__OnSelectItem`,
   - `__RefreshCategoryItems` gasi wszystkie sloty (`DeactivateSlot`) i zapala wybrany (`ActivateSlot`),
   - nowe `__OnSelectItem(index)` przełącza wybór, a `__GetSelectedItem()` zwraca `(vnum, socket0)` albo `None` (zawsze `None` dla kategorii broni, zbroi i biżuterii, bo tam siatka jest ukryta),
   - `__OnClickCategory` i `__OnClickSubCategory` zerują wybór,
   - `__OnSearch` przekazuje `self.__GetSelectedItem()`.

Uwaga: listy przedmiotów klienta (`SHOP_SEARCH_FILTERS`) i serwera (`PrepareShopSearchFilters`) nie są identyczne (np. przy księgach klient ma 5 pozycji, a serwer 6). Dlatego poprawka wysyła sam vnum i socket0, a nie numer pozycji na liście.

## Test

1. Rybołówstwo → Inne → klik w Małża → Szukaj: znajduje tylko sklepy i stragany z małżem.
2. Drugi klik w Małża (odznaczenie) → Szukaj: znajduje wszystko z „Inne”, jak dawniej.
3. Księgi → dowolna podkategoria → klik w konkretną księgę → Szukaj: znajduje tylko księgę tej umiejętności.
