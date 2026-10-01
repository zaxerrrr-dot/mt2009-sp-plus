# Menedżer eventów w grze (30 września) – `MT2009_PLUS_EVENT_MANAGER_V1`

Wspólny szkielet dla mini gier z Owsapa (Złap Króla, Rumi, Yut Nori, Dzieci Kwiaty), które
dojdą następne. Logika jest w nakładce `linux-port/overlays/playerbot/src/game/src/playerbot_ingame_events.h`
(dołączonej do `playerbot_manager.cpp`, tik co sekundę z `playerbot_events.h`); tu są tylko
zmiany plików silnika, opisane w `edits.json`:

| Znacznik | Plik | Co robi |
|---|---|---|
| `MT2009_PLUS_EVENT_MANAGER_V1 (header)` | `packet.h` | `HEADER_GC_INGAME_EVENT = 183` |
| `MT2009_PLUS_EVENT_MANAGER_V1 (packet)` | `packet.h` | `TPacketGCInGameEvent` (5 B) + `TPacketGCInGameEventInfo` (42 B: klucz do 24 znaków, włączony, start, koniec, koniec okna nagród, liczba), `INGAME_EVENT_SUBHEADER_GC_LIST/UPDATE` |
| `MT2009_PLUS_EVENT_MANAGER_V1 (declare)`, `(table)` | `cmd.cpp` | komenda `/ingame_event` |
| `MT2009_PLUS_EVENT_MANAGER_V1 (command)` | `cmd_general.cpp` | `ACMD(do_ingame_event)` → `InGameEventCommand` z nakładki |

- `Apply-EventManagerPatch.ps1` – Windows (`tools/port/Apply-MT2009PlusEngine.ps1`, po playerqol,
  bo kotwiczy na liniach goblina);
- `apply_eventmanager.py <game/src>` – Linux/VPS; oba czytają ten sam `edits.json`.

Zmiana już nałożona (jest jej znacznik) jest pomijana; zmiana, której kodu nie ma dokładnie raz,
przerywa całość, zanim cokolwiek zostanie zapisane.

## Jak to działa

- **Lista eventów**: każdy rodzaj harmonogramu z paneli (`chest`, `exp`, `drop`, `yang`, `tanaka`,
  `zuo`, `bossloot`, `metinloot`, `goblin` i nowe `catchking`, `rumi`, `yutnori`, `flower`,
  `easter`) jest eventem pod swoją nazwą, do tego eventy samej flagi (`rumi_xmas` =
  `mini_game_okey`, świąteczne Rumi Owsapa). Każdy rdzeń liczy stan sam, co sekundę.
- **Do klienta**: dopiero po `/ingame_event hello <caps>` z pythona klienta (1 = pakiet 183,
  2 = linie `IGE begin/ev/end` dla starego exe, 4 = polecenia Owsapa `<flaga> <wartość>`):
  przy powitaniu cała lista, potem przy każdej zmianie. Warp i zmiana kanału to nowe okno gry
  i nowe powitanie. `/ingame_event info` – lista jeszcze raz, `/ingame_event gm` – stan dla GM.
- **Flagi Owsapa** (pisze tylko rdzeń lidera, ten od ogłoszeń): start – flaga (`mini_game_okey_normal`,
  `mini_game_yutnori`, `mini_game_catchking`: epoka końca; `e_flower_drop`: drop 100;
  `easter_drop` i `easter_rabbit`: 1), `*_drop` = 100 jeśli puste, `*_reward` = 0; w trakcie flaga
  idzie za końcem okna; koniec – flaga 0, Rumi, Yut Nori i Dzieci Kwiaty (`e_flower_reward`, MT2009_PLUS_FLOWER_V1) otwierają 7-dniowe okno nagród
  (`*_reward` = teraz + 7 dni). Flaga ustawiona ręcznie przez GM też uruchamia event, a lider
  kończy flagę-epokę po czasie (jak `UpdateInGameEvent` Owsapa).
- **NPC stołów** na mapach 1/21/41 (komórki Owsapa, sprawdzone jako przechodnie na naszym
  `server_attr`): Rumi 20417 (607,619 / 595,613 / 353,741), Yut Nori 20502 (608,614 / 596,608 /
  358,748), Złap Króla 20506 (608,623 / 596,614 / 350,738) – w czasie eventu, a Rumi i Yut Nori
  także w oknie nagród. NPC bez wiersza `mob_proto` jest pomijany (jedna linia w logu), dopóki
  mini gra go nie doda. 20505 (rzucający w Yut Nori) to tylko model w oknie klienta – nie stoi
  na mapie.
- **Dla mini gier**: `InGameEventIsActive(key)`, `InGameEventEndTime(key)`,
  `InGameEventRewardEndTime(key)`, `InGameEventValue(key)` (zadeklarować tam, gdzie używane, jak
  `GoblinCommand`).

Klient: `client-patches/exe` (pakiet, moduł `ingameEventSystem`) i
`client-patches/client-2.0.30/root` (`ingameevent.py`, `uiingameevent.py`, haki w `game.py`,
`interfacemodule.py`, `uieventcalendar.py`). Jak dodać nowy event bez nowego exe:
`client-patches/exe/README.md`.
