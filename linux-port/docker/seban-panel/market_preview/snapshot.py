# =============================================================================
#  Podgląd rynku (MT2009_PLUS_MARKET_PREVIEW_V1) -- the snapshot of every offer.
#
#  The panel never scans the stalls per request. Every 60 s while somebody
#  looks at the page (every fifteen minutes otherwise, so the week of prices
#  goes on being written), the IkarusShop tables are read once - player.item's
#  IKASHOP_OFFLINESHOP lines in chunks along the primary key, read-only, a
#  pause between chunks - and turned into an SQLite database in memory with the
#  columns every filter and sort reads and an index on each. A request is one
#  or two statements on it; the next snapshot is built aside and swapped in
#  whole, so nobody reads half of one.
#
#  The week of prices is the panel's own: every listing the snapshot sees is
#  written once, by its item id, into a small SQLite file in the panel's spool
#  (market_history.sqlite) with its unit price over its own bonus multiplier -
#  two pieces of one vnum with different bonuses are one thing to the median -
#  and an hour's median of each kind for the chart.
# =============================================================================

import os
import sqlite3
import threading
import time

try:
    from . import rules, sheet
except ImportError:                                  # loaded as plain modules by a test
    import rules                                     # noqa: F401
    import sheet                                     # noqa: F401

ITEM_CHUNK = 20000
CHUNK_PAUSE = 0.05                    # between two chunks: the cores' queries first
STATEMENT_SECONDS = 20
ACTIVE_SECONDS = 60
IDLE_SECONDS = 15 * 60
VIEWED_KEEPS_ACTIVE = 5 * 60
REFRESH_MIN_SECONDS = 15
FIRST_BUILD_DELAY = 0
PROTO_SECONDS = 3600
HISTORY_KEEP_DAYS = 8
COUNT_CACHE_KEYS = 64
# The snapshot thread stops after this long without a viewer; the next visit
# starts it again (the history then has a gap, which the chart shows).
STOP_AFTER_IDLE_SECONDS = 6 * 3600

OFFER_COLUMNS = ("id", "owner", "vnum", "var", "cat", "sub", "plus", "lvl", "cls", "price", "cnt", "unit",
                 "nb", "nmax", "tiers", "avg", "skl",
                 "a0", "v0", "a1", "v1", "a2", "v2", "a3", "v3", "a4", "v4", "a5", "v5", "a6", "v6",
                 "ks", "s0", "s1", "s2", "emp", "ch", "map", "bot", "running", "ref", "bkey", "slip",
                 "rare", "rcnt", "rsrc")
SCHEMA = (
    "CREATE TABLE offers (id INTEGER PRIMARY KEY, owner INT, vnum INT, var INT, cat INT, sub INT, plus INT, "
    "lvl INT, cls INT, price INT, cnt INT, unit REAL, nb INT, nmax INT, tiers INT, avg INT, skl INT, "
    "a0 INT, v0 INT, a1 INT, v1 INT, a2 INT, v2 INT, a3 INT, v3 INT, a4 INT, v4 INT, a5 INT, v5 INT, "
    "a6 INT, v6 INT, ks INT, s0 INT, s1 INT, s2 INT, emp INT, ch INT, map INT, bot INT, running INT, "
    "ref REAL, bkey INT, slip INT, rare INT, rcnt INT, rsrc INT)",
    "CREATE TABLE kinds (vnum INT, var INT, norm TEXT, PRIMARY KEY (vnum, var)) WITHOUT ROWID",
    "CREATE TABLE shops (owner INTEGER PRIMARY KEY, norm TEXT)",
)
INDEXES = (
    "CREATE INDEX o_cat ON offers (cat, sub)",
    "CREATE INDEX o_vnum ON offers (vnum, var)",
    "CREATE INDEX o_plus ON offers (plus)",
    "CREATE INDEX o_lvl ON offers (lvl)",
    "CREATE INDEX o_price ON offers (price)",
    "CREATE INDEX o_unit ON offers (unit)",
    "CREATE INDEX o_bkey ON offers (bkey)",
    "CREATE INDEX o_emp ON offers (emp)",
    "CREATE INDEX o_ch ON offers (ch)",
    "CREATE INDEX o_owner ON offers (owner)",
)

