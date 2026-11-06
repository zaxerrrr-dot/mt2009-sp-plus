# logtrim – wiersze botów w bazie logów i zegary questów

Decyzje właściciela z 6.11.2026 (druga analiza botów, pkt 1 i 13). Logika liczników jest w nakładce
`linux-port/overlays/playerbot/src/game/src/playerbot_logtrim.cpp`; ta łatka dodaje tylko haki w silniku.
Edycje generuje `gen_edits.py` → `edits.json`.

**Nakładana jako ostatnia** (kotwice: silnik po wszystkich innych łatkach). Linux/VPS: `python3 apply_logtrim.py <game/src>`;
Windows: `Apply-LogTrimPatch.ps1` (`tools/port/Apply-MT2009PlusEngine.ps1`, na końcu). Edycja już nałożona jest pomijana;
edycja, której stary kod nie występuje dokładnie raz, zatrzymuje całość. Przy wdrożeniu dopisać `logtrim` na końcu listy
łatek (po `language`).

| Plik | Znacznik | Co |
|---|---|---|
| `log.cpp` | `MT2009_PLUS_BOT_LOG_TRIM_V1` | `CharLog(ch, …)`: `GET_GOLD` bota → licznik rdzenia, raz na godzinę jeden wiersz `log.log` (`who=0`, `how=GET_GOLD`, `what`=suma yang, `ip=playerbot`, `hint=BOTS_HOURLY picks=… bots=… ch=… port=…`), więc `SUM(what)` dalej liczy yang botów; `ItemSocketLog` (`SOCKET*`) i `ItemAttrLog` (`ATTR_FORCE`) bota → bez wiersza w `item_meta_log` |
| `questmanager.h/.cpp`, `questevent.cpp` | `MT2009_PLUS_QUEST_TIMER_RESCHEDULE_V1` | `server_timer` o nazwie i argumencie już zarejestrowanym przestawia zegar (stary anulowany, nowy zarejestrowany) zamiast `already registered server timer`; po obsłudze jednorazowego zegara wpis znika tylko wtedy, gdy to wciąż ten zegar |

Gracze: ich wiersze `GET_GOLD`, `SOCKET*`, `ATTR_FORCE` zostają jak były.

Dlaczego zegary: silnik czyścił wpis zegara dopiero **po** jego obsłudze. Quest, który w obsłudze prosił o następny tik
(`server_timer("x_tick", …)`), dostawał błąd, a nowy zegar i tak ruszał – bez wpisu, więc ani `clear_server_timer`, ani
koniec lochu (`CancelServerTimers`) nie mógł go zatrzymać. Każdy kolejny start etapu/piętra dokładał następny taki łańcuch.

## Przełączniki (flagi zdarzeń)

- `m2_bot_log_rows_on` = 1 – boty znów piszą wiersze jak dawniej (domyślnie 0 = przycięte; czytana co 30 s);
- `m2_quest_timer_legacy` = 1 – stara odmowa `already registered server timer`.

## Log

- `BOT_LOGTRIM: hour gold=… picks=… bots=… meta_socket_skipped=… meta_attr_skipped=… span_s=…` – raz na godzinę
  (przy następnym podniesieniu yang / zapisie bota po pełnej godzinie), razem z wierszem sumy;
- `BOT_LOGTRIM: switch rows_on=0|1` – zmiana flagi;
- `QUEST_TIMER: rescheduled own_handler=… while_waiting=… last=<nazwa>:<arg>` – co najwyżej raz na 10 min.

Licznik bieżącej godziny przepada przy zatrzymaniu rdzenia (najwyżej godzina yang botów mniej w sumie).
