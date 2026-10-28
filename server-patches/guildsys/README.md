# guildsys – system gildii (poziomy do 40, umiejętności Balathora, daty dla Krypty Balathora)

Znacznik: `MT2009_PLUS_GUILDSYS_V1`. Podstawa: paczka **Guild Systems** (GitHub „Guild-Systems”), którą skompilował
i uzupełnił **Nazox** (sam pisze, że nie jest autorem systemów – zebrał je z kilku baz). Ostrzeżenia autora: kod
niepełny, pisany na bazie TMP4, teksty przez locale_string Mali, testowany tylko na 10–15 kontach. Dlatego z paczki
wzięliśmy pomysły i liczby, a kod napisaliśmy pod nasz silnik od nowa: **bez nowych pakietów, bez nowego typu
przedmiotu**, stary klient działa dalej.

Cel właściciela: system gildii połączony z **Kryptą Balathora** (`server-patches/balathor`). Krypta wymaga (pl-wiki):
gildia poz. ≥ 21, gildia istnieje ≥ 24 h, gracz w gildii ≥ 24 h, 600 pkt rankingu, skarbiec ≥ 500 000 Yang, 4–16
członków; w nagrodach księgi 3 nowych umiejętności gildii. Wszystko to daje ten patch.

## Co robi

1. **Poziomy gildii 1–40** (moduł paczki `GUILD_NEW_LEVEL_40`, nasza tabela):
   - `common/length.h` `GUILD_MAX_LEVEL` 20 → 40;
   - `constants.cpp` `guild_exp_table`: 20→21 = 10,5 mln, potem +0,5 mln za poziom, 39→40 = 20 mln (1–19 bez zmian;
     indeks 40 = 42 mln to granica „ostatni poziom”, jak dawniej indeks 20). Paczka miała tabelę z błędem (poziom 20
     przesunięty na koniec) – nie wzięta;
   - db `GuildManager.cpp` `c_aiScoreByLevel` (punkty rankingu wojen za poziom) do 40: 60 000 + 5 000 za poziom
     (bez tego poziomy 21–40 liczyłyby się jako 0);
   - limit członków rośnie do poz. 40 tak samo jak do 20: 48 + 4 × (poziom − 1), czyli 124 na 20 i **204 na 40**
     (plus premia budynków do 72) – decyzja właściciela z 29.10.2026 (edycja `members to 40` na `members`; tekst
     zachowuje znacznik `members`, więc drzewo po wcześniejszym wdrożeniu przyjmuje ją bez zmian). Klient pokazuje
     limit z pakietu serwera (`max_member_count`, WORD), rdzeń db limitu nie liczy;
   - punkt umiejętności za każdy poziom jak dotąd (do 39 punktów; umiejętności 151–157 potrzebują 49).
2. **Umiejętności gildii Balathora** na wolnych miejscach 158–160 tablicy umiejętności gildii (to numery GF z jego
   `skilltable.txt`: 진백룡의 가호 / 결의 / 견고 – w naszej bazie były tu puste `PASSIVANONAMEx`; rozmiar tablicy
   `GUILD_SKILL_COUNT` = 12 się nie zmienia, więc pakiety i baza też nie):
   - 158 **Burza Balathora** – odporność na omdlenie (stun) i spowolnienie,
   - 159 **Wola Balathora** – odporność na ogłuszenie (stun), kajdany (root) i zamrożenie Balathora,
   - 160 **Nieugiętość Balathora** – odporność na odrzucenie (push) i powalenie (fall);
   - maks. poziom 10, **tylko z ksiąg** (`CGuild::SkillLevelUp` odmawia punktu, klient nie pokazuje „+”);
   - użycie (lider/ranga z prawem umiejętności, koszt Ducha Smoka `100+150*k`, czas `300+429*k` s, odnowienie
     `600-300*k` s): wszyscy członkowie na mapie rzucającego dostają efekt (typ = vnum umiejętności), który daje
     odporność z szansą **10 % za poziom** (`CHARACTER::IsImmune`, `IsResistPush`);
   - działają w Krypcie Balathora (mapa 420 i jej kopie) bez wojny, a na arenie wojny gildii (jak inne) tylko w czasie
     wojny.
3. **Księgi** (moduł paczki `GUILD_SKILLBOOK`, odwrócony): `ITEM_USE`/`USE_SPECIAL`, czyta **tylko lider gildii**:
   - 50344 Księga: Burza Balathora, 50345 Księga: Wola Balathora, 50346 Księga: Nieugiętość Balathora – +1 poziom;
   - 50347 **Księga Zapomnienia Gildii** – zwraca wszystkie punkty rozdane na 151–157 (umiejętności Balathora
     zostają). Księga paczki obniżała **losową** umiejętność o 1 i wymagała nowego typu przedmiotu 37 (u nas 37 to
     zwierzak) – tego nie bierzemy.
   - Księgi Balathora daje skrzynia 83076 Krypty (`game/balathor/special_item_group.balathor.txt`, wiersze 12–14, po
     20 %; decyzja właściciela z 29.10.2026, wcześniej 10 %).
   - Księga Zapomnienia Gildii w ItemShopie: zakładka „Zwoje i księgi”, indeks **631**, **79 Smoczych Monet** (cena
     Zwoju Powrotu Statusu; `apply.sh` `ishop_once guildsys_forget_631`, panel `BOOT_ONCE`).
