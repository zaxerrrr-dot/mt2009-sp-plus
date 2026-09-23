# Metin2 Playerbots – paczka modyfikacji

Serwer Metin2 z botami (na bazie projektu **metin2-playerbots**, silnik mt2009,
wersja 2.2.0) z naszymi modyfikacjami. Instaluje się i uruchamia dokładnie tak
samo jak oficjalne wydanie: lokalnie, na Windowsie, w Docker Desktop.

## Instalacja

1. Zainstaluj **Docker Desktop** (https://www.docker.com/products/docker-desktop/)
   i uruchom go.
2. Rozpakuj całe archiwum, np. do `C:\Metin2Mod\`. Ścieżka bez polskich znaków
   i spacji jest najbezpieczniejsza.
3. Uruchom **`Metin2-Launcher-GUI.bat`**.
4. Kliknij **1. INSTALUJ / PRZYGOTUJ**, potem **2. GRAJ**.
   Pierwsze uruchomienie trwa długo (kilkanaście–kilkadziesiąt minut):
   Docker buduje serwer ze źródeł i tworzy bazę z botami.

Hasła (baza, panel) są losowane przy pierwszym starcie i zapisywane w
`linux-port\docker\.env` – tylko na Twoim komputerze.

## Klient

Do gry potrzebny jest **nasz klient** (z nowymi kostiumami, mountami, petami
i przedmiotami). Oficjalny klient nie pokaże nowych przedmiotów.

## Aktualizacje

**Wyłączone.** Oficjalna aktualizacja nadpisałaby modyfikacje, więc launcher
i panele nie sprawdzają i nie pobierają aktualizacji z oficjalnego repozytorium.
Nowe wersje tej paczki będą wydawane osobno.

## Co zmienia ta paczka

**Przedmioty i systemy**
- Kostiumy, fryzury i nakładki na broń Gameforge 26.1.11 (ok. 2200 przedmiotów).
- Mounty z pieczęci (kostium wierzchowca, ok. 240 pieczęci, 129 modeli) z
  poprawioną prędkością ruchu; deski/chmury/łodzie pozwalają używać umiejętności.
- Proste pety (ok. 190), jeden naraz, bonusy z przedmiotu, powrót po relogu;
  pety oznaczone „(łup)” same podnoszą przedmioty i yang (tylko Twoje).
- Bonusy kostiumów: **Transformuj kostium** (70063, losuje 1–3 bonusy),
  **Zaczaruj kostium** (70064, zmienia wartości), **Transfer bonusów** (70065,
  u Kowala: przenosi bonusy z jednego kostiumu na drugi tego samego rodzaju).
  Do kupienia u Handlarki Różności.
- System Smoczych Kamieni (alchemia), Szarfy (kombinacja i przechwytywanie
  bonusów u Uriela), zestaw Władcy Śmierci, kostiumy Nosiciela Światła i Diademy,
  sklep kostiumów u Ah-Yu, Magma Manni.
- ItemShop w grze i ItemShop w przeglądarce z nowymi kategoriami (Fryzury +,
  Kostiumy, Nakładki na broń, Pety, Mounty); w przeglądarkowym przedmioty są
  filtrowane pod klasę i płeć postaci, z której otwarto sklep.
- Kosz na śmieci, podgląd dropu potworów, przełącznik eventu wielkanocnego
  w panelu.

**Boty**
- Płynniejsza praca serwera przy wielu botach (budżet czasu na turę).
- Boty trzymają zapas mikstur 27101/27104 zamiast wystawiać je na straganach.
- „Emerytura” botów z panelu (wymiana starych botów na nowe).

**Inne**
- Serwer wpuszcza klienta bez względu na jego wersję (brak blokady wersji).

## Kopia i powrót

Launcher ma przycisk **KOPIA ŚWIATA** – zapisuje cały świat do pliku zip.
Przycisk „Zatrzymaj i zapisz” nigdy nie usuwa postaci ani postępu botów.

## Licencja

Narzędzia projektu metin2-playerbots są na licencji MIT (plik `LICENSE`).
Kod serwera gry, dane gry i klient nie należą do autorów projektu ani do nas –
przeczytaj `NOTICE.md` przed dalszym udostępnianiem.
