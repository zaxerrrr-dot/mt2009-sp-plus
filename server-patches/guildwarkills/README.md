# Wojna gildii liczona w zabójstwach (2 października)

Zmiana silnika opisana w `edits.json`, ze znacznikiem `MT2009_PLUS_GUILD_WAR_KILLS_V1`:

| Znacznik | Plik | Co robi |
|---|---|---|
| `MT2009_PLUS_GUILD_WAR_KILLS_V1` | `guild_manager.cpp` | `CGuildManager::Kill`: wojna polowa (`GUILD_WAR_TYPE_FIELD`) dostaje za każde zabicie jeden punkt. Dotąd do wyniku dodawał się poziom zabitego, więc wynik nie był liczbą zabójstw. |

Resztę robią boty (`playerbot_guild_war.h`, ten sam znacznik): wojna z gildią botów po
jednej ze stron (botów z botami i gracza z botami) kończy się, gdy któraś gildia pierwsza
zabije `WAR_KILLS` wrogów (panel, strona AI; domyślnie 100, 0 = tylko czas), a po upływie
czasu wygrywa ta z większą liczbą zabójstw, jak dotąd. Każdy rdzeń wysyła członkom obu
gildii komendę klienta `guild_war_kills <gildia> <wróg> <zabójstwa>`, a tablica wojny w
kliencie (`guildwarkills.py`, `uiguild.py`) pokazuje cel, ile zabójstw brakuje każdej
stronie i kto prowadzi. Wojna areny między gildiami graczy zostaje bez zmian.

## Pliki

- `edits.json` – zmiany (plik, znacznik, stary i nowy kod);
- `Apply-GuildWarKillsPatch.ps1` – Windows (`tools/port/Apply-MT2009PlusEngine.ps1`);
- `apply_guildwarkills.py` – Linux/VPS; oba czytają ten sam `edits.json`.

Zmiana już nałożona (jest jej znacznik) jest pomijana; zmiana, której kodu nie
ma dokładnie raz, przerywa całość, zanim cokolwiek zostanie zapisane.
