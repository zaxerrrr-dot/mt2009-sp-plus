# riposty – Riposty i Dopalacze (7. i 8. umiejętność)

`MT2009_PLUS_RIPOSTY_V1` (21.10.2026, decyzja właściciela: „Riposty i dopalacze” – księgi 50516–50523, 50560–50567 i
Kamień Duchowy+ 50525 były do zdobycia, ale nic nie robiły; „Jeśli czegoś nie wiesz – wszystko zgodnie z wiki”).
Źródło: pl-wiki „Umiejętności - Riposty i Dopalacze” (kopia: `cache/yohara/wiki/Umiejętności_-_Riposty_i_Dopalacze.raw`),
strony przedmiotów (Podręcznik: Riposta / Dopalacz, Kamień Duchowy+, Zwój Zmiany Treningu); implementacja wzorowana na
Owsapie (`__7AND8TH_SKILLS__`: `skill.h`, `char_skill.cpp`, `cmd_general.cpp`, `training_passive_skill.quest`, wiersze
`skill_proto` 221–244 z `player.sql`).

## Umiejętności

| vnum | Riposta (mniej obrażeń od…) | vnum | Dopalacz (więcej obrażeń…) | klasa dopalacza |
|---|---|---|---|---|
| 221 | Wir Miecza | 236 | Wir Miecza | Wojownik Body |
| 222 | Zasadzka | 237 | Zasadzka | Ninja Dagger |
| 223 | Uderzenie Palcem | 238 | Uderzenie Palcem | Sura WP |
| 224 | Strzelający Smok | 239 | Strzelający Smok | Szaman Smok |
| 225 | Duchowe Uderzenie | 240 | Duchowe Uderzenie | Wojownik Mental |
| 226 | Ognista Strzała | 241 | Ognista Strzała | Ninja Archer |
| 227 | Mroczne Uderzenie | 242 | Mroczne Uderzenie | Sura BM |
| 228 | Przywołanie Błyskawicy | 243 | Przywołanie Błyskawicy | Szaman Healer |

(229 / 244 Wilczy Dech – Likan, u nas brak.) `skill_proto`: `linux-port/docker/mariadb/playerbot/riposty_skill.sql`
(wiersze Owsapa: typ 6 – punkty umiejętności klasy).

## Zasady (wiki)

- **Nauka**: poziom postaci ≥ 5 i wybrana droga. Riposta – **Podręcznik: Riposta** (50515), wybór jednej z 8, poziom 1;
  można znać **tylko jedną**. Dopalacz – **Podręcznik: Dopalacz** (50514), zawsze dopalacz własnej klasy i drogi,
  wymaga **riposty na P**. Quest `riposty` (pc.learn_passive_skill).
- **1 → M1**: punkty umiejętności (pewne; od 17 do 20 klasyczny rzut na M jak 9. umiejętność, bez blokady „użyj zwoju
  resetu”) albo księgi riposty/dopalacza (35 % za odczyt jak księgi klasowe, Rada Pustelnika 100 %, 20 000 PD, odstęp
  między księgami). **M1 → G1**: księgi (jak księgi klasowe). **G1 → P**: **Kamień Duchowy+** (50525) – jak Kamień Duchowy
  (`pc.learn_grand_master_skill`: punkty rangi 1000 + 500 za stopień, przy ujemnej podwójnie, nieudana próba 1/3–1/2,
  następna po 12 h, Zwój Egzorcyzmu od razu).
- **Wartości** (tabela wiki): riposta 1: 1,2 %, M1: 12 %, G1: 19,7 %, P: 30 % (24·k); dopalacz 0,8 / 8 / 13,1 / 20 %
  (16·k); k = moc umiejętności poziomu z tabeli GF / 100 (`riposty::Percent`, niezależnie od naszego
  `SKILL_POWER_BY_LEVEL`).
- **Działanie**: w obrażeniach umiejętności (`char_skill.cpp`, tam gdzie stare anty-umiejętności 112–119) – najpierw
  dopalacz atakującego (gracz/bot), potem riposta ofiary (gracz/bot) przeciw tej umiejętności. Potwory nie mają ani
  jednego, ani drugiego.
- **Reset**: zwykły reset umiejętności (zwoje, zmiana drogi – `ResetSkill`/`ClearSkill`) **zostawia** ripostę i dopalacz,
  a punkty na nie wydane zostają wydane (`riposty.pts_<vnum>` w flagach questa). **Zwój Zmiany Treningu** (71000,
  ItemShop „Bonusy” za 49 – `riposty_itemshop.sql`) usuwa oba i oddaje te punkty. Zmiana drogi przenosi poziom
  dopalacza na dopalacz nowej drogi (`RipostyGroupChanged`). Księga Zapomnienia ich nie cofa (`SkillLevelDown`).

## Pliki

`common/skill_length.h` `(vnum)`; `char_skill.cpp` `(learnable)`, `(book check)`, `(book grade)`, `(level up book)`,
`(level up stop)`, `(level up roll)`, `(points)`, `(reset)`, `(clear)`, `(level down)`, `(damage)`, `(group)`;
`cmd_general.cpp` `(skillup)` – 14 edycji, każda ze swoim znacznikiem. `gen_edits.py [<game/src>]` tworzy `edits.json`
i sprawdza kotwice. Logika: `playerbot_riposty.{h,cpp}` (nakładka; funkcje questa rejestrowane razem z funkcjami
Czempiona w `playerbot_champion.cpp`). Quest: `linux-port/docker/game/quest/riposty.quest`. Przedmioty (Podręczniki,
Zwój Zmiany Treningu, opisy ksiąg): `tools/yohara_items/gen_yitems.py` → `yohara_items.sql`.

- Linux/VPS: `python3 apply_riposty.py <game/src>`; Windows: `Apply-RipostyPatch.ps1 -SourceDir <game/src>`
  (`tools/port/Apply-MT2009PlusEngine.ps1`, ostatni – po `bonusy67`).
- Klient: `client-patches/client-2.0.30/tools/yriposty` (skilldesc/skilltable, ikony) i `root/riposty.py`
  (miejsce w oknie umiejętności, dymki).
