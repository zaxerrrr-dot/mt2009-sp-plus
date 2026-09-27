# Podkreślnik w loginie

Serwer logowania przyjmował w loginie tylko litery i cyfry
(`FN_IS_VALID_LOGIN_STRING` w `input_auth.cpp`), a każde konto bota to
`playerbot_NNN`. Bot przejęty z panelu zaawansowanego („Przejmij bota”) odpowiadał
więc na poprawne hasło „nieprawidłowa nazwa użytkownika”, zanim hasło w ogóle
zostało sprawdzone. Teraz podkreślnik `_` jest dozwolonym znakiem loginu.

- `Apply-LoginUnderscorePatch.ps1` – Windows (`tools/port/Apply-MT2009PlusEngine.ps1`);
- `apply_loginunderscore.py` – Linux/VPS, ta sama zmiana i ten sam znacznik
  `MT2009_PLUS_LOGIN_UNDERSCORE_V1`.
