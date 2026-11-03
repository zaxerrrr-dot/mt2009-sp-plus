# Siła ataku potworów

Poprawka silnika (`game/src/char_battle.cpp`, `game/src/questmanager.cpp`),
znacznik `MT2009_PLUS_MOB_ATTACK_V1` (pomysł z konfiguratora serwera:
profile EASY / SAPPHIRE „obrażenia od potworów 80%”), bliźniak `server-patches/mobhp`.

- **Obrażenia zadawane przez potwory jako procent**: flaga zdarzenia
  `m2_mob_attack` (10–300; 0 albo 100 = jak w grze). Ustawia ją migrator z
  `M2_MONSTER_ATTACK` w `.env` (tylko gdy linia się zmieniła od ostatniego
  startu), a panel zaawansowany („Konfiguracja serwera”) i kolejka
  `web_admin` (`MOB_ATTACK`) zmieniają ją od razu.
- Skalowane raz, na początku `CHARACTER::Damage`, gdy zadający jest potworem
  (nie zwierzakiem, nie Metinem, nigdy graczem ani botem): zwykłe ciosy,
  umiejętności, strzały i trucizna. Obrażenia graczy i botów bez zmian.
- Na żywo na każdym rdzeniu (`CQuestManager::SetEventFlag`); w syslogu linia
  `MOB_ATTACK:`.

Stosowanie: `python3 apply_mobattack.py <game/src>` (po `mobhp`, którego
hak w `questmanager.cpp` jest kotwicą). Każdy krok nakłada się raz; brak
oczekiwanego kodu przerywa bez zmian.

## Siła ataku graczy (MT2009_PLUS_PC_ATTACK_V1)

Ta sama poprawka, znacznik `MT2009_PLUS_PC_ATTACK_V1` (konfiguracja serwera
EMERALD: „+10% obrażeń zadawanych przez gracza”).

- **Obrażenia zadawane przez graczy potworom, bossom i Metinom jako procent**:
  flaga `m2_pc_attack` (10–300; 0 albo 100 = jak w grze). Ustawia ją migrator
  z `M2_PLAYER_ATTACK` w `.env` (tylko gdy linia się zmieniła), panel
  zaawansowany i kolejka `web_admin` (`PC_ATTACK`) – od razu.
- Skalowane raz w `CHARACTER::Damage`, zaraz po skali potworów, gdy zadający
  jest postacią gracza (także bot) a trafiony potworem albo Metinem. PvP bez
  zmian (wiki nie wymienia PvP).
- W syslogu linia `PC_ATTACK:`.
