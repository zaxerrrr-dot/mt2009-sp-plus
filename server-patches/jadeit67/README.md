# jadeit67 – biżuteria z jadeitu przyjmuje 6. i 7. bonus

`MT2009_PLUS_JADE_BONUS67_V1` (8.11.2026, właściciel: „napraw” – Obręcze Jadeitu odrzucały każdy 6/7 bonus).

## Przyczyna

`obreczjadeitu` (V1) wstawia w `CItem::AddRareAttribute`, `AddRareAttribute2`, `ChangeRareAttribute` i
`ChangeRareAttribute2` strażnika `if (Mt2009JadeBraceletType(...)) return false;` (linia Woli leżała wtedy w 6. bonusie).
`obreczjadeitu2` (`MT2009_PLUS_JADE_BASE_V1`, 3.11.2026) zamienia go na `Mt2009JadeBaseMigrate` – Precyzja i Wola są
od tego dnia atrybutem podstawowym (`player.item_yextra`), a 6. i 7. komórka należą do systemu 6/7. Zamiana usuwała
jednak razem ze strażnikiem znacznik V1, a skrypty patchy pomijają edycję tylko wtedy, gdy jej znacznik jest w pliku.
Każde kolejne nałożenie łańcucha na to samo drzewo (`yohara-deploy.sh`, `Apply-MT2009PlusEngine.ps1`) wstawiało więc
strażnika V1 z powrotem nad blokiem JADE_BASE – na serwerze testowym obręcze, kolie i klipsy z jadeitu odrzucały
71051, 71052, 72351 i Seon-Hae (Seon-Hae przyjmował przedmiot i odłamki, a dodanie i tak się nie udawało).

## Poprawka

4 edycje `item_attribute.cpp` (po jednej na funkcję, każda ze swoim znacznikiem): komentarz nad blokiem
`MT2009_PLUS_JADE_BASE_V1 (...)`, który zawiera znacznik V1 danej funkcji – V1 już nigdy go nie wstawi. Na drzewie,
gdzie strażnik już wrócił, edycja go usuwa (pierwsza z `olds`), na świeżym drzewie tylko dopisuje komentarz.

Zasada (pl-wiki „6. i 7. bonus” – kolumny bransolet, naszyjników i kolczyków; „Biżuteria może mieć 2 podstawowe
bonusy”): Precyzja i Wola jadeitu to linie podstawowe przedmiotu, żaden przedmiot 6/7 ich nie zmienia ani nie usuwa;
6. i 7. bonus dochodzą jak na każdej biżuterii (dwa), 71052 / 72351 losują tylko je, ulepszenie przenosi linie
podstawowe (`Mt2009JadeBraceletV2Refine`) i zostawia 6/7 bonusy skopiowane przez silnik (V1 `Mt2009JadeBraceletWrite`,
który czyścił komórki 6/7, nie jest już wołany). Stary przedmiot z linią podstawową w 6./7. komórce przenosi ją
najpierw do bazy. Odłamki Seon-Hae dla poziomu 105: Żółte Lśniące (39080), jak u Owsapa (`67AttrMaterial`).

Boty: `playerbot_bonus67_bots.h` – biżuteria z jadeitu (poziom 105) w zakresie bonusów 6/7 jak inna biżuteria.

- Po `obreczjadeitu2` (kotwice to jego bloki JADE_BASE). Linux/VPS: `python3 apply_jadeit67.py <game/src>`;
  Windows: `Apply-JadeIt67Patch.ps1 -SourceDir <game/src>` (`tools/port/Apply-MT2009PlusEngine.ps1`).
  `gen_edits.py [<game/src>]` tworzy `edits.json` i sprawdza kotwice.
- Format: `olds` – lista szukanego kodu; pierwszy znaleziony dokładnie raz jest zastępowany przez `new`.
