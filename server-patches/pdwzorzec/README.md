# pdwzorzec – PD jak we wzorcu: tabela różnicy poziomów i bonus grupy

Znacznik: `MT2009_PLUS_EXP_REFERENCE_V1`. Decyzja właściciela z 7.11.2026 po analizie
`dist/aktualizacje/test-plus/ANALIZA-EXP-ZAKLETY-LAS-2026-11-07.md` (punkty L1 i S1). Cały serwer.

## Zmiana (`edits.json`, `gen_edits.py`)

| Plik | Znacznik | Co |
|---|---|---|
| `constants.cpp` | `(delta table)` | `aiPercentExperienceByDeltaLev`: potwór wyżej od gracza daje jak we wzorcu (+5% za poziom, 180% przy +15); stara tabela zostaje jako `aiPercentExperienceByDeltaLevOld` |
| `char_battle.cpp` | `(old table)`, `(delta switch)` | `GiveExp`: flaga wydarzenia `exp_reference_off` = 1 bierze starą tabelę (bez budowania) |
| `party.cpp` | `(include)`, `(party bonus)` | `CParty::GetExpBonusPercent`: bonus grupy także przy podziale „według poziomu” (domyślnym); `exp_reference_off` = 1 przywraca 0 w tym trybie |

### Różnica poziomów (potwór wyżej od gracza), %

| różnica | +1 | +2 | +3 | +4 | +5 | +6 | +7 | +8 | +9 | +10 | +11 | +12 | +13 | +14 | +15 i więcej |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| było | 102 | 105 | 108 | 111 | 114 | 117 | 120 | 123 | 126 | 130 | 133 | 136 | 139 | 142 | 145 |
| jest | 105 | 110 | 115 | 120 | 125 | 130 | 135 | 140 | 145 | 150 | 155 | 160 | 165 | 170 | 180 |

Potwór niżej od gracza (98, 96, 94, 92, 90, 85, 80, 70, 50, 30, 20, 10, 5, 1) – bez zmian, identycznie jak we wzorcu.

### Bonus grupy (osoby w pobliżu), %

| osób | 2 | 3 | 4 | 5 | 6 | 7 | 8 |
|---|---|---|---|---|---|---|---|
| „równo” (było i jest) | 12 | 18 | 26 | 40 | 53 | 70 | 100 |
| „według poziomu” było | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| „według poziomu” jest | 12 | 18 | 26 | 40 | 53 | 70 | 100 |

Do tego jak dotąd w obu trybach: +5% po 60 minutach grupy, +30% gdy w grupie są wszystkie klasy, +30% z pierścienia
lidera (unikalne przedmioty bonusu grupy). Tabela `CHN_aiPartyBonusExpPercentByMemberCount` jest ta sama co we wzorcu.

## Przełącznik

`exp_reference_off` (flaga wydarzenia, `/e exp_reference_off 1` lub panel) = 1: stara tabela różnicy poziomów i 0%
bonusu grupy przy podziale „według poziomu”. Domyślnie 0 (brak flagi) – wartości wzorca.

## Wdrożenie

`python3 apply_pdwzorzec.py <game/src>` – na końcu listy łatek `yohara-deploy.sh` (po `botneeddrop`). Edycja już
nałożona jest pomijana (drugi przebieg: „0 edit(s) applied”); edycja, której stary kod nie występuje dokładnie raz,
zatrzymuje całość, zanim cokolwiek zostanie zapisane.

## Baza (ta sama zmiana, `MT2009_PLUS_EXP_REFERENCE_V1`)

`linux-port/docker/mariadb/playerbot/drop307.sql`, krok 6: PD ×2 dla potworów, które żyją tylko w Zaklętym Lesie
(353) i Erebu – 6401–6404, 6406, 6407, 6408, 6192, 6409, 6410–6414, 8059, 8061. Tylko nad wartościami z pakietu
(`yohara_zaklety.sql`), więc wartość z edytora bazy zostaje. Poza tym: Strażnik En-Tai 6400 (Świątynia Ochao), SZC
4260–4272 / 4403, wiersze Bossa Świata.
