# Bonusy PD i dropu, limity bonusów, datek PD dla gildii – `MT2009_PLUS_PD_BONUS_V1`

Lista właściciela z 3.11.2026 (Yohara 3.0.7, sekcja A) i punkt 6 z `poprawki-3.0.8.md`. Silnik: `edits.json`
(`gen_edits.py [<game/src>]` tworzy go i sprawdza kotwice; `apply_pdbonus.py <game/src>` – Linux/VPS,
`Apply-PdBonusPatch.ps1` – Windows). Nakłada się **po `ringfx`** (ostatnia na liście). Nakładka:
`mt2009_attrmax.cpp`, `playerbot_champion.cpp`. Dane: `linux-port/docker/game/Dockerfile` (39002 w grupie 10000).
Klient: `client-patches/client-2.0.30/root` – `uiattributelist.py`, `localeinfo_point.py`, `uitooltip.py`, `game.py`,
`uiaffectbar.py`.

## 1. Bonus PD przedmiotów (okno bonusów pokazywało PD 0%)

Jak było (sprawdzone w kodzie):

| przedmiot | jak dawał PD | działało? | okno „PD” |
|---|---|---|---|
| Mikstura Mądrości (71153, 71155), Pierścień Doświadczenia 71015 | efekt `POINT_MALL_EXPBONUS` (116) +50/+100 | tak, `GiveExp`: `rateFactor += 116` | tak |
| Pierścień Doświadczenia (unikat, grupa 10000: 72001–72003, 72049, 72050, 70005) | stałe `rateFactor += 50` w `GiveExp`, gdy `IsEquipUniqueGroup(10000)` | tak | **0%** (żaden punkt) |
| Pierścień Doświadczenia z Metinów map 90 (39002) | nic – nie był w grupie 10000 ani w grupie bonusów | **nie** | 0% |
| Lizak Potęgi, Lizak Magii, Czekoladowy Amulet, Amulet Nazara, Medal Bohatera, pierścienie IS, Amulet Wiecznej Miłości | grupy bonusów `special_item_group` (100000–100014): punkt **127** `POINT_RAMADAN_CANDY_BONUS_EXP` +30/+50 | tak (`rateFactor += 127`) | **0%** (okno czytało tylko 116) |
| Set kostiumowy (`costume_sets.txt`, `MT2009_PLUS_COSTUME_SET_V2`) | punkt 127 +50…+150 | tak | **0%** |
| Czempion (pasek Sung Ma, `playerbot_champion.cpp`) | tylko 116 | pierścienie, lizaki, amulety i sety **nie** | – |

Teraz:

- `item.cpp` (`unique points`): założony pierścień z grupy 10000 daje **+50 do punktu 127** (jak lizaki, amulety i sety),
  `char_battle.cpp` (`ring rate`, `ring old formula`): stałe +50 usunięte – suma bez zmian, ale jest w punkcie.
- Dockerfile: 39002 dopisany do grupy 10000 (kolejny numer wiersza) – daje +50% i nie da się go założyć z drugim
  Pierścieniem Doświadczenia (jak każdy pierścień z tej grupy).
- Czempion: pasek Sung Ma liczy też punkt 127.
- Klient (`uiattributelist.py`): wiersz **PD** = 116 + 127 – wszystkie bonusy PD naraz, dokładnie to, co `GiveExp` dodaje
  do mnożnika (jak raty serwera: wszystko sumuje się w jednym mnożniku).

## 2. Rękawica Złodzieja

- Unikat (grupa 10002: 70043, 72004, 72005, 72006): +100% szansy dropu działało (`GetDropPct`), ale stałą liczbą – okno
  „Szansa Dropu” (`POINT_MALL_ITEMBONUS`) pokazywało 0. Teraz rękawica daje **+100 do punktu 117** (`item.cpp`), a
  `GetDropPct` (`drop`) bierze punkt; 72006 („punktowa”) dalej tylko na Metiny, bossy i mini-bossy (na zwykłym potworze
  jej +100 odpada).
