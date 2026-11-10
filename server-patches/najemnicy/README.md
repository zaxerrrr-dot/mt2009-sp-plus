# najemnicy – Najemnicy, etap 1 (rdzeń), etap 2 (ekwipunek), etap 3 (mapy, rozkazy, lochy) i etap 4 (mechanika lochów)

`MT2009_PLUS_NAJEMNICY_V1` (etap 1), `MT2009_PLUS_NAJEMNICY_V2` (etap 2, ekwipunek), `MT2009_PLUS_NAJEMNICY_V3`
(etap 3: powrót po zmianie rdzenia/kanału i po zalogowaniu, rozkazy, lochy z graczem jako liderem) i `MT2009_PLUS_NAJEMNICY_V4`
(etap 4: mechanika lochów jak w wyprawach botów, powrót do grupy w środku lochu) i `MT2009_PLUS_NAJEMNICY_V5` (etap 5,
uwagi właściciela z 10.11.2026: powrót po zmianie kanału, „Stój tutaj” po wezwaniu, zakładka „Najemnicy” w oknie
Kolekcjonera, progi z panelu – sekcja „Etap 5” na końcu) – decyzje właściciela z 8.11.2026,
plan: `/opt/metin2/cache/yohara/najemnicy-plan.md`.
Stała drużyna botów gracza: od 80 poziomu gracz tworzy najemników (klasa, droga, płeć, imię), wzywa ich do swojej
grupy, a oni chodzą za nim i walczą. Za każdego wezwanego płaci ze skarbca najemników.

Cała logika jest w nakładce `linux-port/overlays/playerbot/src/game/src/playerbot_najemnicy.h` (opis w nagłówku pliku).
Quest: `linux-port/docker/game/quest/najemnicy.quest` (list „Najemnicy”). Tabele: `linux-port/docker/mariadb/playerbot/najemnicy.sql`.
Panel Seban: `Wydarzenia → Najemnicy` (`najemnicy.py`). Ta łatka dodaje tylko komendę, haki silnika i (etap 2)
funkcję questa `pc.is_najemnik()`.

**Nakładana po `pvpfan`** (kotwice to wiersze PVP Fan w `cmd.cpp` i `battle.cpp`). Linux/VPS:
`python3 apply_najemnicy.py <game/src>`; Windows: `Apply-NajemnicyPatch.ps1`. Edycja już nałożona jest pomijana;
edycja, której stary kod nie występuje dokładnie raz, zatrzymuje całość. Przy wdrożeniu dopisać `najemnicy`
do listy łatek **za** `pvpfan` (w `yohara-deploy.sh` na końcu listy).

| Plik | Co |
|---|---|
| `cmd.cpp` | `ACMD(do_najemnicy)` → `PlayerBotNajemnicyCommand`, wiersz tabeli `najemnicy` (GM_PLAYER; część GM sprawdza GM_HIGH_WIZARD sama) |
| `battle.cpp` | `battle_is_attackable`: `NajemnicyBlockAttack` – najemnik nie bije żadnej postaci i żadna postać nie bije jego, chyba że ich gildie mają ze sobą wojnę |
| `char_battle.cpp` | `CHARACTER::ItemDropPenalty`: `NajemnikNoItemDrop` – śmierć najemnika nie gubi przedmiotów |
| `char_item.cpp` | (V2) `CHARACTER::PickupItem`: `NajemnikMayTakePeopleLoot` – najemnik podnosi swoją część „łupu ludzi” z bossów (inne boty dalej nie) |
| `questlua_pc.cpp` | (V2) `pc.is_najemnik()` → `IsNajemnikCharacter` – questy lochów liczą najemnika do „ludzi” przy nagrodach |

## Jak to działa (etap 1)

- **Postać najemnika** tworzy gra (nie panel): konto `playerbot_njNNNN` (hasło `!`, status BLOCK – nikt się tam nie
  zaloguje), postać z wybraną klasą, płcią, drogą i imieniem (litery i cyfry, 3–16 znaków, filtr słów, imię wolne na
  serwerze), wiersz w `player.najemnicy`. Najemnik nie jest w `common.playerbot_seed_state`, więc pula botów go nie zna
  (nie poluje, nie handluje, nie ma go w rankingach, w spisie botów, w SM botów ani na czacie).
- **Odblokowanie i miejsca – Kolekcjoner Najemników** (decyzja właściciela z 8.11.2026, ostatnia sekcja planu):
  każde z 6 zadań daje kolejny próg, który działa dopiero od swojego poziomu – 1 zadanie + 80 poz. → 2 najemników,
  2 + 85 → 3, 3 + 90 → 4, 4 + 95 → 5, 5 + 100 → 6, 6 + 105 → 7. Zadania zrobione wcześniej czekają na poziom.
  Okna Kolekcjonera i oddawania przedmiotów **nie ma** w etapie 1 (osobny etap z łatką klienta). Licznik ukończonych
  zadań: flaga questa `najemnicy.tasks` (podniesie ją quest Kolekcjonera) albo wiersz `player.najemnicy_unlock.tasks`
  (GM i panel) – liczy się wyższa wartość (wyższy wiersz jest kopiowany na flagę). Flaga testowa
  `m2_najemnicy_free_unlock` = 1 liczy każdemu 6/6 (tabela poziomów dalej decyduje).
- **Wezwanie:** loguje się obok gracza (na jego rdzeniu i kanale; to samo wejście co PVP Fan), dołącza do jego grupy
  (grupa tworzy się sama), chodzi za nim i walczy jak Towarzysz: cel gracza, to, co atakuje gracza lub jego, potem
  potwory obok. Szaman buffuje gracza. Swój drop (część drużyny, która przypadła jemu) podnosi do swojego plecaka.
- **Poziom = poziom gracza**, statystyki rozdzielane pod drogę, umiejętności „połowa” gracza od M1
  (P → G1, M4 → M2, M1 → M1; najlepsza umiejętność gracza → główna najemnika). Przeliczane przy wezwaniu i przy
  awansie gracza.
- **Opłata:** 5 kk/h za każdego wezwanego (flaga `m2_najemnicy_price_h`), pobierana co minutę ze skarbca (pierwsza
  minuta od razu przy wejściu). Ostrzeżenie, gdy zostaje ≤ 10 minut. Pusty skarbiec = wszyscy odchodzą.
- **Odchodzi:** odwołany, przy pustym skarbcu albo po wyłączeniu modułu. Wylogowanie gracza – odchodzi po 20 s, ale
  zostaje „wezwany” i wraca po zalogowaniu (etap 3). Zmiana rdzenia/kanału – od razu loguje się przy graczu w nowym
  miejscu (etap 3). Przejście gracza na inną mapę tego samego rdzenia (także do lochu) – najemnik idzie za nim.
