"""MT2009_PLUS_DB_EDITOR_CRAFTING_V1: "Wytwarzanie przedmiotów" - the crafting
window most NPCs open with their "Wytwarzanie" talk (Kowal, Baek-Go,
Heuk-Young, Octavio, Uriel, the arrow sellers, the guild alchemists ...): a list of
things to make, sorted into categories, with a search box, the quantity,
the chance, the yang price and "Wytwórz". (Only Seon-Pyeong uses the old
cube window - that one is cube.py.)

Where each piece lives:

  * The recipes: world.crafting_proto (vnum, item_vnum, count, price,
    chance, recipe "vnum,count,vnum,count..." - up to
    CRAFTING_MATERIAL_MAX_NUM = 10 materials, req_progress, req_level,
    recipe_vnum). The db core reads it while it boots
    (ClientManagerBoot.cpp InitializeCraftingTable) and hands it to every game
    core (CCraftingManager); the quests read one recipe with
    get_crafting_data / get_crafting_recipe. Edited here through
    common_items (history with undo, "Zastosuj", export / import, the
    world reset's replay).
  * Which recipes a window lists: the quest library
    quest/libs/crafting/crafting_data.lua - crafting_data[<window>] = {recipe
    vnums}; the window number is what the NPC's quest passes to
    crafting.open() (crafting.lua, herbalism, horse_crafting,
    black_steel_crafting, guild_building_melt - WINDOWS below). This part
    keeps the operator's changes to those lists in world.crafting_window
    (craft_vnum, recipe_vnum, present: 1 = added to the image's list, 0 =
    taken off it) - only the differences, so a world reset (the image's
    dumps again) plus the history's replay gives the same lists. The game's
    bin/m2-crafting (m2-supervise, before the cores boot) reads the table and
    appends them to the live crafting_data.lua as calls of a small Lua
    function; the quests and the client window stay as they were. It
    publishes the image's file as <spool>/crafting/crafting_data.base.lua
    (until then the panel uses dbeditor/crafting_data.snapshot.lua) and how
    the last boot went as <spool>/crafting/status.
  * The categories: the CLIENT decides them (root/uicraft.py,
    CRAFTING_CATEGORIES_BY_VNUM) from the window number and the result item
    - Kowal (101): untradeable (ANTIFLAG_MYSHOP) / tradeable; Baek-Go (102):
    item value1 1/2/3 = Wzmacniające / Ofensywne / Defensywne, else Inne;
    Heuk-Young (104): recipes 100-102 "Zwoje i Marmury", 104 "Wymiany", else
    "Inne"; every other window: weapons / armours / "Inne". The page shows
    the category each recipe will land in; changing the rules would need a
    new client.
  * The client gets the list from the server when the window opens
    ("craft_recipe" / "craft_avail" chat commands); names and icons come
    from its own item_proto, so a result or material item must also be in
    the client's data (the Przedmioty part's client data zip).

Live: crafting_proto and the lists are read at boot, so a change works after
"Zastosuj" (restart of the cores).
"""
import json
import re
from pathlib import Path

from flask import flash, redirect, render_template, request, url_for

from dbeditor import common_items as common
from dbeditor import tables_common

MARK = "MT2009_PLUS_DB_EDITOR_CRAFTING_V1"
PROTO = "world.crafting_proto"
WINDOW = "world.crafting_window"
FOLDER = "crafting"
BASE_NAME = "crafting_data.base.lua"
SNAPSHOT = Path(__file__).resolve().parent / "crafting_data.snapshot.lua"   # the image's file, 6 Oct 2026
MATERIALS_MAX = 10                       # CRAFTING_MATERIAL_MAX_NUM (common/item_length.h)
RECIPE_TEXT_MAX = 255                    # crafting_proto.recipe varchar(255)
INT_MAX = 2147483647                     # int(10) columns
ANTIFLAG_MYSHOP = 1 << 16                # ITEM_ANTIFLAG_MYSHOP (server and client)
HISTORY_SHOWN = 15

ROW_COLS = ("vnum", "item_vnum", "count", "price", "chance", "recipe", "req_progress", "req_level", "recipe_vnum")
WINDOW_COLS = ("craft_vnum", "recipe_vnum", "present")


def _spec(low, high, label):
    return {"kind": "int", "min": low, "max": high, "label": label}


