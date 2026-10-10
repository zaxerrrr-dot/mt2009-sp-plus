#!/usr/bin/env python3
"""gen_sheet.py <engine common/length.h> -- renders sheet.py (MT2009_PLUS_MARKET_PREVIEW_V1)
from the bots' own price and tier tables in the overlay
(linux-port/overlays/playerbot/src/game/src/playerbot_price_tables.h and
playerbot_item_tiers.h), so the market preview's reference prices are the ones
the bots price their stalls from. length.h gives the POINT numbers the
APPLY_* names stand for on this engine (player.item.attrtype holds POINT
numbers here). Not imported by the panel; run it again after the tables change:

    python3 gen_sheet.py /path/to/server/common/length.h > sheet.py
"""
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
OVERLAY = os.path.normpath(os.path.join(HERE, "..", "..", "..", "overlays", "playerbot", "src", "game", "src"))


def strip_comments(text):
    return re.sub(r"//[^\n]*", "", text)


def table(text, name):
    m = re.search(r"\b" + re.escape(name) + r"\[\]\s*=\s*\{(.*?)\n\s*\};", text, re.S)
    if not m:
        sys.exit("gen_sheet: table %s not found" % name)
    body = "\n".join(line for line in m.group(1).splitlines() if not line.strip().startswith("#"))
    return strip_comments(body)


def rows(body):
    out = []
    depth, cur = 0, ""
    for ch in body:
        if ch == "{":
            depth += 1
            if depth == 1:
                cur = ""
                continue
        elif ch == "}":
            depth -= 1
            if depth == 0:
                out.append(cur)
                continue
        if depth >= 1:
            cur += ch
    return out


def ints(text):
    return [int(x, 0) for x in re.findall(r"0x[0-9a-fA-F]+|\d+", text)]


def point_numbers(length_h):
    text = open(length_h, encoding="latin-1").read()
    m = re.search(r"enum EPointTypes\s*\{(.*?)\};", text, re.S)
    if not m:
        sys.exit("gen_sheet: enum EPointTypes not found in " + length_h)
    out, value = {}, -1
    for line in strip_comments(m.group(1)).splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        for part in line.split(","):
            part = part.strip()
            if not part:
                continue
            name, _, explicit = part.partition("=")
            name, explicit = name.strip(), explicit.strip()
            if explicit:
                value = int(explicit) if explicit.isdigit() else out.get(explicit, value + 1)
            else:
                value += 1
            out[name] = value
    return out


def apply_points(points):
    compat = open(os.path.join(OVERLAY, "playerbot_engine_compat.h"), encoding="latin-1").read()
    out = {}
    for apply_name, point_name in re.findall(r"#define\s+(APPLY_\w+)\s+(POINT_\w+)", compat):
        if point_name in points:
            out[apply_name] = points[point_name]
    for name, expected in (("APPLY_ATTBONUS_ANIMAL", 44), ("APPLY_STR", 12), ("APPLY_ST_REGEN", 139),
                           ("APPLY_SKILL_DURATION", 147), ("APPLY_MAX_HP", 6)):
        if out.get(name) != expected:
            sys.exit("gen_sheet: %s is %s, expected %d - wrong length.h?" % (name, out.get(name), expected))
    return out


SLOTS = {"PRICE_SLOT_HEAD": 1, "PRICE_SLOT_BODY": 2, "PRICE_SLOT_SHIELD": 4, "PRICE_SLOT_FOOTS": 8,
         "PRICE_SLOT_WRIST": 16, "PRICE_SLOT_NECK": 32, "PRICE_SLOT_EAR": 64, "PRICE_SLOT_WEAPON": 128}