- **Zasady:** brak handlu (wymiana anulowana od razu), sklepu i rynku; nie atakuje graczy poza wojną gildii swojej
  gildii. Może być w gildii gracza („Gildia” w liście albo zwykłe zaproszenie od gracza – tylko od niego); na mapę
  wojny gildii idzie tylko, gdy jest w gildii gracza. Doświadczenie: zwykły podział w grupie.
- **Śmierć:** bez utraty przedmiotów i doświadczenia, wstaje obok gracza po 30 s.
- **Ekwipunek:** w etapie 1 tylko przyciski listu („Daj mu rzecz” po numerze pola, „Zabierz wszystko”) – zostają;
  od etapu 2 jest okno (niżej). Przy pierwszym wejściu plecak nowej postaci jest czyszczony (żeby startowe przedmioty
  nie trafiały do gracza).
- **Zwolnienie:** wezwany najpierw oddaje wszystko; niewezwany musi nic nie mieć. Postać, konto i przedmioty usuwa gra
  20 minut po zwolnieniu.

## Etap 2 – ekwipunek (`MT2009_PLUS_NAJEMNICY_V2`)

- **Okno ekwipunku = okno dawnego Towarzysza** (`client-patches/client-2.0.30/root/uisidekickinventory.py`): to samo
  okno torby (obraz ekwipunku, 4 strony po 45 pól, yang, linie odpowiedzi serwera), ten sam panel kostiumów, ten sam
  protokół (`SidekickEqBegin/Item/Empty/End/Result`), przeciąganie, prawy klik i dwuklik. Dla najemnika: tytuł
  „Ekwipunek: <imię>”, na obrazie ekwipunku doszły **pas, talizman i rękawica** (także u Towarzysza), zamiast
  „Odepnij” jest **„Kostiumy”** (kostium, fryzura, skórka broni, pieczęć wierzchowca, szarfa), zamiast „Daj” yang jest
  tylko **„Weź”** (najemnik nic nie kupuje), pod spodem przycisk **„Zabierz wszystko”**. Nie ma alchemii (kamieni smoka
  nie da się przekazać) ani znaczników przypięcia (najemnik sam niczego nie zakłada ani nie zdejmuje).
- **Jak otworzyć:** klik na swojego wezwanego najemnika → na tablicy celu przycisk **„Ekwipunek”** (serwer co 20 s i przy
  każdej zmianie mówi klientowi, które postacie to twoi najemnicy: `NajemnikVids`; u najemnika nie ma „Pojedynek”,
  „Dodaj do znajomych”, „Zgłoś”) albo list „Najemnicy → Ekwipunek → Otwórz okno ekwipunku” (`/najemnicy okno <nr>`).
- **Co działa w oknie:** przeciągnij rzecz ze swojego ekwipunku na slot najemnika (zakłada) albo do jego plecaka; prawy
  klik na rzeczy w swoim ekwipunku przy otwartym oknie = daj najemnikowi; z okna do swojego ekwipunku = zabierz; prawy
  klik na rzeczy w jego plecaku = zabierz do siebie; dwuklik w jego plecaku = załóż; prawy klik na założonej = zdejmij do
  jego plecaka; przeciąganie w jego plecaku = przestawianie i łączenie stosów. Wybielacz/farba na fryzurę jak u
  Towarzysza. Komendy okna: `/najemnicy eq <nr> [1 | daj <twoje pole> <cel> | wez <skąd> <twoje pole> | ruch <skąd> <dokąd>
  | wszystko | yang wez <kwota>]` (pole torby 0–179, slot = 1000 + WEAR_*, −1 = gdziekolwiek).
- **Zasady:** tylko właściciel, tylko wezwany najemnik, tylko na tej samej mapie i do 50 m od niego (inaczej okno mówi
  „Podejdź bliżej”). Wymagania przedmiotu (klasa, płeć, poziom, statystyki, grupa pierścieni) sprawdzane jak dla
  zwykłej postaci, zanim rzecz opuści ekwipunek gracza. Cios w toku: rzecz czeka do 20 s i zostaje założona w pierwszej
  chwili, w której silnik pozwala (najemnik na ten czas nie zaczyna nowych ciosów). Rzeczy zostają na najemniku po
  wylogowaniu (zwykły zapis postaci) i należą do gracza: najemnik nic nie sprzedaje, nie wyrzuca, nie wymienia, nie
  odkłada do magazynu i nic nie traci przy śmierci; nic nie trafia do magazynów dodatkowego ekwipunku
  (`PlayerBotEkwRouteWindow`), a to, co tam było, wraca do jego plecaka. Logi przedmiotów: `NAJEMNIK_DAJ`,
  `NAJEMNIK_ZABIERZ`, `NAJEMNIK_ZALOZ`, `NAJEMNIK_ZDEJMIJ`; syslog `NAJEMNICY: eq …`.
- **Zużywalne rzeczy od gracza** (najemnik nigdy nic nie kupuje): mikstury PŻ/PE przy progach botów (65% PŻ, 30% PE;
  najpierw listy botów – czerwone, niebieskie, pieczone ryby, wino – potem każda inna mikstura gracza), auto‑mikstury,
  a w walce zielone i fioletowe mikstury, **rosy, Kryształ Energii** i inne wzmocnienia (soki, mikstury ataku/obrony/
  krytyka) – nie, gdy ten sam efekt już działa równie mocno; odmowę silnika ponawia po 30 s. Na mapie wojny gildii nie
  pije „obcych” mikstur PŻ (zasada botów).
- **Łup i nagrody do plecaka najemnika:** jego część dropu z zabójstw (jak w etapie 1), teraz także **„łup ludzi”** z
  bossów (silnik pozwala mu go podnieść); **nagrody lochów liczą najemnika jak postać** (`pc.is_najemnik()`): Razador,
  Nemere, Niebieski Smok (łup na ziemi wokół bossa, kolejno dla każdej postaci – najemnik podnosi swój), Ruiny
  Skorpiona, Starożytna Dżungla, Wzgórze Wukonga, Ruiny Atlantydy (pula skrzyń dzielona też na najemników – prosto do
  plecaka), Meley (Skrzynia Królowej od razu do plecaka), Świątynia Węży i Głębie (nagroda za bossa od razu do plecaka);
  **skrzynie Zodiaku** dostaje każda postać na piętrze, więc i najemnik. Pełny plecak: gracz dostaje co 5 min
  przypomnienie na czacie, a łup zostaje na ziemi.

## Komendy

