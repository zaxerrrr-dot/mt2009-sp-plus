# Sklepy offline – runda 2 i nazwa księgi w powiadomieniach (Autor: Vekirion)

Poprawka silnika z paczek Vekiriona „Sklepy offline i filtr podnoszenia” i „Nazwa księgi w sklepie”
(13–15 października 2026). Znaczniki: `MT2009_PLUS_SHOP_QOL_V2`, `MT2009_PLUS_SHOP_SOLD_BOOK_NAME_V1`,
`MT2009_PLUS_SHOP_BOOK_NOTIFICATION_V1` (każda zmiana ma własny dopisek w nawiasie). Nakładana raz,
przy przygotowaniu wydania (`tools/port/Apply-MT2009PlusEngine.ps1`, po `auctionhouse` i
`pickuprules`). `Apply-ShopQolPatch.ps1` i `apply_shopqol.py <game/src>` czytają ten sam `edits.json`;
ścieżki plików bazy i `common` są względne do `game/src`.

Nowy plik `ikashop_qol.h` jest w nakładce (`linux-port/overlays/playerbot/src/game/src/`, jak
`auction_house.cpp`) i trafia do drzewa silnika razem z plikami Playerbota.

**Nowe subheadery GD/DG w `common/tables.h` – game i db trzeba przebudować razem.**

| Znacznik | Plik | Co |
|---|---|---|
| `SHOP_QOL_V2 (gd extend)`, `(dg set duration)` | `common/tables.h` | `SUBHEADER_GD_SHOP_EXTEND_DURATION`, `SUBHEADER_DG_SHOP_SET_DURATION` i ich pakiety (na końcu enumów) |
| `(db decl)`, `(db recv)`, `(db extend)` | `db/src/ClientManager.h`, `ClientManagerIkarusShop.cpp` | „Przedłuż” – rdzeń bazy dodaje minuty (do `OFFLINESHOP_DURATION_MAX_MINUTES`), zapisuje i rozsyła nowy czas |
| `(decl)`, `(set duration)`, `(case)` | `ikarus_shop_manager.h`, `input_db.cpp` | odbiór nowego czasu |
| `(include)` … `(commands)` | `ikarus_shop_manager.cpp` | `ikashop_qol.h`; wiek linii i auto-obniżka ceny (tabela `player.ikashop_item_meta`, tworzona też w grze), większy sklep dla ludzi przy fladze `m2_shop_big_on` (przełącznik w panelach), kupno części stosu z okna sklepu (`/ikashop_buy_part`), `/ikashop_autoprice`, `/ikashop_extend` |
| `(cmd declare)`, `(cmd table)` | `cmd.cpp` | trzy nowe komendy |
| `(move in shop)` | `char_item.cpp` | przy otwartym oknie własnego sklepu można przesuwać/dzielić przedmioty w plecaku (Shift + LPM) |
| `SHOP_SOLD_BOOK_NAME_V1 (part)`, `(whole)`, `(notify)` | `ikarus_shop_manager.cpp` | przed powiadomieniem o sprzedaży księgi idzie `IkaShopSoldBook <vnum> <umiejętność>` – klient pisze „<umiejętność> - Księga Umiejętności” |
| `SHOP_BOOK_NOTIFICATION_V1 (who)` i reszta | `db/src/ClientManagerIkarusShop.cpp` | historia/powiadomienia sklepu: umiejętność księgi jako „#S<nr>” w polu „kto” (bez zmian tabel i pakietów); klient zdejmuje znacznik i nazywa księgę |
