#!/usr/bin/env python3
"""A reference for translators: the game's own words per language
(MT2009_PLUS_WEB_I18N_V1). The reference client's locale_game.txt,
locale_interface.txt (and new_*) per language, paired with the Polish ones by
key, plus skill names (skilldesc.txt) -> tools/i18n/glossary/<lang>.tsv
(Polish TAB translation, short texts only). Used so a page says "Drachenmünzen"
where the game says it, not a word of our own.

    python3 tools/i18n/build_glossary.py
"""
import os
import re

HERE = os.path.dirname(os.path.abspath(__file__))
LOC = "/opt/metin2/cache/owsap/Client/Client/pack/locale/locale"
CP = {"pl": "cp1250", "cz": "cp1250", "hu": "cp1250", "ro": "cp1250", "tr": "cp1254", "gr": "cp1253", "ae": "cp1256"}
LANGS = ["en", "de", "tr", "ro", "es", "it", "fr", "pt", "cz", "hu", "gr", "ae"]
FILES = ["locale_game.txt", "locale_interface.txt", "new_locale_game.txt", "new_locale_interface.txt"]


def read_keyed(lang, name):
    path = os.path.join(LOC, lang, name)
    out = {}
    try:
        raw = open(path, "rb").read()
    except OSError:
        return out
    for line in raw.decode(CP.get(lang, "cp1252"), "replace").splitlines():
        p = line.split("\t")
        if len(p) >= 2 and p[0].strip():
            out[p[0].strip()] = p[-1].strip()
    return out


def read_skills(lang):
    path = os.path.join(LOC, lang, "skilldesc.txt")
    out = {}
    try:
        raw = open(path, "rb").read()
    except OSError:
        return out
    for line in raw.decode(CP.get(lang, "cp1252"), "replace").splitlines():
        p = line.split("\t")
        if len(p) >= 3 and p[0].strip().isdigit():
            out[p[0].strip()] = p[2].strip()
    return out


def main():
    os.makedirs(os.path.join(HERE, "glossary"), exist_ok=True)
    pl = {}
    for f in FILES:
        pl.update({(f, k): v for k, v in read_keyed("pl", f).items()})
    pl_sk = read_skills("pl")
    for lang in LANGS:
        rows = {}
        for f in FILES:
            other = read_keyed(lang, f)
            for (ff, k), v in pl.items():
                if ff == f and k in other and v and other[k] and len(v) <= 80 and "%" not in v:
                    rows.setdefault(v, other[k])
        for k, v in read_skills(lang).items():
            if k in pl_sk and pl_sk[k]:
                rows.setdefault(pl_sk[k], v)
        with open(os.path.join(HERE, "glossary", lang + ".tsv"), "w", encoding="utf-8") as fh:
            for k in sorted(rows):
                if re.search(r"[^\W\d_]", k):
                    fh.write("%s\t%s\n" % (k.replace("\t", " "), rows[k].replace("\t", " ")))
        print(lang, len(rows))


if __name__ == "__main__":
    main()
