#!/usr/bin/env python3
"""Staging TSVs for translators who only translate (MT2009_PLUS_WEB_I18N_V1).

    python3 tools/i18n/staging.py export [--out /opt/metin2/cache/i18n-staging/panel] [--lines 300] [lang ...]
    python3 tools/i18n/staging.py import [--out /opt/metin2/cache/i18n-staging/panel] [lang ...]

export writes, for every language and every part still untranslated,
<out>/<lang>/<part>_NNN.tsv with the columns

    id <TAB> source (Polish, or English for the classic panel) <TAB> English reference <TAB> target (empty)

<part> is seban (Seban panel), panel (classic panel), itemshop (ItemShop V3) or
names (item/monster names). A translator fills ONLY the 4th column. Nothing else
in the file may change. Sources never contain tabs or newlines.

import reads every filled row back, checks it and merges the good ones:
  - target must keep every {0}/{1}.., %d/%s/%.1f/%%, and every <tag> of the source
  - valid UTF-8, no U+FFFD, no control characters, no mojibake (Ã, Å, Ä followed by a byte char)
  - no forbidden names (the game's brand, its publisher, "official" in any language, Tieru,
    Ameria, metin2alerts) - the file name Metin2Distribute.exe and metin2sp.pl excepted
  - a target equal to its source is accepted (a name/code that stays the same)
and writes the rejects to <out>/<lang>/REJECTED.tsv (reason in a 5th column).
Good rows go to tools/i18n/work/<part>/<lang>/done_2NN.json (merged with
catalog.py merge, as are any other done files there) or, for names, to
tools/i18n/names_extra/<lang>.tsv (then build_names.py is run).
"""
import glob
import hashlib
import json
import os
import re
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import catalog  # noqa: E402

DEFAULT_OUT = "/opt/metin2/cache/i18n-staging/panel"
LANGS = ["de", "tr", "ro", "es", "it", "fr", "pt", "cz", "hu", "gr", "ae"]
PARTS = ["seban", "panel", "itemshop"]
TIERU = os.environ.get("TIERU_NAMES", "/tmp/claude-0/-root/9f475014-d1bc-4cf4-a3e1-da3c380fc52c/scratchpad/tieru-panel/linux-port/docker/seban-panel/static")

HOLDERS = re.compile(r"\{\d+\}|\{\w+\}|%\.?\d*[sdf]|%%|</?[a-zA-Z][^>]*>")
BRAND = re.compile(r"metin\s*2|gameforge|\btieru\b|\bameria\b|metin2alerts", re.I)
OFFICIAL = re.compile(r"\bofficial|oficjal|offiziell|\bofficiel|ufficial|\boficial|\bresm[iî]\b|hivatalos|oficiáln|επίσημ|رسمي", re.I)
ALLOWED = re.compile(r"Metin2Distribute\.exe|metin2sp\.pl|/opt/metin2\S*|\bmetin2\b(?= *$)", re.I)
MOJIBAKE = re.compile(r"Ã.|Å.|Ä.|Å‚|â€|Ĺ.|Ă.")
CONTROL = re.compile(r"[\x00-\x08\x0b-\x1f\x7f]")


def rid(part, text):
    return part + ":" + hashlib.sha1(text.encode("utf-8")).hexdigest()[:12]


def clean(s):
    return s.replace("\t", " ").replace("\r", " ").replace("\n", " ")


def names_todo(lang):
    """[(Polish, English)] names with no name in lang."""
    path = os.path.join(HERE, "names_todo", lang + ".txt")
    out = []
    if os.path.isfile(path):
        for line in open(path, encoding="utf-8"):
            line = line.rstrip("\n")
            if not line:
                continue
            pl, _, en = line.partition("\t")
            out.append((pl, en))
    return out


def export(out, langs, lines):
    # names_todo from the current tables (rebuilds the per-language names)
    subprocess.run([sys.executable, os.path.join(HERE, "build_names.py"), "--tieru", TIERU, "--todo"], check=False,
                   stdout=subprocess.DEVNULL)
    for lang in langs:
        d = os.path.join(out, lang)
        os.makedirs(d, exist_ok=True)
        for old in glob.glob(os.path.join(d, "*.tsv")):
            os.remove(old)
        total = 0
        for part in PARTS:
            src = catalog.sources(part, lang)
            cat = catalog.load_catalog(part, lang)
            ref = catalog.load_catalog(part, "en")
            rows = []
            for text in sorted(src):
                if catalog.has(cat, text):
                    continue
                en = "" if part == "panel" else (ref["exact"].get(text) or ref["patterns"].get(text) or "")
                rows.append((rid(part, text), clean(text), clean(en)))
            total += write_chunks(d, part, rows, lines)
        rows = [(rid("names", pl), clean(pl), clean(en)) for pl, en in names_todo(lang)]
        total += write_chunks(d, "names", rows, lines)
        print(lang, "rows", total)


