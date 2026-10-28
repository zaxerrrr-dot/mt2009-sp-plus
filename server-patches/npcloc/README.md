# npcloc – Lokalizator NPC (ulepszona mapa świata)

Znacznik: `MT2009_PLUS_NPC_LOCATION_HELPER_V1`. Autor systemu: Best Studio (paczka „NPC Location Helper”), przeniesiony
na MT2009 Plus.

Duża mapa (atlas) dostaje drugi widok: lista NPC każdej mapy według kategorii (sklepy, magazyn, teleporter, wejścia do
lochów…), zaznaczenie wybranego NPC na mapie, strzałka pod postacią w jego stronę, przewodnik po potworach mapy i ich
łupie oraz teleport obok wybranego NPC za Kamień Teleportacji.

## Serwer

| Plik | Zmiana |
|---|---|
| `npc_location_helper.cpp/.h` (overlay, `linux-port/overlays/playerbot/src/game/src/`) | **nowe**: pakiety (nagłówek CG/GC **196**, 18 + bajt sekwencji / 24 bajty, `static_assert`), wczytanie `locale/poland/npc_location_helper/` (przy pierwszym użyciu, bez obiektu w `main.cpp`), włączenie przedmiotem 79667, teleport z kontrolami |
| `packet_info.cpp` | `#include "npc_location_helper.h"`, `Set(HEADER_CG_NPC_LOCATION_HELPER, 18, …, true)` |
| `input_main.cpp` | `#include`, `case HEADER_CG_NPC_LOCATION_HELPER` → `NpcLocationHelperPacket` |
| `char_item.cpp` | `USE_SPECIAL` → `case 79667` → `NpcLocationHelperUseItem` (drugi przedmiot nie jest zużywany) |

5 edycji (`edits.json`), każda z własnym znacznikiem. Bez zmian w `packet.h`, `main.cpp`, `input.h`, `service.h`,
`item_length.h` (paczka dodawała podtyp `USE_MAP` dla kawałków map – u nas mapy są odblokowane, patrz niżej).

### Teleport do NPC – kontrole (`WarpToNPC`)

- Lokalizator włączony (flaga questowa `npc_location_helper.active`), 5 minut przerwy między teleportami
  (`npc_location_helper.last_warp_time`).
- Jak mapa teleportacji pod TAB (`mapa_tab`) i zapisane pozycje: nie martwy, nie na wierzchowcu, nie w pojedynku / na
  arenie, bez otwartego handlu / sklepu / magazynu / kostki (`IsBusy`, `CanWarp`), nie z instancji lochu (≥ 10000), nie
  z wesela, pojedynków, OX, wojny królestw, map GM, areny wojny gildii (gdy gildia walczy). Dolina Cyklopów (360) i
  Pustkowie Faraona (361) tylko przy włączonym module Arezzo (`mt2009_arezzo_closed` = 0).
- Cel: NPC z pliku punktów mapy (±3 m od tego, co wysłał klient – serwer nigdy nie bierze współrzędnych od klienta),
  mapa z `show_atlas` ≠ 0 i `show_npc_list` = 1, poziom / królestwo z `npc_location_helper.txt`, mapę hostuje któryś
  rdzeń kanału (`CMapLocation`, np. wyłączony 3 Loch Pająków odpada).
- Na inną mapę tylko tam, gdzie wejście nic nie kosztuje (`IsOpenTargetMap`): królestwa (kategoria 1), ziemie
  neutralne (2), pola Yohary (6) oraz miejsca Pierścienia Teleportacji: Loch Pająków 1 (104), Świątynia Ochao (209),
  301–304, Port (368). Lochy, Królestwo Żywiołów (378–381, 50 000 000 Yang), Tajemnicza Instancja (396, bilet),
  Płaskowyż Iluzji (397), Grota Wygnańców (72/73), Erebus, Sung Ma, Gnolle, Świątynia Węży – tylko w obrębie tej samej
  mapy (gracz już tam jest). Klient mówi to przed pytaniem (`_WarpBlockedReason`, ta sama lista).
- Nigdy do portalu (ikona 1 w pliku punktów) – lądowanie obok przeniosłoby przez portal.
- Pozycja: baza mapy + punkt NPC, 2 m obok NPC na komórce, po której da się chodzić (gdy ten rdzeń hostuje mapę;
  generator sprawdził każdy punkt w `server_attr`).
- Koszt: 1 kamień na tej samej mapie, 2 w tym samym regionie (indeks mapy / 10), 3 dalej; najpierw Kamień
  Teleportacji 79669 (związany), potem Kamień Teleportacji+ 79668.
- Boty: nigdy nie wysyłają tego pakietu; serwer nic nie wysyła postaci bez połączenia (`GetDesc`) ani botom.
- Starszy klient: pakiet 196 idzie tylko do połączenia, które samo go wysłało (nowy klient pyta o stan po wejściu do
  gry) – stary exe nie dostaje nieznanego nagłówka; Lokalizator NPC użyty ze starego klienta nie jest zużywany
  („wymaga nowszego klienta gry”).
- Pakiet STATUS niesie indeks mapy postaci (klient nie ma własnego).

### Kawałki map (otwarte pytanie do właściciela)

Paczka zamyka część map za kawałkami map (`show_atlas` = 2, przedmioty 79670–79822). U nas **wszystkie mapy są
otwarte** (`show_atlas` = 1 w danych). Mechanizm zostaje po stronie danych: mapa z `show_atlas` 2 jest celem dopiero z
flagą questową `npc_location_helper.unlocked_map.<indeks>` (np. z questa) – przedmiotów kawałków nie dodano.

## Dane i przedmioty

- `linux-port/docker/game/npc_location_helper/` → obraz `/opt/metin2/share/locale/poland/npc_location_helper/`
  (`npc_location_helper.txt` + `<map_dir>_point.txt`), robione z naszych map przez `tools/npcloc/gen_npcloc_data.py`
  (te same pliki dostaje klient).
- `linux-port/docker/mariadb/playerbot/npc_location_helper.sql` (apply.sh): 79667 Lokalizator NPC, 79668 Kamień
  Teleportacji+, 79669 Kamień Teleportacji.

## Kolejność / uruchomienie

Po `kupon100` (na końcu listy; kotwice: `#include "packet_info.h"`, linia `Set(HEADER_CG_SWITCHBOT…)`,
`#include "input.h"`, `case HEADER_CG_REQUEST_INFO_RESPONSE:`, komentarz Yut Nori w `USE_SPECIAL`).

Linux/VPS: `python3 apply_npcloc.py <game/src>`; Windows: `Apply-NpcLocPatch.ps1 -SourceDir <game/src>` (wołane na
końcu `tools/port/Apply-MT2009PlusEngine.ps1`).
