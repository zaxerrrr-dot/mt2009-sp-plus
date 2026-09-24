---
title: Konta GM i komendy
group: serwer
category: Serwer i administracja
order: 135
keywords: gm, admin, komendy, implementor, /item, /go, /reload
---
## Konto GM

Świeży świat ma konto **`admin`** (hasło **`admin`**) z czterema postaciami GM (IMPLEMENTOR) 90 poziomu: **Admin** (wojownik), **AdminNinja**, **AdminSura** i **AdminSzaman** – w pełnym ekwipunku +9, z koniem 21 poziomu, miksturami i Yang.

Jeśli serwer jest dostępny dla innych (VPS, COOP), **zmień hasło konta admin** – w COOP robi to przycisk **Zabezpiecz konta**.

Postać GM gra jak zwykły gracz: kupuje w sklepach, otwiera własny sklep i ma zwykłe zasady PvP. Znaczek GM zostaje.

## Nowy GM

W Seban Panelu (**Konta**) załóż konto z rangą (`LOW_WIZARD`, `GOD`, `HIGH_WIZARD`, `IMPLEMENTOR`). Nowa ranga działa po restarcie serwera albo po wpisaniu `/reload a` przez zalogowanego GM.

## Najważniejsze komendy

| Komenda | Działanie |
|---|---|
| `/item <id> [ilość]` | daje przedmiot |
| `/m <id>` | przywołuje potwora lub NPC |
| `/l <poziom>` / `/a <nick> <poziom>` | ustawia poziom sobie / graczowi |
| `/set <nick> gold <ilość>` | dodaje Yang |
| `/setsk <id> 59` | umiejętność na P |
| `/warp <nick>` / `/transfer <nick>` | przenosi do gracza / gracza do siebie |
| `/go s`, `/go t`, `/go m`, `/go d` | Sohan, Dolina Orków, Świątynia Hwang, Pustynia |
| `/go A`, `/go B`, `/go C` | M1 Shinsoo, Chunjo, Jinno (`A3`, `B3`, `C3` – M2) |
| `/purge` | usuwa potwory z okolicy |
| `/weak` | zaznaczonemu potworowi zostaje 1 HP |
| `/dc <nick>` | wyrzuca gracza z gry |
| `/pkmode 0/1/2` | tryb PvP: pokojowy / agresywny / wolny |
| `/priv_empire 0 4 <procent> <czas>` | czasowy bonus do doświadczenia |
| `/reload a` | wczytuje listę GM |
| `/xmas 1` / `/xmas 0` | dzień / noc |

## Komendy botów

| Komenda | Działanie |
|---|---|
| `/bot_spawn <id> <królestwo 1–3>` | wpuszcza bota (1 Shinsoo, 2 Chunjo, 3 Jinno) |
| `/bot_despawn <id>` | wylogowuje bota |
| `/bot_spawn_many <start> <ilość> <królestwo>` | wpuszcza wiele botów |
| `/bot_despawn_many <start> <ilość>` | wylogowuje wiele botów |
| `/bot_rank` | ranking poziomów botów (dla wszystkich) |

Pełna lista jest w Seban Panelu, w zakładce **Komendy GM**.
