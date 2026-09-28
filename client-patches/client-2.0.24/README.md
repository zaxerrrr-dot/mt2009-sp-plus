# Klient 2.0.24: filtr podnoszenia, szybszy kosz, kategoria MT2009 Plus

Względem klienta 2.0.23 (`client-patches/client-2.0.23`). Część serwerowa:
`server-patches/playerqol` (serwer 2.12.0).

- `root/uipickupfilter.py` (nowy) – okno „Filtr podnoszenia (Z i pet)”:
  13 rodzajów jak w Auto Łowach, zapis w `autohunt/filtr.cfg`, wysyłane na
  serwer po każdym wejściu do gry i każdej zmianie (`/pickup_filter`).
  Otwiera je Ctrl+Z albo `/filtr`.
- `root/updateable.py`, `root/game.py` – z włączonym filtrem przytrzymanie Z
  i klawisz ` podnoszą przez serwer (filtr), a nie najbliższy przedmiot.
- `root/game.py` – F5 otwiera i zamyka wyszukiwarkę sklepów zawsze (był
  tylko w bloku kamery kinowej i otwierał też nieistniejący ranking);
  obsługa odpowiedzi kosza paczkami i filtra.
- `root/uiautohunt.py` – cel przy 0 PŻ (komenda serwera `TargetHP`) jest
  martwy: exe nie ma `player.IsTargetDead`, więc Auto Łowy biły trupa, aż
  zniknął jego model.
- `root/uigarbagebin.py`, `root/interfacemodule.py` – kosz najpierw pyta
  o potwierdzenie, potem sprawdza i usuwa po 18 stosów na komendę
  (`/garbage prepare_many` / `commit_many`); ze starszym serwerem działa
  jak dotąd, stos po stosie.
- `root/inventoryarrange.py`, `root/uiinventory.py` – przycisk porządkowania
  otwiera wybór: „Ułóż i scal” albo „Tylko scal stosy” (`/inventory_arrange
  merge`).
- `root/offlineshopsearch.py`, `root/offlineshopguest.py` – kategoria
  „MT2009 Plus”: Cor Draconis, szarfy proste, dostojne, zacne i unikatowe,
  alchemia antyczna, legendarna i mityczna – bez podziału na wzory, kamienie
  i plusy.
- `root/uisidekick.py` – przycisk „Na ryby” w oknie Towarzysza.

Z klienta 2.0.46 bazy (scalone trójstronnie, baza 2.0.45): Dom Towarowy
(`root/customfleamarket.py`, nowy; `offlineshopsearch.py`, `interfacemodule.py`,
`game.py`), podpowiedź ceny przy wystawianiu (`offlineshopmanage.py`) i tytuły
czterech Hazardzistów (`playerbot_status_tail.py`). Pominięte: maksima bonusów
w `localeinfo_point.py` (Maks. PŻ 2000 nie wchodzi do MT2009 PLUS).

gamedata i season2 bez zmian. Pakowanie: pliki 2.0.23 i 2.0.24 na `root`
klienta 2.0.22 przez `m2pack.repack_add` (nowy plik `uipickupfilter.py`).
