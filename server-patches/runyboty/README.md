# runyboty – boty i Runy Wykuwania: komenda `/bot_runa`

`MT2009_PLUS_BOT_RUNES_V1` (decyzja właściciela, 5.11.2026: boty mają znać system run). Cała logika jest w nakładce
`linux-port/overlays/playerbot/src/game/src/playerbot_runes.h` (opis w nagłówku pliku); ta łatka dodaje tylko komendę GM.

**Nakładana po `remotecall`** (kotwice: blok `ACMD(do_remote_call)` i jego wiersz tabeli w `cmd.cpp`). Linux/VPS:
`python3 apply_runyboty.py <game/src>`; Windows: `Apply-RunyBotyPatch.ps1` (`tools/port/Apply-MT2009PlusEngine.ps1`, po
remote call). Edycja już nałożona jest pomijana; edycja, której stary kod nie występuje dokładnie raz, zatrzymuje całość.
Przy wdrożeniu dopisać `runyboty` na końcu listy łatek (po `remotecall`).

| Plik | Co |
|---|---|
| `cmd.cpp` | `ACMD(do_bot_runa)` → `PlayerBotRuneCommand` (playerbot_runes.h), wiersz tabeli `bot_runa`, `GM_HIGH_WIZARD` |

## Komenda (boty tego rdzenia)

- `/bot_runa` – przełączniki i spis (boty z runami, runy wg gwiazdek, użycia, ulepszenia, wymiany, nagrody, zakupy);
- `/bot_runa daj <bot|pid> <runa> [ile]` – jednemu botowi;
- `/bot_runa wszystkim <runa> [ile] [lv_min] [lv_max] [imperium 1-3, 0 – wszystkie] [limit, 0 – bez]`;
- `<runa>`: vnum 79605–79659, `<rodzaj>:<1-5>` (pasy bron zbroja pozostale akcesoria ksiegi zestbron zesthelm
  zestzbroja rekawice zwierzaki) albo `auto:<1-5>` – rodzaj, którego bot sam używa (twórca pasów – Pasów, bot 66+ –
  Zbroi, inny – Poz. Prz.). Komenda daje zawsze (niezależnie od flagi nagród).

Flagi zdarzeń: `m2_bot_runes_off` (wyłącza wszystko poza trzymaniem run), `m2_bot_rune_rewards_on` (domyślnie 0 –
`Mt2009PlayerBotRuneReward` z wyzwań nic nie daje, dopóki nie 1), `m2_bot_rune_exchange_on` (domyślnie 0 – wymiana botów
u Yu-Hwana wyłączona; tabela: `playerbot_rune_exchange.txt` w katalogu rdzenia albo wartości domyślne z nagłówka).
