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
  biżuteria z 5 bonusami i mniej niż 2 dodatkowymi), 1–10 Odłamków poziomu przedmiotu, 0–5
  Suplementów. Szansa jak u Owsapa: `odłamki × 2 + suplement% × suplementy × odłamki / 50`, najwyżej
  100 (10 odłamków = 20%, z 5 Silnymi Suplementami 70%).
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
- **Przełącznik**: flaga `m2_seonhae_on` (apply.sh z `M2_SEONHAE`, domyślnie 0; strona „Seon-Hae”
  w panelu klasycznym na żywo przez `web_admin.quest` SEONHAE, tam też czas w minutach).
- GM: `/seonhae gm` (stan), `/seonhae gm now` (czas trzymanego przedmiotu na zero).

## Przedmioty (apply.sh, `world.item_proto`)

| vnum | nazwa | poziom przedmiotu |
|---|---|---|
| 39070 | Szary Odłamek | 0–29 |
| 39071 | Biały Odłamek | 30–39 |
| 39072 | Zielony Odłamek | 40–49 |
| 39073 | Żółty Odłamek | 50–59 |
| 39074 | Niebieski Odłamek | 60–74 |
| 39075 | Fioletowy Odłamek | 75–89 |
| 39076 | Czerwony Odłamek | 90–104 |
| 39077 | Tęczowy Odłamek | 105–119 |
| 39081 | Święty Odłamek | 120+ |
| 72064–72067 | Mały / Średni / Duży / Silny Suplement | +5 / 10 / 20 / 50 |

Lśniące odłamki Owsapa (39078–39080) należą do jego specjalnych zestawów – pominięte.

## Drop (decyzja właściciela, 1 października)

Tylko z Metinów (`IsStone`) i bossów (ranga boss/król) na mapach progresji: Grota Wygnańców V1 i V2
(72, 73), Świątynia Ochao (209), Zaczarowany Las (362) – także w ich instancjach (indeks / 10000).
Nigdzie indziej, bez sklepu i ItemShopu. Tylko dla prawdziwego gracza: właściciel dropu (zabójca,
którego dostaje `CreateDropItem` – największe obrażenia albo jego drużyna) nie może być botem;
przedmioty dołączają do listy dropu, więc padają z jego zwykłą własnością. Nic, gdy `m2_seonhae_on` = 0.

Reguły: `/opt/m2spool/seonhae_drops.tsv` (pisze go strona „Seon-Hae” panelu klasycznego), czytany
ponownie po zmianie (sprawdzany co najwyżej co 5 s); brak pliku albo brak sekcji = wartości domyślne:

```
map 72 39075 70        # map <indeks> <vnum odłamka> <waga>; mapa na liście = mapa z dropem
map 72 39076 30
map 73 39075 70
map 73 39076 30
map 209 39076 100
map 362 39076 70
map 362 39077 30
metin_shards 1 3       # Metin: 1-3 odłamki zawsze
metin_additive_chance 20
metin_additive 72064 60
metin_additive 72065 30
metin_additive 72066 10
boss_shards 3 6        # boss: 3-6 odłamków, 1-2 suplementy zawsze
boss_additives 1 2
boss_additive 72065 50
boss_additive 72066 35
boss_additive 72067 15
```

Błędny wiersz rdzeń pomija (syserr), panel go nie zapisze. Leże Smoka (208) nie jest na liście.
Klient: `client-patches/client-2.0.30/tools/seonhae` (wiersze item_proto, item_list, itemdesc).
