# Moby Yohary wg arkusza właściciela – `MT2009_PLUS_MOBY_ARKUSZ_V1`

Arkusz właściciela z 20.10.2026 (`Metin2_Moby_statystyki_EXP_i_drop.xlsx`: HP, EXP, EXP SungMa, statystyki, odporności,
żywioły, listy „Łup” bez szans) porównany z naszymi potworami Yohary (wiersze `mariadb/playerbot/yohara_*.sql` i
`shipdefense.sql`). Pełne porównanie (także potwory sprzed Yohary – do decyzji właściciela):
`/opt/metin2/cache/yohara/porownanie-moby.md`. Generator: `tools/ymoby_arkusz/gen_ymoby_arkusz.py`, decyzje:
`tools/ymoby_arkusz/ymoby_data.py`.

## Statystyki
- Obrona Statku: oficjalne poziomy (3953 → 105, 3956–3959 → 110, Hydra 3960–3964 → 120, Jajo Hydry 20432 → 120) –
  wcześniej obniżone „na oko” do 90–110 (`shipdefense.sql`).
- EXP: SZC: Wojownik En-Tai 4267 → 41 001, SZC: Uzdrowiciel En-Tai 4270 → 61 350, Bojownik En-Tai 6402 → 28 934
  (arkusz = Owsap; wcześniej liczby z pl-wiki) – `tools/yohara_crack`, `tools/yohara_zaklety`.
- Alastor 6790 / 6791: 22 587 258 HP (było 67 751 800 / 48 751 800), 6790 regeneracja co 30 s – `tools/yohara_maps3`.
- Świat sprzed zmiany: `mariadb/playerbot/yohara_moby_arkusz.sql` (UPDATE tylko wiersza ze starą wartością; apply.sh).
- Bez zmian (decyzje): żywioły Yohary wg pl-wiki (właściciel 14.10), NOMOVE figur Wieży Sung Mahi (quest), EXP potworów
  Meley (pl-wiki; arkusz 0 – do decyzji), regeneracja Drewna na Naprawę 20437.

## Drop
`mob_drop_item.yohara_arkusz.txt` – przedmioty z list arkusza, których nasze potwory Yohary nie miały (171 potworów,
1322 wiersze), grupy `MT2009_yarkusz_<mob>` typu drop (silnik dokleja je do własnych grup potwora). Nasze wiersze
zostają. Vnumy oficjalne → nasze (`tools/yohara_chestdrops` SUBST, ymoby_data); pominięte: przedmioty, których nie
mamy (Lykan, Księgi Misji, Eliksiry SungMa, …), przedmioty zadań lochów, Spróchniała Skrzynia; bez dropu zostają
Szczelina Czasu (404) i Skarb Hydry. Szanse **tymczasowe** (arkusz ich nie podaje): mediana tego samego przedmiotu
u naszych potworów Yohary tego samego rodzaju (zwykły / boss / Metin), inaczej innego rodzaju (z limitem), inaczej
domyślna wg rodzaju przedmiotu. Wartość v w pliku = v/4 % na zabicie przed różnicą poziomów i bonusami dropu.
Dockerfile: krok `MT2009_PLUS_MOBY_ARKUSZ_V1` (po wszystkich krokach Yohary, przed wycięciem 50124).
