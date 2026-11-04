# wideattr – dwubajtowy typ bonusu (faza 1)

`MT2009_PLUS_WIDE_ATTR_V1` (właściciel, 3.11.2026: „miejsce na wszystkie pozostałe bonusy 6/7 z wiki”). Po rundzie 2
(`server-patches/bonusy67b`) zajęte były wszystkie 256 numerów punktów, bo typ bonusu przedmiotu miał 1 bajt. Ta łatka
robi z niego **2 bajty (WORD) od bazy po exe** – bez nowych bonusów (to faza 2) i bez zmiany żadnej wartości: stare
numery 0–255 znaczą to samo, stare przedmioty i stare wiersze bazy działają bez konwersji.

**Nakładana jako OSTATNIA** z listy łatek (jej kotwice to linie wszystkich pozostałych, m.in. `bonusy67b`,
`switchbot`, `antimagic`). Linux/VPS: `python3 apply_wideattr.py <game/src>`; Windows: `Apply-WideattrPatch.ps1`
(`tools/port/Apply-MT2009PlusEngine.ps1`, na końcu). Edycja już nałożona jest pomijana (jej nowy kod jest w pliku);
edycja, której stary kod nie występuje dokładnie raz, zatrzymuje całość, zanim cokolwiek zostanie zapisane.

## Co jest dwubajtowe

| Miejsce | Było | Jest |
|---|---|---|
| `TPlayerItemAttribute::bType` (`common/tables.h`) – każdy bonus przedmiotu w pamięci, w pakietach db↔game i game↔klient | `BYTE` | `WORD` (linia bonusu 3 B → 4 B) |
| `TItemApply::bType` (`common/tables.h`) – `aApplies[3]` z `item_proto` i `item_extra_apply` w rdzeniach | `BYTE` | `WORD` |
| `CAffect::bApplyOn`, `TPacketAffectElement::bApplyOn`, `TPacketGDRemoveAffect`, `TPacketGCAffectRemove` | `BYTE` | `WORD` |
| `TPacketGCPointChange::type` (zmiana punktu do klienta) | `BYTE` | `WORD` |
| `POINT_MAX_NUM` (`common/length.h`) | 256 (= ostatni + 1) | **512** na sztywno; `POINT_WIDE_END` (256) = pierwszy wolny numer |
| `CHARACTER::GetPoint/SetPoint/GetRealPoint/SetRealPoint/GetLimitPoint/GetPolymorphPoint/GetResistPoint/PointChange/IsUtilityPoint`, `AddAffect/CanAddAffect/OnAddAffect/FindAffect`, `SendAffectRemovePacket` | `BYTE` | `WORD` |
| `CItem::GetAttributeType/SetAttribute/SetForceAttribute/AddAttribute/AddAttr/AddRareAttr/HasAttr/HasRareAttr/FindAttribute/RemoveAttributeType/FindApplyValue` | `BYTE` | `WORD` |
| skille (`bPointOn`, `bPointOn2`, `bPointOn3`, `FuncSplashAffect`), `AttackAffect` (`battle.h`), lochy (`AddAffectAll/RemoveAffectAll`), Smocze Kamienie (`SApply::apply_type`, `FindDragonSoulApplyType`), `LogManager::ItemAttrLog`, `GetUniqueApplyWeapon70*`, zestawy kostiumów (`TMt2009PlusSetBonus`), reguły podnoszenia (`SMt2009PlusPickupCond`, do `POINT_MAX_NUM`), funkcje quest/lua (`affect.add`, `affect.remove`, `pc.mount_bonus`, `pc.get_point`, `party.give_buff`, `d.add_affect_all` itd. – liczba z Lua nie jest już obcinana do bajtu), `/remove_affect` | `BYTE` | `WORD` |

Rozmiary (gcc `-m32`, `pack(1)`; `packet.h` ma `static_assert`, exe tak samo): linia bonusu 4 B, `TPlayerItem` 63 B,
GC item set 65 B, item update 52 B, wymiana 65 B, przedmiot sklepu 57 B, podgląd ekwipunku 48 B, filtr wyszukiwania
Ikarus 86 B, zmiana punktu 18 B, efekt (affect) 26 B, usunięcie efektu 7 B, switchbot: alternatywa 20 B, tabela 534 B,
aktualizacja przedmiotu 51 B.

Punkty od 256 w górę (faza 2) idą do klienta same: zmiana punktu (`char.cpp`, warunek „point packet”) i lista punktów
przy logowaniu (`char.cpp`, „login points”) wysyłają każdy numer od `POINT_BLEEDING_REDUCE`+1 do `POINT_WIDE_END`-1 –
exe ma `POINT_MAX_NUM` 512, więc nowy punkt nie wymaga nowego exe.

## Nakładka botów (`linux-port/overlays/playerbot`)

