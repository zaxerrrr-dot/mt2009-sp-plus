# antimagic – Kamienie Antymagii (przebicie odporności na magię, PvP)

Znacznik: `MT2009_PLUS_ANTI_RESIST_MAGIC_V1`. Źródło: paczka „Anti Magic penetrate stone” (`APPLY_ANTI_RESIST_MAGIC`,
changelog 0.1: kamień do zbroi jest biały, 0.2: Sura dostaje połowę). Właściciel, 28 października 2026: „Add the new
soul stones. Drop like all the other stones.”; poprawka tego samego dnia: kamienie działają **tylko w PvP**, boty ich
nie osadzają.

## Przedmioty

| vnum | nazwa | slot | wartość +0…+9 |
|---|---|---|---|
| 28044 + 100·N | Kamień Duszy Antymagii+N | broń (`WEARABLE_WEAPON`) | 5, 8, 12, 17, 25, 30, 35, 40, 45, 50 |
| 28045 + 100·N | Biały Kamień Antymagii+N | zbroja (`WEARABLE_BODY`) | jak wyżej |

Numery paczki na każdym stopniu (nasze inne kamienie mają +6…+9 pod 28g00+k – te zostają przy 28g44 / 28g45, wolne
w `world.item_proto`). Reszta jak nasze kamienie duszy (28043): `ITEM_METIN`, stos 200, flaga 4, ceny 2 500 … 80 000
dla +0…+5, 0 dla +6…+9; `value5` (rodzaj – dwa kamienie jednego rodzaju nie wejdą do jednego przedmiotu) 31 / 32.
`linux-port/docker/mariadb/playerbot/antymagia.sql` (`apply.sh`, INSERT IGNORE), generator
`tools/antimagic/gen_antimagic.py`.

## Punkt i działanie

- `POINT_ANTI_RESIST_MAGIC` = **252** (po `POINT_GLOVE_BASE_ATTR_PCT` 251 z `bonusy67`; `POINT_MAX_NUM` 253, typ
  bonusu to 1 bajt – do 256). W tym silniku apply = punkt: `applytype0` kamieni to 252, a w ENUM `apply` tabel
  `item_attr` / `item_attr_rare` dochodzi `'POINT_ANTI_RESIST_MAGIC'` jako 252. wartość (`apply.sh`, tylko gdy ENUM kończy
  się na 251 nazwach – idempotentnie; żaden wiersz puli go nie używa).
- **Sura**: każdy kamień daje połowę (`PointChange`, jak paczka 0.2) – punkt i linia w oknie postaci to wartość, która
  działa.
- **Walka (tylko PvP)**: umiejętność magiczna gracza (`SKILL_ATTR_TYPE_MAGIC`, `char_skill.cpp`) w innego gracza:
  odporność ofiary na magię = max(0, min(odporność, 100) − Antymagia). Potwory, Metiny i ciosy zwykłe – bez zmian
  (u nas zwykły cios nie liczy odporności na magię).
- Punkt idzie do klienta jako zmiana punktu (`char.cpp (point packet)`; nowy exe ma `POINT_MAX_NUM` 253 –
  `client-patches/exe`, okno postaci: linia „Antymagia”, `player.POINT_RESIST_MAGIC_REDUCTION`); stary exe go pomija.
- Poprawka 3.0.8 (okno bonusów: „Antymagia -415579686%”): zmiana punktu z fazy ładowania (przedmioty liczone przy
  wczytaniu) nie dochodziła do klienta (exe zapisuje ją tylko, gdy ma już postać gracza), a bez kamienia punkt nigdy
  nie przychodził – pusty slot exe czyta się jako jego klucz XOR 0xe73ac1da = -415579686. Teraz `PointsPacket`
  wysyła też punkty spoza pakietu, które klient pokazuje (193-197 Sung Ma %/Precyzja, 252 Antymagia) –
  `char.cpp (login points)` – a `Entergame` woła `PointsPacket` jeszcze raz po wejściu do gry
  (`input_login.cpp (enter points)`).
- GM: `/state` pokazuje `ANTI-MAGIC`.

## Drop – jak każdy kamień duszy

- **Metiny** (`CHARACTER::DetermineDropMetinStone`, `char.cpp (metin stones)`): 16 rodzajów zamiast 14, ta sama szansa
  i te same stopnie (+0…+4 z `aStoneDrop`) dla każdego; podgląd potworów i wiki dropu (`item_manager.cpp (preview
  stones)`) pokazują je tak samo.
- Grupy `Kamien_Duszy_0..4` (10980–10984; a za nimi `Losowy_Kamien_Duszy_*` i każda skrzynia, która je losuje) i
  `ice_witch` (Silna Lodowa Wiedźma, +4 po `1 50 15`) – krok `game/Dockerfile`.
