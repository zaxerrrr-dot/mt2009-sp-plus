#!/usr/bin/env python3
"""gen_yohara_prices.py - MT2009_PLUS_YOHARA_PRICES_TEMP_V1: a TEMPORARY, approximate price list of the
Yohara-era items for the bots' market (the owner, 27 October 2026: "Dodaj jakos mniej wiecej, logicznie cennik
przedmiotow z yohary, tak aby byl tymczasowy, bo teraz boty nie ogarniaja w ogole").

What it writes (and nothing else):
  * linux-port/overlays/playerbot/src/game/src/playerbot_price_tables.h - two blocks between the markers
        // ---- BEGIN MT2009_PLUS_YOHARA_PRICES_TEMP_V1 ...   and   // ---- END MT2009_PLUS_YOHARA_PRICES_TEMP_V1
    one at the end of PLAYERBOT_GEAR_PRICES (the Sung Ma gloves, the Talizmany Woli, the jade jewellery) and one at
    the end of PLAYERBOT_EXTRA_MATERIAL_PRICES (the materials, ores, jade, herbs, elixirs, set shards). Every row
    says how its number was made. Rows outside the blocks (the owner's / Iwakura's) are never touched, and a vnum
    they already price is never written again (the sheet's number wins).
  * linux-port/docker/seban-panel/market_preview/sheet.py - its GEAR, MATERIALS and REFINE_MATERIALS rendered again
    from the header with gen_sheet.py's own readers, so the panel's market preview shows the same numbers.

Every price is the sheet's base (x1.0, before the yang-rate curve and the world's inflation), like every other
row of the sheet. To change one: edit OVERRIDES (or a constant) below and run the script again; to drop the lot:
delete the two blocks (or run with --remove) - the bots fall back to what they did before.

    python3 tools/yohara_prices/gen_yohara_prices.py            # write the blocks + the panel sheet
    python3 tools/yohara_prices/gen_yohara_prices.py --dry-run  # print the rows only
    python3 tools/yohara_prices/gen_yohara_prices.py --refresh [--drops F --chests F]
        # read item_proto / refine_proto / crafting from the repo's SQL and the drop / chest tables of a running
        # world again into snapshot.json (default: the Yohara test server's live files), then write
    python3 tools/yohara_prices/gen_yohara_prices.py --remove   # take the two blocks out again

How a number is made (the rule is in each row's comment):
  drop     a material by how easy it is to come by. Availability S = the sum over every monster that drops it of
           chance x count x a weight of the monster's rank (ordinary 1, elite 0.5, ...0.3, boss 0.05, Metin /
           king 0.1) plus every chest that holds it (share x count x 0.05). price = P0 x (S0 / S) ^ K, clamped -
           P0 300 000 at S0 0.2, K 0.4, 60 000 .. 3 000 000 for a material (fitted to the sheet's own suggested
           Yohara-era rows: Mithril 200 000 at S 0.19, Dwutlenek Tytanu 600 000 at 0.10, Ksiega Prawdy 3 000 000 at
           0.001); a herb or a bottle P0 20 000, 5 000 .. 60 000 (the sheet's late herbs are 19 000). x0.4 for a
           material a recipe asks 10 or more of at once ("bulk": Utwardzacz Skory goes 10..200 a glove step).
  recipe   what it costs to make: the inputs at their prices + the fee, over the chance ^ RISK (0.5 - half of the
           risk of a failure is in the price; the whole of it made the 30 % jade and its jewellery dearer than any
           piece of gear on the sheet), over the yield.
  ladder   gear +0 .. +9: +0 by its recipe (or fixed), every next plus = (this plus + the step's materials + the
           smith's fee) / chance ^ RISK, from the world's refine_proto (refine_global.sql's steps where it has them);
           a Talizman Woli step eats a second talisman of the same plus. A ladder whose +9 passes LADDER_CAP is squeezed:
           +5..+9 climb geometrically from +4 (or the last plus under the cap) to LADDER_CAP at +9.
  like     another priced item's number x a factor (a sibling, the same thing in a new colour).
  fixed    a number with its reason (no source in this world yet, or a choice).
Never under what the merchant pays for it; nothing here is sold by an NPC shop for Yang (so no NPC cap applies).
Items that can not be put on a shop or given (anti-flags MYSHOP / GIVE), the Young Heroes' weapons (21900-21975),
the chests and keys (bots open them; their worth is a lottery of gear) and the quest items are left out on purpose.
"""
import argparse
import collections
import json
import math
import os
import re
import sys
import unicodedata

