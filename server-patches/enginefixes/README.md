# Poprawki silnika (1 października)

Zmiany silnika opisane w `edits.json`, każda z własnym znacznikiem:

| Znacznik | Plik | Co robi |
|---|---|---|
| `MT2009_PLUS_EARLY_PACKET_V1` | `input.cpp`, `input_login.cpp` | Komenda czatu albo szept, który przyszedł, zanim nowe połączenie przywitało się z serwerem (faza powitania) albo w trakcie ładowania postaci, jest pomijany w całości. Dotąd obie fazy czytały tylko nagłówek pakietu, a jego tekst brały za kolejne pakiety – nieznany nagłówek i zerwane połączenie. Okno Towarzysza (P) pyta serwer komendą `/towarzysz`, więc przy otwartym oknie zmiana kanału i teleport kończyły się powrotem do ekranu logowania. |
| `MT2009_PLUS_MAP_ALLOW_COPY_V1` | `config.cpp` | Lista map rdzenia w pakiecie startowym do bazy: granica `MAP_ALLOW_LIMIT` sprawdzana przed zapisem, nie po nim. Mapa ponad limit jest pomijana z błędem w syserr zamiast nadpisywać liczbę zalogowanych kont (śmieciowe logowania w bazie i nieskończone ładowanie przy pierwszym teleporcie). Limit to 48 (`MT2009_PLUS_MAP_ALLOW_48_V1`, playerqol); game1 układu „unified” ma dziś 43 mapy (od `MT2009_PLUS_BOT_DUNGEONS_ALL_V1` wszystkie lochy są na game1), układu „split” 35. |
| `MT2009_PLUS_AUTOHUNT_MINIBOSS_V1` | `cmd_general.cpp` | Auto Łowy: minibossowie (ranga S_KNIGHT – Chuong, Lykos, Scrofa, Bera, Tigris, Bestialski Łucznik, Bestialny Specjalista, elitarne potwory lochów) są celem przy „Moby” i przy „Bossy”. Przy „Bossy” idą zaraz po bossie, przed Metinem. |
| `MT2009_PLUS_ARROW_RANGE_V1` | `battle.cpp` | Strzały żywiołów (Ognista, Trująca, Lodowa, Przeklęta Strzała, 8006–8009) mają w `item_proto` zero w `value2`, `value4` i `value5`, a `CalcArrowDamage` osłabia strzał od `value4` do `value5` do `value2` procent – więc każdy strzał dalej niż z przyłożenia dawał 0 obrażeń (łucznik z taką strzałą nie zadawał żadnych). Strzała bez zakresu osłabienia (`value5` nie większe od `value4`) bije pełną siłą na każdą odległość, jak srebrna strzała w potwora. |
| `MT2009_PLUS_AUTOHUNT_CROWD_V1` | `cmd_general.cpp` | Auto Łowy wychodzą z tłumu: `/autohunt_target` przyjmuje ósmy argument (po VID-zie do pominięcia). `1` oznacza „najbliższy potwór, bez kolejności” – bez pierwszeństwa potwora, który bije postać, Metinu i bossa. Klient (`uiautohunt.py`) wysyła go, gdy postać w drodze do celu utknie w grupce potworów: po chwili bierze najbliższego zamiast dalej biec za pierwszym. Klient bez tej zmiany wysyła siedem argumentów i nic się nie zmienia. |
| `MT2009_PLUS_WUKONG_GUARDIANS_V1 (crush)` | `char_skill.cpp` | Odepchnięcie (umiejętności z flagą CRUSH – potworów i graczy) kończy się na ostatnim wolnym punkcie: linia od celu do końca odepchnięcia jest sprawdzana co 25 jednostek i odepchnięcie staje przed zablokowanym terenem (atrybut BLOCK/OBJECT), a gdy już pierwszy punkt jest zablokowany, cel zostaje w miejscu. Dotąd cel lądował tam, gdzie kończyła się długość odepchnięcia – za krawędzią platformy, w ścianie – a potwór szedł za nim. Na Wzgórzu Wukonga (3 października, serwer dla wspierających) Obrońcy Chmur zepchnęli towarzysza gracza 25 kratek poza arenę, jeden Obrońca poszedł za nim i został tam – nie dało się go dojść ani ukończyć lochu. Siatka zabezpieczająca w `wzgorze_wukonga.quest` (ten sam znacznik). |
| `MT2009_PLUS_AREZZO_BALANCE_V1` (push, sync) | `char_battle.cpp`, `input_main.cpp` | Bossa (potwór rangi BOSS i KING) nie da się odepchnąć (właściciel, 5 października: „bossowie nie powinni ani odpychać gracza, ani być odpychani”). `IsResistPush` odpowiada „tak” dla bossa – to pytanie zadaje odepchnięcie umiejętności z flagą CRUSH (konne, łucznika, wojownika; `char_skill.cpp`) i odrzut strzału łucznika z konia. Przesunięcie, które klient atakującego nadaje potworowi przy ciosie (combo, szarża z konia) i zgłasza pakietem `SyncPosition`, dla bossa jest odrzucane – boss zostaje tam, gdzie ma go rdzeń, a klient wraca go na to miejsce przy jego następnym ataku lub kroku (oba niosą pozycję). Na zboczach map Arezzo nie da się już przyprzeć bossa do ściany z konia. Druga połowa – bossowie nie odpychają gracza – to dane: umiejętności potworów 256/258/260 bez flagi CRUSH (`mariadb/playerbot/apply.sh`, ten sam znacznik). |
| `MT2009_PLUS_DUNGEON_GROUND_LOOT_V1` (declare, drop_item_at, register, people, pickup) | `questlua_game.cpp`, `char_item.cpp` | Funkcja questów `game.drop_item_at(vnum, ile, x, y [, sek [, ludzie]])`: przedmiot na ziemi w podanym miejscu mapy bieżącego gracza (piksele; zablokowane miejsce przesuwa się na najbliższe wolne), jego własność na `sek` sekund (0 – zwykłe 30 s silnika), więc drużyna może go podnieść dla niego jak zwykły drop bossa. `ludzie` = 1: żaden bot go nie podniesie (`CHARACTER::PickupItem`, znacznik po identyfikatorze przedmiotu na 10 minut; boty też go nie szukają – `playerbot_loot.h`, `playerbot_party_dungeon.h`, `playerbot_sidekick.h`). Używają jej Razador, Nemere i Beran-Setaou: skrzynie i dodatkowy łup leżą wokół bossa zamiast trafiać do toreb (właściciel, 15 października). |
| `MT2009_PLUS_HERB_BUSY_V1` (field, init, set, hit, stun) | `char_player.h`, `char_player.cpp`, `char_battle.cpp`, `battle.h` | Zbieranie ziół (`BUSY_ACTION_HERB`) nie jest przerywane trafieniem ani ogłuszeniem od potwora. Rdzeń zapamiętuje typ trwającej akcji (`m_bBusyActionType`); atak gracza, ogłuszenie od gracza i ruch postaci przerywają jak dotąd, inne akcje bez zmian. Dotąd w miejscach z potworami (Jaskiniowy Grzyb w lochu małp) nie dało się nic zebrać. |
| `MT2009_PLUS_TOOL_REFINE_POINTS_V1` (helper, packet, reopen) | `input_main.cpp` | Nożyk Zielarza i kilof ulepszają się tylko z zebranymi punktami (`socket0 >= value2`), jak sprawdza `ReceiveItem`. Pakiet ulepszania narzędzia bez punktów jest odrzucany, a okno ulepszania po ulepszeniu („keep open”) nie otwiera się ponownie dla takiego narzędzia – dotąd można było ulepszać je dalej bez punktów. |

