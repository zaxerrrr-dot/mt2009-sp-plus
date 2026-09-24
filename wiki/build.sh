#!/bin/sh
# MT2009 PLUS Wiki: builds dist/wiki (upload its "wiki" folder to the hosting's
# public_html, so it is metin2sp.pl/wiki) and a zip of it. Needs Docker only.
#   sh wiki/build.sh [MIRROR] [OUT]
set -eu
HERE=$(cd "$(dirname "$0")" && pwd)
MIRROR=${1:-/opt/metin2/wiki-src/mirror}
OUT=${2:-/opt/metin2/dist/wiki}
mkdir -p "$OUT"
docker run --rm -v "$HERE:/w:ro" -v "$MIRROR:/m:ro" -v "$OUT:/o" python:3.12-slim \
  sh -c 'pip install -q markdown >/dev/null 2>&1 && python /w/build.py /m /o'
docker run --rm -v "$HERE:/w:ro" -v "$OUT:/o" node:20-slim \
  node /w/lunr-build.js /o/search-docs.json /o/wiki/lib/lunr.min.js /o/wiki/search-index.json
rm -f "$OUT/search-docs.json" "$OUT/mt2009plus-wiki.zip"
docker run --rm -v "$OUT:/o" -w /o python:3.12-slim python -c \
  "import shutil; shutil.make_archive('mt2009plus-wiki', 'zip', '.', 'wiki')"
ls -la "$OUT"
