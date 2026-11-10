# MT2009 PLUS – Yohara Patcher

Osobny patcher klienta **Yohara (3.x)** z własnym serwerem aktualizacji na
naszym VPS-ie. Działa obok patchera klienta 2.x (`client-patches/patcher`,
`MT2009-Patcher.exe`) i z nim nie koliduje: każdy patcher pracuje tylko w
folderze „swojego” klienta i pobiera tylko ze „swojego” serwera.

| Co | Gdzie |
|---|---|
| Źródła (C# WPF, .NET Framework 4.8) | `MT2009-Yohara-Patcher/` |
| Logika aktualizacji (bez okna) | `MT2009-Yohara-Patcher/Core/` |
| Testy logiki na Linuksie | `MT2009-Yohara-Patcher.Tests/` |
| Budowanie (Docker) | `build.sh` |
| Grafika okna (z grafiki patchera 2.x) | `tools/grafika_yohara.py` |
| Generator serwera aktualizacji | `tools/make_mirror.py` |
| Gotowy program | `/opt/metin2/dist/aktualizacje/yohara/MT2009-Yohara-Patcher.exe` (+ `.sha256`) |
| Serwer aktualizacji | `/opt/metin2/dist/aktualizacje/yohara/` = `http://141.94.100.53/aktualizacje/yohara/` |

## Czym różni się od patchera 2.x (rozdzielenie)

| | Patcher 2.x | Patcher Yohary |
|---|---|---|
| Plik | `MT2009-Patcher.exe` (+ `.exe.config`) | `MT2009-Yohara-Patcher.exe` (sam exe; `.exe.config` opcjonalny) |
| Tytuł okna | MT2009 PLUS Patcher | **MT2009 PLUS – Yohara Patcher** |
| Wygląd | czerwono-pomarańczowy ogień | turkusowa ramka i iskry, nagłówek „YOHARA PATCHER”, wiersz „Klient Yohara 3.0.23 · kanał test”, ikona z „Y” |
| Serwer | `http://141.94.100.53/patcher/` (patchlist.json, MD5) | `http://141.94.100.53/aktualizacje/yohara/` (channels.json + manifest.json, SHA-256) |
| Folder | klient 2.x; **odmawia w folderze Yohary** | tylko klient Yohara; **odmawia w folderze 2.x** i w folderze bez klienta |
| Jedna kopia naraz | po nazwie procesu `MT2009-Patcher` | mutex `Local\MT2009PLUS-Yohara-Patcher-<folder>` (osobno dla każdego folderu) |
| Pliki w folderze gry | `MT2009-Patcher-kanaly.log`, `MT2009-Patcher-dbdata.log`, `MT2009-Patcher.exe.bak` | `MT2009-Yohara-Patcher.log`, `YOHARA_VERSION`, folder `.yohara-patcher\` (stan, części pobierania), `MT2009-Yohara-Patcher.exe.old` (chwilowo po samoaktualizacji) |
| Rejestr, AppData, %TEMP% | nie używa | nie używa (wszystko w folderze klienta) |
| Samoaktualizacja | z listy 2.x | tylko z serwera Yohary (`patcher` w manifeście) |
| Skrót na pulpicie | nie tworzy | nie tworzy |

Rozpoznanie klienta (to samo w obu patcherach): Yohara = plik `YOHARA_VERSION`
w folderze gry **albo** paczka tylko Yohary: `pack\hydra_map.index`,
`pack\balathor_map.index`, `pack\seoganland_map.index`. Klient Yohara z łatek
testowych (bez `YOHARA_VERSION`) jest więc rozpoznany od razu; po pierwszej
aktualizacji ma też `YOHARA_VERSION`. Folder z `pack\` bez tych znaczników =
klient 2.x.

Lista z serwera musi mieć znacznik `MT2009_PLUS_YOHARA_MIRROR_V1` i właściwy
kanał - lista 2.x (`client-files.json`, `update-manifest-mt2009.json`,
`patchlist.json`) jest odrzucana. Pliki są pobierane zawsze z
`<serwer>/files/<aa>/<sha256>` - adres buduje patcher, nie lista, więc nie
da się go skierować na GitHub ani na pliki 2.x. Nazwy plików patchera 2.x
(`MT2009-Patcher.exe*`) i list 2.x na liście Yohary są odrzucane.

Pliki gracza nigdy nie są publikowane ani ruszane: `*.cfg` (coop.cfg,
coop2.cfg, config.cfg…), `channel.inf`, `UserData\`, `screenshot\`, `mark\`,
logi, `syserr.txt`, `*.bak`, `*.tmp`.

## Dla gracza

1. Skopiuj `MT2009-Yohara-Patcher.exe` do folderu klienta **Yohara** (obok
   `metin2client.exe` i folderu `pack`). Klient 2.x zostaje ze swoim
   `MT2009-Patcher.exe` w swoim folderze - oba mogą być zainstalowane naraz.
2. Uruchom. Patcher sprawdza pliki, pobiera tylko zmienione, potem **GRAJ**.
3. **Napraw klienta** - sprawdza sumy SHA-256 wszystkich plików (ok. 3 GB,
   kilkanaście sekund) i pobiera uszkodzone / brakujące. Zwykłe uruchomienie
   jest szybkie: plik o tym samym rozmiarze i czasie zmiany co przy ostatnim
   sprawdzeniu nie jest liczony od nowa.
4. Gdy pobieranie się przerwie (sieć, zamknięcie okna), następne uruchomienie
   wznawia je od miejsca przerwania. Stary plik zostaje nietknięty, dopóki nowy
   nie jest cały i nie ma poprawnej sumy - wtedy jest podmieniany jednym ruchem.
5. Gra uruchomiona w trakcie = pliki zajęte → komunikat „zamknij grę i uruchom
   patcher ponownie”. Brak serwera → „możesz grać”.

Wymaga .NET Framework 4.8 (jest w Windows 10 1903+ i 11). Bez okna (testy,
zaawansowani): `MT2009-Yohara-Patcher.exe --cli [--napraw] [--kanal test|stable]
[--serwer URL] [--bez-samoaktualizacji] [--graj]` - kod wyjścia 0 = aktualny /
zaktualizowany, 1 = błąd, 2 = to nie folder Yohary, 3 = patcher podmieniony
(uruchom ponownie). `--kanal` i `--serwer` działają też z oknem; `--zrzut plik.png [sekundy]` zapisuje
obraz okna i kończy (testy pod Wine/Xvfb).

Okno: jak w patcherze 2.x - aktualności (z `news.json` serwera Yohary),
stan serwera z `coop.cfg` / `coop2.cfg` (strzałki ‹ ›), okno „Dodaj własny
serwer VPS”, strona i Discord. Bez przycisku kawy (`Vote4Coins` pusty). Nie
ma tu automatycznych danych bazy z panelu (`pack\dbdata` z DbDataSync) ani
kanałów CH3/CH4 z panelu (ChannelSync) - to mechanizmy wersji 2.x.

### `pack\dbdata` (pliki z edytora bazy danych)

`pack/dbdata.index` i `.data` mają na liście `"keep": true`: kopia gracza (zip
„Pobierz aktualne pliki klienta” z panelu jego serwera) wygrywa i „Napraw
klienta” jej nie przywraca. Patcher pobiera je tylko, gdy ich brak, albo gdy
serwer Yohary opublikuje **nową bazę** (inna suma niż ta, którą patcher
zapamiętał przy poprzednim uruchomieniu w `.yohara-patcher\stan.json`).
Przy pierwszym uruchomieniu patcher tylko zapamiętuje bazę - pliki gracza
zostają. Gracz, który chce bazę z serwera aktualizacji, usuwa oba pliki i
uruchamia patcher.

## Serwer aktualizacji (mirror)

`/opt/metin2/dist/aktualizacje/yohara/` - serwowany przez nginx kontenera
`mt2009plus-wiki` (istniejący blok `location ^~ /aktualizacje/`, katalog
zamontowany tylko do odczytu; konfiguracji nginx nie trzeba zmieniać).
Pliki 2.x w `/opt/metin2/dist/aktualizacje/` i `/opt/metin2/dist/patcher/`
nie są ruszane.

```
channels.json                 {"marker": "MT2009_PLUS_YOHARA_MIRROR_V1", "default": "test",
                               "channels": {"test": {"manifest": "test/manifest.json", "version": "3.0.23"}}}
test/manifest.json            wersja, wersja exe (1.3.3), pliki: path / size / sha256 / keep,
                              delete (pliki do usunięcia u graczy), patcher (version / size / sha256)
test/manifest-poprzedni.json  lista sprzed ostatniej publikacji (jej pliki zostają w magazynie)
stable/…                      to samo dla kanału stable (gdy powstanie)
files/<aa>/<sha256>           magazyn plików wg treści, bez kompresji (jak mirror 2.x:
                              paczki są już skompresowane); plik nigdy nie jest nadpisywany
news.json                     aktualności okna (generowane: wersja każdego kanału)
MT2009-Yohara-Patcher.exe     patcher do pobrania przez graczy (+ .sha256)
```

Pliki z gotowego klienta (`native-3.0.15` z webklienta, który się nie zmienia)
są w magazynie **twardymi linkami** - bez zajmowania miejsca drugi raz;
paczki z builda (`cY/out/pack`) są kopiowane (build je przebudowuje), ale
tylko te, których jeszcze nie ma w magazynie. Stan 10.11.2026: 522 pliki,
2,85 GB klienta, na dysku ok. 0,9 GB więcej.

### Publikacja po każdym buildzie klienta Yohara

Po `clientY.sh` + spakowaniu łatki (nowe `cY/out/pack`, ewentualnie nowe exe w
`yohara/exe-outNN`, sumy w `yohara/base-30NN/pack.sha256`):

```sh
cd /opt/metin2/git/wt-y-patcher/client-patches/yohara-patcher   # albo gałąź, na której to leży
python3 tools/make_mirror.py --kanal test --wersja 3.0.24 --wersja-klienta 1.3.3 \
    --zrodlo-link /opt/metin2/cache/webclient/work/inputs/native-3.0.15 \
    --zrodlo /opt/metin2/cache/cY/out/pack=pack \
    --zrodlo /opt/metin2/cache/yohara/exe-out24/metin2client.exe=metin2client.exe \
    --zrodlo /opt/metin2/dist/aktualizacje/test-plus/klient-test-yohara-3.0.24-latka.zip \
    --sprawdz /opt/metin2/cache/yohara/base-3024/pack.sha256=pack
```

- `--zrodlo` w kolejności, późniejsze wygrywa: folder (`FOLDER=pack` = folder
  wstawiony jako `pack/`), pojedynczy plik (`PLIK=ścieżka`) albo zip łatki
  (jej jeden folder główny i `LATKA-*-INSTRUKCJA.txt` są pomijane).
  `--zrodlo-link` = to samo, ale twarde linki (tylko dla folderu, który się
  nie zmienia w miejscu).
- `--sprawdz SUMY=pack` - każdy plik z `sha256sum` builda musi się zgadzać, inaczej
  nic nie jest publikowane.
- `--usun ścieżka` - plik do usunięcia u graczy (np. wycofana paczka).
- `--pomin WZORZEC`, `--zachowaj WZORZEC` (domyślnie `pack/dbdata.*`),
  `--bez-zachowania`.
- `--proba` - tylko pokazuje, co by zrobił.
- Lista, `channels.json` i `news.json` są zamieniane na końcu (`rename`), pliki
  w magazynie nigdy nie są nadpisywane, więc kto akurat pobiera, dokończy.
  Stare pliki (spoza bieżącej i poprzedniej listy każdego kanału) są usuwane
  (`--bez-sprzatania` - zostaw).
- Sumy plików źródłowych są zapamiętane w `/opt/metin2/cache/yohara-mirror-hashes.json`:
  ponowna publikacja trwa kilka sekund.

Test z vps1 (publiczny IP nie wraca na siebie): `curl http://127.0.0.1/aktualizacje/yohara/channels.json`.

### Kanały test / stable

Patcher bez ustawionego kanału bierze `default` z `channels.json`. Teraz jest
tylko `test` (3.0.23). Wydanie dla graczy:

```sh
python3 tools/make_mirror.py --kanal stable --domyslny --wersja 3.1.0 ... (te same źródła)
```

`--domyslny` przestawia wszystkich graczy bez ustawionego kanału na `stable`;
testerzy zostają na `test` przez `MT2009-Yohara-Patcher.exe --kanal test`
(skrót) albo `MT2009-Yohara-Patcher.exe.config` z `<add key="Channel" value="test" />`.

### Nowa wersja patchera

```sh
./build.sh                 # -> /opt/metin2/dist/aktualizacje/yohara/MT2009-Yohara-Patcher.exe + .sha256
TESTY=1 ./build.sh         # + testy logiki
```

potem `make_mirror.py ... --patcher /opt/metin2/dist/aktualizacje/yohara/MT2009-Yohara-Patcher.exe --wersja-patchera 1.0.1`
dla każdego kanału. Gracze dostaną go przy następnym uruchomieniu: patcher
pobiera nowy exe do `.yohara-patcher\tmp`, sprawdza sumę, zmienia nazwę
działającego na `.old`, wstawia nowy i uruchamia się ponownie (stary `.old`
jest kasowany). Bez `--patcher` lista zachowuje poprzedni wpis patchera.
Podnieś `AssemblyVersion` w `Properties/AssemblyInfo.cs`. Kompilacja jest
deterministyczna (ten sam kod = ten sam plik).

Budowanie: Docker `python:3.12-slim` + Pillow (grafika z `../patcher/MT2009-Patcher/resources`
do `MT2009-Yohara-Patcher/gen/`, poza gitem) i `mcr.microsoft.com/dotnet/sdk:8.0`
(jak patcher 2.x). Wspólny kod z patchera 2.x jest **podlinkowany**, nie
skopiowany: `CoopServer`, `ServerProbe`, `ChannelState`, `NewsItem`, `NewsSystem`,
`PicWarpper`, okno VPS, czcionki.

## Testy

```sh
docker run --rm --network host -v $PWD/..:/cp -w /cp/yohara-patcher/MT2009-Yohara-Patcher.Tests \
  mcr.microsoft.com/dotnet/sdk:8.0 sh -c 'dotnet run -c Release -- unit; \
    dotnet run -c Release -- update http://127.0.0.1/aktualizacje/yohara/ /t/klient [--napraw]'
```

- `unit` - atrapa serwera: ścieżki, odrzucanie list 2.x, rozpoznanie folderu,
  odmowa w folderze 2.x (bez żadnego połączenia), wznowienie po zerwaniu,
  serwer bez Range, plik uszkodzony na serwerze (stary nietknięty), `delete`,
  `keep` (dbdata), Napraw klienta, samoaktualizacja, nowszy schemat, brak
  kanału, brak serwera;
- `update` - prawdziwy przebieg na kopii klienta.

Prawdziwy exe można uruchomić pod Wine (obraz `mt2009/exebuild-msvc`, wine-mono):
`wine MT2009-Yohara-Patcher.exe --cli ...` (aktualizacja, naprawa,
samoaktualizacja, odmowa w folderze 2.x - sprawdzone 10.11.2026), okno z
`Xvfb`. Wygląd okna warto raz obejrzeć na prawdziwym Windowsie.
