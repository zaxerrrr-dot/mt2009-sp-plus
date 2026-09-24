# Zadanie dla agenta klienta: Cor Draconis w stosach (łączenie i dzielenie)

Zgłoszenie po kliencie 2.0.11 / serwerze 2.4.1: Corów Draconis (50255) z dropu
nie da się połączyć (przeciągnięcie na drugi Cor) ani podzielić (Shift +
klik), choć `/i 50255 20` daje normalny stos 20.

## To nie serwer

- Proto serwera: 50255 `flag = 4` (STACKABLE), `antiflag = 16512`
  (DROP | PKDROP – **bez** ANTI_STACK), `stack = 200`.
- Serwer łączy Cory: w syslogu serwera testowego bot robi
  `ITEM_STACK Cor Draconis (Rough) ... count 1`.
- Dodatkowo `server-patches/corstack` (`IsStackableCorDraconisVnum`) pozwala
  w `MoveItem` łączyć i dzielić Cory nawet przy ANTI_STACK.
- Przy próbach gracza w syslogu nie ma żadnego `ITEM_MOVE` / `ITEM_STACK` –
  **klient w ogóle nie wysyła** ruchu na drugi Cor ani okna podziału.

## Przyczyna w kliencie

Klient decyduje o łączeniu (przeciągnięcie na ten sam przedmiot) i o oknie
podziału stosu z **własnego** `item_proto` (flaga `ITEM_FLAG_STACKABLE`,
antyflaga `ITEM_ANTIFLAG_STACK`). W danych klienta Cor ma najpewniej
ANTI_STACK albo nie ma STACKABLE. Nasza poprawka `client-patches/autohunt-trade/
ItemManager.cpp.patch` (`IsTradeableCorOrSash`) zdejmuje dla Corów tylko
GIVE i MYSHOP.

## Poprawka

W `GameLib/ItemManager.cpp`, `CItemManager::LoadItemTable`, obok istniejącego:

```cpp
if (IsTradeableCorOrSash(dwVnum))
    table->dwAntiFlags &= ~(ITEM_ANTIFLAG_GIVE | ITEM_ANTIFLAG_MYSHOP);
```

dodaj **tylko dla Corów** (nie szarf – szarfy się nie stackują):

```cpp
if (IsCorDraconisVnum(dwVnum))   // lista Corów z IsTradeableCorOrSash:
{                                // 50252, 50255-50260, 51501-51510, 51541, 51548,
    table->dwAntiFlags &= ~ITEM_ANTIFLAG_STACK;      // 51549, 51562, 51569, 51576,
    table->dwFlags |= ITEM_FLAG_STACKABLE;           // 51583, 51590, 51597, 51604,
}                                                    // 51611, 51618, 51625, 51632, 76040
```

(wydziel listę Corów z `IsTradeableCorOrSash` do `IsCorDraconisVnum` i użyj
jej w obu miejscach). Sprawdź też w Pythonie (`uiInventory.py`, obsługa
Shift + klik i upuszczenia na ten sam przedmiot), czy nie ma osobnego
wykluczenia Corów / typu 23 (`ITEM_SPECIAL_DS`) – jeśli jest, zdejmij je dla
Corów.

## Test

1. Zabij dwa Metiny albo weź `/i 50255` dwa razy (dwa osobne Cory po 1).
2. Przeciągnij jeden Cor na drugi – powstaje stos 2 (w syslogu serwera
   `ITEM_STACK`).
3. Shift + klik na stos – okno podziału, oddzielenie 1 szt. działa.
4. Stos 20 z `/i 50255 20` – podział działa.

Wchodzi do następnej pełnej (kumulatywnej) paczki klienta (2.0.12).
