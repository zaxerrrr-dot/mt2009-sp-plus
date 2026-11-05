#!/usr/bin/env python3
"""build_server_lang.py - the server's generated dictionaries (MT2009_PLUS_LANGUAGE_V1, server-patches/language/README.md).

Writes, for every language of LANGS, into linux-port/docker/game/lang/<code>/ (UTF-8, "Polish<TAB>translation"):
  10_quest_stock.tsv   the stock quests' texts (share translate.lua - gameforge.*, quest/libs/translate - translate.*,
                       quest/locale.lua - locale.*): the official translation of the same text where the sources have it;
  20_server_locale.tsv the engine's LC_TEXT lines (locale_string.txt + our locale_string.*.txt): the Polish value ->
                       the official translation of its key;
  item_names.tsv, mob_names.tsv  vnum<TAB>name, the official names (only where the official Polish name is ours);
  language.cfg         the client's code page of the language.
The hand-made files (30_quest_custom.tsv, 40_server_custom.tsv, zz_*.tsv) are never touched.

Sources (read only; see SOURCES below): the test tree's share (the Polish), Owsap's client locale_quest.txt /
locale_string.txt per language (GF's official texts by id) and Dump Proto item / mob names, Tieru's quest_texts_en/tr.lua
and locale_string_en.tsv (signature-checked English / Turkish of the same Polish), the Vegas package's German
translate.lua / locale_string.txt (data only), the test database's item_proto / mob_proto Polish names
(--items/--mobs TSV dumps: vnum<TAB>locale_name).

A translation is taken only with the Polish's printf conversions; never one naming Metin2 / Gameforge (the reader
gets the English, else the Polish).
"""
import argparse
import collections
import hashlib
import os
import re
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.abspath(os.path.join(HERE, "..", ".."))
OUT = os.path.join(REPO, "linux-port", "docker", "game", "lang")

# Owsap's language codes; the client's code page of each (GF's).
LANGS = ["en", "de", "tr", "ro", "es", "it", "fr", "pt", "cz", "hu", "gr", "ae"]
CODEPAGE = {"pl": 1250, "cz": 1250, "hu": 1250, "ro": 1250, "tr": 1254, "gr": 1253, "ae": 1256}

SCRATCH = "/tmp/claude-0/-root/9f475014-d1bc-4cf4-a3e1-da3c380fc52c/scratchpad"
SOURCES = {
    "share": "/opt/metin2/mt2009plustest/linux-port/docker/game/src/serverfiles/share/locale/poland",
    "owsap_client": "/opt/metin2/cache/owsap/Client/Client/pack/locale/locale",
    "owsap_names": "/opt/metin2/cache/owsap/Tools/Tools/Dump Proto/share",
    "tieru": "/opt/metin2/cache/tieru-releases/metin2-server-protected-update-2.2.129.zip",
    "vegas": SCRATCH + "/tr-up/vegas/Multilanguage/Multilanguage/Multilanguage System V1.0/Server/locale/your service like germany/translate",
}

FORBIDDEN = re.compile(r"metin\s*2|gameforge", re.I)


def cp(lang):
    return "cp%d" % CODEPAGE.get(lang, 1252)


def esc(s):
    return s.replace("\\", "\\\\").replace("\t", "\\t").replace("\n", "\\n").replace("\r", "")


def unesc(s):
    out, i = [], 0
    while i < len(s):
        if s[i] == "\\" and i + 1 < len(s) and s[i + 1] in "tn\\":
            out.append({"t": "\t", "n": "\n", "\\": "\\"}[s[i + 1]])
            i += 2
            continue
        out.append(s[i])
        i += 1
    return "".join(out)


CONV = re.compile(r"%(%|[-+ #0]*\d*(?:\.\d+)?(?:hh|h|ll|l|L|q|j|z|t)?[diouxXeEfgGcs])")


def conversions(s):
    return [m.group(0) for m in CONV.finditer(s) if m.group(0) != "%%"]


def same_conversions(a, b):
    return conversions(a) == conversions(b)


def norm(s):
    return " ".join(s.replace("[ENTER]", " ").split())


def lua50():
    exe = os.path.join(HERE, "lua50", "lua50")
    if not os.path.exists(exe):
        subprocess.check_call([os.path.join(HERE, "lua50", "build.sh")])
    return exe


def read_tsv(path, enc):
    rows = []
    for line in open(path, "rb").read().decode(enc, errors="replace").split("\n"):
        if line:
            rows.append(line.split("\t"))
    return rows


