# Towarzysz i przyciski paska z klienta Tieru

Ten katalog przechowuje selektywny port funkcji z klienta Tieru do
MT2009 Plus. Pełne paczki Tieru nie są podmieniane, dzięki czemu pozostają
nasze cztery strony ekwipunku, COOP, Auto Łowy, ItemShop i pozostałe poprawki.

## Zawartość

- `root/uisidekick.py` — okno Towarzysza pod klawiszem **P**;
- `root/uisidekickinventory.py` — ekwipunek i umiejętności Towarzysza;
- `root/sidekickskilltip.py` — opisy umiejętności Towarzysza;
- `root/playerbot_ui/*.tga` — trzy stany przycisku Towarzysza i Auto Łowów;
- `client-sidekick-autohunt.patch` — integracja okna w `game.py`, przycisków
  w pasku oraz poprawka Auto Łowów po wskrzeszeniu.

Okno pokazuje poziom, HP, PE, miejsce, wykonywaną czynność oraz ekwipunek
Towarzysza. Obsługuje przywołanie, oczekiwanie, wolną rękę, zakupy, raport,
odprawienie, sposób walki, podnoszenie, ochronę i buffy. Przyciski
**Ekwipunek** i **Umiejętności** otwierają dodatkowe okna; przedmiot można
przeciągnąć z ekwipunku Towarzysza do własnego plecaka.

Auto Łowy podczas oczekiwania na wymagany poziom HP po wskrzeszeniu rzucają
wyłącznie bezpieczne buffy. Nie używają wtedy umiejętności atakujących.

## Wymagania serwera

Serwer musi obsługiwać komendę `/towarzysz` i odpowiedzi `SidekickInfo`,
`SidekickNames`, `SidekickGear` oraz `SidekickWindow`. Brak obsługi serwerowej
nie powoduje awarii klienta; okno pozostaje w stanie oczekiwania na odpowiedź.

## Instalacja

1. Rozpakuj klientowy pack `root`.
2. Skopiuj zawartość katalogu `root` z tego patcha do rozpakowanego `root`.
3. Zastosuj `client-sidekick-autohunt.patch` względem katalogu nadrzędnego.
4. Spakuj ponownie `root.data` i `root.index`.

Nowy plik EXE ani pełny pack `locale` z wydania Tieru nie są wymagane przez
te funkcje.
