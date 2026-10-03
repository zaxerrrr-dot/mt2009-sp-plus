# Boty w znajomych (3 października)

Zmiana silnika opisana w `edits.json`, ze znacznikiem `MT2009_PLUS_BOT_FRIENDS_V1`:

| Znacznik | Plik | Co robi |
|---|---|---|
| `MT2009_PLUS_BOT_FRIENDS_V1` | `messenger_manager.cpp` | `MessengerManager::RequestToAdd`: zaproszenie do znajomych wysłane botowi nie czeka na okienko „messenger_auth”, którego bot nie ma (jego deskryptor nie wysyła żadnych pakietów) – bot odpowiada od razu (`Mt2009BotFriendRequest`, `playerbot_bot_friends.h`), a odpowiedź idzie tym samym `AuthToAdd`, co „Tak”/„Nie” gracza. |

Dotąd zaproszenie do bota zostawało bez odpowiedzi na zawsze. Teraz bot zwykle przyjmuje
(i odpisuje szeptem), a odmawia tylko bot z wrogiego królestwa z tej części botów, które
walczą z innymi królestwami (suwak KINGDOMPVP), oraz wykrzykiwacz (on nie odpisuje nikomu).
Status online/offline bota na liście daje sam silnik: bot wchodzi do gry przez
`CInputLogin::Entergame` (`MessengerManager::Login`) i wychodzi przez `CHARACTER::Disconnect`
(`Logout`). Usunięcie bota z listy to zwykłe usuwanie znajomego (w obie strony).

## Pliki

- `edits.json` – zmiany (plik, znacznik, stary i nowy kod);
- `Apply-BotFriendsPatch.ps1` – Windows (`tools/port/Apply-MT2009PlusEngine.ps1`);
- `apply_botfriends.py` – Linux/VPS; oba czytają ten sam `edits.json`.

Zmiana już nałożona (jest jej znacznik) jest pomijana; zmiana, której kodu nie
ma dokładnie raz, przerywa całość, zanim cokolwiek zostanie zapisane.
