# Szybkie otwieranie skrzynek – limit tylko dla skrzynek

Poprawka silnika, znacznik `MT2009_PLUS_VEKIRION_V1` (każda zmiana ma własny dopisek w nawiasie).
**Autor pomysłu i klienta: Vekirion** (paczka z 3 października 2026: „Szybkie otwieranie paczek”).
Nakładana raz, przy przygotowaniu wydania (`tools/port/Apply-MT2009PlusEngine.ps1`, po
`mountquickswap`); `Apply-VekirionPatch.ps1` i linuksowy bliźniak `apply_vekirion.py` czytają ten
sam `edits.json`. Zmieniony plik: `char_item.cpp` (już na liście `launcher/server-update-files.mod.txt`).

## Skąd zmiana

Klient Vekiriona otwiera Ctrl + PPM cały stos skrzynek (do 50 sztuk, `uiinventory.py`,
`ItemOpenAllRunner`). Silnik przyjmuje 5 użyć przedmiotu na 500 ms (`CHARACTER::UseItem`,
`PulseManager`, `ePulse::ItemUse`), resztę po cichu odrzuca. Jego notatka do serwera: zmienić w tej
linii 5 na 60. To podniosłoby limit dla **każdego** przedmiotu – 60 mikstur, zwojów czy
przedmiotów z questów na pół sekundy.

## Co robi poprawka

| Dopisek | Gdzie | Co |
|---|---|---|
| `(chest keys)` | przed `CHARACTER::UseItemEx` | Dwa własne klucze `PulseManager` (wartości spoza nazw `ePulse`, `common/PulseManager.h` bez zmian) i stała 60. |
| `(chest rate)` | `CHARACTER::UseItem` | Przedmiot typu `ITEM_GIFTBOX` (skrzynki, Cor Draconis, paczki z ItemShopu – wszystko, co otwiera `DropSpecialItemGroup` w `UseItemEx`) liczy się na własnym liczniku: do **60 na 500 ms**. Każdy inny przedmiot zostaje przy 5 na 500 ms na `ePulse::ItemUse`; skrzynka nie zjada tego limitu, a mikstury nie zjadają limitu skrzynek. |
| `(chest notice ds)` | `UseItemEx`, `ITEM_GIFTBOX` | „Before you open the Cor Draconis…” (brak questa Alchemii) raz na sekundę zamiast raz na każdą odrzuconą skrzynkę. |
| `(chest notice room)` | `UseItemEx`, `ITEM_GIFTBOX` | „You need room for atleast 3 slot item…” – to samo. |

## Pełny plecak i drop przy szybkim otwieraniu

Nic się nie zmienia w tym, co dostaje gracz: każda skrzynka jest obsługiwana osobno, po kolei, jak
dotąd. Przed każdą `UseItemEx` sprawdza 3 wolne pola (`GetEmptyInventory(3)`) i quest Alchemii dla
Cor Draconis; gdy plecak się zapełni w trakcie serii, następne skrzynki zostają zamknięte (nic nie
spada na ziemię z powodu tempa), a komunikat przychodzi raz na sekundę. Przedmiot z jednej skrzynki,
który nie zmieści się w plecaku (`AutoGiveItem`), leży na ziemi z właścicielem jak zawsze. Klient
przed otwieraniem Cor Draconis liczy wolne miejsca na stronie Alchemii i staje, zanim kamień nie
miałby gdzie trafić. Flaga `box_use_limit_time` (`g_BoxUseTimeLimitValue`, domyślnie 0) działa dalej.

Przyciski „Otwórz / Otwórz 10” w podglądzie skrzynki (`uichestpreview.py`, osobny port) korzystają z
tego samego licznika – razem z Ctrl + PPM dzielą 60 użyć na pół sekundy; użycie ponad limit serwer
odrzuca, a Ctrl + PPM wysyła je ponownie (do 2 razy).

Bez zmian w exe i w protokole.

Zmiana już nałożona (jest jej znacznik) jest pomijana; zmiana, której kodu nie ma dokładnie raz,
przerywa całość, zanim cokolwiek zostanie zapisane.

- `Apply-VekirionPatch.ps1 -SourceDir <game/src>` – Windows (Apply-MT2009PlusEngine.ps1);
- `apply_vekirion.py <game/src>` – to samo na Linuksie/VPS.
