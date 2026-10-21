# Yohara – Jaskinie Gnolli i Wieża Sung Mahi (MT2009_PLUS_YOHARA_DUNG4_V1)

Decyzja właściciela 14.10.2026 (`cache/yohara/decyzje.md`): „Jaskinie Gnolli 1/2/3 i Wieża Sung Mahi – dodać”,
wszystko wg pl-wiki, czego brak – wg wiki TR. Pliki tego katalogu robią `tools/yohara_dung4/gen_ydung4_maps.py`
(mapy, grupy, `spawned.txt`) i `tools/yohara_dung4/gen_yitems_d4.py` (drop, skrzynie); wiersze potworów –
`tools/yohara_dung4/gen_ydung4_sql.py` (`mariadb/playerbot/yohara_dung4.sql`, żywioły `yohara_dung4_zywioly.sql`),
przedmioty – `yohara_items_d4.sql`. Rdzeń: Yohara (game3). Klient: `client-patches/client-2.0.30/tools/ydung4`.

| indeks | miejsce | folder (GF/Owsap) | rodzaj | spawny |
|---|---|---|---|---|
| 382 | Jaskinie Gnolli (pierwszy poziom) | metin2_map_maze_dungeon1 (3×3) | mapa (`jaskinie_gnolli`) | punkty Owsapa, potwory wg wiki |
| 383 | Jaskinie Gnolli (drugi poziom) | metin2_map_maze_dungeon2 (3×3) | mapa | jw. |
| 384 | Jaskinie Gnolli (trzeci poziom) | metin2_map_maze_dungeon3 (3×3) | mapa | jw. |
| 386 | Wieża Sung Mahi – hala | metin2_map_smhdungeon_01 (1×1) | mapa | NPC z punktów GF |
| 387 | Wieża Sung Mahi | metin2_map_smhdungeon_02 (2×2) | loch (`wieza_sung_mahi`) | quest |

**Baza wieży**: GF ma 947200 614400 – u nas to Komnata Wiedzy (`plechito_chamber_of_wisdom`), a klient rozpoznaje
mapę po bazie. Wieża stoi na **998400 614400** (wolne w każdej naszej mapie, każdym worktree i w kliencie GF) – serwer
(`Setting.txt`) i klient (`setting.txt`, `atlasinfo.txt`) mówią to samo.

## Jaskinie Gnolli
- Wejście: Halabardnik (20836) w Dongan (990,973) – od 1. Poziomu Czempiona, jedna Przepustka (71095 / 71130) za
  wejście. Labirynt portali GOTO wg punktów klienta GF (10901–10924, 10931–10954, 10961–10984; nazwy = cele, Owsap).
  Odcinek 2 (20838) i Odcinek 3 (20839) prowadzą niżej bez powrotu; Wyjście (20837) i Dongan (20840) – do Dongan.
- Potwory poziomów wg wiki (grupy 9230–9244 na 245–255 punktach Owsapa – jego grupy nie wystawiały Ahtrinów 2. poziomu
  ani Szpiega/Wiedźmina/Komendanta 3.), bossowie na punktach Owsapa co 1 h / 2 h / 3 h (TR), żywioły wg wiki.
- Drop wg wiki (Talizmany Woli, płyty, Róg Trolla, Twarda Skóra, Wzór Rękawicy, Ziemne Pnącze, Żółty Lśniący
  Odłamek; bossowie – skrzynie: Mistrza Gnolli, Mistrza Ahtrina, Zdobiona Złotem ×3, Labiryntowa – zawsze).
- Śmierć: po wstaniu powrót do Dongan. Panel lochów: `gnolle` (Ahtrin Wielki Mistrz (mrok)).

## Wieża Sung Mahi
- Wejście Piekielnej Wieży (4019) w Seoganland (76,1459) → hala; w hali portal 4020: wybór odblokowanego piętra,
  Sztandar Czaszki (70401) za wspinaczkę, sam lub z drużyną; Wyjście (10126) do Seoganland.
- 50 pięter × 3 etapy (sale i punkty z questów Amerii): fale; jedna z 7 misji wiki; fale + boss (Wóżbit, co 5. piętro
  Wielki Mistrz, co 10. Książę/Czarnoksiężnik); co 20 s gałęzie z ziemi (podwójne obrażenia na 10., 20. … piętrze);
  żywioł piętra po kolei, co 10. wszystkie; losowy bonus/klątwa na każdy etap (afekty 1847/1849, łatka
  `server-patches/wiezasm`); Wola SungMa piętra (`d.set_sungma`, nakładka `playerbot_champion.cpp`).
- Handlarka (9014) w hali: mikstury wieży 70390–70395 po 50 i 200 sztuk, ceny wiki (sklep 9552 w
  `yohara_items_d4.sql`, `MT2009_PLUS_SMH_SHOP_V1`); działają tylko w wieży (387) – łatka `server-patches/wiezasm`.
- Nagrody pięter z tabeli wiki raz na sezon (miesiąc); odblokowanie i czasy – też na sezon. Potwory wieży nie dają
  doświadczenia czempiona (wiki: 0). Panel lochów: `wieza_smh`.

Uproszczenia: brak zakazu innych przedmiotów w wieży, Skrzynki Pocztowej, rankingu
sezonu ze skrzyniami; z nagród pominięte Małe Błogosławieństwo, Błogosławieństwo, Spirala Czasu, Akcja Piekielnej
Wieży (brak systemów); łucznicy budzą się, gdy kamień straci PŻ; Niszczyciele wybuchają, gdy padną; w jaskiniach brak
zakazu zwojów/pierścieni teleportu. Gałęzie i klątwa ranią przez `d.zone_attack`/`d.zone_hurt`
(`server-patches/strefy`, gałąź claude/yohara-mech), a bez nich – „3 s w tym samym miejscu”, nigdy do zera PŻ.
