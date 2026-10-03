# Ranking tygodniowy i tytuły (3 października)

Na podstawie systemu rankingu tygodniowego z plików Arezzo (byLUZER: `char_weekly.cpp`,
`char_titles.cpp`, blok sezonu w `main.cpp`, `WeeklyRewards` w bazie, okno
`new_uiweeklyrank.py`). Przerobione na nasz kod: bez nowych pakietów, bez zmian exe, bez nowych
kolumn w `TPlayerTable` – wszystko idzie poleceniami czatu (`/ranking`, linie `WRANK`).

Zmiany silnika opisane w `edits.json`, każda z własnym znacznikiem
`MT2009_PLUS_WEEKLY_RANKING_V1 (...)`. Reszta systemu (liczniki, sezon, tytuły, bonusy, okno)
jest w nakładce botów: `playerbot_weekly_rank.h`.

| Znacznik | Plik | Co robi |
|---|---|---|
| `(declare)`, `(table)` | `cmd.cpp` | polecenie `/ranking` (`do_weekly_rank`) dla okna klienta |
| `(grade)`, `(step)`, `(strength)` | `DragonSoul.cpp` | udane ulepszenie Smoczego Kamienia (klasa, stopień, siła) liczy się do kategorii Alchemia |
| `(login)` | `input_login.cpp` | przy wejściu do gry bonusy posiadacza tytułu są ustawiane według bieżącego sezonu (stare zdejmowane) |

Pozostałe liczniki są w nakładce, bez zmian silnika: zabójstwa (`BattlePassOnKill`,
`BattlePassOnKillShared`), zabici gracze (`PlayerBotLegendOnDeath`), udane ulepszenia
(`BattlePassOnStat`, `PLAYER_STATS_REFINE_SUCCESS_FLAG`), ukończone wyprawy
(`DungeonPanelUpdateRanking`, czyli `d.update_ranking` w questach lochów).

## Kategorie, tytuły i bonusy (miejsca 1 / 2 / 3)

| Kategoria | Tytuł | Bonus |
|---|---|---|
| Zabite potwory | Łowca I/II/III | silny przeciwko potworom +15 / +8 / +4% |
| Zniszczone Metiny | Niszczyciel | silny przeciwko potworom +15 / +8 / +4% |
| Pokonane bossy (ranga ≥ boss, nie kamień; każdy, kto zadał obrażenia) | Pogromca Bossów | silny przeciwko bossom +15 / +8 / +4% |
| Zabici gracze (PvP; ta sama para zabójca–ofiara liczy się raz na 10 min) | Zabójca | silny przeciwko ludziom +15 / +8 / +4% |
| Ukończone wyprawy | Podróżnik | silny przeciwko potworom +15 / +8 / +4% |
| Udane ulepszenia przedmiotów (kowal i zwoje) | Kowal | max PŻ +2500 / +2000 / +1500 |
| Alchemia (udane ulepszenia Smoczych Kamieni) | Alchemik | wartość ataku +75 (każde miejsce, jedna wartość od właściciela) |
| Poziom (poziom, potem exp) | Mistrz Poziomów | silny przeciwko potworom i ludziom +15 / +8 / +4% |

Bonusy z kilku tytułów się sumują. Są to własne efekty (typy 592–596, zakres 500–599 nie
znika po śmierci), nakładane i zdejmowane co minutę i przy logowaniu – gracze i boty tak samo.

## Sezon

- Tabela `player.weekly_rank_state` (ustawienia w obu panelach): włączony/wyłączony, długość
  w dniach (7 = od poniedziałku 00:00 do poniedziałku 00:00 czasu serwera), numer i koniec.
- Liczniki w pamięci rdzenia, dopisywane do `player.weekly_rank_score` raz na minutę
  (`value = value + delta`), nigdy zapis przy każdym zabójstwie.
- 90 s po końcu sezonu jeden rdzeń (`GET_LOCK` + warunkowy `UPDATE`) zapisuje top 3 każdej
  kategorii jako posiadaczy tytułów na następny sezon (`player.weekly_rank_title`), otwiera nowy
  sezon i ogłasza wyniki jednym ogłoszeniem. Zostają 4 ostatnie sezony.
- GM: `/ranking koniec` (sezon kończy się teraz), `/ranking przeladuj`.

## Pliki

- `edits.json` – zmiany (plik, znacznik, stary i nowy kod);
- `Apply-WeeklyRankPatch.ps1` – Windows (`tools/port/Apply-MT2009PlusEngine.ps1`, ostatnia);
- `apply_weeklyrank.py` – Linux/VPS: `python3 apply_weeklyrank.py <game/src>`; oba czytają ten sam `edits.json`.

Zmiana już nałożona (jest jej znacznik) jest pomijana; zmiana, której kodu nie ma dokładnie
raz, przerywa całość, zanim cokolwiek zostanie zapisane.
