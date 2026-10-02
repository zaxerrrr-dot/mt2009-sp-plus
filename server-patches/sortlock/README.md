# Ekwipunek: blokada sortowania (Alt + LPM)

Poprawka silnika `game/src/cmd_general.cpp` (`do_inventory_arrange`), znacznik
`MT2009_PLUS_INVENTORY_SORT_LOCK_V1`. Nakładana raz, przy przygotowaniu wydania
(`tools/port/Apply-MT2009PlusEngine.ps1`, po `playerqol`, na którego kodzie
„merge” się opiera); `Apply-SortLockPatch.ps1` i linuksowy bliźniak
`apply_sortlock.py` czytają ten sam `edits.json`.

## Co robi

Alt + lewy przycisk myszy na przedmiocie w plecaku (cztery strony ekwipunku)
blokuje go przed sortowaniem; drugie kliknięcie zdejmuje blokadę. Zablokowany
przedmiot ma małą złotą gwiazdkę w lewym górnym rogu pola i wiersz
„Zablokowany przy sortowaniu (Alt+LPM)” w opisie. Gdy pisze się na czacie
albo w szepcie, Alt + LPM wkleja link przedmiotu jak dotąd.

Oba przyciski porządkowania wysyłają zablokowane pola razem z prośbą:

- **Ułóż i scal** – `/inventory_arrange keep=<hex>`,
- **Tylko scal stosy** – `/inventory_arrange merge keep=<hex>`.

`keep=` to maska pól: jedna cyfra szesnastkowa na cztery pola, pierwsza cyfra
to pola 0–3, najniższy bit to najniższe pole (najwyżej 45 cyfr na 180 pól).
Bez zablokowanych pól klient wysyła polecenie jak wcześniej, bez `keep=`.

Serwer (`playerbot_arrange::InventoryArrangeCommand`, parser
`playerbot_arrange_rules::ParseArrangeWords` w
`linux-port/overlays/playerbot/.../playerbot_arrange*.{h,cpp}`):

- zablokowany przedmiot zostaje na swoim polu (jak aktywna auto-mikstura),
  reszta plecaka jest układana dookoła niego;
- zablokowany stos przy łączeniu stosów tylko **przyjmuje** sztuki tego samego
  przedmiotu (dostaje je jako pierwszy), nigdy nie oddaje swoich – nie znika
  i nie zmienia pola;
- zablokowane puste pole nie jest blokadą (może na nie trafić inny przedmiot);
- nieznane słowo, powtórzone słowo albo zła maska → `RESULT_BAD_REQUEST`
  (8), zanim cokolwiek się zmieni i bez liczenia 2 s przerwy.

## Gdzie są blokady

Po stronie klienta (`root/inventorysortlock.py`), osobno dla każdej postaci:
`autohunt/sortowanie/<nick>.cfg`, wiersze `pole=vnum`. Blokada trzyma się
przedmiotu, który stał na polu w chwili zablokowania:

- przedmiot przeniesiony ręcznie w całości na puste pole plecaka zabiera
  blokadę ze sobą; część odcięta ze stosu zostawia blokadę na starym polu;
- stos wlany w całości w stos tego samego przedmiotu przenosi blokadę na ten
  stos;
- inny przedmiot na polu (zużyty, sprzedany, wyrzucony, założony, oddany do
  magazynu – i na pole trafiło coś innego) kończy blokadę przy następnym
  odświeżeniu plecaka; puste pole kończy ją przy następnym sortowaniu;
- ulepszenie broni lub zbroi (vnum w tej samej dziesiątce) blokady nie zdejmuje.

Serwer bez tej poprawki odpowiada na `keep=` kodem 8; klient pisze wtedy, że
serwer nie obsługuje blokady sortowania. Stary klient z nowym serwerem działa
jak dotąd.

Zmiana już nałożona (jest jej znacznik) jest pomijana; zmiana, której kodu nie
ma dokładnie raz, przerywa całość, zanim cokolwiek zostanie zapisane.
