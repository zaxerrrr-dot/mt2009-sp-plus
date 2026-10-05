"""MT2009_PLUS_DB_EDITOR_DRAGONSOUL_V1: "Alchemia (Smocze Kamienie)" - the
Dragon Soul table of the game.

Where it lives: share/locale/poland/dragon_soul_table.txt in the game image
(EUC-KR: the stone groups carry the package's Korean names; the game
Dockerfile already swaps its BasicApplys / AdditionalApplys groups for the
operator's balance, dragon_soul_applys.mt2009plus.txt). Every core reads it
once, when it boots (DragonSoulTable::ReadDragonSoulTableFile), and a stone's
bonuses are rolled when the stone is made or refined:
    value on the stone = ceil(Apply_value x weight / 100)
with the weight from WeightTables (grade x step x strength +0..+6).

The panel keeps the whole file: it edits the numbers in place in a copy of
the image's file (every line, comment and tab stays as it was) and writes it
into the spool both containers mount:
    <spool>/dragonsoul/dragon_soul_table.custom.txt
The game's m2-dragonsoul (bin/m2-dragonsoul, run by m2-supervise before the
cores boot) puts that file in place of the live one after checking its
structure (and that the stone list, VnumMapper, is the image's); a file that
fails is not used and <spool>/dragonsoul/status says why. The image's file
comes back as dragonsoul/dragon_soul_table.base.txt; until a game with
m2-dragonsoul has run, the panel shows its snapshot
(dbeditor/dragon_soul_table.snapshot.txt).

Backups, "pending" and the game's report use dropfiles.py's machinery (key
"dragonsoul"), so /db/apply lists it and the config export / import
(config.py, part "dragonsoul") carries and reverts it.
"""
import hashlib
import math
import re
from pathlib import Path

from flask import flash, redirect, render_template, request, url_for

from dbeditor import dropfiles as df
from dbeditor import tables_common
from dbeditor.items import POINT_LABELS

MARK = "MT2009_PLUS_DB_EDITOR_DRAGONSOUL_V1"
KEY = "dragonsoul"
FOLDER = "dragonsoul"
SNAPSHOT = Path(__file__).resolve().parent / "dragon_soul_table.snapshot.txt"   # the image's file, 5 Oct 2026
ENCODING = "euc_kr"
MAX_BYTES = 512 * 1024

GRADES = ("GRADE_NORMAL", "GRADE_BRILLIANT", "GRADE_RARE", "GRADE_ANCIENT", "GRADE_LEGENDARY", "GRADE_MYTH")
GRADE_NAMES = ("Zwykły", "Szlachetny", "Rzadki", "Pradawny", "Legendarny", "Mityczny")
STEPS = ("STEP_LOWEST", "STEP_LOW", "STEP_MID", "STEP_HIGH", "STEP_HIGHEST")
STEP_NAMES = ("Najniższy", "Niski", "Średni", "Wysoki", "Najwyższy")
STRENGTHS = tuple(range(7))
MATERIALS = ("MATERIAL_DS_REFINE_NORMAL", "MATERIAL_DS_REFINE_BLESSED", "MATERIAL_DS_REFINE_HOLLY")
MATERIAL_NAMES = ("Kamień ulepszenia", "Błogosławiony kamień ulepszenia", "Kamień ulepszenia Smoczego Boga")
APPLYNUM_ROWS = (("basis", "Stałe bonusy (liczba)"), ("add_min", "Losowe bonusy – najmniej"),
                 ("add_max", "Losowe bonusy – najwięcej"))
# the package's Korean stone names (VnumMapper) -> the Polish ones
STONE_NAMES = {"백룡석": "Diament", "화룡석": "Rubin", "풍룡석": "Jadeit", "철룡석": "Szafir", "뇌룡석": "Granat",
               "흑룡석": "Onyks", "성혼석": "Ametyst"}
REQUIRED_GROUPS = ("VnumMapper", "BasicApplys", "AdditionalApplys", "ApplyNumSettings", "WeightTables",
                   "RefineGradeTables", "RefineStepTables", "RefineStrengthTables", "DragonHeartExtTables",
                   "DragonSoulExtTables")
