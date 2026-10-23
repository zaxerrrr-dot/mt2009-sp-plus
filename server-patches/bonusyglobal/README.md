# Bonusy i żywioły: tryb mt2009 albo global – `MT2009_PLUS_GLOBAL_BONUS_V1`

Właściciel, 14.10.2026: „zmiany bonusów i żywiołów dokładnie jak w wydaniu Tieru (2.2.31, „Bonusy jak na serwerze
globalnym”), ale z opcją w .env: albo bonusy MT2009 PLUS (jak dotąd), albo bonusy serwera globalnego”, a w trybie
global żywioły na wszystkich potworach. Jedna zmienna, **`M2_BONUS_MODE`** (`linux-port/docker/.env.example`):

| | `mt2009` (domyślnie) | `global` |
|---|---|---|
| Maks. PŻ | do 1500 | do 2000 (szansa 35, 500/500/1000/1500/2000) |
| Maks. PE | do 250 (bransoleta, buty, naszyjnik) | do 80 na bransolecie i butach, do 200 na naszyjniku |
| Regeneracja PŻ / PE | do 12% | do 30% (4/8/12/20/30) |
| Odporność na ogień / błyskawice / wiatr | tylko talizman (5–25%) | też zbroja, bransoleta, hełm: 2/4/6/10/15%; talizman dalej 5–25% |
| Szansa na bonus DOŚ | – | buty, naszyjnik, tarcza: do 20% |
| Szansa na podwójną ilość przedmiotów | – | bransoleta, kolczyki: do 20%, podnosi szansę dropu (20% = o 20% częściej) |
| Wytrzymałość, reg. wytrzymałości, czas trwania umiejętności, odbicie strzał, stałe PD | losują się | nie losują się na broni, zbroi i biżuterii (kostiumy i talizman bez zmian) |
| Szybkość ruchu | buty, kolczyki | buty, kolczyki (bez zmian) |
| Żywioły potworów | zasady właściciela z 7.10 (`zywioly_moby.sql` + pliki Yohary) | to samo **plus** żywioł każdego potwora z oryginalnych danych |
| Odporność na żywioł gracza wobec potwora tego żywiołu | odejmuje cały swój procent (strop 80%) – Digi Rasta | pełny procent (1% = 1% mniej obrażeń, strop 80%) – decyzja właściciela 23.10.2026 (wcześniej 30%) |
| Alchemia (Smocze Kamienie) | nasz balans z 24.09 (`dragon_soul_applys.mt2009plus.txt`) | domyślna tabela (Owsap = paczka = klient GF 26.1.11, bez 2 linii Wilkołaka): `MT2009_PLUS_DS_GLOBAL_TABLE_V1` |

Przedmioty **zachowują wszystkie bonusy**, które mają – w obu kierunkach zmienia się tylko pula losowania
(`player.item` nie jest ruszane). Przełączać można dowolnie często; działa po restarcie (migrator).

## Co zmienił Tieru (2.2.31) i jak to jest u nas

| Tieru | U nas |
|---|---|
| `apply.sh`: migracja `item_attr_global_2231` (jednorazowa, UPDATE po wartościach paczki + INSERT 5 wierszy) | `mariadb/playerbot/bonusy_global.sql` – te same wartości, po nazwie bonusu (`apply` = `POINT_*`, nigdy po numerze); kopia 14 wierszy trybu mt2009 w `world.item_attr_mt2009`, `bonusy_mt2009.sql` oddaje je z powrotem |
| `apply.sh`: `mob_elements_r40250_2231` (bity 11 i 14 na 47 + 63 vnumach z r40250) | `tools/zywioly/gen_zywioly_moby_global.py` → `zywioly_moby_global.sql`: kolumny Att* oficjalnego mob_proto (Owsap = pl-wiki; zawiera całą listę Tieru) dla każdego potwora, wszystkie 6 żywiołów |
| `battle.cpp`: odkomentowane `iAtk -= iAtk * 30 * resist / 10000` w `CalcAttBonus` | nasz `ElementsAttackBonus` (`playerbot_elements.cpp`) już liczy odporność; w trybie global bierze 30% jej wartości (`BonusModeElementResist`) – bez drugiego, podwójnego odejmowania |
| `item_manager.cpp`: `POINT_ITEM_DROP_BONUS` dodany do `item_drop_bonus` | `edits.json` (drop) → `BonusModeItemDropBonus`, tylko w trybie global |
| klient 2.0.45: `ATTR_MAX_VALUES` (maks. wartości świecą na pomarańczowo) | root `localeinfo_point.py`: zestaw mt2009 i global, `SetBonusMode` po komendzie serwera `BonusMode 0/1` |

