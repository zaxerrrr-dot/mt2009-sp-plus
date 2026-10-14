#!/usr/bin/env python3
"""gen_sungma_data.py <GF client dir> <Owsap mob_proto.txt> <out dir>

MT2009_PLUS_SUNGMA_V1 / MT2009_PLUS_CHAMPION_V1 (server-patches/czempion/README.md): the game's two data
files, copied to share/locale/<locale>/ by the Dockerfile step "share: Poziom Czempiona":

  sungma_table.txt    <map name> <str> <hp> <move> <immune> <hit_pct> - every <map>/sungma_attr.txt of the GF
                      client (26.1.11: the 19 maps of Yohara). The engine matches the names against the maps the
                      core hosts (map/index), so a map we do not have changes nothing. MT2009_PLUS_PRECISION_V1:
                      hit_pct (the map's Precyzja) is Owsap's share/locale/uk/map/new_world.txt (by map index ->
                      index.txt's name; GF's sungma_attr.txt has none) - 0 for a map Owsap does not list.
  sungma_mob_exp.txt  <vnum> <champion exp> - Owsap v6.2.6 mob_proto.txt column SungMaExp, monsters and
                      stones only (an NPC row there, e.g. 20082, is a different NPC here). The engine gives
                      it only for kills on a Sung Ma map.

Example: python3 tools/champion/gen_sungma_data.py /opt/metin2/cache/gf/Gameforge_26.1.11/_client \
         /opt/metin2/cache/owsap/Server/Server/db/mob_proto.txt linux-port/docker/game/champion
"""
import csv
import os
import sys


def owsap_hit_pct(mob_proto):
    """MT2009_PLUS_PRECISION_V1: {map name: hit_pct} of Owsap's new_world.txt (next to its mob_proto: Server/Server/db ->
    Server/Server/share/locale/uk/map), the map numbers named by its index.txt."""
    share = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(mob_proto))), "share", "locale", "uk", "map")
    names = {}
    for line in open(os.path.join(share, "index.txt"), encoding="latin-1"):
        parts = line.split()
        if len(parts) >= 2 and parts[0].isdigit():
            names[int(parts[0])] = parts[1]
    hit = {}
    for line in open(os.path.join(share, "new_world.txt"), encoding="latin-1"):
        parts = line.split()
        if len(parts) >= 6 and parts[0].isdigit() and int(parts[0]) in names:
            hit[names[int(parts[0])]] = int(parts[5])
    return hit


def main():
    if len(sys.argv) != 4:
        sys.exit(__doc__)
    client, mob_proto, out = sys.argv[1:]
    hit = owsap_hit_pct(mob_proto)
    rows = []
    for name in sorted(os.listdir(client)):
        path = os.path.join(client, name, "sungma_attr.txt")
        if not os.path.isfile(path):
            continue
        values = {}
        for line in open(path, encoding="latin-1"):
            parts = line.split()
            if len(parts) == 2:
                values[parts[0].lower()] = int(parts[1])
        rows.append((name, values.get("sungma_str", 0), values.get("sungma_hp", 0),
                     values.get("sungma_move", 0), values.get("sungma_immune", 0), hit.get(name, 0)))
    with open(os.path.join(out, "sungma_table.txt"), "w", newline="\n") as f:
        f.write("# MT2009_PLUS_SUNGMA_V1: Sung Ma requirements of a map (GF 26.1.11 <map>/sungma_attr.txt;\n")
        f.write("# tools/champion/gen_sungma_data.py). Only maps this core hosts by this name count.\n")
        f.write("# MT2009_PLUS_PRECISION_V1: hit_pct = the map's Precyzja (Owsap's new_world.txt; 0 = none asked).\n")
        f.write("# map\tstr\thp\tmove\timmune\thit_pct\n")
        for r in rows:
            f.write("%s\t%d\t%d\t%d\t%d\t%d\n" % r)

    reader = csv.reader(open(mob_proto, encoding="latin-1"), delimiter="\t")
    head = next(reader)
    i_vnum, i_type, i_exp = head.index("Vnum"), head.index("Type"), head.index("SungMaExp")
    mobs = []
    for row in reader:
        if len(row) <= i_exp or row[i_type] not in ("MONSTER", "STONE"):
            continue
        try:
            vnum, exp = int(row[i_vnum]), int(row[i_exp])
        except ValueError:
            continue
        if exp > 0:
            mobs.append((vnum, exp))
    mobs.sort()
    with open(os.path.join(out, "sungma_mob_exp.txt"), "w", newline="\n") as f:
        f.write("# MT2009_PLUS_CHAMPION_V1: champion experience of a monster killed on a Sung Ma map (Owsap v6.2.6\n")
        f.write("# mob_proto.txt SungMaExp; tools/champion/gen_sungma_data.py). Calibration: event flag conqueror_exp_rate.\n")
        f.write("# vnum\texp\n")
        for vnum, exp in mobs:
            f.write("%d\t%d\n" % (vnum, exp))
    print("%d map(s), %d monster(s)" % (len(rows), len(mobs)))


if __name__ == "__main__":
    main()
