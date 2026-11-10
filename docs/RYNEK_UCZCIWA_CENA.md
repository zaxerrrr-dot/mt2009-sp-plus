# Rynek uczciwej ceny (boty, Yohara 3.x)

Znacznik w kodzie: `MT2009_PLUS_BOT_FAIR_PRICE_V1`. Gra: `playerbot_fair_price.h` (uczciwa cena) i `playerbot_lada.h` (ceny botów). Panel: **Gospodarka → Rynek – uczciwa cena** (`rynek.py`). Tabele: `rynek_fair.sql`.

Rynek reguluje się sam, sprzedażą i ilością towaru, jak na prawdziwym serwerze. Zastępuje stary system: wyprzedaż nadwyżek (cena schodziła co 30 min o 10%), progi -5% / -3% dla najtańszych ofert i podłogę 90%.

## Czego to dotyczy

Towar „w stosach”: materiały do ulepszeń, rudy, kamienie, zwoje, ryby i inne przedmioty, które się łączą, plus pieczone ryby z Twojej listy.

Nie dotyczy sprzętu, ksiąg, kamieni dusz i Smoczych Kamieni, Corów, kuponów SM, run, owoców rangi, kul polimorfii ani Zwoju Zapomnienia. Te przedmioty zostają przy swoich cenach.

## 1. Uczciwa cena każdego przedmiotu

**Uczciwa cena = cena bazowa × mnożnik rynku.**

**Cena bazowa** pochodzi z jednego z czterech źródeł:
- Twoja cena, np. pieczone ryby;
- cennik z kursem yang i inflacją, jak dotąd;
- cena od kupca, jeśli przedmiotu nie ma w cenniku;
- średnia z prawdziwych sprzedaży. Zastępuje cenę od kupca, gdy jest już co najmniej 8 sprzedaży, i zmienia się najwyżej o 10% na dobę.

Inflacja działa na cenę bazową tak jak dotąd.

**Mnożnik** mieści się w granicach **60–200% ceny bazowej**. Jeden rdzeń kanału handlowego przelicza go **co 15 minut** i patrzy na trzy rzeczy:

| Co | Jak działa |
|---|---|
| **Zapas** | Sztuki na wszystkich straganach (boty i gracze, oba kanały) ÷ sprzedaż na dzień. Mniej niż 7 dni sprzedaży oznacza, że towar schodzi, więc cena idzie w górę. Więcej niż 7 dni oznacza, że zalega, więc cena idzie w dół, ale tylko z wagą 30%: lada trzyma cały towar botów i sama ilość nie może zrzucić ceny. Brak jakiejkolwiek sprzedaży przy towarze na rynku powoduje powolny spadek. |
| **Ceny sprzedaży** | Jeśli w ostatnich 6 godzinach kupujący płacili uczciwą cenę albo więcej, to tańsze oferty się wyczerpały i cena idzie w górę (waga 50%). |
| **Tempo sprzedaży** | Ostatnie 6 godzin porównane z 48 godzinami: sprzedaż przyspiesza, cena w górę; zwalnia, cena w dół (waga 30%). |

- **Szybkość:** przy skrajnej nierównowadze cena rośnie do **+15% na godzinę** albo spada do **−10% na godzinę**. Blisko równowagi zmiany są mniejsze, a przy wyniku poniżej 0,08 cena stoi.
- **Pewność:** ruch mnoży się przez liczbę transakcji / (liczba transakcji + 8). Rzadkie przedmioty prawie się nie ruszają i zostają przy cenie bazowej.
- **Odrzucone sprzedaże:** sprzedaż poniżej 35% albo powyżej 300% uczciwej ceny, np. linia gracza za 1 yang albo pomyłka z zerem, nie wpływa ani na cenę, ani na liczenie sprzedaży.

Wynik trafia do bazy (`player.playerbot_market_fair`). Pozostałe rdzenie czytają go co 5 minut. Historia jest zapisywana co godzinę.

## 2. Jak boty wystawiają

- Bot wystawia **cały swój zapas** danego rodzaju **od razu, po jednej cenie** za sztukę. Lada jest jego magazynem i nic nie jest zdejmowane z rynku.
- Każdy bot ma dla każdego rodzaju **własny przedział**, zawsze w granicach 60–200% uczciwej ceny. Przedział jest stały dla danego bota i przedmiotu:

  | Typ bota | Udział | Najniżej | Najwyżej | Pierwsza cena |
  |---|---|---|---|---|
  | handlarze | 30% | 60–70% | 110–140% | 90–100% |
  | normalni | 50% | 70–85% | 120–170% | 97–108% |
  | cierpliwi | 20% | 90–110% | 140–200% | 105–120% |

  Dzięki temu na rynku zawsze są ceny od tanich do drogich. Przykład: 100 Zwojów Błogosławieństwa przy uczciwej cenie ok. 1 kk kosztuje od ok. 600 k do 1,5 kk.
- **Co 30–60 minut** (losowo dla każdego bota i przedmiotu, żeby nie ruszały wszystkie naraz) bot sprawdza swoją cenę:
  - **coś sprzedał** od ostatniego sprawdzenia: cena **+3–5%**;
  - **nic nie sprzedał**: cena **−3–5%**;
  - nigdy poza swój przedział.

  Potem wszystkie jego linie tego przedmiotu dostają nową cenę. Bot **nie** patrzy na najtańszą ofertę, więc tnie cenę tylko ten, komu towar nie schodzi.
- Jego cena = uczciwa cena × jego mnożnik. Gdy rynek przesuwa uczciwą cenę, oferty bota przesuwają się razem z nią.

## 3. Kupujący

