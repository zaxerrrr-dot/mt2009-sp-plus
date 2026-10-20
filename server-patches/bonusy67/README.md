# bonusy67 – brakujące bonusy 6/7 z wiki

`MT2009_PLUS_BONUS67_V1` (20.10.2026, decyzja właściciela: „dodać brakujące grupy 2, 3, 4, 7 i 9” z
`/opt/metin2/cache/yohara/bonusy-6-7-wiki.md`; „Bonusy 6/7 takie same w jednym i drugim trybie”). Źródła: pl-wiki
„6. i 7. bonus” (rodzaje przedmiotów i maksima), Owsap `item_attr_rare` (stopnie, 10 poziomów → u nas 2/4/6/8/10).
Owsap i Ameria nie mają kodu silnika dla tych bonusów (tylko nazwy w kliencie / dane) – działanie jest nasze.

## Punkty (198–251, po `POINT_HIT_PCT`)

Typ bonusu na przedmiocie to 1 bajt: 252 z 256 zajęte (`POINT_MAX_NUM` 252, `static_assert` w `playerbot_bonus67.cpp`).
Punkty są tylko na serwerze: pakiet punktów i zmiana punktu kończą się na 197 (exe Yohary ma `POINT_MAX_NUM` 198) –
**exe bez zmian**; dymek przedmiotu nazywa je z `root/localeinfo_point.py`.

| Nr | Punkty | Działanie (`playerbot_bonus67.cpp`) |
|---|---|---|
| 198–203 | `HIT_BUFF_ENCHANT_FIRE/ICE/ELEC/WIND/DARK/EARTH` | zadany cios (zwykły lub umiejętność): na x sek. Siła żywiołu +`b67_hitbuff_value` (domyślnie 10); ponownie po `b67_hitbuff_cooldown` (15 s) |
| 204–209 | `HIT_BUFF_RESIST_*` | otrzymany cios: na x sek. odporność na żywioł +10 (te same flagi) |
| 210–217 | `ATTBONUS_PER_MONSTER/STONE/CZ/MILGYO/ORC/DEVIL/INSECT/ANIMAL` | +x% łącznej wartości „Silny przeciwko …” (`battle.cpp` `CalcAttBonus`); Zodiak: u nas nie ma osobnego „Silny przeciwko potworom Zodiaku”, więc na potworze Zodiaku (`RACE_FLAG_CZ`) linia podnosi całą premię rasową |
| 218–223 | `ENCHANT_PER_ELECT/FIRE/ICE/WIND/EARTH/DARK` | +x% łącznej Siły żywiołu (`playerbot_elements.cpp`) |
| 224–231 | `RESIST_PER_HUMAN/MAGIC/ELEC/FIRE/ICE/WIND/EARTH/DARK` | +x% łącznej odporności (`GetResistPoint`, żywioły w `playerbot_elements.cpp`) |
| 232–235 | `NORMAL_HIT_/SKILL_ DEFEND/DAMAGE_BONUS_BOSS_OR_MORE` | zwykłe ciosy / umiejętności od bossa (−x%) i przeciw bossowi (+x%); boss = potwór rangi boss i wyżej, bez Metinów |
| 236–240 | `FIRST..FIFTH_ATTRIBUTE_BONUS` | 1.–5. zwykły bonus tego samego przedmiotu liczy się x% wyżej (`CItem::ModifyPoints`) |
| 241 | `GLOVE_FALL_RESIST` | rękawice: otrzymany cios – x% szans na odporność na upadek (`IsResistPush`) na `b67_fall_seconds` (10 s); potem 60 s przerwy |
| 242 | `GLOVE_LIGHTNING` | rękawice: zwykły cios w potwora – błyskawice na potwory w pobliżu (`b67_lightning_range` 600, do 8) za te same obrażenia; co 15 s |
| 243–250 | `GLOVE_COOLDOWN_FINISH … ILIPUNGU` | rękawice: użycie umiejętności Czempiona (176–183) – x% szans, że jej kolejny czas odnowienia jest krótszy o 5 s; klient dostaje `HEADER_GC_SKILL_COOLTIME_END` (73, exe go ma) w nowej chwili |
| 251 | `GLOVE_BASE_ATTR_PCT` | rękawice: wbudowana linia rękawic (Wola Sung Ma, 6. bonus) +x% |

## Rękawice

Rękawice mają w 6. slocie własną Wolę – teraz **7. slot** bierze się z puli (kolumna `glove`): 71051 / 71052
(`Bonus67GloveRare`, krawędzie `item_attribute.cpp`), ulepszenie go przenosi (`playerbot_yohara_gear.cpp`). Pula
rękawic (wiki): bossowie ×4, Metiny 8%, Wola ×4 do 15%, 11 linii rękawic. Seon-Hae rękawic nie przyjmuje
(`playerbot_seonhae.h`, `MT2009_PLUS_SEONHAE_RESERVED_V1` – inny agent).

## Silnik (`edits.json`, `gen_edits.py [<game/src>]`)

| plik | edycja |
|---|---|
| `common/length.h` | `(points)` – 198–251, `POINT_MAX_NUM` 252 |
| `char.cpp` | `(point change)`, `(point packet)` – nie do klienta, `(resist)` |
| `battle.cpp` | `(att bonus)` |
| `char_battle.cpp` | `(damage)`, `(push)` |
| `char_skill.cpp` | `(cooldown)` |
| `item.cpp` | `(attr value)` |
| `item_attribute.cpp` | `(add rare)`, `(add rare 2)`, `(change rare)`, `(change rare 2)` – rękawice |

13 edycji, każda ze swoim znacznikiem; **po** `precyzja` i `rekawice` (zmienia ich linie). Linux/VPS:
`python3 apply_bonusy67.py <game/src>`; Windows: `Apply-Bonusy67Patch.ps1` (`tools/port/Apply-MT2009PlusEngine.ps1`, na końcu).
db bez zmian (nie używa `POINT_MAX_NUM`).

## Baza – jedna pula w obu trybach

`apply.sh` (`MT2009_PLUS_BONUS67_V1`, w miejscu dawnej podmiany `MT2009_PLUS_RARE_WIKI_V1`): ENUM `apply` w
`item_attr` i `item_attr_rare` dostaje 54 nowe nazwy (pozycja = numer punktu), potem **raz na świat** (znacznik
`rare_6_7_wiki_v2`) `bonusy67_wiki.sql` (`tools/bonusy67/gen_bonusy67_sql.py` z `bonusy67_data.py`): stara pula mt2009
(tabela właściciela z 1.10) zostaje jako kopia w `world.item_attr_rare_mt2009`, pula = 13 wierszy wiki + 54 nowe
(wagi 18; Burza Szponów 0 – nie ma Likana). `M2_BONUS_MODE` już jej nie przełącza. `bonusy67_global.sql` /
`bonusy67_mt2009.sql` usunięte.

## Klient i panel

- `root/localeinfo_point.py`: nazwy 198–251 słowami wiki (cp1250). Bez ikon afektów, bez zmian w exe.
- Panel: `dbeditor/items.py` (nazwy 198–251), `dbeditor/attrs.py` (kolumna Rękawice, opis kroku).
- Boty: wagi w `playerbot_bonus.h` (`ScorePlayerBotBonusLineRaw`).
