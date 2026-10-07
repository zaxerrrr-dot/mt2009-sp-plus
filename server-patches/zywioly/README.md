# Żywioły i talizmany – `MT2009_PLUS_ELEMENTS_V1`

**Autor: Digi Rasta** (paczka „nowy-system” 0.28.0, karta `SYSTEMY/zywioly-talizmany.md`). Przeniesione do MT2009 PLUS
jako nasz kod, z **zasadami właściciela z 7.10.2026** w miejscu części decyzji z karty (niżej). Silnik tutaj
(`edits.json`, praca w `linux-port/overlays/playerbot/src/game/src/playerbot_elements.cpp`), dane serwera w
`linux-port/docker/mariadb/playerbot/zywioly_*.sql` (generatory w `tools/zywioly/`), quest `zywioly`, klient w
`client-patches`.

## Co daje graczowi

- **Talizman żywiołu** (Ognia 94000–94200, Błyskawicy 94250–94450, Lodu 94500–94700, Wiatru 94750–94950, Ziemi
  95000–95200, Mroku 95250–95450): pole „Talizman” w ekwipunku (WEAR_PENDANT 25, pod naszyjnikiem), wszystkie klasy;
  +0…+200, każdy poziom = **+1% Siły swojego żywiołu**; wymagany poziom gracza 20/40/60/80/100 dla +0/+40/+80/+120/+160.
- **Siła żywiołu** (wzór z wiki jak u Digi Rasty): przeciw potworowi tego żywiołu pierwszy 1% = +18% obrażeń, każdy
  kolejny +0,5%, strop 80% (przy +125); każde pełne 10% = +1% obrażeń przeciw wszystkiemu (max +20%) – tak jak on to
  zrobił, więc także w PvP, gdzie samego bonusu żywiołu nie ma (gracz nie ma żywiołu). Zwykłe ataki, strzały, umiejętności.
- **Odporność na żywioł** gracza (istniejące 6 punktów, bez zmian w przedmiotach) zmniejsza obrażenia od potwora tego
  żywiołu (strop 80%) – jak u niego.
- **Własne 5 losowych bonusów talizmanu** (Wzmocnienie/Zaczarowanie przedmiotu): tylko kolumna `item_attr.pendant` –
  Złamanie odporności na broń 1–5%, Silny p. Insektom/Potworom Pustyni 6–30%, Silny p. Ludziom do 3%, Odporność na
  ludzi 2–10%, Omdlenie do 8%, Odporność na żywioły 5–25%.
- **Ulepszanie u Kowala** do +200: 10× Kwiat Żywiołu + Ornament (30031) + Talizman +0 tego żywiołu + opłata
  (280 tys. … 20,95 mln za krok), 100% – razem ok. 2 mld Yang.
- **Kwiat Żywiołu** (95500): Mistrz (20082, przy Kowalu w M1/M3) – „Kwiaty Żywiołu” (sklep 9550, 100 000 Yang) i
  „Żywioły i talizmany” (opis), quest `zywioly`.
- **Źródła talizmanów +0**: boss (ranga ≥ boss) swojego żywiołu 5%, Metin swojego żywiołu 2% (wg zasad właściciela
  żaden Metin nie ma żywiołu – ta ścieżka jest martwa), Skrzynia Razadora – Talizman Ognia 25%, Skrzynia Nemere –
  Talizman Lodu 25% (`special_item_group.dungeons.txt`, pozycja 9).
- **Znak żywiołu przy celu** (nowy exe, `ENABLE_ELEMENTAL_TARGET`) i nazwa części / bonusy w dymku (root).

## Zasady właściciela (7.10) zamiast karty Digi Rasty

1. Brak odporności na żywioły (ani niczego) w losowych bonusach bransolet, hełmów, zbroi i innych przedmiotów; żywiołów
   nie ma na biżuterii; istniejące dane bonusów bez zmian – nowe wiersze `item_attr` mają wszystkie kolumny poza
   `pendant` = 0, a w istniejących (Silny p. Ludziom, Omdlenie) zmienia się tylko `pendant`.
2. Żywioły potworów (bity 11–16 `setRaceFlag`) zamiast jego listy 253 mobów – `tools/zywioly/gen_zywioly_moby.py`:
   - wszyscy bossowie (ranga ≥ 4) z jego listy z wiki (`tools/zywioly/zywioly_wiki.json`) – żywioł z wiki;
   - zwykłe potwory tylko na mapach: Grota Wygnańców 1/2 (72, 73) – Błyskawica; Świątynia Ochao (209) i Zaczarowany
     Las (362) – Wiatr (wszystkie vnumy z regen/boss/stone mapy, grupy i grupy grup rozwinięte, przywołania; bez
     Metinów i NPC); boss bez wpisu w wiki dostaje żywioł mapy;
   - lochy – wszystkie potwory i bossowie (pliki mapy, `data/dungeon/<katalog>`, vnumy ≥ 1000 z questu, przywołania),
     żywioł lochu wygrywa z wiki: Nemere (352) – Lód, Leże Smoka (208, Błękitny Smok / Beran-Setaou) – Błyskawica,
     Starożytna Dżungla (366) – Wiatr;
   - reszta (także Metiny) bez żywiołu – SQL zdejmuje bity 11–16 z każdego innego moba (m.in. wojska Czarnego Wiatru).
     Bitów 11–16 nic innego w silniku, overlayu, questach, panelu i kliencie nie używa (sprawdzone 7.10; klient:
     `mobraceflag.py` maskuje 0–10, `uitarget.py` – ikona żywiołu).
   - vnum ma żywioł wszędzie, gdzie się pojawia (raport generatora wypisuje takie miejsca).
