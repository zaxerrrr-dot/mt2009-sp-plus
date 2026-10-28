# Magazyn Item-Shopu: 3 strony

Poprawka silnika, znacznik `MT2009_PLUS_MALL_PAGES_V1`, nakładana po `addeq`
(`tools/port/Apply-MT2009PlusEngine.ps1`, `yohara-deploy.sh`);
`Apply-Mall3Patch.ps1` i linuksowy bliźniak `apply_mall3.py` czytają ten sam `edits.json`.

## Jak było

- Gra (`CHARACTER::LoadMall`) od zawsze tworzy magazyn Item-Shopu na
  `SAFEBOX_PAGE_COUNT` = 3 strony (135 pól) i wysyła klientowi rozmiar 3;
  exe (`CPythonSafeBox::OpenMall`) robi z tego 135 pól.
- Okno w `root/uisafebox.py` (`MallWindow`) pokazywało tylko pierwszą stronę (45 pól).
- Baza (`CClientManager::RESULT_SAFEBOX_LOAD`) ustawiała magazynowi Item-Shopu
  rozmiar 1, więc dostawy z `item_award` trafiały tylko na pierwsze 45 pól,
  a reszta czekała w `item_award`.

## Co robi

- `common/tables.h` – `TSafeboxLoadPacket` dostaje `bMallPages`;
- `cmd_general.cpp` (`do_mall_password`) – nowy klient wysyła
  `/mall_password <hasło> 3`; bez drugiego słowa (stary klient) zostaje 1 strona;
- `db ClientManager.cpp` – liczba stron trafia do `pi->ip[1]`, a siatka dostaw
  `item_award` ma tyle stron (1 albo 3).

Stary klient: dostawy dalej tylko na stronę 1, jak dotąd (pola 45+ i tak już
przychodziły do jego exe bez szkody – wektor ma 135 pól, okno ich nie rysuje).
Klient: `MallWindow` z przyciskami stron I / II / III jak w magazynie.
Exe bez zmian.
