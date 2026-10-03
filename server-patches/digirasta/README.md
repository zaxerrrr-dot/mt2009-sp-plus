# Systemy Digi Rasty (2 października) – Rytuał Przebudzenia, kamienie duchowe do +9, koń do 30 poziomu

**Autor: Digi Rasta** (paczka „nowy-system” v0.16, zbudowana pod 2.17.1). Systemy są przeniesione do
MT2009 PLUS jako nasz kod – bez haków `zastosuj.py`: zmiany silnika są tutaj (`edits.json`), reszta
w naszych zwykłych miejscach (niżej). Znaczniki: `MT2009_PLUS_AWAKENING_V1`, `MT2009_PLUS_SOULSTONE9_V1`,
`MT2009_PLUS_HORSE30_V1`.

## Zmiany silnika (`edits.json`)

| Znacznik | Plik | Co robi |
|---|---|---|
| `MT2009_PLUS_AWAKENING_V1 (declare)` | `char_item.cpp` | deklaracje haków z `playerbot_awakening.h` |
| `MT2009_PLUS_AWAKENING_V1 (do refine)` | `char_item.cpp` | `DoRefine`: broń 75 +9 → broń przebudzona +0 (receptura 7110) i kamień duchowy +4…+8 → +1 stopień (receptury 7204–7208) – tylko zwykłe okno zwykłego Kowala; rytuał i broń przebudzona nigdy u Kowala gildii ani w Wieży Demonów |
| `MT2009_PLUS_AWAKENING_V1 (do refine proto)` | `char_item.cpp` | `DoRefine` sprawdza proto wyniku, nie `refined_vnum` (0 dla rytuału i kamieni) |
| `MT2009_PLUS_AWAKENING_V1 (do refine no burn)` | `char_item.cpp` | nieudane ulepszenie broni przebudzonej jej nie niszczy i nie obniża |
| `MT2009_PLUS_AWAKENING_V1 (sockets)` | `char_item.cpp` | broń przebudzona ma zawsze 3 gniazda |
| `MT2009_PLUS_AWAKENING_V1 (scroll no burn)` | `char_item.cpp` | `DoRefineWithScroll`: to samo przy zwojach |
| `MT2009_PLUS_AWAKENING_V1 (refine info)`, `(refine info recipe)` | `char_item.cpp` | okno ulepszenia pokazuje rytuał / krok kamienia jako ulepszenie do wyniku |
| `MT2009_PLUS_AWAKENING_V1 (smith takes)`, `(smith window)` | `char_item.cpp` | Kowal przyjmuje broń 75 +9 i kamień +4…+8 (`refined_vnum` zostaje 0) |
| `MT2009_PLUS_SOULSTONE9_V1 (cracked)` | `char_item.cpp` | pęknięty kamień w gnieździe nie blokuje kamienia „rodzaju 0” |
| `MT2009_PLUS_AWAKENING_V1 (boss drop)` | `char_battle.cpp` | Kamień Przebudzenia (30670) z bossów tabeli `AWAKENING_BOSS_DROPS` |
| `MT2009_PLUS_HORSE30_V1 (black steed)` | `char_horse.cpp` | koń 30 poziomu to Czarny Rumak (rasa 20119), bez odcienia gildii |

Haki (`AwakeningSpecialRefineResult`, `AwakeningSpecialRefineSet`, `AwakeningIsAwakenedWeapon`,
`AwakeningCreateBossDrop`) są zdefiniowane w nakładce botów,
`linux-port/overlays/playerbot/src/game/src/playerbot_awakening.h`.

- `Apply-DigiRastaPatch.ps1` – Windows (`tools/port/Apply-MT2009PlusEngine.ps1`);
- `apply_digirasta.py <game/src>` – Linux/VPS; oba czytają ten sam `edits.json`.

Zmiana już nałożona (jest jej znacznik) jest pomijana; zmiana, której kodu nie ma dokładnie raz,
przerywa całość, zanim cokolwiek zostanie zapisane.

## Rytuał Przebudzenia

Broń 75 +9 + Kamień Przebudzenia (30670) + 200 000 000 Yang u Kowala (szansa 100%) → broń przebudzona +0;
bonusy i kamienie przechodzą. Pary: Zatruty Miecz → Śmiercionośne Ostrze (210), Lwi Miecz → Księżycowy
Miecz (220), Skrzydła Demona → Nóż Strumienia (1160), Stalowy Łuk Kruka → Upiorna Kusza (2190), Miecz Żalu →
Zabójca Żółt. Smoka (3170), Bambusowy Dzwon → Hibiskusowy Dzwon (5150), Wachlarz 8 Trigramów → Wachlarz
Leżąc. Smoka (7170). Statystyki jak w jego `10_przebudzenie.sql`: poziom 90…105, Silny przeciwko ludziom
−15…−50%, przeciwko potworom +2…+15%, bez bonusu średnich/umiejętności.

Ulepszanie +0 → +9 (receptury właściciela, Yang i szansa z paczki; porażka nie niszczy i nie obniża):

| Krok | Materiały | Yang | Szansa |
|---|---|---|---|
| +0→+1 | 2× Zdobycz Dzikusa | 5 mln | 90% |
| +1→+2 | 2× Shuriken + 1× Serce Wojownika | 8 mln | 85% |
| +2→+3 | 3× Biała Perła | 12 mln | 80% |
| +3→+4 | 3× Niebieska Perła | 16 mln | 75% |
| +4→+5 | 3× Krwawa Perła | 22 mln | 70% |
| +5→+6 | po 3× Biała, Niebieska, Krwawa Perła | 30 mln | 60% |
| +6→+7 | 1× Smocza Łuska + 1× Smoczy Szpon | 50 mln | 50% |
| +7→+8 | 8× Smocza Łuska + 8× Smoczy Szpon | 100 mln | 40% |
| +8→+9 | 15× Smocza Łuska + 15× Smoczy Szpon | 200 mln | 30% |

