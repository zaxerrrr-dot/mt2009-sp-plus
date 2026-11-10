"""MT2009_PLUS_NAJEMNICY_V1: "Najemnicy" - a player's hired party (the owner, 8 November 2026,
/opt/metin2/cache/yohara/najemnicy-plan.md). Stage 1's panel page: who has which mercenaries, the vaults, the unlocks
and the switches. Nothing here talks to the game directly; the tables are mariadb/playerbot/najemnicy.sql, the game's
side playerbot_najemnicy.h ("/najemnicy", the quest najemnicy.quest).

* the switches: event flags as player.quest rows with dwPID 0, which the game reads every 10 s -
  m2_najemnicy_off (1 = nobody summons, the summoned leave), m2_najemnicy_free_unlock (1 = every character 80+ is
  unlocked, for the tests), m2_najemnicy_price_h (one summoned mercenary's fee an hour; 0 = 5 000 000);
* a character's Kolekcjoner Najemnikow tasks done (player.najemnicy_unlock.tasks, 0..6 - stage 1's unlock until the
  collector exists) - by name; the game reads the row when the player opens the letter and copies a higher count onto
  the quest flag najemnicy.tasks. Slots = the tasks done whose level the character has: 1 + 80 -> 2, 2 + 85 -> 3,
  3 + 90 -> 4, 4 + 95 -> 5, 5 + 100 -> 6, 6 + 105 -> 7;
* the list: the mercenaries per player (slot, class, path, name, created, retired), the vaults (balance, paid in,
  paid as the fee), the unlocks.
"""
import secrets

from kolekcjoner_config import read_tiers

CLASSES = {0: "Wojownik", 1: "Ninja", 2: "Sura", 3: "Szaman"}
PATHS = {(0, 1): "Ciało", (0, 2): "Mental", (1, 1): "Skrytobójca", (1, 2): "Łucznik",
         (2, 1): "Broń", (2, 2): "Czarna Magia", (3, 1): "Smok", (3, 2): "Leczenie"}
FLAGS = ("m2_najemnicy_off", "m2_najemnicy_free_unlock", "m2_najemnicy_price_h")
DEFAULT_PRICE_H = 5000000
MAX_TASKS = 16	# the game's clamp (MT2009_PLUS_KOLEKCJONER_CONFIG_V1: the panel may add tasks; the tiers decide the slots)


def slots_for(tasks, level, tiers=None):
    """The game's GetNajemnicySlots over the tier table (player.najemnicy_kolekcjoner_tiers, MT2009_PLUS_KOLEKCJONER_CONFIG_V1:
    the n-th completed task -> slots from a level); the built-in 1 + 80 -> 2 ... 6 + 105 -> 7 when it is empty/missing."""
    from kolekcjoner_config import slots_for_tiers
    return slots_for_tiers(tiers, tasks, level)
DDL_CHECK = "SELECT 1 FROM information_schema.TABLES WHERE TABLE_SCHEMA='player' AND TABLE_NAME='najemnicy'"


def tables_ready(cur):
    cur.execute(DDL_CHECK)
    return bool(cur.fetchone())


def read_flags(cur):
    cur.execute("SELECT szName, lValue FROM player.quest WHERE dwPID=0 AND szName IN (%s,%s,%s)", FLAGS)
    flags = {name: 0 for name in FLAGS}
    for row in cur.fetchall():
        flags[row["szName"]] = int(row["lValue"] or 0)
    return flags


def write_flag(cur, name, value):
    if name not in FLAGS:
        raise ValueError("Nieznana flaga.")
    cur.execute("REPLACE INTO player.quest (dwPID, szName, szState, lValue) VALUES (0, %s, '', %s)", (name, int(value)))


def class_label(job, group):
    job = int(job or 0) % 4
    return f"{CLASSES.get(job, '?')} {PATHS.get((job, int(group or 1)), '')}".strip()


def yang(value):
    value = int(value or 0)
    return f"{value:,}".replace(",", " ")


