#!/bin/sh
# MT2009_PLUS_NPC_LOCATION_HELPER_V1 (Autor: Best Studio) - dumps, read-only, what gen_npcloc_data.py reads:
#   dump_npcloc_inputs.sh <OUT dir> [<client pack dir, default /opt/metin2/cache/cY/pack>]
# From the running test server (container mt2009plustest-game, /opt/metin2/share/locale/poland): map/index and every
# indexed map's npc/regen/boss/stone/Setting/Town/server_attr, group.txt, group_group.txt, mob_drop_item.txt; from the
# database (SELECT only): world.mob_proto (vnum, rank, type, level, on_click, locale_name as hex, name), the item vnums
# of world.item_proto and the shop NPCs (world.shop + world.shop_item); from the client packs: gamedata/atlasinfo.txt
# (the client's map names and base positions). Nothing is written anywhere but OUT.
set -eu
OUT=${1:?usage: dump_npcloc_inputs.sh OUT [PACKDIR]}
PK=${2:-/opt/metin2/cache/cY/pack}
G=mt2009plustest-game
D=mt2009plustest-db
mkdir -p "$OUT"
docker exec $G sh -c 'cd /opt/metin2/share/locale/poland && tar cf - map/index $(for d in $(awk "{print \$2}" map/index); do for f in npc.txt regen.txt boss.txt stone.txt Setting.txt Town.txt server_attr; do [ -f map/$d/$f ] && echo map/$d/$f; done; done) group.txt group_group.txt mob_drop_item.txt' | tar xf - -C "$OUT"
q() { docker exec $D sh -c "mariadb -uroot -p\"\$MARIADB_ROOT_PASSWORD\" -N -e \"$1\""; }
q 'SELECT vnum,rank,type,level,on_click,HEX(locale_name),name FROM world.mob_proto' > "$OUT/mob_proto.tsv"
q 'SELECT vnum FROM world.item_proto' > "$OUT/item_vnums.txt"
q 'SELECT s.npc_vnum, s.name, COUNT(i.item_vnum), SUM(i.item_vnum<10000 OR (i.item_vnum>=11000 AND i.item_vnum<20000)) FROM world.shop s LEFT JOIN world.shop_item i ON i.shop_vnum=s.vnum GROUP BY s.npc_vnum, s.name' > "$OUT/shop_npcs.tsv"
H=$(cd "$(dirname "$0")" && pwd)
docker run --rm -v /opt/metin2:/opt/metin2 -v "$OUT:$OUT" -v "$H:$H" m2pack-lzo python3 -c "
import sys
sys.path.insert(0,'/opt/metin2/cache/c36'); sys.path.insert(0,'/opt/metin2/cache/tcm/tz'); sys.path.insert(0,'/opt/metin2/cache/arezzo-work/client/az58')
import m2pack,packlib
f,v,e=m2pack.read_index('$PK/gamedata.index'); d=packlib.rd('$PK/gamedata.data')
x=[x for x in e if x['name']=='gamedata/atlasinfo.txt'][0]
open('$OUT/atlasinfo.txt','wb').write(m2pack.read_entry(d,x))
"
echo "dumped to $OUT"
