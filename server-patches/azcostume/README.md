# Nakładki na szarfy z zestawów Arezzo

Poprawka silnika, znacznik `MT2009_PLUS_AREZZO_COSTUME_SETS_V1` (każda zmiana ma własny dopisek w nawiasie).
Część zestawów kostiumów z Arezzo (właściciel, 6 października 2026: „Dodaj również wszystkie sety kostiumów
z Arezzo, ale bez żadnych dodatkowych bonusów”). Nakładana raz, przy przygotowaniu wydania
(`tools/port/Apply-MT2009PlusEngine.ps1`, na końcu listy); `Apply-AzCostumePatch.ps1` i linuksowy bliźniak
`apply_azcostume.py <game/src>` czytają ten sam `edits.json`. Zmienione pliki: `item.h`, `char_item.cpp`,
`char.cpp`, `itemshop_manager.cpp` (na liście `launcher/server-update-files.mod.txt`).

Arezzo nosi „plecy” zestawu (skrzydła, peleryny) w osobnym slocie (stole). U nas są **nakładką na szarfę**:
przedmiot 85200–85221 (ITEM_USE 3/10 z flagą ITEM_FLAG_APPLICABLE, więc przeciągnięty na przedmiot w torbie
wysyła „użyj na przedmiocie”) przeciągnięty na szarfę zdjętą do ekwipunku zapisuje swój vnum w gnieździe 2
szarfy. Szarfa wygląda jak nakładka (model z `item_list.txt`, typ WING), jej stopień, pochłanianie, bonusy i
efekt świecenia (+500) zostają. Bez nowego slotu, bez zmiany pakietów i bez nowego exe.

## Co robi

| Dopisek | Gdzie | Co |
|---|---|---|
| (bez dopisku) | `item.h`, `CItem::GetAcceVnum` | vnum nakładki z gniazda 2 (85200–85299) zamiast vnumu szarfy – to idzie do `PART_ACCE`, który widzą wszyscy; stałe `MT2009_SASH_SKIN_*`, `GetMt2009SashSkin()`. |
| `(use)` | `char_item.cpp`, przed `CHARACTER::UseItemEx` | `Mt2009PlusUseSashSkin`: tylko szarfa w torbie (nie założona, nie w handlu, nie zablokowana); ta sama nakładka – komunikat; inaczej gniazdo 2 = nakładka, nakładka zużyta, poprzednia wraca do torby (`AutoGiveItem`), log `SASH_SKIN_SET`. |
| `(combine)` | `char.cpp`, `RefineAcceMaterials` | Udane łączenie szarf u Uriela przenosi nakładkę (z pierwszej szarfy, a jak jej nie ma – z drugiej). |
| `MT2009_PLUS_AREZZO_COSTUME_SETS_V2 (ishop-list` | `itemshop_manager.cpp`, `CItemShopManager::CanSendItem` | Przedmiot zestawu Arezzo nie trafia do okna ItemShopu, gdy moduł Arezzo jest wyłączony (flaga `mt2009_arezzo_closed`). Funkcja `Mt2009PlusArezzoCostumeLocked` jest w overlayu (`playerbot_arezzo_costumes.h`, generowany). |
| `MT2009_PLUS_AREZZO_COSTUME_SETS_V2 (ishop-buy)` | `itemshop_manager.cpp`, `CItemShopManager::BuyItem` | Zakup takiego przedmiotu przy wyłączonym module jest odrzucany z komunikatem (okno otwarte przed przełączeniem, boty). |

Nakładki nie da się zdjąć do „gołej” szarfy – można ją tylko zamienić na inną (stara wraca do torby).
Przy nieudanym łączeniu szarf nakładka z szarfy, która przepada, przepada razem z nią.

## Reszta zestawów (bez zmian w silniku)

Przedmioty: `linux-port/docker/mariadb/playerbot/arezzo_costumes.sql` (apply.sh przy każdym starcie, INSERT
IGNORE), sklepy: blok `ishop_once arezzo_costume_sets` w apply.sh i `arezzo_costumes_webshop.sql`, bonus
zestawu: `linux-port/docker/game/costume_sets.txt` (MT2009_PLUS_COSTUME_SET_V1 z `server-patches/playerqol`).
Wszystko generuje `client-patches/client-2.0.30/tools/azcostume/gen_azcostume_server.py` z
`azcostume_items.json` – te same wiersze dostaje klient (`patch_azcostume_client.py`).

## V2 (6 października 2026)

* Usunięte zestawy **Ognistego Rycerza** i **Krwawej Zemsty** (właściciel: brak efektów na kostiumach, mieczach
  i szarfach) – 22 przedmioty: 42930, 42931, 42946, 42947 (kostiumy), 45930, 45931, 45946, 45947 (hełmy),
  40960–40965 i 40840–40845 (nakładki na broń), 85205 i 85213 (nakładki na szarfę). Pozostałe vnumy i indeksy
  ItemShopu bez zmian. apply.sh przy starcie: `DELETE` z `world.item_proto` (każdy start), `ishop_once
  arezzo_costume_sets_v2` (ItemShop w grze), oferty sklepu WWW, a raz (`azcostume_removed_v2`) przedmioty graczy
  (`player.item`), nieodebrane `player.item_award` i nakładka 85205/85213 na szarfie (gniazdo 2 = 0) – z liczbą w logu.
* Zestawy kostiumów z Arezzo są dostępne tylko przy włączonym **module Arezzo** (`M2_AREZZO`, panel „Moduł
  Arezzo”, flaga `mt2009_arezzo_closed`): ItemShop w grze (dopiski `ishop-list` / `ishop-buy` wyżej), boty
  (`playerbot_itemshop.h` – katalog bez nich, przebudowany od razu po przełączeniu), sklep WWW
  (`itemshop/arezzo_costumes.php`: lista, kategoria, szczegóły, zakup). Wiersze `item_proto` zostają – to, co
  gracz już ma, działa dalej.
