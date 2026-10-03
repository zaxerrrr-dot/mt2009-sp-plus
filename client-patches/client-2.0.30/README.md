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

# Etapy 5–8: Pustkowie Faraona, Wzgórze Wukonga, Ruiny Skorpiona, Starożytna Dżungla

Budowane przez `tools/az58/rebuild58.sh` na aktualnych paczkach klienta (`/opt/metin2/cache/tcm/c30/pack`, w których
jest już etap 1 i panel lochów), wynik w `/opt/metin2/cache/arezzo-work/client/out58/pack`. Pliki tekstowe i protos
w tym katalogu (`gamedata/`, `locale/`, `root/localeinfo.py`) są już wersją z etapami 1 i 5–8. Pliki wygenerowane są
w `gen58/`, lista wpisów nowych paczek ze źródłami w `manifest58.json`.

| Mapa | Indeks | Folder w kliencie | BasePosition | Rozmiar |
|---|---|---|---|---|
| Pustkowie Faraona | 361 | `metin2_map_pustynia` | 230400 384000 | 4×4 |
| Wzgórze Wukonga | 364 | `plechito_wukong_dungeon` | 844800 537600 | 2×2 |
| Ruiny Skorpiona | 365 | `plechito_scorpion_dungeon` | 844800 588800 | 2×2 |
| Starożytna Dżungla | 366 | `plechito_easter2023_dungeon` | 768000 537600 | 3×3 |

## Nowe paczki (`Index`: `az_maps2`, `az_maps3`, `az_mobs2`, `az_mobs3`, `az_mobs4` na końcu)

Podział tak, żeby każdy zip był mały (zmierzone: 8–15 MB).

- `az_maps2` (138 plików, 15,5 MB w paczce): Pustkowie Faraona – textureset `pustynia.txt`, tekstury terenu,
  `plechito_desert_map_01.msenv` ze skyboxem, obiekty `zone/plechi_env/desert_map_01`, `devils_dragon_island`,
  `daimao`, `trusiakwork`, `.mdatr`, tekstury 17 oficjalnych obiektów (modele z klienta bazowego) i atlas.
- `az_maps3` (133 pliki, 18,3 MB): trzy lochy – texturesety, msenv, obiekty `zone/plechi_dungeon/*`, `.mdatr`, atlasy.
- `az_mobs2` (203 pliki, 12,8 MB): rasy Wzgórza Wukonga (`monster2/plechito_wukong/*`, kamienie w `monster/plechito_wukong/*`)
  z efektami `effect/plechito/*`.
- `az_mobs3` (250 plików, 9,9 MB): rasy piramidy (`monster2/plechito_pyramid_monsters/*`, `monster2/plechito_pyramid_stone1|4`).
- `az_mobs4` (319 plików, 17,6 MB): Ruiny Skorpiona (`monster2/plechito_scorpion_monsters/*`, `monster/metinstone/scorpion_stone1.msm`)
  i Starożytna Dżungla (`monster2/plechito_easter2023/*`, kamienie w `monster/plechito_easter2023/*`).

## Zmienione paczki

- `maps` +343 (4 foldery map i kopie msenv, bez `server_attr`), `property` +58 (obiekty map; kolizji CRC z naszą paczką brak –
  17 obiektów Pustkowia to te same oficjalne obiekty, które już mamy).
