# Yohara – druga partia map (MT2009_PLUS_YOHARA_MAPS2_V1)

Decyzja właściciela 14.10.2026 (`cache/yohara/decyzje.md`, „14.10”): Seoganland, Namgan, Schronienie Północnego
Wiatru (dane Owsapa), Przełęcz Yilad (Ameria), Wąwóz Północnego Wiatru (zwykłe potwory wg wiki). Wszystko wg pl-wiki:
potwory, bossowie, Metiny, NPC, rudy, drop, połączenia, żywioły. Rozpadlina Dusz – na razie nie.

Wszystkie pliki tego katalogu robi `tools/yohara_maps/gen_ymaps2.py` (drop i skrzynie – `tools/yohara_items/gen_yitems2.py`);
`gen_report.txt` – raport ostatniego przebiegu, `spawned.txt` – vnumy każdej mapy (czyta je budowniczy klienta
`client-patches/client-2.0.30/tools/ymaps2`). Rdzeń: Yohara (game3, MT2009_PLUS_YOHARA_CORE_V1).

| indeks | mapa | folder (GF/Owsap) | rozmiar | Wola SungMa (`sungma_table.txt`) | źródło spawnów |
|---|---|---|---|---|---|
| 376 | Seoganland | metin2_map_eastplain_02 | 3×6 | 20/10/20/25 | Owsap + wiki |
| 377 | Namgan | metin2_map_eastplain_03 | 4×2 | 25/15/25/30 | Owsap + wiki (pozycje GF) |
| 385 | Przełęcz Yilad | metin2_map_snakevalley | 6×3 | 30/20/30/35 | Ameria + wiki |
| 388 | Wąwóz Północnego Wiatru | metin2_map_icecrystalcave | 5×4 | 30/25/30/35 | nasze (pozycje GF) |
| 393 | Schronienie Północnego Wiatru | metin2_map_whitedragoncave_01 | 6×6 | 45/35/45/50 | Owsap |

## Wąwóz to `metin2_map_icecrystalcave`, nie `whitdragonvalley`

W planie i w zleceniu Wąwóz stał przy folderze `metin2_map_whitdragonvalley` (Owsap 389). Dane klienta GF i Owsapa mówią inaczej:

- klient GF 26.1.11, `npc_location_helper.txt`: 388 = `metin2_map_icecrystalcave` z koreańską nazwą portalu Owsapa 10139
  „Northwind Canyon” / „WąwózPłnW.” (cel 1106 15997 leży w kwadracie icecrystalcave, 5×4 od 0 1510400);
- tenże `map_mob_list.txt`: na 388 stoją potwory Wąwozu z wiki (Zamarznięty Lis…Wódz Wojenny 6770–6776 i 6882–6888,
  Metin Shiho 8066, Metin z Gumar 8077) w punktach do 1077,905 – poza mapą 3×3; na 389 (whitdragonvalley) – jelenie,
  leopardy, yeti 6777–6783, czyli potwory Rozpadliny Dusz;
- Owsap: na whitdragonvalley stoją NPC Rozpadliny z wiki (Strażnik Rozpad. Dusz 20806, Generał Kohan 20808, Łowca Głów
  (Roz.Płn.W.) 20846) i portal 10143 „WąwózPłnW.” (z Rozpadliny do Wąwozu).

Ameria trzyma swój „Wąwóz” na terenie whitdragonvalley (jej mapy są przemianowane), więc jej boss.txt/stone.txt/npc.txt
nie pasują do terenu Wąwozu – bossowie, Metiny i NPC Wąwozu stoją tu w miejscach z danych GF i wiki.

## Skąd co

- **server_attr**: `attr.atr` klienta GF (`tools/gf28/srvattr.py`, `--attr-only`); zgodność z Owsapem: 376 i 393 100%,
  377 99,93%, 385 100%, 388 99,76% (Owsap blokuje więcej). Każdy środek spawnu, NPC i portal sprawdzony na wolnym
  terenie GF (zablokowane przesunięte do najbliższego wolnego metra; 21 grup Owsapa na Seoganland w całkiem
  zablokowanym kwadracie 400–570 × 1270–1411 – pominięte).
- **Seoganland**: regen/boss/stone/npc Owsapa (grupy 6185–6192, group_group 6706–6710; Myr (ziemia) 6718–6724,
  Prymus 6724, Metiny: Szacunku 8063 ×7, Świadomość 8067 ×3, 1. Posterunek Myr 8626 ×7); + Myr Weteran (ziemia) 6723
  (wiki: boss; Owsap go nie stawia) w punkcie GF; + Łowca Głów (Seoganland) 20851 (700,521 – wiki); bez Wieży Sung
  Mahi 4020 (loch – jeszcze nie).
