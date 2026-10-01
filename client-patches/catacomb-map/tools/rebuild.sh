#!/bin/sh
# MT2009 client 2.0.36: the Devil's Catacomb (map 216) - NEW pack catacomb_map on top of the 2.0.35 packs.
# BASE (read only) -> /opt/metin2/cache/c36-catacomb/pack (catacomb_map.index/.data + Index with the line at the end).
#   plan_cc.py   closure from GF 26.1.11 (+ Arezzo fallback) + generated msenv/atlas -> final_cc.json
#   build_cc.py  the new pack, every entry read back
#   verify_cc.py independent closure from the packs (map, environment, textureset, properties, 24 races)
set -eu
H=/opt/metin2/cache/c36-catacomb
T=$(dirname "$(readlink -f "$0")")
BASE=${1:-/opt/metin2/cache/c35/pack}
D="docker run --rm -v /opt/metin2:/opt/metin2 -v $T:$T m2pack-lzo python3"
$D $T/plan_cc.py "$BASE"
$D $T/build_cc.py "$BASE" "$H/pack"
$D $T/verify_cc.py "$BASE" "$H/pack" > $H/verify_cc.out || { tail -5 $H/verify_cc.out; exit 1; }
tail -1 $H/verify_cc.out
