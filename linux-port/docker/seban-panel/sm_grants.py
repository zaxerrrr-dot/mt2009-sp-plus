"""MT2009_PLUS_SM_GRANTS_V1: Smocze Monety (SM) paid to accounts at an interval.

The owner (28 October 2026): the admin picks how many SM accounts get, daily,
weekly or monthly, in tiers ("pakiety") - one set for players and a separate
one for bots, each from a level and optionally from a Champion level.

Where the SM go: account.account.cash. That is the balance the in-game shop
reads (CItemShopManager::GetPlayerAccountBalance runs "SELECT cash, cash_mark
FROM account" on every purchase, nothing is cached in the core), the web
ItemShop spends (Account::currencyColumn(1) == 'cash') and the panel's own
"Nadaj Smocze Monety" adds to. The core only ever changes it relatively
(cash = cash + n through HEADER_GD_REQUEST_CHARGE_CASH), so a relative UPDATE
here never overwrites a purchase made at the same moment. A player who is
online can spend the new SM at once; the number in an ItemShop window that is
already open is the one the core sent when it was opened, and is refreshed
the next time the shop sends the balance (reopening it, a purchase, relog).

Who is a bot: an account whose login starts with "playerbot_" - the same test
item_grants.candidates() and bot_identity() use for the account. Bot accounts
get only the bot tiers and every other account only the player tiers. A
player account must also be status 'OK' (a banned account gets nothing); bot
accounts are 'BLOCK' by design, so their status is not read.

Which tier: an account qualifies for a tier when ONE of its characters has
level >= min_level and conqueror_level >= min_champion_level (czempion.sql,
MT2009_PLUS_CHAMPION_V1), so it is judged by its highest qualifying
character. It gets only its ONE best tier over all intervals (the owner, 28
Oct 2026) - the highest Champion requirement, then the highest level
requirement, then the most SM per 30 days. A player account must have
played within the tier's interval (day / 7 / 30 days; active_days > 0
overrides it); bots need no login.

When: the current period in Europe/Warsaw time (SM_GRANT_TZ). Whoever
qualifies at a run and has not been paid in this period is paid now; a
period that passed without a run (the server was off) is not paid later.
account.sm_grant_log's unique (account_id, period, period_key) and the
payment in one transaction with its log row make every period paid once,
whatever restarts in between. A run pays at most per_run_limit accounts
(players first) in transactions of CHUNK, and runs again after RUN_AGAIN
seconds while something is still due, so 5000 bots at midnight are a few
short runs, not one long lock.
"""
import datetime
import os
import secrets
import sys
import time

try:
    from zoneinfo import ZoneInfo
except ImportError:  # pragma: no cover - python < 3.9
    ZoneInfo = None

TARGETS = (("player", "Gracze"), ("bot", "Boty"))
PERIODS = (("day", "Codziennie"), ("week", "Co tydzień"), ("month", "Co miesiąc"))
PERIOD_NOUN = {"day": "dzień", "week": "tydzień", "month": "miesiąc"}
MAX_AMOUNT, MAX_LEVEL, MAX_CHAMPION, MAX_ACTIVE_DAYS = 1_000_000, 250, 255, 365
MAX_PER_RUN, DEFAULT_PER_RUN = 5000, 500
CASH_MAX = 2147483647          # account.cash is a signed int(10)
CHUNK = 100                    # accounts per transaction
RUN_EVERY, RUN_AGAIN, FLAG_CHECK = 300, 20, 15
LOCK = "seban_sm_grants"
RUN_NOW_KEY, LAST_RUN_KEY, LAST_SUMMARY_KEY, LAST_ERROR_KEY = (
    "sm_grants_run_now", "sm_grants_last_run", "sm_grants_last_summary", "sm_grants_last_error")
BOT_ACCOUNT = "LEFT(a.login,10)='playerbot_'"
TZ_NAME = os.environ.get("SM_GRANT_TZ", "Europe/Warsaw")