Gracz (to samo robią przyciski listu): `/najemnicy` (lista), `wezwij <nr|wszyscy>`, `odwolaj <nr|wszyscy>`,
`wplac <yang>` (np. `50000000` albo `50kk`), `skarbiec`, `okno <nr>` (V2), `eq <nr> …` (V2, okno), `daj <nr> <pole>`,
`zabierz <nr>`, `rozkaz <nr|wszyscy> <za_mna|stoj|bij|sam|nie_podnos|podnos>` (V3), `powrot <0|1>` (V3),
`przybycie` (V3, quest przy logowaniu), `gildia <nr>`,
`gildia_wyjdz <nr>`, `zwolnij <nr> tak`, `stworz <rasa 0-7> <droga 1-2> <imię>`, `sync` (flagi listu).

GM (GM_HIGH_WIZARD): `/najemnicy odblokuj <nick> [1-6]` (zadania Kolekcjonera, domyślnie 6),
`/najemnicy zadania <nick> <0-6>`, `/najemnicy zablokuj <nick>` (= 0 zadań), `/najemnicy spis` (spis teraz w syslog).

## Przełączniki (flagi zdarzeń)

W grze `/eventflag <nazwa> <wartość>` albo w panelu (wiersz `player.quest`, gra czyta co 10 s):

- `m2_najemnicy_off` = 1 – nikt nie wzywa, wezwani odchodzą;
- `m2_najemnicy_free_unlock` = 1 – każdy ma 6/6 zadań Kolekcjonera (na testy; miejsca dalej wg poziomu);
- `m2_najemnicy_price_h` – opłata za godzinę za jednego najemnika (0 = 5 000 000).
- `m2_najemnicy_rejoin_off` = 1 – (V3) po zalogowaniu wezwani nie wracają sami (zmiana rdzenia/kanału – dalej wracają).

Logi: linie `NAJEMNICY:` w syslog rdzenia (powtarzalne – ograniczane), spis `NAJEMNICY: census` co 10 minut.

## Jak przetestować na serwerze testowym

1. Wdrożenie: łatka `najemnicy` za `pvpfan`, migracja `najemnicy.sql` sama przy starcie.
2. Odblokowanie: GM wpisuje `/najemnicy odblokuj <nick>` (6 zadań) albo `/najemnicy zadania <nick> 2` (albo
   `/eventflag m2_najemnicy_free_unlock 1` dla wszystkich, albo panel Seban → Najemnicy). Sprawdź tabelę: postać 85
   z 2 zadaniami ma 3 miejsca, z 6 zadaniami też 3 (poziom), postać 79 – 0 (brak listu).
3. List „Najemnicy” (przychodzi przy logowaniu od 80 poziomu): **Stwórz najemnika** – klasa, płeć, droga, imię.
   Sprawdź odmowę dla zajętego imienia i dla imienia z polskimi znakami/spacją.
4. **Skarbiec → Wpłać yang**: np. `50kk`. Na czacie stan i czas („wystarczy na …”).
5. **Wezwij** – najemnik pojawia się obok, dołącza do grupy (grupa tworzy się sama), poziom = twój, umiejętności
   połowa twoich (okno grupy / podgląd postaci). Biegnij – idzie za tobą; zaatakuj potwora – pomaga; stań w miejscu
   – walczy z potworami obok. Exp dzieli się w grupie.
6. Opłata szybciej: `/eventflag m2_najemnicy_price_h 600000` (10 000 yang/min) i mała wpłata, np. `100000` –
   po kilku minutach ostrzeżenie „zostało … min”, potem „skarbiec pusty” i najemnicy odchodzą. Wróć do `0`.
7. **Odwołaj** jednego i „Wszyscy”.
8. **Gildia**: gracz w gildii → „Gildia → Dołącz do mojej gildii” (albo zaproś najemnika zwykłym zaproszeniem do
   gildii). Zaproszenie od innej postaci – odmowa. Wojna gildii: najemnik w gildii idzie na mapę wojny i bije wrogów
   z gildii przeciwnej; bez gildii czeka poza mapą wojny i nie bije graczy nigdzie.
9. Śmierć: daj najemnikowi zginąć – po 30 s wstaje obok, nic nie traci.
10. **Ekwipunek → Daj mu rzecz do założenia** (np. broń dla jego klasy z pola 1) i **Zabierz wszystko**.
11. Wyloguj się – po ~20 s najemnicy znikają (syslog: `NAJEMNICY: dismissed … why=owner_gone`); od etapu 3 wracają
    po zalogowaniu (punkt 26).
12. **Zwolnij najemnika** – miejsce wolne; po 20 min postać znika z bazy (`retired character deleted`).
13. Panel Seban → Wydarzenia → Najemnicy: lista najemników graczy, skarbce, odblokowania, przełączniki.

### Etap 2 – ekwipunek (wymaga nowego klienta: łatka root z tej gałęzi)

14. Wezwij najemnika (np. Wojownik), stań obok i **kliknij go**: na tablicy celu jest przycisk **„Ekwipunek”** (nie ma
    „Pojedynek”/„Zgłoś”). Otwiera się okno „Ekwipunek: <imię>” – obraz ekwipunku z pasem, talizmanem i rękawicą,
    4 strony plecaka, yang, „Weź”, „Kostiumy”, „Zabierz wszystko”. To samo z listu: Najemnicy → Ekwipunek → Otwórz
    okno ekwipunku.
15. Przeciągnij ze swojego ekwipunku broń jego klasy na slot broni – zakłada (odpowiedź „Zalozone.” pod oknem,
    statystyki rosną). Spróbuj broni innej klasy i przedmiotu z za wysokim poziomem – odmowa z powodem, rzecz zostaje
    u ciebie. Załóż zbroję, hełm, tarczę, buty, bransoletę, naszyjnik, kolczyki, pas, talizman, pierścienie.
16. „Kostiumy”: przeciągnij kostium, fryzurę, szarfę i pieczęć wierzchowca na sloty panelu.
17. Prawy klik na założonej rzeczy – schodzi do jego plecaka; prawy klik w jego plecaku – wraca do ciebie; dwuklik w
    jego plecaku – zakłada. Przy otwartym oknie prawy klik na rzeczy w **swoim** ekwipunku – idzie do jego plecaka.
18. Daj mu do plecaka mikstury czerwone i niebieskie, rosy (np. 50821), Kryształ Energii 51002, pieczone ryby. Walcz
    (np. przy metinie): pije przy ~65% PŻ / 30% PE, w walce używa ros i kryształu (syslog `NAJEMNICY: potion` /
    `NAJEMNICY: buff item`, liczba sztuk w oknie spada). Nie kupuje nic (żadnej wizyty u NPC).
