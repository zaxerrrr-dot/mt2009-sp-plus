---
title: Instalacja (Windows)
keywords: instalacja, docker, launcher, windows, grać
group: serwer
category: Serwer i administracja
order: 110
---
## Czego potrzebujesz

- Windows 10 lub 11 z włączoną wirtualizacją (w BIOS/UEFI: Intel VT-x albo
  AMD SVM).
- [Docker Desktop](https://www.docker.com/products/docker-desktop/).
- Pełną paczkę MT2009 PLUS (serwer + klient). Same aktualizacje z GitHuba
  nie wystarczą do pierwszej instalacji.

## Krok po kroku

1. Zainstaluj i uruchom **Docker Desktop**. Poczekaj, aż na dole po lewej
   pojawi się zielone *Engine running*.
2. Rozpakuj pełną paczkę, najlepiej do ścieżki bez polskich znaków
   i spacji, np. `C:\Metin2Mod\`.
3. Uruchom **`Metin2-Launcher-GUI.bat`**.
4. Kliknij **1. INSTALUJ / PRZYGOTUJ**, potem **2. GRAJ**. Pierwsze
   uruchomienie trwa od kilkunastu do kilkudziesięciu minut – Docker buduje
   serwer ze źródeł i tworzy bazę z botami. Nie zamykaj launchera w trakcie.

Po starcie działają dwa panele w przeglądarce:

| Adres | Co to jest |
|---|---|
| `http://127.0.0.1:7788` | panel administracyjny i mapa botów |
| `http://127.0.0.1:7790` | Seban Panel: mapa na żywo, profile botów, rankingi, gospodarka |

Hasła (baza, panel) launcher losuje przy pierwszym starcie i zapisuje
w `linux-port\docker\.env` – tylko na Twoim komputerze.

## Aktualizacje

Launcher sam sprawdza aktualizacje przy starcie. Możesz też kliknąć
**SPRAWDŹ AKTUALIZACJE** (serwer) i **AKTUALIZUJ KLIENTA** (klient). Przed
aktualizacją klienta zamknij grę.
