# jadeit – Żyły Jadeitu (Yohara)

`MT2009_PLUS_JADE_VEINS_V1` (14.10.2026, decyzja właściciela: mapy Yohary „wszystko wg wiki”, w tym rudy).

Wiki („Żyła Jadeitu Słońca/Nocy/Dymu/Mgły”): żyły stoją losowo na Dongan, Seoganland, Namgan, Przełęczy Yilad
i w Wąwozie Północnego Wiatru; wydobywa się z nich kilofem (30. poziom postaci) **Rudę Jadeitu**, a 100 sztuk rudy
przetapia się w **Jadeit** (materiał biżuterii z jadeitu).

| żyła | ruda | jadeit |
|---|---|---|
| 30310 Żyła Jadeitu Słońca | 50641 Ruda Jadeitu Słońca | 50661 Jadeit Słońca |
| 30311 Żyła Jadeitu Nocy | 50642 Ruda Jadeitu Nocy | 50662 Jadeit Nocy |
| 30312 Żyła Jadeitu Dymu | 50643 Ruda Jadeitu Dymu | 50663 Jadeit Dymu |
| 30313 Żyła Jadeitu Mgły | 50644 Ruda Jadeitu Mgły | 50664 Jadeit Mgły |

- Silnik: tabela rud `mining.cpp` (`MAX_ORE` 19 → 23, cztery wiersze Owsapa v6.2.6) – `CHARACTER::mining`,
  `IsVeinOfOre` (żyła sama znika po 7–15 min, `regen.txt` mapy ją odnawia) i `OreRefine` znają żyły.
- Kliknięcie żyły: quest `yohara_mapy2` (`pc.mining()`, jak `mining.quest` dla starych żył).
- Przetop: okno wytwarzania alchemików gildii 20060–20072 (jak MT2009_PLUS_JEWELS75_V1): przepisy
  `world.crafting_proto` 50661–50664 (100 rudy, 60 000 Yang, 60%; `yohara_items2.sql`), lista – krok Dockerfile
  „Yohara: Seoganland, Namgan, …”.
- Przedmioty i wiersze mob_proto: `tools/yohara_items/gen_yitems2.py`, `tools/yohara_maps/gen_ymaps2.py`.

Linux/VPS: `python3 apply_jadeit.py <game/src>`; Windows: `Apply-JadeitPatch.ps1 -SourceDir <game/src>` (wołane przez
`tools/port/Apply-MT2009PlusEngine.ps1`). Plik silnika: `mining.cpp` (lista `launcher/server-update-files.mod.txt`).
