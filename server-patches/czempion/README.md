# Poziom Czempiona i statystyki Sung Ma

Poziom Czempiona (w kodzie GF/Owsap „conqueror level”) i cztery statystyki Sung Ma dla MT2009 PLUS 3.x „Yohara”.
Plan: `cache/yohara/plan-champion-sungma.md` (kroki 1–8). Znaczniki: `MT2009_PLUS_CHAMPION_V1 (…)` (poziom, exp,
zapis) i `MT2009_PLUS_SUNGMA_V1 (…)` (punkty i kary na mapach). Makro silnika: `ENABLE_CONQUEROR_LEVEL`
(`common/CommonDefines.h`; skrypt zapisuje wszystkie zmiany albo żadnej, więc makro nigdy nie przyjdzie bez haków).

Logika według Amerii (`ENABLE_YOHARA_SYSTEM` – jedyna pełna publiczna implementacja), liczby z klienta GF 26.1.11
(`<mapa>/sungma_attr.txt`) i z Owsapa v6.2.6 (`mob_proto.txt`, kolumna `SungMaExp`; nazwy funkcji questów).

## Gdzie co jest

| Część | Miejsce |
|---|---|
| Logika | `linux-port/overlays/playerbot/src/game/src/playerbot_champion.h/.cpp` (nazwa `playerbot_*`, żeby nakładka i lista plików aktualizacji niosły je same) |
| Haki silnika | `edits.json` (25 zmian w 12 plikach: common, db, game); `apply_czempion.py <game/src>` (Linux) i `Apply-CzempionPatch.ps1` (Windows, krok `tools/port/Apply-MT2009PlusEngine.ps1` po Obronie Statku) czytają ten sam plik |
| Baza | `linux-port/docker/mariadb/playerbot/czempion.sql` (`apply.sh`): 8 kolumn w `player.player` i `player_deleted` (ta sama kolejność – usunięta postać jest kopiowana `SELECT *`), przedmioty 72068–72071 |
| Dane serwera | `linux-port/docker/game/champion/` → `share/locale/poland/` (krok Dockerfile „share: Poziom Czempiona”): `sungma_table.txt`, `sungma_mob_exp.txt`; generator `tools/champion/gen_sungma_data.py` |
| Questy | `linux-port/docker/game/quest/czempion.quest` (posąg 20433), `czempion_nowa_wola.quest` (72068–72071) |
| Klient (Etap B, exe 3.0) | exe: `client-patches/exe` (`MT2009_PLUS_CHAMPION_V2`, `UserInterface/Mt2009Champion.cpp`); root: `uicharacter.py` + `uiscript/characterwindow.py` (strona Sung Ma okna postaci), `game.py`, `interfacemodule.py`, `keybind.py`, `constinfo.py`, `uitooltip.py`, `localeinfo_point.py` |

Zmiana zachowana, gdy jest już jej znacznik; zmiana, której kodu nie ma dokładnie raz, przerywa całość, zanim
cokolwiek zostanie zapisane. Pliki zachowują swoje końce linii.

## Jak to działa

- **Zapis**: `TPlayerTable` (common/tables.h) dostaje na końcu `conqueror_level`, `conqueror_level_step`,
  `conqueror_point`, `conqueror_exp`, `sungma_str/hp/move/immune`; db czyta je w `SELECT` gracza zaraz po
  `horse_skill_point` (z zabezpieczeniem liczby kolumn) i zapisuje w `UPDATE`. **db i game muszą być z tej samej
  budowy** (ten sam nagłówek) – pakiet `HEADER_GD_PLAYER_SAVE` / `HEADER_DG_PLAYER_LOAD_SUCCESS` ma `sizeof(TPlayerTable)`
  (+16 B, `#pragma pack(1)`, 32 bit bez zmian układu wcześniejszych pól). `czempion.sql` musi przejść przed startem db.
- **Punkty**: `POINT_SUNGMA_STR/HP/MOVE/IMMUNE` za `POINT_ENCHANT_DARK` – tylko na serwerze (jak żywioły, nie idą
  w pakiecie punktów, exe bez zmian). Wartość „real” = rozdane punkty (`player.sungma_*`), `GetPoint()` = real +
  to, co dodadzą przedmioty/afekty (APPLY_SUNGMA_* przyjdzie z przedmiotami Yohary). Kary liczone na `GetPoint()`.
