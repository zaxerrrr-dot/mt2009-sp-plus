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
  (`item_attr.glove`). Pasywnej umiejętności Precyzja (Księga Precyzji 50325) nie ma – zostaje bez zastosowania.
- **Efekt doświadczenia Czempiona**: `FLY_CONQUEROR_EXP` = 30 (pomarańczowy `ga_piece_orange_small.msf` GF, exe
  rejestruje go pod tym numerem; pliki: `client-2.0.30/atlas/d_/ymir work/effect/etc/conqueror_exp/`) zamiast żółtego
  `FLY_EXP` przy exp Czempiona (`champion::GiveExp`).
- `sungma_map` ma teraz 5 liczb (`… <hit>`); root czyta i 4, i 5.
- GM: `/champion` pokazuje też `hit` mapy, Precyzję i procenty.

## Pliki

`common/length.h` (`(points)`, `(fly)`), `char.cpp` (`(point change)`, `(point packet)`) – 4 edycje, każda ze swoim
znacznikiem; `gen_edits.py [<game/src>]` tworzy `edits.json` i sprawdza kotwice. Logika: `playerbot_champion.cpp`,
`playerbot_yohara_gear.cpp` (nakładka). Asercje numerów po obu stronach (`playerbot_yohara_gear.cpp`,
`client-patches/exe/UserInterface/Mt2009Champion.cpp`).

- Linux/VPS: `python3 apply_precyzja.py <game/src>`; Windows: `Apply-PrecyzjaPatch.ps1 -SourceDir <game/src>`
  (`tools/port/Apply-MT2009PlusEngine.ps1`, po `szczelina`).
