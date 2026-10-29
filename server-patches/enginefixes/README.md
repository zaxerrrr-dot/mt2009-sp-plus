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

## Kamienie Metin i żyły z przedmiotów (MT2009_PLUS_SUMMON_STONE_V1, 2.38.1)

- `MT2009_PLUS_SUMMON_STONE_V1` (helpers, dungeon, spawn) (`char_item.cpp`): dotyczy tylko wpisów `mob`
  z `special_item_group`, czyli potworów przywołanych z przedmiotu (`ITEM_GIFTBOX`: 71080–71082 Kamień Metin
  (Słaby/Średni/Silny), także z pudełek Dzieci Kwiaty 83023–83027; 71057–71067 zwoje przywołania żył i Sterty
  Muszli). Rodzaj potwora: kamień = `mob_proto` typu `CHAR_TYPE_STONE`, żyła = `mining::IsVeinOfOre`.
  - **spawn**: po `SpawnMob` kamień albo żyła dostaje własne zdarzenie (`mt2009_summon_lifetime_event`, VID + rasa,
    bez wskaźnika) i po 15 minutach jest usuwana (`M2_DESTROY_CHARACTER`), o ile wciąż istnieje i żyje. Zdarzenie
    należy do potwora, nie do gracza – teleport, wylogowanie ani koniec lochu (potwór już nie istnieje) niczego
    nie psują. Gracz dostaje linię na czacie. Żyła ma w silniku własny losowy koniec po 7–15 minutach
    (`kill_ore_load_event`, `char.cpp`) – przywołanej żyle jest on anulowany, więc stoi dokładnie 15 minut; żyły
    z respawnu zachowują 7–15 minut.
  - **dungeon**: przed otwarciem pudełka – jeśli grupa (także zagnieżdżone `s<grupa>`) przywołuje kamień albo
    żyłę, a postać jest w lochu (`GetDungeon()`, indeks mapy ≥ 10000 albo wspólna mapa lochu z listy
    `Mt2009PlusDungeonNoFade`: 66 – parter Wieży Demonów, 208, 216, 351, 352, 363–366), przedmiot się nie otwiera
    i nie znika: „Nie mozesz przywolac kamienia Metin w lochu.” / „Nie mozesz przywolac zyly w lochu.” (raz na
    sekundę, `MT2009_PLUS_PULSE_CHEST_NOTICE`). Ten sam warunek w gałęzi `MOB` zatrzymuje przywołanie z grupy
    otwartej przez quest. Drop w lochach dalej celowo nie patrzy na różnicę poziomów.
  - Kamienie z respawnu, kamienie lochów (`d.spawn_mob`), żyły botów (`playerbot_mining.h`) i zwoje bossów
    (71036–71043) bez zmian.
