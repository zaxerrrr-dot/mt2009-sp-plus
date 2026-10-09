# =============================================================================
#  Podgląd rynku (MT2009_PLUS_MARKET_PREVIEW_V1) -- the pure rules.
#
#  No Flask, no database: what a request's parameters mean, the categories,
#  the SQL a filter becomes (fixed text, every value a parameter), the sort
#  orders, a price as a player writes it, a name as the search reads it, the
#  reference price and the bargain. test_market_preview.py tests it.
# =============================================================================

import math
import re
import time
import unicodedata

try:
    from . import sheet
except ImportError:                                  # loaded as a plain module by a test
    import sheet                                     # noqa: F401

# -----------------------------------------------------------------------------
#  Categories. The numbers are the snapshot's `cat`/`sub` columns; a
#  category's sub 0 is "nothing finer".
# -----------------------------------------------------------------------------
CATEGORIES = (
    # key, id, name, ((sub key, sub id, name), ...)
    ("weapons", 1, "Bronie", (
        ("swords", 1, "Miecze"), ("twohanded", 2, "Broń dwuręczna"), ("daggers", 3, "Sztylety"),
        ("bows", 4, "Łuki"), ("bells", 5, "Dzwony"), ("fans", 6, "Wachlarze"))),
    ("armour", 2, "Zbroje", ()),
    ("shields_helmets", 3, "Tarcze i hełmy", (("shields", 1, "Tarcze"), ("helmets", 2, "Hełmy"))),
    ("jewellery", 4, "Biżuteria", (("bracelets", 1, "Bransolety"), ("necklaces", 2, "Naszyjniki"),
                                   ("earrings", 3, "Kolczyki"))),
    ("boots", 5, "Buty", ()),
    ("books", 6, "Księgi umiejętności", (
        ("warrior", 1, "Wojownik"), ("ninja", 2, "Ninja"), ("sura", 3, "Sura"), ("shaman", 4, "Szaman"),
        ("forget", 5, "Księgi Zapomnienia"), ("passive", 6, "Księgi pasywne"))),
    ("soul_stones", 7, "Kamienie duszy", (
        ("g0", 1, "+0"), ("g1", 2, "+1"), ("g2", 3, "+2"), ("g3", 4, "+3"), ("g4", 5, "+4"),
        ("g5", 6, "+5 i wyżej"))),
    ("chests", 8, "Skrzynie", ()),
    ("usable", 9, "Mikstury i użytkowe", ()),
    ("materials", 10, "Materiały", (
        ("refine", 1, "Ulepszacze"), ("ores", 2, "Rudy i przetopy"), ("herbs", 3, "Zioła"), ("fish", 4, "Ryby"))),
    ("other", 11, "Inne", ()),
)
CATEGORY_BY_KEY = {c[0]: c for c in CATEGORIES}
SUB_BY_KEY = {(c[0], s[0]): s[1] for c in CATEGORIES for s in c[3]}
CAT_BOOKS = 6

# item_length.h (mt2009)
ITEM_WEAPON, ITEM_ARMOR, ITEM_USE, ITEM_AUTOUSE, ITEM_MATERIAL, ITEM_SPECIAL = 1, 2, 3, 4, 5, 6
ITEM_METIN, ITEM_FISH, ITEM_ROD, ITEM_RESOURCE, ITEM_SKILLBOOK = 10, 12, 13, 14, 17
ITEM_QUEST, ITEM_POLYMORPH, ITEM_TREASURE_BOX, ITEM_TREASURE_KEY = 18, 19, 20, 21
ITEM_SKILLFORGET, ITEM_GIFTBOX, ITEM_POTION = 22, 23, 36
WEAPON_SUBS = {0: 1, 3: 2, 1: 3, 2: 4, 4: 5, 5: 6}          # sword, two-handed, dagger, bow, bell, fan
ARMOR_SUBS = {0: (2, 0), 1: (3, 2), 2: (3, 1), 3: (4, 1), 4: (5, 0), 5: (4, 2), 6: (4, 3)}
# The bots' price slot of an armour subtype, and a weapon's (PRICE_SLOT_*).
ARMOR_PRICE_SLOT = {0: 2, 1: 1, 2: 4, 3: 16, 4: 8, 5: 32, 6: 64}
WEAPON_PRICE_SLOT = 128
SKILL_BOOK_GENERAL = 50300
SKILL_BOOK_INSTR = (50401, 50599)
PASSIVE_BOOKS = frozenset(list(range(50301, 50307)) + list(range(50311, 50317)) + [50060, 50061, 50600])
HERBS = frozenset(list(range(50721, 50741)) + [50056])
ORES = (50601, 50640)
SOUL_STONES = (28000, 28999)