- Rękawica Złodzieja z IS (71016, 76037; efekt 117 +50) **nie robiła nic** – żaden kod nie czytał `POINT_MALL_ITEMBONUS`.
  Teraz +50% szansy dropu. Yang – rękawica nigdy nie dawała (opis mówi o przedmiotach).
- `char.cpp` (`item bonus cap`, `item bonus sum`): punkt 117 sumuje się bez stropu 100 (rękawica 100 + mikstura-rękawica
  50); strop obcinał dodawaną wartość, a przy zdjęciu odejmował całą – punkt „pływał” w dół.

## 3. Złote wyróżnienie maksymalnych bonusów wg limitów świata

Było: stała tabela klienta (`ATTR_MAX_VALUES`, dwa zestawy mt2009/global), jedna wartość na bonus (np. maks. PE 250
na każdym przedmiocie). Teraz serwer przy każdym logowaniu wysyła (`mt2009_attrmax.cpp`, `input_login.cpp`):

```
AttrMaxBegin <liczba zestawów>
AttrMax <0|1> <bonus>:<maks. broń>/<zbroja>/<bransoleta>/<buty>/<naszyjnik>/<hełm>/<tarcza>/<kolczyki>/<kostium>/<fryzura>/<kostium broni>/<talizman>/<rękawice> ...
AttrMaxEnd
```

– `0` = `item_attr` (bonusy 1–5), `1` = `item_attr_rare` (6/7), wartość = `lValues[min(5, maks. poziom zestawu) - 1]`
tak jak losuje `CItem::AddAttr` / `AddRareAttribute` / Seon-Hae, z talizmanem trybu global (5% na poziom), czyli to, co
gra wczytała z bazy – tryb bonusów i edytor panelu (po restarcie gry) w cenie. Klient (`localeinfo_point.IsMaxAttrValue`)
dobiera zestaw po typie przedmiotu (jak `GetAttributeSetIndex`); szarfa i bonus spoza zestawu – najwyższa wartość ze
wszystkich zestawów; bez tabeli z serwera (stary serwer) – stara tabela.

## 4. Medal Szczęścia / Rękawica Złodzieja (IS) – opis

Efekt `POINT_MALL_GOLDBONUS` / `POINT_MALL_ITEMBONUS` +50 to mnożnik ×1,5 szansy; tekst „pomnożona o %.1f” dostawał samo
50 („x50.0”). `localeinfo_point.GetApplyString` i pasek efektów (`uiaffectbar.py`) pokazują teraz „Szansa na zdobycie
Yang x1.5” / „Szansa na zdobycie przedmiotów x1.5”.

## 5. Datek PD dla gildii na 120 poziomie

`CGuild::OfferExp` sprawdza PD i woła `PointChange(POINT_EXP, -x)`, a ta na najwyższym poziomie z pełnym paskiem
(`MT2009_PLUS_CHAMPION_V1`: pasek staje punkt przed końcem) wracała od razu – gildia dostawała PD, postać nic nie traciła,
w kółko. `char.cpp` (`exp given away`): odejmowane PD zawsze schodzą z paska (poniżej 120 – bez zmian). Ta sama dziura
dotyczyła czytania ksiąg umiejętności i kary PD za śmierć na 120 poziomie z pełnym paskiem – też już kosztują.

## 6. `POINT_ERROR type 114 val 65 (max 50)`

Punkt 114 = `POINT_MALL_ATTBONUS` („Wartość ataku +%”). Postacie z syserr (Kordyl133, ZOOMv3, devlogspammer, primax123)
noszą broń Młodych Bohaterów (Requiem, Zabójca Króla – stała linia +50) i piją Atak Boga Smoków (+15/+20) albo mają
efekt Bossa Świata – 65–70 zgodnie z zasadami. `GetLimitPoint` logował błąd powyżej 50 przy każdym ciosie (setki linii
na sekundę), choć `PointChange` sam pilnuje stropu 100. Próg błędu = 100 (`mall att error`); w ciosie liczy się dalej
`limit = 20` (bez zmiany balansu – do decyzji właściciela).
