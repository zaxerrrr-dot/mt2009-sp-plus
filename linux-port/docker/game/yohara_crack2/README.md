# Szczeliny Czasu: Grota Wygnańców 2, Twierdza Czerwonego Smoka i Strażnica Nemere (SZC) (MT2009_PLUS_YOHARA_CRACK2_V1)

Decyzja właściciela z 21.10.2026 (`cache/yohara/decyzje.md`, „Właściciel 21.10 – robimy”): „Szczeliny Czasu –
3 brakujące lochy”, „Jeśli czegoś nie wiesz – wszystko zgodnie z wiki”. Pierwszy loch Szczeliny – Zaklęty Las (SZC) –
to `../yohara_crack` (MT2009_PLUS_YOHARA_CRACK_V1).

Źródła:
- pl-wiki: „Statua Szczeliny Czasu”, „Grota Wygnańców 2 (SZC)”, „Świątynia Smoka (SZC)”, „Twierdza Czerwonego Smoka
  (SZC)”, „Strażnica Nemere (SZC)”, „Beran-Setaou (SZC)”, „Razador (SZC)”, „Nemere (SZC)”, „Generał Yonghan (SZC)”,
  „Kapitan Yonghan (SZC-110)”, „Kręty Klucz (SZC)”, „Duch Sura (SZC)” (kopie w `cache/yohara/wiki/crack`);
- tr-wiki tam, gdzie pl-wiki milczy: „ZÇ: Beran-Setaou” (20 000 000 Yang), „ZÇ: General Yonghan (110)” (klucz),
  „Zaman Çatlağı Nemere Gözlemevi” / „… Kırmızı Ejderha Kalesi” (piętra i strefy);
- arkusz właściciela z 20.10 (`Metin2_Moby_statystyki_EXP_i_drop.xlsx`): poziom, PŻ, PD, obrażenia i obrona każdego
  potwora SZC – zgodne co do liczby z wierszami Owsapa (sprawdzone);
- Owsap v6.2.6: `crack_skipia/flame/snow_dungeon.quest` (= questy PB z wierszami „TR:”), `data/dungeon/crack_*`,
  `mob_proto` / `item_proto`, `group.txt` / `group_group.txt` „crack_*”.

Pliki tego katalogu, trzy questy i wiersze bazy generuje `tools/yohara_crack2/gen_ycrack2.py` (poza tym README nie
edytować ręcznie). Rdzeń: Yohara (game3). Klient: `client-patches/client-2.0.30/tools/ycrack2`. Silnik:
`server-patches/szczelina` (nowe zmiany z tym znacznikiem).

| indeks | loch | folder | teren | quest | boss |
|---|---|---|---|---|---|
| 405 | Grota Wygnańców 2 (SZC) + Świątynia Smoka (SZC) | metin2_map_boss_crack_skipia (6×6, baza 0 1817600) | Grota Wygnańców 2 (PB) (398) | `beran_szc` | Beran-Setaou (SZC) 4400 |
| 406 | Twierdza Czerwonego Smoka (SZC) | metin2_map_boss_crack_flame (3×3, baza 153600 1817600) | nasza 351 / PB 369 | `razador_szc` | Razador (SZC) 4401 |
| 407 | Strażnica Nemere (SZC) | metin2_map_boss_crack_snow (4×3, baza 230400 1817600) | nasza 352 / PB 370 | `nemere_szc` | Nemere (SZC) 4402 |

Indeksy: oficjalne 364–366 są u nas zajęte (lochy Wukonga, Skorpiona, Wielkanocny) – stąd 405–407, wolne we wszystkich
worktree. Bazy oficjalne (GF = Owsap), tuż pod mapami PB; prostokąty nie nachodzą na żadną mapę z atlasinfo.
W kliencie każda mapa to **pełny folder** (teren bliźniaka PB skopiowany przy budowie, `ycrack2`) – nasz exe nie
czyta map kopiowanych (`ParentMapName`, zob. `tools/ycopymaps`).

## Wejście – Statua Szczeliny Czasu (quest `szczelina_czasu`)
Jak dla Zaklętego Lasu (SZC): od 110 poziomu, tylko w grupie (2–8 osób, GM sam), otwiera przywódca, wszyscy przy
statui, każdy ma **Zegarek Kieszonkowy** (znika przy pierwszym wejściu do nowej wyprawy), 60 minut, po zwycięstwie
(minuta) albo po czasie powrót na Płaskowyż Iluzji obok statui, „Wróć do lochu”. Do **Strażnicy Nemere (SZC)** w grupie
musi być Ninja i Szaman (Owsap, jak w PB). Kolejność w menu jak u Owsapa: Grota, Twierdza, Strażnica, Zaklęty Las.
Panel lochów: `beran_szc`, `razador_szc`, `nemere_szc`. Boty nie wchodzą (rdzeń Yohary, questy pomijają boty).

