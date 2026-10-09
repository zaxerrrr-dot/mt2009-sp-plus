#!/usr/bin/env python3
"""gen_zodiak_edits.py <zodiak_haki.py> <patched game/src dir> <out edits.json>

MT2009_PLUS_ZODIAC_V1 - Swiatynia Zodiaku (Autor: Digi Rasta, nowy-system 0.35.0,
server-patches/zodiak/README.md). Turns the package's 68 hooks (Serwer/nowy-system/
zodiak_haki.py: a loose anchor, a mode po|przed|zamien|podmien and the code) into our
server-patches format: each edit's exact "old" text is the anchor resolved on OUR
engine with every other server patch already applied (the hooks go last), "new" is
the old text with the hook's code and a marker "MT2009_PLUS_ZODIAC_V1 (<n>)".

Changes against the package, so the hooks fit our tree:
- the new engine files live in the overlay as playerbot_zodiac_*.{h,cpp,inc}
  (zodiac_temple.h -> playerbot_zodiac_temple.h, regen_zodiac.inc ->
  playerbot_zodiac_regen.inc);
- the Dockerfile and m2-render-config hooks are not edits here (those are our own
  files, edited in the repo);
- ENABLE_12ZI (CommonDefines.h) is the LAST edit: apply_zodiak.py writes nothing
  unless every edit's code is found, so the define never comes without its hooks.
Run it again after an engine update moves an anchor; an anchor found 0 or 2+ times
stops with its name.
"""
import importlib.util
import json
import re
import sys

MARK = "MT2009_PLUS_ZODIAC_V1"
RENAMES = [
    ('#\tinclude "zodiac_temple.h"', '#\tinclude "playerbot_zodiac_temple.h"'),
    ('#\tinclude "regen_zodiac.inc"', '#\tinclude "playerbot_zodiac_regen.inc"'),
]
DEFINE = "CommonDefines.h: ENABLE_12ZI"


def flex(anchor):
    return r"\s+".join(re.escape(t) for t in anchor.split())


def mark_code(code, n, name):
    """Put the marker into the hook's code: replace the package's '// ZODIAK x' comment
    of its first #ifdef line, or add a comment line of our own."""
    tag = "%s (%d)" % (MARK, n)
    for a, b in RENAMES:
        code = code.replace(a, b)
    m = re.search(r"// ZODIAK[^\n]*", code)
    if m:
        return code[:m.start()] + "// " + tag + ": " + name + code[m.end():]
    first, nl, rest = code.partition("\n")
    if first.lstrip().startswith("#"):
        return first + " // " + tag + ": " + name + nl + rest
    return "\t// " + tag + ": " + name + "\n" + code


def main():
    if len(sys.argv) != 4:
        sys.exit(__doc__)
    spec = importlib.util.spec_from_file_location("zodiak_haki", sys.argv[1])
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    src = sys.argv[2].rstrip("/")
    hooks = [h for h in mod.HAKI if h[0] in ("game", "common")]
    hooks = [h for h in hooks if h[2] != DEFINE] + [h for h in hooks if h[2] == DEFINE]
    texts = {}
    edits = []
    bad = []
    for n, (root, fname, name, anchor, mode, code) in enumerate(hooks, 1):
        rel = ("../../common/" + fname) if root == "common" else fname
        if rel not in texts:
            texts[rel] = open("%s/%s" % (src, rel), "rb").read().decode("latin-1").replace("\r\n", "\n")
        t = texts[rel]
        code = mark_code(code, n, name)
        if anchor == mod.INC:
            incs = list(re.finditer(r"^[ \t]*#[ \t]*include[^\n]*", t, re.M))
            exact = incs[-1].group(0)
            if t.count(exact) != 1:
                bad.append("%s: last include not unique" % name)
                continue
        else:
            ms = list(re.finditer(flex(anchor), t))
            if len(ms) != 1:
                bad.append("%s: anchor found %d times in %s" % (name, len(ms), rel))
                continue
            s, e = ms[0].span()
            if mode == "podmien":
                exact = t[s:e]
            else:
                ls = t.rfind("\n", 0, s) + 1
                le = t.find("\n", e)
                exact = t[ls:(len(t) if le < 0 else le)]
        if mode == "po":
            new = exact + "\n" + code
        elif mode == "przed":
            new = code + "\n" + exact
        else:
            new = code
        # the next hook in the same file anchors on the text with this one in it
        texts[rel] = t.replace(exact, new, 1)
        edits.append({"file": rel, "marker": "%s (%d)" % (MARK, n), "old": exact, "new": new})
    if bad:
        sys.exit("gen_zodiak_edits: " + "; ".join(bad))
    for e in edits:
        if e["marker"] not in e["new"]:
            sys.exit("gen_zodiak_edits: no marker in %s" % e["marker"])
    json.dump(edits, open(sys.argv[3], "w"), indent=1, ensure_ascii=True)
    open(sys.argv[3], "a").write("\n")
    print("gen_zodiak_edits: %d edits" % len(edits))


if __name__ == "__main__":
    main()
