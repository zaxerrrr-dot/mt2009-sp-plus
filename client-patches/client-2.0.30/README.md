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

## Stosy 200 i poprawki Digi Rasty (v0.23.0) – bez zmian exe

**Autor: Digi Rasta** (paczka „nowy-system” v0.23.0: `20_stakowanie.sql`, `STACK_*` i `ROOT_PATCHES` jego
`klient.py`), przeniesione jako nasz kod. Znaczniki `MT2009_PLUS_DIGI_STACK_V1`, `MT2009_PLUS_DIGI_FIXES_V1`;
serwer: `server-patches/digirasta-fixes`, `apply.sh`.

- `tools/digirasta/patch_digirasta_stack.py` (obraz `m2pack-lzo`, idempotentne) – `gamedata/item_proto`: każdy
  kamień duchowy (typ 10), każda skrzynia-prezent (typ 23) i szkatułki / skrzynie z listy `apply.sh` – flaga 4,
  bez `ANTI_STACK`, stos 200; Odłamek Smoczego Kamienia (30270) bez limitu 24 h. Nowych wpisów paczek nie ma.
- `root/uiinventory.py` – kamień duchowy upuszczony na ten sam kamień łączy stos (wcześniej pytał o gniazdo
  i serwer odmawiał).
- `root/game.py` – komenda `CubeReload` (`/reload c`): klient zapomina listy receptur kostki i przy następnym
  otwarciu prosi o nowe.
- `root/uitip.py` (nowy w tym katalogu – wpis paczki `root` klienta 2.0.44, poprawiony) – ogłoszenia
  (TipBoard, BigBoard) bez kodów koloru `|c…|r` i linków `|H…|h`: pole tekstowe ich nie rysuje, szły dosłownie
  i psuły środkowanie.

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

## Auto-cena przy wystawianiu (rozszerzenie „Auto-cena Extension”) – bez zmian exe

Znacznik `MT2009_PLUS_SHOP_AUTO_PRICE_V1`. Serwer bez zmian: `/flea_price <id> <okno> <pole> 3` (`cmd_gm.cpp`
`do_flea_price`, `playerbot_manager` `SendFleaMarketPriceQuote`/`SendFleaMarketShopItemPriceQuote`,
`server-patches/playerqol` `MT2009_PLUS_FLEA_SALES_V1`) odpowiada `FleaPriceRange` (min/maks podobnych ofert
innych sklepów dla takiego stosu), `FleaPriceSales` (ostatnia sprzedaż i mediana botów) i `FleaPriceQuote`
(cena wystawiania botów). Okno 255 = linia własnego sklepu po id; inne okno niż ekwipunek i wyłączony Dom
Towarowy – brak odpowiedzi. Z rozszerzenia przeniesione tylko jego zmiany (jego `game.py` i
`offlineshopmanage.py` miały starszą bazę); pliki `root`:

- `shopautoprice.py` (nowy) – przycisk „Ceny” i okno cen dla okna ceny w kreatorach sklepu
  (`offlineshopbuilder.py`, `uiprivateshopbuilder.py`); tryby: Minimalna, Nieaktywna, Maksymalna, Mediana,
  Sugerowana, Ostatnia (jedno ustawienie `shop_auto_price.cfg` z oknem własnego sklepu). Cena wpisywana tylko,
  gdy gracz nie zmienił ceny w oknie. Poprawki względem rozszerzenia: tylko słabe referencje do okna ceny
  (cykl przycisk↔okno trzymał okno ceny prywatnego sklepu na ekranie po akceptacji), okno smoczego kamienia
  nie wysyła zapytania (serwer go nie obsłuży), brak odpowiedzi po 6 s – komunikat zamiast „Pobieranie…”,
  okno „Ceny” zamyka się samo, gdy okno ceny zniknie (zamknięty kreator, teleport), Esc z okna „Ceny”
  zamyka oba (także po zmianie przedmiotu), cena przycinana do 9 cyfr w oknie prywatnego sklepu.
- `offlineshopmanage.py` – okno „Ceny” własnego sklepu: sześć przycisków trybu zamiast jednego
  przełączanego, „Zmień ceny wszystkich” (cena każdej linii wg trybu, przez `shoppricepump`; pytanie
  przed zmianą, odrzucane przy łącznej wartości ≥ 2 mld, przerwane przy zamknięciu okna sklepu), tekst
  „Pobieranie danych cenowych…” i po 6 s „Serwer nie podał cen…”, odpowiedź na pojedyncze okno nie gubi
  się po starcie zmiany wszystkich, opis przedmiotu pod kursorem odświeżany po zmianie ceny, Esc z „Ceny” zamyka też okno ceny.
- `offlineshopbuilder.py`, `uiprivateshopbuilder.py` (wpisy paczki `root`, zastępowane) – wywołania
  `shopautoprice`, poprzednie okno ceny zamykane przy nowym przedmiocie, zamknięciu i zniszczeniu kreatora.
- `shoppricepump.py` (wpis paczki `root`, zastępowany) – nic nie wysyła poza fazą gry (`warpsafe.InGame()`),
  komunikat dwujęzyczny.
- `playerbot_lang.py` (nowy) – `T(pl, en)`: polski dla klienta po polsku, angielski dla każdego innego
  (`systemSetting.GetLanguage()`); bez `AnswerServer` rozszerzenia (serwer nie zna `/playerbot_lang`).
- `game.py` – `FleaPriceQuote`/`FleaPriceRange`/`FleaPriceSales` przekazują też do `shopautoprice`
  (id zapytań kreatorów od 1 500 000 000).