## Przebieg
Każdy loch to druga wersja lochu PB (Owsap: quest crack = quest awaken z wierszami „TR:”), więc questy powstają z
`beran_pb` / `razador_pb` / `nemere_pb` – te same etapy, pozycje i szanse, numery SZC, bilet Zegarek Kieszonkowy,
powrót przez flagi `szczelina_czasu`, napisy „(SZC)” i komunikat „Potwory Szczeliny Czasu nie dają dropu, ale dają
więcej PD”. Jedna różnica wg wiki:
- **Kręte Klucze (SZC)**: gdzie padnie Kapitan Yonghan (SZC), pojawia się Generał Yonghan (SZC) (SZC-116 4207 →
  4209, SZC-110 4208 → 4210); klucz (31160) zostawia **tylko 4210** – Generał po Kapitanie (SZC-110) (pl-wiki, tr-wiki
  „ZÇ: General Yonghan (110)”, arkusz właściciela: drop 4210). Owsap (i nasza grota PB) daje klucz z każdego Yonghana.
  Punkty Owsapa (Generałowie też stoją sami, co 70 s) zostają.
- Twierdza (SZC): Gardziel Am-heha (SZC) – sześć zadań w losowej kolejności (Złota Zębatka (SZC) 31167, Ignator (SZC)
  4229, Kamienie Maat (SZC) 31168, Metin Purgatorium (SZC) 8124), potem Razador (SZC).
- Strażnica (SZC): dziesięć pięter jak PB (Mroźny Klucz (SZC) 31169 – tylko Szaman; Gwiazdy Północy (SZC) 31170;
  Metin Chłodu (SZC) 8125 – rani go tylko Szaman; Klucz Lod. Kwiatu (SZC) 31171 – gdy zabija Ninja; Kolumna Smoka
  Północy (SZC) 20518 – rani ją tylko Ninja albo Szaman; Nemere (SZC)). Blokada ciosów: `server-patches/szczelina`.

## Drop i PD
- Wiki: „potwory nie dają dropu, ale dają więcej PD”. PD, PŻ i reszta to wiersze „TR:” (= arkusz właściciela).
- Silnik (`server-patches/szczelina`, `MT2009_PLUS_YOHARA_CRACK2_V1 (no drop maps)`): na mapach 405–407 nic nie wypada
  poza Yangami z `mob_proto` – ma je tylko **Beran-Setaou (SZC): 20 000 000** (tr-wiki). Razador / Nemere (SZC) – żadna
  wiki nie podaje Yangów, więc 0.
- Brak pliku dropu i skrzyń. Przedmioty zadań (klucze, zębatki, kamienie, gwiazdy) dają questy (`game.drop_item`) –
  to nie drop potwora, silnik ich nie blokuje. Odłamki Smoczego Kamienia z wiki – systemu nie mamy.
- Nowe przedmioty (`yohara_items_crack2.sql`): Kręty Klucz (SZC) 31160 (handel jak wiki), Złota Zębatka / Kamień Maat /
  Mroźny Klucz / Gwiazda Północy / Klucz Lod. Kwiatu (SZC) 31167–31171 – wiersze bliźniaków PB z „(SZC)”.

## Pliki
- `map/<folder>/`: Setting.txt (Owsap = GF), Town.txt, server_attr (= bliźniaka PB; sektor 000000 groty GF = PB).
- `data/dungeon/{beran_szc,razador_szc,nemere_szc}/`: punkty Owsapa (kamienie świątyni i grupę Berana stawia quest).
- `group.yohara_crack2.txt` (4201–4212, 6021–6031, 6071–6082), `group_group.yohara_crack2.txt` (4201–4207, 6021–6023) –
  numery Owsapa, u nas wolne.
- `spawned.txt`: dla klienta.
- Baza: `yohara_crack2.sql` (49 wierszy mob_proto: 41 potworów / Metinów, 8 NPC), `yohara_items_crack2.sql`
  (6 przedmiotów), `yohara_crack2_zywioly.sql` (grota błyskawica, twierdza ogień, strażnica lód; Metiny bez żywiołu).
