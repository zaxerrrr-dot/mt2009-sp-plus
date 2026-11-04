# bonusy67c – bonusy 6/7 z wiki, runda 3 (umiejętności)

`MT2009_PLUS_BONUS67_SKILL_V1` (4.11.2026, właściciel: „dodać WSZYSTKIE brakujące bonusy 6/7 dokładnie jak na wiki, bez
Likana” – lista `/opt/metin2/cache/yohara/BONUSY-67-BRAKUJACE.md`). Źródła: pl-wiki „6. i 7. bonus”, „Niski ranking
powoduje zwiększenie zadawanych obrażeń”, „Odporność na Upadek”, en-wiki „Bonuses” (sekcje 6/7), nazwy punktów jak
oficjalne `APPLY_*` (ENUM `item_attr_rare` Owsapa – koreańskie nazwy umiejętności). Runda 1: `bonusy67` (198–251),
runda 2: `bonusy67b` (253–255). **Nakładana po `wideattr`** (punkty idą nad jego linią `POINT_WIDE_END`).

Jedna tabela dla wszystkiego: `tools/bonusy67/bonusy67c_data.py` (numer, nazwa, rodzaj, nasza umiejętność, słowa wiki,
wartości, rodzaje przedmiotów, waga). Generatory: `gen_edits.py` (ta łatka), `tools/bonusy67/gen_bonusy67c_sql.py`
(`bonusy67c_wiki.sql`, nazwy ENUM), `tools/bonusy67/gen_bonusy67c_misc.py` (tabela nakładki
`playerbot_bonus67c_table.h`, dymki klienta `root/localeinfo_point.py`, nazwy panelu `dbeditor/items.py`).

## Punkty 256–318

| Nr | Rodzaj | Gdzie | Działanie (`playerbot_bonus67.cpp` / `playerbot_bonus67c.inc`) |
|---|---|---|---|
| 256 | „Niski ranking powoduje zwiększenie zadawanych obrażeń” | broń, hełm (wartość 1) | każdy cios gracza/bota (zwykły i umiejętność, PvM i PvP) × ranga: Agresywny +1%, Nieuczciwy +2%, Złośliwy +3%, Okrutny +5% (stopnie klienta z `GetAlignment()/10`: <0, ≤−4000, ≤−8000, ≤−12000); broń + hełm = ×2 |
| 257–259 | „Silny przeciwko pół-ludziom / nieumarłym / potworom pustyni (+x% łącznej wartości)” (en-wiki) | broń 3–15 / 3–15 / 4–20 | jak `ATTBONUS_PER_*` 210–217 (`Bonus67AttBonus`); pół-ludzie także przeciw graczom (`CalcPlayerBonus`) |
| 260–267 | „Absorbuje x% PŻ przy użyciu …” (Wir Miecza 2, Zasadzka 31, Powtarzalny Strzał 46, Duchowy Cios 80, Strzelający Smok 92, Smoczy Skowyt 93, Przywołanie Błyskawicy 107, Burzowy Szpon 108) | broń 1–5% | x% PŻ, które cios umiejętności zabrał ofierze, wraca do atakującego (każda ofiara obszarówki) |
| 268–275 / 276–283 | „Czas regeneracji …: -x sek. z 10% / 20% szans” (1, 20, 32, 47, 62, 76, 91, 106) | broń 1–5 s | przy użyciu umiejętności z tą szansą kolejny czas odnowienia krótszy o x s (zawsze ≥1 s zostaje); klient dostaje `HEADER_GC_SKILL_COOLTIME_END` (jak rękawice); obie linie – każda losuje, dłuższe cięcie |
| 284–286 | „Czas trwania aury miecza / krycia się / bezszelestnego chodu +x sek.” (4, 34, 49) | broń 2–10 s | +x s do afektu umiejętności (`ComputeSkill`, po % przedmiotów) |
| 287–294 | „Na x sek. otrzymujesz bonus do ataku przy użyciu …” (Wola Życia 6, Krąg Mieczy 21, Trująca Chmura 35, Trująca Strzała 50, Strach 64, Ognisty Duch 78, Pomoc Smoka 96, Leczenie 109) | broń 2–10 s | użycie umiejętności: Wartość Ataku +`b67_skill_att_pct` (5%) własnej Wartości Ataku na x s (afekt 830) |
| 295–297 | „… bonus do obrony przy użyciu …” (Czarowane Ostrze 63, Błogosławieństwo 94, Zwiększenie Ataku 111) | broń 2–10 s | Obrona +`b67_skill_def_pct` (5%) własnej Obrony na x s (afekt 831) |
| 298–299 | „Na x sek. zwiększa szybkość zaklęcia przy użyciu silnego ciała / mrocznej ochrony” (19, 79) | broń 2–10 s | Szybkość zaklęcia +`b67_skill_cast` (20%) na x s (afekt 832) |
| 300–304 | „… ma x% szans na ogłuszenie przeciwnika” (1, 16, 33, 66, 81) | broń 1–5% | każda trafiona ofiara: ogłuszenie 2 s (gracz) / 4 s (potwór), chyba że odporna (`IMMUNE_STUN`, odporność Czempiona) |
| 305–309 | „… ma x% szans na oddanie przeciwnikowi” (Walnięcie 17, Wolno Działająca Trucizna 36, Deszcz Strzał 47, Uderzenie Palcem 61, Ogniste Uderzenie 77) | broń 1–5% | odrzut o `b67_knock_length` (300) od atakującego (`CHARACTER::Knockback`; boss, Metin, nieruchomy potwór i „Odporność na Upadek” się opierają; nigdy w ścianę) |
| 310–318 | „Obrażenia od … +x%” (1, 20, 32, 47, 62, 76, 91, 92, 106) | zbroja 1–5% | obrażenia tej umiejętności +x% (przed obroną ofiary) |
| 90 | „Odporność na Upadek +x%” | zbroja 5/10/15/20 | `POINT_IMMUNE_FALL` był flagą (nic jej nie czytało); teraz szansa x%, że pchnięcie / przewrócenie (umiejętności z odrzutem, linie odrzutu, ślizg mocnego ciosu – `IsResistPush`) się nie uda. Wiki: upadek z wierzchowca od potworów Zodiaku – tej mechaniki u nas nie ma |

