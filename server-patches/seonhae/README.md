# Seon-Hae: 6. i 7. bonus (1 października) – `MT2009_PLUS_SEONHAE_V1`

System Owsapa v6.2.6 (`__ATTR_6TH_7TH__`: `CHARACTER::Attr67Add`, `questlua_attr67add.cpp`,
`add_attr67.quest`, `uiattr67add.py`) tylko w wersji z NPC Seon-Hae (20095), bez klasycznego
przełącznika 71051, i **bez nowego exe**: zamiast pakietu 169 i okna `NPC_STORAGE` – nasz protokół
poleceń czatu (jak Poszukiwanie skarbów). Logika jest w nakładce
`linux-port/overlays/playerbot/src/game/src/playerbot_seonhae.h` (dołączonej do
`playerbot_manager.cpp`); tu są tylko zmiany plików silnika, opisane w `edits.json`:

| Znacznik | Plik | Co robi |
|---|---|---|
| `MT2009_PLUS_SEONHAE_V1 (declare)`, `(table)` | `cmd.cpp` | komenda `/seonhae` |
| `MT2009_PLUS_SEONHAE_V1 (command)` | `cmd_general.cpp` | `ACMD(do_seonhae)` → `SeonHaeCommand` z nakładki |
| `MT2009_PLUS_SEONHAE_V1 (drop)` | `item_manager.cpp` | `CreateDropItem` → `Mt2009PlusSeonHaeDrop` (po evencie podwójnego łupu, przed dropem z questów) |

- `Apply-SeonHaePatch.ps1` – Windows (`tools/port/Apply-MT2009PlusEngine.ps1`, po event managerze;
  kotwiczy na liniach goblina z playerqol);
- `apply_seonhae.py <game/src>` – Linux/VPS; oba czytają ten sam `edits.json`.

## Jak to działa

- **Rozmowa z Seon-Hae** (20095, pierwsze wioski) – quest `seonhae` (`linux-port/docker/game/quest/seonhae.quest`):
  opcja „Dodatkowy bonus (6. i 7.)”, gdy system jest włączony albo Seon-Hae trzyma przedmiot gracza;
  zapisuje `seonhae.npc_vid` / `seonhae.npc_time` i wysyła `SEONHAE open`. Boty – nigdy (`pc.is_bot()`,
  a rdzeń odrzuca każdy deskryptor bota).
- **Okno** (`uiseonhae.py` + `uiscript/seonhaewindow.py` w kliencie): przedmiot (broń, zbroja,
  biżuteria z 5 bonusami i mniej niż 2 dodatkowymi; biżuteria z jadeitu też – jej Precyzja i Wola to atrybut
  podstawowy, nie 6./7. bonus, `MT2009_PLUS_JADE_BASE_V1`, `server-patches/obreczjadeitu2`), 1–10 Odłamków poziomu przedmiotu, 0–5
  Suplementów. Szansa jak na wiki (`MT2009_PLUS_SEONHAE_WIKI_V1`, niżej): `odłamki × 2 + % suplementu ×
  sztuki`, najwyżej 100 (10 odłamków = 20%, z 5 Silnymi Suplementami 70%; 1 odłamek + 5 Silnych = 52%).
- **Rdzeń sprawdza wszystko jeszcze raz** (`/seonhae add <komórka> <odłamki> <komórka suplementu>
  <suplementy>`): flaga, NPC po vid na tej samej mapie w promieniu 25 m i rozmowa sprzed najwyżej
  30 min, żadnego handlu/sklepu/magazynu/kostki/okna, komórka ekwipunku, typ, 5 bonusów, < 2
  dodatkowe, pula rzadkich bonusów dla zestawu, przedmiot niezablokowany / nie na czas / nie unikat,
  vnum odłamka z tabeli poziomów (nie z klienta), liczby w limitach i w ekwipunku, suplement po
  vnumie (72064–72067: 5/10/20/50 – nie z proto). Dziury Owsapa zamknięte: liczby bez limitu, dowolny
  przedmiot jako „suplement”, odłamki zabrane przed ostatnim sprawdzeniem, przedmiot z 7 bonusami.
