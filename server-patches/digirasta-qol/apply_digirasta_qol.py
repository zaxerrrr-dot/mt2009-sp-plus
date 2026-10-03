#!/usr/bin/env python3
"""apply_digirasta_qol.py <engine game/src dir> -- Linux/VPS twin of
Apply-DigiRastaQolPatch.ps1: the edits of edits.json (README.md, Digi Rasta's
server conveniences, MT2009_PLUS_DIGI_SERVER_QOL_V1), each with its own
marker. An edit already there is skipped; one whose code is not found exactly
once stops everything before a file is written.

Some engine files mix CRLF and LF lines (exchange.cpp, guild.cpp,
cmd_emotion.cpp), so an edit is looked for as written (LF) and then with CRLF
line ends, and is put in with the line ends it was found with - the rest of
the file is left byte for byte."""
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))


def main():
    if len(sys.argv) != 2:
        sys.exit("usage: apply_digirasta_qol.py <game/src dir>")
    edits = json.load(open(os.path.join(HERE, "edits.json"), encoding="utf-8"))
    texts, original = {}, {}
    for e in edits:
        if e["file"] not in texts:
            raw = open(os.path.join(sys.argv[1], e["file"]), "rb").read()
            original[e["file"]] = raw
            texts[e["file"]] = raw.decode("latin-1")
    applied = 0
    for e in edits:
        text = texts[e["file"]]
        if e["marker"] in text:
            continue
        old, new = e["old"], e["new"]
        if text.count(old) != 1:
            old, new = old.replace("\n", "\r\n"), new.replace("\n", "\r\n")
            if text.count(old) != 1:
                sys.exit("digirasta-qol: %s - the expected code of %s is not in the file; nothing changed" % (e["file"], e["marker"]))
        texts[e["file"]] = text.replace(old, new)
        applied += 1
    for name, text in texts.items():
        data = text.encode("latin-1")
        if data != original[name]:
            open(os.path.join(sys.argv[1], name), "wb").write(data)
    print("digirasta-qol: %d edit(s) applied" % applied)


if __name__ == "__main__":
    main()