## Pliki

- `edits.json` – zmiany (plik, znacznik, stary i nowy kod);
- `Apply-EngineFixesPatch.ps1` – Windows (`tools/port/Apply-MT2009PlusEngine.ps1`);
- `apply_enginefixes.py` – Linux/VPS; oba czytają ten sam `edits.json`.

Zmiana już nałożona (jest jej znacznik) jest pomijana; zmiana, której kodu nie
ma dokładnie raz, przerywa całość, zanim cokolwiek zostanie zapisane.

- `MT2009_PLUS_CUBE_FOR_PLAYERS_V1` (`cmd.cpp`): komenda `cube` dostępna dla graczy (była tylko dla GM), więc okno wytwarzania u Seon-Pyeonga i innych NPC otwiera się zwykłemu graczowi. `Cube_open` dalej sprawdza NPC i odległość.
- `MT2009_PLUS_GUILD_TREASURY_V1` (`guild.h`, `guild.cpp`, `questlua_guild.cpp`, `cmd_gm.cpp`): skarbiec gildii (wpłaty członków i zrzutki botów) można wydać tylko na gildię. Wypłata do ekwipunku jest odrzucana. Za budynek (`/build`) i ziemię (quest `guild_building`, funkcje `guild.treasury_available` / `guild.treasury_spend`) najpierw płaci skarbiec, resztę lider ze swojego yang.
- `MT2009_PLUS_PACKET_TRACE_V1` (`desc.h`, `desc.cpp`, `input.cpp`): każde połączenie pamięta 48 ostatnich pakietów wysłanych do gracza (nagłówek, rozmiar, dla czatu typ i początek tekstu). Gdy klient przyśle niezrozumiały pakiet („UNKNOWN HEADER”), syserr dostaje listę „PACKET_TRACE” z tym, co serwer wysłał mu tuż przed. Od razu logowany jest też każdy pakiet powyżej 16 KB.
- `MT2009_PLUS_ITEM_EXTRA_APPLY_V1` (`item.cpp`, nakładka `playerbot_item_extra_apply.h`): dodatkowe bonusy przedmiotu ponad trzy z `item_proto` (format `item_proto` i exe klienta mają miejsce na dokładnie 3). Wiersze tabeli `world.item_extra_apply` (vnum, slot, apply_type = ten sam numer POINT_* co `applytype`, apply_value; tworzy ją `mariadb/playerbot/apply.sh`, wypełnia edytor bazy danych panelu Seban) rdzeń czyta raz, przy pierwszym założonym przedmiocie po starcie („Zastosuj” w edytorze restartuje rdzenie). `CItem::ModifyPoints` zakłada je i zdejmuje razem z bonusami z `item_proto`, tak samo jak je (punkty użytkowe pominięte, ruda w gnieździe biżuterii podnosi je tak samo; pieczęć wierzchowca – bez nich, jej bonusy idą przez AFFECT_MOUNT_BONUS). Boty liczą je w ocenie ekwipunku (`playerbot_gear.h`). Klient pokazuje je w opisie przedmiotu z pliku `gamedata/item_extra_apply.txt` paczki dbdata (zip z panelu, `uitooltip.py`).
- `MT2009_PLUS_RARE_ATTR_INDEPENDENT_V1` (`item_attribute.cpp`): `CItem::HasAttr` sprawdza tylko bonusy 1-5 (oryginał czytał też pierwszy bonus 6/7, więc np. szansa na krytyk w 6. bonusie blokowała krytyk w 1-5).
- `MT2009_PLUS_AREZZO_STONE_GROUPS_V1` (`char_state.cpp`): na Dolinie Cyklopów (mapa 360) Metin Cienia (8009) przywołuje grupy cyklopów tej mapy (36001–36003, `group.arezzo.txt`), a nie swoje pustynne (1301–1310 – Pustynny Zawadiaka 2108, wężowi łucznicy). Nocny test 6/7 października: pustynne potwory z Metinów zabijały boty poziomu 45 na mapie cyklopów. Poza mapą 360 Metin Cienia przywołuje to co dotąd.
| `MT2009_PLUS_AREZZO_ENCHANT_PERMIT_V1` | `item_manager.cpp` | Na mapach Arezzo 360/361/362 Pozwolenie na Zaczar. Przedmiotu (30370) z dropu zostaje z szansą 1/4 (właściciel 7.10); gdzie indziej bez zmian. |
| `MT2009_PLUS_AUTOHUNT_CLEAR_LINE_V1` | `cmd_general.cpp` | Auto Łowy: przy wyborze celu (`/autohunt_target`) potwór, do którego prosta linia przechodzi przez ścianę/skałę/budynek (`AutoHuntSegmentBlocked`), dostaje karę +250000 do wyniku – w obrębie swojej kategorii (boss / Metin / mob, kolejność z okna bez zmian) najpierw idą cele z czystą linią, zablokowany tylko gdy nie ma innego. Linia liczona tylko dla kandydata, który mógłby wygrać; odpowiedź `AutoHuntTarget <vid> <blocked>` bierze wynik z rankingu. |
| `MT2009_PLUS_AUTOHUNT_TRUE_NEAREST_V1` | `cmd_general.cpp` | Auto Łowy, wybór celu: odległość liczona dokładnie (`Mt2009PlusDistance`, pierwiastek zamiast przybliżenia `DISTANCE_APPROX`, które myli się do ~1/8), a cel za ścianą/drzewem/płotem dostaje zamiast +250000 karę „objazdu” = jego odległość + 500 (liczy się jak 2×odległość+500). Wcześniej dowolny potwór na otwartej przestrzeni w całym zasięgu wygrywał z tym kilka kroków dalej za drzewem – stąd „biegnie do bardzo dalekich celów”. Kategorie (boss / Metin / mob) i kolejność z okna bez zmian (kara ≪ 500000). Klient: `uiautohunt.py`, ten sam znacznik. |
| `MT2009_PLUS_RAZADOR_GATE_V1` (helper, move) | `input_main.cpp` | Loch Razadora (mapa 351 i jej instancje): dopóki stoi Zamek Przeznaczenia (20387, łańcuchy na moście) albo Smocza Brama (20388) – quest zabija je `d.kill_unique` dopiero przy starcie zadania danej komnaty – ruch gracza nie może wejść w koło 6,5 m wokół nich. Pakiet ruchu, którego odcinek wchodzi w to koło (albo głębiej, gdy gracz już w nim stoi), jest odrzucany jak za długi ruch (`Show` + `Stop`): postać zostaje tam, gdzie ma ją rdzeń. Wyjść z koła wolno. To NPC, nie obiekty mapy, a atrybuty mapy (`server_attr`) są wspólne dla wszystkich instancji, więc blokady nie da się nałożyć na mapę jednej wyprawy. 6,5 m pokrywa najszersze przejście przy bramie (5,5 m wg `server_attr`) i odpowiada kuli kolizji bramy w kliencie (6,8 m). Boty (bez pakietów ruchu) nie są tym objęte. |
| `MT2009_PLUS_STONE_GROUP_GUARD_V1` | `char_state.cpp` | Metin z zakresem grup 0–0 (Metiny SZC/PB 8120–8123, 8130–8133, Kamień Duchowy 7600 w Wieży Sung Mahi – bez grup, jak oficjalnie) nikogo nie przywołuje i nie pisze błędu; grupa, której nie ma w `group.txt`, jest zgłaszana raz na rdzeń (`STONE_GROUP_MISSING` w syserr) zamiast linii `NOT_EXIST_GROUP_VNUM` przy każdym progu PŻ każdego takiego Metinu. Metin z grupami działa jak dotąd. Brakujące grupy Yohary: `game/yohara_metiny` (druga analiza botów 6.11, pkt 2). |
| `MT2009_PLUS_POLYMORPH_MOTION_V1` | `char.cpp` | Gracz zamieniony w postać bez ruchu na serwerze – posągi Zodiaku (20452–20463, tylko ruch pojawienia się, jak oficjalnie) i lodowy kryształ Balathora (20498) – ma prędkość ruchu swojej rasy zamiast zgadywanej 300, bez linii `cannot find motion` przy każdym kroku (ok. 1 900 dziennie na teście Yohary, głównie boty w lodzie). Pkt 11 drugiej analizy botów. |
| `MT2009_PLUS_MOUNT_UNSUMMON_QUIET_V1` | `MountSystem.cpp` | Zdjęta (albo wygasła) pieczęć wierzchowca, którego nikt nie przywołał (zamiana pieczęci przez bota, wylogowanie, które zabrało go wcześniej), nie ma czego odsyłać – dotąd `CMountSystem::Unsummon` pisał „Null Pointer (actor)” (ok. 290 dziennie na teście Yohary). Pkt 11. |
| `MT2009_PLUS_BOT_LOAD_PLACE_V1` | `input_db.cpp` (+ nakładka `CPlayerBotManager::PlaceLoadingBot`) | Bot zapisany na mapie, której ten rdzeń nie ma, dostaje miejsce przed sprawdzeniem `GetValidLocation`: punkt przekazania (handover) albo towarzysza, a gdy go nie ma – pierwszą wioskę królestwa, jeśli rdzeń ją ma. Te same miejsca dawał dotąd hak po sprawdzeniu i `ENABLE_GOHOME_IF_MAP_NOT_EXIST`, ale po dwóch liniach SYSERR (ok. 5 000 dziennie na teście Yohary; żadne wejście nie było nieudane). Rdzeń bez mapy i bez wioski zostawia wejście silnikowi i pisze `PLAYERBOT_LOAD_PLACE: no_place`. Wyłącznik: `PLAYERBOT_LOAD_PLACE=0`. Pkt 10. |

