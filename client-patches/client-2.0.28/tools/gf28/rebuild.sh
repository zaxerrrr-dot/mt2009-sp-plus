#!/bin/sh
# Re-apply the GF asset import on top of the CURRENT /opt/metin2/cache/tcm/c28/pack (e.g. after
# someone rebuilt root/gamedata), verify every pack, stage, and rebuild all 2.0.28 zips.
# Idempotent: packs already containing the GF files come out "unchanged".
set -eu
H=/opt/metin2/cache/tcm/gf28
cd "$H"
[ -f final.json ] || { python3 plan.py && python3 gen.py; }
docker run --rm -v /opt/metin2:/opt/metin2 m2pack-lzo python3 $H/build_gf.py
[ -z "$(ls -A $H/out/pack)" ] || cp -v $H/out/pack/* /opt/metin2/cache/tcm/c28/pack/
docker run --rm -v /opt/metin2:/opt/metin2 m2pack-lzo python3 $H/verify_all.py
python3 $H/stage.py
python3 $H/make_zips.py