19. Odejdź dalej niż 50 m albo zmień mapę bez niego – okno pisze „Podejdź bliżej do najemnika”. Odwołaj go – „Ten
    najemnik nie jest teraz wezwany”.
20. Wyloguj się i zaloguj, wezwij go znowu – rzeczy dalej na nim. Pozwól mu zginąć – niczego nie traci.
21. Łup: zabij potwory w grupie – jego część dropu ląduje w jego plecaku (widać w oknie). Loch: Świątynia Zodiaku –
    Złota Skrzynia Zodiaku w jego plecaku; Razador/Nemere – jego część łupu z bossa podnosi on; Ruiny Skorpiona – pula
    skrzyń dzielona też na niego; Meley – Skrzynia Królowej w jego plecaku.
22. **„Zabierz wszystko”** – wszystko, co ma i nosi, oraz jego yang przechodzą do ciebie („Zabrano wszystko (N
    przedmiotow).”); przy pełnym ekwipunku część zostaje u niego.
23. Spróbuj handlu z najemnikiem – anulowany od razu (jak w etapie 1).

## Etap 3 – mapy, rozkazy, lochy (`MT2009_PLUS_NAJEMNICY_V3`)

Bez zmian w silniku: łatka `najemnicy` zostaje w wersji V2 (te same edycje), cała logika jest w nakładce
`playerbot_najemnicy.h`, w questach i w Pythonie klienta (bez zmian w exe). Nowe kolumny (`najemnicy.sql` i
`EnsureNajemnicyTables`): `player.najemnicy.summoned`, `order_mode`, `no_loot`, `player.najemnicy_vault.billed_until`.

### Powrót po zmianie rdzenia, kanału i po zalogowaniu

- **Zbiór wezwanych jest w bazie** (`najemnicy.summoned` = 1 od wezwania). Kasują go tylko: „Odwołaj”, pusty
  skarbiec, wyłączenie modułu, nieudane wejście (45 s). Wylogowanie gracza i zmiana rdzenia/kanału go **nie** kasują.
- **Zmiana rdzenia albo kanału:** stary rdzeń widzi gracza na innym rdzeniu (P2P) i od razu wylogowuje jego najemników
  (`why=owner_moved`; zostają w grupie gracza). Na rdzeniu docelowym quest „Najemnicy” przy `login` wysyła
  `/najemnicy przybycie`: wezwani, których tu nie ma, logują się obok gracza (to samo wejście co PVP Fan –
  `SpawnPvpFan` + `PlaceLoadingBot` na mapie gracza, także w instancji lochu). Próba co 2 s przez 90 s (stary rdzeń
  musi ich najpierw wypuścić). Na czacie nie ma „… jest przy tobie” (cichy powrót).
- **Opłata bez przerwy i bez podwójnej minuty:** `billed_until` = sekunda, do której minuta jest zapłacona; nowy rdzeń
  pobiera następną minutę dopiero wtedy. Opłata liczy się tylko, gdy najemnicy są w świecie.
- **Wylogowanie:** najemnicy odchodzą po 20 s (opłata staje). **Po zalogowaniu** wracają sami – czat:
  „[Najemnicy] Najemnicy wracają... (N)”. Gracz wyłącza to w liście: **Najemnicy → Lista i rozkazy → Powrót po
  zalogowaniu** (`/najemnicy powrot 0|1`, flaga questa `najemnicy.no_rejoin`); globalnie flaga zdarzenia
  `m2_najemnicy_rejoin_off` = 1. Przełącznik dotyczy tylko logowania – przy zmianie rdzenia/kanału wracają zawsze.
  „Logowanie” a „przenosiny” rozróżnia `billed_until`: zapłacona minuta skończyła się ponad 30 s temu = logowanie.
- Przed powrotem skarbiec musi mieć minutę dla wszystkich (inaczej: „Skarbiec … pusty – najemnicy nie wracają”, zbiór
  wezwanych kasowany). Na mapie wojny gildii powrót czeka (wracają przy następnym wejściu poza nią).
- **Przycisk „Ekwipunek” bez 20 s:** przy każdym wejściu gracza (logowanie, teleport, zmiana kanału) serwer od razu
  wysyła `NajemnikVids` i jeszcze raz po 3 s.

### Rozkazy

| Rozkaz | Słowo komendy | Co robi |
|---|---|---|
| **Za mną** | `za_mna` | jak dotąd: przy graczu, bije cel gracza, to, co atakuje jego lub gracza, i potwory obok |
| **Stój tutaj** (po pierwszym wezwaniu w sesji, V5) | `stoj` | **od V5 bierny:** stoi w miejscu, w którym stał w chwili rozkazu (albo wejścia), nic nie bije (także tego, co bije jego), nie używa umiejętności ani buffów (tylko mikstury PŻ/PE), nie podnosi łupu, wraca na miejsce, gdy go zepchnąć; nie teleportuje się za graczem na tej samej mapie (inna mapa – idzie za graczem i stoi w nowym miejscu) |
| **Bij mój cel** | `bij` | tylko cel gracza (także boss albo kamień tylko zaznaczony); bez celu – broni gracza i siebie |
| **Walcz sam w pobliżu** | `sam` | wszystko do 25 m od gracza (także bossy i kamienie), wraca do gracza dopiero powyżej 15 m |
| **Nie podnoś łupu** / **Podnoś łup** | `nie_podnos` / `podnos` | przełącznik łupu (niezależny od rozkazu) |

- Dla jednego najemnika albo dla wszystkich; zapamiętane w bazie (`order_mode`, `no_loot`) także po wylogowaniu.
- Skąd: **tablica celu** (klik na swojego najemnika → przycisk **„Rozkazy”** obok „Ekwipunek” – okienko z rozkazami dla
  niego, przełącznikiem łupu i rzędem „Wszyscy najemnicy”, obecny rozkaz jest podświetlony), **list** (Najemnicy →
  Lista i rozkazy → Rozkazy; lista pokazuje rozkaz każdego) albo komenda `/najemnicy rozkaz <nr|wszyscy> <słowo>`.
- `NajemnikVids` niesie teraz rozkaz i łup (`slot:vid:imię:rozkaz:łup`); stary klient czyta pierwsze trzy pola.

### Przechodzenie przez najemników

Jak przez dawnego Towarzysza i Buffi: klient (`sidekickcollision.py`) typuje swoich wezwanych najemników (VID-y z
`NajemnikVids`) jako NPC na czas aktualizacji świata – gracz przez nich przechodzi; ten pod kursorem zostaje postacią
(klik działa). Tylko Python.

