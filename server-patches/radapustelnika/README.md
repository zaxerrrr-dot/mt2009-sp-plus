# Rada Pustelnika ×2,5 (`MT2009_PLUS_RADA_PUSTELNIKA_V1`)

Właściciel, 3 listopada 2026 (lista Yohary): Rada Pustelnika (39030, 71094) ma działać jak w opisie przedmiotu na pl-wiki
(„Podnosi szansę na pomyślne przeczytanie następnej Księgi Umiejętności (lub Kamienia Duchowego) na 250%”) – szansa
następnego odczytu ×2,5, najwyżej 100 %, a nie pewny sukces. Silnik (jak GF / Ameria) dawał przy niej 100 % tylko
księgom klasowym, a przy księgach pasywnych i Kamieniu Duchowym zdejmował ją bez żadnego efektu.

| Znacznik | Plik | Co robi |
|---|---|---|
| `(class chance)` | `char_skill.cpp` `LearnSkillByBook` | księgi klasowe (też Sztuka Wojny, riposty/dopalacze, 9. umiejętność, Buffi): 35 % → 87 % (było 100 %) |
| `(passive chance)` | `char_skill.cpp` `LearnSkillByBook` | księgi z własną szansą: Sztuka Combo, Księgi Polimorfii, języki, Instr. Oswajania Konia, Przewodnik Do Górnictwa, Księga Precyzji – szansa ×2,5 (było: Rada zdjęta za nic) |
| `(stone affect)`, `(stone chance)` | `char_skill.cpp` `LearnGrandMasterSkill` | Kamień Duchowy (i riposty/dopalacze G→P): 30 % → 75 %, przed minimalną liczbą odczytów 4 % → 10 % (było: Rada zdjęta za nic) |
| `(horse)` | `char_item.cpp` | Instr. Jazdy Konnej / Walki Konno (50060 / 50062): Rada zużyta, szansa ×2,5 (wcześniej jej nie dotykały) |

Poza łatką: `playerbot_champion.cpp` (Księga Precyzji nie wymusza już 100 % – mnoży silnik), krok Dockerfile
`crafting.lua` (odczyt receptury nie zdejmuje już Rady – wiki nie wymienia receptur), Mikstura Talentu
(`mikstura_talentu.quest`) miała już ×2,5 (30 % → 75 %). Mikstury nauki (`POINT_LEARN_CHANCE`) liczą się przed ×2,5.
Boty: używają Rady tuż przed księgą klasową jak dotąd; nieudany odczyt to zwykła porażka. Opisy przedmiotów
(itemdesc klienta, ItemShop) już mówią „×2,5 / 250%” – bez zmian klienta.

- `apply_radapustelnika.py` – Linux/VPS: `python3 apply_radapustelnika.py <game/src>`;
- `Apply-RadaPustelnikaPatch.ps1` – Windows; oba czytają ten sam `edits.json`.