Szansa na bonus DOŚ (`POINT_EXP_DOUBLE_BONUS`) działa w silniku od zawsze (`char_battle.cpp`) – nic do zmiany, w trybie
mt2009 po prostu się nie losuje. Polskie nazwy wszystkich pięciu bonusów są w `locale_game.txt` klienta (np. „Szansa na
podwójną ilość Przedmiotów: %d%%”) – bez zmian w exe i bez nowych punktów (numeracja POINT/APPLY bez zmian).

Nie przeniesione (u nas własne): launcher, boty, Seon-Pyeong (jest), towarzysz, pasek życia celu.

## Konflikt z naszymi żywiołami (`MT2009_PLUS_ELEMENTS_V1`, Autor: Digi Rasta) – decyzje

1. **Jeden wiersz `item_attr` na bonus.** Odporność na ogień/błyskawice/wiatr ma u nas wiersz talizmanu (5–25%, tylko
   kolumna `pendant`). W trybie global wiersz ma wartości Tieru (2–15%) i kolumny zbroi/bransolety/hełmu, a rdzeń daje
   talizmanowi jego własne 5% na poziom (`BonusModeAttrValue` w `CItem::AddAttr`, `edits.json` attr value) – talizman
   losuje tak samo w obu trybach. Lód/ziemia/mrok – bez zmian (tylko talizman).
2. **Wzór odporności:** mt2009 – nasz (pełny procent, strop 80%); global – Tieru/oryginał (30%).
3. **Żywioły potworów w trybie global:** oficjalny żywioł wygrywa z naszymi regułami (np. Podziemne Lodowe potwory Groty
   1131–1137: lód zamiast błyskawicy mapy; Ezoteryczni Przywoływacze 791–795, Rakszas: wiatr; Piekielny Bastard: mrok –
   18 zmian); potwór bez oficjalnego żywiołu zachowuje nasz (nadpisania bossów właściciela); prawdziwe kopie oficjalnych
   potworów (ta sama nazwa: Cyklopi 9601–9605 itd.) dziedziczą żywioł źródła, przeróbki z Arezzo (mumie, skorpiony,
   małpy z Cyklopów) – nie. **Bez zmian:** Yohara (wszystkie `*_zywioly.sql` i `YOHARA_ELEMENTS*` – już według wiki),
   Świątynia Zodiaku (żywioł piętra w czasie gry), Ruiny Atlantydy (reguła f), Metiny (zasada właściciela) i NPC.
   Tryb mt2009 nie potrzebuje kroku: `zywioly_moby.sql` przy każdym starcie zdejmuje bity z każdego moba spoza swojej
   listy.
4. **Klient** (bez zmian w exe): `mob_proto` klienta ma żywioły trybu mt2009 (krok `yfinal`). Ikona żywiołu celu w trybie
   global bierze żywioł z `root/zywioly_global.py` (generowany razem z SQL), gdy serwer przy logowaniu wyśle
   `BonusMode 1` (quest `zywioly`, `game.py`, `uitarget.py`).


## Alchemia w trybie global – `MT2009_PLUS_DS_GLOBAL_TABLE_V1`

Właściciel, 15.10.2026 (lista poprawek, pkt 5): przy `M2_BONUS_MODE=global` Smocze Kamienie mają **domyślne** bonusy
(Owsap `share/locale/uk/dragon_soul_table.txt` = tabela paczki = klient GF 26.1.11, `shared/common`). Różnią się tylko grupy
`BasicApplys`/`AdditionalApplys` (wagi, ilości bonusów i ulepszanie – wspólne). Przykłady (wartość bazowa; Mityczny,
najwyższy stopień, +6 = ×160%):