# dragon_soul_table.cpp FindDragonSoulApplyType: the name -> the POINT it gives
# (the ones that map to POINT_NONE in this engine are left out: they give nothing)
APPLY_POINTS = {
    "STR": "POINT_ST", "INT": "POINT_IQ", "DEX": "POINT_DX", "CON": "POINT_HT",
    "MAX_HP": "POINT_MAX_HP", "MAX_SP": "POINT_MAX_SP", "MAX_HP_PCT": "POINT_MAX_HP_PCT",
    "MAX_SP_PCT": "POINT_MAX_SP_PCT", "HP_REGEN": "POINT_HP_REGEN", "SP_REGEN": "POINT_SP_REGEN",
    "ATT_BONUS": "POINT_ATT_GRADE_BONUS", "DEF_BONUS": "POINT_DEF_GRADE_BONUS",
    "MAGIC_ATT_GRADE": "POINT_MAGIC_ATT_GRADE_BONUS", "MAGIC_DEF_GRADE": "POINT_MAGIC_DEF_GRADE_BONUS",
    "BLOCK": "POINT_BLOCK", "DODGE": "POINT_DODGE", "REFLECT_MELEE": "POINT_REFLECT_MELEE",
    "STEAL_HP": "POINT_STEAL_HP", "STEAL_SP": "POINT_STEAL_SP", "KILL_HP_RECOVER": "POINT_KILL_HP_RECOVERY",
    "KILL_SP_RECOVER": "POINT_KILL_SP_RECOVER", "SKILL_DAMAGE_BONUS": "POINT_SKILL_DAMAGE_BONUS",
    "SKILL_DEFEND_BONUS": "POINT_SKILL_DEFEND_BONUS", "NORMAL_HIT_DAMAGE_BONUS": "POINT_NORMAL_HIT_DAMAGE_BONUS",
    "NORMAL_HIT_DEFEND_BONUS": "POINT_NORMAL_HIT_DEFEND_BONUS", "RESIST_FIRE": "POINT_RESIST_FIRE",
    "RESIST_ELEC": "POINT_RESIST_ELEC", "RESIST_WIND": "POINT_RESIST_WIND", "RESIST_ICE": "POINT_RESIST_ICE",
    "RESIST_EARTH": "POINT_RESIST_EARTH", "RESIST_DARK": "POINT_RESIST_DARK",
    "RESIST_CRITICAL": "POINT_RESIST_CRITICAL", "RESIST_PENETRATE": "POINT_RESIST_PENETRATE",
    "RESIST_WARRIOR": "POINT_RESIST_WARRIOR", "RESIST_ASSASSIN": "POINT_RESIST_ASSASSIN",
    "RESIST_SURA": "POINT_RESIST_SURA", "RESIST_SHAMAN": "POINT_RESIST_SHAMAN",
    "ATTBONUS_DEVIL": "POINT_ATTBONUS_DEVIL", "ATTBONUS_STONE": "POINT_ATTBONUS_STONE",
    "ATTBONUS_HUMAN": "POINT_ATTBONUS_HUMAN", "ATTBONUS_ANIMAL": "POINT_ATTBONUS_ANIMAL",
    "ATTBONUS_ORC": "POINT_ATTBONUS_ORC", "ATTBONUS_MILGYO": "POINT_ATTBONUS_MILGYO",
    "ATTBONUS_UNDEAD": "POINT_ATTBONUS_UNDEAD", "ATTBONUS_MONSTER": "POINT_ATTBONUS_MONSTER",
    "CRITICAL_PCT": "POINT_CRITICAL_PCT", "PENETRATE_PCT": "POINT_PENETRATE_PCT",
    "ATT_BONUS_TO_WARRIOR": "POINT_ATTBONUS_WARRIOR", "ATT_BONUS_TO_ASSASSIN": "POINT_ATTBONUS_ASSASSIN",
    "ATT_BONUS_TO_SURA": "POINT_ATTBONUS_SURA", "ATT_BONUS_TO_SHAMAN": "POINT_ATTBONUS_SHAMAN",
}
SHORT_MAX = 32767           # the stone's attribute value is a short
WEIGHT_CAP = 1000           # a weight above 1000% is surely a typo
FEE_MAX = 2000000000
NUM_RE = re.compile(r"^\d{1,10}(\.\d{1,3})?$")
INT_RE = re.compile(r"^\d{1,10}$")
TOKEN_RE = re.compile(r"[^\t ]+")