3. PvP bez żywiołów (jak u niego).
4. Boty (`MT2009_PLUS_BOT_TALISMANS_V1`, `playerbot_talismans.h`, zmiana z 7.10): zakładają talizman, który na mapie,
   na której polują, daje największy oczekiwany bonus wg wzoru z `ElementsAttackBonus` (bonus ogólny + udział potworów
   żywiołu na mapie × bonus żywiołu), i ulepszają go u Kowala (część botów od 30 poziomu); na mapie z dominującym
   żywiołem ulepszają talizman tego żywiołu, aż przegoni noszony. Kwiaty kupują u Mistrza, Ornament i Talizman +0 na
   rynku (700 000); część botów dostaje talizman +0 i materiały 10 kroków (flaga zdarzenia `m2_bot_craft_seed_off`
   wyłącza dary, `m2_bot_workshop_off` całe zadanie).

## Zmiana silnika (`edits.json`)

| Znacznik | Plik | Co robi |
|---|---|---|
| `(points)` | `common/length.h` | `POINT_PACKET_NUM` (178) i `POINT_ENCHANT_ELECT…DARK` = 178…183 przed `POINT_MAX_NUM`; `#define MT2009_PLUS_ELEMENTS_V1` |
| `(points packet)` | `packet.h` | `TPacketGCPoints.points[POINT_PACKET_NUM]` – pakiet bez zmian (exe: 178) |
| `(points packet loop)`, `(no point packet)`, `(point change)` | `char.cpp` | pakiet punktów i zmiany punktu tylko do 177; `PointChange` zna nowe punkty |
| `(damage)` | `battle.cpp` | `CalcAttBonus` → `ElementsAttackBonus` (siła, bonus ogólny, odporność; syslog `ZYWIOLY:` dla GM) |
| `(state)` | `cmd_gm.cpp` | `/state` pokazuje `ENCHANT:` |
| `(talisman drop)` | `char_battle.cpp` | drop talizmanu +0 z bossa/Metinu żywiołu obok dropu przebudzenia |
| `(refine declare/count/remove [scroll])` | `char_item.cpp` | `DoRefine` i `DoRefineWithScroll`: materiał o vnumie ulepszanego przedmiotu liczony i zdejmowany z pominięciem samego przedmiotu |

- `Apply-ZywiolyPatch.ps1` – Windows (`tools/port/Apply-MT2009PlusEngine.ps1`, ostatni z patchy);
- `apply_zywioly.py <game/src>` – Linux/VPS; oba czytają ten sam `edits.json` (kolejność ma znaczenie: najpierw para
  `scroll`, potem zwykła ścieżka – wtedy jej kod jest jedyny).

## Dane

- `linux-port/docker/mariadb/playerbot/zywioly_talizmany.sql` (`tools/zywioly/gen_zywioly_talizmany.py` z
  `zywioly_dane.py`): `item_proto` (1206 talizmanów + Kwiat), `refine_proto` 20001–21200, `item_attr.pendant`, sklep 9550.
- `linux-port/docker/mariadb/playerbot/zywioly_moby.sql` + `tools/zywioly/zywioly_moby.json` (`gen_zywioly_moby.py`, dane
  z obrazu gry: `--container <game>` i `--mobs <tsv>` z `world.mob_proto`).
- Oba uruchamia `apply.sh` przy każdym starcie, na samym końcu (po wszystkim, co zapisuje mob_proto/item_proto/item_attr).
- Klient: `client-patches/client-2.0.30/tools/zywioly/patch_zywioly_client.py` (item_proto, item_list, itemdesc, mob_proto),
  ikony `root/icon/item/94000…95500.tga` (jego), root `uiscript/inventorywindow.py`, `uiinventory.py`, `uitooltip.py`,
  `localeinfo_point.py`; exe `ENABLE_PENDANT_SYSTEM`, `ENABLE_ELEMENTAL_TARGET` (+ `PythonNonPlayer.h`,
  `PythonNonPlayerModule.cpp`).

## Poza zakresem

Odporności w bonusach zwykłego sprzętu (zasada właściciela), Talizmany Woli/Zaświatów, Kamień Żywiołów, Zaczarowanie
Żywiołu Broni, żywioły w PvP, ikona żywiołu przy postaci, rękawice.