Kamień Przebudzenia: bossowie 75–97 3–4%, Beran-Setaou (Leże Smoka) i Azrael 10%, bossowie 103–107 5–7%,
Królowa Dżungli (Starożytna Dżungla) 12% – `playerbot_awakening.h`. Razador i Nemere go nie dają
(decyzja właściciela z 3 października; wcześniej 15% w `boss_drop` ich questów).

## Kamienie duchowe +0…+9

Od +4 u Kowala: Magiczny Pył 8/12/18/25/35 i (od v0.17) Olejek Niebios 1/1/2/2/3, 5/10/20/40/80 mln Yang,
50/40/35/30/25%; porażka niszczy kamień.
Wartości +5…+9 jak w jego `30_kamienie.sql`; każdy +5…+9 ma swój „rodzaj” (`value5`), więc dwa różne nie
blokują się nawzajem. Klient pokazuje wszystkie 7 bonusów przedmiotu (`root/uitooltip.py`).

## Olejek Niebios (v0.17) i poprawki klienta (v0.17.2)

**Autor: Digi Rasta** (paczka „nowy-system” v0.17 / v0.17.2: `66_olejek.sql`, receptury w `30_kamienie.sql`,
wiersz `BOSS_DROP_TABLE`, `klient.py`), przeniesione jako nasz kod, bez haków `zastosuj.py`. Znacznik
`MT2009_PLUS_HEAVEN_OIL_V1`.

- **Olejek Niebios (71056)** – w danych moda unikat na 5 dni bez działania; teraz zwykły materiał (typ 5, bez
  limitu czasu, handlowalny, stos 200) i drugi składnik ulepszania kamieni duchowych u Kowala: +4→+5: 1,
  +5→+6: 1, +6→+7: 2, +7→+8: 2, +8→+9: 3 (obok Magicznego Pyłu; Yang i szanse bez zmian) – `apply.sh`.
- **Drop** (`HEAVEN_OIL_BOSS_DROPS` w `playerbot_awakening.h`, ten sam hak co Kamień Przebudzenia, jednostki
  na 10 000): Silna Lodowa Wiedźma (1192, Grota Wygnańców 1) 3% – jak w jego paczce; Beran-Setaou (2493, Leże
  Smoka) 3%; Królowa Dżungli (9714, Starożytna Dżungla – najtrudniejszy loch Arezzo, od 95 poziomu) 10%.
- **Boty**: cena 5 000 000 Yang (`playerbot_price_tables.h`), nigdy do kupca (`IsPlayerBotAwakeningGoods`), towar
  na stragan (materiał ulepszania). Bot od 75 poziomu z kamieniem duchowym +4…+8 w plecaku sam ulepsza go
  u Kowala (`ManagePlayerBotSoulStoneStep`, najniższy stopień najpierw) – tylko gdy ma pył, olejek i dwa razy
  opłatę ponad rezerwę; po każdej próbie lub odmowie 10 minut przerwy (bez pętli przy braku olejku). Olejek
  na najbliższy krok trzyma w plecaku, resztę wystawia; kupuje go ze straganów, gdy brakuje tylko olejku.
- **Klient** (`client-patches/client-2.0.30`): rekord 71056 i nowy opis w `itemdesc.txt`; poprawki z v0.17.2 –
  Yut Nori: okienko „rzuć jeszcze raz” bez rekurencji (`uiminigameyutnori.py`, `Hide()` zamiast `Close()`),
  podgląd skrzynki: duże liczby skracane i od prawej (`uichestpreview.py`), ikony w `item_list.txt` (7170 →
  `07180.tga`, nowy wiersz 22030).

## Koń do 30 poziomu

Quest `konie` (Stajenny, „Szkolenie konia”): poziomy 1–9 / 11–19 / 21–28 za Medale Konne, karmę, Materiały
Rzemieślnicze i Yang zamiast misji treningowych (`pony_levelup`, `horse_levelup` – nie są już kompilowane);
10→11 i 20→21 zostają misjami; 29→30 Próba Czarnego Rumaka (50 Łuczników Setaou w 30 minut, od 75 poziomu).
Od 21 poziomu koń daje stały bonus (Potwory/Bossy/Metiny 1/1/1 … 5/5/5%). Juki do 30 poziomu konia
(`horse_inventory`, tabela też w kliencie `root/uihorseinventory.py`). Boty: `playerbot_horse30.h`.

## Gdzie jest reszta

- dane: `linux-port/docker/mariadb/playerbot/apply.sh` (przy każdym starcie);
- questy: `linux-port/docker/game/quest/konie.quest`, `horse_inventory.quest`, `razador_dungeon.quest`,
  `nemere_dungeon.quest`; Dockerfile (lista questów, usunięcie starych misji, Broszura Szermierki w 50121);
- boty: `playerbot_awakening.h`, `playerbot_horse30.h`, ceny w `playerbot_price_tables.h`;
- klient: `client-patches/client-2.0.30/tools/digirasta/patch_digirasta_client.py` (item_proto, item_list,
  itemdesc, mob_proto) i `client-patches/client-2.0.30/root/` (`uitooltip.py`, `uihorseinventory.py`,
  `uiattributelist.py`).
