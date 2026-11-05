# pety – System Zwierząt Domowych

`MT2009_PLUS_GROWTH_PET_V1` (właściciel, 4.11.2026: decyzje w `/opt/metin2/cache/yohara/decyzje-pety.md`). System
„growth pet” na wzór portu Anka2 (`growth_pet.cpp` tam), napisany od nowa pod nasz silnik i dopasowany do wiki
(pl przede wszystkim, tr tam, gdzie pl milczy): <https://pl-wiki.metin2.gameforge.com/index.php/System_Zwierz%C4%85t_Domowych>,
<https://tr-wiki.metin2.gameforge.com/index.php/Pet_Sistemi>. Zastępuje New Pet System (`MT2009_PLUS_NEW_PET_V1`).

**Nakładana jako OSTATNIA** (po `tytuly`). Linux/VPS: `python3 apply_pety.py <game/src>`; Windows: `Apply-PetyPatch.ps1`
(`tools/port/Apply-MT2009PlusEngine.ps1`, na końcu). `gen_edits.py [<game/src>]` pisze `edits.json` (26 edycji) i sprawdza
kotwice. Oprócz edycji skrypt **instaluje pliki** z `files/` obok `game/src` (nadpisuje, gdy się różnią – zmiana dociera
do już załatanego drzewa): `common/growth_pet_types.h`, `db/src/growth_pet_db.cpp`.

## Dane – jedno źródło

`tools/pety/pety_data.py` (gatunki, przedmioty, umiejętności z tabelami wiki, PD, typy, ewolucje, potencjał) →
`tools/pety/gen_pety_sql.py` pisze:
- `linux-port/docker/mariadb/playerbot/pety.sql` (tabele, 69 przedmiotów, 42 moby, proto umiejętności, migracja),
- `linux-port/overlays/playerbot/src/game/src/growth_pet_data.h` (te same tabele dla gry),
- `tools/pety/pety_items.json` (rekordy dla paczek klienta, `client-patches/client-2.0.30/tools/pety`).

## Jak działa (gra: `growth_pet.cpp`, nakładka)

- **Jajo** (55401–55414, 7 dni): okno inkubatora, imię 4–20 znaków (`check_name` + banword), 100 000 Yang → **pieczęć**
  (55701–55714). Id zwierzaka = socket 2 pieczęci (i klatki), wiersz `player.growth_pet`.
- **Poziomy 1–105**: czerwone kule = PD z zabójstw właściciela (z jego bonusami PD, przed jego limitami; właścicielowi
  nic nie ubywa), niebieska = PD przedmiotów (broń/zbroja: cena sprzedaży u NPC / 2, Smakołyk 80 000, Smakołyk+ 5 %),
  nadwyżka niebieskiej przechodzi na następny poziom; tabela PD z wiki (dodatek A). Poziom ≤ poziom właściciela.
- **Ewolucje**: Młody → Dziki (40, pełne PD) → Dzielny (80) → Bohaterski (81+, 30 dni) → Przebudzony (105, pełne PD,
  czempion 1) → Mocny (czempion 14, pełne PD → 15); materiały z wiki (wszystkie z ekwipunku, także magazynów kategorii).
- **Typ 1–8** (wyklucie 1–6; Zaczaruj zwierzaka 1–8, Małpiszon/Pająk/Azrael 1–6), statystyki właściciela PŻ/Obrona/PE
  w 0,001 % (start 0,1–2,0 %, przyrosty co X poziomów wg typu, typy parzyste stałe, nieparzyste losowe) + premia wieku
  0,001 %/dzień (do 800 dni). Wartości startowe nie zmieniają się przy Zaczaruj (przeliczenie od nowa z wiekiem).
- **Umiejętności**: 3 miejsca (1–3 otwarte wg gatunku), 23 księgi (55010–55027, 55034–55038), od Bohaterskiego,
  poziomy 1–20 po 2 000 000 Yang; wartości z wiki: krzywa poziomów 1–20 (de), wartości poziomu 20 wg gatunku i typu
  (specjalizacje, pl) i progi wzrostu z poziomem zwierzaka (tr); Revertus (jedna) / Reverti (wszystkie).
  Automatyczne: Odnowa (<20 % PŻ, 480 s), Nieśmiertelność (<10 % PŻ, 600 s), Uzdrowienie (trucizna/spowolnienie,
  480 s), Lekkie jak Piórko (walka, 180 s: zwierzak atakuje cel, 175–1400 obrażeń na sekundę przez 5 s, efekt
  `gyeonggong_boom.mse`).