## Handel kamieniami Smoczej Alchemii (`MT2009_PLUS_EXCHANGE_DS_V1`)

`exchange.cpp` (`AddItem`, `Check`): przedmiot o numerze pola powyżej rozmiaru ekwipunku był odrzucany jako
„juki konne”, bez sprawdzenia okna – kamień Smoczej Alchemii (własne okno, duże numery pól) zawsze dostawał
komunikat „Przywołaj konia…”. Teraz tylko pole okna INVENTORY za ekwipunkiem to juki (`IsHorseInventory`).

## Kamienie Smoczej Alchemii w sklepie offline (`MT2009_PLUS_IKASHOP_DS_V1`)

Przyczyna była w kliencie (`offlineshopmanage.py`, ten sam znacznik): siatka sklepu podawała typ pola myszy zamiast
okna – dla plecaka to ta sama liczba (1), dla okna Smoczej Alchemii nie (11 zamiast 5), więc kamień był szukany
i wysyłany z okna, którego nie ma. Rdzeń wystawia kamień z okna DRAGON_SOUL_INVENTORY bez zmian i daje go kupującemu
do tego okna (`CanTakeInventoryItem`). `ikarus_shop_manager.cpp` (`IkashopHasRoomFor`): przed kupnem i przed zdjęciem
linii ze sklepu miejsce na kamień jest sprawdzane w oknie Smoczej Alchemii (było: w plecaku – pełny plecak blokował
kupno kamienia, a pełne okno alchemii przepuszczało go do depozytu sklepu); kupujący bez odblokowanej Smoczej
Alchemii dostaje komunikat.