### Lochy (gracz jest liderem)

Najemnik wchodzi do lochu za graczem (na tym samym rdzeniu: od razu na jego mapę; na innym rdzeniu: powrót jak wyżej,
wprost do instancji). W instancji lochu (`IsPlayerBotPartyDungeonMap`) z graczem robi to, co boty w grupie gracza
(`playerbot_party_dungeon.h`) i to, co umieją skrypty botów:

- **przedmioty lochu** (`ManagePlayerBotPdgItems`): pieczęcie i klucze używa od razu, Złotą Zębatkę, Kamienie Maat,
  Kryształy Lodu i klucz Atlantydy oddaje NPC, Pierścień Smoczego Ognia (Meley), Ognistą Strzałę (Balathor);
- **klucze Yohary wg klasy** (`ManagePlayerBotYdgItems` na grupie gracza: najemnicy na miejscu + gracz): Mroźny Klucz
  używa Szaman, Klucz Lodowego Kwiatu Ninja albo Szaman – klucz innej klasy przechodzi do najemnika właściwej klasy (albo
  do gracza); Złota Zębatka, Kamień Maat, Gwiazda Północy do swoich NPC; podnosi klucze swojej klasy z ziemi.
  Gracz może też włożyć klucz do plecaka najemnika (okno ekwipunku) – najemnik go użyje;
- **walka w lochu**: „Za mną” – cel gracza, to, co atakuje, kamienie i potwory przy graczu (`PickPlayerBotPdgFoe`);
  „Walcz sam” – sam czyści loch wokół (`PickPlayerBotPdgSoloFoe`); „Bij mój cel” i „Stój” – jak na mapie. Zawsze
  z zasadami lochów: najpierw kamienie Niebieskiego Smoka, bez osłoniętych posągów Meley, bez Metinów Świątyni Węży
  poza kolejnością, bez jaj i Hwachy Balathora, bez bossów Zodiaku zostawionych graczowi;
- **nigdy nie wychodzi sam**: mapa gracza jest jego mapą (dogania gracza przeniesionego do innej sali), wychodzi
  z `d.exit_all` albo za graczem;
- jego plecak nie jest opróżniany na miejsce (boty sprzedają śmieci po kluczu – najemnik nie).

Questy (wejścia i logowanie):

- `when login` w instancji i w poczekalni lochów klasycznych i Arezzo (Razador, Nemere, Smok, Biblioteka, Wukong,
  Skorpion, Dżungla, Atlantyda) wyrzucał bota – najemnika już nie (`pc.is_najemnik()`); to samo Płaskowyż Iluzji
  (`przebudzeni_bossowie`). Świątynia Węży, Głębie i Meley przy logowaniu bota nic nie robią – najemnik zostaje.
- `d.new_jump_pids` przenosi tylko ludzi (bilety, klucze, limity dzienne płacą ludzie) – najemnicy wchodzą sami za
  graczem; liczą się jednak do warunków drużyny: **Głębie** (`party_min`/`party_max`), **Erebu** (`party_min`),
  **Przebudzeni Bossowie** („co najmniej dwóch”), **Ninja + Szaman** Strażnicy Nemere (Szczeliny i Przebudzeni),
  **Krypta Balathora** (członkowie gildii obok mistrza – najemnik w gildii gracza).
- Świątynia Węży: najemnik nie ma limitu ożywień (wstaje po 30 s przy graczu).

Stan każdego lochu po etapie 4 – tabela w sekcji „Etap 4” niżej.

### Jak przetestować etap 3 (nowy klient: łatka root z tej gałęzi; serwer: nakładka + questy, migracja sama)

24. **Powrót po zmianie kanału:** wezwij 2 najemników, zmień kanał (albo przejdź na mapę innego rdzenia, np. Yohara).
    Po wejściu najemnicy pojawiają się obok w ciągu kilku sekund, są w grupie. Syslog starego rdzenia: `dismissed …
    why=owner_moved`; nowego: `owner arrived … move=1`, `summoned … rejoin=1`, `entered … rejoin=1`. Skarbiec: ubywa
    dalej 1 minuta na minutę (nie dwie przy przejściu).
25. **Przycisk „Ekwipunek”/„Rozkazy” po teleporcie:** zaraz po wejściu kliknij najemnika – przyciski są od razu (bez
    czekania 20 s).
26. **Wylogowanie i logowanie:** wyloguj się, odczekaj ponad 1,5 min, zaloguj – czat „Najemnicy wracają... (2)”,
    najemnicy wchodzą obok. Lista → Powrót po zalogowaniu → „Nie wracają (wyłącz)”, wyloguj i zaloguj (po 1,5 min) –
    nie wracają; wezwij ręcznie; włącz z powrotem. „Odwołaj” przed wylogowaniem – po zalogowaniu nie wracają.
27. **Rozkazy:** klik na najemnika → „Rozkazy”. „Stój tutaj” – odejdź 30 m: stoi i bije potwory, które podejdą.
    „Bij mój cel” – zaznacz potwora daleko od innych: bije tylko jego. „Walcz sam w pobliżu” – czyści okolicę, także
    bossa/kamień. „Nie podnoś łupu” – łup leży. „Za mną” – jak zwykle. Rząd „Wszyscy najemnicy” zmienia wszystkich.
    Wyloguj/zaloguj – rozkaz zostaje (lista pokazuje „rozkaz: …”). Komenda: `/najemnicy rozkaz 1 stoj`.
28. **Przechodzenie:** wejdź w najemnika – przechodzisz przez niego (klient z tej gałęzi).
29. **Lochy:** z 2+ najemnikami: Nemere PB z Szamanem-najemnikiem – Mroźny Klucz (włóż mu albo niech podniesie) –
    syslog `BOT_YDG: used … name=<najemnik>`; Głębie z 1 człowiekiem + najemnicy (`party_min`); Szczelina Strażnica
    Nemere: gracz Wojownik + najemnik Ninja + najemnik Szaman – wejście przechodzi; Świątynia Zodiaku; Meley; klasyczny
    Razador/Nemere – najemnik oddaje zębatki/kryształy, które dropnie. Zaloguj się ponownie w środku lochu – najemnicy
    wracają do instancji (nie są wyrzucani). Syslog: `NAJEMNICY: dungeon …`, `PLAYERBOT_DUNGEON: party bot used/handed in`.

## Etap 4 – mechanika lochów jak w wyprawach botów (`MT2009_PLUS_NAJEMNICY_V4`)

