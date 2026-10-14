# Umiejętności 9. (Yohara)

Dziewiąte umiejętności klas z aktualizacji Yohara dla MT2009 PLUS 3.x – po jednej na klasę i specjalizację, uczone
wyłącznie z ksiąg 50569–50575 (już w świecie: `tools/yohara_items`, `yohara_items.sql`) przez postać z Poziomem
Czempiona. Znacznik: `MT2009_PLUS_SKILL9_V1 (…)`. Wzory i liczby z Owsapa v6.2.6 (`skill_proto` 176–183 – formuły GF),
zasady nauki z wiki (pl/en/tr/de) i z danych klienta GF 26.1.11 (`value1`/`value2` ksiąg).

| vnum | Umiejętność | Klasa / specjalizacja | Działanie |
|---|---|---|---|
| 176 | Trzęsienie | Wojownik (obie) | wręcz, cztery uderzenia w linii przed sobą (do ~550), do 8 celów |
| 177 | Światło Gwiazd | Ninja – sztylety | rzut gwiazdami, obszar wokół celu (200), zasięg 2000 |
| 178 | Strzał Wichury | Ninja – łuk | strzała (zużywa strzałę), obszar 200, zasięg 2500 |
| 179 | Piekielny Cios | Sura – broń | wręcz, do 4 celów |
| 180 | Fala Śmierci | Sura – czarna magia | magiczny pocisk, obszar 200, zasięg 2000 |
| 181 | Meteor | Szaman – smok | meteor na cel (liczony od razu przy rzucie, jak u Owsapa), obszar 500, podpalenie 20·k % |
| 182 | Tarcza Eteru | Szaman – leczenie | wzmocnienie grupy 50+8·k s: co 12 s szansa 0,4k+18k % (0/9/15/23 %) na ochronę 4·k s (0/2/3/5 s) – w tym czasie każdy cios jest blokowany |

Koszt PE 200+200·k (210/300/364/450), odnowienie 35+20·k s (36/45/51/60), Tarcza Eteru 386+80·k s (390/426/451/486) –
dokładnie tabele wiki. Burza Szponów (183) jest Likana – u nas nie ma Likana, nie ma wiersza.

## Nauka

- Księga 9. umiejętności: tylko od **1. Poziomu Czempiona**; każda próba czytania kosztuje **PD Czempiona: 2 000**
  poniżej M1 i **5 000** od M1 do G1 (`value1`/`value2` ksiąg w item_proto GF; wiki en/tr – pl wiki ma jeszcze stare
  „20 000”). Brak PD – nie czyta.
- Od 0 do M1 **księgami** (punktów umiejętności nie da się użyć: `DISABLE_BY_POINT_UP`, w kliencie `CANNOT_LEVEL_UP`):
  udana próba = +1 poziom, od 17 do 19 klasyczny los na M (de wiki), 20 = M1. M1 → G1 jak każda umiejętność
  (nasza reguła ksiąg: liczba udanych odczytów rośnie z poziomem). Szansa i czas klątwy jak przy innych księgach
  (`m2_book_wait`, Zwój Egzorcyzmu, Rada Pustelnika = 100 %).
- G1 → P: **Kamienie Duchowe** (quest `training_grandmaster_skill` pokazuje 9. umiejętność obok innych –
  `linux-port/docker/game/quest/skill9.lua` + krok Dockerfile „share: 9th skills and the Soul Stones”).
- Księga uczy tylko umiejętności **własnej** klasy i specjalizacji (ninja sztyletowy nie przeczyta Strzału Wichury).
- Reset umiejętności (zwoje, zmiana drogi) **nie kasuje** 9. umiejętności (to księgi, nie punkty); Księga Zapomnienia
  jej nie obniża (nie było punktów do oddania).
- Boty: **nie** – nie mają Poziomu Czempiona (decyzja właściciela przy Czempionie), więc żadna księga 9. umiejętności
  im się nie otworzy; AI ich nie używa.

## Gdzie co jest

