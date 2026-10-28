#!/usr/bin/env python3
"""gen_yohara_prices.py - MT2009_PLUS_YOHARA_PRICES_REF_V1: the Yohara-era items for the bots' market, priced from
the reference server's market (28.10.2026) - the owner, 28 October 2026: "wylicz proporcje cen i zmien ceny u nas".
It replaces the temporary list of 27 October (MT2009_PLUS_YOHARA_PRICES_TEMP_V1), which stays below as the baseline.

The data: reference_prices_20261028.json, made from the owner's sheet by ref_from_xlsx.py (every offer it read, a
piece's Yang; won = 100 000 000 Yang, the sheet's own assumption). snapshot.json carries the item_proto rows of
every item priced here (read from the repo's SQL; the few no repo SQL inserts - Seon-Hae's ordinary shards,
Skrzynia Hydry, Pakiet Kamieni Duszy, the pet goods - were copied from the test world's item_proto).

What it writes (and nothing else):
  * linux-port/overlays/playerbot/src/game/src/playerbot_price_tables.h - blocks between
        // ---- BEGIN MT2009_PLUS_YOHARA_PRICES_REF_V1 ...   and   // ---- END MT2009_PLUS_YOHARA_PRICES_REF_V1
    at the end of PLAYERBOT_GEAR_PRICES (the gear ladders +0..+9), PLAYERBOT_EXTRA_MATERIAL_PRICES (materials,
    half-made pieces, shards, herbs, elixirs, non-skill books, chests, keys), PLAYERBOT_BOOK_PRICES (the 9th skills,
    Riposty, Dopalacze - by skill) and PLAYERBOT_SOUL_STONE_PRICES (the demon stones, kinds 46 / 47 by grade);
    and the rows of the existing MT2009_PLUS_SEONHAE_SHARD_PRICES_TEMP_V1 block (Seon-Hae's ordinary shards).
    Rows outside the blocks (the owner's / Iwakura's) are never touched and a vnum they price is never written
    again (the sheet's number wins) - where the reference differs from such a row by more than 2x it is listed
    as a conflict for the owner (--conflicts) instead.
  * linux-port/docker/seban-panel/market_preview/sheet.py - its GEAR, MATERIALS, REFINE_MATERIALS, BOOKS and
    SOUL_STONES rendered again from the header with gen_sheet.py's own readers.

Every price is the sheet's base (x1.0, before the yang-rate curve and the world's inflation).

    python3 tools/yohara_prices/gen_yohara_prices.py              # write the blocks + the panel sheet
    python3 tools/yohara_prices/gen_yohara_prices.py --dry-run    # print the blocks only
    python3 tools/yohara_prices/gen_yohara_prices.py --ratio      # the exchange ratio and its per-item table
    python3 tools/yohara_prices/gen_yohara_prices.py --conflicts  # the owner's rows the reference disagrees with
    python3 tools/yohara_prices/gen_yohara_prices.py --report F   # every row as JSON (the review sheet)
    python3 tools/yohara_prices/gen_yohara_prices.py --refresh [--drops F --chests F]   # the TEMP baseline's data
    python3 tools/yohara_prices/gen_yohara_prices.py --remove     # take the blocks out again (the Seon-Hae block
                                                                  # goes back to its provisional rows)

How a number is made (the method is in each row's comment):
  ratio    the exchange ratio R = our Yang / theirs: the median of ours / theirs over the key items the owner priced
           on both servers (sheet "Kluczowe przedmioty"), one per vnum, without the outliers in RATIO_OUTLIERS.
  ref      the median of the offers read for the item (a piece's Yang; the sheet's average where no offer is
           listed) x R. Gear is priced at the plus the offers are for, the rest of the ladder by the shape below.
           Offers that all carry extra bonuses do not count (the item is priced by analogy).
  family   inside a family of siblings (SIB) a reference more than OUT x off the family's median is pulled to that
           bound - one market listing at 37 x its siblings is a listing, not a price. Demon stones never cost less
           than the grade under them.
  analogy  an item without a reference: ANALOGY (a named sibling x a factor), else the TEMP rule's own sibling
           ("like"), else its TEMP baseline x the group's median correction (ref / baseline over the group's
           priced items; GLOBAL - over every priced material - when the group has fewer than MIN_GROUP), else the
           family's median.
  ladder   a gear family the TEMP list priced keeps its TEMP shape (+n / +0); a new one climbs geometrically to
           LADDER_TOP x +0 at +9 (the owner's own late gear: Cyjanit weapons, the level-100 helmets). +9 never over
           GEAR_CAP: past it the ladder climbs geometrically from +0 to GEAR_CAP.
  bounds   never under what the merchant pays (shop_buy_price); nothing but gear over MAT_CAP.
Items that can not be put on a shop or given (anti-flags MYSHOP / GIVE), costumes, Gaya-shop goods, the element
talismans (MT2009_PLUS_BOT_ENERGY_SHARDS_V1) and items with a pricing rule of their own are left out.
"""
import argparse
import collections
import json
import math
import os
import re
import statistics
import sys
import unicodedata

MARKER = "MT2009_PLUS_YOHARA_PRICES_REF_V1"
OLD_MARKERS = ("MT2009_PLUS_YOHARA_PRICES_TEMP_V1",)
SEONHAE_MARKER = "MT2009_PLUS_SEONHAE_SHARD_PRICES_TEMP_V1"
HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.normpath(os.path.join(HERE, "..", ".."))
TABLES = os.path.join(ROOT, "linux-port", "overlays", "playerbot", "src", "game", "src", "playerbot_price_tables.h")
SHEET_DIR = os.path.join(ROOT, "linux-port", "docker", "seban-panel", "market_preview")
SQL_DIR = os.path.join(ROOT, "linux-port", "docker", "mariadb", "playerbot")
GAME_DIR = os.path.join(ROOT, "linux-port", "docker", "game")
SNAPSHOT = os.path.join(HERE, "snapshot.json")
REFERENCE = os.path.join(HERE, "reference_prices_20261028.json")
LIVE = "/var/lib/docker/volumes/mt2009plustest_game-var/_data"

# ---------------------------------------------------------------------------- the TEMP baseline's knobs
P0 = {"mat": 300000, "herb": 20000}
S0 = 0.2
K = 0.4
CLAMP = {"mat": (60000, 3000000), "herb": (5000, 60000)}
BULK_FROM = 10          # a recipe asking this many or more of it at once
BULK_FACTOR = 0.4
RISK = 0.5              # chance ^ RISK divides a recipe / a refine step
# The owner's fixed +0 prices (28 Oct 2026, "daj 100mln" for the Sung Ma gloves; the market's 818M was too high);
# the ladder above +0 keeps its shape.
OWNER_PLUS0 = {23000: 100000000, 23010: 100000000, 23020: 100000000, 23030: 100000000}
LADDER_CAP = 600000000  # the TEMP ladders' +9 at most (their shape is what the reference keeps)
GAYA_YANG = 25000       # PLAYERBOT_CHI_GAYA_YANG (playerbot_yohara_chi.h): what a bot pays a Gaya at Mistrz Chi
TOPAZ = 20000           # Topaz Woli: no shop or trade (anti-flags), a drop of 103 monsters - the talisman steps' 6..54
RANK_WEIGHT = {0: 1.0, 1: 1.0, 2: 0.5, 3: 0.3, 4: 0.05, 5: 0.1, 6: 0.05}
CHEST_WEIGHT = 0.05
NO_TRADE = (1 << 13) | (1 << 16)   # ITEM_ANTIFLAG_GIVE | ITEM_ANTIFLAG_MYSHOP