def dump_stock(tmp):
    """path -> Polish (gameforge.*, translate.*, locale.*) of the share."""
    out = os.path.join(tmp, "stock_pl.tsv")
    subprocess.check_call([lua50(), os.path.join(HERE, "lua50", "dump.lua"), SOURCES["share"], out])
    # The image renames the world in both translate.lua files at build time (game/Dockerfile, "Metin2 SinglePlayer"):
    # the runtime's Polish is that.
    res = {}
    for r in read_tsv(out, "cp1250"):
        if len(r) == 2:
            v = unesc(r[1])
            if r[0].startswith(("gameforge.", "translate.")):
                v = v.replace("Metin2009", "Metin2 SinglePlayer")
            res[r[0]] = v
    return res


def mysql_password(b):
    return hashlib.sha1(hashlib.sha1(b).digest()).hexdigest().upper()


def tieru(tmp, name, table, enc, polish):
    """path -> text of Tieru's quest_texts_<lang>.lua, only where its signature names our Polish."""
    import zipfile
    z = zipfile.ZipFile(SOURCES["tieru"])
    src = os.path.join(tmp, name)
    open(src, "wb").write(z.read("linux-port/docker/game/quest/" + name))
    out = src + ".tsv"
    subprocess.check_call([lua50(), os.path.join(HERE, "lua50", "dumpt.lua"), src, table, out])
    res, stale = {}, 0
    for r in read_tsv(out, enc):
        if len(r) != 4 or r[0] == "items":
            continue
        path = r[0] + "." + r[1]
        pl = polish.get(path)
        if pl is None:
            continue
        m = re.match(r"^(\d+):([0-9A-Fa-f]*)$", r[2])
        b = pl.encode("cp1250", errors="replace")
        if not m or int(m.group(1)) != len(b) or (m.group(2) and not mysql_password(b).startswith(m.group(2).upper())):
            stale += 1
            continue
        res[path] = unesc(r[3])
    print("tieru %s: %d texts, %d stale" % (name, len(res), stale))
    return res


def tieru_locale_string_en():
    import zipfile
    z = zipfile.ZipFile(SOURCES["tieru"])
    data = z.read("linux-port/docker/game/share-add/locale_string_en.tsv").decode("utf-8", errors="replace")
    res = {}
    for line in data.split("\n"):
        if not line or line.startswith("#"):
            continue
        p = line.split("\t")
        if len(p) >= 4:
            res[unesc(p[1])] = unesc(p[2])
    return res


def owsap_table(lang, name):
    path = os.path.join(SOURCES["owsap_client"], lang, name)
    res = {}
    if not os.path.exists(path):
        return res
    for line in open(path, "rb").read().decode(cp(lang), errors="replace").split("\n"):
        line = line.rstrip("\r")
        if "\t" in line:
            k, v = line.split("\t", 1)
            res[k.strip()] = v
    return res


def index(table):
    idx = {}
    for k in sorted(table, key=lambda x: int(x) if x.isdigit() else 0):
        idx.setdefault(norm(table[k]), k)
    return idx


def parse_locale_string(data):
    """The pairs of a locale_string.txt ("key";\\n"value";)."""
    strings = []
    i, n = 0, len(data)
    while i < n:
        if data[i] == '"':
            j = i + 1
            buf = []
            while j < n and data[j] != '"':
                if data[j] == "\\" and j + 1 < n:
                    if data[j + 1] == "n":
                        buf.append("\n")
                        j += 2
                        continue
                    buf.append(data[j + 1])
                    j += 2
                    continue
                buf.append(data[j])
                j += 1
            strings.append("".join(buf))
            i = j + 1
        elif data[i] == "/" and data[i:i + 2] == "//":
            while i < n and data[i] != "\n":
                i += 1
        else:
            i += 1
    return [(strings[k], strings[k + 1]) for k in range(0, len(strings) - 1, 2)]


def vegas_de(tmp):
    src = os.path.join(SOURCES["vegas"], "de", "translate.lua")
    if not os.path.exists(src):
        return {}, {}
    text = open(src, "rb").read().replace(b'gameforge["de"]', b"gameforge").replace(b"\r", b"")
    fixed = os.path.join(tmp, "vegas_de_translate.lua")
    open(fixed, "wb").write(text)
    out = fixed + ".tsv"
    subprocess.check_call([lua50(), os.path.join(HERE, "lua50", "dumpow.lua"), fixed, out, "gameforge"])
    quest = {r[0]: unesc(r[1]) for r in read_tsv(out, "cp1252") if len(r) == 2}
    # Korean -> German of the engine's lines.
    ls = {}
    p = os.path.join(SOURCES["vegas"], "de", "locale_string.txt")
    if os.path.exists(p):
        for k, v in parse_locale_string(open(p, "rb").read().decode("cp949", errors="replace").replace("\r", "")):
            ls[k] = v
    # Korean -> German needs the Korean of our English keys: the Vegas English file (Korean -> English).
    ko_en = {}
    p = os.path.join(SOURCES["vegas"], "en", "locale_string.txt")
    if os.path.exists(p):
        for k, v in parse_locale_string(open(p, "rb").read().decode("cp949", errors="replace").replace("\r", "")):
            ko_en.setdefault(v, k)
    de_by_en = {}
    for en, ko in ko_en.items():
        if ko in ls:
            de_by_en[en] = ls[ko]
    return quest, de_by_en


