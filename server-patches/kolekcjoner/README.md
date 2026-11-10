# kolekcjoner – Kolekcjoner Najemników

`MT2009_PLUS_KOLEKCJONER_NAJEMNIKOW_V1` i `_V2` (V2: uwagi właściciela z 10.11.2026 – zadania z panelu Seban, odświeżanie
okna na żywo, nowy wygląd i zakładka „Najemnicy”; sekcja „V2” na końcu) (decyzje właściciela z 8.11.2026, plan: `/opt/metin2/cache/yohara/najemnicy-plan.md`,
sekcje „Odblokowanie: Kolekcjoner Najemników” i „Stałe bonusy za zadania Kolekcjonera”).
Sześć zadań w dowolnej kolejności, każde raz. Przedmioty oddaje się jak u Biologa: przy każdej próbie przedmiot znika
z ekwipunku, szansa na zaliczenie to 95%, a nieudana próba nie podnosi licznika. Nie ma limitu czasu.
Ukończone zadanie daje od razu **stały bonus postaci** (bez względu na poziom) i **+1 zadanie najemników**.
Miejsca najemników liczy już `najemnicy` (zadania × poziom: 1 + 80 → 2, 2 + 85 → 3, … 6 + 105 → 7).

Port systemu „Collections System” z Arezzo (`CollectionsSystem.cpp/.hpp`, `uicollections.py`). Działanie zostało
(kategorie, przedmioty z licznikami, klik = oddaj, Ctrl + klik = oddaj wszystko), a kod jest przepisany. Wygląd jest nasz,
a nie z Arezzo. Logika: `linux-port/overlays/playerbot/src/game/src/playerbot_kolekcjoner_najemnikow.cpp` (opis w nagłówku).
Tabele: `linux-port/docker/mariadb/playerbot/kolekcjoner_najemnikow.sql`. Okno: `client-patches/client-2.0.30/root/uinajemnicykolekcjoner.py`
oraz `root/uiscript/najemnicykolekcjonerwindow.py`.

**Nakładana po `najemnicy`**, bo kotwice to wiersze komendy `/najemnicy` w `cmd.cpp`. Linux/VPS:
`python3 apply_kolekcjoner.py <game/src>`, Windows: `Apply-KolekcjonerPatch.ps1`. Edycja już nałożona jest pomijana.
Edycja, której stary kod nie występuje dokładnie raz, zatrzymuje całość. Przy wdrożeniu dopisz `kolekcjoner` do listy
łatek **za** `najemnicy` (w `yohara-deploy.sh` na końcu listy). `gen_edits.py [<game/src>]` zapisuje `edits.json`
i sprawdza kotwice.

| Plik | Co |
|---|---|
| `cmd.cpp` | `ACMD(do_kolekcja_najemnikow)` → `KolekcjonerNajemnikowCommand`, wiersz tabeli `kolekcja_najemnikow` (GM_PLAYER; część GM sama sprawdza GM_HIGH_WIZARD) |
| `char.cpp` | `CHARACTER::ComputePoints` („compute”): `KolekcjonerNajemnikowComputePoints`, czyli bonusy ukończonych zadań przy każdym przeliczeniu punktów, przed `ComputeBattlePoints` |

## Zadania (seed w `kolekcjoner_najemnikow.sql`, `INSERT IGNORE`)

| # | Zadanie | Przedmioty | Bonus stały |
|---|---|---|---|
| 1 | Skrzynie bossów | 5× 50077, 5× 50078, 5× 50079 (po 1) | Silny przeciwko bossom +10% (`ATTBONUS_BOSS`) |
| 2 | Kamienie Duszy | 3× 28442, 3× 28443, 3× 28437 (po 1) | Silny przeciwko kamieniom Metin +10% (`ATTBONUS_STONE`) |
| 3 | Cor Draconis | 100× 50255 (paczki po 10) | Silny przeciwko potworom +10% (`ATTBONUS_MONSTER`) |
| 4 | Odłamki Energii | 1000× 51001 (paczki po 100) | +10% odporności na ogień, lód, błyskawice, wiatr, ziemię i ciemność |
| 5 | Perły i małże | 10× 27992, 10× 27993, 10× 27994 (po 1), 50× 27987 (paczki po 10) | +5000 Max PŻ (`MAX_HP`) |
| 6 | Bossowie lochów | 5× 50082, 5× 33033, 10× 50271 – tylko nieotwierane | +100 wartości ataku i +100 wartości ataku magicznego (`ATT_GRADE_BONUS`, `MAGIC_ATT_GRADE_BONUS`) |

