# Podatek od sprzedaży między graczami (suwak w panelach)

Poprawka silnika, znacznik `MT2009_PLUS_SALE_TAX_V1` (każda zmiana ma własny
dopisek w nawiasie). Nakładana raz, przy przygotowaniu wydania
(`tools/port/Apply-MT2009PlusEngine.ps1`, na końcu – opiera się na liniach
„część stosu” z `shopsearch2`); `Apply-SaleTaxPatch.ps1` i linuksowy bliźniak
`apply_saletax.py` czytają ten sam `edits.json`.

## Co robi

Część ceny przedmiotu sprzedanego innemu graczowi albo botowi znika z gry –
sprzedający dostaje mniej, kupujący płaci tyle samo co dotąd. Ogranicza ilość
yang w obiegu. Sprzedaż NPC bez podatku.

Wysokość ustawia suwak „Podatek od sprzedaży między graczami (%)” w obu
panelach (panel klasyczny: strona AI, panel Sebana: „Zachowanie botów”),
0–50%, co 1%. Panel zapisuje linię `SALE_TAX <procent>` w
`/opt/m2spool/playerbot_weights.tsv`; rdzenie czytają ten plik co 5 sekund,
bez restartu. Brak linii albo 0 = bez podatku (świat jak dotąd).

| Dopisek | Plik | Co |
|---|---|---|
| `(shop include)`, `(stall)` | `shop.cpp` | `CShop::Buy` – zwykły sklep gracza i stragan bota: podatek odjęty od tego, co dostaje właściciel. |
| `(ikashop include)`, `(buy)` | `ikarus_shop_manager.cpp` | Lady offline i Dom Towarowy (wyszukiwarka kupuje przez lady): procent suwaka dodany do podatku lady (`offline_shop_tax`, domyślnie 5%), który rdzeń bazy już odejmuje od zapłaty dla sprzedającego (cały stos i część stosu). |
| `(owner window)` | `ikarus_shop_manager.cpp` | Okno właściciela lady pokazuje podatek razem z suwakiem. |
| `(count part)`, `(count line)` | `ikarus_shop_manager.cpp` | Tylko licznik do linii podsumowania. |
| `(char_item include)`, `(open shop)` | `char_item.cpp` | Okno zakładania lady pokazuje podatek razem z suwakiem. |
| `(db reader)`, `(offer)`, `(auction)` | `../../db/src/ClientManagerIkarusShop.cpp` | Przyjęta oferta prywatna i aukcja – rozliczane tylko w rdzeniu bazy, który sam czyta `SALE_TAX` z tego samego pliku (co 5 s). |

Wartość w rdzeniu gry: `playerbot_sale_tax.h` (nakładka Playerbots), ustawiana
przez `playerbot_config.h` przy wczytaniu pliku wag (`PLAYERBOT_CONFIG: sale
tax between players and bots N%`). Co najwyżej raz na 10 minut na rdzeń
syslog dostaje linię `MT2009_SALE_TAX: N% - X sales worth Y yang, Z yang taken
out of the game ...`; rdzeń bazy pisze `MT2009_SALE_TAX: offer accepted|auction
sold owner ... gross ... tax ...` przy każdej opodatkowanej ofercie/aukcji.

Bez podatku: wymiana przez okno handlu (to zamiana, nie sprzedaż – nie da się
odróżnić od prezentu), opłaty za usługi botów (najemnicy), sprzedaż NPC.

Zmiana już nałożona (jest jej znacznik) jest pomijana; zmiana, której kodu nie
ma dokładnie raz, przerywa całość, zanim cokolwiek zostanie zapisane.
