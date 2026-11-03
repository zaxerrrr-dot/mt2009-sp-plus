"""MT2009_PLUS_POTEGA_MADROSCI_V1: "Potęga mądrości" - Uriel's experience bonus.

The owner (3 November 2026, the pl-wiki's server pages): "Spytaj Uriela o
potęgę mądrości, aby otrzymać bonus PD w zależności od przedziału poziomów" -
levels 41-80 +25%, 81-100 +50%, 101-120 +100%, Champion 1-10 +125%,
Champion 11-30 +100%, each for 4 hours; the village guard tells the table.

How it runs (nothing here talks to the game directly):

* whether the event runs is the event flag potega_madrosci, which the
  in-game event manager writes for the events planner's kind "potega"
  (playerbot_ingame_events.h) - so it is scheduled in the planner like any
  other event, and this page's "Włącz teraz" / "Wyłącz" write the planner's
  own "now" line (read_events / write_events of app.py);
* the ranges, the time and the bots' share are player.potega_madrosci_tier /
  _config (mariadb/playerbot/potega_madrosci.sql). The quest
  (potega_madrosci.quest) reads them on every talk with Uriel or the guard
  and the cores (playerbot_potega.h, the bots) every minute - a save here is
  live at once, no restart.

A Champion (Champion level 1+) is judged by the Champion ranges only, anybody
else by the level ranges; the first enabled range (by kind, from, to) that
holds the level gives the percent. The bonus is the affect 730 on point 127
(POINT_RAMADAN_CANDY_BONUS_EXP): added to the experience like the server's
rates, uncapped, counted by the Champion bar and the bonus window's PD line.

The rules are pure and unit-tested (test_potega_madrosci.py); install() takes
the panel's functions it needs, so this module imports nothing of app.py.
"""
import secrets
import time

KIND = "potega"
WIKI_TIERS = ((0, 41, 80, 25), (0, 81, 100, 50), (0, 101, 120, 100), (1, 1, 10, 125), (1, 11, 30, 100))
MAX_LEVEL, MAX_CHAMPION, MAX_PCT, MAX_MINUTES = 250, 255, 1000, 10080
DEFAULT_MINUTES, DEFAULT_BOT_SHARE = 240, 60
NOW_MINUTES = (60, 120, 240, 360, 720, 1440, 2880, 4320, 7200, 10080)

# The same statements as mariadb/playerbot/potega_madrosci.sql (apply.sh runs that one every start), so a panel
# started before it ran still finds its tables. The wiki's table only with the settings row's first creation.
DDL = (
    """CREATE TABLE IF NOT EXISTS player.potega_madrosci_tier (
      id INT UNSIGNED NOT NULL AUTO_INCREMENT PRIMARY KEY,
      enabled TINYINT(1) NOT NULL DEFAULT 1,
      champion TINYINT(1) NOT NULL DEFAULT 0,
      lvl_from SMALLINT UNSIGNED NOT NULL,
      lvl_to SMALLINT UNSIGNED NOT NULL,
      pct SMALLINT UNSIGNED NOT NULL,
      updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
      KEY champion_from (champion, lvl_from)
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4""",
    """INSERT INTO player.potega_madrosci_tier (champion, lvl_from, lvl_to, pct)
      SELECT * FROM (SELECT 0 AS c, 41 AS f, 80 AS t, 25 AS p UNION ALL SELECT 0, 81, 100, 50
                     UNION ALL SELECT 0, 101, 120, 100 UNION ALL SELECT 1, 1, 10, 125 UNION ALL SELECT 1, 11, 30, 100) AS wiki
      WHERE NOT EXISTS (SELECT 1 FROM information_schema.TABLES
                        WHERE TABLE_SCHEMA = 'player' AND TABLE_NAME = 'potega_madrosci_config')""",
    """CREATE TABLE IF NOT EXISTS player.potega_madrosci_config (
      id TINYINT UNSIGNED NOT NULL PRIMARY KEY,
      minutes INT UNSIGNED NOT NULL DEFAULT 240,
      bots TINYINT(1) NOT NULL DEFAULT 1,
      bot_share TINYINT UNSIGNED NOT NULL DEFAULT 60,
      updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4""",
    "INSERT IGNORE INTO player.potega_madrosci_config (id, minutes, bots, bot_share) VALUES (1, 240, 1, 60)",
)


# ---- the rules (pure) ---------------------------------------------------------

def number(raw, label, low, high):
    raw = str(raw if raw is not None else "").strip()
    try:
        value = int(raw)
    except ValueError:
        raise ValueError(f"{label}: wpisz liczbę całkowitą.")
    if not low <= value <= high:
        raise ValueError(f"{label}: dozwolony zakres to {low}–{high}.")
    return value


