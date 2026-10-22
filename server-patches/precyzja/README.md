# precyzja – Precyzja, procentowe bonusy Sung Ma, efekt doświadczenia Czempiona

`MT2009_PLUS_PRECISION_V1` (14.10.2026, decyzja właściciela z „14.10 ok. 8:10”: „Czempion: pasek doświadczenia, ikona
buffa i debuffa, efekt zdobywania doświadczenia, procentowe bonusy Sung Ma, celność”). Druga runda exe Yohary
(`client-patches/exe`, `MT2009_PLUS_YOHARA_EXE2_V1`).

## Punkty

| punkt | numer | GF | co robi |
|---|---|---|---|
| `POINT_SUNGMA_PER_STR` | 193 | `APPLY_SUNGMA_PER_STR` | Siła Sung Ma +x% |
| `POINT_SUNGMA_PER_HP` | 194 | `APPLY_SUNGMA_PER_HP` | Witalność Sung Ma +x% |
| `POINT_SUNGMA_PER_MOVE` | 195 | `APPLY_SUNGMA_PER_MOVE` | Odporność Sung Ma +x% |
| `POINT_SUNGMA_PER_IMMUNE` | 196 | `APPLY_SUNGMA_PER_IMMUNE` | Inteligencja Sung Ma +x% |
| `POINT_HIT_PCT` | 197 | `APPLY_HIT_PCT` | Precyzja |

`POINT_MAX_NUM` = 198 (tak samo w exe). W tym silniku apply = punkt, więc te numery są też `applytype` przedmiotów
i bonusami (`item_attr`: `POINT_HIT_PCT` – `yohara_gloves.sql`).

**Protokół bez zmian**: pakiet punktów dalej ma 193 punkty (`POINT_PACKET_NUM`), nowe przychodzą jako zmiana punktu
(`HEADER_GC_CHARACTER_POINT_CHANGE`, `char.cpp (point packet)`) i z `champion::SendInfo` (logowanie, zmiany
Czempiona). Bramka wersji 3.0 zostaje (`server_version` 1010300) – stary exe 3.0 nowe zmiany punktu pomija
(`SetStatus` odrzuca typ ≥ 193), więc nie trzeba podbijać wersji klienta.

## Jak działa

- **Procent Woli** (wiki/GF „Wola SungMa +x%”): skuteczna statystyka = punkt (rozdane + przedmioty + afekty) ×
  (100 + procent) / 100 – `yohara_gear::SungmaEffective` (`playerbot_yohara_gear.cpp`). Z nią porównują wymagania mapy
  wszystkie kary Sung Ma (`playerbot_champion.cpp`: obrażenia, PŻ, ruch, trucizna/ogień/krwawienie) i komunikat
  wejścia na mapę; okno postaci i ikony afektów liczą tak samo (`root/sungmastate.py`). Owsap mnożył dodawaną
  wartość z błędem całkowitego dzielenia – tu procent działa na całość.
- **Precyzja** (pl-wiki „Precyzja”: „Każdy potwór na mapach Nowego Kontynentu ma ukrytą wartość precyzji. Próbując go
  trafić, postać zacznie chybiać”): mapa Sung Ma ma `hit_pct` (6. kolumna `champion/sungma_table.txt`, z Owsapa
  `share/locale/uk/map/new_world.txt` – Dongan/Seoganland/Namgan 10, Jaskinie Gnolli 20, Tajemnicza Instancja 25,
  Przełęcz Yilad i 1. poziom Świątyni Węży 30, Wąwóz, Rozpadlina, Schronienie, Zejście 50; mapy, których Owsap nie
  ma – 0). Cios gracza w potwora (zwykły, strzała, umiejętność; nie w Metina) chybia z szansą
  `(hit_pct − Precyzja) × 100 / hit_pct` % (jak Owsap) – serwer odsyła `DAMAGE_BLOCK` (`ChampionDamage`).
  `d.set_sungma(str, hp, move, immune[, hit])` – piąty argument dla instancji (Wieża Sung Mahi: bez niego 0).
  Źródła Precyzji: Obręcze Jadeitu (`server-patches/obreczjadeitu2`), bonus rękawic `POINT_HIT_PCT`
  (`item_attr.glove`), pasywna umiejętność Precyzja (niżej).
- **Efekt doświadczenia Czempiona**: `FLY_CONQUEROR_EXP` = 30 (pomarańczowy `ga_piece_orange_small.msf` GF, exe
  rejestruje go pod tym numerem; pliki: `client-2.0.30/atlas/d_/ymir work/effect/etc/conqueror_exp/`) zamiast żółtego
  `FLY_EXP` przy exp Czempiona (`champion::GiveExp`).
- `sungma_map` ma teraz 5 liczb (`… <hit>`); root czyta i 4, i 5.
- GM: `/champion` pokazuje też `hit` mapy, Precyzję i procenty.

## Umiejętność pasywna Precyzja