- Pakiet Kamieni Duszy 72058 (`tools/yohara_chestdrops`: wiersze arkusza właściciela, wcześniej pomijane),
  skrzynia Atlantydy `MT2009_chest_30921_dusza5` (+5), bossowie Yohary z arkusza (`tools/ymoby_arkusz`: 6789, 6797,
  6870, 6871 – +4 po 4).
- Mielenie na Gaya (`quest/ygaya.quest`) przyjmuje je jak inne kamienie +0…+3.

## Ulepszanie

+0…+3 jak inne – bez ulepszania (`char_item.cpp (tuning +3)`). +4 → +9 u Kowala tymi samymi recepturami co inne kamienie
(`refine_proto` 7204–7208: Magiczny Pył 8/12/18/25/35 + Olejek Niebios 1/1/2/2/3, 5/10/20/40/80 mln Yang, 50/40/35/30/25 %,
porażka niszczy kamień) – `playerbot_awakening.h` (`StoneVnum` / `StoneGradeKind` znają rodzaje 14 / 15),
`char_item.cpp (tuning +4)`.

## Boty

Nigdy nie osadzają (`GetPlayerBotSoulStoneSeatTier` = 0, `IsPlayerBotAntiMagicSoulStoneKind`), nie ulepszają u Kowala
(`FindPlayerBotSoulStoneStep`), nie kupują pod gniazdo. Kupują i sprzedają jak każdy łup: ceny jak Kamień Duszy
Wojownika (33, kamień PvP) – `playerbot_price_tables.h` (+4 354 713, +5…+9 12,8 mln … 854 mln; +0…+3 cena stopnia),
`IsPlayerBotSoulStoneVnum` przyjmuje rodzaje 44 / 45 (stosy na straganie, pył u Alchemika dla +0…+2 jak każdego
nieosadzanego rodzaju, reguła +4).

## Pliki silnika (`edits.json`, `gen_edits.py [<game/src>]`)

| plik | edycja |
|---|---|
| `common/length.h` | `(point)` – 252, `#define MT2009_PLUS_ANTI_RESIST_MAGIC` |
| `char.cpp` | `(point change)` – połowa dla Sury, `(point packet)`, `(login points)`, `(metin stones)` |
| `input_login.cpp` | `(enter points)` – punkty jeszcze raz po wejściu do gry |
| `char_skill.cpp` | `(magic)` – PvP |
| `item_manager.cpp` | `(preview stones)` |
| `cmd_gm.cpp` | `(state)` |
| `char_item.cpp` | `(tuning +3)`, `(tuning +4)` |
| `ikarus_shop.cpp`, `ikarus_shop_manager.cpp` | `(shop search)`, `(shop search lines)` – wyszukiwarka sklepów |
| `db/src/ProtoReader.cpp` | `(proto reader)` – nazwa `APPLY_ANTI_RESIST_MAGIC` w item_proto.txt |

12 edycji, każda ze swoim znacznikiem; **na końcu**, po `npcloc`. Linux/VPS: `python3 apply_antimagic.py <game/src>`
(kolejność `yohara-deploy.sh`: dopisać `antimagic` za `npcloc`); Windows: `Apply-AntiMagicPatch.ps1`
(`tools/port/Apply-MT2009PlusEngine.ps1`, na końcu). `playerbot_bonus67.cpp` sprawdza 252 / 253 (`static_assert`).

## Klient

- exe (`client-patches/exe`, `ENABLE_MT2009_ANTI_RESIST_MAGIC`): `Server/common/length.h` `POINT_ANTI_RESIST_MAGIC` 252,
  `POINT_MAX_NUM` 253 (zawsze – rozmiar tablic punktów musi być wszędzie ten sam), `item.APPLY_ANTI_RESIST_MAGIC`,
  `player.POINT_ANTI_RESIST_MAGIC` / `player.POINT_RESIST_MAGIC_REDUCTION`, `app.ANTI_RESIST_MAGIC_BONUS`.
- root: `localeinfo_point.py` (linia dymka „Ignoruje %d%% odporności na magię (PvP)” – `uitooltip.py` bierze nazwy
  bonusów stamtąd), `offlineshopsearch.py` (wyszukiwarka: +0…+4), ikony `icon/item/28044.tga`, `28045.tga` (z paczki).
- dane: `client-patches/client-2.0.30/tools/antimagic` (`build_antimagic_packs.py`, `verify_antimagic.py`) – item_proto,
  item_list, itemdesc w paczkach gamedata / dbdata.
