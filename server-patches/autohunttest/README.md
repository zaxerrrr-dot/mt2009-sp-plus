# autohunttest – zgoda serwera na TESTOWE Auto Łowy (Alt+H)

Znacznik: `MT2009_PLUS_AUTOHUNT_TEST_V1` (właściciel, 28.10.2026: „dodaj to jako TESTOWE auto łowy, np. pod Alt+H”).

Testowe Auto Łowy z wgranej paczki „Oto Av” polują same w exe klienta (`client-patches/exe`, `ENABLE_MT2009_AUTOHUNT_TEST`,
`UserInterface/Mt2009AutoHuntTest.cpp`; okno `root/uiautohunt_test.py`). Serwer niczego nie wybiera – wysyłane są tylko
zwykłe pakiety ataku, umiejętności, celu i użycia przedmiotu. Ta poprawka mówi jedynie, czy wolno polować:

- `cmd.cpp`: polecenie `/autohunt_test` (gracz, `POS_DEAD`), za `/autohunt_stop` z `autohuntnorevenge` – **stosować po niej**.
- `cmd_general.cpp` `do_autohunt_test`:
  - `/autohunt_test b` (start i co minutę w trakcie) → `AutoHuntTest on`;
  - flaga eventu `autohunt_test_off` ≠ 0 → `AutoHuntTest off flag` (wyłącza dla wszystkich: `/e autohunt_test_off 1`);
  - flaga `autohunt_test_ticket` ≠ 0 → bez biletu Auto Łowów (afekt 560 albo przedmiot 72800 / 72801, jak zwykłe Auto Łowy)
    `AutoHuntTest off item`;
  - `/autohunt_test d` – zatrzymane (tylko log).
  - postać bez połączenia (bot) nie dostaje nic.

Bez flag test jest dostępny dla wszystkich. Nowych pakietów ani afektów nie ma.

Linux/VPS: `python3 apply_autohunttest.py <game/src>`; Windows: `Apply-AutoHuntTestPatch.ps1 -SourceDir <game/src>`
(na końcu `tools/port/Apply-MT2009PlusEngine.ps1`).
