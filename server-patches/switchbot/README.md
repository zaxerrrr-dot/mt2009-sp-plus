# Bonus Switcher (switchbot z Amerii)

Switchbot z Ameria Project (`srcs/server/game/new_switchbot.cpp/.h`, `char_item.cpp` pod `ENABLE_SWITCHBOT` +
`ENABLE_SWITCHBOT_RENEWAL`; klient `srcs/client/UserInterface/PythonSwitchbot.cpp`, `root/uiswitchbot.py`) zamiast naszej
„Zmiany bonusów” z 6 października (`MT2009_PLUS_BONUS_SWITCH_V1`, `server-patches/bonusswitch` i
`playerbot_bonus_switch.h` – usunięte). Prośba właściciela z 21.10.2026: *„Zamień bonus switcher z naszej wersji na ten z
Amerii, zastosuj nowy kod po stronie serwera jak i klienta.”* Znacznik: `MT2009_PLUS_SWITCHBOT_V1 (…)`.

## Gdzie co jest

| Część | Miejsce |
|---|---|
| Logika serwera | `linux-port/overlays/playerbot/src/game/src/playerbot_switchbot.cpp` (`CSwitchbot`, `CSwitchbotManager` Amerii, `/switchbot`) |
| Haki silnika | `edits.json` (19 zmian w 9 plikach + 3 „reverty” starej zmiany bonusów); `gen_edits.py` je generuje i sprawdza, `apply_switchbot.py` (Linux) i `Apply-SwitchbotPatch.ps1` (Windows, krok `tools/port/Apply-MT2009PlusEngine.ps1` po ekwipunku) czytają ten sam plik |
| Baza | `linux-port/docker/mariadb/playerbot/apply.sh`: `player.switchbot` (pid, slot, cell, used) – w Amerii pliki `local_database/switchbot/pid_<pid>.txt` |
| Exe (3.0) | `client-patches/exe` – `ENABLE_SWITCHBOT` (opis w `client-patches/exe/README.md`) |
| Klient (root) | `client-2.0.30/root/uiswitchbot.py` (okno Amerii), grafiki `root/poza/switchbot/*` (z Amerii); haki w `uiinventory.py`, `game.py`, `keybind.py` |

## Haki silnika (`edits.json`)

| Dopisek | Plik | Co |
|---|---|---|
| `values`, `window` | `common/length.h` | `SWITCHBOT_SLOT_COUNT` 5, `SWITCHBOT_ALTERNATIVE_COUNT` 5, `SWITCHBOT_ATTR_COUNT` 5; okno `SWITCHBOT` = 16 (po `CHEST_INVENTORY`). Żaden przedmiot nie jest w tym oknie zapisywany – `player.item.window` bez zmian |
| `cg header`, `gc header`, `gg header`, `structs` | `packet.h` | CG 170, GC 171, GG 39 (wolne numery – sprawdzone z `packet.h` serwera i `Packet.h` exe), struktury ze stałymi rozmiarami (`static_assert`) |
| `cg size`, `gg size` | `packet_info.cpp` | rejestracja pakietów (CG z bajtem sekwencji, jak u Amerii `SendSequence`) |
| `packet`, `move`, `use` | `input_main.cpp` | pakiet switchbota; przeciągnięcie do/z pola switchbota i użycie pola (zdjęcie przedmiotu) |
| `p2p` | `input_p2p.cpp` | stan switchbota przechodzi z graczem na inny rdzeń |
| `warp`, `channel`, `logout` | `char.cpp` | przed pakietem teleportu (WarpSet, zmiana kanału) i przy wylogowaniu |
| `equip`, `swap` | `char_item.cpp` | przedmiotu w polu switchbota (zablokowanego) nie da się założyć ani zamienić miejscami |
| `declare`, `table` | `cmd.cpp` | `/switchbot` |
| reverty | `cmd.cpp`, `cmd_general.cpp` | usuwają linie starego `/bonus_switch`, jeśli są (drzewo testowe); na świeżym silniku nic nie robią |

## Zasady (jak w Amerii)

