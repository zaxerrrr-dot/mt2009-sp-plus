# relikty – Bonus Reliktu (Relikt Duszy, dusze, okno reliktu)

Znacznik: `MT2009_PLUS_RELIC_V1`. Prośba właściciela z 29.10.2026: *„Add relics according to the wiki”* – pl-wiki
„Bonus Reliktu” i strony, do których prowadzi („Relikt Duszy”, „Odłamek Reliktu”, „Dusza Miecza / Ochrony / Ozdoby /
Światła”, „Pakiet Dusz”, misje „Uratuj Handlarza Bronią / Handlarza Zbrojami / Alchemika / Uriela / Chaegiraba” i ich
wersje powtarzalne). Paczka bazowa: **„Official Passive Attr System” – Best Studio** (github.com/ybeststudio,
discord.gg/NXmc6JrwYr) – z niej numery przedmiotów (= klienta GF 26.1.11), okno `passive_attr` i dwa okienka reliktu;
zasady i bonusy według wiki, kod nasz (paczkowe `ApplyPoint` przy każdym procu nie miało w naszym silniku sensu).

## Bez nowego pakietu, typu przedmiotu i punktu

- **Pakiety**: brak nowych nagłówków – klient pisze `/relikt …`, serwer odpowiada `relikt_state …` / `relikt_open`
  (jak `addeq`, `ekwipunek`). Paczkowe `HEADER_CG_PASSIVE_ATTR = 184` / `HEADER_GC_PASSIVE_ATTR = 188` nie są użyte.
- **Exe**: bez zmian (żadnego `ENABLE_PASSIVE_ATTR`, `ITEM_PASSIVE`, `WEAR_PASSIVE`, `POINT_MAX_NUM` zostaje 253).
- **Relikt nie jest zakładany**: leży w ukrytym polu postaci – okienko I / II = `MT2009_RELIC_SLOT_START + strona`
  (`MT2009_ADDEQ_SLOT_END` = 436, czyli 436 i 437 – za czterema blokami stron `addeq` V2 308–435; okno `INVENTORY`, w bazie zwykłe wiersze `player.item` z `pos` 436/437), nigdy
  nie idzie do klienta i żaden pakiet klienta go nie dotyka (jak magazyn `addeq`). Jego atrybuty 0-3 to bonusy reliktu
  (typ = id bonusu 1-16, wartość = x z wiki) – czyta je tylko `playerbot_relikty.cpp`, nigdy jako punkty.
- Efekty używają istniejących punktów przez afekty 761-776 (`760 + id`): `POINT_SUNGMA_STR/HP/MOVE/IMMUNE` (184-187),
  `POINT_ATTBONUS_STONE`, `POINT_DEF_BONUS` (94), `POINT_ATT_BONUS` (93), `POINT_MOV_SPEED` (19).

## Przedmioty (`relikty.sql`, `tools/relikty/gen_relikty.py`)

| vnum | nazwa | typ | uwagi |
|---|---|---|---|
| 30255 / 30256 / 30257 / 30258 | Dusza Miecza / Ochrony / Ozdoby / Światła | `ITEM_MATERIAL`, stos 200 | handel tak; ItemShop V3 39 SM |
| 30263 | Pakiet Dusz | `ITEM_GIFTBOX` | po jednej z 4 dusz (`special_item_group.relikty.txt`, Pct); V3 100 SM – ilość nie podana na wiki |
| 30272-30276 | Relikt Duszy Wojownika / Ninja / Sura / Szamana / Likana | `ITEM_QUEST`, 1 | klasa = vnum − 30272 (`JOB_*`) |
| 30280-30284 | Odłamek Reliktu (Odł. Reliktu Wojownika, …) | `ITEM_QUEST`, stos 200 | tylko magazyn (bez handlu / sklepu / upuszczenia) |

Sockety reliktu: 0 – pozostały czas (s), 1 – czas reliktu (losowany raz przy pierwszym umieszczeniu: 1-12 h), 2 – flagi
(1 aktywny, 2 był aktywowany).

