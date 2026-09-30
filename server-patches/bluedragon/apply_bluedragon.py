#!/usr/bin/env python3
"""apply_bluedragon.py <engine game/src dir> -- Linux/VPS twin of
Apply-BlueDragonPatch.ps1: the edits of edits.json (README.md), each with its
own marker (MT2009_PLUS_BLUE_DRAGON_V1 ...). An edit already there is skipped;
one whose code is not found exactly once stops everything before a file is
written. The files keep their own line endings (BlueDragon.cpp mixes CRLF
lines with a few LF ones): an edit is matched and written with CRLF where the
file's matching code has CRLF, with LF otherwise."""
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))


def main():
    if len(sys.argv) != 2:
        sys.exit("usage: apply_bluedragon.py <game/src dir>")
    edits = json.load(open(os.path.join(HERE, "edits.json")))
    texts, originals = {}, {}
    for e in edits:
        if e["file"] not in texts:
            raw = open(os.path.join(sys.argv[1], e["file"]), "rb").read()
            originals[e["file"]] = raw
            texts[e["file"]] = raw.decode("latin-1")
    applied = 0
    for e in edits:
        text = texts[e["file"]]
        if e["marker"] in text:
            continue
        old, new = e["old"], e["new"]
        if text.count(old.replace("\n", "\r\n")) == 1:
            old, new = old.replace("\n", "\r\n"), new.replace("\n", "\r\n")
        if text.count(old) != 1:
            sys.exit("bluedragon: %s - the expected code of %s is not in the file; nothing changed" % (e["file"], e["marker"]))
        texts[e["file"]] = text.replace(old, new)
        applied += 1
    for name, text in texts.items():
        data = text.encode("latin-1")
        if data != originals[name]:
            open(os.path.join(sys.argv[1], name), "wb").write(data)
    print("bluedragon: %d edit(s) applied" % applied)


if __name__ == "__main__":
    main()