| Kamień | mt2009 | global |
|---|---|---|
| Diament | INT 8, Silny przeciwko Milgyo 9 | INT 10, odp. na lód 10, siła lodu 10 (3. bonus od Mitycznego) |
| Rubin | STR 8, Silny przeciwko Diabłom 9; dod.: wartość ataku 200, obrona 150, 10% | STR 10, odp. na ogień 10, siła ognia 10; dod.: 300, 200, 15% |
| Jadeit | PE 500, Zwierzęta 9; dod.: PŻ 2000, kradzież PŻ 6, Maks. PŻ 12% | PE 500, odp. na wiatr, siła wiatru; dod.: PŻ 3000, 10, 20% |
| Szafir | DEX 8, Orki 9; dod.: silny/odporny na klasy 10 | DEX 10, odp. na ziemię, siła ziemi; dod.: 15 |
| Granat | PŻ 1000, Silny przeciwko Ludziom 6 | PŻ 1500, odp. na błyskawice, siła błyskawic |
| Onyks | CON 8, Nieumarli 9; dod.: blok/unik 8, odbicie 6 | CON 10, odp. na mrok, siła mroku; dod.: 10 |
| Ametyst | Potwory 6, Metiny 6; dod.: kryt. 5, przeszywające 5, wartość ataku 100 | Diabły 10, Precyzja 10, Witalność Sung Ma 10; dod.: Siła/Odporność/Inteligencja Sung Ma 10, Metiny 5 |

- `linux-port/docker/game/dragon_soul_applys.global.txt` – grupy domyślne; `game/Dockerfile` robi z nich
  `dragon_soul_table.global.txt` i zostawia tabelę mt2009 jako `dragon_soul_table.mt2009.txt`.
- `edits.json` (`DragonSoul.cpp` load/refresh, `dragon_soul_table.cpp` apply names): rdzeń czyta `M2_BONUS_MODE` ze
  środowiska (flaga zdarzenia przychodzi po wczytaniu tabel) i w trybie global ładuje tabelę global zamiast
  `dragon_soul_table.txt`; siła żywiołów, Sung Ma i Precyzja z tabeli to prawdziwe punkty (Yohara 3.0).
- **Kamienie zachowują swoje bonusy**: atrybuty kamienia są w `player.item` i nikt ich nie przelicza. Ulepszenie siły
  (+1 / spadek) przelicza wartości – z tabeli, do której pasują bonusy kamienia (pozostałe tabele są wczytane), więc
  kamień z trybu mt2009 rośnie dalej ze swoimi bonusami w trybie global i odwrotnie; bonus, którego nie ma żadna tabela,
  zostaje (wcześniej spadał do 0). Nowy kamień, ulepszenie klasy/stopnia i zmiana bonusów Mitycznego – z tabeli bieżącej.
- Strona panelu „Alchemia” edytuje tabelę trybu mt2009; w trybie global jej status mówi, że rdzenie używają tabeli global.
- Klient nie czyta `dragon_soul_table` (opisy z atrybutów przedmiotu; nazwy punktów 178–187 i 197 ma `localeinfo_point.py`).

## Stałe bonusy przedmiotów w trybie global – `MT2009_PLUS_GLOBAL_PROTO_V1`

Właściciel, lista poprawek z 15.10.2026, pkt 19: w trybie global przedmioty mają stałe bonusy (`item_proto`
applytype0..2/applyvalue0..2) jak na serwerze globalnym (Owsap `Server/Server/db/item_proto.txt`), np. Bambusowe
Buty+9 (15029): ruch 15 + odporność na ogień 10 zamiast ruchu 25 + maks. wytrzymałości 800. Tryb mt2009 bez zmian.

