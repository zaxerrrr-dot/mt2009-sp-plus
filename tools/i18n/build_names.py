#!/usr/bin/env python3
"""Item and monster names for the web pages, per language (MT2009_PLUS_WEB_I18N_V1).

The pages print an item's Polish name (world.item_proto.locale_name); a
translated page shows the name the game itself uses in that language, never
one made up here when an original exists. Sources, first hit wins:

  1. tools/i18n/names_extra/<lang>.tsv      (Polish name TAB name: our own
     items that no original names, and any later client name files)
  2. the reference client's name tables (Owsap Dump Proto share/<lang>/
     item_names.txt, mob_names.txt) by vnum, when the item there is ours
     (the same Polish name, letters' marks aside)
  3. the same tables by the Polish name, for one of ours on another vnum
  4. the upstream English/Turkish tables (Tieru item_names_en.json ...)
  5. "Name+N": the name of the item it is a level of

Written as <app>/i18n/<lang>/names.json ({"names": {Polish: name}}) into
seban-panel, panel/app and the ItemShop, and tools/i18n/names_report.json says
how many of our names each language has.

    python3 tools/i18n/build_names.py [--owsap DIR] [--tieru DIR]
"""
import argparse
import json
import os
import re
import sys
import unicodedata

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", ".."))
DOCKER = os.path.join(ROOT, "linux-port", "docker")
APPS = [os.path.join(DOCKER, "seban-panel", "i18n"), os.path.join(DOCKER, "panel", "app", "i18n"),
        os.path.join(DOCKER, "itemshop", "app", "i18n")]
LANGS = ["en", "de", "tr", "ro", "es", "it", "fr", "pt", "cz", "hu", "gr", "ae"]
CP = {"pl": "cp1250", "cz": "cp1250", "hu": "cp1250", "ro": "cp1250", "tr": "cp1254", "gr": "cp1253", "ae": "cp1256"}


def parse_proto_sql(path):
    txt = open(path, encoding="utf-8").read()
    out = {}
    for m in re.finditer(r"INSERT IGNORE INTO \S+ \(([^)]*)\) VALUES", txt):
        cols = [c.strip("` ") for c in m.group(1).split(",")]
        iv, iname = cols.index("vnum"), cols.index("locale_name")
        i, n = m.end(), len(txt)
        while i < n:
            c = txt[i]
            if c == ";":
                break
            if c != "(":
                i += 1
                continue
            vals, cur, i, inq = [], "", i + 1, False
            while True:
                c = txt[i]
                if inq:
                    if c == "\\":
                        cur += txt[i + 1]
                        i += 2
                        continue
                    if c == "'":
                        if txt[i + 1] == "'":
                            cur += "'"
                            i += 2
                            continue
                        inq = False
                        i += 1
                        continue
                    cur += c
                    i += 1
                    continue
                if c == "'":
                    inq = True
                elif c == ",":
                    vals.append(cur)
                    cur = ""
                elif c == ")":
                    vals.append(cur)
                    i += 1
                    break
                else:
                    cur += c
                i += 1
            out[int(vals[iv])] = vals[iname]
    return out


def owsap_names(base, lang, kind):
    path = os.path.join(base, lang, kind + "_names.txt")
    out = {}
    try:
        raw = open(path, "rb").read()
    except OSError:
        return out
    for line in raw.decode(CP.get(lang, "cp1252"), "replace").splitlines()[1:]:
        p = line.split("\t")
        if len(p) >= 2 and p[0].strip().isdigit() and p[1].strip():
            out[int(p[0])] = p[1].strip()
    if lang == "ro":
        out = {k: v.replace("ã", "ă").replace("þ", "ț").replace("ª", "Ș").replace("º", "ș") for k, v in out.items()}
    return out


def norm(s):
    s = unicodedata.normalize("NFKD", s.replace("ł", "l").replace("Ł", "L").lower())
    return re.sub(r"[^a-z0-9+]", "", s.encode("ascii", "ignore").decode())


LEVEL = re.compile(r"^(.*?)\+(\d+)$")


