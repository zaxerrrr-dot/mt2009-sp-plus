# Kamienie Duchowe według poziomu trudności

Poprawka silnika (`game/src/char_skill.cpp`, `game/src/questlua_pc.cpp`),
znacznik `MT2009_PLUS_SOUL_STONE_WAIT_V1` (zgłoszenia NerrVoVy, Hiob, sosen).

- **Czekanie między Kamieniami Duchowymi (G1 → P)** jest takie jak między
  księgami (flaga `m2_book_wait`): łatwy - bez czekania, średni - 7 h,
  trudny - 12 h jak w oryginale, własny - godziny ksiąg, **najwyżej 12 h**.
  Dotąd zawsze 12 h.
- Quest z paczki (`training_grandmaster_skill.quest`) dalej zapisuje
  `next_time` na 12 h; silnik w `pc.getqf`/`pc.setqf` przycina tę jedną
  flagę do „teraz + czekanie świata”, więc czekanie już zapisane na postaci
  skraca się przy następnym użyciu kamienia.
- Boty mają swoje czekanie (`m2_bot_book_wait`, też najwyżej 12 h) w
  nakładce `playerbot_config.h` (`GetPlayerBotSoulStoneWaitSeconds`) i
  `playerbot_manager.cpp` (`ManagePlayerBotGrandMasterTraining`).

Stosowanie: `Apply-SoulStoneWaitPatch.ps1 -SourceDirectory <game/src>`
(Windows) albo `python3 apply_soulstonewait.py <game/src>` (Linux/VPS). Każdy
krok nakłada się raz; brak oczekiwanego kodu przerywa bez zmian.
