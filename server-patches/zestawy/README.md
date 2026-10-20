# zestawy – zestawy kostiumów jak na globalu

`MT2009_PLUS_COSTUME_SET_V2` (20.10.2026, właściciel: „system zestawów ... musi być dokładnie tak samo jak na globalu
polskim, czyli różne stopnie bonusów i różne bonusy dla danego zestawu. Jeśli jakichś przedmiotów brakuje, np. Amulet
Nazara, to dodaj, z bonusami z wiki”). Źródło: arkusz właściciela `Metin2_Zestawy_kostiumow.xlsx`
(metin2alerts.com/pl/wiki/costumes, odczyt 16.10.2026) → `tools/zestawy/zestawy_wiki.json`. Opis zasad po polsku:
`/opt/metin2/cache/yohara/zestawy-kostiumow.md`.

## Zasady

- 48 zestawów. Zestaw ma 2–6 **części**: kostium, fryzura, nakładka na broń, zwierzak, wierzchowiec,
  pierścień/amulet, szarfa. Każda część to lista wariantów (płeć, kolor) – liczy się dowolny z nich.
- Liczy się to, co założone: kostium, fryzura, nakładka na broń, wierzchowiec (kostium), szarfa, oba sloty
  unikatowe, oraz **przywołany** zwierzak (pieczęć z aktywnym gniazdem i przywołany pet). Ukryty kostium też się liczy.
- **Stopień** = liczba założonych części (2..6). Bonusy stopnia to cały bonus (nie sumuje się z niższymi). Gdy
  pasuje kilka zestawów naraz, działa ten z największą liczbą części.
- Stare linie `costume_sets.txt` (V1: kostium + fryzura), których przedmiotów nie ma w żadnym zestawie z arkusza –
  starsze zestawy bez „+” i 22 zestawy z Arezzo – zostają zestawami dwuczęściowymi z dawnym bonusem +800 PŻ i +15
  wartości ataku (do decyzji właściciela).

## Silnik

| Znacznik | Plik | Co |
|---|---|---|
| `(sets)` | `item.cpp` | Tabela zestawów z linii `#Z` pliku `costume_sets.txt` (czytnik V1 je pomija, boty dalej pytają V1), stare linie jako zestawy dwuczęściowe; `Mt2009PlusCostumeSetDecide`: afekt 545 (niezapisywany) – pierwszy wpis bez punktu z wartością `zestaw × 10 + części` (ikona i dymek w kliencie), potem po wpisie na bonus; flaga `AFF_FIRE_RAGE` (poświata jak w V1). Zmiana stopnia: `RemoveAffect(545)` i nowe wpisy, komunikat na czacie. Szansa na drop nie jest punktem – `Mt2009PlusCostumeSetDropBonus`. Sędzia V1 zostaje pod nazwą `Mt2009PlusCheckCostumeSetV1` (nieużywany). |
| `(hook)` | `item.cpp`, `CItem::ModifyPoints` | Każdy przedmiot zestawu założony (poza `ComputePoints`). |
| `(unequip)` | `item.cpp`, `CItem::Unequip` | Zdjęty – po zwolnieniu slotu (V1 liczył z przedmiotem jeszcze w slocie). |
| `(depth)`, `(computed)` | `char.cpp`, `CHARACTER::ComputePoints` | Licznik zagnieżdżenia; na końcu najbardziej zewnętrznego przeliczenia zestaw jeszcze raz (przywołanie / odwołanie peta, logowanie). W środku przeliczenia nic się nie zakłada – afekt dodany w pętli przedmiotów liczyłby się podwójnie. |
| `(drop)` | `item_manager.cpp`, `ITEM_MANAGER::GetDropPct` | Szansa na drop zestawu dodana jak rękawica złodzieja / premium. |

Punkty: PD = `POINT_RAMADAN_CANDY_BONUS_EXP` (sumuje się, bez limitu 100% bonusów MALL – zestawy dają do +150%),
silny przeciw potworom / bossom / Metinom = `POINT_ATTBONUS_MONSTER / BOSS / STONE`, obrażenia umiejętności / średnie =
`POINT_SKILL_DAMAGE_BONUS / POINT_NORMAL_HIT_DAMAGE_BONUS`, magiczny/krótkodystansowy atak =
`POINT_MELEE_MAGIC_ATT_BONUS_PER`, siła żywiołów = `POINT_ENCHANT_*` (talizmany), 5% obrażeń do PŻ = `POINT_STEAL_HP`,
regeneracja PŻ = `POINT_HP_REGEN`, wartość ataku = `POINT_ATT_GRADE_BONUS / POINT_MAGIC_ATT_GRADE_BONUS`
(tabela w `tools/zestawy/gen_zestawy.py`, `POINTS`).

Nakładane po `playerqol` (zastępuje sędziego V1), na końcu `tools/port/Apply-MT2009PlusEngine.ps1`.
Linux/VPS: `python3 apply_zestawy.py <game/src>`; Windows: `Apply-ZestawyPatch.ps1 -SourceDir <game/src>`.
`gen_edits.py [<game/src>]` tworzy `edits.json` i sprawdza kotwice.

## Dane i klient

- `tools/zestawy/gen_zestawy.py [--xlsx PLIK]`: linie `#Z` w `linux-port/docker/game/costume_sets.txt`,
  `client-patches/client-2.0.30/root/costume_set_bonus.py`, brakujące przedmioty `zestawy_items.sql` (apply.sh), ich
  bonusy w `special_item_group.unique_attr.txt` (blok generowany, grupa specjalna 10051, grupy atrybutów
  100010–100014), `tools/zestawy/zestawy_items.json` dla klienta i ikony GF w `root/icon/item`.
- Dodane przedmioty: Amulet Nazara 71202, Lizak Magii 71188, Czekoladowy Amulet 71199, Mistrzowski Emblemat 70607,
  Błogosławieństwo Mocy 72713 (jak Lizak Potęgi: slot unikatowy, czas rzeczywisty), Szarfa Serca (unikat.) 86064
  (szarfa 4. stopnia jak Rocznicowa Szarfa +3). Źródło: ItemShop (zakładka Wyposażenie, indeksy 60–65,
  `ishop_once zestawy_60`) i sklep WWW – propozycja.
- Klient: `root/uiaffectbar.py` (545: nazwa zestawu, „Założone części zestawu: n/m” i bonusy stopnia),
  `root/uitooltip.py` (przedmiot zestawu: zestaw, części i bonusy każdego stopnia; pierścień wielu zestawów: ich
  nazwy), `tools/zestawy/build_zestawy_packs.py` (item_proto / item_list / itemdesc oraz paczka `gf_zestawy` z
  modelem Szarfy Serca).
- Pazury (Lykan) z arkusza – 40156, 40198, 40205, 40226 – pominięte: nie ma tej klasy.
