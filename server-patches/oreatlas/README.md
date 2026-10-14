# oreatlas – żyły rud nie są zaznaczane na mapie świata

`MT2009_PLUS_ORE_ATLAS_V1` (lista błędów z testów Yohary, 14.10.2026, punkt 5).

Na mapach Yohary żyły jadeitu (Żyła Jadeitu Słońca/Nocy/Dymu/Mgły, 30310–30313) pokazywały się na mapie świata (M)
jak NPC – zielone kropki z nazwą. W grze tak nie jest: rudy nie mają znaczników na mapie.

Skąd to się brało: rdzeń przy wczytywaniu `regen.txt`/`npc.txt` każdego potwora typu NPC (także portale i bramy)
dopisuje do listy znaczników mapy (`SECTREE_MANAGER::InsertNPCPosition`, wysyłanej klientowi pakietem pozycji NPC).
Żyły rud mają w `mob_proto` typ NPC, więc trafiały na tę listę.

Jedna zmiana w `regen.cpp` (znaczniki `MT2009_PLUS_ORE_ATLAS_V1 (atlas)` i `(declaration)`): obok ukrytego już NPC
20403 pomijany jest każdy potwór, który jest żyłą rudy według tabeli kopania (`mining::IsVeinOfOre` z `mining.cpp`
– żyły jadeitu Yohary i wszystkie inne). Samo kopanie, odradzanie żył i ich miejsca – bez zmian.

Linux/VPS: `python3 apply_oreatlas.py <game/src>`; Windows: `Apply-OreAtlasPatch.ps1 -SourceDir <game/src>` (wołane
przez `tools/port/Apply-MT2009PlusEngine.ps1`, po `szczelina`). Plik silnika: `regen.cpp` (jest już na liście
`launcher/server-update-files.mod.txt`).