def tier_from_form(form):
    """One range from the page's form; ValueError with a Polish message."""
    champion = 1 if str(form.get("champion", "0")) == "1" else 0
    top = MAX_CHAMPION if champion else MAX_LEVEL
    label = "Poziom Czempiona" if champion else "Poziom"
    lvl_from = number(form.get("lvl_from"), f"{label} od", 1, top)
    lvl_to = number(form.get("lvl_to"), f"{label} do", 1, top)
    if lvl_to < lvl_from:
        raise ValueError(f"{label}: „do” nie może być mniejsze niż „od”.")
    pct = number(form.get("pct"), "Bonus PD (%)", 1, MAX_PCT)
    return {"champion": champion, "lvl_from": lvl_from, "lvl_to": lvl_to, "pct": pct,
            "enabled": 1 if form.get("enabled") == "1" else 0}


def config_from_form(form):
    return {"minutes": number(form.get("minutes"), "Czas bonusu (minuty)", 1, MAX_MINUTES),
            "bots": 1 if form.get("bots") == "1" else 0,
            "bot_share": number(form.get("bot_share"), "Udział botów (%)", 0, 100)}


def ordered(tiers):
    """The order the quest and the cores read them in."""
    return sorted(tiers, key=lambda t: (int(t["champion"]), int(t["lvl_from"]), int(t["lvl_to"]), int(t.get("id") or 0)))


def pct_for(tiers, level, champion_level=0):
    """The quest's rule: a Champion by the Champion ranges only; the first enabled range that holds the level."""
    champion = 1 if champion_level >= 1 else 0
    value = champion_level if champion else level
    for t in ordered(tiers):
        if not int(t.get("enabled", 1)):
            continue
        if int(t["champion"]) == champion and int(t["lvl_from"]) <= value <= int(t["lvl_to"]):
            return int(t["pct"])
    return 0


def overlaps(tiers):
    """Pairs of enabled ranges of one kind that share levels (the earlier wins in the game) - the page warns."""
    found = []
    live = [t for t in ordered(tiers) if int(t.get("enabled", 1))]
    for i, a in enumerate(live):
        for b in live[i + 1:]:
            if int(a["champion"]) == int(b["champion"]) and int(b["lvl_from"]) <= int(a["lvl_to"]):
                found.append((a, b))
    return found


def range_text(t):
    return f"{'Czempion' if int(t['champion']) else 'Poziom'} {int(t['lvl_from'])}–{int(t['lvl_to'])}"


def minutes_text(minutes):
    minutes = int(minutes)
    hours, rest = divmod(minutes, 60)
    if hours and rest:
        return f"{hours} godz. {rest} min"
    return f"{hours} godz." if hours else f"{rest} min"


def now_line(nows, kind=KIND):
    """The planner's "now" item of the kind, None when there is none (or it has ended)."""
    item = nows.get(kind)
    if item and int(item.get("until", 0)) > time.time():
        return item
    return None


# ---- the database -------------------------------------------------------------

def ensure(cur):
    for sql in DDL:
        cur.execute(sql)


def read_config(cur):
    cur.execute("SELECT minutes, bots, bot_share FROM player.potega_madrosci_config WHERE id=1")
    row = cur.fetchone() or {}
    return {"minutes": int(row.get("minutes") or DEFAULT_MINUTES), "bots": int(row.get("bots") or 0),
            "bot_share": int(row.get("bot_share") if row.get("bot_share") is not None else DEFAULT_BOT_SHARE)}


def read_tiers(cur):
    cur.execute("SELECT id, enabled, champion, lvl_from, lvl_to, pct FROM player.potega_madrosci_tier")
    return ordered([dict(row) for row in cur.fetchall()])


# ---- the page -------------------------------------------------------------------

