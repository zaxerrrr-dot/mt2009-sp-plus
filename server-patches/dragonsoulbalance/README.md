# Bonusy alchemii (kamienie smoka) – balans MT2009 Plus

Balans operatora z 24 września 2026. Dwie części:

- **tabela** `dragon_soul_applys.mt2009plus.txt` (w `linux-port/docker/game/`):
  przy budowie obrazu (`game/Dockerfile`) zastępuje grupy `BasicApplys`
  i `AdditionalApplys` w `share/locale/poland/dragon_soul_table.txt`
  z paczki. Plik jest w EUC-KR, bo nazwy grup to koreańskie nazwy kamieni
  z paczki;
- **silnik** `dragon_soul_table.cpp` (znacznik `MT2009_PLUS_DS_APPLYS_V1`):
  nakładany raz, przy przygotowaniu wydania
  (`tools/port/Apply-MT2009PlusEngine.ps1`); `Apply-DragonSoulBalancePatch.ps1`
  i jego linuksowy bliźniak `apply_dragonsoulbalance.py` robią to samo.

## Co było nie tak w silniku

- **„Wartość ataku” (`ATT_BONUS`) i „Obrona” (`DEF_BONUS`)** trafiały do
  `POINT_ATT_BONUS` / `POINT_DEF_BONUS`, czyli do **mnożników procentowych**
  (`battle.cpp`: `atak × (100 + ATT_BONUS) / 100`). Mityczny Rubin +6 dawał
  więc **+480% ataku** zamiast +480 wartości ataku. Teraz to płaskie
  `POINT_ATT_GRADE_BONUS` / `POINT_DEF_GRADE_BONUS`, jak bonus z przedmiotu.
  Atak i obrona magiczna idą przez `*_GRADE_BONUS` z tego samego powodu.
- **Bonusy na żywioły (`ENCHANT_*`), wszystkie Sungma i `HIT_PCT`** nie
  dawały nic: silnik nie ma tych statystyk i zamieniał je na pusty bonus.
- **Silny na ludzi, zwierzęta, orki, mistyków, nieumarłych, potwory,
  krytyk i przeszywające** nie były znane tabeli – poprawka je dopisuje.

## Balans

Wartość na kamieniu = wartość z tabeli × waga (od 1% do **160%** – mityczny,
najwyższy stopień, +6). W nawiasie maksimum.

Stałe bonusy (2. od kamienia pradawnego; odporności i „silne na żywioły”
usunięte):

| Kamień | 1. | 2. |
|---|---|---|
| Diament | INT 8 (13) | Silny na Mistyków 9 (15%) |
| Rubin | STR 8 (13) | Silny na Diabły 9 (15%) |
| Jadeit | Max PE 500 (800) | Silny na Zwierzęta 9 (15%) |
| Szafir | DEX 8 (13) | Silny na Orki 9 (15%) |
| Granat | Max PŻ 1000 (1600) | Silny na Ludzi 6 (10%) |
| Onyks | VIT 8 (13) | Silny na Nieumarłych 9 (15%) |
| Ametyst | Silny na potwory 6 (10%) | Silny na Metiny 6 (10%) |

Bonusy losowe (0–3):

- **Diament:** atak magiczny, obrona magiczna, obrażenia umiejętności,
  odporność na umiejętności – po 10 (16);
- **Rubin:** wartość ataku 200 (320), obrona 150 (240), średnie obrażenia
  i odporność na średnie – po 10 (16);
- **Jadeit:** Max PŻ 2000 (3200), Max PŻ% 12 (20), kradzież PŻ 6 (10),
  regeneracja PŻ 10, PŻ za zabicie 5;
- **Szafir:** silny na 4 klasy i odporność na 4 klasy – po 10 (16);
  Wilkołak usunięty (klasa wyłączona, bonus był pusty);
- **Granat:** bonusy PE bez zmian;
- **Onyks:** blok i unik 8 (13), odbicie 6 (10), odporność na krytyczne
  i przeszywające 8 (13);
- **Ametyst:** szansa na krytyk 5 (8%), na przeszywające 5 (8%), wartość
  ataku 100 (160). Sungma usunięte.

Zmiana dotyczy kamieni tworzonych od teraz; bonusy ustawiają się przy
tworzeniu kamienia. Klient nie powinien wymagać aktualizacji: kamień
wysyła numery statystyk, które klient zna z bonusów zwykłych przedmiotów
(do potwierdzenia w grze – opis kamienia).
