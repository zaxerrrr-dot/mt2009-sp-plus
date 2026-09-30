# Klient 2.0.30: mapy z Arezzo, etap 1 (Dolina Cyklopów, Zaczarowany Las, Biblioteka Wiedzy)

Względem klienta 2.0.29 (wydanie 2.15.0; jego pliki są w `client-patches/client-2.0.28`). Paczki są kumulatywne: budowane
na aktualnych paczkach 2.0.29 (`/opt/metin2/cache/tcm/c28/pack`, tylko do odczytu) przez
`tools/az29/rebuild.sh`. Wynik: `/opt/metin2/cache/arezzo-work/client/out/pack` (tylko paczki,
które się zmieniają, i `Index`). Exe bez zmian (2.0.25).

Znacznik zmian w plikach klienta: `MT2009_PLUS_AREZZO_V1`. Numery (mapy, moby, itemy) są w
`/opt/metin2/cache/arezzo-work/data/allocation.json` (jedno źródło dla serwera i klienta).

| Mapa | Indeks | Folder w kliencie | BasePosition | Rozmiar |
|---|---|---|---|---|
| Dolina Cyklopów | 360 | `metin2_map_exp` | 230400 281600 | 4×4 |
| Zaczarowany Las | 362 | `natural_map` | 332800 384000 | 4×4 |
| Biblioteka Wiedzy | 363 | `plechito_chamber_of_wisdom` | 947200 614400 | 2×2 |

Układ katalogów jak w 2.0.28: `<paczka>/<nazwa wpisu>`, `d:/` jako `d_/`. W repozytorium są
tylko pliki tekstowe, protos, pliki wygenerowane (`gen/`) i narzędzia. Duże zasoby (modele,
tekstury) są w paczkach; `manifest.json` wymienia każdy wpis każdej paczki ze źródłem
(`AREZZO:` rozpakowany klient Arezzo, `GF:` klient Gameforge 26.1.11, `GEN:` plik zrobiony
przez `gen.py`), rozmiarem i sha1.

## Nowe paczki (`Index`: `*` + `az_maps`, `az_mobs` na końcu)

- `az_maps` – 216 plików, 53,7 MB (31,5 MB w paczce, 22,9 MB w zipie). Wszystko, czego trzy
  mapy potrzebują poza folderem mapy i plikami property: texturesety (`vasto_exp1.txt`,
  `ateop_fm_4.txt`, `chamber_of_wisdom_dungeon.txt`), tekstury terenu, środowiska
  (`alune_wiking_1.msenv`, `ateoptoniepoeta2.msenv`, `chamber_of_wisdom.msenv`) ze skyboxami,
  obiekty map (`daimao/magic_forest`, `daimao/drzewa`, `zone/shyeonline`, `zone/plechi_env`,
  `zone/plechi_dungeon/chamber_of_wisdom`, `zone/santhia_poust`, `redwood`, `tree/plechito_trees`
  itd.), efekty, pliki kolizji `.mdatr` oraz duże mapy (atlas) wszystkich trzech map:
  `d:/ymir work/ui/<mapa>_atlas.dds` + `d:/ymir work/ui/atlas/<mapa>/atlas.sub`.
  Plik, który jest też w kliencie GF 26.1.11, pochodzi z GF (26 plików).
- `az_mobs` – 112 plików, 2,1 MB, wszystko z GF: `monster2/cyclops_boss` (Arges, 9606) i
  `monster2/cyclops_boss2` (Polifem, 9607) z dźwiękami i efektami. Pozostałe cyklopy są w
  `gf_mobs`/`gf_misc`, lemury w `ochao`, pająki i `jinno_patrol_spear` w kliencie bazowym.

## Zmienione paczki

- `maps` – +370 wpisów (1973 → 2343): `maps/metin2_map_exp/` (16 sektorów),
  `maps/natural_map/` (16), `maps/plechito_chamber_of_wisdom/` (4) z `attr.atr`, `water.wtr`,
  minimapami, plus kopia msenv w folderze każdej mapy. Bez `server_attr` (to plik serwera).
- `property` – +62 wpisy (1387 → 1449). Exe wczytuje obiekty map tylko z całej paczki
  `pack/property`, więc pliki są dołożone do niej, stare wpisy bez zmian.
- `gamedata` – `atlasinfo.txt` (+3 mapy), `npclist.txt` (+17 wierszy), `item_list.txt` (+2),
  `mob_proto` (1454 → 1471 wierszy), `item_proto` (6089 → 6091).
- `locale` – `locale/pl/itemdesc.txt` (+2 opisy, CP1250, CRLF).
- `root` – `localeinfo.py`: nazwy trzech map w `MINIMAP_ZONE_NAME_DICT`.

### mob_proto i npclist

Wiersze są kopiami wiersza źródłowego z nowym vnum, polską nazwą i statystykami z
`allocation.json` (poziom, ranga, yang, exp, PŻ, obrona, flagi AI, statystyki, obrażenia,
prędkości, zasięg). Przesunięcia w 256-bajtowym rekordzie klienta sprawdzone na 3101, 3190,
2092, 20394 i 8009 względem `world.mob_proto`. Lemury 9611–9615 to lemury 3301–3305 z PŻ ×1,3,
obrażeniami ×1,25, exp i yang ×1,3.

