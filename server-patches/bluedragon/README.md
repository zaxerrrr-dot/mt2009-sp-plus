# Leże Smoka (Beran-Setaou)

Zmiany silnika opisane w `edits.json`, każda z własnym znacznikiem
(`MT2009_PLUS_BLUE_DRAGON_V1 …`). Nakładane raz, przy przygotowaniu wydania
(`tools/port/Apply-MT2009PlusEngine.ps1`); `Apply-BlueDragonPatch.ps1` i
linuksowy bliźniak `apply_bluedragon.py` robią to samo. Loch opisuje
`linux-port/docker/game/quest/blue_dragon_lair.quest`.

| Znacznik | Plik | Co robi |
|---|---|---|
| `MT2009_PLUS_BLUE_DRAGON_V1 (decl)` | `BlueDragon.h` | Deklaracje `BlueDragon_IsBoss` i `BlueDragon_Block`. |
| `MT2009_PLUS_BLUE_DRAGON_V1 (block)` | `BlueDragon.cpp` | `BlueDragon_Block(indeks mapy)`: w instancji mapy 208 (2080000–2089999) liczy żywe kamienie smoka 8031–8034 (jedno przejście po mapie, martwy kamień się nie liczy). Publiczna mapa 208 i inne mapy bez zmian. Do tego tabela czasów odnowienia umiejętności smoka według VID. |
| `MT2009_PLUS_BLUE_DRAGON_V1 (cooldown use)` | `BlueDragon.cpp` | `BlueDragon_StateBattle` bierze czasy odnowienia swojego smoka zamiast jednej statycznej tablicy wspólnej dla wszystkich smoków – dwa lochy naraz nie podbierają sobie ziania i trzęsienia ziemi. |
| `MT2009_PLUS_BLUE_DRAGON_V1 (damage)` | `char_battle.cpp` | `CHARACTER::Damage`: Beran-Setaou (2493) nie przyjmuje obrażeń (`DAMAGE_BLOCK`, jak w odnowionym lochu Owsapa), dopóki w jego instancji stoi którykolwiek z czterech kamieni. |

Liczby smoka i kamieni są w bazie (`mariadb/playerbot/apply.sh`,
`MT2009_PLUS_BLUE_DRAGON_V1`), siła umiejętności w `BlueDragon.lua`
(`linux-port/docker/game/dungeons/BlueDragon.lua`, kopiowany przez Dockerfile).

Zmiana już nałożona (jest jej znacznik) jest pomijana; zmiana, której kodu nie
ma dokładnie raz, przerywa całość, zanim cokolwiek zostanie zapisane. Pliki
zachowują swoje końce linii (CRLF tam, gdzie pasujący kod ma CRLF).
