# Zadanie dla agenta klienta: Target Drop Info i wyszukiwarka sklepów prywatnych

Serwer MT2009 PLUS ma już obie funkcje (poprawka `server-patches/shopsearchplus`,
działa na serwerze testowym mt2009plustest). Klient ma je dostać tak, żeby
pakiety zgadzały się **bajt w bajt** z serwerem. Specyfikacja pakietów:
`server-patches/shopsearchplus/README.md` (kopia obok: `PROTOKOL.md`),
struktury serwera: `shop_search_plus.h` (obok).

W paczce są oryginalne pliki klienta obu modów:

- `mods/Target Drop Info/` – mod „Target Drop Info” (C++ `source/client/UserInterface`,
  Python `pack/root`, grafiki `pack/root/kairos/target`, `ss.png`),
- `mods/Metin2-Private-Shop-Search-master/` – „Private Shop Search” (C++
  `1.Svn/Client`, Python/UI `3.Client/root`, `3.Client/uiscript`, grafiki
  `3.Client/ymir work/ui`, ikony `3.Client/icon/item/60004.tga`, `60005.tga`).

Pliki modów to instrukcje „znajdź / dodaj”. Część **serwerowa** modów
(`source/game`, `1.Svn/Server`, `2.Server`) jest już zrobiona – pomiń ją.

Klient jest 32-bitowy: `long` = 4 bajty, `long long` = 8 bajtów. Wszystkie
pakiety `#pragma pack(1)`. `ENABLE_CHEQUE_SYSTEM` i `ENABLE_WOLFMAN_CHARACTER`
są u nas **wyłączone** – pomiń wszystkie ich gałęzie w modach.

## 1. Target Drop Info – zamiast naszego obecnego podglądu dropu

Weź mod bez zmian w pakietach:

- `HEADER_CG_DROP_ITEM = 151` (`BYTE header`), wysyłany przy kliknięciu
  przycisku w oknie celu (`uitarget.py`),
- `HEADER_GC_TARGET_DROP = 160`: `BYTE header; WORD raceVnum; WORD size;
  DWORD items[70]` – **stały rozmiar 285 bajtów**; zarejestruj go w tabeli
  rozmiarów pakietów klienta (`CPythonNetworkStream` – mapa nagłówków fazy
  gry) jako stały, `sizeof(TPacketGCTargetDrop)`.
- `ITEM_DROP_SIZE 70`, `#define DROP_WIKI` w `Locale_inc.h`.

Serwer sam scala plusy: z Miecza +0/+1/+3 przychodzi tylko Miecz +0 (najniższy
dostępny plus). Klient ma tylko wyświetlić listę. Serwer odpowiada najwyżej
raz na sekundę – blokada 3 s w kliencie może zostać.

**Usuń stary podgląd dropu:** przycisk **Drop** na pasku celu, który wysyła
`/mob_drop <req> <vid> <page>` i odbiera `MobDropBegin/MobDropItem/MobDropEnd/
MobDropError` (CHAT_TYPE_COMMAND). Okno Target Drop Info ma go zastąpić. Serwer
nadal odpowiada na `/mob_drop`, więc usunięcie jest bezpieczne.

Tekst `RECV_ITEM_DROP_WAIT` z `locale/poland/locale_string.txt` modu jest dla
serwera – nie jest potrzebny (serwer go nie wysyła).

## 2. Wyszukiwarka sklepów prywatnych – nowa, obok wyszukiwarki Ikarusa

Weź mod, ale **zmień pakiety na nasze** (serwer przeszukuje sklepy offline
Ikarusa, graczy i botów, a nie zwykłe stragany):

| Nagłówek | Rozmiar | Uwagi |
|---|---|---|
| `HEADER_GC_PRIVATE_SHOP_SEARCH = 216` | zmienny: `WORD size` zaraz po nagłówku | lista wyników, może być pusta (size = 3) |
| `HEADER_GC_PRIVATE_SHOP_SEARCH_OPEN = 217` | stały 2 B | `BYTE header; BYTE bMode` – 1 Lupa, 2 Lupa Handlarza |
| `HEADER_GC_PRIVATE_SHOP_SEARCH_MARK = 218` | stały 13 B | `BYTE header; DWORD dwShopVID; long lX; long lY` |
| `HEADER_CG_PRIVATE_SHOP_SEARCH = 216` | 72 B | filtry, niżej |
| `HEADER_CG_PRIVATE_SHOP_SEARCH_CLOSE = 217` | 1 B | przy zamknięciu okna |
| `HEADER_CG_PRIVATE_SHOP_SEARCH_BUY_ITEM = 218` | 17 B | zakup / oznaczenie, niżej |

Zarejestruj trzy nagłówki GC w tabeli rozmiarów klienta (216 jako zmienny).

