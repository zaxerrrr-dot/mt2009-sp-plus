# skillcolor – Kolor umiejętności

`MT2009_PLUS_SKILL_COLOR_V1` (właściciel, 4.11.2026: „jeszcze dodaj ten skill color”). Na podstawie paczki właściciela
„SKILL_COLOR_SYSTEM by OSWAP (FULL)” (Owsap, V1.0.1.4) – przepisanej, nie skopiowanej: ten sam pomysł (gracz wybiera kolor
efektów umiejętności w oknie z zakładki umiejętności, kolor jest zapisany przy postaci, inni gracze widzą go u niej),
inne wnętrze tam, gdzie paczka nie pasowała do naszego silnika albo miała błędy.

**Nakładana jako OSTATNIA** z listy łatek (po `bonusy67c`; kotwice: linie pakietów puzzli rybackich i linia logowania
`skillhack`). Linux/VPS: `python3 apply_skillcolor.py <game/src>`; Windows: `Apply-SkillcolorPatch.ps1`
(`tools/port/Apply-MT2009PlusEngine.ps1`, na końcu). Edycja już nałożona jest pomijana; edycja, której stary kod nie
występuje dokładnie raz, zatrzymuje całość, zanim cokolwiek zostanie zapisane. `gen_edits.py [<game/src>]` pisze
`edits.json` (i sprawdza kotwice).

## Co robi

- Kolor ma **pięć warstw**: warstwa n barwi n-ty system cząsteczek efektu umiejętności, 5. także każdy następny.
  Wartość 0 = własny kolor efektu, inaczej `0xFFrrggbb`. Exe zachowuje przezroczystość i jasność każdej cząsteczki i
  podmienia tylko barwę (efekt, który gaśnie do czerni, dalej gaśnie).
- **Które umiejętności**: obie ścieżki klasy (także druga ścieżka „skill hacka”, `skillhack`), umiejętności 9.
  (176–182), konne 137–140 i umiejętności Buffi 164–167 (barwią wzmocnienia rzucane przez Buffi i jej ruch). Riposty i
  dopalacze (221–243) są pasywne – nie mają efektu do pokolorowania.
- **Kiedy**: od poziomu **P** umiejętności (zasada paczki; konne – gdy są znane). „Domyślne” (same zera) zawsze.
- **Co jest barwione** (exe): każdy efekt, efekt na celu i pocisk (z trafieniem) ruchu umiejętności – u gracza i u
  każdego, kto go widzi; skoki Burzowego Szpona i strzały Ognistego Ducha; efekty wzmocnień na postaci: własne
  (Berserk, Aura Miecza – poświata broni, Silne Ciało, Krycie Się, Bezszelestny Chód, Czarowane Ostrze, Strach,
  Czarowana Zbroja, Ognisty Duch, Mroczna Ochrona) w kolorze postaci, szamańskie (Błogosławieństwo, Odbicie, Pomoc
  Smoka, Zwinność, Zwiększenie Ataku) w kolorze **tego, kto je rzucił** (Buffi – kolor właściciela dla jej umiejętności).

## Silnik (`edits.json`, 9 edycji) i nakładka

| Plik | Miejsce | Co |
|---|---|---|
| `packet.h` | nagłówki | `HEADER_CG_SKILL_COLOR = 56` (numer paczki), `HEADER_GC_SKILL_COLOR = 59` – wolne u nas i w exe (sprawdzone: wszystkie CG/GC naszego `packet.h`, `npc_location_helper.h`, `input_udp.cpp` i `Packet.h` exe) |
| `packet.h` | struktury | `TPacketCGSkillColor` (23 B: nagłówek, vnum `WORD`, 5 × `DWORD`), `TPacketGCSkillColor` (28 B: + VID, typ `SKILL_COLOR_TYPE_OWN`/`_BUFF`), `static_assert` rozmiarów (exe to samo) |
| `packet_info.cpp` | rozmiary | CG 56, stały, z bajtem sekwencji |
| `input_main.cpp` | pakiety | `SkillColorPacket` |
| `char.cpp` | `EncodeInsertPacket` | po pakietach dodania postaci – jej kolory temu, kto ją widzi (`SkillColorEncodeInsert`) |
| `char.cpp` | `Destroy` | stan VID-u znika (`SkillColorOnDestroy`) |
| `char_skill.cpp` | `ComputeSkill` | wzmocnienie szamańskie na celu dostaje kolor rzucającego – **przed** efektem, więc klient od razu zakłada je w tym kolorze (`SkillColorOnBuff`; także członkowie drużyny) |
| `input_login.cpp` | po `Skill2OnLogin` | wiersze postaci z bazy, do niej i do wszystkich wokół (`SkillColorOnLogin`) |

Nakładka: `linux-port/overlays/playerbot/src/game/src/playerbot_skillcolor.cpp` (cała logika: walidacja, odstęp 0,4 s
między zmianami, zapis, rozsyłanie) i `playerbot_buffi.cpp` (`Cast`: `SkillColorOnBuffiCast`).

