# Scal i uporządkuj ekwipunek

Przycisk automatycznego stackowania w ekwipunku korzysta z
`root/inventoryarrange.py`. Moduł wysyła do serwera jedno polecenie
`/inventory_arrange`, zamiast setek pojedynczych przeniesień przedmiotów.

Serwer wykonuje scalanie i sortowanie, a następnie zwraca wynik do klienta.
Brak tego pliku powodował błąd `No module named inventoryarrange` po kliknięciu
przycisku, mimo że serwer był gotowy do obsługi tej funkcji.

## Instalacja

1. Rozpakuj pakiet `root` klienta.
2. Skopiuj `root/inventoryarrange.py` z tego katalogu do rozpakowanego `root`.
3. Upewnij się, że `game.py` przekazuje `InventoryArrangeResult` do
   `inventoryarrange.OnResult`.
4. Spakuj ponownie `root.data` i `root.index`.
