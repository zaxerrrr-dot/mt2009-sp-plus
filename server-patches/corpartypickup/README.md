# Cor Draconis dla Towarzysza (corpartypickup)

Bot nie może podnieść Cor Draconis z ziemi (`CHARACTER::PickupItem`, blokada
z 17 września 2026, żeby boty nie zbierały Corów graczy po wygaśnięciu
ochrony). Towarzysz zbiera jednak łup właściciela przez gałąź drużyny
w `PickupItem`, która od razu oddaje przedmiot właścicielowi – a blokada
zatrzymywała go wcześniej: podchodził do Cora gracza, dostawał odmowę
i rezygnował („Towarzysz nie podnosi Corów”, 27 września 2026).

Łatka w `char_item.cpp`: bot może podnieść Cor, który ma właściciela i tym
właścicielem jest **gracz (nie bot) z jego drużyny** – Cor trafia od razu do
tego gracza. Każdy inny Cor (bez właściciela, bota, obcego gracza) zostaje
zablokowany jak dotąd.

- `Apply-CorPartyPickupPatch.ps1` – Windows (instalator silnika,
  `tools/port/Apply-MT2009PlusEngine.ps1`);
- `apply_corpartypickup.py` – ta sama zmiana dla Linuksa/VPS;
- znacznik: `MT2009_PLUS_COR_PARTY_PICKUP_V1`.
