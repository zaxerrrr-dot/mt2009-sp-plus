# mlodzi – Bronie dla Młodych Bohaterów

`MT2009_PLUS_MLODZI_BOHATEROWIE_V1` (22.10.2026, polecenie właściciela). Wiki PL: „Bronie dla Młodych Bohaterów”.
Pełny opis systemu: `cache/yohara/bronie-mlodych-bohaterow.md` (dla prowadzącego) – tu tylko część silnika.

## Co robi łatka (`edits.json`, `gen_edits.py`)

| plik | znacznik | po co |
|---|---|---|
| `questlua.cpp` | `(lua)` | rejestruje moduł questów `mlodzi.*` (`playerbot_mlodzi.cpp`) |
| `char_item.cpp` | `(use on)` | na broń 21900–21975 nie da się niczego użyć: zmiana/dodanie bonusu (1–5 i 6/7), kamienie duszy, czyszczenie gniazd, zwoje ulepszeń, skórki szarf, anulacja transmutacji. Zakładanie broni/zbroi/kostiumu nie jest blokowane |
| `item_attribute.cpp` | `(change)`, `(add)`, `(add one)`, `(change rare)`, `(change rare 2)`, `(add rare)`, `(add rare 2)` | własne funkcje bonusów przedmiotu nic nie robią dla tych broni – zatrzymuje to każdą drogę (switchbot, Seon-Hae, `item.*` questów, boty) |
| `char.cpp` | `(sash decl)`, `(sash)` | szarfa nie wchłania bonusów takiej broni |

Poza łatką (pliki overlay, ten sam znacznik): `playerbot_changelook.cpp` (transmutacja: broń ani nie daje, ani nie
bierze wyglądu), `playerbot_switchbot.cpp` (nie wchodzi do slotu), `playerbot_seonhae.h` (Seon-Hae jej nie przyjmuje).

Czego łatka nie robi, bo robią to dane (`mlodzi_bohaterowie.sql`): handel, wyrzucanie, sprzedaż, sklep offline i
magazyn – antyflagi; ulepszanie u kowala i zwojem – `refined_vnum = 0`; kamienie duszy – brak gniazd (`socket_pct = 0`);
losowe bonusy przy tworzeniu – `magic_pct = 0`; znikanie po 15 dniach także założonej – `LIMIT_REAL_TIME 1296000`
(silnik: `real_time_expire_event` usuwa przedmiot, także z ekwipunku).

## Kolejność

Ostatnia (po `g0bind`): kotwice na liniach `talizmanwoli` (funkcje bonusów), `shipdefense` (rejestracja modułu),
`switchbot`. Linux: `python3 server-patches/mlodzi/apply_mlodzi.py <game/src>`; Windows:
`tools/port/Apply-MT2009PlusEngine.ps1` (zarejestrowana na końcu). Ponowne uruchomienie niczego nie zmienia.
