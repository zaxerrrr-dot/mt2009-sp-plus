# Szata Aury (system szat aury)

`MT2009_PLUS_AURA_V1` (15.10.2026, właściciel: „Dodajemy cały system szaty aury”). Zasady z pl-wiki („System Szat
Aury”, „Szaty Aury”, „Zwyczajna … Promienista Szata Aury”, „Lodowa / Ognista Runa Aury”, „Świadectwo Aury+”,
„Theowahdan”), liczby i przebieg z Owsapa v6.2.6 (`__AURA_COSTUME_SYSTEM__`, `char_aura.cpp`, `constants.cpp`,
`root/uiaura.py`). Makro silnika: `ENABLE_AURA_COSTUME_SYSTEM`.

## Projekt (krótko)

- **Miejsce na szatę**: `WEAR_COSTUME_AURA` = 27 (pierwsze wolne za `WEAR_GLOVE` 26; `WEAR_MAX` 32 bez zmian),
  podtyp `COSTUME_AURA` = 5 (oficjalny). Okno kostiumów klienta: trzecia ramka dolnego rzędu (obok wierzchowca i
  szarfy), z oczkiem „Ukryj szatę aury”.
- **Przedmioty**: oficjalne vnumy szat 49001–49006 to u nas nakładki Władcy Śmierci, więc szaty mają **49101–49106**
  (rodzaj = vnum − 49100, jak `vnum % 10` u Owsapa). Runy i świadectwo – oficjalne 49990–49995, 89999.
- **Gniazda szaty** (Owsap): `socket0` – vnum przedmiotu, z którego przeniesiono parametry (0: brak), `socket1` –
  `(1000 + poziom) * 100000 + doświadczenie`; nowa szata (`socket1` = 0) to pierwszy poziom swojego rodzaju.
- **Bonusy**: założona szata daje `poziom / 10 %` (poziom 250 – 25%) bonusów pochłoniętego przedmiotu: jego
  `item_proto` (bez szybkości ruchu), nasze dodatkowe linie `item_extra_apply`, obronę tarczy oraz wszystkie 7
  przeniesionych bonusów (atrybuty); linia poniżej 1 zaokrąglana w górę do 1 (Owsap). `CItem::ModifyPoints` oddaje
  szatę `Mt2009AuraModifyPoints` i nic więcej z nią nie robi.
- **Okna u Theowahdana bez nowych pakietów** (jak Transmutacja): komendy czatu, okno w pythonie
  (`root/uiaura.py`), serwer sprawdza wszystko jeszcze raz przy „accept” po id przedmiotów.
  - klient → `/aura in <pole> <komórka>` (0 szata, 1 drugi przedmiot), `/aura out <pole>`, `/aura accept`, `/aura cancel`
  - serwer → `AURA open <typ>` (0 przenoszenie, 1 ulepszanie, 2 rozwój), `AURA set <pole> <komórka> <vnum> <ilość>`,
    `AURA del <pole>`, `AURA close`, `AURA done`
- **Wygląd u innych**: `AURA view <vid> <vnum>` (0: brak) – gdy postać wchodzi w pole widzenia (`EncodeInsertPacket`)
  i gdy jej szata się zmienia (`UpdatePacket`, tylko raz na zmianę; postać bez szaty nic nie wysyła). Efekt rysuje
  exe 3.0 (`chrmgr.SetAura`, `client-patches/exe`, `ENABLE_MT2009_AURA`); stary exe go pomija, protokół bez zmian.
  Ukryta szata (oczko, flaga `costume_option.hide_aura`) albo polimorfia – brak efektu; „Ukryj cudze” chowa cudze
  szaty u klienta.

## Zasady (pl-wiki) i ich wykonanie

