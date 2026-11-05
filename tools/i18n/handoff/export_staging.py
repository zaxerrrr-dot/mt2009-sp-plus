#!/usr/bin/env python3
"""export_staging.py [lang ...] - every text of our quests / engine still untranslated in a language, as staging TSVs for
translators: /opt/metin2/cache/i18n-staging/quest/<lang>/NNN.tsv, ~300 lines each, columns
id<TAB>Polish source<TAB>English reference<TAB>target (empty). Default languages: fr pt cz hu gr ae.
The master list is w2_A + w2_B + w2_CTL (only texts that need translating; ids Q/T/F/S/L - see merge.py)."""
import os, sys
HERE = os.path.dirname(os.path.abspath(__file__))
LANG = os.path.abspath(os.path.join(HERE, "..", "..", "..", "linux-port", "docker", "game", "lang"))
OUT = "/opt/metin2/cache/i18n-staging/quest"
FILES = {"Q": "30_quest_custom.tsv", "T": "32_quest_templates.tsv", "F": "35_quest_fragments.tsv",
         "S": "40_server_custom.tsv", "L": "22_server_locale_more.tsv"}
CHUNK = 300


def have(lang):
    done = set()
    for name in set(FILES.values()):
        p = os.path.join(LANG, lang, name)
        if os.path.exists(p):
            for line in open(p, encoding="utf-8"):
                if line.startswith("#") or "\t" not in line:
                    continue
                done.add((name, line.split("\t", 1)[0]))
    return done


def main():
    langs = sys.argv[1:] or ["fr", "pt", "cz", "hu", "gr", "ae"]
    rows = []
    for g in ("w2_A", "w2_B", "w2_CTL"):
        for line in open(os.path.join(HERE, g), encoding="utf-8"):
            p = line.rstrip("\n").split("\t")
            if len(p) == 3:
                rows.append(p)
    for lang in langs:
        done = have(lang)
        todo = [r for r in rows if (FILES[r[0][0]], r[1]) not in done]
        d = os.path.join(OUT, lang)
        os.makedirs(d, exist_ok=True)
        for f in os.listdir(d):
            if f.endswith(".tsv"):
                os.remove(os.path.join(d, f))
        for i in range(0, len(todo), CHUNK):
            with open(os.path.join(d, "%03d.tsv" % (i // CHUNK + 1)), "w", encoding="utf-8", newline="\n") as fp:
                for r in todo[i:i + CHUNK]:
                    fp.write("%s\t%s\t%s\t\n" % (r[0], r[1], r[2]))
        print("%s: %d untranslated, %d file(s) in %s" % (lang, len(todo), (len(todo) + CHUNK - 1) // CHUNK, d))


if __name__ == "__main__":
    main()
