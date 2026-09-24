---
title: Baza danych
group: serwer
category: Serwer i administracja
order: 165
keywords: baza danych, mariadb, navicat, heidisql, 3306
---
Baza MariaDB działa tylko lokalnie: host `127.0.0.1`, port `3306`. Login i hasło pokazuje przycisk **DANE DO BAZY (NAVICAT)** w launcherze. Połączysz się Navicatem, HeidiSQL albo DBeaverem.

Najważniejsze bazy: `account` (konta, SM w `account.cash`), `player` (postacie, przedmioty, proto), `log`.

Przy błędzie `1045 - Access denied` użyj **NAPRAW DOSTĘP DO BAZY** – postacie, przedmioty i boty zostają nietknięte.

Zmieniaj dane postaci, gdy jest wylogowana: serwer trzyma zalogowane postacie w pamięci i przy zapisie nadpisze zmiany z bazy. Boty też są zalogowanymi postaciami.
