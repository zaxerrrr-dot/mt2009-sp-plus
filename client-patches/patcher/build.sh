#!/bin/sh
# MT2009 PLUS Patcher - build on Linux (Docker, mcr.microsoft.com/dotnet/sdk:8.0).
#   ./build.sh            -> MT2009-Patcher.exe + .exe.config w /opt/metin2/dist/patcher-app
#   ./build.sh <folder>   -> w podanym folderze
#   TESTY=1 ./build.sh    -> dodatkowo testy logiki (MT2009-Patcher.Tests, "unit")
set -e
cd "$(dirname "$0")"
OUT=${1:-/opt/metin2/dist/patcher-app}
IMAGE=mcr.microsoft.com/dotnet/sdk:8.0
docker run --rm -v "$PWD":/src -w /src/MT2009-Patcher "$IMAGE" \
    sh -c 'rm -rf bin obj && dotnet build -c Release -nologo -v q' 
if [ -n "$TESTY" ]; then
    docker run --rm --network host -v "$PWD":/src -w /src/MT2009-Patcher.Tests "$IMAGE" \
        sh -c 'dotnet run -c Release -- unit; rc=$?; rm -rf bin obj; exit $rc'
fi
mkdir -p "$OUT"
cp MT2009-Patcher/bin/Release/net48/MT2009-Patcher.exe MT2009-Patcher/bin/Release/net48/MT2009-Patcher.exe.config "$OUT"/
chmod 644 "$OUT"/MT2009-Patcher.exe "$OUT"/MT2009-Patcher.exe.config
rm -rf MT2009-Patcher/bin MT2009-Patcher/obj
ls -l "$OUT"
sha256sum "$OUT"/MT2009-Patcher.exe
