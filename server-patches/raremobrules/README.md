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

- `MT2009_PLUS_DT_DROPS_V1` (5 października): w Wieży Demonów (mapa 66 i jej instancje 660000-669999)
  gracz dostaje drop bez kary za różnicę poziomów (`GetDropPct`, `iDeltaPercent` = 100). Wcześniej
  postać 75 poziomu biła demony 1001-1004 (57-60) i Metiny 8015-8017 na 1% tabel: ulepszacze
  30015/30087/30016/30086 i Pamiątka po Demonie Biologa (0,315% na zabicie) praktycznie nie
  wypadały (1 na ~31 700 zabić). Boty bez zmian (stara kara). Cor/szarfy/księgi bez zmian.
  Dane: `linux-port/docker/game/mob_drop_item.dtdrops.append.txt` (Brutalne demony 1061-1071).

Stosowanie: `Apply-RareMobRulesPatch.ps1 -SourceDir <game/src>` (Windows) albo
`python3 apply_raremobrules.py <game/src>` (Linux/VPS); zmiany w `edits.json`.
