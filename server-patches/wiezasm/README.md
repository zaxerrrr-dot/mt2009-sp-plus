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

## Użycie przedmiotów questowych (`MT2009_PLUS_QUEST_USE_V1`, 21.10.2026)

Silnik (`char_item.cpp`, `CHARACTER::UseItemEx`, `case ITEM_QUEST`) przekazywał „użycie” do questa tylko przedmiotom
**bez** flagi `ITEM_FLAG_QUEST_USE` / `_MULTIPLE` – a generatory przedmiotów Yohary stawiają ją właśnie na przedmiotach,
które quest obsługuje po kliknięciu (`when <vnum>.use`). Prawy klik nic nie robił: Zagadkowy Klucz 70403 i Antidotum
SungMa 70405 (ta wieża), Kamień Metin z Yohara 72339, Pierścień Siły Natury 39114/39116 i Medal 39113, Reset /
Rozszerzenie Sklepu Gaya 39063/39064, Pył Węża 70428, Wejście do Świątyni Węży 70430, Pierścień Smoczego Ognia 30340,
31189/31191 (PB Nemere). Edycja usuwa ten warunek – przedmiot bez obsługi w queście nadal nic nie robi. Żaden nasz quest
nie liczy na to, że flaga wycisza „use” (brak ogólnego `when use`).

Linux/VPS: `python3 apply_wiezasm.py <game/src>`; Windows: `Apply-WiezaSmPatch.ps1 -SourceDir <game/src>` (wołane przez
`tools/port/Apply-MT2009PlusEngine.ps1`). Pliki silnika: `char_skill.cpp`, `char_item.cpp` (lista `launcher/server-update-files.mod.txt`).

`MT2009_PLUS_SMH_TOWER_V2` (właściciel 21.10: „tak, zablokuj”): w Piekielnej Wieży (mapa 387 i jej instancje) działają
tylko mikstury wieżowe (W) 70390–70395 – zwykłe mikstury (USE_POTION, USE_POTION_NODELAY, USE_POTION_CONTINUE) i
autoeliksiry (Eliksir Słońca/Księżyca 72723–72730, 39037–39042) są odrzucane, a włączony wcześniej autoeliksir nie leczy
w wieży (`AutoRecoveryItemProcess`). Edycje `(other potions)` i `(auto potions)` w `char_item.cpp`.