SPECS = {
    "item_vnum": _spec(1, INT_MAX, "Wynik (przedmiot)"),
    "count": _spec(1, 10000, "Ilość wyniku"),
    "price": _spec(0, 2000000000, "Koszt (Yang)"),
    "chance": _spec(0, 100, "Szansa %"),
    "recipe": {"kind": "ascii", "max": RECIPE_TEXT_MAX, "label": "Składniki"},
    "req_progress": _spec(0, 100000, "Wymagany postęp receptury"),
    "req_level": _spec(0, 255, "Wymagany poziom"),      # TCraftingItem::reqLevel is a BYTE
    "recipe_vnum": _spec(0, INT_MAX, "Receptura (licznik postępu)"),
}
FORM_FIELDS = ("item_vnum", "count", "price", "chance", "req_level", "req_progress", "recipe_vnum")

# The windows: what the NPCs' quests pass to crafting.open() (the image's quests, 6 Oct 2026).
# (window, NPC vnums, quest, note, client category set)
GUILD_ALCHEMISTS = tuple(range(20060, 20073))
WINDOWS = (
    (101, (20016,), "crafting_manage", "rozmowa „Wytwarzanie”", "tradeable"),
    (102, (20018,), "herbalism", "po wstępie do zielarstwa; boty-zielarze robią przepisy 11–95 bez okna", "herb"),
    (103, (20008,), "crafting_manage", "", "default"),
    (104, (20090,), "crafting_manage", "", "sura"),
    (105, (20349,), "horse_crafting", "od poziomu 25", "default"),
    (106, (11001, 11003, 11005), "crafting_manage", "rozmowa o strzałach", "default"),
    (107, (20402,), "black_steel_crafting", "po ukończeniu questa Czarnej Stali", "default"),
    (108, (20364,), "crafting_manage", "", "default"),
    (109, (20001,), "crafting_manage", "rozmowa o kruszcu", "default"),
    (110, (20041,), "crafting_manage", "", "default"),
    # MT2009_PLUS_SASH_CLOTH_V1: Uriel - 10 Delikatne Sukno + 80 000 Yang -> Szarfa Władcy +0 (85001);
    # the window and its list come from game/Dockerfile (crafting_data.lua, CRAFTING_URIEL).
    (111, (20011,), "acce_costume_uriel", "rozmowa „Wytwarzanie” – szarfa z Delikatnego Sukna", "default"),
) + tuple((v, (v,), "guild_building_melt", "alchemik gildii (−5% ceny dla własnej gildii przy 50621–50633)", "default")
          for v in GUILD_ALCHEMISTS)
WINDOW_BY_VNUM = {w[0]: w for w in WINDOWS}

# root/uicraft.py: the window's categories, in the client's order; the first that fits wins.
CATEGORY_SETS = {
    "tradeable": (("Niehandlowalne", lambda r, it: bool(it.get("antiflag", 0) & ANTIFLAG_MYSHOP)),
                  ("Handlowalne", None)),
    "herb": (("Wzmacniające", lambda r, it: it.get("value1") == 1),
             ("Ofensywne", lambda r, it: it.get("value1") == 2),
             ("Defensywne", lambda r, it: it.get("value1") == 3),
             ("Inne", None)),
    "sura": (("Zwoje i Marmury", lambda r, it: r in (100, 101, 102)),
             ("Wymiany", lambda r, it: r == 104),
             ("Inne", None)),
    "default": (("Bronie", lambda r, it: it.get("type") == 1),
                ("Pancerze", lambda r, it: it.get("type") == 2 and it.get("subtype") == 0),
                ("Inne", None)),
}
CATEGORY_RULES = {
    "tradeable": "Niehandlowalne = wynik ma zakaz sprzedaży w sklepiku (ANTIFLAG_MYSHOP), reszta Handlowalne.",
    "herb": "Kategoria z wartości value1 wyniku: 1 Wzmacniające, 2 Ofensywne, 3 Defensywne, inne – Inne.",
    "sura": "Przepisy nr 100, 101, 102 – „Zwoje i Marmury”, nr 104 – „Wymiany”, reszta – „Inne”.",
    "default": "Broń (typ 1) – Bronie, pancerz (typ 2, podtyp 0) – Pancerze, reszta – Inne.",
}

_STATE = {"window_table": False}


# ------------------------------------------------------------------ pure ---
def window_kind(craft_vnum):
    return {101: "tradeable", 102: "herb", 104: "sura"}.get(int(craft_vnum), "default")


def category(craft_vnum, recipe_vnum, item):
    """The category the client puts the recipe in (uicraft.py __CanAddItemToCategory)."""
    for name, test in CATEGORY_SETS[window_kind(craft_vnum)]:
        if test is None or test(int(recipe_vnum), item or {}):
            return name
    return "Inne"


def categories(craft_vnum):
    return [name for name, _t in CATEGORY_SETS[window_kind(craft_vnum)]]