| vnum | nazwa | npclist |
|---|---|---|
| 9601–9605 | cyklopy (lvl 43–49) | `cyclops_soldier`, `cyclops_soldier2`, `cyclops_magic`, `cyclops_officer`, `cyclops_general` |
| 9606, 9607 | Arges, Polifem | `cyclops_boss`, `cyclops_boss2` (nowe w `az_mobs`) |
| 9611–9615 | lemury Zaczarowanego Lasu | `lemures_*` (paczka `ochao`) |
| 9703–9706 | Trujący Pająk, Pajęcze Jajo, Królowa Pająków, Baronówna Pająków | `spider_nipper`, `spider_spawn`, `spider_queen`, `spider_king` |
| 20430 | Strażnik Biblioteki | `jinno_patrol_spear` |

npclist klienta miał już wiersz `20430 ten` (oficjalny NPC GF, którego nasz serwer nie ma
w `mob_proto`). Skrypt zastępuje go wierszem `20430 jinno_patrol_spear`.

Itemy: 30765 Pieczęć Biblioteki (kopia 30760, ikona `icon/item/30327.tga`, bo
`icon/item/30329.tga` nie ma w naszej paczce `icon`), 30773 Skrzynia Biblioteki (kopia 50270,
ikona `icon/item/50270.tga`, model `item/etc/boss_box.gr2`).

## Decyzje przy imporcie

- **Kolizje CRC property w Dolinie Cyklopów (3):** 720392170, 2585303992 i 952339315 to u
  Arezzo i u nas te same drzewa (`b3_beech_rt*.spt`, rozmiar 1000). Różnią się tylko
  `propertyname` i pustą linią na końcu. Zostają nasze pliki, bez nowych CRC. Wszystkie 47 CRC
  Doliny mają plik w paczce `property`.
- **64-bitowe GR2 w Zaczarowanym Lesie:** `zone/plechi_env/dungeon/forest/tree00b.gr2`,
  `tree01.gr2` (i nieużywany `tree01b.gr2`) mają nagłówek `e59b495e`, którego exe 2.0.25 nie
  przeczyta. To pnie drzew (property typu Building 2593667659 i 1519687220), a ich korony to
  osobne obiekty-efekty (`tree00b.mse`, `tree01a.mse`, 2269369239 i 3974574155) w tych samych
  miejscach. Obie property pni mają teraz typ Tree z drzewami SpeedTree tego samego zestawu
  Plechito (`ptf_tree00b.spt`, `ptf_tree00a.spt`, 32-bit, las już ich używa), a 17 obiektów koron
  jest usuniętych z `areadata.txt` (1893 → 1876 obiektów). W paczkach nie ma żadnego pliku
  `.gr2` 64-bit.
- **Obiekty oficjalne na Dolinie** (31 property takich jak nasze: buki, skrzynie, dzbany z
  `zone/b/obj`, kości wieloryba i bramy obozu z `zone/devils_dragon_island`): modele zostają w
  kliencie bazowym (32 pliki GF, których nie ma na naszych listach, zakładamy jak przy mapach 61/62
  w 2.0.28), a ich tekstury i `.mdatr` są w `az_maps`: 21 z GF, a 6 z Arezzo, bo GF nie ma dla nich
  kolizji (kości wieloryba i bramy obozu).
- **Tekstury SpeedTree:** resolver czyta też pliki `.spt` (kora pełną ścieżką, mapa liści obok
  pliku), więc tekstury drzew Plechito są w paczce.
- **Atlas:** GF robi atlas z minimap sektorów (sprawdzone na 351: korelacja 0,98, bez odbicia).
  Tak samo tutaj: minimapy DXT1 → sklejenie → 512×512 (4×4) lub 256×256 (2×2) → DXT1.

## Czego brakuje

- Biblioteka Wiedzy: modele `books00/books01/pillar00.gr2` wymieniają 17 tekstur korytarza
  piramidy (`plechito_tex_bottom1.dds`, `plechito_tex_wall00.dds`, 9 lightmap `plechito_corridor01_*`
  itd.). Nie ma ich też u Arezzo. To pozostałości sceny 3ds Max (materiały użyte przez siatki są
  w paczce: `plechito_tex00/04.dds` i lightmapy komnaty). Do obejrzenia w grze.
- Dolina Cyklopów: `d:/ymir work/treex/treeredwoodbark.dds` (brak też u Arezzo).
- Cyklop Mag (9603): `effect/monster2/fire_boom1.msf` (brak też u Arezzo i GF).
- Modele pająków (`spider_nipper`, `spider_spawn`, `spider_queen`, `spider_king`) i
  `jinno_patrol_spear` są w kliencie bazowym, którego listy nie ma na VPS.

## Licencje

Mapy i obiekty pochodzą z klienta Arezzo: Plechito (`plechito_*`, `plechi_*`), daimao,
shyeonline, santhia_poust, trusiakwork i inne (sekcja 11 w `cache/arezzo/ANALIZA.md`).
Właściciel oświadczył, że ma prawo do plików Arezzo.

## Narzędzia (`tools/az29`)

`common.py` (indeksy: Arezzo, GF, nasze paczki, property po CRC), `plan.py` (zamknięcie
zależności → `plan.json`), `gen.py` (msenv w folderach map, atlasy, `areadata.txt` lasu →
`final.json`), `dxt.py` (DXT1), `patch_gamedata.py` (atlasinfo, npclist, item_list, itemdesc,
localeinfo, wiersze protos, idempotentnie), `build_az.py` (paczki w dockerze `m2pack-lzo`,
odczyt każdego wpisu, stare wpisy bez zmian), `verify_az.py` (obiekty map → property →
modele → tekstury, `.mdatr`, rasy z npclist), `extract_out.py`, `stage.py`, `rebuild.sh`.