4. **Umiejętności gildii w Krypcie Balathora**: na mapie 420 (i `indeks / 10000 == 420`) każda umiejętność gildii
   działa bez wojny i trafia w członków na tej samej kopii mapy (`CGuild::UseSkill` – kontrola areny + nasz hook przed
   `switch`). Exe: `PythonPlayerSkill.cpp` przepuszcza `ONLY_FOR_GUILD_WAR` na `metin2_map_guild_whitedragon_boss`.
5. **Daty** (pomysł `join_date` z modułu paczki `GUILD_DONATE_ATTENDANCE`): kolumny `player.guild.create_time`
   i `player.guild_member.join_time` (`INT UNSIGNED`, **INVISIBLE**, domyślnie `UNIX_TIMESTAMP()` – wypełnia je sama
   baza, więc pozycyjny `INSERT INTO guild_member VALUES(...)` rdzenia db i każde `SELECT *` zostają bez zmian).
   Wiersze sprzed patcha mają 0 = „dawno” (reguły 24 h przechodzą). Gracz, który wyjdzie i wróci, dostaje nowy wiersz,
   czyli nową datę.

## Funkcje dla Balathora (i innych questów)

Quest (`questlua_guild.cpp`, definicje w `guildsys.cpp`; dopisane do listy `qc` w `game/Dockerfile`):

| Funkcja | Zwraca |
|---|---|
| `guild.get_level()` | poziom gildii postaci (0 bez gildii) |
| `guild.create_time()` | unix czas założenia gildii (0 = sprzed patcha / brak gildii) |
| `guild.age()` | sekundy od założenia gildii (−1 bez gildii) |
| `guild.member_join_time([pid])` | unix czas wejścia postaci (albo `pid`) do jej gildii (0 = sprzed patcha) |
| `guild.member_age([pid])` | sekundy w gildii (−1 bez gildii); w `q.begin_other_pc_block(pid)` liczy tamtą postać |
| `guild.get_bank()` | skarbiec, który można wydać (= `guild.treasury_available()`) |
| `guild.check_requirements(min_level, min_guild_h, min_member_h, min_bank)` | 0 OK, 1 brak gildii, 2 poziom, 3 gildia za młoda, 4 postać za krótko w gildii, 5 za mały skarbiec |

Już istniejące, przydatne: `guild.get_money()`, `guild.treasury_available()`, `guild.treasury_spend(yang, "co")`
(tylko lider), `guild.get_ladder_point()`, `guild.set_ladder_point(±n)`, `guild.get_skill_level(vnum)`.

C++ (`guildsys.h`): `GuildSysIsBalathorMap(map)`, `GuildSysCreateTime(g)`, `GuildSysMemberJoinTime(g, pid)`,
`GuildSysCheckRequirements(ch, …)`, `GuildSysIsImmune(ch, flag)` – w tym `GUILDSYS_IMMUNE_FREEZE` dla zamrożenia
Balathora (jego polimorfia w kryształ lodu): Wola Balathora go chroni, jeśli Krypta zapyta przed zamrożeniem.

**Podłączone w Krypcie** (`quest/krypta_balathora.quest`): `guild_age_ok` = `guild.age() >= 24 h`,
`member_age_ok` = `guild.member_age() >= 24 h` (każdy zgłaszany członek), `guild_money` = `guild.get_bank()`;
`balathor.json` `register_min_guild_level` 21; księgi w skrzyni 83076. `guild.get_level` silnika Krypty
(`balathor_support.cpp`) rejestruje się tylko, gdy nazwy nie ma – wygrywa ta z `guildsys.cpp`.

## Pliki

| Plik | Zmiana |
|---|---|
| `guildsys.cpp/.h` (overlay `linux-port/overlays/playerbot/src/game/src/`) | **nowe**: cała logika (księgi, efekty, odporności, daty, funkcje questowe) |
| `../../common/length.h` | `GUILD_MAX_LEVEL` 40 |
| `constants.cpp` | tabela doświadczenia 21–40 |
| `../../db/src/GuildManager.cpp` | `c_aiScoreByLevel` do 40 |
| `guild.h` | `friend struct GuildSysAccess` (tablica umiejętności, punkty, członkowie online) |
| `guild.cpp` | limit członków do poz. 40; Krypta jako miejsce umiejętności; hook w `UseSkill`; 158–160 bez punktów |
| `char_item.cpp` | `USE_SPECIAL` → 50344–50347 |
| `char_resist.cpp` | `IsImmune` → efekty 158/159/160 |
| `char_battle.cpp` | `IsResistPush` → Nieugiętość Balathora |
| `questlua_guild.cpp` | deklaracje + 7 funkcji w tabeli `guild` |

