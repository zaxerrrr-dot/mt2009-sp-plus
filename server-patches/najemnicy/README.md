# najemnicy – Najemnicy, etap 1 (rdzeń) i etap 2 (ekwipunek)

`MT2009_PLUS_NAJEMNICY_V1` (etap 1) i `MT2009_PLUS_NAJEMNICY_V2` (etap 2, ekwipunek) – decyzje właściciela z 8.11.2026,
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
- **Odchodzi:** odwołany, gdy gracz wyloguje się albo przejdzie na inny rdzeń/kanał (po 20 s; ponowne
  wejście za graczem to etap 3), przy pustym skarbcu albo po wyłączeniu modułu. Przejście gracza na inną mapę
  tego samego rdzenia (także do lochu) – najemnik idzie za nim.
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
`zabierz <nr>`, `gildia <nr>`,
`gildia_wyjdz <nr>`, `zwolnij <nr> tak`, `stworz <rasa 0-7> <droga 1-2> <imię>`, `sync` (flagi listu).

GM (GM_HIGH_WIZARD): `/najemnicy odblokuj <nick> [1-6]` (zadania Kolekcjonera, domyślnie 6),
`/najemnicy zadania <nick> <0-6>`, `/najemnicy zablokuj <nick>` (= 0 zadań), `/najemnicy spis` (spis teraz w syslog).

## Przełączniki (flagi zdarzeń)

W grze `/eventflag <nazwa> <wartość>` albo w panelu (wiersz `player.quest`, gra czyta co 10 s):

- `m2_najemnicy_off` = 1 – nikt nie wzywa, wezwani odchodzą;
- `m2_najemnicy_free_unlock` = 1 – każdy ma 6/6 zadań Kolekcjonera (na testy; miejsca dalej wg poziomu);
- `m2_najemnicy_price_h` – opłata za godzinę za jednego najemnika (0 = 5 000 000).

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
11. Wyloguj się – po ~20 s najemnicy znikają (syslog: `NAJEMNICY: dismissed … why=owner_gone`).
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

## Co dalej (etap 3)

- Etap 3: ponowne wejście za graczem po zmianie rdzenia/kanału i po zalogowaniu, rozkazy („Za mną”, „Stój”,
  „Bij mój cel”, „Walcz sam”, „Nie podnoś łupu”), skrypty lochów pod lidera-gracza.
- Z etapu 2 zostaje na etap 3: wejście najemnika do lochów, które wpuszczają tylko listę „ludzi” (`d.new_jump_pids`
  – Świątynia Węży, Głębie, Meley) i wyrzucają bota przy logowaniu w środku (`when login … pc.is_playerbot()`);
  nagrody tych lochów są już podpięte pod `pc.is_najemnik()`. Przechodzenie przez najemnika jak przez dawnego
  Towarzysza (`sidekickcollision.py`). Po teleporcie gracza przycisk „Ekwipunek” wraca w ciągu 20 s (`NajemnikVids`).
- Kolekcjoner Najemników jest w osobnej łatce `server-patches/kolekcjoner` (okno, oddawanie przedmiotów 95%, stałe bonusy
  za zadania). Ukończone zadanie podnosi flagę `najemnicy.tasks` i wiersz `najemnicy_unlock.tasks` (GREATEST).
