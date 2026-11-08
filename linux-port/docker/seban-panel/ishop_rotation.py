"""MT2009_PLUS_ISHOP_ROTACJA_V1: "ItemShop - rotacja zestawów" (właściciel, 8 listopada 2026: "gracze nie mają już
stałego dostępu do wszystkich skrzyń zestawów ... codziennie tylko 2 skrzynie ... nowa zakładka Dzisiejsze oferty").

What the page does (nothing here talks to the game; the tables are mariadb/playerbot/itemshop3_schema.sql, written by
tools/itemshop3/gen_itemshop3_sql.py):

* the switch and the numbers - rows of itemshop3.settings the players' web shop reads at every page:
  rot_enabled (1 = the rotation, 0 = every set chest listed as before), rot_per_day (chests a day, 2),
  rot_price (SM of one set piece, 79), rot_days (days of one set piece, 7), rot_seed (the shuffle's seed);
* the preview: today's chests and the next days' (Europe/Warsaw days - the change at midnight), each with the pieces
  of its set it sells on its own (the view itemshop3.rotation_pieces);
* the pins: a chest for a date (itemshop3.rotation_pins) - shown that day first, the rotation fills the rest.

The schedule is computed the same way as the shop's (app/shop3/include/classes/Shop.php, rotationDay): the set chests
(itemshop3.chests with set_id > 0) by id, shuffled once a cycle with md5("seed|cycle|i") -> Fisher-Yates; day d (days
since 2026-01-01) takes the slots d*k .. d*k+k-1 of the cycles laid end to end, so every chest comes once a cycle; at
the seam of two cycles a chest of the old one's last days is moved back from the new one's head (no chest twice a day,
none on two days in a row).
Changing rot_per_day or rot_seed (or a new set chest) gives a new schedule from that day on.

The bots are not affected: they buy in the game from itemshop3.shop (playerbot_itemshop.h), every chest at any time.
"""
import datetime
import hashlib
import secrets

try:
    from zoneinfo import ZoneInfo
except ImportError:  # pragma: no cover - python < 3.9
    ZoneInfo = None

EPOCH = datetime.date(2026, 1, 1)
TZ_NAME = "Europe/Warsaw"
MAX_PER_DAY = 10
DEFAULTS = {"enabled": 1, "per_day": 2, "price": 79, "days": 7, "seed": "mt2009plus"}
LIMITS = {"per_day": (1, MAX_PER_DAY), "price": (1, 100000), "days": (1, 365)}
PREVIEW_DAYS, PREVIEW_MAX = 14, 120
PIECE_ID_BASE = 800000000


# ---- the schedule (= Shop.php rotation*) -----------------------------------------------------------------------

def warsaw_today(now=None):
    if now is not None:
        return now
    if ZoneInfo is not None:
        try:
            return datetime.datetime.now(ZoneInfo(TZ_NAME)).date()
        except Exception:
            pass
    return datetime.date.today()


def day_index(day):
    return max(0, (day - EPOCH).days)


def _hash(text):
    return int(hashlib.md5(text.encode("utf-8")).hexdigest()[:8], 16)


def shuffle(ids, seed, cycle):
    out = list(ids)
    for i in range(len(out) - 1, 0, -1):
        j = _hash(f"{seed}|{cycle}|{i}") % (i + 1)
        out[i], out[j] = out[j], out[i]
    return out


