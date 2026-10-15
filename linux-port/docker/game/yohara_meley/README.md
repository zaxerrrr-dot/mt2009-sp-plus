# Schronienie Meley (MT2009_PLUS_YOHARA_MELEY_V1)

Leże Królowej Smoków Meley – loch dodany 15 października 2026 („dodaj loch Meley, drop zgodnie z wiki”).
Wzór: pl-wiki „Schronienie Meley (dla gildii)” (etapy, potwory, skrzynie) i Owsap v6.2.6 (`GuildDragonLair.lua`,
`guild_dragonlair.cpp` – liczby potworów, czasy, pozycje). Wszystko w tym katalogu generuje
`tools/yohara_meley/gen_ymeley.py` (poza tym plikiem).

## Wejście

- **Strażnik Smoków Dolnarr** (20419) na Doyyumhwaji (mapa 62), pole 83,851 (jak na wiki).
- Poziom **90** (jak wersja gildyjna).
- **Sam albo z drużyną do 8 osób** – boty z drużyny wchodzą za człowiekiem. Wersja gildyjna chce 4–16 członków
  gildii przy NPC i 600 pkt. rankingu, wersja dla grup – Przepustki i 4–8 osób; w świecie jednego gracza z botami
  to nie działa, więc wejście jest jak w naszych innych lochach.
- **7 500 000 Yang** za wejście, najwyżej **5 wypraw dziennie** (płaci tylko człowiek, boty i towarzysz nic).
- Bez czekania między wyprawami dla ludzi; boty odpoczywają 3 h (wiki: „co 3h”). Przepustka (Meley) niepotrzebna.
- „Wróć do lochu” u Dolnarra, póki trwa godzina wyprawy.

## Przebieg (limit 60 minut)

| Etap | Co robić | Potwory |
|---|---|---|
| 1 | Zbić cztery **Smocze Statuy** (6118, 7 mln HP) do 75% | 12 Magmowych Insektów (wracają po 5 s) |
| 2 | Zniszczyć **Smocze Jaja** (20422), zbić statuy do 50% | 12 Magmowych Golemów (30 s), grupa Ognistego Księcia Żaru |
| 3 | Jaja + czterech **Smoczych Strażników Idallów** (6116, każdy z 3 Sługusami), statuy do końca | 12 Magmowych Wiwern (30 s) |
| 4 | Statuy świecą na niebiesko – **Pierścień Smoczego Ognia** przy każdej z czterech | Wiwerny, jaja co 2 min |

- Statua, która doszła do progu etapu, zostaje na nim i jest nietykalna (silnik: `d.set_damage_from_race`).
- Póki stoi choć jedno jajo (w etapie 3 – także Idall), statuy są nietykalne. Jaja wracają co 120 s.
- Po pierwszym etapie zamyka się brama wejściowa (Smocza Brama 20388). Kto zginie, wstaje w środku.
- Statuy przy trafieniu przywołują grupy 6337 (Golem Lawy, Magmowy Yeti, Magmowy Kryształ) i 6339 (Magmowy Wiwern,
  Magmowy Golem) – jak w danych Owsapa.
- **Pierścień** (30340): wypada z magmowych potworów (Owsap: 5% w etapach 1–2, 1% w 3–4), zawsze człowiekowi
  z drużyny. W etapie 4 stań przy statui i kliknij pierścień prawym przyciskiem myszy (klient przeciąga przedmioty
  tylko na NPC, a statua to kamień). Bot z drużyny kładzie swój pierścień sam. Pierścienie znikają po wyjściu.
- **Królowa Meley** (6193) stoi za północną ścianą areny i nie da się jej zabić – pada po czwartym pierścieniu.

## Nagroda

Po zwycięstwie pojawia się **Złota Smocza Skrzynia** (20420). Każdy człowiek wybiera **jedną** skrzynię:

- **Skrzynia Królowej Meley** (54706),
- **Skrzynia Sm. Strażników** (54707).

Kto nie wybierze w ciągu minuty, dostaje Skrzynię Królowej Meley po wyjściu. Boty nic. Numery skrzyń z GF / Owsapa
(50270 / 50271) to u nas Skrzynia Razadora / Nemere, a pierścienia (30341) – Zupa Grzybowa, stąd nowe numery.

Skrzynie: lista z wiki, **3 losowania na otwarcie**, każda pozycja wiki – równy udział (warianty +4/+5/+6, x5/x10,
10–60 mln Yang dzielą go). Pominięte (nie ma ich u nas): Księga Dzikiego / Dzielnego Zwierza, Hełm Zielonego Lasu
(Lykan), Władca Smoków. Kufer / Skrzynia Riposty i Dopalacza → nasze Skrzynie Ksiąg: Riposta / Dopalacz (50323 /
50324; Kufer = 5 sztuk).

Drop potworów (wiki): Magmowy Yeti, Golem Lawy, Magmowy Golem, Magmowy Kryształ, Magmowy Wiwern – Czerwona Smocza
Łuska (30621), Plan Zbroi: Hełm (30622), Czerwony Smoczy Róg (30620); Jajo Smoka – Kamień Duchowy. Materiały to
wiersze z gałęzi hełmów 100 (`yohara_helm100.sql`).

**Wszystkie szanse są tymczasowe** – lista w `/opt/metin2/cache/yohara/PROCENTY.md`, „Do ustalenia” 5.

## Mapa i rdzeń

- Indeks **356** (`metin2_map_n_flame_dragon`, 1x1) – jak u Owsapa. Baza z GF 307200 1510400 to u nas Świątynia
  Zodiaku, więc **281600 1510400** (bez nakładania w atlasinfo, w bazach serwera i w atlasinfo GF).
- `server_attr` = attr.atr klienta GF; pola pod Meley (130,77) otwarte, żeby dało się ją postawić – z areny nie da
  się tam dojść.
- Rdzeń **game1** (z botami). Jedna sekcja terenu – najmniejsza możliwa mapa (game1 jest blisko limitu 4 GB).

## Pliki

- `tools/yohara_meley/ymeley_data.py`, `gen_ymeley.py` – dane i generator (uruchamiany w obrazie `m2pack-lzo`).
- `linux-port/docker/game/quest/meley_dungeon.quest` – quest (cp1250).
- `linux-port/docker/mariadb/playerbot/yohara_meley.sql`, `yohara_meley_zywioly.sql`, `yohara_items_meley.sql`.
- `client-patches/client-2.0.30/tools/ymeley` – paczki klienta (mapa, modele, wiersze mob_proto / item_proto).
- Boty: `playerbot_party_dungeon.h`, `playerbot_dungeon_runs.h` (rodzaj MELEY), `playerbot_dungeon_runs_rules.h`.