## Zapisane pozycje (teleport, 6 miejsc) – bez zmian exe

Znacznik `MT2009_PLUS_TP_BOOKMARKS_V1`. Okno Arezzo `root/uilocation.py` (25 pozycji na 5 stronach, tabela w
bazie, pakiety i `net.SendLocationManagerPacket`, których exe 2.0.25 nie ma) przerobione na 6 pozycji na
poleceniach czatu. Serwer: quest `tp_bookmarks` (`linux-port/docker/game/quest/tp_bookmarks.quest`, lista
w Dockerfile), bez zmian silnika. Dla gracza: przycisk „Zapisane pozycje” na pasku ikon przy ekwipunku
otwiera okno; „Zapisz” zapisuje obecne miejsce (nazwa do 15 znaków), „Teleport” przenosi na zapisane
miejsce, „Usuń” czyści pozycję. Teleport zużywa 1 czysty Zwój Powrotu z ItemShopu (22010, także 22020
Zwój Teleportacji; czysty = bez zapisanej w nim pozycji), co 15 minut; bez czystego zwoju w ekwipunku nie
działa ani zapis, ani teleport. Zwykłe użycie zwoju działa jak dotąd. Pozycje są w flagach questa postaci
(zostają po relogu). Tylko mapy otwarte (miasta własnego królestwa, mapy M3, 61–70 bez Wieży Demonów, 104,
301–304 od 90 poz., 209 i 362 od 95 poz., 360–361); nigdy lochy, instancje, mapy eventów, wojen,
przepustek (71–73). Serwer sprawdza wszystko jeszcze raz przy teleporcie. Pliki `root`:

- `uitpbookmarks.py` (nowy) – okno 470×(6 wierszy), linia czystych zwojów i odliczanie do następnego
  teleportu, pytania przed teleportem/nadpisaniem/usunięciem, okno nazwy. Wysyła `/tpzapis
  lista|zapisz|usun|tp` tylko po kliknięciu i tylko w fazie gry (`warpsafe.InGame()`); odbiera `TPBM
  begin|slot|end`.
- `uiinventory.py` – przycisk `teleport` na pasku ikon (`SidebarWindow.BUTTONS`).
- `game.py` – polecenie `TPBM` i zamknięcie okna z resztą.
- `mt2009_ui/sidebar/teleport_01.tga`, `_02`, `_03` (nowe) – ikona: ramka przycisku lochów i zwój
  `icon/item/22000.tga`, zrobione `tools/tpbookmarks/make_icons.py`.

## Kołczan z ItemShopu (MT2009_PLUS_QUIVER_V1)

`tools/quiver/patch_quiver_client.py` – nowy przedmiot 8010 „Kołczan” (ItemShop, 100 SM, 14 dni): rekord
`item_proto` (kopia Srebrnej Strzały 8005: WEAPON/ARROW, slot strzał, tylko ninja, bez handlu/sprzedaży/
wyrzucania, limit `LIMIT_REAL_TIME` 1 209 600 s, wartości 0/0/100/25/1300/2250), wiersz `item_list.txt`
(`icon/item/08010.tga`) i wiersz `itemdesc.txt`. Ikona `tools/quiver/08010.tga` (32×32 RGBA, narysowana – GF
26.1.11 nie ma ikony kołczanu) to **nowy wpis paczki `icon`**. Klient 2.0.x nie zna `WEAPON_QUIVER`, więc
kołczan jest strzałą z limitem czasu; nielimitowane strzały daje serwer (`server-patches/quiver`).

## Zbroja „warrior king03” i miecz – kostium i nakładka z ItemShopu (MT2009_PLUS_WARRIOR_KING03_V1)

`tools/king03/patch_king03_client.py` – dwa nowe przedmioty z paczek właściciela (3 października), 100 SM, 30 dni:

- **41986 „Zbroja Króla Wojowników+”** – kostium (COSTUME/BODY), kopia Wikinga Światła+ (41982), **tylko
  wojownik, tylko postać męska** (antiflag 49337 = 49281 + ninja 8 + sura 16 + szaman 32). Paczka nie ma
  modelu żeńskiego (jej README: brak `pc2/warrior/warrior_king03.dds`). Kształt 41986 tylko w
  `gamedata/warrior_m.msm`: model z paczki jako `warrior_king03.gr2` (+ `_lod_01..03`), skóra
  `warrior_king01.dds` (plik bazowy pc_1, który model wskazuje) zamieniona na nowy `warrior_king03.dds`.
- **40233 „Święty Miecz Bogów+”** – nakładka na broń (COSTUME/WEAPON), kopia Miecza Smoka Północy+ (40227):
  miecz jednoręczny (value3 0), wojownik/ninja/sura (antiflag 49312). Model z paczki (`07300.gr2`) jako
  `d:/ymir work/item/weapon/costume/40233.gr2` (GF ma swój, inny `07300.gr2`), tekstura
  `d:/ymir work/item/weapon/bamboomt2_0005.dds` (ścieżka zapisana w gr2).