- `gamedata`: `atlasinfo.txt` +4, `npclist.txt` +38 linii ras i NPC oraz 33 linie aliasów `0 <rasa> <katalog>/<rasa>` (z npclist
  Arezzo, `\` zamienione na `/`; aliasy stoją przed liniami vnumów), `mob_proto` 1471 → 1509, `item_proto` 6091 → 6097,
  `item_list.txt` +6 (pieczęcie z ikoną `30327.tga`, skrzynie `50270.tga`/`50271.tga` z modelem `boss_box.gr2`).
- `locale`: `itemdesc.txt` +6. `root`: `localeinfo.py` – 4 nazwy map w bloku `MT2009_PLUS_AREZZO_V1`.

## Rasy Plechito (katalogi zagnieżdżone)

Arezzo trzyma rasy w podkatalogach (`monster2/plechito_wukong/plechi_wukong_boss1/…`), a ścieżki w `.msm` są pełne
i wskazują na `monster2`. Układ jest zachowany; npclist dostaje alias, np. `0 plechi_wukong_boss1 plechito_wukong/plechi_wukong_boss1`.
Arezzo ma część ras podwójnie (`monster/` i `monster2/`) – wzięta jest kopia z `monster2` (na nią wskazują `.msm`), kamienie
Wukonga i Dżungli są tylko w `monster/`. Kamień Skorpiona (9696) to `monster/metinstone/scorpion_stone1.msm` na oficjalnym
`metinstone_01.gr2` (klient bazowy). Numery z allocation.json: kamienie i bossowie piramidy 9677/9678/9675/9681, Dżungla 9707–9714
(w npclist klienta 8207–8209 i 16101–16131 są zajęte przez oficjalne NPC).

## Czego brakuje (Arezzo też tego nie ma)

- Pustkowie: 14 tekstur (`zone/plechi_env/desert_map_01/maze_*.dds`, `sand.dds`, 2 tekstury `terrainmaps/daimao/bydaimao`).
- Ruiny Skorpiona: 2 tekstury logo `m2m_logo*`.
- Rasy: `guardian warrior_e.dds` (9673), `guardian_thoth_e.dds` i `waepon_e.dds` (9675), `spawn.msa` WuKonga (9682);
  żadna rasa Plechito nie ma dźwięków (`sound/…`).
- GR2 64-bit: brak w tych mapach i rasach.

## Narzędzia (`tools/az58`)

`rebuild58.sh [BASE] [OUT]` (domyślnie `c30/pack` → `client/out58/pack`): `c30list.py` (lista i pliki bazy), `plan58.py`,
`gen58.py`, `build58.py`, `verify58.py`, `extract58.py`, `stage58.py`. Drugie uruchomienie na bazie z tymi paczkami daje „unchanged”.

## Boty: osobowość Zielarz (`MT2009_PLUS_BOTLIFE_V1`)

- `root`: `playerbot_status_tail.py` (baza: wpis z paczki `root` 2.0.29/2.0.30) – tytuł 119 „Zielarz”
  („Herbalist” w kliencie angielskim), kolor (0.45, 0.85, 0.4). Serwer wysyła go jako `PlayerBotTitle <vid> 119`
  (`PERSONA_TITLE_BASE` + `PERSONA_ZIELARZ`); starszy klient go nie zna i nic nie rysuje.

## System Legend botów (`MT2009_PLUS_LEGENDS_V1`)

- `root`: `playerbot_status_tail.py` – serwer wysyła `PlayerBotTitle <vid> <osobowość> <tier> <królestwo>`
  (`ManagePlayerBotPersonalityTitle`, `playerbot_legends.h`). Bot z tierem ma w wierszu osobowości
  (`textTail.AttachPersonality`, nad nickiem) kolorowy tytuł zamiast osobowości: „Wyróżniający się”
  (jasnoniebieski), „Specjalny” (fioletowy), „Chodząca Legenda” (pomarańczowy), „Czempion Shinsoo/Chunjo/Jinno”
  (złoty); w kliencie angielskim „Distinguished”, „Special”, „Walking Legend”, „Champion of …”.
  Przełącznik „Tytuły botów” wyłącza tylko osobowości – tiery widać zawsze. Tier 0 albo starszy serwer
  (dwa słowa) – osobowość jak dotąd.
- `root`: `game.py` – `__PlayerBotTitle` przekazuje dwa dodatkowe słowa do `show_title`.
- Exe bez zmian.

## Menedżer eventów w grze (`MT2009_PLUS_EVENT_MANAGER_V1`)

Wspólna podstawa pod mini gry Owsapa (Złap Króla, Rumi, Yut Nori, Dzieci Kwiaty) i każdy
przyszły event. Serwer: `server-patches/eventmanager`, `playerbot_ingame_events.h`; exe:
`client-patches/exe` (pakiet 183, moduł `ingameEventSystem`). Pliki `root` (baza: paczka `root`
z `tcm/c31`):

- `ingameevent.py` (nowy) – lista eventów dla pythona: z modułu exe, a na starym exe z linii
  `IGE …`; powitanie `/ingame_event hello <caps>`; nazwy Owsapa i jego polecenia flag.
- `uiingameevent.py` (nowy) – okno „Wydarzenia w grze” (lista, czas do końca, okno nagród,
  do 3 nagród, przycisk kalendarza) i przycisk obok minimapy (obrazy `e_open_*` z GF, gdy paczka
  je ma; do tego czasu `mt2009_ui/calendar_button_*`). Wszystko o evencie jest w `EVENTS`
  – nowy event to jeden wpis, bez nowego exe. Mini gra dopina swoje okno przez
  `RegisterOpener(key, func)`.
- `game.py` – start (po wejściu do świata, obok kalendarza), zamknięcie, polecenia `IGE`,
  `mini_game_okey`, `mini_game_okey_normal`, `mini_game_yutnori`, `mini_game_catchking`,
  `e_flower_drop`, `easter_drop`, `BINARY_RefreshInGameEvent`.
- `interfacemodule.py` – tooltip przedmiotów dla nagród, ukrywanie przycisku z resztą okien,
  nazwy Owsapa `ShowInGameEvent`, `ShowMiniMapInGameEventButton`, `HideMiniMapInGameEventButton`.
- `uieventcalendar.py` – nazwy nowych rodzajów (9–13) i na ikonie „trwa teraz” także eventy z samej
  flagi (np. strona Wielkanocy w panelu).

## Seon-Hae: 6. i 7. bonus (`MT2009_PLUS_SEONHAE_V1`)

Okno Owsapa (`uiattr67add.py`, `uiscript/attr67adddialog.py`) na poleceniach czatu – **bez zmian
exe** (serwer: `server-patches/seonhae`, `playerbot_seonhae.h`, quest `seonhae`). Pliki `root`
(baza: paczka `root` z `tcm/c31`):

- `uiseonhae.py` (nowy) – okno: przedmiot, Odłamki i Suplementy, szansa, „Dodaj bonus”, a gdy
  Seon-Hae trzyma przedmiot – przedmiot z tooltipem, odliczanie i „Odbierz”. Polecenia `SEONHAE
  cfg|open|state|item|close|done|msg`, odpowiedzi `/seonhae open|add|collect`. Teksty po polsku
  (CP1250 jako `\x..`).
- `uiscript/seonhaewindow.py` (nowy) – układ 312×224 jak u Owsapa. Grafika GF
  `d:/ymir work/ui/game/attr6th7th/*.sub` (+ `d:/ymir work/ui/properties_01.dds`) jest używana, gdy
  jest w paczkach (`app.IsExistFile`); bez niej zwykłe ramki `slot_base.sub` i przyciski `+`/`-`
  (`xsmall_button`), więc okno działa i bez nowych grafik.
- `game.py` – polecenie `SEONHAE` i zamknięcie okna z resztą.
- `uitooltip.py` (nowy w łatkach, baza c31) – broń: 6. i 7. bonus w swoim kolorze po pięciu (były
  doklejane do wartości bazowych), zbroja i biżuteria: 6. i 7. bonus wreszcie widoczne; linia
  „Seon-Hae może dodać temu przedmiotowi dodatkowy bonus.”, gdy system jest włączony.

Do spakowania przez koordynatora:

- `gamedata/item_proto`, `gamedata/item_list.txt`, `locale/pl/itemdesc.txt` – 13 przedmiotów
  (39070–39077, 39081, 72064–72067) narzędziem `tools/seonhae/patch_seonhae_client.py`
  (dane: `tools/seonhae/seonhae_items.json`; idempotentne, w obrazie `m2pack-lzo`).
- ikony z GF 26.1.11: `icon/item/39070.tga` … `39077.tga`, `icon/item/39081.tga`,
  `icon/item/72064.tga` (72065–72067 używają 72064.tga, jak w GF);
- grafika okna z GF: `d:/ymir work/ui/game/attr6th7th/` (10 plików `.sub`: `arrow_up_*`,
  `arrow_down_*` ×3, `material_count_text`, `material_slot`, `memu_text`, `regist_slot`) i
  `d:/ymir work/ui/properties_01.dds`.
## Dzieci Kwiaty (`MT2009_PLUS_FLOWER_V1`)

Event kwiatów Owsapa (serwer: `server-patches/flower/README.md`). Okno działa z nowym exe
(pakiety 187, nazwy pythona Owsapa); na starym exe moduł się ładuje, a przycisk w oknie eventów
mówi, że okno przyjdzie z aktualizacją klienta.

- `root/uiflowerevent.py` (nowy) – `FlowerEventUtil` i okno `FlowerEvent` Owsapa, `ComboBoxImage`
  (brak w naszym `ui.py`), pytanie przed zamianą bonusu kwiatu, ikona bonusu (affect 570) w pasku
  efektów, przycisk w oknie eventów (`uiingameevent.RegisterOpener('flower', ...)`); teksty z
  `localeInfo`, gdy locale ma klucze Owsapa, inaczej polskie z pliku.
- `root/uiscript/flowereventwindow.py` (nowy) – układ Owsapa, teksty z `uiScriptLocale` albo polskie.
- `root/game.py` – `FlowerEventProcess` (wołane przez exe), `Start`/`DestroyWindow`,
  `e_flower_drop` → `player.SetFlowerEventEnable`.
- `root/uiinventory.py` – pytanie przed użyciem kwiatu, który zastąpi bonus innego kwiatu.
- `root/uiingameevent.py` – nagrody w wierszu `flower` (pudełka 83023, 83025, 83027).
- `gamedata/gamedata/item_list.txt` (+10), `locale/locale/pl/itemdesc.txt` (+10): kwiaty
  25121–25125, pudełka 83023–83027.
- `flower_items.json` – wiersze klienckiego `item_proto` (jak `world.item_proto`) i lista plików
  z klienta GF 26.1.11 do paczki: ikony 25121–25125, 25131–25135, `ui/minigame/flower_event/*.sub`
  + `ui/floweralram.dds`, efekt `effect/etc/buff/buff_item15_flower.mse` + `flower_001.dds`, `leaf_001.dds`.
## Rumi (Okey) Owsapa (`MT2009_PLUS_RUMI_V1`)

Serwer: `server-patches/rumi`, `playerbot_rumi.h` (pakiety CG/GC 181 – opis w README łatki).
Exe: `client-patches/exe` (osobny port; nazwy Owsapa: `net.SendMiniGameRumi*`, wywołania
`MiniGameRumi*` na oknie gry). Bez nich przycisk eventu mówi, że okno przyjdzie z aktualizacją.

- `root/uiminigamerumi.py` (nowy) – okno Owsapa (strona oczekiwania z licznikami kart i zestawów,
  strona gry). To, czego nasze exe nie ma (`ui.MoveImageBox`, `AniImageBox.ResetFrame` /
  `SetKeyFrameEvent` / `SetScale`, sloty rysowane z `grpImage`), jest w pythonie: każda karta to
  osobny `ImageBox`, animacje to `FrameAnimation`, lot karty to `MovingCard`. Teksty polskie
  (CP1250), klucz `localeInfo` o nazwie Owsapa ma pierwszeństwo.
- `root/uiscript/minigamerumigamepage.py`, `minigamerumiwaitingpage.py` – uiscripty Owsapa (sloty
  jako zwykłe okna, efekty w kodzie; strona oczekiwania w wersji `__OKEY_EVENT_FLAG_RENEWAL__`).
- `root/game.py` – start (`uiminigamerumi.Start()` po `uiingameevent.Start()`: przycisk w liście
  eventów i `REQUEST_QUEST_FLAG`, po którym serwer wysyła temu klientowi pakiety 181), zamknięcie,
  `MiniGameRumiStart/End/MoveCard/SetDeckCount/IncreaseScore/FlagProcess`, polecenie
  `MiniGameRumiOpen` (opcja „Zagraj w Okey” przy stole 20417).
- `root/uiingameevent.py` – przy `rumi` / `rumi_xmas` trzy skrzynie jako nagrody.
- `locale/locale/pl/mini_game_okey_desc.txt` (nowy, CP1250, CRLF) – opis zasad (tekst Owsapa,
  punkt o przerwanej grze zmieniony: gra jest rozliczana).
- `locale/locale/pl/itemdesc.txt` (+8), `gamedata/gamedata/item_list.txt` (+8): 79505, 79506,
  50267-50269, 50275-50277 (ikony 50275-50277 = ikony 50267-50269, jak w GF).
- `npclist.txt` ma już `20417 okey_npc`.

Do zrobienia przy budowie paczek (pliki binarne / zasoby):

- `item_proto` klienta: 79505 „Karta Okey”, 79506 „Zestaw kart Okey” (typ 3/10, stos 200, jak
  70617), 50275 „Złota Skrzynia Okey”, 50276 „Srebrna Skrzynia Okey”, 50277 „Brązowa Skrzynia Okey”,
  50267-50269 „Świąteczna Złota/Srebrna/Brązowa Skrzynia Okey” (typ 23, stos 200, jak 50270);
  `mob_proto` klienta: 20417 „Stół Okey” (kopia 20005), jeśli go nie ma.
- z GF 26.1.11 (`/opt/metin2/cache/gf/Gameforge_26.1.11/_client`): cały katalog
  `d:/ymir work/ui/minigame/rumi/` (77 plików) i `ui/minigame/rumi_nor/rumi_nor_bg.tga`; atlasy,
  do których odwołują się te `.sub`: `d:/ymir work/ui/public_minigame.dds`,
  `public_effect_01.dds`, `public_effect_02.dds`; strona oczekiwania: `ui/event/slot.sub`,
  `ui/event/count_bg2.sub`, `ui/event/horizontal_line_left.sub`, `horizontal_line_right.sub` (atlas
  `ui/event_002.dds`), `ui/pattern/border_a_*.tga` (9 plików), `ui/public/public_intro_btn/prev_btn_01/02.sub`,
  `next_btn_01/02.sub` (atlas `ui/public_intro.dds`), `ui/public/parameter_slot_07.sub`,
  `ui/public/check_image.sub` – każdy, którego nie ma w naszych paczkach (atlasy o tej samej nazwie
  sprawdzić, czy nasze nie są inną wersją z innym układem);
- ikony `icon/item/79505.tga`, `79506.tga`, `50267.tga`, `50268.tga`, `50269.tga`;
- model stołu `d:/ymir work/npc/okey_npc/` (`okey_npc.gr2`, `.dds`, `.msm`, `motlist.txt`,
  `wait.gr2/.msa`, `wait1.gr2/.msa`).

## Poprawki po teście klienta 2.0.35 (1 października)

- `uiminigameutil.py` (nowy): `UpdateTicker` – nasze exe nie woła pythonowego `OnUpdate` dla
  `ImageBox`/`ExpandedImageBox`/`Button`/`TextLine`, więc animacje i lecące karty napisane jako
  obrazek z `OnUpdate` stały w miejscu (Złap Króla: efekt „Moja karta” na pierwszej klatce, plansza
  zablokowana). Ticker to zwykłe okno-dziecko, które co klatkę woła `TickUpdate()` właściciela.
  `LoadError`/`SafeCreate` – błąd wczytania okna idzie do syserr i do czatu, okno się nie otwiera
  (zamiast `exception.Abort`, który zamykał klienta). `DescriptionText` – zasady gier jako
  zwykłe `TextLine` w ramce opisu (stronicowanie strzałkami, zawijanie po szerokości).
- `uiminigamerumi.py` + `uiscript/minigamerumi*.py`: teksty okien przez `uiScriptLocale`
  (uiscript nie może importować `uiminigamerumi` – był `None` i klient padał); bezpiecznik
  odblokowania kart po 6 s.
- `uiminigameyutnori.py`: `SetOnMouseLeftButtonUpEvent` dostaje zwykłą metodę (nasz `ui.py` sam
  owija ją w `__mem_func__`).
- `uiminigamecatchking.py`: animacje przez ticker; bezpiecznik – po 3 s bez końca animacji gra
  wykonuje zaległy krok i odblokowuje planszę.
- `uiflowerevent.py`: pole ilości wymiany na `public/parameter_slot_00.sub` (`cheque_slot.sub`
  leży w wierszach 506–524 atlasu `public.dds` 256×524 i nasze exe rysowało z niego czerwony pasek
  z wiersza 0).
- `uitooltip.py`: 6. i 7. bonus – `world.item_attr_rare` liczy bonusy starą listą APPLY (STR = 5),
  a nasze tooltipy (i `item_attr`) numerami `POINT_*` (STR = 12); typ z rzadkiego slotu jest
  zamieniany na `POINT_*` (`RareAttrType`), gdy tooltip nie zna go jako `POINT_*` (STR 5, CON 3, …);
  numery dwuznaczne (6, 8, 15, 17, 19, 53, 59–62) zostają `POINT_*` – to stosuje serwer. Właściwa
  poprawka jest po stronie serwera (`item_attr_rare` na nazwy `POINT_*`).
- `uiseonhae.py`: bez `item.SelectItem(0)` („Cannot find item by 0”).
- `minigames/d_/ymir work/npc/yut/wait1.msa` … `wait6.msa`: bez efektu
  `effect/monster2/npc_yut_result_02.mse` (nie ma go w kliencie GF ani w innych źródłach).

## Dom Towarowy 2 (wydanie oficjalne, klient 2.0.60) – bez zmian exe

Serwer: `server-patches/shopsearch2` (`MT2009_PLUS_SHOP_PART_STACK_V1`, `MT2009_PLUS_SHOP_SEARCH_PL_V1`).
Pliki `root` (baza: paczka `root` 2.0.30/`tcm/c31` – nasze wersje z „Kup wiele”, scalone ze zmianami
2.0.57 → 2.0.60; bez `playerbot_lang`, teksty tylko po polsku):

- `customfleamarket.py` – kupno części stosu (ilość od 1, cena części zaokrąglona w górę, wiersz
  od razu pokazuje resztę), polskie wielkie litery w wyszukiwaniu (`PolishLower`), Ulepszacze bez
  „+” pokazują zwykłą wersję („+”/„+3” przywraca ulepszone), Zbroje i Hełmy rozwijane na klasy
  (filtr po antyflagach, tylko w kliencie), okno „Filtry” (do 5 bonusów z minimalną wartością,
  w kliencie na pobranych ofertach), sortowanie po kliknięciu nagłówków „Ilość” i „Cena” (obie
  kolumny naraz), „R”/„C” (odśwież / wyczyść filtry) przy krzyżyku okna, krótka paginacja
  „<< 1 / N >>”. „Kup wiele” (pola wyboru, „Kup wszystko”, „Odznacz”) zostaje – kupuje całe linie.
- `offlineshopsearch.py` – okno ilości dla stosu otwiera się na 1.
- `offlineshopmanage.py` – „Cena sprzedaży” w oknie wystawiania 2 px wyżej (y 57).

## Magazyn: „Ułóż i scal” i „Tylko scal stosy” – bez zmian exe

Znacznik `MT2009_PLUS_SAFEBOX_ARRANGE_V1`. Serwer: `/safebox_arrange` (było w silniku,
`playerbot_arrange::ArrangeSafebox`) i `/safebox_arrange merge` (`server-patches/safeboxmerge`,
`MT2009_PLUS_SAFEBOX_MERGE_V1`, `playerbot_arrange::MergeSafeboxStacks`). Pliki `root` (baza: wpisy
paczki `root` 2.0.30–2.0.38, bez zmian od 2.0.28); wszystkie trzy są już w paczce (bez nowych wpisów):

- `uiscript/safeboxwindow.py` – na pasku tytułu magazynu dwa przyciski jak w ekwipunku: po lewej
  „Ułóż i scal” (ikona `flamewind/public/refresh_button_0x`), po prawej „Tylko scal stosy” (ikona
  przycisku ekwipunku `flamewind/inventory/autostack_0x`).
- `uisafebox.py` – przyciski wysyłają jedną komendę (cały magazyn, wszystkie strony, po stronie
  serwera); pakiet przenoszenia w magazynie nie łączy stosów (`ENABLE_MT2009_DISABLE_SAFEBOX_STACK`),
  a seria przeniesień trafiałaby w limity pakietów. Drugie kliknięcie, zanim przyjdzie odpowiedź,
  nic nie robi (5 s bez odpowiedzi zwalnia przyciski; serwer trzyma 2 s między prośbami). Nic nie
  idzie, gdy przedmiot wisi na kursorze albo trwa otwieranie sklepu; handel, sklep, inne okno –
  odmawia serwer. Wynik po polsku na czacie (`OnArrangeResult`).
- `game.py` – `SafeboxArrangeResult` → `uiSafebox.OnArrangeResult`.

## Systemy Digi Rasty: Przebudzenie, kamienie duchowe +9, koń do 30 – bez zmian exe

**Autor: Digi Rasta** (paczka „nowy-system” v0.16; jego `klient.py` pokazywał, czego potrzebuje klient).
Znaczniki `MT2009_PLUS_AWAKENING_V1`, `MT2009_PLUS_SOULSTONE9_V1`, `MT2009_PLUS_HORSE30_V1`; serwer:
`server-patches/digirasta`, `apply.sh`, questy `konie` i `horse_inventory`.

- `tools/digirasta/patch_digirasta_client.py` (obraz `m2pack-lzo`, idempotentne) – `gamedata/item_proto`:
  siedem rodzin broni przebudzonych +0…+9 (210, 220, 1160, 2190, 3170, 5150, 7170) tymi samymi wartościami
  co `apply.sh`, kamienie duchowe +5…+9 (28530+k, 28g00+k: typ, bonus, `value5`), nowy rekord Kamienia
  Przebudzenia 30670 (kopia 30228, stos 200); `gamedata/item_list.txt` i `locale/pl/itemdesc.txt` – wiersz
  30670 (ikona 30228); `gamedata/mob_proto` – nazwa 20119 „Czarny Rumak”. Nowych wpisów paczek nie ma.
  Sprawdzone rekord po rekordzie (141) z `world.item_proto` po `apply.sh`.
- `root` (wpisy paczki `root`, zastępowane – bez nowych): `uitooltip.py` (opis przedmiotu pokazuje
  wszystkie 7 bonusów), `uihorseinventory.py` (rzędy juków do 30 poziomu konia – tabela questu
  `horse_inventory`), `uiattributelist.py` („Silny przeciwko potworom” w spisie bonusów – bonus konia od 21).

## Olejek Niebios i poprawki klienta Digi Rasty (v0.17 / 0.17.2) – bez zmian exe

**Autor: Digi Rasta** (paczka „nowy-system” v0.17 i v0.17.2: `66_olejek.sql`, `OLEJEK_NIEBIOS`,
`OPISY_ZMIENIONE`, `IKONY_POPRAWKI`/`IKONY_DODATKOWE` i `ROOT_PATCHES` jego `klient.py`), przeniesione jako nasz kod.
Znacznik `MT2009_PLUS_HEAVEN_OIL_V1`; serwer: `apply.sh` (blok kamieni duchowych), `playerbot_awakening.h`.

- `tools/digirasta/patch_digirasta_client.py` (to samo narzędzie, nadal idempotentne):
  - `gamedata/item_proto` – Olejek Niebios (71056) jak na serwerze: typ 5/0, stos 200, antiflag 0, flag 4, wear 0,
    wartości 0 (wcześniej unikat na 5 dni);
  - `locale/pl/itemdesc.txt` – wiersz 71056 zastąpiony: składnik ulepszania Kamieni Duszy (1, 1, 2, 2, 3 sztuki
    od +4, obok Magicznego Pyłu), skąd wypada (Silna Lodowa Wiedźma, Beran-Setaou, Królowa Dżungli);
  - `gamedata/item_list.txt` – 7170 (Wachlarz Leżąc. Smoka+0) dostaje ikonę swojej rodziny `icon/item/07180.tga`
    zamiast ikony Wachlarza 8 Trygramów (`07170.tga` istnieje, ale to ikona 7180–7189; tylko kolumna ikony),
    dopisany brakujący wiersz `22030\tETC\ticon/item/22000.tga` (Zwój Teleportu).
- `root/uiminigameyutnori.py` – Yut Nori: okienko „rzuć jeszcze raz” zamykane przez `Hide()` zamiast `Close()`
  (jego akcja to ten sam przycisk – rekurencja do limitu Pythona i setki pakietów rzutu).
- `root/uichestpreview.py` (nowy w tym katalogu – kopia `client-2.0.18/root/uichestpreview.py`, ta sama co wpis
  paczki `root` klienta 2.0.42, poprawiona):
  podgląd skrzynki – duże liczby skracane (10k, 1.5M) i ustawiane od prawej krawędzi slotu, bez nachodzenia
  na sąsiednie sloty.

## Ekwipunek: blokada sortowania (Alt + LPM) – bez zmian exe

Znacznik `MT2009_PLUS_INVENTORY_SORT_LOCK_V1`. Serwer: `server-patches/sortlock` (`/inventory_arrange [merge]
keep=<hex>`, `playerbot_arrange::InventoryArrangeCommand`; zablokowany przedmiot zostaje na polu, zablokowany stos
przy łączeniu tylko przyjmuje sztuki). Pliki `root` (baza: wpisy paczki `root` 2.0.39):

- `inventorysortlock.py` (nowy) – blokady po stronie klienta, osobno dla postaci (`autohunt/sortowanie/<nick>.cfg`,
  wiersze `pole=vnum`); blokada idzie za przedmiotem przeniesionym ręcznie w całości, kończy się, gdy na polu stoi
  inny przedmiot (puste pole – przy następnym sortowaniu); ulepszenie broni/zbroi jej nie zdejmuje.
- `inventoryarrange.py` (wpis paczki z 2.0.24, zastępowany) – oba przyciski („Ułóż i scal”, „Tylko scal stosy”)
  dopisują `keep=<hex>`, gdy coś jest zablokowane; serwer bez poprawki (kod 8) → komunikat o braku obsługi.
- `uiinventory.py` – Alt + LPM na przedmiocie w plecaku przełącza blokadę (przy otwartym czacie albo pisaniu
  szeptu Alt + LPM wkleja link jak dotąd); gwiazdka w lewym górnym rogu pola (obrazki-dzieci okna slotów
  z `not_pick`, nad odliczaniem i podświetleniem aktywnej mikstury); wiersz „Zablokowany przy sortowaniu
  (Alt+LPM)” w opisie przedmiotu; ręczne przeniesienie przekazuje blokadę (`__SendMoveItemPacket`).
- `mt2009_ui/sortlock/star.tga` (nowy) – złota gwiazdka 11×11, 32-bit TGA jak `mt2009_ui/sidebar`.
