# Katakumby Diabła w kliencie (mapa 216) — klient 2.0.36

Znacznik: `MT2009_PLUS_CATACOMB_MAP_V1`.

## Dlaczego mapa „nie wczytywała się”

Klient wybiera mapę po pozycji z `gamedata/atlasinfo.txt`, nie po nazwie z serwera.
Linia `metin2_map_devilsCatacomb 307200 1203200 8 8` była już w kliencie, a teren 7×7
(`maps/metin2_map_devilscatacomb`) leżał w paczce `maps`. Brakowało jednak tego, do czego
odsyła `setting.txt` mapy:

- `textureset/metin2_map_devilscatacomb.txt` i tekstur `terrainmaps/dungeon/devilcave` — bez
  zestawu tekstur exe nie ładuje terenu i zamyka grę;
- środowiska `d:/ymir work/environment/map_devilscatacomb.msenv`;
- modeli potworów, bram, posągów i bossów (zombie_* w `monster2`/`npc2`) oraz części obiektów.

Serwer ma mapę 8×8 w tej samej bazie, ale poza obszarem 7×7 nie ma ani jednej komórki,
po której da się chodzić (sprawdzone na `server_attr`), a układ blokad zgadza się z `attr.atr`
klienta — więc mapa 7×7 klienta pasuje.

## Paczka `catacomb_map`

Nowa paczka dopisywana na końcu `pack/Index`. 1425 plików, ok. 44 MB:

- textureset i tekstury terenu, `minimap.dds` sektorów, atlas mapy;
- środowisko z GF z mgłą przerobioną na `Enable/NearDistance/FarDistance` (exe 2.0.25 nie zna
  `foglevel`; te same wartości co w Czyśćcu Ognia: 1000/30000, kolor GF);
- 24 rasy: zombie_* (piętra 1–7, Tartar, Charon, Azrael), kamienie 30101–30104, Wrota
  Potępienia 30111–30119, Strażnik 20367 (`jinno_patrol_spear`), Domokrążca 20368, z dźwiękami;
- modele i efekty obiektów z `areadata.txt`, których brakowało (GF; trzy pliki z klienta Arezzo:
  `ob-11-03-bonetunnel04.gr2/.mdatr`, `tent_s_lamp.mse`).

Właściwości obiektów (`property/`) były już wszystkie w paczce `property` — bez zmian.
Paczka niczego nie nadpisuje: plik obecny we wcześniejszej paczce ma pierwszeństwo.

## Czego nie ma (modele szyfrowane w GF, brak w innych źródłach)

- `d:/ymir work/zone/dungeon/devil_underground/cliff_01.gr2` (21 obiektów) i `cliff_corner.gr2`
  (14) — skały/ściany; jeśli nie ma ich w paczkach bazowych klienta (`zone_*`), te obiekty nie
  będą widoczne (gra działa, chodzenie wyznacza serwer);
- `d:/ymir work/zone/sample0000/666.gr2` (3 obiekty, próbny obiekt GF);
- `.mdatr` dla `cliff_*` i `devilcave_door_rock` (opcjonalne — brak kolizji klienta).

71 animacji pięciu ras (zombie_bigboss2, zombie_diseased_spear/boss/bow, zombie_magician) jest
w formacie BitKnit — tak samo jak u Niebieskiego Smoka w 2.0.32.

## Zmiany w `root` (client-patches/client-2.0.30/root)

- `localeinfo.py`: nazwa mapy na minimapie „Katakumby Diabła” (oraz zaległa linia Niebieskiego
  Smoka z 2.0.32);
- `game.py`: tryb nocny nie przełącza się w Katakumbach (nazwa z atlasu, wielkość liter).

## Budowanie

`tools/rebuild.sh [BASE]` (domyślnie paczki 2.0.35 z `/opt/metin2/cache/c35/pack`), obraz
`m2pack-lzo`: `plan_cc.py` (domknięcie zależności z GF 26.1.11) → `build_cc.py` (nowa paczka,
odczyt kontrolny) → `verify_cc.py` (niezależne domknięcie z paczek: mapa, środowisko, textureset,
obiekty, 24 rasy z `npclist.txt`). Wynik: `/opt/metin2/cache/c36-catacomb/pack/`.
