# Płaskowyż Iluzji, Beran-Setaou (PB) i Jotun Thrym (PB) (MT2009_PLUS_YOHARA_ILUZJA_V1)

Decyzja właściciela 14.10.2026 (`cache/yohara/decyzje.md`, ostatnie linie): „dodać Płaskowyż Iluzji jako hub lochów PB
(Statua Przebudzenia, Handlarka Iluzji, Statua Kowala Zbroi, Statua Fabryki Broni, Teleporter); dodać Beran PB i Jotun
PB”. Wszystko wg pl-wiki („Płaskowyż Iluzji”, „Grota Wygnańców 2 (PB)”, „Świątynia Smoka (PB)”, „Zaklęty Las (PB)”,
„Erebu (PB)”, bossowie, skrzynie, „Wytwarzanie Broni / Zbroi”), źródła planów, których pl-wiki nie podaje – de-wiki
(„EW: …entwurf”); przebieg, pozycje, liczby i receptury – Owsap v6.2.6 (`awaken_skipia_dungeon.quest`,
`awaken_dawnmist_dungeon(_access).quest`, `labyrinth_dungeon.quest`, `cube.txt`). Pliki tego katalogu i wiersze bazy
robi `tools/yohara_iluzja/gen_yiluzja.py` (nie edytować ręcznie). Rdzeń: Yohara (game3). Klient:
`client-patches/client-2.0.30/tools/yiluzja`.

| indeks | miejsce | folder | teren | quest |
|---|---|---|---|---|
| 397 | Płaskowyż Iluzji | metin2_map_labyrinth (1×1, baza 307200 1792000) | GF | `przebudzeni_bossowie` |
| 398 | Grota Wygnańców 2 (PB) + Świątynia Smoka (PB) | metin2_map_boss_awaken_skipia (6×6, baza 0 1971200) | GF Grota Wygnańców 2 + własny sektor 000000 GF (świątynia otwarta) | `beran_pb` |
| 371 | Zaklęty Las (PB) + Erebu (PB) | metin2_map_boss_awaken_dawnmist (3×4, baza 332800 1971200) | GF metin2_map_dawnmist_dungeon_01 | `jotun_pb` |

Indeksy: oficjalny 371 (wolny u nas); oficjalne 363 (płaskowyż) i 368 (grota) są u nas zajęte (Komnata Wiedzy, Port
Nowego Kontynentu) – stąd 397 i 398. W kliencie obie mapy lochów to **pełne** foldery (exe 2.0.25 czyta `attr.atr`
kopii mapy z rodzica, a sektor 000000 groty PB otwiera świątynię, którą zwykła Grota 2 ma zamkniętą; rodzica lasu nie
ma żaden nasz klient).

## Płaskowyż Iluzji (397)
- Wejście: **Statua Iluzji** (20470) w Yongan 540,500, Joan 688,748, Pyungmoo 342,800 – „Płaskowyż Iluzji” (od 110
  poziomu). Tam też Codzienna misja „Świat Iluzji” (Razador i Nemere – zwykłego Jotuna Thryma u nas nie ma) i okno
  **kamieni przebudzenia** (5 Małych + Dusza = Drobny 45%, 3 Drobne → Ładny 35%, 2 Ładne → Zacny 30%, Zacny → Silny
  25%; 200–500 tys. Yang – Owsap `cube.txt` 20470).
- Bez potworów; poniżej 110 poziomu (nie GM) – do wioski. NPC na komórkach z wiki: **Statua Przebudzenia** 153,89
  (cztery lochy), **Statua Fabryki Broni** 141,181, **Statua Kowala Zbroi** 113,179, **Teleporter** 127,190 (zwykły
  quest `map_warp`), **Handlarka Iluzji** 128,98 (u nas 20469 – nasz 9013 to Pomocnik Zdarzeń; sklep 9551:
  Czerwona / Niebieska Mikstura (XXL) po 20 i 200, Transformuj / Zaczaruj Kostium). **Statua Szczeliny Czasu** 103,90 – od
  MT2009_PLUS_YOHARA_CRACK_V1 (`../yohara_crack`: Zaklęty Las (SZC), quest `szczelina_czasu`).
- **Statua Przebudzenia**: Grota Wygnańców 2 (PB), Twierdza Czerwonego Smoka (PB), Strażnica Nemere (PB), Zaklęty Las
  (PB) – od 110, tylko w grupie (min. 2 ludzi, GM sam), otwiera przywódca, każdy ma Książkę Przebudzenia (zabierana
  przy wejściu do nowej wyprawy), do Strażnicy Nemere Ninja i Szaman. 60 minut; po zwycięstwie (minuta) lub po czasie
  – z powrotem na płaskowyż (obok statui). „Wróć do lochu” – do trwającej wyprawy. Panel lochów: `beran_pb`,
  `jotun_pb` (i `razador_pb`, `nemere_pb`) – wejście na płaskowyżu.
- **Statua Fabryki Broni** / **Statua Kowala Zbroi** (rozmowa albo przeciągnięcie przedmiotu): ekwipunek Smoka Mroku
  +0 (Owsap `cube.txt` 20473/20474 = wiki): broń – 10 Kowadeł, 5 planów (PB), 5 Środków Ściernych, 5 Stali; zbroja –
  10 Zwykłych Skór, 5 planów, 5 Cienkich Przędz, 5 Oznak Sławy; **hełm smoka** – 10 Zwykłych Skór, 5 planów, 5 Cienkich
  Przędz, 5 Stali; do tego kamień przebudzenia (szansa: Mały 2%, Drobny 5%, Ładny 10%, Zacny 15%, Silny 25%) i
  2 500 000 Yang. 79 receptur (bez Likana).

