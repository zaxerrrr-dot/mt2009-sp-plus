# tytuly – Tytuły postaci

`MT2009_PLUS_TITLES_V1` (właściciel, 4.11.2026: „dodaj”). Na podstawie paczki właściciela „Official Title System Renewal”
– przepisanej, nie skopiowanej: ten sam pomysł (gracz zdobywa tytuły na stałe albo na czas, zakłada jeden z nich, a każdy
w pobliżu widzi go przy jego imieniu – tabliczka z nazwą, animowany baner albo efekt nad głową; okno tytułów z podglądem;
certyfikaty 57000–57002), inne wnętrze tam, gdzie paczka nie pasowała do naszego silnika albo miała błędy.

**Nakładana jako OSTATNIA** z listy łatek (po `skillcolor`; kotwice: linie pakietów, logowania, `EncodeInsertPacket` i
`Destroy` koloru umiejętności). Linux/VPS: `python3 apply_tytuly.py <game/src>`; Windows: `Apply-TytulyPatch.ps1`
(`tools/port/Apply-MT2009PlusEngine.ps1`, na końcu). Edycja już nałożona jest pomijana; edycja, której stary kod nie
występuje dokładnie raz, zatrzymuje całość, zanim cokolwiek zostanie zapisane. `gen_edits.py [<game/src>]` pisze
`edits.json` (i sprawdza kotwice).

## Co robi

- **Katalog** jest w nakładce (`playerbot_titles.cpp`, `TITLES`): numer, wygląd (tabliczka z nazwą / efekt nad głową),
  polska nazwa i sposób zdobycia, na stałe albo domyślny czas, zasób klienta
  (`d:/ymir work/ui/game/title/titles/title_<zasób>.sub`) i plik efektu. Serwer wysyła go klientowi (pakiet TABLE) –
  nowy tytuł to linia tutaj i ewentualnie obrazki w kliencie, bez zmian w danych klienta.
- **Wygląd**: tabliczka (lewa/środek/prawa część + nazwa w kolorze tytułu; 1005, 1006, 1011 dodatkowo z animowanym
  banerem nad nią) albo efekt nad głową (bez nazwy) – jak w paczce.
- **Posiadanie**: `player.player_title` (wiersz na tytuł: `pid`, `title_index`, `end_time` – 0 = na stałe, `equipped`).
  Czytane przy logowaniu, pisane przy zmianie; tytuł, któremu minął czas, znika (wiersz, lista, założony) – sprawdzane co
  60 s, godzinę przed końcem gracz dostaje komunikat.
- **Zakładanie**: okno tytułów (portret w oknie postaci), 1 zmiana na sekundę (jak w paczce).
- **Kto co nosi**: `GC VISUAL` (VID, tytuł) do każdego widza, którego klient się przywitał – po jego pakietach dodania
  postaci (`EncodeInsertPacket`) i przy zmianie.

### Lista tytułów – jak na wiki (`MT2009_PLUS_TITLES_V2`, 4.11.2026)

Właściciel: „Tytuły jak na wiki, ale wiele tych rzeczy nie mamy dostępnych u nas, więc trzeba kupić certyfikaty w
ItemShopie”. Źródła: tr-wiki „Ünvan Sistemi” (11 tytułów), en „Titles”, de „Titel System” (+ Nyx-Champion), it „Titoli
(Sistema)” (+ Wielki Mistrz Okey, Łowca Monet); pl-wiki ma „System Tytułów”, przedmioty „Tytuł Czciciel Słońca” / „Tytuł
Gwiazda Polarna” (365 dni) i rangi Heroiczna / Legendarna / Mistyczna – polskie nazwy stamtąd, reszta z polskich plików
paczki. Żaden tytuł nie daje bonusu (wiki nie podaje żadnego).

