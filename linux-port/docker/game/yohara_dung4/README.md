# Yohara – Jaskinie Gnolli i Wieża Sung Mahi (MT2009_PLUS_YOHARA_DUNG4_V1)

Decyzja właściciela 14.10.2026 (`cache/yohara/decyzje.md`): „Jaskinie Gnolli 1/2/3 i Wieża Sung Mahi – dodać”,
wszystko wg pl-wiki, czego brak – wg wiki TR. Pliki tego katalogu robią `tools/yohara_dung4/gen_ydung4_maps.py`
(mapy, grupy, `spawned.txt`) i `tools/yohara_dung4/gen_yitems_d4.py` (drop, skrzynie); wiersze potworów –
`tools/yohara_dung4/gen_ydung4_sql.py` (`mariadb/playerbot/yohara_dung4.sql`, żywioły `yohara_dung4_zywioly.sql`),
przedmioty – `yohara_items_d4.sql`. Rdzeń: Yohara (game3). Klient: `client-patches/client-2.0.30/tools/ydung4`.

| indeks | miejsce | folder (GF/Owsap) | rodzaj | spawny |
|---|---|---|---|---|
| 382 | Jaskinie Gnolli (pierwszy poziom) | metin2_map_maze_dungeon1 (3×3) | mapa (`jaskinie_gnolli`) | punkty Owsapa, potwory wg wiki |
| 383 | Jaskinie Gnolli (drugi poziom) | metin2_map_maze_dungeon2 (3×3) | mapa | jw. |
| 384 | Jaskinie Gnolli (trzeci poziom) | metin2_map_maze_dungeon3 (3×3) | mapa | jw. |
| 386 | Wieża Sung Mahi – hala | metin2_map_smhdungeon_01 (1×1) | mapa | NPC z punktów GF |
| 387 | Wieża Sung Mahi | metin2_map_smhdungeon_02 (2×2) | loch (`wieza_sung_mahi`) | quest |

**Baza wieży**: GF ma 947200 614400 – u nas to Komnata Wiedzy (`plechito_chamber_of_wisdom`), a klient rozpoznaje
mapę po bazie. Wieża stoi na **998400 614400** (wolne w każdej naszej mapie, każdym worktree i w kliencie GF) – serwer
(`Setting.txt`) i klient (`setting.txt`, `atlasinfo.txt`) mówią to samo.

## Jaskinie Gnolli
- Wejście: Halabardnik (20836) w Dongan (990,973) – od 1. Poziomu Czempiona, jedna Przepustka (71095 / 71130) za
  wejście. Labirynt portali GOTO wg punktów klienta GF (10901–10924, 10931–10954, 10961–10984; nazwy = cele, Owsap).
  Odcinek 2 (20838) i Odcinek 3 (20839) prowadzą niżej bez powrotu; Wyjście (20837) i Dongan (20840) – do Dongan.
- Potwory poziomów wg wiki (grupy 9230–9244 na 245–255 punktach Owsapa – jego grupy nie wystawiały Ahtrinów 2. poziomu
  ani Szpiega/Wiedźmina/Komendanta 3.), bossowie na punktach Owsapa co 1 h / 2 h / 3 h (TR), żywioły wg wiki.
- Drop wg wiki (Talizmany Woli, płyty, Róg Trolla, Twarda Skóra, Wzór Rękawicy, Ziemne Pnącze, Żółty Lśniący
  Odłamek; bossowie – skrzynie: Mistrza Gnolli, Mistrza Ahtrina, Zdobiona Złotem ×3, Labiryntowa – zawsze).
- Śmierć: po wstaniu powrót do Dongan. Panel lochów: `gnolle` (Ahtrin Wielki Mistrz (mrok)).

## Wieża Sung Mahi
- Wejście Piekielnej Wieży (4019) w Seoganland (76,1459) → hala; w hali portal 4020: wybór odblokowanego piętra,
  Sztandar Czaszki (70401) za wspinaczkę, sam (od `MT2009_PLUS_SMH_TOWER_V3` – bez drużyny); Wyjście (10126) do
  Seoganland.
- Postęp pięter (`MT2009_PLUS_SMH_FLOORS_V1`, 21.10.2026): ukończone piętro, czas i nagroda zapisują się przy
  zabiciu bossa piętra (zdarzenie `kill`; zegar lochu nie ma postaci i `q.begin_other_pc_block` w nim nie działa –
  wcześniej nic się nie zapisywało); portal hali: „Piętro N” albo „Wybierz piętro” – lista (dziesiątki, potem
  piętro) wszystkich ukończonych i następnego, 1 Sztandar Czaszki za wspinaczkę.
- Fale (`MT2009_PLUS_SMH_WAVES_V1`, 21.10.2026): pokonana fala – następna od razu (zegar co 1 s; odstęp fali to już
  tylko najdłuższe czekanie, gdy grupa żyje); w misji klucza i pieczęci potwory płyną do końca misji.
- Sztandar Czaszki użyty z ekwipunku (`MT2009_PLUS_SMH_BANNER_V1`, 21.10.2026): opis i droga do hali wieży (warunki
  Wejścia), sam nie znika; przedmiot questowy bez handlu i magazynu (wiki; `tools/yohara_items/gen_yitems2.py`).
- 50 pięter × 3 etapy (sale i punkty z questów Amerii): fale; jedna z 7 misji wiki; fale + boss (Wóżbit, co 5. piętro
  Wielki Mistrz, co 10. Książę/Czarnoksiężnik); co 20 s gałęzie z ziemi (podwójne obrażenia na 10., 20. … piętrze);
  żywioł piętra po kolei, co 10. wszystkie; losowy bonus/klątwa na każdy etap (afekty 1847/1849, łatka
  `server-patches/wiezasm`); Wola SungMa piętra (`d.set_sungma`, nakładka `playerbot_champion.cpp`).
