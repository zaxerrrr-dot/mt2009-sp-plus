#!/usr/bin/env python3
"""apply_switchbot.py <engine game/src dir> -- Linux/VPS twin of Apply-SwitchbotPatch.ps1: the entries of
edits.json (README.md). An edit already there (its marker) is skipped; a revert (the old bonus switcher's lines,
MT2009_PLUS_BONUS_SWITCH_V1) is done when its code is there once and skipped when it is not. An edit whose code
is not found exactly once stops everything before a file is written."""
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))


def main():
    if len(sys.argv) != 2:
        sys.exit("usage: apply_switchbot.py <game/src dir>")
    edits = json.load(open(os.path.join(HERE, "edits.json"), encoding="utf-8"))
    texts, crlf = {}, {}
    for e in edits:
        if e["file"] not in texts:
            raw = open(os.path.join(sys.argv[1], e["file"]), "rb").read()
            crlf[e["file"]] = b"\r\n" in raw
            texts[e["file"]] = raw.decode("latin-1").replace("\r\n", "\n")
    applied = reverted = 0
    for e in edits:
        text = texts[e["file"]]
        n = text.count(e["old"])
        if e.get("revert"):
            if n == 0:
                continue
            if n != 1:
                sys.exit("switchbot: %s - %s found %d times; nothing changed" % (e["file"], e["marker"], n))
            texts[e["file"]] = text.replace(e["old"], e["new"])
            reverted += 1
            continue
        if e["marker"] in text:
            continue
        if n != 1:
            sys.exit("switchbot: %s - the expected code of %s is not in the file; nothing changed" % (e["file"], e["marker"]))
        texts[e["file"]] = text.replace(e["old"], e["new"])
        applied += 1
    for name, text in texts.items():
        if crlf[name]:
            text = text.replace("\n", "\r\n")
        path = os.path.join(sys.argv[1], name)
        if open(path, "rb").read() != text.encode("latin-1"):
            open(path, "wb").write(text.encode("latin-1"))
    print("switchbot: %d edit(s) applied, %d old bonus switcher line(s) taken out" % (applied, reverted))


if __name__ == "__main__":
    main()