class Schedule:
    def __init__(self, chest_ids, per_day, seed):
        self.ids = list(chest_ids)
        self.n = len(self.ids)
        self.k = min(max(1, int(per_day)), MAX_PER_DAY, self.n) if self.n else 0
        self.seed = str(seed)
        self.orders = []

    def order(self, cycle):
        n, k = self.n, self.k
        for c in range(len(self.orders), cycle + 1):
            perm = shuffle(self.ids, self.seed, c)
            if c > 0:
                # the seam: the first head + k of this cycle take none of the last tail + k of the previous one
                tail = (c * n) % k
                head = (k - tail) % k
                m = min(n, head + k)
                avoid = self.orders[c - 1][n - min(n, tail + k):]
                for i in range(m):
                    if perm[i] not in avoid:
                        continue
                    for j in range(m, n):
                        if perm[j] not in avoid:
                            perm[i], perm[j] = perm[j], perm[i]
                            break
            self.orders.append(perm)
        return self.orders[cycle]

    def picks(self, day):
        if not self.n:
            return []
        d = day_index(day)
        out = []
        for j in range(self.k):
            p = d * self.k + j
            cid = self.order(p // self.n)[p % self.n]
            if cid not in out:
                out.append(cid)
        return out

    def day(self, day, pins=()):
        pins = [c for i, c in enumerate(pins) if c in self.ids and c not in pins[:i]]
        out = list(pins)
        for cid in self.picks(day):
            if len(out) < max(self.k, len(pins)) and cid not in out:
                out.append(cid)
        return out


# ---- the database ---------------------------------------------------------------------------------------------

def read_settings(cur):
    s = dict(DEFAULTS)
    cur.execute("SELECT name, value FROM itemshop3.settings WHERE name IN "
                "('rot_enabled','rot_per_day','rot_price','rot_days','rot_seed')")
    for row in cur.fetchall():
        key = row["name"][4:]
        if key == "seed":
            s[key] = str(row["value"])
        else:
            try:
                s[key] = int(row["value"])
            except (TypeError, ValueError):
                pass
    s["enabled"] = 1 if s["enabled"] else 0
    s["per_day"] = max(1, min(MAX_PER_DAY, s["per_day"]))
    return s


def write_setting(cur, name, value):
    cur.execute("INSERT INTO itemshop3.settings (name, value) VALUES (%s,%s) ON DUPLICATE KEY UPDATE value=VALUES(value), "
                "date=NOW()", (name, str(value)))


def tables_ready(cur):
    cur.execute("SELECT COUNT(*) AS n FROM information_schema.tables WHERE table_schema='itemshop3' AND table_name IN "
                "('chests','rotation_pins','rotation_pieces','set_members')")
    return int(cur.fetchone()["n"]) == 4


def chests(cur):
    cur.execute("SELECT c.id, c.line, c.set_id, c.name, c.price, c.image FROM itemshop3.chests c WHERE c.set_id > 0 "
                "ORDER BY c.id")
    return cur.fetchall()


def pins_between(cur, first, last):
    cur.execute("SELECT day, chest_id FROM itemshop3.rotation_pins WHERE day BETWEEN %s AND %s ORDER BY day, date, chest_id",
                (first, last))
    out = {}
    for row in cur.fetchall():
        out.setdefault(row["day"], []).append(int(row["chest_id"]))
    return out


def pieces_by_chest(cur):
    cur.execute("SELECT rot_chest, id, vnum, name, set_sort, coins, time FROM itemshop3.rotation_pieces "
                "ORDER BY rot_chest, set_sort, vnum")
    out = {}
    for row in cur.fetchall():
        out.setdefault(int(row["rot_chest"]), []).append(row)
    return out


def preview(cur, settings, first, days):
    rows = chests(cur)
    by_id = {int(c["id"]): c for c in rows}
    sched = Schedule(by_id.keys(), settings["per_day"], settings["seed"])
    last = first + datetime.timedelta(days=days - 1)
    pins = pins_between(cur, first, last)
    out = []
    for i in range(days):
        day = first + datetime.timedelta(days=i)
        ids = sched.day(day, pins.get(day, []))
        out.append({"day": day, "ids": ids, "pinned": set(pins.get(day, [])), "chests": [by_id[c] for c in ids if c in by_id]})
    return out, by_id, sched


# ---- the page -------------------------------------------------------------------------------------------------

def install(app, db, login_required, csrf_token, icon_url=None):
    from flask import abort, flash, redirect, render_template, request, session, url_for

    icon = icon_url or (lambda vnum: None)

    def number(raw, label, key):
        lo, hi = LIMITS[key]
        try:
            value = int((raw or "").strip())
        except ValueError:
            raise ValueError(f"{label}: wpisz liczbę całkowitą.")
        if not lo <= value <= hi:
            raise ValueError(f"{label}: dozwolony zakres to {lo}–{hi}.")
        return value

    def parse_day(raw):
        try:
            return datetime.date.fromisoformat((raw or "").strip())
        except ValueError:
            raise ValueError("Data: wybierz dzień (RRRR-MM-DD).")

    @app.route("/manage/ishop-rotation", methods=["GET", "POST"])
    @login_required
    def manage_ishop_rotation():
        with db() as con, con.cursor() as cur:
            if not tables_ready(cur):
                return render_template("ishop_rotation.html", ready=False, rot_csrf=csrf_token())
            if request.method == "POST":
                expected = session.get("seban_update_csrf", "")
                if not expected or not secrets.compare_digest(request.form.get("rot_csrf", ""), expected):
                    abort(400, "Odśwież stronę i spróbuj ponownie.")
                action = request.form.get("action", "")
                anchor = ""
                try:
                    if action == "config":
                        n_chests = len(chests(cur))
                        enabled = 1 if request.form.get("enabled") == "1" else 0
                        per_day = number(request.form.get("per_day"), "Skrzyń dziennie", "per_day")
                        if n_chests and per_day > n_chests:
                            raise ValueError(f"Skrzyń dziennie: najwyżej {n_chests} (tyle jest skrzyń zestawów).")
                        price = number(request.form.get("price"), "Cena przedmiotu (SM)", "price")
                        days = number(request.form.get("days"), "Czas przedmiotu (dni)", "days")
                        seed = (request.form.get("seed") or "").strip()[:32] or DEFAULTS["seed"]
                        for name, value in (("rot_enabled", enabled), ("rot_per_day", per_day), ("rot_price", price),
                                            ("rot_days", days), ("rot_seed", seed)):
                            write_setting(cur, name, value)
                        app.logger.info("ISHOP_ROTACJA: config enabled=%s per_day=%s price=%s days=%s seed=%s",
                                        enabled, per_day, price, days, seed)
                        flash("Rotacja włączona – gracze widzą skrzynie zestawów tylko w „Dzisiejsze oferty”." if enabled
                              else "Rotacja wyłączona – wszystkie skrzynie zestawów są w sklepie jak dawniej.", "success")
                    elif action == "pin":
                        anchor = "przypiecia"
                        day = parse_day(request.form.get("day"))
                        chest_id = int(request.form.get("chest_id", "0") or 0)
                        if chest_id not in {int(c["id"]) for c in chests(cur)}:
                            raise ValueError("Wybierz skrzynię zestawu.")
                        cur.execute("INSERT IGNORE INTO itemshop3.rotation_pins (day, chest_id) VALUES (%s,%s)", (day, chest_id))
                        app.logger.info("ISHOP_ROTACJA: pin day=%s chest=%s", day, chest_id)
                        flash(f"Przypięto skrzynię do dnia {day:%d.%m.%Y}.", "success")
                    elif action == "unpin":
                        anchor = "przypiecia"
                        day = parse_day(request.form.get("day"))
                        chest_id = int(request.form.get("chest_id", "0") or 0)
                        cur.execute("DELETE FROM itemshop3.rotation_pins WHERE day=%s AND chest_id=%s", (day, chest_id))
                        app.logger.info("ISHOP_ROTACJA: unpin day=%s chest=%s", day, chest_id)
                        flash("Usunięto przypięcie.", "success")
                    else:
                        abort(400)
                except ValueError as exc:
                    flash(str(exc), "error")
                return redirect(url_for("manage_ishop_rotation") + (f"#{anchor}" if anchor else ""))

            settings = read_settings(cur)
            try:
                days = max(1, min(PREVIEW_MAX, int(request.args.get("dni", PREVIEW_DAYS))))
            except ValueError:
                days = PREVIEW_DAYS
            today = warsaw_today()
            plan, by_id, sched = preview(cur, settings, today, days)
            pieces = pieces_by_chest(cur)
            cur.execute("SELECT day, chest_id FROM itemshop3.rotation_pins WHERE day >= %s ORDER BY day, chest_id", (today,))
            pins = cur.fetchall()
            # how often each chest comes: its next day in the preview window
            cycle_days = (sched.n + sched.k - 1) // sched.k if sched.k else 0
        return render_template("ishop_rotation.html", ready=True, settings=settings, plan=plan, by_id=by_id,
                               pieces=pieces, pins=pins, today=today, days=days, limits=LIMITS, tz_name=TZ_NAME,
                               n_chests=len(by_id), cycle_days=cycle_days, icon=icon, rot_csrf=csrf_token(),
                               piece_id_base=PIECE_ID_BASE)
