# MT2009 PLUS Patcher

Patcher klienta dla graczy: okno z animowanym tłem, aktualnościami, stanem
serwera i przyciskiem **GRAJ**. Sprawdza pliki klienta, pobiera tylko te,
które się zmieniły, i uruchamia `metin2client.exe`.

To jest **N2Play Patcher** autorstwa **[DEV]Akito** (© 2023), użyty za zgodą
autora i przystosowany do MT2009 PLUS. Wygląd i działanie są 1:1 jak w
oryginale - zmieniona jest tylko grafika z marką, teksty (po polsku), adresy
i rzeczy potrzebne naszej paczce (lista niżej). Informacja o autorze jest w
`Properties/AssemblyInfo.cs` (widać ją we Właściwościach pliku .exe).

| Co | Gdzie |
|---|---|
| Źródła (C# WPF, .NET Framework 4.8) | `MT2009-Patcher/` |
| Testy logiki na Linuksie | `MT2009-Patcher.Tests/` |
| Budowanie (Docker) | `build.sh` |
| Lista plików + pliki na serwer | `tools/generuj_patchliste.py` |
| Aktualności (źródło / generator) | `aktualnosci.md`, `tools/generuj_aktualnosci.py` |
| Grafika z marką | `tools/grafika.py` (+ `tools/oryginal/`, `tools/Cinzel.ttf`, licencja OFL) |
| Gotowy program | `/opt/metin2/dist/patcher-app/MT2009-Patcher.exe` + `.exe.config` |
| Serwer aktualizacji | `/opt/metin2/dist/patcher/` = `http://141.94.100.53/patcher/` |

## Dla gracza

1. Skopiuj `MT2009-Patcher.exe` (i `MT2009-Patcher.exe.config`) do folderu
   gry, obok `metin2client.exe`. Bez folderu `pack` obok patcher nic nie
   pobiera i prosi o przeniesienie.
2. Uruchom. Patcher sprawdza pliki (pasek "Sprawdzanie plików klienta"),
   pobiera brakujące/zmienione, potem **GRAJ** uruchamia grę i zamyka patcher.
3. Wymaga .NET Framework 4.8 - jest w Windows 10 (od 1903) i Windows 11.
   Nic nie trzeba instalować. `.exe.config` jest opcjonalny (bez niego
   działają te same adresy, wbudowane w program).

Przyciski: z lewej strona (metin2sp.pl), Discord, "Postaw kawę"
(buycoffee.to/mt2009plus); u góry z prawej: **serwer VPS**, (zębatka),
minimalizuj, zamknij. Zębatka uruchamia `config.exe` z folderu gry - klient
MT2009 go nie ma, więc zwykle jest ukryta, a jej miejsce zajmuje przycisk
serwera VPS.

### Własny serwer VPS

Przycisk z ikoną serwera otwiera okno **Dodaj własny serwer VPS** - takie
samo jak w MT2009-Aktualizatorze: dwa miejsca na liście serwerów w grze
(`coop.cfg` = 1, `coop2.cfg` = 2), nazwa + IP wystarczą, porty wpisane
domyślnie (logowanie 11000, CH1 13000, 2 kanały, CH2 = CH1 + 10), zapis,
poprawianie i usuwanie. Walidacja jest identyczna z aktualizatorem i z
`serverinfo.py` klienta (sprawdzone testami - niżej).

### Stan serwera

Nad przyciskiem GRAJ: nazwa serwera i **Logowanie / CH1 / CH2: ONLINE /
OFFLINE**. Patcher łączy się (TCP, limit 2 s) z portem logowania i portami
kanałów serwera z `coop.cfg` / `coop2.cfg` (gdy są oba - strzałki ‹ › przełączają),
a bez nich z localhost (127.0.0.1: 11000, 13000, 13010). Odświeżanie co 20 s i
po zamknięciu okna serwera VPS.

## Wydanie nowej wersji klienta na serwer patchera

Po zbudowaniu nowego klienta (paczki + `metin2client.exe`), na vps1:

```sh
cd /opt/metin2/git/mt2009-sp-plus/client-patches/patcher
python3 tools/generuj_patchliste.py --wyjscie /opt/metin2/dist/patcher \
    --zrodlo /opt/metin2/dist/klient/klient-test-<V>-pelny.zip \
    --zrodlo '/opt/metin2/cache/relout/metin2-client-update-<V>.zip::metin2client.exe,Dolacz.*' \
    --patcher /opt/metin2/dist/patcher-app
python3 tools/generuj_aktualnosci.py      # jeśli zmieniły się aktualności
```

- `--zrodlo` - zip albo folder; kilka źródeł, późniejsze nadpisują tę samą
  ścieżkę; po `::` lista plików/wzorców do wzięcia (domyślnie wszystko). Sam zip
  aktualizacji klienta też wystarczy: `--zrodlo .../metin2-client-update-<V>.zip`.
- `--patcher` - dokłada `MT2009-Patcher.exe` i `.exe.config` (samoaktualizacja
  patchera: gracz dostaje nową wersję przy następnym uruchomieniu).
- `--usun <ścieżka>` - plik do usunięcia u graczy (np. stara paczka).
- `--client-version <V>` - dokłada `CLIENT_VERSION` (dla MT2009-Aktualizatora);
  domyślnie nie, bo paczki testowe nie są wydaniem `<V>`.
- Pliki gracza nigdy nie trafiają na serwer: `*.cfg` (coop.cfg, coop2.cfg,
  metin2.cfg, config.cfg...), `UserData/`, `screenshot/`, `mark/`, logi,
  `syserr.txt`, `*.bak`, `*.tmp`.

Pliki leżą w `files/<md5>` (nazwa = suma MD5): nowa wersja nigdy nie
podmienia pliku, który ktoś właśnie pobiera, a `patchlist.json` jest
zamieniany na końcu jednym `rename`. Stare pliki są usuwane, ale te z
poprzedniej listy zostają (`patchlist-poprzednia.json`) - kto zaczął pobierać
tuż przed publikacją, dokończy. `patchlist-info.json` mówi, kiedy i z czego
zbudowano listę. Skrypt działa kilka sekund (216 MB).

Nowa wersja samego patchera: `./build.sh` (kopiuje do
`/opt/metin2/dist/patcher-app/`), potem powyższe polecenie z `--patcher`.
Kompilacja jest deterministyczna - ten sam kod daje ten sam plik, więc
przebudowanie bez zmian nie wymusza samoaktualizacji u graczy.

### Format listy (jak w oryginale)

`patchlist.json` - tablica JSON:

```json
[{"name": "pack\\root.data", "size": 4124928, "md5": "B1946AC92492D2347C6235B4D2611184",
  "uid": "b1946ac92492d2347c6235b4d2611184", "delete": 0}]
```

- `name` - ścieżka w folderze klienta, separator `\`;
- `size` - bajty; wpis z `size` 0 patcher pomija w całości (także `delete`);
- `md5` - MD5 pliku, 32 znaki **wielkimi literami** (patcher porównuje tekst);
- `uid` - plik pobierany jest z `Clientdata` + `uid`
  (`http://141.94.100.53/patcher/files/` + md5 małymi literami);
- `delete` - `1` = usuń ten plik u gracza.

Patcher pobiera plik, gdy go brak albo MD5 się różni. Plik o nazwie samego
patchera (`MT2009-Patcher.exe`) = samoaktualizacja: stary exe dostaje nazwę
`.bak`, nowy jest pobierany, patcher uruchamia się ponownie i usuwa `.bak`
(gdy pobieranie się nie uda - stary exe wraca na miejsce).

## Aktualności

Edytuj `aktualnosci.md` (opis formatu jest na górze pliku):

```
## AKTUALIZACJA | Klient 2.0.29
autor: 01.10.2026
link: https://metin2sp.pl/zmiany.php
data: 2026-10-01
Opis (nie jest wyświetlany, zostaje w JSON).
```

Typy: `WYDARZENIE`, `NOWOŚĆ`, `AKTUALIZACJA`. Tytuł krótki - okno mieści ok.
3 linie po ~12 liter (skrypt ostrzega powyżej 40 znaków). `autor` to
pomarańczowy tekst obok typu (tu: data), `link` - tytuł staje się klikalny.
Potem:

```sh
python3 tools/generuj_aktualnosci.py                     # -> /opt/metin2/dist/patcher/news.json
python3 tools/generuj_aktualnosci.py --changelog ../../CHANGELOG.md --ile 2   # + 2 najnowsze wpisy CHANGELOG
```

Patcher pobiera `news.json` przy każdym uruchomieniu; kolejność = kolejność w
pliku, kropki pod ramką = liczba wpisów (miejsca jest na ok. 10).
Format (`NewsItem` oryginału): `newsType` (0/1/2), `topic`, `creator`,
`threadUrl`, `date`, `message`, `avatarLink` - wyświetlane są typ, `creator`,
`topic` i link.

## Serwer WWW

Kontener `mt2009plus-wiki` (nginx:alpine, port 80 = publiczny port 80
dedyka) ma dodatkowo `/opt/metin2/dist/patcher` zamontowany tylko do odczytu
jako `/patcher`, a w `/opt/metin2/wiki-preview/nginx.conf` blok
`location ^~ /patcher/` (JSON z `charset utf-8` i `Cache-Control: no-cache`,
`files/` z `immutable`, bez listowania katalogów). Odtworzenie kontenera:

```sh
docker run -d --name mt2009plus-wiki --restart unless-stopped -p 80:80 \
  -v /opt/metin2/dist/wiki:/srv:ro \
  -v /opt/metin2/wiki-preview/nginx.conf:/etc/nginx/conf.d/default.conf:ro \
  -v /opt/metin2/dist/patcher:/patcher:ro nginx:alpine
```

Inny serwer (np. hosting metin2sp.pl): wgraj zawartość `/opt/metin2/dist/patcher/`
i zmień adresy `Clientdata`, `Patchlist`, `News` w `MT2009-Patcher.exe.config`
(albo `Config.DefaultServer` w `N2_Patcher/Model/Config.cs` i przebuduj).
Uwaga: `.exe.config` też jest na liście plików, więc nowy adres trafi do
graczy przez stary serwer - stary musi działać, aż wszyscy się zaktualizują.

## Ustawienia (`MT2009-Patcher.exe.config`)

| Klucz | Wartość | Uwagi |
|---|---|---|
| `Homepage`, `Discord`, `Vote4Coins` | adresy przycisków z lewej | pusty `Vote4Coins` = przycisk ukryty |
| `Clientdata`, `Patchlist`, `News` | serwer patchera | |
| `PatchServerSettingsCrypted` | `false` | `true` = te adresy zaszyfrowane (Rijndael z kluczem oryginału, `CryptoService`) |
| `CloseOnClientStart` | `true` | zamknij patcher po uruchomieniu gry |
| `Start` | `metin2client.exe` | gra (katalog roboczy = folder klienta) |
| `StartToken` | `false` | `true` = argument-token oryginału (MD5 klucza i godziny); klient MT2009 go nie używa |
| `Config` | `config.exe` | program zębatki; brak pliku = zębatka ukryta |
| `Slider`, `Stats`, `Update` | puste | oryginał czytał je, ale okno ich nie używało (`Stats` = JSON `ServerState`, zastąpiony sprawdzaniem portów; `Update` = zewnętrzny updater, zastąpiony samodzielnym restartem) |

## Budowanie

```sh
./build.sh                 # Docker mcr.microsoft.com/dotnet/sdk:8.0, ok. 10 s
TESTY=1 ./build.sh         # + testy "unit"
```

Projekt SDK (`net48`, `UseWPF`, `EnableWindowsTargeting`,
`Microsoft.NETFramework.ReferenceAssemblies`) kompiluje WPF dla .NET
Framework na Linuksie. `Newtonsoft.Json.dll` jest wbudowany w exe
(`App.ResolveEmbedded`) - gracz dostaje jeden plik. Exe ma ok. 37 MB,
prawie całość to 96 klatek animacji tła (jak w oryginale).

Grafika: `python3 tools/grafika.py` (Pillow) odtwarza `bg.png`,
`btn_play*`, `btn_vote*`, `btn_vps*` i `icon.ico` z oryginałów i tła wiki
`mt2009plus-tlo.webp`. Ramka z ogniem, przyciski, paski, ramka aktualności i
animacja (iskry) to grafika oryginału bez zmian.

## Testy (Linux)

`MT2009-Patcher.Tests` kompiluje te same pliki `N2_Patcher/Core/*.cs` i modele
co patcher (bez WPF):

```sh
docker run --rm --network host -v $PWD:/src -w /src/MT2009-Patcher.Tests mcr.microsoft.com/dotnet/sdk:8.0 \
  sh -c 'dotnet run -c Release -- unit; dotnet run -c Release -- patch http://127.0.0.1/patcher/ /tmp/k; \
         dotnet run -c Release -- news http://127.0.0.1/patcher/news.json; dotnet run -c Release -- probe'
```

- `unit` - lista (MD5, rozmiar 0, delete, niebezpieczne nazwy `..`), coop.cfg;
- `patch` - lista z serwera, pobranie wszystkiego, ponowne sprawdzenie = 0,
  uszkodzony + usunięty plik = 2 do pobrania;
- `news` - news.json z polskimi znakami;
- `probe` - stan serwera testowego na 127.0.0.1, zamknięty port, brak odpowiedzi, zła domena;
- `coop <cases.json> <dir>` / `read <pliki>` - wyniki jako JSON do porównania z
  `MT2009-Aktualizator.ps1` (`New-AktCoopConfig`, `Read-AktCoopConfig`) i z
  `__LoadCoopServer` z `serverinfo.py` (Python 2.7).

Okna WPF nie da się uruchomić na Linuksie - trzeba je raz obejrzeć na Windowsie.

## Zmiany względem oryginału

- Teksty po polsku (okno, komunikaty, typy aktualności WYDARZENIE / NOWOŚĆ /
  AKTUALIZACJA; autor wpisu przesuwa się za dłuższy polski typ).
- Grafika: nasze tło w ramce oryginału, "GRAJ", filiżanka zamiast "V4B",
  nowy przycisk serwera VPS w stylu przycisków okna, ikona z logo.
- Stan serwera (sprawdzanie portów) i okno serwera VPS - nowe.
- Adresy wbudowane w program (działa bez `.exe.config`), zębatka ukryta bez
  `config.exe`, gra startuje z katalogiem roboczym = folder klienta, bez tokenu.
- Samoaktualizacja bez zewnętrznego updatera; nieudane pobranie exe przywraca stary.
- Poprawki błędów: pusta pętla oczekiwania (100% jednego rdzenia) -> `Sleep`;
  błędy pobierania były ignorowane ("gra aktualna" mimo braków) -> komunikat z
  liczbą plików; brak serwera pokazywał "gra aktualna" -> "Serwer aktualizacji
  niedostępny - możesz grać."; lista, która nie jest JSON, wyłączała program;
  nazwy z `..` / ścieżką bezwzględną są pomijane; JSON zawsze jako UTF-8;
  klatki animacji dekodowane poza wątkiem okna; brak `StartupUri` i zły adres
  pierwszej klatki (błędy dekompilacji źródeł) poprawione; zamknięcie okna
  kończy proces.
