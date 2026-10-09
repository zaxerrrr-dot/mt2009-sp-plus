# Metiny osobno od bossów w respawnach – `MT2009_PLUS_REGEN_METIN_SPLIT_V1`

## Co daje

Panele (zaawansowany: Serwer → Respawny, klasyczny: /rates) mają osobne ustawienia **czasu odrodzenia** i **liczby**
dla Metinów, bossów i zwykłych potworów. Dotąd Metiny i bossowie miały jedno wspólne ustawienie.

## Jak

- `regen.h`: linia respawnu ma pole `is_stone` – w linii jest kamień Metin (`CHAR_TYPE_STONE`).
- `regen.cpp`:
  - `read_line` ustawia `is_stone` obok dotychczasowego `is_boss_or_stone`;
  - `regen_event` (czas): linia Metina czyta `fastMetinSpawn<mapa>`, a gdy go nie ma – `fastMetinSpawn`;
    linia bossa jak dotąd `fastBossSpawn<mapa>` / `fastBossSpawn`;
  - `regen_target_count` (liczba): Metin – `m2_metin_count`, boss – `m2_boss_count`, reszta – `m2_mob_count`;
  - limit Metinów wielkanocnych (`EasterMetinCap`) liczy z ustawień Metinów.
- Migracja (`linux-port/docker/mariadb/playerbot/regen_metin_split.sql`, raz – znacznik `m2_regen_metin_split`):
  dotychczasowe wiersze `fastBossSpawn%` i `m2_boss_count` kopiowane do `fastMetinSpawn%` i `m2_metin_count`,
  więc świat odradza się jak dotąd, dopóki operator czegoś nie zmieni.
- `web_admin.quest`: `REGEN` i `REGEN_COUNT` przyjmują `metin,boss,mob` (oraz stare `boss,mob` – wtedy Metiny i bossowie
  dostają tę samą wartość).

`Apply-RegenMetinPatch.ps1` – Windows (`tools/port/Apply-MT2009PlusEngine.ps1`); `apply_regenmetin.py <game/src>` – Linux/VPS;
oba czytają ten sam `edits.json`.

## Sprawdzenie

Panel zaawansowany → Respawny: Metiny ×4 i czas 10%, bossowie bez zmian → na mapie przybywa Metinów, bossów nie.
Wartości widać w panelu (flagi `fastMetinSpawn`, `m2_metin_count` w `player.quest`, `dwPID=0`).