# ----------------------------------------------------------------- parsing ---
def decode(data):
    """The file's bytes -> text whose characters are its bytes (latin-1):
    numbers and names are ASCII, the Korean group names stay byte for byte."""
    return data.decode("latin-1") if isinstance(data, (bytes, bytearray)) else (data or "")


def korean(name):
    try:
        return name.encode("latin-1").decode(ENCODING)
    except (UnicodeError, ValueError):
        return name


def stone_name(name):
    k = korean(name)
    return STONE_NAMES.get(k, k)


def apply_label(apply):
    point = APPLY_POINTS.get(apply)
    if point is None:
        return f"{apply} (nie działa w tej grze)"
    try:
        from dbeditor.attrs import POINT_NAMES
        number = POINT_NAMES.index(point) + 1
    except (ImportError, ValueError):
        return apply
    name, unit = POINT_LABELS.get(number, (apply, ""))
    return f"{name}{' (' + unit + ')' if unit == '%' else ''}"


def parse(text):
    """dragon_soul_table.txt -> the root group: {"name", "groups": {lower
    name: group}, "order": [names], "rows": [{"label", "values", "line"}]},
    the way CGroupTextParseTreeLoader reads it (# lines are comments)."""
    lines = decode(text).splitlines(keepends=True)
    root = {"name": "", "groups": {}, "order": [], "rows": [], "line": -1}
    stack, pending, problems = [root], None, []
    for i, raw in enumerate(lines):
        body = raw.strip()
        if not body or body.startswith("#"):
            continue
        tokens = body.split()
        if tokens[0].lower() == "group":
            if len(tokens) < 2:
                problems.append(f"linia {i + 1}: „Group” bez nazwy")
                continue
            pending = {"name": tokens[1], "groups": {}, "order": [], "rows": [], "line": i}
            continue
        if body.startswith("{"):
            if pending is None:
                problems.append(f"linia {i + 1}: „{{” bez „Group”")
                continue
            parent = stack[-1]
            parent["groups"][pending["name"].lower()] = pending
            parent["order"].append(pending["name"])
            stack.append(pending)
            pending = None
            continue
        if body.startswith("}"):
            if len(stack) == 1:
                problems.append(f"linia {i + 1}: nadmiarowe „}}”")
            else:
                stack.pop()
            continue
        stack[-1]["rows"].append({"label": tokens[0], "values": tokens[1:], "line": i})
    if len(stack) > 1:
        problems.append(f"grupa „{stack[-1]['name']}” nie jest zamknięta („}}”)")
    root["problems"] = problems
    root["lines"] = lines
    return root


def child(group, *path):
    for name in path:
        if group is None:
            return None
        group = group["groups"].get(name.lower())
    return group


def row(group, label):
    if group is None:
        return None
    for r in group["rows"]:
        if r["label"].lower() == label.lower():
            return r
    return None


def set_cell(lines, line, col, value):
    """Replaces the value number `col` (0 = the first after the row label)
    of one line, everything else of the line kept."""
    raw = lines[line]
    stripped = raw.rstrip("\r\n")
    end = raw[len(stripped):]
    spans = [m.span() for m in TOKEN_RE.finditer(stripped)]
    start, stop = spans[col + 1]
    lines[line] = stripped[:start] + str(value) + stripped[stop:] + end


def sha(data):
    return hashlib.sha256(data if isinstance(data, bytes) else decode(data).encode("latin-1")).hexdigest()[:16]


def fmt(value):
    """A number as the file writes it (no needless .0)."""
    if isinstance(value, float):
        text = f"{value:.3f}".rstrip("0").rstrip(".")
        return text or "0"
    return str(value)


