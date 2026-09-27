# Klient 2.0.21: szansa w oknie kowala, pełne nicki w szepcie, Auto Łowy

Względem klienta 2.0.20 (`client-patches/client-2.0.20`), zmiany z klientów
2.0.42 i 2.0.43 Metin2 Playerbots scalone trójstronnie na nasze pliki
(baza: 2.0.41):

- `root/constinfo.py` – `ENABLE_REFINE_PCT = True`;
- `root/uirefine.py` – okno ulepszania pokazuje szansę, którą wysyła serwer
  (od serwera 2.10.0; starszy wysyła 0 i linijka się chowa);
- `root/uiscript/whisperdialog.py` – nick w oknie szeptu do 24 znaków;
- `root/uiautohunt.py` – Auto Łowy idą do dalekiego celu i przedmiotu,
  dopóki się zbliżają; przedmiot porzucony dla walki podnoszą po walce;
  bez „Wracaj” nie wracają na start; umiejętność 47 według exe;
- `root/uisidekickinventory.py` – przyciski „Daj” i „Weź” yang w oknie
  Towarzysza;
- `root/intrologin.py` – exe bez czterech stron ekwipunku
  (`player.INVENTORY_PAGE_COUNT` < 4) nie wchodzi do gry i mówi, żeby pobrać
  pełny klient z Discorda. Nasz metin2client.exe zgłasza 5, więc go to nie
  dotyczy; launcher MT2009 PLUS nie podmienia exe (manifest nie ma
  `clientExe`).

gamedata i season2 bez zmian. Pakowanie: podmienić te pliki w `root`
klienta 2.0.20 i przepakować (m2pack.py).
