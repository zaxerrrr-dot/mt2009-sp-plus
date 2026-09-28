# Klient 2.0.28: pasek boczny, Koło Fortuny, nowe pety, Poszukiwanie skarbów (goblin), Świątynia Ochao, lochy Razadora i Nemere

Względem klienta 2.0.27 (`client-patches/client-2.0.27`). Paczki są
kumulatywne: gotowe pliki są w `/opt/metin2/cache/tcm/c28/pack` (`root`,
`gamedata`, `locale`, `icon`, `maps`, `property`, nowe `newpet`, `ochao`, `goblin`,
`gf_razador`, `gf_nemere`, `gf_misc` i `Index`). Oficjalne zasoby z klienta Gameforge
opisuje sekcja „Zasoby z klienta Gameforge”.
Zbudowane przez `tools/build28.py` (obraz `m2pack-lzo`) z paczek testowego
klienta 2.0.27 (`/opt/metin2/cache/tcm/c27/pack`).

Układ katalogów: `<paczka>/<nazwa wpisu w paczce>`, a `d:/` jako `d_/`
(np. `goblin/d_/ymir work/npc2/...` = wpis `d:/ymir work/npc2/...` w paczce `goblin`).

## root (`root/`) – 11 zmienionych i 140 nowych plików

Zmienione: `game.py`, `localeinfo.py`, `uiinventory.py` (pasek boczny),
`uieventcalendar.py`, `uibattlepass.py`, `uidragonsoul.py`, `uiguild.py`,
`uisafebox.py`, `uisidekickinventory.py`, `sidekickcollision.py`, `uitooltip.py`.

Nowe:
- `uiwheel.py` – Koło Fortuny (F12),
- `uinewpet.py`, `uiscript/mt2009newpet.py`, `uiscript/mt2009newpetname.py` – okno
  nowego systemu petów (GUI 1:1 z modu) i okno zmiany imienia peta,
- `uiguildduty.py` – obowiązki gildii,
- `uigoblin.py`, `uiscript/goblinwindow.py`, `uiscript/goblinrankingwindow.py`,
  `uiscript/goblinrewardlistwindow.py` – Poszukiwanie skarbów,
- grafiki `mt2009_ui/sidebar/*` (24), `mt2009_ui/wheel/*` (10),
  `mt2009_ui/calendar/{board,goblin_event,halloween_event,npc_search}.tga`,
  `mt2009_ui/goblin/**` (51), `mt2009_ui/newpet/**` (42: tło, przyciski, inkubator,
  `seal/557xx.tga`, `skill/1–22.tga`).

`localeinfo.py` ma też nazwy lochów Razadora i Nemere na minimapie.
Każdy plik `.py` kompiluje się w Pythonie 2.7, a pyflakes (<2.2) nie zgłasza
żadnej nowej niezdefiniowanej nazwy względem 2.0.27. Zostają tylko nazwy
wstrzykiwane przez klienta (`SCREEN_WIDTH`/`SCREEN_HEIGHT` w `uiscript`,
nazwy z `locale_game.txt`).

## gamedata (`gamedata/gamedata/`)

Kolejność: c27 → pety → Ochao → lochy → goblin → bilet Koła Fortuny.
- `item_proto` – 6027 → 6087 wierszy (+60): pety 55001–55411 (53 wiersze, w tym
  55009 „Skrzynia Ksiąg Peta”), 30760–30762 (klucze Nemere), 70617 „Bilet Skarbów”,
  70618 „Klucz Goblina”, 70619 „Szkatułka z Kluczami Goblina” (typ 3/10, stos 200,
  antiflag 221312, flag 8196, 70617 od 70 poz., jak w `world.item_proto`),
  80030 „Bilet Koła Fortuny” (kopia 80017: typ 18, stos 200, antiflag 384, flag 8196,
  value0 0).
- `mob_proto` – 1438 → 1454 (+16): Ochao 6301–6305, 6311, 6390, 6400, 20415, 20426;
  lochy 8058, 20397–20399 (oraz nowe nazwy i poziomy potworów 6001–6191);
  20856 „Goblin Skarbów”, 20857 „Wielka Skrzynia Skarbów” (dane z `world.mob_proto`).
- `item_list.txt` – +60 linii (pety, 30760–30762, `7061x ETC icon/item/7061x.tga`,
  `80030 ETC icon/item/dragonticket.tga`).