Wiki nie podaje wielkości „bonusu do ataku/obrony/szybkości zaklęcia na x s” – domyślnie maksimum linii 6/7 Wartości
Ataku (50), obrona tyle samo, szybkość zaklęcia 20%; flagi zdarzeń je zmieniają.

**Wola Życia (6), Krąg Mieczy (21), Wolno Działająca Trucizna (36)** – szóste umiejętności Wojownika i Ninja (sztylety)
z gry oficjalnej. W `world.skill_proto` (test) i w oknie umiejętności klienta (`playersettingmodule.py`) ich **nie ma**,
są tylko nazwy ich ksiąg (50406/50421/50436 w itemdesc). Ich linie (287, 288, 306) działają po numerze umiejętności, ale
wiersze puli mają wszystkie kolumny 0 (nie losują się nigdzie – jak Burza Szponów); gdy umiejętności dojdą, wystarczy
`weapon = 5` w panelu.

**Deszcz Strzał** to u nas umiejętność **47** (oficjalnie `KWANKYEOK` = 47, druga łucznika), choć nasz klient nazywa 47
„Iskrzące Uderzenie”, a 51 „Deszcz Strzał” (51 nie ma w oknie umiejętności). Linie mówią słowami wiki.

## Pula

Linia umiejętności losuje się tylko na przedmiocie klasy, która tę umiejętność ma (`Bonus67RareFits`: flagi anty-klasy
przedmiotu; łuk – tylko linie łucznika, inna broń – nigdy łucznika), w `AddRareAttribute`, `PutRareAttributeWithLevel`
i w sprawdzeniu Seon-Hae. Wagi 18 jak pozostałe wiersze.

## Silnik (`edits.json`, `gen_edits.py [<game/src>]`)

| plik | edycja |
|---|---|
| `common/length.h` | `(points)` – 256–318, `#define MT2009_PLUS_BONUS67_SKILL` |
| `char.cpp` | `(point change)` |
| `char_skill.cpp` | `(skill hit)` – `FuncSplashDamage`, `(duration)` – `ComputeSkill` |
| `item_attribute.cpp` | `(rare fits)`, `(rare fits add)`, `(rare fits put)` |
| `battle.cpp` | `(per human)` – `CalcPlayerBonus` |

8 edycji. Linux/VPS: `python3 apply_bonusy67c.py <game/src>`; Windows: `Apply-Bonusy67cPatch.ps1`
(`tools/port/Apply-MT2009PlusEngine.ps1`, po `wideattr`). Pełna przebudowa rdzenia; db bez zmian. Punkty idą do klienta
same (`wideattr`: zmiana punktu i lista przy logowaniu dla 256..`POINT_WIDE_END`−1). Nakładka buduje się i linkuje
także bez tej łatki (puste funkcje).

## Baza

`apply.sh` (`MT2009_PLUS_BONUS67_SKILL_V1`, po kroku rundy 2): ENUM `apply` w `item_attr` i `item_attr_rare` dostaje
63 nazwy po `POINT_BLEEDING_REDUCE` (tylko ENUM z 255 nazwami; idempotentnie), potem **raz na świat** (znacznik
`rare_6_7_wiki_v4`, po `rare_6_7_wiki_v3`) `bonusy67c_wiki.sql`: 63 wiersze + `POINT_IMMUNE_FALL` (zbroja). Nie czyści puli.

## Klient, panel, boty

- `root/localeinfo_point.py`: dymki 256–318 słowami wiki, 90 = „Odporność na Upadek +x%” (cp1250 jako `\x..`).
- `root/uiattributelist.py`: kategoria „Bonusy 6/7 (dodatkowe)” – niski ranking, 3× „+% łącznej”, odporność na upadek
  (punkty ≥256 tylko z exe `player.MAX_NUM` 512). Linie umiejętności – tylko w dymku przedmiotu.
- `client-patches/exe/Server/common/length.h`: same nazwy 256–318 (exe ich nie używa – bez przebudowy).
- Panel: `dbeditor/items.py` (nazwy 256–318, 90).
- Boty: `Bonus67SkillLineScore` (`playerbot_bonus.h`, `playerbot_gear.h`) – linia umiejętności warta coś tylko dla klasy
  i drogi, która jej używa; niski ranking tylko przy randze ujemnej; „Odporność na Upadek” jako szansa.
