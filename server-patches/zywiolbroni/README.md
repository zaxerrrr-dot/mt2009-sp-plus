# zywiolbroni – Zaczarowanie Żywiołu Broni

`MT2009_PLUS_WEAPON_ELEMENT_V1` (właściciel, 29.10.2026; linia 3.x / Yohara). Na bazie paczki „[System] Elemental
Spell” (WorldArd), przepisane pod nasz silnik; okno zmiany żywiołu i grafiki (ikony, przyciski, efekty) z klienta GF.
Analiza: `cache/yohara/zywiol-broni-analiza.md` (zasady wiki, 16 błędów paczki, plan).

## Jak działa (pl-wiki „Zaczarowanie Żywiołu Broni”)

- **Zwój żywiołu** (56002 Ognia, 56003 Lodu, 56004 Błyskawicy, 56005 Wiatru, 56006 Ziemi, 56007 Mroku) przeciągnięty na
  broń w ekwipunku (nie założoną) – miecz, broń dwuręczna, sztylety, łuk, dzwon, wachlarz, szpony (bez strzał, kołczanów,
  włóczni jeździeckiej), ulepszoną co najmniej do **+7** – otwiera okno „Ulepszenie” (podgląd broni z nowym poziomem,
  koszt, OK / Anuluj). Żywioł dodaje się albo podnosi o 1 poziom, najwyżej do **+3**, tylko zwojem tego samego żywiołu.
- **Szansa 50%** na próbę (każdy poziom osobno w configu). Porażka: zwój i opłata przepadają, broń i jej zaczarowanie
  zostają jak były (broń nigdy nie ginie).
- Sukces: poziom +1 i **losowe wartości tego poziomu** (tabela wag niżej) – Siła Żywiołu (punkty `POINT_ENCHANT_*`
  178–183, te same co talizmany i Kamień Mocy Żywiołów – wspólny wzór) i Wartość Ataku (dodawana do ataku jak `value5`
  broni: `battle.cpp`, wręcz i łuk, × 2).
- **Zwój Klątwy** (56008): poziom −1 (z +1 żywioł znika), zawsze się udaje. **Zwój Zmiany** (56009): inny żywioł
  (okno GF z 6 przyciskami), poziom i wartości zostają, zawsze się udaje; nie na przedmiocie przypisanym do konta.
- **Szarfa** wchłaniająca zaczarowaną broń przejmuje zaczarowanie (`CopyAttributeTo`) i daje swój % (absorpcja) Siły
  Żywiołu i Wartości Ataku (jako `POINT_ATT_GRADE_BONUS`, jak atak wchłoniętej broni); oczyszczenie szarfy je usuwa.
- Ulepszenie broni u kowala (i +10..+15) przenosi zaczarowanie na nową broń.
- **Efekt** (wiki): zaczarowanie +3 i „gwiazdki” broni – poziom broni 1–29 od +9, 30–44 od +8 (Antyczny Dzwon
  5110–5119 od +7), 45+ od +7; broń transmutowana – tylko gdy broń wyglądu też ma gwiazdki (żywioł broni bazowej).
  Serwer wysyła `WELEMFX`, rysuje nowe exe (`client-patches/exe`, `Mt2009WeaponElement.cpp`); stare exe – bez efektu.
- **Boty nie używają systemu** (właściciel): użycie, zakup i potwierdzenie bota są odrzucane.

## Ceny (decyzja właściciela) – jedno miejsce: `linux-port/docker/game/zywiolbroni/weapon_element.txt`

| | Zwój (Stróż Medali) | Opłata w oknie | Razem |
|---|---|---|---|
| Zwój żywiołu (dodanie / podniesienie) | 9 000 000 | 3 000 000 (jak wiki) | **12 000 000** za próbę |
| Zwój Klątwy | 10 000 000 | 0 (okno bez linii kosztu – pole nie jest potrzebne) | **10 000 000** |
| Zwój Zmiany | 30 000 000 | 10 000 000 (jak wiki) | **40 000 000** |

Silnik trzyma cenę sklepu na wartości z configu (bez dopłaty za obce królestwo), `item_proto.gold` zwojów to ta sama
liczba (generator). Gdy przyjdą Medale Męstwa z systemu gildii, zmienia się ceny w configu i walutę w
`Mt2009WElemShopPrice` / `CShop::Buy` (jedno miejsce w kodzie).

Zakup zwojów: gildia co najmniej **21** (zwoje żywiołów) / **24** (Klątwa, Zmiana) – `guild_level_element` /
`guild_level_special` (0 = bez wymogu).

## Wartości (losowanie ważone, config `power` / `attack`)

Wiki: każdy poziom dodaje Siłę 1/2/4/6/8% i Wartość Ataku 2/4/6/8/12 – okno pokazuje więc zawsze „+1% ~ +8%” i
„(+2~+12)” jak oficjalne. Właściciel: wartość nie jest stała – każdy poziom ma własne wagi („typowa” wartość poziomu
najczęstsza, niższe częstsze od wyższych, najwyższa rzadka):