## Zabójstwo gracza z gildii na wojnie liczy się dla questów (`MT2009_PLUS_WAR_KILL_QUEST_V1`)

`char_battle.cpp` (`CHARACTER::Dead`): zabójca, którego gildia prowadzi wojnę, nie dostaje doświadczenia ani dropu,
ale rdzeń pomijał całe `Reward()` – razem ze zdarzeniem `kill` questów. Licznik lochu („Pozostało: 2” na Wzgórzu
Wukonga, 16.10) stał. Teraz w tej gałęzi idzie samo `CQuestManager::Kill` (z zaliczeniem zabójstwa towarzysza jego
właścicielowi, jak w `Reward()`); doświadczenie, drop, karty, owoce rang i Przepustka Bojowa – dalej nie.
- `MT2009_PLUS_BOT_SHOP_PAGES4_V1` (slot), (person) (`ikarus_shop_manager.cpp`): sklep offline bota ma 4 strony (320 pól, `playerbot_offline::BOT_SHOP_PAGES` w nakładce, czytane też przez silnik). Sklep gracza dalej najwyżej 2 strony (przełącznik większych sklepów) – linia gracza na polu 160+ jest odrzucana. Test pola premium/zablokowanego (`CanAddItemToShop`, argument BYTE) dla pola za pierwszą stroną pyta o pole 80 – czwarta strona (240–319) zawijała się na pierwszą. `pos` przedmiotu to WORD, pakiet otwarcia sklepu (320 × `TShopItem`) mieści się w rozmiarze WORD. Okno gościa: `client-patches/client-2.0.30/root/offlineshopguest.py` (strony 2×2) – potrzebny nowy klient 2.x.
- `MT2009_PLUS_CUBE_SHORT_LIST_FIX_V1` (result, material; `cube.cpp`): okno wytwarzania NPC z jedną–dwiema krótkimi recepturami – `resultText.size() - 20` na `size_t` przekręcał się poniżej 20 znaków, rdzeń pisał „Too long cube result list text” i wysyłał pustą listę (klient: IndexError w `uiCube.py`). Teraz `size() >= CHAT_MAX_LEN + 20`; to samo w liście materiałów. Z paczki właściciela p-gf-po-3.0.1 (21 października).

