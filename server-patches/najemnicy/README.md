# najemnicy – Najemnicy, etap 1 (rdzeń)

`MT2009_PLUS_NAJEMNICY_V1` (decyzje właściciela z 8.11.2026, plan: `/opt/metin2/cache/yohara/najemnicy-plan.md`).
Stała drużyna botów gracza: od 80 poziomu gracz tworzy najemników (klasa, droga, płeć, imię), wzywa ich do swojej
grupy, a oni chodzą za nim i walczą. Za każdego wezwanego płaci ze skarbca najemników.

Cała logika jest w nakładce `linux-port/overlays/playerbot/src/game/src/playerbot_najemnicy.h` (opis w nagłówku pliku).
Quest: `linux-port/docker/game/quest/najemnicy.quest` (list „Najemnicy”). Tabele: `linux-port/docker/mariadb/playerbot/najemnicy.sql`.
Panel Seban: `Wydarzenia → Najemnicy` (`najemnicy.py`). Ta łatka dodaje tylko komendę i dwa haki silnika.

**Nakładana po `pvpfan`** (kotwice to wiersze PVP Fan w `cmd.cpp` i `battle.cpp`). Linux/VPS:
`python3 apply_najemnicy.py <game/src>`; Windows: `Apply-NajemnicyPatch.ps1`. Edycja już nałożona jest pomijana;
edycja, której stary kod nie występuje dokładnie raz, zatrzymuje całość. Przy wdrożeniu dopisać `najemnicy`
do listy łatek **za** `pvpfan` (w `yohara-deploy.sh` na końcu listy).

| Plik | Co |
|---|---|
| `cmd.cpp` | `ACMD(do_najemnicy)` → `PlayerBotNajemnicyCommand`, wiersz tabeli `najemnicy` (GM_PLAYER; część GM sprawdza GM_HIGH_WIZARD sama) |
| `battle.cpp` | `battle_is_attackable`: `NajemnicyBlockAttack` – najemnik nie bije żadnej postaci i żadna postać nie bije jego, chyba że ich gildie mają ze sobą wojnę |
| `char_battle.cpp` | `CHARACTER::ItemDropPenalty`: `NajemnikNoItemDrop` – śmierć najemnika nie gubi przedmiotów |

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
- **Ekwipunek (zaślepka do etapu 2):** „Ekwipunek → Daj mu rzecz do założenia” (numer pola w ekwipunku gracza) i
  „Zabierz wszystko” (wszystko, co ma i nosi, oraz jego yang wraca do gracza). Przy pierwszym wejściu plecak nowej
  postaci jest czyszczony (żeby startowe przedmioty nie trafiały do gracza).
- **Zwolnienie:** wezwany najpierw oddaje wszystko; niewezwany musi nic nie mieć. Postać, konto i przedmioty usuwa gra
  20 minut po zwolnieniu.

## Komendy

Gracz (to samo robią przyciski listu): `/najemnicy` (lista), `wezwij <nr|wszyscy>`, `odwolaj <nr|wszyscy>`,
`wplac <yang>` (np. `50000000` albo `50kk`), `skarbiec`, `daj <nr> <pole>`, `zabierz <nr>`, `gildia <nr>`,
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

## Co dalej (etapy 2–3)

- Etap 2: okno ekwipunku najemnika w kliencie (klik na najemnika), zużywalne przedmioty od gracza, nagrody lochów
  w plecaku najemnika (także łup bossów, którego boty dziś nie podnoszą – `Mt2009PlusIsPeopleLoot`).
- Etap 3: ponowne wejście za graczem po zmianie rdzenia/kanału i po zalogowaniu, rozkazy („Za mną”, „Stój”,
  „Bij mój cel”, „Walcz sam”, „Nie podnoś łupu”), skrypty lochów pod lidera-gracza.
- Osobno: Kolekcjoner Najemników (okno na bazie Kolekcjonera, oddawanie przedmiotów 95%, bonusy za zadania, łatka
  klienta) – ma tylko podnosić flagę `najemnicy.tasks` (0–6); reszta już ją czyta.
