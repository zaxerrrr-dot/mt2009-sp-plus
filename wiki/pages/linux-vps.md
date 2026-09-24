---
title: Instalacja na Linuksie / VPS
group: serwer
category: Serwer i administracja
order: 115
keywords: linux, vps, docker compose, env, instalacja
---
Na Linuksie serwer działa bez launchera, w Dockerze.

## Wymagania

- Linux x86 (Intel/AMD – **nie ARM**), np. Debian 12/13 albo Ubuntu 22.04/24.04.
- Docker z Compose.
- Co najmniej 4 GB RAM i ok. 40 GB dysku.

## Krok po kroku

1. Rozpakuj folder `Serwer` z pełnej paczki, np. do `/opt/metin2` (w środku ma być `VERSION`, `CHANGELOG.md` i `linux-port/`).
2. Skopiuj `linux-port/docker/.env.example` do `linux-port/docker/.env` i ustaw w nim hasła (`M2_DB_ROOT_PASSWORD`, `M2_DB_PASSWORD`, `M2_PANEL_PASSWORD`) oraz `M2_PUBLIC_ADDRESS` – adres, pod którym klient łączy się z serwerem.
3. Uruchom: `cd linux-port/docker && docker compose up -d --build`

Porty gry: **11000** i **13000–13002** (przy drugim kanale kolejne). Panele: **7788** i **7790**.

## Aktualizacja

Z folderu serwera: `sh linux-port/tools/update.sh` (`sh linux-port/tools/update.sh check` tylko pokazuje wersje). Więcej: [Aktualizacje](/mt2009plus/aktualizacje/).

**Nie używaj** instalatora ani aktualizatora z oficjalnego repozytorium Tieru – nadpisałyby modyfikacje MT2009 PLUS.

Nigdy nie uruchamiaj `docker compose down -v` – `-v` kasuje bazę ze wszystkimi postaciami i botami.