| Nr | Nazwa | Wygląd | Czas (wiki) | Źródło na wiki → u nas |
|---|---|---|---|---|
| 1 | Ostatni Ocalały | korona nad głową | 3 h | Battle Royale (brak) → certyfikat 57008 |
| 2 | Niepokonany | medal 1. miejsca nad głową | 7 dni | 1. miejsce rankingu Strefy Walki → **sam**: 1. miejsce tygodniowego rankingu „Zabójca” |
| 3 | Zwiastun Wojny | medal 2. miejsca | 7 dni | 2. miejsce → **sam**: 2. miejsce „Zabójcy” |
| 4 | Rzeźnik | medal 3. miejsca | 7 dni | 3. miejsce → **sam**: 3. miejsce „Zabójcy” |
| 1000 | Szczęściarz | niebieska tabliczka | na stałe | miesięczne losowanie członkostwa (brak) → certyfikat 57001 |
| 1001 | PLUS (na wiki: tytuł członkostwa) | tarcza nad głową | 30 dni (miesiąc członkostwa) | członkostwo (brak) → certyfikat 57003 |
| 1002 | Heroiczny | złota tabliczka | 30 dni | ranga Heroiczna (brak) → certyfikat 57000 |
| 1003 | Legendarny | złota tabliczka | 30 dni | ranga Legendarna (brak) → certyfikat 57004 |
| 1004 | Mistyczny | złota tabliczka | 30 dni | ranga Mistyczna (brak) → certyfikat 57005 |
| 1005 | Czciciel Słońca | złoty baner (animowany) | 365 dni | Tombola letnia (brak) → certyfikat 57002 |
| 1006 | Gwiazda Polarna | niebieski baner (animowany) | 365 dni | Tombola zimowa (brak) → certyfikat 57006 |
| 1007 | Czempion Nyx | złota tabliczka | na stałe | przeniesienie postaci z serwera Nyx (brak) → certyfikat 57007 |
| 1011 | Wielki Mistrz Okey | czerwony baner (animowany) | na stałe | 500+ pkt w jednej grze Okey → **sam** (Rumi) |
| 1012 | Łowca Monet | czerwona tabliczka | na stałe | 10 000 Doblonów → **sam** (Poszukiwanie skarbów z Goblinem, łącznie) |

Wypadły (żadna wiki ich nie wymienia): 6 Płomienny Pogromca i 7 Bezlitosny Sędzia (rankingi Meley / Balathora).
Nazwa tytułu członkostwa to u nas „PLUS” (bez nazw innych serwerów). Wygląd 2–4: medale wiki (GF `ranking_battle/
ranker_1..3.tga`) jako efekt `title_rank_<n>.mse` (jeden nieruchomy obrazek nad głową) – exe bez zmian.

**Nadawane same** (`TitleSystemGrantPid(pid, tytuł, sekundy)` w nakładce; boty nigdy):
- 2–4: `playerbot_weekly_rank.h` `TryRollover` – przy zamknięciu sezonu 1./2./3. miejsce kategorii „Zabójca” (zabici
  gracze) dostaje tytuł na 7 dni od teraz (dłuższy, który ma, zostaje; miejsce bota nie daje nic);
- 1011: `playerbot_rumi.h` `Settle` – gra z wynikiem ≥ 500 (także przy wyjściu z gry);
- 1012: `playerbot_goblin.h` – każdy zdobyty Doblon (zabójstwo fali, właściwa skrzynia – tyle, ile weszło do sakiewki)
  liczy się na stałe we fladze `goblin.earned` (nowy event jej nie zeruje); przy 10 000 tytuł.
Postać na tym rdzeniu dostaje tytuł od razu (zakładany, gdy nie nosi żadnego); na innym kanale albo offline – wiersz z
`granted_at` = teraz, który rdzeń z postacią czyta w ciągu minuty (`PollGranted`, indeks), a każdy rdzeń przy logowaniu.

