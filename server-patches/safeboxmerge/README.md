# Magazyn: „Tylko scal stosy”

Poprawka silnika `game/src/cmd_general.cpp` (`do_safebox_arrange`), znacznik
`MT2009_PLUS_SAFEBOX_MERGE_V1`. Nakładana raz, przy przygotowaniu wydania
(`tools/port/Apply-MT2009PlusEngine.ps1`); `Apply-SafeboxMergePatch.ps1`
i linuksowy bliźniak `apply_safeboxmerge.py` czytają ten sam `edits.json`.

## Co robi

Okno magazynu ma dwa przyciski obok tytułu, jak ekwipunek („Scal i uporządkuj”):

- **Ułóż i scal** – `/safebox_arrange` (było w silniku): serwer łączy stosy
  i układa przedmioty na stronach magazynu;
- **Tylko scal stosy** – `/safebox_arrange merge` (ta poprawka): serwer tylko
  łączy stosy tego samego przedmiotu, reszta zostaje na swoich miejscach.

Obie odpowiadają `SafeboxArrangeResult <kod> <przestawione> <scalone> <sztuki>`
(klient: `uisafebox.py`, `game.py`). Pracę robi
`playerbot_arrange::MergeSafeboxStacks` (`linux-port/overlays/playerbot/.../playerbot_arrange.cpp`):
te same przelania co przy pełnym układaniu, bez przestawiania, ten sam limit
2 s między kliknięciami. Pakiet przenoszenia w magazynie nie łączy stosów
(`ENABLE_MT2009_DISABLE_SAFEBOX_STACK`), więc scalanie idzie jedną komendą.

Zmiana już nałożona (jest jej znacznik) jest pomijana; zmiana, której kodu nie
ma dokładnie raz, przerywa całość, zanim cokolwiek zostanie zapisane.

## Magazyn botów: 4 strony bez misji (`MT2009_PLUS_BOT_SAFEBOX_PAGES_V1`)

Trzy kolejne zmiany w tym samym `edits.json`:

- `common/length.h` – nowa stała `SAFEBOX_BOT_PAGE_COUNT = 4`, a `SAFEBOX_MAX_NUM`
  (tablica wskaźników `CSafebox`) liczy się od niej: 180 pól zamiast 135.
  `SAFEBOX_PAGE_COUNT = 3` zostaje bez zmian, więc magazyn ludzi i Item-Shop
  (`OpenMall`) działają jak dotąd;
- `input_db.cpp` (`CInputDB::SafeboxLoad`) – postać, której pid jest botem
  (`CPlayerBotManager::IsRegisteredBotPID`), dostaje `SAFEBOX_BOT_PAGE_COUNT` stron
  od razu, bez misji u Magazyniera. Ludzie dalej: 1 strona za 500 Yang, 2 po misji,
  +1 premium;
- `char.cpp` (`LoadSafebox`) – górna granica `SAFEBOX_BOT_PAGE_COUNT` zamiast
  `SAFEBOX_PAGE_COUNT` (człowiek i tak nie przekroczy trzech).

Boty nie mają wiersza w tabeli `safebox` (pakiet zmiany rozmiaru to `UPDATE`
nieistniejącego wiersza), więc po każdym restarcie serwera ich magazyn otwierał się
z jedną stroną – stąd „safebox full”. Liczbę stron botów zmienia się jedną stałą;
zmniejszenie jej później niczego nie kasuje (przedmioty z dalszych stron zostają
w bazie, tylko nie są wczytywane). Klient sam układa tyle zakładek, ile stron
przyśle serwer (`CPythonSafeBox::OpenSafeBox`, `uisafebox.py`), więc człowiek
zalogowany na postać bota zobaczy cztery strony.
