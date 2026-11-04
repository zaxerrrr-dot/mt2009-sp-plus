"""MT2009_PLUS_DB_EDITOR_V1: "Łowienie ryb" - what a fishing rod brings up.

Where it lives: NOT in locale/poland/fishing.txt. This engine's fishing.cpp
(the fishing minigame) has no loader for fishing.txt at all - the file is a
leftover of the old engine (its "map grade" chances and fish lengths are
never read). A catch is decided by the quest library
  share/locale/poland/quest/libs/fishing/fishing_drop.lua
whose table fishing_drop_table holds six numbers per line
(MT2009_PLUS_FISHING_GLOBAL_V1, game/lowienie/fishing_drop.lua):
  itemVnum ("farba" = a random hair dye 70202-70206), itemCount,
  rodFrom, rodTo (the rod's level: Wędka+1 ... Wędka+20 = 1 ... 20 - value0 / 10;
  Wędka Węglowa 22), tier, weight.
The tier: 0 a common fish or an item (its weight), 1 a better fish (weight x
(1 + 0.10 x (level - 1))), 2 a rare fish - only with Rybie Wnętrzności or
the golden tuna's bonus (weight x (1 + 0.25 x (level - 4)) x 2, the tuna's
5 minutes x 2.5), 3 Zloty Tunczyk (once a day, not for bots).
fishing.quest -> fishing_manage.predict_fish() draws one line by weight.
Bots fish through the same CHARACTER::fishing() / quest path.

The quest libraries are read when the cores boot. The panel writes only the
lines (plain text) into the spool both containers mount:
    <spool>/fishing/fishing_drop.v2.custom.txt
and the game's m2-fishing (bin/m2-fishing, run by m2-supervise before the
cores boot) rebuilds the live fishing_drop.lua from the image's copy with
those lines, after checking them (and every item against item_proto, every
rod level 1-20 and 22 having something of tier 0/1 to catch); a file that fails is not used and
<spool>/fishing/status says why. The image's file comes back as
fishing/fishing_drop.base.lua; until a game with m2-fishing has run, the
panel shows its snapshot (dbeditor/fishing_drop.snapshot.lua).

Backups, "pending" and the game's report use dropfiles.py's machinery: the
file is registered there as key "fishing", so /db/apply lists it.
"""
import re
from pathlib import Path

from flask import flash, g, redirect, render_template, request, url_for

from dbeditor import dropfiles as df
from dbeditor import tables_common

KEY = "fishing"
FOLDER = "fishing"
SNAPSHOT = Path(__file__).resolve().parent / "fishing_drop.snapshot.lua"   # the image's file (MT2009_PLUS_FISHING_GLOBAL_V1)
ROD_BASE = 27400
CARBON_ROD = 27591
CARBON_LEVEL = 22                # Wędka Węglowa counts as level 22
ROD_LEVELS = list(range(1, 21)) + [CARBON_LEVEL]   # Wędka+1 ... Wędka+20, Wędka Węglowa
ROD_MAX = 22
DYE = "farba"
DYE_VNUMS = (70202, 70203, 70204, 70205, 70206)
TIERS = ((0, "zwykła / przedmiot"), (1, "lepsza ryba"), (2, "rzadka ryba (Wnętrzności / tuńczyk)"),
         (3, "Złoty Tuńczyk (raz dziennie)"))
# the rare fish's multiplier x100: none (no rare fish), Rybie Wnętrzności / the tuna's 60 minutes x2, its 5 minutes x2.5
RARE = ((0, "bez Rybich Wnętrzności"), (200, "Rybie Wnętrzności / Bonus Tuńczyka 60 min (x2)"),
        (250, "Bonus Tuńczyka 5 min (x2,5)"))
LIMITS = {"count": (1, 200), "rod_min": (1, ROD_MAX), "rod_max": (1, ROD_MAX), "tier": (0, 3),
          "weight": (1, 1000000)}
LABELS = {"item": "Przedmiot", "count": "Ilość", "rod_min": "Od wędki +", "rod_max": "Do wędki +",
          "tier": "Rodzaj", "weight": "Waga"}
TABLE_START = re.compile(r"^\s*local\s+fishing_drop_table\s*=\s*\{")


