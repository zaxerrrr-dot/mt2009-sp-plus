# Druga strona ekwipunku („Official Additional Equipment Page”)

Paczka „Official Additional Equipment Page” (`/opt/metin2/cache/addeqpage/Official-Additional-Equipment-Page-main`,
65 plików: serwer, `DumpProto`, źródła klienta, root, uiscript, locale) przeniesiona na naszą bazę – prośba właściciela
z 28.10.2026: *„Add this too to the client.”* Znacznik: `MT2009_PLUS_ADDEQ_V1 (…)`.

## Co robi paczka

Drugi zestaw slotów ekwipunku (zbroja, hełm, buty, bransoleta, broń, naszyjnik, kolczyki, strzały, tarcza, pas, talizman,
rękawice). Odblokowuje go przedmiot 38306 (związany) albo 76055 (wymienny), który daje umiejętność pomocniczą 200
„Zmiana strony ekwipunku”; stronę przełącza ta umiejętność albo zakładki okna ekwipunku (pakiet CG 208
`ChangeEquipment`), raz na 5 s, nie przy handlu / sklepie / magazynie / kostce. Bonusy daje tylko aktywna strona.

W paczce obie strony są **założone**: 12 nowych pól `WEAR_SECOND_*`, przenumerowany `EWearPositions` (bez
`WEAR_ABILITY*`, pierścienie przeniesione na koniec), nowe `EItemWearableFlag`, kolumna `player.equip_index`, a każde
`GetWear(WEAR_WEAPON)` silnika (walka, umiejętności, łowienie, kopanie, koń, questy) zamienione na `GetEquipWear`. Klient
przemapowuje sloty okna (`SetSlotChange`). To nowy układ pól ekwipunku – stary klient (numery pól ekwipunku, Smoczych
Kamieni i pasa są w nim na sztywno) by go nie przyjął, a każdy nasz system czytający `GetWear` musiałby się zmienić.

## Jak to działa u nas

- **Magazyn nieaktywnej strony**: 32 ukryte pola postaci (jedno na pole ekwipunku) zaraz za ekwipunkiem pasa –
  `MT2009_ADDEQ_SLOT_START = BELT_INVENTORY_SLOT_END` (308) … 339, w bazie zwykłe wiersze `player.item` z oknem
  `INVENTORY` i `pos` 308–339 (enum okien w bazie i w kliencie bez zmian). `INVENTORY_AND_EQUIP_SLOT_MAX` zostaje
  granicą `TItemPos` i `GetItem`, więc żaden pakiet klienta nie sięga do magazynu, a serwer nigdy go nie wysyła
  (`SetItem`, `UpdatePacket`) – **stary klient widzi tylko założoną stronę, bez zmian w pakietach**. Przełącznik
  serwera (jak `M2_SPIDER3_ON`) nie jest potrzebny.
- **Przełączenie** (`CHARACTER::Mt2009AddeqSwitch`): przedmioty założone na stronicowanych polach idą do magazynu,
  magazyn na te pola – zwykłe `Unequip` / `EquipTo` silnika, więc bonusy, wygląd, bonusy zestawów, liczniki czasu i
  zdarzenia akcesoriów są takie jak przy ręcznej zmianie, a liczy się tylko założona strona.
- **Stronicowane**: `WEAR_BODY`, `HEAD`, `FOOTS`, `WRIST`, `WEAPON`, `NECK`, `EAR`, `ARROW`, `SHIELD`, `PENDANT`
  (talizman), `GLOVE`. **Wspólne**: pierścienie (`UNIQUE1/2`), kostiumy, wierzchowiec, szarfa, aura, sloty Buffi i
  **pas** (w paczce stronicowany – u nas trzyma ekwipunek pasa, którego przełączenie nie przeniesie).
- **Zasady**: odblokowana strona, nie martwy / ogłuszony / przemieniony / przy łowieniu / kopaniu, bez okien handlu,
  sklepu, magazynu, kostki, raz na 5 s (paczka) i 1,5 s po ataku lub umiejętności („stój spokojnie”, jak przy
  zakładaniu). Najpierw sprawdzane wszystko: każdy przedmiot drugiej strony musi pasować do postaci teraz (klasa, płeć,
  poziom, Poziom Czempiona, statystyki) i każdy założony musi dać się zdjąć (nie `IRREMOVABLE`, nie zablokowany) –
  inaczej nic się nie rusza, czat podaje przedmiot. Kostium broni, który nie pasuje do broni nowej strony, idzie do torby.
