# irrem – niezdejmowalne przedmioty: pytanie o zniszczenie

Znacznik: `MT2009_PLUS_IRREMOVABLE_DELETE_V1` (lista właściciela z 3.11.2026). Założony przedmiot z flagą
`ITEM_FLAG_IRREMOVABLE` (przedmioty czasowe typu unikat – np. Talizman Pracowitości 70004, Diabelski Kolec 70042,
Pierścień Doświadczenia 72303) przy próbie zdjęcia pokazuje okno „Tego przedmiotu nie można zdjąć. Czy chcesz go
zniszczyć?” – „Zniszcz” niszczy przedmiot, „Nie” / Esc zostawia go na miejscu. Dotąd zdjęcie było po cichu odrzucane.

Logika: `linux-port/overlays/playerbot/src/game/src/irremovable_delete.cpp`, tu tylko haki (`gen_edits.py` →
`edits.json`, `apply_irrem.py` / `Apply-IrremPatch.ps1`). Kolejność: po `switchbot` (input_main.cpp ItemUse/ItemMove)
i `fishren` (cmd.cpp) – na końcu listy.

## Skąd
Przeniesione z drugiego drzewa MT2009 PLUS (vps3, `/opt/mt2009plus`, commit `a7dbe0c3` „Patch 02.11”, 2.11.2026):
`char_item.cpp` `Mt2009AskRemoveIrremovable` (wołane w `MoveItem` przed `CanUnequipNow` i w `UnequipItem` po jego
odmowie) → komenda klienta `usun_zalozony_pytaj <cell> <vnum>` → `root/game.py` `uiCommon.QuestionDialog`
„Tego przedmiotu nie można zdjąć. Usunąć …?” → `/usun_zalozony <cell> <vnum>` (`cmd_general.cpp`, sprawdza śmierć,
wymianę, sklep, magazyn, kostkę, blokadę, `IsEquipped`, flagę i vnum) → `ITEM_MANAGER::RemoveItem(item,
"DELETE_IRREMOVABLE")`.

Różnice u nas:
- pytanie tylko z własnego pakietu gracza (`CInputMain::ItemUse` / `ItemMove` otwierają „zakres”); tamto pytało przy
  każdej odmowie silnika (quest `pc.unequip`, zsiadanie z wierzchowca `UnEquipSpecialRideUniqueItem`, komendy
  kostiumów…). Boty (deskryptory botów) nigdy nie są pytane. Najwyżej jedno pytanie na pakiet i jedno na sekundę
  dla tego samego przedmiotu.
- haki: `CanUnequipNow` (gałąź `ITEM_FLAG_IRREMOVABLE` – PPM na przedmiocie, przeciągnięcie innego przedmiotu na
  jego slot, gałąź ekwipunku `MoveItem`) i wczesny test `MoveItem` (przeciągnięcie założonego przedmiotu z oknem
  INVENTORY nie dochodzi do `CanUnequipNow`; na vps3 ten sam test stoi przed ich hakiem w `MoveItem`).
- „Tak” niesie losowy token związany z ID przedmiotu, graczem, połączeniem i 60 s (nie `<cell> <vnum>` – stare
  „tak” nie zniszczy innego przedmiotu, który później trafił na ten slot). Jedno „tak” na pytanie.
- ponowne sprawdzenie przy „tak”: ten sam ID i vnum, właściciel, założony, nadal `ITEM_FLAG_IRREMOVABLE`, nie
  zablokowany (switchbot) ani w wymianie; gracz żywy, bez wymiany / sklepu / własnego sklepu / magazynu / okna
  wytwarzania, `CanHandleItem()`.
- zniszczenie: `ITEM_MANAGER::RemoveItem(item, "IRREMOVABLE_DELETE")` – wiersz w logu przedmiotów
  (`LogManager::ItemLog`, podpowiedź: nazwa i ilość) + `sys_log` „IRREMOVABLE_DELETE: …”.

## Protokół
| kierunek | tekst |
|---|---|
| serwer → klient | `IRREM ask <token> <vnum>` – otwórz pytanie (`root/uiirremovable.py`) |
| klient → serwer | `/irrem usun <token>` – zniszcz |
| klient → serwer | `/irrem anuluj` – „Nie”, Esc, zamknięte okno |

## Przedmioty zdejmowalne
Haki sprawdzają najpierw `ITEM_FLAG_IRREMOVABLE` – zwykłe zdejmowanie się nie zmienia. Rękawica Złodzieja
72005/70043 i Pierścień Doświadczenia 39002/72003/70005 są zdejmowalne od `MT2009_PLUS_DROP307_V1` (sekcja C, flaga
zdjęta w `item_proto` serwera i klienta) i schodzą jak każdy inny przedmiot.

## Klient
`client-patches/client-2.0.30/root/uiirremovable.py` (nowy, `uiCommon.QuestionDialog2`, teksty cp1250 jako bajty,
plik ascii) + `game.py`: `serverCommandList["IRREM"]` i `DestroyWindow` przy zamknięciu gry. Stary klient bez tego
modułu nie zna komendy `IRREM` – nic nie pokazuje, zdjęcie jest odrzucane jak dotąd.
