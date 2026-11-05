# remotecall – Enasir (Dozorca / Handlarz)

`MT2009_PLUS_REMOTE_CALL_V1` (właściciel, 5.11.2026: „Dodaj jeszcze to”). Na podstawie paczki „Official Remote Call”
(Khaled / LungSam) – przepisanej, nie skopiowanej – i opisu pl-wiki „System Enasira” / „Wersja 26.1” / „Dozorca Enasir
(h)”: przedmiot daje usługę Enasira, przycisk przy ekwipunku przywołuje go obok postaci, a on otwiera magazyn albo
sklep Handlarki Różności.

**Nakładana jako OSTATNIA** z listy łatek (po `energia`; kotwice: linie tytułów, `EncodeInsertPacket`, `CloseSafebox`,
podatek w `CShopManager::Sell`). Linux/VPS: `python3 apply_remotecall.py <game/src>`; Windows:
`Apply-RemoteCallPatch.ps1` (`tools/port/Apply-MT2009PlusEngine.ps1`, na końcu). Edycja już nałożona jest pomijana;
edycja, której stary kod nie występuje dokładnie raz, zatrzymuje całość, zanim cokolwiek zostanie zapisane.
`gen_edits.py [<game/src>]` pisze `edits.json` (i sprawdza kotwice). Przy wdrożeniu dopisać `remotecall` na końcu listy
łatek (po `energia`).

## Jak działa (jak na pl-wiki)

| | |
|---|---|
| Przedmioty | 72368 **Dozorca Enasir**, 72369 **Handlarz Enasir** (bez handlu: bez upuszczania, dawania, sklepu prywatnego), 72370 **Dozorca Enasir (h)**, 72371 **Handlarz Enasir (h)** (do handlu) – po 7 dni (wartość GF), stos 200 |
| Usługa | użycie dodaje czas (value1 s; `socket0` > 0 – tyle sekund) do usługi postaci: Magazyn / Sklep; czas płynie w czasie rzeczywistym (także offline), najwyżej **1000 dni** (więcej – przedmiot zostaje, komunikat); trwa po śmierci; bez ikony buffa (flagi questa `remote_call.safebox_end` / `remote_call.shop_end` = koniec w czasie uniksowym, nie efekty 706/707 paczki) |
| Przywołanie | przycisk po lewej stronie ekwipunku (klient) → CG 190 SUMMON; Enasir (20874) staje obok na **3 minuty**, widzi go **tylko przywołujący** (`EncodeInsertPacket` → `RemoteCallVisibleTo`); znika po oddaleniu się na 5 000, zmianie mapy / kanału, wylogowaniu, po czasie albo odesłaniu; następne przywołanie po **10 s** |
| Gdzie nie | instancje (mapa ≥ 10000), lochy, mapy wojen (gildii, królestw), areny, Sung Zi (wojna trzech królestw), mapa OX (113); martwa postać; otwarte okno handlu |
| Kliknięcie | quest `remote_call` (teksty z polskiego klienta, zrzuty pl-wiki): „Otwórz Magazyn” (hasło, potem magazyn – w kliencie „Magazyn Enasira”: GC 190 SAFEBOX), „Otwórz sklep” (sklep Handlarki Różności 9003; przy **sprzedaży** Enasir bierze **10 %** ceny po zwykłym podatku – `RemoteCallSellFee`), „Odeślij Enasira”, „Anuluj” – każda opcja tylko z aktywną usługą |
| Boty | nigdy (brak przywitania, użycie przedmiotu odmówione; ItemShop V3: `NEVER` + `IsPlayerBotIshop3ExcludedVnum`) |

GM: `/enasir` (czasy usług, czy przywołany, czy tu wolno), `/enasir daj <magazyn|sklep> <dni>` (sobie),
`/enasir zabierz` (obie usługi i Enasir).

## Pakiety

`HEADER_CG_REMOTE_CALL = 190` (2 B + bajt sekwencji: nagłówek, podnagłówek 0 HELLO / 1 SUMMON / 2 UNSUMMON),
`HEADER_GC_REMOTE_CALL = 190` (14 B, stały: nagłówek, podnagłówek, `dwValue0..2`): 0 STATE (sekundy usługi Magazyn,
Sklep; bit0 „tu wolno przywołać”), 1 SUMMONED (sekundy, VID Enasira – exe odtwarza ruch SPAWN), 2 GONE (sekundy
odnowienia), 3 MESSAGE (kod), 4 SAFEBOX (następny magazyn jest Enasira). Numery wolne w naszym `packet.h`,
`Packet.h` exe-src18 i na gałęziach (y-a: 184/187/188, tytuły 185/189, zwierzaki CG 122–134 / GC 224–236 – paczka miała
GC 235 = skala zwierzaka u nas). Klient wita się (CG HELLO) przy każdej fazie gry i tylko taki dostaje GC 190 – starszy
exe nigdy go nie zobaczy; użycie przedmiotu w starszym kliencie działa (czas się dodaje) z komunikatem o aktualizacji.

