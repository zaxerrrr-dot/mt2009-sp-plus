---
title: Instalacja na Linuksie / VPS
group: serwer
category: Serwer i administracja
order: 115
keywords: linux, debian, ubuntu, vps, mini pc, docker compose, env, instalacja
---
Poradnik od czystego Debiana 13 do działającego serwera w najnowszej wersji. Na Ubuntu wygląda to tak samo (w repozytorium Dockera zamień `debian` na `ubuntu`). Na Linuksie nie ma okienkowego launchera – wszystko robisz w terminalu.

## 1. Czego potrzebujesz

- Maszyny z **Debianem 13** (VPS albo mini PC, z pulpitem albo bez) i kontem z `sudo`.
- Procesora **x86 (Intel/AMD)** – serwer gry nie działa na ARM.
- Co najmniej **4 GB RAM** i kilkanaście GB wolnego dysku (więcej przy tysiącach botów albo drugim kanale).
- Internetu – Docker pobiera obrazy bazowe, a serwer aktualizacje.
- Pełnej paczki MT2009 PLUS z [Discorda](https://metin2sp.pl/discord). Potrzebny jest tylko folder `Serwer`.

**Nie używaj** instalatora `installer/install.sh` ani aktualizatora z linii 1.x oficjalnego projektu. Nakładają pliki innej wersji silnika i psują działający serwer (m.in. stawki). Ten poradnik korzysta tylko z paczki i skryptu `linux-port/tools/update.sh`.

## 2. System i Docker

Aktualizacja systemu i narzędzia:

```sh
sudo apt-get update
sudo apt-get upgrade -y
sudo apt-get install -y ca-certificates curl gnupg unzip
```

Docker z oficjalnego repozytorium Dockera (w repozytorium Debiana bywa starsza wersja bez Compose v2):

```sh
sudo install -m 0755 -d /etc/apt/keyrings
sudo curl -fsSL https://download.docker.com/linux/debian/gpg -o /etc/apt/keyrings/docker.asc
sudo chmod a+r /etc/apt/keyrings/docker.asc
echo "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.asc] https://download.docker.com/linux/debian $(. /etc/os-release && echo "$VERSION_CODENAME") stable" | \
  sudo tee /etc/apt/sources.list.d/docker.list > /dev/null
sudo apt-get update
sudo apt-get install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin
sudo systemctl enable --now docker
```

Sprawdź, czy działa:

```sh
sudo docker run hello-world
sudo docker compose version
```

Pierwsza komenda wypisuje powitanie Dockera, druga numer wersji Compose (v2.x). W poradniku wszystkie komendy Dockera mają `sudo`. Jeśli dodasz się do grupy `docker` (`sudo usermod -aG docker $USER`, potem ponowne logowanie), używaj już wszędzie samego `docker` i nie mieszaj go z `sudo docker`.

## 3. Paczka serwera na maszynie

Plik zip wgrywasz na serwer z własnego komputera, np. `scp`:

```sh
scp MT2009-PLUS.zip UZYTKOWNIK@ADRES_SERWERA:~/
```

albo programem WinSCP / FileZilla. Jeśli masz bezpośredni link, możesz pobrać od razu na serwerze: `wget -O MT2009-PLUS.zip "LINK"`.

Rozpakuj tylko folder `Serwer` do `/opt/metin2/stack` (nazwę folderu w zipie sprawdź komendą `unzip -l`):

```sh
sudo mkdir -p /opt/metin2/_new
cd /opt/metin2/_new
sudo unzip -q ~/MT2009-PLUS.zip
sudo mv "/opt/metin2/_new/<folder paczki>/Serwer" /opt/metin2/stack
sudo rm -rf /opt/metin2/_new
cat /opt/metin2/stack/VERSION
```

W `/opt/metin2/stack` mają być m.in. `VERSION`, `linux-port/`, `launcher/` i `tools/`.

## 4. Plik .env

Cała konfiguracja jest w jednym pliku:

```sh
cd /opt/metin2/stack/linux-port/docker
sudo cp .env.example .env
sudo nano .env
```

Wystarczy sekcja **„1. REQUIRED”** na górze:

| Ustawienie | Co wpisać |
|---|---|
| `M2_PUBLIC_ADDRESS` | publiczny adres IP maszyny albo domena (`curl -4 ifconfig.me`). Bez tego klient zawiśnie na „łączenie z serwerem” |
| `M2_DB_ROOT_PASSWORD`, `M2_DB_PASSWORD` | dwa różne, długie hasła, np. z `openssl rand -hex 24` (bez spacji i cudzysłowów) |
| `M2_DB_PUBLISH_PORT` | zostaw `3306`, chyba że port jest zajęty |
| `M2_PANEL_PASSWORD` | możesz zostawić puste – panel wylosuje hasło przy pierwszym starcie |
| `PLAYERBOT_AUTOSPAWN_COUNT` | ile botów startuje z grą; na pierwszy start daj mniej, np. `50` – potem zmienisz w panelu |

`M2_COMPOSE_PROJECT_NAME` i `M2_CONTAINER_PREFIX` zostaw puste. Trzeba je ustawić dopiero przy drugiej, osobnej kopii serwera na tej samej maszynie.

## 5. Pierwsze uruchomienie

```sh
cd /opt/metin2/stack/linux-port/docker
sudo docker compose up -d --build
```

Pierwszy build kompiluje serwer od zera: od kilkunastu do kilkudziesięciu minut. Konsola może długo milczeć – to normalne.

## 6. Czy wszystko działa

```sh
sudo docker compose ps
```

Usługi mają status `Up` / `healthy`. Kontener `*-playerbot-migrate` kończy się raz (`Exited (0)`) – tak ma być.

Hasło panelu, jeśli zostawiłeś je puste:

```sh
sudo docker compose logs panel | grep -A4 PASSWORD
```

Panele: `http://ADRES_SERWERA:7788` (klasyczny, mapa botów) i `http://ADRES_SERWERA:7790` (Seban Panel). W grze: konto **admin** / **admin** z czterema postaciami GM – zmień to hasło, zanim serwer zobaczą inni.

Coś nie wstało? Najpierw logi:

```sh
sudo docker compose logs game --tail 80
sudo docker compose logs panel --tail 40
```

Porty gry: **TCP 11000** i **13000–13002** (z drugim kanałem także 13010–13012) – otwórz je w zaporze i u dostawcy VPS.

## 7. Baza danych z komputera (opcjonalnie)

Baza słucha tylko na `127.0.0.1` serwera.

- **Tunel SSH (bezpieczniej)** – w Navicat / HeidiSQL ustaw połączenie przez SSH do tej maszyny, a w nim `127.0.0.1:3306`.
- **Otwarty port (wygodniej, mniej bezpiecznie)** – obok `docker-compose.yml` utwórz `docker-compose.override.yml`:

```yaml
services:
  mariadb:
    ports: !override
      - "0.0.0.0:3306:3306"
```

i uruchom `sudo docker compose up -d`. Logujesz się jako `root` (hasło `M2_DB_ROOT_PASSWORD`) albo `metin2` (hasło `M2_DB_PASSWORD`). Wtedy bazę chroni tylko siła hasła – rób to świadomie.

## 8. Aktualizacja

```sh
cd /opt/metin2/stack
sudo sh linux-port/tools/update.sh check   # tylko pokazuje wersje
sudo sh linux-port/tools/update.sh run     # instaluje najnowszą
```

Skrypt pobiera paczkę MT2009 PLUS z naszego GitHuba, sprawdza jej sumę SHA-256, rozpakowuje (`.env` i `docker-compose.override.yml` zostają) i przebudowuje serwer. Bazy nie dotyka.

## 9. Przydatne komendy

```sh
sudo docker compose ps            # stan
sudo docker compose down          # zatrzymanie (baza zostaje)
sudo docker compose up -d         # start
sudo docker compose logs -f game  # logi gry
```

Czego nie robić:

- `docker compose down -v` – `-v` kasuje bazę danych.
- Starego `installer/install.sh` i aktualizatora z linii 1.x.
- Ręcznych zmian w `game/src/` bez przebudowy – zobacz [Baza danych i pliki serwera](/mt2009plus/baza-danych/).

Jeśli po aktualizacji coś nie wstaje: nic nie zostało skasowane, poprzednie obrazy są na dysku. Sprawdź logi, popraw i uruchom `sudo docker compose up -d --build` jeszcze raz.