def main():
    if len(sys.argv) != 2:
        sys.exit(__doc__)
    applies = apply_points(point_numbers(sys.argv[1]))
    prices = open(os.path.join(OVERLAY, "playerbot_price_tables.h"), encoding="latin-1").read()
    tiers = open(os.path.join(OVERLAY, "playerbot_item_tiers.h"), encoding="latin-1").read()
    w = sys.stdout.write
    w("# Rendered by gen_sheet.py (MT2009_PLUS_MARKET_PREVIEW_V1) from the bots' own\n"
      "# playerbot_price_tables.h and playerbot_item_tiers.h. DO NOT EDIT; render again.\n"
      "# Bonus lines are keyed by the POINT number (player.item.attrtype on this engine).\n\n")
    w("RATE_POINTS = (%s)\n" % ", ".join("(%d, %d)" % tuple(ints(r)[:2]) for r in
                                         rows(table(prices, "PLAYERBOT_PRICE_RATE_POINTS"))))
    w("GEAR = {\n")
    for r in rows(table(prices, "PLAYERBOT_GEAR_PRICES")):
        n = ints(r)
        w("    %d: (0x%03x, (%s)),\n" % (n[0], n[1], ", ".join(str(x) for x in n[2:12])))
    w("}\n")
    consts = {k: int(v) for k, v in re.findall(r"const DWORD (PLAYERBOT_\w+)\s*=\s*(\d+)\s*;", prices)}

    def material(r):
        vnum, expr = [p.strip() for p in r.split(",")[:2]]
        for name, value in consts.items():
            expr = expr.replace(name, str(value))
        if not re.match(r"^[\d\s/*+-]+$", expr):
            sys.exit("gen_sheet: cannot read the material price " + r)
        return int(vnum), int(eval(expr.replace("/", "//")))
    first = [material(r) for r in rows(table(prices, "PLAYERBOT_MATERIAL_PRICES"))]
    extra = [material(r) for r in rows(table(prices, "PLAYERBOT_EXTRA_MATERIAL_PRICES"))]
    w("MATERIALS = {\n")
    for vnum, price in sorted(dict(first + extra).items()):
        w("    %d: %d,\n" % (vnum, price))
    w("}\n# The first table (upgrade materials).\nREFINE_MATERIALS = frozenset((\n")
    for vnum in sorted(set(v for v, _ in first)):
        w("    %d,\n" % vnum)
    w("))\n")
    for name, out in (("PLAYERBOT_BOOK_PRICES", "BOOKS"), ("PLAYERBOT_FORGET_SCROLL_PRICES", "FORGET_SCROLLS"),
                      ("PLAYERBOT_MARBLE_PRICES", "MARBLES")):
        w("%s = {\n" % out)
        for r in rows(table(prices, name)):
            n = ints(r)
            w("    %d: %d,\n" % (n[0], n[1]))
        w("}\n")
    lo = int(re.search(r"PLAYERBOT_MARBLE_PRICE_MIN\s*=\s*(\d+)", prices).group(1))
    hi = int(re.search(r"PLAYERBOT_MARBLE_PRICE_MAX\s*=\s*(\d+)", prices).group(1))
    w("MARBLE_BAND = (%d, %d)\nSOUL_STONES = {\n" % (lo, hi))
    for r in rows(table(prices, "PLAYERBOT_SOUL_STONE_PRICES")):
        n = ints(r)
        w("    (%d, %d): %d,\n" % (n[0], n[1], n[2]))
    grades = ints(re.search(r"PLAYERBOT_SOUL_STONE_GRADE_PRICES\[\d+\]\s*=\s*\{([^}]*)\}", prices).group(1))
    w("}\nSOUL_STONE_GRADES = (%s)\n" % ", ".join(str(g) for g in grades))
    w("# (slot mask, point, max-roll hundredths, other hundredths, level from, to, own top)\nBONUS_ROWS = (\n")
    for r in rows(table(prices, "PLAYERBOT_BONUS_PRICE_ROWS")):
        parts = [p.strip() for p in r.split(",")]
        mask = 0
        for s in parts[0].split("|"):
            mask |= SLOTS[s.strip()]
        point = applies.get(parts[1])
        if point is None:
            sys.exit("gen_sheet: unknown %s" % parts[1])
        w("    (%d, %d, %s),\n" % (mask, point, ", ".join(parts[2:7])))
    w(")\n")
    for name, out in (("PLAYERBOT_AVERAGE_DAMAGE_TIERS", "AVERAGE_TIERS"), ("PLAYERBOT_SKILL_DAMAGE_TIERS", "SKILL_TIERS")):
        pairs = [tuple(ints(r)[:2]) for r in rows(table(prices, name))]
        w("%s = (%s)\n" % (out, ", ".join("(%d, %d)" % p for p in pairs)))
    w("# point: (PvE, PvP, PvE +1 job mask, PvP +1 job mask, name)\nBONUS_TIERS = {\n")
    m = re.search(r"PLAYERBOT_BONUS_TIERS\[\]\s*=\s*\{(.*?)\n\s*\};", tiers, re.S)
    for line in m.group(1).splitlines():
        lm = re.match(r"\s*\{\s*(APPLY_\w+)\s*,\s*(\d+)\s*,\s*(\d+)\s*,\s*(\d+)\s*,\s*(\d+)\s*\}\s*,?\s*//\s*(.*)$", line)
        if not lm:
            continue
        point = applies.get(lm.group(1))
        if point is None:
            sys.exit("gen_sheet: unknown %s" % lm.group(1))
        w("    %d: (%s, %s, %s, %s, %r),\n" % ((point,) + lm.groups()[1:5] + (lm.group(6).strip(),)))
    w("}\n")


if __name__ == "__main__":
    main()