- **Stan**: flagi questowe `addeq.unlocked` (1) i `addeq.page` (0 = I, 1 = II); umiejętność 200 na poziomie 1 (reset
  umiejętności jej nie zabiera, `hello` przywraca). Pierwsze przełączenie na II: druga strona jest pusta, zakłada się na
  nią przedmioty zwyczajnie.
- **Przedmioty** 38306 „Strona ekwipunku II” (bez handlu / sklepu / magazynu / upuszczenia) i 76055 „Strona ekwipunku II
  (wymienna)” (stos 200, handel) – `ITEM_USE` / `USE_SPECIAL`, pytanie przed użyciem, raz na postać
  (`Mt2009AddeqUseItem`). Nigdzie ich nie dodano (sklep, drop) – decyzja właściciela.
- **Boty**: nic (nie mają przedmiotu ani hello). Ich drugi zestaw (`playerbot_element_second_set.h`) zamienia całe
  komplety przez torbę – później może użyć tego magazynu (`Mt2009AddeqSwitch`) zamiast torby.

## Gdzie co jest

| Część | Miejsce |
|---|---|
| Logika serwera | `linux-port/overlays/playerbot/src/game/src/playerbot_addeq.cpp` (metody `CHARACTER`, `/addeq`) |
| Haki silnika | `edits.json` (13 zmian w 6 plikach: `char.h`, `char_item.cpp`, `char.cpp`, `item.cpp`, `char_skill.cpp`, `cmd.cpp`); `gen_edits.py` je generuje i sprawdza, `apply_addeq.py` (Linux, ostatni krok `yohara-deploy.sh` – po `balathor`) i `Apply-AddeqPatch.ps1` (Windows, ostatni krok `tools/port/Apply-MT2009PlusEngine.ps1`) czytają ten sam plik |
| Baza | `linux-port/docker/mariadb/playerbot/addeq.sql` (`tools/addeq/gen_addeq.py`; krok w `apply.sh`) – tylko dwa przedmioty; bez `skill_proto` (200 obsługuje silnik przed tabelą) i bez kolumn |
| Exe | `client-patches/exe` – `ENABLE_MT2009_ADDEQ` (umiejętność 200 jak Kombo; `app.ENABLE_MT2009_ADDEQ`) |
| Klient (root) | `client-2.0.30/root/uiaddeq.py` (zakładki I / II), haki w `uiinventory.py`, `game.py`, `playersettingmodule.py`, `uicharacter.py`; ikona `root/icon/item/38306.tga` |
| Dane klienta | `client-2.0.30/tools/addeq` – paczka `addeq` (ikona umiejętności), `gamedata`/`dbdata` (przedmioty, `skilldesc`, `skilltable`), `verify_addeq.py` |

## Haki silnika (`edits.json`)

| Dopisek | Plik | Co |
|---|---|---|
| `cells`, `slots`, `methods` | `char.h` | `MT2009_ADDEQ_SLOT_START/END`, `PlayerSlotT::pAddeqItems[WEAR_MAX_NUM]`, metody `Mt2009Addeq*` |
| `set` | `char_item.cpp` | `SetItem` pola magazynu → `Mt2009AddeqSetItem` (bez pakietu) |
| `clear` | `char_item.cpp` | `ClearItem` niszczy też magazyn (jak torbę) |
| `use` | `char_item.cpp` | `UseItemEx`: 38306 / 76055 |
| `flush` | `char.cpp` | `FlushDelayedSaveItem` (przed teleportem) zapisuje magazyn |
| `remove` | `item.cpp` | `RemoveFromCharacter` przedmiotu z magazynu czyści jego pole |
| `update` | `item.cpp` | `UpdatePacket` przedmiotu z magazynu nie idzie do klienta |
| `skill` | `char_skill.cpp` | `UseSkill(200)` przełącza stronę (przed `CanUseSkill`) |
| `reset` | `char_skill.cpp` | `ResetSkill` zostawia 200 |
| `declare`, `table` | `cmd.cpp` | `/addeq` |

## Komendy

	/addeq hello      po każdym wczytaniu (root) – odpowiedź "addeq_page <odblokowana 0/1> <strona 0/1>"
	/addeq 0 | 1      zakładka I / II
	/addeq toggle     druga strona

Log: `ADDEQ: <postać> (<pid>) page <1|2>, <n> slot(s) swapped`, `... unlocked the second page with <vnum>`.