| Część | Miejsce |
|---|---|
| Logika | `linux-port/overlays/playerbot/src/game/src/playerbot_skill9.h/.cpp` |
| Haki silnika | `edits.json` (24 zmiany w 6 plikach: `common/skill_length.h`, `char_skill.cpp`, `char_battle.cpp`, `char_affect.cpp`, `constants.cpp`, `battle.cpp`); generator `gen_edits.py`; `apply_skill9.py <game/src>` (Linux) i `Apply-Skill9Patch.ps1` (Windows, krok `tools/port/Apply-MT2009PlusEngine.ps1` po Żyłach Jadeitu) |
| Baza | `linux-port/docker/mariadb/playerbot/yskill9.sql` (`tools/yskill9/gen_yskill9_sql.py`, dane `tools/yskill9/yskill9_data.py`; `apply.sh`): wiersze 176–182 i nowe członki `setFlag` (`ATTACK_BLEEDING`, `PARTY` = bit 28) |
| Quest | `linux-port/docker/game/quest/skill9.lua` (Kamienie Duchowe) |
| Klient | `client-patches/client-2.0.30/tools/yskill9` (paczka `yskill9`, skilldesc/skilltable), `root/playersettingmodule.py` (miejsce 7 okna umiejętności), `root/uiaffectbar.py` (ikony Tarczy Eteru), exe `client-patches/exe` (`ENABLE_NINTH_SKILL`) |

## Haki (edits.json)

- `skill_length.h`: `SKILL_FINISH` … `SKILL_CHEONUN` (176–182) i `SKILL_ILIPUNGU` (183).
- `IsLearnableSkill`, `CanUseSkill`: 9. umiejętność tylko klasy i specjalizacji postaci.
- `LearnSkillByBook`: Czempion i PD Czempiona (sprawdzenie przed, opłata przy próbie), czytanie od 0, indeks tabeli
  w logu nigdy ujemny. `SkillLevelUp`: księgą od 0, bez blokady 17–19, klasyczny los M. `SkillLevelDown`: nie.
  `ResetSkill`: zachowuje 176–182.
- `IsUsableSkillMotion`: ruchy 9 i 24 (+25 na stopień) – bez tego klient dostawał `SKILL_HACK` i rozłączenie.
- `UseSkill`: Meteor liczony od razu na celu. `FuncShoot`: Strzał Wichury jak Trująca Strzała (łuk + strzała),
  Światło Gwiazd i Fala Śmierci jak inne pociski, Meteor bez drugiego trafienia. `IsShootSkill` / `is_distance_skill`:
  177, 178, 180, 181. `GetMeleeSkillDistanceAttack`: Trzęsienie 600.
- `ComputeAffect`: Tarcza Eteru uruchamia losowanie co 12 s (zdarzenie na postać); ochrona = afekt **608**
  (`AFFECT_CHEONUN_INVINCIBILITY`, jak Owsap), efekt `chunwoon_moojuk.mse` (`SpecificEffectPacket`).
  `Damage`: przy afekcie 608 cios → `DAMAGE_BLOCK`. `RemoveSkillAffect` / `IsGoodAffect`: Tarcza Eteru jest dobrym
  afektem (zdejmuje ją Rozproszenie, pojedynek).

## Czego nie ma

- **Bonus Precyzji** (`HIT_PCT`, 0,4k+16k %): nasz silnik nie ma statystyki Precyzji (liczy się ona tylko przy wymaganiu
  map Sung Ma, którego nie mamy) – wiersze mają `szPointOn2 = NONE`, w opisie umiejętności brak tej linii.
- Wizualny efekt aury Tarczy Eteru na postaci (GF: flagi `AFF_CHEONUN_*` i efekty exe) – jest ikona afektu i błysk
  `chunwoon_moojuk.mse` przy każdej ochronie.

## Sprawdzone (14.10.2026)

Pełna kompilacja i linkowanie game + db na kopii drzewa testowego ze wszystkimi łatkami (enginefixes … shipdefense,
czempion, talizmanwoli, jadeit) + skill9 (`m2-libs:check`); `yskill9.sql` dwa razy w czystym MariaDB 11.8 (zrzut
`world.skill_proto`); `apply_skill9.py` dwa razy (drugi raz 0 zmian).