def parse_materials(text):
    """crafting_proto.recipe -> ([(vnum, count)], error or None), the way the db
    core reads it (pairs of comma tokens, at most CRAFTING_MATERIAL_MAX_NUM;
    get_crafting_recipe stops at the first vnum or count 0)."""
    text = str(text or "").strip()
    if not text:
        return [], None
    parts = [p.strip() for p in text.split(",")]
    if any(not re.fullmatch(r"\d{1,10}", p) for p in parts):
        return [], "składniki: tylko liczby rozdzielone przecinkami"
    if len(parts) % 2:
        return [], "składniki: para „przedmiot, ilość” bez ilości"
    pairs = [(int(parts[i]), int(parts[i + 1])) for i in range(0, len(parts), 2)]
    if len(pairs) > MATERIALS_MAX:
        return pairs, f"najwyżej {MATERIALS_MAX} składników (gra czyta tylko tyle)"
    for vnum, count in pairs:
        if vnum <= 0 or count <= 0:
            return pairs, "składnik z numerem lub ilością 0 – gra ucięłaby na nim listę"
        if vnum > INT_MAX or count > 1000000:
            return pairs, "składnik: liczba poza zakresem"
    return pairs, None


def format_materials(pairs):
    return ",".join(f"{int(v)},{int(c)}" for v, c in pairs)


def _strip_comments(text):
    text = re.sub(r"--\[\[.*?\]\]", " ", text, flags=re.S)
    return re.sub(r"--[^\n]*", " ", text)


def parse_lua(text):
    """crafting_data.lua -> {window: [recipe vnums]} of its crafting_data table
    (constants CRAFTING_X = N resolved, comments - including the --[[ ]] block
    of Baek-Go's PvP dews - left out)."""
    text = _strip_comments((text or "").replace("\r", ""))
    consts = {m.group(1): int(m.group(2)) for m in re.finditer(r"^\s*([A-Z_][A-Z0-9_]*)\s*=\s*(\d+)\s*$", text, re.M)}
    start = re.search(r"^\s*crafting_data\s*=\s*\{", text, re.M)
    if not start:
        return {}
    body, depth, i = [], 1, start.end()
    while i < len(text) and depth:
        ch = text[i]
        depth += 1 if ch == "{" else -1 if ch == "}" else 0
        if depth:
            body.append(ch)
        i += 1
    lists = {}
    for m in re.finditer(r"\[\s*([A-Za-z_][A-Za-z0-9_]*|\d+)\s*\]\s*=\s*\{([^}]*)\}", "".join(body)):
        key = m.group(1)
        window = int(key) if key.isdigit() else consts.get(key)
        if window is None:
            continue
        lists[window] = [int(v) for v in re.findall(r"\d+", m.group(2))]
    return lists


def effective(base, rows):
    """The window lists the game will have: the image's lists with the table's
    rows applied (present 1 added at the end, 0 taken off) - what
    m2-crafting's Lua does."""
    lists = {w: list(v) for w, v in base.items()}
    for row in sorted(rows, key=lambda r: (int(r["craft_vnum"]), int(r["recipe_vnum"]))):
        w, r = int(row["craft_vnum"]), int(row["recipe_vnum"])
        current = lists.setdefault(w, [])
        if int(row["present"]):
            if r not in current:
                current.append(r)
        elif r in current:
            current[:] = [x for x in current if x != r]
    return lists


def window_ops(base, rows, craft_vnum, recipe_vnum, wanted):
    """(inserts, deletes) on world.crafting_window so that the recipe is
    (wanted True) or is not on the window's list."""
    w, r = int(craft_vnum), int(recipe_vnum)
    in_base = r in base.get(w, [])
    row = next((x for x in rows if int(x["craft_vnum"]) == w and int(x["recipe_vnum"]) == r), None)
    key = {"craft_vnum": w, "recipe_vnum": r}
    inserts, deletes = [], []
    if row is not None:
        deletes.append(dict(key, present=int(row["present"])))
    if wanted and not in_base:
        inserts.append(dict(key, present=1))
    elif not wanted and in_base:
        inserts.append(dict(key, present=0))
    if row is not None and inserts and int(inserts[0]["present"]) == int(row["present"]):
        return [], []                   # already so
    if row is None and not inserts:
        return [], []
    return inserts, deletes


def window_title(craft_vnum, mob_names=None):
    meta = WINDOW_BY_VNUM.get(int(craft_vnum))
    names = mob_names or {}
    if not meta:
        return f"Okno {craft_vnum} (żaden znany quest go nie otwiera)"
    first = names.get(meta[1][0]) or f"NPC {meta[1][0]}"
    return first + (f" (+{len(meta[1]) - 1})" if len(meta[1]) > 1 else "")