# ---------------------------------------------------------------------------- the TEMP_V1 rows (the baseline)
# What the temporary list of 27 October made of each item. Kept as the baseline the reference corrects: an
# unpriced item of a group whose priced members moved by a factor moves by the same factor, and a ladder keeps
# the shape these rules gave it.
# (vnum, rule, args) - rules: ("drop", "mat"|"herb"), ("recipe", [(vnum, n)...], fee, pct, yield),
# ("like", vnum, factor, why), ("fixed", price, why)
JADE_ORE = {50661: 50641, 50662: 50642, 50663: 50643, 50664: 50644}
MATERIALS = [
    ("Jade and Mistrz Chi (gloves, jade jewellery)", [
        (50641, ("fixed", 5000, "a vein ore: Ruda Rubinu 3 300 + half (a level-120 vein, 100 a jade)")),
        (50642, ("fixed", 5000, "as Ruda Jadeitu Slonca")),
        (50643, ("fixed", 5000, "as Ruda Jadeitu Slonca")),
        (50644, ("fixed", 5000, "as Ruda Jadeitu Slonca")),
    ] + [(j, ("recipe", [(o, 100)], 1500000, 30, 1)) for j, o in sorted(JADE_ORE.items())] + [
        (31216, ("drop", "mat")), (31217, ("drop", "mat")), (31218, ("drop", "mat")), (31224, ("drop", "mat")),
        (31251, ("drop", "mat")), (31252, ("drop", "mat")),
        (31245, ("drop", "mat")), (31246, ("drop", "mat")),
        (31247, ("drop", "mat")), (31248, ("drop", "mat")), (31249, ("drop", "mat")), (31250, ("drop", "mat")),
        (31225, ("fixed", 1000000, "one a glove (Mistrz Chi); no monster or chest of this world drops it yet")),
        (31226, ("drop", "mat")), (31227, ("drop", "mat")), (31228, ("drop", "mat")),
    ]),
    ("The north wind, the serpents and the white dragon", [
        (31233, ("drop", "mat")), (31234, ("drop", "mat")), (31235, ("drop", "mat")), (31236, ("drop", "mat")),
        (31237, ("drop", "mat")),
        (31239, ("like", 27992, 1.0, "the Yohara copy of Biala Perla")),
        (31240, ("like", 27993, 1.0, "the Yohara copy of Niebieska Perla")),
        (31241, ("like", 27994, 1.0, "the Yohara copy of Krwawa Perla")),
        (31242, ("drop", "mat")), (31243, ("drop", "mat")), (31244, ("drop", "mat")),
        (31257, ("drop", "mat")), (31258, ("drop", "mat")), (31259, ("drop", "mat")), (31261, ("drop", "mat")),
        (31262, ("drop", "mat")), (31263, ("drop", "mat")), (70428, ("drop", "mat")),
        (31270, ("recipe", [(81000, 1), (81250, 1), (81300, 1), (81550, 1)], 5000000, 90, 1)),
    ]),
    ("Plaskowyz Iluzji (PB dungeons, awakening)", [
        (31108, ("drop", "mat")),
        (31109, ("drop", "mat")),   # 8 PB bosses at 20% - far under its cube (5 Maly + Dusza + 200 000, 45%)
        # 31109-31112 are worth the chance they give a PB weapon at Angmur (20473): 5 / 10 / 15 / 25 % - their own
        # chain (3 / 2 / 1 of the one under, 35..25 %) is a sink, 44 x a Drobny for a Silny
        (31110, ("like", 31109, 2.0, "10% at Angmur against a Drobny's 5%")),
        (31111, ("like", 31109, 3.0, "15% at Angmur against a Drobny's 5%")),
        (31112, ("like", 31109, 5.0, "25% at Angmur against a Drobny's 5%")),
        (31113, ("drop", "mat")), (31114, ("drop", "mat")), (31115, ("drop", "mat")), (31117, ("drop", "mat")),
        (31118, ("drop", "mat")), (31120, ("drop", "mat")), (31121, ("drop", "mat")), (31122, ("drop", "mat")),
        (31123, ("drop", "mat")), (31124, ("drop", "mat")), (31125, ("drop", "mat")), (31126, ("drop", "mat")),
        (31127, ("drop", "mat")), (31128, ("drop", "mat")), (31129, ("drop", "mat")), (31130, ("drop", "mat")),
        (31131, ("drop", "mat")), (31132, ("drop", "mat")), (31133, ("drop", "mat")), (31134, ("drop", "mat")),
        (31135, ("drop", "mat")), (31136, ("drop", "mat")), (31137, ("drop", "mat")), (31138, ("drop", "mat")),
        (31149, ("drop", "mat")),
    ] + [(v, ("drop", "mat")) for v in (31196, 31197, 31198, 31199, 31200, 31201, 31203, 31204, 31205, 31206,
                                         31207, 31209, 31210, 31211, 31212)] + [
        (30606, ("drop", "mat")), (30608, ("drop", "mat")),
    ]),
    ("Armours 105-120 (Kawuco / Seon-Pyeong) - the ones the sheet does not price yet", [
        (30601, ("drop", "mat")), (30605, ("drop", "mat")), (30607, ("drop", "mat")), (30609, ("drop", "mat")),
        (30614, ("like", 30602, 1.0, "a dye, as Niebieski Barwnik")),
        (30615, ("drop", "mat")), (30619, ("drop", "mat")),
        (30625, ("like", 50639, 1.0, "a gem of the 105 recipes, as Turmalin")),
        (30628, ("like", 30627, 1.0, "as Owoc Bogow - no monster or chest of this world drops it yet")),
    ]),
    ("Set shards and projects (the set smiths)", [
        (v, ("drop", "mat")) for v in (39078, 39079, 39080, 39085, 39086, 39087, 39088, 39089, 39090, 39091,
                                       39092, 39093, 39094, 39095, 39096, 39097, 39098, 39099, 39100, 39101,
                                       39102, 39103, 39104, 39105, 39106, 39107, 39108, 39110, 39111, 39112)
    ]),
    ("Aura runes", [(49991, ("drop", "mat")), (49992, ("drop", "mat")), (49993, ("drop", "mat"))]),
    ("Huahn-So's herbs, bottles and elixirs", [
        (95733, ("drop", "herb")), (95734, ("drop", "herb")), (95735, ("drop", "herb")),
        (95736, ("drop", "herb")), (50737, ("drop", "herb")), (50738, ("drop", "herb")),
        (50739, ("drop", "herb")), (50740, ("drop", "herb")),
    ] + [(50830 + i, ("recipe", [(h, 10), (50739, 20)], 0, 90, 1))
         for i, h in enumerate((95733, 95734, 95735, 95736, 50737, 50738))]
      + [(50836 + i, ("recipe", [(h, 10), (50740, 20)], 0, 90, 1))
         for i, h in enumerate((95733, 95734, 95735, 95736, 50737, 50738))]),
]

# The gear: (family +0 vnum, its +0 rule, label). The +1..+9 follow the world's refine steps.
CHI_GLOVE = [(31247, 10), (31245, 25), (31246, 5), (31225, 1)]    # playerbot_yohara_chi.h, Rekawice Mocy+0
GLOVE_FEE = 10000000 + 100 * GAYA_YANG
JADE_RECIPE = {   # by jade: (plates 31216, extra vnum, extra n, Gaya) - PLAYERBOT_CHI_JADE; Slonca as Mgly
    50664: (25, 0, 0, 100), 50661: (25, 0, 0, 100), 50662: (25, 31227, 5, 300), 50663: (30, 31228, 10, 400)}
JADE_KINDS = [(0, 50664, "Mgly"), (10, 50661, "Slonca"), (20, 50662, "Nocy"), (30, 50663, "Dymu")]


def gear_rows():
    out = []
    for base in (23000, 23010, 23020, 23030):
        out.append((base, ("recipe", CHI_GLOVE, GLOVE_FEE, 75, 1), "Mistrz Chi: 10 runes, 25 Twarda Skora, 5 Wzor "
                    "Rekawicy, Kamien Runiczny, 100 Gaya (in Yang) and 10 mln, 75%"))
    for base in (81000, 81250, 81300, 81550):
        out.append((base, ("fixed", 1500000, "a drop of the Yohara chests: twice an element's talisman +0 "
                           "(700 000), rounded"), "Talizman Woli"))
    out.append((81560, ("fixed", 3000000, "level 120, no steps: twice a Talizman Woli +0"), "Tajemniczy Talizman"))
    for first in (14580, 16580, 17570):
        for off, jade, kind in JADE_KINDS:
            plates, extra, extra_n, gaya = JADE_RECIPE[jade]
            inputs = [(jade, 10), (31216, plates)] + ([(extra, extra_n)] if extra else [])
            out.append((first + off, ("recipe", inputs, 1000000 + gaya * GAYA_YANG, 30, 1),
                        "Mistrz Chi: 10 Jadeit %s, %d Plyt, %s%d Gaya (in Yang) and 1 mln, 30%%" %
                        (kind, plates, "%d of %s, " % (extra_n, extra) if extra else "", gaya)))
    return out


# ---------------------------------------------------------------------------- reading the world
def fold(text):
    text = text.replace("ł", "l").replace("Ł", "L")
    return unicodedata.normalize("NFKD", text).encode("ascii", "ignore").decode("ascii")


TOK = re.compile(r"[^,)]*")


def sql_tuple(s, i):
    i += 1
    vals = []
    while True:
        while s[i] in " \n\r\t":
            i += 1
        if s[i] == "'":
            j, buf = i + 1, []
            while True:
                c = s[j]
                if c == "\\":
                    buf.append(s[j + 1]); j += 2; continue
                if c == "'":
                    if s[j + 1] == "'":
                        buf.append("'"); j += 2; continue
                    break
                buf.append(c); j += 1
            vals.append("".join(buf)); i = j + 1
        elif s.startswith("_cp1250 X", i) or s.startswith("X'", i):
            j = s.index("'", i) + 1
            k = s.index("'", j)
            vals.append(bytes.fromhex(s[j:k]).decode("cp1250", "replace")); i = k + 1
        else:
            m = TOK.match(s, i)
            tok = m.group(0).strip(); i = m.end()
            try:
                vals.append(int(tok))
            except ValueError:
                vals.append(tok)
        while s[i] in " \n\r\t":
            i += 1
        if s[i] == ",":
            i += 1; continue
        if s[i] == ")":
            return vals, i + 1
        raise ValueError(s[i - 40:i + 40])