- **Seon-Hae trzyma przedmiot** (Owsap: 24 h; tu `m2_seonhae_wait_min`, 0 = 1440 min): przedmiot
  znika z ekwipunku, a jego pola (vnum, liczba, 3 sockety, 7 bonusów) są we flagach questa gracza
  (`seonhae.*`). Losowanie jest przy oddaniu (`seonhae.result`); `/seonhae collect` przy NPC po czasie
  odtwarza przedmiot (nowe id) i przy sukcesie dodaje bonus (`AddRareAttribute2`, jak 71051).
  Kolejność przy awarii: zniszczenie przedmiotu idzie do rdzenia db od razu, flagi zaraz potem
  (`ch->Save()`) – najwyżej strata, nigdy duplikat. Wyłączenie systemu zatrzymuje tylko nowe zlecenia.
- **Przełącznik**: flaga `m2_seonhae_on` (apply.sh z `M2_SEONHAE`, domyślnie 1 od 28.10.2026; strona „Seon-Hae”
  w panelu klasycznym na żywo przez `web_admin.quest` SEONHAE, tam też czas w minutach).
- GM: `/seonhae gm` (stan), `/seonhae gm now` (czas trzymanego przedmiotu na zero).

## Przedmioty (apply.sh, `world.item_proto`)

| vnum | nazwa | poziom przedmiotu |
|---|---|---|
| 39070 | Szary Odłamek | 0–29 |
| 39071 | Biały Odłamek | 31–39 (30: Szary Lśniący 39078) |
| 39072 | Zielony Odłamek | 40–49 |
| 39073 | Żółty Odłamek | 50–59 |
| 39074 | Niebieski Odłamek | 60–74 |
| 39075 | Fioletowy Odłamek | 76–89 (75: Zielony Lśniący 39079) |
| 39076 | Czerwony Odłamek | 90–104 (broń, zbroje, hełmy 96: Żółty Lśniący 39080) |
| 39077 | Tęczowy Odłamek | 106–119 (105: Żółty Lśniący 39080) |
| 39081 | Święty Odłamek | 120+ |
| 72064–72067 | Mały / Średni / Duży / Silny Suplement | +1 / 2 / 4 / 10% za sztukę (5 szt.: 5 / 10 / 20 / 50) |

