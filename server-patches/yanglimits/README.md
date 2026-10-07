# Limity Yang – `MT2009_PLUS_YANG_LIMITS_V1`

**Autor: Digi Rasta** (paczka „nowy-system” v0.26.0, karta `SYSTEMY/limity.md`). Przeniesione do MT2009 PLUS jako
nasz kod – bez haków `zastosuj.py`. Decyzja właściciela (7.10): **100 mld w kieszeni, 10 mld w handlu, 50 mld cena
na straganie**. Zmiana stosu na 1000 z tej samej wersji Digi Rasty **nie** jest przeniesiona (zostają stosy 200).

## Co się zmienia

| Limit | Było | Jest | Gdzie |
|---|---|---|---|
| Yang przy sobie (`GOLD_MAX`) | 2 mld | **100 mld** | `CHARACTER::ChangeGold`, handel, sprzedaż u NPC, stragan, odbiór Yang ze sklepu offline |
| Yang w jednym handlu (`EXCHANGE_GOLD_MAX`) | 100 mln | **10 mld** | `CExchange::AddGold`, `input_main.cpp` (komunikat przy przekroczeniu) |
| Cena jednej pozycji sklepu (`SHOP_PRICE_MAX`) | < 2 mld | **50 mld** | sklep offline (`IsGoodSalePrice`), stary stragan (`char_shop.cpp`) |
| Portfel i ceny bota (`PLAYERBOT_GOLD_MAX`) | 2 mld | **2 mld (bez zmian)** | `CHARACTER::Mt2009PlusGoldMax`, kod botów |

Stałe są w `enum LongData : long long` (`common/length.h`) – wartość większa niż `INT_MAX` w `EMisc` zmieniłaby typ
całego enuma. Blokady „masz za dużo Yang” działają dopiero **powyżej** limitu (było `>=`: przy równych 2 mld handel
był zablokowany). Komunikaty limitu są po polsku wprost w kodzie (klucze `LC_TEXT` mówiły o 2 miliardach).

## Boty

Boty zostają przy dawnych 2 mld: `ChangeGold` przycina zysk bota do `PLAYERBOT_GOLD_MAX` (bot już powyżej – np.
ustawiony ręcznie w bazie – tylko nie zyskuje), handel z botem i odbiór Yang ze sklepu bota liczą się do jego
limitu. Kod botów (`playerbot_*`, overlay) porównuje swoje ceny z `PLAYERBOT_GOLD_MAX` zamiast `GOLD_MAX`, więc
wystawia, przecenia i kupuje dokładnie jak dotąd (ich ceny i portfele są w `DWORD`/`int` – nasycenie 0xFFFFFFFF
„którego żaden stragan nie weźmie” dalej odrzucają ich własne sprawdzenia). Ceny graczy boty czytają w 64 bitach
i kupują tylko w ramach budżetu, więc oferta za 50 mld niczego im nie psuje. Przenoszenie Yang Towarzysz ↔ właściciel
liczy limit każdej sakiewki osobno (`Mt2009PlusGoldMax`).

## Baza danych (`linux-port/docker/mariadb/playerbot/apply.sh`)

Jednorazowo (sprawdza `information_schema`, potem nic nie robi): `player.myshop_pricelist.price` INT UNSIGNED →
BIGINT UNSIGNED (zapamiętane ceny straganu; INT obcinał po cichu do 4,29 mld) i `log.money_log.gold` INT → BIGINT
(też w `log_schema.sql` i `initdb.d/20-log-schema.sql`). Pozostałe kolumny Yang były już 64-bitowe (`player.gold`,
`safebox.gold`, `ikashop_*`, `log.offline_shop`, `log.ikarusshop_log`, `log.playerbot_listing`).

## Pakiety i exe

Pakiety się **nie** zmieniają: handel (`TPacketCGExchange/GCExchange.arg1`), złoto (`TPacketGCGoldUpdate`), ceny
straganu i sklepu offline (`TShopItemTable.price`, `TPriceInfo.yang`) były 64-bitowe po obu stronach. Nowy exe
(`client-patches/exe`, `ENABLE_MT2009_YANG_LIMITS`) liczy Yang w handlu w 64 bitach (`exchange.GetElkFrom*`,
`net.SendExchangeElkAddPacket`) i podaje `player.GOLD_MAX` / `EXCHANGE_GOLD_MAX` / `SHOP_PRICE_MAX`.

Stary exe działa dalej: okno handlu przyjmuje 8 cyfr (do 99 999 999), ceny w sklepie offline do 2 mld (skrypty
`root` biorą limity przez `getattr`), Yang w kieszeni do 100 mld pokazuje się poprawnie (pakiet złota był 64-bitowy).
Jedyna różnica: kwota powyżej 2,1 mld położona w handlu przez drugą stronę (z nowym exe) wyświetli się w starym exe
źle (obcięta do 32 bitów) – przeniesiona zostaje poprawna kwota (liczy serwer). Boty dają w handlu najwyżej 2 mld.

Upuszczanie Yang na ziemię i Yang w magazynie zostają 32-bitowe (jak u Digi Rasty).

## Pliki

- `edits.json` – 16 zmian silnika, każda z własnym znacznikiem `MT2009_PLUS_YANG_LIMITS_V1 (…)`: `../../common/length.h`
  (2), `char.h`, `char.cpp` (2), `input_main.cpp` (3), `shop_manager.cpp` (2), `char_shop.cpp` (3),
  `ikarus_shop_manager.cpp` (3);
- `Apply-YangLimitsPatch.ps1` – Windows (`tools/port/Apply-MT2009PlusEngine.ps1`, na końcu);
- `apply_yanglimits.py <game/src>` – Linux/VPS; oba czytają ten sam `edits.json`.

Zmiana już nałożona (jest jej znacznik) jest pomijana; zmiana, której kodu nie ma dokładnie raz, przerywa całość,
zanim cokolwiek zostanie zapisane.
