# Wygody graczy (28 września)

Zmiany silnika opisane w `edits.json`, każda z własnym znacznikiem:

| Znacznik | Plik | Co robi |
|---|---|---|
| `MT2009_PLUS_GARBAGE_BATCH_V1` | `cmd_general.cpp` | Kosz sprawdza i usuwa do 24 stosów jedną komendą (`/garbage prepare_many`, `/garbage commit_many`); `hello` mówi dodatkowo `GarbageBinBatch 1`. |
| `MT2009_PLUS_PICKUP_FILTER_V1` | `char_item.cpp`, `cmd_general.cpp`, `cmd.cpp` | Filtr tego, co podnosi klawisz Z i pet zbierający drop: `/pickup_filter <wł> <rodzaje>` (13 rodzajów Auto Łowów), `/filtr` otwiera okno. |
| `MT2009_PLUS_ARRANGE_MERGE_V1` | `cmd_general.cpp` | `/inventory_arrange merge` – samo łączenie stosów, bez przestawiania. |
| `MT2009_PLUS_SHOP_SEARCH_PLUS_V1` | `ikarus_shop_manager.cpp` | Kategoria wyszukiwarki „MT2009 Plus”: Cory, szarfy według stopnia, alchemia antyczna, legendarna i mityczna. |
| `MT2009_PLUS_MOUNT_HORSE_SKILLS_V1` | `char_skill.cpp` | Umiejętności konne (np. Cięcie z Siodła) na moncie kostiumowym, który może walczyć. |

- `Apply-PlayerQolPatch.ps1` – Windows (`tools/port/Apply-MT2009PlusEngine.ps1`);
- `apply_playerqol.py` – Linux/VPS; oba czytają ten sam `edits.json`.

Zmiana już nałożona (jest jej znacznik) jest pomijana; zmiana, której kodu nie
ma dokładnie raz, przerywa całość, zanim cokolwiek zostanie zapisane.