- `tools/protoglobal/gen_item_proto_global.py` porównuje każdy vnum obu item_proto (nazwy bonusów → nasze numery
  `POINT_*`). Właściciel 20.10: „tak, wszystko jak global”. Bierze **ten sam przedmiot** (ten sam typ/podtyp, poziom,
  stopień +N; mikstury i pieczone ryby – ten sam czas działania, bonus z value0/value2 globalu), najwyżej 3 bonusy, każdy
  znany silnikowi; `APPLY_RANDOM` (losowy bonus robiony na przedmiocie) i `APPLY_MOUNT` (rasa wierzchowca) to nie stałe
  bonusy – pomijane (wierzchowiec trzyma pustą 1. szczelinę jak dotąd). Wynik: 436 przedmiotów – 280 zbroi/biżuterii,
  110 broni, 15 kamieni duszy (Magii, Witalności, Obrony +0..+4), 17 zwierzaków (żywioły zwierzaków, Precyzja, Sung
  Ma), 7 wierzchowców, 6 mikstur/ryb, 1 unikalny (Buty Wiatru). Nie zmienia: przedmiotów Wilkołaka (szpony, kamienie
  i fryzury Likanów – nie ma u nas Wilkołaka), szarf (absorpcja w value0/gniazdach), przedmiotów, którym global nie
  daje stałego bonusu (efekt gdzie indziej) albo których tam nie ma, naszych przeróbek (inny poziom: Miecz+0, Pogromca
  Niebieskiego Smoka, Tarcza Trzech Władców – w raporcie jako „rework”). Pełna lista różnic z kategorią i werdyktem:
  `--report` (`/opt/metin2/cache/yohara/item-proto-global-diff.tsv`).
- `mariadb/playerbot/item_proto_global.sql` – tabela `world.item_proto_apply_global` (wartości global + strażnik:
  typ, podtyp, poziom). Krok `apply.sh` (po wszystkich krokach, które piszą `item_proto`): global – zapisuje bonusy
  mt2009 w `world.item_proto_apply_mt2009` i wpisuje global; mt2009 – oddaje zapisane (tylko tam, gdzie dalej są
  wartości global) i czyści tabelę. Przełączanie tam i z powrotem daje bajt w bajt tę samą tabelę. Przedmioty graczy
  zmieniają się od razu (stałe bonusy są z proto). Edycja tych bonusów w edytorze bazy panelu w trybie global trafia
  do zapisu trybu mt2009 przy następnym starcie (global ma pierwszeństwo).
- Klient: tooltip czyta `item_proto` klienta (wartości mt2009). `client-patches/client-2.0.30/tools/protoglobal/
  build_protoglobal_pack.py` (ostatni krok przedmiotów, po yfinal) dokłada do paczki `gamedata` dwa małe item_proto
  z rekordami klienta tych przedmiotów (24 zwierzaki/wierzchowce nie mają rekordu w item_proto klienta – bez
  zmian w opisie): `gamedata/item_proto_global` (bonusy global) i `gamedata/item_proto_mt2009` (bez
  zmian). `root/protoglobal.py` po `BonusMode 1` z serwera woła `item.LoadItemTable("gamedata/item_proto_global")`
  (exe nadpisuje rekordy tych vnumów), po `BonusMode 0` – wersję mt2009, tylko przy zmianie trybu. Bez zmian w exe i
  w `dbdata` (zip edytora bazy panelu podmienia dbdata – nie rusza tych plików). Klient bez tych plików pokazuje
  wartości mt2009 (serwer i tak liczy global).

## 6. i 7. bonus w trybie global – `MT2009_PLUS_RARE_WIKI_V1`

> **Zastąpione 20.10.2026 przez `MT2009_PLUS_BONUS67_V1` (`server-patches/bonusy67/README.md`):** pula wiki (z 54
> nowymi bonusami) jest teraz w **obu** trybach, wpisywana raz na świat; tryb już jej nie podmienia, a pliki
> `bonusy67_global.sql` / `bonusy67_mt2009.sql` zastąpił `bonusy67_wiki.sql`. Opis niżej – historia.

Właściciel, 20.10.2026: „zmień wszystkie bonusy 6/7 według wiki" (pl-wiki „6. i 7. bonus"). W trybie global pula
`world.item_attr_rare` (Seon-Hae, 71051/71052) to bonusy z wiki, które silnik ma; tryb mt2009 zostaje przy tabeli
właściciela z 1.10 (27 bonusów). Wiki podaje tylko maksimum na typ przedmiotu – stopnie z oficjalnej tabeli (10
poziomów, u nas 5: jej poziomy 2/4/6/8/10):