def write_chunks(d, part, rows, lines):
    for i in range(0, len(rows), lines):
        with open(os.path.join(d, "%s_%03d.tsv" % (part, i // lines)), "w", encoding="utf-8", newline="\n") as fh:
            fh.write("id\tsource\tenglish\ttarget\n")
            for r in rows[i:i + lines]:
                fh.write("%s\t%s\t%s\t\n" % r)
    return len(rows)


def holders(s):
    return sorted(HOLDERS.findall(s))


def problem(part, src, tgt):
    if "�" in tgt or CONTROL.search(tgt):
        return "encoding"
    if MOJIBAKE.search(tgt) and not MOJIBAKE.search(src):
        return "mojibake"
    if holders(src) != holders(tgt):
        return "placeholders %s != %s" % (holders(src), holders(tgt))
    cleaned = ALLOWED.sub("", tgt)
    if tgt.strip() != src.strip():
        if BRAND.search(cleaned) and not (part == "names" and BRAND.search(ALLOWED.sub("", src))):
            return "forbidden name"
        if part != "names" and OFFICIAL.search(cleaned):
            return "forbidden word (official)"
    return None


def do_import(out, langs):
    for lang in langs:
        d = os.path.join(out, lang)
        if not os.path.isdir(d):
            continue
        good = {p: {} for p in PARTS}
        names, rejected, seen = [], [], 0
        for path in sorted(glob.glob(os.path.join(d, "*_[0-9][0-9][0-9].tsv"))):
            part = os.path.basename(path).rsplit("_", 1)[0]
            try:
                text = open(path, encoding="utf-8").read()
            except UnicodeDecodeError:
                rejected.append((os.path.basename(path), "", "", "", "file is not UTF-8"))
                continue
            for n, line in enumerate(text.split("\n")[1:], 2):
                if not line.strip():
                    continue
                cols = line.split("\t")
                if len(cols) < 4:
                    rejected.append((cols[0] if cols else "?", "", "", line, "line %d: not 4 columns" % n))
                    continue
                rid_, src, en, tgt = cols[0], cols[1], cols[2], "\t".join(cols[3:]).strip()
                if not tgt:
                    continue
                seen += 1
                if rid_ != rid(part, src):
                    rejected.append((rid_, src, en, tgt, "id/source changed"))
                    continue
                why = problem(part, src, tgt)
                if why:
                    rejected.append((rid_, src, en, tgt, why))
                    continue
                if part == "names":
                    names.append((src, tgt))
                elif part in good:
                    good[part][src] = tgt
        for part, rows in good.items():
            if not rows:
                continue
            work = os.path.join(HERE, "work", part, lang)
            os.makedirs(work, exist_ok=True)
            n = 200
            while os.path.exists(os.path.join(work, "done_%03d.json" % n)):
                n += 1
            with open(os.path.join(work, "done_%03d.json" % n), "w", encoding="utf-8") as fh:
                json.dump(rows, fh, ensure_ascii=False, indent=0)
        for part in PARTS:
            if glob.glob(os.path.join(HERE, "work", part, lang, "done_*.json")):
                catalog.merge(part, lang)
        if names:
            path = os.path.join(HERE, "names_extra", lang + ".tsv")
            have = {}
            if os.path.isfile(path):
                for line in open(path, encoding="utf-8"):
                    p = line.rstrip("\n").split("\t")
                    if len(p) >= 2:
                        have[p[0]] = p[1]
            have.update(dict(names))
            with open(path, "w", encoding="utf-8") as fh:
                for k in sorted(have):
                    fh.write("%s\t%s\n" % (k, have[k]))
        with open(os.path.join(d, "REJECTED.tsv"), "w", encoding="utf-8") as fh:
            fh.write("id\tsource\tenglish\ttarget\treason\n")
            for r in rejected:
                fh.write("\t".join(clean(x) for x in r) + "\n")
        print(lang, "filled", seen, "accepted", seen - len([r for r in rejected if r[3]]), "rejected", len(rejected),
              "(see %s)" % os.path.join(d, "REJECTED.tsv"))
    subprocess.run([sys.executable, os.path.join(HERE, "build_names.py"), "--tieru", TIERU], check=False)


def main(argv):
    if not argv or argv[0] not in ("export", "import"):
        print(__doc__)
        return 2
    out, lines, langs, rest = DEFAULT_OUT, 300, [], argv[1:]
    i = 0
    while i < len(rest):
        if rest[i] == "--out":
            out = rest[i + 1]
            i += 2
        elif rest[i] == "--lines":
            lines = int(rest[i + 1])
            i += 2
        else:
            langs.append(rest[i])
            i += 1
    langs = langs or LANGS
    if argv[0] == "export":
        export(out, langs, lines)
    else:
        do_import(out, langs)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