Wiersze: `gamedata/gf_official_costumes.txt` (klient czyta kosmetyki 40xxx/41xxx z tej tabeli, nie z
`item_proto`), `item_list.txt` (ikony, model miecza), `itemdesc.txt` (opisy), `gamedata/warrior_m.msm`
(nowa grupa ShapeData, ShapeDataCount + 1). **Nowe wpisy paczek** (`tools/king03/assets`): `icon` –
`icon/item/41986.tga`, `icon/item/40233.tga`; `gamedata` – `d_/ymir work/...` jako `d:/ymir work/...`
(model i tekstura zbroi, model i tekstura miecza). Serwer: `apply.sh` (MT2009_PLUS_WARRIOR_KING03_V1).
Paczka robocza do budowy klienta: `/opt/metin2/cache/c53-staging` (README.txt tam).
## Wygody Digi Rasty: serwer i jego komendy (nowy-system v0.23.0) – exe opcjonalnie

**Autor: Digi Rasta.** Znacznik `MT2009_PLUS_DIGI_SERVER_QOL_V1`; serwer i decyzje:
`server-patches/digirasta-qol/README.md`. Pliki `root`:

- `digiserverqol.py` (nowy; `digiqol.py` to część kliencka Digi Rasty) – komendy serwera `RefineFailedType`, `KillBar`, `KillSound`, `SkillCoolTimeReset`,
  `DeadTime`, `NOWY_KSIEGI`, wpisywane do `serverCommander` okna gry.
- `uikillbar.py` (nowy) – pasek zabójstw w prawym górnym rogu (5 wierszy po 6 s), ikony
  `mt2009_ui/killbar/*.png` (16, z jego paczki).
- `uiskillbookexchange.py` (nowy) – okno wymiany ksiąg u Seon-Hae (`/nowy_ksiegi`). MT2009_PLUS_BOOK_EXCHANGE_V2: 20 pól na całe stosy, prawy klik w ekwipunku dodaje księgę (Ctrl: wszystkie z torby; `uiinventory.py`, `OnRightClickBagItem`), prawy klik na polu okna ją wyjmuje, przyciski „Wymień” / „x10” / „Wszystko” (pytanie przed wymianą wielokrotną).
- `mt2009_ui/killstreak/1..13.wav` (nowe, 5,3 MB) – dźwięki serii zabójstw (z jego paczki).
- `game.py` – `digiserverqol.Register(self)` po komendach serwera, `digiserverqol.DestroyWindows()` przy zamknięciu okna gry.
- `uichat.py` (wpis paczki `root`, zastępowany) – „@nick tekst” w zwykłym czacie = szept; w trybie handlu
  (TAB) i dla „@ tekst” dalej czat handlowy.
- `uirestart.py` (wpis paczki `root`, zastępowany) – okno śmierci odlicza sekundy na przyciskach, nieaktywne do zera.
- `uichestpreview.py` – „Otwórz” / „Otwórz 10” w podglądzie skrzynki (co 0,25 s, `warpsafe.InGame()`).

Reset odnowień po śmierci w samym kliencie potrzebuje `player.ResetSkillCoolTimes()` (łatka exe
`server-patches/digirasta-qol/digi-server-qol-exe.patch`, `ENABLE_SKILL_COOLTIME_RESET`); bez niej serwer i tak zeruje odnowienia.


## Pakiet Vekiriona: skróty klawiszowe, szybkie otwieranie, „Wszystkie” w Alchemii – bez zmian exe

Znacznik `MT2009_PLUS_VEKIRION_V1`. **Autor: Vekirion** (paczka z 3 października 2026). Jego pliki były
pełnymi kopiami starszego `root` (ok. 2.0.41); przeniesione tylko jego zmiany, dopasowane do naszych
klawiszy. Serwer: `server-patches/vekirion` (limit 60 skrzynek na 500 ms tylko dla `ITEM_GIFTBOX`,
reszta przedmiotów bez zmian). Pliki `root`:

- `keybind.py` (nowy) – wszystkie skróty okna gry jako akcje (2 klawisze na akcję, kombinacje
  Ctrl/Shift/Alt), zapis dla komputera w `autohunt/klawisze.cfg` (tylko zmienione akcje; brak/uszkodzony
  plik albo wiersz = domyślne). Domyślne = klawisze, które klient miał: X Wyprawy, Ctrl+G jazda, Ctrl+J
  zdjęcie pieczęci (wcześniej README mountquickswap obiecywało, a klawisz otwierał kosz), Z i ~ podnoszenie,
  Ctrl+Z filtr, F11/F12, K Auto Łowy, P towarzysz itd. **Sprint: Lewy Shift jak dawniej** – stuknięcie
  samego Shifta (wciśnięty i puszczony bez innego klawisza, Entera ani kliknięcia w plecaku) włącza/wyłącza
  sprint przy puszczeniu; Shift+M, Shift+Enter, Shift+klik są tylko modyfikatorem. Gracz może przenieść
  sprint np. na Caps Lock. Okna bez klawisza (Battle Pass, Zapisane pozycje) mają akcję bez klawisza.
- `uikeybind.py` (nowy) – okno „Skróty klawiszowe” (Esc → przycisk nad „Sklep z przedmiotami”): lista
  po kategoriach, klik na klawisz czeka na nowy (Esc anuluje, Backspace/PPM czyści), klawisz zabrany innej
  akcji jest wypisany, „Domyślne”, „Zapisz” (bez zapisu zmiany przepadają), stałe klawisze i kliknięcia
  okien (Alt + LPM blokada sortowania, Ctrl + PPM otwieranie skrzynek…) na końcu listy.
- `game.py` – `__BuildKeyDict` buduje akcje zamiast słowników `DIK_*`; `OnKeyDown`/`OnKeyUp` pytają
  `keybind` (stuknięcie Shifta, przechwytywanie klawisza dla okna), Esc anulujący czekanie nie otwiera menu.
