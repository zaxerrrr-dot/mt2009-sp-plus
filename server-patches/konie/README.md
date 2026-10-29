# server-patches/konie — koń powyżej 21 poziomu (MT2009_PLUS_HORSE40_V1)

Właściciel (29.10.2026): „Do 21 poziomu tak jak teraz. Powyżej 21 według wiki (pl-wiki „Koń”) i naszego nowego
systemu. Połącz to z nowymi umiejętnościami konia.” Nowy system = przesłana paczka **„system_rozwoju_konia”** —
eksport oficjalnego *Mount Upgrade System* przygotowany przez **Best Studio** (GitHub: ybeststudio, Discord:
beststudio, https://bestpro.dev) — `/opt/metin2/cache/yohara/konie-src`.

## Co było (bez zmian do 21)

* `quest/konie.quest` (Digi Rasta, MT2009_PLUS_HORSE30_V1): szkolenie u Stajennego 1–9 i 11–19 (Medale Konne,
  Materiały Rzemieślnicze, Yang), stały bonus konia od 21 (Potwory/Bossy/Metiny, do 30 poziomu);
* `pony_buy` (0→1), `horse_upgrade` (10→11, Koń Bojowy), `horse_upgrade2` (20→21, Koń Wojskowy, 300 Demonicznych
  Łuczników);
* juki `horse_inventory` (rzędy do 30 poziomu konia), Czarny Rumak (rasa 20119) od 30 poziomu (digirasta).

**Zniesione:** płatne szkolenie 21–28 i „Próba Czarnego Rumaka” 29→30 (gracz w trakcie próby wraca do stanu start).

## Powyżej 21 (wiki + paczka)

| | |
|---|---|
| Poziomy | 22–40 (`HORSE_MAX_LEVEL` 40) |
| Pasza dla Konia (50048) | karmienie w oknie u Stajennego: 200–250 dośw. za sztukę (paczka), pasek z wiki (12 500 … 308 200) |
| Próba awansu | pełny pasek + 50 paszy + Yang z wiki (500 000 … 5 000 000), postać 75+, od 30 poziomu konia Poziom Czempiona 1 |
| Porażka | 50% (paczka); pasek zostaje; następna próba kosztuje dodatkowo 50 Gaya (<30) / 100 Gaya (≥30) i się udaje (paczka) |
| Statystyki konia | 22–30 tabela wiki (WIT/INT/SIŁA/ZRĘ), 31–40 Wola SungMa wiki (10/15/25/25 … 35/40/45/45, minimum na wierzchowcu) |
| Misja codzienna | „Pasza dla konia”: koń 21+, postać 75+, co 24 h 30 paszy z potworów (15% za potwora), nagroda 22–27× 50048 |
| Złota Księga Konia (50049) | Poziom Czempiona 1, koń 30+, 100 potworów w Jaskiniach Gnolli (1. poziom, mapa 382) w 30 min, 100 000 000 Yang przy odbiorze, 24 h (gdy świat ma czas oczekiwania, `m2_horse_wait`) → od 31 poziomu wygląd Potężnego Konia Wojskowego (20149–20151), przywołanie księgą (300 PE) |
| Czer. Żeń-szeń (premium) 50047 | karma (prawy klik / podanie koniowi 30+); drop 0,5% z potworów map Sung Ma (Yohara) |
| Szlachetna Trawa 50046 | wskrzesza konia 31+; drop 25% z Ahtrin Wielki Mistrz (6820) |
| Umiejętności konia | księgi 55050–55067 (drop jak dotąd z Wodzów Wojennych Schronienia): 1 umiejętność od 21, 2 od 31, poziom 1–20 (1000 Gaya + 20 000 000 Yang), zapomnienie za darmo u Stajennego, działają na każdym wierzchowcu |

Wartości umiejętności = wielomiany `skill_proto.sql` paczki (zgodne z tabelą wiki dla poziomu 20 i koni 21/25/30/35/40;
`Jazda (umiej. konne)` z k = poziom umiejętności — paczka miała k = 100, wiki 3,36%…4%):

* stałe podczas jazdy: PD (`MALL_EXPBONUS`), Precyzja (`HIT_PCT`), silny przeciw rasom/klasom (losowa księga 55056:
  półludzie, zwierzęta, orki, mistycy, nieumarli, diabły, pustynia, insekty, potwory);
* czasowe po ciosie z wierzchowca: Zwinne Kopyta (MOV_SPEED), Gwałt. Wichura (ATT_SPEED), 4× Wola SungMa — odnowienie
  180 s; Brak Odrzutu 1% szansy (180 s); pieszo: Bezszelestny Chód = Lekki Krok (AFF_SKILL_FEATHER_WALK + MOV_SPEED,
  300 s); Nieśmiertelność gdy cios zostawiłby < 30% PŻ (600 s); Jazda (umiej. konne) do obrażeń umiejętności 137–140;
* Likan (55061/306) i Zodiak (297) — brak w tym świecie.

## Pliki

* `edits.json` (z `gen_edits.py`), `apply_konie.py <game/src>` — 16 edycji, każda ze znacznikiem
  `MT2009_PLUS_HORSE40_V1 (...)`: `horse_rider.h/.cpp` (40 poziomów, tabela, stopień ≤ 3), `char_horse.cpp`
  (rasa 20149+, koniec jazdy), `char.cpp` (ComputePoints), `char_battle.cpp` (Damage, IsResistPush),
  `char_skill.cpp` (typ wierzchowca 20149–20151), `char_item.cpp` (karmienie 20119/20149–20151), `item_manager.cpp`
  (drop 50046/50047), `cmd.cpp` (`/konie_rozwoj`), `questlua_horse.cpp` (`horse.konie_*`), `cmd_gm.cpp` (panel GM do 40);
* `linux-port/overlays/playerbot/src/game/src/konie_rozwoj.cpp` — cała logika (nowy plik, Makefile bierze `*.cpp`);
  boty: `playerbot_horse30.h`, `playerbot_activities.h`;
* questy: `quest/konie_rozwoj.quest` (nowy, kompiluje osobny krok Dockerfile z funkcjami `horse.konie_*`),
  `quest/konie.quest` (bez 21–28 i Czarnego Rumaka);
* SQL: `mariadb/playerbot/konie.sql` (`tools/konie/gen_konie.py`) + blok w `apply.sh` (mob_proto 20149–20151);
  **bez nowej tabeli/kolumny** — dośw., porażka, umiejętności to flagi questa `konie_rozwoj.*` (tablica umiejętności
  gracza kończy się na 265, a skill_proto 285–311 paczki nie zmieściłby się w niej bez zmiany bloba w DB i exe);
* klient: `root/uikonierozwoj.py` (okno paczki zbudowane w kodzie, bez modułu exe `mount`), `root/game.py`,
  `root/uiaffectbar.py`, `root/icon/item/50046-50049.tga`; paczka `konie` + dbdata/gamedata:
  `client-patches/client-2.0.30/tools/konie/` (`stage_konie.py`, `build_konie_packs.py`, `verify_konie.py`).
  Exe bez zmian, **bez nowych nagłówków pakietów** (komenda czatu `/konie_rozwoj` i `konie_rozwoj_info/_msg`).

## Wdrożenie

* afekty czasowych umiejętności konia: **780–788** (760–776 to relikty, MT2009_PLUS_RELIC_V1); ikony w `root/uiaffectbar.py`;
* boty nigdy nie sprzedają 50046–50049 i ksiąg 55050–55067 (`Mt2009KonieIsKeptVnum`: złom, stragan, handel na czacie);

* `yohara-deploy.sh`: dopisać `konie` na KONIEC pętli łatek (po `relikty`) - kotwice sprawdzone na drzewie z całą listą;
* `clientY.sh`: po linii `czepiec`
  `docker run --rm -v /opt/metin2:/opt/metin2 m2pack-lzo python3 $T/konie/build_konie_packs.py $C/azbase $C/out/pack > $C/konie.json`
  i `konie/verify_konie.py` w pętli weryfikacji;
* zmiana dbdata (item_proto) → ostrzeżenie „nieaktualne pliki” i nowa baza panelu (jak przy każdej zmianie przedmiotów).
