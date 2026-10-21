# Boss Świata (World Boss) – `MT2009_PLUS_WORLDBOSS_V1`

Event z polskiej wiki („Boss Świata”, decyzja właściciela z 21 października 2026). Kopie stron:
`/opt/metin2/cache/yohara/wiki/worldboss/`, opis zmian i różnic: `/opt/metin2/cache/yohara/boss-swiata.md`.
Cała logika jest w nakładce `linux-port/overlays/playerbot/src/game/src/playerbot_worldboss.h` (dołączonej do
`playerbot_manager.cpp`, tik co sekundę z `playerbot_events.h`); tu są tylko zmiany plików silnika, opisane w
`edits.json`:

| Znacznik | Plik | Co robi |
|---|---|---|
| `MT2009_PLUS_WORLDBOSS_V1 (damage)` | `char_battle.cpp` | `CHARACTER::Damage`: każde trafienie gracza w stojącego bossa → `WorldBossOnDamage` (suma obrażeń gracza) |
| `MT2009_PLUS_WORLDBOSS_V1 (no drop)` | `char_battle.cpp` | `CHARACTER::Reward`: bossowie i słudzy 4420-4479 nic nie dropią (ani yang); śmierć bossa jest tu notowana |
| `MT2009_PLUS_WORLDBOSS_V1 (drop)` | `item_manager.cpp` | `CreateDropItem`: buff poziomu łupu (+100/50/25 % szansy na drop, affect 720) |
| `MT2009_PLUS_WORLDBOSS_V1 (declare)`, `(table)` | `cmd.cpp` | komenda `/worldboss` |

- `Apply-WorldBossPatch.ps1` – Windows (`tools/port/Apply-MT2009PlusEngine.ps1`, na końcu: kotwiczy na liniach
  shipdefense, zestawy i ysets);
- `apply_worldboss.py <game/src>` – Linux/VPS; oba czytają ten sam `edits.json`.

Zmiana już nałożona (jest jej znacznik) jest pomijana; zmiana, której kodu nie ma dokładnie raz, przerywa całość,
zanim cokolwiek zostanie zapisane.

## Jak działa

- **Tryb** (`player.worldboss_config.mode`, strona panelu Seban „Boss Świata”): 1 zawsze włączony (domyślnie, jak
  na serwerze eventowym), 2 tylko w oknach harmonogramu (rodzaj `worldboss` w Planerze eventów), 0 wyłączony.
- **Pojawienie**: losowy z 6 bossów (Azrael 4449, Bagjanamu 4429, Ogr Maximus 4479, Polifem 4439, Smoczy Strażnik
  Idall 4469, Zjawa Żółtego Tygrysa 4459 – numery i modele „w_*” GF) w losowym miejscu Doliny Seungryong (64),
  Pustyni Yongbi (63), Doyyumhwan (62) albo Góry Sohan (61) – `worldboss.txt` (`tools/worldboss/gen_worldboss.py`).
  **Co 120 minut** (`MT2009_PLUS_WORLDBOSS_ICON_V1`, decyzja właściciela z 21.10.2026): kolejny boss pojawia się
  `break_min`–`break_max` minut (domyślnie 120–120) **od pojawienia się poprzedniego** – niezależnie od tego, czy padł
  po 10 minutach, czy uciekł – ale najwcześniej 5 min po jego upadku/ucieczce. Instalacje z pierwszą domyślną
  przerwą 60–120 przechodzą raz na 120–120 (`worldboss.sql`, kolumna `defaults_rev`; ustawienia zmienione przez
  operatora zostają). Komunikat na cały serwer z obszarem i kanałem; przypomnienie co 10 min.
- **Ikona na mapie** (`MT2009_PLUS_WORLDBOSS_ICON_V1`): rdzeń bossa co 3 s wysyła graczom na jego mapie
  `WB mark <x> <y> <x lokalne> <y lokalne> <vnum>`, po upadku/ucieczce `WB unmark`; klient (`root/uiworldboss.py`,
  haki w `root/uiminimap.py`) rysuje ikonę Bossa Świata na mapie (M) i na minimapie (dalej – na brzegu minimapy,
  w jego kierunku), nazwa bossa po najechaniu myszą. Bez zmian w exe.
- **Prowadzi go jeden rdzeń**: ten z kanału `worldboss_config.channel` (domyślnie 1), który hostuje te mapy.
  Pozostałe rdzenie czytają `player.worldboss_state` dla okna.
- **Walka**: sumowane obrażenia graczy i botów (od 21.10.2026 boty liczą się jak gracze) od `min_level` (30); kto
  opuści mapę albo grę, traci swoje obrażenia. Przy 75/50/25 % życia boss wzywa `groups_per_call` (6) grup po 5 sług. Po `fight_minutes` (45)
  boss ucieka: nikt nie dostaje nagrody.
- **Życie**: `hp_full` (8 000 000) × procent, który rośnie: pierwszy boss `hp_start_pct` (30 %), każdy upadek
  `+hp_step_pct` (5 %) do 100 % („na początku bossowie są słabi”).
- **Ranking i nagrody** (postacie – gracze i boty – na mapie w chwili upadku, z ≥ `min_damage` = 250 000): miejsca 1-10 poziom łupu I,
  11-25 II, 26-100 III, dalej IV – przedmioty i buff dropu z `worldboss.txt`, punkty rangi 10/5/2/1 dla postaci i jej
  gildii (`player.worldboss_points`). Misja „Pokonaj Bossa Świata”: ≥ `mission_damage` (100 000) w pokonanego
  bossa = Wartość Ataku +20 % na 3 h (affect 721), raz dziennie. Nagrody czekają w oknie (`player.worldboss_reward`)
  do pojawienia się kolejnego bossa – potem przepadają.
- **Sezon** (`season_weeks`, 8 tygodni): 25 najlepszych postaci i 3 najlepsze gildie każdego królestwa dostają
  nagrody sezonu (nagroda gildii dla każdego członka, który nadal w niej jest i zdobył dla niej ≥ 1 pkt).
- **Boty** (`bots` = 1): rajdują bossa (wiersze `PLAYERBOT_WORLD_BOSSES`, poziom 100-135, wszystkie królestwa).
  Decyzja właściciela z 21.10.2026 („W rankingach również boty. Nagrody również dla botów.”): obrażenia botów liczą
  się w rankingu jak graczy (poziomy łupu, misja, punkty rangi postaci i gildii, sezon), a nagrody czekające na bota
  każdy rdzeń wydaje mu sam co 30 s (`BotClaims` – przedmioty do ekwipunku, gdy ma wolne miejsce, buffy dropu/ataku).

## Komendy

Gracz: `/worldboss info`, `/worldboss ranking`, `/worldboss sezon <1-3>`, `/worldboss odbierz` (okno klienta
`root/uiworldboss.py`). GM: `/worldboss spawn [boss 1-6] [mapa]`, `/worldboss ucieczka`, `/worldboss przeladuj`,
`/worldboss stan`.

Dane: `linux-port/docker/mariadb/playerbot/worldboss.sql` (moby, przedmioty 38015/80031/80032, tabele),
`linux-port/docker/game/worldboss/` (worldboss.txt, Skrzynka Tajemnic), quest `quest/worldboss_kupony.quest`
(Kupon SM (20)/(10)); klient: `client-patches/client-2.0.30` (`uiworldboss.py`, `uiscript/worldboss*.py`,
`tools/yworldboss`).
