#!/usr/bin/env python3
"""The web pages' language files: what is missing, merging translations in,
and how much each language has (MT2009_PLUS_WEB_I18N_V1).

    python3 tools/i18n/catalog.py stats
    python3 tools/i18n/catalog.py todo  <app> <lang> [--chunk 30000] [--ref en]
        -> tools/i18n/work/<app>/<lang>/todo_NNN.json  ([{"s": text, "en": ref}])
    python3 tools/i18n/catalog.py merge <app> <lang>
        <- tools/i18n/work/<app>/<lang>/done_NNN.json  ({text: translation})
    python3 tools/i18n/catalog.py sync
        copies m2i18n.py / m2i18n-watch.js to every app that uses them

<app> is seban (seban-panel), panel (the classic panel, English-based: its
texts are the English of admin_panel.py's tables plus the Polish written
where it stands) or itemshop (both shops). The sources are what
tools/i18n/extract.py found (tools/i18n/source/<app>.json).
"""
import glob
import json
import os
import re
import shutil
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", ".."))
DOCKER = os.path.join(ROOT, "linux-port", "docker")
APP_DIRS = {
    "seban": os.path.join(DOCKER, "seban-panel", "i18n"),
    "panel": os.path.join(DOCKER, "panel", "app", "i18n"),
    "itemshop": os.path.join(DOCKER, "itemshop", "app", "i18n"),
}
META = {
    "pl": ("Polski", "Polish"), "en": ("English", "English"), "de": ("Deutsch", "German"),
    "tr": ("Türkçe", "Turkish"), "ro": ("Română", "Romanian"), "es": ("Español", "Spanish"),
    "it": ("Italiano", "Italian"), "fr": ("Français", "French"), "pt": ("Português", "Portuguese"),
    "cz": ("Čeština", "Czech"), "hu": ("Magyar", "Hungarian"), "gr": ("Ελληνικά", "Greek"),
    "ae": ("العربية", "Arabic"),
}
PH = re.compile(r"\{\d+\}")
PL_CHARS = re.compile(r"[ąćęłńóśźżĄĆĘŁŃÓŚŹŻ]")


def path_of(app, lang):
    return os.path.join(APP_DIRS[app], lang + ".json")


def load_catalog(app, lang):
    try:
        with open(path_of(app, lang), encoding="utf-8") as fh:
            data = json.load(fh)
    except (OSError, ValueError):
        data = {}
    name, english = META.get(lang, (lang, lang))
    meta = data.get("_meta") or {}
    data["_same_set"] = set(data.get("same") or [])
    meta.setdefault("name", name)
    meta.setdefault("english", english)
    return {"_meta": meta, "exact": data.get("exact") or {}, "patterns": data.get("patterns") or {},
            "regex": data.get("regex") or [], "same": data.get("same") or [], "_same_set": data["_same_set"]}


def save_catalog(app, lang, cat):
    os.makedirs(APP_DIRS[app], exist_ok=True)
    out = {"_meta": cat["_meta"], "exact": dict(sorted(cat["exact"].items())),
           "patterns": dict(sorted(cat["patterns"].items()))}
    if cat.get("regex"):
        out["regex"] = cat["regex"]
    if cat.get("same"):
        # texts the language says the same way (or code a page shows as it is): counted, never looked up
        out["same"] = sorted(set(cat["same"]))
    with open(path_of(app, lang), "w", encoding="utf-8") as fh:
        json.dump(out, fh, ensure_ascii=False, indent=1)
        fh.write("\n")


def sources(app, lang=None):
    """{text: kind} the language needs. The classic panel's English needs
    only its Polish leftovers - the rest of it is English already."""
    data = json.load(open(os.path.join(HERE, "source", app + ".json"), encoding="utf-8"))
    english = set(data.get("english") or [])
    out = {}
    for kind in ("exact", "patterns"):
        for text in data[kind]:
            if app == "panel" and lang == "en" and text in english:
                continue
            out[text] = kind
    return out


