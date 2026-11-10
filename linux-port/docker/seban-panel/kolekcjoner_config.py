"""MT2009_PLUS_KOLEKCJONER_CONFIG_V1: "Kolekcjoner Najemników – zadania" - the advanced config of the collector's tasks
(the owner, 10 November 2026: "zaawansowany panel konfiguracji Kolekcjonera"). A sub-page of Wydarzenia -> Najemnicy
(/events/najemnicy/kolekcjoner). The game's side: playerbot_kolekcjoner_najemnikow.cpp (the tasks, items, rewards) and
playerbot_najemnicy.h (the tiers); the tables: mariadb/playerbot/kolekcjoner_najemnikow.sql.

What it edits (player.najemnicy_kolekcjoner_*):
* categories - a task: the ascii key name, title (Polish), description, min_level (to hand in), percent (the success
  chance of one hand-in), sort_order (the window's order); add / remove / up / down;
* items - a task's item rows: vnum (must be in player.item_proto), count, pack (1..count), unopened, sort_order;
  item_index is the stable id the players' progress is keyed by: a new item takes MAX+1, reordering touches only
  sort_order, removing an item deletes its progress rows;
* rewards - the permanent bonus lines of a task (point name from POINTS + a value != 0), several a task;
* tiers - the n-th completed task -> slots (1..7) from level (1..120), both non-decreasing by nr.
Removing a task deletes its categories / items / rewards / progress rows; the completed rows stay (the players keep the
tier count and lose that bonus). After every change the live-reload flag m2_kolekcjoner_najemnikow_ver (player.quest,
dwPID 0) = UNIX_TIMESTAMP(): every core re-reads the definitions within ~30 s and the tiers within ~10 s.
"""
import secrets

