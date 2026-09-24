# Ikony kostiumów i petów dla Seban Panelu

Seban Panel (7790) pokazuje ikonę przedmiotu z
`linux-port/docker/seban-panel/static/icons/<plik>.png`, a numer przedmiotu
zamienia na nazwę pliku przez `static/item_icons.json` (`"vnum": "plik.png"`;
bez wpisu panel próbuje jeszcze vnumu zaokrąglonego w dół do dziesiątek).
Ikon nie ma w Git, bo pochodzą z klienta gry. Trafiają do graczy w paczce
serwera, z pełnego folderu serwera.

`missing-vnums.txt` to 1675 kostiumów, fryzur, nakładek, szarf, mountów
i petów (`item_proto.type` 28 i 37), dla których panel nie ma ikony. To
głównie przedmioty z paczki GF26. Stan z 24 września 2026.

## Do zrobienia po stronie klienta

1. Dla każdego vnumu z listy weź jego ikonę z klienta: ścieżkę ikony
   z `item_list.txt` (pack `gamedata`), plik z packa `icon`.
2. Zapisz ją jako PNG 32×32, 32×64 albo 32×96 (jak w kliencie) z przezroczystością.
   Nazwa pliku: vnum z zerami do 5 cyfr, np. `40122.png`, `53221.png`.
   Kilka vnumów z tą samą ikoną może dostać ten sam plik.
3. Oddaj folder PNG i plik `icons-map.json` w formie `{"40122": "40122.png", ...}`,
   zawierający tylko vnumy z listy, które mają ikonę.
4. Vnumy bez ikony w kliencie wypisz w `icons-not-found.txt`.
