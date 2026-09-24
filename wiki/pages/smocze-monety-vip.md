---
title: Smocze Monety i VIP
group: serwer
category: Serwer i administracja
order: 140
keywords: smocze monety, SM, nadawanie SM, cash, vip, itemshop
---
Smoczych Monet (SM) nikt nie sprzedaje – na własnym serwerze nadajesz je sam.

## W panelu (najprościej)

1. Otwórz **Seban Panel** (`http://127.0.0.1:7790`) → **Gracze**.
2. Wybierz postać.
3. W sekcji **Nadaj Smocze Monety** wpisz ilość i kliknij **Dodaj monety**.

Monety trafiają na **konto** tej postaci, więc widzą je wszystkie jego postacie. Obok jest **Nadaj VIP**, a w zakładce Zarządzanie – masowe nadawanie VIP.

## Przez bazę danych

SM to kolumna `cash` w tabeli `account.account`:

```sql
UPDATE account.account SET cash = cash + 1000 WHERE login = 'twoj_login';
```

Dane do bazy pokazuje launcher (**DANE DO BAZY (NAVICAT)**). Najlepiej zmieniać to, gdy postać jest wylogowana.

## W grze

Gracze zdobywają też **Kupony SM** z Metinów (domyślnie 3‰) i bossów (5%). Szanse ustawiają klucze `M2_DRAGON_COIN_STONE_PERMILLE` i `M2_DRAGON_COIN_BOSS_PERMILLE` w `.env`.