# The valid reward point names (the game's s_aKnPoints, the client's POINTS) and their Polish labels (one %d).
POINTS = (
    ("MAX_HP", "Maks. PŻ +%d"),
    ("MAX_SP", "Maks. PE +%d"),
    ("MAX_HP_PCT", "Maks. PŻ +%d%%"),
    ("ATT_GRADE_BONUS", "Wartość ataku +%d"),
    ("MAGIC_ATT_GRADE_BONUS", "Wartość ataku magicznego +%d"),
    ("DEF_GRADE_BONUS", "Obrona +%d"),
    ("MAGIC_DEF_GRADE_BONUS", "Obrona magiczna +%d"),
    ("ATTBONUS_MONSTER", "Silny przeciwko potworom +%d%%"),
    ("ATTBONUS_BOSS", "Silny przeciwko bossom +%d%%"),
    ("ATTBONUS_STONE", "Silny przeciwko kamieniom Metin +%d%%"),
    ("ATTBONUS_HUMAN", "Silny przeciwko ludziom +%d%%"),
    ("CRITICAL_PCT", "Szansa na krytyczne uderzenie +%d%%"),
    ("PENETRATE_PCT", "Szansa na przeszywające uderzenie +%d%%"),
    ("RESIST_FIRE", "Odporność na ogień +%d%%"),
    ("RESIST_ICE", "Odporność na lód +%d%%"),
    ("RESIST_ELEC", "Odporność na błyskawice +%d%%"),
    ("RESIST_WIND", "Odporność na wiatr +%d%%"),
    ("RESIST_EARTH", "Odporność na ziemię +%d%%"),
    ("RESIST_DARK", "Odporność na ciemność +%d%%"),
    ("ATT_SPEED", "Szybkość ataku +%d%%"),
    ("MOV_SPEED", "Szybkość ruchu +%d%%"),
    ("CASTING_SPEED", "Szybkość zaklęć +%d%%"),
    ("HP_REGEN", "Regeneracja PŻ +%d%%"),
    ("SP_REGEN", "Regeneracja PE +%d%%"),
    ("STEAL_HP", "Absorpcja PŻ +%d%%"),
    ("STEAL_SP", "Absorpcja PE +%d%%"),
    ("ATTBONUS_ANIMAL", "Silny przeciwko zwierzętom +%d%%"),
    ("ATTBONUS_ORC", "Silny przeciwko orkom +%d%%"),
    ("ATTBONUS_MILGYO", "Silny przeciwko mistykom +%d%%"),
    ("ATTBONUS_UNDEAD", "Silny przeciwko nieumarłym +%d%%"),
    ("ATTBONUS_DEVIL", "Silny przeciwko diabłom +%d%%"),
    ("ATTBONUS_WARRIOR", "Silny przeciwko wojownikom +%d%%"),
    ("ATTBONUS_ASSASSIN", "Silny przeciwko ninja +%d%%"),
    ("ATTBONUS_SURA", "Silny przeciwko surom +%d%%"),
    ("ATTBONUS_SHAMAN", "Silny przeciwko szamanom +%d%%"),
    ("RESIST_WARRIOR", "Odporność na wojowników +%d%%"),
    ("RESIST_ASSASSIN", "Odporność na ninja +%d%%"),
    ("RESIST_SURA", "Odporność na sury +%d%%"),
    ("RESIST_SHAMAN", "Odporność na szamanów +%d%%"),
    ("BLOCK", "Szansa na blok +%d%%"),
    ("DODGE", "Szansa na unik strzał +%d%%"),
    ("RESIST_SWORD", "Odporność na miecze +%d%%"),
    ("RESIST_TWOHAND", "Odporność na broń dwuręczną +%d%%"),
    ("RESIST_DAGGER", "Odporność na sztylety +%d%%"),
    ("RESIST_BELL", "Odporność na dzwony +%d%%"),
    ("RESIST_FAN", "Odporność na wachlarze +%d%%"),
    ("RESIST_BOW", "Odporność na strzały +%d%%"),
    ("RESIST_MAGIC", "Odporność na magię +%d%%"),
    ("RESIST_CRITICAL", "Odporność na krytyczne uderzenia +%d%%"),
    ("RESIST_PENETRATE", "Odporność na przeszywające uderzenia +%d%%"),
    ("NORMAL_HIT_DAMAGE_BONUS", "Średnie obrażenia +%d%%"),
    ("SKILL_DAMAGE_BONUS", "Obrażenia umiejętności +%d%%"),
    ("NORMAL_HIT_DEFEND_BONUS", "Odporność na średnie obrażenia +%d%%"),
    ("SKILL_DEFEND_BONUS", "Odporność na obrażenia umiejętności +%d%%"),
    ("POISON_PCT", "Szansa na otrucie +%d%%"),
    ("STUN_PCT", "Szansa na omdlenie +%d%%"),
    ("SLOW_PCT", "Szansa na spowolnienie +%d%%"),
    ("EXP_DOUBLE_BONUS", "Szansa na podwójne doświadczenie +%d%%"),
    ("GOLD_DOUBLE_BONUS", "Szansa na podwójny yang +%d%%"),
    ("ITEM_DROP_BONUS", "Szansa na podwójny drop +%d%%"),
)
POINT_NAMES = frozenset(name for name, _ in POINTS)
POINT_LABELS = dict(POINTS)

DEFAULT_TIERS = tuple((n, n + 1, 75 + 5 * n) for n in range(1, 7))	# (nr, slots, level): 1 -> 2 @ 80 ... 6 -> 7 @ 105
MAX_SLOTS = 7
MAX_LEVEL = 120
MAX_TIERS = 16
RELOAD_FLAG = "m2_kolekcjoner_najemnikow_ver"
RELOAD_NOTE = "Gra wczyta zmiany w ciągu ~30 s (bez restartu)."

