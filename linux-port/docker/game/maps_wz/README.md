# Wężowe Pole i Kraina Gigantów (MT2009_PLUS_MAPS_WZ_V1)

Mapy z linii Yohara (zlecenie właściciela 15.10.2026), przeniesione do linii 2.x (26.10.2026: „do 2.x dodaj wężowe
pole i krainę gigantów i dodaj piasek kwarcowy zgodnie z dropem z globala”). Pliki tego katalogu robi
`tools/maps_wz/gen_maps_wz.py` (`gen_report.txt` – raport ostatniego przebiegu, `spawned.txt` – vnumy map dla
budowniczego klienta `client-patches/client-2.0.30/tools/wzmaps`); poziomy Gigantów i Ogrów –
`mariadb/playerbot/maps_wz.sql`. Rdzeń: game3 razem z innymi nowymi mapami (`bin/m2-render-config`,
MT2009_PLUS_237_NEWCORE_V1; przy `M2_MAP_CORE=0` – game2), w każdym kanale.

| indeks | mapa | folder | folder wzorcowy | rozmiar | baza |
|---|---|---|---|---|---|
| 80 | Wężowe Pole | metin2_map_snakefield | metin2_map_WL_01 | 4×4 | 1049600 716800 |
| 70 | Kraina Gigantów | metin2_map_giantland | metin2_map_nusluck01 | 2×2 | 819200 716800 |

Indeks 69 był Przełęczą (`metin2_map_wl_pass`) – usunięta (MT2009_PLUS_PASS69_OFF_V1, krok Dockerfile po tym
katalogu): jej portal na pustyni prowadzi teraz na Wężowe Pole, Min-Sun (20402: Labirynt, Czarna Stal) stoi na
Pustyni Yongbi przy tym portalu, a `apply.sh` raz przenosi postacie zapisane na 69 na przybycie Wężowego Pola.
Kraina Gigantów zostaje na 70 (była już w `map/index`, ale bez wejścia). Foldery mają nowe nazwy, bo klient dostaje
teren tych map w nowej paczce (`wzmaps_map`) pod nazwą, której żaden klient nie ma.

## Skąd co

- **server_attr, spawny, NPC, Metiny**: pliki serwera wzorcowego (= nasza baza). `regen.txt` po jednej linii
  (529 / 155), czasy z naszej bazy (przeklęte zwierzęta 180 s, reszta 120 s; Kraina 15/20/25 s; Metiny 30 min).
  98 środków spawnu Wężowego Pola stało na skale – przesunięte na najbliższy wolny metr.
- **Wężowe Pole**: część 1 – przeklęte wilki, dziki, niedźwiedzie i tygrysy (gg 1101–1104), część 2 za rzeką –
  Niszczyciel, Ogr Wojownik, Ogr Rzeźnik (gg 1401/1402), Skalny / Kamienny / Olbrzymi Skalny Golem (gg 1501–1504).
  NPC: Teleporter 9012 (245,580), portal 10030 → Pustynia Yongbi, portal 10032 → Kraina Gigantów (92,349). Town
  94,94 – miejsce przybycia.
- **Kraina Gigantów**: Niszczyciel, Wojownik z Toporem, Tysięczny Wojownik, Ogr Wojownik, Ogr Rzeźnik, Ogr Szaleniec
  (gg 1451–1453), Metin Pung-Ma 8024 i Metin Ma-An 8025, krzaki ziół (gg 20611). Portal 10031 → Wężowe Pole. Town
  91,467 – miejsce przybycia.
- **Wejście (wiki)**: Pustynia Yongbi, prawy dolny róg – portal 10029 „Wężowe_Pole” (1477,1357) w miejsce 10108 do
  Przełęczy (krok Dockerfile podmienia linię w `npc.txt` pustyni, `links.maps_wz.txt`). Bez wymogu poziomu.
- **Poziomy**: Niszczyciel 66, Wojownik z Toporem 73, Tysięczny Wojownik 77, Ogr Szaleniec 75 (wiki), Ogr Wojownik 71,
  Ogr Rzeźnik 73 (arkusz globala, decyzja właściciela 20.10); golemy 69/72/76 – już jak wiki. Tylko poziom – HP,
  obrażenia i exp zostają nasze (w trybie global – jak w `moby_global_2x.sql`).
- **Drop** (`mob_drop_item.maps_wz.txt`): to, co wiki wymienia, a nasze grupy nie dawały – Piasek Kwarcowy 30195
  (Skalny, Kamienny i Olbrzymi Skalny Golem – jak strona przedmiotu na wiki), Orkowa Maczuga 30194 (Ogr Wojownik,
  Ogr Rzeźnik), zioła Ogra Wojownika, Marmur Polimorfii, Srebrna Szkatułka, Kamienna Strzała ×100 i broń / zbroje /
  biżuteria z list wiki na +0. Wiki nie podaje szans: wartości tymczasowe z linii Yohara – materiały i zioła 2
  (0,5% na zabicie), sprzęt +0 0,8 (0,2%), Marmur / Szkatułka / Strzały 1 (0,25%). Krok jest przed krokiem dropu
  trybu global, więc `mob_drop_item.global.txt` też go ma. Pominięte: Zwój Ewolucji / Mutacji (bez zastosowania),
  Certyfikat Tugyisa (daje go quest Biologa).
- **GM**: `/goto sneak` (był indeks 69), `/goto wezowe`, `/goto giant` (miejsce przybycia), `/goto gigantow`.
- **Boty** (MT2009_PLUS_MAPS_WZ_BOTS_V1, `playerbot_types.h`, `_travel.h`, `_wandering.h`, `_navigation.h`,
  `_status.h`, `_yohara_bots.h`): boty żyją na game1, a mapy stoją na game3 – przechodzą tam przekazaniem między
  rdzeniami (jak do Zaklętego Lasu): przedziały 63–78 (Wężowe Pole, bez Metinów – nie dla łowców Metinów) i 63–80
  (Kraina), po ćwiartce losowania w tych przedziałach, limity `PLAYERBOT_SNAKEFIELD_MAX` / `PLAYERBOT_GIANTLAND_MAX`
  (domyślnie -1 = bez limitu, MT2009_PLUS_MAPS_WZ_NOCAP_V1; 0 wyłącza), pobyt `PLAYERBOT_WZ_STAY_MIN` (120 min), 24 / 17 miejsc polowania, przybycie przy Teleporterze
  (część 2 Wężowego Pola) / w Town Krainy, wyjście, siatka nawigacji tylko na rdzeniu, który mapy hostuje.
