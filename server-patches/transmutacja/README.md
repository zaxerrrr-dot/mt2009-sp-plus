# Transmutacja (zmiana wyglądu przedmiotu)

System Owsapa v6.2.6 `__CHANGE_LOOK_SYSTEM__` (Autor: blackdragonx61 / Mali) dla MT2009 PLUS 3.x „Yohara”, z zasadami
z pl-wiki („Transmutacja”). Znacznik: `MT2009_PLUS_CHANGE_LOOK_V1 (…)`. Makro silnika: `ENABLE_CHANGELOOK_SYSTEM`
(`common/CommonDefines.h`; to samo makro mają już linie sklepu Ikarus, które teraz przenoszą wygląd przez sklep
offline, aukcje i magazyn sklepu).

## Gdzie co jest

| Część | Miejsce |
|---|---|
| Logika | `linux-port/overlays/playerbot/src/game/src/playerbot_changelook.cpp` |
| Haki silnika | `edits.json` (44 zmiany: common, db, game; `gen_edits.py` je pisze); `apply_transmutacja.py <game/src>` (Linux), `Apply-TransmutacjaPatch.ps1` (Windows, krok `tools/port/Apply-MT2009PlusEngine.ps1` po Zyłach Jadeitu) |
| Baza | `linux-port/docker/mariadb/playerbot/transmutacja.sql` (`apply.sh`, idempotentny): kolumna `player.item.transmutation`, przedmioty 72325, 72326, 72341, 72343, 72344 |
| Quest | `linux-port/docker/game/quest/transmutacja.quest` – Teowaden (60003), opcja „Transmutacja” (osobny plik, opcje szarf zostają w `acce_costume_uriel.quest`) |
| Klient | exe 3.0: `client-patches/exe` (`UserInterface/Mt2009ChangeLook.cpp`, `Packet.h`, `GameType.h`); root: `uichangelook.py`, `uiscript/changelookwindow.py`, `uitooltip.py`, `uiinventory.py`, `game.py`; dane: `tools/transmutacja/patch_transmutacja_client.py` |

**db i game muszą być z tej samej budowy** (`TPlayerItem` ma na końcu `dwTransmutation`), a `transmutacja.sql` musi
przejść przed startem db (każde zapytanie o przedmioty czyta kolumnę). Pakiety przedmiotu (zestaw 21, zmiana 25,
magazyn 85/128, handel) mają na końcu 4 bajty wyglądu – tylko exe 3.0 je zna (bramka wersji 1010300).

## Zasady (pl-wiki)

- Broń – wygląd broni tego samego podtypu i tych samych flag klasy (jednoręczna z jednoręcznej itd.) albo wizerunku
  broni jej rodzaju; zbroja i kostium (pancerz) – między sobą; wizerunek broni – z broni swojego rodzaju; płeć
  kostiumów musi się zgadzać. Wierzchowiec – z innego wierzchowca (osobne okno, „Polimorfia wierzchowca”).
- Koszt 50 000 000 Yang (wierzchowiec 30 000 000) albo bilet w małym polu: Bilet Transmutacji 72326 / 72341 (handlowy),
  Bilet Polimorfii Wierzchowca 72344.
- Przedmiot, z którego bierzemy wygląd, **znika**. Przenosi się tylko wygląd (statystyki i bonusy zostają). Zmiana
  bonusów nie rusza wyglądu; ulepszenie (każde, także zwojem) tworzy nowy przedmiot – **bez** transmutacji.
- Anulacja Transmutacji 72325 (Anulacja Polimorfii Wierzchowca 72343 dla wierzchowców) przeciągnięta na przedmiot w
  ekwipunku (niezałożony) przywraca mu jego wygląd.
- Zakładając przedmiot: wygląd musi pasować do klasy postaci (a wygląd kostiumu – do płci).
- Wygląd widzą wszyscy (części postaci: `PART_MAIN`, `PART_WEAPON`; wierzchowiec – `Mt2009MountMobVnum`); „Ukryj
  cudze” (playerqol) też pokazuje zbroję i broń w ich wyglądzie.

## Okno

Okno nie używa pakietów Owsapa (CG 228 / GC 228–231), tylko komend czatu:
`/transmutacja in <pole> <komórka>` (0 – dostaje wygląd, 1 – daje wygląd, 2 – bilet), `/transmutacja out <pole>`,
`/transmutacja accept`, `/transmutacja cancel`; serwer: `ChangeLookOpen`, `ChangeLookSet`, `ChangeLookDel`,
`ChangeLookClose`, `ChangeLookDone`. Przy „accept” wszystko jest sprawdzane jeszcze raz po id przedmiotów (przedmiot
przeniesiony, w handlu, w sklepie albo założony – odmowa), a postać nie może odejść dalej niż 1500 od miejsca
otwarcia. Quest: `game.open_changelook(0|1)`, `item.get_changelook_vnum()`.
