# maleblog – Małe Błogosławieństwo (72351)

Znacznik: `MT2009_PLUS_SMALL_BLESSING_V1` (właściciel, 3.11.2026: kalendarz SAPPHIRE – wtorek 16–20 i czwartek 12–16
„Małe Błogosławieństwo” z Metinów i bossów).

- `char_item.cpp`: `case 72351` obok Błogosławieństwa Przedmiotu 71052 – te same warunki i ta sama zmiana 6. i 7.
  bonusu (`ChangeRareAttribute2`: pula rękawic Seon-Hae, broń Młodych Bohaterów, talizmany), ale tylko z 10% szansą
  (pl-wiki: „Ma 10% szansy na zmianę 6. oraz 7. bonusu”; Ameria `SMALL_ORISON`). Przy nieudanym rzucie bonusy wracają
  do poprzednich, przedmiot się zużywa, a na czacie pojawia się komunikat. Przedmiot, którego zmiana nie obejmuje,
  zachowuje błogosławieństwo (jak przy 71052).
- Przedmiot: `linux-port/docker/mariadb/playerbot/male_blogoslawienstwo.sql` (world.item_proto, `INSERT IGNORE`),
  klient: `client-patches/client-2.0.30/tools/ysapph`.

Kolejność: dowolna (kotwiczy na kodzie `case 71052`, którego nie zmienia żadna inna łatka).

Linux/VPS: `python3 apply_maleblog.py <game/src>`.