# The same statements as mariadb/playerbot/sm_grants.sql (apply.sh runs that one every start).
DDL = (
    """CREATE TABLE IF NOT EXISTS account.sm_grant_config (
      id TINYINT UNSIGNED NOT NULL PRIMARY KEY,
      enabled TINYINT(1) NOT NULL DEFAULT 0,
      per_run_limit INT UNSIGNED NOT NULL DEFAULT 500,
      updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4""",
    "INSERT IGNORE INTO account.sm_grant_config (id, enabled, per_run_limit) VALUES (1, 0, 500)",
    """CREATE TABLE IF NOT EXISTS account.sm_grant_tier (
      id INT UNSIGNED NOT NULL AUTO_INCREMENT PRIMARY KEY,
      target ENUM('player','bot') NOT NULL,
      enabled TINYINT(1) NOT NULL DEFAULT 1,
      name VARCHAR(64) NOT NULL,
      min_level SMALLINT UNSIGNED NOT NULL DEFAULT 1,
      min_champion_level SMALLINT UNSIGNED NOT NULL DEFAULT 0,
      amount INT UNSIGNED NOT NULL,
      period ENUM('day','week','month') NOT NULL DEFAULT 'day',
      active_days SMALLINT UNSIGNED NOT NULL DEFAULT 0,
      created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
      updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
      KEY target_enabled (target, enabled)
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4""",
    """CREATE TABLE IF NOT EXISTS account.sm_grant_log (
      id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT PRIMARY KEY,
      account_id INT UNSIGNED NOT NULL,
      target ENUM('player','bot') NOT NULL,
      tier_id INT UNSIGNED NOT NULL,
      tier_name VARCHAR(64) NOT NULL DEFAULT '',
      amount INT UNSIGNED NOT NULL,
      period ENUM('day','week','month') NOT NULL,
      period_key VARCHAR(10) NOT NULL,
      granted_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
      UNIQUE KEY one_per_period (account_id, period, period_key),
      KEY period_key (period, period_key),
      KEY granted_at (granted_at)
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4""",
)


# ---- time ------------------------------------------------------------------

def local_now(now=None):
    """Now in the grant time zone (naive datetime)."""
    if now is not None:
        return now
    if ZoneInfo is not None:
        try:
            return datetime.datetime.now(ZoneInfo(TZ_NAME)).replace(tzinfo=None)
        except Exception:
            pass
    return datetime.datetime.now()


def period_key(period, now):
    if period == "day":
        return now.strftime("%Y-%m-%d")
    if period == "week":
        year, week, _ = now.isocalendar()
        return f"{year}-W{week:02d}"
    if period == "month":
        return now.strftime("%Y-%m")
    raise ValueError(period)


def next_period_start(period, now):
    day = datetime.datetime(now.year, now.month, now.day)
    if period == "day":
        return day + datetime.timedelta(days=1)
    if period == "week":
        return day + datetime.timedelta(days=7 - now.weekday())
    if period == "month":
        return datetime.datetime(now.year + (now.month == 12), now.month % 12 + 1, 1)
    raise ValueError(period)


# ---- data ------------------------------------------------------------------

def ensure(cur):
    for sql in DDL:
        cur.execute(sql)


def read_config(cur):
    cur.execute("SELECT enabled, per_run_limit FROM account.sm_grant_config WHERE id=1")
    row = cur.fetchone() or {}
    return {"enabled": bool(int(row.get("enabled") or 0)),
            "per_run_limit": int(row.get("per_run_limit") or DEFAULT_PER_RUN)}


def read_tiers(cur, enabled_only=False):
    cur.execute("SELECT id,target,enabled,name,min_level,min_champion_level,amount,period,active_days "
                "FROM account.sm_grant_tier" + (" WHERE enabled=1" if enabled_only else "")
                + " ORDER BY target, period, min_champion_level, min_level, amount, id")
    return [dict(row) for row in cur.fetchall()]


PERIOD_DAYS = {"day": 1, "week": 7, "month": 30}


def tier_rank(tier):
    """Sort key, best first: the highest Champion requirement, then the highest level requirement, then the most SM
    per 30 days (a daily 10 beats a monthly 200), across all intervals (the owner, 28 Oct 2026: one best tier)."""
    per_month = int(tier["amount"]) * 30 // PERIOD_DAYS.get(tier["period"], 30)
    return (-int(tier["min_champion_level"]), -int(tier["min_level"]), -per_month, int(tier["id"]))


def login_days(tier):
    """A player must have played within the tier's interval (the owner, 28 Oct 2026: monthly - the last month,
    weekly - the last week); active_days > 0 overrides it. Bots: active_days only."""
    days = int(tier.get("active_days") or 0)
    if days > 0:
        return days
    return PERIOD_DAYS.get(tier["period"], 30) if tier["target"] == "player" else 0