**Wyszukiwanie** (`TPacketCGPrivateShopSearch`, 72 B):
`BYTE header; BYTE bJob; BYTE bMaskType; int iMaskSub; int iMinRefine;
int iMaxRefine; int iMinLevel; int iMaxLevel; long long llMinGold;
long long llMaxGold; char szItemName[33]` – **ceny jako `long long`** (w modzie
`int`), `szItemName` to fragment nazwy (serwer szuka „zawiera”, nie „zaczyna
się od”); puste = każda nazwa. Maksima domyślnie: refine 9, poziom 120, cena
`9223372036854775807`.

**Wynik** (`TPacketGCPrivateShopSearchItem`, 96 B, po `BYTE header; WORD size`):
`packet_shop_item item` (ta sama co w sklepie: `DWORD vnum; long long price;
DWORD count; BYTE display_pos; long alSockets[3]; {BYTE bType; short sValue} aAttr[7]`)
+ `char szSellerName[25]; DWORD dwShopPID; DWORD dwItemID; long lMapIndex;
long lX; long lY; BYTE bChannel`. Zapamiętaj przy każdym wyniku `dwShopPID`,
`dwItemID` i `price` – są potrzebne do zakupu. W tabeli możesz pokazać mapę /
kanał sklepu.

**Kupno / oznaczenie** (`TPacketCGPrivateShopSearchBuyItem`, 17 B):
`BYTE header; DWORD dwShopPID; DWORD dwItemID; long long llSeenPrice` –
`llSeenPrice` = cena z wyniku. Ten sam przycisk w oknie: w trybie 1 (Lupa)
serwer odsyła `..._MARK` z pozycją sklepu, w trybie 2 (Lupa Handlarza) kupuje.
Komunikaty o błędach serwer wysyła zwykłym czatem (po polsku, bez znaków PL).

**Oznaczenie sklepu:** mod oznacza sklep przez `TPacketGCTargetUpdate.bIsShopSearch`
– **nie zmieniaj tej struktury**. Zamiast tego po `HEADER_GC_PRIVATE_SHOP_SEARCH_MARK`
narysuj znacznik na minimapie w (lX, lY) (współrzędne globalne jak w innych
pakietach celu) – możesz wywołać ten sam kod rysowania, którego mod używa dla
`bIsShopSearch` (grafika z modu).

**Otwieranie:** okno otwiera się **tylko** po pakiecie `..._OPEN` (serwer wysyła
go, gdy gracz użyje lupy). `bMode` ustawia tryb okna (tekst przycisku: „Oznacz”
albo „Kup”). Przy zamknięciu okna wyślij `..._CLOSE`.

**Przedmioty 60004 i 60005** – dodaj do klienta:

- `item_list.txt`: `60004 ETC icon/item/60004.tga` i `60005 ETC icon/item/60005.tga`
  (ikony z modu, `3.Client/icon/item`),
- klientowe `item_proto`: 60004 „Lupa”, 60005 „Lupa Handlarza” – typ `ITEM_USE`
  (3), podtyp `USE_SPECIAL` (10), limit `REAL_TIME` 3600 / 604800 s, antyflagi
  DROP|SELL|GIVE|PKDROP|STACK|MYSHOP, cena 50 000 / 1 000 000 Yang,
- `itemdesc.txt`: „Otwiera wyszukiwarkę sklepów i oznacza znaleziony sklep na
  mapie.” / „Otwiera wyszukiwarkę sklepów i pozwala kupować z niej z dowolnego
  miejsca.”
- Kupuje się je u Handlarki Różności (serwer już je tam dodał).

Teksty okna (`locale_interface.txt`, `locale_game.txt` z `3.Client/locale/en`)
przetłumacz na polski.

## 3. Czego nie ruszać

- Wyszukiwarka Ikarusa (klik ikony, `ikashop.SendSearchItem`) zostaje – to
  osobny system.
- `TPacketGCTargetUpdate`, `packet_shop_item` i inne istniejące struktury bez zmian.

## 4. Jak sprawdzić

Serwer testowy: mt2009plustest (179.61.251.72). Konto GM daje lupy komendą
`/i 60004` i `/i 60005`.

1. Zaznacz potwora → Target Drop Info pokazuje listę, bez powtórzeń plusów.
2. Użyj Lupy Handlarza → okno w trybie „Kup” → wyszukaj np. „Miecz” → kup
   przedmiot ze sklepu bota daleko od ciebie → przedmiot w ekwipunku, Yang
   mniej, przedmiot znika ze sklepu.
3. Użyj Lupy → wyszukaj → „Oznacz” sklep na tej samej mapie → znacznik na minimapie.
4. Zmień cenę w swoim sklepie w trakcie → zakup odrzucony („Cena przedmiotu
   sie zmienila”).

Przygotuj paczkę klienta jak zwykle (pełna, kumulatywna – exe + root +
pozostałe pliki), ale **nie publikuj** jej w manifeście przed testem operatora.
