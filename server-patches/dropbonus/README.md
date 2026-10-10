# Szansa na bonusy w wydropionej broni i zbroi – `MT2009_PLUS_DROP_BONUS_PCT_V1`

## Co daje

Nowe ustawienie w „Poziomie trudności” obu paneli: procent szansy z gry na bonusy w broni i zbroi (także biżuterii,
butach, hełmach i tarczach) wypadających z potworów. 100% = jak w grze, zakres 10–1000%. Działa na żywo (flaga
zdarzenia `m2_drop_bonus_pct`) i zostaje po restarcie (wiersz w `player.quest`).

## Jak

- `item_manager.cpp`:
  - `SetDropRarePct` (pytana przez każdy drop z potwora tuż przed `CreateItem`) zostawia procent z flagi;
  - `CreateItem` go zabiera: szansa na pierwszy bonus × procent; zwykły potwór (w grze bez bonusów – tylko Metiny,
    bossowie i wodzowie) powyżej 100% dostaje szansę z tabeli przedmiotu × nadwyżka (200% = tyle, ile w tabeli).
- `item.cpp` (`AlterToMagicItem`): szansa na drugi i trzeci bonus × procent (najwyżej 100%), tylko przy dropie.
- Sklepy, questy, skrzynie, ItemShop – bez zmian (nie pytają `SetDropRarePct`). Wartości bonusów bez zmian.

`Apply-DropBonusPatch.ps1` – Windows (`tools/port/Apply-MT2009PlusEngine.ps1`); `apply_dropbonus.py <game/src>` – Linux/VPS;
oba czytają ten sam `edits.json`.

## Sprawdzenie

Panel → Poziom trudności → „Bonusy w dropie” 1000% → zwykłe potwory dropią broń/zbroję z bonusami; 10% – prawie bez.
Wartość: flaga `m2_drop_bonus_pct` w `player.quest` (`dwPID=0`).