def qualifying_sql(tier):
    """The accounts that meet one tier, with their best qualifying character."""
    conditions = ["p.level >= %s"]
    params = [int(tier["min_level"])]
    if int(tier["min_champion_level"]) > 0:
        conditions.append("p.conqueror_level >= %s")
        params.append(int(tier["min_champion_level"]))
    if tier["target"] == "bot":
        conditions.append(BOT_ACCOUNT)
    else:
        conditions.append("NOT " + BOT_ACCOUNT)
        conditions.append("a.status = 'OK'")
    if login_days(tier) > 0:
        conditions.append("a.last_play >= NOW() - INTERVAL %s DAY")
        params.append(login_days(tier))
    champion = "MAX(p.conqueror_level)" if int(tier["min_champion_level"]) > 0 else "0"
    sql = ("SELECT p.account_id, MAX(p.level) AS level, " + champion + " AS champion "
           "FROM player.player p JOIN account.account a ON a.id = p.account_id WHERE "
           + " AND ".join(conditions) + " GROUP BY p.account_id")
    return sql, params


def assign(tiers, qualifying):
    """{(period, account_id): tier} - the ONE best tier of each account over
    all intervals (tier_rank). qualifying maps tier id -> iterable of account ids."""
    best = {}
    for tier in sorted(tiers, key=tier_rank):
        for account_id in qualifying.get(tier["id"], ()):
            best.setdefault(int(account_id), tier)
    return {(tier["period"], account_id): tier for account_id, tier in best.items()}


def plan(cur, now=None, tiers=None):
    """What a run would do now. Read-only."""
    now = local_now(now)
    if tiers is None:
        tiers = read_tiers(cur, enabled_only=True)
    keys = {period: period_key(period, now) for period, _ in PERIODS}
    qualifying, details = {}, {}
    for tier in tiers:
        sql, params = qualifying_sql(tier)
        cur.execute(sql, params)
        found = cur.fetchall()
        qualifying[tier["id"]] = [int(row["account_id"]) for row in found]
        for row in found:
            details[(tier["id"], int(row["account_id"]))] = row
    paid = {}
    for period, key in keys.items():
        if any(t["period"] == period for t in tiers):
            cur.execute("SELECT account_id FROM account.sm_grant_log WHERE period=%s AND period_key=%s", (period, key))
            paid[period] = {int(row["account_id"]) for row in cur.fetchall()}
    best = assign(tiers, qualifying)
    per_tier = {t["id"]: {"tier": t, "eligible": 0, "paid": 0, "due": 0, "due_sm": 0} for t in tiers}
    due = []
    for (period, account_id), tier in best.items():
        stats = per_tier[tier["id"]]
        stats["eligible"] += 1
        if account_id in paid.get(period, ()):
            stats["paid"] += 1
        else:
            stats["due"] += 1
            stats["due_sm"] += int(tier["amount"])
            due.append({"account_id": account_id, "tier": tier, "period": period, "period_key": keys[period],
                        "detail": details.get((tier["id"], account_id), {})})
    # Players first, then the bots; inside each the oldest account first.
    due.sort(key=lambda d: (d["tier"]["target"] != "player", d["account_id"], d["period"]))
    return {"now": now, "keys": keys, "tiers": tiers, "per_tier": per_tier, "due": due,
            "due_sm": sum(d["tier"]["amount"] for d in due),
            "next": {period: next_period_start(period, now) for period, _ in PERIODS}}


def pay(con, items):
    """Pay a list of plan()'s due entries, CHUNK per transaction. Returns
    (paid entries, skipped count)."""
    done, skipped = [], 0
    with con.cursor() as cur:
        for start in range(0, len(items), CHUNK):
            chunk = items[start:start + CHUNK]
            con.begin()
            try:
                for item in chunk:
                    tier = item["tier"]
                    amount = int(tier["amount"])
                    cur.execute("INSERT IGNORE INTO account.sm_grant_log "
                                "(account_id,target,tier_id,tier_name,amount,period,period_key) "
                                "VALUES (%s,%s,%s,%s,%s,%s,%s)",
                                (item["account_id"], tier["target"], tier["id"], tier["name"][:64], amount,
                                 item["period"], item["period_key"]))
                    if cur.rowcount != 1:
                        skipped += 1          # paid meanwhile (another run, or the panel's "now")
                        continue
                    log_id = cur.lastrowid
                    cur.execute("UPDATE account.account SET cash = COALESCE(cash,0) + %s "
                                "WHERE id=%s AND COALESCE(cash,0) <= %s", (amount, item["account_id"], CASH_MAX - amount))
                    if cur.rowcount != 1:     # account gone, or at the column's limit
                        cur.execute("DELETE FROM account.sm_grant_log WHERE id=%s", (log_id,))
                        skipped += 1
                        continue
                    done.append(item)
                con.commit()
            except Exception:
                con.rollback()
                raise
    return done, skipped


