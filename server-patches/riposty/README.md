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
  Źródła Podręczników: Skrzynia Jotuna Thryma, Książę Ochao, a od 21.10.2026 (`MT2009_PLUS_RIPOSTY_FORGET_V1`, wiki)
  **Metin Lasu** (8061: Riposta, 4) i **Niszczyciel En-Tai** (6406: Riposta i Dopalacz, po 0,2) – w
  `tools/yohara_zaklety/gen_yzaklety.py` → `mob_drop_item.yohara_zaklety.txt` (wiki nie podaje szans – domyślne
  `tools/ymoby_arkusz` dla „innego” przedmiotu).
- **1 → M1**: punkty umiejętności (pewne; od 17 do 20 klasyczny rzut na M jak 9. umiejętność, bez blokady „użyj zwoju
  resetu”) albo księgi riposty/dopalacza (35 % za odczyt jak księgi klasowe, Rada Pustelnika ×2,5 = 87 % (`radapustelnika`), 20 000 PD, odstęp
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
  dopalacza na dopalacz nowej drogi (`RipostyGroupChanged`).
- **Księga Zapomnienia** (`MT2009_PLUS_RIPOSTY_FORGET_V1`, decyzja właściciela 21.10.2026; wiki: „W grze istnieją także
  Księgi Zapomnienia dla Ripost / Dopalaczy”, strona przedmiotu: „Odejmuje jeden punkt umiejętności”, „Umiejętności na M
  i wyższej nie można cofnąć”): to zwykła Księga Zapomnienia 70037 z ripostą / dopalaczem w gnieździe 0 (klient pisze
  „Riposta: Wir Miecza Księga Zapomnienia”). Nowa Księga Zapomnienia (`ITEM_MANAGER::CreateItem`) dostaje ripostę lub
  dopalacz tak, jakby każda z 16 była jeszcze jedną umiejętnością losowania (16 na 63 – `RipostyForgetBookSkill`) – te
  same źródła co każda Księga Zapomnienia (Metiny od 15, bossy, szkatułki). Użycie (`RipostyLevelDown`, w `SkillLevelDown`
  przed regułami silnika): tylko poniżej M1, poziom w dół i punkt umiejętności z powrotem – tylko za punkty na nią wydane
  (`riposty.pts_<vnum>`); poziomu 1 z Podręcznika i poziomów z ksiąg nie cofa (całość usuwa Zwój Zmiany Treningu).

## V2 – nauka i zmiana jak na globalu (`MT2009_PLUS_RIPOSTY_V2`, 8.11.2026)

Zgłoszenie #8 (Discord, 6.11) i właściciel 8.11: „nauka riposty ma być jak na globalu” (pl-wiki, sekcja *Nauka
Riposty*). Silnik (edycje `edits.json`) się nie zmienił – ta sama łatka `riposty`; zmiany są w queście, nakładce botów,
ItemShopie i danych klienta.

- **Zmiana riposty była niemożliwa.** Wiki: ripostę zmienia tylko Zwój Zmiany Treningu (Item-Shop, 49 SM), potem nowy
  Podręcznik: Riposta. `riposty_itemshop.sql` wstawiał zwój tylko do starego sklepu WWW (`itemshop.ishop_items`), którego
  nie pokazuje ani ItemShop w grze, ani V3 (widok na `common.itemshop_items`) – nie dało się go kupić. Teraz
  `apply.sh` (`ishop_once riposty_zwoj_632`): linia 632 w „Zwoje i księgi”, 49 Smoczych Monet (raz na instalację, nie
  dubluje linii operatora). Boty go nie kupują (`IsPlayerBotIshop3ExcludedVnum`, `gen_bot_catalogue.py` NEVER).
- **Mylone efekty.** Gracz Sury BM wziął „Ripostę/Dopalacz: Duchowe Uderzenie” (Wojownik Mental) za swój Duchowy Cios.
  Przypisanie umiejętności było zgodne z wiki (sprawdzone: `s_adwSkill`, `BoostFor`, skill_proto Owsapa 221–243 =
  팔방풍우/암습/쇄령지/용파산/기공참/화조파/마령/벼락), ale nigdzie nie było napisane, czyja to umiejętność. Teraz
  wszędzie stoi klasa i droga z kolumny wiki: lista Podręcznika (`Duchowe Uderzenie (Wojownik Mental)` …), dialog
  dopalacza („Twoja droga: Sura BM – twój dopalacz to: Dopalacz: Mroczne Uderzenie”), dymek umiejętności w kliencie
  (`root/riposty.py`: „Umiejętność klasy: …” + uwaga przy Duchowym/Mrocznym Uderzeniu), opis w `skilldesc`
  (`tools/yriposty/patch_yriposty_client.py`) i opisy ksiąg 50516–50523 / 50560–50567 (`tools/yohara_items/gen_yitems.py`
  → `yohara_items.json`). Zwój Zmiany Treningu pyta dwa razy („Tego procesu nie można cofnąć!”), jak na globalu.