## Budynki gildii: mapa botów, potwory, powód odmowy (2.37.2)

- `MT2009_PLUS_BOT_NAV_GUILD_BUILDINGS_V1` (declare, define, show, destroy) (`building.h`, `building.cpp`): `CObject::Show`
  (po oznaczeniu ATTR_OBJECT) i `CObject::Destroy` (po zdjęciu) wołają `g_pfnMt2009ObjectAreaChanged` z prostokątem,
  który obejmuje wszystkie komórki budynku (suma czterech wartości regionu z `object_proto` + 100 – `ForAttrRegion`
  przy obrocie o 90° zaczepia ślad w rogu, nie w środku). Nakładka botów (`playerbot_navigation.h`) ustawia ten
  wskaźnik i odświeża w tym prostokącie siatkę tras (komórki, odstęp od ścian, składowe, regiony i przejścia HPA
  dotkniętych klastrów). Wcześniej siatka znała tylko budynki stojące przy jej zbudowaniu.
- `MT2009_PLUS_GUILD_BUILDING_CLEAR_V1` (move, show) (`building.cpp`): potwór stojący na komórce, którą nowy budynek
  właśnie zablokował, jest przestawiany (`Show`) na najbliższe wolne miejsce (pierścienie co 50 jednostek, 16 kierunków).
  `RequestCreateObject` nie liczy potworów jako przeszkody, więc wcześniej zostawały zamknięte w ścianach.
