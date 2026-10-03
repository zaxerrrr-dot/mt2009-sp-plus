# Poprawki i stosy Digi Rasty (3 października)

**Autor: Digi Rasta** (paczka „nowy-system” v0.23.0, zbudowana na modzie 2.19.0). Przeniesione do MT2009 PLUS
jako nasz kod – bez haków `zastosuj.py`, tak jak jego wcześniejsze systemy (`server-patches/digirasta`):
zmiany silnika są tutaj (`edits.json`), baza w `apply.sh`, klient w `client-patches/client-2.0.30`.
Znaczniki: `MT2009_PLUS_DIGI_FIXES_V1` (poprawki błędów), `MT2009_PLUS_DIGI_STACK_V1` (stosy).

## Zmiany silnika (`edits.json`)

| Znacznik | Plik | Co robi |
|---|---|---|
| `MT2009_PLUS_DIGI_FIXES_V1 (safebox grid)` | `safebox.cpp` | `CSafebox::ChangeSize`: siatka sprawdzana po `std::move` była zawsze pusta, więc powiększony **otwarty** magazyn nie znał zajętych pól (przedmiot mógł wejść na inny) – siatka budowana od nowa z przedmiotów |
| `MT2009_PLUS_DIGI_FIXES_V1 (cube reload include)`, `(cube reload)` | `cube.cpp` | `/reload c` wczytywał receptury, ale listy okna kostki (`cube_info_map`) budowały się raz na start – teraz budowane od nowa, otwarte okna kostki zamykane, gracz dostaje `CubeReload` (klient zapomina swoje listy, `game.py`) |
| `MT2009_PLUS_DIGI_STACK_V1 (refine stack helpers)` | `char_item.cpp` | `DigiStackRefineAllowed` / `DigiStackRefineSplit` (niżej) |
| `MT2009_PLUS_DIGI_STACK_V1 (do refine room)`, `(scroll room)` | `char_item.cpp` | `DoRefine` / `DoRefineWithScroll`: stos da się ulepszyć tylko z wolnym polem w ekwipunku (i nigdy recepturą, która bierze jego własny vnum) – sprawdzane, zanim cokolwiek zostanie zabrane |
| `MT2009_PLUS_DIGI_STACK_V1 (do refine split)`, `(scroll split)` | `char_item.cpp` | po sprawdzeniach i opłacie: w polu stosu zostaje **jedna** sztuka, reszta przechodzi na wolne pole (te same gniazda i bonusy, nowy przedmiot) – sukces, porażka i obniżenie dotyczą tylko tej sztuki |
| `MT2009_PLUS_DIGI_STACK_V1 (socket one stone)` | `char_item.cpp` | osadzenie kamienia duchowego zabiera jedną sztukę ze stosu (było: cały przedmiot) |

U niego ulepszenie zdejmowało sztukę ze stosu i wynik szedł na wolne pole – a bez wolnego pola na pole stosu
(dwa przedmioty w jednym polu); zwoju nie obsługiwał. Tu stos jest dzielony przed rzutem, więc cała dalsza
ścieżka (`DoRefine`, zwoje, Rytuał / kamienie +4…+8 z `playerbot_awakening.h`, boty) działa na pojedynczej
sztuce bez zmian. Kamień ulepszany przez bota (`ManagePlayerBotSoulStoneStep`) zostaje w swoim polu, jak dotąd.

Poprawki `MountSystem.cpp` z tej samej paczki przenosi osobna zmiana (nie tutaj). „Biore” i recykling – nie
w tym zakresie.

- `Apply-DigiRastaFixesPatch.ps1` – Windows (`tools/port/Apply-MT2009PlusEngine.ps1`, po pozostałych łatkach);
- `apply_digirasta_fixes.py <game/src>` – Linux/VPS; oba czytają ten sam `edits.json`.

Zmiana już nałożona (jest jej znacznik) jest pomijana; zmiana, której kodu nie ma dokładnie raz, przerywa
całość, zanim cokolwiek zostanie zapisane.

## Stosy 200 (`apply.sh`, blok `MT2009_PLUS_DIGI_STACK_V1`)

Jak jego `20_stakowanie.sql`, przy każdym starcie, idempotentnie:

- każdy kamień duchowy (typ 10: +0…+9, pęknięty kamień, Kamień Przebudzenia), każda skrzynia-prezent
  (typ 23: szkatułki bossów – dotąd po 10, Cory, szkatułki ebonitowe…) i szkatułki / skrzynie z jego listy
  (typy 3, 5, 18, 20: Złota / Srebrna Szkatułka – dotąd po 20, skrzynie 30300, 38054…, 50130…): flaga
  `STACKABLE`, **bez `ANTI_STACK`**, stos 200. Jego plik zostawiał `ANTI_STACK`, przez co 222 skrzynie i tak
  się nie łączyły (silnik i boty łączą tylko `STACKABLE` bez `ANTI_STACK`);
- Odłamek Smoczego Kamienia (30270) bez limitu 24 h (każda sztuka miała inny czas w `socket0`, więc żadne
  dwie się nie łączyły) – sztuki graczy też go tracą (`player.item.socket0 = 0`).

Stos to cecha proto – przedmioty w bazie nie wymagają zmian (poza odłamkiem). Silnik łączy tylko sztuki
o równych gniazdach.

## Klient

- `client-patches/client-2.0.30/tools/digirasta/patch_digirasta_stack.py` – te same stosy w `item_proto`
  klienta (listy jak w `apply.sh`);
- `root/uiinventory.py` – kamień upuszczony na ten sam kamień łączy stos (zamiast pytać o gniazdo);
- `root/game.py` – komenda `CubeReload` (`MT2009_PLUS_DIGI_FIXES_V1`);
- `root/uitip.py` – ogłoszenia bez kodów koloru `|c…|r` i linków `|H…|h` (rysowało je dosłownie i psuło
  środkowanie; `MT2009_PLUS_DIGI_FIXES_V1`).
