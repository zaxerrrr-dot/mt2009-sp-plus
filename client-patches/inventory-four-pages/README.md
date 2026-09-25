# Liczenie przedmiotów na czterech stronach ekwipunku

Klient miał w `root/utils.py` wpisane na stałe dwie strony ekwipunku.
Powodowało to, że okno ulepszania oraz inne interfejsy korzystające z
`CountItemCountInInventory()` nie widziały materiałów umieszczonych na stronie
3. lub 4.

`client-utils-inventory-count.patch` wylicza liczbę zwykłych stron z
`player.INVENTORY_PAGE_COUNT`. Ostatnia strona jest przeznaczona na ekwipunek
konia i zostaje doliczona tylko wtedy, gdy klient udostępnia ją graczowi.
Zachowuje to dotychczasowe zachowanie magazynu konia i usuwa stałą wartość `2`.

## Zakres

Poprawka obejmuje wszystkie klientowe okna używające wspólnej funkcji, między
innymi podgląd materiałów u kowala, crafting, sklep specjalny i ekwipunek konia.
Serwer już sprawdza zwykłe sloty 0–179 przez `GetInventoryMaxCount()`, dlatego
nie wymaga zmiany.

## Instalacja

1. Rozpakuj klientowy pack `root`.
2. Zastosuj patch względem katalogu zawierającego folder `root`.
3. Spakuj ponownie `root.data` i `root.index`.

## Test

1. Umieść wymagany materiał osobno na każdej ze stron 1–4.
2. Otwórz okno ulepszania i sprawdź poprawny licznik bez przelogowania.
3. Przenieś materiał między stronami i ponownie otwórz okno.
4. Wykonaj ulepszenie oraz sprawdź licznik materiałów w craftingu.
5. Przywołaj konia i sprawdź przedmiot znajdujący się w jego ekwipunku.
