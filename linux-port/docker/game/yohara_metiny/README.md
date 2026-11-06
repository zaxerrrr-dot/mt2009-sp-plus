# Grupy Metinów i jaj Yohary (MT2009_PLUS_YOHARA_STONE_GROUPS_V1)

Druga analiza botów 6.11.2026, pkt 2 (decyzja właściciela: „zdefiniuj je”). Metin przy każdym progu PŻ (90%, 80% …
10%) przywołuje 2–3 grupy o losowym numerze z zakresu `attack_speed`..`move_speed` swojego wiersza `mob_proto`
(`char_state.cpp`, `__StateIdle_Stone`). Tych grup nie było w żadnym źródle (ani `group.txt` Owsapa, ani dane GF),
więc Metiny Świątyni Węży i Białe Jaja Smoka nikogo nie przywoływały, a rdzeń pisał `NOT_EXIST_GROUP_VNUM` przy
każdym progu (test Yohary, 6.11: ok. 17 tys. linii).

`group.yohara_metiny.txt` (pisany ręcznie, krok Dockerfile „Yohara Metins' and eggs' groups”, żaden z numerów nie może
istnieć wcześniej):

| grupy | kto przywołuje | gdzie | skład (potwory miejsca) |
|---|---|---|---|
| 6218–6220 | Metin Shiho (8066), Metin z Gumar (8077) | Wąwóz Płn. Wiatru (388); wg arkusza też Yilad (385) i Rozpadlina (389) | Zamarznięty Lis / Zwiadowca / Wojownik / Łowca (6770–6773), po 3 |
| 6229, 6230 | Metiny Wężowe (8630–8634), Metin Wężowy Przestrzeni (8076) | Świątynia Węży (391), 1. poziom Świątyni (390) | Skorpion / Robotnik / Kappa Wężowy (6850–6852), po 3 |
| 6249, 6250 | Białe Jajo Smoka (słaby) 8635 | Głębie Płn. Wiatru (395) | Żołnierz / Zadziora Schron. Płn. W. (6792, 6793), po 2 |
| 6252, 6253 | Białe Jajo Smoka (silny) 8636 | Głębie Płn. Wiatru (395) | Wojownik / Czarownik / Zadziora / Żołnierz Schron. (6792–6795), po 3 |

Grupy przywołane przez Metin nie należą do lochu (`d.count_monster()` ich nie liczy), więc nie wstrzymują przejścia
na kolejny poziom Świątyni ani Kowala/Wojownika.

Cztery Metiny Szczeliny Czasu i Płaskowyżu Iluzji miały numery grup Owsapa, które nasze generatory przenumerowały
(`tools/yohara_crack`: 6401–6407 → 6178–6184, `tools/yohara_iluzja`: 6411–6417 → 6171–6177; 6408–6412 to tu grupy
Atlantydy). `mariadb/playerbot/yohara_metiny_grupy.sql` (apply.sh, po wszystkich plikach potworów Yohary) przestawia je
na nasze numery – ten sam skład co u Owsapa:

- 8126 SZC: Metin Drz. Stworzeń 6401–6404 → 6178–6181, 8127 SZC: Metin Lasu 6420–6423 → 6178–6181;
- 8136 PB: Metin Drz. Stworzeń 6411–6414 → 6171–6174 (6411/6412 przywoływały na mapę 371 Stwora z Głębin
  i Nieumarłego Rybiego Wojownika z Atlantydy), 8137 PB: Metin Lasu 6430–6433 → 6171–6174.

Metiny bez żadnych grup (zakres 0–0: SZC/PB 8120–8123, 8130–8133, Kamień Duchowy 7600 w Wieży Sung Mahi) zostają bez
przywołań; silnik nie pisze już dla nich błędu (`server-patches/enginefixes`, `MT2009_PLUS_STONE_GROUP_GUARD_V1`).

Sprawdzenie po wdrożeniu: `grep -c NOT_EXIST_GROUP_VNUM channel1/game3/syserr` – zostają tylko numery 0 Zodiaku
(358xxxx, osobna sprawa) i ewentualnie jedna linia `STONE_GROUP_MISSING` na brakującą grupę w `syserr`.
