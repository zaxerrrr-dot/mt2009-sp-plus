---
title: COOP: gra ze znajomymi
group: serwer
category: Serwer i administracja
order: 155
keywords: coop, znajomi, hostowanie, kod zaproszenia, vpn, radmin, tailscale, cgnat, dolacz
---
COOP otwiera twój świat dla znajomych przez internet – z twoimi botami, gospodarką i ustawieniami.

- **Host** to osoba z zainstalowanym serwerem (launcher + Docker), która udostępnia świat.
- **Znajomy** potrzebuje tylko klienta gry – bez Dockera, bez serwera i bez hasła COOP.
- Każdy znajomy ma w świecie hosta **własne konto**; jego postacie zapisują się u hosta.
- Host gra dalej jak zawsze (serwer „Metin2 SinglePlayer” na liście), a znajomi łączą się przez pozycję **„Online: <nazwa świata>”**.

COOP to funkcja eksperymentalna. Problemy zgłaszaj na [Discordzie](https://metin2sp.pl/discord) w kanale **błędy i bugi** razem z paczką logów z launchera.

## Hasło do hostowania

Hostowanie odblokowuje się w launcherze **hasłem COOP** – wpisujesz je raz, launcher je zapamięta. Skąd je wziąć, dowiesz się na naszym [Discordzie](https://metin2sp.pl/discord). Hasła potrzebuje tylko host; znajomym wystarczy kod zaproszenia. Nie wklejaj hasła na publicznych kanałach.

## Co potrzebuje host

- Windows 10/11 (64-bit), Docker Desktop i zwykłą instalację MT2009 PLUS.
- **Najnowszą wersję serwera i klienta** – znajomi muszą mieć klienta w tej samej wersji.
- Komputer, który uciągnie świat: serwer z botami działa u hosta. Serwer musi być włączony (**GRAJ**) przez cały czas gry; host nie musi być zalogowany.
- Sieć – jedna z trzech sytuacji:
    1. publiczny adres IPv4 i router z UPnP – launcher sam otworzy porty (najprościej);
    2. router bez UPnP – ręcznie przekieruj **TCP 11000 i 13000–13002** (z drugim kanałem także **13010–13012**) na komputer hosta;
    3. CGNAT albo brak publicznego adresu (częste w internecie mobilnym) – gra przez **VPN** (niżej).

Przycisk **Sprawdź sieć** w oknie COOP powie, która sytuacja jest twoja.

## Host krok po kroku

1. Zaktualizuj serwer i klienta, uruchom serwer (**GRAJ**).
2. W launcherze: **COOP: GRA ZE ZNAJOMYMI**, wpisz hasło COOP i kliknij **Odblokuj**.
3. **Sprawdź sieć** – czy możesz hostować wprost, czy potrzebny jest VPN.
4. **Zabezpiecz konta** – launcher zmienia hasła kont `admin` i `test` z paczki. Bez tego hostowanie się nie włączy (każdy w internecie znałby te hasła). Nowe hasła zobaczysz od razu, a później pod **Moje hasła** – wpisuj je w swoim kliencie.
5. **Dodaj znajomego** – wpisz nick, launcher założy mu konto z losowym hasłem.
6. Na liście **Połączenie** zostaw *Automatycznie* albo wybierz swój VPN. Kliknij **HOSTUJ ŚWIAT**: serwer gry uruchomi się ponownie (ok. minuty – wcześniej wyloguj się z gry), Windows zapyta o regułę zapory (kliknij *Tak*), a launcher otworzy porty w routerze. W logu przy portach ma być „otwarty”, nie „router odmówił”.
7. Zaznacz znajomego, kliknij **Kod zaproszenia** i wyślij kod **prywatnie** – zawiera jego hasło. Po zmianie sposobu hostowania (internet ↔ VPN) wyślij nowy kod.
8. Po graniu: **ZAKOŃCZ HOSTOWANIE** – zamyka porty i uruchamia serwer ponownie (znajomi zostaną rozłączeni).

Hostowanie zostaje włączone także po restarcie komputera – wystarczy **GRAJ**.

## Znajomy krok po kroku

1. Pobierz pełną paczkę z [Discorda](https://metin2sp.pl/discord) i rozpakuj – potrzebny jest folder `Klient`. Żeby mieć tę samą wersję co host, uruchom raz `Serwer\Metin2-Launcher-GUI.bat`: na pytanie o aktualizację serwera kliknij *Nie*, o klienta – *Tak* (albo **AKTUALIZUJ KLIENTA**). Docker nie jest do tego potrzebny.
2. Dostań od hosta **kod zaproszenia** – długi tekst zaczynający się od `M2COOP1:`.
3. Uruchom `Klient\Dolacz.bat`, wklej kod i kliknij **Dołącz**. Zobaczysz swój login i hasło (hasło trafi też do schowka). Z launchera to samo zrobisz w oknie COOP → **Mam kod zaproszenia**, bez hasła COOP.
4. Kliknij **Uruchom grę**, wybierz serwer **„Online: <nazwa świata>”** i zaloguj się.

Pozycja „Metin2 SinglePlayer” to świat na twoim własnym komputerze – bez własnego serwera się nie połączy i tak ma być.

## CGNAT – gra przez VPN

Jeśli **Sprawdź sieć** mówi o CGNAT albo podwójnym NAT, znajomi nie połączą się wprost i żadne ustawienie routera tego nie zmieni. Wtedy:

1. Host i wszyscy znajomi instalują ten sam program VPN: **Radmin VPN** (darmowy, najprostszy), Tailscale, ZeroTier albo Hamachi.
2. Host zakłada w nim sieć, znajomi dołączają (dane sieci host przekazuje prywatnie).
3. Host wybiera w oknie COOP na liście **Połączenie** swój VPN (np. Radmin VPN, adres 26.…) i klika **HOSTUJ ŚWIAT** – w routerze nic się wtedy nie otwiera. Nie ma VPN na liście? Zamknij i otwórz okno COOP, gdy VPN jest już połączony.
4. Kod zaproszenia zawiera adres z sieci VPN, a `Dolacz.bat` ostrzeże znajomego, jeśli nie ma włączonego VPN.

VPN musi być włączony u wszystkich za każdym razem, gdy gracie. Ruch przez VPN jest dodatkowo szyfrowany.

## Pytania

| Pytanie | Odpowiedź |
|---|---|
| Czy znajomy musi mieć Dockera albo serwer? | Nie, tylko klienta gry. |
| Czy znajomy potrzebuje hasła COOP? | Nie, wystarczy mu kod zaproszenia. |
| Czy host musi być w grze? | Nie, wystarczy włączony serwer i hostowanie. |
| Ilu znajomych mogę zaprosić? | Każdy dostaje osobne konto; granicą jest komputer i łącze hosta. |
| Czy postacie znajomych się zapisują? | Tak, w bazie świata hosta. |
| Czy znajomi widzą boty? | Tak, to ten sam świat. |
| Czy mogę zablokować znajomego? | Tak, przycisk **Zablokuj / odblokuj**. |
| Czy panel WWW jest widoczny z internetu? | Nie, panele i baza zostają tylko na komputerze hosta. |

## Gdy nie działa

- **„Nie można połączyć się z serwerem”** – host musi mieć włączony serwer i hostowanie; przy VPN wszyscy muszą być w tej samej sieci z włączonym programem.
- **Działało, a przestało** – adres hosta mógł się zmienić (np. po restarcie routera). Host generuje nowy **Kod zaproszenia**, znajomy wkleja go w `Dolacz.bat`.
- **Wymagana aktualizacja klienta** – klient znajomego jest starszy niż serwer hosta: zaktualizuj klienta.
- **Hostowanie się nie włącza, bo konta mają hasła z paczki** – najpierw **Zabezpiecz konta**.
- **Przy portach „router odmówił”** – router nie otworzył portów. Włącz w nim UPnP albo przekieruj ręcznie TCP 11000 i 13000–13002 na komputer hosta. FRITZ!Box: *Internet → Freigaben → Portfreigaben → Gerät für Freigaben hinzufügen* → ten komputer → zaznacz *Selbstständige Portfreigaben für dieses Gerät erlauben*, potem znów **HOSTUJ ŚWIAT**. Albo graj przez VPN.
- **Przy zmianie mapy zawiesza się ładowanie** (hosting przez internet) – router hosta nie obsługuje takiego połączenia; najprościej hostować przez Radmin VPN albo Tailscale.
- **Nadal nic** – zgłoś na Discordzie w kanale **błędy i bugi** z paczką logów (**ZBIERZ / WYŚLIJ LOGI**).

**Bezpieczeństwo:** kod zaproszenia zawiera hasło znajomego – nie wklejaj go publicznie. Połączenie gry nie jest szyfrowane, dlatego launcher daje znajomym losowe hasła tylko do tego świata. Nie używajcie tam haseł z innych miejsc.