Bez zmian w silniku i w kliencie: łatka `najemnicy` dalej ma tylko edycje V1/V2, wszystko jest w nakładce
(`playerbot_najemnicy.h`, drobne zmiany w `playerbot_dungeon_runs_ydg_glebie.h` i `playerbot_dungeon_runs_ydg_weze.h`)
i w `meley_dungeon.quest`. Klient (exe i Python) – bez zmian.

### Grupa gracza jako „wyprawa” dla skryptów botów

Drużyna gracza w instancji lochu jest dla skryptów wypraw botów osobną wyprawą (`GetNajemnicyDgRun`): lider = gracz,
członkowie = jego najemnicy w instancji + gracz, **ujemny numer wyprawy** – nigdy nie trafia do rejestru wypraw botów
(żaden planer, nadzór, wyciąganie z lochu ani „utknięcie” botów jej nie dotyka). Na tej podstawie najemnicy robią to,
co robią boty w swojej wyprawie, a rozmowy lidera (posąg Razadora, lew Nemere, Duch Sura, Portal i Kowal Świątyni Węży,
jajo Alastora, Dolnarr) robi gracz – to on jest liderem.

- **Cel etapu** (`PickNajemnikDgObjective`, rozkazy „Za mną” i „Walcz sam”): to, co bije lider wyprawy botów –
  Metiny/Królowe/Baronowa Biblioteki, Zapalnik/Metin/Razador, Szele/Filar/Nemere, kamienie Niebieskiego Smoka, muszle
  i Strażnicy Atlantydy, jaja/Idalle/posągi Meley, Uzdrowiciele i bossowie Erebu, potwory z kluczami, Metiny i bossowie
  lochów Yohary, Metin Świątyni Węży **tylko w kolejności**, Metiny Czasu, Wojownicy i Nethis, Alastor. Do 60 m od
  gracza i osiągalny; najpierw cel gracza (gdy jest celem etapu), w Meley najbardziej zbity posąg, potem ten w ręku,
  potem najbliższy. Gdy najemnik ma < 30% PŻ albo gracz < 40% PŻ – zwykła walka drużynowa (obrona gracza).
- Obowiązek z dala od gracza (komnata jaj, NPC po drugiej stronie sali, cel etapu) wstrzymuje „dociąganie” do gracza;
  w lochu dociąga dopiero powyżej 70 m (na zwykłej mapie 30 m).

### Loch po lochu

- **Schronienie Meley – role posągów** (jak w wyprawie botów `MT2009_PLUS_BOT_MELEY16_V1`, ale już od 2 najemników):
  Szamani (droga) – leczą i buffują drużynę; ćwierć najsilniejszych (min. 1) – **zabójcy jaj** (każdy swoje jajo, póki
  jaja stoją – tarcza posągów); od 4 najemników ćwierć Wojowników/Sur z największym PŻ – **straż magmy** (to, co bije
  drużynę; w etapach 2–3 tylko to, co bije Szamana – inaczej idzie na cel etapu); reszta z graczem – **drużyna posągu**
  (jaja, Idall, potem najbardziej zbity posąg). Role przeliczane, gdy zmieni się skład w instancji, i co minutę
  (syslog `NAJEMNICY: meley roles`). **Pierścienie:** pierścień z zabójstwa najemnika jest jego (quest daje go zabójcy-
  najemnikowi), najemnik go podnosi i w etapie 4 sam kładzie na statuę bez pierścienia (bez warunku odległości – jak bot).
  Pierścienie z zabójstw gracza są gracza (może je też włożyć najemnikowi do plecaka).
- **Głębie (Alastor) – jajo i portale:** komnata jaj jak w wyprawie botów – gdy Alastor się budzi, 1 najemnik (2 przy
  6–7 najemnikach; Ninja, Sura, Wojownik, najsilniejszy; nigdy gracz) idzie przez Kryształ (3971) i portal 3972 do
  komnaty i zbija Białe Jaja Smoka (najbardziej zbite najpierw), reszta bije Alastora; najemnik bez obowiązku, który
  znalazł się w komnacie, wraca portalem 3973. Wszyscy schodzą z kręgów na ziemi (kolce, Śmiertelny Chłód) – bez bonusów
  wypraw botów. Budzi Alastora gracz (lider dotyka Białego Jaja Smoka). Syslog: `NAJEMNICY: glebie`, `BOT_GLEBIE: egg
  duty / portal / dodge / egg run=-…`.
- **Świątynia Węży – klucze, klatki, kolejność:** Klucze Wężowe podnosi i oddaje właściwej Kolumnie (ta, gdzie stał Metin
  Czasu tej tury – flaga questa), Klucze do Więzienia oddaje kowalom w klatkach, Odłamki Węża – Głowie z kolejki
  (pozostałe trzyma na swoją kolej), Pył Wężowy z plecaka używa, dopóki zegar Portalu < 60 min (sam nie kupuje – daje
  gracz). Metiny Wężowe 3. poziomu tylko w kolejności (zły Metin nigdy nie jest celem, także „Bij mój cel”).
  Syslog: `BOT_YDG: weze handed in run=-… what=column|cage|head`, `NAJEMNICY: weze dust`.
- **Beran (PB i Szczelina):** Duch Sura bierze 3 Kręte Klucze od każdego **człowieka** – klucze, które podniosą
  najemnicy, oddają graczowi, dopóki ma mniej niż 3 (czat „… oddaje ci Krete Klucze”).
- **Krypta Balathora:** najemnik jest na liście graczy Krypty (jak bot w drużynie gracza) i polimorf lodu kończy od razu.
- **Powrót do grupy w środku lochu:** po zalogowaniu gracza w lochu (jego grupa zniknęła przy wylogowaniu) najemnicy
  wchodzą do instancji i **dołączają do grupy gracza** (grupa tworzy się sama). Silnik odmawia tylko zaproszenia
  (`PERR_DUNGEON` w `IsPartyJoinableMutableCondition`); `CParty::Join/Link` tego nie sprawdza – dołącza tylko najemnik,
  tylko do grupy swojego gracza i tylko w jego instancji, a licznik grupy w instancji (`CDungeon::IncPartyMember`) jest
  prowadzony tak, jak przy wejściu z grupą. Syslog: `NAJEMNICY: made a party … dungeon=<instancja>`, `joined the owner's
  party … dungeon=<instancja>`.

### Stan lochów (gracz + tylko najemnicy)

