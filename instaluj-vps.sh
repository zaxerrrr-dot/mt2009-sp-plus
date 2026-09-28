#!/bin/sh
# =============================================================================
#  instaluj-vps.sh -- MT2009 PLUS na VPS jednym plikiem.
#
#  Na świeżym VPS (Debian lub Ubuntu, 64-bit x86, zalogowany jako root):
#
#      wget -O instaluj-vps.sh https://metin2sp.pl/wiki/pobierz/instaluj-vps.sh
#      sh instaluj-vps.sh
#
#  Co robi, po kolei:
#    1. sprawdza maszynę i doinstalowuje wget, unzip, curl, python3;
#    2. pobiera (wget) pełną paczkę serwera z metin2sp.pl (PACZKA_URL niżej,
#       inna: --paczka URL) i rozpakowuje ją do FOLDER (domyślnie
#       /opt/mt2009plus);
#    3. aktualizuje ją do najnowszej wersji z GitHuba: czyta
#       update-manifest-mt2009.json, pobiera paczkę aktualizacji serwera,
#       sprawdza jej SHA-256 i nakłada na folder;
#    4. uruchamia linux-port/tools/vps-install.sh install z paczki: Docker,
#       plik wymiany, .env z bezpiecznymi ustawieniami, budowa obrazów (pierwszy
#       raz 15-40 minut) i start serwera, losowe hasła kont admin i test;
#    5. na końcu pokazuje adres serwera, hasła i to, jak otworzyć panele.
#
#  Drugie uruchomienie niczego nie psuje: pobrana paczka nie jest pobierana
#  drugi raz, a vps-install.sh zachowuje .env i hasła.
#
#  Opcje:
#    --paczka URL     inny bezpośredni link do pełnej paczki (.zip albo .tar.gz)
#    --folder KATALOG gdzie ma stać serwer (domyślnie /opt/mt2009plus)
#    --address ADRES  publiczny adres serwera (domyślnie: odczytany IPv4 VPS)
#    --bots N         liczba botów (domyślnie według pamięci)
#    --bez-aktualizacji  zostaw wersję z pełnej paczki
#    --force          instaluj mimo małej pamięci albo dysku
#    --tylko-pliki    tylko kroki 1-3 (pliki gotowe w FOLDER), bez Dockera
# =============================================================================
set -u

# Pełna paczka serwera: BEZPOŚREDNI link do pliku (wget musi pobrać sam plik,
# nie stronę z przyciskiem "Pobierz").
PACZKA_URL=${M2_PACZKA_URL:-http://metin2sp.pl/MT2009-PLUS-Serwer-2.12.0.zip}
FOLDER=${M2_FOLDER:-/opt/mt2009plus}
REPO=zaxerrrr-dot/mt2009-sp-plus
BRANCH=main
MANIFEST=update-manifest-mt2009.json

ADDRESS=''
BOTS=''
UPDATE=1
FORCE=0
FILES_ONLY=0
WORK=''
WORK2=''
cleanup() { [ -n "$WORK" ] && rm -rf "$WORK"; [ -n "$WORK2" ] && rm -rf "$WORK2"; return 0; }
trap cleanup EXIT

say() { printf '\n\033[1;36m==> %s\033[0m\n' "$*"; }
info() { printf '    %s\n' "$*"; }
die() { printf '\n\033[1;31mBLAD: %s\033[0m\n' "$*" >&2; exit 1; }
have() { command -v "$1" >/dev/null 2>&1; }

while [ $# -gt 0 ]; do
    case "$1" in
        --paczka) [ $# -ge 2 ] || die "--paczka wymaga linku"; PACZKA_URL=$2; shift 2 ;;
        --folder) [ $# -ge 2 ] || die "--folder wymaga katalogu"; FOLDER=$2; shift 2 ;;
        --address) [ $# -ge 2 ] || die "--address wymaga adresu"; ADDRESS=$2; shift 2 ;;
        --bots) [ $# -ge 2 ] || die "--bots wymaga liczby"; BOTS=$2; shift 2 ;;
        --bez-aktualizacji) UPDATE=0; shift ;;
        --force) FORCE=1; shift ;;
        --tylko-pliki) FILES_ONLY=1; shift ;;
        -h|--help) sed -n '2,35p' "$0"; exit 0 ;;
        *) die "nieznana opcja: $1 (pomoc: sh $0 --help)" ;;
    esac
done

