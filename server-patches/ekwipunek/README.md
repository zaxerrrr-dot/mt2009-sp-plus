# Dodatkowy ekwipunek (specjalny magazyn z Amerii)

Okno dodatkowego ekwipunku z Ameria Project (`ENABLE_SPECIAL_STORAGE`: `srcs/server/game/char_item.cpp`, `item.cpp`,
`cmd_general.cpp`, klient `uispecialinventory.py` / `uispecialstorage.py`) dla MT2009 PLUS 3.x „Yohara” – prośba
właściciela z 21.10.2026: *„Dodaj okno dodatkowego ekwipunku z Amerii, z automatycznym wpadaniem przedmiotów do danych
kategorii.”* Znacznik: `MT2009_PLUS_EKWIPUNEK_V1 (…)`.

## Gdzie co jest

| Część | Miejsce |
|---|---|
| Logika serwera | `linux-port/overlays/playerbot/src/game/src/playerbot_ekwipunek.cpp` (metody `CHARACTER`, `/ekwipunek`) |
| Haki silnika | `edits.json` (71 zmian w 15 plikach: common `length.h`, db `ClientManagerPlayer.cpp`, game); `gen_edits.py` je generuje i sprawdza, `apply_ekwipunek.py` (Linux) i `Apply-EkwipunekPatch.ps1` (Windows, krok `tools/port/Apply-MT2009PlusEngine.ps1` po Buffi) czytają ten sam plik |
| Baza | `linux-port/docker/mariadb/playerbot/apply.sh` (krok „extra inventory”): `player.item.window` dostaje na końcu `UPGRADE_INVENTORY`, `BOOK_INVENTORY`, `STONE_INVENTORY`, `CHANGE_INVENTORY`, `CHEST_INVENTORY` |
| Exe (3.0) | `client-patches/exe` – `ENABLE_SPECIAL_STORAGE` (opis w `client-patches/exe/README.md`) |
| Klient (root) | `client-2.0.30/root/uiekwipunek.py` (okno), haki w `uiinventory.py`, `uiexchange.py`, `uicube.py` (nowa kopia), `game.py`, `interfacemodule.py`, `keybind.py`; ikony `root/mt2009_ui/ekwipunek/*.png` (z Amerii), `root/mt2009_ui/sidebar/ekwipunek_0[1-3].tga` |

## Jak to działa

- **Okna**: pięć magazynów kategorii to nowe okna przedmiotów 11–15 (w Amerii w środku listy; tu dopisane po oknach
  sklepu offline, żeby `player.item.window` – enum zapisywany numerem – i klient zachowały stare numery). Każdy ma 4
  strony 5 × 9 (180 pól), przedmiot zajmuje swoją wysokość w kolumnie i nie przechodzi na następną stronę.
- **Kategorie (jak w Amerii)**: Materiały ulepszeń (`ITEM_MATERIAL`/`MATERIAL_LEATHER` + 27987, 27799, 70031,
  27992–27994; **u nas także zwoje i kamienie ulepszania** `ITEM_USE`/`USE_TUNING` – Zwój Błogosławieństwa, Magiczny
  Kamień, Podręcznik Kowala, Zwój Wojny, Zwój Boga Smoków, Kamień Rytualny, Gwarancje Rzemiosła;
  `MT2009_PLUS_EKWIPUNEK_REFINE_V1`), Księgi (`ITEM_SKILLBOOK` + 50301–50303; **u nas wszystkie czytane księgi** – `ITEM_SKILLFORGET` (Księga Zapomnienia), Sztuka Combo 50304–50306, Księgi Misji, języki 50311–50313, Księgi Polimorfii, Księga Precyzji 50325, Charyzma/Inspiracja 50338–50343, Podręczniki 50514/50515, księgi konne 50052/50053/50060 i 55050–55067, księgi umiejętności peta 55010–55031; `MT2009_PLUS_EKWIPUNEK_BOOKS_V1`, ta sama lista w `uiekwipunek.py`), Kamienie Duszy (`ITEM_METIN`/`METIN_NORMAL`), Zaczarowania
  (`ITEM_USE`/`USE_CHANGE_ATTRIBUTE` + 72346), Skrzynie (`ITEM_GIFTBOX`). Szóste okno Amerii (kostiumy) pominięte –
  w Amerii `CItem::IsCostume()` zawsze zwraca `false`, więc nic tam nie trafia.