## Zasady (wiki)

- Dwa okienka (I / II), działa relikt **wybranego** okienka; czas płynie tylko, gdy jest aktywny (tik co 1 s, zapis
  socketu co 30 s, przy teleporcie i wylogowaniu).
- **Dodaj**: po jednej Duszy Miecza, Ochrony, Ozdoby i Światła (torba + dodatkowy ekwipunek) → nowy losowy bonus spośród
  16, którego relikt jeszcze nie ma; poziom losowany wagami 100, 70, 49, … (niższe częstsze); max 4, bez zmiany, nie
  przy aktywnym reliktcie. **Doładuj**: te same 4 dusze → pełny czas. **Aktywuj / dezaktywuj** – tylko wybrane okienko.
- **Wyjmij**: relikt nigdy nieaktywowany wraca do torby; po pierwszej aktywacji wyjęcie go **niszczy** (okno pyta).
- Relikt tylko swojej klasy; prawy klik na relikt w torbie wkłada go do wybranego (albo drugiego wolnego) okienka.

| id | bonus | x (wiki) | wyzwalacz | odnowienie |
|---|---|---|---|---|
| 1-4 | Wola SungMa WIT / SIŁA / ODP / INT +15 na x s | 1-8, 10 s | gdy zostaniesz zaatakowany | 120 s |
| 5 | x% na 30 s automatycznego zbierania (własny drop wokół, co 2 s `PickupNearbyItems`) | 1-7, 9, 15 % | gdy zaatakowany | 300 s |
| 6 / 7 | eliksir słońca / księżyca – brakujące PŻ / PE od razu | 100 % | w walce, PŻ / PE niepełne | 300 s |
| 8 | x%: reset czasu odnowienia wszystkich umiejętności (klient: pakiet 73 jak `bonusy67`) | 1-7, 9, 15 % | użycie umiejętności | 120 s |
| 9 / 10 | +x% obrażeń przeciw Metinom / +x% obrony na 5 s | 1-10 % | trafienie Kamienia Metin | 120 s |
| 11 | +x% obrażeń na 10 s | 1-5 % | dosiadanie wierzchowca | 120 s |
| 12 | +x prędkości ruchu na 10 s | 1-8, 10 | zsiadanie | 120 s |
| 13 | +x% szansy na drop z bossa | 1-8, 10 % | każde zabicie bossa (`GetDropPct`) | – |
| 14 | x%: śmierć anulowana, 30% PŻ | 5, 7, 11, 15, 20, 30, 50 % | śmierć | 600 s |
| 15 | x%: wszystkie potwory wokół atakują (Peleryna Męstwa – `AggregateMonster`) | 1-10 % | atak na potwora | 180 s |
| 16 | x%: 20 s deptania – trafienie z wierzchowca ogłusza potwora na 2 s (nie bossa / Metina / odpornego; graczy nie) | 1-10 % | atak z wierzchowca | 120 s |

Odnowienie liczone od każdego losowania (wiki: „co 120 sekund mamy 8% szans”). Interpretacje własne (wiki nie mówi
dokładnie): eliksir = jednorazowe uzupełnienie, deptanie = ogłuszenie potworów, zbieranie = własny drop w zasięgu.

## Źródła (nasz świat)

Misje w Dongan (mapa 373, od poz. 120; `quest/relikt_*.quest`, generowane):
`relikt_bron` (Handlarz Bronią 9001) → `relikt_zbroja` (Handlarz Zbrojami 9002) → `relikt_alchemik` (Alchemik 20001) →
`relikt_uriel` (Uriel 20011) → `relikt_chaegirab` (Chaegirab 20810). Pierwsza misja każdego: Metiny Świadomość (8067,
Dongan) aż do Lekarstwa (35% za Metin; wiki: „Metin Świadomość (misja)” – u nas zwykły Metin mapy), u Chaegiraba też 10
popiołów (1/6 z potworów Dongan) → dusza / Odłamek Reliktu klasy (100%). Potem co 24 h: 10 fragmentów duszy (1/8 z
potworów Yohary), wynik po dobie, 60% (wiki: „może się nie udać”; spiral czasu brak); u Chaegiraba 10 popiołów → 60%
odłamka. `relikt_uszlachetnianie`: Chaegirab zawsze zamienia odłamek klasy w Relikt Duszy (wiki: „okienko
uszlachetnienia”). ItemShop V3: dusze 39 SM, Pakiet Dusz 100 SM (`tools/itemshop3/global/decisions.py` wiersze 107-111).