## Silnik (`edits.json`, 13 edycji) i nakładka

| Plik | Co |
|---|---|
| `packet.h` | nagłówki CG/GC 190, struktury `TPacketCGRemoteCall` (2 B) / `TPacketGCRemoteCall` (14 B), `static_assert` (exe to samo) |
| `packet_info.cpp` | CG 190, stały, z bajtem sekwencji |
| `input_main.cpp` | `RemoteCallPacket` |
| `char.cpp` | `EncodeInsertPacket` (Enasir tylko dla właściciela), `Destroy` (gracz zabiera Enasira; Enasir usunięty – właściciel o tym wie), `CloseSafebox` (magazyn już nie Enasira) |
| `char_item.cpp` | `UseItemEx`: 72368–72371 przed typem przedmiotu (`RemoteCallUseItem`) |
| `shop_manager.cpp` | `Sell`: 10 % dla Enasira po podatku |
| `questlua.cpp` | moduł `remote_call` (`is_owner`, `has_safebox`, `has_shop`, `open_safebox`, `open_shop`, `unsummon`, `time_left`; funkcja rejestrująca w `namespace quest` nakładki) |
| `cmd.cpp` | `/enasir` (GM_LOW_WIZARD) |

Nakładka: `linux-port/overlays/playerbot/src/game/src/remote_call.cpp` (cała logika; stan graczy tego rdzenia po PID,
właściciele po VID Enasira, jeden licznik 1 s tylko gdy ktoś ma Enasira).

**Różnice względem paczki** (świadome): usługi jako czas rzeczywisty we flagach questa (paczka: efekty, które liczą się
tylko online); bez zmiany `TPacketGCSafeboxSize` (paczka dokładała bajt – stary exe by się rozjechał) – zamiast tego GC
SAFEBOX; lista zakazanych map po stronie serwera (paczka: nazwy map w exe); własny pakiet CG zamiast komendy czatu
`/cmd_remote_call`; `pc.remote_call_unsummon` paczki zostawiał działający licznik (`bFromEvent = true`) – tu jeden
licznik dla wszystkich; sklep Handlarki Różności i opłata 10 % jak na pl-wiki (paczka: `npc.open_shop()` sklepu NPC
20874, którego nie ma); ITEM_QUEST jak certyfikaty tytułów (paczka: `USE_AFFECT` 706/707).

## Baza i ItemShop

`linux-port/docker/mariadb/playerbot/remote_call.sql` (w `apply.sh` po tytułach): 72368–72371 w `world.item_proto`
(`INSERT IGNORE`, ITEM_QUEST, value0 = usługa 0/1, value1 = 604800) i NPC 20874 „Enasir” w `world.mob_proto` (wiersz
Kawuco). Zaraz po nim ItemShop (zakładka Wyposażenie, `ishop_once remote_call_50` / BOOT_ONCE panelu; ItemShop V3
/shop3/ przez widok `itemshop3.shop`; ikony `img/item/72368–72371.png` z ikon GF, opisy `client_itemdesc.json`).
Na pl-wiki przedmioty są w ItemShopie (oraz z Aukcji Błyskawicznych i „Karty Magazynu Enasira” – u nas ich nie ma);
GF sprzedaje wariant 15-dniowy. Ceny – propozycja (wiki nie podaje):

| Linia | Przedmiot | Ilość | Cena |
|---|---|---|---|
| 50 | 72370 Dozorca Enasir (h) | 1 (7 dni) | 19 SM |
| 51 | 72371 Handlarz Enasir (h) | 1 (7 dni) | 19 SM |
| 52 | 72368 Dozorca Enasir | 4 (28 dni) | 59 SM |
| 53 | 72369 Handlarz Enasir | 4 (28 dni) | 59 SM |

Ceny zmienia się w panelu Seban → Edytor bazy danych → ItemShop.

## Klient

- Exe (`client-patches/exe`, `ENABLE_MT2009_REMOTE_CALL`, `Mt2009RemoteCall.cpp`): CG/GC 190, moduł `remoteCall`,
  `app.MT2009_REMOTE_CALL_EXE` – README exe.
- Root: `uiremotecall.py` (przycisk przy ekwipunku, podpowiedź z usługami i czasem, pytania „Czy chcesz przywołać
  Enasira?” / „Czy chcesz skorzystać z usług …?”), `uiinventory.py`, `game.py`, `interfacemodule.py`, `uisafebox.py`
  („Magazyn Enasira”). Bez exe z `remoteCall` nic z tego się nie pokazuje.
- Dane: `client-2.0.30/tools/remotecall` – paczka `remotecall` (model, ruchy, efekty, dźwięk Enasira i przyciski z
  klienta GF 26.1.11) + 72368–72371 w `item_proto` / `item_list` / `itemdesc`, Enasir w `mob_proto` klienta.