- **Boty** (`playerbot_riposty.cpp`, `RipostyManageBot` z przebiegu ksiąg w `playerbot_manager.cpp`, raz na minutę;
  `RipostyBotSpendPoints` na końcu `ManagePlayerBotSkills`; nie towarzysze graczy): Podręcznik: Riposta → riposta przeciw
  drodze najczęstszej wśród postaci innych królestw online (losowanie ważone, bez nikogo online – wg pid); Podręcznik:
  Dopalacz przy riposcie na P → dopalacz klasy; księgi własnej riposty/dopalacza (do G1, przez silnik, 20 000 PD
  pożyczone jak przy księgach klasowych); Kamień Duchowy+ jak quest (ranga, 12 h, tylko gdy ranga nie spadnie poniżej
  zera); punkty umiejętności, które zostają po buildzie → riposta, potem dopalacz, do M1. Nigdy Zwój Zmiany Treningu.
  Nazwy na straganach botów: „Księga Zapomnienia (Riposta: Wir Miecza)”.

### Jak sprawdzić w grze (serwer testowy)

1. Postać ≥ 5 poz. bez drogi: `/i 50515`, użyj → „Najpierw ukończ Szkolenie…”. Wybierz drogę u nauczyciela.
2. Użyj Podręcznika: Riposta → lista 8 pozycji z klasą w nawiasie, np. `Mroczne Uderzenie (Sura BM)`,
   `Duchowe Uderzenie (Wojownik Mental)`; wybór pokazuje wartości (1: 1,2 %, M1: 12 %, G1: 19,7 %, P: 30 %) →
   „Naucz się teraz” → riposta na 1. poziomie w 7. polu okna umiejętności; dymek: poziom, %, „Umiejętność klasy: …”.
3. Drugi Podręcznik: Riposta → „Znasz już ripostę …” + jak ją zmienić (Zwój Zmiany Treningu).
4. Plus w 7. polu: punkt umiejętności → poziom w górę (pewnie); od 17 do 20 skok na M1. `/i 50520` (księga innej
   riposty) → odmowa „Znasz już inną ripostę”; księga własnej riposty → odczyt jak księga klasowa (do G1).
5. Item-Shop w grze → „Zwoje i księgi” → **Zwój Zmiany Treningu, 49 SM** (też w Item-Shopie V3). Kup, użyj → dwa
   potwierdzenia → riposta i dopalacz znikają, wydane punkty wracają; nowy Podręcznik: Riposta → inna riposta.
6. Sura BM: `/i 50514` z ripostą na P (`/setskill` lub Kamień Duchowy+ `/i 50525` od G1) → „Twoja droga: Sura BM –
   twój dopalacz to: Dopalacz: Mroczne Uderzenie”. Bez riposty na P → „Dopalacza nauczysz się, gdy…”.
7. PvP / test: z `test_server` w syslogu `RIPOSTY: skill <vnum> damage a -> b` (riposta zmniejsza, dopalacz zwiększa).
8. Boty: `grep "riposty learn\|riposty book\|riposty points\|riposty soul stone" syslog` – bot z Podręcznikiem w torbie
   uczy się riposty w ciągu minuty; `player.quest` `riposty.pts_<vnum>` rośnie przy punktach.
9. Klient (po zbudowaniu przez właściciela): dymek księgi 50520 – „…od Duchowego Uderzenia - umiejętności Wojownika
   Mental…”; dymek riposty 227 – „Umiejętność klasy: Sura (Czarna Magia).” i „To nie Duchowy Cios ani Mroczna Sfera.”

## Pliki

`common/skill_length.h` `(vnum)`; `char_skill.cpp` `(learnable)`, `(book check)`, `(book grade)`, `(level up book)`,
`(level up stop)`, `(level up roll)`, `(points)`, `(reset)`, `(clear)`, `(damage)`, `(group)`;
`cmd_general.cpp` `(skillup)`; `MT2009_PLUS_RIPOSTY_FORGET_V1`: `char_skill.cpp` `(level down)`, `item_manager.cpp`
`(forget book)` – 15 edycji, każda ze swoim znacznikiem (pierwsza wersja `MT2009_PLUS_RIPOSTY_V1 (level down)` – „brak
punktu z riposty” – wypadła; w drzewie, które ją ma, nowa edycja i tak decyduje pierwsza). `gen_edits.py [<game/src>]` tworzy `edits.json`
i sprawdza kotwice. Logika: `playerbot_riposty.{h,cpp}` (nakładka; funkcje questa rejestrowane razem z funkcjami
Czempiona w `playerbot_champion.cpp`). Quest: `linux-port/docker/game/quest/riposty.quest`. Przedmioty (Podręczniki,
Zwój Zmiany Treningu, opisy ksiąg): `tools/yohara_items/gen_yitems.py` → `yohara_items.sql`.

- Linux/VPS: `python3 apply_riposty.py <game/src>`; Windows: `Apply-RipostyPatch.ps1 -SourceDir <game/src>`
  (`tools/port/Apply-MT2009PlusEngine.ps1`, ostatni – po `bonusy67`).
- Klient: `client-patches/client-2.0.30/tools/yriposty` (skilldesc/skilltable, ikony) i `root/riposty.py`
  (miejsce w oknie umiejętności, dymki).
