#!/bin/sh
# MT2009 PLUS - Yohara Patcher - build on Linux (Docker: python:3.12-slim + Pillow for the
# window art, mcr.microsoft.com/dotnet/sdk:8.0 for the exe). The same toolchain as the 2.x
# patcher (../patcher/build.sh); both projects live side by side and never share output.
#   ./build.sh            -> MT2009-Yohara-Patcher.exe (+ .sha256) w /opt/metin2/dist/aktualizacje/yohara
#   ./build.sh <folder>   -> w podanym folderze
#   TESTY=1 ./build.sh    -> dodatkowo testy logiki (MT2009-Yohara-Patcher.Tests "unit")
set -e
cd "$(dirname "$0")"
HERE=$PWD
CP=$(cd .. && pwd)            # client-patches: the project links ../patcher (shared code + 2.x art)
OUT=${1:-/opt/metin2/dist/aktualizacje/yohara}
DOTNET=mcr.microsoft.com/dotnet/sdk:8.0
PY=python:3.12-slim
NUGET=/opt/metin2/cache/nuget-ypatcher
PIP=/opt/metin2/cache/pip-ypatcher
mkdir -p "$NUGET" "$PIP"
docker run --rm -v "$CP":/cp -v "$PIP":/root/.cache/pip -w /cp/yohara-patcher "$PY" \
    sh -c 'pip install -q --disable-pip-version-check --root-user-action=ignore Pillow==11.0.0 && python tools/grafika_yohara.py'
docker run --rm -v "$CP":/cp -v "$NUGET":/root/.nuget/packages -w /cp/yohara-patcher/MT2009-Yohara-Patcher "$DOTNET" \
    sh -c 'rm -rf bin obj && dotnet build -c Release -nologo -v q'
if [ -n "$TESTY" ]; then
    docker run --rm --network host -v "$CP":/cp -v "$NUGET":/root/.nuget/packages -w /cp/yohara-patcher/MT2009-Yohara-Patcher.Tests "$DOTNET" \
        sh -c 'dotnet run -c Release -- unit | grep -v "^        |"; rc=$?; rm -rf bin obj; exit $rc'
fi
mkdir -p "$OUT"
EXE=MT2009-Yohara-Patcher/bin/Release/net48/MT2009-Yohara-Patcher.exe
cp "$EXE" "$OUT"/MT2009-Yohara-Patcher.exe.tmp
mv -f "$OUT"/MT2009-Yohara-Patcher.exe.tmp "$OUT"/MT2009-Yohara-Patcher.exe
chmod 644 "$OUT"/MT2009-Yohara-Patcher.exe
(cd "$OUT" && sha256sum MT2009-Yohara-Patcher.exe > MT2009-Yohara-Patcher.exe.sha256)
rm -rf MT2009-Yohara-Patcher/bin MT2009-Yohara-Patcher/obj
ls -l "$OUT"/MT2009-Yohara-Patcher.exe
cat "$OUT"/MT2009-Yohara-Patcher.exe.sha256
