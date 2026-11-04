#!/usr/bin/env python3
"""apply_pety.py <engine game/src dir> -- Linux/VPS twin of Apply-PetyPatch.ps1: System Zwierzat Domowych
(README.md, MT2009_PLUS_GROWTH_PET_V1).
1. Installs files/ (common/growth_pet_types.h, db/src/growth_pet_db.cpp) into the tree next to game/src - overwritten
   when they differ, so a change there always reaches a patched tree (unlike an edit, whose marker stops it).
2. The edits of edits.json, each with its own marker. An edit already there is skipped; one whose code is not found
   exactly once stops everything before a file is written.
Applied LAST (after tytuly)."""
import json
import os
import shutil
import sys

HERE = os.path.dirname(os.path.abspath(__file__))


def main():
    if len(sys.argv) != 2:
        sys.exit("usage: apply_pety.py <game/src dir>")
    src = sys.argv[1]
    root = os.path.normpath(os.path.join(src, '..', '..'))
    edits = json.load(open(os.path.join(HERE, "edits.json")))
    texts, crlf = {}, {}
    for e in edits:
        if e["file"] not in texts:
            raw = open(os.path.join(src, e["file"]), "rb").read()
            crlf[e["file"]] = b"\r\n" in raw
            texts[e["file"]] = raw.decode("latin-1").replace("\r\n", "\n")
    applied = 0
    for e in edits:
        text = texts[e["file"]]
        if e["marker"] in text:
            continue
        if text.count(e["old"]) != 1:
            sys.exit("pety: %s - the expected code of %s is not in the file; nothing changed" % (e["file"], e["marker"]))
        texts[e["file"]] = text.replace(e["old"], e["new"])
        applied += 1
    installed = 0
    files = os.path.join(HERE, "files")
    for dp, dn, fn in os.walk(files):
        for f in fn:
            rel = os.path.relpath(os.path.join(dp, f), files)
            dst = os.path.join(root, rel)
            if not os.path.isdir(os.path.dirname(dst)):
                sys.exit("pety: no directory for %s in %s" % (rel, root))
            data = open(os.path.join(dp, f), "rb").read()
            if not os.path.exists(dst) or open(dst, "rb").read() != data:
                shutil.copyfile(os.path.join(dp, f), dst)
                installed += 1
    for name, text in texts.items():
        if crlf[name]:
            text = text.replace("\n", "\r\n")
        path = os.path.join(src, name)
        if open(path, "rb").read() != text.encode("latin-1"):
            open(path, "wb").write(text.encode("latin-1"))
    print("pety: %d edit(s) applied, %d file(s) installed" % (applied, installed))


if __name__ == "__main__":
    main()