- `npclist.txt` – Ochao: 6311, 6390, 6400, 20426 (20856/20857 były już w c27).
  Lochy Razadora i Nemere: modele zastępcze z `dungeons_client/tools/patch_npclist.py`
  zostały cofnięte, bo prawdziwe modele są teraz w paczkach `gf_razador`/`gf_nemere`.
  31 linii ma znowu oficjalne nazwy (jak w npclist Gameforge): 6001–6005 `fire_ghost1`,
  `fire_tiger_boss1`, `fire_man1`, `fire_knight1`, `fire_king1`; 6006–6009 `firegolem_soldier`,
  `firegolem_magician`, `firegolem_general`, `firegolem_boss`; 6051 `firegolem_boss`;
  6091 `yamachun_boss`; 6101–6105 `ice_snow_monster1`, `ice_snow_insect1`, `ice_snow_man1`,
  `ice_snow_giant_man1`, `ice_snow_golem1`; 6106–6109 `icegolem_soldier`, `icegolem_magician`,
  `icegolem_general`, `icegolem_boss`; 6151 `icegolem_boss`; 6191 `hanma_boss`;
  8057 `metinstone_12`; 8058 `metinstone_13`; 20385 `flame_npc`; 20386 `seal_stone`;
  20387 `bridge_block_chain`; 20388 `flame_door_npc`; 20397 `ICE_lionstone`; 20398 `ice_keybox`;
  20399 `ice_stonepillar`. Aliasy (`0 fire_man1 fire_man`, `0 flame_npc flame_dungeon_npc` itd.)
  już były w pliku. Robi to `tools/gf28/build_gf.py` (idempotentnie, na aktualnym npclist).
- `atlasinfo.txt` – `metin2_map_Mt_Th_dungeon_01 844800 1408000 3 3` oraz
  `metin2_map_treasure_hunt 512000 1203200 3 3` (bez nakładania się z innymi mapami).

## locale (`locale/locale/pl/itemdesc.txt`)

Dodane 60 opisów: pety, 30760–30762, 70617–70619, 80030 (CP1250, CRLF).

## icon (`icon/icon/item/`)

Dodane `70617.tga`, `70618.tga`, `70619.tga`. Bilet Koła Fortuny używa istniejącej
ikony `icon/item/dragonticket.tga`.

## maps (`maps/maps/`)

- `metin2_map_treasure_hunt/` – Wyspa Skarbów: `setting.txt`, `mapproperty.txt`,
  9 sektorów, plus `metin2_map_treasure_hunt.msenv`.
- `metin2_map_mt_th_dungeon_01/` – Świątynia Ochao.

## Nowe paczki (`Index`: `*` + `newpet`, `ochao`, `goblin`, `gf_razador`, `gf_nemere`, `gf_misc` na końcu)

- `newpet/` – modele petów (`d:/ymir work/npc_pet/*`, 9 folderów) i ikony
  `icon/item/55xxx.tga`, 176 plików (paczka zbudowana przez agenta petów).
- `ochao/` – modele i tekstury świątyni, potworów i NPC, tekstury terenu
  `terrainmaps/mtthunder`, `textureset/metin2_mtthunder_dungeon.txt` i dźwięki (181 plików).
  Bez `optional_overrides/`.
- `goblin/` – 92 pliki: `d:/ymir work/npc2/treasure_hunt_goblin/*`,
  `d:/ymir work/npc2/treasure_hunt_box/*`, `d:/ymir work/zone/treasure_hunt/*`,
  `d:/ymir work/environment/metin2_map_treasure_hunt.msenv`,
  `d:/ymir work/ui/atlas/metin2_map_treasure_hunt/atlas.sub`,
  `d:/ymir work/ui/atlas_resize/...`, `d:/ymir work/ui/metin2_map_treasure_hunt_atlas.dds`,
  `d:/ymir work/ui/treasure_hunt_01.dds`, `textureset/metin2_map_treasure_hunt.txt`.

**Textureset Wyspy Skarbów:** zastępczy textureset z tekstur mtthunder (wcześniejsza wersja
2.0.28) jest zastąpiony oryginalnym z klienta GF, razem z teksturami (patrz „Zasoby z klienta Gameforge”).

## property (`property/property/`) – paczka `property`