def import_row_errors(part, new):
    """config.py import: what a whole row must satisfy beyond the column types."""
    if not new:
        return []
    if part == "crafting":
        errors = []
        if not 1 <= new["vnum"] <= INT_MAX:
            errors.append(f"numer przepisu {new['vnum']} poza 1…{INT_MAX}")
        _pairs, error = parse_materials(new["recipe"])
        if error:
            errors.append(error)
        return errors
    if part == "crafting_win":
        ensure_window_table()
        if new["present"] not in (0, 1):
            return ["present musi być 0 albo 1"]
    return []


def check_recipe(values, known_items=None):
    """(errors, warnings) of one recipe as the form gives it."""
    errors, warnings = [], []
    pairs, error = parse_materials(values.get("recipe", ""))
    if error:
        errors.append(error)
    if not pairs:
        warnings.append("Przepis bez składników – gra da wynik za samo Yang.")
    if known_items is not None:
        for v in [values.get("item_vnum")] + [v for v, _c in pairs]:
            if v and v not in known_items:
                errors.append(f"Nie ma przedmiotu {v} w item_proto.")
    if values.get("chance") == 0:
        warnings.append("Szansa 0% – wytwarzanie zawsze się nie uda (składniki i Yang przepadają).")
    if values.get("req_progress", 0) > 0 and not values.get("recipe_vnum"):
        errors.append("Wymagany postęp > 0 bez numeru receptury – nikt nie spełni warunku.")
    return errors, warnings


# --------------------------------------------------------------- database ---
def _rows(sql, params=()):
    return common.ctx()["rows"](sql, params)


def ensure_window_table():
    if _STATE["window_table"]:
        return
    _rows(f"CREATE TABLE IF NOT EXISTS {WINDOW} (craft_vnum INT UNSIGNED NOT NULL, recipe_vnum INT UNSIGNED NOT NULL, "
          "present TINYINT UNSIGNED NOT NULL DEFAULT 1, PRIMARY KEY (craft_vnum, recipe_vnum)) ENGINE=InnoDB")
    _STATE["window_table"] = True


def load_recipes():
    found = _rows(f"SELECT {', '.join('`%s`' % c for c in ROW_COLS)} FROM {PROTO} ORDER BY vnum")
    out = {}
    for row in found:
        rec = {c: (common.text_of(row[c]) or "") if c == "recipe" else int(row[c] or 0) for c in ROW_COLS}
        rec["materials"], rec["materials_error"] = parse_materials(rec["recipe"])
        out[rec["vnum"]] = rec
    return out


def load_window_rows():
    ensure_window_table()
    return [{c: int(r[c]) for c in WINDOW_COLS}
            for r in _rows(f"SELECT craft_vnum, recipe_vnum, present FROM {WINDOW} ORDER BY craft_vnum, recipe_vnum")]


def item_info(vnums):
    """{vnum: {name, type, subtype, antiflag, value1}} from item_proto."""
    wanted = sorted({int(v) for v in vnums if v})
    out = {}
    for start in range(0, len(wanted), 500):
        chunk = wanted[start:start + 500]
        marks = ",".join(["%s"] * len(chunk))
        for row in _rows(f"SELECT vnum, CAST(locale_name AS BINARY) AS locale_name, type, subtype, antiflag, value1 "
                         f"FROM world.item_proto WHERE vnum IN ({marks})", chunk):
            def num(key):
                try:
                    return int(row.get(key) or 0)
                except (TypeError, ValueError):
                    return 0
            out[int(row["vnum"])] = {"name": (common.text_of(row["locale_name"]) or "").strip() or f"#{row['vnum']}",
                                     "type": num("type"), "subtype": num("subtype"), "antiflag": num("antiflag"),
                                     "value1": num("value1")}
    return out


def mob_names(vnums):
    wanted = sorted({int(v) for v in vnums})
    if not wanted:
        return {}
    marks = ",".join(["%s"] * len(wanted))
    try:
        found = _rows(f"SELECT vnum, CAST(locale_name AS BINARY) AS locale_name FROM player.mob_proto WHERE vnum IN ({marks})",
                      wanted)
    except Exception:
        return {}
    return {int(r["vnum"]): (common.text_of(r["locale_name"]) or "").strip() for r in found}


# ------------------------------------------------------------- the files ---
def spool_dir():
    from dbeditor import dropfiles as df
    return df.spool_dir()


