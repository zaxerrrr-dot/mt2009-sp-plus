# Losowanie poziomu 6. i 7. bonusu

Poprawka silnika (`game/src/item_attribute.cpp`, `CItem::AddRareAttribute` –
Seon-Hae i Zaczarowanie 71051). Znacznik: `MT2009_PLUS_RARE_LEVEL_ROLL_V1`.

- Poziom bonusu (lv1–lv5 z tabeli `world.item_attr_rare`) jest losowany według
  wag z flag `m2_rare_lv1` … `m2_rare_lv5` (panel → Seon-Hae → „Szanse poziomów
  6. i 7. bonusu”, działa od razu). Wszystkie zero = domyślnie 35/30/20/10/5
  (właściciel, 1 października 2026). Wcześniej zawsze wchodził poziom 5.
- Poziom nigdy nie przekracza „maks. poziomu” bonusu dla typu przedmiotu.
- Gdy dla przedmiotu nie zostało nic do dodania, funkcja zwraca błąd zamiast
  czytać poza pustą listą.

Stosowanie: `Apply-RareLevelRollPatch.ps1 -SourceDirectory <game/src>` (Windows)
albo `python3 apply_rarelevelroll.py <game/src>` (Linux/VPS).
