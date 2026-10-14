# Przebudzeni bossowie – Razador (PB) i Nemere (PB) (MT2009_PLUS_YOHARA_PB_V1)

Decyzja właściciela 14.10.2026 (`cache/yohara/decyzje.md`, „14.10 ok. 8:10”): „Przebudzeni bossowie: Razador (PB) i
Nemere (PB) – dodać wg wiki (źródło materiałów Mrocznego Smoka)”. Wszystko wg pl-wiki; przebieg pięter, pozycje i
szanse kluczy – Owsap v6.2.6 (`awaken_flame_dungeon.quest`, `awaken_snow_dungeon.quest` = oficjalne). Pliki tego
katalogu i wiersze bazy robi `tools/yohara_pb/gen_ypb.py` (nie edytować ręcznie). Rdzeń: Yohara (game3). Klient:
`client-patches/client-2.0.30/tools/ypb`.

| indeks | miejsce | folder | teren | quest |
|---|---|---|---|---|
| 369 | Twierdza Czerwonego Smoka (PB) | metin2_map_boss_awaken_flame (3×3, baza 153600 1971200) | nasza 351 | `razador_pb` |
| 370 | Strażnica Nemere (PB) | metin2_map_boss_awaken_snow (4×3, baza 230400 1971200) | nasza 352 | `nemere_pb` |

Obie mapy to **kopie** terenu zwykłych lochów (351/352 zostają bez zmian): w kliencie folder ma tylko `setting.txt` i
`mapproperty.txt` z `ParentMapName` (kopiowana mapa exe, `GameLib/MapBase.cpp` – jak w kliencie GF), na serwerze
`server_attr` z `attr.atr` GF mapy-rodzica – identyczny komórka w komórkę z naszym 351/352.

## Wejście (quest `przebudzeni_bossowie`)
- **Statua Iluzji** (20470) w Yongan 540,500, Joan 688,748, Pyungmoo 342,800 (komórki z wiki) – przenosi na
  **Płaskowyż Iluzji** (397, `game/yohara_iluzja`, MT2009_PLUS_YOHARA_ILUZJA_V1); **Codzienna misja: Świat Iluzji** od
  110 poziomu: zabij Razadora i Nemere (zwykłe lochy; zwykłego Jotuna Thryma u nas nie ma) i wróć – nagroda **Książka
  Przebudzenia** (31146); powtórka 24 h po ukończeniu; okno kamieni przebudzenia.
- **Statua Przebudzenia** (20471) stoi na Płaskowyżu Iluzji (153,89 – wiki), już nie w wioskach: cztery lochy (te dwa
  oraz Grota Wygnańców 2 (PB) i Zaklęty Las (PB)), od 110 poziomu, **tylko w grupie** (min. 2 osoby; GM może sam),
  otwiera przywódca, wszyscy blisko statui; każdy musi mieć Książkę Przebudzenia – zabierana przy pierwszym wejściu do
  nowej wyprawy. Do Strażnicy Nemere (PB) w grupie musi być **Ninja i Szaman**. „Wróć do lochu” – do trwającej
  wyprawy.
- **60 minut**; po zwycięstwie (minuta) lub po czasie każdy wraca na Płaskowyż Iluzji (obok Statui Przebudzenia). Boty nie wchodzą
  (rdzeń Yohary). Panel lochów: `razador_pb`, `nemere_pb` (najlepszy czas).
- **Baek-Go** (20018): Lekarstwo Iluzji (31144: 500 PŻ i 500 PE od razu) za 20 Liści Życia (31145).

## Twierdza Czerwonego Smoka (PB) – `razador_pb`
Gardziel Am-heha (PB) (20531) wyznacza sześć zadań w losowej kolejności (każde otwiera Zamek Losu 20534 i Smoczą
Bramę 20535): 2× zabij wszystkie potwory; Złota Zębatka (PB) (31187, 5% z potwora, 30% prawdziwych) na Stelę Isfet
(PB) (20533); Ignator (PB) (4309); siedem Stel Isfet (PB) Kamieniami Maat (PB) (31188, 5%) w ukrytej kolejności;
Metin Purgatorium (PB) (8134). Potem przywódca – sala bossa: **Razador (PB)** (4411, ogień, 130 poz.; przywołuje
Ognistych Generałów Żaru (PB)).

