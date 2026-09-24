---
title: COOP: gra ze znajomymi
group: serwer
category: Serwer i administracja
order: 155
keywords: coop, znajomi, hostowanie, kod zaproszenia, vpn, radmin, tailscale
---
COOP pozwala znajomym grać na twoim świecie przez internet. Każdy znajomy ma w nim własne konto.

## Host

W launcherze: **COOP: GRA ZE ZNAJOMYMI** (wymaga hasła dostępu do COOP), potem:

1. **Zabezpiecz konta** – zmienia hasła kont `admin` i `test` z paczki na nowe (launcher je pamięta – przycisk **Moje hasła**).
2. **Dodaj znajomego** – zakłada mu konto.
3. **HOSTUJ ŚWIAT** – launcher otwiera porty gry, ustawia router (UPnP) albo używa VPN (Radmin VPN, Tailscale, ZeroTier, Hamachi), dodaje regułę zapory i daje **kod zaproszenia** dla każdego znajomego.

**ZAKOŃCZ HOSTOWANIE** wraca do gry lokalnej.

## Znajomy

Potrzebuje tylko **klienta MT2009 PLUS**. Uruchamia `Dolacz.bat` w folderze klienta albo wkleja kod w oknie COOP launchera. Na liście serwerów pojawia się świat hosta jako **„Online: …”**.

## Gdy coś nie działa

Jeśli przy zmianie mapy zawiesza się ładowanie, router hosta nie obsługuje takiego połączenia. Wtedy najprościej hostować przez **Radmin VPN** albo **Tailscale**. Przycisk **Sprawdź sieć** w oknie COOP pokazuje, czy porty są otwarte.