## Boty

`playerbot_manager.cpp` woła `Mt2009RelicBotTick` (własny zegar 5 min) obok pomocy sklepowych: bot od poz. 120 na mapie
Yohary „robi” dzienne misje (pierwszy odłamek i dusze 100%, potem 60% dziennie), robi relikt u Chaegiraba, wkłada go na
okienko I, dodaje bonusy, aktywuje przy 4 bonusach i doładowuje. Brakującą duszę kupuje w ItemShop V3 – cel `relic_soul`
(`playerbot_shop_aids.h`, 1 sztuka, nigdy pilny). Flaga eventu `m2_bot_relic_off` wyłącza całość.
Dusze, Pakiet Dusz, relikty i odłamki nigdy nie są złomem bota ani towarem jego straganu
(`Mt2009RelicIsKeptVnum`: `IsPlayerBotJunkItem` w `playerbot_economy.h`, `ScorePlayerBotShopStockRules` w `playerbot_town.h`).

## Gdzie co jest

| Część | Miejsce |
|---|---|
| Logika serwera | `linux-port/overlays/playerbot/src/game/src/playerbot_relikty.cpp`, tabela `playerbot_relikty_table.h` (generowana) |
| Haki silnika | `edits.json` (17 zmian: `char.h`, `char_item.cpp`, `char.cpp`, `item.cpp`, `input_db.cpp` (drugi wiersz na zajętym polu reliktu → torba), `char_battle.cpp`, `char_skill.cpp`, `item_manager.cpp`, `cmd.cpp`); `gen_edits.py` je generuje i sprawdza; `apply_relikty.py` (Linux) / `Apply-ReliktyPatch.ps1` (Windows, ostatni krok `tools/port/Apply-MT2009PlusEngine.ps1`) |
| Baza | `linux-port/docker/mariadb/playerbot/relikty.sql` (krok w `apply.sh` po `yohara_biolog.sql`), `itemshop3_schema.sql` (linie V3) |
| Gra | `game/Dockerfile`: lista questów (6 nowych) i `special_item_group.relikty.txt` |
| Klient (root) | `uirelikt.py`, `uiscript/reliktwindow.py`, `relikt_data.py` (generowany), haki: `game.py` (hello, `relikt_state`, `relikt_open`, klawisz `relic`), `uitooltip.py` (podpowiedź reliktu), `keybind.py`, `uisystem.py` + `uiscript/systemdialog.py` (przycisk w menu Esc); ikony `root/icon/item/302xx.tga` |
| Dane klienta | `client-patches/client-2.0.30/tools/relikty` – `gamedata`/`dbdata` (15 przedmiotów) i paczka `relikty` (obrazy okna GF: `passive_01.dds`, `passive_attr/*.sub`) |

## Komendy

	/relikt hello | page <0|1> | put <pole> [<okienko>] | take|add|charge|activate <okienko>

Log: `RELIC: <postać> (<pid>) put / activated / bonus <id> (<x>) added / destroyed …`, `RELIC_BOT: …`.

## Kolejność / wdrożenie

Ostatni (po `superstone`, `questren`, `dmgprint`, `autohuntreach`) – kotwice na liniach `addeq` i `bonusy67`. `yohara-deploy.sh`: dopisać `relikty` na końcu listy
łatek. Komórki 436-437 leżą za magazynem `addeq` (`MT2009_ADDEQ_SLOT_END`): zmiana `INVENTORY_MAX_NUM` / pasa przesuwa
oba magazyny – zapisane relikty trzeba by wtedy przenumerować (jak przedmioty `addeq`).
