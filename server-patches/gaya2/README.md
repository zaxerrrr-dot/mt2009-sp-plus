# gaya2 – Gaya jako waluta postaci (licznik obok Yang)

Znacznik: `MT2009_PLUS_GAYA_CURRENCY_V1` (28.10.2026, właściciel: „u nas Gaya jest trochę kaleka – nie ma ikonki i
licznika w ekwipunku obok Yang, Gaya zbiera się jako sloty w ekwipunku; zrobić jak na globalu”). Wzorce: paczki
właściciela w `cache/gaya2` – „gem ve patron gaya sistemi” (punkt `gem` w `player`, `pc.*` w questach), „Zenu Gem
system”, „Gaya Taskbar” i „Expanded Money Taskbar” (pasek walut: Won / Gaya / Yang). Sklep Gaya, szlifowanie Kamyków i
koszty wytwarzania zostają nasze (`ygaya`, `server-patches/gaya`) – zmienia się tylko to, skąd bierze się Gaya.

## Serwer (17 edycji, każda z własnym znacznikiem; po `npcloc`, ostatnia w `cache/yohara-deploy.sh`)

| Plik | Zmiana |
|---|---|
| `common/tables.h` | `TPlayerTable::gaya` (na końcu – db i game z tego samego nagłówka) |
| `db/src/ClientManagerPlayer.cpp` | `SELECT … ,gaya` po kolumnach czempiona, odczyt (gdy zapytanie ją ma), `UPDATE … gaya = %d` |
| `char.h` | `GetGaya`, `ChangeGaya(delta, powód)`, `SendGaya`, `Mt2009GayaSweep`, `Mt2009GayaEnter`; maks. 999 999 |
| `char.cpp` | zapis / odczyt `player.gaya`; `ChangeGaya` (nigdy poniżej 0 ani powyżej 999 999 – wtedy nic się nie zmienia, `false`), log postaci `GAYA` (powód: `QUEST`, `CUBE`, `PICKUP`, `ITEM`, `SAFEBOX`, `MALL`), linia do klienta `GAYA <stan> <zmiana>`; zamiana przedmiotów (niżej); magazyn i magazyn ItemShopu przy otwarciu |
| `item.cpp` | `CItem::AddToCharacter`: przedmiot 95927 u postaci → zamiana puls później |
| `char_item.cpp` | `PickupItem`: Gaya z ziemi od razu na licznik (jak Yang – bez wolnego miejsca w ekwipunku; przy 999 999 zostaje na ziemi z komunikatem) |
| `input_login.cpp` | `Entergame`: stan licznika do klienta (+ komunikat o zamianie z wczytywania) |
| `cube.cpp` | receptury `gaya N` (kowale zestawów, Statua Węży, ołtarz, Mistrz Chi…): sprawdzenie i pobranie z licznika |
| `questlua_pc.cpp` | `pc.get_gaya()`, `pc.change_gaya(n)` (zwraca `true` / `false`) |

### Zamiana starych przedmiotów Gaya (95927) – raz, sama, w logach

Bez skryptu do uruchamiania ręcznie – robi to rdzeń gry:

- **ekwipunek i magazyny dodatkowego ekwipunku** (`UPGRADE_INVENTORY` itd.): każde `AddToCharacter` przedmiotu 95927 –
  także wczytanie przedmiotów przy logowaniu – zamawia „przegląd” (zdarzenie po PID, jeden na postać); przegląd zdejmuje
  wszystkie stosy 95927 i dopisuje dokładnie tyle, ile zdjął (log przedmiotu `GAYA_CURRENCY`, log postaci `GAYA` `ITEM`).
  Dzięki temu łapie też Gaya z questa, skrzynki, wyniku wytwarzania, przeniesienia z magazynu, podniesienia przez
  towarzysza;
- **magazyn i magazyn ItemShopu**: przy otwarciu (wczytaniu) – przedmiot nie trafia do okna, jego wiersz w `item` jest
  kasowany (`HEADER_GD_ITEM_DESTROY`), licznik dostaje ilość;