def names(lang, kind, ours, owsap_pl):
    """vnum -> official name in lang, only where the official Polish name is ours (else our vnum is another thing)."""
    path = os.path.join(SOURCES["owsap_names"], lang, kind + "_names.txt")
    res = {}
    if not os.path.exists(path):
        return res
    for line in open(path, "rb").read().decode(cp(lang), errors="replace").split("\n")[1:]:
        p = line.rstrip("\r").split("\t")
        if len(p) < 2 or not p[0].isdigit() or not p[1].strip():
            continue
        v = int(p[0])
        if v not in ours or v not in owsap_pl:
            continue
        if "".join(ours[v].split()).lower() != "".join(owsap_pl[v].split()).lower():
            continue
        if FORBIDDEN.search(p[1]):
            continue
        res[v] = p[1].strip()
    return res


def load_names(path):
    res = {}
    if path and os.path.exists(path):
        for line in open(path, encoding="utf-8", errors="replace"):
            p = line.rstrip("\n").split("\t")
            if len(p) >= 2 and p[0].isdigit():
                res[int(p[0])] = p[1]
    return res


def owsap_pl_names(kind):
    res = {}
    path = os.path.join(SOURCES["owsap_names"], "pl", kind + "_names.txt")
    for line in open(path, "rb").read().decode("cp1250", errors="replace").split("\n")[1:]:
        p = line.rstrip("\r").split("\t")
        if len(p) >= 2 and p[0].isdigit():
            res[int(p[0])] = p[1]
    return res


