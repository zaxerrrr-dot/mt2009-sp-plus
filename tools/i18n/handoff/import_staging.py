#!/usr/bin/env python3
"""import_staging.py <lang> [file.tsv ...] - validates filled staging TSVs (id<TAB>Polish<TAB>English<TAB>target; default:
every /opt/metin2/cache/i18n-staging/quest/<lang>/*.tsv) and merges the good lines into
linux-port/docker/game/lang/<lang>/{30_,32_,35_,40_,22_}*.tsv. A line is rejected (and listed) when its target is empty,
has other printf placeholders / [TAGS] / leading-trailing spaces than the Polish, a character the language's code page
cannot hold, or names Metin2 / Gameforge / Ameria / metin2alerts. A target equal to the Polish is skipped (the
Polish stays). Exit 1 when anything was rejected. --dry-run: check only."""
import glob, os, re, sys
HERE = os.path.dirname(os.path.abspath(__file__))
LANG = os.path.abspath(os.path.join(HERE, "..", "..", "..", "linux-port", "docker", "game", "lang"))
STAGING = "/opt/metin2/cache/i18n-staging/quest"
FILES = {"Q": "30_quest_custom.tsv", "T": "32_quest_templates.tsv", "F": "35_quest_fragments.tsv",
         "S": "40_server_custom.tsv", "L": "22_server_locale_more.tsv"}
CP = {"pl": "cp1250", "cz": "cp1250", "hu": "cp1250", "ro": "cp1250", "tr": "cp1254", "gr": "cp1253", "ae": "cp1256"}
CONV = re.compile(r"%(?:%|[-+#0]*\d*(?:\.\d+)?(?:hh|h|ll|l|L|q|j|z|t)?[diouxXeEfgGcs])")
TAG = re.compile(r"\[[A-Z][A-Z_0-9]+(?:[ \t][^\]]*)?\]")
FORBIDDEN = re.compile(r"metin\s*2|gameforge|\bt[i]eru\b|\bameria\b|metin2alerts", re.I)


def problem(pl, t, cp):
    if not t.strip():
        return "empty"
    if [c for c in CONV.findall(pl) if c != "%%"] != [c for c in CONV.findall(t) if c != "%%"]:
        return "placeholders"
    if [x.split()[0] for x in TAG.findall(pl)] != [x.split()[0] for x in TAG.findall(t)]:
        return "tags"
    if (pl[:1] == " ") != (t[:1] == " ") or (pl[-1:] == " ") != (t[-1:] == " "):
        return "edge spaces"
    if FORBIDDEN.search(t) and not FORBIDDEN.search(pl):
        return "forbidden name"
    try:
        t.encode(cp)
    except UnicodeEncodeError as e:
        return "code page %s cannot hold %r" % (cp, t[e.start:e.end])
    return None


def main():
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    dry = "--dry-run" in sys.argv
    lang = args[0]
    files = args[1:] or sorted(glob.glob(os.path.join(STAGING, lang, "*.tsv")))
    cp = CP.get(lang, "cp1252")
    good, bad = {}, []
    for f in files:
        for n, line in enumerate(open(f, encoding="utf-8"), 1):
            line = line.rstrip("\n").rstrip("\r")
            if not line or line.startswith("#"):
                continue
            p = line.split("\t")
            if len(p) < 4 or p[0][:1] not in FILES:
                bad.append((f, n, p[0] if p else "?", "not 4 columns / unknown id"))
                continue
            i, pl, t = p[0], p[1], "\t".join(p[3:])
            why = problem(pl, t, cp)
            if why == "empty":
                continue
            if why:
                bad.append((f, n, i, why))
                continue
            if t != pl:
                good.setdefault(FILES[i[0]], {})[pl] = t
    for f, n, i, why in bad:
        print("REJECTED %s:%d %s - %s" % (os.path.basename(f), n, i, why))
    total = sum(len(v) for v in good.values())
    if not dry:
        for name, pairs in good.items():
            path = os.path.join(LANG, lang, name)
            table = {}
            if os.path.exists(path):
                for line in open(path, encoding="utf-8"):
                    if line.startswith("#") or "\t" not in line:
                        continue
                    a, b = line.rstrip("\n").split("\t", 1)
                    table[a] = b
            table.update(pairs)
            os.makedirs(os.path.dirname(path), exist_ok=True)
            with open(path, "w", encoding="utf-8", newline="\n") as fp:
                fp.write("# MT2009_PLUS_LANGUAGE_V1 - Polish<TAB>%s (by hand; UTF-8; tools/i18n/handoff/import_staging.py)\n" % lang)
                for a in sorted(table, key=lambda x: (x.lower(), x)):
                    fp.write("%s\t%s\n" % (a, table[a]))
    print("%s: %d line(s) %s, %d rejected" % (lang, total, "valid (dry run)" if dry else "merged", len(bad)))
    sys.exit(1 if bad else 0)


if __name__ == "__main__":
    main()