- **Życie**: losowe wg gatunku (wiki), Odżywka = 100 % (martwy: 50 %, wiek od 1 dnia), jaja/inne pieczęcie w oknie
  „Nakarm” = 3–5 %, Boska Odżywka (zakładka wskrzeszania innego, żywego zwierzaka): 100 %, 80 % wieku, ilość
  max(1, wiek/10) (tabela pl).
- **Klatka Transportowa** (55002): pieczęć → klatka (30 dni, bez starzenia, tylko żywy zwierzak), handel oknem wymiany
  (partner widzi zwierzaka w podpowiedzi, GC 226), prawy przycisk wyjmuje (czas trwania odnowiony), pusta klatka na
  przeterminowaną = nowe 30 dni.
- **Sfera Losu** pokazuje typ (zapamiętany: punkt `TYPE`), **Pergamin Nazwy** + 100 000 Yang zmienia imię.
- Przywołany zwierzak idzie za właścicielem (mob z flagą peta, nie atakowalny), skala wg stopnia (GC 235: 100/120/140 %,
  Bohaterski i czempion – własne modele 34xxx), jeden naraz (obok peta z ItemShopu).
- GM: `/pet_set <level|clevel|evo|type|exp|iexp|cexp|life|age|skill slot id lv> <wartość>` (GM_IMPLEMENTOR).

## Poziomy czempiona zwierzaka (projekt wg wiki)

Wiki (tr/en/de) daje: odblokowanie Bohaterski 105 + pełne PD (+30 dni), materiały ewolucji Przebudzony/Mocny, poziomy
czempiona 1–30 (druga ewolucja przy 14), osobne PD czempiona i PD przedmiotu czempiona (tabela), „zwierzaki czempiona
rosną tylko w regionach Yohary”, Smaczny Smakołyk (200 000 PD albo 1 200 PD czempiona), nowe statystyki Wola SungMa
(ODP) / Przebicie bloku / Precyzja (start 0,1–0,5 %, przyrosty wg typu co X poziomów czempiona), 2 miejsca potencjału
(od poziomu 1 i 15) z jajami (losowa umiejętność z listy gatunku jaja, nigdy ta sama dwa razy, trwa tyle co jajo,
poziom 1/3/4/5/6 wg poziomu czempiona, ≤ 2 gdy drugie miejsce puste). Połączenie z naszym czempionem
(`MT2009_PLUS_CHAMPION_V1`):
- PD czempiona zwierzaka = PD czempiona właściciela z potwora mapy Sung Ma (`champion::GiveExp`, te same premie) –
  więc tylko na mapach Yohary i tylko gdy właściciel jest czempionem (inaczej nie bije tamtejszych potworów);
- poziom czempiona zwierzaka ≤ poziom czempiona właściciela (zasada „nie wyżej niż właściciel” przeniesiona na
  czempiona – wiki nic nie mówi);
- Wola SungMa → `POINT_SUNGMA_PER_IMMUNE`, Precyzja → `POINT_HIT_PCT`, Przebicie bloku – nowa reguła w `Damage`
  (szansa bloku celu minus przebicie).

## Silnik (`edits.json`)

| Plik | Co |
|---|---|
| `common/tables.h` | GD 147/148/149, DG 185/186, `#include "growth_pet_types.h"` |
| `packet.h`, `packet_info.cpp` | CG 122–134, GC 224–236, `#include "growth_pet_packets.h"`, rozmiary |
| `input_main.cpp` | pakiety okna |
| `input_db.cpp` | po wczytaniu przedmiotów i magazynu: zwierzaki pieczęci/klatek; DG 185/186 |
| `char_item.cpp` | użycie przedmiotów (przed resztą `UseItemEx`; `PET_PAY` z ItemShopu idzie dalej) |
| `item.cpp` | pieczęć/klatka, która przyszła po zalogowaniu (handel, magazyn) |
| `exchange.cpp` | klatka w oknie wymiany → GC 226 dla partnera |
| `char_battle.cpp` | PD z zabójstw, utrata PD przy śmierci właściciela, nieśmiertelność, przebicie bloku |
| `char.cpp` | zniszczenie postaci (zapis, sprzątanie), GC 235 dla widza |
| `cmd.cpp` | `/pet_set` |
| `db/src/ClientManager.cpp` | GD 147–149, tabela umiejętności po pakiecie startu, zapis co 10 s, zapis przy zamknięciu |