- `uisystem.py`, `uiscript/systemdialog.py` – przycisk „Skróty klawiszowe” (obok „Opcje dodatkowe” Digi
  Rasty; `Recalculate` układa przyciski).
- `uihelp.py` (wpis paczki `root`, zastępowany) – okno pomocy (H) pokazuje aktualne klawisze w wierszach
  z klawiszem, gdy gracz je zmienił; zamyka się swoim klawiszem.
- `updateable.py` (wpis paczki `root`, zastępowany) – trzymane podnoszenie według `keybind` (Ctrl+Z nie
  podnosi).
- `uiinventory.py` – podpowiedzi paska ikon z aktualnym klawiszem („Kosz (J)”); **Ctrl + PPM** na stosie
  skrzynek (`ITEM_GIFTBOX`, bez pytania przed użyciem) otwiera do 50 sztuk (50 użyć na 0,5 s, ponowienie
  odrzuconych, stop przy pełnej stronie Alchemii dla Cor Draconis, ponowne Ctrl + PPM zatrzymuje);
  Shift + LPM: pole „Paczki po:” dzieli stos na paczki po N sztuk w wolne pola; obie serie stają przy
  teleporcie (`warpsafe.InGame()`).
- `uidragonsoul.py` – przycisk „Wszystkie” obok „Uszlachetnij” (tryb Klasa lub Stopień): uszlachetnia
  wszystkie pełne zestawy kamieni ze strony Alchemii (do 10 żądań naraz, Yang liczony z wysłanymi,
  odmowa serwera albo brak odpowiedzi 5 s kończy, podsumowanie w czacie); Poziom: kamień i stos kamieni
  wzmocnienia wracają do okna po próbie. Zgodne z jednym komunikatem okna i sprawdzaniem przed wysłaniem
  (2.18.1): ręczne „Uszlachetnij” podczas serii nic nie robi.
- `offlineshopmanage.py`, `offlineshopbuilder.py`, `uiprivateshopbuilder.py` – Enter w oknie ceny nie
  otwiera już czatu pod spodem (funkcje akceptacji zwracają `True` na każdej ścieżce), Enter w oknie
  zmiany ceny działa jak OK.
- `uiaffectbar.py` – efekt bez ikony w `AFFECT_SHOW_DATA` nie wywraca paska (log zamiast `KeyError`).

Pominięte z paczki: Shift + klik w torbie towarzysza (`uisidekickinventory.py`) – to samo robi już nasz
prawy klik (`MT2009_PLUS_SIDEKICK_QUICK_TRANSFER_V1`); `XMAS_SNOW_SHOW` w
`game.py` (wyłączał śnieg i świąteczną muzykę z nocnej flagi) – nie był częścią zgłoszenia.

## Bonusy na pasku celu (Vekirion) – bez zmian exe i serwera

Znacznik `MT2009_PLUS_TARGET_BONUS_V1`. **Autor: Vekirion** (paczka `root` z 6 października 2026, zbudowana na
naszym `root` 2.0.55 – zmienił tylko `uitarget.py` i dodał `mobraceflag.py`). Pod nazwą i paskiem HP potwora/Metina
(cel wroga albo kamień) wiersz „Silny przeciwko: Zwierzętom 12%, Bossom 5%, Potworom 10%” – bonusy, które serwer
(`battle.cpp` CalcAttBonus) liczy przeciw temu celowi, z wartością gracza (`player.GetStatus`):

- rasy z flag mob_proto: Zwierzętom, Nieumarłym, Diabłom, Ludziom, Orkom, Mistykom, Insektom, Potworom pustyni
  (FIRE/ICE/TREE bez bonusu przedmiotu pominięte, żywioły `ATT_*` też – serwer ma je zakomentowane);
- ranga Boss+: „Metinom” (kamień) albo „Bossom”; „Potworom” dopisane tylko, gdy gracz ma ten bonus;
- odświeżane co 0,5 s, więc zmiana ekwipunku widać od razu; plansza rośnie do 52 px wysokości.

- `uitarget.py` (wpis paczki `root`, zastępowany) – `GetTargetBonusText`, wiersz `bonusText`, `__RefreshBonusText`.
- `mobraceflag.py` (nowy) – flagi ras potworów według vnum (exe nie ma `nonplayer.GetMonsterRaceFlag`), wygenerowane
  z `player.mob_proto` (`(setRaceFlag+0) & 2047`); sprawdzone 6.10: 668 wpisów = baza testowa. **Po zmianie flag ras
  w mob_proto trzeba go wygenerować ponownie.** Exe nie zna `POINT_ATTBONUS_INSECT/DESERT` – brane indeksy serwera
  (49/52), tylko gdy `POINT_ATTBONUS_HUMAN` klienta = 43.

## Zmiana bonusów i poprawka mgły (Vekirion)

**Autor: Vekirion** (paczka „VekirionAiO_v3”, 6 października 2026, `root` zbudowany na naszym 2.0.55). Z paczki wzięte
tylko te dwie rzeczy; pakiet 60+ FPS (`Ustaw_FPS.bat` łatający exe, `updateable.py`, `uisystemoption.py`,
`ui.py`, `eventmanager.py`, `interfacemodule.py`, `uiautohunt.py`, `uigoblin.py`, `uiminigamerumi.py` i linie
`FPS_CAP_RAISE_V1` w `game.py`) **pominięty**; bonusy pod nazwą moba są już wyżej (`MT2009_PLUS_TARGET_BONUS_V1`).
Jego `etc.index/.data` to inna, pełna paczka `etc` (m.in. `environment/*.msenv`) – bazowej paczki `etc` naszego klienta
nie ma na VPS, więc nie da się jej porównać; kod poprawki mgły jest w całości w `root`, `etc` nie jest przenoszone.

