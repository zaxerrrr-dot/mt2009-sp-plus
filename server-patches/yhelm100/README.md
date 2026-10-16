# yhelm100 – okno wytwarzania Strażnika Smoków Jaharra (hełmy na 100 poziom)

`MT2009_PLUS_HELM100_CUBE_V1` (runda poprawek 15.10, nr 3; właściciel: „tak jak u innych NPC, np. Mistrz →
Wytwarzanie pasów”). Hełmy na 100 poziom (`MT2009_PLUS_HELM100_V1`, `tools/yhelm100`) robi się w oknie wytwarzania
(cube), nie przez przeciąganie hełmu na NPC:

- receptury: `linux-port/docker/game/cube.helm100.txt` (generuje `tools/yhelm100/gen_yhelm100.py`), dopisywane do
  `cube.txt` przez Dockerfile; 40 receptur (4 hełmy 80. poziomu × +5..+9 × Smoków / Dragona), silnik łączy plusy
  jednego hełmu w jeden wiersz („+5 lub +6 … lub +9”), więc okno ma 8 wierszy – zawsze wszystkie, niezależnie od
  ekwipunku; quest `helm100` otwiera okno (rozmowa albo przeciągnięcie hełmu na Jaharra);
- Smoków: 5 Rogów, 5 Łusek, 10 Planów, 1 000 000 Yang, 30–70% wg plusa – zwykła receptura: porażka zabiera hełm
  i materiały;
- Dragona: 5 Rogów, 5 Łusek, 5 Planów, 3 Skrzydła Smoka, 1 000 000 Yang, 10–50% wg plusa – linia
  `fail_keep <vnum hełmu>`: porażka zabiera materiały i Yang, hełm zostaje (w ekwipunku i w oknie);
- receptury Dragona stoją w pliku przed Smoków: `FN_find_cube` bierze pierwszą pasującą, więc okno ze Skrzydłami
  Smoka robi hełm Dragona, bez nich – hełm Smoków.

Silnik (ta łatka, cztery edycje z własnymi znacznikami): `cube.h` – `CUBE_DATA::fail_keep`; `cube.cpp` – linia
`fail_keep` przy wczytywaniu, `Mt2009CubeMakeFailKeep` (sukces: wszystko jak zwykle; porażka: materiały oprócz
`fail_keep`, Gaya i Yang) i wywołanie w `Cube_make`. Po `gaya` (używa `Mt2009GayaCubeCheck/Take`).

Linux/VPS: `python3 apply_yhelm100.py <game/src>`; Windows: `Apply-YHelm100Patch.ps1 -SourceDir <game/src>` (wołane
przez `tools/port/Apply-MT2009PlusEngine.ps1`). `gen_edits.py [<game/src>]` tworzy `edits.json` i sprawdza kotwice.
