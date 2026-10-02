# Poprawki silnika (1 października)

Zmiany silnika opisane w `edits.json`, każda z własnym znacznikiem:

| Znacznik | Plik | Co robi |
|---|---|---|
| `MT2009_PLUS_EARLY_PACKET_V1` | `input.cpp`, `input_login.cpp` | Komenda czatu albo szept, który przyszedł, zanim nowe połączenie przywitało się z serwerem (faza powitania) albo w trakcie ładowania postaci, jest pomijany w całości. Dotąd obie fazy czytały tylko nagłówek pakietu, a jego tekst brały za kolejne pakiety – nieznany nagłówek i zerwane połączenie. Okno Towarzysza (P) pyta serwer komendą `/towarzysz`, więc przy otwartym oknie zmiana kanału i teleport kończyły się powrotem do ekranu logowania. |
| `MT2009_PLUS_MAP_ALLOW_COPY_V1` | `config.cpp` | Lista map rdzenia w pakiecie startowym do bazy: granica `MAP_ALLOW_LIMIT` sprawdzana przed zapisem, nie po nim. Mapa ponad limit jest pomijana z błędem w syserr zamiast nadpisywać liczbę zalogowanych kont (śmieciowe logowania w bazie i nieskończone ładowanie przy pierwszym teleporcie). Limit to 48 (`MT2009_PLUS_MAP_ALLOW_48_V1`, playerqol); game1 układu „unified” ma dziś 36 map. |
| `MT2009_PLUS_AUTOHUNT_MINIBOSS_V1` | `cmd_general.cpp` | Auto Łowy: minibossowie (ranga S_KNIGHT – Chuong, Lykos, Scrofa, Bera, Tigris, Bestialski Łucznik, Bestialny Specjalista, elitarne potwory lochów) są celem przy „Moby” i przy „Bossy”. Przy „Bossy” idą zaraz po bossie, przed Metinem. |
| `MT2009_PLUS_ARROW_RANGE_V1` | `battle.cpp` | Strzały żywiołów (Ognista, Trująca, Lodowa, Przeklęta Strzała, 8006–8009) mają w `item_proto` zero w `value2`, `value4` i `value5`, a `CalcArrowDamage` osłabia strzał od `value4` do `value5` do `value2` procent – więc każdy strzał dalej niż z przyłożenia dawał 0 obrażeń (łucznik z taką strzałą nie zadawał żadnych). Strzała bez zakresu osłabienia (`value5` nie większe od `value4`) bije pełną siłą na każdą odległość, jak srebrna strzała w potwora. |
| `MT2009_PLUS_AUTOHUNT_CROWD_V1` | `cmd_general.cpp` | Auto Łowy wychodzą z tłumu: `/autohunt_target` przyjmuje ósmy argument (po VID-zie do pominięcia). `1` oznacza „najbliższy potwór, bez kolejności” – bez pierwszeństwa potwora, który bije postać, Metinu i bossa. Klient (`uiautohunt.py`) wysyła go, gdy postać w drodze do celu utknie w grupce potworów: po chwili bierze najbliższego zamiast dalej biec za pierwszym. Klient bez tej zmiany wysyła siedem argumentów i nic się nie zmienia. |

## Pliki

- `edits.json` – zmiany (plik, znacznik, stary i nowy kod);
- `Apply-EngineFixesPatch.ps1` – Windows (`tools/port/Apply-MT2009PlusEngine.ps1`);
- `apply_enginefixes.py` – Linux/VPS; oba czytają ten sam `edits.json`.

Zmiana już nałożona (jest jej znacznik) jest pomijana; zmiana, której kodu nie
ma dokładnie raz, przerywa całość, zanim cokolwiek zostanie zapisane.
