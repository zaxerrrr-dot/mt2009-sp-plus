# Zegar innej misji – `q.set_clock_of` (`MT2009_PLUS_SPIRALA_CZASU_V2`)

Spirala Czasu (72347–72349, `spirala_czasu.quest`) skraca czas oczekiwania misji Biologa, stajennego i reliktów
w trakcie WŁASNEJ misji (użycie przedmiotu). Zegar w liście misji (z boku ekranu i w oknie misji) należy do
stanu TAMTEJ misji (`QuestState::_clock_name/_clock_value`, pakiet `QuestInfo`), a `q.set_clock` zmienia tylko
bieżącą – dotąd nowy czas było widać dopiero po rozmowie z NPC albo ponownym wejściu.

`q.set_clock_of(nazwa misji, nazwa zegara, sekundy)` – jak `q.set_title2` dla tytułu: zapisuje zegar w stanie
podanej misji i od razu wysyła klientowi aktualizację `QuestInfo` (flagi `QUEST_SEND_CLOCK_NAME | QUEST_SEND_CLOCK_VALUE`,
bez `ISBEGIN` – klient zmienia tylko zegar i odświeża okno). Wysyła tylko, gdy list tej misji jest u klienta
(`bStart`: `q.start`/`send_letter`, nie skasowany `q.done`) – aktualizacja nieznanego indeksu zrobiłaby u klienta
pustą misję. Zwraca `true`, gdy wysłano. Bez zmiany pakietów i exe.

| Znacznik | Plik | Co robi |
|---|---|---|
| `(decl)` | `questpc.h` | `PC::M2SetQuestClock` |
| `(clock)` | `questpc.cpp` | zapis zegara i wysyłka (podmiana `m_RunningQuestState` jak w `SetQuestTitle`) |
| `(lua)`, `(table)` | `questlua_quest.cpp` | `q.set_clock_of` |

qc: `q.set_clock_of` dopisane do listy funkcji w `linux-port/docker/game/Dockerfile`.

- `apply_spiralaclock.py` – Linux/VPS: `python3 apply_spiralaclock.py <game/src>`;
- `Apply-SpiralaClockPatch.ps1` – Windows; oba czytają ten sam `edits.json`.
