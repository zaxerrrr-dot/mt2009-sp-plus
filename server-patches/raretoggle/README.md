# Przełączniki alchemii i szarf

Poprawka silnika `game/src/item_manager.cpp` (`ITEM_MANAGER::CreateDropItem`)
i `game/src/char_item.cpp` (skrzynia bossa otwierana kluczem), znacznik
`MT2009_PLUS_RARE_TOGGLE_V1`. Nakładana raz, przy przygotowaniu wydania
(`tools/port/Apply-MT2009PlusEngine.ps1`), po `rarelevel`;
`Apply-RareTogglePatch.ps1` i linuksowy bliźniak `apply_raretoggle.py` robią
to samo.

## Co robi

Dwie flagi świata (`player.quest`, `dwPID` 0):

- `m2_alchemy_off` = 1 – żaden Metin ani boss nie daje Cor Draconis;
  `dragon_soul.quest` nie daje Odłamków Smoczego Kamienia, Alchemik nie
  wymienia ich na Cory i nie wysyła listu na 30 poziomie.
- `m2_sash_off` = 1 – żaden boss ani skrzynia bossa nie daje szarfy.

To, co gracze już mają, zostaje: kamienie w plecaku alchemii działają,
szarfy się nosi i łączy u Uriela, handel działa.

## Skąd flagi

- `.env`: `M2_ALCHEMY=1/0`, `M2_SASHES=1/0` (domyślnie 1). Migracja startowa
  (`mariadb/playerbot/apply.sh`) zapisuje je tylko wtedy, gdy `.env` zmienił
  się od ostatniego startu (`m2_rare_env`), więc ustawienie z panelu zostaje
  po restarcie.
- Panel admina, strona „Alchemia i szarfy” (`/rare`): zmiana od razu, przez
  pomocnika w grze (`web_admin.quest`, polecenie `RARE`).