- **Namgan**: regen/boss/stone/npc Owsapa (grupy 6711–6715, gg 6715–6719: Myr (wiatr); Prymus (wiatr) 6731; 2. Posterunek
  Myr 8627 ×8; portale 10130/10136, Łowca Głów (Namgan) 20852, Tajemniczy Ołtarz 20850) + to, co wiki wymienia, a Owsap
  nie stawia, w punktach GF (`map_mob_list` 377): trolle, piekielne psy i Dręczony Duch (grupy Dongan 6700–6705),
  Myr (ziemia) (gg 6706–6710), bossowie Myr Weteran (wiatr) 6730 ×2, Natanan (mrok) 6705, Metiny Świadomość 8067,
  Uważności 8064 ×2, Szacunku 8063, Jin 8065.
- **Przełęcz Yilad**: Ameria (`home.tar.gz`: regen 483 pojedyncze potwory co 30 s, boss 11 miejsc, stone 33 miejsca,
  npc 3) przełożona na wiki: żywioł potworów na przemian (mrok 6758–6764 / ziemia 6875–6881), Skażony Wojownik
  6760/6877 (Ameria go nie ma) ×6 w każdym z 5 punktów GF; bossowie Skażony Wódz / Wódz Wojenny (oba żywioły) na 11
  miejscach Amerii, co godzinę; Metiny: Ameria ma 33× Metin Szacunku co 10 s w trzech pierścieniach (farma) – tu
  po dwa miejsca z pierścienia (6; właściciel 14.10: „Yilad: 6 Metinów co 30 min”), co 30 min, wg wiki i punktów
  GF: wschodni pierścień Metin Shiho 8066, środkowy Metin Jin 8065, zachodni Metin Uważności 8064; NPC: Łowca Głów 20841, Statua Węży 20844, Strażnik Węży 20804; portale Owsapa 10137
  (do Namgan) i 10139 (do Wąwozu, u Owsapa wykomentowany NPC misji – tu portal).
- **Wąwóz Północnego Wiatru** – rozstawione tutaj: zwykłe potwory jako grupy po 4 (nasze grupy 9170–9175, gg 4040 lód /
  4041 błyskawice) w punktach rozrzuconych po całym osiągalnym terenie (wypełnienie od miejsca przybycia z Yilad,
  odstęp ~23 m), w liczbie = gęstość Owsapa na Seoganland (435 grup na 278 674 m² osiągalnego terenu) × teren Wąwozu
  (384 463 m²) → 590 grup; żywioł grupy wg najbliższego punktu GF danego żywiołu (297 lód / 293 błyskawice), 30 m
  wolnego miejsca przy NPC i portalach; bossowie: Zamarznięty Wódz / Wódz Wojenny obu żywiołów w punktach GF
  (580,750 / 850,850) i dwa Wodze w najdalszych miejscach (6 bossów, 1 h); Metiny: Shiho w 3 i z Gumar w 1 punkcie GF
  + kolejne miejsca do udziału Seoganland (19, 30 min); NPC: Strażnik Płn. Wiatru 20805 (503,456 – wiki), Łowca Głów
  (Wąw.Płn.W.) 20845 (1117,871 – wiki); portal 10140 do Yilad (Owsap) przy miejscu przybycia, 10145 do Schronienia.
- **Schronienie Północnego Wiatru**: regen/boss/npc Owsapa (grupy 9150–9157, gg 4030–4033; 6784–6788, Wódz Wojenny
  Schronienia 6789), Zagubiony Zwiadowca 20814 (Owsap), + Łowca Głów (Schron.) 20847 (wiki) i portal 10146 do Wąwozu
  przy wejściu (Town 80,640). Wiki: Schronienie łączy się z Rozpadliną Dusz i Zejściem – obu jeszcze nie ma, więc
  10145/10146 (nasze numery) łączą je z Wąwozem w zastępstwie Rozpadliny.
- **Żyły Jadeitu** (wiki: „losowo”): Seoganland i Namgan – wszystkie cztery (8 żył), Yilad – Nocy i Mgły (6),
  Wąwóz – Dymu, Nocy, Słońca (6), Schronienie – brak; losowe miejsca osiągalnego terenu 60 m od siebie, zasięg 30,
  odnowienie 600 s (żyła sama znika po 7–15 min wydobycia). Kilof: quest `yohara_mapy2`, silnik: `server-patches/jadeit`.
- **Portale** (mob_proto WARP, cel w nazwie): Dongan 10128 (40,531) → Seoganland; Seoganland 10127 → Dongan, 10129 →
  Namgan; Namgan 10130 → Seoganland, 10136 → Przełęcz Yilad; Yilad 10137 → Namgan, 10139 → Wąwóz; Wąwóz 10140 → Yilad,
  10145 → Schronienie; Schronienie 10146 → Wąwóz. Cele Owsapa; każdy cel wolny i ≥ 15 m od portalu powrotnego.
- **Wejście**: od 120 poziomu, bez Poziomu Czempiona (jak 373/374) – quest `yohara_mapy2` odsyła niższych do portu.
  Boty: mapy Sung Ma (`sungma_table.txt`) są dla botów zamknięte, a rdzeń Yohary botów nie ma.
