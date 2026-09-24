---
title: FAQ – najczęstsze pytania
category: MT2009 PLUS
order: 1
keywords: faq, pytania, pomoc, autołowy, auto łowy, panel gm, f9, sm, smocze monety, aktualizacja klienta, docker, wirtualizacja, konto, rejestracja, boty, kostiumy, pety, mounty, szarfy, antyexp, mikstura stagnacji, koń, peleryna
---
Najczęstsze pytania z naszego [Discordu](https://metin2sp.pl/discord), z odpowiedziami krok po kroku. Nie ma tu twojego pytania? Zajrzyj do [Problemy i FAQ](/mt2009plus/problemy/) albo zapytaj na Discordzie.

**Szybki skok:**
[Konto](#jak-zalozyc-konto) ·
[Auto Łowy](#jak-uruchomic-auto-lowy) ·
[Panel GM (F9)](#jak-przywolac-bossa-metina-dac-sobie-poziom-albo-stworzyc-przedmiot) ·
[Aktualizacja klienta](#jak-zaktualizowac-klienta) ·
[Docker / wirtualizacja](#docker-virtualization-support-not-detected) ·
[SM dla siebie](#jak-doladowac-sobie-smocze-monety-sm) ·
[SM dla botów](#jak-dac-sm-wszystkim-botom) ·
[Liczba botów](#gdzie-zwiekszyc-liczbe-botow) ·
[Metiny i bossy](#jak-zwiekszyc-liczbe-metinow-bossow-i-potworow) ·
[Kostiumy, pety, mounty](#skad-wziac-kostiumy-pety-i-mounty) ·
[Koń](#jak-szkolic-konia) ·
[Zmianki i dodania](#skad-wziac-zmianki-i-dodania) ·
[Antyexp](#czy-jest-antyexp)

---

## Pierwsze kroki

### Jak założyć konto?

1. Uruchom serwer w launcherze (**GRAJ**).
2. W przeglądarce otwórz **[http://localhost:7788/register](http://localhost:7788/register)**.
3. Wpisz login i hasło i załóż konto.
4. Zaloguj się nim w grze.

Na start masz też gotowe konto **admin** / hasło **admin** z czterema postaciami GM.

### Jak zaktualizować klienta?

1. Uruchom launcher (`Metin2-Launcher-GUI.bat`).
2. Kliknij **WYBIERZ KLIENTA** i wskaż folder, w którym jest twój klient gry.
3. Kliknij **AKTUALIZUJ KLIENTA**.
4. Przed aktualizacją zamknij grę.

Serwer aktualizuje się przyciskiem **SPRAWDŹ AKTUALIZACJE**. Więcej: [Aktualizacje](/mt2009plus/aktualizacje/).

---

## W grze

### Jak uruchomić Auto Łowy?

Wciśnij **K**. Otworzy się okno Auto Łowów: ustawiasz umiejętności, mikstury, co bić (moby, Metiny, bossy) i co podnosić, a potem włączasz atak. Opis wszystkich opcji: [Auto Łowy](/mt2009plus/auto-lowy/).

### Jak przywołać bossa, Metina, dać sobie poziom albo stworzyć przedmiot?

Wciśnij **F9** – otworzy się **panel admina**. Przywołasz w nim potwory i Metiny, ustawisz poziom i stworzysz przedmioty z dowolnymi bonusami.

**Działa tylko na koncie z GM** (np. **admin** / **admin**). Na zwykłym koncie F9 nic nie robi. Komendy GM do wpisania na czacie: [Konta GM i komendy](/mt2009plus/gm/).

### Skąd wziąć kostiumy, pety i mounty?

Z **ItemShopu** w grze, za Smocze Monety (SM). Pełne listy z ikonami: [Kostiumy](/mt2009plus/kostiumy/), [Pety](/mt2009plus/pety/), [Wierzchowce](/mt2009plus/wierzchowce/).

### Jak przenieść bonusy z kostiumu na inny kostium?

U **Kowala**, przedmiotem **Transfer bonusów** (70065). Przenosi bonusy na kostium tego samego rodzaju. Więcej: [Bonusy kostiumów](/mt2009plus/bonusy-kostiumow/).

### Gdzie połączyć szarfy?

U NPC **Uriel** – łączenie szarf i transmutacja (przechwytywanie bonusów). Więcej: [Szarfy](/mt2009plus/szarfy/).

### Czy można bić z mounta?

**Nie ze wszystkich.** Z części wierzchowców bijesz normalnie, z innych nie. Na deskach, chmurach i łodziach działają też umiejętności. Więcej: [Wierzchowce](/mt2009plus/wierzchowce/).

### Jak automatycznie podnosić przedmioty i Yang?

Kup w ItemShopie **peta z łupem** – ma w nazwie **„(łup)”**. Sam podnosi twoje przedmioty i Yang. Lista: [Pety](/mt2009plus/pety/).

Auto Łowy też podnoszą łup – zaznaczasz, jakie rodzaje przedmiotów zbierać.

### Jak szkolić konia?

1. Od **25 poziomu** idź do **Stajennego** i bierz u niego misje konia.
2. Zbieraj **Medale Konne** (wypadają w Lochach Małp).
3. Oddawaj medale Stajennemu, żeby trenować konia.

Na łatwym poziomie trudności nie czekasz między treningami. Więcej: [Jeździectwo](/Systemy/jezdziectwo), [Stajenny](/NPC/stajenny), [Poziom trudności](/mt2009plus/poziom-trudnosci/).

### Jak używać peleryny przed 50 poziomem?

Daj sobie z konta GM **Pelerynę Męstwa**: na czacie wpisz `/i 39006`.

### Skąd wziąć zmianki i dodania?

- **Zmianki** (Zaczarowanie Przedmiotu) – z **ItemShopu**.
- **Dodania** (Wzmocnienie Przedmiotu) – z **Metinów i bossów z endgame'u**.
- Chcesz łatwiej? Włącz drop **Szkatułek Blasku Księżyca** (event w panelu – [Stawki i eventy](/mt2009plus/stawki-eventy/)). Z szkatułek wypadają zmianki i dodania.

### Czy jest antyexp?

**Nie.** Jest **Mikstura Stagnacji** – przez kilka godzin blokuje zdobywanie doświadczenia. Zrobisz ją z **receptury Mikstury Stagnacji** albo dasz sobie z konta GM: `/i 51784`.

---

## Smocze Monety (SM)

### Jak doładować sobie Smocze Monety (SM)?

1. Otwórz **[http://localhost:7790/players](http://localhost:7790/players)** (Seban Panel).
2. Kliknij swoją postać.
3. Przewiń w dół do **Nadaj Smocze Monety**, wpisz ilość i kliknij **Dodaj monety**.

Monety trafiają na całe konto. Inne sposoby i kupony SM: [Smocze Monety i VIP](/mt2009plus/smocze-monety-vip/).

### Jak dać SM wszystkim botom?

Wtedy boty swobodnie kupują kostiumy, pety i mounty, a świat wygląda kolorowo.

1. Otwórz **[http://localhost:7790/manage](http://localhost:7790/manage)**.
2. Wejdź w **Masowe nadawanie przedmiotów**.
3. Jako ID przedmiotu wpisz **80017** (Kupon SM 50).
4. Nadaj go **każdemu botowi**, np. **10 sztuk**.

Boty same użyją kuponów i zrobią zakupy w ItemShopie.

---

## Serwer i boty

### Gdzie zwiększyć liczbę botów?

- **Windows:** w launcherze kliknij **LICZBA BOTÓW (0–2500)**. Ustawisz liczbę na cały świat albo osobno dla Shinsoo, Chunjo i Jinno (0–1500 każde), a także drugi kanał (CH2).
- **Linux / VPS:** w panelu albo w `.env` (`PLAYERBOT_AUTOSPAWN_COUNT`).

Więcej botów to więcej pracy dla komputera – potrzeba więcej RAM i procesora. Więcej: [Boty: jak działają](/mt2009plus/boty/).

### Jak zwiększyć liczbę Metinów, bossów i potworów?

Otwórz **[http://localhost:7788/rates](http://localhost:7788/rates)** (strona **Stawki**):

- **Liczba potworów w respie** – od ×1 do ×4, osobno dla Metinów i bossów i dla zwykłych potworów.
- **Czas odradzania** – ×1 do ×10, szybsze odradzanie.

Więcej: [Stawki, respy i eventy](/mt2009plus/stawki-eventy/).

### Jak wyłączyć drop kamieni glyph?

Na postaci GM wpisz na czacie: `/e hc_drop 0`

---

## Docker: „Virtualization support not detected”

Docker Desktop nie startuje i pisze o wirtualizacji? Zrób po kolei:

**Najszybciej:** pobierz nasz skrypt **[Docker_WSL2_SMART.zip](/pobierz/Docker_WSL2_SMART.zip)**, uruchom go jako administrator i rób, co mówi (opis: [Problemy i FAQ](/mt2009plus/problemy/)). Albo ręcznie:

### Krok 1: sprawdź, czy wirtualizacja jest włączona

1. Wciśnij **Ctrl + Shift + Esc** – otworzy się Menedżer zadań.
2. Zakładka **Wydajność** → **Procesor (CPU)**.
3. Na dole po prawej znajdź pole **Wirtualizacja**:
    - **Włączone** → przejdź do kroku 3,
    - **Wyłączone** → zrób krok 2.

### Krok 2: włącz wirtualizację w BIOS/UEFI

1. Uruchom komputer ponownie. Przy starcie wciskaj **Del** albo **F2** (czasem **F10**, **F12** lub **Esc** – zależy od płyty głównej albo laptopa).
2. Poszukaj opcji w zakładce **Advanced**, **CPU Configuration** albo **OC** i ustaw ją na **Enabled**:
    - procesor **Intel**: `Intel Virtualization Technology` / `Intel VT-x`,
    - procesor **AMD**: `SVM Mode` / `AMD-V`.
3. Zapisz i wyjdź (najczęściej **F10**).

### Krok 3: włącz funkcje Windows

Uruchom **PowerShell jako administrator** (prawy przycisk na Start → „Windows PowerShell (Administrator)” albo „Terminal (Administrator)”) i wklej po kolei:

```
wsl --install --no-distribution
dism /online /enable-feature /featurename:VirtualMachinePlatform /all /norestart
bcdedit /set hypervisorlaunchtype auto
```

Potem **uruchom komputer ponownie**.

### Krok 4: uruchom Docker Desktop

Po restarcie włącz **Docker Desktop** i poczekaj, aż na dole po lewej pojawi się zielone **Engine running**. Teraz uruchom launcher MT2009 PLUS.

### Nadal nie działa?

- **Wirtualizacja już działa, a Docker chce nowszego WSL** – w PowerShell (administrator) wpisz `wsl --update` i uruchom komputer ponownie.
- **W BIOS-ie nie ma w ogóle opcji wirtualizacji** – zaktualizuj BIOS albo napisz na [Discordzie](https://metin2sp.pl/discord) model płyty głównej lub laptopa – pomożemy znaleźć właściwą opcję.

---

Nie znalazłeś odpowiedzi? [Problemy i FAQ](/mt2009plus/problemy/) · [Gra na MT2009 PLUS](/mt2009plus/gra/) · [Serwer i administracja](/mt2009plus/serwer/) · [Discord](https://metin2sp.pl/discord)