**Zmiana bonusów** – `MT2009_PLUS_BONUS_SWITCH_V1`, część serwerowa: `server-patches/bonusswitch` +
`playerbot_bonus_switch.h`. Okno z 5 polami (przedmiot na pole przeciągnięciem albo PPM w ekwipunku przy otwartym
oknie), wybór bonusów, które przedmiot może mieć, i ich minimalnych wartości, „Wszystkie” / „Co najmniej X z”,
szybkość 1–20 zmian/s, Start/Stop, „Zmień raz”. Zmienia serwer: 1 zmiana = 1 zmianka (najpierw 76014, potem 71084,
71284, 39028; kostiumy 70063/70064).

- `uibonusswitch.py` (nowy) – okno; komendy `/bonus_switch`, odpowiedzi `BSW ...`.
- `mt2009_ui/sidebar/bonusswitch_01/02/03.tga` (nowe) – ikona na pasku obok ekwipunku.
- `uiinventory.py` – przycisk paska, PPM na broni/zbroi przy otwartym oknie wkłada ją do pola zamiast zakładać.
- `keybind.py` – akcja „Zmiana bonusów” (`bonus_switch`, domyślnie bez klawisza).
- `game.py` – `serverCommandList["BSW"]`, klawisz, zamknięcie okna przy wyjściu.

**Poprawka mgły** – `MT2009_PLUS_FOG_FIX_V1`. W `introloading.py` ustawienia odległości widzenia
(`SetViewDistanceSet` 1–3) były zakomentowane, a zawsze wybrany był zestaw 0, który exe co klatkę przelicza z FPS
(od `app.SetMinFog` do 25600) – przyciski mgły w opcjach prawie nic nie zmieniały, a zasięg rysowania „pływał” przy
spadkach FPS. Teraz zestawy są ustawione (gęsta 16000, średnia 19200, lekka 25600), przycisk mgły wybiera swój
zestaw (`constInfo.APPLY_FOG_DISTANCE`), a `game.py` wybiera go ponownie po każdej zmianie środowiska (noc/dzień,
mapa świąteczna). Domyślna mgła: średnia (było: gęsta).

- `constinfo.py` (nowy w repo, z paczki 2.0.55) – `FOG_DISTANCE_LIST`, `APPLY_FOG_DISTANCE`, domyślnie `FOG_LEVEL1`.
- `introloading.py` (nowy w repo, z paczki 2.0.55) – `__StartGame`: zestawy odległości i wybór zestawu mgły.
- `game.py` – `constInfo.APPLY_FOG_DISTANCE()` po `SetEnvironmentData`.

## Ranking tygodniowy i tytuły – bez zmian exe

Znacznik `MT2009_PLUS_WEEKLY_RANKING_V1`. Na podstawie systemu rankingu tygodniowego z plików Arezzo
(`new_uiweeklyrank.py`, `uiscript/weeklyrank.py`; ich okno czytało pakiety, których exe 2.0.25 nie ma).
Okno jest nasze, na poleceniach czatu (`/ranking info|lista <kat>`, linie `WRANK`); serwer:
`playerbot_weekly_rank.h` i `server-patches/weeklyrank`. Pliki `root`:

- `uiweeklyrank.py` (nowy) – okno „Ranking tygodniowy”: 8 kategorii (zabite potwory, Metiny, bossy,
  zabici gracze, ukończone wyprawy, udane ulepszenia, alchemia, poziom), top 50 z przewijaniem
  (miejsce, korona top 3, nick z dopiskiem [Bot]/[Gracz], poziom, królestwo, wynik), własne miejsce
  i wynik, posiadacze tytułów wybranej kategorii (zwycięzcy poprzedniego sezonu) z bonusem, numer
  sezonu, odliczanie do końca, własne tytuły. Pasek pod oknem postaci z tytułami gracza
  (`AttachCharacterWindow`). Wysyła tylko po kliknięciu/otwarciu i tylko w fazie gry (`warpsafe.InGame()`).
- `playerbot_status_tail.py` – tytuł z rankingu nad nickiem posiadacza (gracza i bota) w wierszu
  tytułów botów (`textTail.AttachPersonality`): „Łowca I” w kolorze miejsca; tier Systemu Legend
  zostaje przed nim („Chodząca Legenda | Łowca I”), osobowość bota ustępuje.
- `game.py` – polecenie `WRANK` (`tail` do `playerbot_status_tail.show_rank_title`), akcja klawisza
  `weekly_rank`, zamknięcie okna z resztą.
- `keybind.py` – akcja „Ranking tygodniowy” (bez domyślnego klawisza, do ustawienia w „Skróty klawiszowe”).
- `uiinventory.py` – przycisk `ranking` na pasku ikon przy ekwipunku.
- `interfacemodule.py` – pasek tytułów pod oknem postaci.
- `mt2009_ui/ranking/` (nowe) – obrazki okna z plików Arezzo (`d:/ymir work/ui/new_weekly_rank/`):
  `row_1..4.png` (wiersze: złoty, srebrny, brązowy, zwykły), `title_1..4.png`, `crown_1..3.png`,
  `header_big.png`, `header_small.png`, `cat_0..2.tga` (przyciski kategorii). Każdy obrazek jest
  sprawdzany `pack.Exist` i ma zwykły zamiennik.
