# bonusy67b – bonusy 6/7 z wiki, runda 2

`MT2009_PLUS_BONUS67_WIKI_V1` (3.11.2026, właściciel: „Obrażenia od ataku przeciwko bossom” jak na wiki, „Jeśli masz
powyżej 90% PŻ, doznajesz obrażenia niższe o x%” tylko na zbroi, wszystkie bonusy 6/7 z pl-wiki „6. i 7. bonus”
i en-wiki „Bonuses”). Runda 1: `server-patches/bonusy67` (punkty 198–251). Po `antimagic` (kotwice to jej linie).

## Punkty 253–255 (ostatnie numery)

Typ bonusu przedmiotu ma 1 bajt (`player.item.attrtypeN` `tinyint unsigned`, `TPlayerItemAttribute::bType`, pakiety
do klienta) – po tej rundzie **wszystkie 256 numerów są zajęte** (`POINT_MAX_NUM` 256).

| Nr | Punkt | Działanie (`playerbot_bonus67.cpp`) |
|---|---|---|
| 253 | `POINT_RESIST_COMBAT` | „Jeśli masz powyżej 90% PŻ, doznajesz obrażenia niższe o x%”: cios otrzymany przez gracza/bota (zwykły albo umiejętność, od potwora albo gracza), gdy PŻ przed ciosem ≥ 90% maks. – obrażenia × (100 − x)/100, raz w `Bonus67Damage` (po obronie silnika i liniach bossów), strop `b67_combat_max` (10, maks. 50), nigdy poniżej 1. Trucizna, krwawienie, podpalenie i ciosy specjalne się nie liczą. |
| 254 | `POINT_BLEEDING_PCT` | „Atak krwawienia +x%”: zwykły cios gracza/bota (`NormalAttackAffect`, obok trucizny) z x% szans wywołuje krwawienie: 9 tików (od razu, potem co 3 s = 24 s), tik = maks. PŻ × stawka trucizny (postać 5%, potwór wg rangi 8/5/4/3/2,5/0,1% minus jego odporność na truciznę), regeneracja PŻ stoi. Potwór krwawi raz (potem odporny), postać za każdym razem; reguła poziomu jak trucizna; Metiny nie krwawią. Obrażenia jak trucizny (`DAMAGE_TYPE_POISON` – kolor trucizny, nie zabijają). Gracz dostaje na czacie „Krwawisz! (24 sek.)”. |
| 255 | `POINT_BLEEDING_REDUCE` | „Odporność na atak krwawienia +x%”: obrażenia krwawienia × (100 − 2x)% (wiki), szansy nie zmienia. Działa tylko w PvP (potwory nie mają ataku krwawienia). |

Punkty idą do klienta jako zmiana punktu (i przy logowaniu, lista antimagic): exe z `POINT_MAX_NUM` 256
(`client-patches/exe`, `MT2009_PLUS_BONUS67_WIKI_V1`) pokazuje je w oknie bonusów, starszy odrzuca typ ≥ 253
(`CPythonPlayer::SetStatus`). Dymek przedmiotu: `root/localeinfo_point.py`.

## Bossowie i Metiny

„Obrażenia od ataku przeciwko bossom” (wiki) to nasz punkt 234 `NORMAL_HIT_DAMAGE_BONUS_BOSS_OR_MORE` z rundy 1
(naszyjnik, rękawice, 1–5%, zwykłe ciosy). Wiki: potwory „Stopnia 5” (u nas `MOB_RANK_BOSS`, „należą do niego wszystkie
Metiny”) i „Stopnia Boss” (`MOB_RANK_KING`) – więc od tej rundy **Metin też jest bossem** dla 4 linii bossów
(`IsBoss`); flaga zdarzenia `b67_boss_no_metin` 1 przywraca starą regułę (bez Metinów).

## Silnik (`edits.json`, `gen_edits.py [<game/src>]`)

| plik | edycja |
|---|---|
| `common/length.h` | `(points)` – 253–255, `POINT_MAX_NUM` 256, `#define MT2009_PLUS_BONUS67_WIKI` |
| `char.cpp` | `(point change)`, `(point packet)`, `(login points)`, `(regen npc)`, `(regen pc)` |
| `battle.cpp` | `(bleeding)` |