def sql_inserts(text, table):
    pat = re.compile(r"INSERT\s+(?:IGNORE\s+)?INTO\s+(?:world\.)?`?" + table + r"`?\s*\(([^)]*)\)\s*VALUES\s*", re.I)
    for m in pat.finditer(text):
        cols = [c.strip(" `") for c in m.group(1).split(",")]
        i = m.end()
        while True:
            while text[i] in " \n\r\t":
                i += 1
            if text[i] != "(":
                break
            vals, i = sql_tuple(text, i)
            yield dict(zip(cols, vals))
            while text[i] in " \n\r\t":
                i += 1
            if text[i] != ",":
                break
            i += 1


def read_groups(path):
    out, cur = [], None
    for raw in open(path, encoding="utf-8", errors="replace"):
        line = raw.split("--")[0].strip()
        if not line:
            continue
        t = line.split()
        if t[0] == "Group":
            cur = {"key": None, "items": []}
            out.append(cur)
        elif cur is None:
            continue
        elif t[0] in ("Mob", "Vnum") and len(t) > 1:
            cur["key"] = int(t[1])
        elif t[0].isdigit() and len(t) >= 3:
            try:
                cur["items"].append((int(t[1]), int(t[2]) if t[2].isdigit() else 1, float(t[3]) if len(t) > 3 else 0.0))
            except ValueError:
                pass
    return out


def proto_row(r):
    return {"name": fold(str(r.get("locale_name", ""))), "type": r["type"], "sub": r["subtype"], "af": r["antiflag"],
            "gold": r["gold"], "sell": r["shop_buy_price"], "set": r["refine_set"], "next": r["refined_vnum"],
            "v0": r.get("value0", 0), "level": r["limitvalue0"] if r.get("limittype0") == 1 else 0}


def sql_files():
    return [os.path.join(SQL_DIR, "item_proto.mt2009plus.sql")] + sorted(
        os.path.join(SQL_DIR, f) for f in os.listdir(SQL_DIR) if f.endswith(".sql") and f != "item_proto.mt2009plus.sql")


def sql_text(path):
    raw = open(path, "rb").read()
    try:
        return raw.decode("utf-8")
    except UnicodeDecodeError:      # zbroje105.sql and a few more are cp1250
        return raw.decode("cp1250", "replace")


def ensure_items(snap, vnums):
    """The item_proto rows of `vnums` the snapshot lacks (the reference's new items), read from the repo's SQL
    alone - the drop / chest availability is left as it is. True when the snapshot changed."""
    missing = set(str(v) for v in vnums) - set(snap["items"])
    if not missing:
        return False
    for path in sql_files():
        text = sql_text(path)
        if "item_proto" not in text:
            continue
        for r in sql_inserts(text, "item_proto"):
            if isinstance(r.get("vnum"), int) and str(r["vnum"]) in missing:
                snap["items"][str(r["vnum"])] = proto_row(r)
                missing.discard(str(r["vnum"]))
    return True


def refresh(drops_path, chests_path):
    files = sql_files()
    items, mobs, refine, crafting = {}, {}, {}, {}
    rg_map = {}
    for path in files:
        text = sql_text(path)
        if "item_proto" in text:
            for r in sql_inserts(text, "item_proto"):
                if isinstance(r.get("vnum"), int) and r["vnum"] not in items:   # INSERT IGNORE: the first one stays
                    items[r["vnum"]] = proto_row(r)
        if "mob_proto" in text:
            for r in sql_inserts(text, "mob_proto"):
                if isinstance(r.get("vnum"), int) and r["vnum"] not in mobs:
                    mobs[r["vnum"]] = {"name": fold(str(r.get("locale_name", ""))), "rank": r.get("rank", 0),
                                       "level": r.get("level", 0)}
        if "refine_proto" in text:
            last = os.path.basename(path) == "refine_global.sql"   # ON DUPLICATE KEY UPDATE, run last
            for r in sql_inserts(text, "refine_proto"):
                if isinstance(r.get("id"), int) and (last or r["id"] not in refine):
                    refine[r["id"]] = {"mats": [(r["vnum%d" % k], r["count%d" % k]) for k in range(5)
                                                if r.get("vnum%d" % k)], "cost": r["cost"], "prob": r["prob"]}
            for m in re.finditer(r"UPDATE world\.refine_proto SET vnum1=(\d+), count1=(\d+) WHERE id=(\d+)", text):
                rid = int(m.group(3))
                if rid in refine and len(refine[rid]["mats"]) == 1:
                    refine[rid]["mats"].append((int(m.group(1)), int(m.group(2))))
            if last:
                for m in re.finditer(r"^\((\d+),(\d+),(\d+),\d+\),?$", text, re.M):
                    rg_map[int(m.group(1))] = int(m.group(3))
        if "crafting_proto" in text:
            for r in sql_inserts(text, "crafting_proto"):
                crafting[r["vnum"]] = r
    # the steps of every piece: refine_global's where it has one, else the item's own refine_set
    steps = {}
    for v, it in items.items():
        rid = rg_map.get(v, it["set"])
        if rid and rid in refine and it["next"]:
            steps[v] = refine[rid]
    # what recipes ask at once (refine steps + the cubes): the bulk test
    at_once = collections.defaultdict(int)
    for st in steps.values():
        for mv, n in st["mats"]:
            at_once[mv] = max(at_once[mv], n)
    for root, _, fs in os.walk(GAME_DIR):
        for f in fs:
            if f.startswith("cube") and f.endswith(".txt"):
                for mv, n in re.findall(r"^\s*item\s+(\d+)\s+(\d+)", open(os.path.join(root, f), encoding="utf-8",
                                                                          errors="replace").read(), re.M):
                    at_once[int(mv)] = max(at_once[int(mv)], int(n))
    # availability
    avail, top = collections.defaultdict(float), collections.defaultdict(list)
    for g in read_groups(drops_path):
        mob = mobs.get(g["key"], {})
        for v, c, p in g["items"]:
            w = RANK_WEIGHT.get(mob.get("rank", 4), 0.05)
            avail[v] += min(p, 100.0) / 100.0 * c * w
            top[v].append((min(p, 100.0) * c * w, "%s %g%%x%d" % (mob.get("name", "?")[:18], p, c)))
    for g in read_groups(chests_path):
        tot = sum(p for _, _, p in g["items"]) or 1.0
        for v, c, p in g["items"]:
            avail[v] += p / tot * c * CHEST_WEIGHT
            top[v].append((p / tot * 100 * c * CHEST_WEIGHT, "chest %s %.1f%%x%d" % (
                items.get(g["key"], {}).get("name", str(g["key"]))[:18], 100.0 * p / tot, c)))
    snap = {"items": {}, "steps": {}, "at_once": {}, "avail": {}, "sources": {}}
    for v in items:
        snap["items"][str(v)] = items[v]
    for v, st in steps.items():
        snap["steps"][str(v)] = st
    for v, n in at_once.items():
        snap["at_once"][str(v)] = n
    for v, s in avail.items():
        snap["avail"][str(v)] = round(s, 6)
        snap["sources"][str(v)] = "; ".join(t for _, t in sorted(top[v], reverse=True)[:2])
        snap["sources"][str(v)] += " (+%d more)" % (len(top[v]) - 2) if len(top[v]) > 2 else ""
    # keep only what the rules can reach (a smaller file)
    wanted = set()
    for _, rows in MATERIALS:
        for v, rule in rows:
            wanted.add(v)
            if rule[0] == "recipe":
                wanted.update(x for x, _ in rule[1])
            if rule[0] == "like":
                wanted.add(rule[1])
    for base, rule, _ in gear_rows():
        wanted.update(base + p for p in range(10))
        if rule[0] == "recipe":
            wanted.update(x for x, _ in rule[1])
    for v in list(wanted):
        for mv, _ in snap["steps"].get(str(v), {}).get("mats", []):
            wanted.add(mv)
    wanted.update(int(v) for v in json.load(open(REFERENCE, encoding="utf-8"))["items"])
    small = {k: {str(v): d[str(v)] for v in sorted(wanted) if str(v) in d} for k, d in snap.items()}
    json.dump(small, open(SNAPSHOT, "w"), indent=0, sort_keys=True, ensure_ascii=True)
    print("snapshot: %d items, %d steps, from %s and %s" % (len(small["items"]), len(small["steps"]), drops_path,
                                                         chests_path), file=sys.stderr)


# ---------------------------------------------------------------------------- the sheet as it stands
def strip_ours(text):
    for mk in (MARKER, SEONHAE_MARKER) + OLD_MARKERS:
        text = re.sub(r"// ---- BEGIN " + mk + r".*?// ---- END " + mk + r"[^\n]*\n", "", text, flags=re.S)
    return text


def sheet_prices(text):
    """vnum -> price of the rows outside our blocks (materials) and gear families."""
    text = strip_ours(text)
    consts = {k: int(v) for k, v in re.findall(r"const DWORD (PLAYERBOT_\w+)\s*=\s*(\d+)\s*;", text)}
    mats, gear = {}, set()
    for name in ("PLAYERBOT_MATERIAL_PRICES", "PLAYERBOT_EXTRA_MATERIAL_PRICES"):
        body = re.search(r"\b" + name + r"\[\]\s*=\s*\{(.*?)\n\s*\};", text, re.S).group(1)
        for m in re.finditer(r"\{\s*(\d+)\s*,\s*([^}]*?)\s*\}", re.sub(r"//[^\n]*", "", body)):
            expr = m.group(2)
            for k, v in consts.items():
                expr = expr.replace(k, str(v))
            mats.setdefault(int(m.group(1)), int(eval(expr.replace("/", "//"))))
    body = re.search(r"\bPLAYERBOT_GEAR_PRICES\[\]\s*=\s*\{(.*?)\n\s*\};", text, re.S).group(1)
    for m in re.finditer(r"\{\s*(\d+)\s*,\s*0x", re.sub(r"//[^\n]*", "", body)):
        gear.add(int(m.group(1)))
    return mats, gear