def summary_text(result):
    if result.get("disabled"):
        return "wyłączone"
    text = f"wypłacono {result['paid_accounts']} kontom {result['paid_sm']} SM"
    if result.get("remaining"):
        text += f", czeka jeszcze {result['remaining']}"
    if result.get("skipped"):
        text += f", pominięto {result['skipped']}"
    return text


def stamp(cur, key, value):
    cur.execute("INSERT INTO player.web_seban_settings (name,value) VALUES (%s,%s) "
                "ON DUPLICATE KEY UPDATE value=VALUES(value)", (key, str(value)[:255]))


def run(con, now=None, dry_run=False, limit=None):
    """One run. dry_run reads only; otherwise it pays what is due (when the
    switch is on) under a database lock, so the panel's "pay now" and the
    worker never pay twice at once (the unique key would stop it anyway)."""
    with con.cursor() as cur:
        config = read_config(cur)
        if not config["enabled"] and not dry_run:
            return {"disabled": True, "paid_accounts": 0, "paid_sm": 0, "remaining": 0, "skipped": 0}
        limit = config["per_run_limit"] if limit is None else limit
        if dry_run:
            planned = plan(cur, now)
            return {"dry_run": True, "plan": planned, "would_pay": planned["due"][:limit],
                    "paid_accounts": 0, "paid_sm": 0, "remaining": len(planned["due"]), "skipped": 0}
        cur.execute("SELECT GET_LOCK(%s,0) AS acquired", (LOCK,))
        if (cur.fetchone() or {}).get("acquired") != 1:
            return {"busy": True, "paid_accounts": 0, "paid_sm": 0, "remaining": 0, "skipped": 0}
        try:
            planned = plan(cur, now)
            batch = planned["due"][:limit]
            done, skipped = pay(con, batch)
            per_tier = {}
            for item in done:
                per_tier[item["tier"]["name"]] = per_tier.get(item["tier"]["name"], 0) + 1
            result = {"paid_accounts": len(done), "paid_sm": sum(int(i["tier"]["amount"]) for i in done),
                      "remaining": len(planned["due"]) - len(batch), "skipped": skipped, "per_tier": per_tier}
            if done:
                print(f"[sm-grants] {summary_text(result)} " + ", ".join(f"{k}: {v}" for k, v in per_tier.items()),
                      flush=True)
            return result
        finally:
            cur.execute("SELECT RELEASE_LOCK(%s)", (LOCK,))


# ---- worker (called from item_grants.py's loop) -----------------------------

_state = {"next_run": 0.0, "next_flag": 0.0}


def worker_step(db):
    """Called on every tick of the seban-item-grants loop (3 s). Runs every
    RUN_EVERY seconds, after RUN_AGAIN while something is still due, and at
    once when the panel asked ("Wypłać teraz")."""
    now = time.time()
    if now < _state["next_run"] and now < _state["next_flag"]:
        return
    with db() as con:
        with con.cursor() as cur:
            if now < _state["next_run"]:
                _state["next_flag"] = now + FLAG_CHECK
                cur.execute("SELECT value FROM player.web_seban_settings WHERE name=%s", (RUN_NOW_KEY,))
                row = cur.fetchone()
                if not row or row.get("value") in ("", "0", None):
                    return
            ensure(cur)
            stamp(cur, RUN_NOW_KEY, "0")
        error = ""
        try:
            result = run(con)
        except Exception as exc:
            error = f"{type(exc).__name__}: {exc}"
            result = None
            print(f"[sm-grants] {error}", flush=True)
        with con.cursor() as cur:
            stamp(cur, LAST_RUN_KEY, int(time.time()))
            stamp(cur, LAST_ERROR_KEY, error)
            if result is not None and not result.get("busy"):
                stamp(cur, LAST_SUMMARY_KEY, summary_text(result))
    again = result is not None and result.get("remaining", 0) > 0
    _state["next_run"] = time.time() + (RUN_AGAIN if again else RUN_EVERY)
    _state["next_flag"] = time.time() + FLAG_CHECK


