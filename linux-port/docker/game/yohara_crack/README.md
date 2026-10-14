# Szczelina Czasu: Statua Szczeliny Czasu i Zaklęty Las (SZC) (MT2009_PLUS_YOHARA_CRACK_V1)

Decyzja właściciela z 14.10.2026: „Statua Szczeliny Czasu na Płaskowyżu Iluzji, na razie tylko jeden loch –
Zaklęty Las”. Pozostałe trzy lochy dojdą później: Grota Wygnańców 2, Twierdza Czerwonego Smoka i Strażnica
Nemere (SZC).

Źródła:
- pl-wiki: „Statua Szczeliny Czasu”, „Płaskowyż Iluzji” (rozdział „Statua Szczeliny Czasu”), „Zaklęty Las (SZC)”,
  „Erebu (SZC)”, „Zegarek Kieszonkowy”, „Handlarka Iluzji”, sześć misji SZC, potwory i przedmioty SZC
  (kopie w `cache/yohara/wiki/crack`);
- tr-wiki tam, gdzie pl-wiki milczy: „ZÇ: Jotun Thrym” (Yangi), „Zaman Çatlağı Heykeli”;
- Owsap v6.2.6: `crack_dawnmist_dungeon(_access).quest`, `data/dungeon/crack_dawnmist_dungeon`, `mob_proto` / `item_proto`
  (wiersze „TR:”), `group.txt` 6401–6408.

Pliki tego katalogu i wiersze bazy generuje `tools/yohara_crack/gen_ycrack.py` (poza tym README nie edytować ręcznie).
Rdzeń: Yohara (game3). Klient: `client-patches/client-2.0.30/tools/ycrack`. Silnik: `server-patches/szczelina`.

| indeks | miejsce | folder | teren | quest |
|---|---|---|---|---|
| 404 | Zaklęty Las (SZC) + Erebu (SZC) | metin2_map_boss_crack_dawnmist (3×4, baza 332800 1817600) | ten sam co Zaklęty Las (PB) (371) | `jotun_szc` |

Indeks: oficjalny 367 to u nas Obrona Statku; 404 jest wolny u nas, we wszystkich worktree i na liście Owsapa.
Baza jest oficjalna – na prawo od Płaskowyżu Iluzji. Prostokąt nie nachodzi na żadną mapę z atlasinfo klienta ani na
żaden `Setting.txt` serwera. W kliencie to mapa **kopiowana**: `ParentMapName "metin2_map_boss_awaken_dawnmist"`, czyli
nasz pełny folder lasu PB. GF wskazuje tu `metin2_map_dawnmist_dungeon_01`, którego nie ma w żadnym naszym kliencie.
Exe czyta Setting.txt, sektory (także attr.atr) i msenv z rodzica, a bazę mapy bierze z atlasinfo.

## Statua Szczeliny Czasu (20472, Płaskowyż Iluzji 103,90) – quest `szczelina_czasu`
- Wejście od 110 poziomu, tylko w grupie (co najmniej 2 ludzi; GM może wejść sam, maks. 8 osób). Otwiera przywódca,
  a cała grupa musi stać przy statui.
- Każdy członek grupy musi mieć **Zegarek Kieszonkowy** (31147). Zegarek znika przy pierwszym wejściu do nowej
  wyprawy. Sprzedaje go Handlarka Iluzji: 1, 10 i 100 sztuk po 25 000 Yang za sztukę. Wiki podaje za 100 sztuk
  2 300 000 – nasz sklep liczy cenę przedmiotu razy liczbę sztuk.
- Loch trwa 60 minut. Po zwycięstwie (po minucie) albo po czasie wszyscy wracają na płaskowyż, obok statui (106,96).
  „Wróć do lochu” zabiera do trwającej wyprawy.
- Codziennej misji przy statui nie ma – ani pl-, ani tr-wiki jej nie podaje. Misja Owsapa `crack_daily_boss` wymaga
  czterech bossów SZC.