# -------------------------------------------------------------- the model ---
def stones(root):
    """[(group name as in the file, Polish name, type)] of VnumMapper."""
    out = []
    for r in (child(root, "VnumMapper") or {"rows": []})["rows"]:
        if len(r["values"]) >= 2:
            out.append((r["values"][0], stone_name(r["values"][0]), r["values"][1]))
    return out


def cell(r, col, kind, label):
    """One editable value: {"id", "value", "kind", "label"}."""
    if r is None or col >= len(r["values"]):
        return None
    return {"id": f"c{r['line']}_{col}", "line": r["line"], "col": col, "value": r["values"][col], "kind": kind,
            "label": label}


def model(text):
    """What the page shows and edits."""
    root = parse(text)
    m = {"root": root, "stones": [], "applynum": [], "weights": [], "refine_grade": [], "refine_step": [],
         "refine_strength": [], "cells": {}}

    def add(c):
        if c is not None:
            m["cells"][c["id"]] = c
        return c

    for name, polish, _type in stones(root):
        stone = {"name": polish, "basic": [], "additional": []}
        for section, key, has_prob in (("BasicApplys", "basic", False), ("AdditionalApplys", "additional", True)):
            for r in (child(root, section, name) or {"rows": []})["rows"]:
                if not r["label"].isdigit() or len(r["values"]) < 2:
                    continue
                where = f"{polish}, {'stały' if key == 'basic' else 'losowy'} bonus {r['label']}"
                stone[key].append({
                    "n": r["label"], "apply": add(cell(r, 0, "apply", where + " – rodzaj")),
                    "name": apply_label(r["values"][0]),
                    "value": add(cell(r, 1, "value", where + " – wartość")),
                    "prob": add(cell(r, 2, "num", where + " – szansa")) if has_prob else None})
        m["stones"].append(stone)
    settings = child(root, "ApplyNumSettings", "Default")
    for label, polish in APPLYNUM_ROWS:
        r = row(settings, label)
        m["applynum"].append({"name": polish, "cells": [add(cell(r, g, "count", f"{polish} – {GRADE_NAMES[g]}"))
                                                        for g in range(len(GRADES))]})
    weights = child(root, "WeightTables", "Default")
    for g, grade in enumerate(GRADES):
        steps = []
        for s, step in enumerate(STEPS):
            r = row(child(weights, grade), step)
            steps.append({"name": STEP_NAMES[s], "cells": [
                add(cell(r, k, "weight", f"Waga: {GRADE_NAMES[g]}, {STEP_NAMES[s]}, +{k}")) for k in STRENGTHS]})
        m["weights"].append({"name": GRADE_NAMES[g], "steps": steps})
    refine = child(root, "RefineGradeTables", "Default")
    for g, grade in enumerate(GRADES[:-1]):
        r = row(refine, grade)
        m["refine_grade"].append({"name": GRADE_NAMES[g],
                                  "need": add(cell(r, 0, "need", f"Klasa {GRADE_NAMES[g]} – ile kamieni")),
                                  "fee": add(cell(r, 1, "fee", f"Klasa {GRADE_NAMES[g]} – koszt")),
                                  "probs": [add(cell(r, 2 + t, "num", f"Klasa {GRADE_NAMES[g]} → {GRADE_NAMES[t]}"))
                                            for t in range(len(GRADES))]})
    refine = child(root, "RefineStepTables", "Default")
    for s, step in enumerate(STEPS[:-1]):
        r = row(refine, step)
        m["refine_step"].append({"name": STEP_NAMES[s],
                                 "need": add(cell(r, 0, "need", f"Stopień {STEP_NAMES[s]} – ile kamieni")),
                                 "fee": add(cell(r, 1, "fee", f"Stopień {STEP_NAMES[s]} – koszt")),
                                 "probs": [add(cell(r, 2 + t, "num", f"Stopień {STEP_NAMES[s]} → {STEP_NAMES[t]}"))
                                           for t in range(len(STEPS))]})
    refine = child(root, "RefineStrengthTables", "Default")
    for k, material in enumerate(MATERIALS):
        r = row(refine, material)
        m["refine_strength"].append({"name": MATERIAL_NAMES[k],
                                     "fee": add(cell(r, 0, "fee", f"{MATERIAL_NAMES[k]} – koszt")),
                                     "probs": [add(cell(r, 1 + t, "num", f"{MATERIAL_NAMES[k]}: +{t} → +{t + 1}"))
                                               for t in range(6)]})
    return m