DAMAGE_POINTS = (rules.POINT_SKILL_DAMAGE, rules.POINT_AVERAGE_DAMAGE)
# An item line's seven bonus lines as one flat tuple: type0, value0, type1, ...
ATTR_COLUMNS = tuple(name for k in range(7) for name in ("attrtype%d" % k, "attrvalue%d" % k))
NO_ATTRS = (0,) * 14


class Proto(object):
    """What the snapshot needs of one item_proto row."""
    __slots__ = ("vnum", "type", "subtype", "antiflag", "level", "values", "applies", "plus", "name")

    def __init__(self, vnum, itype, subtype, antiflag=0, level=0, values=(0,) * 6, applies=(), plus=-1, name=""):
        self.vnum, self.type, self.subtype, self.antiflag = int(vnum), int(itype), int(subtype), int(antiflag)
        self.level, self.values, self.applies, self.plus = int(level), tuple(values), tuple(applies), int(plus)
        self.name = name


def variant_of(proto, socket0):
    """What tells two lines of one vnum apart as goods: a book's skill, a
    marble's monster; nothing for the rest (a piece's plus is its vnum)."""
    if proto is None:
        return 0
    if proto.type in (rules.ITEM_SKILLBOOK, rules.ITEM_SKILLFORGET, rules.ITEM_POLYMORPH):
        return int(socket0 or 0)
    return 0