def base_lists(spool=None):
    """(the image's window lists, "game" | "snapshot")."""
    try:
        path = Path(spool or spool_dir()) / FOLDER / BASE_NAME
        text = path.read_bytes().decode("latin-1")
        lists = parse_lua(text)
        if lists:
            return lists, "game"
    except OSError:
        pass
    return parse_lua(SNAPSHOT.read_bytes().decode("latin-1")), "snapshot"


def game_status(spool=None):
    status = {}
    try:
        for line in (Path(spool or spool_dir()) / FOLDER / "status").read_text(encoding="utf-8", errors="replace").splitlines():
            key, sep, value = line.partition("=")
            if sep:
                status[key.strip()] = value.strip()
    except OSError:
        return None
    if status.get("time", "").isdigit():
        from datetime import datetime
        status["when"] = datetime.fromtimestamp(int(status["time"])).strftime("%Y-%m-%d %H:%M")
    return status


# ---------------------------------------------------------------- history ---
def _formatter(col, value):
    if col != common.ROW_COL or not value:
        return None
    row = json.loads(value)
    if "present" in row:
        return (f"przepis #{row['recipe_vnum']} " + ("dodany do okna" if row["present"] else "zdjęty z okna")
                + f" {row['craft_vnum']}")
    return (f"przepis #{row['vnum']}: {row['item_vnum']} ×{row['count']} z [{row['recipe']}], "
            f"{row['price']} Yang, {row['chance']}%, poz. {row['req_level']}")


def register_tables():
    common.register_table(PROTO, "vnum", SPECS, "Wytwarzanie – przepis", "dbeditor.crafting_recipe",
                          formatter=_formatter, row_cols=ROW_COLS, row_label="cały przepis (nowy / usunięty)",
                          row_text=("recipe",))
    common.register_table(WINDOW, ("craft_vnum", "recipe_vnum"), {}, "Wytwarzanie – lista okna NPC", "dbeditor.crafting",
                          formatter=_formatter, row_cols=WINDOW_COLS, row_label="przepis na liście okna")


def history(limit=HISTORY_SHOWN):
    merged = {}
    for table in (PROTO, WINDOW):
        for b in common.history_batches(limit, table):
            if b["batch"] in merged:
                merged[b["batch"]]["rows"] += b["rows"]
                merged[b["batch"]]["fields"] += b["fields"]
            else:
                merged[b["batch"]] = b
    return sorted(merged.values(), key=lambda b: -int(b["first_id"]))[:limit]