- `MT2009_PLUS_GUILD_BUILD_REFUSE_MSG_V1` (declare, who, globals, reasons, tell) (`building.h`, `building.cpp`, `cmd_gm.cpp`):
  `RequestCreateObject` zapisuje powód odmowy (poza terenem, inny budynek, ktoś stoi w miejscu budynku – z imieniem),
  a `/build c` mówi go liderowi (wcześniej tylko serwer testowy dostawał komunikat) i zapisuje w syslog
  (`BUILD: ... refused ... reason`). Boty (bot sam schodzi z budynku), zwierzaki i wierzchowce nie blokują już budowy.

## Obrócone budynki gildii (MT2009_PLUS_GUILD_ROTATE_V1)

- `MT2009_PLUS_GUILD_ROTATE_V1` (footprint, destroy, show, who, who test, land, check, people) (`building.cpp`):
  teren pod obróconym budynkiem liczony tak, jak klient go rysuje (obrót wokół punktu budynku, ten sam
  kierunek co `RegenNPC` i stara kontrola terenu). `SECTREE_MANAGER::ForAttrRegion` obracał ślad źle:
  przy 90° i 270° kładł obrócony prostokąt od rogu nieobróconego (pół budynku w bok), przy innym kącie
  zamieniał szerokość z wysokością i brał tylko część budynku (kamień przy 43°: 8 z 25 komórek, Insygnia –
  nic). Skutek: Kowal Zbroi obrócony o 90° 60 jednostek od Kwatery Głównej (z lewej albo od góry) był
  odrzucany („W tym miejscu stoi juz inny budynek”), a obrócony kamień zostawiał większość swojej
  powierzchni wolną dla następnych budynków i przejścia. Teraz komórka należy do budynku, gdy jej środek,
  obrócony z powrotem o `zRot`, leży w `lRegion` powiększonym o pół komórki; to samo przy sprawdzaniu
  (`RequestCreateObject`), oznaczaniu (`Show`) i zdejmowaniu (`Destroy`). Kontrola osób (`FIsIn`) pyta
  o obrócony budynek, kontrola terenu gildii bierze wszystkie cztery obrócone rogi (dwa dawne pozwalały
  obróconemu budynkowi wystawać poza teren). Budynek bez obrotu (`zRot` = 0) idzie dokładnie starą drogą
  (`ForAttrRegion`), komórka w komórkę. Po restarcie `FinalizeBoot` pokazuje każdy budynek nową metodą,
  więc `Destroy` zdejmuje te same komórki, które `Show` oznaczył. Klient bez zmian.

