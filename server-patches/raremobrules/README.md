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

- `MT2009_PLUS_DUNGEON_DROPS_NO_FADE_V1` (6 października, zgłoszenie do 2.24.0): to samo co w Wieży Demonów we
  wszystkich lochach panelu (`dungeon_info.txt`): Leże Smoka 208, Katakumby 216, Razador 351, Nemere 352, Biblioteka
  Wiedzy 363, Wzgórze Wukonga 364, Ruiny Skorpiona 365, Starożytna Dżungla 366 (i Wieża 66) oraz ich instancje
  (mapa * 10000 ...). Zabicie przez gracza losuje drop (`GetDropPct`, `iDeltaPercent` = 100) i yang
  (`char_battle.cpp`, `CHARACTER::RewardGold`) bez kary za różnicę poziomów. Wcześniej postać 75 poziomu w Razadorze
  (potwory 6001-6009 na 56-64 poziomie) losowała wszystkie tabele, także mikstury z dropu ogólnego, na 1-30%,
  a wiki dropu pokazuje szansę dla gracza na poziomie potwora. Funkcja `Mt2009PlusDungeonNoFade` (item_manager.cpp).
  Boty bez zmian.

- `MT2009_PLUS_RARE_DROP_SWITCHES_V1` (5 października): sześć wyłączników z edytora bazy danych panelu
  Seban (strona „Kupony SM, szarfy, Cor”, `dbeditor/raredrop.py`) – flagi świata w `player.quest`
  (dwPID 0, 1 = wyłączony, brak/0 = włączony): `m2_sm_boss_off`, `m2_sm_metin_off`, `m2_sash_boss_off`,
  `m2_sash_metin_off`, `m2_cor_boss_off`, `m2_cor_metin_off`. Wyłączają tylko źródła wbudowane:
  rzut na Kupon SM (80017, CONFIG `DRAGON_COIN_*_PERMILLE`), rzut na szarfę +0 i na Cor Draconis
  (z regułami tej poprawki), szarfę unikatową ze skrzyni bossa (`char_item.cpp`, przełącznik bossów)
  i wiersze tabel dropu z gry (`item_manager_read_tables.cpp` oznacza każdy wiersz grupy „drop”, której
  nazwa nie zaczyna się od `MT2009_panel_`; `item_manager.h`, `SDropItemGroupInfo::bBuiltin`). Grupa zapisana
  w panelu („Drop z potworów”) dropi dalej. Metin = `IsStone()`, reszta = boss. Gracze i boty tak samo.
  Podgląd dropu potwora i autopolowanie też; wiki dropu: `server-patches/dropwiki`.

- `MT2009_PLUS_SASH_CLOTH_V1` (6 października, właściciel): zamiast szarfy +0 z metinów i bossów wypada
  **Delikatne Sukno** (80019) – ten sam rzut co szarfa (boss 80%, metin 15%, reguły potworów wyżej: WuKong 15%,
  Kamień Wzgórza / Feniksy / Metin Ciemności w Bibliotece – nigdy; zabójca najwyżej 15 poziomów nad potworem;
  `m2_sash_off` i przełączniki `m2_sash_boss_off` / `m2_sash_metin_off`, w panelu „Delikatne Sukno (szarfy)”),
  gracze i boty tak samo (bot – do plecaka, przy pełnym przepada). Ilość wg poziomu **zabójcy**: 1–49 ×2,
  50–74 ×5, 75+ ×10. Log `[SUKNO_DROP]`. Podgląd dropu pokazuje sukno w ilości dla poziomu oglądającego,
  wiki dropu (`server-patches/dropwiki`) – dla zabójcy na poziomie potwora. 10 sukien + 80 000 Yang = Szarfa
  Władcy +0 (85001) u Uriela (okno „Wytwarzanie” 111). Szarfa unikatowa ze skrzyń bossów (`char_item.cpp`) bez zmian.
  Funkcje `Mt2009PlusSashClothCount`, `Mt2009PlusSashClothDrop` (item_manager.cpp).

Stosowanie: `Apply-RareMobRulesPatch.ps1 -SourceDir <game/src>` (Windows) albo
`python3 apply_raremobrules.py <game/src>` (Linux/VPS); zmiany w `edits.json`.
