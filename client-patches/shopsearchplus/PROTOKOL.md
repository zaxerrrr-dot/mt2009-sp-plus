# Target Drop Info i wyszukiwarka sklepów prywatnych

Poprawka silnika, znacznik `MT2009_PLUS_SHOP_SEARCH_PLUS_V1`. Nakładana raz, przy
przygotowaniu wydania (`tools/port/Apply-MT2009PlusEngine.ps1`);
`Apply-ShopSearchPlusPatch.ps1` i linuksowy bliźniak `apply_shopsearchplus.py`
robią to samo:

- kopiują `src/shop_search_plus.h` i `src/shop_search_plus.cpp` do `game/src`,
- dopisują numery pakietów (`packet.h`), ich rozmiary (`packet_info.cpp`),
  obsługę (`input_main.cpp`) i użycie lup 60004/60005 (`char_item.cpp`).

Przedmioty 60004 (Lupa) i 60005 (Lupa Handlarza) dodaje
`linux-port/docker/mariadb/playerbot/mod/30_shop_search_glasses.sql` (raz na
instalację): `item_proto` i sklep Handlarki Różności (sklep 3).

Oba systemy są **niezależne** od dotychczasowych: podgląd dropu `/mob_drop`
i wyszukiwarka Ikarusa działają dalej, więc stary klient nic nie traci.

## Target Drop Info

Na podstawie modu „Target Drop Info” (pakiety bez zmian), ale listę przedmiotów
liczy nasze `ITEM_MANAGER::GetPossibleMobDropItems` (to samo co `/mob_drop`):
uwzględnia poziom gracza i potwora, Cor Draconis, szarfy, kupony SM, księgi.

**Plusy scalone:** broń, zbroje, biżuteria i pasy +0…+9 to 10 kolejnych numerów
(`vnum / 10` wspólne). Jeśli potwór może dać Miecz +0, +1 i +3, lista pokazuje
tylko najniższy (+0), reszta to dubel. Strzały i przedmioty stackowane nie są
scalane. Lista jest posortowana po numerze, najwyżej 70 pozycji.

| Kierunek | Nagłówek | Struktura |
|---|---|---|
| klient → serwer | `HEADER_CG_TARGET_DROP = 151` | `BYTE header` |
| serwer → klient | `HEADER_GC_TARGET_DROP = 160` | `BYTE header; WORD raceVnum; WORD size; DWORD items[70]` (stały rozmiar 285 B) |

Dotyczy aktualnego celu gracza (kliknięty potwór albo Metin na tej samej mapie).
Najwyżej jedno zapytanie na sekundę (nadmiarowe są ignorowane).

## Wyszukiwarka sklepów prywatnych

Na podstawie „Metin2 Private Shop Search” (blackdragonx61), przeniesiona na
**sklepy offline Ikarusa** (gracze i boty). Otwiera ją użycie lupy:

- **Lupa (60004, 1 h):** wyszukiwanie i oznaczenie znalezionego sklepu na
  minimapie (sklep na tej samej mapie i kanale),
- **Lupa Handlarza (60005, 7 dni):** wyszukiwanie i **zakup z dowolnego
  miejsca** – ta sama zablokowana transakcja w bazie co zakup przy sklepie
  (Yang schodzi dopiero po potwierdzeniu, zmieniona cena jest odrzucana).

Wszystkie struktury `#pragma pack(1)`. `packet_shop_item` to istniejąca
struktura sklepu (`vnum DWORD, price long long, count DWORD, display_pos BYTE,
alSockets long[3], aAttr {BYTE type; short value}[7]`), bez `ENABLE_CHEQUE_SYSTEM`.

| Kierunek | Nagłówek | Struktura |
|---|---|---|
| serwer → klient | `HEADER_GC_PRIVATE_SHOP_SEARCH_OPEN = 217` | `BYTE header; BYTE bMode` (1 = Lupa, 2 = Lupa Handlarza) |
| klient → serwer | `HEADER_CG_PRIVATE_SHOP_SEARCH = 216` | `BYTE header; BYTE bJob; BYTE bMaskType; int iMaskSub; int iMinRefine; int iMaxRefine; int iMinLevel; int iMaxLevel; long long llMinGold; long long llMaxGold; char szItemName[33]` |
| serwer → klient | `HEADER_GC_PRIVATE_SHOP_SEARCH = 216` | `BYTE header; WORD size;` + N × `TPacketGCPrivateShopSearchItem` (N = (size − 3) / sizeof) |
| klient → serwer | `HEADER_CG_PRIVATE_SHOP_SEARCH_CLOSE = 217` | `BYTE header` |
| klient → serwer | `HEADER_CG_PRIVATE_SHOP_SEARCH_BUY_ITEM = 218` | `BYTE header; DWORD dwShopPID; DWORD dwItemID; long long llSeenPrice` |
| serwer → klient | `HEADER_GC_PRIVATE_SHOP_SEARCH_MARK = 218` | `BYTE header; DWORD dwShopVID; long lX; long lY` |

`TPacketGCPrivateShopSearchItem` = `packet_shop_item item; char szSellerName[25];
DWORD dwShopPID; DWORD dwItemID; long lMapIndex; long lX; long lY; BYTE bChannel`.

Filtry (jak w modzie): `bJob` 0–3 (inna wartość: każda klasa), `bMaskType` typ
przedmiotu (0 = każdy), `iMaskSub` podtyp (−1 = każdy), poziom ulepszenia
(dla broni/zbroi = `vnum % 10`), poziom wymagany, cena w Yang (64 bity – ceny
powyżej 2,1 mld), `szItemName` – **fragment** nazwy, bez rozróżniania wielkości
liter ASCII; pusty = każda nazwa.

Serwer zawsze odpowiada na wyszukiwanie (także pustą listą), najwyżej raz na
2 s, najwyżej ~680 wyników (limit rozmiaru pakietu).

Różnice względem oryginału modu (klient musi je uwzględnić):

- ceny min/max jako `long long`, nie `int`;
- wynik ma dodatkowo `dwItemID`, mapę, pozycję i kanał sklepu;
- zakup wysyła `dwShopPID` + `dwItemID` + widzianą cenę zamiast pozycji;
- otwarcie okna niesie tryb (`bMode`);
- oznaczenie sklepu to osobny pakiet `HEADER_GC_PRIVATE_SHOP_SEARCH_MARK`,
  **bez** zmiany `TPacketGCTargetUpdate` (starszy klient z nowym serwerem
  nie rozjedzie się na strzałkach questów).
