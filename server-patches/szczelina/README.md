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
Kolejne lochy Szczeliny Czasu dopiszą swoje mapy do `Mt2009PlusTimeRiftNoDrop`.

Linux/VPS: `python3 apply_szczelina.py <game/src>`; Windows: `Apply-SzczelinaPatch.ps1 -SourceDir <game/src>` (wołane
przez `tools/port/Apply-MT2009PlusEngine.ps1`, po `skill9`). Plik silnika: `char_battle.cpp` (lista
`launcher/server-update-files.mod.txt`).