def max_weight(root):
    best = 0.0
    weights = child(root, "WeightTables", "Default")
    for grade in GRADES:
        for step in STEPS:
            r = row(child(weights, grade), step)
            for v in (r["values"] if r else []):
                try:
                    best = max(best, float(v))
                except ValueError:
                    pass
    return best or 100.0


def on_stone(value, weight):
    """The engine's ceil(value x weight / 100 - 0.01)."""
    return int(math.ceil(float(value) * float(weight) / 100.0 - 0.01))


# -------------------------------------------------------------- checking ---
def validate(text, base_text=None):
    """Problems the game would hit, in Polish ([] = fine) - the checks of
    DragonSoulTable::ReadDragonSoulTableFile and its Check* functions."""
    data = text if isinstance(text, bytes) else decode(text).encode("latin-1")
    if len(data) > MAX_BYTES:
        return [f"Plik jest za duży (ponad {MAX_BYTES // 1024} KB)."]
    root = parse(data)
    problems = list(root["problems"])
    for name in REQUIRED_GROUPS:
        if child(root, name) is None:
            problems.append(f"Brak grupy „{name}”.")
    if problems:
        return problems
    names = stones(root)
    if not names:
        problems.append("Grupa VnumMapper jest pusta.")
    if base_text is not None:
        base = parse(base_text)
        if [(n, t) for n, _p, t in stones(base)] != [(n, t) for n, _p, t in names]:
            problems.append("Lista kamieni (VnumMapper) różni się od pliku gry – tej grupy nie wolno zmieniać.")

    def number(v, integer=False):
        return bool((INT_RE if integer else NUM_RE).match(v))

    top = max_weight(root)
    for name, polish, _t in names:
        for section, need in (("BasicApplys", 2), ("AdditionalApplys", 3)):
            group = child(root, section, name)
            if group is None:
                problems.append(f"{section}: brak grupy kamienia {polish}.")
                continue
            rows = [r for r in group["rows"] if r["label"].isdigit()]
            labels = sorted(int(r["label"]) for r in rows)
            if labels != list(range(1, len(labels) + 1)):
                problems.append(f"{section} / {polish}: wiersze muszą być numerowane 1, 2, 3…")
            for r in rows:
                v = r["values"]
                where = f"{polish}, bonus {r['label']}"
                if len(v) < need:
                    problems.append(f"{where}: za mało kolumn.")
                    continue
                if v[0] not in APPLY_POINTS:
                    problems.append(f"{where}: nieznany bonus „{v[0]}”.")
                if not number(v[1], True):
                    problems.append(f"{where}: wartość „{v[1]}” musi być liczbą całkowitą.")
                elif on_stone(int(v[1]), top) > SHORT_MAX:
                    problems.append(f"{where}: wartość {v[1]} × {fmt(top)}% przekracza {SHORT_MAX}.")
                if need == 3 and not number(v[2]):
                    problems.append(f"{where}: szansa „{v[2]}” musi być liczbą.")
    settings = child(root, "ApplyNumSettings", "Default")
    for label, polish in APPLYNUM_ROWS:
        r = row(settings, label)
        if r is None or len(r["values"]) < len(GRADES) or not all(number(v, True) for v in r["values"][:6]):
            problems.append(f"ApplyNumSettings: wiersz „{label}” musi mieć 6 liczb całkowitych.")
        elif any(int(v) > 10 for v in r["values"][:6]):
            problems.append(f"ApplyNumSettings: {polish} – najwyżej 10.")
    lo, hi = row(settings, "add_min"), row(settings, "add_max")
    if lo and hi and all(number(v, True) for v in lo["values"][:6] + hi["values"][:6]):
        for g in range(len(GRADES)):
            if int(lo["values"][g]) > int(hi["values"][g]):
                problems.append(f"ApplyNumSettings: {GRADE_NAMES[g]} – „najmniej” większe niż „najwięcej”.")
    weights = child(root, "WeightTables", "Default")
    for g, grade in enumerate(GRADES):
        for step in STEPS:
            r = row(child(weights, grade), step)
            if r is None or len(r["values"]) < len(STRENGTHS) or not all(number(v) for v in r["values"][:7]):
                problems.append(f"WeightTables: {GRADE_NAMES[g]} / {step} musi mieć 7 liczb.")
            elif any(float(v) > WEIGHT_CAP for v in r["values"][:7]):
                problems.append(f"WeightTables: {GRADE_NAMES[g]} / {step} – waga ponad {WEIGHT_CAP}%.")
    for group, labels, size, title in (("RefineGradeTables", GRADES[:-1], 2 + len(GRADES), "Ulepszanie klasy"),
                                       ("RefineStepTables", STEPS[:-1], 2 + len(STEPS), "Ulepszanie stopnia")):
        node = child(root, group, "Default")
        for label in labels:
            r = row(node, label)
            if r is None or len(r["values"]) < size or not all(number(v) for v in r["values"][:size]):
                problems.append(f"{title}: wiersz {label} musi mieć {size} liczb.")
                continue
            if not number(r["values"][0], True) or int(r["values"][0]) < 1:
                problems.append(f"{title}: {label} – liczba kamieni co najmniej 1.")
            if not number(r["values"][1], True) or int(r["values"][1]) > FEE_MAX:
                problems.append(f"{title}: {label} – koszt musi być liczbą całkowitą do {FEE_MAX}.")
            if sum(float(v) for v in r["values"][2:size]) <= 0:
                problems.append(f"{title}: {label} – wszystkie szanse są zerowe.")
    node = child(root, "RefineStrengthTables", "Default")
    for k, material in enumerate(MATERIALS):
        r = row(node, material)
        if r is None or len(r["values"]) < 7 or not all(number(v) for v in r["values"][:7]):
            problems.append(f"Ulepszanie siły: {MATERIAL_NAMES[k]} musi mieć koszt i 6 szans.")
        elif not number(r["values"][0], True) or int(r["values"][0]) > FEE_MAX:
            problems.append(f"Ulepszanie siły: {MATERIAL_NAMES[k]} – koszt musi być liczbą całkowitą.")
        elif any(float(v) > 100 for v in r["values"][1:7]):
            problems.append(f"Ulepszanie siły: {MATERIAL_NAMES[k]} – szansa ponad 100%.")
    return problems