- `mt2009_ui/sidebar/ranking_01/02/03.tga` (nowe) – ikona: ramka przycisku lochów i korona z
  `image-example-005.png` Arezzo, zrobione `tools/ranking/make_icons.py`.

## Usuwanie misji (/usunmisje) – bez zmian exe

Znacznik `MT2009_PLUS_CLEAR_MISSIONS_V1`. Gracz wpisuje na czacie `/usunmisje`: otwiera się okno z misjami,
które ma teraz otwarte (z listem na liście misji), każda z polem wyboru (domyślnie zaznaczona). „Usuń
zaznaczone” (z pytaniem) ustawia je w ich własny stan ukończenia – bez nagród, bez rozmów, jakby były zrobione
dawno temu – więc nie wracają. Jeśli ukończenie misji uruchamia następną część łańcucha (fabuła, Biolog), ta
część startuje tak, jak przy zwykłym ukończeniu: otworzy się na swoim poziomie (np. 55), a gdy gracz ma już
ten poziom – od razu, i okno pokaże ją po odświeżeniu. Przedmioty samej misji (np. strona pamiętnika, list)
znikają z nią; przedmioty do oddania Biologowi zostają. List usuniętej misji znika od razu z listy misji,
jej przycisk z lewej strony ekranu i jej strzałki z mapy (`pc.clear_quest_letter`, poprawka silnika
`server-patches/clearmissions`) – bez teleportu i ekranu ładowania. Flaga eventu `mt2009_usunmisje_off 1`
wyłącza.

Usuwalne (tabela w quescie, z `tools/gen_usun_misje.py`): fabuła `main_quest_lv*`, `find_squareguard`,
`find_brother_article`, `patrol_townaround`; poboczne `subquest_*`, `new_quest_lv*`, `new_quest_premium_lv4`;
Biolog `collect_quest_lv*`; zioła Baek-Go `make_herb_lv*`. Nigdy: Towarzysz, Cor Draconis (`dragon_soul*`),
konie, gildia, umiejętności, samouczki łowienia/zielarstwa, reputacja, księgi misji, polowania, eventy, lochy,
Seon-Hae, `hwang_introduction` (jego ukończenie otwiera sklep), `trade_chat`, `warehouse_expand`,
`black_steel_crafting` i nasze questy systemowe. Serwer: quest `usun_misje`
(`linux-port/docker/game/quest/usun_misje.quest`, lista w Dockerfile). Pliki `root`:

- `uiusunmisje.py` (nowy) – okno 12 wierszy na stronę, „Zaznacz/Odznacz wszystkie”, licznik. Wysyła
  `/usunmisje usun <id…>` (do 20 na linię) i `/usunmisje gotowe` tylko po kliknięciu i tylko w fazie gry
  (`warpsafe.InGame()`); odbiera `MISJE begin|m|end` i `MISJE gone <indeks questa>` (zdejmuje przycisk
  listu przez `BINARY_ClearQuest` interfejsu). Po usunięciu otwiera się samo tylko dla misji, których nie
  było w poprzednim oknie (np. następna część łańcucha).
- `game.py` – polecenie `MISJE` (z interfejsem) i zamknięcie okna z resztą.

## Magazyn kolekcjonera (natychmiastowy) – bez zmian exe

Znacznik `MT2009_PLUS_COLLECTOR_STORAGE_V1`. Na podstawie systemu z projektu upstream (based on the
upstream Metin2 Playerbots project), przepisany tak, by wkładanie i wyjmowanie było natychmiastowe.
Serwer, zapis, protokół i powody opóźnień upstream: `server-patches/collector/README.md`.

- `uicollector.py` (nowy) – okno: kategorie z ikonami i licznikami, wyszukiwarka, siatka 10 × 10
  ze stronami, podpowiedzi, pasek zajętości, „Rozbuduj”; cały magazyn w pamięci okna, ruch pokazany
  od razu i wysłany jedną komendą (`warpsafe.InGame()`), serwer odsyła tylko zmieniony wpis.
- `uisafebox.py` – przycisk „Kolekcjoner” nad „Zmień hasło” (okno magazynu o 23 px wyższe).
- `uiinventory.py` – przy otwartym magazynie kolekcjonera PPM chowa przedmiot (Ctrl – wszystkie
  stosy rodzaju, Shift – ilość), upuszczenie wpisu na ekwipunek go wyjmuje.
- `game.py` – komenda serwera `COLL` → `uicollector.OnServer`.
- Nowe wpisy paczki `root`: `uicollector.py` i `mt2009_ui/collector/*` – ikony kategorii
  `cat_<all|equipment|materials|upgrade|books|stones|herbs|consumables|chests|gathering|quests|appearance|other>_<1|2|3>.tga`
  (25×25; sześć okrągłych ikon z paczki Arezzo `ekenvanter`, siedem złożonych w tej samej ramce z
  ikon przedmiotów), `catbtn_01..03.tga` (Arezzo `collections/button0x`), `header.tga`
  (Arezzo `new_weekly_rank/header_small`), `slot.tga` (GF `belt_inventory/slot_normal`),
  `search_01..03.tga` (GF `pattern/btn_search_0x`), `bar_empty.tga` / `bar_full.tga` (Arezzo
  `collections/total_progress_*`), `input.png` (Arezzo `collect_input`). Brak którejś grafiki w
  paczce gracza = zastępstwo z paczek klienta albo jej pominięcie (`pack.Exist`, `try`).

