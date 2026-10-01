# Poprawki silnika (1 października)

Zmiany silnika opisane w `edits.json`, każda z własnym znacznikiem:

| Znacznik | Plik | Co robi |
|---|---|---|
| `MT2009_PLUS_EARLY_PACKET_V1` | `input.cpp`, `input_login.cpp` | Komenda czatu albo szept, który przyszedł, zanim nowe połączenie przywitało się z serwerem (faza powitania) albo w trakcie ładowania postaci, jest pomijany w całości. Dotąd obie fazy czytały tylko nagłówek pakietu, a jego tekst brały za kolejne pakiety – nieznany nagłówek i zerwane połączenie. Okno Towarzysza (P) pyta serwer komendą `/towarzysz`, więc przy otwartym oknie zmiana kanału i teleport kończyły się powrotem do ekranu logowania. |
| `MT2009_PLUS_MAP_ALLOW_COPY_V1` | `config.cpp` | Lista map rdzenia w pakiecie startowym do bazy: granica `MAP_ALLOW_LIMIT` sprawdzana przed zapisem, nie po nim. Mapa ponad limit jest pomijana z błędem w syserr zamiast nadpisywać liczbę zalogowanych kont (śmieciowe logowania w bazie i nieskończone ładowanie przy pierwszym teleporcie). Limit to 48 (`MT2009_PLUS_MAP_ALLOW_48_V1`, playerqol); game1 układu „unified” ma dziś 36 map. |
| `MT2009_PLUS_AUTOHUNT_MINIBOSS_V1` | `cmd_general.cpp` | Auto Łowy: minibossowie (ranga S_KNIGHT – Chuong, Lykos, Scrofa, Bera, Tigris, Bestialski Łucznik, Bestialny Specjalista, elitarne potwory lochów) są celem przy „Moby” i przy „Bossy”. Przy „Bossy” idą zaraz po bossie, przed Metinem. |

## Pliki

- `edits.json` – zmiany (plik, znacznik, stary i nowy kod);
- `Apply-EngineFixesPatch.ps1` – Windows (`tools/port/Apply-MT2009PlusEngine.ps1`);
- `apply_enginefixes.py` – Linux/VPS; oba czytają ten sam `edits.json`.

Zmiana już nałożona (jest jej znacznik) jest pomijana; zmiana, której kodu nie
ma dokładnie raz, przerywa całość, zanim cokolwiek zostanie zapisane.