MARKER = "MT2009_PLUS_YOHARA_PRICES_TEMP_V1"
HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.normpath(os.path.join(HERE, "..", ".."))
TABLES = os.path.join(ROOT, "linux-port", "overlays", "playerbot", "src", "game", "src", "playerbot_price_tables.h")
SHEET_DIR = os.path.join(ROOT, "linux-port", "docker", "seban-panel", "market_preview")
SQL_DIR = os.path.join(ROOT, "linux-port", "docker", "mariadb", "playerbot")
GAME_DIR = os.path.join(ROOT, "linux-port", "docker", "game")
SNAPSHOT = os.path.join(HERE, "snapshot.json")
LIVE = "/var/lib/docker/volumes/mt2009plustest_game-var/_data"

# ---------------------------------------------------------------------------- the knobs
P0 = {"mat": 300000, "herb": 20000}
S0 = 0.2
K = 0.4
CLAMP = {"mat": (60000, 3000000), "herb": (5000, 60000)}
BULK_FROM = 10          # a recipe asking this many or more of it at once
BULK_FACTOR = 0.4
RISK = 0.5              # chance ^ RISK divides a recipe / a refine step
LADDER_CAP = 600000000  # +9 of a Yohara piece at most (the sheet's top armour +9 is 441 600 000)
GAYA_YANG = 25000       # PLAYERBOT_CHI_GAYA_YANG (playerbot_yohara_chi.h): what a bot pays a Gaya at Mistrz Chi
TOPAZ = 20000           # Topaz Woli: no shop or trade (anti-flags), a drop of 103 monsters - the talisman steps' 6..54
RANK_WEIGHT = {0: 1.0, 1: 1.0, 2: 0.5, 3: 0.3, 4: 0.05, 5: 0.1, 6: 0.05}
CHEST_WEIGHT = 0.05
NO_TRADE = (1 << 13) | (1 << 16)   # ITEM_ANTIFLAG_GIVE | ITEM_ANTIFLAG_MYSHOP

# ---------------------------------------------------------------------------- the rows
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


def refresh(drops_path, chests_path):
    files = [os.path.join(SQL_DIR, "item_proto.mt2009plus.sql")] + sorted(
        os.path.join(SQL_DIR, f) for f in os.listdir(SQL_DIR) if f.endswith(".sql") and f != "item_proto.mt2009plus.sql")
    items, mobs, refine, crafting = {}, {}, {}, {}
    rg_map = {}
    for path in files:
        raw = open(path, "rb").read()
        try:
            text = raw.decode("utf-8")
        except UnicodeDecodeError:      # zbroje105.sql and a few more are cp1250
            text = raw.decode("cp1250", "replace")
        if "item_proto" in text:
            for r in sql_inserts(text, "item_proto"):
                if isinstance(r.get("vnum"), int) and r["vnum"] not in items:   # INSERT IGNORE: the first one stays
                    items[r["vnum"]] = {"name": fold(str(r.get("locale_name", ""))), "type": r["type"],
                                        "sub": r["subtype"], "af": r["antiflag"], "gold": r["gold"],
                                        "sell": r["shop_buy_price"], "set": r["refine_set"],
                                        "next": r["refined_vnum"],
                                        "level": r["limitvalue0"] if r.get("limittype0") == 1 else 0}
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
    small = {k: {str(v): d[str(v)] for v in sorted(wanted) if str(v) in d} for k, d in snap.items()}
    json.dump(small, open(SNAPSHOT, "w"), indent=0, sort_keys=True, ensure_ascii=True)
    print("snapshot: %d items, %d steps, from %s and %s" % (len(small["items"]), len(small["steps"]), drops_path,
                                                         chests_path), file=sys.stderr)


# ---------------------------------------------------------------------------- the sheet as it stands
def sheet_prices(text):
    """vnum -> price of the rows outside our blocks (materials) and gear families."""
    text = re.sub(r"// ---- BEGIN " + MARKER + r".*?// ---- END " + MARKER + r"[^\n]*\n", "", text, flags=re.S)
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


def build(snap, sheet_mats, sheet_gear):
    pr = Pricer(snap, sheet_mats)
    blocks_mat, blocks_gear, skipped = [], [], []
    for title, rows in MATERIALS:
        out = []
        for v, rule in rows:
            it = pr.item(v)
            if not it:
                skipped.append((v, "not in item_proto"))
                continue
            if v in sheet_mats:
                skipped.append((v, "the sheet already prices it (%d)" % sheet_mats[v]))
                continue
            if it.get("af", 0) & NO_TRADE or 21900 <= v <= 21975:
                skipped.append((v, "no shop / no trade (anti-flags %d)" % it.get("af", 0)))
                continue
            p = pr.get(v)
            out.append((v, p, pr.name(v), pr.why[v]))
        blocks_mat.append((title, out))
    gear = []
    for base, rule, label in gear_rows():
        if base in sheet_gear:
            skipped.append((base, "the sheet already prices the family"))
            continue
        if not pr.item(base):
            skipped.append((base, "not in item_proto"))
            continue
        vals, why = pr.ladder(base, rule)
        gear.append((base, vals, pr.name(base).split("+")[0], "%s; +0 %s; steps: the world's refine_proto, "
                     "/ chance^%g" % (label, why, RISK)))
    blocks_gear.append(("Sung Ma gloves, Talizmany Woli, jade jewellery", gear))
    return blocks_mat, blocks_gear, skipped


