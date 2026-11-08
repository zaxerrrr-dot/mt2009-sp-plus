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
szarfy się nosi i łączy u Theowahdana, handel działa.

## Skąd flagi

- `.env`: `M2_ALCHEMY=1/0`, `M2_SASHES=1/0` (domyślnie 1). Migracja startowa
  (`mariadb/playerbot/apply.sh`) zapisuje je tylko wtedy, gdy `.env` zmienił
  się od ostatniego startu (`m2_rare_env`), więc ustawienie z panelu zostaje
  po restarcie.
- Panel admina, strona „Alchemia i szarfy” (`/rare`): zmiana od razu, przez
  pomocnika w grze (`web_admin.quest`, polecenie `RARE`).

## Odłamki u Alchemika: szansa i limit dzienny

Dwie kolejne flagi świata czyta `dragon_soul.quest` (i boty,
`playerbot_alchemy.h`):

- `ds_drop` – szansa na Odłamek Smoczego Kamienia z potwora w procentach
  (1–100, poza zakresem 10);
- ile Cor Draconis dziennie powstaje z odłamków (Moc Smoczego Oka) – od
  8 listopada 2026 według poziomu postaci (`MT2009_PLUS_DS_COR_LEVEL_V1`;
  dolna granica włącznie): 30–44 → 10, 45–54 → 15, 55–74 → 20, 75–94 → 25,
  95–109 → 30, 110–120 → 35; Czempion (120 i Poziom Czempiona ≥ 1):
  1–9 → 45, 10–19 → 60, 20–30 → 80. Awans do wyższego progu w ciągu dnia
  dodaje różnicę, nigdy nie odejmuje. Pierwszy Cor za 10 odłamków oddanych
  Alchemikowi wlicza się do pierwszego dnia;
- `ds_cor_level_off` – 1 wyłącza tabelę: wszyscy dostają stałe `ds_cor_day`
  (1–20, poza zakresem 5), jak przed 8 listopada.

Dzień to doba czasu polskiego (Europe/Warsaw, z czasem letnim). Moc odnawia
się sama po północy – przy logowaniu, przy pierwszym zabitym potworze albo
podniesionym odłamku nowego dnia, przy awansie albo z listu misji; rozmowa
z Alchemikiem dalej też odnawia. Raz na dobę (`dragon_soul.eye_timestamp`
= dzień, `eye_tz` = 1 – dzień polski; stary znacznik bez `eye_tz` to doba
UTC i obowiązuje do jej końca, więc przejście nie daje drugiej puli ani nie
zabiera dnia). Boty: `playerbot.ds_day` / `ds_tz` / `ds_grant` tak samo.

Migracja startowa wpisuje domyślne wartości tylko raz (`INSERT IGNORE`);
zmienia je panel (strona „Alchemia i szarfy”, od razu, polecenie `RARE`
z drugim argumentem `szansa,limit,tabela_wyl`) albo GM komendą
`/e ds_drop N`, `/e ds_cor_day N`, `/e ds_cor_level_off 1`.
