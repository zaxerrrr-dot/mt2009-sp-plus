# energia – System Energii (Yohara 3.x, MT2009_PLUS_ENERGY_V1)

Prośba właściciela (5 listopada 2026): „Wprowadź aby było 1:1 jak na Wiki” – pl-wiki „System Energii”,
„Kryształ Energii”, „Odłamek Energii” (en-wiki „Energy System”, „Energy Crystal” uzupełniają).

## Jak na wiki

- **Odłamki Energii (51001)** – u Alchemika (20001) już były (`quest/energia_alchemik.quest`, `MT2009_PLUS_BELTS_V1`,
  bez zmian): przedmiot od 35 poziomu (broń bez strzał, zbroja, biżuteria) przeciągnięty na NPC przez gracza od 35
  poziomu rozkłada się na 0–15 odłamków; im wyższy poziom przedmiotu, tym więcej (oficjalne tabele 35–50 / 51–70 / 71+).
- **Kryształ Energii (51002)** – nowy `quest/energia_krysztal.quest` u Alchemika („Złóż Kryształ Energii”):
  30 Odłamków Energii + 1 000 Yang, od 35 poziomu; pierwszy kryształ postaci zawsze się udaje, każdy następny w 30%
  (oficjalny `energy_system.quest`). Nieudana próba zabiera odłamki i Yang (wiki).
- **Działanie** – użycie kryształu (prawy przycisk myszy) podnosi bonusy ekwipunku o 1, 3, 5, 7 lub 10% (wartość
  kryształu, losowana przy jego powstaniu: 5/10/45/25/15% – `blend_item.cpp`, `FN_ECS_random_index`) na **2 godziny gry**
  – czas płynie tylko w grze (jak każdy efekt). Kryształy o tej samej wartości łączą się w stos (do 200), inne nie.
  Ponowne użycie: silniejszy kryształ zastępuje słabszy, ten sam odnawia czas, słabszy jest odrzucany
  (`MiksturyMayRefresh`, jak przy innych miksturach).
- **Pasek energii** przy pasku zadań (klient): niebieski – energia, żółty – mniej niż 15% czasu (ok. 18 min), czarny –
  brak; podpowiedź „Energia: bonusy ekwipunku +X% (pozostało …)”.

„Bonusy ekwipunku” = bonusy (atrybuty) przedmiotów założonych jako zbroja, hełm, buty, bransoleta, broń, naszyjnik,
kolczyki, tarcza i rękawice – zsumowane wg rodzaju, każda suma × procent (oficjalne `CBuffOnAttributes` energii, z
rękawicami jak w źródłach Yohary). Stałe bonusy z `item_proto` przedmiotu nie rosną (jak na oficjalnym serwerze).
Linie „1./2./3./4./5. dodany bonus +x%” same nie rosną – energia liczy podniesione nimi wartości.

## Silnik (`edits.json`, generator `gen_edits.py`, nakładka `energia.cpp`)

Silnik miał tylko resztki systemu (`POINT_ENERGY` 128, `g_aBuffOnAttrPoints`, pusta `m_map_buff_on_attrs`, bez
`buff_on_attributes.cpp`): `POINT_ENERGY` był „unknown point change type”, a `blend.txt` miał dla 51002
`apply_type ENERGY` (czytane jako liczba = 0) i 1800 s.

| Znacznik | Plik | Co robi |
|---|---|---|
| `MT2009_PLUS_ENERGY_V1 (member)` | `char.h` | `m_mapMt2009EnergyApplied` – co energia dodała do punktów (punkt → wartość). |
| `MT2009_PLUS_ENERGY_V1 (compute)` | `char.cpp` | `ComputePoints` zeruje punkty, więc i tę mapę; `RefreshAffect` daje energię ponownie po przedmiotach. |
| `MT2009_PLUS_ENERGY_V1 (point change)` | `char.cpp` | `PointChange(POINT_ENERGY)`: punkt zapisany, wysłany do klienta (pasek), bonusy przeliczone (`Mt2009EnergyRefresh`). |
| `MT2009_PLUS_ENERGY_V1 (equip)` / `(unequip)` | `item.cpp` | Założenie / zdjęcie przedmiotu przelicza udział energii. |
| `MT2009_PLUS_ENERGY_V1 (crystal)` | `char_item.cpp` | Kryształ 51002 zawsze `POINT_ENERGY` na 7200 s (także kryształ zrobiony przed poprawką `blend.txt`). |

`energia.cpp` (`linux-port/overlays/playerbot/src/game/src`): `Mt2009EnergyRefresh` odbiera to, co dał poprzednio, i
daje udział przedmiotów założonych teraz – można go wołać zawsze (brak podwójnego liczenia).

- `apply_energia.py <game/src>` – Linux/VPS; `Apply-EnergiaPatch.ps1` – Windows (`tools/port/Apply-MT2009PlusEngine.ps1`);
  oba czytają ten sam `edits.json`. Po `ysets`, `mikstury`, `wideattr` – na końcu listy. Przy wdrożeniu dopisać `energia`
  na końcu listy łatek skryptu wdrożenia (po `sesja`). Zmiana `char.h` = pełna przebudowa rdzenia.

## Dane

- `Dockerfile` (share): sekcja 51002 w `blend.txt` – `apply_type 128`, `apply_duration 7200` dla każdej wartości
  (wartości 1 3 5 7 10 bez zmian). Quest `energia_krysztal` kompilowany w obrazie jak inne (lista questów).
- `item_proto` bez zmian (51002: typ 27 BLEND, stos 200, wszystkie handle dozwolone, poziom 35; 51001 bez zmian) – bez SQL.
- Klient: nowa paczka `energia` (4 obrazki paska z klienta GF 26.1.11 = te same bajty co w paczce właściciela) i root
  (`interfacemodule.py` – pasek zawsze, exe ma `ENABLE_ENERGY_SYSTEM 0`, ale `player.ENERGY` / `ENERGY_END_TIME` wypełnia
  bez definicji; `uitaskbar.py` – podpowiedź i kolor co sekundę; `uitooltip.py` – „Bonusy ekwipunku +X%” w opisie
  kryształu) – `client-patches/client-2.0.30/tools/energia`. Exe bez zmian.

## Poza zakresem

- Inne źródła kryształu z wiki („Skrzynka na Ozdoby”) – takiej skrzynki nie ma w naszej bazie.
- Boty (od 10 listopada 2026, `MT2009_PLUS_BOT_ENERGY_CRYSTALS_V1`, `playerbot_energy_crystals.h`): rozkładają u
  Alchemika złom, którego oczekiwane odłamki są warte więcej niż płaci handlarz; składają kryształy jak w queście
  (30 odłamków + 1 000 Yang, pierwszy pewny, potem 30%); od 35 poziomu używają kryształu w polowaniu, gdy energia nie
  działa; trzymają rezerwę (flaga `m2_bot_energy_reserve_h`, 4 h = 2 kryształy), nadwyżkę kryształów i odłamków
  wystawiają na rynek. Flagi i spis – nagłówek pliku.
- Paczka właściciela (francuska) to nieoficjalna wersja na flagach questa (losowy bonus zamiast energii, `cmdchat`,
  `mysql_query`, flaga zdarzenia „energy”) – przeniesione są tylko obrazki paska; zasady są oficjalne.
