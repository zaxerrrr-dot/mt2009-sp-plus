# Klient: zmiany Tieru 2.0.38–2.0.40 i kolejka zmian cen

Pliki `root` po scaleniu naszego klienta 2.0.17 ze zmianami klienta Tieru
2.0.37 → 2.0.40 (baza scalenia: Tieru 2.0.37). Serwer musi mieć Tieru 2.2.23
(komendy `/chest_preview`, `/mob_drop_preview`, `SidekickVid`).

## Zawartość `root/`

- `uichestpreview.py`, `playerbot_ui/chest_button.tga`, `chest_slot.tga` –
  podgląd skrzyni (przycisk w ekwipunku; `uiinventory.py`,
  `uiscript/inventorywindow.py`);
- `uimobpreview.py` – podgląd dropu „?” przy pasku życia (`uitarget.py`,
  `game.py`); **zastępuje nasz** `uimobdrop.py` i przycisk „Drop” (usunięte
  z `uitarget.py`, `interfacemodule.py`, `game.py`);
- `sidekickcollision.py` – przenikanie przez Towarzysza (komenda
  `SidekickVid`); zastępuje nasz `SidekickGhost`;
- `uiautohunt.py` – po umiejętności Auto Łowy nie ruszają się 1,3 s, więc
  obrażenia ze skilli wchodzą;
- `shoppricepump.py` + `offlineshopmanage.py` – masowa zmiana ceny (Ctrl +
  PPM) wysyła zmiany po jednej co 0,25 s i na końcu sprawdza, czy wszystkie
  weszły (serwer przyjmuje jedną operację na sklepie co 200 ms).

## Pakowanie

- `root`: podmienić powyższe pliki w `root` klienta 2.0.17 i **usunąć**
  `uimobdrop.py`, potem przepakować `root.data`/`root.index`.
- `maps`: dodać do paczki `maps` katalog `maps/metin2_map_devilscatacomb/`
  z paczki `season2` klienta Tieru 2.0.38+ (mapa Katakumb Diabła).