`treasure_hunt/*.prb` (33 obiekty Wyspy Skarbów) oraz `mt_thunder_dungeon/*.prd`
(15) i `b/eff/waterwheel_small.pre` (Ochao), razem 49 plików. Exe wczytuje obiekty
map tylko z całej paczki `pack/property` (`CPropertyManager::Initialize("pack/property")`),
więc pliki są dołożone do paczki `property` z klienta właściciela: 1337 → 1386 wpisów,
stare wpisy bez zmian (`tools/buildprop.py`). Syserr z testu właściciela zawierał
890 błędów `CArea::LoadObject Property(<crc>) Load ERROR` dla 40 różnych CRC.
Wszystkie 40 to nasze pliki (25 z Wyspy Skarbów, 15 z Ochao). Bez nich Świątynia
Ochao była czarną pustką, bo cała świątynia to obiekty.
Efekt `waterwheel_small.pre` wskazuje na `d:/ymir work/effect/etc/fall/waterwheel_small.mse`.
Ten plik jest teraz w paczce `ochao` (z klienta GF). Doszedł też `flame_dungeon/horn01_2.prb`
(obiekt lochu Razadora), więc paczka ma 1387 wpisów.

## Zasoby z klienta Gameforge (Gameforge_26.1.11, import 2026-09-28)

Źródło: rozpakowany oficjalny klient (`/opt/metin2/cache/gf/Gameforge_26.1.11/_client`,
zwykłe foldery: `d_/ymir work`, `icon`, `sound`, `property`, `textureset`, foldery map).
215 plików w `_unnamed/M*/00000000.mcsp` (3,8 MB) to zaszyfrowane bloki bez nazw
(nagłówek `MCSP`, szyfr i kompresja nowego klienta GF, klucza nie ma). Nie da się ich użyć.
Narzędzia: `tools/gf28/` (kopie z `/opt/metin2/cache/tcm/gf28`): `plan.py` szuka
zależności (msm → gr2/dds/efekty, motlist → msa → gr2/mse, mse → tekstury/mde,
dźwięki `sound/<ścieżka>.mss` → wav, obiekty map przez CRC z `areadata.txt` → pliki
`property` → modele/efekty, msenv → skybox), `gen.py` robi pliki przerobione,
`build_gf.py` pakuje, `verify_all.py` czyta z powrotem każdy wpis każdej paczki,
`rebuild.sh` powtarza całość na aktualnym `c28/pack` i robi zipy (`make_zips.py`).
Pliki, które są już w naszych paczkach albo w paczkach właściciela, których listy mamy
(`pc`, `pc2`, `season2`), nie są dokładane. Duplikatów nazw między naszymi paczkami: 0.

**Zgodność formatów.** GR2: 360 plików w formacie Granny v6 i 169 w v7. v6 czyta każdy
granny2.dll. Klient najpewniej czyta też v7: ma już wierzchowce GF z lat 2023–2026
(`npc_mount/summer_2023_hoverboard`, `summer_2026_drakkar`, syserr zgłasza przy nich tylko brak
`wait1/wait2.msa`) i kostiumy z 2026 w `pc`/`pc2`, a w GF to wszystko jest v7.
Wcześniejsze `goblin` i `newpet` też są w v7. Jeśli jakiś model z
v7 byłby niewidoczny, to pierwszy trop. DDS: tylko DXT1/DXT3/DXT5
i nieskompresowane RGB, bez BC7/DX10. Tokeny w .mse/.msa/.msm/.mss są w exe
(`sourceskin%d`, `sounddata%02d`). Wyjątki: `enablefrustum` (mse) i `mainsphereradius`
(msm) exe pomija. Za to `foglevel` w .msenv nowego GF exe 2.0.25 nie zna (czyta tylko
`Enable/NearDistance/FarDistance`), więc 4 pliki msenv są przerobione.
.mde: ten sam format `EffectData`.