7 edycji. Linux/VPS: `python3 apply_bonusy67b.py <game/src>`; Windows: `Apply-Bonusy67bPatch.ps1`
(`tools/port/Apply-MT2009PlusEngine.ps1`, po antimagic). Pełna przebudowa rdzenia (`POINT_MAX_NUM`); db bez zmian.
Nakładka (`playerbot_bonus67.cpp`, `playerbot_bonus.h`) kompiluje się też bez tej łatki (`#ifdef`).

## Baza

`apply.sh` (`MT2009_PLUS_BONUS67_WIKI_V1`, po kroku antimagic): ENUM `apply` w `item_attr` i `item_attr_rare` dostaje
3 nazwy po `POINT_ANTI_RESIST_MAGIC`, potem **raz na świat** (znacznik `rare_6_7_wiki_v3`, po `rare_6_7_wiki_v2`)
`bonusy67b_wiki.sql` (`tools/bonusy67/gen_bonusy67b_sql.py`). Nie czyści puli – pisze tylko swoje wiersze i kolumny:

| Wiersz | lv1–lv5 | Gdzie (maks. poziom) |
|---|---|---|
| `POINT_RESIST_COMBAT` | 1–5 | zbroja 5 |
| `POINT_BLEEDING_PCT`, `POINT_BLEEDING_REDUCE` | 1–5 | broń, zbroja, bransoleta, buty, naszyjnik, hełm, tarcza, kolczyki, talizman: 5 |
| `POINT_STEAL_SP` („x% obrażeń będzie dodanych do PE”) | 1–5 | broń 5, zbroja 5 (pl-wiki), buty 3 (pl), hełm/tarcza/bransoleta/kolczyki/naszyjnik 3 (en-wiki) |
| `POINT_STEAL_HP` („x% obrażeń będzie dodanych do PŻ”) | 1–5 | buty 3 (en-wiki) |
| `POINT_DAMAGE_SP_RECOVER` | – | wszystkie kolumny 0: runda 1 wzięła go za „Absorbuje obrażenia do x% jako PE”, a link wiki to obrażenia **zadane** (`STEAL_SP`); przedmioty zachowują swoje linie |
| `POINT_FIRST..FIFTH_ATTRIBUTE_BONUS` | – | + talizman 5 (en-wiki) |

## Klient i panel

`root/localeinfo_point.py` (słowa wiki), `root/uiattributelist.py` (3 linie okna bonusów – tylko gdy
`player.MAX_NUM` > numer, czyli z nowym exe), `client-patches/exe` (`Server/common/length.h` 253–255 i
`POINT_MAX_NUM` 256, `Mt2009Champion.cpp` `static_assert`, `PythonPlayerModule.cpp` `player.POINT_RESIST_COMBAT` …).
Panel: `dbeditor/items.py` (nazwy 253–255), `dbeditor/attrs.py` (opis). Boty: `playerbot_bonus.h` (wagi).

## Czego nie ma (brak numerów)

Zostało 0 wolnych numerów. Bez zmiany typu bonusu (1 bajt → 2 bajty: `player.item` i inne tabele z atrybutami,
`TPlayerItemAttribute`, wszystkie pakiety z przedmiotami, exe, nakładka botów) albo bez odzyskania martwych numerów
(sprawdzone wolne: 125 `PC_BANG_EXP_BONUS`, 126 `PC_BANG_DROP_BONUS` – żaden przedmiot ani pula ich nie używa) nie da
się dodać: „Niski ranking powoduje zwiększenie zadawanych obrażeń” (broń, hełm), „Odporność na upadek” (zbroja – upadek
z wierzchowca w Świątyni Zodiaku, tej mechaniki u nas nie ma), „Obrażenia od <umiejętność> +x%” (zbroja, 11), linie
umiejętności broni (absorpcja PŻ/PE, czas regeneracji, czasy trwania, bonusy na x s, ogłuszenie, odrzucenie – ok. 60;
część to umiejętności Likana), en-wiki: nieumarli / pół-ludzie / pustynia (+x% łącznej wartości).