def has(cat, text):
    return bool(cat["exact"].get(text) or cat["patterns"].get(text) or text in cat.get("_same_set", ()))


def stats():
    rows = []
    for app in APP_DIRS:
        for lang in META:
            if lang == "pl":
                continue
            src = sources(app, lang)
            cat = load_catalog(app, lang)
            done = sum(1 for t in src if has(cat, t))
            chars = sum(len(t) for t in src)
            done_chars = sum(len(t) for t in src if has(cat, t))
            rows.append((app, lang, done, len(src), round(100.0 * done_chars / max(1, chars), 1)))
    for r in rows:
        print("%-9s %-3s %6d / %-6d  %5.1f%% of the text" % r)
    return rows


def todo(app, lang, chunk=30000, ref=None):
    src = sources(app, lang)
    cat = load_catalog(app, lang)
    refcat = load_catalog(app, ref) if ref else None
    work = os.path.join(HERE, "work", app, lang)
    os.makedirs(work, exist_ok=True)
    for old in glob.glob(os.path.join(work, "todo_*.json")):
        os.remove(old)
    missing = [t for t in sorted(src) if not has(cat, t)]
    chunks, cur, size = [], [], 0
    for t in missing:
        item = {"s": t}
        if refcat is not None:
            r = refcat["exact"].get(t) or refcat["patterns"].get(t)
            if r:
                item["en"] = r
        cur.append(item)
        size += len(t) + len(item.get("en", ""))
        if size >= chunk:
            chunks.append(cur)
            cur, size = [], 0
    if cur:
        chunks.append(cur)
    for i, c in enumerate(chunks):
        with open(os.path.join(work, "todo_%03d.json" % i), "w", encoding="utf-8") as fh:
            json.dump(c, fh, ensure_ascii=False, indent=0)
    print(app, lang, "missing", len(missing), "chunks", len(chunks))


def merge(app, lang):
    src = sources(app, lang)
    cat = load_catalog(app, lang)
    work = os.path.join(HERE, "work", app, lang)
    added = bad = 0
    for path in sorted(glob.glob(os.path.join(work, "done_*.json"))):
        try:
            data = json.load(open(path, encoding="utf-8"))
        except ValueError as e:
            print("broken", path, e)
            continue
        for text, val in data.items():
            if not isinstance(val, str) or not val.strip():
                continue
            text = re.sub(r"\s+", " ", text).strip()
            if text not in src:
                bad += 1
                continue
            if sorted(PH.findall(text)) != sorted(PH.findall(val)):
                bad += 1
                continue
            kind = "patterns" if PH.search(text) else "exact"
            if val.strip() == text:
                cat["exact"].pop(text, None)
                cat["patterns"].pop(text, None)
                cat["same"].append(text)
            else:
                cat[kind][text] = val
            added += 1
    save_catalog(app, lang, cat)
    print(app, lang, "merged", added, "rejected", bad)


def sync():
    core = os.path.join(DOCKER, "seban-panel", "m2i18n.py")
    watch = os.path.join(DOCKER, "seban-panel", "static", "m2i18n-watch.js")
    shutil.copyfile(core, os.path.join(DOCKER, "panel", "app", "m2i18n.py"))
    shutil.copyfile(watch, os.path.join(DOCKER, "panel", "app", "m2i18n-watch.js"))
    shutil.copyfile(watch, os.path.join(DOCKER, "itemshop", "app", "m2i18n-watch.js"))
    print("synced")


def main(argv):
    if not argv or argv[0] == "stats":
        stats()
    elif argv[0] == "todo":
        chunk = 30000
        ref = None
        rest = argv[3:]
        if "--chunk" in rest:
            chunk = int(rest[rest.index("--chunk") + 1])
        if "--ref" in rest:
            ref = rest[rest.index("--ref") + 1]
        todo(argv[1], argv[2], chunk, ref)
    elif argv[0] == "merge":
        merge(argv[1], argv[2])
    elif argv[0] == "sync":
        sync()


if __name__ == "__main__":
    main(sys.argv[1:])