**Różnice względem paczki** (świadome):
- Kolory **nie są w pakietach dodania/aktualizacji postaci** (paczka: +220 B w każdym `TPacketGCCharacterUpdate` każdej
  postaci do każdego widza). Osobny pakiet GC 59, jeden na pokolorowaną umiejętność, po pakiecie dodania i przy zmianie –
  postać bez kolorów (boty, większość graczy) nie kosztuje nic, rozmiary `TPacketGCCharacterAdditionalInfo` (70 B) /
  `TPacketGCCharacterUpdate` (52 B) i ich `static_assert` bez zmian.
- **Własna tabela** `player.skill_color` (wiersz na umiejętność), czytana przez rdzeń przy logowaniu (jak
  `player.switchbot`) i pisana przy zmianie – bez zmian w rdzeniu db, `TPlayerTable`, `tables.h`, cache'u db
  (paczka: 55 kolumn i własny cache w db; jej `SELECT` miał brakujący przecinek).
- Kolor po vnumie umiejętności, nie po „slocie” (paczka: 6 slotów ścieżki widocznej + 5 wzmocnień szamana) – stąd druga
  ścieżka, 9., konne i Buffi.
- Wzmocnienie od innego gracza: kolor rzucającego trzymany przy celu w pamięci, **nie zapisywany** w jego wierszu (paczka
  nadpisywała i zapisywała „sloty wzmocnień” celu).
- Exe barwi instancję efektu, nie wczytane dane `.mse` (paczka zmieniała współdzielone dane przy każdym utworzeniu i
  potrzebowała kopii każdego efektu na imię gracza: `GetCaseCRC32(imię + plik)`).

Boty: nie wysyłają pakietu, nie mają wiersza, logowanie bota nie robi zapytania – nic im się nie zmienia.

## Kolory po relogu – `MT2009_PLUS_SKILL_COLOR_RELOG_V1`

Właściciel, 4.11.2026 (poprawki 3.0.11, p. 1): po wylogowaniu i zalogowaniu trwające wzmocnienia (Aura Miecza, Silne
Ciało, szamańskie, Buffi) miały domyślny kolor, dopiero ponowne użycie przywracało wybrany.

- **Serwer** (tylko nakładka `playerbot_skillcolor.cpp`, bez nowych edycji rdzenia): kolor „got” (wzmocnienie od
  szamana / Buffi w kolorze rzucającego) żył tylko tyle co VID – po relogu, teleporcie czy zmianie CH znikał. Teraz jest
  w `player.skill_color_buff` (wiersz na wzmocnienie, zapis przy zmianie), czytany przy logowaniu razem z własnymi i
  wysyłany postaci i wszystkim wokół **przed** afektami (`LoadAffect` czeka na `PHASE_GAME`). Kolor „got” wzmocnienia,
  które już minęło, wypada (z wierszem) przy następnym pokazaniu postaci komuś (`SkillColorEncodeInsert`).
- **Exe**: każdy efekt afektu (i poświata Aury Miecza) zapamiętuje kolor, w którym go założono (`__AttachEffect`);
  `Mt2009SetSkillColor` i `Update` (co 0,5 s) zakładają od nowa każdy efekt, którego kolor nie jest już kolorem jego
  umiejętności – czyli efekty trwających wzmocnień założone, zanim kolory dotarły do instancji (logowanie, wejście w
  zasięg, nowa instancja), dostają kolor same, bez ponownego użycia. Nie przy niewidzialności (efekt by przepadł) ani
  w 5 s ochrony po wejściu (efekty ukryte) – wtedy chwilę później.

## Baza

`linux-port/docker/mariadb/playerbot/apply.sh` (`MT2009_PLUS_SKILL_COLOR_V1`, po bloku `switchbot`):
`CREATE TABLE IF NOT EXISTS player.skill_color (player_id INT UNSIGNED, skill_vnum SMALLINT UNSIGNED, col1..col5 INT
UNSIGNED DEFAULT 0, PRIMARY KEY (player_id, skill_vnum))` – idempotentne, brak wiersza = domyślne kolory. Sprawdzone na
jednorazowym MariaDB 11.8 (dwa przebiegi, `REPLACE`/`SELECT`/`DELETE` z wartościami do `0xFFFFFFFF`).

## Klient

- Exe (`client-patches/exe`, `ENABLE_MT2009_SKILL_COLOR`, `Mt2009SkillColor.cpp`) – README exe.
- Root: `uiskillcolor.py`, `skillcolorpick.py`, `uiscript/skillcolorwindow.py`, przycisk „Kolory” w zakładce umiejętności
  (`uicharacter.py`, prawa kolumna, 5. rząd – pusty na każdej zakładce).
- Obrazki: paczka `skillcolor` (`client-2.0.30/tools/skillcolor`: `build_skillcolor_packs.py` + `verify_skillcolor.py`).

## Bramka wersji klienta

GC 59 to nowy pakiet – starszy exe by go nie odczytał. Root `constinfo.py` mówi **1.3.2** (1010302) tylko z exe, który
ma `app.MT2009_SKILL_COLOR_EXE`; auth (`m2-render-config`, `M2_CLIENT_MIN_VERSION` domyślnie **1010302**) odrzuca 1.3.1 i
starsze komunikatem „UPDATE”. Serwer z własnym `M2_CLIENT_MIN_VERSION` w `.env` musi je podnieść.
