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
