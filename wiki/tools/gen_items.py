#!/usr/bin/env python3
"""MT2009 PLUS Wiki: the lists of costumes, hairstyles, weapon skins, sashes,
mounts and pets that are really in the game, with their icons.

Reads item_proto from a running server's database (TSV on stdin, from the
query below) and the Seban Panel's icon map, and writes wiki/data/items.json
and wiki/items/<icon>.png. Run it again after items are added:

    docker exec <db> mariadb -uroot -p... --default-character-set=utf8mb4 -N -e \\
      "select vnum,type,subtype,locale_name,limittype0,limitvalue0 from player.item_proto
       where (type=28 and subtype in (0,1,2,3,4)) or (type=37 and subtype=12)
          or vnum between 80014 and 80018" \\
      | python3 wiki/tools/gen_items.py <seban-panel/static>
"""
import json, os, shutil, sys

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
KINDS = {("28", "0"): "kostiumy", ("28", "1"): "fryzury", ("28", "4"): "nakladki",
         ("28", "3"): "szarfy", ("28", "2"): "wierzchowce", ("37", "12"): "pety"}
# item_proto limit types: 7 counts real time from creation, 8 from first use.
TIMED = ("7", "8")


def duration(ltype, lvalue):
    if ltype not in TIMED or not int(lvalue):
        return "stały"
    s = int(lvalue)
    if s % 86400 == 0:
        return "%d d" % (s // 86400)
    return "%d h" % (s // 3600) if s % 3600 == 0 else "%d min" % (s // 60)


def main():
    static = sys.argv[1]
    icons = json.load(open(os.path.join(static, "item_icons.json"), encoding="utf-8"))
    out_icons = os.path.join(HERE, "items")
    shutil.rmtree(out_icons, ignore_errors=True)
    os.makedirs(out_icons)
    items = {k: {} for k in set(KINDS.values()) | {"kupony"}}
    for line in sys.stdin.read().splitlines():
        vnum, typ, sub, name, ltype, lvalue = line.split("\t")
        # Kupon SM 50-1000 (80014-80018): an ItemShop voucher, type 18.
        kind = "kupony" if 80014 <= int(vnum) <= 80018 else KINDS.get((typ, sub))
        if not kind or not name.strip():
            continue
        entry = items[kind].setdefault(name, {"name": name, "vnums": [], "time": [], "icon": ""})
        entry["vnums"].append(int(vnum))
        d = duration(ltype, lvalue)
        if d not in entry["time"]:
            entry["time"].append(d)
        f = icons.get(vnum)
        if f and not entry["icon"] and os.path.exists(os.path.join(static, "icons", f)):
            shutil.copyfile(os.path.join(static, "icons", f), os.path.join(out_icons, f))
            entry["icon"] = f
    order = {"stały": 0}
    data = {k: sorted(({**e, "time": sorted(e["time"], key=lambda t: (order.get(t, 1), int(t.split()[0]) if t[0].isdigit() else 0))}
                       for e in v.values()), key=lambda e: e["name"].lower())
            for k, v in items.items()}
    os.makedirs(os.path.join(HERE, "data"), exist_ok=True)
    json.dump(data, open(os.path.join(HERE, "data", "items.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=0)
    for k, v in sorted(data.items()):
        print("%-12s %4d (bez ikony: %d)" % (k, len(v), sum(1 for e in v if not e["icon"])))


if __name__ == "__main__":
    main()