## Kamienie Metin i żyły z przedmiotów (MT2009_PLUS_SUMMON_STONE_V1, linia Yohary)

- `MT2009_PLUS_SUMMON_STONE_V1` (helpers, dungeon, spawn) (`char_item.cpp`): te same trzy zmiany co w 2.38.1
  (gałąź 2.x, commit e00d1c1c). Dotyczą wpisów `mob` z `special_item_group`, czyli potworów przywołanych z
  przedmiotu (`ITEM_GIFTBOX`: 71080–71082 Kamień Metin (Słaby/Średni/Silny), także z pudełek Dzieci Kwiaty
  83023–83027; 71057–71067 zwoje przywołania żył i Sterty Muszli). Rodzaj potwora: kamień = `mob_proto` typu
  `CHAR_TYPE_STONE`, żyła = `mining::IsVeinOfOre` (na Yoharze także żyły jadeitu 30310–30313).
  - **spawn**: po `SpawnMob` kamień albo żyła dostaje własne zdarzenie (`mt2009_summon_lifetime_event`, VID + rasa,
    bez wskaźnika) i po 15 minutach jest usuwana (`M2_DESTROY_CHARACTER`), o ile wciąż istnieje i żyje. Żyle
    anulowany jest losowy koniec silnika po 7–15 minutach (`kill_ore_load_event`), więc stoi dokładnie 15 minut;
    żyły z respawnu zachowują 7–15 minut.
  - **dungeon**: przed otwarciem pudełka – jeśli grupa (także zagnieżdżone `s<grupa>`) przywołuje kamień albo
    żyłę, a postać jest w lochu (`GetDungeon()`, indeks mapy ≥ 10000 albo wspólna mapa lochu), przedmiot się nie
    otwiera i nie znika: „Nie mozesz przywolac kamienia Metin w lochu.” / „Nie mozesz przywolac zyly w lochu.”.
    Wspólne mapy lochów: lista `Mt2009PlusDungeonNoFade` (66 – parter Wieży Demonów, 208, 216, 351, 352,
    363–366) i na Yoharze dodatkowo Jaskinie Gnolli (382–384, wspólne piętra labiryntu) oraz hala wejściowa
    Wieży Sung Mahi (386). Pozostałe lochy Yohary (Hydra 367, Erebu, Meley, Atlantyda, wieża 387, Świątynia
    Węży, Głębie, PB / SZC) są wyłącznie instancjami (≥ 10000). Drop w lochach dalej celowo nie patrzy na
    różnicę poziomów.