class Snapshot(object):
    """One built snapshot: an in-memory SQLite database and the dictionaries
    that render its rows. Read-only once built; a lock serializes the
    connection's statements."""

    def __init__(self):
        self.conn = sqlite3.connect(":memory:", check_same_thread=False)
        self.lock = threading.Lock()
        self.generated_at = 0.0
        self.build_ms = 0
        self.offers = 0
        self.shops = {}            # owner: dict(name, map, x, y, ch, running, seller, bot, emp)
        self.protos = {}
        self.tops = {}
        self.bonus_points = ()
        self.stones = ()
        self.counts = {}
        self.variants = {}         # (vnum, var): socket0 to name it by
        self.names = {}            # (vnum, var): display name

    def execute(self, sql, params=()):
        with self.lock:
            return self.conn.execute(sql, params).fetchall()

    def category_counts(self, f):
        key = rules.count_key(f)
        with self.lock:
            cached = self.counts.get(key)
        if cached is not None:
            return cached
        where, params = rules.build_where(f, ignore_category=True)
        rows = self.execute("SELECT cat, sub, COUNT(*) FROM offers WHERE " + where + " GROUP BY cat, sub", params)
        counts = {(int(c), int(s)): int(n) for c, s, n in rows}
        with self.lock:
            if len(self.counts) >= COUNT_CACHE_KEYS:
                self.counts.clear()
            self.counts[key] = counts
        return counts

    def page(self, f):
        """(rows as dicts of OFFER_COLUMNS, total, counts, page, pages)."""
        counts = self.category_counts(f)
        if "cat" in f:
            total = sum(n for (c, s), n in counts.items() if c == f["cat"] and ("sub" not in f or s == f["sub"]))
        else:
            total = sum(counts.values())
        per, page = f.get("per", rules.DEFAULT_PER), f.get("page", 1)
        pages = max(1, (total + per - 1) // per)
        page = min(page, pages)
        where, params = rules.build_where(f)
        rows = self.execute("SELECT " + ", ".join(OFFER_COLUMNS) + " FROM offers WHERE " + where +
                            " ORDER BY " + rules.order_by(f) + " LIMIT ? OFFSET ?",
                            list(params) + [per, (page - 1) * per])
        return [dict(zip(OFFER_COLUMNS, r)) for r in rows], total, counts, page, pages


def build_snapshot(items, protos, shops, owners, tops, names, samples, yang_pct=100):
    """A Snapshot of offer lines.

    items: iterable of (id, owner, vnum, count, s0, s1, s2, (type0, value0, ... type6, value6), price)
    protos: {vnum: Proto}
    shops: {owner: (map, x, y, channel, running, shop name)}
    owners: {owner: (name, bot, empire)}
    tops: {point: top roll}
    names: {(vnum, var): display name}
    samples: {(vnum, plus, var): (base, ...)} the week's bases (History.samples)
    yang_pct: the bots' price multiplier at the world's yang rate, percent
    """
    started = time.time()
    snap = Snapshot()
    snap.protos, snap.tops = protos, tops
    cur = snap.conn.cursor()
    for statement in SCHEMA:
        cur.execute(statement)
    # The pieces of each kind on all the running stalls, read before the rows
    # are written so each row carries its kind's count (the "rare" mark).
    pieces = {}
    for _item_id, owner, vnum, count, s0, _s1, _s2, _attrs, price in items:
        proto = protos.get(vnum)
        shop = shops.get(owner)
        if proto is None or price is None or price <= 0 or not shop or not shop[4]:
            continue
        key = (vnum, variant_of(proto, s0))
        pieces[key] = pieces.get(key, 0) + max(1, int(count or 1))
    classes, kinds, points, stones, bases = {}, set(), set(), set(), {}
    batch = []
    insert = "INSERT INTO offers (" + ", ".join(OFFER_COLUMNS) + ") VALUES (" + ", ".join("?" * len(OFFER_COLUMNS)) + ")"
    for item_id, owner, vnum, count, s0, s1, s2, attrs, price in items:
        proto = protos.get(vnum)
        if proto is None or price is None or price <= 0:
            continue
        count = max(1, int(count or 1))
        shop = shops.get(owner)
        seller = owners.get(owner, ("", False, 0))
        var = variant_of(proto, s0)
        key = (vnum, var)
        if key not in classes:
            classes[key] = (rules.classify(proto.type, proto.subtype, vnum, s0),
                            rules.class_mask(proto.type, proto.antiflag, vnum, s0))
            snap.variants[key] = int(s0 or 0)
        (cat, sub), cls = classes[key]
        kinds.add(key)
        lines, avg, skl, nmax, tiers = [], 0, 0, 0, 0
        for k in range(0, 14, 2):
            point, value = attrs[k], attrs[k + 1]
            if not point or not value:
                continue
            if point == rules.POINT_AVERAGE_DAMAGE:
                avg = value
            elif point == rules.POINT_SKILL_DAMAGE:
                skl = value
            else:
                lines.append((point, value))
                points.add(point)
                if rules.is_max_line(point, value, tops):
                    nmax += 1
                tiers += rules.line_tier(point)
        sockets = []
        for s in (s0, s1, s2):
            s = int(s or 0)
            if proto.type in (rules.ITEM_WEAPON, rules.ITEM_ARMOR) and rules.SOUL_STONES[0] <= s <= rules.SOUL_STONES[1]:
                sockets.append(s)
                stones.add(s)
            else:
                sockets.append(0)
        unit = float(price) / count
        damage = [(p, v) for p, v in ((rules.POINT_AVERAGE_DAMAGE, avg), (rules.POINT_SKILL_DAMAGE, skl)) if v]
        plus = proto.plus
        mult = rules.reference_multiplier(proto.type, proto.subtype, proto.level, lines, damage, tops)
        sheet_day = rules.sheet_price(proto.type, vnum, s0) * yang_pct / 100.0
        week_key = (vnum, plus, var)
        if week_key in bases:
            base = bases[week_key]
        else:
            # Once a kind: a busy kind has thousands of listings in the week.
            base = bases[week_key] = rules.history_base(samples.get(week_key) if samples else None, sheet_day)
        if base:
            ref, rsrc = base * mult, rules.REF_WEEK
        else:
            ref, rsrc = sheet_day * mult, rules.REF_SHEET
        if ref <= 0:
            rsrc = rules.REF_NONE
        pct = rules.bargain_pct(unit, ref) if ref > 0 else None
        slip = rules.is_slip(count, cat == rules.CAT_BOOKS, vnum in sheet.REFINE_MATERIALS, unit, ref)
        on_market = pieces.get(key, 0)
        batch.append((item_id, owner, vnum, var, cat, sub, plus, proto.level, cls, int(price), count, unit,
                      len(lines), nmax, tiers, avg, skl) + tuple(attrs) +
                     (sum(1 for s in sockets if s), sockets[0], sockets[1], sockets[2],
                      int(seller[2] or 0), int(shop[3]) if shop else 0, int(shop[0]) if shop else 0,
                      1 if seller[1] else 0, 1 if shop and shop[4] else 0, ref, rules.bargain_key(pct),
                      1 if slip else 0, 1 if rules.is_rare(on_market) else 0, on_market, rsrc))
        if len(batch) >= 5000:
            cur.executemany(insert, batch)
            batch = []
    if batch:
        cur.executemany(insert, batch)
    rows = []
    for key in kinds:
        name = names.get(key, "")
        snap.names[key] = name
        rows.append((key[0], key[1], rules.normalize(name)))
    cur.executemany("INSERT OR REPLACE INTO kinds VALUES (?, ?, ?)", rows)
    shop_rows = []
    for owner, shop in shops.items():
        seller = owners.get(owner, ("", False, 0))
        snap.shops[owner] = {"name": shop[5], "map": int(shop[0]), "x": int(shop[1]), "y": int(shop[2]),
                             "ch": int(shop[3]), "running": bool(shop[4]), "seller": seller[0],
                             "bot": bool(seller[1]), "emp": int(seller[2] or 0)}
        shop_rows.append((owner, rules.normalize(seller[0] + " | " + shop[5])))
    cur.executemany("INSERT OR REPLACE INTO shops VALUES (?, ?)", shop_rows)
    for statement in INDEXES:
        cur.execute(statement)
    cur.execute("ANALYZE")
    snap.conn.commit()
    snap.offers = snap.execute("SELECT COUNT(*) FROM offers")[0][0]
    snap.bonus_points = tuple(sorted(points | set(sheet.BONUS_TIERS)))
    snap.stones = tuple(sorted(stones))
    snap.generated_at = time.time()
    snap.build_ms = int((snap.generated_at - started) * 1000)
    return snap


# -----------------------------------------------------------------------------
#  The week of prices.
# -----------------------------------------------------------------------------
class History(object):
    """market_history.sqlite: each listing once by its item id, and an hour's
    median of each kind. Both panel workers write it; SQLite's own locking
    and INSERT OR IGNORE / OR REPLACE keep that harmless."""

    def __init__(self, path):
        self.path = path
        self.lock = threading.Lock()
        self.samples = {}
        self.samples_at = 0.0
        self._ready = False

    def _connect(self):
        conn = sqlite3.connect(self.path, timeout=10)
        if not self._ready:
            conn.execute("CREATE TABLE IF NOT EXISTS seen (item_id INTEGER PRIMARY KEY, vnum INT, plus INT, "
                         "var INT, base REAL, first_ts INT)")
            conn.execute("CREATE INDEX IF NOT EXISTS seen_kind ON seen (vnum, plus, var, first_ts)")
            conn.execute("CREATE TABLE IF NOT EXISTS hourly (hour INT, vnum INT, plus INT, var INT, n INT, "
                         "median REAL, low REAL, PRIMARY KEY (vnum, plus, var, hour))")
            conn.commit()
            self._ready = True
        return conn

    def record(self, lines, now=None):
        """lines: [(item_id, vnum, plus, var, unit, base)] of the running offers."""
        now = int(now or time.time())
        hour = now // 3600
        per_kind = {}

        def seen_rows():
            # One pass over `lines` (a generator is fine): the stall lines are
            # written as they come and only their unit prices are kept here.
            for item_id, vnum, plus, var, unit, base in lines:
                per_kind.setdefault((vnum, plus, var), []).append(unit)
                yield item_id, vnum, plus, var, base, now
        with self.lock:
            conn = self._connect()
            try:
                conn.executemany("INSERT OR IGNORE INTO seen VALUES (?, ?, ?, ?, ?, ?)", seen_rows())
                conn.executemany("INSERT OR REPLACE INTO hourly VALUES (?, ?, ?, ?, ?, ?, ?)",
                                 ((hour, v, p, w, len(units), rules.median(units), min(units))
                                  for (v, p, w), units in per_kind.items()))
                horizon = now - HISTORY_KEEP_DAYS * 86400
                conn.execute("DELETE FROM seen WHERE first_ts < ?", (horizon,))
                conn.execute("DELETE FROM hourly WHERE hour < ?", (horizon // 3600,))
                conn.commit()
            finally:
                conn.close()

    def compute_samples(self, now=None):
        """{(vnum, plus, var): (base, ...)} of the last seven days."""
        now = int(now or time.time())
        samples = {}
        with self.lock:
            conn = self._connect()
            try:
                for vnum, plus, var, base in conn.execute(
                        "SELECT vnum, plus, var, base FROM seen WHERE first_ts >= ?",
                        (now - rules.HISTORY_DAYS * 86400,)):
                    if base and base > 0:
                        samples.setdefault((vnum, plus, var), []).append(base)
            finally:
                conn.close()
        self.samples = {k: tuple(v) for k, v in samples.items() if len(v) >= rules.HISTORY_MIN_OFFERS}
        self.samples_at = time.time()
        return self.samples

    def chart(self, vnum, plus, var, now=None):
        """[(hour start, median, low, lines)] of the last seven days."""
        now = int(now or time.time())
        with self.lock:
            conn = self._connect()
            try:
                rows = conn.execute("SELECT hour, median, low, n FROM hourly WHERE vnum = ? AND plus = ? AND var = ? "
                                    "AND hour >= ? ORDER BY hour",
                                    (int(vnum), int(plus), int(var), (now - rules.HISTORY_DAYS * 86400) // 3600)
                                    ).fetchall()
            finally:
                conn.close()
        return [(int(h) * 3600, float(m or 0), float(lo or 0), int(n or 0)) for h, m, lo, n in rows]


# -----------------------------------------------------------------------------
#  The database's side: what one build reads, read-only.
# -----------------------------------------------------------------------------
def _text(value):
    if isinstance(value, (bytes, bytearray)):
        for encoding in ("cp1250", "utf-8", "latin1"):
            try:
                return bytes(value).decode(encoding)
            except UnicodeDecodeError:
                pass
        return bytes(value).decode("cp1250", "replace")
    return str(value or "")


def _ids(ids):
    return "(" + ",".join(str(int(i)) for i in sorted(set(ids))) + ")" if ids else "(NULL)"


class DbSource(object):
    """Reads one build's worth from MariaDB through the panel's db().
    Every statement is a SELECT under max_statement_time; the item lines come
    in chunks along the primary key with a pause between."""

    def __init__(self, connect, yang_rate=None):
        self._connect = connect
        self._yang_rate = yang_rate
        self._protos = None
        self._protos_at = 0.0
        self._tops = {}

    def connect(self):
        conn = self._connect()
        try:
            with conn.cursor() as cur:
                cur.execute("SET SESSION max_statement_time = %s", (STATEMENT_SECONDS,))
        except Exception:                            # noqa: BLE001 - not every server has it
            pass
        return conn

    def protos(self, conn):
        if self._protos is not None and time.time() - self._protos_at < PROTO_SECONDS:
            return self._protos, self._tops
        out = {}
        with conn.cursor() as cur:
            cur.execute("SELECT vnum, type, subtype, antiflag, limittype0, limitvalue0, limittype1, limitvalue1, "
                        "value0, value1, value2, value3, value4, value5, applytype0, applyvalue0, applytype1, "
                        "applyvalue1, applytype2, applyvalue2, CAST(locale_name AS BINARY) AS name "
                        "FROM player.item_proto")
            for r in cur.fetchall():
                level = 0
                for k in (0, 1):
                    if int(r.get("limittype%d" % k) or 0) == 1:
                        level = int(r.get("limitvalue%d" % k) or 0)
                applies = tuple((int(r.get("applytype%d" % k) or 0), int(r.get("applyvalue%d" % k) or 0))
                                for k in range(3) if int(r.get("applytype%d" % k) or 0))
                name = _text(r.get("name")).strip()
                _base, plus = rules.split_plus(name)
                vnum = int(r["vnum"] or 0)
                out[vnum] = Proto(vnum, r.get("type") or 0, r.get("subtype") or 0, r.get("antiflag") or 0, level,
                                  tuple(int(r.get("value%d" % k) or 0) for k in range(6)), applies, plus, name)
            tops = {}
            for table in ("world.item_attr", "world.item_attr_rare"):
                try:
                    cur.execute("SELECT apply+0 AS p, GREATEST(lv1, lv2, lv3, lv4, lv5) AS top FROM " + table)
                    for r in cur.fetchall():
                        point, top = int(r["p"] or 0), int(r["top"] or 0)
                        if point and top > tops.get(point, 0):
                            tops[point] = top
                except Exception:                    # noqa: BLE001 - a world without the table
                    pass
        self._protos, self._tops, self._protos_at = out, tops, time.time()
        return out, tops

    def shops(self, conn):
        out = {}
        with conn.cursor() as cur:
            cur.execute("SELECT owner, duration, `map`, x, y, channel, CAST(name AS BINARY) AS name "
                        "FROM player.ikashop_offlineshop")
            for r in cur.fetchall():
                out[int(r["owner"])] = (int(r["map"] or 0), int(r["x"] or 0), int(r["y"] or 0),
                                        int(r["channel"] or 0), int(r["duration"] or 0) > 0,
                                        _text(r.get("name")).strip())
        return out

    def owners(self, conn, pids):
        out = {}
        pids = sorted(pids)
        with conn.cursor() as cur:
            for i in range(0, len(pids), 1000):
                cur.execute("SELECT p.id, CAST(p.name AS BINARY) AS name, "
                            "(LEFT(a.login, 10) = 'playerbot_' OR p.name LIKE 'bot%%') AS bot, "
                            "(SELECT pi.empire FROM player.player_index pi WHERE pi.id = p.account_id) AS emp "
                            "FROM player.player p LEFT JOIN account.account a ON a.id = p.account_id "
                            "WHERE p.id IN " + _ids(pids[i:i + 1000]))
                for r in cur.fetchall():
                    out[int(r["id"])] = (_text(r.get("name")).strip(), bool(int(r.get("bot") or 0)),
                                         int(r.get("emp") or 0))
        return out

    def items(self, conn, sleep=time.sleep):
        last, out = 0, []
        columns = ["id", "owner_id", "vnum", "`count`", "socket0", "socket1", "socket2"]
        for k in range(7):
            columns += ["attrtype%d" % k, "attrvalue%d" % k]
        with conn.cursor() as cur:
            while True:
                cur.execute("SELECT " + ", ".join(columns) + ", "
                            "CAST(JSON_UNQUOTE(JSON_EXTRACT(ikashop_data, '$.yang')) AS UNSIGNED) AS yang "
                            "FROM player.item WHERE `window` = 'IKASHOP_OFFLINESHOP' AND id > %s "
                            "AND ikashop_data IS NOT NULL AND ikashop_data <> '' ORDER BY id LIMIT %s",
                            (last, ITEM_CHUNK))
                rows = cur.fetchall()
                for r in rows:
                    # One flat tuple a line, and the one shared tuple for a line
                    # without bonuses (most of them): a quarter of a million
                    # lines stay a few tens of MB in the panel's memory.
                    attrs = tuple(int(r.get(c) or 0) for c in ATTR_COLUMNS)
                    if not any(attrs):
                        attrs = NO_ATTRS
                    out.append((int(r["id"]), int(r["owner_id"]), int(r["vnum"]), int(r.get("count") or 1),
                                int(r.get("socket0") or 0), int(r.get("socket1") or 0), int(r.get("socket2") or 0),
                                attrs, int(r.get("yang") or 0)))
                if len(rows) < ITEM_CHUNK:
                    break
                last = int(rows[-1]["id"])
                sleep(CHUNK_PAUSE)
        return out

    def yang_rate(self):
        try:
            return int(self._yang_rate() if self._yang_rate else 100) or 100
        except Exception:                            # noqa: BLE001
            return 100


class Store(object):
    """The current snapshot, the thread that renews it and the history."""

    def __init__(self, source, history_path, names=None, logger=None):
        self.source = source
        self.names = names              # function(proto, vnum, socket0) -> display name
        self.logger = logger
        self.history = History(history_path)
        self.current = None
        self.lock = threading.Lock()
        self.building = False
        self.last_error = ""
        self.viewed_at = 0.0
        self.requested_at = 0.0
        self.thread = None

    def viewed(self):
        self.viewed_at = time.time()

    def request_refresh(self):
        """A rebuild now, unless the snapshot is younger than fifteen seconds."""
        snap = self.current
        if snap is not None and time.time() - snap.generated_at < REFRESH_MIN_SECONDS:
            return False
        self.requested_at = time.time()
        return True

    def start(self, first_delay=FIRST_BUILD_DELAY):
        with self.lock:
            if self.thread is not None and self.thread.is_alive():
                return
            self.thread = threading.Thread(target=self._run, args=(first_delay,), name="market-preview",
                                           daemon=True)
            self.thread.start()

    def _run(self, first_delay):
        wake = time.time() + first_delay
        attempted = 0.0
        while time.time() - self.viewed_at < STOP_AFTER_IDLE_SECONDS:
            now = time.time()
            if self.requested_at and now - attempted >= REFRESH_MIN_SECONDS and \
                    (self.current is None or self.requested_at > self.current.generated_at):
                wake = now
            if now >= wake:
                attempted = now
                self.requested_at = 0.0
                self.rebuild()
                active = time.time() - self.viewed_at < VIEWED_KEEPS_ACTIVE
                wake = time.time() + (ACTIVE_SECONDS if active else IDLE_SECONDS)
            time.sleep(1.0)
        # Nobody has looked for hours: free the snapshot's memory too.
        self.current = None

    def _log(self, message):
        if self.logger is not None:
            try:
                self.logger.exception(message)
            except Exception:                        # noqa: BLE001
                pass

    def rebuild(self):
        if self.building:
            return self.current
        self.building = True
        try:
            snap = self._build()
            self.current = snap
            self.last_error = ""
            return snap
        except Exception as exc:                     # noqa: BLE001 - the page says so; the old snapshot stays
            self.last_error = "%s: %s" % (type(exc).__name__, str(exc)[:300])
            self._log("market preview: snapshot failed")
            return self.current
        finally:
            self.building = False

    def _build(self):
        src = self.source
        conn = src.connect()
        try:
            protos, tops = src.protos(conn)
            shops = src.shops(conn)
            items = src.items(conn)
            owners = src.owners(conn, {i[1] for i in items} | set(shops))
        finally:
            try:
                conn.close()
            except Exception:                        # noqa: BLE001
                pass
        yang_pct = rules.yang_rate_price_pct(src.yang_rate())
        if time.time() - self.history.samples_at > 3600 or not self.history.samples:
            try:
                self.history.compute_samples()
            except Exception:                        # noqa: BLE001 - no history: the price list alone
                self._log("market preview: history read failed")
        names = {}
        for item in items:
            proto = protos.get(item[2])
            key = (item[2], variant_of(proto, item[4]))
            if key not in names:
                names[key] = self.names(proto, item[2], item[4]) if self.names else (proto.name if proto else "")
        snap = build_snapshot(items, protos, shops, owners, tops, names, self.history.samples, yang_pct)
        snap.yang_pct = yang_pct
        self._record_history(snap, protos)
        return snap

    def _record_history(self, snap, protos):
        """Every running line's unit price over its own bonus multiplier."""
        def lines():
            # In chunks along the id, so a quarter of a million lines never
            # stand in memory twice.
            last = -1
            while True:
                rows = snap.execute("SELECT id, vnum, plus, var, unit, a0, v0, a1, v1, a2, v2, a3, v3, a4, v4, a5, v5, "
                                    "a6, v6, lvl FROM offers WHERE running = 1 AND slip = 0 AND id > ? "
                                    "ORDER BY id LIMIT 20000", (last,))
                if not rows:
                    return
                for r in rows:
                    proto = protos.get(r[1])
                    attrs = [(r[5 + 2 * k], r[6 + 2 * k]) for k in range(7)]
                    ordinary = [(p, v) for p, v in attrs if p and v and p not in DAMAGE_POINTS]
                    damage = [(p, v) for p, v in attrs if p and v and p in DAMAGE_POINTS]
                    mult = rules.reference_multiplier(proto.type, proto.subtype, r[19], ordinary, damage, snap.tops) \
                        if proto else 1.0
                    yield r[0], r[1], r[2], r[3], r[4], r[4] / mult if mult else r[4]
                last = rows[-1][0]
        try:
            self.history.record(lines())
        except Exception:                            # noqa: BLE001 - a full disk costs the chart, not the page
            self._log("market preview: history write failed")


def default_history_path(spool_dir):
    return os.path.join(str(spool_dir), "market_history.sqlite")