- 5 pól, w każdym jeden przedmiot z ekwipunku: broń albo zbroja, hełm, tarcza, bransoleta, buty, naszyjnik, kolczyki,
  talizman, rękawice (`MT2009_PLUS_SWITCHBOT_GLOVE_TALISMAN_V1`, lista właściciela z 3.11.2026), kostium, fryzura,
  nakładka na broń (`MT2009_PLUS_SWITCHBOT_COSTUME_V1`) – bez strzał/kołczanów, wierzchowców i szarf. Przedmiot zostaje na swoim miejscu w torbie, zablokowany –
  nie da się go przenieść, założyć, sprzedać, wymienić ani schować, dopóki jest w polu.
- Na pole do 5 „alternatyw” po 5 bonusów z minimalną wartością; pole kończy, gdy przedmiot ma wszystkie bonusy jednej
  ustawionej alternatywy. Okno pokazuje 2 alternatywy (Ameria odblokowywała 3–5 płatnym „premium switchbotem” – pominięte).
- Zmiana co 0,2 s na każde aktywne pole (zwykłe `ChangeAttribute` silnika). Koszt: 1 Zaczarowanie Przedmiotu na zmianę,
  w kolejności 39028, 71084, 76014, 71284, 71151 (71151 tylko broń / zbroja do 40 poziomu). Kostium, fryzura i nakładka:
  tylko 70064 Zaczaruj kostium (jak ręcznie – ta sama liczba bonusów; los z inną liczbą przywraca stare bonusy, nie
  zabiera przedmiotu i zatrzymuje pole). Okno pod Start/Stop pokazuje, który przedmiot zużywa wybrane pole. Liczone i zabierane także z
  dodatkowego ekwipunku (zakładka Zaczarowania). Brak zaczarowań – switchbot staje.
- Koniec: szept od „[Switchbot]” z nazwą przedmiotu, numerem pola i liczbą zużytych zaczarowań. Przerwa, gdy gracz nie
  może działać (śmierć, handel, sklep, magazyn, kostka, trwający quest, teleport).

## Różnice względem Amerii

- Pola gracza w bazie (`player.switchbot`) zamiast plików tekstowych (system plików kontenera nie jest trwały).
- Bez gałęzi Zodiaku Amierii (jej własne zaczarowanie 94912 – u nas 94912 to talizman): przedmioty Zodiaku używają
  tych samych zaczarowań, jak ręcznie.
- Bez „premium switchbota” (Ameria: przedmiot 50027 + afekt; u nas 50027 to Bilet Na Loterię).
- Przedmiot bez bonusów (albo bez zestawu bonusów) zatrzymuje pole – ręcznie silnik też go odrzuca.
- Każda zmiana w logu przedmiotów (`CHANGE_ATTRIBUTE`, podpowiedź `switchbot`), jak ręcznie.
- Prawdziwe wylogowanie zatrzymuje pola (Ameria trzymała je w pamięci rdzenia); teleport i zmiana kanału nie.
- Pakiety o stałych rozmiarach pól (`WORD size`, `DWORD vnum` – w Amerii `vnum` był `BYTE`).
- Tylko gracz z nowym exe: klient wysyła `/switchbot hello` po wejściu do gry i po teleporcie (tylko gdy exe ma moduł
  `switchbot`); bez tego serwer nie wysyła pakietu 171 (stary exe by się zamknął). Boty nigdy.

## Komendy

`/switchbot hello` (root/uiswitchbot.py). Reszta to pakiety: CG 170 (`START` + 5 alternatyw / `STOP`), GC 171
(`UPDATE` – cała tabela, `UPDATE_ITEM` – nowe bonusy przedmiotu, `SEND_ATTRIBUTE_INFORMATION` – bonusy i maksima
każdego zestawu z `item_attr`), GG 39.

Lista bonusów do wyboru i ich maksima (`MT2009_PLUS_SWITCHBOT_ATTR_VALUES_V1`): wartości liczone tak jak przy
losowaniu (`BonusModeSetAttrValue`, `playerbot_bonus_mode.cpp`) – w trybie `M2_BONUS_MODE=global` talizman ma odporność
na ogień / błyskawice / wiatr do 25% (5% na poziom), a nie 15% z wiersza zbroi. Wiersz, który się właśnie wybiera,
widzi na liście swój własny bonus (ukryte są tylko bonusy pozostałych wierszy tej alternatywy).
