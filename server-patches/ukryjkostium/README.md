# Ukrywanie kostiumu, fryzury, wizerunku broni i szarfy

System Owsapa v6.2.6 `__HIDE_COSTUME_SYSTEM__` (Autor: Owsap) zamiast naszego „Ukryj kostiumy”
(`MT2009_PLUS_COSTUME_HIDE_V1/V2`, server-patches/playerqol) – oczko nad każdym polem okna kostiumów, teraz także nad
szarfą. Znacznik: `MT2009_PLUS_HIDE_COSTUME_V1 (…)`, makro `ENABLE_HIDE_COSTUME_SYSTEM`. Po playerqol i transmutacji.

| Część | Miejsce |
|---|---|
| Logika | `linux-port/overlays/playerbot/src/game/src/playerbot_hidecostume.cpp` |
| Haki silnika | `edits.json` (7 zmian: CommonDefines.h, char.cpp – części w pakietach dodania i zmiany postaci, input_login.cpp, cmd_general.cpp, cmd.cpp); `apply_ukryjkostium.py`, `Apply-UkryjkostiumPatch.ps1` |
| Klient | root: `uicostumehide.py` (przepisany), `uiinventory.py` (okno kostiumów), `game.py`; obrazki oczek z klienta Owsapa w `client-patches/client-2.0.30/atlas` |

- Każda część osobno, zapisana na serwerze **dla każdej postaci** w flagach questów Owsapa
  (`costume_option.hide_body`, `hide_hair`, `hide_acce`, `hide_weapon`). Klient: `/hide_costume_part <podtyp> <0|1>`
  (0 kostium, 1 fryzura, 3 szarfa, 4 wizerunek broni); serwer: `SetHiddenCostumePart <podtyp> <0|1>` (też po
  każdym logowaniu). Zasady Owsapa: trzeba stać, jedna zmiana na 3 s.
- Kostium zostaje założony i daje bonusy; zmienia się tylko to, co widać (u wszystkich i u siebie): ukryty kostium –
  zbroja pod nim (w jej wyglądzie z transmutacji) albo własne ciało, fryzura – własne włosy, wizerunek broni – broń,
  szarfa – brak szarfy. Prawdziwe części postaci się nie zmieniają (tylko pakiety).
- **Przeniesienie starych ustawień**: stary klient trzymał maskę w `autohunt/kostiumy.cfg` (wspólną dla wszystkich
  postaci). Nowy klient po każdym wejściu wysyła ją raz starą komendą `/kostiumy_ukryj m <maska>`; serwer przyjmuje
  ją tylko dla postaci, która jeszcze nic nie wybrała oczkami (`costume_option.migrated`). Stary kod maski już nie działa.
- „Ukryj cudze” (`MT2009_PLUS_COSTUME_VIEW_OTHERS_V1`, przycisk pod oknem kostiumów) zostaje bez zmian i działa po
  ukrywaniu (podmienia części dla jednego widza).
