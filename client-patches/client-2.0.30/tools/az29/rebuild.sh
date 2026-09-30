#!/bin/sh
# MT2009 client 2.0.30 - Arezzo phase 1 (maps 360/362/363): rebuild on the CURRENT client packs.
# BASE (read only) = the latest full client packs (default /opt/metin2/cache/tcm/c28/pack); OUT gets only the
# changed/new packs + Index. Idempotent: a base that already has everything gives "unchanged".
set -eu
H=/opt/metin2/cache/arezzo-work/client/az29
BASE=${1:-/opt/metin2/cache/tcm/c28/pack}
OUT=${2:-/opt/metin2/cache/arezzo-work/client/out/pack}
cd "$H"
[ -x gr2/gr2dec ] || python3 -c 'import gfres; gfres._gr2dec()'
python3 plan.py
python3 gen.py
docker run --rm -v /opt/metin2:/opt/metin2 m2pack-lzo python3 $H/build_az.py "$BASE" "$OUT"
docker run --rm -v /opt/metin2:/opt/metin2 m2pack-lzo python3 $H/verify_az.py "$BASE" "$OUT" > $H/verify.out 2>&1 || { cat $H/verify.out; exit 1; }
tail -1 $H/verify.out
docker run --rm -v /opt/metin2:/opt/metin2 m2pack-lzo python3 $H/extract_out.py
python3 $H/stage.py