## Auto Łowy: szybki start/stop (Shift+K) – bez zmian exe

Znacznik `MT2009_PLUS_AUTOHUNT_QUICK_V1`. Shift+K (akcja `autohunt_quick` w Skrótach klawiszowych,
do przepięcia) albo nowy przycisk na pasku ikon przy ekwipunku od razu zaczyna polowanie bez
otwierania okna K; drugie naciśnięcie je zatrzymuje. Ustawienia są brane tak jak przy „Start” w oknie:
plik postaci wczytany raz (`EnsureLoaded`, także gdy okna nie otwierano), pola otwartego okna
najpierw – z włączonym atakiem. Czat: „Auto Łowy: szybki start, zasięg N (Shift+K - stop).” /
„Auto Łowy: stop.”. Odmowa serwera (`AutoHuntOff`: świat bez Auto Łowów albo brak czasu z
„Auto Łowy (8h)”) zatrzymuje polowanie tak samo jak przy starcie z okna.

- `uiautohunt.py` – `Hunter.QuickToggle`, `Start(startText)`, moduł: `QuickToggle()`, `IsRunning()`.
- `keybind.py` – akcja `autohunt_quick` (domyślnie Shift+K; samo K dalej otwiera okno).
- `game.py` – akcja w `__BuildKeyDict`.
- `uiinventory.py` – przycisk `autohuntgo` pod „Autołowy” (`SidebarWindow.BUTTONS`); plakietka
  zielona (strzałka) albo czerwona (kwadrat) w trakcie polowania, jakkolwiek je włączono.
- `mt2009_ui/sidebar/autohuntgo_01..03.tga`, `autohuntstop_01..03.tga` (nowe) – ikona Autołowów z
  plakietką, zrobione `tools/autohuntquick/make_icons.py` z `client-2.0.28` `autohunt_0N.tga`.

## Opcje Gry z zakładkami – bez zmian exe

Znacznik `MT2009_PLUS_OPTIONS_TABS_V1` (propozycja właściciela, 5 października). Menu Esc ma jeden przycisk
„Opcje Gry” zamiast czterech („Opcje Systemowe”, „Opcje Gry”, „Opcje dodatkowe”, „Skróty klawiszowe”).
Nad otwartym oknem stoi pasek zakładek **Gra / System / Dodatkowe / Skróty**; każda zakładka to dotychczasowe
okno (ustawienia, zapis i działanie bez zmian). Klik w zakładkę zamyka pokazane okno i otwiera wybrane w tym
samym miejscu (ten sam środek i górna krawędź), pasek idzie za przeciąganym oknem i znika, gdy okno się zamknie
(X, Esc, „Zapisz” skrótów). Szkic skrótów (niezapisane klawisze) zostaje przy przechodzeniu między zakładkami;
zamknięcie opcji go odrzuca, jak dotąd. Ostatnia zakładka i miejsce są pamiętane do wyjścia z gry.

- `uioptionstabs.py` (nowy) – pasek zakładek (`d:/ymir work/ui/game/windows/tab_button_large_01..03.sub`
  z paczki etc).
- `uisystem.py`, `uiscript/systemdialog.py` – przycisk `options_button` w miejscu „Opcje Systemowe”, cztery
  stare przyciski usunięte z listy (`Recalculate` układa resztę); `SystemDialog.GetOptionPage` tworzy okna
  tak jak wcześniej ich przyciski.
- `uikeybind.py` – `GetWindow`, `KeybindWindow.Suspend/Resume` (ukrycie ze szkicem przy innej zakładce).
- `uiopcjedodatkowe.py` – okno szersze (270 → 305), jak Opcje Systemowe pod paskiem zakładek.

## Karty Potworów (Monster Card System) – bez zmian exe

**Autor systemu: Digi Rasta** (paczka „nowy-system” v0.25.2 – jego port paczki „Official-Monster-Card-System”,
Best Studio). Znacznik `MT2009_PLUS_MONSTER_CARDS_V1`; serwer: `server-patches/monstercard`, nakładka
`playerbot_monster_card.h` (+ `_data.h`), `apply.sh` (tabele `player.nowy_karty_*`, przedmioty
50283/50284/72322/72323), przełącznik `M2_MONSTER_CARDS`. Okno otwiera przycisk „Karty Potworów” w menu pod Esc
(klawisz domyślnie żaden – J paczki to u nas Kosz; akcja `monster_card` w Skrótach klawiszowych).

- Nowe wpisy paczki `root`: `monstercard.py` (funkcje `player.*`/`net.*`, których okno paczki chce od exe,
  w Pythonie; komenda serwera `MONSTERCARDSYSTEM`; opis kart 50283/50284; podgląd potwora – obrazek karty ×2,
  model 3D dopiero z exe z `player.Mt2009Model*`), `monstercard_data.py` (pule, kolekcja, zestawy – bliźniak
  `playerbot_monster_card_data.h`), `monstercard_text.py` (polskie teksty), `uimonstercard.py` (okno paczki),
  `uiscript/monstercardwindow.py`, `uiscript/monstercardachievdetailwindow.py`; ikony `icon/item/50283.tga`,
  `50284.tga`, `72322.tga`, `72323.tga` (z klienta oficjalnego 26.1.11).