- **Odblokowanie** (`pc.set_conqueror()`, quest posągu 20433): poziom = `max_level` serwera (120), flaga Hydry
  `obrona_statku.completed_at_120` (jedyne miejsce: `champion::HYDRA_DONE_FLAG` w `playerbot_champion.cpp`) i co
  najmniej jedna pełna kula exp (¼ paska = 625 000 000 na 120). Boty – na razie nie (decyzja właściciela).
- **Exp na 120** (`char.cpp`, „max level exp”): pasek rośnie do `next_exp − 1` i staje, bez awansu (wcześniej
  exp na 120 był całkowicie blokowany, więc warunku kuli nie dało się spełnić). Skutek uboczny jak w oficjalnej grze:
  śmierć na 120 zabiera exp (1%, najwyżej 800 000 – stara reguła silnika).
- **Exp Czempiona**: tylko z potworów zabitych **na mapie Sung Ma**, wartość z `sungma_mob_exp.txt` (356 potworów
  Owsapa), podział według obrażeń jak zwykły exp; udział drużyny po równo między jej Czempionów w zasięgu.
  Mnożniki: event exp (`PRIV_EXP_PCT`), bonus exp przedmiotów, bonus z ItemShopu i flaga zdarzeń
  **`conqueror_exp_rate`** (procent, 0/brak = 100) do kalibracji; najwyżej 1/10 paska na zabójstwo.
  Tabela exp poziomów 1–29 z Amerii (433 400 … 188 537 554), poziom 30 = koniec.
- **Punkty statystyk**: 1 punkt za każdą ¼ paska (3 na poziom, 4. ćwiartka = awans) – 87 do poziomu 30;
  najwyżej 90 na statystykę. `/conqueror_stat smh_str|smh_hp|smh_move|smh_inmune` (nazwy z `uicharacternew.py` GF).
- **Kary na mapie Sung Ma** (gdy statystyka poniżej wymagania mapy):
  Siła – obrażenia gracza w potwory /2; Witalność – maks. PŻ /2; Odporność – prędkość ruchu /2;
  Inteligencja – trucizna/podpalenie/krwawienie gracza na potworach wchodzą o połowę rzadziej (zwykłe ciosy i umiejętności).
  Bez Poziomu Czempiona: brak ataku na potwory (`battle_is_attackable`) i 0 obrażeń.
- **Mapy**: `sungma_table.txt` wymienia mapy po **nazwach** (19 map Yohary z klienta GF). Silnik porównuje je z
  `map/index` rdzenia – nazwa, której nie mamy, nic nie zmienia. Na dziś **żadna nasza mapa** nie jest mapą Sung Ma
  (sprawdzone 13.10.2026: `metin2_map_eastplain_*`, `empirecastle` itd. to mapy Yohary – w Owsapie indeksy 373–396).
- **Boty**: bez Poziomu Czempiona (decyzja właściciela: na razie nie – `pc.set_conqueror` odmawia botowi) i bez
  wejścia na mapy Sung Ma: `TransitionPlayerBotMap` (`playerbot_travel.h`) odmawia (`sungma_map`) – przez nią idą
  łowiska i wyjazdy, podążanie Towarzysza i drużyny, LFG lochów/gildii i `WarpBot` (warp z questa/GM).
- **Klient (Etap B)**: liczby to punkty pakietu punktów (`POINT_CONQUEROR_*`, `POINT_SUNGMA_*`), wymagania mapy –
  komenda czatu `sungma_map <str> <hp> <move> <imm>` (przy wejściu na mapę i po zmianie). Etap A (`champion_info`,
  `uichampion.py`) usunięty.

## Komendy

- gracz: `/conqueror_stat smh_str|smh_hp|smh_move|smh_inmune` (punkt), `/conqueror_stat info` (odśwież okno).
- GM (`GM_HIGH_WIZARD`): `/champion` (stan), `/champion unlock` (bez warunków), `/champion level <n>`, `exp <n>`,
  `give <exp>`, `points <n>`, `stat <0-3> <n>`, `reset`, `reload` (oba pliki danych).

## Questy (funkcje)

`pc.get_conqueror_level`, `pc.get_conqueror_exp`, `pc.get_conqueror_next_exp`, `pc.get_conqueror_point`,
`pc.get_conqueror_unlock_state` (0 ok, 1 już Czempion, 2 za niski poziom, 3 brak Hydry, 4 brak kuli exp, 5 bot),
`pc.set_conqueror`, `pc.give_conqueror_exp(2)`, `pc.get_sungma_str/vit/res/int`, `pc.reset_sungma_status(idx)`,
`npc.get_sungma_exp` – dopisywane do istniejących tabel `pc`/`npc` (`questlua.cpp`, po Obronie Statku).