def write(lang, name, pairs, header):
    d = os.path.join(OUT, lang)
    os.makedirs(d, exist_ok=True)
    with open(os.path.join(d, name), "w", encoding="utf-8", newline="\n") as f:
        for h in header:
            f.write("# " + h + "\n")
        for k in sorted(pairs, key=lambda x: (str(x).lower(), str(x))):
            f.write("%s\t%s\n" % (esc(str(k)), esc(pairs[k])))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--items", help="vnum<TAB>Polish name dump of world.item_proto")
    ap.add_argument("--mobs", help="vnum<TAB>Polish name dump of world.mob_proto")
    ap.add_argument("--tmp", default=os.path.join(SCRATCH, "i18n-build"))
    args = ap.parse_args()
    os.makedirs(args.tmp, exist_ok=True)

    polish = dump_stock(args.tmp)
    gameforge = {k: v for k, v in polish.items() if k.startswith("gameforge.")}
    gf_values = set(gameforge.values())
    stock = {k: v for k, v in polish.items()
             if k.startswith("gameforge.") or k.startswith("translate.") or v not in gf_values}
    t_en = tieru(args.tmp, "quest_texts_en.lua", "quest_texts_en", "cp1252", polish)
    t_tr = tieru(args.tmp, "quest_texts_tr.lua", "quest_texts_tr", "cp1254", polish)
    v_de, v_de_ls = vegas_de(args.tmp)

    lq = {l: owsap_table(l, "locale_quest.txt") for l in ["pl"] + LANGS}
    for l in lq:
        lq[l].update(owsap_table(l, "new_locale_quest.txt"))
    pl_idx = index(lq["pl"])
    en_idx = index(lq["en"])
    ls = {l: owsap_table(l, "locale_string.txt") for l in ["pl"] + LANGS}
    ls_en_idx = index(ls["en"])
    ls_pl_idx = index(ls["pl"])

    stats = collections.defaultdict(collections.Counter)

    # ---- the stock quests
    quest = {l: {} for l in LANGS}
    for path, pl in sorted(stock.items()):
        if not pl.strip() or not re.search(r"[A-Za-z\u0080-\uffff]", pl):
            continue
        en_verified = t_en.get(path)
        qid = pl_idx.get(norm(pl))
        if qid is None and en_verified is not None:
            qid = en_idx.get(norm(en_verified))
        for l in LANGS:
            cand = []
            if l == "en":
                cand.append(("tieru", en_verified))
            if qid is not None:
                cand.append(("owsap", lq[l].get(qid)))
            if l == "tr":
                cand.append(("tieru", t_tr.get(path)))
            if l == "de" and path.startswith("gameforge."):
                cand.append(("vegas", v_de.get(path)))
            for src, t in cand:
                if not t or not t.strip():
                    continue
                if not same_conversions(pl, t):
                    stats[l]["conversions"] += 1
                    continue
                if FORBIDDEN.search(t):
                    stats[l]["forbidden"] += 1
                    continue
                if pl not in quest[l]:
                    quest[l][pl] = t
                    stats[l]["quest_" + src] += 1
                break
    total_quest = len({v for v in stock.values() if v.strip() and re.search(r"[A-Za-z\u0080-\uffff]", v)})

    # ---- the engine's lines
    share_ls = parse_locale_string(open(os.path.join(SOURCES["share"], "locale_string.txt"), "rb").read().decode("cp1250", errors="replace").replace("\r", ""))
    for extra in ("zodiak/locale_string.zodiak.txt", "shipdefense/locale_string.shipdefense.txt"):
        p = os.path.join(REPO, "linux-port", "docker", "game", extra)
        if os.path.exists(p):
            share_ls += parse_locale_string(open(p, "rb").read().decode("cp1250", errors="replace").replace("\r", ""))
    lc = {}
    for k, v in share_ls:
        lc.setdefault(k, v)
    t_ls_en = tieru_locale_string_en()
    server = {l: {} for l in LANGS}
    prose = re.compile(r"^[\x20-\x7e]+$")
    for key, pl in lc.items():
        if not pl.strip():
            continue
        en = t_ls_en.get(key)
        if en is None and prose.match(key) and " " in key and not re.match(r"^[A-Z0-9_]+$", key):
            en = key
        sid = ls_pl_idx.get(norm(pl))
        if sid is None:
            sid = ls_en_idx.get(norm(key)) or (en is not None and ls_en_idx.get(norm(en))) or None
        for l in LANGS:
            cand = []
            if l == "en":
                cand.append(("tieru", en))
            if sid is not None:
                cand.append(("owsap", ls[l].get(sid)))
            if l == "de":
                cand.append(("vegas", v_de_ls.get(key)))
            for src, t in cand:
                if not t or not t.strip():
                    continue
                if not same_conversions(pl, t):
                    stats[l]["ls_conversions"] += 1
                    continue
                if FORBIDDEN.search(t):
                    stats[l]["forbidden"] += 1
                    continue
                if pl not in server[l]:
                    server[l][pl] = t
                    stats[l]["ls_" + src] += 1
                break
    total_ls = len({v for v in lc.values() if v.strip()})

    # ---- names
    ours_items = load_names(args.items)
    ours_mobs = load_names(args.mobs)
    ow_items = owsap_pl_names("item")
    ow_mobs = owsap_pl_names("mob")

    for l in LANGS:
        hdr = ["generated by tools/i18n/build_server_lang.py - DO NOT EDIT (hand fixes: zz_*.tsv)",
               "Polish<TAB>%s, UTF-8; the server converts it to code page %d" % (l, CODEPAGE.get(l, 1252))]
        write(l, "10_quest_stock.tsv", quest[l], hdr + ["the stock quests: %d of %d texts" % (len(quest[l]), total_quest)])
        write(l, "20_server_locale.tsv", server[l], hdr + ["the engine's LC_TEXT lines: %d of %d" % (len(server[l]), total_ls)])
        if ours_items:
            it = names(l, "item", ours_items, ow_items)
            write(l, "item_names.tsv", it, ["generated by tools/i18n/build_server_lang.py - vnum<TAB>name (official, where the official Polish name is ours)"])
            stats[l]["items"] = len(it)
        if ours_mobs:
            mb = names(l, "mob", ours_mobs, ow_mobs)
            write(l, "mob_names.tsv", mb, ["generated by tools/i18n/build_server_lang.py - vnum<TAB>name (official, where the official Polish name is ours)"])
            stats[l]["mobs"] = len(mb)
        with open(os.path.join(OUT, l, "language.cfg"), "w", newline="\n") as f:
            f.write("# MT2009_PLUS_LANGUAGE_V1: the client's code page of this language; a text without a translation here is\n"
                    "# looked up in the fallback language (English), then said in Polish.\n")
            f.write("codepage %d\n" % CODEPAGE.get(l, 1252))
            f.write("fallback %s\n" % ("none" if l == "en" else "en"))
        print("%s: quest %d/%d (%.0f%%), engine %d/%d (%.0f%%), %s" % (
            l, len(quest[l]), total_quest, 100.0 * len(quest[l]) / max(1, total_quest),
            len(server[l]), total_ls, 100.0 * len(server[l]) / max(1, total_ls), dict(stats[l])))


if __name__ == "__main__":
    main()
