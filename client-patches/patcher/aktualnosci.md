# Aktualności patchera MT2009 PLUS
#
# Każdy wpis zaczyna się od "## TYP | Tytuł". TYP: WYDARZENIE, NOWOŚĆ albo
# AKTUALIZACJA. Tytuł krótki (patcher pokazuje ok. 3 linie po ~12 liter).
# Pod nagłówkiem opcjonalnie: autor:, link:, data: (link = tytuł klikalny).
# Dalsze linie to opis - trafia do news.json, patcher go nie wyświetla.
# Po zmianie: python3 tools/generuj_aktualnosci.py (szczegóły w README.md).
#
# Wpisy AKTUALIZACJA (Serwer X.Y.Z / Klient X.Y.Z) NIE są tu wpisywane: przy
# każdym wydaniu tools/publish-update-mirror.sh bierze 4 najnowsze z
# CHANGELOG.md i stawia je przed wpisami z tego pliku.

## NOWOŚĆ | Własny serwer VPS
autor: MT2009 PLUS
Ikona serwera w prawym górnym rogu patchera: nazwa i IP serwera VPS, porty są wpisane domyślnie. Serwer pojawi się w grze jako "Online: nazwa".

## NOWOŚĆ | Nowy patcher MT2009 PLUS
autor: MT2009 PLUS
link: https://metin2sp.pl
Patcher sam sprawdza i pobiera nowe pliki klienta - wystarczy go uruchomić przed grą.