**Certyfikaty** (`tytuly.sql`, ITEM_QUEST, 1 w slocie; jak na pl-wiki: bez handlu, sklepu, sprzedaży u NPC, upuszczania,
łączenia; magazyn tak – antiflag 123264; ikony GF 57000 czerwona / 57001 niebieska / 57002 zielona; nazwy jak pl-wiki
„Tytuł <nazwa>”; opis: „Natychmiast odblokowuje tytuł „…” dla twojej postaci. Czas trwania tytułu: …”). Certyfikat
tytułu czasowego, który gracz ma, przedłuża go. W ItemShopie w grze (zakładka Wyposażenie, linie 40–48, `ishop_once
tytuly_certs_40` / BOOT_ONCE panelu) i przez widok `itemshop3.shop` w ItemShopie V3 (/shop3/, ikony `img/item/5700x.png`,
opisy `client_itemdesc.json`); boty nigdy (`gen_bot_catalogue.py` NEVER, `IsPlayerBotIshop3ExcludedVnum`).

| Linia | Certyfikat | Tytuł | Cena (propozycja – wiki nie podaje ceny) |
|---|---|---|---|
| 40 | 57003 Tytuł PLUS | 1001, 30 dni | 49 SM |
| 41 | 57000 Tytuł Heroiczny | 1002, 30 dni | 79 SM |
| 42 | 57004 Tytuł Legendarny | 1003, 30 dni | 99 SM |
| 43 | 57005 Tytuł Mistyczny | 1004, 30 dni | 129 SM |
| 44 | 57002 Tytuł Czciciel Słońca | 1005, 365 dni | 299 SM |
| 45 | 57006 Tytuł Gwiazda Polarna | 1006, 365 dni | 299 SM |
| 46 | 57001 Tytuł Szczęściarz | 1000, na stałe | 199 SM |
| 47 | 57007 Tytuł Czempion Nyx | 1007, na stałe | 149 SM |
| 48 | 57008 Tytuł Ostatni Ocalały | 1, 3 godziny | 9 SM |

(Dla porównania pl-wiki: miesiąc członkostwa, które daje te tytuły i buffy, kosztuje 499 SM.) Ceny zmienia się w panelu
Seban → Edytor bazy danych → ItemShop.

## Silnik (`edits.json`, 12 edycji) i nakładka

| Plik | Miejsce | Co |
|---|---|---|
| `packet.h` | nagłówki | `HEADER_CG_TITLE = 185`, `HEADER_GC_TITLE = 189` (numery paczki) – wolne u nas i w exe (sprawdzone: wszystkie CG/GC naszego `packet.h`, `npc_location_helper.h`, `input_udp.cpp`, `Packet.h` exe i gałęzi y-lowienie / y-mikstury2 / y-grupy) i poza zakresami zarezerwowanymi dla zwierzaków (CG 122–133, GC 200–215) |
| `packet.h` | struktury | `TPacketCGTitle` (6 B), `TPacketGCTitle` (6 B, dynamiczny), wiersze `TPacketGCTitleRow` (309 B), `TPacketGCTitleOwned` (8 B), `TPacketGCTitleNotify` (5 B), `TPacketGCTitleVisual` (8 B), `static_assert` (exe to samo) |
| `packet_info.cpp` | rozmiary | CG 185, stały, z bajtem sekwencji |
| `input_main.cpp` | pakiety | `TitleSystemPacket` (powitanie/odświeżenie, załóż, zdejmij) |
| `input_login.cpp` | po kolorze umiejętności | wiersze postaci z bazy, założony tytuł do wszystkich wokół (`TitleSystemOnLogin`) |
| `char.cpp` | `EncodeInsertPacket`, `Destroy` | założony tytuł temu, kto widzi postać; stan VID-u znika |
| `char_item.cpp` | `UseItemEx` | certyfikaty 57000–57008 (V2; zakres w nakładce) przed limitami i typem przedmiotu (`TitleSystemUseItem`) |
| `cmd.cpp` | polecenia | `/tytul` i nazwa paczki `/title_system` (GM_LOW_WIZARD, jak w paczce) |
| `questlua.cpp` | moduły questów | `title.give(nr [, sekundy])`, `title.has(nr)`, `title.remove(nr)`, `title.equipped()` |