# ---------------------------------------------------------------------------- pricing
def round_price(p):
    if p >= 10000000:
        step = 100000
    elif p >= 1000000:
        step = 10000
    elif p >= 100000:
        step = 1000
    else:
        step = 100
    return int(max(step, round(p / step) * step))


class Pricer:
    def __init__(self, snap, sheet):
        self.snap, self.sheet = snap, sheet
        self.price, self.why = {}, {}
        self.rules = {}
        self.gear = dict((base, rule) for base, rule, _ in gear_rows())
        for _, rows in MATERIALS:
            for v, rule in rows:
                self.rules[v] = rule

    def item(self, v):
        return self.snap["items"].get(str(v), {})

    def name(self, v):
        return self.item(v).get("name") or str(v)

    def get(self, v, stack=()):
        if v in self.sheet:
            return self.sheet[v]
        if v == 72353:
            return TOPAZ
        if v in self.price:
            return self.price[v]
        if v - v % 10 in self.gear and v not in stack:     # a piece of a gear family priced here
            return self.ladder(v - v % 10, self.gear[v - v % 10])[0][v % 10]
        if v in stack or v not in self.rules:
            raise KeyError("no price for %d (%s), needed by %s" % (v, self.name(v), stack))
        p, why = self.make(v, self.rules[v], stack + (v,))
        self.price[v], self.why[v] = p, why
        return p

    def make(self, v, rule, stack):
        kind = rule[0]
        if kind == "fixed":
            return rule[1], "fixed: " + rule[2]
        if kind == "like":
            base = self.get(rule[1], stack)
            return round_price(base * rule[2]), "like %d %s (%s) x%g: %s" % (rule[1], self.name(rule[1]),
                                                                           "{:,}".format(base).replace(",", " "),
                                                                           rule[2], rule[3])
        if kind == "drop":
            cat = rule[1]
            s = self.snap["avail"].get(str(v), 0.0)
            if s <= 0:
                raise KeyError("%d %s: no drop or chest source - give it a fixed / like rule" % (v, self.name(v)))
            raw = P0[cat] * (S0 / s) ** K
            lo, hi = CLAMP[cat]
            p = min(hi, max(lo, raw))
            bulk = self.snap["at_once"].get(str(v), 0) >= BULK_FROM
            if bulk:
                p *= BULK_FACTOR
            why = "drop: S=%.4g -> %s%s%s [%s]" % (s, "{:,}".format(int(raw)).replace(",", " "),
                                                   " (clamped)" if raw != min(hi, max(lo, raw)) else "",
                                                   " x%g bulk (%d at once)" % (BULK_FACTOR, self.snap["at_once"][str(v)])
                                                   if bulk else "", self.snap["sources"].get(str(v), ""))
            return round_price(p), why
        if kind == "recipe":
            return self.recipe(rule, stack)
        raise ValueError(rule)

    def recipe(self, rule, stack):
        _, inputs, fee, pct, yld = rule
        cost = fee + sum(self.get(x, stack) * n for x, n in inputs)
        p = cost / (pct / 100.0) ** RISK / yld
        parts = ", ".join("%d x %s" % (n, self.name(x)) for x, n in inputs)
        return round_price(p), "recipe: %s%s, %d%% (^%g)" % (parts, " + %s Yang" % "{:,}".format(fee).replace(",", " ")
                                                            if fee else "", pct, RISK)

    def ladder(self, base, rule):
        if rule[0] == "recipe":
            v0, why0 = self.recipe(rule, (base,))
        else:
            v0, why0 = rule[1], "fixed: " + rule[2]
        vals = [float(v0)]
        notes = []
        for plus in range(9):
            st = self.snap["steps"].get(str(base + plus))
            if not st:
                vals += [vals[-1]] * (9 - plus)
                notes.append("no steps past +%d" % plus)
                break
            mats = 0.0
            for mv, n in st["mats"]:
                mats += (vals[-1] if mv == base + plus else self.get(mv, (base,))) * n
            vals.append((vals[-1] + mats + st["cost"]) / (st["prob"] / 100.0) ** RISK)
        if vals[9] > LADDER_CAP:
            k = min(4, max(i for i in range(10) if vals[i] <= LADDER_CAP))
            ratio = (LADDER_CAP / vals[k]) ** (1.0 / (9 - k))
            for i in range(k + 1, 10):
                vals[i] = vals[k] * ratio ** (i - k)
            notes.append("+%d..+9 squeezed to %s" % (k + 1, "{:,}".format(LADDER_CAP).replace(",", " ")))
        return [round_price(x) for x in vals], why0 + ("; " + "; ".join(notes) if notes else "")


# ---------------------------------------------------------------------------- the reference (MT2009_PLUS_YOHARA_PRICES_REF_V1)
# The key items the exchange ratio leaves out, and why.
RATIO_OUTLIERS = {
    27994: "Krwawa Perla: 37 593 there against our 2 275 850 (x60) - their market is flooded with it",
    123000: "Antyczny Rubin: 300 000 000 there is for stones with extra bonuses; ours is the alchemy formula",
    113000: "Antyczny Diament: as the ruby - 190 000 000 with bonuses against our formula",
    80017: "Kupon SM (50): an ItemShop coupon - their price is cash-shop money, ours a nominal 1 000 000",
}
OUT = 5                     # a sibling's reference more than OUT x off its family's median is pulled to the bound
MIN_GROUP = 3               # a group's own correction needs this many priced members, else the global one
LADDER_TOP = 3.0            # a new gear family: +9 = LADDER_TOP x +0, geometric
GEAR_CAP = 1500000000       # +9 at most
MAT_CAP = 300000000         # anything but gear at most
BOOK_FLOOR = 100000         # PLAYERBOT_BOOK_PRICE_FLOOR (playerbot_types.h): no skill book under it

