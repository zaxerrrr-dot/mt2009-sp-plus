# ladaview – okno straganu ograniczone do jego stron

`MT2009_PLUS_BOT_LADA_VIEW_V1` (8.11.2026, właściciel: „Nie limituj pozycji na bota”). Lada bota
(`linux-port/overlays/playerbot/src/game/src/playerbot_lada.h`) nie ma już limitu linii, więc rdzeń gry – nie klient –
pilnuje, żeby żaden pakiet do klienta gracza nie niósł wszystkich linii sklepu. Logika i liczniki są w nakładce
`ikashop_lada_view.h` (jak `ikashop_qol.h`); ta łatka dodaje tylko haki w silniku. Edycje generuje `gen_edits.py` → `edits.json`
(sprawdza też, że każda kotwica jest w drzewie dokładnie raz).

**Nakładana jako ostatnia** (kotwice: silnik po wszystkich innych łatkach, m.in. `shopqol`, `saletax`, nazwa właściciela).
Linux/VPS: `python3 apply_ladaview.py <game/src>`; Windows: `Apply-LadaViewPatch.ps1` (`tools/port/Apply-MT2009PlusEngine.ps1`,
na końcu). Przy wdrożeniu dopisać `ladaview` na końcu listy łatek. Bez zmian pakietów, bazy i klienta.

| Plik | Znacznik | Co |
|---|---|---|
| `ikarus_shop_manager.cpp` | `(include)` | `ikashop_lada_view.h` |
| `ikarus_shop_manager.cpp` | `(open)`, `(open size)`, `(open count)`, `(open lines)` | okno straganu (`SUBHEADER_GC_SHOP_OPEN`, otwarcie i każde odświeżenie): tylko linie stron okna – `pos < 320` (4 strony × 80), najwyżej 320 linii; nic dla deskryptora bota |
| `ikarus_shop_manager.cpp` | `(owner)`, `(owner count)`, `(owner lines)` | okno właściciela (`SUBHEADER_GC_SHOP_OPEN_OWNER`): to samo |
| `ikarus_shop_manager.cpp` | `(safebox)`, `(safebox lines)` | skrytka sklepu (`SUBHEADER_GC_SHOP_SAFEBOX_REFRESH`): najwyżej 4000 przedmiotów; nic dla bota |
| `ikarus_shop.cpp` | `(include)`, `(add)` | linia dodana poza strony (lada, `pos ≥ 320`) nie odświeża okien gości ani właściciela |

Rozmiary (g++ -m32, struktury silnika): `TShopItem` 75 B, `TShopPlayerItem` 67 B, `TSearchResultInfo` 113 B; bufor odbioru
klienta = max(ustawiony, 600 KB). Okno straganu: najwyżej 86 + 320 × 75 = 24 086 B; skrytka: najwyżej ~268 KB. Bez tej
łatki już 8190 linii jednej lady dawało pakiet, którego klient nie przeczyta w całości. Wyszukiwarki były ograniczone
wcześniej: Dom Towarowy 6000 wyników po 100 w pakiecie (11 300 B), wyszukiwarka filtrów 2500 w jednym pakiecie
(282 500 B), szukanie straganów 400 sklepów. Linie lady (`pos ≥ 320`) gracz znajduje i kupuje przez wyszukiwarki.

Gracze: ich sklepy mają najwyżej 2 strony (160 pól), więc ich okna nic nie tracą.
