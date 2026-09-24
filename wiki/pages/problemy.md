---
title: Problemy i FAQ
group: serwer
category: Serwer i administracja
order: 170
keywords: problemy, faq, błędy, logi, diagnostyka, wirtualizacja, docker, wsl, smartscreen, defender
---
## Docker: „Virtualization support not detected”

Komunikat *„Docker Desktop failed to start because virtualisation support wasn't detected”* pojawia się, gdy wirtualizacja jest wyłączona w BIOS-ie **albo** gdy w Windows nie są włączone i zaktualizowane Platforma maszyny wirtualnej i WSL 2 – to częste nawet przy włączonym BIOS-ie.

### Szybko: skrypt Docker_WSL2_SMART

**[Pobierz Docker_WSL2_SMART.zip](/pobierz/Docker_WSL2_SMART.zip)**

Skrypt sprawdza wirtualizację i start hypervisora, włącza potrzebne składniki Windows, instaluje albo aktualizuje WSL do wersji 2 i mówi, co zrobić dalej. Niczego nie kasuje, nie restartuje komputera sam i nie zmienia BIOS-u.

1. Rozpakuj zip i uruchom `Docker_WSL2_SMART.bat`. Zgódź się na uprawnienia administratora.
2. Skrypt sprawdzi i skonfiguruje system. Jeśli instalator WSL o coś zapyta, odpowiedz w tym samym oknie.
3. Gdy zobaczysz **[RESTART]** – zapisz pracę, uruchom Windows ponownie i odpal ten sam plik jeszcze raz.
4. Po **[OK]** uruchom Docker Desktop.

Wymaga Windows 10/11 build 19041 lub nowszego. Log przebiegu: `%LOCALAPPDATA%\DockerWSL2Setup\Logs` – dołącz go przy zgłoszeniu problemu.

### Ręcznie

1. W BIOS/UEFI włącz **Intel Virtualization Technology** (Intel) albo **SVM Mode** (AMD).
2. W Windows wyszukaj „Włącz lub wyłącz funkcje systemu Windows” i zaznacz **Platforma maszyny wirtualnej** oraz **Podsystem Windows dla systemu Linux**. Uruchom ponownie.
3. W PowerShell jako administrator: `wsl --update` i `wsl --set-default-version 2`.

## Windows blokuje Metin2Distribute.exe

Komunikat SmartScreen / Inteligentnej kontroli aplikacji to fałszywy alarm Windows 11 dla plików bez firmowego certyfikatu.

1. Prawy przycisk na `Metin2Distribute.exe` → **Właściwości** → na dole zaznacz **Odblokuj** → OK.
2. **Zabezpieczenia Windows** → Ochrona przed wirusami i zagrożeniami → Zarządzaj ustawieniami → **Wykluczenia** → Dodaj wykluczenie → Folder → wybierz folder klienta.

Jeśli antywirus usunął plik przy rozpakowywaniu, dodaj wykluczenie i rozpakuj paczkę jeszcze raz.

## Serwer albo gra nie startuje

1. Kliknij **DIAGNOSTYKA** w launcherze.
2. Kliknij **ZBIERZ / WYŚLIJ LOGI** – powstanie zip z logami, hasła są w nim zamazane.
3. Wyślij go na [Discordzie](https://metin2sp.pl/discord) w kanale **błędy i bugi** z opisem problemu.

## Częste pytania

**Gdzie założyć postać, żeby grać z botami?**
W dowolnym królestwie – boty grają w Shinsoo, Chunjo i Jinno.

**Jakie jest konto testowe?**
Login `admin`, hasło `admin` – cztery postacie GM. Jeśli hostujesz COOP, launcher zmieni to hasło (**Zabezpiecz konta**).

**Jak zobaczyć boty na mapie w przeglądarce?**
**OTWÓRZ PANEL WWW** w launcherze albo `http://localhost:7788/map`.

**Jak zaktualizować serwer?**
**SPRAWDŹ AKTUALIZACJE** w launcherze. Postacie i baza zostają. Aktualizacja buduje serwer na nowo, co może potrwać kilkanaście minut – nie zamykaj okna. Więcej: [Aktualizacje](/mt2009plus/aktualizacje/).

**W ekwipunku nie widać nazw przedmiotów albo nowe przedmioty nie mają ikon.**
Zaktualizuj klienta: **AKTUALIZUJ KLIENTA** w launcherze.

**Nie mogę połączyć się z bazą.**
**NAPRAW DOSTĘP DO BAZY** w launcherze. Zobacz [Baza danych i pliki serwera](/mt2009plus/baza-danych/).

## Błąd w grze

Zgłoś go na Discordzie w kanale **błędy i bugi**: co robiłeś, na jakiej mapie, nazwa przedmiotu albo potwora, najlepiej ze zrzutem ekranu.
