# wiezasm – Wieża Sung Mahi (Yohara)

`MT2009_PLUS_SMH_TOWER_V1` (14.10.2026, decyzja właściciela: „Jaskinie Gnolli 1/2/3 i Wieża Sung Mahi – dodać”,
wszystko wg pl-wiki, czego brak – wg wiki TR).

Wiki („Wieża Sung Mahi”): na każdym etapie piętra gracz dostaje losowy bonus albo klątwę; jedna z klątw to
**„Umiejętności są zablokowane”**. Quest `wieza_sung_mahi` nakłada ją afektem **1849** na wszystkich w instancji
(`d.affect_all(1849, 0, 0, …)`) i zdejmuje po etapie (`d.remove_affect_all(1849)`).

- Silnik: `char_skill.cpp`, `CHARACTER::UseSkill` – z afektem 1849 każda umiejętność jest odrzucana z komunikatem
  „Klatwa Sunga Mahi blokuje twoje umiejetnosci.” (jedna zmiana, znacznik `MT2009_PLUS_SMH_TOWER_V1 (skills)`).
- Mikstury wieży 70390–70395 (Handlarka 9014 w hali, `MT2009_PLUS_SMH_SHOP_V1`): `char_item.cpp`,
  `CHARACTER::UseItem` – poza mapą 387 (i jej instancjami) odmowa z komunikatem „Tego przedmiotu mozna uzyc tylko w
  Piekielnej Wiezy Sunga Mahi.” (znacznik `MT2009_PLUS_SMH_TOWER_V1 (potions)`), jak oficjalnie.
- Pozostałe bonusy i klątwy (wartość ataku, obrona, PŻ, prędkości, regeneracja, odporności, Wola SungMa, precyzja)
  to zwykłe punkty – afekt 1847 questa, bez zmian w silniku.
- Wymagania Woli SungMa pięter (co pięć pięter wyżej: 35/25/35/55 … 70/58/70/90) – `d.set_sungma(str, hp, move,
  immune)` / `d.clear_sungma()` z nakładki `playerbot_champion.cpp` (`MT2009_PLUS_YOHARA_DUNG4_V1 (sungma)`;
  wymaganie instancji zamiast wiersza mapy w `sungma_table.txt`) – nie jest częścią tej łatki.

Linux/VPS: `python3 apply_wiezasm.py <game/src>`; Windows: `Apply-WiezaSmPatch.ps1 -SourceDir <game/src>` (wołane przez
`tools/port/Apply-MT2009PlusEngine.ps1`). Pliki silnika: `char_skill.cpp`, `char_item.cpp` (lista `launcher/server-update-files.mod.txt`).
