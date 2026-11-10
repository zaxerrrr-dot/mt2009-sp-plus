"""MT2009_PLUS_BOT_FAIR_PRICE_V1: "Rynek - uczciwa cena" - the bots' fair price market (the owner, 10 November 2026;
docs/RYNEK_UCZCIWA_CENA.md). The game's side is playerbot_fair_price.h (the fair price by kind) and playerbot_lada.h (the
bots' own prices); nothing here talks to the game directly:

* the kinds: player.playerbot_market_fair - one row a kind, written by the game's writer core every m2_bot_fair_step_min
  minutes: the reference (and where it came from), the fair price and its ratio, the bounds, the stock on every stand,
  the sellers, the sales of the window and of the last 6 h, the cover, the trimmed mean of the sales, the spread of the
  offers (min / p25 / median / p75 / max), the imbalance, the confidence and the move an hour;
* the history: player.playerbot_market_fair_hist - a point an hour a kind (fair, reference, stock, units sold, the
  sales' mean, the median offer, sellers);
* the pins: player.playerbot_market_fair_pin - a pinned fair price a unit and / or the kind's own bounds (percent of the
  reference); the writer reads them every step;
* the switches: event flags (player.quest rows with dwPID 0, read by the game every ~10 s; 0 = the default).
"""
import secrets
from datetime import datetime

FLAGS = (
    # name, label, default, lo, hi, help
    ("m2_bot_fairprice_off", "Wyłącz rynek uczciwej ceny (stary system: wyprzedaż nadwyżek, progi -5/-3 %, podłoga 90 %)", 0, 0, 1, "1 = stary system"),
    ("m2_bot_fair_step_min", "Co ile minut przeliczać uczciwą cenę", 15, 5, 120, "domyślnie 15"),
    ("m2_bot_fair_down_pct", "Maks. spadek uczciwej ceny na godzinę (%)", 10, 1, 50, "przy skrajnej nadwyżce i pełnej pewności"),
    ("m2_bot_fair_up_pct", "Maks. wzrost uczciwej ceny na godzinę (%)", 15, 1, 50, "przy skrajnym braku i pełnej pewności"),
    ("m2_bot_fair_min_pct", "Dolna granica uczciwej ceny (% ceny bazowej)", 60, 10, 100, "domyślnie 60"),
    ("m2_bot_fair_max_pct", "Górna granica uczciwej ceny (% ceny bazowej)", 200, 100, 1000, "domyślnie 200"),
    ("m2_bot_fair_cover_days", "Zapas w równowadze (dni sprzedaży)", 7, 1, 90, "więcej towaru niż tyle dni sprzedaży = nacisk w dół"),
    ("m2_bot_fair_stock_weight", "Waga ilości towaru (w dół, %)", 30, -1, 100, "-1 = ilość nie obniża ceny"),
    ("m2_bot_fair_price_weight", "Waga zakupów po uczciwej cenie lub drożej (w górę, %)", 50, -1, 100, "-1 = wyłączone"),
    ("m2_bot_fair_trend_weight", "Waga przyspieszenia / spowolnienia sprzedaży (%)", 30, -1, 100, "-1 = wyłączone"),
    ("m2_bot_fair_conf_sales", "Sprzedaży do połowy pewności", 8, 1, 1000, "rzadkie przedmioty ruszają się mało"),
    ("m2_bot_fair_window_h", "Okno sprzedaży (godziny)", 48, 6, 96, "domyślnie 48"),
    ("m2_bot_fair_check_min", "Bot sprawdza swoją cenę co (min, od)", 30, 5, 1440, "losowo w przedziale od-do"),
    ("m2_bot_fair_check_max", "Bot sprawdza swoją cenę co (min, do)", 60, 5, 1440, ""),
    ("m2_bot_fair_step_lo", "Krok ceny bota (%, od)", 3, 1, 50, "sprzedało się: w górę, nie: w dół"),
    ("m2_bot_fair_step_hi", "Krok ceny bota (%, do)", 5, 1, 50, ""),
    ("m2_bot_fair_list_min_pct", "Najniżej, jak bot wystawi (% uczciwej ceny)", 60, 10, 100, "domyślnie 60"),
    ("m2_bot_fair_list_max_pct", "Najwyżej, jak bot wystawi (% uczciwej ceny)", 200, 100, 1000, "domyślnie 200"),
    ("m2_bot_fair_edits_s", "Zmian cen na sekundę (rdzeń)", 20, 1, 200, ""),
    ("m2_bot_fair_hist_days", "Historia (dni)", 14, 1, 90, ""),
)
FLAG_NAMES = tuple(f[0] for f in FLAGS)
SRC_LABELS = {"O": "właściciela", "S": "cennik", "P": "kupiec/portfel", "M": "ze sprzedaży"}
SORTS = {
    "stock": "f.stock DESC",
    "sold": "f.sold_w DESC",
    "sellers": "f.sellers DESC",
    "down": "f.ratio_pm ASC",
    "up": "f.ratio_pm DESC",
    "move": "f.move_bp ASC",
    "name": "ip.locale_name ASC",
    "vnum": "f.vnum ASC",
}
DDL_CHECK = ("SELECT COUNT(*) AS n FROM information_schema.TABLES WHERE TABLE_SCHEMA='player' AND TABLE_NAME IN "
             "('playerbot_market_fair','playerbot_market_fair_hist','playerbot_market_fair_pin')")