## Etap B – exe 3.0 „Yohara” (`MT2009_PLUS_CHAMPION_V2`, 13.10.2026)

Wymusza aktualizację klienta przy 3.0 (zgoda właściciela). Zmiany serwera: 11 edycji `MT2009_PLUS_CHAMPION_V2 (…)`
na końcu `edits.json` (po edycjach V1, ta sama kolejność na świeżym drzewie i na już załatanym) + `playerbot_champion.cpp`.

| Co | Gdzie | Szczegóły |
|---|---|---|
| Numeracja punktów | `common/length.h` (`(packet points)`, `(champion points)`) | żywioły **178–183 bez zmian** (applytype 1206 talizmanów w `item_proto`), `POINT_SUNGMA_STR/HP/MOVE/IMMUNE` **184–187** (jak w Etapie A, = `APPLY_SUNGMA_*` – w tym silniku apply to punkt), `POINT_CONQUEROR_LEVEL/_LEVEL_STEP/_EXP/_NEXT_EXP/_POINT` **188–192**, `POINT_PACKET_NUM` = `POINT_MAX_NUM` = **193** (exe: `POINT_MAX_NUM` 193). Kolejność „sungma przed conqueror” zamiast GF – żeby nie przenumerować żywiołów ani sungmy. |
| Pakiet punktów | `packet.h` (bez zmian w tekście) | `INT points[POINT_PACKET_NUM]`: 1 + 4·178 = 713 B → **773 B**; zmiana punktu (`PointChange`) wysyła teraz też żywioły i sungmę |
| Wypełnienie | `char.cpp` `(points packet)` → `ChampionFillPoints` | poziom, krok, exp, exp do następnego, wolne punkty Czempiona |
| Niebieski poziom nad głową | `packet.h` `(add packet)`, `(update packet)`; `char.cpp` `(insert)`, `(update)` | `DWORD dwConquerorLevel` na końcu `TPacketGCCharacterAdditionalInfo` (66 → **70 B**) i `TPacketGCCharacterUpdate` (48 → **52 B**); `champion::Unlock`/awans wysyłają `UpdatePacket()` |
| Odświeżanie | `playerbot_champion.cpp` `SendInfo` | 5 punktów Czempiona + 4 sungmy jako `HEADER_GC_CHARACTER_POINT_CHANGE` (było: `champion_info` na czacie) |
| Limit przedmiotu | `common/item_length.h` `(limit)`, `char_item.cpp` `(use limit)`, `(equip limit)`, `db/src/ProtoReader.cpp` `(limit name)` | `LIMIT_CONQUEROR_LEVEL` = **10** (u nas nie ma `LIMIT_PITTY_REFINE`, który w Amerii daje 11); użycie/założenie przy za niskim Poziomie Czempiona – komunikat po polsku |
| Bramka wersji | `linux-port/docker/game/bin/m2-render-config` | auth `server_version: ${M2_CLIENT_MIN_VERSION:-1010300}`; root `constinfo.py` mówi 1.3.0 (1010300) tylko z exe Yohary – starszy klient dostaje „UPDATE” = „Wymagana aktualizacja klienta gry przez Patcher.” |
| Asercje | `playerbot_champion.cpp` (serwer), `Mt2009Champion.cpp` (exe) | numery 178/184/188/193, `LIMIT_CONQUEROR_LEVEL` 10, rozmiary 773/70/52 B – rozjazd nie skompiluje się po żadnej stronie |

Bez zmian: `APPLY_SUNGMA_PER_*` / `HIT_BUFF_SUNGMA_*` (Owsap/GF; nie mamy jeszcze przedmiotów z nimi), nowy pakiet
`HEADER_GC_SUNGMA_ATTR_UPDATE` (Ameria) – wymagania mapy zostają komendą czatu `sungma_map`, bo okno postaci tylko je
wyświetla (wartość na czerwono + dymek), a komenda nie wymaga zmiany protokołu.

## PŻ i PE za poziomy Czempiona (`MT2009_PLUS_CHAMPION_HPSP_V1`)

Decyzja właściciela z 13.10.2026: każdy poziom Czempiona dodaje tyle, co zwykły awans – PŻ i PE klasy na
poziom (`JobInitialPoints`: 40 PŻ i 20 PE dla każdej klasy), czyli do +1200 PŻ i +600 PE na 30 poziomie.
Liczone w `ComputePoints` (`char.cpp`), więc działa od razu po awansie i po zalogowaniu.