_CLASS_SKILLS = (
    (0, set(range(1, 6)) | set(range(16, 21))),          # warrior
    (1, set(range(31, 36)) | set(range(46, 52))),        # ninja
    (2, set(range(61, 67)) | set(range(76, 82))),        # sura
    (3, set(range(91, 97)) | set(range(106, 112))),      # shaman
)
CLASS_BITS = (1, 2, 4, 8)
CLASS_ANTIFLAGS = (1 << 2, 1 << 3, 1 << 4, 1 << 5)      # ITEM_ANTIFLAG_WARRIOR .. SHAMAN
ALL_CLASSES = 15
CLASS_KEYS = ("warrior", "ninja", "sura", "shaman")
CLASS_NAMES = ("Wojownik", "Ninja", "Sura", "Szaman")


def skill_class(skill):
    for job, skills in _CLASS_SKILLS:
        if int(skill or 0) in skills:
            return job
    return -1


def book_skill(vnum, socket0):
    vnum = int(vnum or 0)
    if vnum == SKILL_BOOK_GENERAL:
        return int(socket0 or 0)
    if SKILL_BOOK_INSTR[0] <= vnum <= SKILL_BOOK_INSTR[1]:
        return vnum - 50400
    return 0


def soul_stone_grade(vnum):
    return (int(vnum) // 100) % 10


def classify(itype, subtype, vnum, socket0=0):
    """(cat, sub) of an item, from its proto."""
    itype, subtype, vnum = int(itype or 0), int(subtype or 0), int(vnum or 0)
    if itype == ITEM_WEAPON:
        sub = WEAPON_SUBS.get(subtype)
        return (1, sub) if sub else (11, 0)
    if itype == ITEM_ARMOR:
        return ARMOR_SUBS.get(subtype, (11, 0))
    if itype == ITEM_SKILLBOOK:
        job = skill_class(book_skill(vnum, socket0))
        return (6, job + 1) if job >= 0 else (6, 6)
    if itype == ITEM_SKILLFORGET:
        return (6, 5)
    if vnum in PASSIVE_BOOKS:
        return (6, 6)
    if itype == ITEM_METIN:
        if SOUL_STONES[0] <= vnum <= SOUL_STONES[1]:
            return (7, min(soul_stone_grade(vnum), 5) + 1)
        return (7, 0)
    if itype in (ITEM_TREASURE_BOX, ITEM_GIFTBOX):
        return (8, 0)
    if vnum in HERBS:
        return (10, 3)
    if ORES[0] <= vnum <= ORES[1]:
        return (10, 2)
    if itype == ITEM_FISH:
        return (10, 4)
    if vnum in sheet.REFINE_MATERIALS or itype in (ITEM_MATERIAL, ITEM_RESOURCE):
        return (10, 1)
    if itype in (ITEM_USE, ITEM_AUTOUSE, ITEM_POTION, ITEM_POLYMORPH):
        return (9, 0)
    return (11, 0)


def class_mask(itype, antiflag, vnum=0, socket0=0):
    """The classes that may use the item, as CLASS_BITS."""
    if int(itype or 0) == ITEM_SKILLBOOK:
        job = skill_class(book_skill(vnum, socket0))
        return CLASS_BITS[job] if job >= 0 else ALL_CLASSES
    if int(itype or 0) not in (ITEM_WEAPON, ITEM_ARMOR):
        return ALL_CLASSES
    mask = 0
    for bit, anti in zip(CLASS_BITS, CLASS_ANTIFLAGS):
        if not int(antiflag or 0) & anti:
            mask |= bit
    return mask


# -----------------------------------------------------------------------------
#  Names as the search reads them: "luk z rogu" finds "Łuk Z Rogu Jelenia".
# -----------------------------------------------------------------------------
_PL_FOLD = str.maketrans("ąćęłńóśźżĄĆĘŁŃÓŚŹŻ", "acelnoszzACELNOSZZ")
_PLUS_TAIL = re.compile(r"\s*\+\s*(\d{1,2})\s*$")


def normalize(text):
    text = str(text or "").translate(_PL_FOLD)
    text = unicodedata.normalize("NFKD", text)
    text = "".join(ch for ch in text if not unicodedata.combining(ch))
    return " ".join(text.lower().split())


def split_plus(name):
    """("Miecz", 7) of "Miecz+7"; (name, -1) without one."""
    name = str(name or "").strip()
    m = _PLUS_TAIL.search(name)
    if not m:
        return name, -1
    return name[:m.start()].rstrip(), int(m.group(1))


def like_pattern(query):
    q = normalize(query)
    return "%" + q.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_") + "%"


# -----------------------------------------------------------------------------
#  A price as a player writes it: 500k, 1.5kk, 2kkk, 1 500 000.
# -----------------------------------------------------------------------------
PRICE_MAX = 10 ** 13
_PRICE_K = re.compile(r"^(\d+(?:[.,]\d+)?)\s*(k{1,4})$")
_PRICE_GROUPS = re.compile(r"^\d{1,3}(?:[ .,_]\d{3})+$")


def parse_price(text):
    """The yang a text means, None for an empty field; ValueError otherwise."""
    s = str(text if text is not None else "").strip().lower().replace(" ", " ")
    if not s:
        return None
    s = re.sub(r"\s*yang$", "", s)
    m = _PRICE_K.match(s.replace(" ", ""))
    if m:
        number = m.group(1).replace(",", ".")
        whole, _, frac = number.partition(".")
        scale = 1000 ** len(m.group(2))
        value = int(whole) * scale
        if frac:
            value += int(frac) * scale // (10 ** len(frac))
    elif s.isdigit():
        value = int(s)
    elif _PRICE_GROUPS.match(s):
        value = int(re.sub(r"[ .,_]", "", s))
    else:
        raise ValueError(text)
    if value < 0 or value > PRICE_MAX:
        raise ValueError(text)
    return value


def format_price(value):
    return "{:,}".format(int(value or 0)).replace(",", " ")


# -----------------------------------------------------------------------------
#  Filters: every parameter is read against a whitelist and becomes fixed SQL
#  text with its value as a parameter. Nothing of a request is pasted.
# -----------------------------------------------------------------------------
SORTS = {
    "deals": "bkey DESC, id DESC",
    "price_asc": "price ASC, id DESC",
    "price_desc": "price DESC, id DESC",
    "unit_asc": "unit ASC, id DESC",
    "plus_desc": "plus DESC, price ASC, id DESC",
    "level_desc": "lvl DESC, price ASC, id DESC",
    "level_asc": "lvl ASC, price ASC, id DESC",
    "bonus_count": "nb DESC, nmax DESC, price ASC, id DESC",
    "tier_sum": "tiers DESC, nb DESC, price ASC, id DESC",
    "newest": "id DESC",
}
SORT_NAMES = {
    "deals": "Najlepsze okazje", "price_asc": "Cena: od najniższej", "price_desc": "Cena: od najwyższej",
    "unit_asc": "Cena za sztukę: od najniższej", "plus_desc": "Ulepszenie: od najwyższego",
    "level_desc": "Poziom przedmiotu: od najwyższego", "level_asc": "Poziom przedmiotu: od najniższego",
    "bonus_count": "Najwięcej bonusów", "tier_sum": "Najwyższa suma ocen bonusów", "newest": "Najnowsze wystawienia",
}
UNIT_SORTS = {"price_asc": "unit ASC, id DESC", "price_desc": "unit DESC, id DESC"}
DEFAULT_SORT = "deals"
PER_PAGE = (25, 50, 100)
DEFAULT_PER = 50
MAX_PAGE = 100000
DEFAULT_DEAL_PCT = 40
# An offer is a bargain from 25% under its usual price; from 80% it also gets
# a warning (a price slip, or a weak piece).
DEAL_BADGE_PCT = 25
DEAL_SUSPECT_PCT = 80
NO_REFERENCE_KEY = -1000000          # sorts last under "Najlepsze okazje"
MAX_BONUS_FILTERS = 3
TEXT_MAX = 60
LEVEL_MAX = 255
PLUS_MAX = 19
DAMAGE_MAX = 200

DEFAULTS = {
    "q": "", "cat": "", "sub": "", "pmin": "", "pmax": "", "unit": "0", "lmin": "", "lmax": "",
    "rmin": "", "rmax": "", "cls": "", "nbmin": "", "maxonly": "0", "nmaxmin": "",
    "avgmin": "", "avgmax": "", "sklmin": "", "sklmax": "", "ks": "", "emp": "", "seller": "", "sname": "",
    "shop": "", "vnum": "", "deals": "0", "dmin": str(DEFAULT_DEAL_PCT), "hideslip": "1", "expired": "0",
    "var": "", "rare": "0", "sort": DEFAULT_SORT, "page": "1", "per": str(DEFAULT_PER),
    "b1": "", "b1v": "", "b2": "", "b2v": "", "b3": "", "b3v": "",
}


def _int(value, low, high):
    s = str(value or "").strip()
    if not s:
        return None
    if not re.match(r"^-?\d{1,12}$", s):
        raise ValueError(value)
    n = int(s)
    if n < low or n > high:
        raise ValueError(value)
    return n


def _flag(value):
    return str(value or "").strip() in ("1", "on", "true", "yes")


def parse_filters(args, bonus_points=()):
    """(filters, errors) of a request's arguments; `errors` names each field
    whose value means nothing (left out of the filter, marked on the page)."""
    get = (lambda k: args.get(k)) if hasattr(args, "get") else (lambda k: None)
    f, errors = {}, {}

    def field(name, fn):
        raw = get(name)
        try:
            return fn(raw)
        except (TypeError, ValueError):
            errors[name] = "invalid"
            return None

    q = str(get("q") or "").strip()[:TEXT_MAX]
    if normalize(q):
        f["q"] = normalize(q)
    cat = str(get("cat") or "").strip()
    if cat in CATEGORY_BY_KEY:
        f["cat"] = CATEGORY_BY_KEY[cat][1]
        sub = str(get("sub") or "").strip()
        if (cat, sub) in SUB_BY_KEY:
            f["sub"] = SUB_BY_KEY[(cat, sub)]
    elif cat:
        errors["cat"] = "invalid"
    f["unit"] = _flag(get("unit"))
    for name in ("pmin", "pmax"):
        value = field(name, parse_price)
        if value is not None:
            f[name] = value
    for name, high in (("lmin", LEVEL_MAX), ("lmax", LEVEL_MAX), ("rmin", PLUS_MAX), ("rmax", PLUS_MAX),
                       ("nbmin", 7), ("nmaxmin", 4), ("avgmin", DAMAGE_MAX), ("avgmax", DAMAGE_MAX),
                       ("sklmin", DAMAGE_MAX), ("sklmax", DAMAGE_MAX), ("dmin", 100)):
        value = field(name, lambda v, h=high: _int(v, 0, h))
        if value is not None:
            f[name] = value
    for low, high in (("pmin", "pmax"), ("lmin", "lmax"), ("rmin", "rmax"), ("avgmin", "avgmax"),
                      ("sklmin", "sklmax")):
        if low in f and high in f and f[low] > f[high]:
            errors[high] = "range"
            del f[high]
    cls = str(get("cls") or "").strip()
    if cls in CLASS_KEYS:
        f["cls"] = CLASS_BITS[CLASS_KEYS.index(cls)]
    elif cls:
        errors["cls"] = "invalid"
    if _flag(get("maxonly")):
        f["nmaxmin"] = max(1, f.get("nmaxmin") or 1)
    bonuses = []
    allowed = set(int(p) for p in bonus_points)
    for i in range(1, MAX_BONUS_FILTERS + 1):
        point = field("b%d" % i, lambda v: _int(v, 1, 0xFFFF))
        if point is None:
            continue
        if point not in allowed:
            errors["b%d" % i] = "invalid"
            continue
        floor = field("b%dv" % i, lambda v: _int(v, -100000, 100000))
        bonuses.append((point, floor if floor is not None else 1))
    if bonuses:
        f["bonuses"] = bonuses
    ks = str(get("ks") or "").strip()
    if ks == "has":
        f["ks"] = "has"
    elif ks:
        stone = field("ks", lambda v: _int(v, SOUL_STONES[0], SOUL_STONES[1]))
        if stone is not None:
            f["ks"] = stone
    emp = field("emp", lambda v: _int(v, 1, 3))
    if emp is not None:
        f["emp"] = emp
    seller = str(get("seller") or "").strip()
    if seller in ("bot", "person"):
        f["seller"] = seller
    elif seller:
        errors["seller"] = "invalid"
    sname = normalize(str(get("sname") or "")[:TEXT_MAX])
    if sname:
        f["sname"] = sname
    for name in ("shop", "vnum"):
        value = field(name, lambda v: _int(v, 1, 0xFFFFFFFF))
        if value is not None:
            f[name] = value
    if "vnum" in f:
        variant = field("var", lambda v: _int(v, 0, 0xFFFFFFFF))
        if variant is not None:
            f["var"] = variant
    if _flag(get("deals")):
        f["deals"] = f.get("dmin", DEFAULT_DEAL_PCT)
    if _flag(get("rare")):
        f["rare"] = True
    f["hideslip"] = str(get("hideslip") if get("hideslip") is not None else "1").strip() != "0"
    f["expired"] = _flag(get("expired"))
    sort = str(get("sort") or DEFAULT_SORT).strip()
    if sort not in SORTS:
        errors["sort"] = "invalid"
        sort = DEFAULT_SORT
    f["sort"] = sort
    per = field("per", lambda v: _int(v, 1, 1000))
    f["per"] = per if per in PER_PAGE else DEFAULT_PER
    page = field("page", lambda v: _int(v, 1, MAX_PAGE))
    f["page"] = page or 1
    return f, errors


def build_where(f, ignore_category=False):
    """(SQL after WHERE, params) of a filter: fixed text, values as '?'."""
    sql, params = [], []
    if not f.get("expired"):
        sql.append("running = 1")
    if f.get("hideslip", True):
        sql.append("slip = 0")
    if not ignore_category and "cat" in f:
        sql.append("cat = ?")
        params.append(f["cat"])
        if "sub" in f:
            sql.append("sub = ?")
            params.append(f["sub"])
    if "q" in f:
        sql.append("(vnum, var) IN (SELECT vnum, var FROM kinds WHERE norm LIKE ? ESCAPE '\\')")
        params.append(like_pattern(f["q"]))
    if "vnum" in f:
        sql.append("vnum = ?")
        params.append(f["vnum"])
        if "var" in f:
            sql.append("var = ?")
            params.append(f["var"])
    if "shop" in f:
        sql.append("owner = ?")
        params.append(f["shop"])
    column = "unit" if f.get("unit") else "price"
    if "pmin" in f:
        sql.append(column + " >= ?")
        params.append(f["pmin"])
    if "pmax" in f:
        sql.append(column + " <= ?")
        params.append(f["pmax"])
    if "rmax" in f and "rmin" not in f:
        sql.append("plus >= 0")
    for key, col, op in (("lmin", "lvl", ">="), ("lmax", "lvl", "<="), ("rmin", "plus", ">="),
                         ("rmax", "plus", "<="), ("nbmin", "nb", ">="), ("nmaxmin", "nmax", ">="),
                         ("avgmin", "avg", ">="), ("avgmax", "avg", "<="), ("sklmin", "skl", ">="),
                         ("sklmax", "skl", "<="), ("emp", "emp", "=")):
        if key in f:
            sql.append("%s %s ?" % (col, op))
            params.append(f[key])
    if "cls" in f:
        sql.append("(cls & ?) <> 0")
        params.append(f["cls"])
    for point, floor in f.get("bonuses", ()):
        sql.append("(" + " OR ".join("(a%d = ? AND v%d >= ?)" % (i, i) for i in range(7)) + ")")
        for _ in range(7):
            params.extend((point, floor))
    if f.get("ks") == "has":
        sql.append("ks > 0")
    elif "ks" in f:
        sql.append("(s0 = ? OR s1 = ? OR s2 = ?)")
        params.extend((f["ks"],) * 3)
    if f.get("seller") == "bot":
        sql.append("bot = 1")
    elif f.get("seller") == "person":
        sql.append("bot = 0")
    if "sname" in f:
        sql.append("owner IN (SELECT owner FROM shops WHERE norm LIKE ? ESCAPE '\\')")
        params.append(like_pattern(f["sname"]))
    if "deals" in f:
        sql.append("bkey >= ?")
        params.append(max(DEAL_BADGE_PCT, int(f["deals"])))
    if f.get("rare"):
        sql.append("rare = 1")
    return (" AND ".join(sql) if sql else "1 = 1"), params


def order_by(f):
    if f.get("unit") and f.get("sort") in UNIT_SORTS:
        return UNIT_SORTS[f["sort"]]
    return SORTS.get(f.get("sort"), SORTS[DEFAULT_SORT])


def count_key(f):
    """What the category counts depend on: every filter but the category,
    the sort and the page - so a click on a category reuses them."""
    skip = ("cat", "sub", "sort", "page", "per")
    return repr(sorted((k, v) for k, v in f.items() if k not in skip))


# -----------------------------------------------------------------------------
#  The reference price and the bargain.
# -----------------------------------------------------------------------------
def yang_rate_price_pct(rate):
    """The bots' price multiplier (percent) at a yang drop rate (percent):
    straight between the table's points, proportional outside them
    (playerbot_price_tables.h PLAYERBOT_PRICE_RATE_POINTS)."""
    rate = int(rate or 0)
    points = sheet.RATE_POINTS
    if rate <= 0:
        return 0
    first, last = points[0], points[-1]
    if rate <= first[0]:
        return first[1] * rate // first[0]
    if rate >= last[0]:
        return last[1] * rate // last[0]
    for i in range(1, len(points)):
        hi = points[i]
        if rate > hi[0]:
            continue
        lo = points[i - 1]
        return lo[1] + (hi[1] - lo[1]) * (rate - lo[0]) // (hi[0] - lo[0])
    return last[1]


def sheet_price(itype, vnum, socket0=0):
    """The bots' list price of one unit at x1.0, 0 where they have none."""
    itype, vnum = int(itype or 0), int(vnum or 0)
    if itype in (ITEM_WEAPON, ITEM_ARMOR):
        row = sheet.GEAR.get(vnum - vnum % 10)
        refine = vnum % 10
        if not row or (row[0] >> refine) & 1:
            return 0
        return row[1][refine]
    if itype == ITEM_SKILLBOOK:
        return sheet.BOOKS.get(book_skill(vnum, socket0), 0)
    if itype == ITEM_SKILLFORGET:
        return sheet.FORGET_SCROLLS.get(int(socket0 or 0), 0)
    if itype == ITEM_METIN and SOUL_STONES[0] <= vnum <= SOUL_STONES[1]:
        grade = soul_stone_grade(vnum)
        named = sheet.SOUL_STONES.get((vnum % 100, grade))
        if named:
            return named
        return sheet.SOUL_STONE_GRADES[grade] if 0 <= grade < len(sheet.SOUL_STONE_GRADES) else 0
    if itype == ITEM_POLYMORPH:
        return sheet.MARBLES.get(int(socket0 or 0), (sheet.MARBLE_BAND[0] + sheet.MARBLE_BAND[1]) // 2)
    return sheet.MATERIALS.get(vnum, 0)


def price_slot(itype, subtype):
    itype = int(itype or 0)
    if itype == ITEM_WEAPON:
        return WEAPON_PRICE_SLOT
    if itype == ITEM_ARMOR:
        return ARMOR_PRICE_SLOT.get(int(subtype or 0), 0)
    return 0


def _tier_pct(tiers, value):
    pct = 100
    for start, p in tiers:
        if value >= start:
            pct = p
    return pct


POINT_SKILL_DAMAGE = 121          # POINT_SKILL_DAMAGE_BONUS (UM)
POINT_AVERAGE_DAMAGE = 122        # POINT_NORMAL_HIT_DAMAGE_BONUS (ŚR)

# playerbot_price_rules.h: two lines at their top x1.7, three x2.5, four and
# more x4.0 over the lines' product, which stops at a hundredfold first.
MAX_LINES_PERCENT = (100, 100, 170, 250, 400)
BONUS_PRODUCT_CAP = 100.0
AVERAGE_DAMAGE_MAX_FROM = 40


def line_at_top(value, top):
    value = int(value or 0)
    return value > 0 and bool(top) and value >= int(top)


def max_lines_percent(count):
    return MAX_LINES_PERCENT[max(0, min(int(count), len(MAX_LINES_PERCENT) - 1))]


def bonus_multiplier(slot, level, lines, tops):
    """The bots' bonus multiplier of a piece (GetPlayerBotBonusPricePercent):
    each line by the row its slot and level band names, a weapon's average and
    skill damage by their tiers, and the extra for two to four lines at their
    top. 1.0 for anything the table does not price."""
    if not slot:
        return 1.0
    pct = 1.0
    at_top = 0
    for point, value in lines:
        if not point or not value:
            continue
        if slot == WEAPON_PRICE_SLOT and point == POINT_AVERAGE_DAMAGE:
            pct *= _tier_pct(sheet.AVERAGE_TIERS, value) / 100.0
            at_top += 1 if value >= AVERAGE_DAMAGE_MAX_FROM else 0
            continue
        if slot == WEAPON_PRICE_SLOT and point == POINT_SKILL_DAMAGE:
            if value >= sheet.SKILL_TIERS[0][0]:
                pct *= _tier_pct(sheet.SKILL_TIERS, value) / 100.0
            at_top += 1 if value >= sheet.SKILL_TIERS[-1][0] else 0
            continue
        own = 0
        for slots, row_point, max_pct, other_pct, lv_from, lv_to, own_top in sheet.BONUS_ROWS:
            if row_point != point or not slots & slot or not lv_from <= int(level or 0) <= lv_to:
                continue
            own = own_top
            pct *= (max_pct if line_at_top(value, own_top or tops.get(point, 0)) else other_pct) / 100.0
            break
        at_top += 1 if line_at_top(value, own or tops.get(point, 0)) else 0
    return min(pct, BONUS_PRODUCT_CAP) * max_lines_percent(at_top) / 100.0


def reference_multiplier(itype, subtype, level, lines, damage, tops):
    slot = price_slot(itype, subtype)
    return bonus_multiplier(slot, level, list(lines) + list(damage), tops) if slot else 1.0


def gear_plus(itype, vnum, plus):
    if int(plus) >= 0:
        return int(plus)
    if int(itype or 0) in (ITEM_WEAPON, ITEM_ARMOR):
        return int(vnum) % 10
    return -1


# An item is rare while all the running stalls of every kingdom hold fewer
# than RARE_BELOW pieces of it.
RARE_BELOW = 10


def is_rare(pieces):
    return int(pieces) < RARE_BELOW


def is_max_line(point, value, tops):
    return line_at_top(value, tops.get(int(point or 0), 0))


def line_tier(point):
    """The higher of a line's PvE and PvP rating (1..6); 0 for a line the
    bots do not rate."""
    row = sheet.BONUS_TIERS.get(int(point or 0))
    return max(row[0], row[1]) if row else 0


def tier_pair(point):
    row = sheet.BONUS_TIERS.get(int(point or 0))
    return (row[0], row[1]) if row else (0, 0)


def bargain_pct(unit, reference):
    """1 - price / reference in whole percent; None without a reference."""
    if not reference or reference <= 0 or unit is None:
        return None
    return int(math.floor((1.0 - float(unit) / float(reference)) * 100.0 + 0.5))


def bargain_key(pct):
    return NO_REFERENCE_KEY if pct is None else int(pct)


def median(values):
    values = sorted(values)
    n = len(values)
    if not n:
        return None
    mid = n // 2
    return float(values[mid]) if n % 2 else (values[mid - 1] + values[mid]) / 2.0


HISTORY_MIN_OFFERS = 5            # fewer than five listings in the week: the price list's price
HISTORY_DAYS = 7
# Where the price list prices a kind, the week counts only the listings within
# a quarter to four times the list's day price - a stray line priced by
# mistake is no "usual price".
HISTORY_BAND_LOW = 0.25
HISTORY_BAND_HIGH = 4.0

# Where an offer's reference came from (`rsrc`): nothing, the bots' price list
# (x the bonus multipliers), the week's median (x the bonus multipliers).
REF_NONE, REF_SHEET, REF_WEEK = 0, 1, 3


def history_base(values, sheet_day):
    """The week's base of a kind, or None for the price list's: `values` the
    bases seen in seven days, `sheet_day` the list's day price of a plain
    piece (0: the list does not price it)."""
    if values is None:
        return None
    sheet_day = float(sheet_day or 0)
    if sheet_day > 0:
        low, high = sheet_day * HISTORY_BAND_LOW, sheet_day * HISTORY_BAND_HIGH
        values = [v for v in values if low <= v <= high]
    if len(values) < HISTORY_MIN_OFFERS:
        return None
    return median(values)


# A single book or upgrade material asking five times its usual price or more
# is marked as a probable price slip and hidden by default.
SLIP_FACTOR = 5


def is_slip(count, is_book, is_refine, unit, fair_unit):
    if int(count or 0) != 1 or not (is_book or is_refine) or not fair_unit or fair_unit <= 0:
        return False
    return unit >= fair_unit * SLIP_FACTOR


# -----------------------------------------------------------------------------
#  Ten requests a second from one browser: a token bucket a key.
# -----------------------------------------------------------------------------
class RateLimiter(object):
    def __init__(self, rate=10.0, burst=10.0, clock=time.monotonic, max_keys=4096):
        self.rate, self.burst, self.clock, self.max_keys = float(rate), float(burst), clock, max_keys
        self.buckets = {}

    def allow(self, key):
        now = self.clock()
        tokens, stamp = self.buckets.get(key, (self.burst, now))
        tokens = min(self.burst, tokens + (now - stamp) * self.rate)
        if len(self.buckets) >= self.max_keys and key not in self.buckets:
            for old in sorted(self.buckets, key=lambda k: self.buckets[k][1])[: self.max_keys // 4]:
                del self.buckets[old]
        if tokens < 1.0:
            self.buckets[key] = (tokens, now)
            return False
        self.buckets[key] = (tokens - 1.0, now)
        return True
