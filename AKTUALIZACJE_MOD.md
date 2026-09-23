# Aktualizacje paczki moda

Launcher Windows, `linux-port/tools/update.sh` (VPS), panel admina (7788) i
updater Seban Panelu czytają aktualizacje **tylko** z repozytorium moda:

| Co | Skąd |
|---|---|
| Manifest (launcher, `update.sh`, updater Seban) | `https://raw.githubusercontent.com/zaxerrrr-dot/mt2009-sp-plus/main/update-manifest-mt2009.json` (najpierw przez GitHub API, CDN raw jako zapas) |
| Powiadomienie w panelu admina (7788) | `VERSION` i `CHANGELOG.md` z gałęzi `main` tego repozytorium |
| Powiadomienie w Seban Panelu (7790) | najnowszy GitHub Release tego repozytorium (tag `vX.Y.Z`) |
| Paczka ZIP | adres `url` z manifestu, zwykle załącznik GitHub Release |

Adres z oficjalnego repozytorium (`TieruYT/metin2-playerbots`) jest odrzucany.
Pusty `manifestUrl` zapisany w `.m2launcher.json` z czasów, gdy aktualizacje
były wyłączone, launcher sam zamienia na adres moda.

> [!IMPORTANT]
> Repozytorium musi być **publiczne**. GitHub nie wyda plików z prywatnego
> repozytorium bez logowania, więc launcher i `update.sh` dostałyby 404.

## Numer wersji

Aktualizatory porównują `VERSION` z dysku z `server.version` z manifestu
**dokładnie** (równe = aktualne), a panel porównuje je jako `X.Y.Z`. Dlatego
każde wydanie moda podnosi `VERSION` (np. `2.2.0` → `2.2.1` → `2.2.2`).
`MOD_VERSION` (`mod-3`, `mod-4`, …) to tylko etykieta — możesz ją podbijać
równolegle.

## Wydanie nowej wersji serwera (Windows)

W **pełnym folderze serwera moda** (tym z `VERSION`, `MOD_VERSION`,
`linux-port\`, silnikiem w `linux-port\docker\game\src\server\` itd.):

1. Wprowadź zmiany. Plik, którego nie ma w
   `launcher\server-update-files.mod.txt`, **nie trafi do graczy** — nowe pliki
   dopisz w sekcji „the mod's own files”.
2. Ustaw nową wersję w `VERSION` (np. `2.2.1`), podbij `MOD_VERSION` i dopisz
   na górze `CHANGELOG.md` sekcję `## 2.2.1 — RRRR-MM-DD` (panel pokazuje ją
   graczom przed aktualizacją).
3. Zbuduj paczkę:

   ```powershell
   powershell -ExecutionPolicy Bypass -File tools\New-M2UpdatePackage.ps1 `
     -Type server -Version 2.2.1 -SourceRoot . `
     -FileList launcher\server-update-files.mod.txt `
     -OutputDirectory ..\wydania `
     -DownloadUrl https://github.com/zaxerrrr-dot/mt2009-sp-plus/releases/download/v2.2.1/metin2-server-update-2.2.1.zip
   ```

   Skrypt odmówi, jeśli `VERSION` nie zgadza się z `-Version`. Wypisze SHA-256
   i zapisze `server-manifest-fragment-2.2.1.json`.
4. Na GitHubie utwórz **Release** z tagiem `v2.2.1` i dołącz
   `metin2-server-update-2.2.1.zip`.
5. **Dopiero potem** w repozytorium na `main` zaktualizuj
   `update-manifest-mt2009.json` (blok `server` z fragmentu), `VERSION`,
   `MOD_VERSION`, `CHANGELOG.md` i zmienione pliki źródłowe; commit i push.
   Od tej chwili launchery i serwery widzą nową wersję (API GitHuba po ok.
   minucie, CDN raw po do 5 minutach).

Przykładowy manifest:

```json
{
  "schema": 1,
  "channel": "stable",
  "publishedAt": "2026-09-30T00:00:00Z",
  "server": {
    "version": "2.2.1",
    "url": "https://github.com/zaxerrrr-dot/mt2009-sp-plus/releases/download/v2.2.1/metin2-server-update-2.2.1.zip",
    "sha256": "SKOPIUJ_Z_FRAGMENTU"
  }
}
```

Klienta aktualizuje się tak samo: `-Type client`, własna lista plików
(wzór: `launcher\client-update-files.example.txt`) i blok `client` w
manifeście. Bez bloku `client` launcher klienta nie rusza.

Dopóki manifest nie ma bloku `server`, launcher mówi, że w kanale nie ma
wersji, i niczego nie zmienia.

## Na serwerze Linux / VPS

```sh
cd /opt/metin2            # folder serwera (VERSION, linux-port/)
sh linux-port/tools/update.sh check   # co jest zainstalowane, co wydane
sh linux-port/tools/update.sh         # pobierz, sprawdź SHA-256, rozpakuj, zbuduj
```

Przycisk aktualizacji w panelu działa po włączeniu `M2_UPDATE_APPLY=1` w
`.env` i uruchomieniu updatera:
`docker compose --profile update up -d updater` (patrz `UPDATING.md`).
Inne repozytorium lub gałąź: zmienne `M2_UPDATE_REPO` i `M2_UPDATE_BRANCH`.

Baza danych (postacie, boty, przedmioty) nie jest ruszana przez żadną z tych
dróg.

## Istniejące instalacje

Instalacje z wersji moda, w której aktualizacje były wyłączone, mają stary
launcher i stary `update.sh`, które niczego nie pobiorą. Taka instalacja
musi **raz** dostać nowe pliki ręcznie (albo pełną nową paczkę):

- Windows: `launcher\Metin2Launcher.psm1`
- Linux: `linux-port/tools/update.sh`
- panele (powiadomienia): `files/admin_panel.py`,
  `linux-port/docker/panel/app/admin_panel.py`,
  `linux-port/docker/seban-panel/app.py`,
  `linux-port/docker/seban-panel/updater/update-mt2009.py`

Każda kolejna aktualizacja przychodzi już sama.
