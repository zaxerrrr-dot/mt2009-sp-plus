# strzaly – amunicja jak na serwerze globalnym (Yohara 3.x, MT2009_PLUS_ARROWS_GLOBAL_V1)

Prośba właściciela (5 listopada 2026): „wgraj na serwer strzały i wartości bonusów jak na globalu, nie ograniczaj
ataku w moby jak dotychczas” + pl-wiki, kategoria Przedmioty/Amunicja.

## Silnik (`edits.json`, generator `gen_edits.py`)

| Znacznik | Plik | Co robi |
|---|---|---|
| `MT2009_PLUS_ARROWS_GLOBAL_V1 (no mob cut)` | `battle.cpp` | `CalcArrowDamage` nie tnie już zwykłego strzału łucznika w potwora, który nie jest jego celem, o 10–30% (30% na 1 poziomie, 10% od 60, połowa przy dwóch ofiarach), gdy strzał ma więcej niż jedną ofiarę – czyli każdej dodatkowej strzały `MT2009_PLUS_ARCHER_MULTISHOT` (gracze i boty). Na serwerze globalnym takiego cięcia nie ma: każda strzała bije potwora pełną siłą. |
| `MT2009_PLUS_ARROWS_GLOBAL_V2 (falloff)` | `battle.cpp` | Osłabienie z odległością jak na serwerze globalnym (decyzja właściciela, 5 listopada; wzór ze źródeł Owsapa, `CalcArrowDamage`): pełne obrażenia do 5 m (500) + premia `POINT_BOW_DISTANCE` (w metrach), potem −5% za każdy kolejny pełny metr (`iGap = odległość/100 − 5 − premia`, `procent = 100 − 5·iGap`): 10 m – 75%, 15 m – 50%, 20 m – 25%, od 25 m – 0. Tak samo w potwora i w gracza, dla każdej strzały i umiejętności łucznika. **Kołczan** (strzała z limitem czasu rzeczywistego, 8010–8012) nie traci obrażeń. Zastępuje osłabienie `MT2009_PLUS_ARROW_RANGE_V1` z wartości strzały (`value2/4/5`, teraz 0) – jego znacznik zostaje w komentarzu, więc `enginefixes` dalej się pomija. Wymaga nałożonego wcześniej `enginefixes`. |

Owsap (`Srcs/Server/game/src/battle.cpp`) liczy obrażenia strzały jako `rzut(łuk) × 2 + value3 strzały`; u nas
`(rzut(łuk) + value3) × 2` – bez zmian (nie było w zakresie). Premia +10% w bossy/minibossy/Metiny z paczki zostaje
(właściciel: zostaje).

Boty: `GetPlayerBotArrowGrade` (`playerbot_gear.h`) nie odrzuca już strzał po `value2/4/5` (silnik ich nie czyta) –
najlepsza strzała to najwyższe `value3`, kołczan idzie przed każdym stosem; katalog ItemShopu V3 – kołczan od poziomu 0.

- `apply_strzaly.py <game/src>` – Linux/VPS; `Apply-StrzalyPatch.ps1` – Windows (`tools/port/Apply-MT2009PlusEngine.ps1`);
  oba czytają ten sam `edits.json`. Kolejność: dowolna. Przy wdrożeniu dopisać `strzaly` do listy łatek skryptu wdrożenia.

## Dane (`linux-port/docker/mariadb/playerbot/strzaly_global.sql`, krok w `apply.sh` po `refine_global.sql`)

| vnum | Przedmiot | Poziom | Atak / Atak magiczny (wiki) | Zmiana |
|---|---|---|---|---|
| 8000 | Drewniana Strzała | – | 3 / 1 | cena 5 sztuk za 1 Yang (wiki: 100 za 20 Yang; było 1 za 1 Yang) |
| 8001 | Bambusowa Strzała | 10 | 10 / 2 | – |
| 8002 | Kamienna Strzała | 30 | 15 / 3 | – |
| 8003 | Żelazna Strzała | 40 | 17 / 4 | – |
| 8004 | Stalowa Strzała | 45 | 20 / 5 | – |
| 8005 | Srebrna Strzała | 50 | 25 / 4 | – |
| 8010 | Kołczan (ItemShop, 14 dni) | 1 (było 35) | 25 / 4 | atak magiczny 0 → 4, bez zakresu osłabienia (`value2/4/5` 100/1300/2250 → 0) |
| 8011 | Kołczan (1 dzień) | 1 | 25 / 4 | **nowy**: Handlarka Różności (sklep 3), 100 000 Yang |
| 8012 | Kołczan (7 dni) | 1 | 25 / 4 | **nowy**: Handlarka Różności (sklep 3), 550 000 Yang |
| 30395 | Płonąca Strzała | – | – | nazwa jak na wiki (było „Ognista Strzała”, jak umiejętność i strzała 8006) |

Strzały nie mają linii bonusów (wiki: żadnych). Wartości 8000–8005 serwer miał już z `gf_wartosci.sql`; krok
zapisuje je jeszcze raz (poziom, `value1`, `value3`, zero w `value2/4/5`, bez bonusów). Kołczany 8011/8012 to kopie
8010 (tylko ninja, nielimitowane strzały – reguła `server-patches/quiver`, boty: `IsPlayerBotQuiver`; bez handlu,
upuszczania, sklepiku i magazynu); czas liczy się od zakupu. Poziom kołczanu w obu ItemShopach 35 → 0 (`apply.sh`). Cena raz (zmiana operatora zostaje). Idempotentne.

## Klient

`client-patches/client-2.0.30/tools/strzaly`: `patch_strzaly_client.py` (item_proto 8000–8005, 8010–8012, 30395;
item_list 8011/8012 z ikoną 08010; itemdesc 8000–8012 – strzały: osłabienie z odległością, kołczan: bez – i 30395; kołczany od poziomu 1), `build_strzaly_packs.py` (paczki gamedata + dbdata, po
wszystkich innych krokach, które je zapisują), `verify_strzaly.py`.