14 edycji (`edits.json`, generowane przez `gen_edits.py`), każda z własnym znacznikiem. Kolejność: po `npcloc`, przed
`balathor` (`... npcloc guildsys balathor`); sprawdzone, że wszystkie edycje Krypty dalej pasują po tym patchu.
`guildsys.sql` (apply.sh): kolumny, `skill_proto` 158–160, `item_proto` 50344–50347 (INSERT IGNORE).

Boty: nic z tego nie wysyła pakietów postaci bez połączenia (`GetDesc`); boty gildii wydają punkty jak dotąd na
152–157, ich gildie rosną dalej niż 20. Większy limit: gildie botów średnie, zwykłe i Legend biorą limit silnika
(`GetPlayerBotGuildMemberCap`), elitarne i silne zostają przy 24 / 40; rekrutacja (`playerbot_guild_lfg.h`, Legendy,
zaproszenia z czatu) sprawdza `GetMaxMemberCount()`, listy członków to kontenery bez stałych rozmiarów.

## Moduły paczki – co wzięte, co nie

| Moduł | Werdykt |
|---|---|
| `GUILD_NEW_LEVEL_40` | **wzięty** (własna tabela; exe `Locale.cpp`/`PythonGuild.cpp`); bez „3 punktów na start” |
| `GUILD_SKILLBOOK` | **wzięty po swojemu**: księgi Balathora (+1) i Księga Zapomnienia Gildii (zwrot punktów); bez nowego typu przedmiotu 37 |
| `GUILD_DONATE_ATTENDANCE` | tylko **data wejścia** do gildii; same datki (dzienny limit, „medale”, okno, pakiety, exe) nie – mamy zrzutki do skarbca w Obowiązkach gildii |
| `USE_MONEY_FROM_GUILD` | nie – mamy to już (`MT2009_PLUS_GUILD_TREASURY_V1`: budynek/ziemia ze skarbca); paczka pozwalała też **wypłacać** złoto do torby, czego skarbiec celowo nie pozwala (wpłaty botów) |
| `GUILD_STORAGE` (+ `PythonGuildBank` klienta) | nie – 3800 linii, nowe okno/pakiety/exe, przedmioty dzielone przez członków na kilku rdzeniach bez blokad między kanałami = ryzyko dupów; mamy bank przedmiotów w Obowiązkach gildii. Krypta potrzebuje tylko Yang w skarbcu |
| `GUILDBANK_LOG`, `GUILDBANK_LOG_EXTENDED` | nie – dziennik banku z `GUILD_STORAGE` (nowe pakiety i okno); do decyzji właściciela, gdyby chciał dziennik skarbca |
| `NEW_WAR_OPTION`, `GUILD_WAR_SCORE` | nie – zmieniają wojny gildii i ich tabele, a nasze wojny (arena 110, boty, `guildwarexit/watch/warrankkeep`) są przebudowane |
| `ENABLE_GUILDWAR_BUTTON` | nie – mamy wejście na wojnę (`guildwarjoin`) |
| `COLEADER_WAR_PRIVILEGES` | nie – zmienia `do_war` (deklaracje wojen) używane też przez boty; do decyzji właściciela |
| `ENABLE_SHOW_LIDER_AND_GENERAL_GUILD` | nie – zmienia pakiet dodania postaci (serwer + exe), tylko kosmetyka |
| `EXTENDED_RENEWAL_FEATURES` | nie – przekazanie lidera za pierścień 71099 i porzucanie ziemi z okna; mamy `guild.change_master` i questy ziem |
| `GUILD_LAND_INFO` | nie – informacja w oknie (nowy podpakiet + exe) |
| `INACTIVITY_LANDS` | nie – kasuje ziemie nieaktywnych gildii przy starcie db; nasze boty używają ziem i budynków |
| `###QUEST###`, `##UPDATE##`, `##LOCALE_STRING##`, `###COMPARE###`, SQL paczki | nie (hiszpańskie questy na nasze już istniejące, SQL z `DROP TABLE`) – liczby i pomysły wzięte do kodu wyżej |

## Klient

- exe (`client-patches/exe`, `ENABLE_MT2009_GUILDSYS`): `Locale.cpp` tabela do 40, `PythonGuild.cpp` maks. poziom 40,
  `PythonPlayerSkill.cpp` umiejętności gildii w Krypcie. Stary exe: okno gildii nie pokazuje doświadczenia od poz. 20,
  w Krypcie umiejętności gildii zablokowane po stronie klienta; reszta działa.
- root: `playersettingmodule.py` (158–160 na miejscach 216–218 rzędu aktywnych), `uiguild.py` (bez „+” dla 158–160,
  scalone z naszym oknem), `uiaffectbar.py` (ikony i opisy efektów 158–160).
- paczki: `client-2.0.30/tools/guildsys` (`build_guildsys_packs.py` + `verify_guildsys.py`): księgi w `gamedata`/`dbdata`,
  wiersze 158–160 w `skilldesc.txt`/`skilltable.txt`, ikony (atlas GF `guildsys_common.dds` + 6 `.sub`) w `root`.