- **Automatyczne wpadanie** (`GetEmptyInventoryRouted`): podniesienie (własne i drużyny), `AutoGiveItem` (questy,
  skrzynie, nagrody), zakup w sklepie NPC, handel, zwrot ze sklepu offline, GM `/item`. Najpierw łączy się ze stosami
  w magazynie (`Mt2009EkwAutoStack*`, także Cor Draconis), potem wolne pole magazynu. **Inaczej niż w Amerii**: pełny
  magazyn nie odmawia – przedmiot idzie do zwykłego ekwipunku.
- **Tylko prawdziwy gracz z nowym exe**: klient z oknami (exe 3.0 + `uiekwipunek.py`) wysyła `/ekwipunek hello` po
  wejściu do gry i po każdym teleporcie; dopiero wtedy serwer kieruje przedmioty do magazynów. Stary exe ich nie
  pokazuje, więc bez hello wszystko zostaje w torbie. **Boty nigdy** – ich AI (sprzedaż, magazyn, crafting) czyta
  tylko `INVENTORY`. Boty same nie dostają przekierowania, ale od `MT2009_PLUS_BOT_EKWIPUNEK_V1`
  (`playerbot_ekwipunek_bots.h`, 27.10.2026) **pożyczają magazynom nadmiar torby**: przy mniej niż 10 wolnych polach
  odkładają dodatkowe stosy tego samego przedmiotu (w torbie zostaje największy stos, dopełniony), potem całe stosy
  „towaru” (materiały, księgi cudzych umiejętności, kamienie duszy, których nie osadzą, skrzynie poza Corami alchemii)
  do 16 wolnych pól; zapas roboczy (zwoje ulepszania, zaczarowania, własne księgi, kamienie do osadzenia, Cory) wraca
  do torby od razu, gdy go w niej brak, a towar – gdy torba ma ponad 22 wolne pola. Flaga `m2_ekw_bots_off` wyłącza,
  log `PLAYERBOT_EKW`.
  Od `MT2009_PLUS_BOT_EKW_PAGES_V1` (28.10.2026) magazyny są dla bota **dalszymi stronami torby**: szukanie towaru
  (umowy z szeptu i spotkania, „masz X?”, rynek, Cory i fasolki alchemii) widzi torbę i magazyny
  (`CollectPlayerBotOwnedItems`); zanim silnik czegoś dotknie (okno handlu, użycie), przedmiot wraca do pola torby
  (`PlayerBotEkwBringToBag` / `PlayerBotEkwFetchMatching`), a pełna torba najpierw oddaje magazynom nadmiar lub towar.
  Przed wizytą przy ladzie i w mieście towar z magazynów wraca do wolnego miejsca torby (`PlayerBotEkwFetchGoods`,
  nie poniżej 10 wolnych pól). Silnik bez zmian (`CountSpecifyItem` / `RemoveSpecifyItem` czytały magazyny już
  wcześniej). Ta sama flaga `m2_ekw_bots_off` i zasada towarzyszy; log `PLAYERBOT_EKW: pages`.
  Od `MT2009_PLUS_BOT_EKW_ROUTE_V1` (31.10.2026, decyzja właściciela) **boty kierują przedmioty jak gracz**:
  `GetSpecialWindowFor` / `Mt2009EkwAutoStackProto` pytają dla deskryptora bota regułę botów
  (`PlayerBotEkwRouteWindow`, `playerbot_ekwipunek_bots.h`) – towar kategorii od razu do magazynu, zapas roboczy do
  torby, dopóki torba nie ma pełnego stosu danego rodzaju. Jednorazowe przeniesienie zawartości torby (flaga questowa
  `playerbot.ekw_moved`, najwyżej 30 botów na minutę na rdzeń), sprzedaż śmieci, skrzynie, wymiana u Dozorcy, miejsce
  na łup i zakup w ItemShopie czytają magazyny. Flaga `m2_ekw_bots_route_off` wraca do samego pożyczania; log
  `PLAYERBOT_EKW: route report` / `moved once`. Łatka silnika (`edits.json`) bez zmian – zmiana jest w nakładce.
