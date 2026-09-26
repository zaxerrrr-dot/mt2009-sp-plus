# Klient 2.0.18: podgląd skrzyń i dropu, przenikanie Towarzysza, kolejka cen

Pliki `root` klienta 2.0.18 względem klienta 2.0.17. Wymagają serwera
z komendami `/chest_preview`, `/mob_drop_preview` i `SidekickVid`.

## Zawartość `root/`

- `uichestpreview.py`, `playerbot_ui/chest_button.tga`, `chest_slot.tga` –
  podgląd skrzyni: przycisk w ekwipunku, przeciągnięta skrzynka pokazuje,
  co może z niej wypaść (`uiinventory.py`, `uiscript/inventorywindow.py`);
- `uimobpreview.py` – „?” przy pasku życia potwora albo metina pokazuje jego
  drop (`uitarget.py`, `game.py`); zastępuje dawny `uimobdrop.py` i przycisk
  „Drop” (usunięte z `uitarget.py`, `interfacemodule.py`, `game.py`);
- `sidekickcollision.py` – postać przechodzi przez własnego Towarzysza
  (komenda serwera `SidekickVid`);
- `uiautohunt.py` – po użyciu umiejętności Auto Łowy nie ruszają się
  1,3 s, więc obrażenia ze skilli wchodzą;
- `shoppricepump.py` + `offlineshopmanage.py` – masowa zmiana ceny (Ctrl +
  PPM) wysyła zmiany po jednej co 0,25 s i na końcu sprawdza, czy wszystkie
  weszły (serwer przyjmuje jedną operację na sklepie co 200 ms).

## Pakowanie

- `root`: podmienić powyższe pliki w `root` klienta 2.0.17, **usunąć**
  `uimobdrop.py`, przepakować `root.data`/`root.index`.
- `maps`: dodać do paczki `maps` katalog `maps/metin2_map_devilscatacomb/`
  (mapa Katakumb Diabła).