Tabele definicji (`najemnicy_kolekcjoner_categories`, `_items`, `_rewards`) można zmieniać w bazie. Po zmianie wpisz
`/kolekcja_najemnikow przeladuj` (GM). Nazwy bonusów: `s_aKnPoints` w pliku `.cpp`.

## Jak to działa

- **Szansa:** `percent` to szansa POWODZENIA (95). Arezzo liczyło ją odwrotnie, jako szansę porażki.
- **Oddanie:** jedno oddanie zabiera paczkę (`pack`: 1, 10 albo 100 sztuk) z ekwipunku. Jeśli w ekwipunku nie ma, bierze
  z dodatkowego ekwipunku (magazyny kategorii). Przedmiot znika przy każdej próbie. Udana próba dolicza całą paczkę,
  nieudana nic nie dolicza. **Ctrl + „Oddaj”** oddaje po kolei tyle paczek, ile masz, aż przedmiot będzie cały oddany.
  Nie da się oddać w czasie handlu, sklepu, magazynu, kostki ani ulepszania, ani po śmierci.
- **Skrzynia Nemere (50271), tylko nieotwierana:** skrzynię można otworzyć 3 razy, a liczba użytych otwarć jest
  w gnieździe 0 (`socket0`, `ShipDefense_ChestKeep` w `playerbot_ship_defense.cpp`). Skrzynia nie łączy się w stosy.
  Kolekcjoner bierze tylko skrzynię z `socket0 = 0`, czyli z 3/3 otwarć. Otwierana skrzynia nie liczy się do „masz N”
  i nie zostanie zabrana. Skrzynie 50082 i 33033 otwiera się raz i wtedy znikają, więc każda w ekwipunku jest nieotwierana.
- **Bonus na stałe:** ukończone zadanie to wiersz `najemnicy_kolekcjoner_complete`. Gra dodaje jego bonusy do punktów
  postaci przy każdym `ComputePoints`. To nie jest efekt (affect), więc nic nie wygasa i gracz niczego nie zdejmie.
  Bonus działa po wylogowaniu, zmianie mapy, kanału i rdzenia. Stan postaci jest czytany z bazy przy pierwszym
  przeliczeniu nowej instancji postaci (nowe VID), więc pierwsze przeliczenie po zalogowaniu ma już bonusy.
  Dzięki temu +5000 PŻ nie przycina zapisanego HP.
- **Najemnicy:** po ukończeniu zadania flaga `najemnicy.tasks` i wiersz `player.najemnicy_unlock.tasks` dostają
  `GREATEST` (wyższą liczbę od GM zostawiamy). Potem idzie `najemnicy sync` (flagi listu). Gracz dostaje duży napis na ekranie
  i dwie linie na czacie: bonus i „Odblokowuje: n. miejsce najemnika (od L poziomu)”.
- **Boty:** nic. Komenda bota jest pomijana, a bot (także najemnik) nie wczytuje stanu, więc nie dostaje bonusów.
- **Wyłącznik:** `/eventflag m2_kolekcjoner_najemnikow_off 1`. Wyłącza oddawanie przedmiotów. Okno i bonusy działają dalej.

## Poprawione błędy Arezzo

1. `percent` było szansą porażki (`number(1,100) <= percent` → „zły przedmiot”). Teraz to szansa powodzenia.
2. `RECV_Collection %d %s %d %d` miało 4 miejsca na wartości, a dostawało 3 argumenty (groziło awarią). Teraz wszystkie
   formaty są sprawdzone, a komunikaty na czat idą przez `KnTell` z `__attribute__((format(printf)))`.