def yang(value):
    value = int(value or 0)
    return f"{value:,}".replace(",", " ")


def tables_ready(cur):
    cur.execute(DDL_CHECK)
    row = cur.fetchone()
    return bool(row) and int(row["n"] or 0) >= 3


def read_flags(cur):
    marks = ",".join(["%s"] * len(FLAG_NAMES))
    cur.execute(f"SELECT szName, lValue FROM player.quest WHERE dwPID=0 AND szName IN ({marks})", FLAG_NAMES)
    flags = {name: 0 for name in FLAG_NAMES}
    for row in cur.fetchall():
        flags[row["szName"]] = int(row["lValue"] or 0)
    return flags


def write_flag(cur, name, value):
    if name not in FLAG_NAMES:
        raise ValueError("Nieznana flaga.")
    cur.execute("REPLACE INTO player.quest (dwPID, szName, szState, lValue) VALUES (0, %s, '', %s)", (name, int(value)))


def parse_flag(spec, text):
    """The form's value of one flag: empty or 0 = the default (0 is stored), else an int in [lo, hi]."""
    name, label, default, lo, hi, _help = spec
    text = (text or "").replace(" ", "").strip()
    if text == "":
        return 0
    try:
        value = int(text)
    except ValueError:
        raise ValueError(f"„{label}”: liczba całkowita.")
    if value == 0:
        return 0
    if value < lo or value > hi:
        raise ValueError(f"„{label}”: od {lo} do {hi} (0 = domyślnie {default}).")
    return value


def parse_pin(form):
    """(pin_unit, min_pct, max_pct, note) of the pin form; ValueError with a Polish message."""
    def number(key, lo, hi, label):
        text = (form.get(key) or "").replace(" ", "").strip()
        if text == "":
            return 0
        try:
            value = int(text)
        except ValueError:
            raise ValueError(f"{label}: liczba całkowita.")
        if value != 0 and (value < lo or value > hi):
            raise ValueError(f"{label}: 0 (brak) albo od {lo} do {hi}.")
        return value
    pin = number("pin_unit", 1, 2000000000, "Przypięta cena")
    min_pct = number("min_pct", 10, 1000, "Dolna granica")
    max_pct = number("max_pct", 10, 1000, "Górna granica")
    if min_pct and max_pct and max_pct < min_pct:
        raise ValueError("Górna granica nie może być niższa od dolnej.")
    note = (form.get("note") or "").strip()[:80]
    return pin, min_pct, max_pct, note


def enrich(row, game_text):
    window = int(row.get("window_h") or 0) or 1
    row["name"] = game_text(row.get("locale_name")) if row.get("locale_name") else f"#{row['vnum']}"
    row["ratio_pct"] = round(int(row.get("ratio_pm") or 0) / 10.0, 1)
    row["min_pct"] = round(int(row.get("min_pm") or 0) / 10.0)
    row["max_pct"] = round(int(row.get("max_pm") or 0) / 10.0)
    row["src_label"] = SRC_LABELS.get(row.get("ref_src") or "", row.get("ref_src") or "?")
    row["sold_day"] = round(int(row.get("sold_w") or 0) * 24.0 / window, 1)
    cover = int(row.get("cover_h") or 0)
    row["cover_days"] = None if cover >= 999999 else round(cover / 24.0, 1)
    row["x"] = round(int(row.get("x_pm") or 0) / 1000.0, 2)
    row["conf"] = round(int(row.get("conf_pm") or 0) / 1000.0, 2)
    row["move_h"] = round(int(row.get("move_bp") or 0) / 100.0, 2)
    row["hi_share"] = (round(100.0 * int(row.get("sold_hi_6h") or 0) / int(row["sold_6h"]))
                       if int(row.get("sold_6h") or 0) else None)
    for key in ("ref_unit", "fair_unit", "pin_unit", "sale_mean", "p_min", "p25", "p50", "p75", "p_max", "stock"):
        row[key + "_text"] = yang(row.get(key))
    return row