def check_value(c, raw):
    """(value text, error) of one form value."""
    raw = (raw or "").strip().replace(",", ".")
    if c["kind"] == "apply":
        return (raw, None) if raw in APPLY_POINTS else (raw, f"{c['label']}: nieznany bonus „{raw}”.")
    integer = c["kind"] in ("value", "count", "need", "fee")
    if not (INT_RE if integer else NUM_RE).match(raw):
        return raw, f"{c['label']}: „{raw}” to nie {'liczba całkowita' if integer else 'liczba'}."
    if not integer:
        raw = fmt(float(raw)) if "." in raw else str(int(raw))
    else:
        raw = str(int(raw))
    limit = {"count": 10, "need": 100, "fee": FEE_MAX, "weight": WEIGHT_CAP, "num": 1000000,
             "value": SHORT_MAX}[c["kind"]]
    if float(raw) > limit:
        return raw, f"{c['label']}: najwyżej {limit}."
    return raw, None


def apply_form(text, form):
    """The edit form -> (new text, changed cells, errors)."""
    m = model(text)
    lines = list(m["root"]["lines"])
    changed, errors = 0, []
    for cid, c in m["cells"].items():
        if cid not in form:
            continue
        value, error = check_value(c, form.get(cid))
        if error:
            errors.append(error)
            continue
        if value != c["value"]:
            set_cell(lines, c["line"], c["col"], value)
            changed += 1
    return "".join(lines), changed, errors


