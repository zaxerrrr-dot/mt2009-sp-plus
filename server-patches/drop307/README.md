# drop307 – drop z listy właściciela z 03.11.2026 (Yohara 3.x, sekcja C)

Znaczniki: `MT2009_PLUS_DROP307_V1`, `MT2009_PLUS_CATACOMB_YANG_HALF_V1`, `MT2009_PLUS_MISSION_NO_DROP_V1`.

- `char_battle.cpp`:
  - **Katakumby Diabła** (mapa 216 i jej instancje): potwór poniżej rangi bossa daje połowę yang, gdy respawn potworów
    z panelu („Respawny”) jest powyżej standardu – szybszy czas (`fastMobSpawn216`, inaczej `fastMobSpawn`: 10–99%)
    albo więcej potworów na linię (`m2_mob_count` > 100%). Bossowie i Metiny bez zmian; przy standardowym respawnie
    nic się nie zmienia.
  - **Król Bao (misja)** (6692): bez dropu i bez yang (pl-wiki: brak dropu, Champion-EXP 1) –
    `Mt2009PlusMissionNoDrop(race)`. Zabójstwo liczy się dalej (questy, karty, Battle Pass), exp bez zmian.
- `item_manager.cpp`:
  - Król Bao (misja): `CreateDropItem` nic nie daje (także dodatki świata – Kupon SM, Cor Draconis, Sukno, talizman),
    podgląd dropu (`SendMobDropPreview`) pusty, wiki dropu bez wierszy.
  - **Kupon SM z bossów map championa 10%** (było 5%): bossowie map Sung Ma (pola, nie lochy) – 6691, 6698, 6699
    (374), 6705/6706/6716/6717 (373, 377), 6723/6724/6730/6731 (376, 377), 6789 (393), 6797 (394) – rzucają kupon
    z podwójnym promilem bossa (CONFIG `DRAGON_COIN_BOSS_PERMILLE`, domyślnie 50 ‰ → 100 ‰). Wiki dropu pokazuje to samo.
    Przełącznik panelu `m2_sm_boss_off` działa jak dotąd.

Reszta zmian tej sekcji jest w danych: `linux-port/docker/game/drop307/` (krok Dockerfile „drop 3.0.7”),
`linux-port/docker/mariadb/playerbot/drop307.sql` (apply.sh), klient
`client-patches/client-2.0.30/tools/yitems307/patch_yitems307_client.py`.

Kolejność: na końcu listy łatek, po `kupon100` (kotwiczy na liniach rzutu kuponu i na `WorldBossNoDrop`).

Linux/VPS: `python3 apply_drop307.py <game/src>` (bez bliźniaka PowerShell).
