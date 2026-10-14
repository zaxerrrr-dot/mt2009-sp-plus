# Bonusy i żywioły: tryb mt2009 albo global – `MT2009_PLUS_GLOBAL_BONUS_V1`

Właściciel, 14.10.2026: „zmiany bonusów i żywiołów dokładnie jak w wydaniu Tieru (2.2.31, „Bonusy jak na serwerze
globalnym”), ale z opcją w .env: albo bonusy MT2009 PLUS (jak dotąd), albo bonusy serwera globalnego”, a w trybie
global żywioły na wszystkich potworach. Jedna zmienna, **`M2_BONUS_MODE`** (`linux-port/docker/.env.example`):

| | `mt2009` (domyślnie) | `global` |
|---|---|---|
| Maks. PŻ | do 1500 | do 2000 (szansa 35, 500/500/1000/1500/2000) |
| Maks. PE | do 250 (bransoleta, buty, naszyjnik) | do 80 na bransolecie i butach, do 200 na naszyjniku |
| Regeneracja PŻ / PE | do 12% | do 30% (4/8/12/20/30) |
| Odporność na ogień / błyskawice / wiatr | tylko talizman (5–25%) | też zbroja, bransoleta, hełm: 2/4/6/10/15%; talizman dalej 5–25% |
| Szansa na bonus DOŚ | – | buty, naszyjnik, tarcza: do 20% |
| Szansa na podwójną ilość przedmiotów | – | bransoleta, kolczyki: do 20%, podnosi szansę dropu (20% = o 20% częściej) |
| Wytrzymałość, reg. wytrzymałości, czas trwania umiejętności, odbicie strzał, stałe PD | losują się | nie losują się na broni, zbroi i biżuterii (kostiumy i talizman bez zmian) |
| Szybkość ruchu | buty, kolczyki | buty, kolczyki (bez zmian) |
| Żywioły potworów | zasady właściciela z 7.10 (`zywioly_moby.sql` + pliki Yohary) | to samo **plus** żywioł każdego potwora z oryginalnych danych |
| Odporność na żywioł gracza wobec potwora tego żywiołu | odejmuje cały swój procent (strop 80%) – Digi Rasta | 30% swojej wartości (15% = 4,5% mniej obrażeń), jak w oryginalnym kodzie gry |

Przedmioty **zachowują wszystkie bonusy**, które mają – w obu kierunkach zmienia się tylko pula losowania
(`player.item` nie jest ruszane). Przełączać można dowolnie często; działa po restarcie (migrator).

## Co zmienił Tieru (2.2.31) i jak to jest u nas

| Tieru | U nas |
|---|---|
| `apply.sh`: migracja `item_attr_global_2231` (jednorazowa, UPDATE po wartościach paczki + INSERT 5 wierszy) | `mariadb/playerbot/bonusy_global.sql` – te same wartości, po nazwie bonusu (`apply` = `POINT_*`, nigdy po numerze); kopia 14 wierszy trybu mt2009 w `world.item_attr_mt2009`, `bonusy_mt2009.sql` oddaje je z powrotem |
| `apply.sh`: `mob_elements_r40250_2231` (bity 11 i 14 na 47 + 63 vnumach z r40250) | `tools/zywioly/gen_zywioly_moby_global.py` → `zywioly_moby_global.sql`: kolumny Att* oficjalnego mob_proto (Owsap = pl-wiki; zawiera całą listę Tieru) dla każdego potwora, wszystkie 6 żywiołów |
| `battle.cpp`: odkomentowane `iAtk -= iAtk * 30 * resist / 10000` w `CalcAttBonus` | nasz `ElementsAttackBonus` (`playerbot_elements.cpp`) już liczy odporność; w trybie global bierze 30% jej wartości (`BonusModeElementResist`) – bez drugiego, podwójnego odejmowania |
| `item_manager.cpp`: `POINT_ITEM_DROP_BONUS` dodany do `item_drop_bonus` | `edits.json` (drop) → `BonusModeItemDropBonus`, tylko w trybie global |
| klient 2.0.45: `ATTR_MAX_VALUES` (maks. wartości świecą na pomarańczowo) | root `localeinfo_point.py`: zestaw mt2009 i global, `SetBonusMode` po komendzie serwera `BonusMode 0/1` |

Szansa na bonus DOŚ (`POINT_EXP_DOUBLE_BONUS`) działa w silniku od zawsze (`char_battle.cpp`) – nic do zmiany, w trybie
mt2009 po prostu się nie losuje. Polskie nazwy wszystkich pięciu bonusów są w `locale_game.txt` klienta (np. „Szansa na
podwójną ilość Przedmiotów: %d%%”) – bez zmian w exe i bez nowych punktów (numeracja POINT/APPLY bez zmian).