3. Na stałe 15 pól na przedmioty. Teraz zadanie może mieć dowolnie wiele przedmiotów (okno dzieli kafelki na strony po 10, a lista zadań się przewija).
4. Bonusy były efektami na 365 dni (303–309) dawanymi jeszcze raz przy pierwszym logowaniu. Teraz są stałe (patrz wyżej).
5. Przy nieudanym pojedynczym oddaniu przedmiot zostawał. Teraz znika jak u Biologa. Przy „oddaj wszystko” pętla
   liczyła `CountSpecifyItem` w warunku, a ten malał przy każdej próbie. Teraz każda paczka jest sprawdzana osobno.
6. Postęp był w flagach questa. Teraz jest we własnych tabelach (`_progress`: oddane i próby, `_complete`: kolejność ukończenia).

Nie przeniesione: zwój +50% szansy (`collection.percent_up`, `char_item.cpp:7743`) i efekty 303–309 (`affect.h`).

## Komendy

Gracz (to samo robi okno): `/kolekcja_najemnikow open` (wszystko i okno), `lista` (tylko odświeżenie),
`oddaj <zadanie> <przedmiot> [all]`.
GM (GM_HIGH_WIZARD): `przeladuj` (definicje z bazy), `ukoncz <1-6>` (na własnej postaci, bez przedmiotów),
`wyczysc` (na własnej postaci: postęp i ukończone zadania znikają razem z bonusami, liczbę zadań najemników
ustawia `/najemnicy zadania`).

Protokół (CHAT_TYPE_COMMAND): `KNAJ begin|task|item|end|res|done`, opis w nagłówku `.cpp` i w `uinajemnicykolekcjoner.py`.
Logi: linie `KOLEKCJONER_NAJ:` w syslog rdzenia (wczytanie definicji, każde oddanie, każde ukończenie). Log przedmiotów
`KOLEKCJONER_NAJ` ma vnum i opis: zadanie, pozycja, sztuki, udane, nieudane, stan.

## Okno (klient)

Układ według obrazka właściciela z 8.11.2026 („dla rozeznania”). Grafiki są tylko z naszego klienta: ciemna tablica,
jednolite paski w kolorach kart domu aukcyjnego, pole slotu z magazynu kolekcjonera (`mt2009_ui/collector/slot.tga`),
publiczny przycisk zamknięcia i ikony przedmiotów. Nie ma nowych plików graficznych.
- U góry: złoty tytuł „K O L E K C J O N E R” między dwoma rombami, krzyżyk, jedna zakładka „Kolekcjoner” ze złotym
  podkreśleniem, a po prawej „Ukończone: x z 6, Miejsca najemników: n”.
- **Po lewej** lista zadań, która się przewija, gdy zadań jest więcej niż 6. Każde zadanie ma ikonę pierwszego
  przedmiotu w ramce, nazwę, „x / N” (oddane sztuki ze wszystkich) i cienki pasek postępu (zielony po ukończeniu).
  Wybrane zadanie ma złotą ramkę.
- **W środku** wybrane zadanie: nazwa, po prawej „od N poziomu” (próg najemnika, który da) albo „ukończone (n.)”,
  linia opisu i kafelki przedmiotów w 2 kolumnach. Kafelek ma ikonę, nazwę skróconą „..” i pigułkę „x / N”
  (zielone „Oddane”, gdy przedmiot jest cały oddany). Wybrany kafelek ma złotą ramkę. Ponad 10 kafelków dzieli się
  na strony. Wszystkie przedmioty zadania są dostępne od razu, bez blokady „zablokowana”.