def register_file():
    """The fishing file in dropfiles' table: custom path, status, backups and
    the "pending" list of /db/apply come with it."""
    df.FILES.setdefault(KEY, (FOLDER, "fishing_drop.v2.custom.txt", "status", "Łowienie ryb (fishing_drop.lua)"))
    df.BASES.setdefault(KEY, (FOLDER, "fishing_drop.base.lua"))


# ----------------------------------------------------------------- parsing ---
def parse_lua(text):
    """fishing_drop.lua -> [entry] of its fishing_drop_table (lines commented
    out with -- are not in the table)."""
    entries, inside = [], False
    for raw in (text or "").replace("\r", "").split("\n"):
        if not inside:
            if TABLE_START.match(raw):
                inside = True
            continue
        line = raw.split("--", 1)[0].strip()
        if line.startswith("}"):
            break
        if not line:
            continue
        fields = [f.strip() for f in line.split(",") if f.strip()]
        if len(fields) != 6:
            continue
        item = fields[0].strip('"').strip("'")
        try:
            numbers = [int(f) for f in fields[1:]]
        except ValueError:
            continue
        comment = raw.split("--", 1)[1].strip() if "--" in raw else ""
        entries.append(entry(item, *numbers, comment=comment))
    return entries


def entry(item, count, rod_min, rod_max, tier, weight, comment=""):
    return {"item": str(item).lower(), "count": int(count), "rod_min": int(rod_min), "rod_max": int(rod_max),
            "tier": int(tier), "weight": int(weight), "comment": comment}


def parse_custom(text):
    """The panel's file: one line per catch, tab separated, "#" comments."""
    entries = []
    for raw in (text or "").replace("\r", "").split("\n"):
        line, _sep, comment = raw.partition("#")
        fields = line.split()
        if len(fields) != 6:
            continue
        try:
            entries.append(entry(fields[0], *[int(f) for f in fields[1:]], comment=comment.strip()))
        except ValueError:
            continue
    return entries


def render_custom(entries, reason=""):
    from datetime import datetime
    lines = ["# MT2009_PLUS_DB_EDITOR_V1 - tabela lowienia ryb zapisana w panelu Seban",
             f"# zapis: {datetime.now():%Y-%m-%d %H:%M:%S} - {df.ascii_comment(reason)}",
             "# m2-fishing wstawia te linie do quest/libs/fishing/fishing_drop.lua (fishing_drop_table).",
             "# przedmiot\tilosc\twedka_od\twedka_do\trodzaj\twaga", ""]
    for e in entries:
        line = "\t".join(str(e[k]) for k in ("item", "count", "rod_min", "rod_max", "tier", "weight"))
        comment = df.ascii_comment(e.get("comment", ""))
        lines.append(line + (f"\t# {comment}" if comment else ""))
    return ("\r\n".join(lines) + "\r\n").encode("ascii")


# ------------------------------------------------------------------- odds ---
def rod_level(vnum):
    return CARBON_LEVEL if int(vnum) == CARBON_ROD else (int(vnum) - ROD_BASE) // 10 + 1


def row_weight(e, level, rare, tuna):
    """fishing_drop.lua's row_weight: the line's weight for a rod level, the rare fish's multiplier x100 and whether
    Zloty Tunczyk may bite."""
    if not e["rod_min"] <= level <= e["rod_max"]:
        return 0
    w = e["weight"]
    if e["tier"] == 1:
        return w * (10 + (level - 1)) // 10
    if e["tier"] == 2:
        return 0 if rare <= 0 else w * (4 + max(0, level - 4)) * rare // 400
    if e["tier"] == 3:
        return w if tuna else 0
    return w


def chances(entries, level, rare=0, tuna=False):
    """[(entry index, %)] of one rod level - the quest's own draw."""
    allowed = [(i, row_weight(e, level, rare, tuna)) for i, e in enumerate(entries)]
    allowed = [(i, w) for i, w in allowed if w > 0]
    total = sum(w for _i, w in allowed)
    return {i: (100.0 * w / total if total else 0.0) for i, w in allowed}, total


