# Klient 2.0.20: wędka, filtr Auto Łowów, bilet Auto Łowów

Względem klienta 2.0.19 (`client-patches/client-2.0.19`):

- `root/game.py` – komenda serwera `AutoHuntOff` przekazuje powód
  (`item` = brak czasu z biletu „Auto Łowy (8h)”);
- `root/uiautohunt.py` – filtr podnoszenia ma osobno hełmy, tarcze,
  bransolety, buty, naszyjniki i kolczyki (bity 7–12), `/autohunt_loot`
  wysyła maskę zgrubną (siedem rodzajów, dla starszego serwera) i pełną;
  ustawienia w wersji 6 przenoszą stare „Zbroje”/„Ozdoby” na nowe
  przełączniki; komunikat o braku czasu Auto Łowów;
- `root/uitooltip.py` – opisy biletu Auto Łowów (31073) i Pierścienia
  Anty-Exp (40002) w podpowiedzi przedmiotu;
- `gamedata/item_proto` – wędki (27400–27590) wymagają 30 poziomu,
  31073 to „Auto Łowy (8h)”, 40002 „Pierścień Anty-Exp”. Reszta rekordów
  identyczna z item_proto klienta 2.0.19.

Pakowanie: podmienić trzy pliki w `root` klienta 2.0.19 i `gamedata/item_proto`
w `gamedata.data`/`gamedata.index` (nie całą paczkę gamedata: nasza ma
kostiumy i dodatkowe modele), przepakować.
