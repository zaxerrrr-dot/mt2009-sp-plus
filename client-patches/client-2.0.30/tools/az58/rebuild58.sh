#!/bin/sh
# MT2009 client 2.0.30 - Arezzo phases 5-8 (maps 361/364/365/366, Plechito races): rebuild on the CURRENT client packs.
# BASE (read only) = the latest full client packs (default /opt/metin2/cache/tcm/c30/pack, phase 1 + dungeon panel in it);
# OUT gets only the changed/new packs + Index. Idempotent: a base that already has everything gives "unchanged".
set -eu
H=/opt/metin2/cache/arezzo-work/client/az58
BASE=${1:-/opt/metin2/cache/tcm/c30/pack}
OUT=${2:-/opt/metin2/cache/arezzo-work/client/out58/pack}
cd "$H"
[ -x gr2/gr2dec ] || python3 -c 'import gfres; gfres._gr2dec()'
# the base's listing and property/gamedata/locale/root files (c30list.py reads /opt/metin2/cache/tcm/c30/pack)
docker run --rm -v /opt/metin2:/opt/metin2 m2pack-lzo python3 /opt/metin2/cache/arezzo-work/client/c30list.py > /dev/null
python3 plan58.py > plan58.out
python3 gen58.py
docker run --rm -v /opt/metin2:/opt/metin2 m2pack-lzo python3 $H/build58.py "$BASE" "$OUT"
docker run --rm -v /opt/metin2:/opt/metin2 m2pack-lzo python3 $H/verify58.py "$BASE" "$OUT" > $H/verify58.out 2>&1 || { cat $H/verify58.out; exit 1; }
tail -1 $H/verify58.out
docker run --rm -v /opt/metin2:/opt/metin2 m2pack-lzo python3 $H/extract58.py
python3 $H/stage58.py