## Strażnica Nemere (PB) – `nemere_pb`
Lodowy Lew (PB) (20536) – start; dziesięć pięter: 1/3 zabij wszystkich; 2 Mroźny Klucz (PB) (31189, 30%, tylko
Szaman, 30% prawdziwych); 4 dwie fale + Szel (PB) (4329); 5 pięć Arktycznych Kostek (PB) (20537) Gwiazdami Północy
(PB) (31190, 30%) w ukrytej kolejności; 6 Metin Chłodu (PB) (8135) – **rani go tylko Szaman**; 7 czterech Szelów –
trzy sobowtóry znikają poniżej 50% PŻ; 8 Klucz Lod. Kwiatu (PB) (31191, 3%, tylko gdy zabija Ninja; używa Ninja
albo Szaman); 9 Kolumna Smoka Północy (PB) (20538) – **rani ją tylko Ninja albo Szaman**, potem Lodowy Lew; 10
**Nemere (PB)** (4412, lód, 130 poz.; przywołuje Mroźnych Generałów (PB)). Blokada ciosów innych klas:
`server-patches/przebudzeni` (silnik).

## Drop i skrzynie (wiki; szanse nasze, „jak oficjalne” – event 500% na serwerze testowym nie jest kompensowany)
- Razador (PB): Skrzynia Razadora (PB) ×4 i Skrzynia Przebudzenia ×3 zawsze; Cienka Nić, Cienka Przędza, Gruba Nić,
  Mały / Drobny Kam. Przebudzenia, Liście Życia, Kamień Duchowy, Łza Bogini, Pierścień Doświadczenia (1 h),
  Spróchniała Skrzynia. Nemere (PB): Skrzynia Nemere (PB) ×4, Skrzynia Przebudzenia ×3; Cienka Nić, kamienie
  przebudzenia, Odłamki, Liście Życia, Środek Ścierny, Kamień Duchowy, Peleryna Maskująca (nasz Płaszcz Uciekiniera),
  Pierścień Doświadczenia, Spróchniała Skrzynia. Metin Chłodu (PB), Kolumna (PB): Kamień Duchowy.
- **Materiały Mrocznego Smoka** (31122–31138, `ysets`): ze skrzyń PB są wszystkie poza Czaszką Smoka, Smoczym Zębem
  (tylko Skrzynia Berana-Setaou (PB)) i Ostrymi Kolcami (tylko Skrzynia Jotuna Thryma (PB)) – obu bossów dodaje
  `game/yohara_iluzja`. Odłamki – z Nemere (PB).
- **Plany ekwipunku Smoka Mroku** (PB: Plan …, `yohara_items_iluzja.sql`): Razador (PB) – Hełm Wojownika / Sura,
  Ostrze, Wachlarz (pl-wiki); Nemere (PB) – Miecz, Brzeszczot, Łuk, Hełm Sura (de-wiki); Szel (PB), Mroźni Golem /
  Troll / Generał / Broda / Książę (PB), Og. Generał / Ognisty Książę Żaru (PB) – po planie wg de-wiki („EW: …”).
- Kamienie przebudzenia, Dusza Przebudzenia, Zwykła Skóra, Kowadło, Cienka Przędza, Środek Ścierny, Stal, Mocny Sznur
  mają już zastosowanie: statuy na Płaskowyżu Iluzji (kamienie, wytwarzanie ekwipunku Smoka Mroku, hełmy smoka).
- Pominięte: Torba Emocji, Miedziane / Złote Płyty, Ciężkie Pasy i Księga Umiejętności Metinu Chłodu (nie mamy), plany
  Likana.

## Pliki
- `map/metin2_map_boss_awaken_{flame,snow}/` – Setting.txt (Owsap), Town.txt (wejście), server_attr.
- `data/dungeon/razador_pb/fd_*.txt`, `data/dungeon/nemere_pb/sd_*.txt` – punkty Owsapa, grupy PB.
- `group.yohara_pb.txt` (6101–6112, 6121–6132), `group_group.yohara_pb.txt` (6101–6103), `mob_drop_item.yohara_pb.txt`,
  `special_item_group.yohara_pb.txt`, `spawned.txt` (dla klienta).
- Baza: `mariadb/playerbot/yohara_pb.sql` (34 wiersze mob_proto), `yohara_items_pb.sql` (23 przedmioty),
  `yohara_pb_zywioly.sql` (ogień / lód).