# (key, title, table, siblings?, vnums[, the family whose correction an unpriced member takes])
# table: gear (PLAYERBOT_GEAR_PRICES, +0..+9), mat (PLAYERBOT_EXTRA_MATERIAL_PRICES), book (PLAYERBOT_BOOK_PRICES by
# the book's skill), soul (PLAYERBOT_SOUL_STONE_PRICES by kind and grade), seonhae (the Seon-Hae shard block).
FAMILIES = [
    ("bron_weza", "Serpent weapons (Swiatynia Wezy, lv 120; +10..+15 stay unpriced)", "gear", True,
     [360, 380, 1210, 2230, 3250, 5200, 7330]),
    ("zbroje_weza", "Serpent armours (lv 120)", "gear", True, [21310, 21330, 21350, 21370]),
    ("rekawice", "Sung Ma gloves", "gear", True, [23000, 23010, 23020, 23030]),
    ("jadeit_biz", "Jade jewellery", "gear", True,
     [14580, 14590, 14600, 14610, 16580, 16590, 16600, 16610, 17570, 17580, 17590, 17600]),
    ("talizman_woli", "Talizmany Woli", "gear", True, [81000, 81250, 81300, 81550]),
    ("talizman_taj", "Tajemniczy Talizman", "gear", False, [81560]),
    ("bron_smoka", "Smok Mroku weapons (PB, lv 96)", "gear", True, [320, 340, 1190, 2210, 3230, 5170, 7310]),
    ("zbroje_smoka", "Smok armours (PB, lv 96)", "gear", True, [21210, 21230, 21250, 21270]),
    ("helmy_smoka", "Smok helmets (PB, lv 96)", "gear", True, [12780, 12800, 12820, 12840]),
    ("zbroje105", "Armours of level 105-110 (Cyjanit, Polarny, Magmy, Wielorybi, Deszczu Popiolu sets)", "gear", True,
     [12050, 12060, 12070, 12080, 20760, 20770, 20780, 20790, 20810, 20820, 20830, 20840,
      20860, 20870, 20880, 20890, 20910, 20920, 20930, 20940]),
    ("demony", "Demon stones (the gloves' stones; kind 46 Kamien Demonow, 47 Kamien Mocy Demonow)", "soul", False,
     [28046, 28146, 28246, 28346, 28446, 28047, 28147, 28247, 28347, 28447]),
    ("polprodukty", "Serpent half-made pieces (wykon.)", "mat", True,
     [376, 396, 1226, 2246, 3266, 5216, 6166, 7346, 21326, 21346, 21366, 21386, 21406]),
    ("odl_lsn", "Lucent shards (Seon-Hae)", "mat", True, [39078, 39079, 39080]),
    ("odl_set1", "Set shards I (Seon-Hae)", "mat", True,
     [39085, 39086, 39087, 39091, 39092, 39093, 39097, 39098, 39099]),
    ("odl_set2", "Set shards II (Seon-Hae)", "mat", True,
     [39088, 39089, 39090, 39094, 39095, 39096, 39100, 39101, 39102], "odl_set1"),
    ("odl_set3", "Princely / majestic set shards (Seon-Hae)", "mat", True,
     [39103, 39104, 39105, 39106, 39107, 39108], "odl_set1"),
    ("projekty", "Set designs (Seon-Hae)", "mat", True, [39110, 39111, 39112]),
    ("seonhae", "Seon-Hae's ordinary shards", "seonhae", True,
     [39070, 39071, 39072, 39073, 39074, 39075, 39076, 39077, 39081]),
    ("perly", "Polyskujace perly", "mat", True, [31239, 31240, 31241]),
    ("rudy", "Jade ores", "mat", True, [50641, 50642, 50643, 50644]),
    ("jadeit", "Jade", "mat", True, [50661, 50662, 50663, 50664]),
    ("runy", "SungMa runes", "mat", True, [31247, 31248, 31249, 31250]),
    ("runy_aury", "Aura runes", "mat", False, [49991, 49992, 49993]),
    ("rekawice_mat", "Glove materials", "mat", False, [31225, 31245, 31246, 31251, 31252]),
    ("ulepszacze", "Serpent and north-wind refine materials", "mat", False,
     [31233, 31234, 31237, 31242, 31243, 31244, 31257, 31258, 31259, 31262, 31263, 70428]),
    ("drop_yohara", "Yohara map drops", "mat", False,
     [31216, 31217, 31218, 31224, 31226, 31227, 31228, 31235, 31236]),
    ("talizman_mat", "Talisman materials", "mat", False, [31270, 95500]),
    ("inne", "Other Yohara materials and chest contents", "mat", False,
     [30606, 30608, 31261, 55003, 90015, 90016, 90017, 27990, 30165, 30166, 30167, 30168, 30251, 30252, 50525,
      50527]),
    ("ziola", "Huahn-So's herbs", "mat", True, [95733, 95734, 95735, 95736, 50737, 50738]),
    ("butelki", "Empty elixir bottles", "mat", True, [50739, 50740]),
    ("eliksiry", "Elixirs", "mat", False, list(range(50830, 50842))),
    ("ksiegi9", "9th skill books", "book", False, list(range(50569, 50576))),
    ("riposty", "Riposte books", "book", False, list(range(50516, 50524))),
    ("dopalacze", "Booster books", "book", False, list(range(50560, 50568))),
    ("ksiegi_inne", "Book chests and manuals", "mat", False, [50529, 50323, 50324, 50514, 50515]),
    ("charyzma", "Charyzma / Inspiracja / Precyzja", "mat", True, [50338, 50339, 50340, 50341, 50342, 50343, 50325]),
    ("jazda", "Horse books (Yohara)", "mat", True, list(range(55050, 55068))),
    ("pb", "Przebudzeni Bossowie materials", "mat", False,
     [31108, 31109, 31110, 31111, 31112, 31113, 31114, 31115, 31117, 31120, 31121, 31149]),
    ("plaskowyz", "Plaskowyz Iluzji materials", "mat", False, [31118] + list(range(31122, 31139))),
    ("pb_plany", "PB plans", "mat", True,
     [31196, 31197, 31198, 31199, 31200, 31201, 31203, 31204, 31205, 31206, 31207, 31209, 31210, 31211, 31212]),
    ("zbroje105_mat", "Armour 105-120 materials", "mat", False,
     [30601, 30605, 30607, 30609, 30614, 30615, 30619, 30625, 30628]),
    ("skrzynie_boss", "Boss chests (priced for a counter; the bots still open them)", "mat", True,
     [54707, 50266, 54701, 54705, 54706, 31139, 31140, 31141, 31142, 31143, 70411, 70412, 70429]),
    ("skrzynie", "Boxes and caskets (priced for a counter; the bots still open them)", "mat", True,
     [31238, 39068, 83051, 95737, 31253, 31254, 31255, 31256, 50528, 72058, 83052, 83053, 83055, 83067, 70434]),
    ("klucze", "Dungeon keys, tickets and passes", "mat", True,
     [31160, 31180, 31167, 31168, 31169, 31170, 31171, 31187, 31188, 31189, 31190, 31191, 70408, 70410, 72740,
      70430]),
    ("klucze_skrz", "Chest keys", "mat", True, [50043, 83054, 83056]),
    ("og_mat", "General materials no row priced yet (they drop on Yohara too)", "mat", False,
     [30151, 30193, 30195, 30197, 30500] + list(range(30502, 30518)) + [30520, 30521, 71130, 100300]),
]
# An item without a reference priced from a named one: vnum -> (source, factor, why). A factor "a/b" is the ratio
# of the new prices of a and b.
ANALOGY = {
    16610: (14610, 1.0, "the Dymu jade's bracelet - no necklace offer"),
    17600: (14610, 1.0, "the Dymu jade's bracelet - no earring offer"),
    12780: (21210, 0.5, "half its set's armour"),
    12800: (21230, 0.5, "half its set's armour"),
    12820: (21250, 0.5, "half its set's armour"),
    12840: (21270, 0.5, "half its set's armour"),
    28047: (28046, "28447/28446", "Kamien Demonow of the grade x (Mocy+4 / Demonow+4)"),
    28147: (28146, "28447/28446", "Kamien Demonow of the grade x (Mocy+4 / Demonow+4)"),
    28247: (28246, "28447/28446", "Kamien Demonow of the grade x (Mocy+4 / Demonow+4)"),
    50739: (50740, 1.0, "the other empty bottle"),
    31140: (50266, 1.0, "the same boss's chest (Zaklety Las)"),
    50043: (83051, 0.5, "half a box-and-key pair (Id. Skrzynia Talizmanu)"),
    83054: (83051, 0.5, "half a box-and-key pair (Id. Skrzynia Talizmanu)"),
    83056: (83051, 0.5, "half a box-and-key pair (Id. Skrzynia Talizmanu)"),
}
# The provisional block this generator now writes (restored by --remove).
SEONHAE_PROVISIONAL = (
    "\t\t// ---- BEGIN MT2009_PLUS_SEONHAE_SHARD_PRICES_TEMP_V1 - PROVISIONAL prices of Seon-Hae's ordinary shards (the\n"
    "\t\t// owner, 28 October 2026: they drop for the bots too now and go on the counters; the real prices will come from\n"
    "\t\t// another server - replace this block then). Kept at the compendium sheet's suggestion (its factor in brackets),\n"
    "\t\t// which ranks them by the item level band each serves (MaterialVnum: grey the lowest ... red the highest, the\n"
    "\t\t// rainbow and the holy one beside) and sits in the range of the Lucent shards' drop-derived 315 000 - 515 000.\n"
    "\t\t{ 39070,   120000 },\t// Szary Odlamek (TEMP; suggested x2)\n"
    "\t\t{ 39071,   160000 },\t// Bialy Odlamek (TEMP; suggested x2)\n"
    "\t\t{ 39072,   300000 },\t// Zielony Odlamek (TEMP; suggested x3)\n"
    "\t\t{ 39073,   450000 },\t// Zolty Odlamek (TEMP; suggested x3)\n"
    "\t\t{ 39074,   750000 },\t// Niebieski Odlamek (TEMP; suggested x3)\n"
    "\t\t{ 39075,  1600000 },\t// Fioletowy Odlamek (TEMP; suggested x4)\n"
    "\t\t{ 39076,  1800000 },\t// Czerwony Odlamek (TEMP; suggested x4)\n"
    "\t\t{ 39077,   350000 },\t// Teczowy Odlamek (TEMP; suggested)\n"
    "\t\t{ 39081,   300000 },\t// Swiety Odlamek (TEMP; suggested)\n"
    "\t\t// ---- END MT2009_PLUS_SEONHAE_SHARD_PRICES_TEMP_V1\n")
SEONHAE_BASE = {39070: 120000, 39071: 160000, 39072: 300000, 39073: 450000, 39074: 750000, 39075: 1600000,
                39076: 1800000, 39077: 350000, 39081: 300000}


def fmt(n):
    return "{:,}".format(int(round(n))).replace(",", " ")


def load_reference():
    return json.load(open(REFERENCE, encoding="utf-8"))


def exchange_ratio(ref):
    """R = our Yang / theirs: the median over the key items, one per vnum, without RATIO_OUTLIERS."""
    rows, seen = [], set()
    for k in ref["key_items"]:
        if not k["vnum"] or not k["ours"] or not k["theirs"]:
            rows.append(dict(k, ratio=None, used=False, why="no price on one side"))
            continue
        r = float(k["ours"]) / k["theirs"]
        if k["vnum"] in RATIO_OUTLIERS:
            rows.append(dict(k, ratio=r, used=False, why=RATIO_OUTLIERS[k["vnum"]]))
        elif k["vnum"] in seen:
            rows.append(dict(k, ratio=r, used=False, why="the same item as a row above"))
        else:
            seen.add(k["vnum"])
            rows.append(dict(k, ratio=r, used=True, why=""))
    used = sorted(x["ratio"] for x in rows if x["used"])
    logs = [math.log(x) for x in used]
    trim = logs[2:-2] if len(logs) > 6 else logs
    stats = {"median": statistics.median(used), "n": len(used), "geomean": math.exp(sum(logs) / len(logs)),
             "trimmed_geomean": math.exp(sum(trim) / len(trim)), "min": used[0], "max": used[-1]}
    return round(stats["median"], 3), rows, stats