- **Ochao (paczka `ochao`, +397 plików, +8,7 MB).** Pełne foldery potworów
  `monster2/lemures_{soldier,soldier2,magic,officer,general,boss,boss2}` (gr2, animacje,
  motlist, tekstury). Wcześniej były tylko skórki `_2`, a klient bazowy nie ma modeli
  lemurów, więc potworów nie było widać. Do tego `trent_officer`, `npc/warp`,
  `redguild_guard_m` (brakujące pliki), dźwięki (`sound/monster2/lemures_*`, wspólne wav),
  efekty map: `effect/background/fire_general_obj_campfire.mse` (192 ogniska w świątyni),
  `torch1.mse`, `effect/etc/fall/waterwheel_small.mse` (+.mde), efekty z animacji,
  `environment/dark.msenv` (przerobiony: mgła 1000–20000, czarna) i `sunflare.dds`,
  atlas `ui/atlas/metin2_map_mt_th_dungeon_01/atlas.sub` + `ui/atlas_resize/..._atlas.dds`.
  3 pliki tekstowe zamienione na oficjalne: `npc/redguild_guard_m/motlist.txt` (+RUN),
  `trent_officer/normal_attack{,1}.msa` (`EnableHitProcess 1`).
  npclist bez zmian, bo foldery są takie jak u GF (`lemures_*_2` → `lemures_*`).
- **Razador (nowa paczka `gf_razador`, 688 plików).** Modele: `monster2/fire_ghost`,
  `fire_tiger_boss`, `fire_man`, `fire_knight`, `fire_king` (z wariantami `*1.msm` lochu),
  `firegolem_{soldier,magician,general,boss}`, `yamachun_boss`, `monster/metinstone_02`
  (`metinstone_12.msm`), `npc2/flame_dungeon_npc` (`flame_npc.msm`), `flame_bridge_block_chain`,
  `flame_door_npc`, ich dźwięki i efekty, tekstury terenu (`terrainmaps/n/flame area`),
  `textureset/metin2_map_n_flame_dungeon_01.txt`, `environment/metin2_map_n_flame_dungeon_01.msenv`
  (przerobiony), atlas. Poprawki: `flame_bridge_block_chain/front_dead.msa` wskazywał na ścieżkę
  deweloperską `D:/scm/metin2/...`. GF nie ma `effect/monster2/yellowred1_great.mse`
  (poświata Razadora), więc jest kopią `yellowred1.mse`.
- **Nemere (nowa paczka `gf_nemere`, 448 plików).** `monster/ice_snow_{monster,insect,man,giant_man,golem}`
  (warianty `*1.msm`), `monster2/icegolem_{soldier,magician,general,boss}`, `hanma_boss`,
  `npc2/ice_lionstone`, `ice_keybox`, `ice_stonepillar`, dźwięki, efekty, tekstury
  (`zone/dungeon/snow_dungeon`), textureset, msenv (przerobiony). Części modeli `icegolem_*`
  (wspólne animacje) są w `gf_razador`, dlatego obie paczki trzeba mieć razem.
- **Mapy (paczka `maps`, +217).** `maps/metin2_map_n_flame_dungeon_01/` (3×3) i
  `maps/metin2_map_n_snow_dungeon_01/` (4×3) z oficjalnego klienta, razem z `attr.atr`,
  `water.wtr` i minimapami, plus kopie msenv w folderach map. Świątynia Ochao: 3 pliki
  `areadata.txt` podmienione na oficjalne (różnica 10 jednostek). Wyspa Skarbów:
  przerobiony msenv. Obiekty obu lochów były już w paczce `property` właściciela, brakował
  jeden: `property/flame_dungeon/horn01_2.prb` (dołożony, 1386 → 1387).
- **Wyspa Skarbów (paczka `goblin`, +55, 2 podmienione).** Prawdziwy
  `textureset/metin2_map_treasure_hunt.txt` z GF (17 tekstur) zamiast zastępczego z mtthunder
  oraz jego tekstury (`terrainmaps/treasure_hunt/*`, `b/beach`, `b/field`, `b/stone`, `a/beach`,
  `capedragonhead`, `elemental_01`, `guild_battle`). Do tego skybox `environment/skybox/capedragonhead_*`
  i przerobiony msenv. Efektów `effect/monster2/goblin_*` nie ma w GF (goblin skarbów
  nie ma efektów w msa).