| Loch | Stan po etapie 4 |
|---|---|
| Świątynia Zodiaku | za graczem po piętrach, walka lochowa; posągi, armata i bossy zostawione graczowi (jak boty w drużynie), skrzynie każdej postaci – do przejścia |
| Nemere (klasyczny 352) | klucze 30760/30762 używa, Kryształy Lodu oddaje pieczęciom, cel etapu (Szele, Filar, Nemere); rozmowa z lwem/posągiem – gracz (lider) – do przejścia |
| Nemere PB / Szczelina | Mroźny Klucz (Szaman), Klucz Lodowego Kwiatu (Ninja/Szaman), Gwiazda Północy do Kostek, cel etapu; najemnik liczy się do Ninja+Szaman – do przejścia |
| Jotun PB / Zaklęty Las (SZC) | przedmioty i cele misji PB (Wojownik, Druid, Metin, Niszczyciel, Władca En-Tai, bossy); SZC – walka lochowa – do przejścia |
| Erebu | liczy się do `party_min`, najpierw Uzdrowiciele, potem Bagjanamu i Jotun Thrym; Kamień Driad płaci gracz – do przejścia |
| Meley | role (jaja, magma, leczenie, posąg), pierścienie z własnych zabójstw w etapie 4, Skrzynia Królowej w plecaku – mechanika kompletna (siła drużyny 8 osób zależy od sprzętu; boty mają w wyprawach bonus 80%, najemnicy nie) |
| Głębie (Alastor) | komnata jaj, portale, uniki stref, Alastor jako cel; budzenie – gracz (lider) – do przejścia |
| Krypta Balathora | najemnik w gildii gracza liczy się do członków, lista graczy Krypty i polimorf, strzały do Hwachy, jaja/Hwacha nie są celem; strzał z Hwachy i spychanie Ognistych Jaj – gracz (mistrz gildii). **Nie sprawdzone w grze** (kod przejrzany) |
| Razador (klasyczny i PB) | Zębatka i Kamienie Maat do Steli, cel etapu (Zapalnik, Metin, Razador); rozmowy z posągiem – gracz – do przejścia |
| Beran PB / Szczelina | Kręte Klucze do gracza (do 3), cel etapu (Yonghany, 4 Metiny, Beran-Setaou); Duch Sura – gracz – do przejścia |
| Wukong / Skorpion / Dżungla | pieczęcie fal używa, kamienie najpierw, przerwanie walki z bossem jak boty Arezzo – do przejścia |
| Atlantyda | klucz 30920 do zamkniętego Filaru, cel etapu (muszle, Strażnicy, Morkhot) – do przejścia |
| Niebieski Smok | najpierw kamienie, potem smok (cel etapu), łup – etap 2 – do przejścia |
| Świątynia Węży | klucze do Kolumn, klucze do klatek, odłamki do Głów, pył, Metiny w kolejności; rozmowy z Portalem i Kowalem – gracz – do przejścia |

### Jak przetestować etap 4 (serwer: nakładka + `meley_dungeon.quest`; klient bez zmian)

30. **Powrót do grupy w lochu:** wejdź z 3 najemnikami do dowolnego lochu (np. Razador), wyloguj się w środku, odczekaj
    ponad 1,5 min, zaloguj. Najemnicy wracają do instancji i w ciągu kilku sekund są **w grupie** (okno grupy, exp
    dzielony). Syslog: `made a party for owner=… dungeon=<instancja>`, `joined the owner's party … dungeon=<instancja>`.
    Wyjdź z lochu – grupa zostaje, brak `cannot find party` w syslogu.
31. **Meley:** 6–7 najemników (2 Szamanów, Wojownicy). Syslog `NAJEMNICY: meley roles … egg=… magma=…`. W etapie 2 jaja
    padają (zabójcy jaj), straż magmy bije potwory na Szamanach, posągi zbijane po kolei od najbardziej zbitego. Pierścień
    z zabójstwa najemnika (5% w etapach 1–2) – `PLAYERBOT_DUNGEON: party bot picked up … vnum=30340`; w etapie 4, gdy jaja
    padną – `party bot used … vnum=30340 … ok=1` i statua płonie.
32. **Głębie:** gracz + 3 najemników (w tym Ninja/Sura). Dotknij Białego Jaja Smoka. Syslog `NAJEMNICY: glebie … egg_duty=1`,
    `BOT_GLEBIE: egg duty run=-…`, `portal run=-… portal=3972`, `egg run=-…`; jeden najemnik bije jaja w komnacie, reszta
    Alastora, wszyscy schodzą z kręgów (`BOT_GLEBIE: dodge run=-…`). Po zabiciu Alastora wraca do gracza.
33. **Świątynia Węży:** gracz + najemnicy, daj jednemu kilka Pyłów Wężowych. Rozpocznij walkę u Portalu: pył się zużywa
    (`NAJEMNICY: weze dust`), na 3. poziomie najemnicy biją tylko Metin z kolejki (spróbuj „Bij mój cel” na złym Metinie –
    nie bije), na 5. oddają Klucze Wężowe Kolumnom (`weze handed in … what=column right=1`), na 6. klucze do klatek
    (`what=cage`), na 7. odłamki Głowom (`what=head`); Nethis – cel etapu.
34. **Beran PB:** najemnicy zabijają Yonghany i podnoszą Kręte Klucze – czat „… oddaje ci Krete Klucze: 1 (masz 1/3)”; przy
    3 kluczach u gracza przestają oddawać (trzymają resztę). Rozmowa z Duchem Sura otwiera Świątynię Smoka.
35. **Cel etapu:** Razador / Nemere / Biblioteka / Erebu – najemnicy na „Za mną” sami biją Zapalnik, Szele, Uzdrowicieli
    itd. (syslog `NAJEMNICY: dungeon goal … why=objective`). Gracz z < 40% PŻ – bronią gracza.
36. **Krypta Balathora** (gracz w gildii z najemnikami): po wejściu najemnicy są na liście Krypty (polimorf lodu znika po
    ~1,5 s), ładują strzały do Hwachy, nie biją jaj ani Hwachy.

## Co dalej

- Panel, spis, wiki, changelog (plan: etap 4 „Dopracowanie”).
- Kolekcjoner Najemników jest w osobnej łatce `server-patches/kolekcjoner` (okno, oddawanie przedmiotów 95%, stałe bonusy
  za zadania). Ukończone zadanie podnosi flagę `najemnicy.tasks` i wiersz `najemnicy_unlock.tasks` (GREATEST).

## Etap 5 – uwagi właściciela z 10.11.2026 (`MT2009_PLUS_NAJEMNICY_V5`)

Bez zmian w silniku (łatka `najemnicy` dalej V1/V2). Nakładka `playerbot_najemnicy.h`, quest `najemnicy.quest`,
klient (Python: `uinajemnicykolekcjoner.py`, `uinajemnicyrozkazy.py`, `uisidekickinventory.py`, `game.py`,
`interfacemodule.py`), panel Seban (`kolekcjoner_config.py`) i tabela progów z `kolekcjoner_najemnikow.sql`.

