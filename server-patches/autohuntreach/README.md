# autohuntreach – Auto Łowy nie wybierają celów, do których nie da się dojść

Znacznik: `MT2009_PLUS_AUTOHUNT_REACH_V1` (właściciel, 29.10.2026: „serwer pomija potwory, do których nie da się dojść;
działa od razu także na starym kliencie”).

- `cmd_general.cpp` (`/autohunt_target`, `FAutoHuntTarget::Mt2009PlusOffer`): potwór stojący na terenie, na który
  postać nie może dojść (wyspa, szczyt skały, sąsiednia sala lochu – inna spójna składowa siatki botów), nie jest
  podawany jako cel. Sprawdzenie: `CPlayerBotManager::CanHumanReach` (overlay playerbot, `playerbot_manager.cpp`),
  które pyta `CPlayerBotNavigation` tylko o **już zbudowaną** siatkę mapy – wybór celu nigdy nie buduje siatki
  (4–160 MB na 32-bitowym rdzeniu). Brak siatki albo któryś koniec poza siatką = „nie wiadomo” → cel zostaje jak dotąd.
  Potwór w zasięgu ciosu (≤ 400) zostaje zawsze.
- Koszt: dwa odczyty składowej (O(1)) tylko dla kandydata, który wygrałby ranking.
- Wymaga `server-patches/enginefixes` (`MT2009_PLUS_AUTOHUNT_TRUE_NEAREST_V1`, `Mt2009PlusDistance`); nakładany po nim.

Linux/VPS: `python3 apply_autohuntreach.py <game/src>`; Windows: `Apply-AutoHuntReachPatch.ps1 -SourceDir <game/src>`
(wołane w `tools/port/Apply-MT2009PlusEngine.ps1` po autohuntpass).