Edytowana wprost (to jej pliki): każda zmienna, parametr i pole, które trzyma typ bonusu albo punkt (ok. 100 miejsc:
`playerbot_bonus.h`, `playerbot_gear.h`, `playerbot_sash.h`, `playerbot_seonhae.h` – zapis bonusu w fladze questa ma
teraz 16 bitów typu, `playerbot_item_extra_apply.h` – bez limitu 255, …). Funkcje, które deklaruje silnik (łatki), a
definiuje nakładka (`Bonus67Total`, `Bonus67AttrValue`, `BonusModeAttrValue`, `ChampionAffectBonus`,
`mt2009_quest_rewards::OnBonus`), biorą `TMt2009PointNum` z `mt2009_wideattr.h`: `WORD` z tą łatką, `BYTE` bez niej –
nakładka buduje się i linkuje w obu przypadkach.

Sprawdzone: wszystkie TU gry i db skompilowane z `-Wconversion` – zero zwężeń `WORD` → `BYTE` w kodzie bonusów (zostały
tylko stare, niezwiązane: komórki ekwipunku, rasa itd.); pełny build db + game (link).

## Baza

`mariadb/playerbot/apply.sh` (`MT2009_PLUS_WIDE_ATTR_V1`, przed końcem migratora): każda kolumna bazowej tabeli, która
trzyma typ bonusu, dostaje `SMALLINT UNSIGNED` – znaleziona przez `information_schema` (więc idempotentnie i z
każdą kopią/backupem): `attrtype0..6` (`player.item`, `player.item_award`, kopie typu `playerbot_yohara_*_bak_item`),
`applytype0..2` (`world.item_proto` i kopie, `item_proto_apply_global/_mt2009`), `player.affect.bApplyOn`,
`world.item_extra_apply.apply_type`, `world.locale_point.point`. Widoki (np. `itemshop3.shop`) idą za tabelami same.
Jeden `ALTER` na tabelę; InnoDB (MariaDB 11.8) nie zmienia typu kolumny w miejscu (INSTANT/NOCOPY/INPLACE odmawiają),
więc to kopia tabeli z `LOCK=SHARED` (odczyty działają, zapisy czekają). Pomiar na kopii świata testowego (1,43 mln
wierszy `player.item`, wartości i suma kontrolna identyczne przed i po): 34–49 s pod obciążeniem; produkcyjny test
(~1,07 mln) ok. 25–35 s. Migrator działa przy zatrzymanych rdzeniach (serwis gry czeka na niego). Drugi przebieg: nic.

## Bramka wersji klienta

Nowy układ pakietów czyta tylko exe z tą zmianą (`client-patches/exe`, `app.MT2009_WIDE_ATTR_EXE`). Root
`constinfo.py` mówi wtedy wersję **1.3.1** (1010301); auth (`linux-port/docker/game/bin/m2-render-config`,
`server_version: ${M2_CLIENT_MIN_VERSION:-1010301}`) odrzuca 1.3.0 i starsze komunikatem „UPDATE” („Wymagana
aktualizacja klienta gry przez Patcher.”) – zanim dotrze do nich pierwszy pakiet przedmiotu. Nowy root na starym exe
mówi dalej 1.3.0 i też jest odrzucany. Serwer, który ma własne `M2_CLIENT_MIN_VERSION` w `.env`, musi je podnieść.

## Faza 2 – jak dodać nowy punkt / bonus

1. `common/length.h`: nowy `POINT_*` **nad** linią `POINT_WIDE_END` (kolejno 256, 257, …; `POINT_MAX_NUM` zostaje 512,
   `playerbot_bonus67.cpp` ma `static_assert`, że `POINT_WIDE_END <= POINT_MAX_NUM`). Działanie punktu – jak w rundach
   1–2 (`char.cpp` „point change”, logika w nakładce).
2. Baza: nazwa `POINT_*` na końcu ENUM `apply` w `world.item_attr` i `world.item_attr_rare` **w tej samej kolejności**
   (pozycja w ENUM = numer punktu; rdzeń db czyta `apply+0`; ENUM ponad 255 nazw działa – sprawdzone, `apply+0` = 257).
   Wiersze puli jak w `bonusy67b_wiki.sql`.
3. Inne mapy nazw (tylko jeśli punkt ma tam być): `skill.cpp` `FindPointType` (skill_proto), `dragon_soul_table.cpp`
   `FindDragonSoulApplyType`, `item.cpp` `Mt2009PlusSetPoint` (zestawy kostiumów), `db/src/ProtoReader.cpp`
   (`item_proto.txt`, przy PROTO_FROM_DB=1 nieużywany), panel `dbeditor/items.py` (nazwy punktów).
4. Klient: `root/localeinfo_point.py` (opis w dymku), `root/uiattributelist.py` (okno bonusów; `player.GetStatus(n)`
   działa dla każdego n < 512 bez nowego exe), stała `player.POINT_*` w exe tylko jeśli C++ jej potrzebuje.
5. Nakładka botów: wagi w `playerbot_bonus.h` / `playerbot_item_tiers.h` (tablice stałych z typem `BYTE` dadzą błąd
   kompilacji „narrowing” dla numeru > 255 – wtedy pole na `WORD`).
6. **Nie** w `item_proto.applytype` przedmiotu, który ma iść do klienta: rekord `item_proto` exe (184 B) trzyma apply
   jako 1 bajt i zostaje bez zmian (panel waliduje 0–255). Nowe bonusy 6/7 to linie przedmiotu (`attrtype`), nie applies
   protu.