- **Po prawej** wybrany przedmiot: duża ikona w złotej ramce, nazwa, pasek, „x / N”, „Szansa: 95%”,
  „Co ile: bez przerwy”, „Masz: N szt.” i „Paczka: po 10 szt.” albo „Tylko nieotwierane (3/3)”. Pod tym pigułka
  stanu: „Możesz oddać teraz”, „Brak przedmiotu”, „Za mało na paczkę”, „Oddane” albo „Zadanie ukończone”. Dalej
  „NAGRODA”, czyli stały bonus zadania i „Odblokowuje: n. miejsce najemnika (od L poziomu)” (po ukończeniu
  „Odblokowało: …”), oraz duży złoty przycisk „Oddaj”.
- **Na dole**: „Za całą kategorię (x/N): <bonus>” (x/N to przedmioty zadania oddane w całości), po ukończeniu
  z dopiskiem „aktywny na stałe”.

Oddawanie: klik na kafelek wybiera przedmiot, a „Oddaj” oddaje 1 (jedną paczkę). **Ctrl + „Oddaj”** oddaje wszystko,
co masz. Dwuklik albo PPM na ikonie kafelka oddaje 1, a z Ctrl wszystko. Podpowiedź przedmiotu to zwykła podpowiedź
przedmiotu z dopiskami (oddane, paczka, „tylko nieotwierane”, ile masz, klawisze). Wynik („Udane: 1, nieudane: 0”)
pojawia się pod kafelkami.

Okno otwierają:
- przycisk „Kolekcjoner Najemników” w liście „Najemnicy” (od 80 poziomu; także gdy najemnicy są jeszcze zablokowani
  albo wszystkie miejsca są zajęte),
- przycisk „Kolekcjoner Najemników” w menu Esc (pod „Bonus Reliktu”), dostępny dla każdego poziomu,
- klawisz akcji `kolekcjoner_najemnikow` w „Skróty klawiszowe” (domyślnie bez klawisza),
- komenda `/kolekcja_najemnikow open`.

Pliki klienta: `root/uinajemnicykolekcjoner.py` (nowy), `root/uiscript/najemnicykolekcjonerwindow.py` (nowy), `root/game.py`
(`KNAJ`, akcja klawisza, zamykanie okna), `root/keybind.py` (akcja), `root/uiscript/systemdialog.py` i `root/uisystem.py`
(przycisk w menu Esc). Teksty w CP1250, każdy w parze PL/EN (`playerbot_lang.T`).

## Jak przetestować na serwerze testowym

1. Wdrożenie: łatka `kolekcjoner` za `najemnicy`. Migracja `kolekcjoner_najemnikow.sql` uruchamia się sama przy starcie
   (w logu `apply.sh`: „Kolekcjoner Najemnikow: kolekcjoner_najemnikow.sql applied”). W syslog rdzenia po pierwszym
   logowaniu gracza: `KOLEKCJONER_NAJ: 6 task(s), 15 item(s) read`. Nowa łatka klienta (root).
2. Postać 85+ bez najemników. Esc → „Kolekcjoner Najemników”: 6 zadań po lewej (0 / N), w środku Skrzynie bossów
   („od 80 poziomu”), po prawej pierwszy przedmiot: „Szansa: 95%”, NAGRODA „Silny przeciwko bossom +10%”,
   „Odblokowuje: 1. i 2. miejsce najemnika (od 80 poziomu)”, na dole „Za całą kategorię (0/3): …”.
3. Daj sobie przedmioty (`/i 50077 5`, `/i 50078 5`, `/i 50079 5`). Wybierz kafelek i klikaj „Oddaj” (albo dwuklik
   na ikonie). Przy każdym kliknięciu znika 1 sztuka, a licznik rośnie mniej więcej 19 razy na 20. Pod kafelkami
   jest „Udane / nieudane”. Ctrl + „Oddaj” na 50078 oddaje wszystko naraz. Gdy zabraknie przedmiotów, licznik stoi,
   a pigułka pokazuje „Brak przedmiotu”.