def build(kind, ours, owsap_dir, tieru_dir):
    owpl = owsap_names(owsap_dir, "pl", kind)
    tieru = {}
    for lang in ("en", "tr"):
        try:
            tieru[lang] = json.load(open(os.path.join(tieru_dir, "%s_names_%s.json" % (kind, lang)), encoding="utf-8"))
        except (OSError, ValueError):
            tieru[lang] = {}
    result, report, knowns = {}, {}, {}
    for lang in LANGS:
        names = {}
        extra_path = os.path.join(HERE, "names_extra", lang + ".tsv")
        if os.path.isfile(extra_path):
            for line in open(extra_path, encoding="utf-8"):
                p = line.rstrip("\n").split("\t")
                if len(p) >= 2 and p[0] and p[1] and not p[0].startswith("#"):
                    names[p[0]] = p[1]
        owl = owsap_names(owsap_dir, lang, kind)
        # 2. by vnum, the same item
        for vnum, pl in ours.items():
            if pl in names:
                continue
            if vnum in owl and vnum in owpl and norm(owpl[vnum]) == norm(pl):
                names[pl] = owl[vnum]
        # 3. by the Polish name (unique in the reference)
        by_name, clash = {}, set()
        for vnum, pl in owpl.items():
            if vnum in owl:
                k = norm(pl)
                if by_name.setdefault(k, owl[vnum]) != owl[vnum]:
                    clash.add(k)
        for k in clash:
            by_name.pop(k, None)
        for pl in set(ours.values()):
            if pl not in names and norm(pl) in by_name:
                names[pl] = by_name[norm(pl)]
        # 4. upstream tables
        if lang in tieru:
            for vnum, pair in tieru[lang].items():
                if isinstance(pair, list) and len(pair) == 2 and pair[0] and pair[1] and pair[0] not in names:
                    names[pair[0]] = pair[1]
        # 5. levels: "Name+N" from "Name+M" / "Name"
        base_names = {}
        for pl, tr in list(names.items()):
            m, mt = LEVEL.match(pl), LEVEL.match(tr)
            if m and mt:
                base_names.setdefault(m.group(1), mt.group(1))
            elif not m:
                base_names.setdefault(pl, tr)
        for pl in set(ours.values()):
            if pl in names:
                continue
            m = LEVEL.match(pl)
            if m and m.group(1) in base_names:
                names[pl] = base_names[m.group(1)] + "+" + m.group(2)
        # only names of ours, and only where the language says something else
        mine = set(ours.values())
        known = {k for k, v in names.items() if k in mine and v}
        # a name the language says the same way needs no entry
        names = {k: v for k, v in names.items() if k in mine and v and v != k}
        result[lang] = names
        knowns[lang] = known
        covered = sum(1 for v in ours.values() if v in known)
        report[lang] = {"vnums": len(ours), "named": covered, "pct": round(100.0 * covered / max(1, len(ours)), 1),
                        "unique_names": len(mine), "unique_named": len([k for k in mine if k in known])}
    return result, report, knowns


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--owsap", default="/opt/metin2/cache/owsap/Tools/Tools/Dump Proto/share")
    ap.add_argument("--tieru", default=os.environ.get("TIERU_NAMES", ""))
    ap.add_argument("--todo", action="store_true", help="write tools/i18n/names_todo/<lang>.txt: names with no source")
    args = ap.parse_args()
    sql = os.path.join(DOCKER, "mariadb", "playerbot")
    items = parse_proto_sql(os.path.join(sql, "item_proto.mt2009plus.sql"))
    mobs = parse_proto_sql(os.path.join(sql, "mob_proto.mt2009plus.sql"))
    item_names, item_report, item_known = build("item", items, args.owsap, args.tieru)
    mob_names, mob_report, mob_known = build("mob", mobs, args.owsap, args.tieru)
    known_all = {lang: item_known[lang] | mob_known[lang] for lang in LANGS}
    for lang in LANGS:
        merged = dict(item_names[lang])
        for k, v in mob_names[lang].items():
            merged.setdefault(k, v)
        for app in APPS:
            d = os.path.join(app, lang)
            os.makedirs(d, exist_ok=True)
            with open(os.path.join(d, "names.json"), "w", encoding="utf-8") as fh:
                json.dump({"names": dict(sorted(merged.items()))}, fh, ensure_ascii=False, indent=0)
                fh.write("\n")
    with open(os.path.join(HERE, "names_report.json"), "w", encoding="utf-8") as fh:
        json.dump({"items": item_report, "mobs": mob_report}, fh, indent=1)
    if args.todo:
        todo = os.path.join(HERE, "names_todo")
        os.makedirs(todo, exist_ok=True)
        allnames = sorted(set(items.values()) | set(mobs.values()))
        for lang in LANGS:
            have = set(item_names[lang]) | set(mob_names[lang]) | known_all.get(lang, set())
            miss = [n for n in allnames if n not in have and not LEVEL.match(n) and re.search(r"[^\W\d_]", n)]
            en = dict(item_names["en"])
            en.update(mob_names["en"])
            with open(os.path.join(todo, lang + ".txt"), "w", encoding="utf-8") as fh:
                # Polish name, then (a reference for the translator) the English one where there is one
                fh.write("\n".join(n + ("\t" + en[n] if lang != "en" and n in en else "") for n in miss) + "\n")
    for kind, rep in (("items", item_report), ("mobs", mob_report)):
        print(kind, " ".join("%s:%s%%" % (k, v["pct"]) for k, v in rep.items()))


if __name__ == "__main__":
    sys.exit(main())
