---
title: Poprawki MT2009 PLUS
group: serwer
category: Serwer i administracja
order: 175
keywords: poprawki, patche, silnik, server-patches, zmiany
---
Lista poprawek silnika i dodatków, które MT2009 PLUS nakłada na serwer Tieru. Przychodzą w aktualizacjach – nic nie trzeba robić ręcznie. Kod i opis każdej są w repozytorium, w folderze [`server-patches`](https://github.com/zaxerrrr-dot/mt2009-sp-plus/tree/main/server-patches).

## Alchemia

| Poprawka | Co zmienia |
|---|---|
| Alchemia bez misji | każdy gracz dostaje kwalifikację alchemii przy wejściu do gry; Cor otwiera się, a kamień trafia do plecaka alchemii |
| `/dragon_soul` dla graczy | aktywacja i dezaktywacja zestawu kamieni działa u zwykłego gracza (wcześniej tylko GM) |
| Balans bonusów | wartość ataku i obrona z kamieni to płaskie punkty, a nie procent; usunięte martwe bonusy (żywioły, Sungma); dodane bonusy na rasy, potwory i Metiny. [Alchemia](/mt2009plus/alchemia/) |

## Wierzchowce i pety

| Poprawka | Co zmienia |
|---|---|
| Prędkość wierzchowców | serwer liczy dozwolony dystans z prędkości biegu każdego wierzchowca, więc szybkie mounty (np. Manni, Cerber) nie cofają |
| Bonusy wierzchowca raz | przed nałożeniem bonusów pieczęci stare są zdejmowane – nie kumulują się po śmierci czy teleporcie |
| Atak magiczny % z peta | bonus 131 jest naliczany (wcześniej był ignorowany) |

## Cor Draconis i szarfy

| Poprawka | Co zmienia |
|---|---|
| Drop dla botów | boty też losują Cor (5%) i szarfę (3%); ich zdobycz idzie do plecaka, nie na ziemię |
| Podział dropu | Cor albo szarfa, które przy podziale łupu przypadną botowi, trafiają do jego plecaka zamiast leżeć na ziemi z jego nazwą |
| Handel | Cor i szarfy można dawać i wystawiać w sklepach |
| Skrzydła Władcy Śmierci | wadliwe 85101–85104 nie wypadają z Metinów, bossów ani szkatułek |

## Sklepy i klient

| Poprawka | Co zmienia |
|---|---|
| Wyszukiwarka sklepów | szukanie jednego, klikniętego przedmiotu (vnum i socket) |
| Bez blokady wersji klienta | serwer wpuszcza klienta w każdej wersji |
| Lista serwerów | localhost zawsze pierwszy; świat COOP jako „Online: …” |

## Dodatki serwera

- Kostiumy, fryzury, nakładki, pety i wierzchowce GF26, bonusy kostiumów, sklep Ah-Yu.
- Szarfy (slot, łączenie, transmutacja), zestaw Władcy Śmierci, Nosiciel Światła, Diademy.
- ItemShop w grze z nowymi kategoriami.
- Kosz na śmieci, podgląd dropu potworów, przełącznik eventu wielkanocnego w panelu.
- Płynniejsza praca serwera przy wielu botach (budżet czasu na turę), emerytura botów w Seban Panelu, ikony kostiumów i petów w Seban Panelu.
- Boty: zakupy w ItemShopie, bonusowanie kostiumów, jazda na wierzchowcach, sprzedaż Corów i szarf (ok. 500 000 i 700 000 Yang przy kursie 100%; tanieje o 10% co 2 h bez sprzedaży, najwyżej o połowę), zapas mikstur 27101/27104.

Pełna historia zmian: [CHANGELOG na GitHubie](https://github.com/zaxerrrr-dot/mt2009-sp-plus/blob/main/CHANGELOG.md).