| Bonus | lv1–lv5 | Gdzie (maks.) |
|---|---|---|
| Maks. PŻ | 100/200/300/400/500 | broń, zbroja, hełm, tarcza, bransoleta, buty, naszyjnik, kolczyki, talizman |
| Maks. PE | 10/20/40/60/80 | jw. |
| Szansa na otrucie, odporność na trucizny | 1–5% | jw. |
| Wartość ataku, wartość magicznego ataku | 8/15/25/35/50 | jw. |
| Silny przeciwko Metinom | 2/4/5/7/8% | broń, naszyjnik |
| Transfer obrażeń do PE (wiki: „% obrażeń będzie dodanych do PE") | 1–5% | broń, zbroja 5%; buty 3% |
| Szansa na blok (wiki: „x% szans na zablokowanie obrażeń od ataku") | 1–5% | tarcza |
| Wola Sung Ma SIŁA/WIT/ODP/INT +x% (punkty 193–196) | 2/4/6/8/15% | talizman 8% (poziom 4) |

Rękawice, Talizmany Woli i Obręcz Jadeitu mają w slotach 6/7 własne linie – silnik nie dokłada im bonusu z puli, a
Seon-Hae ich nie przyjmuje (`MT2009_PLUS_SEONHAE_RESERVED_V1`, wcześniej Obręcz Jadeitu mogła zjeść odłamki). Bonusy
z wiki, których silnik nie ma (krwawienie, moce/odporności żywiołów w walce, „+x% łącznej wartości", bonusy
umiejętności, bossów, 1.–5. bonus +x%, bonusy rękawic…): `/opt/metin2/cache/yohara/bonusy-6-7-wiki.md` – decyzja
właściciela.

- `mariadb/playerbot/bonusy67_global.sql` / `bonusy67_mt2009.sql`, krok `apply.sh` zaraz po kroku `item_attr`: ten
  sam stan co wyżej – `world.item_attr_rare_mt2009` trzyma pulę mt2009 dokładnie wtedy, gdy w `item_attr_rare` jest
  pula wiki. Najpierw ENUM `apply` tabeli `item_attr_rare` dostaje pełną listę `item_attr` (do `POINT_HIT_PCT`, 197).
- Klient: nazwy wszystkich tych punktów są w `localeinfo_point.py` – bez zmian. Panel: nazwy punktów 178–197.

## Pliki

- `linux-port/overlays/playerbot/src/game/src/playerbot_bonus_mode.cpp` – flaga `m2_bonus_global`, trzy funkcje wyżej;
  `playerbot_elements.cpp` – odporność przez `BonusModeElementResist`.
- `edits.json` (`item_manager.cpp` drop, `item_attribute.cpp` attr declare/value); `apply_bonusyglobal.py` (Linux/VPS),
  `Apply-BonusyGlobalPatch.ps1` (Windows, w `tools/port/Apply-MT2009PlusEngine.ps1` po szczelinie).
- `linux-port/docker/mariadb/playerbot/bonusy_global.sql`, `bonusy_mt2009.sql`, `zywioly_moby_global.sql`;
  krok `apply.sh` (po wszystkich plikach żywiołów): `world.item_attr_mt2009` pusta + global → `bonusy_global.sql`;
  niepusta + mt2009 → `bonusy_mt2009.sql`; global → `zywioly_moby_global.sql`; zawsze flaga `m2_bonus_global`.
- `.env.example`, `docker-compose.yml` (środowisko migratora i gry), `tools/update.sh` (dopisuje klucz do starego .env),
  `seban-panel/env_schema.py` (sekcja „Świat i rates”, restart gry i migratora).
- Quest `zywioly`: `cmdchat("BonusMode ...")` przy logowaniu, opis żywiołów u Mistrza zależny od trybu.
- Klient root: `localeinfo_point.py`, `game.py`, `uitarget.py`, `zywioly_global.py` (nowy).

## Sprawdzenie

`M2_BONUS_MODE=global` → restart → log migratora „bonus mode: global – item_attr switched…”; Wzmocnienie Przedmiotu na
bransolecie losuje odporność na ogień do 15% i szansę na podwójne przedmioty; `/state` celu-potwora; powrót
`M2_BONUS_MODE=mt2009` → „item_attr back to the mt2009 set (12 rows)”, bonusy przedmiotów zostają.
