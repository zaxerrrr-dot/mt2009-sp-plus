# Cor Draconis i szarfa według potwora

Poprawka silnika (`game/src/item_manager.cpp`), nakładana po `metindrops`.
Znacznik: `MT2009_PLUS_RARE_MOB_RULES_V1`. Arkusz dropu od właściciela, 1 października 2026.

- Tabela `Mt2009PlusRareMobRuleFor`: potwór (i opcjonalnie mapa) -> liczba i szansa Cor
  Draconis, szansa szarfy +0 (0 = brak). Pozostałe potwory bez zmian (Metin 20% / 15%,
  boss 80% / 80%).
  - 9701 Kamień Wzgórza, 9702 Jajo Feniksa, 9684 Płomienny Feniks: bez Cor i szarf.
  - 9682 WuKong: 5 Cor na 15%, szarfa na 15%.
  - 8006 Metin Ciemności tylko w Bibliotece Wiedzy (instancje mapy 363): bez Cor i szarf.
- Metin Ciemności w Bibliotece bierze grupę dropu pseudo-potwora 98006
  (`linux-port/docker/game/mob_drop_item.dropedit.append.txt`): bez złomu, Pigułki Krwi
  i Księgi Zapomnienia. Na mapach świata 8006 bez zmian. Podgląd dropu w grze pokazuje
  dla niego nadal listę światową.

Stosowanie: `Apply-RareMobRulesPatch.ps1 -SourceDir <game/src>` (Windows) albo
`python3 apply_raremobrules.py <game/src>` (Linux/VPS); zmiany w `edits.json`.