Nakładka: `linux-port/overlays/playerbot/src/game/src/playerbot_titles.cpp` (cała logika).

GM: `/tytul lista`, `/tytul <nr|nazwa>` (sobie), `/tytul daj <gracz> <nr> [dni]`, `/tytul zabierz <gracz> <nr>`,
`/tytul pokaz <gracz>` (gracz na tym samym kanale).

**Różnice względem paczki** (świadome):
- Klient **wita się** (CG 185 OPEN po wejściu do gry) i tylko taki klient dostaje GC 189 – starszy exe nigdy nie zobaczy
  nieznanego pakietu (bez podnoszenia wersji klienta), boty nie kosztują nic (nie mają wiersza ani zapytania).
- Kto nosi który tytuł – własny podpakiet `VISUAL` tylko do widzów, nie `SpecificEffectPacket` z „ścieżka|numer” do
  wszystkich wokół przy każdym pojawieniu się postaci.
- Posiadanie i założony tytuł tylko w `player.player_title` (paczka: tabela + flagi questów `title_system.*`); tytuł „na
  stałe” jest na stałe (paczka: 365 dni).
- Certyfikat = jeden tytuł (value0) i jego czas (value1, 0 = domyślny); certyfikat tytułu czasowego, który gracz już ma,
  przedłuża go (paczka: odmawiała). Bez nowego podtypu `USE_TITLE` – `ITEM_QUEST` jak pudła puzzli, więc bez zmian w
  `item_length.h`, `ProtoReader.cpp`, DumpProto i `ItemData.h` exe.
- Bez wpisu do syserr przy każdym otwarciu okna (paczka zostawiła `TITLE_SYSTEM DEBUG`).

## Baza

`linux-port/docker/mariadb/playerbot/tytuly.sql` (w `apply.sh` po puzzlach rybackich): `player.player_title` (`CREATE
TABLE IF NOT EXISTS`, `ADD COLUMN IF NOT EXISTS equipped`, V2: `granted_at` + indeks) i certyfikaty 57000–57008 w
`world.item_proto` (`INSERT IGNORE`, ITEM_QUEST, 1 w slocie, antyflagi jak na pl-wiki = 123264; trzy wiersze V1 raz
poprawione – znacznik `tytuly:certs_v2` w `player.playerbot_migrations`). Zaraz po nim w `apply.sh` linie ItemShopu 40–48
(`ishop_once tytuly_certs_40`). Sprawdzone na jednorazowym MariaDB 11.8 (dwa przebiegi, wiersze V1 przed, zapytanie
`TitleSystemGrantPid` i `EXPLAIN` odczytu `granted_at`).

## Klient

- Exe (`client-patches/exe`, `ENABLE_MT2009_TITLES`, `Mt2009Titles.cpp`) – README exe.
- Root: `uicharactertitle.py` (okno: lista tytułów z katalogu serwera – kłódka / klepsydra / nieskończoność, założony
  tytuł, „Załóż” / „Zdejmij”, podgląd tabliczki z banerem albo efektu, opis zdobycia i czas; komunikaty na czacie także
  przy zamkniętym oknie), `uiscript/charactertitlewindow.py` (układ paczki), portret w oknie postaci otwiera okno
  (`uicharacter.py`, przycisk GF nad ramką twarzy), „Ukryj tytuły innych graczy” w Opcjach dodatkowych
  (`uiopcjedodatkowe.py`). Bez exe z `titleSystem` nic z tego się nie pokazuje.
- Dane: paczka `tytuly` + certyfikaty 57000–57008 w `gamedata`/`dbdata` (`client-2.0.30/tools/tytuly`; V2: medale
  rankingu `title_rank_1..3.mse` + `ranker_1..3.tga` GF, 6 nowych certyfikatów z ikonami GF 57000–57002).
