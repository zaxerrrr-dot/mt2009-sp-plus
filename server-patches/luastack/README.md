# Miejsce na stosie Lua (1 października)

Zmiany silnika opisane w `edits.json`, każda z własnym znacznikiem
`MT2009_PLUS_LUA_STACK_V1`:

| Znacznik | Plik | Co robi |
|---|---|---|
| `MT2009_PLUS_LUA_STACK_V1 (special item group)` | `questlua_global.cpp` | `get_special_item_group(vnum)` przed wypisaniem grupy prosi Lua o miejsce na stosie (`lua_checkstack`) na wszystkie jej wartości (dwie na linię). Funkcja w C ma zagwarantowane tylko 20 wolnych miejsc (`LUA_MINSTACK`), więc grupa dłuższa niż 10 linii pisała za końcem stosu korutyny i niszczyła pamięć Lua. Złoty Łup Królewski (21 linii) przy stole Złap Króla (20506) zabijał rdzeń od razu (`luaV_execute`), a zniszczona pamięć kładła go chwilę później w innych miejscach (`lua_rawget` przy logowaniu, `target_event`). |
| `MT2009_PLUS_LUA_STACK_V1 (quest reward)` | `questlua_global.cpp` | To samo dla `get_quest_reward_data` (do 39 wartości). |
| `MT2009_PLUS_LUA_STACK_V1 (sig items)` | `questlua_pc.cpp` | To samo dla `pc.get_sig_items` (jedna wartość na przedmiot, do całego ekwipunku). |

## Pliki

- `edits.json` – zmiany (plik, znacznik, stary i nowy kod);
- `Apply-LuaStackPatch.ps1` – Windows (`tools/port/Apply-MT2009PlusEngine.ps1`);
- `apply_luastack.py` – Linux/VPS; oba czytają ten sam `edits.json`.

Zmiana już nałożona (jest jej znacznik) jest pomijana; zmiana, której kodu nie
ma dokładnie raz, przerywa całość, zanim cokolwiek zostanie zapisane.