# The spec's columns, idempotent (the migration and the game make them too; this is the page's own net).
SCHEMA = (
    "ALTER TABLE player.najemnicy_kolekcjoner_categories "
    "ADD COLUMN IF NOT EXISTS title VARCHAR(64) NOT NULL DEFAULT '', "
    "ADD COLUMN IF NOT EXISTS description VARCHAR(200) NOT NULL DEFAULT '', "
    "ADD COLUMN IF NOT EXISTS min_level SMALLINT UNSIGNED NOT NULL DEFAULT 0, "
    "ADD COLUMN IF NOT EXISTS sort_order SMALLINT NOT NULL DEFAULT 0",
    "ALTER TABLE player.najemnicy_kolekcjoner_items ADD COLUMN IF NOT EXISTS sort_order SMALLINT NOT NULL DEFAULT 0",
    "CREATE TABLE IF NOT EXISTS player.najemnicy_kolekcjoner_tiers (nr TINYINT UNSIGNED NOT NULL, "
    "slots TINYINT UNSIGNED NOT NULL DEFAULT 2, level SMALLINT UNSIGNED NOT NULL DEFAULT 80, PRIMARY KEY (nr)) "
    "ENGINE=InnoDB",
)
TABLES_CHECK = ("SELECT COUNT(*) AS n FROM information_schema.TABLES WHERE TABLE_SCHEMA='player' AND TABLE_NAME IN "
                "('najemnicy_kolekcjoner_categories','najemnicy_kolekcjoner_items','najemnicy_kolekcjoner_rewards')")


# ------------------------------------------------------------------ pure validation (test_kolekcjoner_config.py)

def to_int(value, what, low=None, high=None):
    text = str(value if value is not None else "").replace(" ", "").strip()
    try:
        number = int(text)
    except ValueError:
        raise ValueError(f"{what}: wpisz liczbę całkowitą.")
    if low is not None and number < low or high is not None and number > high:
        if high is None:
            raise ValueError(f"{what}: co najmniej {low}.")
        raise ValueError(f"{what}: od {low} do {high}.")
    return number


def clean_text(value, what, limit, ascii_only=False, required=False):
    text = " ".join(str(value or "").split())
    if required and not text:
        raise ValueError(f"{what}: pole nie może być puste.")
    if len(text) > limit:
        raise ValueError(f"{what}: najwyżej {limit} znaków.")
    if ascii_only and any(ord(c) < 32 or ord(c) > 126 for c in text):
        raise ValueError(f"{what}: tylko litery bez polskich znaków, cyfry i spacje.")
    if not ascii_only:
        try:
            text.encode("cp1250")
        except UnicodeEncodeError:
            raise ValueError(f"{what}: znak spoza polskiego alfabetu (gra używa CP1250).")
    return text


def validate_task(form):
    """The task's fields -> dict; ValueError with a Polish message."""
    return {
        "name": clean_text(form.get("name"), "Klucz (nazwa ASCII)", 48, ascii_only=True, required=True),
        "title": clean_text(form.get("title"), "Nazwa w oknie", 64),
        "description": clean_text(form.get("description"), "Opis", 200),
        "min_level": to_int(form.get("min_level") or 0, "Minimalny poziom oddawania", 0, MAX_LEVEL),
        "percent": to_int(form.get("percent"), "Szansa (%)", 1, 100),
        "sort_order": to_int(form.get("sort_order") or 0, "Kolejność", -32768, 32767),
    }


def validate_item(form, vnum_exists):
    """An item row -> dict; vnum_exists(vnum) -> bool (player.item_proto)."""
    vnum = to_int(form.get("vnum"), "Vnum", 1, 2 ** 32 - 1)
    if not vnum_exists(vnum):
        raise ValueError(f"Vnum {vnum}: nie ma takiego przedmiotu w item_proto.")
    count = to_int(form.get("count"), "Ilość", 1, 2 ** 31 - 1)
    pack = to_int(form.get("pack") or 1, "Paczka", 1, 2 ** 31 - 1)
    if pack > count:
        raise ValueError(f"Paczka ({pack}) nie może być większa od ilości ({count}).")
    return {"vnum": vnum, "count": count, "pack": pack, "unopened": 1 if form.get("unopened") in ("1", "on", 1, True) else 0,
            "sort_order": to_int(form.get("sort_order") or 0, "Kolejność", -32768, 32767)}