class RefPricer:
    """The reference prices on top of the TEMP baseline."""

    def __init__(self, snap, sheet_mats, sheet_gear, ref, old_text):
        self.snap, self.ref = snap, ref
        self.R, self.ratio_rows, self.ratio_stats = exchange_ratio(ref)
        self.base_pr = Pricer(snap, sheet_mats)
        self.sheet_mats, self.sheet_gear = sheet_mats, sheet_gear
        self.temp_gear = dict((b, rule) for b, rule, _ in gear_rows())
        self.fam = {}
        for f in FAMILIES:
            for v in f[4]:
                if v in self.fam:
                    raise ValueError("%d in two families" % v)
                self.fam[v] = f
        self.old = old_prices(old_text)
        self.new, self.how, self.src = {}, {}, {}
        self.shape = {}
        self.skipped = []

    # -- what we know of an item
    def item(self, v):
        return self.snap["items"].get(str(v), {})

    def name(self, v):
        n = self.item(v).get("name") or (self.ref["items"].get(str(v), {}).get("name")) or str(v)
        return fold(n)

    def refrow(self, v):
        return self.ref["items"].get(str(v), {})

    def base(self, v):
        """The TEMP_V1 baseline (+0 for gear), or None."""
        f = self.fam[v]
        if f[2] == "seonhae":
            return SEONHAE_BASE.get(v)
        if f[2] == "gear":
            if v in self.temp_gear:
                return self.base_ladder(v)[0]
            return None
        if v in self.base_pr.rules:
            try:
                return self.base_pr.get(v)
            except KeyError:
                return None
        return None

    def base_ladder(self, v):
        if v not in self.shape:
            self.shape[v] = self.base_pr.ladder(v, self.temp_gear[v])[0]
        return self.shape[v]

    def ladder_shape(self, v):
        if v in self.temp_gear:
            lad = self.base_ladder(v)
            return [x / float(lad[0]) for x in lad], "the TEMP ladder's shape"
        step = LADDER_TOP ** (1.0 / 9)
        return [step ** i for i in range(10)], "geometric to %gx +0 at +9" % LADDER_TOP

    def unusable(self, v):
        """Why the item can not be priced here, or None."""
        it = self.item(v)
        if not it:
            return "not in item_proto"
        if it.get("af", 0) & NO_TRADE:
            return "no shop / no trade (anti-flags %d)" % it["af"]
        if self.fam[v][2] in ("mat", "seonhae") and v in self.sheet_mats:
            return "the owner's sheet prices it (%s)" % fmt(self.sheet_mats[v])
        if self.fam[v][2] == "gear" and v in self.sheet_gear:
            return "the owner's sheet prices the family"
        return None

    # -- step 1: the reference x R
    def reference(self, v):
        r = self.refrow(v)
        if not r.get("median"):
            return None, None
        if r.get("bonus"):
            return None, "offers with extra bonuses only - not used"
        p = r["median"] * self.R
        if self.fam[v][2] == "gear":
            plus = r.get("plus") or 0
            shape, _ = self.ladder_shape(v)
            p = p / shape[min(plus, 9)]
        n = len(r.get("offers") or [])
        return p, "ref %s x %g (median of %d offer%s%s)" % (
            fmt(r["median"]), self.R, n, "" if n == 1 else "s",
            ", +%d" % r["plus"] if r.get("plus") else "")

    def run(self):
        live = []
        for f in FAMILIES:
            for v in f[4]:
                why = self.unusable(v)
                if why:
                    self.skipped.append((v, self.name(v), f[1], why))
                else:
                    live.append(v)
        self.live = live
        refp, note = {}, {}
        for v in live:
            p, n = self.reference(v)
            if p is not None:
                refp[v] = p
            if n:
                note[v] = n
        # step 2: siblings pulled to OUT x their family's median
        for f in FAMILIES:
            if not f[3]:
                continue
            got = [refp[v] for v in f[4] if v in refp]
            if len(got) < 3:
                continue
            med = math.exp(statistics.median(math.log(x) for x in got))
            for v in f[4]:
                if v in refp:
                    lo, hi = med / OUT, med * OUT
                    if refp[v] > hi * 1.001 or refp[v] < lo / 1.001:
                        bound = hi if refp[v] > hi else lo
                        note[v] += "; pulled to %gx the family median (%s)" % (OUT if bound == hi else 1.0 / OUT,
                                                                            fmt(bound))
                        refp[v] = bound
        # demon stones: never under the grade below
        for kind in (46, 47):
            prev = None
            for g in range(5):
                v = 28000 + 100 * g + kind
                if v in refp:
                    if prev is not None and refp[v] < prev:
                        note[v] += "; raised to the grade below (%s)" % fmt(prev)
                        refp[v] = prev
                    prev = refp[v]
        for v, p in refp.items():
            self.new[v], self.how[v] = p, note[v]
        self.refp, self.notes = refp, note
        # step 3: corrections (ref / baseline)
        self.corr = {}
        allc = []
        for f in FAMILIES:
            cs = []
            for v in f[4]:
                b = self.base(v) if v in refp else None
                if b:
                    cs.append(refp[v] / b)
            self.corr[f[0]] = (statistics.median(cs), len(cs)) if cs else (None, 0)
            if f[2] in ("mat", "seonhae"):
                allc += cs
        self.global_corr = (statistics.median(allc), len(allc))
        # step 4: the unpriced, by analogy (in rounds: an analogy may wait for another)
        todo = [v for v in live if v not in refp]
        for _ in range(5):
            left = []
            for v in todo:
                if not self.analogy(v):
                    left.append(v)
            todo = left
            if not todo:
                break
        if todo:
            raise KeyError("no analogy for %s" % ", ".join("%d %s" % (v, self.name(v)) for v in todo))
        # step 5: bounds
        for v in live:
            f = self.fam[v]
            sell = self.item(v).get("sell", 0) or 0
            p = self.new[v]
            if f[2] == "book" and p < BOOK_FLOOR:
                self.how[v] += "; raised to the book floor %s" % fmt(BOOK_FLOOR)
                p = BOOK_FLOOR
            if f[2] != "gear" and p > MAT_CAP:
                self.how[v] += "; capped at %s" % fmt(MAT_CAP)
                p = MAT_CAP
            if p < sell:
                self.how[v] += "; raised to the merchant's %s" % fmt(sell)
                p = sell
            self.new[v] = p
        self.ladders = {}
        for v in live:
            if self.fam[v][2] == "gear":
                self.ladders[v] = self.ladder(v)
        return self

    def analogy(self, v):
        f = self.fam[v]
        a = ANALOGY.get(v)
        if a:
            src, fac, why = a
            if src not in self.new:
                return False
            if isinstance(fac, str):
                x, y = (int(t) for t in fac.split("/"))
                if x not in self.new or y not in self.new:
                    return False
                fac = self.new[x] / self.new[y]
            self.new[v] = self.new[src] * fac
            self.how[v] = "analogia: %d %s x %.2f (%s)" % (src, self.name(src), fac, why)
            self.src[v] = src
            return True
        rule = self.base_pr.rules.get(v)
        if rule and rule[0] == "like" and rule[1] in self.new and rule[1] in self.refp:
            self.new[v] = self.new[rule[1]] * rule[2]
            self.how[v] = "analogia: %d %s x %g (the TEMP rule: %s)" % (rule[1], self.name(rule[1]), rule[2], rule[3])
            self.src[v] = rule[1]
            return True
        b = self.base(v)
        priced = [u for u in f[4] if u in self.refp]
        if f[3]:
            sib = [(u, self.refp[u] / self.base(u)) for u in priced if self.base(u)]
            if b and sib:
                c = statistics.median(x for _, x in sib)
                self.new[v] = b * c
                self.how[v] = "analogia: TEMP %s x %.3g, the siblings' median correction (%s)" % (
                    fmt(b), c, ", ".join(str(u) for u, _ in sib))
                self.src[v] = sib[0][0]
                return True
            if priced:
                self.new[v] = statistics.median(self.refp[u] for u in priced)
                self.how[v] = "analogia: the family's median of %d priced (%s)" % (
                    len(priced), ", ".join(str(u) for u in priced))
                self.src[v] = priced[0]
                return True
        if b:
            c, n = self.corr[f[0]]
            where = "the group's"
            if n < MIN_GROUP and len(f) > 5:
                c, n = self.corr[f[5]]
                where = "the %s group's" % f[5]
            if c is None or n < MIN_GROUP:
                c, n = self.global_corr
                where = "the global (all priced materials)"
            self.new[v] = b * c
            self.how[v] = "analogia: TEMP %s x %.3g, %s median correction over %d" % (fmt(b), c, where, n)
            return True
        return False

    def ladder(self, v):
        shape, how = self.ladder_shape(v)
        if v in OWNER_PLUS0:
            self.new[v] = OWNER_PLUS0[v]
            self.how[v] = "the owner, 28 Oct 2026: +0 at %s" % fmt(OWNER_PLUS0[v])
        p0 = self.new[v]
        vals = [p0 * s for s in shape]
        if vals[9] > GEAR_CAP:
            if p0 >= GEAR_CAP:
                vals = [float(GEAR_CAP)] * 10
            else:
                st = (GEAR_CAP / p0) ** (1.0 / 9)
                vals = [p0 * st ** i for i in range(10)]
            how += ", +9 capped at %s" % fmt(GEAR_CAP)
        self.how[v] += "; ladder: " + how
        return [round_price(x) for x in vals]

    def price(self, v):
        return round_price(self.new[v])


