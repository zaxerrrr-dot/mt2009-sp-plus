# g0bind – przedmioty przypisane do konta (pakiet G0 botów)

`MT2009_PLUS_ITEM_ACCOUNT_BOUND_V1` (właściciel, 22.10.2026: „Sprzęt z pakietu jest przypisany do konta: bot może go
ulepszać, ale nie może wyrzucić, przekazać w handlu ani sprzedać graczom – może sprzedać tylko innym botom”).

Silnik nie miał działającego mechanizmu przypisania (soulbind/`IsSealed` jest tylko pod `#ifdef`, wyłączony), więc
łatka dodaje flagę na **egzemplarzu** przedmiotu:

- `item.h` / `item.cpp`: `CItem::IsAccountBound()` / `SetAccountBound()` (pole `m_bAccountBound`, zerowane
  w `Initialize`); `GetAntiFlag()` dla takiego przedmiotu dokłada `ITEM_ANTIFLAG_DROP | GIVE | SELL | MYSHOP |
  PKDROP` – więc wyrzucenie, okno handlu, sprzedaż u kupca, upuszczenie po śmierci i wszystkie ścieżki botów, które
  pytają `item->GetAntiFlag()`, odmawiają; `#define MT2009_PLUS_ITEM_ACCOUNT_BOUND_V1` dla nakładki;
- `char_shop.cpp` (`CheckItem` – sklep offline Ikarusa i stragan botów) i `ikarus_shop_manager.cpp` (aukcja): flagi
  egzemplarza zamiast flag protokołu;
- `shop.cpp` (`CShop::SetShopItems`): stary stragan pomija przedmiot przypisany;
- `item_attribute.cpp` (`CopyAttributeTo`): ulepszenie (nowy przedmiot) dziedziczy przypisanie, wiersz w bazie idzie
  za nowym id (`Mt2009AccountBoundCarry`).

Zapis i odczyt: `playerbot_yohara_g0.cpp` (nakładka) – tabela `player.item_account_bound` (id przedmiotu, pid, vnum,
powód, data; tworzona przez rdzeń `CREATE TABLE IF NOT EXISTS`), odczyt przy ładowaniu przedmiotu z rodzin pakietu
(rękawice Sung Ma, biżuteria jadeitowa, Talizmany Woli – hak `Mt2009GloveLoad` na końcu `ITEM_MANAGER::CreateItem`).
Sprzedaż między botami to bezpośrednie przeniesienie (`RemoveFromCharacter` / `AddToCharacter`) – bez okna handlu.

Kolejność: po `obreczjadeitu2` (kotwica w `CopyAttributeTo`), ostatnia. Linux: `python3 apply_g0bind.py <game/src>`,
Windows: `Apply-G0BindPatch.ps1` (z `tools/port/Apply-MT2009PlusEngine.ps1`). Edycje: `gen_edits.py` → `edits.json`.