- Zastępowane wpisy `root`: `ui.py` (pierwszy raz w repo – kopia `ui.py` klienta 2.0.52 i metody `ui.py`
  klienta oficjalnego, których brakowało: `ui.MoveImageBox` w Pythonie, `Button.SetShowToolTipEvent` /
  `SetHideToolTipEvent` / `SetAlwaysToolTip` / `EnableFlash` / `DisableFlash`, `AniImageBox.ResetFrame`,
  `Window.LeftRightReverse`; funkcje `wndMgr` tylko gdy exe je ma), `uitooltip.py` (`ToolTip.SetThinBoardSize`,
  opis karty: potwór i obrazek), `game.py` (komenda `MONSTERCARDSYSTEM`, akcja klawisza), `keybind.py`
  (akcja `monster_card` bez klawisza), `uiscript/systemdialog.py` + `uisystem.py` (przycisk w menu pod Esc).
- `atlas/d_/ymir work/ui/game/monster_card/**` (244 `.sub`) i `atlas/d_/ymir work/ui/public_mcard_001.dds`,
  `public_mcard_card_001.dds` – grafiki okna z paczki, w buildzie jako `d:/ymir work/...` (paczka `root`).
- `tools/monstercard/patch_monstercard_client.py` (obraz `m2pack-lzo`, idempotentne) – `gamedata/item_proto`
  (od 2.0.52 w paczce `dbdata`): cztery nowe rekordy jak w `apply.sh`; `gamedata/item_list.txt` – ikony;
  `locale/pl/itemdesc.txt` (paczka `dbdata`) – opisy. Po buildzie klienta: nowa baza edytora bazy danych
  (`python3 -m m2clientpack.make_base <klient>/pack <wersja>` w `linux-port/docker/seban-panel`).
- Exe (później, na Windows): model 3D potwora w polu podglądu wymaga `player.Mt2009ModelShow/Select/Rotation/
  Zoom/UpDown/Reset/Motion` i `app.RENDER_TARGET_INDEX_ILLUSTRATED` (w paczce Digi Rasty: `CModelViewer`
  w jego `Mt2009Window.cpp`); nasze exe ma render target Yut Nori (`PythonYutnoriManager`, rasa 20505) –
  trzeba go uogólnić na dowolną rasę. Bez tego okno pokazuje obrazek karty ×2, przyciski kamery są ukryte.

## Przypomnienie o plikach klienta z edytora bazy danych (`MT2009_PLUS_DBDATA_STAMP_V1`)

Zip z panelu Seban („Pobierz aktualne pliki klienta (zip)”) ma w folderze klienta `dbdata_stamp.txt`: znacznik
plików (`stamp 2.0.53` bez zmian, `stamp 2.0.53-<12 hex>` ze zmianami) i rozmiary `pack/dbdata.*`, z którymi
przyszedł. Rdzeń przy każdym wejściu do gry (nie boty) wysyła `DbDataStamp <znacznik>` (`playerbot_dbdata_stamp.h`,
plik `/opt/m2spool/dbdata_stamp.txt` z panelu). Gdy serwer ma zmiany, a znacznik klienta jest inny (albo nie ma
pliku, albo aktualizacja klienta podmieniła `pack/dbdata.*`) – okienko i dwie linie na czacie, raz na sesję.

- Nowy wpis paczki `root`: `dbdatastamp.py`.
- Zastępowany `game.py`: komenda `DbDataStamp`, `dbdatastamp.Destroy()` przy zamknięciu okna gry.

## Punkty Rangi – owoce i rangi nad głową (`MT2009_PLUS_RANK_POINTS_V1`)

Część serwerowa: `server-patches/rankpoints` + `playerbot_rank_points.h`. „Dodatkowe rangi” z Arezzo: owoce
80050–80054 (Jabłko, Gruszka, Winogrono, Arbuz, Ananas – vnumy, typ USE/USE_SPECIAL, nazwy i ikony Arezzo),
nazwy rang (Waleczny, Mocarny, Potężny, Władca, Arcymistrz, Legenda) i kolory z `colorinfo.py` Arezzo
(`TITLE_RGB_GOOD_*`).

- `rankpoints.py` (nowy) – komendy `RANGA tail <vid> <ranga>` (ranga od 21 000 punktów w miejscu rangi za
  punkty nad głową, 0 = zwykła ranga) i `RANGA self <punkty> <ranga>` (własne punkty); z nowym exe
  `chrmgr.RegisterRankTitle` / `chrmgr.SetRankTitle` (`client-patches/exe`, `ENABLE_RANK_TITLE`), ze starym exe
  tytuł nakładany co 0,5 s przez `textTail.AttachTitle` (między odświeżeniami exe może mignąć zwykła ranga).
- `game.py` – komenda `RANGA`, odświeżenie dymka rangi w oknie postaci.
- `uicharacter.py` (z paczki 2.0.55, nowy w repo) – w dymku rangi (alignment) w oknie postaci: ranga, Punkty
  Rangi, bonus rangi i owoc na teraz (jak `ALIGN_BONUS` Arezzo).
- `icon/item/80050.tga` … `80054.tga` (nowe wpisy paczki `root`) – ikony Arezzo `icon/item/fruit_2, _1, _7, _6,
  _5.tga`, zapisane bez RLE.
- `tools/rankfruit/patch_rank_fruit_client.py` (obraz `m2pack-lzo`, idempotentne) – `gamedata/item_proto` i
  `locale/pl/itemdesc.txt` (paczka `dbdata`), `gamedata/item_list.txt` (paczka `gamedata`): 5 rekordów / wierszy
  jak w `apply.sh`. Po buildzie klienta: nowa baza edytora bazy danych (`m2clientpack.make_base`).
