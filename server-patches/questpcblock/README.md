# Blok innej postaci bez bieżącej postaci (21 października)

`q.begin_other_pc_block(pid)` w zegarze serwera (`server_timer`, np. takty lochów) nic nie robił:
`CQuestManager::ServerTimer` zeruje bieżącą postać, a `BeginOtherPCBlock` bez niej pisał tylko
syserr „BeginOtherPCBlock: NULL?” i wracał. Każdy quest, który w zegarze przechodzi po graczach,
po cichu pomijał ich wszystkich (Wieża Sung Mahi: gałęzie z ziemi 3. etapu i komunikaty klątwy misji 7;
Głębie Północnego Wiatru: kolce lodu i Śmiertelny Chłód; Świątynia Węży: atak powierzchniowy).

Zmiany silnika w `edits.json`, każda ze znacznikiem `MT2009_PLUS_QUEST_PCBLOCK_V1`:

| Znacznik | Plik | Co robi |
|---|---|---|
| `(block)` | `questmanager.cpp` | `BeginOtherPCBlock` działa też bez bieżącej postaci: zapamiętuje postać (w zegarze – brak), PC, wybrany loch (`d.select`), NPC i członka grupy, wybiera gracza (jego PC, jego postać; wybrany loch zostaje) i daje mu nazwę bieżącego questa (pc.getqf/setqf w bloku piszą flagi questa, który blok otworzył). `EndOtherPCBlock` oddaje dokładnie to, co blok zastał (w zegarze znów brak postaci) i graczowi jego własną nazwę questa. Gracz offline – blok nikogo nie wybiera (pc.get_player_id() zostaje 0 w zegarze), więc zwykłe sprawdzenie questów `if pc.get_player_id() == pid` go pomija. Gdy wywołujący zniknął w trakcie bloku, zostaje PC serwera bez postaci – nigdy zwolniony wskaźnik. |
| `(reset)`, `(timer)` | `questmanager.cpp` | Blok zostawiony otwarty przez błąd questa (bez `end_other_pc_block`) jest zamykany na początku następnego zegara serwera (dotąd blokował `wait`/`select` na stałe). |
| `(state)`, `(decl)` | `questmanager.h` | Stan otwartych bloków; `BeginOtherPCBlock` zwraca `bool`. |
| `(quest name)` | `questpc.h` | `PC::M2SetCurrentQuestName`. |
| `(lua)` | `questlua_quest.cpp` | `q.begin_other_pc_block(pid)` zwraca `true`, gdy gracz jest online i wybrany (stare wywołania wynik pomijają). |

W zdarzeniach z postacią (rozmowa, zabicie, timer gracza) zachowanie jest jak dotąd.

## Pliki

- `edits.json` – zmiany (plik, znacznik, stary i nowy kod);
- `Apply-QuestPcBlockPatch.ps1` – Windows (`tools/port/Apply-MT2009PlusEngine.ps1`);
- `apply_questpcblock.py` – Linux/VPS; oba czytają ten sam `edits.json`.

Zmiana już nałożona (jest jej znacznik) jest pomijana; zmiana, której kodu nie
ma dokładnie raz, przerywa całość, zanim cokolwiek zostanie zapisane.
