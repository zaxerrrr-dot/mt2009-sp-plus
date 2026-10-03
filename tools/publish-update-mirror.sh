#!/bin/sh
# =============================================================================
#  publish-update-mirror.sh -- fills the fallback update server.
#
#      sh tools/publish-update-mirror.sh <server zip> <client zip | ->
#
#  The launcher, the client updater (MT2009-Aktualizator), update.sh,
#  instaluj-vps.sh and the Seban updater read everything from GitHub first.
#  When GitHub does not answer they read the same file names from
#  http://141.94.100.53/aktualizacje/ (nginx serving $DEST below):
#
#      update-manifest-mt2009.json   client-files.json
#      metin2-server-update-<V>.zip  metin2-client-update-<V>.zip
#
#  Run it with every release, after update-manifest-mt2009.json and
#  client-files.json in this checkout are the released ones. It copies the
#  given zips, then client-files.json, then the manifest last -- so the mirror
#  never names a zip it does not have. Each file is written as <name>.tmp and
#  renamed into place (atomic for nginx). Only the two newest server and the
#  two newest client zips are kept (never the ones the manifest names).
#
#  A zip whose file name is the one the manifest names must have the
#  manifest's SHA-256, or nothing is published. `-' for the client zip means
#  no new client in this release.
#
#  DEST=/other/dir sh tools/publish-update-mirror.sh ...  publishes elsewhere.
# =============================================================================
set -eu

HERE=$(cd "$(dirname "$0")" && pwd)
REPO_ROOT=$(cd "$HERE/.." && pwd)
DEST=${DEST:-/opt/metin2/dist/aktualizacje}
MANIFEST="$REPO_ROOT/update-manifest-mt2009.json"
FILE_LIST="$REPO_ROOT/client-files.json"

die() { printf 'BLAD: %s\n' "$*" >&2; exit 1; }
say() { printf '%s\n' "$*"; }

[ $# -eq 2 ] || die "uzycie: sh $0 <server zip> <client zip | ->"
SERVER_ZIP=$1
CLIENT_ZIP=$2
[ -f "$SERVER_ZIP" ] || die "brak pliku: $SERVER_ZIP"
case "$(basename "$SERVER_ZIP")" in
    metin2-server-update-*.zip) ;;
    *) die "paczka serwera ma sie nazywac metin2-server-update-<wersja>.zip: $SERVER_ZIP" ;;
esac
if [ "$CLIENT_ZIP" != "-" ]; then
    [ -f "$CLIENT_ZIP" ] || die "brak pliku: $CLIENT_ZIP"
    case "$(basename "$CLIENT_ZIP")" in
        metin2-client-update-*.zip) ;;
        *) die "paczka klienta ma sie nazywac metin2-client-update-<wersja>.zip: $CLIENT_ZIP" ;;
    esac
fi
[ -f "$MANIFEST" ] || die "brak $MANIFEST"
[ -f "$FILE_LIST" ] || die "brak $FILE_LIST"
command -v python3 >/dev/null 2>&1 || die "potrzebny python3"
command -v sha256sum >/dev/null 2>&1 || die "potrzebny sha256sum"

# manifest_field server|client url|sha256
manifest_field() {
    python3 - "$MANIFEST" "$1" "$2" <<'EOF'
import json, sys
m = json.load(open(sys.argv[1], encoding='utf-8-sig'))
block = m.get(sys.argv[2]) or {}
print(block.get(sys.argv[3], '') if isinstance(block, dict) else '')
EOF
}
python3 -c 'import json,sys; json.load(open(sys.argv[1], encoding="utf-8-sig")); json.load(open(sys.argv[2], encoding="utf-8-sig"))' \
    "$MANIFEST" "$FILE_LIST" || die "manifest albo client-files.json nie jest poprawnym JSON-em"

# check_zip FILE server|client: the manifest's SHA-256 when it names this file.
check_zip() {
    _name=$(basename "$1")
    _url=$(manifest_field "$2" url)
    _want=$(manifest_field "$2" sha256 | tr 'A-F' 'a-f')
    _mname=${_url%%\?*}; _mname=${_mname##*/}
    if [ "$_name" = "$_mname" ]; then
        _got=$(sha256sum "$1" | cut -d' ' -f1)
        [ "$_got" = "$_want" ] || die "$_name: SHA-256 $_got, a manifest podaje $_want - nic nie opublikowano"
        say "$_name: SHA-256 zgodne z manifestem"
    else
        say "UWAGA: manifest ($2) wskazuje ${_mname:-nic}, nie $_name - launcher pobierze z serwera zapasowego tylko plik z manifestu"
    fi
}
check_zip "$SERVER_ZIP" server
[ "$CLIENT_ZIP" = "-" ] || check_zip "$CLIENT_ZIP" client

mkdir -p "$DEST"

# put SRC NAME: copy to NAME.tmp in DEST, then rename into place.
put() {
    cp "$1" "$DEST/$2.tmp"
    chmod 644 "$DEST/$2.tmp"
    mv -f "$DEST/$2.tmp" "$DEST/$2"
    say "opublikowano $DEST/$2"
}
put "$SERVER_ZIP" "$(basename "$SERVER_ZIP")"
[ "$CLIENT_ZIP" = "-" ] || put "$CLIENT_ZIP" "$(basename "$CLIENT_ZIP")"
put "$FILE_LIST" client-files.json
put "$MANIFEST" update-manifest-mt2009.json

# Keep the two newest of each kind, and always what the manifest names.
keep_server=$(manifest_field server url); keep_server=${keep_server%%\?*}; keep_server=${keep_server##*/}
keep_client=$(manifest_field client url); keep_client=${keep_client%%\?*}; keep_client=${keep_client##*/}
prune() {
    ls -1 "$DEST" | grep -E "^$1-[0-9A-Za-z._-]+\.zip\$" | sort -V | head -n -2 | while read -r old; do
        [ "$old" = "$keep_server" ] && continue
        [ "$old" = "$keep_client" ] && continue
        rm -f "$DEST/$old"
        say "usunieto stara paczke $old"
    done
}
prune metin2-server-update
prune metin2-client-update
rm -f "$DEST"/*.tmp

say "Serwer zapasowy gotowy: $DEST"
ls -l "$DEST"

# MT2009_PLUS_PATCHER_NEWS_AUTO_V1: the client patcher's news box - the four
# newest CHANGELOG entries, then the standing ones of aktualnosci.md. Without
# it the patcher showed "Klient 2.0.30" three releases later.
PATCHER_DIR=${PATCHER_DIR:-/opt/metin2/dist/patcher}
if [ -d "$PATCHER_DIR" ]; then
    python3 "$REPO_ROOT/client-patches/patcher/tools/generuj_aktualnosci.py" \
        --changelog "$REPO_ROOT/CHANGELOG.md" --ile 4 --wyjscie "$PATCHER_DIR/news.json" ||
        say "UWAGA: nie udalo sie odswiezyc aktualnosci patchera ($PATCHER_DIR/news.json)"
fi