# ---- 1. maszyna ---------------------------------------------------------------
say "1/5 Sprawdzam VPS"
[ "$(id -u)" = 0 ] || die "uruchom jako root (albo: sudo sh $0)"
case "$(uname -m)" in
    x86_64|amd64) ;;
    *) die "serwer gry jest budowany jako 32-bit x86 - VPS $(uname -m) (np. ARM) się nie nadaje; wynajmij VPS x86_64" ;;
esac
have apt-get || die "ten instalator obsługuje Debiana i Ubuntu (apt-get)"
. /etc/os-release 2>/dev/null
info "System: ${PRETTY_NAME:-nieznany}, $(nproc 2>/dev/null || echo ?) CPU, $(awk '/MemTotal/ {printf "%.1f GB RAM", $2/1048576}' /proc/meminfo)"

need=''
for tool in wget unzip curl python3; do have "$tool" || need="$need $tool"; done
have tar || need="$need tar"
if [ -n "$need" ]; then
    info "Doinstalowuję:$need"
    DEBIAN_FRONTEND=noninteractive apt-get update -qq >/dev/null 2>&1
    # shellcheck disable=SC2086
    DEBIAN_FRONTEND=noninteractive apt-get install -y -qq $need ca-certificates >/dev/null 2>&1 \
        || die "nie udało się zainstalować:$need"
fi

# ---- 2. pełna paczka ----------------------------------------------------------
say "2/5 Pełna paczka serwera"
installer() { printf '%s/linux-port/tools/vps-install.sh' "$FOLDER"; }
if [ -f "$(installer)" ] && [ -f "$FOLDER/VERSION" ]; then
    info "Serwer już jest w $FOLDER (wersja $(tr -d ' \r\n' < "$FOLDER/VERSION")) - nie pobieram drugi raz."
else
    [ -n "$PACZKA_URL" ] || die "brak linku do pełnej paczki - podaj go: sh $0 --paczka https://.../paczka.zip"
    mkdir -p "$FOLDER" || die "nie mogę utworzyć $FOLDER"
    WORK=$(mktemp -d /tmp/mt2009plus.XXXXXX) || die "mktemp"
    info "Pobieram: $PACZKA_URL"
    case "$PACZKA_URL" in
        *.tar.gz|*.tgz) ARCHIVE="$WORK/paczka.tar.gz" ;;
        *) ARCHIVE="$WORK/paczka.zip" ;;
    esac
    wget -q --show-progress --tries=5 --timeout=60 -O "$ARCHIVE" "$PACZKA_URL" || die "pobieranie paczki nie udało się"
    [ "$(wc -c < "$ARCHIVE")" -gt 1000000 ] || die "pobrany plik jest za mały - link nie prowadzi do samego pliku (np. strona Google Drive zamiast pliku)"
    info "Rozpakowuję..."
    mkdir -p "$WORK/x"
    if unzip -tq "$ARCHIVE" >/dev/null 2>&1; then
        unzip -q "$ARCHIVE" -d "$WORK/x" || die "rozpakowanie .zip nie udało się"
    else
        tar -xzf "$ARCHIVE" -C "$WORK/x" 2>/dev/null || die "plik nie jest ani .zip, ani .tar.gz"
    fi
    rm -f "$ARCHIVE"
    # Folder serwera w paczce: ten z linux-port/tools/vps-install.sh (paczka
    # może mieć klienta obok i folder nadrzędny).
    SRC=$(find "$WORK/x" -path '*/linux-port/tools/vps-install.sh' -type f 2>/dev/null | head -n 1)
    [ -n "$SRC" ] || die "w paczce nie ma folderu serwera (linux-port/tools/vps-install.sh)"
    SRC=${SRC%/linux-port/tools/vps-install.sh}
    info "Folder serwera w paczce: ${SRC#"$WORK/x"/}"
    ( cd "$SRC" && tar -cf - . ) | ( cd "$FOLDER" && tar -xf - ) || die "kopiowanie do $FOLDER nie udało się"
    rm -rf "$WORK/x"
    info "Rozpakowane do $FOLDER (wersja $(tr -d ' \r\n' < "$FOLDER/VERSION" 2>/dev/null || echo ?))"
fi

# ---- 3. najnowsza wersja z GitHuba --------------------------------------------
say "3/5 Aktualizacja do najnowszej wersji z GitHuba"
if [ "$UPDATE" = 0 ]; then
    info "Pominięta (--bez-aktualizacji)."