def install(app, db, login_required, csrf_token):
    # MT2009_PLUS_KOLEKCJONER_CONFIG_V1: the sub-page "Kolekcjoner Najemnikow - zadania" (/events/najemnicy/kolekcjoner).
    import kolekcjoner_config
    kolekcjoner_config.install(app, db, login_required, csrf_token)
    from flask import abort, flash, redirect, render_template, request, session, url_for

    def check_csrf():
        expected = session.get("seban_update_csrf", "")
        if not expected or not secrets.compare_digest(request.form.get("nj_csrf", ""), expected):
            abort(400, "Odśwież stronę i spróbuj ponownie.")

    def find_pid(cur, name):
        name = (name or "").strip()
        if not name or len(name) > 24:
            raise ValueError("Wpisz nick postaci.")
        cur.execute("SELECT id, name, level FROM player.player WHERE name=%s", (name,))
        row = cur.fetchone()
        if not row:
            raise ValueError(f"Nie ma postaci „{name}”.")
        return row

    @app.route("/events/najemnicy", methods=["GET", "POST"])
    @login_required
    def najemnicy():
        with db() as con, con.cursor() as cur:
            if not tables_ready(cur):
                return render_template("najemnicy.html", missing=True, nj_csrf=csrf_token())
            if request.method == "POST":
                check_csrf()
                action = request.form.get("action", "")
                try:
                    if action == "flags":
                        write_flag(cur, "m2_najemnicy_off", 1 if request.form.get("off") == "1" else 0)
                        write_flag(cur, "m2_najemnicy_free_unlock", 1 if request.form.get("free_unlock") == "1" else 0)
                        price_text = (request.form.get("price_h") or "").replace(" ", "").strip()
                        price = int(price_text) if price_text else 0
                        if price < 0 or price > 2000000000:
                            raise ValueError("Opłata za godzinę: 0 (domyślne 5 000 000) do 2 000 000 000 yang.")
                        write_flag(cur, "m2_najemnicy_price_h", price)
                        flash("Ustawienia zapisane – gra odczyta je w ciągu ~10 s (bez restartu).", "success")
                    elif action in ("unlock", "lock"):
                        row = find_pid(cur, request.form.get("name"))
                        try:
                            tasks = int(request.form.get("tasks") or MAX_TASKS) if action == "unlock" else 0
                        except ValueError:
                            raise ValueError(f"Zadania: liczba od 0 do {MAX_TASKS}.")
                        if tasks < 0 or tasks > MAX_TASKS:
                            raise ValueError(f"Zadania: liczba od 0 do {MAX_TASKS}.")
                        cur.execute("INSERT INTO player.najemnicy_unlock (owner_pid, unlocked, tasks, unlocked_at, source) "
                                    "VALUES (%s, %s, %s, NOW(), 'panel') ON DUPLICATE KEY UPDATE unlocked=%s, tasks=%s, "
                                    "unlocked_at=NOW(), source='panel'", (row["id"], 1 if tasks else 0, tasks,
                                                                          1 if tasks else 0, tasks))
                        # The quest flag follows down too (the game only ever raises it from the row) - for a
                        # character offline; one online keeps its flag in memory: /najemnicy zadania|zablokuj in the game.
                        cur.execute("UPDATE player.quest SET lValue=%s WHERE dwPID=%s AND szName='najemnicy' "
                                    "AND szState='tasks' AND lValue>%s", (tasks, row["id"], tasks))
                        slots = slots_for(tasks, row["level"], read_tiers(cur))
                        flash(f"{row['name']} (poziom {row['level']}): zadania Kolekcjonera {tasks}/{MAX_TASKS} – "
                              f"miejsca na najemników teraz: {slots}.", "success")
                    else:
                        abort(400, "Nieznana akcja.")
                except ValueError as exc:
                    flash(str(exc), "error")
                return redirect(url_for("najemnicy"))
            flags = read_flags(cur)
            cur.execute("""SELECT n.*, o.name AS owner_name, o.level AS owner_level, p.level AS merc_level,
                                  p.last_play AS merc_last_play
                           FROM player.najemnicy n
                           LEFT JOIN player.player o ON o.id = n.owner_pid
                           LEFT JOIN player.player p ON p.id = n.merc_pid
                           ORDER BY n.retired, o.name, n.slot""")
            mercs = cur.fetchall()
            owners = {}
            for m in mercs:
                m["label"] = class_label(m["job"], m["skill_group"])
                m["sex_name"] = "kobieta" if int(m["sex"] or 0) else "mężczyzna"
                if int(m["retired"] or 0):
                    continue
                o = owners.setdefault(m["owner_pid"], {"pid": m["owner_pid"], "name": m["owner_name"] or f"#{m['owner_pid']}",
                                                       "level": m["owner_level"], "mercs": []})
                o["mercs"].append(m)
            retired = [m for m in mercs if int(m["retired"] or 0)]
            cur.execute("""SELECT v.*, o.name AS owner_name, o.level AS owner_level
                           FROM player.najemnicy_vault v LEFT JOIN player.player o ON o.id = v.owner_pid
                           ORDER BY v.balance DESC LIMIT 500""")
            vaults = cur.fetchall()
            for v in vaults:
                v["balance_text"] = yang(v["balance"])
                v["paid_text"] = yang(v["total_paid"])
                v["deposit_text"] = yang(v["total_deposit"])
            cur.execute("""SELECT u.*, o.name AS owner_name, o.level AS owner_level
                           FROM player.najemnicy_unlock u LEFT JOIN player.player o ON o.id = u.owner_pid
                           ORDER BY u.tasks DESC, u.unlocked_at DESC LIMIT 500""")
            unlocks = cur.fetchall()
            tiers = read_tiers(cur)
            for u in unlocks:
                u["slots"] = slots_for(u["tasks"], u["owner_level"], tiers)
            price = int(flags["m2_najemnicy_price_h"] or 0) or DEFAULT_PRICE_H
            total_balance = sum(int(v["balance"] or 0) for v in vaults)
            return render_template("najemnicy.html", missing=False, flags=flags, price=price, price_text=yang(price),
                                   owners=sorted(owners.values(), key=lambda o: (o["name"] or "").lower()),
                                   retired=retired, vaults=vaults, unlocks=unlocks,
                                   total_mercs=sum(len(o["mercs"]) for o in owners.values()),
                                   total_balance=yang(total_balance), tiers=tiers, nj_csrf=csrf_token())
