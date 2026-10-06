# Zmiana bonusów (bonus switcher)

Poprawka silnika, znacznik `MT2009_PLUS_BONUS_SWITCH_V1` (każda zmiana ma własny dopisek w nawiasie).
**Autor: Vekirion** (paczka „VekirionAiO_v3”, 6 października 2026 – z niej wzięty tylko bonus
switcher i poprawka mgły; 60+ FPS i info o bonusach pod nazwą moba nie wchodzą tą drogą).
Nakładana raz, przy przygotowaniu wydania (`tools/port/Apply-MT2009PlusEngine.ps1`, po
`vekirion`); `Apply-BonusSwitchPatch.ps1` i linuksowy bliźniak `apply_bonusswitch.py` czytają ten
sam `edits.json`. Zmienione pliki: `cmd.cpp`, `cmd_general.cpp` (oba już na liście
`launcher/server-update-files.mod.txt`). Cała logika jest w nakładce
`linux-port/overlays/playerbot/src/game/src/playerbot_bonus_switch.h` (dołączona w
`playerbot_manager.cpp`).

## Co robi

| Dopisek | Gdzie | Co |
|---|---|---|
| `(declare)` | `cmd.cpp`, po Seon-Hae | `ACMD(do_bonus_switch);` |
| `(table)` | `cmd.cpp`, tabela komend | `/bonus_switch` dla graczy (`GM_PLAYER`, `POS_DEAD`). |
| `(command)` | `cmd_general.cpp` | `do_bonus_switch` przekazuje argumenty do `BonusSwitchCommand` (nakładka). |

Gracz otwiera okno „Zmiana bonusów” (przycisk na pasku obok ekwipunku albo własny klawisz
w ustawieniach klawiszy – domyślnie brak). Pięć pól = pięć przedmiotów naraz (broń, zbroja/biżuteria
z ekwipunku albo kostium). Wybiera bonusy, które przedmiot może wylosować, i ich minimalne wartości
(„Wszystkie” albo „Co najmniej X z”), szybkość 1–20 zmian/s i „Start”; „Zmień raz” robi jedną zmianę
po potwierdzeniu.

Koszt jak przy ręcznym użyciu: **1 zmiana = 1 przedmiot**. Najpierw zużywane są 76014
(„Zaczarowanie Przedmiotu (B)”, z jego tabelą szans), potem 71084, 71284, 39028. Kostiumy: 70063
(Transformuj kostium), gdy brakuje bonusów, potem 70064 (Zaczaruj kostium); nieudane losowanie
kostiumu przywraca bonusy i nie zużywa przedmiotu (jak w `char_item.cpp`). Każda zmiana trafia do
logu przedmiotów jak ręczna (`CHANGE_ATTRIBUTE`, `*_COSTUME_ATTR_*`).

Flagi zdarzeń: `m2_bonus_switch_off 1` blokuje nowe starty, `m2_bonus_switch_max` – górna szybkość
(0 = 20, najwyżej 50).

## Bezpieczeństwo (przegląd)

- Zamiana dzieje się tylko na serwerze; klient wysyła numer pola i wybrane cele. Przedmiot musi być
  w zwykłym ekwipunku gracza (`GetOwner() == ch`, okno `INVENTORY`, pole < `INVENTORY_MAX_NUM`),
  nie założony, nie w handlu, nie zablokowany, nie w trakcie zmiany; obrączki/przedmioty ślubne
  odrzucone; broń/zbroja musi już mieć bonusy (jak przy ręcznym użyciu).
- Każdy cel sprawdzany: bonus musi być w zestawie przedmiotu (`world.item_attr`), wartość ≤ maksimum,
  bez powtórzeń, najwyżej 5 celów, „co najmniej” w zakresie.
- Bieg zatrzymuje się sam przy osiągnięciu celu, braku przedmiotów, przesunięciu/zablokowaniu
  przedmiotu, otwarciu handlu/sklepu/magazynu/kostki, śmierci, wylogowaniu i teleporcie (co tick
  sprawdzane jest ID przedmiotu w polu).
- Tempo: najwyżej 20 (flaga do 50) zmian na sekundę, najwyżej 5 biegów na gracza, `start`/`once`
  /`items` co najmniej 150 ms odstępu, do tego zwykły limit komend silnika (10 na 500 ms).
- Boty nigdy: każda komenda i każdy tick wymaga prawdziwego deskryptora (`!IsBot()`).
- Uwaga: `info`/`start` co najwyżej raz na 2 s (globalnie) czytają `world.item_attr` prosto z bazy i
  podmieniają tabelę bonusów rdzenia, gdy się zmieniła (zmiany w tabeli działają bez `/reload`).