| Poziom | Siła Żywiołu (wartość: waga %) | Wartość Ataku (wartość: waga %) | Średnio |
|---|---|---|---|
| +1 | 1:30, **2:40**, 4:18, 6:8, 8:4 | 2:30, **4:40**, 6:18, 8:8, 12:4 | 2,6% / 4,4 |
| +2 | 1:20, 2:25, **4:35**, 6:14, 8:6 | 2:20, 4:25, **6:35**, 8:14, 12:6 | 3,4% / 5,3 |
| +3 | 1:12, 2:18, 4:25, **6:35**, 8:10 | 2:12, 4:18, 6:25, **8:35**, 12:10 | 4,4% / 6,5 |

Na +3: Siła 3–24% (średnio ok. 10,4%), Wartość Ataku 6–36 (średnio ok. 16,2). Lepszy rzut = Zwój Klątwy i ponowne
ulepszenie (jak wiki).

## Dane i klient

- `player.item_element` (id przedmiotu → żywioł 1–6, poziom 0–3, `att0..2`, `pow0..2`; `zywiol_broni.sql`): odczyt
  przy wczytaniu broni / szarfy (`ITEM_MANAGER::CreateItem`), zapis przy zmianie. `player.item`, `TPlayerItem` i
  pakiety przedmiotów bez zmian (jak `item_yextra` ysets).
- Klient: `WELEM <okno> <komórka> <spakowane>` (1 ekwipunek i założone, 3 magazyn, 4 / 5 handel: swoja / druga
  strona; 0 = zapomnij wszystko; komórka −1 = zapomnij okno). Spakowane: bity 0–2 żywioł (1 Błyskawica, 2 Ogień, 3 Lód,
  4 Wiatr, 5 Ziemia, 6 Mrok; punkt = 177 + żywioł), bity 3–4 poziom, poziom i (0..2): atak w bitach 8+8i..11+8i, siła
  w 12+8i..15+8i. `/welem_sync` – wszystko jeszcze raz (najwyżej raz na sekundę).
- Okna: `WELEMOPEN <tryb> <komórka broni> <komórka zwoju> <opłata> <żywioł> <nowy poziom> <spakowane> <atak min>
  <atak max> <siła min> <siła max>` (tryb 1 dodanie / podniesienie, 2 klątwa, 3 zmiana), `WELEMCLOSE`,
  `WELEMRESULT <tryb> <udane> <żywioł>`. Klient odpowiada `/welem ok`, `/welem change <żywioł>`, `/welem close`.
- Wszystko sprawdza serwer: przy przeciągnięciu zapamiętuje **id broni i id zwoju** (nie komórki), przy potwierdzeniu
  szuka ich jeszcze raz (gracza, w ekwipunku, broń niezałożona, bez handlu / blokady, inne okna zamknięte) i sprawdza
  wszystkie zasady od nowa, zanim pobierze Yang i zwój. Logi: `log.log` `WEAPON_ELEMENT` (tryb, wynik, żywioł i poziom
  przed/po, wartości), opłata – `MONEY_LOG_REFINE`.
- `/welem_reload` (GM) – config jeszcze raz.

## Pliki

- Logika: `linux-port/overlays/playerbot/src/game/src/weapon_element.cpp`.
- Haki (`edits.json`, 20 zmian, każda ze swoim znacznikiem; `gen_edits.py [<game/src>]` tworzy plik i sprawdza kotwice):
  `item_manager.cpp` (wczytanie), `item_attribute.cpp` (kopia przy ulepszeniu / wchłonięciu), `item.cpp` (punkty,
  dodanie do postaci), `battle.cpp` (atak wręcz i łuk), `char_item.cpp` (przeciągnięcie zwoju, komórka), `char.cpp`
  (efekt: UpdatePacket / EncodeInsertPacket, oczyszczenie szarfy), `input_login.cpp`, `safebox.cpp`, `exchange.cpp`,
  `shop.cpp` (cena, gildia), `cmd.cpp` (`/welem`, `/welem_sync`, `/welem_reload`). Po wszystkich innych łatkach
  (kotwice na liniach ysets, aura, addeq).
- Linux/VPS: `python3 apply_zywiolbroni.py <game/src>` (w `cache/yohara-deploy.sh` – po `questren`); Windows:
  `Apply-ZywiolBroniPatch.ps1 -SourceDir <game/src>` (wołane przez `tools/port/Apply-MT2009PlusEngine.ps1`, ostatnie).
- Dane: `tools/zywiolbroni/gen_zywiolbroni.py` → `linux-port/docker/mariadb/playerbot/zywiol_broni.sql` (zwoje,
  Stróż Medali 20650, sklep 9560, `player.item_element`; `apply.sh`), `tools/zywiolbroni/zywiolbroni_items.json`
  (rekordy klienta), ikony GF. NPC na mapach (Dockerfile): Jungrang (4, guild_01) 346,171, Waryong (24, guild_02)
  253,236, Imha (44, guild_03) 284,240 – komórki z wiki.
- Klient: `client-patches/client-2.0.30/root` (`welem.py`, `uiweaponelement.py`, `welemfx.py`, haki w `game.py`,
  `uitooltip.py`, `uiinventory.py`), `client-patches/client-2.0.30/tools/zywiolbroni` (dane klienta, pack z efektami i
  przyciskami GF), exe: `client-patches/exe` (tylko efekt na broni).