- Panel lochów: `jotun_szc` (bilet: Zegarek Kieszonkowy, wejście na płaskowyżu obok statui).

## Zaklęty Las (SZC) – quest `jotun_szc`
Misje (każdy osobno, od nowa w każdej wyprawie; liczby i nagrody wg wiki):

| misja | NPC | zadanie | nagroda |
|---|---|---|---|
| Pierwszy rekonesans | Strażnik Lasu (SZC) | 50 Wojowników En-Tai (SZC-107) | 776 600 PD |
| Znajdź apteczkę | Strażnik Lasu (SZC) | Apteczka (SZC) od Druida En-Tai (SZC-111), 1 na 25 | 776 600 PD |
| Dostarcz apteczkę | do Zwiadowcy Lasu (SZC) | – | 5 582 500 PD i 10 Korzeni Gango |
| Drugi rekonesans | Zwiadowca Lasu (SZC) | 5 Metinów Drzewnych Stworzeń (SZC) | 7 766 000 PD |
| Zdobądź Rosy En-Tai | Zwiadowca Lasu (SZC) | 5 Ros od Niszczycieli En-Tai (SZC-113) | 7 766 000 PD i 10 Wody Young |
| Zabij władcę En-Tai | Badacz Lasu (SZC) | Szlachetne Drewno, a potem Drzewny Szmaragd od Władcy En-Tai (SZC) | 2 × 11 650 000 PD i Kamień Driad (SZC) |

Owsap ma tu inne liczby: 20 wojowników, 2 Metiny, 5 825 000 PD, bez ziół i z 200 000 Yang.

Władca En-Tai (SZC) stoi z obstawą (grupa Owsapa, 587,97, co 5 minut), a drugi sam na 300,300 – jak w lesie PB.

Przywódca Straży Lasu (SZC) prowadzi do **Erebu (SZC)**: rusza przywódca grupy, cała grupa musi stać przy nim, a każdy
oddaje Kamień Driad (SZC). Tam czeka Bagjanamu (SZC) (4272), a minutę po nim przychodzi **Jotun Thrym (SZC)** (4403:
wiatr, 135 poziom; przywołuje Niszczycieli En-Tai (SZC-125)).

## Drop i PD
- Według wiki „potwory nie dają dropu, ale dają więcej PD”. PD to wiersze „TR:” – więcej niż w PB. Dwa wiersze
  poprawiono wg pl-wiki: 4267 → 41 101, 4270 → 49 080.
- Drop wyłącza silnik (`server-patches/szczelina`): na mapie 404 nie wypada żaden przedmiot ani owoc rangi.
- Yangi upuszcza tylko Jotun Thrym (SZC): 10–27 mln (tr-wiki).
- Nie ma tu pliku dropu ani skrzyń. Odłamki Smoczego Kamienia z misji, o których pisze wiki, to system, którego u nas
  nie ma.
- Uzdrowicieli Ochao (SZC), których Owsap i tr-wiki przywołują przy 75/55/35/5% PŻ Jotuna, nie dodano – las PB też ich
  nie ma.

## Pliki
- `map/metin2_map_boss_crack_dawnmist/`: Setting.txt (Owsap = GF), Town.txt, server_attr (= lasu PB).
- `data/dungeon/jotun_szc/`: npc, regen, stone, boss – punkty Owsapa.
- `group.yohara_crack.txt`: grupy 6178–6184 i 6193 (Owsapa 6401–6408; 6408+ są u nas zajęte).
- `plateau_npc.txt`: wiersz statui w npc.txt płaskowyżu.
- `spawned.txt`: dla klienta.
- Baza:
  - `yohara_crack.sql`: 19 wierszy mob_proto i wiersze sklepu;
  - `yohara_items_crack.sql`: Zegarek Kieszonkowy, Kamień Driad, Szlachetne Drewno, Rosa En-Tai, Drzewny Szmaragd
    i Apteczka (SZC);
  - `yohara_crack_zywioly.sql`: wiatr.