4. Po ostatniej sztuce: duży napis „ukończone zadanie Skrzynie bossów”, na czacie bonus i „Odblokowuje: 1. i 2. miejsce
   najemnika (od 80 poziomu)”. Zadanie ma „Gotowe”, a karty „Oddane”. W oknie postaci od razu jest bonus przeciw
   bossom (np. `/state` albo podpowiedź). List „Najemnicy”: „Zadania Kolekcjonera: 1 z 6”, 2 miejsca.
   W bazie: `SELECT * FROM player.najemnicy_kolekcjoner_complete` i `player.najemnicy_unlock` (tasks = 1).
5. Paczki: `/i 50255 100` → jedno oddanie zabiera 10, a udane dolicza 10. Przy 9 sztukach jest komunikat
   „za mało na paczkę”. Odłamki 51001: paczki po 100 (sprawdź też Odłamki w dodatkowym ekwipunku, zakładka ulepszaczy).
6. Nemere: weź 2× 50271, jedną otwórz raz (zostaje z 2/3). W oknie „masz 1”. Oddaj, a druga, otwierana skrzynia zostaje
   w ekwipunku. Komunikat „nie masz” przy próbie oddania samej otwieranej.
7. Bonusy stałe: `/kolekcja_najemnikow ukoncz 5` (GM) daje od razu +5000 Max PŻ. Wyloguj się i zaloguj, zmień kanał
   i mapę: Max PŻ zostaje, HP po zalogowaniu nie jest przycięte. Zadanie 4: odporności na 6 żywiołów +10% w oknie
   postaci. Zadanie 6: wartość ataku i ataku magicznego +100.
8. Poziom: postać 82 z 3 zadaniami ma 2 miejsca, a w podsumowaniu „Czeka na poziom 85”. Po awansie na 85 ma 3 miejsca.
9. Odporność na błędy: w trakcie handlu „Oddaj” daje „Zamknij najpierw handel…”. Po śmierci: odmowa.
   `/eventflag m2_kolekcjoner_najemnikow_off 1`: „Kolekcjoner nie przyjmuje teraz przedmiotów”, a bonusy dalej działają.
   Potem wróć do 0.
10. Na koniec `/kolekcja_najemnikow wyczysc` (GM). Wszystko jest od zera, a bonusy znikają po przeliczeniu.

## V2 – uwagi właściciela z 10.11.2026 (`MT2009_PLUS_KOLEKCJONER_NAJEMNIKOW_V2`)

Bez nowych edycji silnika (łatka `kolekcjoner` jak w V1). Zmiany: `playerbot_kolekcjoner_najemnikow.cpp`,
`kolekcjoner_najemnikow.sql`, panel Seban (`kolekcjoner_config.py`, `templates/kolekcjoner_config.html`) i klient
(`uinajemnicykolekcjoner.py`, `uiscript/najemnicykolekcjonerwindow.py`, `interfacemodule.py`, `game.py`).

### Zadania z panelu (zaawansowana konfiguracja)

Panel Seban → Wydarzenia → Najemnicy → **Kolekcjoner** (`/events/najemnicy/kolekcjoner`):
- zadanie: klucz (ASCII, do logów), **tytuł** i **opis** (pokazywane w oknie; puste = wbudowane), **minimalny poziom**
  oddawania (0 = bez), **szansa** (1–100%), kolejność; dodaj / zapisz / w górę / w dół / usuń;
- przedmioty zadania: vnum (sprawdzany w `item_proto`, z nazwą), ile w sumie, paczka (1..ile), „tylko nieotwierane”,
  kolejność; dodaj / zapisz / w górę / w dół / usuń;
- bonusy stałe: dowolnie wiele wierszy „typ + wartość” z listy (62 typy: dotychczasowe + szybkości, regeneracja,
  absorpcja, silny przeciwko rasom i klasom, odporności na klasy i bronie, krytyki/przeszywające, średnie obrażenia i
  umiejętności, otrucie/omdlenie/spowolnienie, podwójne exp/yang/drop);
- **progi najemników** (`najemnicy_kolekcjoner_tiers`): n‑te ukończone zadanie → tyle najemników od poziomu (domyślnie
  1 → 2 od 80 … 6 → 7 od 105); miejsca i poziomy nie mogą maleć.

