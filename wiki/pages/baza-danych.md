---
title: Baza danych i pliki serwera
group: serwer
category: Serwer i administracja
order: 165
keywords: baza danych, mariadb, navicat, heidisql, dbeaver, 3306, questy, drop, pliki serwera
---
## Połączenie z bazą

Baza MariaDB działa lokalnie. W Navicat, HeidiSQL albo DBeaver:

| Pole | Wartość |
|---|---|
| Host | `127.0.0.1` (albo `localhost`) |
| Port | `3306` |
| Użytkownik (pełny dostęp) | `root` – hasło `M2_DB_ROOT_PASSWORD` z `.env` |
| Użytkownik (bazy gry) | `metin2` – hasło `M2_DB_PASSWORD` z `.env` |

Na Windows hasła pokazuje przycisk **DANE DO BAZY (NAVICAT)** w launcherze – są losowane przy instalacji, każdy ma inne. Przy błędzie `1045 - Access denied` użyj **NAPRAW DOSTĘP DO BAZY**; postacie, przedmioty i boty zostają nietknięte. Na VPS zobacz [Instalacja na Linuksie](/mt2009plus/linux-vps/) (tunel SSH).

Najważniejsze bazy: `account` (konta, Smocze Monety w `account.cash`), `player` (postacie, przedmioty, `item_proto`, `mob_proto`), `log`.

## Edycja zawartości gry

**W bazie** (Navicat): przedmioty, konta, postacie, statystyki, sklepy. Zmiany w tabelach proto wchodzą po restarcie serwera (**ZATRZYMAJ I ZAPISZ** → **GRAJ**). Postać zmieniaj, gdy jest wylogowana – serwer trzyma zalogowane postacie (także boty) w pamięci i nadpisze zmiany.

**W plikach serwera**: dropy (`mob_drop_item.txt`), questy (`.quest`), mapy. Leżą w `linux-port\docker\game\src\serverfiles\share\locale\poland\`, ale są wkompilowane w obraz gry. Po edycji przebuduj obraz:

```sh
docker compose --project-directory linux-port\docker up -d --build
```

Przed przebudową zatrzymaj serwer (**ZATRZYMAJ I ZAPISZ**) – budowa potrzebuje dużo pamięci.

Uwaga: aktualizacja MT2009 PLUS może nadpisać zmienione pliki serwera. Zachowaj kopię swoich zmian.

W Dockerze nie ma serwera SSH do WinSCP – bazę edytujesz w Navicat, a pliki lokalnie na dysku z przebudową obrazu.
