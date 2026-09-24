---
title: Smocze Monety i VIP
group: serwer
category: Serwer i administracja
order: 140
keywords: smocze monety, SM, nadawanie SM, cash, vip, itemshop
---
Smoczych Monet (SM) nikt nie sprzedaje – na własnym serwerze nadajesz je sam.

## Kupony SM

Kupon SM użyty w ekwipunku (prawy przycisk myszy) dopisuje Smocze Monety do konta.

| | Kupon | ID (vnum) | Daje | Komenda GM |
|---|---|---|---|---|
| <img src="/images/plus/80017.png" alt="" width="32" height="32"> | **Kupon SM (50)** | `80017` | 50 SM | `/item 80017` |
| <img src="/images/plus/80015.png" alt="" width="32" height="32"> | **Kupon SM (100)** | `80014` | 100 SM | `/item 80014` |
| <img src="/images/plus/80018.png" alt="" width="32" height="32"> | **Kupon SM (250)** | `80018` | 250 SM | `/item 80018` |
| <img src="/images/plus/80014.png" alt="" width="32" height="32"> | **Kupon SM (500)** | `80015` | 500 SM | `/item 80015` |
| <img src="/images/plus/80016.png" alt="" width="32" height="32"> | **Kupon SM (1000)** | `80016` | 1000 SM | `/item 80016` |

Na postaci GM wpisz komendę na czacie. Kilka kuponów naraz: `/item <id> <ilość>`, np. `/item 80016 5` daje pięć kuponów po 1000 SM.

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

Gracze zdobywają **Kupony SM** z Metinów (domyślnie 3‰) i bossów (5%). Szanse ustawiają klucze `M2_DRAGON_COIN_STONE_PERMILLE` i `M2_DRAGON_COIN_BOSS_PERMILLE` w `.env`.
