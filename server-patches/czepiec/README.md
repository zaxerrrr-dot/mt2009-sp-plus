# czepiec – Wężowy Czepiec (hełm 120. poziomu z Krypty Balathora)

Znacznik: `MT2009_PLUS_SERPENT_HOOD_V1`. Właściciel (29.10.2026): „dodaj go do gry” (pl-wiki „Wężowy Czepiec”);
doprecyzowanie: jeden **stały bonus główny** (Mag./krótkodys. atak, rośnie z poziomem ulepszenia) i **jeden drugi
bonus losowany** z listy wiki, który zostaje przy ulepszaniu; bonusy 1–5 i 6/7 jak na każdym hełmie.

## Przedmioty (`tools/czepiec/gen_czepiec.py` → `mariadb/playerbot/yohara_czepiec.sql`, krok `apply.sh`)

Numery klienta GF 26.1.11 (Owsap ich nie ma) – każdy rozpoznany po ikonie (ikona z wiki porównana z każdą ikoną GF):

| vnum | przedmiot |
|---|---|
| 12880–12895 | Wężowy Czepiec+0..+15 – hełm, poz. 120, każda klasa; Obrona 27..233, Mag./krótkodys. atak 1..16% (punkt 132) |
| 31264 | Ścięgno Balathora |
| 31265 | Zroszony Młot (Sklep Gaya, 52 Gaya – rzędy I, II i III, quest `ygaya`) |
| 31266 | Skrzydło Balathora |
| 31267 | Róg Balathora |
| 31268 | Oko Balathora |
| 31269 | Łuska Balathora |

Ulepszanie: `refine_proto` 40500–40514 (+0→+15) – Yang i materiały z wiki (Oko 1..45, Zroszony Młot / Róg do +6,
Łuska od +7, Połyskujące Perły +7..+9, Agat / Dwutlenek Tytanu / Kamień Księżycowy +10..+15). Wiki nie podaje szans –
wzięte z Płaszcza Wężowego (40360–40374: 90, 75, 60, 50, 40, 30, 25, 15, 8, 5, 5, 5, 5, 3, 3%).

Wytwarzanie: Strażnik Smoków Jaharr (20421, okno wytwarzania z questu `helm100`, rozmowa „Wężowy Czepiec”) –
`game/cube.czepiec.txt`: 2 Ścięgna, 7 Zroszonych Młotów, 2 Skrzydła Balathora, 10 Jadeitów Nocy, 40 Wzorów Wężowych,
200 Gaya, 20 000 000 Yang, 50%.

Materiały Balathora: skrzynie Krypty (`game/balathor/special_item_group.balathor.txt`) – zwykła: Skrzydło, Oko ×5,
Róg ×3, Ścięgno; skrzynia+: Skrzydło, Oko ×5, Łuska, Ścięgno (wiki nie podaje ilości ani szans – nasze).

## Silnik – losowy drugi bonus (`edits.json`, 3 edycje w `item.cpp`)

Ten sam mechanizm co losowe bonusy podstawowe wężowego ekwipunku (`server-patches/ysets`): bajt linii w `yextra`
przedmiotu (bity 8–15: bonus 1–9 | wiersz << 4, tabela `player.item_yextra`), losowany w `ITEM_MANAGER::CreateItem`
(nowy przedmiot – też z okna wytwarzania i od GM), przenoszony przy ulepszaniu (`Mt2009YSetsCopy`, ten sam rodzaj),
doliczany w `CItem::ModifyPoints` wg poziomu ulepszenia, widoczny w kliencie przez `YITEM`. Czepiec to rodzaj **2**
(broń 0, zbroja 1) z jedną linią:

| bonus | punkt | +0 | +15 |
|---|---|---|---|
| Wola SungMa (SIŁA / WIT / ODP / INT) | 184 / 185 / 186 / 187 | 1–2 | 34–38 |
| Precyzja | 197 | 1 | 19–22 |
| Odporność na Magię | 77 | 1 | 19–22% |
| Odporność na atak potworów | 142 (`POINT_RESIST_MONSTER_1000PCT`, w tysięcznych: wiki × 10) | 1% | 19–22% |
| Szansa na Blok Ciosu | 67 | 1% | 10% |
| Szansa na uniknięcie Strzały | 68 | 1% | 12% |

Dwa wiersze (najniższa / najwyższa wartość wiki) przy siedmiu pierwszych, jeden przy bloku i uniku. Wartości na każdy
poziom: `tools/czepiec/czepiec_items.json` (`hood`).

Edycje: `(tables)` – tabela i rodzina przed `Mt2009YSetsRandomFamily`, `(roll)` – jedna linia w `Mt2009YSetsRoll`,
`(points)` – punkty w `Mt2009YSetsItemPoints`. **Po `ysets`** (zmienia jego funkcje). Linux/VPS:
`python3 apply_czepiec.py <game/src>` (w `yohara-deploy.sh` po `ysets` – np. na końcu listy); Windows:
`Apply-CzepiecPatch.ps1` (`tools/port/Apply-MT2009PlusEngine.ps1`, na końcu). `gen_edits.py [<game/src>]` tworzy
`edits.json` z tabeli JSON i sprawdza kotwice. db bez zmian.

Bonusy 1–5 (`item_attr`, zestaw hełmu) i 6/7 (`item_attr_rare`, Seon-Hae / 71051 / 71052) – zwykła ścieżka hełmu
(`ARMOR_HEAD`), nic własnego. Efekt zestawu (kowale zestawu) też działa – hełm od 75. poziomu.

## Klient (`client-patches/client-2.0.30/tools/czepiec`)

- `build_czepiec_packs.py` – `gamedata/item_list.txt`, `dbdata` (`gamedata/item_proto`, `locale/pl/itemdesc.txt`):
  22 przedmioty; `verify_czepiec.py` – sprawdza paczki i `root/ysets_hood.py`.
- `root/icon/item/12880.tga`, `31264–31269.tga` (GF 26.1.11), `root/ysets_hood.py` (tabela linii, generowana),
  `root/ysets.py` (ładuje ją; „Losowy bonus podstawowy”, gdy serwer jeszcze nie przysłał linii).
- Hełmy nie są rysowane na postaci w tym kliencie – bez modelu.

## Boty

`tools/yohara_prices/gen_yohara_prices.py` (`MT2009_PLUS_YOHARA_PRICES_REF_V1`): rodzina `czepiec` (+0 ≈ 91 mln – koszt
przepisu u Jaharra, drabina do +9; +10..+15 bez ceny jak bronie wężowe) i `balathor_mat` (Oko / Róg 1,02 mln,
Ścięgno / Skrzydło 3,07 mln, Łuska 4,09 mln – względem Jadeitu Nocy z tej samej skrzyni). Zroszony Młot – towar Sklepu
Gaya, bez ceny (jak inne).