Lśniące Odłamki (`MT2009_PLUS_SEONHAE_LUCENT_V1`, poprawka 3.0 #9 – tabela pl-wiki „6. i 7. bonus”): poziom przedmiotu dokładnie 30 – Szary Lśniący (39078), 75 – Zielony Lśniący (39079), 105 – Żółty Lśniący (39080: Zodiak, biżuteria 105, Talizmany Woli); Żółty Lśniący także do broni, zbroi i hełmów na 96. poziom (Smoka Mroku) oraz do talizmanów. Wypadają z potworów Yohary (`tools/yohara_items`, `tools/yohara_maps3`).

## Drop (decyzja właściciela, 1 października, poprawiona)

Suplementy tylko dla prawdziwego gracza: właściciel dropu (zabójca, którego dostaje `CreateDropItem` –
największe obrażenia albo jego drużyna) nie może być botem. Odłamki od 28.10.2026 także dla botów, z tymi
samymi regułami i szansami (`MT2009_PLUS_BOT_SEONHAE_V2`). Przedmioty dołączają do listy dropu, więc
padają z jego zwykłą własnością. Nic, gdy `m2_seonhae_on` = 0. Bez sklepu i ItemShopu. Instancje map
liczą się jak ich mapa (indeks / 10000).

- **Suplementy** – z Metinów (`IsStone`) i bossów (ranga boss/król) map z wiersza `additive_map`,
  każde zabicie losuje `additive_chance` (60%): Grota Wygnańców V1 i V2 (72, 73) – 1× Średni (72065),
  Zaklęty Las (353; do 3.x Zaczarowany Las Arezzo, 362 – usunięty) – 1× Duży (72066). Wiersz `mob` dotyczy jednego potwora (dowolnej rangi, na
  każdej mapie) zamiast reguły mapy: Beran-Setaou (2493) – 2× Średni. „Wróżki” (9707 Leśna Wróżka?)
  domyślnie nie ma – właściciel jeszcze nie wskazał potwora; wystarczy dopisać `mob 9707 72065 2`.
  Żadnych innych źródeł (Mały, Silny, Ochao) domyślnie.
- **Odłamki** – ze zwykłych potworów (nie Metin, nie boss/król) map z wiersza `shard_map`: Grota V2
  (73), Świątynia Ochao (209), Zaklęty Las (353); szansa `shard_chance` 0,5% (ułamki dozwolone),
  1 odłamek, kolor losowany z wag wierszy `shard` (domyślnie równo: 39070–39077, 39081).

Reguły: `/opt/m2spool/seonhae_drops.tsv` (pisze go strona „Seon-Hae” panelu klasycznego, która
sprawdza każdy wiersz), czytany ponownie po zmianie (sprawdzany co najwyżej co 5 s). Brak pliku albo
brak danego rodzaju wierszy = wartości domyślne (wiersze `mob` z pliku zastępują całą domyślną listę,
więc 2493 musi w nim zostać). Błędny wiersz rdzeń pomija (syserr). Domyślny plik:

```
additive_chance 60
additive_map 72 72065 1      # additive_map <mapa> <vnum suplementu> <liczba>
additive_map 73 72065 1
additive_map 353 72066 1
mob 2493 72065 2             # mob <vnum potwora> <vnum suplementu> <liczba>
shard_chance 0.5             # procent, ułamki dozwolone
shard_map 73
shard_map 209
shard_map 353
shard 39070 1                # shard <vnum odłamka> <waga>; tak samo 39071-39077 i 39081
```

## Szansa i poziom bonusu jak na wiki – `MT2009_PLUS_SEONHAE_WIKI_V1`

Właściciel, 20.10.2026: Seon-Hae „jak z wiki”.

**Szansa powodzenia** – pl-wiki „6. i 7. bonus”: każdy odłamek 2%, suplementy (najwyżej 5): Mały 1% (maks. 5%),
Średni 2% (10%), Duży 4% (20%), Silny 10% (50%) – za sztukę, niezależnie od liczby odłamków (wcześniej, jak u Owsapa,
suplement liczył się proporcjonalnie do odłamków: 1 odłamek + 5 Silnych = 7%). Tabela z wiki (5 suplementów):

| Odłamki | Mały ×5 | Średni ×5 | Duży ×5 | Silny ×5 |
|---|---|---|---|---|
| x1 | 7% | 12% | 22% | 52% |
| x2 | 9% | 14% | 22% | 54% |
| x3 | 11% | 16% | 24% | 56% |
| x4 | 13% | 18% | 26% | 58% |
| x5 | 15% | 20% | 28% | 60% |
| x6 | 17% | 22% | 30% | 62% |
| x7 | 19% | 24% | 32% | 64% |
| x8 | 21% | 26% | 34% | 66% |
| x9 | 23% | 28% | 36% | 68% |
| x10 | 25% | 30% | 38% | 70% |

Rdzeń i okno klienta (`uiseonhae.py`, ten sam wzór) liczą `odłamki × 2 + % × sztuki`: zgadza się z każdą liczbą
tabeli poza kolumną Dużego od x2 (wiki: 22, 22, 24 … 38 – powtórzone 22, przesunięcie o jeden; wzór i podane „4% za
sztukę” dają 24, 26 … 40).

**Poziom 6./7. bonusu** – wiki nie podaje szans poziomów. Seon-Hae losuje poziom tak samo jak Zaczarowanie 71051 i
71052: `AddRareAttribute` z szansami panelu (`m2_rare_lv1` … `m2_rare_lv5`, domyślnie 35/30/20/10/5,
`server-patches/rarelevelroll`), a nie stałą tabelą `AddRareAttribute2` 40/50/10/0/0 – poziomy 4–5 (maksima z wiki)
wchodzą też od Seon-Hae. Bonus jest losowany równo spośród dozwolonych (kolumna wagi nie jest tu używana).

Decyzja właściciela 21.10: Duży Suplement „zgodnie z wiki” – zostaje wzór z wiki (4% za sztukę: 24, 26 … 40), nie
liczby z kolumny tabeli (22, 22 … 38).