### 1. Najemnicy nie pojawiali się na nowym kanale – przyczyna i poprawka

Log testowy (9.11, 08:45): stary rdzeń `dismissed … why=owner_moved`, nowy `owner arrived … move=1`, `summoned … rejoin=1`
i **w tej samej sekundzie** `did not load in 45 s` + `dismissed … why=load_timeout`. Powrót (`ProcessNajemnicyRejoins`)
wzywa najemnika w trakcie przebiegu zegara modułu i zapisuje `askedAt = get_dword_time()` – kilka ms **później** niż
`dwNow` tego przebiegu. Porównanie `dwNow - askedAt > 45000` było na liczbach bez znaku, więc różnica „−3 ms” stawała się
~4 mld ms i ten sam przebieg odwoływał każdego wracającego najemnika jako „nie dotarł”; odwołanie kasowało też
`summoned`, więc już nie wracali. To samo trafiało powrót po zalogowaniu. Teraz porównania zegara (wejście, wstawanie po
śmierci, odejście gracza) są ze znakiem.

### 2. Domyślny rozkaz po wezwaniu: „Stój tutaj” (bierny)

- **Pierwsze „Wezwij”** danego najemnika w sesji logowania gracza ustawia mu „Stój tutaj” (zapisane w bazie,
  `order_mode=1`) i czat mówi „… stoi w miejscu – daj mu ekwipunek i wydaj rozkaz”. Najemnik nic nie bije, nie używa
  umiejętności ani buffów – gracz go ubiera i dopiero wysyła rozkazem.
- **Kolejne wezwania w tej samej sesji** zachowują ostatni rozkaz. **Powrót** (zmiana kanału/rdzenia, powrót po
  zalogowaniu) też zachowuje rozkaz – najemnik pracował, gdy gracz odchodził (np. rozłączenie w lochu).
- Sesja = klucz logowania z serwera autoryzacji (ten sam przy zmianie kanału i rdzenia, nowy przy każdym logowaniu);
  flagi questa `najemnicy.session` i `najemnicy.session_mask` (bit na miejsce). Syslog:
  `NAJEMNICY: first summon of the session pid=… order 0 -> 1`.

### 3–5. Okno: zakładka „Najemnicy” w oknie Kolekcjonera

List „Najemnicy” jest już tylko wejściem: klik → `/najemnicy panel otworz` → okno Kolekcjonera na zakładce
„Najemnicy”. Okno ma wygląd okna „Sesja farmienia” (pasek tytułu, płaskie zakładki, ramki, nagłówki, te same kolory).
Zakładka ma: miejsca (zajęte/dostępne) i wymaganie następnego miejsca (zadanie Kolekcjonera + poziom), tworzenie
najemnika (klasa, płeć, droga, imię), wiersz na każdego najemnika (twarz/klasa, droga, poziom, stan: niewezwany / w
drodze / przy tobie / padł, rozkaz, łup, gildia) z przyciskami **Wezwij/Odwołaj, Ekwipunek, Rozkazy, Łup, Gildia,
Zwolnij** (z pytaniem), skarbiec (stan, koszt na godzinę przy obecnych wezwaniach, na ile wystarczy, wpłata),
„Wezwij wszystkich” / „Odwołaj wszystkich” i przełącznik powrotu po zalogowaniu. Okno „Rozkazy” i przyciski okna
ekwipunku najemnika są w tym samym stylu.

Protokół (`CHAT_TYPE_COMMAND`): `NAJP begin <miejsca> <zadania> <poziom> <liczba> <opłata_h> <skarbiec> <wył> <powrót>`,
`NAJP tier <nr> <miejsca> <poziom>`, `NAJP merc <miejsce> <rasa> <droga> <imię hex> <stan 0-3> <rozkaz> <łup> <gildia -1/0/1>
<poziom>`, `NAJP end <otwórz 0|1>`. Klient: `/najemnicy panel` (stan + odświeżanie na żywo), `/najemnicy panel zamknij`,
a reszta to dotychczasowe komendy przez kolejkę komend klienta. Serwer odświeża zakładkę po każdej komendzie gracza,
wejściu, odejściu, śmierci i wstaniu najemnika, co minutę (opłata) i po ukończeniu zadania Kolekcjonera (raz na
sekundę zbiorczo).

### 6. Progi z panelu

Liczba miejsc liczy się z tabeli `player.najemnicy_kolekcjoner_tiers` (n‑te ukończone zadanie → tyle najemników od
poziomu), którą edytuje panel Seban (Wydarzenia → Najemnicy → Kolekcjoner). Gra czyta ją razem z flagami co ~10 s; pusta
tabela = tabela właściciela (1 + 80 → 2 … 6 + 105 → 7). Liczy się do 16 zadań; komendy GM `zadania <nick> <0-16>`.

### Jak przetestować etap 5 (serwer: nakładka + quest + migracja; klient: łatka root z tej gałęzi)

37. **Zmiana kanału:** wezwij 2 najemników, zmień kanał. W ciągu kilku sekund są obok, w grupie, z tym samym rozkazem.
    Syslog nowego rdzenia: `owner arrived … move=1`, `summoned … rejoin=1`, `entered … rejoin=1` – **bez**
    `did not load in 45 s`. To samo przy przejściu na mapę innego rdzenia i po wylogowaniu/zalogowaniu (po 1,5 min).
38. **Pierwsze wezwanie:** zaloguj się, wezwij najemnika – stoi („stoi w miejscu…” na czacie, w zakładce rozkaz „Stój
    tutaj”). Zaatakuj potwora obok niego / daj się bić – najemnik nie bije, nie buffuje (Szaman), nie podnosi łupu.
    Ubierz go (Ekwipunek), daj „Za mną” – walczy. Odwołaj i wezwij znowu – dalej „Za mną”. Wyloguj się, zaloguj,
    wyłącz powrót, wezwij – znów „Stój tutaj”.
39. **Okno:** kliknij list „Najemnicy” – otwiera się okno Kolekcjonera na zakładce „Najemnicy”. Sprawdź miejsca i
    „następne miejsce”, stwórz najemnika (zajęte imię – odmowa na czacie), wezwij/odwołaj (stan zmienia się sam w
    ~1 s), wpłać `10kk` (stan i czas skarbca od razu), rozkazy, łup, gildia (stan po ~2 s), zwolnij (pytanie).
    Zostaw okno otwarte – co minutę skarbiec maleje bez klikania. Zmień zakładkę na „Kolekcjoner” – odświeżanie staje.