def validate(entries, known_items):
    """Problems the game would hit, in Polish ([] = fine). known_items: the
    VNUMs item_proto has (None = not checked)."""
    problems = []
    if not entries:
        problems.append("Tabela nie może być pusta – wędka nie miałaby czego złowić.")
    for n, e in enumerate(entries, 1):
        if e["item"] != DYE and not e["item"].isdigit():
            problems.append(f"Wiersz {n}: „{e['item']}” to nie numer przedmiotu (ani „{DYE}”).")
        elif e["item"].isdigit() and known_items is not None and int(e["item"]) not in known_items:
            problems.append(f"Wiersz {n}: przedmiotu {e['item']} nie ma w grze.")
        for key, (low, high) in LIMITS.items():
            if not low <= e[key] <= high:
                problems.append(f"Wiersz {n}: {LABELS[key]} – dozwolone {low}–{high}.")
        if e["rod_min"] > e["rod_max"]:
            problems.append(f"Wiersz {n}: „od wędki” jest większe niż „do wędki”.")
    if not problems:
        for level in ROD_LEVELS:
            if not chances(entries, level)[1]:
                problems.append(f"Wędka poziomu {level} bez Rybich Wnętrzności nie złowiłaby nic – gra pokazałaby "
                                "błąd. Dodaj dla niej coś rodzaju 0 albo 1.")
    return problems


def form_entries(form):
    """The rows of the edit form -> (entries, errors)."""
    entries, errors = [], []
    try:
        count = min(500, int(form.get("row_count", "0")))
    except ValueError:
        count = 0
    for i in range(count):
        p = f"r{i}_"
        item = (form.get(p + "item") or "").strip().lower()
        if form.get(p + "delete") or not item:
            continue
        values = {}
        for key in ("count", "rod_min", "rod_max", "tier", "weight"):
            raw = (form.get(p + key) or "").strip()
            if not re.fullmatch(r"\d{1,10}", raw):
                errors.append(f"Wiersz {i + 1}: {LABELS[key]} – „{raw}” to nie liczba całkowita.")
                values[key] = 0
            else:
                values[key] = int(raw)
        entries.append(entry(item, comment=form.get(p + "comment", ""), **values))
    return entries, errors