Nakładka: `growth_pet.cpp/.h`, `growth_pet_packets.h`, `growth_pet_data.h` (generowany), `playerbot_newpet.h`
(dawne haki `playerqol`: `NewPetApplyPoints` → bonusy zwierzaka, reszta pusta / komunikat), `playerbot_newpet_bots.h`
(boty na nowym systemie: wyklucie najlepszego jaja, Odżywka, PD przedmiotów z Smakołyków i złomu, ewolucje z
materiałami, księgi wybranych umiejętności, poziomy za Yang), `playerbot_champion.cpp` (PD czempiona, Smaczny
Smakołyk 1 % z potworów rangi 1–4 map Sung Ma), `playerbot_town.h` (cena klatki), `playerbot_price_tables.h`,
`playerbot_ishop3_catalogue_data.h`.

**Inaczej niż Anka2 (świadomie):** baza nie trzyma zwierzaków właściciela/konta – rdzeń pyta o zwierzaki pieczęci i
klatek, które postać ma (logowanie, magazyn, przedmiot, który przyszedł, otwarcie klatki), a db trzyma pamięć podręczną
po id (`growth_pet_db.cpp`). Dzięki temu nie ma kolizji id konta z id postaci (błąd Anka2 w magazynie), klatka działa
każdą drogą handlu, a pakiet magazynu się nie zmienia. Tabela umiejętności idzie osobnym DG 186 po pakiecie startu (jak
tabela sklepów Ikarusa), bez zmiany samego pakietu startu. Poprawione błędy Anka2: wskrzeszenie liczy prawdziwe stosy
(bez NULL), jaja poza tabelą gatunków, wiek 30 dni naprawdę blokuje, brakujące dane umiejętności, `FindByVID` z id
przedmiotu, podwójna analiza ActivatePct, wyrzucenie przedmiotu-pieczęci przez klienta.

## Baza

`apply.sh` (`MT2009_PLUS_GROWTH_PET_V1`, w miejscu starego bloku New Pet System): `pety.sql`, Sfera Losu u Handlarki
Różności (sklep 3, 10 000 Yang), linie ItemShopu 40930–40937 (raz na instalację; ceny wiki: Skrzynka na Zwierzaka 39,
Odżywka 19, Klatka 79, Pergamin 49, Reverti 79, Revertus 59, Boska Odżywka 179, Skrzynia Ksiąg 129 SM; 40931/40937
ukryte w sklepie WWW, który ma własne linie).

Nazwy przedmiotów = tytuły stron przedmiotów na pl-wiki (wszystkie 69; Jajo Aamona i Mały Aamon (pieczęć) – tylko
w tabeli strony systemu, bez własnych stron). Świat, który zapisał już `pety:items_v1` (potem tylko INSERT IGNORE),
dostaje je raz znacznikiem `pety:names_v1` (UPDATE name/locale_name 69 wierszy) – naprawia m.in. stare przemianowanie
55033/55034 na Reverti/Revertus z bloku ishop5 w `apply.sh` (usunięte). Zmiana nazwy w `pety_data`/`gen_pety_sql` =
nowy znacznik (`NAMES_MARKER`). Opisy tych przedmiotów w sklepie WWW (`shop3/include/db/client_itemdesc.json`) =
opisy z `pety_items.json`.

### Migracja (raz, znacznik `pety:migracja_v1`, jedna transakcja)

- Każdy wiersz `player.newpet_pet` → `player.growth_pet` (id 0xF0000000 + stare id): gatunek (`jajo + 300`), imię,
  poziom (≤ 105), stopień z poziomu (1–40 Młody, 41–80 Dziki, 81+ Dzielny, 81+ i dawny Heroiczny = Bohaterski), wiek
  od dawnego `created`; stan 3 – przy następnym logowaniu gra losuje typ, statystyki, życie i miejsca jak przy wykluciu
  i daje pieczęć (gdy brak miejsca w ekwipunku – przy kolejnym logowaniu). Umiejętności nie przechodzą.
  Zwierzak w transporterze (55007) → Klatka Transportowa (55002) ze zwierzakiem (30 dni).
- Przedmioty (`player.item` – torby, magazyn, sklepy Ikarusa – i `player.item_award`):