def old_prices(text):
    """vnum -> what the header prices it at now ([+0..+9] for gear), whoever's row it is."""
    out = {}
    for name in ("PLAYERBOT_MATERIAL_PRICES", "PLAYERBOT_EXTRA_MATERIAL_PRICES"):
        m = re.search(r"\b" + name + r"\[\]\s*=\s*\{(.*?)\n\t\};", text, re.S)
        for r in re.finditer(r"^\s*\{\s*(\d+)\s*,\s*(\d+)\s*\}", m.group(1), re.M):
            out.setdefault(int(r.group(1)), int(r.group(2)))
    m = re.search(r"\bPLAYERBOT_GEAR_PRICES\[\]\s*=\s*\{(.*?)\n\t\};", text, re.S)
    for r in re.finditer(r"\{\s*(\d+),\s*0x[0-9a-f]+,\s*\{([^}]*)\}", m.group(1)):
        out.setdefault(int(r.group(1)), [int(x) for x in r.group(2).split(",")])
    return out


def own_tables(text):
    """The owner's rows (our blocks taken out): materials, gear, books by skill, soul stones by (kind, grade)."""
    mats, gear = sheet_prices(text)
    t = strip_ours(text)
    gl = {}
    m = re.search(r"\bPLAYERBOT_GEAR_PRICES\[\]\s*=\s*\{(.*?)\n\t\};", t, re.S)
    for r in re.finditer(r"\{\s*(\d+),\s*0x[0-9a-f]+,\s*\{([^}]*)\}", re.sub(r"//[^\n]*", "", m.group(1))):
        gl[int(r.group(1))] = [int(x) for x in r.group(2).split(",")]
    books = {}
    m = re.search(r"\bPLAYERBOT_BOOK_PRICES\[\]\s*=\s*\{(.*?)\n\t\};", t, re.S)
    for r in re.finditer(r"\{\s*(\d+)\s*,\s*(\d+)\s*\}", re.sub(r"//[^\n]*", "", m.group(1))):
        books[int(r.group(1))] = int(r.group(2))
    souls = {}
    m = re.search(r"\bPLAYERBOT_SOUL_STONE_PRICES\[\]\s*=\s*\{(.*?)\n\t\};", t, re.S)
    for r in re.finditer(r"\{\s*(\d+)\s*,\s*(\d+)\s*,\s*(\d+)\s*\}", re.sub(r"//[^\n]*", "", m.group(1))):
        souls[(int(r.group(1)), int(r.group(2)))] = int(r.group(3))
    grades = [int(x) for x in re.search(r"PLAYERBOT_SOUL_STONE_GRADE_PRICES\[\d+\]\s*=\s*\{([^}]*)\}", t).group(1)
              .split(",")]
    return mats, gl, books, souls, grades


