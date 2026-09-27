# Klient 2.0.23: Auto Łowy, pasek celu, okno Towarzysza

Względem klienta 2.0.22 (`client-patches/client-2.0.22`), zmiany z klientów
2.0.44 i 2.0.45 bazy scalone trójstronnie na nasze pliki (baza: 2.0.43):

- `root/game.py` – polecenia serwera `TargetHP` (życie celu liczbą) i
  `IkashopOwnerName` (pełny nick właściciela sklepu offline);
- `root/uitarget.py` – pasek celu pokazuje życie liczbą;
- `root/offlineshopguest.py` – pełny nick właściciela i szept do niego;
- `root/uiautohunt.py` – Auto Łowy zbierają drop po walce, łucznik strzela od
  razu, przedmiot, którego nie da się podnieść, pomijają na 30 s;
- `root/uirefine.py` – okno o linijkę wyższe, gdy pokazuje szansę;
- `root/uisidekick.py` – przełączniki „Lurowanie”, „Gra beze mnie” i
  „Skrzynki” (nasze okno „Statystyki” zostaje).

Świadomie pominięte: większe przyciski przy ekwipunku
(`uiscript/inventorywindow.py`, grafiki `playerbot_ui/*_btn*.tga`) i maksima
nowych bonusów w `localeinfo_point.py` (bonusy jak na serwerze globalnym nie
wchodzą do MT2009 PLUS).

gamedata i season2 bez zmian. Pakowanie: podmienić te pliki w `root`
klienta 2.0.22 i przepakować (m2pack.py).