- **Wyjście**: przeciągnięcie do torby (`MoveItem`: do magazynu tylko jego kategoria, z torby albo z niego samego;
  z magazynu tylko do torby), użycie prosto z magazynu (`UseItem` – księgi, skrzynie, kamień na przedmiot,
  zaczarowanie na przedmiot), `CountSpecifyItem` / `RemoveSpecifyItem` liczą i biorą z magazynów (materiały
  ulepszania u kowala, questy), sprzedaż w sklepie NPC (`/ekwipunek sprzedaj`), magazyn (depozyt) w obie strony
  (do magazynu kategorii tylko jego przedmioty), handel, okno craftingu (`/ekwipunek kostka`).
- **Ulepszanie** (`MT2009_PLUS_EKWIPUNEK_REFINE_V1`, edycje „REFINE” w `gen_edits.py`): zwój z magazynu
  przeciągnięty na przedmiot (w torbie albo w magazynie) otwiera okno ulepszania i ulepszenie zabiera zwój z magazynu;
  przedmiot z magazynu oddany kowalowi (np. Kamień Duszy +4…+8 – następny stopień) ulepsza się w swoim polu, wynik
  wraca w to samo pole (`Mt2009EkwRefinePlace`; reszta stosu zostaje w magazynie). Pakiety ulepszania bez zmian:
  niosą tylko pole, więc serwer pamięta okno przedmiotu i zwoju z `RefineInformation` (`m_bEkwRefineWindow`,
  `m_bEkwRefineScrollWindow`) i czyta po nich w `CInputMain::Refine` / `DoRefineWithScroll` (także „okno zostaje
  otwarte”). Klient dostaje okno komendą `ekwipunek_refine <okno>` tuż przed pakietem (`uirefine.py` pokazuje ten
  przedmiot i liczy materiały także z magazynów). Materiały z przepisu kowala są liczone i zabierane z torby i magazynów
  (`CountSpecifyItem` / `RemoveSpecifyItem`). Usunięte edycje V1 „npc refine” / „scroll refine” (komunikat
  „przenieś do zwykłego ekwipunku”).
- **Szybki pasek** nie przyjmuje przedmiotów z magazynów (serwer odrzuca typ > 3); synchronizacja paska nie
  rusza pól torby o tym samym numerze (strażniki w `SetCount`, `RemoveItem`, `DropItem`, depozycie, handlu).
- **Stos / Sortuj** (pasek ustawień okna jak w Amerii, `MT2009_PLUS_EKWIPUNEK_LOOK_V1`, raz na 3 s):
  `/ekwipunek stos <okno>` – przycisk Amerii „stack”, łączy stosy; `/ekwipunek sortuj <okno>` – „sort”, łączy stosy
  i układa według typu, podtypu i vnum. Zablokowane przedmioty zostają na miejscu.
- **Prawy klik = do torby** (`MT2009_PLUS_EKWIPUNEK_TOBAG_V1`, `/ekwipunek dotorby <okno> <pole>`): cały stos
  z magazynu do zwykłego ekwipunku – najpierw dołącza do stosów tego samego przedmiotu (te same gniazda), reszta
  w pierwsze wolne pole; bez miejsca zostaje, czat „Brak miejsca w ekwipunku.”. Pomija przedmioty zablokowane,
  w handlu i wystawione w sklepie gracza. (W Amerii prawy klik używa przedmiotu – u nas użycie to podwójny klik
  albo Ctrl+PPM.)
- **Przenieś do extra EQ** (`MT2009_PLUS_EKWIPUNEK_MOVE_V1`, trzecia opcja przycisku sortowania ekwipunku,
  `inventoryarrange.py`; `/ekwipunek przenies [keep=<hex>]`, raz na 3 s): każdy przedmiot torby należący do kategorii
  idzie do swojego magazynu – najpierw dołącza do stosów, potem wolne pole. Zostają: założone, zablokowane, w handlu,
  wystawione w sklepie gracza, zablokowane przed sortowaniem (Alt+LPM) i te, dla których magazyn jest pełny (czat
  podaje liczby i pełne kategorie). Tylko prawdziwy gracz z nowym exe.

## Poprawki 3.0.7 (lista właściciela z 03.11.2026, sekcja B – `MT2009_PLUS_EKWIPUNEK_CATS_V2`)

