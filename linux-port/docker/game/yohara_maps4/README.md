# Yohara – Rozpadlina Dusz (MT2009_PLUS_YOHARA_MAPS4_V1)

Decyzja właściciela 14.10.2026 (`cache/yohara/decyzje.md`, „14.10 rano”): „Rozpadlina Dusz: TAK, z danymi Amerii
(metin2_map_whitdragonvalley: boss/stone/npc), zastępuje tymczasowy portal Wąwóz↔Schronienie”. Wszystko wg pl-wiki
(„Rozpadlina Dusz” i strony jej potworów oraz NPC), czego brak – wiki TR. Pliki tego katalogu robi
`tools/yohara_maps4/gen_ymaps4.py` (`gen_report.txt` – raport ostatniego przebiegu, `spawned.txt` – vnumy mapy dla
budowniczego klienta `client-patches/client-2.0.30/tools/ymaps4`); wiersze potworów, NPC i portali –
`mariadb/playerbot/yohara_maps4.sql`, żywioły – `yohara_maps4_zywioly.sql`. Rdzeń: Yohara (game3,
`bin/m2-render-config` MAPS_game3_all).

| indeks | mapa | folder (GF/Owsap) | rozmiar | baza | Wola SungMa (`sungma_table.txt`) |
|---|---|---|---|---|---|
| 389 | Rozpadlina Dusz | metin2_map_whitdragonvalley | 3×3 | 128000 1510400 | 35/25/35/40 (= wiki) |

Folder Rozpadliny to `metin2_map_whitdragonvalley` (Owsap 389): na nim stoją NPC Rozpadliny z wiki (GF
`metin2_map_whitdragonvalley_point.txt`, Owsap `npc.txt`) i jej potwory (GF `map_mob_list.txt` 389: jelenie,
leopardy, yeti, duchy, golemy 6777–6783 / 6889–6895). Wąwóz to `metin2_map_icecrystalcave` (druga partia).

## Skąd co

- **server_attr**: `attr.atr` klienta GF 26.1.11 (`tools/gf28/srvattr.py`), 100% GF; zgodność z Owsapem 99,62%
  (Owsap blokuje trochę więcej). Każdy środek spawnu, NPC i portal sprawdzony na wolnym terenie GF.
- **NPC** (Ameria = Owsap = punkty GF): Strażnik Rozpad. Dusz 20806 (562,670), Generał Kohan 20808 (134,89), Łowca
  Głów (Roz.Płn.W.) 20846 (499,231), portal 10143 do Wąwozu (575,705; cel Owsapa 247,288 w Wąwozie).
- **Bossowie** (wiki: Wielka Stopa i Wódz Wojenny Płn. Wiatru, lód i błyskawice): 8 miejsc z `boss.txt` Amerii,
  po dwa na każdego z czterech bossów, co godzinę.
- **Metiny** (wiki: Metin Shiho, Metin Gumar): Ameria ma 33 miejsca w trzech pierścieniach co 10 s (farma) – tu po
  dwa miejsca z pierścienia (6, co 30 min – jak Przełęcz Yilad, decyzja z 14.10); który Metin – wg najbliższego
  punktu GF (Shiho 8066 ×4, Gumar 8077 ×2). Dropy Metinów – te z drugiej partii.
- **Zwykłe potwory** (wiki: Duch, Golem, Opętany Mroźny Jeleń, Opętany Śnieżny Leopard, Yeti Płn. Wiatru – lód
  6777–6781, błyskawice 6889–6893): rozstawione jak w Wąwozie – grupy po 4 (nasze grupy 9190–9195, gg 4042 lód /
  4043 błyskawice) po całym osiągalnym terenie, w liczbie = gęstość Owsapa na Seoganland × teren Rozpadliny
  (161 738 m²) → 249 grup co ~24 m; żywioł grupy wg najbliższego punktu GF potwora danego żywiołu (139 lód /
  110 błyskawice); 30 m wolnego miejsca przy NPC, portalu i miejscach przybycia.
- **Drop** (wiki, każdy potwór i boss; procenty nasze, oficjalnie rzadkie – skala drugiej partii; nic nie
  wyrównuje eventu 500% na serwerze testowym): potwory – Talizmany Woli 0,05%, Topaz Woli 0,4%, Kamień Wężowy(+),
  Małż, Ognista Runa Aury (10), płyta, Róg Trolla, Utwardzacze, Wzór Wężowy, zioło żywiołu (Mroźny Korzonek /
  Piorunowe Zioło), Puste Eliksiry, Skrzynia Ksiąg (9.skill), Zdobna Skrz. z Odłamkiem, losowe skrzynia/klucz;
  bossowie – broń +5/+6 (Miecz Żądło, Demoniczne Ostrze, Nóż Siamese), Święty Fragment (120), materiały, Runy
  SungMa, Charyzmy, księgi i reszta listy wiki (Wodzowie: + Kowadło Płn. Wiatru, Zwój Skarbu (A)). Pominięte:
  Odłamki 39070–39077 (event Seon-Hae), Eliksiry W. SungMa (nie ma ich u nas); Kamień Demonów +4 → +0.
- **Żywioły**: lód 6777–6783, błyskawice 6889–6895 (wiki; zgodne z Att* Owsapa). 6889 nie ma na liście SungMaExp
  Owsapa – krok Dockerfile dopisuje mu 38 (jak jego bliźniak 6777).
- **Połączenia** (wiki: „Dostępne teleporty: Wąwóz Północnego Wiatru, Schronienie Północnego Wiatru”), w miejsce
  tymczasowych 10145/10146 drugiej partii (usunięte; `yohara_maps4.sql` kasuje ich wiersze):
  - Wąwóz (388): portal 10142 „Rozpadlina Dusz” w punkcie GF 235,267 → Rozpadlina 550,690 (Town, obok Strażnika
    Rozpad. Dusz); Rozpadlina: portal 10143 → Wąwóz 247,288 (Owsap);
  - Schronienie (393): portal 10201 „Wyjdź” w punkcie GF 19,640 → Rozpadlina 146,96 (obok Kohana); Generał Kohan
    (quest `yohara_mapy4`) → Schronienie 80,640 (Town). Wiki: Kohan wpuszcza po okazaniu Przepustki – jej misji
    nie mamy, więc wpuszcza każdego.
  Linie portali w `npc.txt` Wąwozu i Schronienia dopisuje krok Dockerfile (`links.yohara_maps4.txt`).
- **Wejście**: od 120 poziomu, bez Poziomu Czempiona (jak reszta map Yohary) – `yohara_mapy4` odsyła niższych do portu.
  Boty: mapa Sung Ma (`sungma_table.txt`) – zamknięta dla botów; rdzeń Yohary botów nie ma. `/goto rozpadlina`.
