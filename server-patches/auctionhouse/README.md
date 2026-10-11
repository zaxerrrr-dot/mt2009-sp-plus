# auctionhouse – Dom Aukcyjny i „Liczba gier” w minigrach (Autor: Vekirion)

Znaczniki: `AH_V1 [Autor: Vekirion]`, `MT2009_PLUS_PLAY_COUNT_V1 [Autor: Vekirion]`,
nasze ograniczenie pamięci: `MT2009_PLUS_AUCTION_HOUSE_BOUND_V1`.

Łatka (`edits.json`, 10 zmian):
- `cmd.cpp` – komendy `/ah_search`, `/ah_names`, `/ah_bonus`, `/ah_buy`, `/ah_cart_add`, `/ah_cart_buy`,
  `/ah_bulk_quote`, `/ah_bulk_buy`, `/ah_cancel` (w `ENABLE_IKASHOP_RENEWAL`) oraz `/minigame_count`.
- `ikarus_shop_manager.cpp` – deklaracje i wywołania `AuctionHouse_OnBuyLockSent` / `AuctionHouse_OnBuyResult`
  (zlecenie zakupu Domu Aukcyjnego czeka na wynik zwykłego kupna Ikarusa).

Nowy plik silnika `auction_house.cpp` leży w nakładce `linux-port/overlays/playerbot/src/game/src/`
(kopiowanej do `game/src` jak pliki `playerbot_*`; Makefile kompiluje każdy `*.cpp`). Zmiany minigier są
w nakładce: `playerbot_rumi.h`, `playerbot_yutnori.h`, `playerbot_catchking.h`, `playerbot_wheel.h`.

- Linux/VPS: `python3 apply_auctionhouse.py <game/src>`; Windows: `Apply-AuctionHousePatch.ps1 -SourceDir <game/src>`
  (wołane z `tools/port/Apply-MT2009PlusEngine.ps1`). Po `flealimit` (kotwice w pliku już z nią).
- Włącznik: flaga `m2_flea_market_off` = 0 (jak dawny Dom Towarowy), tylko M1 (mapy 1, 21, 41).
