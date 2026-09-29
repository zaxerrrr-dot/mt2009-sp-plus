# MT2009-Aktualizator - launcher/aktualizator samego klienta

Mały program dla graczy, którzy grają na cudzym serwerze VPS i nie potrzebują
launchera serwera. Leży w folderze klienta, obok `metin2client.exe`:

| Plik | Co robi |
|---|---|
| `MT2009-Aktualizator.bat` | Uruchamia okno (Windows PowerShell 5.1, `-ExecutionPolicy Bypass`, bez instalowania czegokolwiek). |
| `MT2009-Aktualizator.ps1` | Całe okno i logika (UTF-8 z BOM, WinForms). |
| `MT2009-Aktualizator.jpg` | Tło: grafika tła wiki (`wiki-src/plus/assets/mt2009plus-tlo.webp`) przeskalowana do 1280x720, z przyciemnionym dołem pod przyciski. WinForms nie wyświetla WebP. |
| `dodaj-do-paczki.py` | Narzędzie wydania (nie trafia do paczki) - dokłada powyższe pliki i `CLIENT_VERSION` do zip-a klienta i zapisuje `client-files.json` w korzeniu repo. |

## Co widzi gracz

- **GRAJ** - uruchamia `metin2client.exe` (katalog roboczy = folder klienta, bo
  klient czyta `coop.cfg` i `pack\` względnie). Jeśli jest aktualizacja, pyta:
  Tak = zaktualizuj i graj, Nie = graj bez aktualizacji.
- **Aktualizuj** - pobiera i instaluje nowego klienta; w trakcie pobierania
  zmienia się w **Anuluj**. Gdy nie udało się sprawdzić aktualizacji:
  **Sprawdź ponownie**.
- **Dodaj własny serwer VPS** - okno z dwoma miejscami na liście serwerów
  (`coop.cfg` = miejsce 1, `coop2.cfg` = miejsce 2), pokazuje co w nich jest,
  pozwala dodać, poprawić i usunąć serwer. Wystarczy nazwa i IP; porty są
  wpisane domyślnie (logowanie 11000, CH1 13000, 2 kanały) i można je zmienić.

## Jak działa aktualizacja

1. Manifest: `https://raw.githubusercontent.com/zaxerrrr-dot/mt2009-sp-plus/main/update-manifest-mt2009.json`
   (najpierw przez GitHub contents API, jak pełny launcher - raw ma 5 min cache),
   sekcja `client`: `version`, `url`, `sha256`, `size`. Tylko HTTPS.
2. Automatycznie przy starcie: lista plików `client-files.json` (korzeń repo,
   pobierana tak samo jak manifest) - wersja + `path`/`size`/`sha256` małych plików,
   które zmieniają się z każdym wydaniem: `metin2client.exe`, `Dolacz.*`,
   `pack/Index`, `pack/*.index` (bez dużych `.data` - ich `.index` zmienia się
   razem z nimi). Jeśli wersja listy = wersja klienta w manifeście, aktualizator
   haszuje te pliki (ok. 0,2 s): wszystkie zgodne = klient aktualny (i zapisuje
   `CLIENT_VERSION`), jakieś inne/brakujące = "Dostępna aktualizacja" z liczbą
   różnych plików. Na górze okna jest pasek stanu: zielony "Klient aktualny",
   żółty "Dostępna aktualizacja klienta X", czerwony "Nie udało się sprawdzić".
   Bez listy (niewydana, offline, inna wersja) - jak wcześniej: plik
   `CLIENT_VERSION` w folderze klienta; brak = wersja nieznana = aktualizacja
   zalecana. Nowszy `CLIENT_VERSION` (build testowy) nigdy nie jest cofany.
3. Gra uruchomiona z tego folderu (albo `metin2client` bez dostępnej ścieżki)?
   Pytanie "Zamknąć grę teraz?" - Tak zamyka ją (CloseMainWindow, po 10 s kill).
4. Sprawdzenie wolnego miejsca (~2,3 x rozmiar zip).
5. Pobieranie do `<klient>\MT2009-Aktualizator.tmp\aktualizacja.zip` - 3 próby co
   5 s (jak `Get-M2Download`), SHA-256 liczone w trakcie pobierania, pasek postępu
   z prędkością, możliwość anulowania. Potem kontrola rozmiaru i SHA-256.
   Niezgodność = nic nie jest zmieniane.
6. Rozpakowanie do `MT2009-Aktualizator.tmp\nowe` z ochroną przed ścieżkami
   `..`/absolutnymi (jak `Expand-M2SafeZip`), plik po pliku (antywirus wskazuje plik).
7. Podmiana: każdy stary plik jest przenoszony do `MT2009-Aktualizator.tmp\kopia`,
   nowy na jego miejsce (ten sam dysk, więc natychmiast). Błąd przy dowolnym
   pliku = wszystkie już podmienione pliki wracają na miejsce.
8. Pliki gracza nie są nadpisywane z zip-a (tylko tworzone, gdy ich nie ma):
   `coop.cfg`, `coop2.cfg`, `game1.cfg`, `metin2.cfg`, `config.cfg`,
   `syserr.txt`, `log.txt` oraz wszystko w `UserData\`, `screenshot\`, `mark\`.
9. Na końcu zapis `CLIENT_VERSION` i usunięcie `MT2009-Aktualizator.tmp`.
   Przerwana aktualizacja (np. zanik prądu) nie zapisuje wersji, więc przy
   następnym starcie jest proponowana ponownie i dokończona; resztki tmp są
   usuwane przy starcie.

Błędy są tłumaczone na polski: blokada antywirusa (fałszywy alarm, wykluczenie
folderu), plik w użyciu (gra w tle), brak prawa zapisu (Program Files, Ochrona
folderów przed ransomware), brak miejsca. Log: `MT2009-Aktualizator.log` w
folderze klienta. Jedno okno na folder klienta (mutex).

### Samoaktualizacja

Aktualizator jest w zip-ie klienta, więc aktualizacja podmienia go w trakcie
działania. To bezpieczne: PowerShell wczytał cały skrypt przed startem, obraz
tła jest wczytany do pamięci (plik nie jest trzymany otwarty), a `.bat` używa
`start` i kończy się od razu, więc `cmd.exe` go już nie czyta. Nowa wersja
działa od następnego uruchomienia.

Gdy okno się nie pokazuje: `MT2009-Aktualizator.bat konsola` uruchamia go z
widoczną konsolą PowerShella (widać błąd).

## Format coop.cfg / coop2.cfg

ASCII, CRLF, jak czyta `serverinfo.py` (`__LoadCoopServer`):

```
# MT2009 PLUS - serwer VPS (zapisane przez MT2009-Aktualizator)
name=Serwer Artura
host=203.0.113.10
auth=11000
channel=13000
channels=2
```

Walidacja jak w `Ustaw_serwer_VPS.bat` i w kliencie: nazwa - polskie znaki na
ASCII, inne akcenty usunięte, tylko drukowalne ASCII, `=` na `-`, maks. 80
znaków; host - IPv4 (4 oktety 0-255) albo domena (etykiety 1-63 znaki,
litery/cyfry/myślnik, nie na brzegach), `http(s)://` i `/` na końcu są
obcinane, `IP:port` jest odrzucany z komunikatem; porty 1-65535; CH2 = CH1 + 10
musi być <= 65535; port logowania nie może być portem kanału (CH1 ani CH2).

## Wydanie klienta - OBOWIĄZKOWO od teraz

Każdy zip aktualizacji klienta (`metin2-client-update-<V>.zip`) musi zawierać w
korzeniu, obok `metin2client.exe`, `Dolacz.bat`, `Dolacz.ps1` i `pack/`:

- `MT2009-Aktualizator.bat`
- `MT2009-Aktualizator.ps1`
- `MT2009-Aktualizator.jpg`
- `CLIENT_VERSION` (wersja klienta, np. `2.0.29`)

i **nie** może zawierać `coop.cfg` / `coop2.cfg`. Po zbudowaniu zip-a:

```
python3 client-patches/launcher-klienta/dodaj-do-paczki.py <sciezka>/metin2-client-update-<V>.zip <V>
```

Skrypt dokłada pliki (podmienia, jeśli już są), sprawdza BOM `.ps1` i brak
`coop*.cfg`, wypisuje `sha256` i `size` do sekcji `client` manifestu (licz je
dopiero po tym kroku) i **zapisuje `client-files.json` w korzeniu repo** - trzeba
go zacommitować razem z manifestem (dalej: dzielenie na `.part1/.part2`,
manifest, wydanie jak zwykle). Sama lista z gotowego zip-a:
`python3 client-patches/launcher-klienta/dodaj-do-paczki.py --tylko-lista <zip> <V>`
(tak powstała lista 2.0.28 z zip-a z release'u `klient-v2.0.28`). Dopóki lista
nie jest na `main`, aktualizator działa po staremu (tylko `CLIENT_VERSION`).

## Testy (Linux, Docker)

Logika jest nad sekcją `OKNO` i nie używa WinForms; `-TylkoFunkcje` kończy
skrypt przed oknem:

```
docker run --rm -v $PWD:/src:ro mcr.microsoft.com/powershell pwsh -NoProfile -Command \
  '. /src/MT2009-Aktualizator.ps1 -TylkoFunkcje; New-AktCoopConfig "Serwer" "203.0.113.10"'
```

Sprawdzone przy tworzeniu (2026-09-29): brak błędów `Parser::ParseFile`,
manifest (lokalny i prawdziwy z GitHuba, z BOM, błędny), porównanie wersji,
walidacja i zapis/odczyt `coop*.cfg` (pliki przepuszczone przez prawdziwe
`__LoadCoopServer` z `serverinfo.py`), aktualizacja z lokalnego zip-a (pliki
gracza zostają, `CLIENT_VERSION`, sprzątanie), zła suma / zły rozmiar, wycofanie
w połowie podmiany, zip ze ścieżką `..`, 404 z 3 próbami, anulowanie, pełne
pobranie prawdziwej paczki 2.0.28 z release'u `klient-v2.0.28` (SHA-256 zgodne)
samoaktualizacja z paczki z dołożonym aktualizatorem, a także lista plików:
klient rozpakowany z prawdziwego zip-a 2.0.28 = aktualny (i zapisany
`CLIENT_VERSION`), zmieniony jeden `.index` = aktualizacja (1 plik), brak listy /
lista innej wersji / nowszy build testowy = zachowanie jak wcześniej. Okna WinForms nie da
się uruchomić na Linuksie - trzeba je raz obejrzeć na Windowsie.