- **Kategorie** (`Mt2009EkwCategoryOf` i `uiekwipunek.CategoryOf` w parze): do **Zaczarowania** także Pozwolenia
  (30368–30370), Marmur Błogosławieństwa (`USE_ADD_ATTRIBUTE2`), Błogosławieństwo Przedmiotu 71052, odłamki 6/7
  39070–39081 (wszystkie kolory, lśniące, Święty), suplementy 72064–72067, Wzmocnienie Przedmiotu i Zielona Siła
  (`USE_ADD_ATTRIBUTE`), Zaczaruj / Transformuj kostium (`USE_CHANGE_COSTUME_ATTR` / `USE_RESET_COSTUME_ATTR`); do
  **Ulepszaczy** runy aury 49990–49995 (po vnumie); do **Ksiąg** receptury zielarstwa (`USE_CRAFT_RECIPE`, 50910).
  **Zwoje ulepszania** (`USE_TUNING`: Zwój Błogosławieństwa, Zwój Boga Smoków, Magiczny Kamień…) i Kamień Runiczny
  31225 zostają w torbie; te, które już leżą w Ulepszaczach, zostają tam (przeciąganie / prawy klik do torby, ulepszanie
  z magazynu działa jak wcześniej).
- **Przeniesienie po zmianie kategorii** (`Mt2009EkwRecategorize`): przy każdym `/ekwipunek hello` przedmioty magazynów,
  których kategoria jest teraz inna (np. Pozwolenia i odłamki z Ulepszaczy), idą do nowego magazynu (najpierw do stosów,
  potem wolne pole; bez miejsca zostają). Bez SQL – zrobi się samo przy wejściu do gry. Boty: przebieg
  `ManagePlayerBotEkwipunek` przenosi je tak samo (bez kategorii – do torby); zaczarowania-materiały (Pozwolenia,
  odłamki, suplementy) i receptury to dla bota „towar” (`IsPlayerBotEkwWorkingStock`).
- **Okno**: bez przycisków Kostiumy / Alchemia / ItemShop (drugi rząd ma same Skrzynie); księga umiejętności ma ikonę
  swojej umiejętności jak w torbie; „Sortuj” sortuje wszystkie kategorie naraz (`/ekwipunek sortuj wszystko`).
- **Ctrl + PPM w torbie** przy otwartym oknie: przedmiot do swojej kategorii (`/ekwipunek doekw <pole>`; skrzynia
  przenoszona, nie otwierana).
- **Seon-Hae**: suplement przeciągnięty z zakładki prosto na pole dodatku (`/seonhae add … <okno dodatku>`, piąte słowo
  opcjonalne – stary klient bez zmian).
- **Pasek szybkiego wyboru** (edycja `potion quickslot` w `item.cpp`): wyczerpany stos w magazynie (zabranie materiałów
  przez quest / wytwarzanie / ulepszanie, łączenie stosów, przeniesienie kategorii po teleporcie) przepinał albo usuwał
  pozycję paska wskazującą pole **torby** o tym samym numerze – przez to po teleporcie znikały mikstury z paska, a skille
  zostawały. Teraz pusty stos magazynu nie rusza paska (gałąź `SetCount(0)` dla podtypu 0 / mikstur).
- **Wytwarzanie u NPC** (kowal, kucharz, alchemicy – `crafting.lua`): serwer już liczył i zabierał materiały z magazynów
  (`CountSpecifyItem` / `RemoveSpecifyItem`); okno (`uicuberenewal.CraftingRenewalWindow`) liczy je teraz też.

## Komendy

`/ekwipunek hello`, `/ekwipunek sortuj <okno 11-15>|wszystko`, `/ekwipunek doekw <pole torby>`, `/ekwipunek stos <okno>`, `/ekwipunek dotorby <okno> <pole>`, `/ekwipunek sprzedaj <okno> <pole> <ilość>`,
`/ekwipunek kostka <pole kostki> <okno> <pole>`, `/ekwipunek przenies [keep=<hex>]` – wysyłają je `uiekwipunek.py`,
`uicube.py`, `inventoryarrange.py`. Serwer → klient: `ekwipunek_ok <strony>`, `ekwipunek_refine <okno>`.