# ------------------------------------------------------------------ pages ---
def install(bp, ctx):
    import dbeditor
    register_file()
    df.register(bp)
    tables_common.register(bp)
    rows, game_text, login_required = ctx["rows"], ctx["game_text"], ctx["login_required"]

    def base_entries(spool):
        text = df.read_text(df.base_path(spool, KEY))
        source = "game"
        if text is None:
            text, source = df.read_text(SNAPSHOT), "snapshot"
        return parse_lua(text or ""), source

    def current(spool):
        text = df.read_text(df.custom_path(spool, KEY))
        if text is not None and parse_custom(text):
            return parse_custom(text), "custom"
        entries, source = base_entries(spool)
        return entries, source

    def rod_info():
        """{level: {"vnum", "name", "chance"}} from item_proto (the bite chance 20 + value5)."""
        if "dbt_rods" in g:
            return g.dbt_rods
        info = {lv: {"vnum": ROD_BASE + 10 * (lv - 1), "name": f"Wędka+{lv}", "chance": 20 + lv // 2}
                for lv in ROD_LEVELS if lv != CARBON_LEVEL}
        info[CARBON_LEVEL] = {"vnum": CARBON_ROD, "name": "Wędka Węglowa", "chance": 32}
        try:
            for r in rows("SELECT vnum, locale_name, value5 FROM player.item_proto WHERE type=13 "
                          "AND vnum BETWEEN %s AND %s", (ROD_BASE, CARBON_ROD)):
                lv = rod_level(r["vnum"])
                if lv in info and (int(r["vnum"]) % 10 == 0 or int(r["vnum"]) == CARBON_ROD):
                    info[lv].update(name=game_text(r["locale_name"]) or info[lv]["name"],
                                    chance=20 + int(r.get("value5") or 0))
        except Exception:
            pass
        g.dbt_rods = info
        return info

    def decorate(entries):
        vnums = set()
        for e in entries:
            if e["item"].isdigit():
                vnums.add(int(e["item"]))
        vnums.update(DYE_VNUMS[:1])
        try:
            names = df.item_names(rows, game_text, sorted(vnums))
        except Exception:
            names = {}
        out = []
        for e in entries:
            if e["item"] == DYE:
                label, icon, bad = "Farba do włosów (losowy kolor)", df.icon_url(DYE_VNUMS[0]), False
            elif e["item"].isdigit():
                known = names.get(int(e["item"]))
                label = known["name"] if known else "NIEZNANY PRZEDMIOT"
                icon, bad = df.icon_url(e["item"]), known is None
            else:
                label, icon, bad = "?", None, True
            out.append(dict(e, label=label, icon=icon, bad=bad))
        return out, names

    @bp.route("/fishing")
    @login_required
    def fishing():
        spool = df.spool_dir()
        entries, source = current(spool)
        rods = rod_info()
        try:
            rare = int(request.args.get("rzadkie", "0"))
        except ValueError:
            rare = 0
        rare = rare if rare in dict(RARE) else 0
        tuna = request.args.get("tunczyk") == "1"
        lines, _names = decorate(entries)
        matrix, totals = {}, {}
        for lv in ROD_LEVELS:
            matrix[lv], totals[lv] = chances(entries, lv, rare, tuna)
        problems = validate(entries, None)
        backups = df.list_backups(spool, [KEY], 20)
        return render_template("dbeditor/fishing.html", lines=lines, source=source, rods=rods, levels=list(ROD_LEVELS),
                               matrix=matrix, totals=totals, rares=RARE, rare=rare, tuna=tuna, tiers=TIERS,
                               problems=problems, status=df.live_state(spool, KEY), backups=backups,
                               pending=[1] if df.live_state(spool, KEY)["pending"] else [], rod_max=ROD_MAX,
                               dye=DYE, csrf=df.csrf_token())

    @bp.post("/fishing")
    @login_required
    def fishing_save():
        spool = df.spool_dir()
        if not df.csrf_ok(request.form):
            flash("Sesja formularza wygasła – odśwież stronę i spróbuj jeszcze raz.", "error")
            return redirect(url_for("dbeditor.fishing"))
        action = request.form.get("action", "save")
        try:
            if action == "reset":
                df.write_custom(spool, KEY, None, "przywrocono tabele z obrazu gry")
                flash("Łowienie wróci do tabeli z obrazu gry po restarcie (Zastosuj).", "success")
                return redirect(url_for("dbeditor.fishing"))
            if action == "restore":
                df.restore_backup(spool, KEY, request.form.get("name", ""))
                flash("Przywrócono kopię. Działa po restarcie (Zastosuj).", "success")
                return redirect(url_for("dbeditor.fishing"))
        except (OSError, ValueError) as exc:
            flash(f"Nie udało się: {exc}", "error")
            return redirect(url_for("dbeditor.fishing"))
        entries, errors = form_entries(request.form)
        rods = rod_info()
        vnums = sorted({int(e["item"]) for e in entries if e["item"].isdigit()})
        try:
            known = set(df.item_names(rows, game_text, vnums)) if vnums else set()
        except Exception:
            known = None
            flash("Nie udało się sprawdzić przedmiotów w bazie – sprawdzi je gra przy starcie.", "warning")
        problems = errors or validate(entries, known)
        if problems:
            for problem in problems[:12]:
                flash(problem, "error")
            flash("Nic nie zapisano – popraw tabelę.", "error")
            return redirect(url_for("dbeditor.fishing"))
        base, _source = base_entries(spool)
        key = lambda es: [(e["item"], e["count"], e["rod_min"], e["rod_max"], e["tier"], e["weight"]) for e in es]
        try:
            if key(entries) == key(base):
                df.write_custom(spool, KEY, None, "tabela taka jak w obrazie gry")
            else:
                df.write_custom(spool, KEY, render_custom(entries, request.form.get("note", "") or "zmiana w panelu"),
                                request.form.get("note", "") or "zmiana tabeli lowienia")
        except OSError as exc:
            flash(f"Nie udało się zapisać pliku w wolumenie spool: {exc}", "error")
            return redirect(url_for("dbeditor.fishing"))
        flash(f"Zapisano tabelę łowienia ({len(entries)} pozycji). Gra wczyta ją po restarcie (Zastosuj).", "success")
        return redirect(url_for("dbeditor.fishing"))

    dbeditor.add_section("dbeditor.fishing", "🎣", "Łowienie ryb",
                         "co i jak często łowi każda wędka +1…+20 i Węglowa, ryby i skarby")