def conflicts(rp, text):
    """The owner's rows (outside our blocks) the reference x R differs from by more than 2x."""
    mats, gear, books, souls, grades = own_tables(text)
    out, seen = [], set()

    def own(v, plus):
        it = rp.item(v)
        if v in mats:
            return mats[v], "material row"
        base = v - v % 10
        if it.get("type") in (1, 2) and base in gear:
            return gear[base][min(plus, 9)], "gear row %d +%d" % (base, plus)
        if it.get("type") == 17 and it.get("v0") in books:
            return books[it["v0"]], "book row (skill %d)" % it["v0"]
        if it.get("type") == 10 and 28000 <= v < 29000:
            kind, grade = v % 100, (v // 100) % 10
            if (kind, grade) in souls:
                return souls[(kind, grade)], "soul stone row (%d, %d)" % (kind, grade)
            if grade < 5 and grades[grade]:
                return grades[grade], "soul stone grade default +%d" % grade
        return None, None

    for vs, r in rp.ref["items"].items():
        v = int(vs)
        if not r.get("median") or v in rp.live:
            continue
        ours, where = own(v, r.get("plus") or 0)
        if not ours:
            continue
        exp = r["median"] * rp.R
        k = exp / ours
        seen.add(v)
        if k > 2 or k < 0.5:
            out.append({"vnum": v, "name": rp.name(v), "group": r["group"], "where": where, "ours": ours,
                        "theirs": r["median"], "theirs_x_R": round(exp), "factor": k,
                        "note": ("offers with extra bonuses; " if r.get("bonus") else "") + (r.get("note") or "")[:160]})
    for k in rp.ratio_rows:
        if not k["vnum"] or k["vnum"] in seen or not k["theirs"] or not k["ours"]:
            continue
        seen.add(k["vnum"])
        exp = k["theirs"] * rp.R
        f = exp / float(k["ours"])
        if f > 2 or f < 0.5:
            out.append({"vnum": k["vnum"], "name": k["name"], "group": "Kluczowe przedmioty", "where": "the owner's key sheet",
                        "ours": k["ours"], "theirs": k["theirs"], "theirs_x_R": round(exp), "factor": f,
                        "note": (k["why"] + "; " if k["why"] else "") + k["note"][:160]})
    return sorted(out, key=lambda x: -abs(math.log(x["factor"])))


# ---------------------------------------------------------------------------- writing
HEAD = ("\t\t// ---- BEGIN %s - Yohara prices from the reference server's market (28.10.2026) x the exchange\n"
        "\t\t// ratio R = %g (our Yang / theirs, the median over the owner's key items). GENERATED by\n"
        "\t\t// tools/yohara_prices/gen_yohara_prices.py from reference_prices_20261028.json - edit the script or the\n"
        "\t\t// data, not these rows; delete the block (or run it with --remove) to go back. Each row: how it was made.\n")
TAIL = "\t\t// ---- END %s\n"
SEONHAE_HEAD = ("\t\t// ---- BEGIN %s - Seon-Hae's ordinary shards at the reference server's market (28.10.2026)\n"
                "\t\t// x R = %g, the real prices the provisional rows of 28 October waited for. GENERATED by\n"
                "\t\t// tools/yohara_prices/gen_yohara_prices.py (--remove puts the provisional rows back).\n")


def comment(s):
    return fold(s).replace("\n", " ")


def render(rp):
    by_table = collections.OrderedDict((t, []) for t in ("gear", "mat", "book", "soul", "seonhae"))
    for f in FAMILIES:
        rows = [v for v in f[4] if v in rp.live]
        if rows:
            by_table[f[2]].append((f, rows))
    out = {}
    lines = [HEAD % (MARKER, rp.R)]
    for f, rows in by_table["gear"]:
        lines.append("\t\t// %s\n" % f[1])
        for v in rows:
            lines.append("\t\t{ %5d, 0x000, { %s } },\t// %s (REF: %s)\n" % (
                v, ", ".join(str(x) for x in rp.ladders[v]), rp.name(v).split("+")[0], comment(rp.how[v])))
    out["PLAYERBOT_GEAR_PRICES"] = "".join(lines + [TAIL % MARKER])
    lines = [HEAD % (MARKER, rp.R)]
    for f, rows in by_table["mat"]:
        lines.append("\t\t// %s\n" % f[1])
        for v in rows:
            lines.append("\t\t{ %5d, %9d },\t// %s (REF: %s)\n" % (v, rp.price(v), rp.name(v), comment(rp.how[v])))
    out["PLAYERBOT_EXTRA_MATERIAL_PRICES"] = "".join(lines + [TAIL % MARKER])
    lines = [HEAD % (MARKER, rp.R)]
    for f, rows in by_table["book"]:
        lines.append("\t\t// %s\n" % f[1])
        for v in rows:
            lines.append("\t\t{ %3d, %9d },\t// %d %s (REF: %s)\n" % (rp.item(v)["v0"], rp.price(v), v, rp.name(v),
                                                                     comment(rp.how[v])))
    out["PLAYERBOT_BOOK_PRICES"] = "".join(lines + [TAIL % MARKER])
    lines = [HEAD % (MARKER, rp.R)]
    for f, rows in by_table["soul"]:
        lines.append("\t\t// %s\n" % f[1])
        for v in sorted(rows, key=lambda x: (x % 100, x)):
            lines.append("\t\t{ %d, %d, %10d },\t// %d %s (REF: %s)\n" % (v % 100, (v // 100) % 10, rp.price(v), v,
                                                                          rp.name(v), comment(rp.how[v])))
    out["PLAYERBOT_SOUL_STONE_PRICES"] = "".join(lines + [TAIL % MARKER])
    lines = [SEONHAE_HEAD % (SEONHAE_MARKER, rp.R)]
    for f, rows in by_table["seonhae"]:
        for v in rows:
            lines.append("\t\t{ %5d, %9d },\t// %s (REF: %s)\n" % (v, rp.price(v), rp.name(v), comment(rp.how[v])))
    out["seonhae"] = "".join(lines + [TAIL % SEONHAE_MARKER])
    return out


def put_block(text, table, block):
    """The table's block (ours, and the TEMP_V1 one before it) replaced by `block` (taken out when it is empty)."""
    m = re.search(r"\b" + table + r"\[\]\s*=\s*\{(.*?)(\n\t\};)", text, re.S)
    if not m:
        sys.exit("gen_yohara_prices: table %s not found" % table)
    body = m.group(1)
    for mk in (MARKER,) + OLD_MARKERS:
        body = re.sub(r"\n\t\t// ---- BEGIN " + mk + r".*?\t\t// ---- END " + mk, "", body, flags=re.S)
    if block:
        body = body + "\n" + block.rstrip("\n")
    return text[:m.start(1)] + body + text[m.end(1):]


def put_seonhae(text, block):
    pat = re.compile(r"\t\t// ---- BEGIN " + SEONHAE_MARKER + r".*?\t\t// ---- END " + SEONHAE_MARKER + r"[^\n]*\n",
                     re.S)
    if not pat.search(text):
        sys.exit("gen_yohara_prices: the %s block is not there" % SEONHAE_MARKER)
    return pat.sub(lambda _: block, text, count=1)


TABLE_NAMES = ("PLAYERBOT_GEAR_PRICES", "PLAYERBOT_EXTRA_MATERIAL_PRICES", "PLAYERBOT_BOOK_PRICES",
               "PLAYERBOT_SOUL_STONE_PRICES")


def write_sheet():
    sys.path.insert(0, SHEET_DIR)
    import gen_sheet as gs  # noqa: E402 - the panel's own readers
    prices = open(TABLES, encoding="latin-1").read()
    path = os.path.join(SHEET_DIR, "sheet.py")
    sheet = open(path, encoding="utf-8").read()
    gear = ["GEAR = {\n"]
    for r in gs.rows(gs.table(prices, "PLAYERBOT_GEAR_PRICES")):
        n = gs.ints(r)
        gear.append("    %d: (0x%03x, (%s)),\n" % (n[0], n[1], ", ".join(str(x) for x in n[2:12])))
    gear.append("}\n")
    consts = {k: int(v) for k, v in re.findall(r"const DWORD (PLAYERBOT_\w+)\s*=\s*(\d+)\s*;", prices)}

    def material(r):
        vnum, expr = [p.strip() for p in r.split(",")[:2]]
        for k, v in consts.items():
            expr = expr.replace(k, str(v))
        return int(vnum), int(eval(expr.replace("/", "//")))
    first = [material(r) for r in gs.rows(gs.table(prices, "PLAYERBOT_MATERIAL_PRICES"))]
    extra = [material(r) for r in gs.rows(gs.table(prices, "PLAYERBOT_EXTRA_MATERIAL_PRICES"))]
    mats = ["MATERIALS = {\n"] + ["    %d: %d,\n" % kv for kv in sorted(dict(first + extra).items())]
    mats += ["}\n# The first table (upgrade materials).\nREFINE_MATERIALS = frozenset((\n"]
    mats += ["    %d,\n" % v for v in sorted(set(v for v, _ in first))] + ["))\n"]
    books = ["BOOKS = {\n"] + ["    %d: %d,\n" % tuple(gs.ints(r)[:2])
                               for r in gs.rows(gs.table(prices, "PLAYERBOT_BOOK_PRICES"))] + ["}\n"]
    souls = ["SOUL_STONES = {\n"] + ["    (%d, %d): %d,\n" % tuple(gs.ints(r)[:3])
                                     for r in gs.rows(gs.table(prices, "PLAYERBOT_SOUL_STONE_PRICES"))] + ["}\n"]
    sheet = re.sub(r"GEAR = \{\n.*?\n\}\n", lambda _: "".join(gear), sheet, count=1, flags=re.S)
    sheet = re.sub(r"MATERIALS = \{\n.*?\n\}\n# The first table \(upgrade materials\)\.\nREFINE_MATERIALS = "
                   r"frozenset\(\(\n.*?\n\)\)\n", lambda _: "".join(mats), sheet, count=1, flags=re.S)
    sheet = re.sub(r"BOOKS = \{\n.*?\n\}\n", lambda _: "".join(books), sheet, count=1, flags=re.S)
    sheet = re.sub(r"SOUL_STONES = \{\n.*?\n\}\n", lambda _: "".join(souls), sheet, count=1, flags=re.S)
    open(path, "w", encoding="utf-8").write(sheet)


def report(rp, text, path):
    rows = []
    for f in FAMILIES:
        for v in f[4]:
            if v not in rp.live:
                continue
            r = rp.refrow(v)
            old = rp.old.get(v)
            if f[2] == "book":
                m = re.search(r"\{\s*%d\s*,\s*(\d+)\s*\}" % rp.item(v)["v0"],
                              re.search(r"PLAYERBOT_BOOK_PRICES\[\]\s*=\s*\{(.*?)\n\t\};", text, re.S).group(1))
                old = int(m.group(1)) if m else None
            if f[2] == "soul":
                old = None
            rows.append({"vnum": v, "name": rp.name(v), "family": f[1], "table": f[2],
                         "old": old[0] if isinstance(old, list) else old,
                         "old9": old[9] if isinstance(old, list) else None,
                         "ref": r.get("median"), "ref_plus": r.get("plus"), "offers": len(r.get("offers") or []),
                         "ref_bonus": bool(r.get("bonus")),
                         "new": rp.ladders[v][0] if f[2] == "gear" else rp.price(v),
                         "new9": rp.ladders[v][9] if f[2] == "gear" else None,
                         "method": "reference" if v in rp.refp else "analogia",
                         "src": rp.src.get(v), "how": rp.how[v]})
    json.dump({"R": rp.R, "ratio_stats": rp.ratio_stats, "ratio_rows": rp.ratio_rows, "rows": rows,
               "skipped": rp.skipped, "conflicts": conflicts(rp, text),
               "global_corr": rp.global_corr, "corr": rp.corr},
              open(path, "w", encoding="utf-8"), indent=1, ensure_ascii=False, default=str)


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--refresh", action="store_true")
    ap.add_argument("--drops", default=os.path.join(LIVE, "drops", "image.live"))
    ap.add_argument("--chests", default=os.path.join(LIVE, "chests", "live.new"))
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--remove", action="store_true")
    ap.add_argument("--ratio", action="store_true")
    ap.add_argument("--conflicts", action="store_true")
    ap.add_argument("--report")
    a = ap.parse_args()
    text = open(TABLES, encoding="latin-1").read()
    if a.remove:
        for t in TABLE_NAMES:
            text = put_block(text, t, "")
        text = put_seonhae(text, SEONHAE_PROVISIONAL)
        open(TABLES, "w", encoding="latin-1").write(text)
        write_sheet()
        return
    if a.refresh:
        refresh(a.drops, a.chests)
    snap = json.load(open(SNAPSHOT))
    ref = load_reference()
    if ensure_items(snap, [int(v) for v in ref["items"]] + [v for f in FAMILIES for v in f[4]]):
        json.dump(snap, open(SNAPSHOT, "w"), indent=0, sort_keys=True, ensure_ascii=True)
    sheet_mats, sheet_gear = sheet_prices(text)
    rp = RefPricer(snap, sheet_mats, sheet_gear, ref, text).run()
    if a.ratio:
        print("R = %g  (%s)" % (rp.R, ", ".join("%s %.3f" % kv for kv in sorted(rp.ratio_stats.items()))))
        for k in rp.ratio_rows:
            print("%-6s %-45s ours %12s theirs %14s ratio %s %s" % (
                k["vnum"], fold(k["name"])[:45], fmt(k["ours"] or 0), fmt(k["theirs"] or 0),
                "%.4f" % k["ratio"] if k["ratio"] else "-", "used" if k["used"] else "OUT: " + k["why"]))
        return
    if a.conflicts:
        for c in conflicts(rp, text):
            print("%6d %-28s %-30s ours %13s theirs x R %13s  x%.2f" % (
                c["vnum"], fold(c["name"])[:28], c["where"][:30], fmt(c["ours"]), fmt(c["theirs_x_R"]), c["factor"]))
        return
    if a.report:
        report(rp, text, a.report)
    blocks = render(rp)
    if a.dry_run:
        for t in TABLE_NAMES:
            sys.stdout.write(blocks[t])
        sys.stdout.write(blocks["seonhae"])
    else:
        for t in TABLE_NAMES:
            text = put_block(text, t, blocks[t])
        text = put_seonhae(text, blocks["seonhae"])
        open(TABLES, "w", encoding="latin-1").write(text)
        write_sheet()
    n_ref = sum(1 for v in rp.live if v in rp.refp)
    print("R = %g; %d rows (%d from the reference, %d by analogy); left out: %s" % (
        rp.R, len(rp.live), n_ref, len(rp.live) - n_ref,
        "; ".join("%d %s" % (s[0], s[3]) for s in rp.skipped) or "none"), file=sys.stderr)


if __name__ == "__main__":
    main()