## Grota Wygnańców 2 (PB) – `beran_pb`
Kapitanowie i Generałowie Yonghan (PB) (4287–4290) zostawiają **Kręty Klucz (PB)** (31180, Owsap: każdy). **Duch Sura
(PB)** (20530, 263,180): przywódca, grupa przy nim, każdy ma 3 klucze (zabierane) → **Świątynia Smoka (PB)**:
**Beran-Setaou (PB)** (4410, błyskawica, 122 poz.; z obstawą – grupa 4292) i cztery Metiny – Góry, Zemsty,
Samotności, Pychy (8130–8133). Dopóki stoi którykolwiek Metin, smoka **nie da się zranić** (wiki) – quest ustawia
`d.set_damage_from_race` na każdą rasę gracza (NEW_ICEDAMAGE_SYSTEM silnika, bez zmian w silniku), ostatni Metin to
zdejmuje. Zniszczony Metin raz na trzy przywołuje oddział Yonghan (Owsap).

## Zaklęty Las (PB) – `jotun_pb`
Siedem misji (każdy osobno, od nowa w każdej wyprawie – jak Owsap; zabójstwa grupy się liczą): Strażnik Lasu (PB) –
20 Wojowników En-Tai (PB); Apteczka (PB) od Druida En-Tai (1 na 25); apteczka do Zwiadowcy Lasu (PB); Zwiadowca –
2 Metiny Drzewnych Stworzeń (PB); 5 Ros En-Tai od Niszczycieli En-Tai; Badacz Lasu (PB) – Szlachetne Drzewo i Drzewny
Szmaragd od **Władcy En-Tai (PB)** (u Owsapa nikt go nie stawia – u nas dwóch w lesie, odrodzenie 5 min) → **Kamień
Driad (PB)** (31181) i 200 000 Yang; PD jak Owsap. **Przywódca Straży Lasu (PB)**: przywódca, grupa przy nim, każdy
ma Kamień Driad (zabierany) → **Erebu (PB)**: Bagjanamu (PB) (4352), minutę po nim **Jotun Thrym (PB)** (4413, wiatr,
135 poz.; przywołuje Niszczycieli En-Tai (PB)).

## Drop, skrzynie, przedmioty (wiki; szanse nasze, „jak oficjalne” – event 500% nie jest kompensowany)
- Beran-Setaou (PB): Skrzynia Berana-Setaou ×2 i Skrzynia Przebudzenia zawsze; Cienka Nić / Przędza / Skóra, Liście
  Życia, Mocny Sznur, Odłamki, Środek Ścierny, Stal, kamienie przebudzenia, plany (Hełm / Zbroja Ninja i Szamana; de-wiki:
  Sztylet, Dzwon), Kamień Duchowy, Spróchniała Skrzynia. **Czaszka Smoka** i **Smoczy Ząb** – tylko jego skrzynia.
- Jotun Thrym (PB): Skrzynia Jotuna Thryma ×4 i Skrzynia Przebudzenia ×3; nici, kamienie, Liście Życia, Odłamki,
  **Oznaka Sławy**, Stal, Środek Ścierny, Łza Bogini, plany (Hełm Ninja / Sura, Brzeszczot, Ostrze, Sztylet). **Ostre
  Kolce** – tylko jego skrzynia. Bagjanamu, Władca En-Tai, Niszczyciele En-Tai, Metin Lasu i kilka potworów Setaou /
  En-Tai – plany i materiały wg wiki (pl, de).
- Nowe przedmioty (`mariadb/playerbot/yohara_items_iluzja.sql`): Oznaka Sławy 31118, 15 planów (PB: Plan …, bez
  Likana), skrzynie 31139/31140, przedmioty misji 31180–31186, **hełmy smoka** 12780/12800/12820/12840 +0…+15 (wojownik,
  ninja, sura, szaman; ulepszanie Mocnym Sznurem, Stalą, a wyżej materiałami przebudzenia – refine 22660–22674 = Owsap
  661–675; efekt zestawu jak inne hełmy od 75. poziomu).

## Pliki
- `map/<folder>/` – Setting.txt (Owsap), Town.txt, server_attr; płaskowyż: npc.txt.
- `data/dungeon/beran_pb/` (npc, regen, boss), `data/dungeon/jotun_pb/` (npc, regen, stone, boss – Władcy En-Tai).
- `group.yohara_iluzja.txt` (4281–4292, 6171–6177 = Owsap 6411–6417, u nas zajęte), `group_group.yohara_iluzja.txt`
  (4281–4287), `mob_drop_item.yohara_iluzja.txt`, `special_item_group.yohara_iluzja.txt`, `cube.yohara_iluzja.txt`,
  `spawned.txt` (dla klienta).
- Baza: `yohara_iluzja.sql` (40 wierszy mob_proto + sklep), `yohara_items_iluzja.sql` (89 przedmiotów + 15 refine),
  `yohara_iluzja_zywioly.sql` (błyskawica / wiatr).

## Szczelina Czasu
Dodana osobno (MT2009_PLUS_YOHARA_CRACK_V1, właściciel 14.10.2026 – na razie jeden loch): `../yohara_crack/README.md`
– Statua Szczeliny Czasu (103,90), Zegarek Kieszonkowy u Handlarki Iluzji, Zaklęty Las (SZC) (404, quest `jotun_szc`);
pozostałe trzy lochy SZC (405–407, MT2009_PLUS_YOHARA_CRACK2_V1): `../yohara_crack2/README.md`.
