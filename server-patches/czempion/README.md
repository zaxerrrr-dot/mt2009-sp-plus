# Poziom Czempiona i statystyki Sung Ma

Poziom Czempiona (w kodzie GF/Owsap „conqueror level”) i cztery statystyki Sung Ma dla MT2009 PLUS 3.x „Yohara”.
Plan: `cache/yohara/plan-champion-sungma.md` (kroki 1–8). Znaczniki: `MT2009_PLUS_CHAMPION_V1 (…)` (poziom, exp,
zapis) i `MT2009_PLUS_SUNGMA_V1 (…)` (punkty i kary na mapach). Makro silnika: `ENABLE_CONQUEROR_LEVEL`
(ostatnia zmiana `edits.json`, w `common/CommonDefines.h`).

Logika według Amerii (`ENABLE_YOHARA_SYSTEM` – jedyna pełna publiczna implementacja), liczby z klienta GF 26.1.11
(`<mapa>/sungma_attr.txt`) i z Owsapa v6.2.6 (`mob_proto.txt`, kolumna `SungMaExp`; nazwy funkcji questów).

## Gdzie co jest

| Część | Miejsce |
|---|---|
| Logika | `linux-port/overlays/playerbot/src/game/src/playerbot_champion.h/.cpp` (nazwa `playerbot_*`, żeby nakładka i lista plików aktualizacji niosły je same) |
| Haki silnika | `edits.json` (24 zmiany w 12 plikach: common, db, game); `apply_czempion.py <game/src>` (Linux) i `Apply-CzempionPatch.ps1` (Windows, krok `tools/port/Apply-MT2009PlusEngine.ps1` po Obronie Statku) czytają ten sam plik |
| Baza | `linux-port/docker/mariadb/playerbot/czempion.sql` (`apply.sh`): 8 kolumn w `player.player` i `player_deleted` (ta sama kolejność – usunięta postać jest kopiowana `SELECT *`), przedmioty 72068–72071 |
| Dane serwera | `linux-port/docker/game/champion/` → `share/locale/poland/` (krok Dockerfile „share: Poziom Czempiona”): `sungma_table.txt`, `sungma_mob_exp.txt`; generator `tools/champion/gen_sungma_data.py` |
| Questy | `linux-port/docker/game/quest/czempion.quest` (posąg 20433), `czempion_nowa_wola.quest` (72068–72071) |
| Klient (Etap A) | `client-patches/client-2.0.30/root/uichampion.py` (+ `game.py`, `interfacemodule.py`, `keybind.py`) |

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
- **Etap A klienta**: komendy czatu `champion_info <lv> <exp> <next> <pkt> <str> <hp> <move> <imm> <krok>` i
  `sungma_map <str> <hp> <move> <imm>` (przy wejściu na mapę i po każdej zmianie) – okno `uichampion.py`.

## Komendy

- gracz: `/conqueror_stat smh_str|smh_hp|smh_move|smh_inmune` (punkt), `/conqueror_stat info` (odśwież okno).
- GM (`GM_HIGH_WIZARD`): `/champion` (stan), `/champion unlock` (bez warunków), `/champion level <n>`, `exp <n>`,
  `give <exp>`, `points <n>`, `stat <0-3> <n>`, `reset`, `reload` (oba pliki danych).

## Questy (funkcje)

`pc.get_conqueror_level`, `pc.get_conqueror_exp`, `pc.get_conqueror_next_exp`, `pc.get_conqueror_point`,
`pc.get_conqueror_unlock_state` (0 ok, 1 już Czempion, 2 za niski poziom, 3 brak Hydry, 4 brak kuli exp, 5 bot),
`pc.set_conqueror`, `pc.give_conqueror_exp(2)`, `pc.get_sungma_str/vit/res/int`, `pc.reset_sungma_status(idx)`,
`npc.get_sungma_exp` – dopisywane do istniejących tabel `pc`/`npc` (`questlua.cpp`, po Obronie Statku).

## Etap B (nowy exe – nie teraz, w jednej budowie klienta po zgodzie właściciela)

- `Locale_inc.h`: `ENABLE_CONQUEROR_LEVEL`, `ENABLE_CONQUEROR_UI` (dziś `app.*` = 0, `uicharacternew.py` śpi).
- `length.h` (wspólny z exe): `POINT_CONQUEROR_LEVEL/_LEVEL_STEP/_EXP/_NEXT_EXP/_POINT`, `POINT_SUNGMA_*` **przed**
  `POINT_PACKET_NUM` w kolejności exe (178 → 187) – serwer przesuwa wtedy `POINT_SUNGMA_*` sprzed elementów i wypełnia
  `points[POINT_CONQUEROR_*]` w `PointsPacket` (wzór Ameria `char.cpp:2350`). Zmiana rozmiaru pakietu punktów =
  wymuszona aktualizacja klienta.
- `PythonPlayerModule.cpp`: stałe `CONQUEROR_*`, `SUNGMA_*`, `GetConquerorEXP()`; `Packet.h`/`PythonNetworkStreamPhaseGame.cpp`:
  `dwConquerorLevel` w CharacterAdd/Update (niebieski poziom nad głową; serwer: `char.cpp` Add/UpdatePacket);
  opcjonalnie `HEADER_GC_SUNGMA_ATTR_UPDATE` zamiast komendy `sungma_map`, `FLY_CONQUEROR_EXP`.
- Python: `uicharacternew.py` + `uiscript/characterwindow.py` GF (strona Sung Ma, grafiki `char_info_sungma_*`),
  pasek exp Czempiona w `uitaskbar.py`; `uichampion.py` (Etap A) można wtedy usunąć.
- Klient (dane, przy najbliższej paczce): `item_list.txt`/`item_proto`/`itemdesc.txt` dla 72068–72071 i ikony
  `icon/item/72068-72071.tga` z GF.