def multiply(text, factor, scope=("basic", "additional")):
    """Every bonus value of the stones (BasicApplys and/or AdditionalApplys)
    times factor, rounded, at least 1 -> (new text, changed values)."""
    m = model(text)
    lines = list(m["root"]["lines"])
    changed = 0
    for stone in m["stones"]:
        for key in scope:
            for b in stone[key]:
                c = b["value"]
                if c is None or not INT_RE.match(c["value"]):
                    continue
                old = int(c["value"])
                new = min(SHORT_MAX, max(1 if old else 0, int(math.floor(old * factor + 0.5))))
                if new != old:
                    set_cell(lines, c["line"], c["col"], new)
                    changed += 1
    return "".join(lines), changed


def scale_weights(text, factor):
    """Every weight of WeightTables times factor (0 stays 0: no further
    refine) -> (new text, changed values)."""
    m = model(text)
    lines = list(m["root"]["lines"])
    changed = 0
    for grade in m["weights"]:
        for step in grade["steps"]:
            for c in step["cells"]:
                if c is None or not NUM_RE.match(c["value"]) or float(c["value"]) == 0:
                    continue
                new = fmt(min(float(WEIGHT_CAP), round(float(c["value"]) * factor, 3)))
                new = str(int(float(new))) if float(new).is_integer() else new
                if new != c["value"]:
                    set_cell(lines, c["line"], c["col"], new)
                    changed += 1
    return "".join(lines), changed


def parse_factor(raw):
    """"2", "x2", "×1,5", "+100%", "200%" -> 2.0 / 1.5 / 2.0 / 2.0 (None = bad)."""
    raw = (raw or "").strip().lower().replace(",", ".").replace("×", "").replace("x", "").replace(" ", "")
    try:
        if raw.startswith(("+", "-")) and raw.endswith("%"):
            factor = 1.0 + float(raw[:-1]) / 100.0
        elif raw.endswith("%"):
            factor = float(raw[:-1]) / 100.0
        else:
            factor = float(raw)
    except ValueError:
        return None
    return factor if 0.01 <= factor <= 20 else None


def encode(text):
    return decode(text).encode("latin-1")


# ------------------------------------------------------------------ files ---
def register_file():
    """The file in dropfiles' table: custom path, status, backups and the
    "pending" list of /db/apply come with it."""
    df.FILES.setdefault(KEY, (FOLDER, "dragon_soul_table.custom.txt", "status",
                              "Alchemia (dragon_soul_table.txt)"))
    df.BASES.setdefault(KEY, (FOLDER, "dragon_soul_table.base.txt"))


def base_bytes(spool):
    try:
        return df.base_path(spool, KEY).read_bytes(), "game"
    except OSError:
        return SNAPSHOT.read_bytes(), "snapshot"


def current_bytes(spool):
    try:
        data = df.custom_path(spool, KEY).read_bytes()
        if b"BasicApplys" in data:
            return data, "custom"
    except OSError:
        pass
    return base_bytes(spool)


def save(spool, data, reason):
    """Writes the panel's file (None or the image's own bytes: no file)."""
    base, _source = base_bytes(spool)
    if data is None or data == base:
        return df.write_custom(spool, KEY, None, reason)
    return df.write_custom(spool, KEY, data, reason)