- **z ziemi**: od razu na licznik;
- czego nie da się dopisać (powyżej 999 999), zostaje przedmiotem (wpis w syslogu).

Gracz dostaje komunikat „Gaya jest teraz walutą: N Gaya trafiło na twój licznik Gaya (obok Yang w ekwipunku).” (przy
wczytywaniu – po wejściu do gry). Na serwerze testowym (28.10): 2 stosy, 6510 Gaya (10 w ekwipunku, 6500 w magazynie
materiałów).

### Starszy klient

Nowego pakietu nie ma. Stan idzie linią czatu-komendy `GAYA <stan> <zmiana>` (jak `YGAYA` sklepu): stary root jej nie
zna – exe pisze tylko do syserr („Unknown Server Command”). Exe się nie zmienia.

## SQL

`linux-port/docker/mariadb/playerbot/gaya2.sql` (apply.sh, każdy start): `player.player.gaya` i
`player.player_deleted.gaya` (`ADD COLUMN IF NOT EXISTS`, int unsigned, domyślnie 0). Rdzeń db z łatką czyta tę kolumnę
– migrator musi przejść przed rdzeniami (jak `czempion.sql`).

## Questy

- `ygaya.quest`: Sklep Gaya płaci z licznika (`pc.get_gaya` / `pc.change_gaya`), szlifowanie Kamyków dopisuje 3 Gaya
  na licznik, okno sklepu dostaje stan licznika;
- `rekawice`, `ysets`, `yohara_mapy3`: tekst „Gaya biorę z twojego licznika Gaya”;
- `game/Dockerfile`: `pc.get_gaya`, `pc.change_gaya` na liście funkcji `qc`.

## Klient (root, `client-patches/client-2.0.30/root`)

- `gayacurrency.py` (nowy): stan (`constInfo.GAYA`), wiersz ekwipunku, pasek walut (Won / Gaya / Yang) z przyciskiem na
  pasku zadań (na lewo od przycisku postaci; na wąskim ekranie bez przycisku), dymki po polsku, `Have(vnum)` dla okien
  wytwarzania;
- `constinfo.py`: `ENABLE_GAYA_CURRENCY = 1`, **`ENABLE_WON = 0`** – jeden przełącznik Wona (slot w ekwipunku i na
  pasku; włączenie wymaga jeszcze waluty Won na serwerze i `d:/ymir work/ui/game/windows/cheque_icon.sub` w kliencie);
- `uiscript/inventorywindow.py`: wiersz Gaya nad Yang (okno o 22 px wyższe); `uiinventory.py`, `interfacemodule.py`,
  `game.py` (linia `GAYA`) – po jednej linii;
- `uiscript/expandedmoneytaskbar.py` (nowy): pasek walut z paczki „Expanded Money Taskbar”;
- `uicuberenewal.py`, `uicubeokno.py`, `uicube.py`: koszt Gaya czytany z licznika.
- Obrazki: nowa paczka klienta `gaya2` (`client-2.0.30/tools/gaya2`: `build_gaya2_pack.py`, `verify_gaya2.py`,
  `gaya2_files.json`, `pliki/`) – same nowe nazwy `d:/ymir work/ui/gaya2/…` (public.dds paczki jako `gaya2_public.dds`,
  sloty Yang / Won / Gaya, ikona Gaya z „Gaya Taskbar”, przycisk paska).

## Boty

Boty nie trzymają ani nie wydają przedmiotu Gaya (Mistrz Chi bota liczy Gaya w Yang – `playerbot_yohara_chi.h`), więc
kod botów się nie zmienia; Gaya podniesiona przez bota trafia na jego licznik.

Linux/VPS: `python3 apply_gaya2.py <game/src>`; Windows: `Apply-Gaya2Patch.ps1 -SourceDir <game/src>` (wołane przez
`tools/port/Apply-MT2009PlusEngine.ps1` po `npcloc`).
