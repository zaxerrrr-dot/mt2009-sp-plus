#!/usr/bin/env python3
"""apply_raremobrules.py <engine game/src dir> -- Linux/VPS twin of
Apply-RareMobRulesPatch.ps1: the edits of edits.json (README.md), each with its
own marker. An edit already there is skipped; one whose code is not found
exactly once stops everything before a file is written."""
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))


def main():
    if len(sys.argv) != 2:
        sys.exit("usage: apply_raremobrules.py <game/src dir>")
    edits = json.load(open(os.path.join(HERE, "edits.json")))
    texts, crlf = {}, {}
    for e in edits:
        if e["file"] not in texts:
            raw = open(os.path.join(sys.argv[1], e["file"]), "rb").read()
            crlf[e["file"]] = b"\r\n" in raw
            texts[e["file"]] = raw.decode("latin-1").replace("\r\n", "\n")
    applied = 0
    for e in edits:
        text = texts[e["file"]]
        if e["marker"] in text:
            continue
        if text.count(e["old"]) != 1:
            sys.exit("raremobrules: %s - the expected code of %s is not in the file; nothing changed" % (e["file"], e["marker"]))
        texts[e["file"]] = text.replace(e["old"], e["new"])
        applied += 1
    for name, text in texts.items():
        if crlf[name]:
            text = text.replace("\n", "\r\n")
        path = os.path.join(sys.argv[1], name)
        if open(path, "rb").read() != text.encode("latin-1"):
            open(path, "wb").write(text.encode("latin-1"))
    print("raremobrules: %d edit(s) applied" % applied)


if __name__ == "__main__":
    main()
