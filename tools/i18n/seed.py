#!/usr/bin/env python3
"""Fill the web pages' language files from translations that already exist
(MT2009_PLUS_WEB_I18N_V1), before anything is translated by hand:

  seban-panel  the upstream panel's English and Turkish tables (translations.py EXACT, static/i18n_tr.json "exact"): Polish
               text -> English/Turkish, where our panel prints the same text
  panel        the classic panel's own tables in admin_panel.py: every dict
               that has "en" next to "de"/"tr" gives English -> German/
               Turkish (the page is rendered in English for every language
               but Polish, see m2i18n.py and admin_panel.py)

Only adds; a translation already in a file is never replaced.

    python3 tools/i18n/seed.py --upstream <dir with seban-panel/translations.py>
"""
import argparse
import ast
import importlib.util
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", ".."))
DOCKER = os.path.join(ROOT, "linux-port", "docker")
sys.path.insert(0, HERE)
from catalog import load_catalog, save_catalog, APP_DIRS  # noqa: E402


def norm(s):
    return re.sub(r"\s+", " ", s).strip()


def upstream_tables(upstream):
    path = os.path.join(upstream, "translations.py")
    spec = importlib.util.spec_from_file_location("upstream_translations", path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    en = {norm(k): v for k, v in mod.EXACT.items()}
    tr = {}
    try:
        tr = {norm(k): v for k, v in json.load(open(os.path.join(upstream, "static", "i18n_tr.json"), encoding="utf-8"))["exact"].items()}
    except (OSError, ValueError, KeyError):
        pass
    return {"en": en, "tr": tr}


def panel_pairs():
    src = open(os.path.join(DOCKER, "panel", "app", "admin_panel.py"), encoding="utf-8").read()
    tree = ast.parse(src)
    pairs = {}

    def const(n):
        return n.value if isinstance(n, ast.Constant) and isinstance(n.value, str) else None

    def add(lang, en, val):
        if en and val and en != val:
            pairs.setdefault(lang, {}).setdefault(norm(en), val)

    for node in ast.walk(tree):
        if not isinstance(node, ast.Dict):
            continue
        keys = [const(k) if k is not None else None for k in node.keys]
        if "en" not in keys:
            continue
        en_node = node.values[keys.index("en")]
        en = const(en_node)
        for k, v in zip(keys, node.values):
            if k in (None, "en", "pl") or not re.fullmatch(r"[a-z]{2}", k):
                continue
            if en is not None:
                add(k, en, const(v))
            elif isinstance(en_node, ast.Dict) and isinstance(v, ast.Dict):
                en_inner = {const(a): const(b) for a, b in zip(en_node.keys, en_node.values) if a is not None}
                for a, b in zip(v.keys, v.values):
                    if a is not None and const(a) in en_inner:
                        add(k, en_inner[const(a)], const(b))
    return pairs


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--upstream", required=True)
    args = ap.parse_args()
    src_seban = json.load(open(os.path.join(HERE, "source", "seban.json"), encoding="utf-8"))
    tables = upstream_tables(args.upstream)
    for lang, table in tables.items():
        cat = load_catalog("seban", lang)
        added = 0
        for text in list(src_seban["exact"]) + list(src_seban["patterns"]):
            if text in table and not cat["exact"].get(text) and text not in cat["patterns"]:
                cat["exact"][text] = table[text]
                added += 1
        save_catalog("seban", lang, cat)
        print("seban", lang, "seeded", added)
    src_panel = json.load(open(os.path.join(HERE, "source", "panel.json"), encoding="utf-8"))
    wanted = set(src_panel["exact"]) | set(src_panel["patterns"])
    for lang, table in panel_pairs().items():
        cat = load_catalog("panel", lang)
        added = 0
        for en, val in table.items():
            if en in wanted and not cat["exact"].get(en):
                cat["exact"][en] = val
                added += 1
        save_catalog("panel", lang, cat)
        print("panel", lang, "seeded", added)


if __name__ == "__main__":
    main()