# ---------------------------------------------------------------------------- writing
HEAD = ("\t\t// ---- BEGIN %s - TEMPORARY Yohara prices (the owner, 27 October 2026: \"mniej wiecej, logicznie,\n"
        "\t\t// tymczasowy\"). GENERATED by tools/yohara_prices/gen_yohara_prices.py - edit the script, not these rows;\n"
        "\t\t// delete the block (or run it with --remove) to go back. Each row: how its number was made.\n")
TAIL = "\t\t// ---- END %s\n"


def render_mat(blocks):
    lines = [HEAD % MARKER]
    for title, rows in blocks:
        if not rows:
            continue
        lines.append("\t\t// %s\n" % title)
        for v, p, name, why in rows:
            lines.append("\t\t{ %5d, %9d },\t// %s (TEMP: %s)\n" % (v, p, name, why))
    lines.append(TAIL % MARKER)
    return "".join(lines)


def render_gear(blocks):
    lines = [HEAD % MARKER]
    for title, rows in blocks:
        lines.append("\t\t// %s\n" % title)
        for base, vals, name, why in rows:
            lines.append("\t\t{ %5d, 0x000, { %s } },\t// %s (TEMP: %s)\n" % (base, ", ".join(str(x) for x in vals),
                                                                           name, why))
    lines.append(TAIL % MARKER)
    return "".join(lines)


def put_block(text, table, block):
    """The table's block replaced by `block` (taken out when it is empty)."""
    m = re.search(r"\b" + table + r"\[\]\s*=\s*\{(.*?)(\n\t\};)", text, re.S)
    if not m:
        sys.exit("gen_yohara_prices: table %s not found" % table)
    body = m.group(1)
    body = re.sub(r"\n\t\t// ---- BEGIN " + MARKER + r".*?\t\t// ---- END " + MARKER, "", body, flags=re.S)
    if block:
        body = body + "\n" + block.rstrip("\n")
    return text[:m.start(1)] + body + text[m.end(1):]


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
    sheet = re.sub(r"GEAR = \{\n.*?\n\}\n", lambda _: "".join(gear), sheet, count=1, flags=re.S)
    sheet = re.sub(r"MATERIALS = \{\n.*?\n\}\n# The first table \(upgrade materials\)\.\nREFINE_MATERIALS = "
                   r"frozenset\(\(\n.*?\n\)\)\n", lambda _: "".join(mats), sheet, count=1, flags=re.S)
    open(path, "w", encoding="utf-8").write(sheet)


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--refresh", action="store_true")
    ap.add_argument("--drops", default=os.path.join(LIVE, "drops", "image.live"))
    ap.add_argument("--chests", default=os.path.join(LIVE, "chests", "live.new"))
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--remove", action="store_true")
    a = ap.parse_args()
    text = open(TABLES, encoding="latin-1").read()
    if a.remove:
        text = put_block(put_block(text, "PLAYERBOT_GEAR_PRICES", ""), "PLAYERBOT_EXTRA_MATERIAL_PRICES", "")
        open(TABLES, "w", encoding="latin-1").write(text)
        write_sheet()
        return
    if a.refresh:
        refresh(a.drops, a.chests)
    snap = json.load(open(SNAPSHOT))
    sheet_mats, sheet_gear = sheet_prices(text)
    mat_blocks, gear_blocks, skipped = build(snap, sheet_mats, sheet_gear)
    mat_text, gear_text = render_mat(mat_blocks), render_gear(gear_blocks)
    n_mat = sum(len(r) for _, r in mat_blocks)
    n_gear = sum(len(r) for _, r in gear_blocks)
    if a.dry_run:
        sys.stdout.write(gear_text + mat_text)
    else:
        text = put_block(text, "PLAYERBOT_GEAR_PRICES", gear_text)
        text = put_block(text, "PLAYERBOT_EXTRA_MATERIAL_PRICES", mat_text)
        open(TABLES, "w", encoding="latin-1").write(text)
        write_sheet()
    print("%d material rows, %d gear families (%d pieces); left out: %s" % (
        n_mat, n_gear, n_gear * 10, "; ".join("%d %s" % s for s in skipped) or "none"), file=sys.stderr)


if __name__ == "__main__":
    main()