Nie przeniesione (u nas własne): launcher, boty, Seon-Pyeong (jest), towarzysz, pasek życia celu.

## Konflikt z naszymi żywiołami (`MT2009_PLUS_ELEMENTS_V1`, Autor: Digi Rasta) – decyzje

1. **Jeden wiersz `item_attr` na bonus.** Odporność na ogień/błyskawice/wiatr ma u nas wiersz talizmanu (5–25%, tylko
   kolumna `pendant`). W trybie global wiersz ma wartości Tieru (2–15%) i kolumny zbroi/bransolety/hełmu, a rdzeń daje
   talizmanowi jego własne 5% na poziom (`BonusModeAttrValue` w `CItem::AddAttr`, `edits.json` attr value) – talizman
   losuje tak samo w obu trybach. Lód/ziemia/mrok – bez zmian (tylko talizman).
2. **Wzór odporności:** mt2009 – nasz (pełny procent, strop 80%); global – Tieru/oryginał (30%).
3. **Żywioły potworów w trybie global:** oficjalny żywioł wygrywa z naszymi regułami (np. Podziemne Lodowe potwory Groty
   1131–1137: lód zamiast błyskawicy mapy; Ezoteryczni Przywoływacze 791–795, Rakszas: wiatr; Piekielny Bastard: mrok –
   18 zmian); potwór bez oficjalnego żywiołu zachowuje nasz (nadpisania bossów właściciela); prawdziwe kopie oficjalnych
   potworów (ta sama nazwa: Cyklopi 9601–9605 itd.) dziedziczą żywioł źródła, przeróbki z Arezzo (mumie, skorpiony,
   małpy z Cyklopów) – nie. **Bez zmian:** Yohara (wszystkie `*_zywioly.sql` i `YOHARA_ELEMENTS*` – już według wiki),
   Świątynia Zodiaku (żywioł piętra w czasie gry), Ruiny Atlantydy (reguła f), Metiny (zasada właściciela) i NPC.
   Tryb mt2009 nie potrzebuje kroku: `zywioly_moby.sql` przy każdym starcie zdejmuje bity z każdego moba spoza swojej
   listy.
4. **Klient** (bez zmian w exe): `mob_proto` klienta ma żywioły trybu mt2009 (krok `yfinal`). Ikona żywiołu celu w trybie
   global bierze żywioł z `root/zywioly_global.py` (generowany razem z SQL), gdy serwer przy logowaniu wyśle
   `BonusMode 1` (quest `zywioly`, `game.py`, `uitarget.py`).

## Pliki

- `linux-port/overlays/playerbot/src/game/src/playerbot_bonus_mode.cpp` – flaga `m2_bonus_global`, trzy funkcje wyżej;
  `playerbot_elements.cpp` – odporność przez `BonusModeElementResist`.
- `edits.json` (`item_manager.cpp` drop, `item_attribute.cpp` attr declare/value); `apply_bonusyglobal.py` (Linux/VPS),
  `Apply-BonusyGlobalPatch.ps1` (Windows, w `tools/port/Apply-MT2009PlusEngine.ps1` po szczelinie).
- `linux-port/docker/mariadb/playerbot/bonusy_global.sql`, `bonusy_mt2009.sql`, `zywioly_moby_global.sql`;
  krok `apply.sh` (po wszystkich plikach żywiołów): `world.item_attr_mt2009` pusta + global → `bonusy_global.sql`;
  niepusta + mt2009 → `bonusy_mt2009.sql`; global → `zywioly_moby_global.sql`; zawsze flaga `m2_bonus_global`.
- `.env.example`, `docker-compose.yml` (środowisko migratora i gry), `tools/update.sh` (dopisuje klucz do starego .env),
  `seban-panel/env_schema.py` (sekcja „Świat i rates”, restart gry i migratora).
- Quest `zywioly`: `cmdchat("BonusMode ...")` przy logowaniu, opis żywiołów u Mistrza zależny od trybu.
- Klient root: `localeinfo_point.py`, `game.py`, `uitarget.py`, `zywioly_global.py` (nowy).

## Sprawdzenie

`M2_BONUS_MODE=global` → restart → log migratora „bonus mode: global – item_attr switched…”; Wzmocnienie Przedmiotu na
bransolecie losuje odporność na ogień do 15% i szansę na podwójne przedmioty; `/state` celu-potwora; powrót
`M2_BONUS_MODE=mt2009` → „item_attr back to the mt2009 set (12 rows)”, bonusy przedmiotów zostają.