def validate_reward(form):
    point = str(form.get("point") or "").strip().upper()
    if point not in POINT_NAMES:
        raise ValueError(f"Nieznany bonus „{point}”. Wybierz z listy.")
    value = to_int(form.get("value"), "Wartość bonusu", -1000000, 1000000)
    if value == 0:
        raise ValueError("Wartość bonusu nie może być 0.")
    return {"point": point, "value": value}


def validate_tiers(rows):
    """rows: [(nr, slots, level)] with numbers or texts -> sorted [(nr, slots, level)]; non-decreasing slots and levels."""
    out = []
    seen = set()
    for nr, slots, level in rows:
        nr = to_int(nr, "Próg (nr zadania)", 1, MAX_TIERS)
        if nr in seen:
            raise ValueError(f"Próg {nr} jest dwa razy.")
        seen.add(nr)
        out.append((nr, to_int(slots, f"Próg {nr}: najemnicy", 1, MAX_SLOTS),
                    to_int(level, f"Próg {nr}: poziom", 1, MAX_LEVEL)))
    out.sort()
    for (n1, s1, l1), (n2, s2, l2) in zip(out, out[1:]):
        if s2 < s1:
            raise ValueError(f"Próg {n2}: liczba najemników ({s2}) mniejsza niż w progu {n1} ({s1}).")
        if l2 < l1:
            raise ValueError(f"Próg {n2}: poziom ({l2}) niższy niż w progu {n1} ({l1}).")
    return out


def slots_for_tiers(tiers, tasks, level):
    """The game's GetNajemnicySlots over a tier table [(nr, slots, level)]: 0 = locked."""
    best = 0
    for nr, slots, need in tiers or DEFAULT_TIERS:
        if int(nr) <= int(tasks or 0) and int(level or 0) >= int(need):
            best = max(best, int(slots))
    return min(MAX_SLOTS, best)


def label(point, value):
    template = POINT_LABELS.get(point)
    return template % value if template else f"{point} {value:+d}"


def swap_order(ids, which, step):
    """ids in the current order -> the new order with `which` moved by step (-1 up, +1 down); unchanged at an edge."""
    ids = list(ids)
    if which not in ids:
        return ids
    i = ids.index(which)
    j = i + step
    if 0 <= j < len(ids):
        ids[i], ids[j] = ids[j], ids[i]
    return ids


# ------------------------------------------------------------------ the database

def ensure_schema(cur):
    cur.execute(TABLES_CHECK)
    if int((cur.fetchone() or {}).get("n") or 0) < 3:
        return False
    for sql in SCHEMA:
        cur.execute(sql)
    cur.execute("SELECT COUNT(*) AS n FROM player.najemnicy_kolekcjoner_tiers")
    if not int(cur.fetchone()["n"] or 0):
        cur.executemany("INSERT IGNORE INTO player.najemnicy_kolekcjoner_tiers (nr, slots, level) VALUES (%s,%s,%s)",
                        DEFAULT_TIERS)
    return True


def read_tiers(cur):
    """The tier table, or the built-in one when it is missing or empty."""
    try:
        cur.execute("SELECT nr, slots, level FROM player.najemnicy_kolekcjoner_tiers ORDER BY nr")
        rows = [(int(r["nr"]), int(r["slots"]), int(r["level"])) for r in cur.fetchall()]
    except Exception:
        rows = []
    return rows or list(DEFAULT_TIERS)


def bump_reload(cur):
    cur.execute("REPLACE INTO player.quest (dwPID, szName, szState, lValue) VALUES (0, %s, '', UNIX_TIMESTAMP())",
                (RELOAD_FLAG,))


