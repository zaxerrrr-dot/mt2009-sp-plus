# Mapy Skipii: poprawna ścieżka zasobów

Klient miał dane `season2/metin2_map_skipia_dungeon_01` i
`season2/metin2_map_skipia_dungeon_02`, ale silnik ładował je przez pełną
ścieżkę `maps/season2/...`. Dla Groty V2 używa też wariantu
`maps/metin2_map_skipia_dungeon_02/...`. Paczka `maps` zawiera kompletne dane
pod wszystkimi trzema ścieżkami oczekiwanymi przez silnik.

Aktualizacja dodaje `pack/maps.data` i `pack/maps.index` oraz dopisuje paczkę
`maps` do `pack/Index`. Zachowuje istniejącą paczkę `season2` bez zmian.

`metin2_map_devilcatacomb` nie został dodany: w dostępnym kliencie Gameforge
jest tylko inna mapa `metin2_map_devilscatacomb` o rozmiarze 7×7, podczas gdy
serwer MT2009 Plus używa mapy 8×8. Nie można ich bezpiecznie zamienić.
