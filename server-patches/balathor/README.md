# Krypta Balathora (autor modułu: dracaryS)

Gildyjne leże Białego Smoka (pl-wiki „Krypta Balathora”, wersja 24.3) dla linii 3.x „Yohara”. Znacznik:
`MT2009_PLUS_BALATHOR_V1` (przełącznik: `MT2009_PLUS_BALATHOR_SWITCH_V1`). Wsad i instrukcja: `mods-incoming/balathor/`.

## Gdzie co jest

| Część | Miejsce |
|---|---|
| Haki silnika | `edits.json` (50 zmian: `common/service.h` – `#define __BALATHOR__`, db `ClientManagerEventFlag.cpp`, game: `char*.cpp/h`, `cmd*.cpp`, `guild.h`, `guild_manager.h`, `input_db/main.cpp`, `main.cpp`, `motion.h/.cpp`, `questlua.h/.cpp`, `utils.h`); `apply_balathor.py <game/src>` (Linux, ostatni w kolejce po `npcloc`) i `Apply-BalathorPatch.ps1` (Windows, ostatni krok `tools/port/Apply-MT2009PlusEngine.ps1`) czytają ten sam plik |
| Logika | nakładka `linux-port/overlays/playerbot/src/game/src/`: `balathor.cpp/.h`, `balathor_manager.cpp`, `questlua_balathor.cpp` (autora, teksty dla graczy po polsku, `std::min`), `balathor_support.cpp` (nasze: pomocnicze funkcje autora z `guild.cpp`, `guild_manager.cpp`, `utils.cpp`, `questlua_guild.cpp` – żeby tamte pliki silnika zostały bez zmian; `guild.get_near_count/get_near_pids/get_flag/set_flag/get_level` dopisane do tabeli `guild`, `balathor.is_open()`), `json.hpp` (nlohmann/json 3.11.3, MIT) |
| Dane serwera | `linux-port/docker/game/balathor/` (krok Dockerfile „Krypta Balathora”): mapa 420 `metin2_map_guild_whitedragon_boss`, ruchy potworów `data/monster/guild_whitedragon*`, `balathor.json` → `locale/poland/`, skrzynie `special_item_group.balathor.txt` |
| Baza | `linux-port/docker/mariadb/playerbot/balathor.sql` (generator `tools/balathor/gen_balathor_sql.py`, krok `apply.sh`): 17 potworów/NPC/kamieni, żywioły, Ognista Strzała 30395, skrzynie 83075/83076 |
| Quest | `linux-port/docker/game/quest/krypta_balathora.quest` (cp1250) |
| Boty | `playerbot_types.h` (`IsPlayerBotOffLimitsMap`: 420) i `playerbot_party_dungeon.h` (`IsPlayerBotDungeonPartyMove`: żaden bot nie wchodzi za człowiekiem) |
| Klient | exe: `client-patches/exe` (`__BALATHOR__`, README tam); root/paczki: `client-patches/client-2.0.30/root` + `tools/balathor` |

## Włączanie

`M2_BALATHOR_ON=0` (domyślnie, `.env`): żaden rdzeń nie hostuje 420, `balathor.is_open()` = false, Dolnarr nic nie
proponuje – serwer bez zmian dla graczy. `1` (dopiero z klientem, który ma mapę – stary klient zamyka się na nowej mapie):
`bin/m2-render-config` dopisuje 420 do **game1**. Mapa musi być na rdzeniu NPC: `CBalathorManager::Create` tworzy prywatną
kopię (4200000+) na rdzeniu, na którym działa quest Dolnarra (`map_allow_find(420)`), więc game1 obok Doyyumhwaji (62),
tak jak Schronienie Meley (356) – nie game3.

## Decyzje i ustawienia (`balathor.json`)

- Wejście: **Strażnik Smoków Dolnarr (20419)** na Doyyumhwaji (62, pole 83,851 – ten sam NPC co Schronienie Meley),
  wyjście 84,853. Quest wejściowy („Dziwne Znalezisko”) pominięty.
- Każdy członek: poziom `register_min_level` 120 i **Champion 4** (`pc.get_conqueror_level() >= 4`).
- Gildia: mistrz rejestruje, 4–16 członków obok (boty się nie liczą), 600 pkt rankingu gildii (pobierane:
  `guild.set_ladder_point(-600)`), skarbiec ≥ 500 000 Yang (sprawdzany), odnowienie 3 h (`register_wait_time` 10800),
  limit 60 min (`waiting_full_time`). Kanał: wejście tylko na kanale rejestracji.
- `register_min_guild_level` **21** (wiki; poziomy gildii do 40 daje system gildii – `server-patches/guildsys`).
- `fail_rewards` = Mroźna Skrz. Balathora (83075), `success_rewards` = 83075 + Mroźna Skrz. Balathora+ (83076).
- Ognista Strzała = **30395** (w paczce 30345 = nasze Ezoteryczne Drewno).
- Ruchy ETC1–ETC3 (`MOTION_ETC_1..3`) mają numery 39–41 = `NAME_ETC_1..3` klienta (klient ma `NAME_SPECIAL_6` = 38).

## Podłączone do systemu gildii (`server-patches/guildsys`, MT2009_PLUS_GUILDSYS_V1)

- bank gildii ≥ 500 000: `guild.get_bank()` (skarbiec, który można wydać),
- gildia istnieje ≥ 24 h (`guild.age()`), każdy zgłaszany członek jest w gildii ≥ 24 h (`guild.member_age()` w bloku
  `q.begin_other_pc_block`) – kolumny `player.guild.create_time` / `guild_member.join_time` (`guildsys.sql`),
- 3 umiejętności gildii Balathora (158–160: Burza / Wola / Nieugiętość Balathora) z ksiąg 50344–50346 – wiersze
  12–14 skrzyni 83076 (po 20 %); umiejętności gildii działają w Krypcie bez wojny gildii.

## Czego linia nie ma (pominięte w skrzyniach)

Z „Mroźna Skrz. Balathora” / „Mroźna Skrz. Balathora+” (pl-wiki) nie ma w naszym świecie (`world.item_proto`, 28.10.2026):

- materiały na **Wężowy Czepiec**: Oko, Róg, Ścięgno, Skrzydło, Łuska Balathora (i sam hełm),
- **Runy Wykuwania**: poz. przedmiotu, zestawu broni, przedmiotów do zwierząt, pasów, akcesoriów,
- **Kula Polimorfii Hwachy**,
- **Bilet Przejścia (Balathor)** – dlatego `register_ticket_vnum` 0 (tylko punkty rankingu),
- Wino z Kwiatu Brzosk. **XL** – zamiast niego zwykłe (70020, ×5); Kula Błogosławieństwa = nasz Marmur
  Błogosławieństwa (70024).

Wiki nie podaje szans ani ilości: zwykła skrzynia daje 1 przedmiot (wagi nasze), skrzynia+ losuje każdy wiersz osobno
(`Type Pct`, procenty nasze).

## Uwagi

- Kolejność wdrożenia: `apply_balathor.py` po `npcloc` (`/opt/metin2/cache/yohara-deploy.sh`).
- Zmiana pliku silnika już ze znacznikiem jest pomijana; kod, którego nie ma dokładnie raz, przerywa całość przed zapisem.
- Komendy GM: `/balathor create|close|reload|next_fail|...` (autora); `/balathor unpoly` dla wszystkich.
