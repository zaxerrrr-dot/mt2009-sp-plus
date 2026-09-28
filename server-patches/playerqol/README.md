# Wygody graczy (28 września)

Zmiany silnika opisane w `edits.json`, każda z własnym znacznikiem:

| Znacznik | Plik | Co robi |
|---|---|---|
| `MT2009_PLUS_GARBAGE_BATCH_V1` | `cmd_general.cpp` | Kosz sprawdza i usuwa do 24 stosów jedną komendą (`/garbage prepare_many`, `/garbage commit_many`); `hello` mówi dodatkowo `GarbageBinBatch 1`. |
| `MT2009_PLUS_PICKUP_FILTER_V1` | `char_item.cpp`, `cmd_general.cpp`, `cmd.cpp` | Filtr tego, co podnosi klawisz Z i pet zbierający drop: `/pickup_filter <wł> <rodzaje>` (13 rodzajów Auto Łowów), `/filtr` otwiera okno. |
| `MT2009_PLUS_ARRANGE_MERGE_V1` | `cmd_general.cpp` | `/inventory_arrange merge` – samo łączenie stosów, bez przestawiania. |
| `MT2009_PLUS_SHOP_SEARCH_PLUS_V1` | `ikarus_shop_manager.cpp` | Kategoria wyszukiwarki „MT2009 Plus”: Cory, szarfy według stopnia, alchemia antyczna, legendarna i mityczna. |
| `MT2009_PLUS_MOUNT_HORSE_SKILLS_V1` | `char_skill.cpp` | Umiejętności konne (np. Cięcie z Siodła) na moncie kostiumowym, który może walczyć. |
| `MT2009_PLUS_FLEA_FILL_V1` | `input_main.cpp` | Pakiet, którym okno Domu Towarowego prosi o katalog (`SEARCH_FILL_REQUEST`) – zakomentowany serwer rozłączał gracza przy otwarciu okna. |
| `MT2009_PLUS_COSTUME_HIDE_V1` | `item.cpp`, `cmd_general.cpp`, `cmd.cpp` | „Ukryj kostiumy”: `/kostiumy_ukryj <0|1>` – kostium zbroi i broni zostaje założony i daje bonusy, a wszyscy widzą zbroję i broń pod nim (kostium fryzury – domyślna fryzura postaci; szarfa bez zmian). Odpowiedź `CostumeHiddenAck <0|1>`. |
| `MT2009_PLUS_MOUNT_ON_EQUIP_V1` | `char_item.cpp` | Pieczęć wierzchowca założona przez gracza (klik w torbie albo przeciągnięcie na slot) od razu go dosiada, jak Ctrl+G z pieczęcią w torbie. Boty i logowanie bez zmian. |
| `MT2009_PLUS_DRAGON_ROAR_EFFECT_V1` | `char_skill.cpp` | Smoczy Skowyt rzucony na cel pokazuje efekt wybuchu przy celu (`paeryong.mse`, `_2`–`_4` według stopnia umiejętności). |
| `MT2009_PLUS_EVENT_CALENDAR_V1` | `cmd_general.cpp`, `cmd.cpp` | `/kalendarz` – harmonogram eventów z paneli dla okna kalendarza (F11), `CPlayerBotManager::SendEventCalendar`. |
| `MT2009_PLUS_COSTUME_SET_V1` | `item.cpp`, `char_affect.cpp` | Zestawy kostiumów z `locale/poland/costume_sets.txt` (`linux-port/docker/game/costume_sets.txt`): kostium i fryzura z jednej linii = +800 PŻ, +15 wartości ataku (affect 545, niezapisywany, liczony przy każdym założeniu). |
| `MT2009_PLUS_BATTLE_PASS_V1` | `char_battle.cpp`, `char.cpp`, `char_item.cpp`, `cmd_general.cpp`, `cmd.cpp` | Battle Pass (`playerbot_battlepass.h`): zabicia, statystyki gracza, próby ulepszenia (u kowala i zwojem), użycie przedmiotu i `/battlepass`. Misje w `player.battlepass_mission`, postęp w `player.battlepass_progress` (sezon = miesiąc), nagroda końcowa Kupon SM (50). Boty nie biorą udziału. |

- `Apply-PlayerQolPatch.ps1` – Windows (`tools/port/Apply-MT2009PlusEngine.ps1`);
- `apply_playerqol.py` – Linux/VPS; oba czytają ten sam `edits.json`.

Zmiana już nałożona (jest jej znacznik) jest pomijana; zmiana, której kodu nie
ma dokładnie raz, przerywa całość, zanim cokolwiek zostanie zapisane.
