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
                      MT2009_PLUS_SUNGMA_STONE_BOSS_EXP_V1: the stones and bosses of the nine Sung Ma maps the
                      bots hunt (SUNGMA_MAP_SPAWNS below) get a multiple of a normal monster of their map instead
                      of Owsap's value - see stone_boss_exp().

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


# MT2009_PLUS_SUNGMA_STONE_BOSS_EXP_V1 (31 October 2026, BOTY-YOHARA-ANALIZA-v2.md, Etap 1 pkt 2, approved by the
# owner): Owsap's SungMaExp gives the Myr posts 8625-8627 and King Bao (Quest) 6692 one point, the Metins 8063-8077
# about what one normal monster gives (24-32) and the bosses only 1-2.5 times a normal monster - while a post calls
# 22 packs and the bots died at them 975 times a day (803 `stone`, 172 `boss`) for nothing. A stone is now worth
# STONE_MULT and a boss BOSS_MULT normal monsters of its map: the map's base is the median (low) Owsap exp of the
# ordinary monsters of its regen.txt; a stone or boss that stands on several maps takes the median (low) of their
# bases. The table is the test world's share/locale/poland/map/<map>/{regen,stone,boss}.txt of 31 October 2026
# (stone.txt: Metins and posts; boss.txt and the BOSS-rank Kao of regen.txt: bosses). The champion tempo itself
# (conqueror_exp_rate, conqueror_exp_rate_bot, the level table) is not touched - "to ma byc wolne".
STONE_MULT = 20
BOSS_MULT = 50


def _r(a, b):
    return list(range(a, b + 1))


# map index: (map name, ordinary monsters of its regen, stones, bosses)
SUNGMA_MAP_SPAWNS = {
    374: ("metin2_map_empirecastle", _r(6686, 6690) + _r(6693, 6697) + [6700], [8067], [6691, 6692, 6698, 6699]),
    373: ("metin2_map_eastplain_01", _r(6700, 6704) + _r(6710, 6715), [8067, 8625], [6705, 6706, 6716, 6717]),
    376: ("metin2_map_eastplain_02", _r(6718, 6722), [8063, 8067, 8626], [6723, 6724]),
    377: ("metin2_map_eastplain_03", _r(6700, 6704) + _r(6710, 6714) + _r(6718, 6722) + _r(6725, 6729),
          [8063, 8064, 8065, 8067, 8627], [6705, 6730, 6731]),
    385: ("metin2_map_snakevalley", _r(6758, 6762) + _r(6875, 6879), [8064, 8065, 8066], [6763, 6764, 6880, 6881]),
    388: ("metin2_map_icecrystalcave", _r(6770, 6774) + _r(6882, 6886), [8066, 8077], [6775, 6776, 6887, 6888]),
    389: ("metin2_map_whitdragonvalley", _r(6777, 6781) + _r(6889, 6893), [8066, 8077], [6782, 6783, 6894, 6895]),
    393: ("metin2_map_whitedragoncave_01", _r(6784, 6788), [], [6789]),
    394: ("metin2_map_whitedragoncave_02", _r(6792, 6796), [], [6797]),
}


def stone_boss_exp(exp):
    """MT2009_PLUS_SUNGMA_STONE_BOSS_EXP_V1: {vnum: champion exp} for the stones and bosses of SUNGMA_MAP_SPAWNS,
    from Owsap's exp of the maps' ordinary monsters (exp: {vnum: Owsap SungMaExp})."""
    base = {}
    for idx, (name, mobs, stones, bosses) in SUNGMA_MAP_SPAWNS.items():
        values = sorted(exp[v] for v in mobs if v in exp)
        if values:
            base[idx] = values[(len(values) - 1) // 2]
    where = {}
    for idx, (name, mobs, stones, bosses) in SUNGMA_MAP_SPAWNS.items():
        if idx not in base:
            continue
        for v in stones:
            where.setdefault(v, (STONE_MULT, []))[1].append(base[idx])
        for v in bosses:
            where.setdefault(v, (BOSS_MULT, []))[1].append(base[idx])
    out = {}
    for v, (mult, bases) in where.items():
        bases.sort()
        out[v] = mult * bases[(len(bases) - 1) // 2]
    return out


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
    # MT2009_PLUS_SUNGMA_STONE_BOSS_EXP_V1: the stones and bosses of the bots' Sung Ma maps.
    over = stone_boss_exp(dict(mobs))
    mobs = [(vnum, over.get(vnum, exp)) for vnum, exp in mobs]
    mobs += [(vnum, exp) for vnum, exp in over.items() if vnum not in dict(mobs)]
    mobs.sort()
    with open(os.path.join(out, "sungma_mob_exp.txt"), "w", newline="\n") as f:
        f.write("# MT2009_PLUS_CHAMPION_V1: champion experience of a monster killed on a Sung Ma map (Owsap v6.2.6\n")
        f.write("# mob_proto.txt SungMaExp; tools/champion/gen_sungma_data.py). Calibration: event flag conqueror_exp_rate.\n")
        f.write("# MT2009_PLUS_SUNGMA_STONE_BOSS_EXP_V1: stones = %dx, bosses = %dx a normal monster of their Sung Ma map.\n"
                % (STONE_MULT, BOSS_MULT))
        f.write("# vnum\texp\n")
        for vnum, exp in mobs:
            f.write("%d\t%d\n" % (vnum, exp))
    print("%d map(s), %d monster(s)" % (len(rows), len(mobs)))


if __name__ == "__main__":
    main()
