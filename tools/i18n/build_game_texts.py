#!/usr/bin/env python3
"""The game's own texts for the web pages, per language (MT2009_PLUS_WEB_I18N_V1).

Bonus lines ("%d%% Szansa na kradzież PE"), class and skill names, the words
of the game's windows: the pages print them in Polish (the ItemShop's
itemshop3.locale_game/skills rows, the panels' tooltips), and the reference
client says each of them in every language. Paired by key with the Polish:

  locale_game.txt, locale_interface.txt (+ new_*)   -> "names" / "patterns"
  skilldesc.txt (the skill's name)                  -> "names"
  itemdesc.txt (an item's description, when ours    -> "names" (ItemShop only:
   is the reference's Polish one)                      the shop shows them)

written as <app>/i18n/<lang>/game.json (and itemdesc.json for the ItemShop).
A format text becomes a pattern: "%d%% Szansa na kradzież PE" ->
"{0}% Szansa na kradzież PE", which the page's "5% Szansa na kradzież PE"
matches.

    python3 tools/i18n/build_game_texts.py
"""
import json
import os
import re
import unicodedata

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", ".."))
DOCKER = os.path.join(ROOT, "linux-port", "docker")
LOC = "/opt/metin2/cache/owsap/Client/Client/pack/locale/locale"
CP = {"pl": "cp1250", "cz": "cp1250", "hu": "cp1250", "ro": "cp1250", "tr": "cp1254", "gr": "cp1253", "ae": "cp1256"}
LANGS = ["en", "de", "tr", "ro", "es", "it", "fr", "pt", "cz", "hu", "gr", "ae"]
FILES = ["locale_game.txt", "locale_interface.txt", "new_locale_game.txt", "new_locale_interface.txt"]
APPS = {"seban": os.path.join(DOCKER, "seban-panel", "i18n"), "panel": os.path.join(DOCKER, "panel", "app", "i18n"),
        "itemshop": os.path.join(DOCKER, "itemshop", "app", "i18n")}
FMT = re.compile(r"%(?:\(\w+\))?[-+ 0#]*\d*(?:\.\d+)?[sdifuxX]")
BAD = re.compile(r"metin\s*2|gameforge|offizi|oficjal|official|officiel|ufficial|oficial|resmi|hivatalos|oficiáln|επίσημ", re.I)


def decode(lang, raw):
    text = raw.decode(CP.get(lang, "cp1252"), "replace")
    if lang == "ro":
        text = text.replace("ã", "ă").replace("þ", "ț").replace("ª", "Ș").replace("º", "ș")
    return text


def keyed(lang, name):
    out = {}
    try:
        raw = open(os.path.join(LOC, lang, name), "rb").read()
    except OSError:
        return out
    for line in decode(lang, raw).splitlines():
        p = line.split("\t")
        if len(p) >= 2 and p[0].strip():
            out[p[0].strip()] = p[-1].strip()
    return out


def column(lang, name, col):
    out = {}
    try:
        raw = open(os.path.join(LOC, lang, name), "rb").read()
    except OSError:
        return out
    for line in decode(lang, raw).splitlines():
        p = line.split("\t")
        if len(p) > col and p[0].strip().isdigit() and p[col].strip():
            out[int(p[0])] = p[col].strip()
    return out


def as_pattern(text):
    """'%d%% Szansa' -> '{0}% Szansa' (and the same numbering for the target)."""
    n = [0]

    def ph(_m):
        k = n[0]
        n[0] += 1
        return "{%d}" % k
    out = FMT.sub(ph, text).replace("%%", "%")
    return out, n[0]


def norm(s):
    s = unicodedata.normalize("NFKD", s.replace("ł", "l").replace("Ł", "L").lower())
    return re.sub(r"[^a-z0-9]", "", s.encode("ascii", "ignore").decode())


def main():
    pl = {f: keyed("pl", f) for f in FILES}
    pl_skill = column("pl", "skilldesc.txt", 2)
    pl_desc = column("pl", "itemdesc.txt", 2)
    try:
        ours_desc = json.load(open(os.path.join(DOCKER, "itemshop", "app", "shop3", "include", "db", "client_itemdesc.json"), encoding="utf-8"))
    except (OSError, ValueError):
        ours_desc = {}
    for lang in LANGS:
        names, patterns = {}, {}
        for f in FILES:
            other = keyed(lang, f)
            for k, v in pl[f].items():
                o = other.get(k)
                if not v or not o or v == o or BAD.search(o) or "\\n" in v or len(v) > 300:
                    continue
                if FMT.search(v) or "%%" in v:
                    pv, nv = as_pattern(v)
                    po, no = as_pattern(o)
                    if nv and nv == no and len(re.sub(r"\{\d+\}|\W", "", pv)) >= 3:
                        patterns.setdefault(pv, po)
                    elif not nv:
                        names.setdefault(v.replace("%%", "%"), o.replace("%%", "%"))
                elif re.search(r"[^\W\d_]", v):
                    names.setdefault(v, o)
        for vnum, name in column(lang, "skilldesc.txt", 2).items():
            if vnum in pl_skill and pl_skill[vnum] != name and not BAD.search(name):
                names.setdefault(pl_skill[vnum], name)
        data = {"_comment": "MT2009_PLUS_WEB_I18N_V1: the reference client's own texts (tools/i18n/build_game_texts.py)",
                "names": dict(sorted(names.items())), "patterns": dict(sorted(patterns.items()))}
        for app, d in APPS.items():
            os.makedirs(os.path.join(d, lang), exist_ok=True)
            with open(os.path.join(d, lang, "game.json"), "w", encoding="utf-8") as fh:
                json.dump(data, fh, ensure_ascii=False, indent=0)
                fh.write("\n")
        desc = {}
        other_desc = column(lang, "itemdesc.txt", 2)
        for vnum, text in ours_desc.items():
            v = int(vnum)
            if v in pl_desc and v in other_desc and norm(pl_desc[v]) == norm(text) and not BAD.search(other_desc[v]):
                desc.setdefault(text, other_desc[v])
        with open(os.path.join(APPS["itemshop"], lang, "itemdesc.json"), "w", encoding="utf-8") as fh:
            json.dump({"names": dict(sorted(desc.items()))}, fh, ensure_ascii=False, indent=0)
            fh.write("\n")
        print(lang, "names", len(names), "patterns", len(patterns), "itemdesc", len(desc), "of", len(set(ours_desc.values())))


if __name__ == "__main__":
    main()