| Stary | Nowy |
|---|---|
| 55001 Proteinowa Przekąska | 55001 Odżywka |
| 55002 Transporter Peta (pusty) | 55002 Klatka Transportowa |
| 55007 Transporter z Petem | 55002 Klatka Transportowa ze zwierzakiem |
| 55003 Księga Młodego Zwierza, 55008 Pergamin, 55009 Skrzynia Ksiąg | bez zmian (nowe znaczenie 55009: księgi wiki) |
| 55010–55031 (22 dawne księgi) | 55009 Skrzynia Ksiąg Zwierza (1 za 1) |
| 55032 Smakołyk | 55028 Smakołyk |
| 55033 Pet Reverti / 55034 Pet Revertus | 55029 Reverti Zwierza / 55030 Revertus Zwierza |
| 55035 Smakołyk+ | 55031 Smakołyk+ |
| 55036 Klucz Miejsca Umiejętności | 55033 Zaczaruj zwierzaka |
| eliksiry S / M (55101-2, 55108-9, 55115-6) | 1 / 2 × 55028 Smakołyk |
| eliksiry L / XL (55103-4, 55110-1, 55117-8) | 1 / 2 × 55031 Smakołyk+ |
| 95737 (zastępcza Przeb. Księga Zwierza) | 55007 Przeb. Księga Zwierza |
| jaja 55401–55411 | te same (nazwy wiki), 7 dni od migracji |

- ItemShop w grze: stare linie 409xx usunięte; eliksiry 55101–55118 usunięte z `item_proto`.
- Sprawdzone na kopii tabel bazy testowej (jednorazowe MariaDB 11.8): 1263 zwierzaki, liczby przedmiotów zgodne z
  tabelą, drugi przebieg nic nie zmienia.

## Dropy (wiki; `linux-port/docker/game/pety` + edycje plików/generatorów)

Skrzynka na Zwierzaka 55400 (stawki tr), Skrzynia Ksiąg Zwierza 55009 (stawki tr), Jajo Mini Azraela z Charona/Azraela
(4 %), Księgi Dzikiego/Dzielnego Zwierza z bossów wiki (5 % / 3 %), Bohat. Księga z kapitanów Gnolli/Ahtrina (10 %),
Przeb. Księga z wodzów Yohary (zamiast 95737), Smakołyki z Metinu Lasu (zamiast brakującego Metinu Agonii), jaja w
skrzyniach Okey/Łupu Królewskiego/Yutnori/kwiatów/B. Smoczej Skrzyni (ciężkiej)/Królowej Meley (Exedyar zamiast
Królów Smoków)/Balathora (Aamon), stare przedmioty w skrzyniach Arezzo/Atlantydy/Balathora/Koła zamienione.

## Klient

Exe: `client-patches/exe` (README, `ENABLE_GROWTH_PET_SYSTEM`, `Mt2009GrowthPet.cpp`), root `uipetinfo.py`,
`petdata.py`, `petlocale.py`, `uiscript/pet*.py`, zaczepy w `game.py`, `interfacemodule.py`, `uiinventory.py`,
`uitooltip.py`, `uisafebox.py`, `constinfo.py` (1.3.3), paczka `pety` (`tools/pety`). Okno: klawisz U (dawny klawisz
okna petów) i przycisk w pasku bocznym. Brama wersji: `M2_CLIENT_MIN_VERSION` 1010303.

## Otwarte / wybory tam, gdzie wiki milczy

- Odporność (likan): księga istnieje, ale bez Likanów (`ENABLE_WOLFMAN_CHARACTER` wyłączone) nic nie daje.
- Brak w świecie: Baashido, Królowie Smoków, Aamon, Inwazja Sunga Mahi, Metin Agonii, Rzeźnik Kalgaroth – zamienniki
  wyżej; Jajo z wieży Sung Mahi pominięte (wieża nie ma losowych nagród).
- Stawki dropu z mobów – wiki ich nie podaje (nasze: 1–10 %); Smaczny Smakołyk 1 %.
- Czas „Lekkie jak Piórko” (5 s), próg Nieśmiertelności (<10 % PŻ), wzrost wartości ciągłych umiejętności (80 % → 100 %
  między poziomem 81 a 105) – nie ma ich na wiki.
- `tools/yohara_prices/gen_yohara_prices.py` wciąż zna 95737 (ponowne uruchomienie przywróci tę linię zamiast 55007).
- Po wdrożeniu: `gen_bot_catalogue.py --docker` (nowe linie ItemShopu).