# ------------------------------------------------------------------ pages ---
def install(bp, ctx):
    import dbeditor

    common.init(ctx)
    register_tables()
    common.install_history(bp, ctx)
    tables_common.register(bp)
    login_required = ctx["login_required"]

    def icon(vnum):
        from dbeditor import dropfiles as df
        return df.icon_url(vnum)

    def state():
        recipes = load_recipes()
        rows = load_window_rows()
        base, base_source = base_lists()
        lists = effective(base, rows)
        return recipes, rows, base, base_source, lists

    def windows_of(lists, recipe_vnum):
        return sorted(w for w, v in lists.items() if recipe_vnum in v)

    def pending():
        try:
            return [c for c in common.pending_changes() if c["tbl"] in (PROTO, WINDOW)]
        except Exception:
            return []

    def decorate(rec, items, craft_vnum=None):
        it = items.get(rec["item_vnum"])
        return dict(rec, result_name=it["name"] if it else "NIEZNANY PRZEDMIOT", result_bad=it is None,
                    result_icon=icon(rec["item_vnum"]),
                    mats=[{"vnum": v, "count": c, "name": items[v]["name"] if v in items else "NIEZNANY PRZEDMIOT",
                           "bad": v not in items, "icon": icon(v)} for v, c in rec["materials"]],
                    category=category(craft_vnum, rec["vnum"], it) if craft_vnum else None)

    def label_of(recipes, items):
        def label(key):
            parts = str(key).split(":")
            rec = recipes.get(int(parts[-1]))
            name = items.get(rec["item_vnum"], {}).get("name") if rec else None
            text = name or f"przepis #{parts[-1]}"
            return f"okno {parts[0]}: {text}" if len(parts) == 2 else text
        return label

    def back(window=None, recipe=None):
        if recipe is not None:
            return redirect(url_for("dbeditor.crafting_recipe", vnum=recipe))
        return redirect(url_for("dbeditor.crafting", okno=window) if window is not None else url_for("dbeditor.crafting"))

    @bp.route("/wytwarzanie-przedmiotow")
    @login_required
    def crafting():
        raw = request.args.get("okno", request.args.get("vnum", ""))
        try:
            recipes, rows, base, base_source, lists = state()
        except Exception as exc:
            flash(f"Nie udało się odczytać przepisów z bazy: {exc}", "error")
            return render_template("dbeditor/crafting.html", error=str(exc), windows=[], selected=None, recipes=[],
                                   groups=[], pending=[], status=None, history=[], base_source="?",
                                   dbe_csrf=common.csrf_token(), num=tables_common.num_text, **common.template_helpers())
        known = sorted(set(lists) | set(WINDOW_BY_VNUM))
        npcs = mob_names({n for w in known for n in WINDOW_BY_VNUM.get(w, (w, (w,)))[1]})
        items = item_info({r["item_vnum"] for r in recipes.values()} | {v for r in recipes.values() for v, _c in r["materials"]})
        windows = []
        for w in known:
            meta = WINDOW_BY_VNUM.get(w)
            windows.append({"vnum": w, "title": window_title(w, npcs), "count": len(lists.get(w, [])),
                            "missing": [r for r in lists.get(w, []) if r not in recipes],
                            "changed": any(r["craft_vnum"] == w for r in rows),
                            "npcs": [(n, npcs.get(n) or f"NPC {n}") for n in (meta[1] if meta else ())],
                            "quest": meta[2] if meta else "", "note": meta[3] if meta else "",
                            "guild": w in GUILD_ALCHEMISTS})
        selected = int(raw) if raw.isdigit() else (windows[0]["vnum"] if windows else 0)
        in_any = {r for v in lists.values() for r in v}
        groups, listed, missing = [], [], []
        if selected:
            listed = lists.get(selected, [])
            by_cat = {name: [] for name in categories(selected)}
            for r in listed:
                if r not in recipes:
                    missing.append(r)
                    continue
                rec = decorate(recipes[r], items, selected)
                rec["windows"] = windows_of(lists, r)
                rec["in_base"] = r in base.get(selected, [])
                by_cat.setdefault(rec["category"], []).append(rec)
            groups = [{"name": n, "recipes": v} for n, v in by_cat.items()]
            others = [decorate(recipes[r], items) for r in sorted(recipes) if r not in listed]
        else:  # "0": every recipe, with the windows listing it
            others = []
            for r in sorted(recipes):
                rec = decorate(recipes[r], items)
                rec["windows"] = windows_of(lists, r)
                others.append(rec)
        try:
            batches = history()
        except Exception:
            batches = []
        return render_template("dbeditor/crafting.html", error=None, windows=windows, selected=selected,
                               selected_window=next((w for w in windows if w["vnum"] == selected), None),
                               groups=groups, others=others, missing=missing, unlisted=len(set(recipes) - in_any),
                               total=len(recipes), rule=CATEGORY_RULES[window_kind(selected or 0)],
                               pending=pending(), status=game_status(), history=batches, base_source=base_source,
                               dbe_csrf=common.csrf_token(), num=tables_common.num_text, **common.template_helpers())

    def form_page(values, vnum=None, windows=(), errors=(), warnings=(), copy_of=None, back_window=None):
        recipes, _rows_, _base, _src, lists = state()
        pairs, _e = parse_materials(values.get("recipe", ""))
        items = item_info([values.get("item_vnum")] + [v for v, _c in pairs])
        known = sorted(set(lists) | set(WINDOW_BY_VNUM))
        npcs = mob_names({n for w in known for n in WINDOW_BY_VNUM.get(w, (w, (w,)))[1]})
        result_item = items.get(values.get("item_vnum") or 0)
        try:
            batches = [b for b in history(40) if any(str(r["row_key"]).split(":")[-1] == str(vnum) for r in b["rows"])] \
                if vnum is not None else []
        except Exception:
            batches = []
        return render_template("dbeditor/crafting_edit.html", values=values, vnum=vnum, copy_of=copy_of,
                               materials=pairs, slots=MATERIALS_MAX, names=items, icon=icon,
                               windows=[{"vnum": w, "title": window_title(w, npcs), "checked": w in windows,
                                         "category": category(w, values.get("vnum") or vnum or 0, result_item)}
                                        for w in known],
                               errors=errors, warnings=warnings, back_window=back_window, history=batches,
                               dbe_csrf=common.csrf_token(), specs=SPECS, **common.template_helpers())

    @bp.get("/wytwarzanie-przedmiotow/przepis/<int:vnum>")
    @login_required
    def crafting_recipe(vnum):
        recipes, _rows_, _base, _src, lists = state()
        if vnum not in recipes:
            flash(f"Nie ma przepisu #{vnum} (usunięty?).", "error")
            return back()
        return form_page(dict(recipes[vnum]), vnum=vnum, windows=windows_of(lists, vnum),
                         back_window=request.args.get("okno"))

    @bp.get("/wytwarzanie-przedmiotow/nowy")
    @login_required
    def crafting_new():
        recipes, _rows_, _base, _src, lists = state()
        window = request.args.get("okno", "")
        copy = request.args.get("kopia", "")
        if copy.isdigit() and int(copy) in recipes:
            values = dict(recipes[int(copy)])
            wins = windows_of(lists, int(copy))
        else:
            values = {"item_vnum": 0, "count": 1, "price": 0, "chance": 100, "recipe": "", "req_progress": 0,
                      "req_level": 0, "recipe_vnum": 0}
            wins = [int(window)] if window.isdigit() else []
        start = max([r for w in wins for r in lists.get(w, [])] or [max(recipes or [0])])
        free = start + 1
        while free in recipes:
            free += 1
        values["vnum"] = free
        return form_page(values, windows=wins, copy_of=int(copy) if copy.isdigit() else None,
                         back_window=window or (wins[0] if wins else None))

    def read_form(form):
        values, errors = {}, []
        for col in FORM_FIELDS:
            value, error = common.validate(SPECS[col], form.get(col, ""), SPECS[col]["label"])
            if error:
                errors.append(error)
            values[col] = value if value is not None else 0
        pairs = []
        for k in range(MATERIALS_MAX):
            v, c = (form.get(f"mv_{k}") or "").strip(), (form.get(f"mc_{k}") or "").strip()
            if not v and not c:
                continue
            v = v.split()[0].lstrip("#") if v else ""
            if not v.isdigit():
                errors.append(f"Składnik {k + 1}: podaj numer przedmiotu (VNUM) albo wybierz z listy.")
                continue
            count, error = common.validate({"kind": "int", "min": 1, "max": 1000000}, c or "1", f"Składnik {k + 1}: ilość")
            if error:
                errors.append(error)
                continue
            pairs.append((int(v), count))
        values["recipe"] = format_materials(pairs)
        if len(values["recipe"]) > RECIPE_TEXT_MAX:
            errors.append(f"Składniki: najwyżej {RECIPE_TEXT_MAX} znaków w bazie.")
        windows = sorted({int(w) for w in form.getlist("okna") if str(w).isdigit()})
        return values, pairs, windows, errors

    @bp.post("/wytwarzanie-przedmiotow/przepis")
    @login_required
    def crafting_save():
        if not common.check_csrf():
            return back()
        form = request.form
        note = (form.get("note") or "").strip()[:120]
        old_vnum = form.get("vnum_old", "")
        old_vnum = int(old_vnum) if old_vnum.isdigit() else None
        values, pairs, windows, errors = read_form(form)
        back_window = form.get("okno") or None
        if old_vnum is None:
            vnum, error = common.validate({"kind": "int", "min": 1, "max": INT_MAX}, form.get("vnum", ""), "Numer przepisu")
            if error:
                errors.append(error)
        else:
            vnum = old_vnum
        try:
            recipes, rows, base, _src, lists = state()
            items = item_info([values["item_vnum"]] + [v for v, _c in pairs])
        except Exception as exc:
            flash(f"Baza nie odpowiada: {exc}", "error")
            return back(back_window)
        if old_vnum is None and vnum in recipes:
            errors.append(f"Przepis #{vnum} już istnieje – wybierz inny numer.")
        if old_vnum is not None and old_vnum not in recipes:
            errors.append(f"Przepisu #{old_vnum} już nie ma.")
        more, warnings = check_recipe(values, set(items))
        errors += more
        if errors:
            for e in errors[:12]:
                flash(e, "error")
            flash("Nic nie zapisano – popraw przepis.", "error")
            return form_page(dict(values, vnum=vnum), vnum=old_vnum, windows=windows, back_window=back_window)
        named = dict(recipes)
        named[vnum] = dict(values, vnum=vnum)
        label = label_of(named, items)
        batch = common.uuid.uuid4().hex[:16]
        what = []
        try:
            if old_vnum is None:
                common.write_rows(PROTO, inserts=[dict(values, vnum=vnum)], note=note or "Wytwarzanie: nowy przepis",
                                  label_of=label, batch=batch)
                what.append("nowy przepis")
            else:
                cur = recipes[vnum]
                diff = {c: values[c] for c in FORM_FIELDS + ("recipe",) if cur[c] != values[c]}
                if diff:
                    common.save_rows(PROTO, [(vnum, diff)], note=note or "Wytwarzanie: zmiana przepisu",
                                     label_of=label, batch=batch)
                    what.append(f"{len(diff)} pól")
            inserts, deletes = [], []
            for w in sorted(set(windows) | set(windows_of(lists, vnum))):
                ins, dels = window_ops(base, rows, w, vnum, w in windows)
                inserts += ins
                deletes += dels
            if inserts or deletes:
                common.write_rows(WINDOW, inserts=inserts, deletes=deletes, note=note or "Wytwarzanie: listy okien",
                                  label_of=label, batch=batch)
                what.append("listy okien")
        except (LookupError, ValueError) as exc:
            flash(f"Nie zapisano: {exc}", "error")
            return back(back_window)
        except Exception as exc:
            flash(f"Baza odrzuciła zapis: {exc}", "error")
            return back(back_window)
        for w in warnings:
            flash(w, "warning")
        if not what:
            flash("Nic się nie zmieniło.", "info")
        else:
            flash(f"Zapisano przepis #{vnum} ({', '.join(what)}). Gra wczyta go po „Zastosuj” (restart rdzeni).", "success")
        if not windows:
            flash("Ten przepis nie jest na liście żadnego okna – gracze go nie zobaczą.", "warning")
        return back(int(back_window) if str(back_window or "").isdigit() else (windows[0] if windows else None))

    @bp.post("/wytwarzanie-przedmiotow/okno")
    @login_required
    def crafting_window():
        if not common.check_csrf():
            return back()
        form = request.form
        action = form.get("action", "")
        try:
            w, r = int(form.get("okno", "")), int(form.get("przepis", "").split()[0].lstrip("#"))
        except (ValueError, IndexError):
            flash("Wybierz okno i przepis.", "error")
            return back(form.get("okno") or None)
        try:
            recipes, rows, base, _src, lists = state()
            if action == "add" and r not in recipes:
                flash(f"Nie ma przepisu #{r}.", "error")
                return back(w)
            items = item_info([recipes[r]["item_vnum"]] if r in recipes else [])
            inserts, deletes = window_ops(base, rows, w, r, action == "add")
            if not inserts and not deletes:
                flash("Lista okna już taka jest.", "info")
                return back(w)
            common.write_rows(WINDOW, inserts=inserts, deletes=deletes,
                              note=("Wytwarzanie: przepis dodany do okna" if action == "add"
                                    else "Wytwarzanie: przepis zdjęty z okna"), label_of=label_of(recipes, items))
        except (LookupError, ValueError) as exc:
            flash(f"Nie zapisano: {exc}", "error")
            return back(w)
        except Exception as exc:
            flash(f"Baza odrzuciła zapis: {exc}", "error")
            return back(w)
        flash((f"Przepis #{r} dodany do okna {w}." if action == "add" else f"Przepis #{r} zdjęty z okna {w}.")
              + " Działa po „Zastosuj”.", "success")
        return back(w)

    @bp.post("/wytwarzanie-przedmiotow/usun")
    @login_required
    def crafting_delete():
        if not common.check_csrf():
            return back()
        form = request.form
        back_window = form.get("okno") or None
        try:
            vnum = int(form.get("vnum", ""))
            recipes, rows, base, _src, lists = state()
            if vnum not in recipes:
                flash(f"Przepisu #{vnum} już nie ma.", "error")
                return back(back_window)
            items = item_info([recipes[vnum]["item_vnum"]])
            label = label_of(recipes, items)
            batch = common.uuid.uuid4().hex[:16]
            note = "Wytwarzanie: usunięty przepis"
            inserts, deletes = [], []
            for w in windows_of(lists, vnum):
                ins, dels = window_ops(base, rows, w, vnum, False)
                inserts += ins
                deletes += dels
            if inserts or deletes:
                common.write_rows(WINDOW, inserts=inserts, deletes=deletes, note=note, label_of=label, batch=batch)
            common.write_rows(PROTO, deletes=[{"vnum": vnum}], note=note, label_of=label, batch=batch)
        except (LookupError, ValueError) as exc:
            flash(f"Nie usunięto: {exc}", "error")
            return back(back_window)
        except Exception as exc:
            flash(f"Baza odrzuciła zapis: {exc}", "error")
            return back(back_window)
        flash(f"Usunięto przepis #{vnum} (i zdjęto go z list okien). Cofnięcie: Historia niżej. Działa po „Zastosuj”.",
              "success")
        return back(back_window)

    dbeditor.add_section("dbeditor.crafting", "⚒️", "Wytwarzanie przedmiotów",
                         "okno „Wytwarzanie” u Kowala, Baek-Go, Heuk-Young i innych NPC: przepisy, składniki, "
                         "szansa, Yang, wymagania, co jest w którym oknie")
