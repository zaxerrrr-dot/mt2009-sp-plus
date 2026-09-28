# Klient 2.0.28: pasek boczny, Koło Fortuny, nowe pety, Poszukiwanie skarbów (goblin), Świątynia Ochao, lochy Razadora i Nemere

Względem klienta 2.0.27 (`client-patches/client-2.0.27`). Paczki są
kumulatywne: gotowe pliki są w `/opt/metin2/cache/tcm/c28/pack` (`root`,
`gamedata`, `locale`, `icon`, `maps`, nowe `newpet`, `ochao`, `goblin` i `Index`).
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
  Lochy Razadora i Nemere: skrypt `dungeons_client/tools/patch_npclist.py` (idempotentny)
  przepina 31 linii na modele, które klient już ma. Uruchomiłem go na naszym `npclist.txt`.
  Syserr właściciela: `RACE[6003] season2/monster/fire_man/shape.msm ERROR`, bo aliasy `fire_man1` i
  podobne nie są rozwiązywane. Przypisania:
  6001–6005 → `fire_ghost`, `fire_tiger_boss`, `fire_man`, `fire_knight`, `fire_king`;
  6006–6009, 6051 → `fire_knight`/`fire_man`/`fire_king`; 6091 → `fire_dragon`;
  6101–6109 → `ice_snow_*` / `ice_snow_witch`; 6151 → `ice_snow_witch`; 6191 → `blue_dragon`;
  8057, 8058, 20399 → `metinstone_02`; 20386, 20398 → `seal_stone`;
  20385/20387/20388/20397 → `#season1/npc/{firestone,steelstone,keyholestone,waterstone}/`
  (pełna ścieżka – exe obsługuje prefiks `#`).
  To modele zastępcze, dopóki nie dojdą prawdziwe.
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

## Nowe paczki (`Index`: `*` + `newpet`, `*` + `ochao`, `*` + `goblin` na końcu)

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

**Textureset Wyspy Skarbów:** w archiwum brakuje `textureset/metin2_map_treasure_hunt.txt`.
Sektory używają tekstur 1–13, a jedyny textureset, który na pewno jest w paczkach
(`metin2_mtthunder_dungeon.txt` z paczki `ochao`), ma ich tylko 5. Dlatego
`setting.txt` zostaje bez zmian. Brakujący plik zbudowałem z 11 tekstur
`d:/ymir work/terrainmaps/mtthunder/*.dds` z paczki `ochao` (dobranych po
kolorach atlasu: piasek, trawa, skała, dno morza). Wyspa będzie mieć brązowe
tony Grzmiących Gór, ale nie będzie czarnych plam.

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
Tego pliku nie ma ani w archiwum Ochao, ani w naszych paczkach, więc musi pochodzić z klienta bazowego.
Jeśli go tam nie ma, zabraknie tylko jednego efektu wodnego.

## Czego brakuje

- Lochy Razadora i Nemere: foldery map `metin2_map_n_flame_dungeon_01`,
  `metin2_map_n_snow_dungeon_01`, ich textureset i msenv oraz modele wyłącznie
  z lochów (`firegolem_*`, `yamachun_boss`, `icegolem_*`, `hanma_boss`,
  `flame_dungeon_npc`, `seal_stone`, `flame_bridge_block_chain`, `flame_door_npc`,
  `ICE_lionstone`, `ice_keybox`, `ice_stonepillar`). Nie ma ich w archiwum ani na VPS.
  Do czasu ich dodania `npclist.txt` wskazuje na modele zastępcze (patrz gamedata).
  Dopóki nie ma map, strażnicy lochów (20394/20395) nie mogą wpuszczać graczy.
- Brak `locale/pl/map/metin2_map_treasure_hunt_point.txt`: klient tylko zapisze
  ostrzeżenie w syserr.

## Instalacja

Rozpakować do folderu klienta, w którym jest już 2.0.27 test (root) oraz
gamedata/locale z 2.0.26. Rozpakować wszystkie `klient-test-2.0.28-*.zip`, nadpisując
pliki: `root`, `gamedata`, `locale`, `icon`, `maps`, `property`, `newpet`, `ochao`, `goblin`.
`pack/Index` jest w zipach `newpet`, `ochao` i `goblin` i jest w nich taki sam.
Inny wariant: jeden zip `klient-test-2.0.28.zip` z całą aktualizacją.
Exe bez zmian (2.0.25).
