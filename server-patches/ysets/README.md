# ysets – zestawy ekwipunku i wyposażenie Yohary

`MT2009_PLUS_YOHARA_SETS_V1` (14.10.2026, decyzja właściciela: „Bronie/zbroje Mrocznego Smoka i węży: TAK, razem
z systemem zestawów – wytwarzanie, kowale zestawów, bonusy zestawów, wszystko wg wiki”).

Dane (przedmioty, receptury, tabele bonusów) robi `tools/ysets/gen_ysets.py`; ten katalog to część silnika.

## Efekt zestawu (pl-wiki „Zestaw Ekwipunku”, de-wiki „Set-Effekt”)

- Pięciu Kowali Zestawu w Porcie Nowego Kontynentu (20475–20479) nadaje broni, zbroi albo hełmowi od 75. poziomu,
  ulepszonym co najmniej do +7, jeden z efektów: Święty, Okazały, Rycerski, Książęcy, Majestatyczny
  (szansa 50/40/30/20/15%, 10/30/50/30/30 odłamków II danej części, Projekt Zestawu części, przy majestatycznym
  Kamień Księżycowy, 100 000 000 Yang). Okno kowala to okno wytwarzania (cube): receptura ma `set_value`
  (1–5) i `set_part` (1 broń, 2 zbroja, 3 hełm); przedmiot leży w oknie obok materiałów, nieudana próba zabiera
  materiały i Yang, nigdy przedmiot. Przedmiot z tym samym efektem – odmowa; inny efekt zostaje zastąpiony.
- Bonus zestawu: dwie albo trzy założone części (broń, zbroja, hełm) z tym samym efektem:

| efekt | 2 części | 3 części |
|---|---|---|
| Święty | +500 PŻ, +5% PD | +1500 PŻ, +15% PD |
| Okazały | +500 PŻ, +3% szybkości ruchu | +1500 PŻ, +7% szybkości ruchu |
| Rycerski | +500 PŻ, +1% silny przeciw potworom | +1500 PŻ, +5% silny przeciw potworom |
| Książęcy | – | +2500 PŻ, +10% magia/walka wręcz, +5% szybkości ruchu |
| Majestatyczny | – | +3500 PŻ, +15% magia/walka wręcz, +7% szybkości ruchu |

  (PD = `POINT_MALL_EXPBONUS`, magia/walka wręcz = `POINT_MELEE_MAGIC_ATT_BONUS_PER`, jak Owsap
  `set_item_table.txt`.) Liczone przy założeniu/zdjęciu (`CItem::EquipTo/Unequip`) i w `ComputePoints`.
- Ulepszenie przedmiotu (`CopyAttributeTo`) przenosi efekt na nowy poziom.

## Losowe bonusy podstawowe wężowego ekwipunku (pl-wiki „BronieWężoweWartości”, „ZbrojeWężoweWartości”)

Bronie Wężowe (360, 380, 1210, 2230, 3250, 5200, 7330) i Zbroje Wężowe (21310, 21330, 21350, 21370) mają trzy linie
bonusu: każda to jeden bonus z listy swojej linii z jednym z wierszy wartości (V1..V5) wiki, wartość wg poziomu
ulepszenia +0..+15. Losowane przy powstaniu przedmiotu (`ITEM_MANAGER::CreateItem`), przenoszone przez ulepszenie,
dodawane do punktów w `CItem::ModifyPoints`. Bonusów, których silnik nie ma (potwory Zodiaku, Precyzja, krwawienie,
upadek w %, odporność na potwory), nie ma na liście.

## Zapis i klient

- Każdy przedmiot ma `yextra` (bity 0–3 efekt zestawu, bity 8–31 trzy linie: bonus 1–15 | wiersz << 4) w tabeli
  `player.item_yextra` (id przedmiotu → yextra; `yohara_sets.sql`). Odczyt przy wczytaniu przedmiotu broni / zbroi /
  hełmu od 75. poziomu albo wężowego (`SELECT` po id), zapis przy zmianie (`REPLACE`/`DELETE`). Bez zmian
  w `TPlayerItem`, w serwerze db i w pakietach klienta.
- Klient: `YITEM <okno> <komórka> <yextra>` (1 ekwipunek i założone, 3 magazyn, 0 = wyczyść) przy każdej zmianie
  komórki z takim przedmiotem i po wejściu do gry; `root/ysets.py` + `uitooltip.py` pokazują przedrostek nazwy
  („Święty Miecz Wężowy+7”), linie losowe i efekt zestawu z aktywnym progiem.
- Sklep offline (ikashop) tworzy przedmiot z tym samym id – efekt i linie wracają z tabeli.

Pliki: `item.h`, `item.cpp`, `item_manager.cpp`, `item_attribute.cpp`, `char.h`, `char.cpp`, `char_item.cpp`,
`input_login.cpp`, `safebox.cpp`, `cube.h`, `cube.cpp` (23 edycje, każda ze swoim znacznikiem). Po `talizmanwoli`.

- Linux/VPS: `python3 apply_ysets.py <game/src>`; Windows: `Apply-YSetsPatch.ps1 -SourceDir <game/src>`
  (wołane przez `tools/port/Apply-MT2009PlusEngine.ps1`). `gen_edits.py [<game/src>]` tworzy `edits.json` (z tabel
  `tools/ysets/ysets_random.json`) i sprawdza kotwice.

## Poprawki po teście 3.0 (`MT2009_PLUS_YOHARA_SETS_V2`, `cache/yohara/bledy-3.0.md` #3, #14, #16)

- **Okno kowala zestawów** (#3): lista wyników nie pokazuje już „Projektu” z tym samym Projektem w materiałach.
  Jak w oficjalnym oknie (zrzuty wiki „Zestaw Ekwipunku”) wynikiem jest sam przedmiot: serwer buduje listę z
  ekwipunku gracza przy każdym otwarciu (`cube r_list` / `cube m_info` w `cube.cpp`: każda broń / zbroja / hełm od
  75. poziomu, +7 i wyżej, bez efektu tego kowala), materiały = przedmiot + odłamki II + Projekt (+ Kamień Księżycowy),
  Yang z receptury. `Cube_make` bez zmian (receptura części + przedmiot obok). Klient (`game.py`) nie trzyma listy
  kowali 20475–20479 w pamięci – pyta przy każdym otwarciu. Projekty i odłamki I – drop Królestwa Żywiołów, odłamki
  II – Płaskowyż Sił Natury albo Statua Wojownika (`tools/yohara_maps3`, `cube.ysets.txt`).
- **Kowale w porcie** (#14): w rzędzie wzdłuż muru co dwie komórki (260,566 … 252,574) – punkty Owsapa/GF są co metr
  i modele stały jeden w drugim (krok Dockerfile'a, `gen_ysets.py`).
- **Bonusy wężowe od razu** (#16): `YITEM` jeszcze raz po `CItem::AddToCharacter` (GM `/item`, podniesienie, skrzynia,
  kostka, handel, magazyn) i po `Mt2009YSetsCopy` na przedmiocie gracza; komenda `/yitem` (najwyżej raz na sekundę)
  wysyła wszystko ponownie – klient (`ysets.py`) pyta, gdy dymek pokazuje wężowy przedmiot gracza bez znanych bonusów.