Walidacja: vnum istnieje, ilość ≥ 1, paczka 1..ilość, szansa 1–100, typ bonusu z listy, wartość ≠ 0, tytuł/opis w CP1250.
Usunięcie przedmiotu kasuje postęp graczy w nim; usunięcie zadania – jego przedmioty, bonusy i postęp (ukończenia
zostają, gracze zachowują próg, tracą bonus tego zadania; panel pyta, podając liczbę graczy). Przestawianie zmienia tylko
`sort_order` (`item_index` zostaje kluczem postępu).

**Bez restartu:** każda zmiana zapisuje flagę `m2_kolekcjoner_najemnikow_ver`; gra sprawdza ją najwyżej co 30 s i wczytuje
definicje (i stan postaci) od nowa – syslog `KOLEKCJONER_NAJ: the panel changed the definitions (version … -> …)`.
Zmieniony bonus trafia do postaci online przy najbliższym przeliczeniu punktów (awans, zmiana przedmiotu, teleport).
Progi najemników czyta co ~10 s `playerbot_najemnicy.h`. Sześć zadań właściciela zostaje domyślnymi (seed `INSERT
IGNORE` + polskie tytuły i opisy wpisywane tylko do pustych pól).

Protokół (nowe linie): `KNAJ tier <nr> <miejsca> <poziom>` (po `begin`), `KNAJ info <zadanie> <tytuł hex> <min. poziom>
<kolejność>`, `KNAJ desc <zadanie> <opis hex>` (po linii `task`), `KNAJ res … 10` = za niski poziom.

### Okno

- Wygląd okna „Sesja farmienia”: tytuł „Kolekcjoner Najemników” na pasku, płaskie zakładki **Kolekcjoner** i
  **Najemnicy**, ramki z nagłówkami, te same kolory i czcionki. Zakładka „Najemnicy” – opis w `server-patches/najemnicy`
  (etap 5).
- **Odświeżanie na żywo:** gdy okno jest otwarte, każda zmiana ekwipunku lub dodatkowego ekwipunku (każdy pakiet
  przedmiotu → `interfacemodule.RefreshInventory`) przelicza „Masz: N” po stronie klienta (plecak + magazyny
  dodatkowego ekwipunku, skrzynie „nieotwierane” tylko z gniazdem 0 = 0), najwyżej co 0,25 s, bez zapytań do serwera;
  „Oddaj” włącza się od razu.

### Jak przetestować V2

11. Panel → Kolekcjoner: zmień tytuł zadania 3 na „Smocze serca”, szansę na 50%, dodaj przedmiot 27992 ×2 (paczka 1),
    dodaj bonus „Szybkość ruchu +5”, przesuń zadanie 3 na górę. Po ≤ 30 s otwórz okno w grze: zadanie 3 jest pierwsze,
    ma nowy tytuł, „Szansa: 50%”, nowy kafelek i bonus. Syslog: `the panel changed the definitions`.
12. Walidacja: vnum 999999, paczka większa od ilości, szansa 0, próg z mniejszą liczbą miejsc niż poprzedni – czerwony
    komunikat, nic nie zapisane.
13. Min. poziom 120 dla zadania – „Oddaj” daje „Za niski poziom”. Wróć do 0.
14. Progi: ustaw próg 1 na 3 miejsca od 80 – zakładka „Najemnicy” po ≤ 10 s pokazuje 3 miejsca (postać 80+ z 1 zadaniem).
    Przywróć 2.
15. Odświeżanie: otwórz okno na zadaniu 1, wyrzuć/podnieś szkatułkę 50077, przenieś Odłamki 51001 między plecakiem a
    dodatkowym ekwipunkiem – „Masz: N” i „Oddaj” zmieniają się od razu.
16. Usuń dodane w pkt 11 przedmiot i bonus, przywróć tytuł (puste pole = nazwa wbudowana) i szansę 95%.