# ------------------------------------------------------------------ pages ---
def install(bp, ctx):
    import dbeditor
    register_file()
    df.register(bp)
    tables_common.register(bp)
    login_required = ctx["login_required"]

    def back():
        return redirect(url_for("dbeditor.dragonsoul"))

    @bp.route("/alchemia")
    @login_required
    def dragonsoul():
        spool = df.spool_dir()
        data, source = current_bytes(spool)
        base, base_source = base_bytes(spool)
        m = model(data)
        problems = validate(data, base)
        state = df.live_state(spool, KEY)
        top = max_weight(m["root"])
        return render_template("dbeditor/dragonsoul.html", m=m, source=source, base_source=base_source,
                               problems=problems, status=state, backups=df.list_backups(spool, [KEY], 20),
                               pending=[1] if state["pending"] else [], grades=GRADE_NAMES, steps=STEP_NAMES,
                               strengths=STRENGTHS, top=top, on_stone=on_stone, fmt=fmt,
                               applies=sorted(((a, apply_label(a)) for a in APPLY_POINTS), key=lambda p: p[1]),
                               sha=sha(data), csrf=df.csrf_token())

    @bp.post("/alchemia")
    @login_required
    def dragonsoul_save():
        spool = df.spool_dir()
        if not df.csrf_ok(request.form):
            flash("Sesja formularza wygasła – odśwież stronę i spróbuj jeszcze raz.", "error")
            return back()
        action = request.form.get("action", "save")
        note = (request.form.get("note") or "").strip()
        try:
            if action == "reset":
                save(spool, None, "przywrocono tabele alchemii z obrazu gry")
                flash("Alchemia wróci do tabeli z obrazu gry po restarcie (Zastosuj).", "success")
                return back()
            if action == "restore":
                df.restore_backup(spool, KEY, request.form.get("name", ""))
                flash("Przywrócono kopię. Działa po restarcie (Zastosuj).", "success")
                return back()
        except (OSError, ValueError) as exc:
            flash(f"Nie udało się: {exc}", "error")
            return back()
        data, _source = current_bytes(spool)
        base, _b = base_bytes(spool)
        if request.form.get("sha") != sha(data):
            flash("Tabela zmieniła się w międzyczasie (inny zapis albo nowa wersja gry) – odśwież stronę i "
                  "wprowadź zmiany jeszcze raz.", "error")
            return back()
        text = decode(data)
        if action == "multiply":
            factor = parse_factor(request.form.get("factor"))
            scope = {"basic": ("basic",), "additional": ("additional",)}.get(request.form.get("scope"),
                                                                            ("basic", "additional"))
            if factor is None:
                flash("Mnożnik musi być liczbą od 0,01 do 20 (np. 2, ×1,5, +100%, 200%).", "error")
                return back()
            text, changed = multiply(text, factor, scope)
            what = f"mnoznik bonusow x{fmt(factor)}"
        elif action == "weights":
            factor = parse_factor(request.form.get("factor"))
            if factor is None:
                flash("Mnożnik musi być liczbą od 0,01 do 20 (np. 2, ×1,5, +100%, 200%).", "error")
                return back()
            text, changed = scale_weights(text, factor)
            what = f"mnoznik wag x{fmt(factor)}"
        else:
            text, changed, errors = apply_form(text, request.form)
            if errors:
                for e in errors[:12]:
                    flash(e, "error")
                flash("Nic nie zapisano – popraw wartości.", "error")
                return back()
            what = "zmiana tabeli alchemii"
        if not changed:
            flash("Nic się nie zmieniło.", "info")
            return back()
        new = encode(text)
        problems = validate(new, base)
        if problems:
            for p in problems[:12]:
                flash(p, "error")
            flash("Nic nie zapisano – gra nie wczytałaby takiej tabeli.", "error")
            return back()
        try:
            save(spool, new, note or what)
        except OSError as exc:
            flash(f"Nie udało się zapisać pliku w wolumenie spool: {exc}", "error")
            return back()
        flash(f"Zapisano tabelę alchemii ({changed} zmienionych wartości). Gra wczyta ją po restarcie (Zastosuj); "
              "bonusy dostają kamienie stworzone lub ulepszone po restarcie.", "success")
        return back()

    @bp.get("/alchemia/plik")
    @login_required
    def dragonsoul_file():
        from flask import Response
        data, _source = current_bytes(df.spool_dir())
        return Response(data, mimetype="text/plain; charset=euc-kr",
                        headers={"Content-Disposition": "attachment; filename=dragon_soul_table.txt"})

    dbeditor.add_section("dbeditor.dragonsoul", "🐉", "Alchemia (Smocze Kamienie)",
                         "bonusy kamieni smoka, wagi stopni i siły, szanse i koszty ulepszania, mnożnik bonusów")
