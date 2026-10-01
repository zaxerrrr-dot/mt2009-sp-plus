# Migawka encji bez zwolnionych postaci (1 października)

Zmiany silnika opisane w `edits.json`, każda z własnym znacznikiem
`MT2009_PLUS_ENTITY_SNAPSHOT_V1`:

| Znacznik | Plik | Co robi |
|---|---|---|
| `MT2009_PLUS_ENTITY_SNAPSHOT_V1 (collector)` | `sectree.h` | `FCollectEntity` (migawka, po której chodzą `ForEachAround` i `SECTREE_MAP::for_each`) zapamiętuje przy każdej postaci jej VID i przed wywołaniem funkcji pomija postać, której menedżer postaci już nie ma pod tym VID-em. |
| `MT2009_PLUS_ENTITY_SNAPSHOT_V1 (check)` | `sectree.cpp` | Sprawdzenie: wpis VID → wskaźnik w `CHARACTER_MANAGER` (porównywany jest tylko wskaźnik, zwolniona pamięć nie jest czytana). Przedmioty i obiekty – bez zmian. |

## Dlaczego

Rdzeń ch1-game2 (lochy Arezzo) padał co kilka minut (SIGSEGV, skok w
`typeinfo name for CMemoryTextFileLoader`). Zrzut pamięci pokazał:
`CHARACTER_MANAGER::Update` → `UpdateStateMachine` → `CFSM::Update` na
postaci już zwolnionej (vptr = `vtable for CEntity`, pusta nazwa).

Przebieg: umiejętność obszarowa (np. Uderzenie Ducha, 107) bije po kolei
potwory z migawki. Jeden ginie, jego zabicie odpala wyzwalacz questa
(`9697.kill` itd.), który przy końcu fali woła `d.purge_area()` – reszta fali
zostaje natychmiast zniszczona i zwolniona, ale wciąż jest w migawce.
`FuncSplashDamage` bił dalej w zwolnioną pamięć (w logu: `CRUSH! … ->  (…)`
z pustą nazwą), `BeginFight` → `SetNextStatePulse` wpisywał martwy wskaźnik z
powrotem na listę stanów, a kilka sekund później `Update` wołał na nim
maszynę stanów. Dotyczy to też prawdziwych graczy, nie tylko botów.

## Pliki

- `edits.json` – zmiany (plik, znacznik, stary i nowy kod);
- `Apply-EntitySnapshotPatch.ps1` – Windows (`tools/port/Apply-MT2009PlusEngine.ps1`);
- `apply_entitysnapshot.py` – Linux/VPS; oba czytają ten sam `edits.json`.

Zmiana już nałożona (jest jej znacznik) jest pomijana; zmiana, której kodu nie
ma dokładnie raz, przerywa całość, zanim cokolwiek zostanie zapisane.
