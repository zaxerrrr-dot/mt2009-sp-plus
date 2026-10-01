# Zasięg ciosu na wierzchowcu i przy dużym bossie (MT2009_PLUS_MOUNT_REACH_V1)

Zgłoszenie właściciela (1 października 2026): wojownik z bronią dwuręczną na wierzchowcu
trafiał Razadora tylko przez chwilę, potem przez kilka sekund wcale - i tak na zmianę.

Przyczyna: zwykły cios jest sprawdzany dwa razy. `CHARACTER::Attack` (char_battle.cpp)
pozwala jeźdźcowi sięgnąć na 900 (`ATTACK_MELEE_HORSE_MAX_DISTANCE`), ale zaraz potem
`battle_melee_attack` (battle.cpp) bez słowa odrzucał każdy cios dalszy niż 405 - także
jeźdźcowi. Gracz na wierzchowcu stoi dalej, a Razador ma duże ciało: ciosy wchodziły tylko
wtedy, gdy boss podszedł blisko.

Poprawka:
- `battle_melee_attack`: jeździec sięga do 600 (nie 405);
- przy bossie i królu (`MOB_RANK_BOSS` i wyżej) gracz ma +250 zasięgu w obu sprawdzeniach
  (ciało bossa jest duże, zasięg liczy się od jego krawędzi).

Pliki: `battle.cpp`, `char_battle.cpp`. Znacznik: `MT2009_PLUS_MOUNT_REACH_V1`.

- `Apply-MountReachPatch.ps1 -SourceDirectory <game/src>` - Windows (Apply-MT2009PlusEngine.ps1);
- `apply_mountreach.py <game/src>` - to samo na Linuksie/VPS.

Obie wersje zmieniają pliki tylko raz; gdy nie znajdą oczekiwanego kodu, przerywają bez zmian.
