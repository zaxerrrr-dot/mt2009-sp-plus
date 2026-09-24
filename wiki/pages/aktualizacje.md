---
title: Aktualizacje
group: serwer
category: Serwer i administracja
order: 125
keywords: aktualizacje, update, klient, serwer, github
---
Aktualizacje MT2009 PLUS przychodzą z naszego repozytorium na GitHubie ([zaxerrrr-dot/mt2009-sp-plus](https://github.com/zaxerrrr-dot/mt2009-sp-plus)), nigdy z oficjalnego – oficjalna paczka nadpisałaby modyfikacje.

- **Windows**: launcher sprawdza aktualizacje przy starcie. Możesz też kliknąć **SPRAWDŹ AKTUALIZACJE**. Serwer i klient aktualizują się osobno – jeśli w ogłoszeniu jest nowy klient, zaktualizuj oba. Przed aktualizacją klienta zamknij grę.
- **Linux / VPS**: `sh linux-port/tools/update.sh` z folderu serwera.

Aktualizacja nie rusza bazy: konta, postacie i boty zostają. Nie zmienia też `.env` (haseł i ustawień). Przed podmianą plików launcher robi ich kopię w folderze `backups`.

Paczki klienta zawierają wszystkie wcześniejsze zmiany, więc wystarczy zainstalować najnowszą.

Ogłoszenia o nowych wersjach pojawiają się na [Discordzie](https://metin2sp.pl/discord).
