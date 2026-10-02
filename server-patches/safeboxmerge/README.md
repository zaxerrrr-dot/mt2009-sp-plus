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