else
    WORK2=$(mktemp -d /tmp/mt2009plus-upd.XXXXXX) || die "mktemp"
    curl -fsSL --connect-timeout 20 --max-time 60 -H 'Accept: application/vnd.github.raw+json' \
            "https://api.github.com/repos/$REPO/contents/$MANIFEST?ref=$BRANCH" -o "$WORK2/manifest.json" 2>/dev/null \
        || curl -fsSL --connect-timeout 20 --max-time 60 "https://raw.githubusercontent.com/$REPO/$BRANCH/$MANIFEST" \
            -o "$WORK2/manifest.json" \
        || die "nie mogę pobrać $MANIFEST z GitHuba"
    eval "$(python3 - "$WORK2/manifest.json" <<'PY'
import json, sys, shlex
m = json.load(open(sys.argv[1]))["server"]
for k in ("version", "url", "sha256"):
    print("NEW_%s=%s" % (k.upper(), shlex.quote(str(m.get(k, "")))))
PY
)" || die "manifest nieczytelny"
    HAVE=$(tr -d ' \r\n' < "$FOLDER/VERSION" 2>/dev/null)
    newer=$(python3 -c "import sys
def v(s):
    try: return tuple(int(x) for x in s.split('.'))
    except ValueError: return (0,)
print(1 if v(sys.argv[2]) > v(sys.argv[1]) else 0)" "${HAVE:-0}" "${NEW_VERSION:-0}")
    if [ "$newer" != 1 ]; then
        info "Paczka ma już najnowszą wersję ($HAVE)."
    else
        info "Wersja w paczce: $HAVE, najnowsza: $NEW_VERSION - pobieram aktualizację."
        wget -q --show-progress --tries=5 --timeout=60 -O "$WORK2/update.zip" "$NEW_URL" \
            || die "pobieranie aktualizacji nie udało się"
        got=$(sha256sum "$WORK2/update.zip" | awk '{print toupper($1)}')
        want=$(printf '%s' "$NEW_SHA256" | tr 'a-f' 'A-F')
        [ "$got" = "$want" ] || die "suma SHA-256 aktualizacji się nie zgadza (pobrany plik uszkodzony) - uruchom jeszcze raz"
        # .env i inne ustawienia serwera nie są w paczce aktualizacji, więc
        # zostają; pliki z paczki są podmieniane.
        unzip -oq "$WORK2/update.zip" -d "$FOLDER" || die "rozpakowanie aktualizacji nie udało się"
        info "Zaktualizowano do $(tr -d ' \r\n' < "$FOLDER/VERSION")."
    fi
    rm -rf "$WORK2"
fi

if [ "$FILES_ONLY" = 1 ]; then
    say "Pliki gotowe w $FOLDER (--tylko-pliki). Dalej: sh $(installer) install"
    exit 0
fi

# ---- 4. Docker, budowa, start -------------------------------------------------
say "4/5 Docker, budowa i start serwera (pierwszy raz 15-40 minut)"
info "Budowa idzie w tle - zerwane połączenie SSH jej nie przerwie."
info "Postęp później: sh $(installer) status"
set -- install --follow
[ -n "$ADDRESS" ] && set -- "$@" --address "$ADDRESS"
[ -n "$BOTS" ] && set -- "$@" --bots "$BOTS"
[ "$FORCE" = 1 ] && set -- "$@" --force
sh "$(installer)" "$@"
rc=$?

# ---- 5. podsumowanie ----------------------------------------------------------
say "5/5 Gotowe"
if [ "$rc" != 0 ]; then
    info "Instalator zakończył się kodem $rc. Stan budowy: sh $(installer) status"
    info "Log: $FOLDER/.vps-install.log"
    exit "$rc"
fi
IP=${ADDRESS:-$(curl -4 -fsS --max-time 10 ifconfig.me 2>/dev/null || echo ADRES_VPS)}
info "Serwer: $IP  (logowanie 11000, kanały 13000+)"
info "Hasła kont gry (admin, test):   sh $(installer) passwords"
info "Stan serwera:                   sh $(installer) status"
info "Konto dla znajomego:            sh $(installer) add-account LOGIN"
info "Aktualizacja w przyszłości:     sh $(installer) update"
info ""
info "Panele są dostępne tylko przez tunel SSH (dla bezpieczeństwa). Na swoim"
info "komputerze: ssh -L 7788:127.0.0.1:7788 -L 7790:127.0.0.1:7790 root@$IP"
info "i w przeglądarce http://127.0.0.1:7788 (panel) oraz http://127.0.0.1:7790 (zaawansowany)."
info "W kliencie gry dodaj serwer: $IP (np. plikiem Ustaw_serwer_VPS.bat)."
