# szczelina – Szczelina Czasu: w lochach Szczeliny Czasu nic nie wypada

`MT2009_PLUS_YOHARA_CRACK_V1` (14.10.2026, decyzja właściciela: „Statua Szczeliny Czasu na Płaskowyżu Iluzji, na razie
tylko jeden loch – Zaklęty Las”).

Wiki („Zaklęty Las (SZC)”, „Płaskowyż Iluzji” – rozdział „Statua Szczeliny Czasu”): „W tej lokacji potwory nie dają
dropu (…), ale w zamian dają więcej Doświadczenia”. Więcej PD dają same rzędy „TR:” w bazie
(`mariadb/playerbot/yohara_crack.sql`); brak dropu wymaga silnika, bo oprócz tabel dropu świat dorzuca swoje (wspólny
drop, księgi z Metinów, Skrzynie Księżycowe, Cor Draconis, szarfy, Kamień Przebudzenia z bossów, talizmany żywiołów,
owoce rangi, dropy questów).

Jedna zmiana w `char_battle.cpp`, `CHARACTER::Reward` (znaczniki `MT2009_PLUS_YOHARA_CRACK_V1 (no drop)`, `(rank
fruits)`, `(items)`): gdy potwór, Metin albo boss ginie na mapie 404 (Zaklęty Las (SZC)) lub w jej instancjach
(4040000+), po Yangach (`RewardGold` – tylko wiersz `mob_proto`, który je ma: Jotun Thrym (SZC), 10–27 mln wg tr-wiki
„ZÇ: Jotun Thrym”; reszta ma 0) funkcja kończy się – żadnego przedmiotu; owoce rangi też nie. PD, zabójstwa dla questów
(misje lasu), Karty Potworów i Przepustka Bitewna – bez zmian.

Same lochy to questy `szczelina_czasu` (statua na płaskowyżu) i `jotun_szc` (Zaklęty Las (SZC)) – bez zmian w silniku.

`MT2009_PLUS_YOHARA_CRACK2_V1` (21.10.2026, właściciel: „Szczeliny Czasu – 3 brakujące lochy”), dwie nowe zmiany (nowe
znaczniki, bo stare się nie nakładają ponownie):
- `(no drop maps)`: `Mt2009PlusTimeRiftNoDrop` obejmuje też mapy 405 (Grota Wygnańców 2 (SZC)), 406 (Twierdza
  Czerwonego Smoka (SZC)) i 407 (Strażnica Nemere (SZC)) z instancjami; Yangi z `mob_proto` ma tylko Beran-Setaou (SZC)
  (20 000 000, tr-wiki);
- `(damage)`: blok z `server-patches/przebudzeni` (Metin Chłodu (PB) 8135 – tylko Szaman, Kolumna Smoka Północy (PB)
  20538 – Szaman albo Ninja) obejmuje też bliźniaki SZC: Metin Chłodu (SZC) 8125 i Kolumnę Smoka Północy (SZC) 20518.
  Wymaga, by `przebudzeni` było nałożone wcześniej (tak jest w `Apply-MT2009PlusEngine.ps1` i w skrypcie wgrywania).

Lochy: `game/yohara_crack2`, questy `beran_szc`, `razador_szc`, `nemere_szc`.

`MT2009_PLUS_BOT_BONUS67_V1` (8.11.2026, właściciel: odłamki Seon-Hae w Zaklętym Lesie i w Szczelinie Czasu „z takimi
samymi procentami jak w Grocie Wygnańców”, drop światowy), zmiana `(rift shards)`: na mapach bez dropu `Reward` przed
`return` woła `Mt2009PlusSeonHaeRiftDrop` (`playerbot_seonhae.h`) – zwykły potwór mapy z listy `shard_map` (domyślnie
404) upuszcza z szansą `shard_chance` (0,5%, jak Grota) jeden odłamek w kolorze poziomów przedmiotów tej mapy
(`shard_pick`: Tęczowy 39077 ×3, Żółty Lśniący 39080 ×1, Święty 39081 ×1), z własnością zabójcy. Nic poza tym; mapy
405–407 nie są na liście – bez zmian.

Linux/VPS: `python3 apply_szczelina.py <game/src>`; Windows: `Apply-SzczelinaPatch.ps1 -SourceDir <game/src>` (wołane
przez `tools/port/Apply-MT2009PlusEngine.ps1`, po `skill9`). Plik silnika: `char_battle.cpp` (lista
`launcher/server-update-files.mod.txt`).