- **Reszta (nowa paczka `gf_misc`, 245 plików).** Modele z syserr: `monster2/gnoll_general` (3005),
  `cyclops_officer` (3104), `triton_soldier` (3401), `redthief_bow` (3501), `redthief2_soldier2` (3552)
  (+`redthief_soldier2`, z którego korzysta) z dźwiękami i efektami. `effect/pet/pet_pve_fire_01.mse`
  (dla peta `pve_dragon_young` z `newpet`). Znaczek Top1: GF nie ma `effect/gm/top1.mse`, więc jest
  nim korona lidera z Battle Royale (`effect/battleroyale/crown01.mse`) nad głową
  (`effect/gm/top1.mse` + `top1.dds`, wysokość 240 jak w komentarzu w `game.py`).
  `npc_mount/summer_2023_hoverboard` i `summer_2026_drakkar`: `wait1.msa`/`wait2.msa`
  (motlist GF je wymienia z szansą 0, ale nikt ich nie ma) to kopie `wait.msa`.
- **icon:** `icon/item/50260.tga` = kopia `50255.tga`, bo tej używa `item_list` dla 50260
  (Cor Draconis, surowe). Syserr pytał o `50260.tga`.
- **Pety (`newpet`) bez zmian.** Modele z modu są w v7, a GF ma te same pety w v6.
  Wszystkie odwołania modu się rozwiązują (poza `pet_pve_fire_01.mse`, teraz w `gf_misc`),
  więc zostają.

Sprawdzone: każdy wpis każdej paczki odczytany z powrotem (crc nazwy i danych,
dekompresja), porównany z plikiem źródłowym. Każda rasa z listy
(6001–6191, 8057/8058, 20385–20399, Ochao, goblin, 3005/3104/3401/3501/3552) rozwiązuje
się tak jak w exe (`d:/ymir work/{guild,npc,npc2,npc_pet,npc_mount,monster,monster2}/<folder>/<nazwa>.msm`,
alias `0 nazwa folder`) do pliku w naszych paczkach. Odwołania msm, motlist, msa i efektów
też się rozwiązują. Wyjątki są w „Czego brakuje”. Każdy obiekt z `areadata.txt`
czterech map ma swój plik w `property`, a każdy plik tego obiektu jest w paczkach
(poza dwoma obiektami gildii w lochu Nemere, patrz niżej).

## Czego brakuje

- Pliki, których nie ma w rozpakowanym kliencie GF (pewnie siedzą w 215 zaszyfrowanych
  `_unnamed`): `effect/monster2/impact7.mde`, `impact9.mde`, `impact10_red.mde`,
  `mash_spell1.mde` (siatki kilku efektów uderzeń, cząsteczki działają), `effect/pet/pet_fenfire_01.mse`,
  `pet_fenfire_02.mse`, `effect/jin_han/work/efect_duel_jin_han_sender.mse`,
  `ui/atlas_resize/metin2_map_n_snow_dungeon_01_atlas.dds` (duża mapa Nemere),
  `ui/metin2_map_n_snow_dungeon_01.dds`, `guild/building/generaltomb.gr2`.
  Mapa Nemere odwołuje się też do `d:/maiinbase.gr2`, a to błąd w danych GF.
- `npc2/flame_dungeon_npc`, `ice_lionstone`, `ice_keybox` nie mają `motlist.txt`, tak samo u GF
  (to posągi). Exe 2.0.25 nie traktuje braku motlist jako błędu (sprawdzone w kodzie
  `CRaceManager`: wynik wczytania motlist jest pomijany).
- Brak `locale/pl/map/metin2_map_treasure_hunt_point.txt` i `..._n_snow_dungeon_01_point.txt`
  (GF też ich nie ma): klient tylko zapisze ostrzeżenie w syserr.
- 20386 `seal_stone` używa modelu z klienta bazowego (Wieża Demonów).

## Instalacja

Rozpakować do folderu klienta, w którym jest już 2.0.27 test (root) oraz
gamedata/locale z 2.0.26. Rozpakować wszystkie `klient-test-2.0.28-*.zip`, nadpisując
pliki: `root`, `gamedata`, `locale`, `icon`, `maps`, `property`, `newpet`, `ochao`, `goblin`,
`gf_razador`, `gf_nemere`, `gf_misc`. `pack/Index` (z `gf_razador`, `gf_nemere`, `gf_misc`
na końcu) jest w zipach `newpet`, `ochao`, `goblin` i `gf_*` i wszędzie jest taki sam.
Inny wariant: jeden zip `klient-test-2.0.28.zip` z całą aktualizacją
(kopia do pobrania przez SFTP: `/opt/metin2/dist/klient/klient-test-2.0.28-pelny.zip`).
Exe bez zmian (2.0.25).
