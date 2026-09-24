---
title: Instalacja (Windows)
group: serwer
category: Serwer i administracja
order: 110
keywords: instalacja, docker, launcher, windows, pobierz, discord
---
## Skąd pobrać grę

Pełna paczka MT2009 PLUS (serwer + klient) jest do pobrania na naszym **Discordzie**: **[metin2sp.pl/discord](https://metin2sp.pl/discord)**. Aktualizacje launcher pobiera już sam z GitHuba.

## Czego potrzebujesz

- Windows 10 lub 11 (64-bit) z włączoną wirtualizacją (w BIOS/UEFI: Intel VT-x albo AMD SVM).
- [Docker Desktop](https://www.docker.com/products/docker-desktop/).
- Pełną paczkę MT2009 PLUS z Discorda.

Docker nie startuje i pisze o wirtualizacji? Zobacz [Problemy i FAQ](/mt2009plus/problemy/) – mamy skrypt, który to naprawia.

## Krok po kroku

1. Zainstaluj i uruchom **Docker Desktop**. Poczekaj, aż na dole po lewej pojawi się zielone *Engine running*.
2. Rozpakuj paczkę, najlepiej do ścieżki bez polskich znaków i spacji, np. `C:\Metin2Mod\`.
3. Uruchom **`Metin2-Launcher-GUI.bat`** z folderu `Serwer`.
4. Kliknij **1. ZAINSTALUJ / PRZYGOTUJ**, potem **2. GRAJ**. Pierwsze uruchomienie trwa od kilkunastu do kilkudziesięciu minut – Docker buduje serwer i tworzy bazę z botami. Nie zamykaj launchera w trakcie.
5. Zaloguj się w grze kontem **admin** / hasło **admin** (cztery postacie GM) albo załóż własną postać.

Po starcie działają dwa panele w przeglądarce:

| Adres | Co to jest |
|---|---|
| `http://127.0.0.1:7788` | panel klasyczny i mapa botów (`/map`) |
| `http://127.0.0.1:7790` | Seban Panel: gracze, SM, rankingi, gospodarka |

Hasła (baza, panel) launcher losuje przy pierwszym starcie i zapisuje w `linux-port\docker\.env` – tylko na twoim komputerze.

Windows blokuje `Metin2Distribute.exe`? Zobacz [Problemy i FAQ](/mt2009plus/problemy/).

## Aktualizacje

Launcher sam sprawdza aktualizacje przy starcie. Więcej: [Aktualizacje](/mt2009plus/aktualizacje/).