def sparkline(points, key, width=640, height=120, pad=6):
    """An SVG polyline's points for the history of `key` (0 values skipped), and its min / max."""
    values = [(i, int(p.get(key) or 0)) for i, p in enumerate(points) if int(p.get(key) or 0) > 0]
    if len(values) < 2:
        return "", 0, 0
    lo = min(v for _, v in values)
    hi = max(v for _, v in values)
    span = max(1, hi - lo)
    n = max(1, len(points) - 1)
    coords = []
    for i, v in values:
        x = pad + (width - 2 * pad) * i / n
        y = height - pad - (height - 2 * pad) * (v - lo) / span
        coords.append(f"{x:.1f},{y:.1f}")
    return " ".join(coords), lo, hi


def install(app, db, login_required, csrf_token, game_text=lambda s: s or "", icon_url=None):
    from flask import abort, flash, redirect, render_template, request, session, url_for

    def check_csrf():
        expected = session.get("seban_update_csrf", "")
        if not expected or not secrets.compare_digest(request.form.get("ry_csrf", ""), expected):
            abort(400, "Odśwież stronę i spróbuj ponownie.")

    def save_pin(cur, vnum, form):
        pin, min_pct, max_pct, note = parse_pin(form)
        if not (pin or min_pct or max_pct):
            cur.execute("DELETE FROM player.playerbot_market_fair_pin WHERE vnum=%s", (vnum,))
            return "Przypięcie i granice usunięte – wraca automatyczna uczciwa cena (od najbliższego przeliczenia)."
        cur.execute("INSERT INTO player.playerbot_market_fair_pin (vnum, pin_unit, min_pct, max_pct, note, updated_at) "
                    "VALUES (%s, %s, %s, %s, %s, NOW()) ON DUPLICATE KEY UPDATE pin_unit=VALUES(pin_unit), "
                    "min_pct=VALUES(min_pct), max_pct=VALUES(max_pct), note=VALUES(note), updated_at=NOW()",
                    (vnum, pin, min_pct, max_pct, note))
        parts = []
        if pin:
            parts.append(f"cena przypięta: {yang(pin)} / szt.")
        if min_pct or max_pct:
            parts.append(f"granice: {min_pct or 'globalna'}–{max_pct or 'globalna'} % ceny bazowej")
        return "Zapisano (" + ", ".join(parts) + "). Gra przejmie to przy najbliższym przeliczeniu (do ~15 min)."

    @app.route("/economy/rynek", methods=["GET", "POST"])
    @login_required
    def rynek():
        with db() as con, con.cursor() as cur:
            if not tables_ready(cur):
                return render_template("rynek.html", missing=True, ry_csrf=csrf_token())
            if request.method == "POST":
                check_csrf()
                action = request.form.get("action", "")
                try:
                    if action == "flags":
                        values = {spec[0]: parse_flag(spec, request.form.get(spec[0])) for spec in FLAGS
                                  if spec[0] != "m2_bot_fairprice_off"}
                        for name, value in values.items():
                            write_flag(cur, name, value)
                        write_flag(cur, "m2_bot_fairprice_off", 1 if request.form.get("m2_bot_fairprice_off") == "1" else 0)
                        flash("Ustawienia zapisane – gra odczyta je w ciągu ~10 s (bez restartu).", "success")
                    elif action == "pin":
                        try:
                            vnum = int((request.form.get("vnum") or "").strip())
                        except ValueError:
                            raise ValueError("VNUM: liczba.")
                        if vnum <= 0:
                            raise ValueError("VNUM: liczba dodatnia.")
                        flash(save_pin(cur, vnum, request.form), "success")
                        if request.form.get("back") == "kind":
                            return redirect(url_for("rynek_kind", vnum=vnum))
                    else:
                        abort(400, "Nieznana akcja.")
                except ValueError as exc:
                    flash(str(exc), "error")
                return redirect(url_for("rynek"))
            flags = read_flags(cur)
            q = (request.args.get("q") or "").strip()
            sort = request.args.get("sort") or "stock"
            order = SORTS.get(sort, SORTS["stock"])
            where, args = [], []
            if q:
                if q.isdigit():
                    where.append("f.vnum=%s")
                    args.append(int(q))
                else:
                    where.append("ip.locale_name LIKE %s")
                    args.append(f"%{q}%")
            if request.args.get("pinned") == "1":
                where.append("(p.vnum IS NOT NULL)")
            sql = ("SELECT f.*, ip.locale_name, p.pin_unit AS p_pin, p.min_pct AS p_min_pct, p.max_pct AS p_max_pct, "
                   "p.note AS p_note FROM player.playerbot_market_fair f "
                   "LEFT JOIN player.item_proto ip ON ip.vnum=f.vnum "
                   "LEFT JOIN player.playerbot_market_fair_pin p ON p.vnum=f.vnum ")
            if where:
                sql += "WHERE " + " AND ".join(where) + " "
            sql += f"ORDER BY {order} LIMIT 400"
            cur.execute(sql, args)
            kinds = [enrich(r, game_text) for r in cur.fetchall()]
            cur.execute("SELECT COUNT(*) AS n, COALESCE(SUM(stock),0) AS units, COALESCE(SUM(sold_w),0) AS sold, "
                        "MAX(updated) AS updated, MAX(port) AS port, SUM(ratio_pm<1000) AS below, "
                        "SUM(ratio_pm>1000) AS above, SUM(pin_unit>0) AS pinned FROM player.playerbot_market_fair")
            summary = cur.fetchone() or {}
            cur.execute("SELECT UNIX_TIMESTAMP() AS now")
            now = int((cur.fetchone() or {}).get("now") or 0)
            age = now - int(summary.get("updated") or 0) if summary.get("updated") else None
            for k in kinds:
                k["icon"] = icon_url(k["vnum"]) if icon_url else None
            return render_template("rynek.html", missing=False, flags=flags, flag_specs=FLAGS, kinds=kinds,
                                   summary=summary, age=age, q=q, sort=sort, sorts=SORTS,
                                   pinned=request.args.get("pinned") == "1", yang=yang, ry_csrf=csrf_token())

    @app.route("/economy/rynek/<int:vnum>", methods=["GET"])
    @login_required
    def rynek_kind(vnum):
        with db() as con, con.cursor() as cur:
            if not tables_ready(cur):
                return redirect(url_for("rynek"))
            cur.execute("SELECT f.*, ip.locale_name FROM player.playerbot_market_fair f "
                        "LEFT JOIN player.item_proto ip ON ip.vnum=f.vnum WHERE f.vnum=%s", (vnum,))
            row = cur.fetchone()
            if row:
                row = enrich(row, game_text)
            else:
                cur.execute("SELECT vnum, locale_name FROM player.item_proto WHERE vnum=%s", (vnum,))
                proto = cur.fetchone()
                if not proto:
                    abort(404)
                row = {"vnum": vnum, "name": game_text(proto.get("locale_name")), "missing": True}
            cur.execute("SELECT * FROM player.playerbot_market_fair_pin WHERE vnum=%s", (vnum,))
            pin = cur.fetchone() or {}
            try:
                hours = max(6, min(24 * 90, int(request.args.get("h") or 168)))
            except ValueError:
                hours = 168
            cur.execute("SELECT * FROM player.playerbot_market_fair_hist WHERE vnum=%s AND hour >= "
                        "FLOOR(UNIX_TIMESTAMP()/3600) - %s ORDER BY hour", (vnum, hours))
            points = cur.fetchall()
            charts = {}
            for key in ("fair_unit", "p50", "sale_mean", "stock"):
                charts[key] = sparkline(points, key)
            max_sold = max([int(p.get("sold") or 0) for p in points] or [0])
            bars = []
            if points and max_sold > 0:
                n = len(points)
                for i, p in enumerate(points):
                    h = 60.0 * int(p.get("sold") or 0) / max_sold
                    bars.append((6 + 628.0 * i / max(1, n - 1), h))
            for p in points:
                p["when_text"] = datetime.fromtimestamp(int(p["hour"]) * 3600).strftime("%d.%m %H:00")
            return render_template("rynek_kind.html", kind=row, pin=pin, points=points[-48:][::-1], charts=charts,
                                   bars=bars, max_sold=max_sold, hours=hours, yang=yang,
                                   icon=icon_url(vnum) if icon_url else None, ry_csrf=csrf_token())

    return app
