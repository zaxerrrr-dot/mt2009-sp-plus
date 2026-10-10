# flealimit – ograniczona lista wyników wyszukiwarki Domu Towarowego

`MT2009_PLUS_FLEA_MARKET_BOUND_V1` (10.10.2026). Wyszukiwarka sklepów (`CShopManager::RecvShopSearchFillRequestClientPacket`,
`ikarus_shop_manager.cpp`) zbierała do pamięci wszystkie pasujące oferty świata, a dopiero potem przycinała je do 6000.
Szukanie samymi filtrami (bez nazwy) brało ~230 tys. ofert i 32-bitowy rdzeń (~3,3 GB) przerywał pracę (`std::bad_alloc`
→ abort). Teraz lista ma najwyżej 2×6000 pozycji: po przekroczeniu zostaje 6000 najlepszych w wybranym porządku
(cena rosnąco / malejąco / za sztukę) – wynik dla gracza jest ten sam.

- Linux/VPS: `python3 apply_flealimit.py <game/src>`; Windows: `Apply-FleaLimitPatch.ps1 -SourceDir <game/src>`
  (wołane przez `tools/port/Apply-MT2009PlusEngine.ps1`).
