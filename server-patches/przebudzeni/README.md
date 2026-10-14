# przebudzeni – Przebudzeni bossowie: kamienie, które rani tylko część klas

`MT2009_PLUS_YOHARA_PB_V1` (14.10.2026, decyzja właściciela: „Przebudzeni bossowie: Razador (PB) i Nemere (PB) – dodać
wg wiki”).

Wiki („Metin Chłodu (PB)”, „Kolumna Smoka Północy (PB)”, „Strażnica Nemere (PB)”):

- **Metin Chłodu (PB)** (8135, 6. piętro Strażnicy Nemere (PB)) – „Tylko Szaman może zbić tego Metina”;
- **Kolumna Smoka Północy (PB)** (20538, 9. piętro) – „Tylko Szaman i Ninja może zbić tego Metina”.

Silnik nie umiał tego z questa (quest nie zablokuje ciosu), więc jedna zmiana w `char_battle.cpp`,
`CHARACTER::Damage` (znacznik `MT2009_PLUS_YOHARA_PB_V1 (damage)`, przed blokadą Berana-Setaou): gdy ofiarą jest kamień
8135 albo 20538, cios zadaje tylko gracz-Szaman (przy kolumnie także Ninja). Każdy inny cios – innej klasy, zwierzaka,
trucizny czy ognia zostawionego przez kogoś – jest blokowany (`DAMAGE_BLOCK`), a gracz dostaje na czacie:
„Ten Metin moze zranic tylko Szaman.” / „Te Kolumne moze zranic tylko Ninja albo Szaman.”.

Reszta lochów (piętra, klucze tylko dla Szamana / Ninja, sobowtóry Szela, kolejność kostek i stel) to questy
`razador_pb`, `nemere_pb` i `przebudzeni_bossowie` – bez zmian w silniku.

Linux/VPS: `python3 apply_przebudzeni.py <game/src>`; Windows: `Apply-PrzebudzeniPatch.ps1 -SourceDir <game/src>` (wołane
przez `tools/port/Apply-MT2009PlusEngine.ps1`). Plik silnika: `char_battle.cpp` (lista
`launcher/server-update-files.mod.txt`).