Bez zmian: boty i gracze kupują najpierw najtańsze oferty. Każda sprzedaż wpływa na liczenie z punktu 1. Gdy tanie oferty znikną, kupujący płacą więcej, a uczciwa cena rośnie.

## Naprawa starych, „rozbitych” linii

Stary system zostawił linie po 1–10% normalnej ceny. Co 10 minut rdzeń, który obsługuje stragan, sprawdza wszystkie linie tego towaru. Każdą, która odbiega o więcej niż 2% od ceny swojego bota albo stoi poniżej jego minimum, ustawia na jedną cenę bota (do 20 zmian na sekundę). Po starcie wszystkie rozbite linie wracają do normy w ciągu kilkunastu minut.

Specjalna „pomyłka z zerem” na pojedynczej sztuce zostaje, jak dotąd: rdzeń poprawia ją sam po kilku godzinach.

## Panel: Gospodarka → Rynek – uczciwa cena

- **Lista przedmiotów:**
  - cena bazowa i jej źródło;
  - uczciwa cena i % bazy;
  - granice;
  - zapas w dniach;
  - sprzedaż na dzień;
  - sztuki na rynku i liczba sprzedawców;
  - rozrzut ofert: najtańsza, p25, mediana, p75, najdroższa;
  - ruch na godzinę i pewność.
- **Przedmiot (kliknij nazwę):** wykres uczciwej ceny, mediany ofert i średniej sprzedaży, sprzedaż na godzinę oraz tabela godzinowa (14 dni).
- **Przypięcie:** stała uczciwa cena za sztukę i/lub własne granice (% ceny bazowej). Gra przejmuje zmianę przy najbliższym przeliczeniu (do ok. 15 min). Puste pola przywracają cenę automatyczną.
- **Ustawienia:** flagi poniżej. Gra czyta je co ok. 10 s, bez restartu. W grze: `/eventflag <nazwa> <wartość>`.

## Flagi

Wartość 0 albo brak oznacza ustawienie domyślne.

| Flaga | Domyślnie | Znaczenie |
|---|---|---|
| `m2_bot_fairprice_off` | 0 | 1 = stary system (wyprzedaż, progi -5/-3%, podłoga 90%) |
| `m2_bot_fair_step_min` | 15 | co ile minut przeliczać uczciwą cenę |
| `m2_bot_fair_up_pct` / `_down_pct` | 15 / 10 | maks. zmiana uczciwej ceny na godzinę (%) |
| `m2_bot_fair_min_pct` / `_max_pct` | 60 / 200 | granice uczciwej ceny (% bazy) |
| `m2_bot_fair_cover_days` | 7 | zapas w równowadze (dni sprzedaży) |
| `m2_bot_fair_stock_weight` | 30 | waga ilości towaru w dół (-1 = wyłączona) |
| `m2_bot_fair_price_weight` | 50 | waga zakupów po uczciwej cenie lub drożej (-1 = wyłączona) |
| `m2_bot_fair_trend_weight` | 30 | waga tempa sprzedaży (-1 = wyłączona) |
| `m2_bot_fair_conf_sales` | 8 | sprzedaży do połowy pewności |
| `m2_bot_fair_window_h` | 48 | okno sprzedaży (godziny, do 96) |
| `m2_bot_fair_check_min` / `_max` | 30 / 60 | co ile minut bot sprawdza swoją cenę |
| `m2_bot_fair_step_lo` / `_hi` | 3 / 5 | krok ceny bota (%) |
| `m2_bot_fair_list_min_pct` / `_max_pct` | 60 / 200 | najniżej / najwyżej, jak bot wystawi (% uczciwej ceny) |
| `m2_bot_fair_edits_s` | 20 | zmian cen na sekundę na rdzeń |
| `m2_bot_fair_hist_days` | 14 | ile dni historii trzymać |

## Logi (syslog rdzeni, co 10 minut)

- `PLAYERBOT_FAIR: census`: przedmioty, sztuki i linie na rynku, sprzedaże, odrzucone sprzedaże, sprawdzenia botów, podwyżki i obniżki, boty na swoim minimum lub maksimum, zmiany cen, naprawione linie (sztuki i yang), typy botów.
- `PLAYERBOT_FAIR: kind` (rdzeń zapisujący, 12 przedmiotów z największym zapasem): cena bazowa, uczciwa cena, mnożnik, granice, zapas, sprzedawcy, sprzedaż, zapas w dniach, średnia sprzedaży, nierównowaga, pewność, ruch na godzinę oraz **rozrzut ofert: najtańsza, p25, mediana, p75, najdroższa**.
- `PLAYERBOT_FAIR: repair`: naprawiona linia (pojawia się w logu najwyżej raz na minutę).
- `PLAYERBOT_FAIR: config`: ustawienia po każdej zmianie.

## Jak sprawdzić na serwerze testowym

1. Po starcie: w logach `PLAYERBOT_FAIR: config on=1`, `writer=1` na jednym rdzeniu kanału 1, a po 10 minutach `census` i `kind`.
2. Panel → Rynek – uczciwa cena: przedmioty z rozrzutem cen. W `census` są niezerowe `checks`, `raised` i `lowered`, a `edits_done` rośnie.
3. Zwój Błogosławieństwa (25040) i Rybia Ość (27799): ceny ofert w przedziale 60–200% uczciwej, nic za 1–10% (`repaired` w `census` rośnie, w „Podglądzie rynku” nie ma już rozbitych linii).
4. Przypięcie ceny w panelu: po ≤15 min `fair` równa się przypiętej, a linie botów stoją w swoich przedziałach wokół niej.
5. `/eventflag m2_bot_fairprice_off 1` wraca do starego systemu (`PLAYERBOT_FAIR: config on=0`, wracają `PLAYERBOT_MARKET_CLEAR` i progi lady).