`MT2009_PLUS_PRECISION_SKILL_V1` (14.10.2026, zlecenie właściciela: „dodaj umiejętność pasywną Precyzja, dokładnie wg
wiki”). pl-wiki „Precyzja” i „Księga Precyzji”, de-wiki „Präzision”.

- `SKILL_PRECISION` = **246** – numer GF (wiersz 246 `skilltable.txt` klienta GF 26.1.11, ikona `hit_attribute`
  w `newskillcommon.dds` – ta sama co na wiki; Ameria: `246 SUPPORT … hit_attribute`). U nas wolny.
  `skill_proto` 246: `linux-port/docker/mariadb/playerbot/precyzja_skill.sql` (`apply.sh`), typ 0 (pomocnicza,
  jak Dowodzenie), poziomy 0–40, `DISABLE_BY_POINT_UP` (punktami się nie da).
- **Nauka**: tylko **Księga Precyzji** (50325) i tylko od **1. Poziomu Czempiona** (`PrecisionReadBook`,
  `playerbot_champion.cpp`); każda udana lektura = +1 poziom, od 0 do P (40): 1→M1 20 ksiąg, M1→G1 10, G1→P 10
  (de-wiki: „20 erfolgreiche”). Czytanie to pasywna ścieżka `LearnSkillByBook`: szansa **35 %** (podstawa ksiąg
  klasowych; mikstury nauki ją podnoszą), Rada Pustelnika = 100 %, odstęp między księgami jak przy innych
  (`m2_book_wait`, klątwa; Zwój Egzorcyzmu ją zdejmuje). Na P i bez Czempiona księga się nie zużywa.
  Stary przypadek silnika (50325 → `SKILL_RESIST_PENETRATE` z wartością0 1 jako minimalnym poziomem – książki nie dało
  się przeczytać) został dla 50325 zastąpiony; 50326 bez zmian.
- **Bonus** (tabela wiki): 1:+0 2:+0 3–5:+1 6–8:+2 9–10:+3 11–14:+4 15–17:+5 18–19:+6 M1–M3:+8 M4–M6:+9 M7–M8:+10
  M9–M10:+11 G1–G2:+13 G3–G4:+14 G5:+15 G6–G7:+16 G8:+17 G9–G10:+18 P:+20 (`PrecisionSkillBonus`; wzór GF
  `0.4*k+(32*k/2)` na mocy umiejętności daje to samo poza poz. 11 – tam wiki ma +4, wzór +3; jest tabela wiki).
  Wchodzi do `POINT_HIT_PCT` w `ComputePoints` (edycja `(compute)`, przed przedmiotami) – logowanie, zmiana poziomu,
  każde przeliczenie; klient dostaje punkt zmianą punktu i `champion::SendInfo`.
- Reset umiejętności (zwoje, zmiana drogi – `ResetSkill`) jej **nie kasuje** (edycja `(reset)`); Księga Zapomnienia
  (`ClearSubSkill`) też nie.
- Boty: Precyzja ich nie dotyczy (`MT2009_PLUS_BOT_YOHARA_MAPS_V1`, właściciel 22.10.2026): każdy bot ma bonus P
  (+20, `PrecisionSkillBonus`) bez ksiąg (Księgi Precyzji bot nie czyta), a jego ciosy nigdy nie chybiają (`ChampionDamage`).
- Klient: zakładka umiejętności pomocniczych (miejsce 111, `root/playersettingmodule.py`, `uicharacter.py`), dymek
  `root/precisionskill.py` (poziom, bonus teraz i na następnym poziomie, wymaganie Czempiona), wiersze 246
  `skilldesc.txt`/`skilltable.txt` i ikona `d:/ymir work/ui/skill/common/support/hit_attribute.sub` (atlas
  `skill9_common.dds` z paczki `yskill9`) – `client-patches/client-2.0.30/tools/yskill9`. Exe bez zmian
  (`SKILL_MAX_NUM` 265, pakiet poziomów umiejętności niesie 246, miejsca 101–112 są Pythona).

## Pliki

`common/length.h` (`(points)`, `(fly)`), `char.cpp` (`(point change)`, `(point packet)`) – 4 edycje, każda ze swoim
znacznikiem; umiejętność Precyzja: `common/skill_length.h` `(vnum)`, `char_item.cpp` `(book)`, `char_skill.cpp` `(reset)`,
`char.cpp` `(compute)` (`MT2009_PLUS_PRECISION_SKILL_V1`); `gen_edits.py [<game/src>]` tworzy `edits.json` i sprawdza kotwice. Logika: `playerbot_champion.cpp`,
`playerbot_yohara_gear.cpp` (nakładka). Asercje numerów po obu stronach (`playerbot_yohara_gear.cpp`,
`client-patches/exe/UserInterface/Mt2009Champion.cpp`).

- Linux/VPS: `python3 apply_precyzja.py <game/src>`; Windows: `Apply-PrecyzjaPatch.ps1 -SourceDir <game/src>`
  (`tools/port/Apply-MT2009PlusEngine.ps1`, po `szczelina`).
