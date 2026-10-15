# Wężowe Pole i Kraina Gigantów (MT2009_PLUS_MAPS_WZ_V1)

Zlecenie właściciela 15.10.2026: dwie stare mapy wg pl-wiki („Wężowe Pole”, „Kraina Gigantów” i strony ich
potworów oraz Metinów). Pliki tego katalogu robi `tools/maps_wz/gen_maps_wz.py` (`gen_report.txt` – raport
ostatniego przebiegu, `spawned.txt` – vnumy map dla budowniczego klienta `client-patches/client-2.0.30/tools/wzmaps`);
poziomy Gigantów i Ogrów – `mariadb/playerbot/maps_wz.sql`. Rdzeń: game2 (`bin/m2-render-config`).

| indeks | mapa | folder (nasz) | oficjalny folder | rozmiar | baza |
|---|---|---|---|---|---|
| 80 | Wężowe Pole | metin2_map_snakefield | metin2_map_WL_01 (oficjalnie 69) | 4×4 | 1049600 716800 |
| 70 | Kraina Gigantów | metin2_map_giantland | metin2_map_nusluck01 (70) | 2×2 | 819200 716800 |

Indeks 69 to u nas Przełęcz (`metin2_map_wl_pass`) – zostaje; Wężowe Pole dostaje wolny 80. Kraina Gigantów zostaje
na 70 (była już w `map/index`, ale bez wejścia). Foldery mają nowe nazwy, bo klient dostaje teren tych map w nowej
paczce (`wzmaps_map`) pod nazwą, której żaden klient nie ma – wtedy rysuje zawsze ten teren, do którego pasują
`server_attr` tych folderów (stary `metin2_map_nusluck01` naszej bazy ma inny teren niż oficjalny – 4% komórek).

## Skąd co

- **server_attr, spawny, NPC, Metiny**: oficjalne pliki serwera (share Amerii, `serverfiles/home.tar.gz`; = nasza
  baza). `regen.txt` Amerii powtarza każdą linię 3× (ich gęstość) – tu po jednej (529 / 155 linii = oficjalnie),
  czasy z naszej bazy (przeklęte zwierzęta 180 s, reszta 120 s; Kraina 15/20/25 s; Metiny 30 min). 98 środków
  spawnu Wężowego Pola stało na skale (oficjalny plik) – przesunięte na najbliższy wolny metr (36 z nich o 51–74 m).
- **Wężowe Pole**: część 1 – przeklęte wilki, dziki, niedźwiedzie i tygrysy (grupy 127–136, gg 1101–1104 –
  „przeklęte zwierzęta” z wiki), część 2 za rzeką i górami – Niszczyciel, Ogr Wojownik, Ogr Rzeźnik (gg 1401/1402),
  Skalny / Kamienny / Olbrzymi Skalny Golem (gg 1501–1504). NPC: Teleporter 9012 (245,580 – jak wiki), portal 10030
  → Pustynia Yongbi, portal 10032 → Kraina Gigantów (92,349 – wiki: 93,350). Town 94,94 – miejsce przybycia
  (oficjalne 92,90 stało na portalu do pustyni).
- **Kraina Gigantów**: Niszczyciel, Wojownik z Toporem, Tysięczny Wojownik, Ogr Wojownik, Ogr Rzeźnik, Ogr Szaleniec
  (gg 1451–1453 – dokładnie lista wiki), Metin Pung-Ma 8024 i Metin Ma-An 8025, krzaki ziół naszej bazy (gg 20611).
  Portal 10031 → Wężowe Pole. Town 91,467 – miejsce przybycia.
- **Wejście (wiki)**: Pustynia Yongbi, prawy dolny róg – portal 10029 „Wężowe_Pole” (1477,1357) w miejsce naszego
  10108 do Przełęczy (krok Dockerfile podmienia linię w `npc.txt` pustyni, `links.maps_wz.txt`). Przełęcz zostaje
  hostowana, ale wchodzi na nią już tylko GM. Bez wymogu poziomu (wiki go nie podaje); część 2 Wężowego Pola ma
  potwory 66–76.
- **Poziomy** (wiki): Niszczyciel 66, Wojownik z Toporem 73, Tysięczny Wojownik 77, Ogr Wojownik 68, Ogr Rzeźnik 70,
  Ogr Szaleniec 75 (u nas było 76/83/87/78/80/85); golemy 69/72/76 – już jak wiki. Tylko poziom – HP, obrażenia
  i exp zostają nasze. Żywioły (wiki): Giganci i Ogry – błyskawica, golemy – ziemia: już są (`zywioly_moby_global.sql`).
- **Drop** (`mob_drop_item.maps_wz.txt`): to, co wiki wymienia, a nasze oficjalne grupy nie dawały – Orkowa Maczuga
  30194 (Ogr Wojownik, Ogr Rzeźnik; materiał butów), Piasek Kwarcowy 30195 (trzy golemy), zioła Ogra Wojownika,
  Marmur Polimorfii (= „Kula Polimorfii”, z gniazdem potwora), Srebrna Szkatułka, Kamienna Strzała ×100 i broń /
  zbroje / biżuteria z list wiki na +0. Szanse tymczasowe (wiki ich nie podaje) – `cache/yohara/PROCENTY.md` p. 8.
  Pominięte: Zwój Ewolucji / Mutacji (bez zastosowania u nas), Certyfikat Tugyisa / Kamień Duszy Tugyi (daje je quest
  Biologa), przedmioty Lykana.
- **GM**: `/goto sneak` (poprawione: był indeks 69), `/goto wezowe`, `/goto giant` (poprawione: róg mapy → miejsce
  przybycia), `/goto gigantow`.
- **Boty**: mapy stoją na game2 (pamięć game1 – patrz `bin/m2-render-config`), a bot nie przechodzi między rdzeniami –
  boty tam nie polują, dopóki mapy są na game2. Kod botów je zna (MT2009_PLUS_MAPS_WZ_BOTS_V1, `playerbot_types.h`,
  `_travel.h`, `_wandering.h`, `_navigation.h`): przedziały 63–78 (Wężowe Pole, bez Metinów – nie dla łowców Metinów)
  i 63–80 (Kraina), po ćwiartce losowania w tych przedziałach, 24 / 17 miejsc polowania (`tools/arezzo_bot_map.py`
  na `server_attr` i spawnach map; na Wężowym Polu tylko część 2), przybycie przy Teleporterze / w Town, siatka
  nawigacji – wszystko tylko na rdzeniu, który mapy hostuje. Wiersz Biologa 80 (Certyfikat Tugyisa, 1401) liczy się
  tylko tam. Przeniesienie „70 80” do MAPS_game1 (gdy game1 będzie miał pamięć) włącza boty bez zmian w kodzie.