- `MT2009_PLUS_SUMMON_STONE_V1` (quest lifetime) (`char_item.cpp`) i (quest decl, quest, quest table)
  (`questlua_global.cpp`): dwie funkcje questów dla przedmiotów Yohary, które stawiają kamień albo żyłę przez
  `spawn_mob`:
  - `set_summon_lifetime(vid)` – to samo 15-minutowe zdarzenie dla kamienia albo żyły o tym VID (żyle anuluje
    losowe 7–15 minut); dla innego potwora nic nie robi i zwraca `false`;
  - `summon_blocked_here()` – `true` w lochu według tej samej reguły co pudełka.
  Używają ich `yohara_mapy4.quest` (72339 Kamień Metin z Yohara) i `yohara_mapy2.quest` (72354 Przenośna Żyła
  Jadeitu): odmowa w lochu przed `spawn_mob`, `set_summon_lifetime(vid)` zaraz po nim.
- Kamienie z respawnu, kamienie lochów (`d.spawn_mob`), żyły botów, zwoje bossów (71036–71043) i przedmioty
  Wielkanocy 50180/50181 bez zmian. Klient bez zmian.

## Łowienie bez questu i karty (MT2009_PLUS_FISHING_FREE_V1, linia Yohary)

- `MT2009_PLUS_FISHING_FREE_V1` (level, no introduction, no card) (`char.cpp`, `CHARACTER::fishing()`): łowienie od
  30 poziomu, bez ograniczeń czasu i liczby. Poniżej 30 poziomu komunikat „Możesz łowić ryby od 30 poziomu.” (wcześniej
  cicha odmowa). Nie jest już sprawdzana flaga `fishing_onboarding.completed` (quest wprowadzający Rybaka, którego
  obsługa znika w Dockerfile gry) ani założona Karta Wędkarska (27620). Wędka, przynęta, woda i łowiska w trzech
  pierwszych wioskach (1, 21, 41) bez zmian. `apply.sh` usuwa kartę ze sklepu specjalnego Rybaka (9009) i jednorazowo
  z ekwipunków (`fishing_free_cards_gone_v1`), boty (`playerbot_activities.h`) i towarzysz już jej nie kupują/nie wymagają.
- `MT2009_PLUS_SHOP3_TOKEN_V1` (`cmd_general.cpp`, nakładka `mt2009_shop3_token.cpp`): link do ItemShopu z `/in_game_mall` (Shift+F12, przyciski ItemShop) niesie przy każdym otwarciu świeży token konta i postaci w grze – `aid`, `ts`, `n`, `tok` = HMAC-SHA256 (klucz `M2_SHOP3_TOKEN_SECRET`, a bez niego wyprowadzony z `M2_DB_PASSWORD`; nigdy hasło konta). Sklep (`shop3/include/functions/game_login.php`) przyjmuje go przez 120 s i tylko raz, wylogowuje stare sesje przeglądarki (także innego konta) i loguje na nowo, z nowym identyfikatorem sesji, dokładnie na konto i postać z tokenu. Nieważny link nie pokazuje żadnego konta, tylko „Otwórz sklep ponownie z gry”. Dotąd link był podpisany samym md5(pid, konto, „GF9001”) – ważnym na zawsze – a sklep przy linku, którego nie przyjął, zostawał przy sesji poprzedniego konta (gracz z kilkoma kontami widział sklep konta X na koncie Y).
