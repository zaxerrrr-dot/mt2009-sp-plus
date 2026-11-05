#!/usr/bin/env python3
"""merge.py <lang> <files...> - ID<TAB>translation files -> lang/<lang>/30_quest_custom.tsv (Q), 35_quest_fragments.tsv (F),
40_server_custom.tsv (S); a translation equal to the Polish is left out. An existing file's entries for keys not in
this run are kept (a re-run replaces only what it has)."""
import os, sys
W = os.path.dirname(os.path.abspath(__file__))
LANG = os.path.abspath(os.path.join(W, "..", "..", "..", "linux-port", "docker", "game", "lang"))
lang = sys.argv[1]
pl = {}
for line in open(os.path.join(W, "all_pl.tsv"), encoding="utf-8"):
    k, v = line.rstrip("\n").split("\t", 1)
    pl[k] = v
tr = {}
for f in sys.argv[2:]:
    for line in open(f, encoding="utf-8"):
        line = line.rstrip("\n")
        if "\t" in line:
            k, v = line.split("\t", 1)
            tr[k] = v
names = {"Q": "30_quest_custom.tsv", "T": "32_quest_templates.tsv", "F": "35_quest_fragments.tsv", "S": "40_server_custom.tsv", "L": "22_server_locale_more.tsv"}
heads = {"Q": "our quests and quest libraries (tools/i18n/data/quest_custom_pl.tsv)",
         "F": "pieces our quests glue to values (tools/i18n/data/quest_fragments_pl.tsv) - replaced inside a line",
         "S": "our engine code's lines (tools/i18n/data/server_custom_pl.tsv)",
         "L": "the engine's LC_TEXT lines the official sources lack in this language (by hand)",
         "T": "the lines our quests glue together, as formats (tools/i18n/data/quest_templates_pl.tsv)"}
for pre, name in names.items():
    path = os.path.join(LANG, lang, name)
    table = {}
    if os.path.exists(path):
        for line in open(path, encoding="utf-8"):
            line = line.rstrip("\n")
            if line and not line.startswith("#") and "\t" in line:
                a, b = line.split("\t", 1)
                table[a] = b
    n = 0
    for k, v in tr.items():
        if not k.startswith(pre) or k not in pl:
            continue
        if v.strip() == "" or v == pl[k]:
            continue
        table[pl[k]] = v
        n += 1
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8", newline="\n") as fp:
        fp.write("# MT2009_PLUS_LANGUAGE_V1 - %s\n# Polish<TAB>%s (by hand; UTF-8). tools/i18n/extract_server_texts.py --check %s lists what is missing.\n" % (heads[pre], lang, lang))
        for a in sorted(table, key=lambda x: (x.lower(), x)):
            fp.write("%s\t%s\n" % (a, table[a]))
    print(lang, name, n, "this run,", len(table), "in the file")