# ---- panel -----------------------------------------------------------------

def tier_from_form(form, number):
    target = form.get("target", "")
    if target not in dict(TARGETS):
        raise ValueError("Nieprawidłowy rodzaj kont.")
    period = form.get("period", "")
    if period not in dict(PERIODS):
        raise ValueError("Nieprawidłowy okres.")
    name = (form.get("name") or "").strip()[:64]
    if not name:
        raise ValueError("Podaj nazwę pakietu.")
    tier = {
        "target": target, "period": period, "name": name,
        "enabled": 1 if form.get("enabled") == "1" else 0,
        "min_level": number(form.get("min_level"), "Minimalny poziom", MAX_LEVEL),
        "min_champion_level": number(form.get("min_champion_level") or "0", "Minimalny poziom Czempiona", MAX_CHAMPION),
        "amount": number(form.get("amount"), "Ilość SM", MAX_AMOUNT),
        "active_days": number(form.get("active_days") or "0", "Aktywność (dni)", MAX_ACTIVE_DAYS),
    }
    if tier["amount"] < 1:
        raise ValueError("Ilość SM: co najmniej 1.")
    if tier["min_level"] < 1:
        raise ValueError("Minimalny poziom: co najmniej 1.")
    return tier


def install(app, db, login_required, csrf_token):
    from flask import abort, flash, redirect, render_template, request, session, url_for

    def number(raw, label, maximum):
        raw = (raw or "").strip()
        try:
            value = int(raw)
        except ValueError:
            raise ValueError(f"{label}: wpisz liczbę całkowitą.")
        if not 0 <= value <= maximum:
            raise ValueError(f"{label}: dozwolony zakres to 0–{maximum}.")
        return value

    @app.route("/manage/sm-grants", methods=["GET", "POST"])
    @login_required
    def manage_sm_grants():
        with db() as con, con.cursor() as cur:
            ensure(cur)
            if request.method == "POST":
                expected = session.get("seban_update_csrf", "")
                if not expected or not secrets.compare_digest(request.form.get("sm_csrf", ""), expected):
                    abort(400, "Odśwież stronę i spróbuj ponownie.")
                action = request.form.get("action", "")
                anchor = ""
                try:
                    if action == "config":
                        limit = number(request.form.get("per_run_limit") or str(DEFAULT_PER_RUN),
                                       "Kont na jedno uruchomienie", MAX_PER_RUN)
                        enabled = 1 if request.form.get("enabled") == "1" else 0
                        cur.execute("UPDATE account.sm_grant_config SET enabled=%s, per_run_limit=%s WHERE id=1",
                                    (enabled, max(1, limit)))
                        flash("Nadawanie SM włączone." if enabled else "Nadawanie SM wyłączone.", "success")
                    elif action == "save_tier":
                        tier = tier_from_form(request.form, number)
                        anchor = "pakiety-" + tier["target"]
                        tier_id = request.form.get("id", "")
                        columns = ("target", "enabled", "name", "min_level", "min_champion_level", "amount", "period",
                                   "active_days")
                        if tier_id:
                            cur.execute("UPDATE account.sm_grant_tier SET " + ",".join(f"{c}=%s" for c in columns)
                                        + " WHERE id=%s", tuple(tier[c] for c in columns) + (int(tier_id),))
                            flash(f"Zapisano pakiet „{tier['name']}”.", "success")
                        else:
                            cur.execute("INSERT INTO account.sm_grant_tier (" + ",".join(columns) + ") VALUES ("
                                        + ",".join(["%s"] * len(columns)) + ")", tuple(tier[c] for c in columns))
                            flash(f"Dodano pakiet „{tier['name']}”.", "success")
                    elif action == "delete_tier":
                        cur.execute("DELETE FROM account.sm_grant_tier WHERE id=%s", (int(request.form.get("id", "0")),))
                        flash("Usunięto pakiet. Historia wypłat zostaje.", "success")
                    elif action == "run_now":
                        stamp(cur, RUN_NOW_KEY, "1")
                        flash("Worker wypłaci należne SM w ciągu kilkunastu sekund (jeśli nadawanie jest włączone).",
                              "success")
                    else:
                        abort(400, "Nieznana akcja.")
                except ValueError as exc:
                    flash(str(exc), "error")
                return redirect(url_for("manage_sm_grants", _anchor=anchor or None))
            config = read_config(cur)
            tiers = read_tiers(cur)
            preview_error = ""
            try:
                planned = plan(cur, tiers=[t for t in tiers if t["enabled"]])
            except Exception as exc:  # e.g. conqueror_level missing on an old database
                planned, preview_error = None, f"{type(exc).__name__}: {exc}"
            sample = []
            if planned:
                players = [d for d in planned["due"] if d["tier"]["target"] == "player"][:50]
                ids = [d["account_id"] for d in players]
                logins = {}
                if ids:
                    cur.execute("SELECT id,login FROM account.account WHERE id IN (" + ",".join(["%s"] * len(ids)) + ")", ids)
                    logins = {int(r["id"]): r["login"] for r in cur.fetchall()}
                for d in players:
                    sample.append({"account_id": d["account_id"], "login": logins.get(d["account_id"], "?"),
                                   "tier": d["tier"], "level": d["detail"].get("level"),
                                   "champion": d["detail"].get("champion")})
            cur.execute("""SELECT l.*, a.login FROM account.sm_grant_log l
                           LEFT JOIN account.account a ON a.id=l.account_id ORDER BY l.id DESC LIMIT 200""")
            history = cur.fetchall()
            cur.execute("""SELECT target, COUNT(*) AS n, COALESCE(SUM(amount),0) AS sm FROM account.sm_grant_log
                           WHERE granted_at >= NOW() - INTERVAL 30 DAY GROUP BY target""")
            totals = {r["target"]: r for r in cur.fetchall()}
            cur.execute("SELECT name,value,UNIX_TIMESTAMP(updated_at) AS at FROM player.web_seban_settings "
                        "WHERE name IN (%s,%s,%s,%s,%s)",
                        (LAST_RUN_KEY, LAST_SUMMARY_KEY, LAST_ERROR_KEY, RUN_NOW_KEY, "item_grants_heartbeat"))
            stamps = {r["name"]: r["value"] for r in cur.fetchall()}
        def age(key):
            try:
                return max(0, int(time.time()) - int(stamps.get(key)))
            except (TypeError, ValueError):
                return None
        worker = {"heartbeat_age": age("item_grants_heartbeat"), "last_run_age": age(LAST_RUN_KEY),
                  "summary": stamps.get(LAST_SUMMARY_KEY, ""), "error": stamps.get(LAST_ERROR_KEY, ""),
                  "run_now": stamps.get(RUN_NOW_KEY) == "1"}
        worker["alive"] = worker["heartbeat_age"] is not None and worker["heartbeat_age"] <= 30
        return render_template("sm_grants.html", config=config, tiers=tiers, plan=planned, sample=sample,
                               history=history, totals=totals, worker=worker, preview_error=preview_error,
                               targets=TARGETS, periods=PERIODS, period_noun=PERIOD_NOUN, tz_name=TZ_NAME,
                               sm_csrf=csrf_token(), limits={"amount": MAX_AMOUNT, "level": MAX_LEVEL,
                               "champion": MAX_CHAMPION, "active": MAX_ACTIVE_DAYS, "per_run": MAX_PER_RUN})


# ---- command line: python sm_grants.py --dry-run ----------------------------

def print_plan(result, out=sys.stdout):
    planned = result["plan"]
    out.write(f"SM grants dry run at {planned['now']:%Y-%m-%d %H:%M} ({TZ_NAME}); periods "
              + ", ".join(f"{p}={k}" for p, k in planned["keys"].items()) + "\n")
    for stats in planned["per_tier"].values():
        tier = stats["tier"]
        out.write(f"  [{tier['target']}] {tier['name']} ({tier['period']}, lv>={tier['min_level']}, "
                  f"C>={tier['min_champion_level']}, {tier['amount']} SM): best tier of {stats['eligible']} accounts, "
                  f"already paid {stats['paid']}, due {stats['due']} = {stats['due_sm']} SM\n")
    out.write(f"  due now: {len(planned['due'])} accounts, {planned['due_sm']} SM; "
              f"one run pays {len(result['would_pay'])}\n")


if __name__ == "__main__":
    if "--dry-run" not in sys.argv:
        sys.exit("usage: python sm_grants.py --dry-run   (the worker runs inside item_grants.py)")
    from app import db as app_db
    with app_db() as connection:
        print_plan(run(connection, dry_run=True))