def install(app, db, login_required, csrf_token):
    from flask import abort, flash, redirect, render_template, request, session, url_for

    def check_csrf():
        expected = session.get("seban_update_csrf", "")
        if not expected or not secrets.compare_digest(request.form.get("nj_csrf", ""), expected):
            abort(400, "Odśwież stronę i spróbuj ponownie.")

    def task_exists(cur, task):
        cur.execute("SELECT 1 FROM player.najemnicy_kolekcjoner_categories WHERE collection_index=%s", (task,))
        if not cur.fetchone():
            raise ValueError(f"Nie ma zadania {task}.")

    def renumber(cur, table, where, args, ids, key):
        for pos, ident in enumerate(ids):
            cur.execute(f"UPDATE player.{table} SET sort_order=%s WHERE {where} AND {key}=%s", (pos * 10,) + args + (ident,))

    def task_order(cur):
        cur.execute("SELECT collection_index FROM player.najemnicy_kolekcjoner_categories "
                    "ORDER BY sort_order, collection_index")
        return [int(r["collection_index"]) for r in cur.fetchall()]

    def item_order(cur, task):
        cur.execute("SELECT item_index FROM player.najemnicy_kolekcjoner_items WHERE collection_index=%s "
                    "ORDER BY sort_order, item_index", (task,))
        return [int(r["item_index"]) for r in cur.fetchall()]

    def act(cur, action, f):
        """One change; returns the flash text. ValueError = a Polish message, nothing written."""
        def vnum_exists(vnum):
            cur.execute("SELECT 1 FROM player.item_proto WHERE vnum=%s", (vnum,))
            return bool(cur.fetchone())

        task = to_int(f.get("task") or 0, "Zadanie", 0, 255)
        if action == "task_add":
            data = validate_task(f)
            cur.execute("SELECT COALESCE(MAX(collection_index),0)+1 AS n, COALESCE(MAX(sort_order),0)+10 AS s "
                        "FROM player.najemnicy_kolekcjoner_categories")
            row = cur.fetchone()
            new = int(row["n"])
            if new > 255:
                raise ValueError("Najwyżej 255 zadań.")
            cur.execute("INSERT INTO player.najemnicy_kolekcjoner_categories (collection_index, name, percent, title, "
                        "description, min_level, sort_order) VALUES (%s,%s,%s,%s,%s,%s,%s)",
                        (new, data["name"], data["percent"], data["title"], data["description"], data["min_level"],
                         int(row["s"]) if not f.get("sort_order") else data["sort_order"]))
            return f"Dodano zadanie {new} („{data['title'] or data['name']}”). Dodaj mu przedmioty – zadanie bez przedmiotów gra pomija."
        if action == "tier_save":
            nrs = f.getlist("tier_nr")
            rows = validate_tiers(list(zip(nrs, f.getlist("tier_slots"), f.getlist("tier_level"))))
            if not rows:
                raise ValueError("Tabela progów nie może być pusta.")
            cur.execute("DELETE FROM player.najemnicy_kolekcjoner_tiers")
            cur.executemany("INSERT INTO player.najemnicy_kolekcjoner_tiers (nr, slots, level) VALUES (%s,%s,%s)", rows)
            return f"Progi zapisane ({len(rows)})."
        if action == "tier_add":
            tiers = read_tiers(cur)
            nr = max([t[0] for t in tiers] or [0]) + 1
            last = tiers[-1] if tiers else (0, 1, 80)
            rows = validate_tiers(tiers + [(nr, min(MAX_SLOTS, last[1] + 1), min(MAX_LEVEL, last[2] + 5))])
            cur.execute("DELETE FROM player.najemnicy_kolekcjoner_tiers")
            cur.executemany("INSERT INTO player.najemnicy_kolekcjoner_tiers (nr, slots, level) VALUES (%s,%s,%s)", rows)
            return f"Dodano próg {nr}."
        if action == "tier_delete":
            nr = to_int(f.get("nr"), "Próg", 1, MAX_TIERS)
            cur.execute("DELETE FROM player.najemnicy_kolekcjoner_tiers WHERE nr=%s", (nr,))
            return f"Usunięto próg {nr}."
        task_exists(cur, task)
        if action == "task_save":
            data = validate_task(f)
            cur.execute("UPDATE player.najemnicy_kolekcjoner_categories SET name=%s, percent=%s, title=%s, description=%s, "
                        "min_level=%s, sort_order=%s WHERE collection_index=%s",
                        (data["name"], data["percent"], data["title"], data["description"], data["min_level"],
                         data["sort_order"], task))
            return f"Zadanie {task} zapisane."
        if action == "task_delete":
            for table in ("items", "rewards", "progress", "categories"):
                cur.execute(f"DELETE FROM player.najemnicy_kolekcjoner_{table} WHERE collection_index=%s", (task,))
            return f"Usunięto zadanie {task} (jego przedmioty, bonusy i postęp graczy; ukończenia zostały)."
        if action in ("task_up", "task_down"):
            renumber(cur, "najemnicy_kolekcjoner_categories", "1=1", (),
                     swap_order(task_order(cur), task, -1 if action == "task_up" else 1), "collection_index")
            return f"Zadanie {task} przesunięte."
        if action == "item_add":
            data = validate_item(f, vnum_exists)
            cur.execute("SELECT COALESCE(MAX(item_index),-1)+1 AS n, COALESCE(MAX(sort_order),0)+10 AS s "
                        "FROM player.najemnicy_kolekcjoner_items WHERE collection_index=%s", (task,))
            row = cur.fetchone()
            new = int(row["n"])
            if new > 255:
                raise ValueError("Najwyżej 256 przedmiotów w zadaniu.")
            cur.execute("INSERT INTO player.najemnicy_kolekcjoner_items (collection_index, item_index, item_vnum, item_count, "
                        "pack, unopened, sort_order) VALUES (%s,%s,%s,%s,%s,%s,%s)",
                        (task, new, data["vnum"], data["count"], data["pack"], data["unopened"],
                         int(row["s"]) if not f.get("sort_order") else data["sort_order"]))
            return f"Zadanie {task}: dodano przedmiot {data['vnum']}."
        item = to_int(f.get("item"), "Przedmiot", 0, 255)
        if action.startswith("item_"):
            cur.execute("SELECT 1 FROM player.najemnicy_kolekcjoner_items WHERE collection_index=%s AND item_index=%s",
                        (task, item))
            if not cur.fetchone():
                raise ValueError(f"Zadanie {task} nie ma przedmiotu {item}.")
        if action == "item_save":
            data = validate_item(f, vnum_exists)
            cur.execute("UPDATE player.najemnicy_kolekcjoner_items SET item_vnum=%s, item_count=%s, pack=%s, unopened=%s, "
                        "sort_order=%s WHERE collection_index=%s AND item_index=%s",
                        (data["vnum"], data["count"], data["pack"], data["unopened"], data["sort_order"], task, item))
            return f"Zadanie {task}: przedmiot zapisany."
        if action == "item_delete":
            cur.execute("DELETE FROM player.najemnicy_kolekcjoner_items WHERE collection_index=%s AND item_index=%s",
                        (task, item))
            cur.execute("DELETE FROM player.najemnicy_kolekcjoner_progress WHERE collection_index=%s AND item_index=%s",
                        (task, item))
            return f"Zadanie {task}: usunięto przedmiot (i postęp graczy w nim)."
        if action in ("item_up", "item_down"):
            renumber(cur, "najemnicy_kolekcjoner_items", "collection_index=%s", (task,),
                     swap_order(item_order(cur, task), item, -1 if action == "item_up" else 1), "item_index")
            return f"Zadanie {task}: przedmiot przesunięty."
        if action == "reward_add":
            data = validate_reward(f)
            cur.execute("INSERT INTO player.najemnicy_kolekcjoner_rewards (collection_index, point_name, value) "
                        "VALUES (%s,%s,%s) ON DUPLICATE KEY UPDATE value=VALUES(value)", (task, data["point"], data["value"]))
            return f"Zadanie {task}: bonus {label(data['point'], data['value'])}."
        if action == "reward_save":
            data = validate_reward(f)
            old = str(f.get("old_point") or "").upper()
            if old != data["point"]:
                cur.execute("SELECT 1 FROM player.najemnicy_kolekcjoner_rewards WHERE collection_index=%s AND point_name=%s",
                            (task, data["point"]))
                if cur.fetchone():
                    raise ValueError("To zadanie ma już ten bonus – zmień jego wartość w tamtym wierszu.")
            cur.execute("UPDATE player.najemnicy_kolekcjoner_rewards SET point_name=%s, value=%s "
                        "WHERE collection_index=%s AND point_name=%s", (data["point"], data["value"], task, old))
            return f"Zadanie {task}: bonus zapisany."
        if action == "reward_delete":
            cur.execute("DELETE FROM player.najemnicy_kolekcjoner_rewards WHERE collection_index=%s AND point_name=%s",
                        (task, str(f.get("old_point") or "").upper()))
            return f"Zadanie {task}: bonus usunięty."
        abort(400, "Nieznana akcja.")

    @app.route("/events/najemnicy/kolekcjoner", methods=["GET", "POST"])
    @login_required
    def najemnicy_kolekcjoner():
        with db() as con, con.cursor() as cur:
            if not ensure_schema(cur):
                return render_template("kolekcjoner_config.html", missing=True, nj_csrf=csrf_token())
            if request.method == "POST":
                check_csrf()
                action = request.form.get("action", "")
                anchor = ""
                try:
                    con.autocommit(False)
                    try:
                        text = act(cur, action, request.form)
                        bump_reload(cur)
                        con.commit()
                    except Exception:
                        con.rollback()
                        raise
                    finally:
                        con.autocommit(True)
                    flash(f"{text} {RELOAD_NOTE}", "success")
                    if request.form.get("task") and action != "task_delete":
                        anchor = "zadanie-" + str(request.form.get("task"))
                except ValueError as exc:
                    flash(str(exc), "error")
                return redirect(url_for("najemnicy_kolekcjoner") + (("#" + anchor) if anchor else ""))
            cur.execute("SELECT * FROM player.najemnicy_kolekcjoner_categories ORDER BY sort_order, collection_index")
            tasks = cur.fetchall()
            cur.execute("SELECT i.*, p.locale_name, p.name AS proto_name FROM player.najemnicy_kolekcjoner_items i "
                        "LEFT JOIN player.item_proto p ON p.vnum = i.item_vnum ORDER BY i.collection_index, i.sort_order, "
                        "i.item_index")
            items = cur.fetchall()
            cur.execute("SELECT * FROM player.najemnicy_kolekcjoner_rewards ORDER BY collection_index, point_name")
            rewards = cur.fetchall()
            cur.execute("SELECT collection_index, COUNT(*) AS n FROM player.najemnicy_kolekcjoner_complete "
                        "GROUP BY collection_index")
            completed = {int(r["collection_index"]): int(r["n"]) for r in cur.fetchall()}
            cur.execute("SELECT lValue FROM player.quest WHERE dwPID=0 AND szName=%s", (RELOAD_FLAG,))
            ver = cur.fetchone()
            tiers = read_tiers(cur)
            by_task = {}
            for t in tasks:
                t["items"] = []
                t["rewards"] = []
                t["completed"] = completed.get(int(t["collection_index"]), 0)
                by_task[int(t["collection_index"])] = t
            for i in items:
                t = by_task.get(int(i["collection_index"]))
                if t is not None:
                    i["item_label"] = i["locale_name"] or i["proto_name"] or "– brak w item_proto –"
                    i["known"] = bool(i["locale_name"] or i["proto_name"])
                    t["items"].append(i)
            for r in rewards:
                t = by_task.get(int(r["collection_index"]))
                if t is not None:
                    r["label"] = label(r["point_name"], int(r["value"] or 0))
                    r["known"] = r["point_name"] in POINT_NAMES
                    t["rewards"].append(r)
            return render_template("kolekcjoner_config.html", missing=False, tasks=tasks, tiers=tiers,
                                   points=POINTS, max_slots=MAX_SLOTS, max_level=MAX_LEVEL,
                                   reload_version=(ver or {}).get("lValue"), nj_csrf=csrf_token())