- Handlarka (9014) w hali: mikstury wieży 70390–70395 po 50 i 200 sztuk, ceny wiki (sklep 9552 w
  `yohara_items_d4.sql`, `MT2009_PLUS_SMH_SHOP_V1`); działają tylko w wieży (387) – łatka `server-patches/wiezasm`.
- Nagrody pięter z tabeli wiki raz na sezon (miesiąc); odblokowanie i czasy – też na sezon. Potwory wieży nie dają
  doświadczenia czempiona (wiki: 0). Panel lochów: `wieza_smh`.
- `MT2009_PLUS_SMH_TOWER_V3` (właściciel 28.10.2026, wg pakietu wieży i poradnika „YOHARA GUIDE #4”):
  - **tylko w pojedynkę** – bez drużyny, wierzchowca i przemiany (wejście; w wieży co 3 s zdejmowane); bot tylko własną wspinaczką rdzenia (`MT2009_PLUS_BOT_WIEZA_V1`,
    `playerbot_dgrun_wieza.h`: te same warunki, timery `wieza_sung_mahi_dgrun` / `_dgrun_next`);
    wspinaczka należy do gracza, który ją zaczął (flaga `owner`); start z jego własnego piętra (`start_floor`);
  - **śmierć = koniec wspinaczki**: `when die` – okno porażki w kliencie, po 3 s powrót do hali (`d.kick_dead`);
  - **okno wieży** przy portalu (klient `uiwiezasm.py`, uiscripty GF `sungmaheetowerenter` /
    `sungmaheetowerinformationboard`): 50 pięter z gwiazdką ukończonych w sezonie, nagrody (5 slotów) i żywioł,
    mój najlepszy czas i miejsce w rankingu, „Wejdź” (najpierw piętro niżej); rozmowa „(rozmowa)” – stary wybór;
  - **tablica w wieży** zamiast minimapy: piętro, etap i 3 ikony ukończonych etapów, cel etapu (przewijany), czas,
    X z potwierdzeniem, bonus/klątwa etapu z ikoną; dane liniami `WSM` (cmdchat), kliknięcia – zdarzenie `button` +
    `input()` (jak Sklep Gaya);
  - bonus/klątwa etapu w flagach lochu (`fx_kind`, `fx_idx`, `fx_until`) – wraca po ponownym zalogowaniu;
  - **unikanie ataków** wg poradnika: 60 s, Niszczyciele biegną do gracza i ładują mały krąg / pojawiają się i ładują
    duży krąg, potem znikają; trafienie przy pełnym PŻ → 1 PŻ, przy niepełnym → śmierć; co 20 s średni krąg pod
    graczem: −50% PŻ i zamęt; etap kończy się, gdy potwory przestają przybywać (nie od zabójstw);
  - 3. etap: co 20 s średni krąg (−50% PŻ i zamęt zamiast 15/30% i oplątania); bossowie: Książę (Tower Tyrant 7610)
    i Wróżbit (Tower Necromant, wilk żywiołu + 5: 7555/7562/7569/7576/7583/7590), na 10./20./…/50. piętrze Książę
    Śmierci (7612) i trzech Wróżbitów różnych żywiołów; umiejętności: siedem kręgów (Książę – Wola SungMa SIŁA −32
    na 7 s, afekt 1851; Wróżbit – ogłuszenie) i atak w linii (70% maks. PŻ);
  - zamęt = ogłuszenie (afekt 1850 z flagą `AFF_STUN`, 2 s) – silnik nie ma losowego ruchu postaci;
  - klątwa (misja 7): +1 stopień co 10 s (było co 20 s), od zera na każdym piętrze;
  - łucznicy budzą się też, gdy kamień demonów padnie w jednym takcie zegara;
  - sezon = miesiąc czasu polskiego z czasem letnim (Europe/Warsaw; było stałe UTC+2);
  - nagrody pięter do **Magazynu ItemShop** (`player.item_award`, `mall=1`, `why` `smh_<sezon>_<pid>_<piętro>_<k>`),
    flaga sezonu dopiero po udanym zapisie – nic nie ginie przy pełnym ekwipunku;
  - **ranking pięter** (`player.wieza_smh_rank`, `mariadb/playerbot/wieza_smh_ranking.sql`): najlepszy czas na piętrze
    w sezonie; po końcu miesiąca 1. miejsce każdego piętra dostaje Skrzynie Triumfu (50249; 1 + piętro/10, na
    10./20./… piętrze 5 × piętro/10 – jak oryginał) do Magazynu ItemShop, raz (`player.wieza_smh_season`, GET_LOCK) –
    rozliczenie przy wejściu do hali;
  - ranking tygodniowy (`d.update_ranking("wieza_smh")`) – raz na wspinaczkę, przy pierwszym zdobytym piętrze.

Uproszczenia: brak zakazu innych przedmiotów w wieży, Skrzynki Pocztowej; z nagród pominięte Małe Błogosławieństwo,
Błogosławieństwo, Spirala Czasu, Akcja Piekielnej Wieży (brak systemów); bossowie rzucają kręgi wokół gracza (quest nie
zna miejsca bossa bez zmiany silnika); potwory unikania ataków (Niszczyciele) atakują też zwyczajnie (ich `mob_proto`
bez zmian); w jaskiniach brak zakazu zwojów/pierścieni teleportu. Kręgi i klątwa ranią przez
`d.zone_attack`/`d.zone_hurt` (`server-patches/strefy`), a bez nich – ostrzeżenie i 50% PŻ, gdy gracz nie odszedł.
