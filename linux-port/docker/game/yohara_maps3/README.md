# Yohara – trzecia partia miejsc (MT2009_PLUS_YOHARA_MAPS3_V1)

Decyzja właściciela 14.10.2026 (`cache/yohara/decyzje.md`, „Kolejna partia (14.10)”): Zejście i Głębie Północnego
Wiatru, Świątynia Węży (obie części), Tajemnicza Instancja, Królestwo Żywiołów – wszystko wg pl-wiki, czego brak –
wg wiki TR. Pliki tego katalogu robią `tools/yohara_maps3/gen_ymaps3_maps.py` (mapy, grupy) i
`tools/yohara_maps3/gen_yitems3.py` (drop, skrzynie); wiersze potworów – `tools/yohara_maps3/gen_ymaps3_sql.py`
(`mariadb/playerbot/yohara_maps3.sql`, żywioły `yohara_maps3_zywioly.sql`), przedmioty – `yohara_items3.sql`.
Rdzeń: Yohara (game3, MT2009_PLUS_YOHARA_CORE_V1). Zależy od drugiej partii (claude/yohara-maps2: mapy 377/385/393,
przedmioty `yohara_items2.sql` – Zamarznięty Klucz, Pył Wężowy, perły, skrzynie skarbów…).

| indeks | miejsce | folder (GF/Owsap) | rodzaj | spawny |
|---|---|---|---|---|
| 394 | Zejście Północnego Wiatru | metin2_map_whitedragoncave_02 (3×3) | mapa | nasze (punkty GF), labirynt portali GF/Owsap |
| 395 | Głębie Północnego Wiatru | metin2_map_whitedragoncave_boss (2×2) | loch (`ymaps3_glebie`) | quest |
| 390 | 1. poziom Świątyni Węży | metin2_map_snake_temple_01 (3×3) | mapa | nasze (punkty GF), bossowie wg TR |
| 391 | Świątynia Węży | metin2_map_snake_temple_02 (3×3) | loch (`swiatynia_wezy`, 7 poziomów) | quest |
| 396 | Tajemnicza Instancja | metin2_map_anglar_dungeon_01 (6×6) | mapa (Tajemniczy Bilet) | Owsap |
| 378–380 | Królestwo Żywiołów (9 obszarów wiki) | metin2_map_elemental_01..03 (5×5) | mapy (z portu: portal 3998 albo Staruszek 20009 – każdy z 9 obszarów, 90 lvl, 50 mln) | Owsap |
| 381 | Płaskowyż Sił Natury | metin2_map_elemental_04 (1×2) | mapa (Pierścień Siły Natury) | Owsap |

`metin2_map_elemental_04_rework` to własna kopia Amerii (te same pliki terenu co `_04`, inna baza, śnieżny
textureset) – nieoficjalna, pominięta. Królestwo Żywiołów to w każdym źródle cztery mapy: `_01` (Turniobłysk,
Szczytobłysk, Lodogóry), `_02` (Ognioturnia, Ognioszczyt, Wyspowiatr), `_03` (Turniomrok, Szczytomrok, Ziemiopust),
`_04` (Płaskowyż); portale między obszarami – Owsapa (10110–10124, 10109 → u nas 10125).

Połączenia (krok Dockerfile „Yohara maps 3: links”, punkty GF): Schronienie (393) 10202 → Zejście, Zejście 10203 →
Schronienie; Przełęcz Yilad (385) Strażnik Węży 20804 → 1. poziom Świątyni, Wyjście 10138 / Statua Węży → Yilad;
Namgan (377) Tajemniczy Ołtarz 20850 → Instancja (bilet 70408, 1. Poziom Czempiona), Wyjście 10204 → Namgan; Port
(368) portal 3998 i Staruszek 20009 (233,581) → wybrany z 9 obszarów Królestwa, Wyjście 3999 → port.

Obszary Królestwa (MT2009_PLUS_YOHARA_REALM_V2, błąd 3.0 #13): wszystkie 9 istnieją – trzy na każdej z map 378–380,
każdy z własnym Metinem i potworami swojego żywiołu. Punkty teleportu (globalne m) = cele portali Owsapa między
obszarami: Turniobłysk 451,9492, Szczytobłysk 830,9454, Lodogóry 690,10169 (378); Ognioturnia 1430,9616, Ognioszczyt
2117,9447, Wyspowiatr 1973,10159 (379); Turniomrok 2710,9616, Szczytomrok 3393,9454, Ziemiopust 3069,10174 (380).
Współrzędne z listy wiki (831,221 …) to miejsca portali prowadzących do danego obszaru. Wstęp 50 000 000 Yang za
teleport (właściciel), drużyna niewymagana (wiki: „żadna grupa nie jest wymagana”). Pierścień Siły Natury (39114,
10%; 39116 – 100%, jest w danych GF) działa tylko na 378–380, wypada ze wszystkich potworów (0,1%) i Metinów (10%)
Królestwa; flagi wg wiki: sprzedaż NPC tak, handel z graczem / sklep / upuszczanie / magazyn nie.

Strefy na ziemi (`server-patches/strefy`, MT2009_PLUS_DUNGEON_ZONE_V1, `d.zone_attack`): lodowe kolce Głębi (co 15 s
pod każdym, 50% PŻ), Śmiertelny Chłód (stałe białe kręgi, 15 000 / 20 000 PŻ + osłabienie) i atak z powierzchni
Świątyni (co 20 s, 20% PŻ) – z efektem ostrzeżenia, prawdziwe obrażenia, mogą zabić. Szał Alastora leczy i
podnosi jego obrażenia (+10/15/20%, silny +20/30/40%), martwy 3 min (silny 2 min) wypada z Głębi. Brak: ciągu misji wejściowych Głębi, misji „Ważne
przygotowania”, zakazu zwojów/pierścieni teleportu na tych mapach, efektów zestawu, rękawic Sung Ma.