| Wiki | U nas |
|---|---|
| Szata zakładana jak szarfa | własne miejsce kostiumu 27, bez limitu poziomu |
| Przenieś parametry (Theowahdan, okno: szata + bransoleta / naszyjnik / kolczyki / tarcza, przedmiot znika) | okno 0; szata bez przeniesionych parametrów; kopiowane wszystkie bonusy, `socket0` = vnum |
| Świadectwo Aury+ usuwa parametry | 89999 przeciągnięte na szatę w ekwipunku: bonusy i `socket0` czyszczone, poziom zostaje |
| Ulepszanie runami (Lodowa 1, Ogniste 10/50/100/250/500 PD) | okno 1; runy po kolei aż do szczytu rodzaju, zabierane tylko użyte |
| Poziom: 1000 / 2000 / 4000 / 8000 / 16000 PD | jak u Owsapa (Zwyczajna … Wytworna) |
| Rozwój na 49/99/149/199/249: Agat x10 5 mln, Prosty KC x10 5 mln, Ładny KC x10 5 mln, Wspaniały KC x10 8 mln, Wspaniały KC x20 10 mln; zawsze się udaje, +1 poziom | okno 2; nowa szata (vnum + 1), bonusy i `socket0` zachowane, poziom + 1; materiał liczony z całego ekwipunku |
| Stopień absorpcji zależy od poziomu | `poziom / 10 %` (Owsap) |
| Wytwarzanie u Baek-Go: Ładny KC, 200 Odłamków Energii, Wyjątkowy Barwnik, 25 mln, 20% | quest `szata_aury` (20018 „Szata Aury”) |
| Zwyczajna … Wytworna bez handlu, Promienista handlowa | `antiflag` jak u Owsapa |
| Lodowa Runa Aury – „Drop alternatywny” (wszystkie potwory) | 1–3 szt., flaga zdarzeń `aura_rune_drop` (promile; 0 = 30, < 0 wyłączone), potwór najwyżej 15 poziomów niżej od gracza (boty nie) |
| Ogniste Runy (10/50/100) | już wypadają (Yohara, `yohara_items2.sql`); 250/500 – tylko przedmioty (brak skrzyń z wiki: Pudło Chaosu SungMa, Pudełko Uszlachetniania Aury) |
| Item-Shop: Zwyczajna Szata Aury 650 SM | ItemShop w grze (indeks 952) i sklep www |
| Świadectwo Aury+ – Aukcja Błyskawiczna | ItemShop 50 SM (indeks 953; cena nasza) |
| Wygląd: „bańka” rośnie z rodzajem, Promienista – skrzydełka | efekty GF `d:/ymir work/pc/common/effect/aura/aura_*.mse` |

Transmutacji szat aury oficjalnie nie ma – tu też nie.

## Gdzie co jest

| Część | Miejsce |
|---|---|
| Logika | `linux-port/overlays/playerbot/src/game/src/playerbot_aura.cpp`; oczko: `playerbot_hidecostume.cpp` (`HIDE_AURA`, `Mt2009HideCostumeIsHidden`) |
| Haki silnika | `edits.json` (13 zmian, `gen_edits.py [<game/src>]` je pisze i sprawdza kotwice): `CommonDefines.h`, `length.h`, `item_length.h`, `item.cpp` (miejsce, punkty), `char_item.cpp` (zakładanie, Świadectwo), `char.cpp` (wejście w widok, `UpdatePacket`), `char_battle.cpp` (runa z potworów), `questlua.cpp`, `cmd.cpp` |
| Baza | `linux-port/docker/mariadb/playerbot/szata_aury.sql` (`tools/aura/gen_aura_sql.py`, `apply.sh`, idempotentny) + ItemShop (`ishop_once aura_952`) |
| Quest | `linux-port/docker/game/quest/szata_aury.quest` (Theowahdan: trzy opcje, Baek-Go: wytwarzanie); `game.open_aura` w liście funkcji Dockerfile |
| Klient | root: `uiaura.py`, `uiscript/aura_absorbwindow.py`, `uiscript/aura_levelupwindow.py`, `uiinventory.py` + `uiscript/costumewindow.py` (miejsce, oczko), `uicostumehide.py`, `uitooltip.py`, `game.py`; efekty i ikony GF; dane: `client-2.0.30/tools/aura/patch_aura_client.py`; exe: `client-patches/exe` (`Mt2009Aura.cpp`) |

**Kolejność**: po `transmutacja`, `ukryjkostium` (kotwice i oczko), `rankpoints`, `rekawice`. Linux/VPS:
`python3 apply_aura.py <game/src>`; Windows: `Apply-AuraPatch.ps1 -SourceDir <game/src>` (krok
`tools/port/Apply-MT2009PlusEngine.ps1`). db bez zmian (tylko game; `szata_aury.sql` przed startem rdzeni – inaczej
przedmiotów 49101+ nie ma w `item_proto`).
