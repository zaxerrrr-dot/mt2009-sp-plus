# szklohandlu – Szkło Handlu: Dom Aukcyjny z każdego miejsca

Znacznik: `MT2009_PLUS_SZKLO_HANDLU_V1` (właściciel, 24.10.2026, runda 5 sklepu V3: „po kliknięciu szkła handlu w grze
otwiera się zdalnie dom aukcyjny”).

- `ikarus_shop_manager.cpp` `IsFleaMarketMap`: gdy postać ma w ekwipunku Szkło Handlu (72802, przedmiot z czasem
  rzeczywistym – w drugim ItemShopie 7 / 15 / 30 dni za 39 / 75 / 135 SM), Dom Aukcyjny działa na każdej mapie
  (wszystkie komendy `/ah_*` pytają tę funkcję). Bez szkła – jak dotąd tylko M1 (mapy 1, 21, 41).
- Użycie szkła (quest `ishop_v3_przedmioty`) wysyła klientowi `FleaMarketOpen` – okno Domu Aukcyjnego.
  Włącznik świata bez zmian (`m2_flea_market_off`).

Linux/VPS: `python3 apply_szklohandlu.py <game/src>`; Windows: `Apply-SzkloHandluPatch.ps1 -SourceDir <game/src>`
(wołane na końcu `tools/port/Apply-MT2009PlusEngine.ps1`).