def install(app, db, login_required, csrf_token, read_events, write_events, read_events_status, minutes_label):
    from flask import abort, flash, redirect, render_template, request, session, url_for

    @app.route("/events/potega-madrosci", methods=["GET", "POST"])
    @login_required
    def manage_potega_madrosci():
        with db() as con, con.cursor() as cur:
            ensure(cur)
            if request.method == "POST":
                expected = session.get("seban_update_csrf", "")
                if not expected or not secrets.compare_digest(request.form.get("pm_csrf", ""), expected):
                    abort(400, "Odśwież stronę i spróbuj ponownie.")
                action = request.form.get("action", "")
                anchor = ""
                try:
                    if action == "config":
                        cfg = config_from_form(request.form)
                        cur.execute("UPDATE player.potega_madrosci_config SET minutes=%s, bots=%s, bot_share=%s WHERE id=1",
                                    (cfg["minutes"], cfg["bots"], cfg["bot_share"]))
                        flash(f"Zapisano: bonus na {minutes_text(cfg['minutes'])}"
                              f"{', boty biorą bonus' if cfg['bots'] else ', boty bez bonusu'}. Działa od następnej rozmowy.",
                              "success")
                        anchor = "ustawienia"
                    elif action == "save_tier":
                        tier = tier_from_form(request.form)
                        anchor = "przedzialy"
                        columns = ("enabled", "champion", "lvl_from", "lvl_to", "pct")
                        tier_id = request.form.get("id", "")
                        if tier_id:
                            cur.execute("UPDATE player.potega_madrosci_tier SET " + ",".join(f"{c}=%s" for c in columns)
                                        + " WHERE id=%s", tuple(tier[c] for c in columns) + (int(tier_id),))
                            flash(f"Zapisano przedział {range_text(tier)}: +{tier['pct']}% PD.", "success")
                        else:
                            cur.execute("INSERT INTO player.potega_madrosci_tier (" + ",".join(columns) + ") VALUES ("
                                        + ",".join(["%s"] * len(columns)) + ")", tuple(tier[c] for c in columns))
                            flash(f"Dodano przedział {range_text(tier)}: +{tier['pct']}% PD.", "success")
                    elif action == "delete_tier":
                        cur.execute("DELETE FROM player.potega_madrosci_tier WHERE id=%s", (int(request.form.get("id", "0")),))
                        flash("Usunięto przedział.", "success")
                        anchor = "przedzialy"
                    elif action == "wiki":
                        cur.execute("DELETE FROM player.potega_madrosci_tier")
                        cur.executemany("INSERT INTO player.potega_madrosci_tier (champion, lvl_from, lvl_to, pct) "
                                        "VALUES (%s,%s,%s,%s)", WIKI_TIERS)
                        cur.execute("UPDATE player.potega_madrosci_config SET minutes=%s WHERE id=1", (DEFAULT_MINUTES,))
                        flash("Przywrócono tabelę z wiki (5 przedziałów, 4 godziny).", "success")
                        anchor = "przedzialy"
                    elif action in ("now", "stop"):
                        rows, nows = read_events()
                        if action == "now":
                            minutes = number(request.form.get("minutes"), "Czas eventu", 5, 10080)
                            started = int(time.time())
                            nows[KIND] = {"kind": KIND, "until": started + minutes * 60, "value": 0, "map": 0,
                                          "since": started}
                            flash(f"Potęga mądrości włączona na {minutes_label(minutes)}. Gra odczyta to w ciągu kilku sekund.",
                                  "success")
                        else:
                            nows.pop(KIND, None)
                            flash("Natychmiastowa Potęga mądrości wyłączona (wiersze harmonogramu zostają).", "success")
                        write_events(rows, nows)
                        anchor = "wlacznik"
                    else:
                        abort(400, "Nieznana akcja.")
                except ValueError as exc:
                    flash(str(exc), "error")
                return redirect(url_for("manage_potega_madrosci", _anchor=anchor or None))
            config = read_config(cur)
            tiers = read_tiers(cur)
            # Who holds the bonus now (saved affects - an online character's are written at its save).
            try:
                cur.execute("SELECT COUNT(*) AS n, COALESCE(SUM(LEFT(acc.login,10)='playerbot_'), 0) AS bots "
                            "FROM player.affect a JOIN player.player p ON p.id=a.dwPID "
                            "LEFT JOIN account.account acc ON acc.id=p.account_id WHERE a.bType=730")
                holders = cur.fetchone() or {}
            except Exception:
                holders = {}
        rows, nows = read_events()
        plan = [r for r in rows if r.get("kind") == KIND]
        status = (read_events_status() or {}).get(KIND, {})
        examples = [(f"Poziom {lv}", pct_for(tiers, lv)) for lv in (30, 41, 80, 81, 100, 101, 120)] + \
                   [(f"Czempion {c}", pct_for(tiers, 120, c)) for c in (1, 10, 11, 30, 31)]
        now = now_line(nows)
        now_text = time.strftime("%d.%m %H:%M", time.localtime(int(now["until"]))) if now else ""
        return render_template("potega_madrosci.html", config=config, tiers=tiers, overlaps=overlaps(tiers),
                               plan=plan, now=now, now_text=now_text, status=status, examples=examples,
                               holders=holders, now_minutes=NOW_MINUTES, minutes_label=minutes_label,
                               minutes_text=minutes_text, range_text=range_text, pm_csrf=csrf_token(),
                               limits={"level": MAX_LEVEL, "champion": MAX_CHAMPION, "pct": MAX_PCT,
                                       "minutes": MAX_MINUTES})
