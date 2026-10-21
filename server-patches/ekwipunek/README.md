# Dodatkowy ekwipunek (specjalny magazyn z Amerii)

Okno dodatkowego ekwipunku z Ameria Project (`ENABLE_SPECIAL_STORAGE`: `srcs/server/game/char_item.cpp`, `item.cpp`,
`cmd_general.cpp`, klient `uispecialinventory.py` / `uispecialstorage.py`) dla MT2009 PLUS 3.x „Yohara” – prośba
właściciela z 21.10.2026: *„Dodaj okno dodatkowego ekwipunku z Amerii, z automatycznym wpadaniem przedmiotów do danych
kategorii.”* Znacznik: `MT2009_PLUS_EKWIPUNEK_V1 (…)`.

## Gdzie co jest

| Część | Miejsce |
|---|---|
| Logika serwera | `linux-port/overlays/playerbot/src/game/src/playerbot_ekwipunek.cpp` (metody `CHARACTER`, `/ekwipunek`) |
| Haki silnika | `edits.json` (47 zmian w 15 plikach: common `length.h`, db `ClientManagerPlayer.cpp`, game); `gen_edits.py` je generuje i sprawdza, `apply_ekwipunek.py` (Linux) i `Apply-EkwipunekPatch.ps1` (Windows, krok `tools/port/Apply-MT2009PlusEngine.ps1` po Buffi) czytają ten sam plik |
| Baza | `linux-port/docker/mariadb/playerbot/apply.sh` (krok „extra inventory”): `player.item.window` dostaje na końcu `UPGRADE_INVENTORY`, `BOOK_INVENTORY`, `STONE_INVENTORY`, `CHANGE_INVENTORY`, `CHEST_INVENTORY` |
| Exe (3.0) | `client-patches/exe` – `ENABLE_SPECIAL_STORAGE` (opis w `client-patches/exe/README.md`) |
| Klient (root) | `client-2.0.30/root/uiekwipunek.py` (okno), haki w `uiinventory.py`, `uiexchange.py`, `uicube.py` (nowa kopia), `game.py`, `interfacemodule.py`, `keybind.py`; ikony `root/mt2009_ui/ekwipunek/*.png` (z Amerii), `root/mt2009_ui/sidebar/ekwipunek_0[1-3].tga` |

## Jak to działa

- **Okna**: pięć magazynów kategorii to nowe okna przedmiotów 11–15 (w Amerii w środku listy; tu dopisane po oknach
  sklepu offline, żeby `player.item.window` – enum zapisywany numerem – i klient zachowały stare numery). Każdy ma 4
  strony 5 × 9 (180 pól), przedmiot zajmuje swoją wysokość w kolumnie i nie przechodzi na następną stronę.
- **Kategorie (jak w Amerii)**: Materiały ulepszeń (`ITEM_MATERIAL`/`MATERIAL_LEATHER` + 27987, 27799, 70031,
  27992–27994), Księgi (`ITEM_SKILLBOOK` + 50301–50303), Kamienie Duszy (`ITEM_METIN`/`METIN_NORMAL`), Zaczarowania
  (`ITEM_USE`/`USE_CHANGE_ATTRIBUTE` + 72346), Skrzynie (`ITEM_GIFTBOX`). Szóste okno Amerii (kostiumy) pominięte –
  w Amerii `CItem::IsCostume()` zawsze zwraca `false`, więc nic tam nie trafia.
- **Automatyczne wpadanie** (`GetEmptyInventoryRouted`): podniesienie (własne i drużyny), `AutoGiveItem` (questy,
  skrzynie, nagrody), zakup w sklepie NPC, handel, zwrot ze sklepu offline, GM `/item`. Najpierw łączy się ze stosami
  w magazynie (`Mt2009EkwAutoStack*`, także Cor Draconis), potem wolne pole magazynu. **Inaczej niż w Amerii**: pełny
  magazyn nie odmawia – przedmiot idzie do zwykłego ekwipunku.
- **Tylko prawdziwy gracz z nowym exe**: klient z oknami (exe 3.0 + `uiekwipunek.py`) wysyła `/ekwipunek hello` po
  wejściu do gry i po każdym teleporcie; dopiero wtedy serwer kieruje przedmioty do magazynów. Stary exe ich nie
  pokazuje, więc bez hello wszystko zostaje w torbie. **Boty nigdy** – ich AI (sprzedaż, magazyn, crafting) czyta
  tylko `INVENTORY`.
- **Wyjście**: przeciągnięcie do torby (`MoveItem`: do magazynu tylko jego kategoria, z torby albo z niego samego;
  z magazynu tylko do torby), użycie prosto z magazynu (`UseItem` – księgi, skrzynie, kamień na przedmiot,
  zaczarowanie na przedmiot), `CountSpecifyItem` / `RemoveSpecifyItem` liczą i biorą z magazynów (materiały
  ulepszania u kowala, questy), sprzedaż w sklepie NPC (`/ekwipunek sprzedaj`), magazyn (depozyt) w obie strony
  (do magazynu kategorii tylko jego przedmioty), handel, okno craftingu (`/ekwipunek kostka`).
- **Ulepszanie u kowala / zwojem** czyta przedmiot po polu torby – przedmiot z magazynu trzeba najpierw przenieść
  do torby (komunikat). Materiały do ulepszenia mogą zostać w magazynie.
- **Szybki pasek** nie przyjmuje przedmiotów z magazynów (serwer odrzuca typ > 3); synchronizacja paska nie
  rusza pól torby o tym samym numerze (strażniki w `SetCount`, `RemoveItem`, `DropItem`, depozycie, handlu).
- **Sortuj** (`/ekwipunek sortuj <okno>`, raz na 3 s): przyciski Amerii „stack” i „sort” w jednym – łączy stosy
  i układa według typu, podtypu i vnum. Zablokowane przedmioty zostają na miejscu.
- Przedmioty, które już są w torbach, zostają tam (Ameria nie ma przycisku „przenieś do kategorii”; przeciąganie
  działa).

## Komendy

`/ekwipunek hello`, `/ekwipunek sortuj <okno 11-15>`, `/ekwipunek sprzedaj <okno> <pole> <ilość>`,
`/ekwipunek kostka <pole kostki> <okno> <pole>` – wszystkie wysyła `uiekwipunek.py` / `uicube.py`.
